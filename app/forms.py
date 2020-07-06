from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, RadioField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
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
