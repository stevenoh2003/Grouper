import click
from app.database import db
from app import bcrypt
from .models import User
from flask import Blueprint

cmd = Blueprint('commands', __name__)

@cmd.cli.command("create_tables")
def create_tables():
	db.create_all()
	click.echo("Created database")

@cmd.cli.command("create_user", help="Args: email password role (Admin/Member)")
@click.argument("email", required=True)
@click.argument("password", required=True)
@click.argument("role", required=True)
def create_user(email, password, role):
	hashed_password = bcrypt.generate_password_hash(password.encode("utf-8")).decode("utf-8")
	new_user = User(email=email, password=hashed_password, role=role)
	db.session.add(new_user)
	db.session.commit()
	click.echo(f"Created User {role} {email} {hashed_password}")
