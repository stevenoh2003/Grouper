from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_admin import Admin
from flask_talisman import Talisman
from app.config import Config
from app.database import db, migrate

bcrypt = Bcrypt()
talisman = Talisman()
admin = Admin()
login_manager = LoginManager()
login_manager.login_view = "login" #pass in the function name of the login route
login_manager.login_message_category = "info" #Styles "Please log in to view this page" with Bootstrap "info" class

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    talisman.init_app(app, content_security_policy=None)

    from app.main.routes import main
    from app.users.routes import users
    from app.commands import cmd

    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(cmd)

    return app
