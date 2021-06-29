from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask_login import current_user, login_required, login_user, logout_user
from app.database import db
from app.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm
from app.users.utils import send_reset_email
from app import bcrypt
from app.models import User, Classroom, Student
import os, io, csv

users = Blueprint("users", __name__)

@users.route('/register', methods=["GET", "POST"])
def register():
	if current_user.is_authenticated: #if the user is already logged in
		return redirect(url_for("main.home")) #redirect the user back to the home page

	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
		user = User(email=form.email.data, password=hashed_password) #pass in the UTF-8 hashed password, not the plain text nor binary
		db.session.add(user)
		db.session.commit()
		flash(f"Account created for {form.email.data}!", "success")

		return redirect(url_for("users.login"))
	return render_template("register.html", title="Register", form=form)


@users.route('/login', methods=["GET", "POST"])
def login():
	if current_user.is_authenticated: #if the user is already logged in
		return redirect(url_for("main.home")) #redirect the user back to the home page

	form = LoginForm()
	if form.validate_on_submit(): #form details are valid - email submitted, password filled in
		user = User.query.filter_by(email=form.email.data).first() #check if there are any emails within our database matching the email that the user entered
		if user and bcrypt.check_password_hash(user.password, form.password.data): #if the email exists and the password hash is valid
			login_user(user, remember=form.remember.data)

			#If the user tried to access a log-in only page and was redirected to /login, then automatically send the user back to where they were going.
			#Otherwise, redirect to the home page
			next_page = request.args.get("next")
			flash("You are logged in!", "success")
			return redirect(next_page) if next_page else redirect(url_for("main.home"))
		else: #login is unsuccessful
			flash("Invalid!", "danger") #danger alert (Bootstrap)
	return render_template("login.html", title="Login", form=form)

@users.route("/logout")
def logout():
	logout_user()
	return redirect(url_for("main.home"))

@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		
		#https://stackoverflow.com/questions/57641300/flasks-request-files-getlist-for-isnt-empty-when-field-is-not-submitted
		#https://stackoverflow.com/questions/58765033/multifilefield-doesnt-return-files-returns-str
		custom_group_files = request.files.getlist(form.custom_groups.name)
		if custom_group_files and all(f for f in custom_group_files):
			for custom_group_file in custom_group_files:
				pass

		class_files = request.files.getlist(form.students.name)
		if class_files and all(f for f in class_files):
			for class_file in class_files: #type(class_file) = <class 'werkzeug.datastructures.FileStorage'>
				csv_reader = csv.DictReader(io.StringIO(class_file.stream.read().decode("UTF8"), newline=None), delimiter=",")
				class_name = os.path.splitext(class_file.filename)[0]

				#create a classroom with the filename of the CSV as the name
				current_user.create_classroom(name=class_name)
				c = Classroom.query.filter_by(name=class_name).first()
				db.session.add(c)
				db.session.commit()

				#add Students in the file to the newly created classroom
				for line in csv_reader:
					s = Student(name=line["Name"], nationality=line["Nationality"], email=line["Email"])
					c.students.append(s)
				db.session.commit()

		current_user.email = form.email.data
		db.session.commit()
		flash("Your profile has been updated!", "success")
		return redirect(url_for("users.account"))
	elif request.method == "GET": #populate the form fields with the user's existing email
		form.email.data = current_user.email
	return render_template("account.html", title="Account", form=form)


@users.route("/reset_request", methods=["GET", "POST"])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for("main.home"))	

	form = RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_reset_email(user)
		flash("An email has been sent with instructions to reset your password.", "info")
		return redirect(url_for("users.login"))

	return render_template("reset_request.html", title="Reset Password", form=form)

@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect(url_for("main.home"))

	user = User.verify_reset_token(token)
	if not user:
		flash("The token is invalid or expired.", "warning")
		return redirect(url_for("users.reset_request"))

	form = ResetPasswordForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
		user.password = hashed_password
		db.session.commit()
		flash(f"Your password has been updated!", "success")
		return redirect(url_for("users.login"))
	return render_template("reset_password.html", title="Reset Password", form=form)