from app import app, db, bcrypt #from the __init__.py inside app/
from app.models import User
from app.selenium_model import get_google_meet_link
import concurrent.futures
from app.forms import RegistrationForm, LoginForm, GrouperForm, UpdateAccountForm
from werkzeug.utils import secure_filename
from flask import render_template, url_for, flash, redirect, request, session
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os, glob
#Grouper algorithm
import random, csv
from itertools import cycle

@app.route("/")
@app.route("/home")
def home():
	return render_template("home.html")

@app.route('/register', methods=["GET", "POST"])
def register():
	if current_user.is_authenticated: #if the user is already logged in
		return redirect(url_for("home")) #redirect the user back to the home page

	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
		hashed_id = secrets.token_hex(8)
		user = User(email=form.email.data, password=hashed_password, user_hash=hashed_id) #pass in the UTF-8 hashed password, not the plain text nor binary
		db.session.add(user)
		db.session.commit()
		flash(f"Account created for {form.email.data}!", "success")
		return redirect(url_for("login"))
	return render_template("register.html", title="Register", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
	if current_user.is_authenticated: #if the user is already logged in
		return redirect(url_for("home")) #redirect the user back to the home page

	form = LoginForm()
	if form.validate_on_submit(): #form details are valid - email submitted, password filled in
		user = User.query.filter_by(email=form.email.data).first() #check if there are any emails within our database matching the email that the user entered
		if user and bcrypt.check_password_hash(user.password, form.password.data): #if the email exists and the password hash is valid
			login_user(user, remember=form.remember.data)

			#If the user tried to access a log-in only page and was redirected to /login, then automatically send the user back to where they were going.
			#Otherwise, redirect to the home page
			next_page = request.args.get("next")
			flash("You are logged in!", "success")
			return redirect(next_page) if next_page else redirect(url_for("home"))
		else: #login is unsuccessful
			flash("Invalid!", "danger") #danger alert (Bootstrap)
	return render_template("login.html", title="Login", form=form)

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for("home"))


def group(differentiator, num_groups, student_file):
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

@app.route('/grouper', methods=["GET", "POST"])
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
			groups = group(form.differentiator.data, form.num_groups.data, students_csv_path)
		else:
			groups = custom_group(os.path.join(app.root_path, f"static/users/{current_user.user_hash}/custom_groups", form.differentiator.data))

		if form.service.data == "Google Meet":
			NUM_GROUPS = form.num_groups.data
			links = []
			with concurrent.futures.ThreadPoolExecutor() as executor:
			    futures = [executor.submit(get_google_meet_link, form.gmail.data, form.gmail_password.data) for _ in range(NUM_GROUPS)]

			for future in concurrent.futures.as_completed(futures):
				links.append(future.result())
			
			groups = [(groups[index], links[index]) for index in range(form.num_groups.data)]

		session["groups"] = groups
		return redirect(url_for("results"))
	return render_template("grouper.html", title="Group Generator", form=form)

@app.route("/results")
def results():
    groups = session['groups'] # counterpart for session
    return render_template("results.html", title="Results", groups=groups)

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		
		#https://stackoverflow.com/questions/57641300/flasks-request-files-getlist-for-isnt-empty-when-field-is-not-submitted
		#https://stackoverflow.com/questions/58765033/multifilefield-doesnt-return-files-returns-str
		custom_group_files = request.files.getlist(form.custom_groups.name)
		if custom_group_files and all(f for f in custom_group_files):
			for custom_group_file in custom_group_files:
				custom_group_file.save(os.path.join(app.root_path, f"static/users/{current_user.user_hash}/custom_groups", custom_group_file.filename))

		class_files = request.files.getlist(form.students.name)
		if class_files and all(f for f in class_files):
			for class_file in class_files:
				class_file.save(os.path.join(app.root_path, f"static/users/{current_user.user_hash}/students", class_file.filename))

		current_user.email = form.email.data
		db.session.commit()
		flash("Your profile has been updated!", "success")
		return redirect(url_for("account"))
	elif request.method == "GET": #populate the form fields with the user's existing email
		form.email.data = current_user.email
	return render_template("account.html", title="Account", form=form)