from flask import Blueprint, render_template, flash, request, abort, redirect, url_for, session
from flask_login import current_user, login_required
from app.database import db
from app.main.selenium_model import get_google_meet_link
from app.main.forms import GrouperForm, SaveGroupForm
from itertools import cycle
import os, glob
import random, csv
import threading
import concurrent.futures


main = Blueprint("main", __name__)

@main.route("/")
@main.route("/home")
def home():
	return render_template("home.html")

def group_function(differentiator, num_groups, student_file):
	groups = [[] for _ in range(num_groups)]
	students = []

	with open(student_file, "r") as data_file:
	    csv_reader = csv.DictReader(data_file)
	    for line in csv_reader:
	        students.append(line)

	random.shuffle(students) #shuffle students

	if differentiator == "Random":
		students_iter = iter(students)

		#first, distribute all students evenly e.g. 4 4 4 for 14 students with 3 groups
		for group in groups:
			for _ in range(len(students)//num_groups):
				group.append(next(students_iter)["Name"])

		#distribute the remaining students e.g. 5 5 4 for 14 students with 3 groups
		for i in range(len(students)%num_groups):
			groups[i].append(next(students_iter)["Name"])

		return groups


	categories = {student[differentiator] for student in students} #e.g. {Male, Female} {American, Brazilian, Spanish} {10G, 10W, 9W}

	indices = cycle(''.join(str(x) for x in range(num_groups))) #cycles through the groups e.g. 0 1 2 0 1 2 0 1 2 (if num_groups = 3)

	for category in categories:
		students_with_category = [student for student in students if student[differentiator]==category]
		for student in students_with_category:
			groups[int(next(indices))].append(student["Name"])
	return groups

def custom_group(custom_group_file):
	students = []
	with open(custom_group_file, "r") as data_file:
		csv_reader = csv.reader(data_file)
		for line in csv_reader:
			students.append(line)
	return students

def send_link_email(recipients, link, service):
	msg = Message(
		f"{service} invitation", 
		sender=app.config["MAIL_USERNAME"], 
		recipients=recipients, 
		body = f"Please join the {service} call: {link}"
	)
	mail.send(msg)

@main.route('/grouper', methods=["GET", "POST"])
def grouper():
	form = GrouperForm()

	#form.differentiator
	current_working_directory = os.getcwd()
	os.chdir(f"app/static/users/{current_user.user_hash}/custom_groups")
	custom_group_csvs = glob.glob('*.csv')
	custom_group_choices = [(custom_group, custom_group) for custom_group in custom_group_csvs]
	form.differentiator.choices = [("Random", "Random"), ("Gender", "Gender"), ("Homeroom", "Homeroom"), ("Nationality", "Nationality")] + custom_group_choices
	os.chdir(current_working_directory) #Go back to the original working directory - should be equal to os.chdir(f"../../../../../")

	#form.students
	current_working_directory = os.getcwd()
	os.chdir(f"app/static/users/{current_user.user_hash}/students")
	student_csvs = glob.glob('*.csv')
	form.students.choices = [(student_list, student_list) for student_list in student_csvs]
	os.chdir(current_working_directory) #Go back to the original working directory - should be equal to os.chdir(f"../../../../../")


	if form.validate_on_submit():
		if form.differentiator.data in ["Random", "Gender", "Homeroom", "Nationality"]:
			students_csv_path = os.path.join(app.root_path, f"static/users/{current_user.user_hash}/students", form.students.data)
			groups = group_function(form.differentiator.data, form.num_groups.data, students_csv_path)
			is_custom_group = False
		else:
			is_custom_group = True
			groups = custom_group(os.path.join(app.root_path, f"static/users/{current_user.user_hash}/custom_groups", form.differentiator.data))

		if form.service.data == "Google Meet":
			NUM_GROUPS = form.num_groups.data
			links = []
			with concurrent.futures.ThreadPoolExecutor() as executor:
			    futures = [executor.submit(get_google_meet_link, form.gmail.data, form.gmail_password.data) for _ in range(NUM_GROUPS)]

			for future in concurrent.futures.as_completed(futures):
				links.append(future.result())
			
			groups = [(groups[index], links[index]) for index in range(form.num_groups.data)]

		
		if form.send_email:
			links = [group[1] for group in groups]
			if is_custom_group:
				recipients = [group[0] for group in groups]
			else:
				recipients = []
				for group in groups:
					with open(os.path.join(app.root_path, f"static/users/{current_user.user_hash}/students", form.students.data), "r") as data_file:
						csv_reader = csv.DictReader(data_file)
						#recipients = [[line["Email"] for line in csv.DictReader(data_file) if line["Name"] in group[0]] for group in groups]
						recipients.append([line["Email"] for line in csv.DictReader(data_file) if line["Name"] in group[0]])

			flash(recipients, "info")
			flash(links, "info")
			"""
			threads = []
			for i in range(form.num_groups.data): #_ is a throw away variable - "ignore this" variable
			    t = threading.Thread(target=send_link_email, args=[recipients[i], links[i], form.service.data]) #Note: do_something, NOT do_something()
			    t.start()
			    threads.append(t)

			for thread in threads:
			    thread.join() #Make sure the thread completes before moving on because otherwise the timer wouldn't work
			"""

			#with concurrent.futures.ThreadPoolExecutor() as executor:		
			#	results = executor.map(send_link_email, recipients, links, form.service.data)
			#for result in results:
			#	print(result)
			#map(send_link_email, recipients, links, form.service.data)

			for i in range(form.num_groups.data):
				send_link_email(recipients[i], links[i], form.service.data)

		session["groups"] = groups
		return redirect(url_for("results", is_custom_group=is_custom_group))
	return render_template("grouper.html", title="Group Generator", form=form)

@main.route("/results/<int:is_custom_group>", methods=["GET", "POST"])
def results(is_custom_group):
    groups = session['groups'] # counterpart for session
    if not is_custom_group:
    	form = SaveGroupForm()

    	if form.validate_on_submit():
    		filename = form.filename.data
    		with open(f"app/static/users/{current_user.user_hash}/custom_groups/{filename}.csv", "w") as csv_file:
    			csv_writer = csv.writer(csv_file, delimiter=",")
    			for group in groups:
    				csv_writer.writerow(group)
    		flash(f"The custom group {filename} has been saved for use later!", "success")
    	return render_template("results.html", title="Results", groups=groups, form=form)
    else:
    	return render_template("results.html", title="Results", groups=groups)