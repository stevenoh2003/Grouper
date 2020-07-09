from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from app import db, login_manager, app #import db and login_manager variables from __init__.py
from flask_login import UserMixin #video 6

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)
	user_hash = db.Column(db.String(8), nullable=False, unique=True)

	def get_reset_token(self, expires_seconds=1800):
		serializer_obj = Serializer(app.config["SECRET_KEY"], expires_seconds)
		return serializer_obj.dumps({"user_id": self.id}).decode()

	@staticmethod
	def verify_reset_token(token):
		serializer_obj = Serializer(app.config["SECRET_KEY"])
		try: 
			user_id = serializer_obj.loads(token)["user_id"]
		except: #token expired. itsdangerous.exc.SignatureExpired: Signature expired
			return None
		return User.query.get(user_id)

	def __repr__(self):
		return f"User({self.email}, {self.image_file})"