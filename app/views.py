from app import app, db, bcrypt #from the __init__.py inside app/
from app.models import User
from app.forms import RegistrationForm, LoginForm, GrouperForm
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

@app.route("/results")
def results():
    groups = session['groups'] # counterpart for session
    return render_template("results.html", title="Results", groups=groups)