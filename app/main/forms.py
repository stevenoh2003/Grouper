from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, SelectField, IntegerField
from wtforms.validators import DataRequired, Optional

class GrouperForm(FlaskForm):
	num_groups = IntegerField("Number of Groups", validators=[Optional()])
	differentiator = SelectField("Group by", coerce=str) #TODO: Add custom groups
	students = SelectField("Class", coerce=str)
	service = RadioField("Service", choices=[("Google Meet", "Google Meet"), ("Zoom", "Zoom"), ("None", "None")], validators=[Optional()], default="None")
	send_email = BooleanField("Send Email", description="Send an email with the video conference link to each participant")
	gmail = StringField("Your Gmail")
	gmail_password = PasswordField("Your Gmail Password")
	submit = SubmitField("Generate")


class SaveGroupForm(FlaskForm):
	filename = StringField("Group name", validators=[DataRequired()])
	submit = SubmitField("Save group")