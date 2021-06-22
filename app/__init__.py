from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from dotenv import load_dotenv
import os
from flask_mail import Mail
from flask_admin import Admin
from flask_talisman import Talisman
from flask_migrate import Migrate

app = Flask(__name__)

load_dotenv()
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") #protect against cookie manipulation and attacks
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db, render_as_batch=True)
talisman = Talisman(app, content_security_policy=None)

login_manager = LoginManager(app)
login_manager.login_view = "login" #pass in the function name of the login route
login_manager.login_message_category = "info" #Styles "Please log in to view this page" with Bootstrap "info" class

admin = Admin(app)

app.config["MAIL_SERVER"] = "smtp.googlemail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("EMAIL")
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASSWORD")
mail = Mail(app)

from app import views