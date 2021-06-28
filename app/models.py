from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from app import login_manager, admin
from app.database import db
from flask_login import UserMixin, current_user
from flask_admin.contrib.sqla import ModelView

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)
	role = db.Column(db.String(10), default="Member")
	classrooms = db.relationship('Classroom', backref='teacher', lazy=True) #Classroom.teacher, User.classrooms

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

	def create_classroom(self, name):
		new_class = Classroom(teacher_id=self.id, name=name)
		db.session.add(new_class)
		db.session.commit()

	def __repr__(self):
		return f"User({self.email}, {self.role})"


class Classroom(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), unique=False)
	teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	students = db.relationship("Student", secondary="student_classroom", lazy=True) #Student.classes, Classroom.members

	def __repr__(self):
		return f"Class({self.name} {self.teacher_id})"


class Student(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), unique=False)
	email = db.Column(db.String(120), unique=True)
	nationality = db.Column(db.String(30), unique=False)
	birthday = db.Column(db.DateTime, unique=False)
	classes = db.relationship("Classroom", secondary="student_classroom", lazy=True) #Classroom.students, Student.

	def __repr__(self):
		return f"Student({self.name}, {self.classes})"


class StudentClassroom(db.Model):
    __tablename__ = 'student_classroom'

    id = db.Column(db.Integer(), primary_key=True)
    student_id = db.Column(db.Integer(), db.ForeignKey('student.id'))
    classroom_id = db.Column(db.Integer(), db.ForeignKey('classroom.id'))


class StudentView(ModelView):
    column_hide_backrefs = False
    column_list = ('name', 'email', 'nationality', 'birthday', 'classes')
    def is_accessible(self):
    	return current_user.is_authenticated and current_user.role == "Admin" 


class TeacherView(ModelView):
    column_hide_backrefs = False
    column_list = ('role', 'email', 'classrooms')
    def is_accessible(self):
    	return current_user.is_authenticated and current_user.role == "Admin" 	


class ClassroomView(ModelView):
    column_hide_backrefs = False
    column_list = ('name', 'teacher', 'students')
    def is_accessible(self):
    	return current_user.is_authenticated and current_user.role == "Admin" 


admin.add_view(TeacherView(User, db.session))
admin.add_view(ClassroomView(Classroom, db.session))
admin.add_view(StudentView(Student, db.session))
