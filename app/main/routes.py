from flask import Blueprint, render_template, flash, request, abort, redirect, url_for, session
from flask_login import current_user, login_required
from app.database import db
from app.main.selenium_model import get_google_meet_link
from app.main.forms import GrouperForm, SaveGroupForm
from app.models import Classroom
from itertools import cycle
import os
import glob
import random
import csv
import threading
import concurrent.futures


main = Blueprint("main", __name__)


@main.route("/")
@main.route("/home")
def home():
	return render_template("home.html")


def group_function(differentiator, num_groups, students):
	groups = [[] for _ in range(num_groups)]

	random.shuffle(students)  # shuffle students

	if differentiator == "Random":
		students_iter = iter(students)

		#first, distribute all students evenly e.g. 4 4 4 for 14 students with 3 groups
		for group in groups:
			for _ in range(len(students)//num_groups):
				group.append(next(students_iter).name)

		#distribute the remaining students e.g. 5 5 4 for 14 students with 3 groups
		for i in range(len(students) % num_groups):
			groups[i].append(next(students_iter).name)

		return groups

	# e.g. {Male, Female} {American, Brazilian, Spanish} {10G, 10W, 9W}
	categories = {getattr(student, differentiator.lower())
               for student in students}

	# cycles through the groups e.g. 0 1 2 0 1 2 0 1 2 (if num_groups = 3)
	indices = cycle(''.join(str(x) for x in range(num_groups)))

	for category in categories:
		students_with_category = [student for student in students if getattr(
			student, differentiator.lower()) == category]
		for student in students_with_category:
			groups[int(next(indices))].append(student.name)
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
		body=f"Please join the {service} call: {link}"
	)
	mail.send(msg)


@main.route('/grouper', methods=["GET", "POST"])
def grouper():
	form = GrouperForm()

	form.differentiator.choices = [("Random", "Random"), ("Gender", "Gender"), (
		"Homeroom", "Homeroom"), ("Nationality", "Nationality")]

	all_classes = Classroom.query.filter_by(teacher_id=current_user.id).all()
	form.classes.choices = [(classroom.name, classroom.name)
                         for classroom in all_classes]

	if form.validate_on_submit():
		students = Classroom.query.filter_by(
			teacher_id=current_user.id, name=form.classes.data).first().students

		if form.differentiator.data in ["Random", "Gender", "Homeroom", "Nationality"]:
			groups = group_function(form.differentiator.data,
			                        form.num_groups.data, students)

		session["groups"] = groups
		return redirect(url_for("main.results"))
	return render_template("grouper.html", title="Group Generator", form=form)


@main.route("/results", methods=["GET", "POST"])
def results():
	groups = session['groups']  # counterpart for session

	form = SaveGroupForm()

	if form.validate_on_submit():
		filename = form.filename.data
		with open(f"app/static/users/{current_user.user_hash}/custom_groups/{filename}.csv", "w") as csv_file:
			csv_writer = csv.writer(csv_file, delimiter=",")
			for group in groups:
				csv_writer.writerow(group)
		flash(
			f"The custom group {filename} has been saved for use later!", "success")
		return redirect(url_for("main.home"))
	return render_template("results.html", title="Results", groups=groups, form=form)
