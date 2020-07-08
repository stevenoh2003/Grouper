from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, RadioField, SelectField, MultipleFileField, IntegerField
from flask_wtf.file import FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User
from flask_login import current_user


class RegistrationForm(FlaskForm):
	email = StringField("Email", validators=[DataRequired(), Email()])
	password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=60)])
	confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
	submit = SubmitField("Register")

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first() #if email exists - if not, None
		if user:
			raise ValidationError("This email is taken.")


class LoginForm(FlaskForm):
 	email = StringField("Email", validators=[DataRequired(), Email()])

 	password = PasswordField("Password", validators=[DataRequired()])
 	remember = BooleanField("Remember Me")

 	submit = SubmitField("Login")

class GrouperForm(FlaskForm):
	num_groups = IntegerField("Number of Groups", validators=[Optional()])
	differentiator = SelectField("Group by", coerce=str) #TODO: Add custom groups
	students = SelectField("Class", coerce=str)
	service = RadioField("Service", choices=[("Google Meet", "Google Meet"), ("Zoom", "Zoom")], validators=[Optional()])
	send_email = BooleanField("Send Email", default=True, description="Send an email with the video conference link to each participant")
	submit = SubmitField("Generate")

class UpdateAccountForm(FlaskForm):
	email = StringField("Email", validators=[DataRequired(), Email()])
	students = MultipleFileField("Students database", validators=[FileAllowed(["csv"])])
	custom_groups = MultipleFileField("Custom groups", validators=[FileAllowed(["csv"])])
	submit = SubmitField("Update")

	def validate_email(self, email):
		if email.data != current_user.email:
			user = User.query.filter_by(email=email.data).first() #if email exists - if not, None
			if user:
				raise ValidationError("This email is taken.")