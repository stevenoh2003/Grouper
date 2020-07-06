from app import app, db, bcrypt #from the __init__.py inside app/
from app.models import User
from app.forms import RegistrationForm, LoginForm
from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required


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
		user = User(email=form.email.data, password=hashed_password) #pass in the UTF-8 hashed password, not the plain text nor binary
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

@app.route('/grouper', methods=["GET", "POST"])