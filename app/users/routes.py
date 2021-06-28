from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask_login import current_user, login_required, login_user, logout_user
from app.database import db
from app.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm
from app.users.utils import send_reset_email
from app import bcrypt
from app.models import User
import secrets
import os

users = Blueprint("users", __name__)

@users.route('/register', methods=["GET", "POST"])
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

		#Create folders for this user
		current_working_directory = os.getcwd()
		os.mkdir(f"app/static/users/{hashed_id}")
		os.chdir(f"app/static/users/{hashed_id}")
		os.mkdir("students")
		os.mkdir("custom_groups")
		os.chdir(current_working_directory)
		return redirect(url_for("login"))
	return render_template("register.html", title="Register", form=form)


@users.route('/login', methods=["GET", "POST"])
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

@users.route("/logout")
def logout():
	logout_user()
	return redirect(url_for("home"))

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


@users.route("/reset_request", methods=["GET", "POST"])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for("home"))	

	form = RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_reset_email(user.email)
		flash("An email has been sent with instructions to reset your password.", "info")
		return redirect(url_for("login"))

	return render_template("reset_request.html", title="Reset Password", form=form)

@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect(url_for("home"))

	user = User.verify_reset_token(token)
	if not user:
		flash("The token is invalid or expired.", "warning")
		return redirect(url_for("reset_request"))

	form = ResetPasswordForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
		user.password = hashed_password
		db.session.commit()
		flash(f"Your password has been updated!", "success")
		return redirect(url_for("login"))
	return render_template("reset_password.html", title="Reset Password", form=form)