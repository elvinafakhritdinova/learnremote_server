import datetime

from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import *

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'df9d9b8a053375dbae2758d00192748b77c1208ddd6e478c65b35e982c3c633b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = Column(Integer(), primary_key=True)
    username = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False, default="teacher")
    last_login_time = Column(DateTime, default=datetime.datetime.now())
    usergroup = relationship('UserGroup',backref='user', lazy = 'dynamic',cascade="all, delete")
    studcoins = relationship('StudCoins',backref='user', lazy = 'dynamic',cascade="all, delete")
    marks = relationship('Marks',backref='user', lazy = 'dynamic',cascade="all, delete")
    notification = relationship('StudNotification', backref = 'user', lazy='dynamic',cascade="all, delete")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"user {self.username}"

class StudCoins(db.Model):
    __tablename__ = "studcoins"
    id = Column(Integer(), primary_key = True)
    user_id = Column(Integer,ForeignKey('user.id'))
    coins=Column(Integer, nullable=False)
    kredit=Column(Integer, nullable=False)

class Course(db.Model):
    __tablename__ = "course"
    id = Column(Integer(), primary_key=True)
    title = Column(String(255), nullable=False)
    max_score= Column(Integer(), nullable=False)
    test = relationship('Test', backref='course', lazy='dynamic',cascade="all, delete")
    lecture = relationship('Lecture', backref='course', lazy='dynamic',cascade="all, delete")
    groupcourse = relationship('GroupCourse', backref='course', lazy='dynamic',cascade="all, delete")


class GroupCourse(db.Model):
    __tablename__ = "groupcourse"
    id = Column(Integer(), primary_key = True)
    group_id = Column(Integer,ForeignKey('group.id'))
    course_id = Column(Integer,ForeignKey('course.id'))
    active=Column(Boolean,nullable = False)

class UserGroup(db.Model):
    __tablename__ = "usergroup"
    id = Column(Integer(), primary_key = True)
    group_id = Column(Integer,ForeignKey('group.id'))
    user_id = Column(Integer,ForeignKey('user.id'))

class Marks(db.Model):
    __tablename__ = "marks"
    id = Column(Integer(), primary_key = True)
    mark = Column(String(255), nullable = False)
    date = Column(DateTime, nullable = False)
    user_id = Column(Integer,ForeignKey('user.id'))
    part_id = Column(Integer, ForeignKey('part.id'))

class Test(db.Model):
    __tablename__ = "test"
    id = Column(Integer(), primary_key=True)
    title = Column(String(255), nullable=False)
    type = Column(Integer(), nullable=False)
    #close_date = Column(DateTime, nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'))
    part = relationship('Part', backref='test', lazy='dynamic',cascade="all, delete")
    deadline = relationship('Deadline', backref='test', lazy='dynamic',cascade="all, delete")

    #таблица сроков сдачи тестов для групп 
class Deadline(db.Model):
    __tablename__ = "deadline"
    id = Column(Integer(), primary_key=True)
    group_id = Column(Integer, ForeignKey('group.id'))
    test_id=Column(Integer, ForeignKey('test.id'))
    date = Column(DateTime, nullable=False)
    

class Part(db.Model):
    __tablename__ = "part"
    id = Column(Integer(), primary_key=True)
    text = Column(String(255),nullable = False)
    number = Column(Integer, nullable = False)
    test_id = Column(Integer, ForeignKey('test.id'))
    lecture_id=Column(Integer, ForeignKey('lecture.id'))
    question = relationship('Question', backref='part', lazy='dynamic',cascade="all, delete")
    marks = relationship('Marks',backref='part', lazy = 'dynamic',cascade="all, delete")


class Question(db.Model):
    __tablename__ = "question"
    id = Column(Integer(), primary_key=True)
    title = Column(String(255), nullable=False)
    number = Column(Integer, nullable = False)
    part_id = Column(Integer, ForeignKey('part.id'))
    answer = relationship('Answer', backref='question', lazy='dynamic',cascade="all, delete")


class Answer(db.Model):
    __tablename__ = "answer"
    id = Column(Integer(), primary_key=True)
    text = Column(Text, nullable=False)
    isTrue = Column(Integer,nullable=False,default=0)
    question_id = Column(Integer, ForeignKey('question.id'))


class Group(db.Model):
    __tablename__ = "group"
    id = Column(Integer(), primary_key=True)
    name = Column(Text, nullable=False)
    code = Column(Text, nullable=False)
    notification = relationship('Notification', backref = 'group', lazy='dynamic',cascade="all, delete")
    groupcourse = relationship('GroupCourse', backref='group', lazy='dynamic',cascade="all, delete")
    usergroup = relationship('UserGroup',backref='group', lazy = 'dynamic',cascade="all, delete")
    deadline = relationship('Deadline', backref='group', lazy='dynamic',cascade="all, delete")


class Notification(db.Model,SerializerMixin):
    __tablename__ = "notifications"
    serialize_only = ('id', 'text', 'date')
    id = Column(Integer(), primary_key = True)
    text = Column(String(255),nullable = False)
    date = Column(DateTime, nullable = false)
    group_id = Column(Integer, ForeignKey('group.id'))

class StudNotification(db.Model,SerializerMixin):
    __tablename__ = "studnotifications"
    serialize_only = ('id', 'text', 'date')
    id = Column(Integer(), primary_key = True)
    text = Column(String(255),nullable = False)
    date = Column(DateTime, nullable = false)
    student_id = Column(Integer, ForeignKey('user.id'))

class InviteCode(db.Model):
    __tablename__ = "invite_code"
    id = Column(Integer(), primary_key=True)
    text = Column(Text, nullable=False)


class Lecture(db.Model,SerializerMixin):
    __tablename__ = "lecture"
    serialize_only = ('id', 'title', 'sub_title', 'path_to_file')
    id = Column(Integer(), primary_key=True)
    title = Column(String(255), nullable=False)
    sub_title = Column(String(255),nullable=False)
    path_to_file = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'))
    part = relationship('Part', backref='lecture', lazy='dynamic',cascade="all, delete")
    