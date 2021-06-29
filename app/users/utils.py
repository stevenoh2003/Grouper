import os
from flask import url_for
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_reset_email(user):
	token = user.get_reset_token()
	message = Mail(
		from_email=os.environ.get('MAIL_USERNAME'), 
		to_emails=(user.email),
		subject="Password Reset Request",
		html_content = f"""
			<p>
			To reset your password, visit the following link:
			{url_for("users.reset_password", token=token, _external=True)}
			</p>

			<p>
			If you did not make this request then simply ignore this email.
			</p>
		""" #_external is to get an absolute URL instead of a relative URL
		)
	try:
	    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
	    response = sg.send(message)
	    print(response.status_code)
	    print(response.body)
	    print(response.headers)
	except Exception as e:
		print(e.body)