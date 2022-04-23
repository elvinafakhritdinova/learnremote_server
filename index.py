import datetime
import calendar
import random
import string
import xml.etree.ElementTree as ET
from os.path import dirname, join, realpath,exists
import flask
from flask import render_template, request, jsonify, flash, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy.sql.expression import null
from operator import attrgetter #кама 

from model import Deadline, StudCoins, StudNotification, db, Lecture, app, User, Test, Question, Course, Answer, Group, InviteCode,GroupCourse,UserGroup,Marks,Part,Notification
import api

import logging
logging.basicConfig(filename='record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
@app.context_processor
def utility_processor():
    def format_date(date1, days,date2=datetime.datetime.now()):
        
        date1=datetime.datetime.strptime(date1, '%d.%m.%Y')
        days_in_month = calendar.monthrange(date1.year, date1.month)[1]
        date1plus1month=date1+datetime.timedelta(days=days_in_month)
        days_in_month2 = calendar.monthrange(date1plus1month.year, date1plus1month.month)[1]
        date1plus2month=date1plus1month+datetime.timedelta(days=days_in_month2)
        if days==7:
            if date1-datetime.timedelta(days=7)> date2:
                return True
        if days==30 and date1plus1month < date2 and date1plus2month > date2:
            return True
        if days==60 and date1plus2month< date2:
            return True
        return False
    return dict(format_date=format_date)
@app.route('/blogs')
def blog():
    app.logger.info('Info level log')
    app.logger.warning('Warning level log')
    return f"Welcome to the Blog"
 
app.run(host='localhost', debug=True)

db.create_all()
login_manager = LoginManager(app)
login_manager.login_view = '/'

UPLOAD_FOLDER = 'data/uploads'
XML_FOLDER = 'data/xml'
ALLOWED_EXTENSIONS = {'doc', 'docx', 'pdf', 'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['XML_FOLDER'] = XML_FOLDER
class UserMarks(object):
    def __init__(self,user_id,theme,theme_id,part_theme,part_id,mark,date, tries):
        self.user_id=user_id
        self.theme = theme
        self.theme_id = theme_id
        self.part_theme = part_theme
        self.part_id = part_id
        self.mark=mark
        self.date=date
        self.tries =tries

class ResultClass(object):
    def __init__(self, average, done, out_of):
        self.average = average
        self.done = done
        self.out_of = out_of

def create_XML_Test(test_id):
    test = db.session.query(Test).filter(Test.id == test_id).first()
    parts = db.session.query(Part).filter(Part.test_id==test_id).all()
    testRoot = ET.Element("test", theme = test.title)
    for part in parts:
        partElement = ET.SubElement(testRoot, "part", number = str(part.number),part_id = str(part.id))
        textPartElement = ET.SubElement(partElement, "text")
        textPartElement.text=part.text
        allquestions=db.session.query(Question).filter(Question.part_id==part.id).all()
        
        if test.type==20 and len(allquestions)>9:
            questions=random.sample(allquestions,5)
            num=1
            for question in questions:
                questionElement = ET.SubElement(partElement,"question",number = str(num))
                textQuestionElement = ET.SubElement(questionElement, "text")
                textQuestionElement.text = question.title
                answers = db.session.query(Answer).filter(Answer.question_id==question.id).all()
                answersElement = ET.SubElement(questionElement,"answers")
                for answer in answers:
                    singleAnswerElement = ET.SubElement(answersElement,"answer", isTrue = str(answer.isTrue))
                    answerTextElement = ET.SubElement(singleAnswerElement,"text")
                    answerTextElement.text = answer.text
                num+=1
        else:
            questions = db.session.query(Question).filter(Question.part_id==part.id).all()
            for question in questions:
                questionElement = ET.SubElement(partElement,"question",number = str(question.number+1))
                textQuestionElement = ET.SubElement(questionElement, "text")
                textQuestionElement.text = question.title
                answers = db.session.query(Answer).filter(Answer.question_id==question.id).all()
                answersElement = ET.SubElement(questionElement,"answers")
                for answer in answers:
                    singleAnswerElement = ET.SubElement(answersElement,"answer", isTrue = str(answer.isTrue))
                    answerTextElement = ET.SubElement(singleAnswerElement,"text")
                    answerTextElement.text = answer.text
    tree = ET.ElementTree(testRoot)
    tree.write(join(dirname(realpath(__file__)),app.config['XML_FOLDER'])+"/"+test_id+".xml", encoding="UTF-8",xml_declaration=True)

#join(dirname(realpath(__file__)), app.config['UPLOAD_FOLDER']) + "/" + file.filename
"""
def insert_xml():
    tree = ET.parse('zalog.xml')
    root = tree.getroot()
    print(root[0][0].text)
    for child in root:
        print(child.tag, child.attrib)
        for two in child:
            print(two.tag, two.attrib)

insert_xml()
"""
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def insert_admin():
    if not db.session.query(User).filter(User.username == "admin").first():
        user = User(username="admin", name="admin", surname="admin", email="admin@admin.ru", role="admin")
        user.set_password("2W9UeqgVfu")
        db.session.add(user)
        db.session.commit()


insert_admin()
#create_XML_Test(1)

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


@app.route("/add_course", methods=['POST'])
@login_required
def add_course():
    if not db.session.query(Course).filter(Course.title == request.form.get("title")).first():
        title = request.form.get('title')
        course = Course(title=title,max_score=100)
        db.session.add(course)
        db.session.commit()
        return show_course_panel()
    else:
        return show_course_panel(message="Курс с таким именем уже существует !!!")

@app.route("/edit_max_score", methods=['POST'])
@login_required
def edit_max_score():
    course_id = request.form.get("course_id")
    max_score=request.form.get("max_score")
    i = db.session.query(Course).filter(Course.id == course_id).first()
    i.max_score = max_score
    db.session.add(i)
    db.session.commit()
    return show_course_control_panel(message="Максимальное количество баллов изменено", course_id=course_id)

@app.route("/edit_lecture<part_id>", methods=['POST'])
@login_required
def edit_lecture(part_id):
    part_id = request.form.get("part_id")
    lecture_id = request.form.get("lecture_id")
    i = db.session.query(Part).filter(Part.id == part_id).first()
    i.lecture_id = lecture_id
    db.session.add(i)
    db.session.commit()
    return show_part(part_id,message="Привязка к лекции изменена")

@app.route("/edit_active<course_id>", methods=['POST'])
@login_required
def edit_active(course_id):
    course_id = request.form.get("course_id")
    group_id = request.form.get("group_id")
    i = db.session.query(GroupCourse).filter(GroupCourse.course_id == course_id,GroupCourse.group_id==group_id).first()
    if i.active==True:
        i.active = False
    else:        
        i.active = True
    db.session.add(i)
    db.session.commit()
    return show_group_list_courses(group_id)

@app.route("/add_deadline", methods=['POST'])
@login_required
def add_deadline():
    test_id= int(request.form.get('test_id'))
    group_id=int(request.form.get('group_id'))
    test=db.session.query(Test).filter(Test.id == test_id).first()
    date=datetime.datetime.fromisoformat(request.form.get('date'))
    if not db.session.query(Deadline).filter(Deadline.test_id == test_id,Deadline.group_id==group_id).first():
        deadline=Deadline(group_id=group_id,test_id=test_id,date=date)
        db.session.add(deadline)
        db.session.commit()
    else:
        i = db.session.query(Deadline).filter(Deadline.test_id == test_id,Deadline.group_id==group_id).first()
        i.date = date
        db.session.add(i)
        db.session.commit()
    return show_group_list(group_id=group_id,course_id=test.course_id)

@app.route("/student_transfer", methods=['POST'])
@login_required
def student_transfer():
    student_id= int(request.form.get('student_id'))
    new_group_id=int(request.form.get('new_group_id'))
    group_id=int(request.form.get('group_id'))
    course_id=int(request.form.get('course_id'))
    i = db.session.query(UserGroup).filter(UserGroup.user_id == student_id).first()
    i.group_id = new_group_id
    db.session.add(i)
    db.session.commit()
    return show_group_list(group_id=group_id,course_id=course_id)

@app.route("/add_group_to_course", methods=['POST'])
@login_required
def add_groupcourse():
    course_id = request.form.get('course_id')
    if not db.session.query(GroupCourse).filter(GroupCourse.course_id==request.form.get('course_id')).filter(GroupCourse.group_id==request.form.get('group_id')).first():
        group_id = request.form.get('group_id')
        othergroupcourse = db.session.query(GroupCourse).filter(GroupCourse.course_id != course_id, GroupCourse.group_id==group_id).all()
        if othergroupcourse:
            for i in othergroupcourse:
                i.active=False
                db.session.add(i)
        groupcourse = GroupCourse(group_id=group_id, course_id = course_id,active=True)#active=True добавила
        db.session.add(groupcourse)
        
        db.session.commit()
        return show_course_overview(course_id,message="Группа успешно прикреплена к курсу")
    else:
        return show_course_overview(message="Эта группа уже прикреплена к курсу", course_id=course_id)


@app.route('/add_lecture', methods=['POST'])
@login_required
def add_lecture():
    course_id = request.form.get("course_id")
    course = db.session.query(Course).filter(Course.id == course_id).first()
    title = request.form.get('title')
    sub_title = request.form.get('sub_title')
    file = request.files['file']
    if file and allowed_file(file.filename):
        file.save(join(dirname(realpath(__file__)), app.config['UPLOAD_FOLDER']) + "/" + file.filename)
        #print(join(dirname(realpath(__file__)), app.config['UPLOAD_FOLDER']) + "/" + file.filename)
        # file.save(app.config['UPLOAD_FOLDER'] + "/" + file.filename)
        lecture = Lecture(title=title,sub_title=sub_title, path_to_file=file.filename,
                          course=course)
        db.session.add(lecture)
        db.session.commit()
        return show_course_control_panel(course_id=course_id,
                                         message="Лекция успешно добавлена")
    else:
        return show_course_control_panel(course_id=course_id,
                                         message="Допустимые форматы pdf,doc,jpg,jpeg")


@app.route('/test<test_id>', methods=['GET', 'POST'])
@login_required
def show_test(test_id):
    course_id = request.form.get("course_id")
    if course_id is None:
        course_id = request.args.get("course_id")
    test = db.session.query(Test).filter(Test.id == test_id).first()
    parts = db.session.query(Part).filter(Part.test_id == test_id).all()
    return render_template("test.html", title=test.title, test_id =test_id, course_id=course_id, parts=parts)



@app.route('/part<part_id>', methods=['POST'])
@login_required
def show_part(part_id, message=""):
    course_id = request.form.get("course_id")
    test_id = request.form.get("test_id")
    lectures = db.session.query(Lecture).filter(Lecture.course_id == course_id).all()
    if not part_id:
        part_id = request.form.get("part_id")

    part = db.session.query(Part).filter(Part.id == part_id).first()
    part_lecture=db.session.query(Lecture).filter(Lecture.id == part.lecture_id).first()
    if test_id is None:
        test_id=part.test_id
    if course_id is None:
        test = db.session.query(Test).filter(Test.id ==test_id).first()
        course_id = test.course_id
    count = 0
    for _ in part.question.all():
        count += 1
    
    return render_template("part.html", title=part.text, questions=part.question.all(), count=count,test_id =test_id, course_id=course_id, part_id = part_id,lectures=lectures,part_lecture=part_lecture)


@app.route('/lecture<lecture_id>', methods=['POST'])
@login_required
def show_lecture(lecture_id):
    course_id = request.form.get("course_id")
    lecture = db.session.query(Lecture).filter(Lecture.id == lecture_id).first()
    return render_template("lecture.html", lecture=lecture, course_id=course_id)


@app.route('/add_test', methods=['POST'])
def add_test():
    course_id = request.form.get("course_id")
    if not db.session.query(Test).filter(Test.title == request.form.get("title")).first():
        course = db.session.query(Course).filter(Course.id == course_id).first()
        test = Test(title=request.form.get("title"), type=request.form.get("type_test"),course=course)
        #test.close_date = null
        db.session.add(test)
        db.session.commit()
        return show_course_control_panel(message="Тест успешно добавлен", course_id=course_id)
    else:
        return show_course_control_panel(message="Тест с таким именем уже существует !!!", course_id=course_id)


@app.route('/add_part', methods=['POST'])
def add_part():
    test_id = request.form.get("test_id")
    course_id = request.form.get("course_id")
    #if not db.session.query(Part).filter(Part.text == request.form.get("title")).first():
    test = db.session.query(Test).filter(Test.id == test_id).first()
    if request.form.get("lecture_id")!=0:
        lecture=db.session.query(Lecture).filter(Lecture.id==request.form.get("lecture_id")).first()
    else:
        lecture=null
    number = db.session.query(Part).filter(Part.test_id==test_id).count()
    number=number+1
    part = Part(text=request.form.get("title"), test=test,lecture=lecture)
    part.number=number
    db.session.add(part)
    db.session.commit()
    return show_course_control_panel(message="Раздел теста успешно добавлен", course_id=course_id)
    #else:
     #   return show_course_control_panel(message="Раздел теста с таким именем уже существует !!!", course_id=course_id)


@app.route('/add_question_in_part', methods=['POST'])
def add_question_in_part():
    part_id = request.form.get("part_id")
    part = db.session.query(Part).filter(Part.id == part_id).first()
    if part:
        count = 0
        for _ in part.question.all():
            count += 1
        question = Question(title=request.form.get(
            "question_title"), part=part, number = count)
        db.session.add(question)
        radio = request.form.get("radio")
        for i in range(1, 11):
            if request.form.get(f"answer{i}") != "":
                if radio == f"radio{i}":
                    db.session.add(Answer(text=request.form.get(
                    f"answer{i}"),question=question,isTrue = 1))
                else:
                    db.session.add(Answer(text=request.form.get(
                    f"answer{i}"),question=question,isTrue = 0))
        db.session.commit()
        return show_part(message="Вопрос успешно добавлен", part_id = part_id)
    else:
        return show_part(message="Ошибка",part_id = part_id)


@app.route("/edit_question_submit", methods=['POST'])
@login_required
def edit_question_submit():
    question_id = request.form.get("question_id")
    question = db.session.query(Question).filter(Question.id == question_id).first()
    part_id = question.part_id
    question.title = request.form.get("question_title")
    db.session.add(question)
    radio = request.form.get("radio")
    answers = db.session.query(Answer).filter(Answer.question_id == question.id).all()
    for answer in answers:
        answer.text = request.form.get(f"answer{answer.id}")
        if radio == f"radio{answer.id}":
            answer.isTrue = 1
        else:
            answer.isTrue = 0
        db.session.add(question)
    db.session.commit()
    return show_part(message="Вопрос успешно добавлен", part_id = part_id)


@app.route("/generate_invite_code", methods=['POST'])
@login_required
def generate_invite_code():
    flash("test")
    choice = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    for i in [i for i in list(string.ascii_uppercase)]:
        choice.append(i)
    code = ""
    for i in range(6):
        code += str(random.choice(choice))
    db.session.add(InviteCode(text=code))
    db.session.commit()
    return show_admin_panel(message=f"Код приглашения  - {code}")


@app.route("/generate_new_group", methods=['POST'])
@login_required
def generate_new_group():
    choice = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    for i in [i for i in list(string.ascii_lowercase + string.ascii_uppercase)]:
        choice.append(i)
    code = ""
    for i in range(6):
        code += str(random.choice(choice))
    question = Group(name=request.form.get("group_name"), code=code)
    db.session.add(question)
    db.session.commit()
    usergroup = UserGroup(group_id = question.id, user_id = current_user.id)
    db.session.add(usergroup)
    db.session.commit()
    return show_groups_panel(message=f"Сгенерированный код - {code}")


@app.route('/')
def index(message=""):
    if current_user.is_authenticated:
        return show_course_panel()
    else:
        return render_template('login.html', message=message)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if flask.request.method == 'POST':
        if db.session.query(InviteCode).filter(InviteCode.text == request.form.get("invite_code")).first():
            user = User(username=request.form.get("username"), surname=request.form.get("surname"),
                        name=request.form.get("name"),
                        email=request.form.get("email"))
            user.set_password(request.form.get("password"))
            db.session.add(user)
            db.session.commit()
            return render_template('login.html', message="Успешная регистрация")
        else:
            return render_template('login.html', message="Неверный код приглашения")
    else:
        return render_template('registration.html')


@app.route('/registration_student', methods=['GET', 'POST'])
def registration_student():
    if flask.request.method == 'POST':
        request_for_registration = request.get_json()
        group = db.session.query(Group).filter(Group.code==request_for_registration['code']).first()
        checkLogin = db.session.query(User).filter(User.username==request_for_registration['username']).first()
        if group is not None:
            if checkLogin is None:
                user = User(username=request_for_registration['username'], surname=request_for_registration['surname'],
                            name=request_for_registration['name'],
                            email=request_for_registration['mail'], role = "student")
                user.set_password(request_for_registration['password'])
                db.session.add(user)
                db.session.commit()
                usergroup = UserGroup(group_id=group.id, user_id=user.id)
                db.session.add(usergroup)
                db.session.commit()
                #стартовое число монет=100, кредитов 0
                studcoins = StudCoins(user_id=user.id, coins=100,kredit=0)
                db.session.add(studcoins)
                db.session.commit()
                return jsonify({'message':'Registration completed'})
            else:
                return jsonify({'message':'This login is already taken'})
        else:
            return jsonify({'message':'invalid group code'})
    else:
        return jsonify({'message':'not post'})


@app.route('/exit')
@login_required
def logout():
    logout_user()
    return render_template('login.html')


@app.route("/admin")
def show_admin_panel(message=""):
    if current_user.is_authenticated:
        if current_user.role == "admin":
            users = db.session.query(User).all()
            return render_template("admin.html", users_list=users, message=message)
        else:
            return index(message="Отказано в доступе")
    else:
        return index(message="Отказано в доступе")


@app.route("/course_panel")
@login_required
def show_course_panel(message=""):
    course_list = db.session.query(Course).all()
    return render_template("course_panel.html", course_list=course_list, message=message)

#уведомления группе
@app.route("/notifications")
@login_required
def show_notifications(message=""):
    groups = db.session.query(UserGroup).filter(UserGroup.user_id==current_user.id).all()
    groups_list=[]
    if groups:
        for i in groups:
            group = db.session.query(Group).filter(Group.id == i.group_id).first()
            groups_list.append(group)
    notifications=[]
    if groups_list:
        for i in groups_list:
            notifications.append(db.session.query(Notification).filter(Notification.group_id==i.id).all())
    
    return render_template("notifications.html", message=message,zip=zip,notifications = notifications,groups_list=groups_list)

@app.route("/send_notification", methods=['POST'])
@login_required
def send_notification(message=""):
    text = request.form.get("notification_text")
    group_id = request.form.get("group_id")
    notification = Notification(text =text, date = datetime.datetime.now(), group_id=group_id)
    db.session.add(notification)
    db.session.commit()
    groups = db.session.query(UserGroup).filter(UserGroup.user_id==current_user.id).all()
    groups_list=[]
    if groups:
        for i in groups:
            group = db.session.query(Group).filter(Group.id == i.group_id).first()
            groups_list.append(group)
    notifications=[]
    if groups_list:
        for i in groups_list:
            notifications.append(db.session.query(Notification).filter(Notification.group_id==i.id).all())
    return render_template("notifications.html", message=message,zip=zip,notifications = notifications,groups_list=groups_list)


@app.route("/get_notifications", methods=['POST'])
def get_notifications():
    if flask.request.method == 'POST':
        request_info = request.data
        request_info = request_info.decode()
        user_id = request_info.strip("[]\"")
        user = db.session.query(User).filter(User.id == user_id).first()
        if user:
            usergroup = db.session.query(UserGroup).filter(UserGroup.user_id == user.id).first()
            group = db.session.query(Group).filter(Group.id == usergroup.group_id).first()
            notifications = db.session.query(Notification).filter(Notification.group_id==group.id).all()
            resultnotifications = []
            for nt in notifications:
                resultnotifications.append(nt.to_dict())
            return jsonify(resultnotifications)
        else:
            return jsonify({'message':'no such user'})
    else:
        return jsonify({'message':'not POST'})
from sqlalchemy import Boolean, desc
#уведомления студенту
@app.route("/studnotifications")
@login_required
def show_studnotifications(message=""):
    groups = db.session.query(UserGroup).filter(UserGroup.user_id==current_user.id).all() 
    groups_list=[]
    if groups:
        for i in groups:
            group = db.session.query(Group).filter(Group.id == i.group_id).first()
            groups_list.append(group)
    
    students_in_groups_list=[]
    students=db.session.query(User).filter(User.role == 'student').all()
    studgroups=db.session.query(UserGroup).filter(UserGroup.user_id!=current_user.id).all()
    if groups_list:
        for i in groups:
            for k in studgroups:
                if i.group_id==k.group_id:
                    for j in students:
                        if j.id==k.user_id:
                            student=db.session.query(User).filter(k.user_id==User.id).first()
                            students_in_groups_list.append((student.id,student.name,student.surname,i.group_id))
    
    studnotifications=[]
    studnotifications.append(db.session.query(StudNotification).filter(StudNotification.student_id!="Выберите студента").order_by(desc(StudNotification.date)).all())
   
    return render_template("studnotifications.html", message=message,zip=zip,studnotifications = studnotifications,groups_list=groups_list,students_in_groups_list=students_in_groups_list)

@app.route("/send_studnotification", methods=['POST'])
@login_required
def send_studnotification(message=""):
    text = request.form.get("notification_text")
    student_id = request.form.get("student_id")
    if student_id!="Выберите студента":
        notification = StudNotification(text =text, date = datetime.datetime.now(), student_id=student_id)
        db.session.add(notification)
        db.session.commit()
    groups = db.session.query(UserGroup).filter(UserGroup.user_id==current_user.id).all() 
    groups_list=[]
    if groups:
        for i in groups:
            group = db.session.query(Group).filter(Group.id == i.group_id).first()
            groups_list.append(group)
    
    students_in_groups_list=[]
    students=db.session.query(User).filter(User.role == 'student').all()
    studgroups=db.session.query(UserGroup).filter(UserGroup.user_id!=current_user.id).all()
    if groups_list:
        for i in groups:
            for k in studgroups:
                if i.group_id==k.group_id:
                    for j in students:
                        if j.id==k.user_id:
                            student=db.session.query(User).filter(k.user_id==User.id).first()
                            students_in_groups_list.append((student.id,student.name,student.surname,i.group_id))
    
    studnotifications=[]
    studnotifications.append(db.session.query(StudNotification).filter(StudNotification.student_id!="Выберите студента").order_by(desc(StudNotification.date)).all())
    return render_template("studnotifications.html", message=message,zip=zip,studnotifications = studnotifications,groups_list=groups_list,students_in_groups_list=students_in_groups_list)


@app.route("/get_studnotifications", methods=['POST'])
def get_studnotifications():
    if flask.request.method == 'POST':
        request_info = request.data
        request_info = request_info.decode()
        user_id = request_info.strip("[]\"")
        user = db.session.query(User).filter(User.id == user_id).first()
        if user:
            notifications = db.session.query(StudNotification).filter(StudNotification.student_id==user.id).all()
            resultnotifications = []
            for nt in notifications:
                resultnotifications.append(nt.to_dict())
            return jsonify(resultnotifications)
        else:
            return jsonify({'message':'no such user'})
    else:
        return jsonify({'message':'not POST'})


@app.route("/groups_panel")
@login_required
def show_groups_panel(message=""):
    groups = db.session.query(UserGroup).filter(UserGroup.user_id==current_user.id).all()
    groups_list=[]
    if groups:
        for i in groups:
            group = db.session.query(Group).filter(Group.id == i.group_id).first()
            groups_list.append(group)
    return render_template("groups_panel.html", groups_list=groups_list, message=message)


@app.route("/edit_question<question_id>", methods=['POST'])
@login_required
def edit_question(question_id):
    course_id = request.form.get("course_id")
    test_id = request.form.get("test_id")
    question = db.session.query(Question).filter(Question.id == question_id).first()
    answers = db.session.query(Answer).filter(Answer.question_id == question.id).all()
    return render_template("edit_question.html", question = question, answers = answers, test_id = test_id, course_id = course_id)

@app.route("/students<group_id>", methods=['POST'])
@login_required
def show_group_list_courses(group_id,message=""):
    group_id=request.form.get("group_id")
    group = db.session.query(Group).filter(Group.id == group_id).first()
    groupname = group.name
    grcourses = db.session.query(GroupCourse).filter(GroupCourse.group_id==group_id).all()
    courses=db.session.query(Course).all()
    studentsId = db.session.query(UserGroup).filter(UserGroup.group_id==group_id).all()
    students=[]
    itogs=[]
    if studentsId:# массив всех студентов группы
        for i in studentsId:
            student = db.session.query(User).filter(User.role=='student').filter(User.id==i.user_id).first()          
            if student is not None:          
                students.append(student)
                itogs.append((i.user_id,itog(i.user_id)))
    return render_template("group_list_courses.html",groupname=groupname,grcourses=grcourses,courses=courses,group_id=group_id,sum_courses=len(grcourses),students=students,itogs=itogs)
def itog(user_id):
    usergroup=db.session.query(UserGroup).filter(UserGroup.user_id == user_id).first()
    group_id=usergroup.group_id
    grcourses = db.session.query(GroupCourse).filter(GroupCourse.group_id==group_id).all()
    courses=db.session.query(Course).all()
    sum_mark=0
    if grcourses:
        for g in grcourses:
            for c in courses:
                if g.course_id==c.id:
                    score=get_student_score(user_id,c.id)
                    max_score=c.max_score
                    if score < 0.61*max_score:
                        sum_mark+=2
                    elif score>= 0.61*max_score and score< 0.72*max_score:
                        sum_mark+=3
                    elif score >= 0.72*max_score and score< 0.85*max_score:
                        sum_mark+=4
                    else:
                        sum_mark+=5
        if round(sum_mark/len(grcourses))<3:
            return "неуд"
        if round(sum_mark/len(grcourses))==3:
            return "удовл"
        if round(sum_mark/len(grcourses))==4:
            return "хор"
        if round(sum_mark/len(grcourses))==5:
            return "отл"
    return "error"


@app.route("/students<group_id>/marks_course<course_id>", methods=['POST'])
@login_required
def show_group_list(group_id,course_id,message=""):
    #course_id=request.form.get("course_id")
    group_id=request.form.get("group_id")
    course=db.session.query(Course).filter(Course.id == course_id).first()
    course_name=course.title
    group = db.session.query(Group).filter(Group.id == group_id).first()
    groupname = group.name
    studentsId = db.session.query(UserGroup).filter(UserGroup.group_id==group_id).all()
    tests = db.session.query(Test).filter(Test.course_id==course_id).all()
    
    parts = db.session.query(Part).all()
    questions=db.session.query(Question).all()
    #сроки сдачи тестов
    deadlines=db.session.query(Deadline).filter(Deadline.group_id==group_id).all()
    tests_info=[]
    for test in tests:
        check=None
        count=0
        for part in parts:
            if (part.test_id==test.id):
                count+=1
        if deadlines:
            for deadline in deadlines:
                if(deadline.test_id==test.id):
                    check=1
                    tests_info.append((test.title,count,test.id,datetime.datetime.date(deadline.date).strftime("%d.%m.%Y")))
        if(check==None):
            tests_info.append((test.title,count,test.id,"нет"))                            
    tests_info=sorted(tests_info,key=lambda tests_info: tests_info[2])
    
    allMarks = db.session.query(Marks).all()
    students = []
    marks = []
    if studentsId:# массив всех студентов группы и все их оценки
        for i in studentsId:
            student = db.session.query(User).filter(User.role=='student').filter(User.id==i.user_id).first()          
            if student is not None:          
                students.append(student)
                for m in allMarks:
                    if(m.user_id == i.user_id):
                        marks.append(m)
    results=[]
    for stud in students:
        for test in tests:            
            for part in parts:
                if(part.test_id==test.id):
                    result1 = UserMarks(stud.id,test.title,test.id,part.text,part.id,"0/0",datetime.datetime.now(),0)
                    results.append(result1)
                        
    """ считаем количество разделов тестов в курсе """
    count_parts=0
    for test in tests:
        for part in parts:
            if(part.test_id==test.id):
                count_parts+=1

    for stud in students:
        for mark in marks:
            if (stud.id==mark.user_id):
                for test in tests:
                    for part in parts:
                        if(mark.part_id==part.id):
                            if(part.test_id==test.id):
                                result = UserMarks(stud.id,test.title,test.id,part.text,part.id,mark.mark,mark.date,1)
                                results.append(result)                
    #уже не бред
    best_marks=[]
    for stud in students:    
        for p in parts:
            user_marks = [x for x in results if stud.id==x.user_id and x.part_id == p.id]
            sorting_params = [('mark', False), ('date', True)]
            sorted_user_marks = multisort(user_marks, sorting_params)
            if sorted_user_marks:
                user_best_mark = sorted_user_marks[0]
                user_best_mark.tries=len(user_marks)-1
                best_marks.append(user_best_mark)
   
    numberQuestions=0 #сколько вопросов по грамматике и по текстам в курсе
    numberQuestionsTexts=0
    numberQuestionsEtiquettes=0
    for test in tests:            
        for part in parts:
            if(test.type==0 and part.test_id==test.id):
                numberQuestion = [x for x in questions if part.id==x.part_id]
                numberQuestions+=len(numberQuestion)
            if(test.type==20 and part.test_id==test.id):
                numberQuestionsText = [x for x in questions if part.id==x.part_id]
                numberQuestionsTexts+=len(numberQuestionsText)
            if(test.type==15 and part.test_id==test.id):
                numberQuestionsEtiquette = [x for x in questions if part.id==x.part_id]
                numberQuestionsEtiquettes+=len(numberQuestionsEtiquette)

    #сколько баллов за грамматику
    countTexts = len([x for x in tests if x.type==20])
    countEtiquette= len([x for x in tests if x.type==15])
    scoreGrammar=course.max_score-countTexts*20-countEtiquette*15

    #сколько баллов у студентов по данной системе выдачи баллов
    newresults=sorted(best_marks,key=lambda UserMarks: (UserMarks.theme_id,UserMarks.part_id))
    averages = []
    for stud in students:
            
            fullscore=get_student_score(stud.id,course_id)
            print(stud.id,"fullscore ",fullscore)
            counter = 0
            for i in range(len(newresults)):
                if(stud.id==newresults[i].user_id and int(str(newresults[i].mark).split("/")[0])!=0):
                    counter+=1
            if(counter == 0):
                average = ResultClass(0,counter,count_parts) #len(parts)
                averages.append(average)
                continue
            average = ResultClass( round (fullscore, 1),counter,count_parts)
            averages.append(average)
    groups=db.session.query(Group).all()
    groups=sorted(groups,key=lambda groups: groups.name)
    return render_template("marks.html", groups=groups,students=students, message=message,results = newresults, group_id=group_id,groupname = groupname, averages=averages,tests_info=tests_info,course_name=course_name,max_score=course.max_score,course_id=course_id)


@app.route("/course_control_panel<course_id>")
@login_required
def show_course_control_panel(course_id, message=""):
    tests = db.session.query(Test).filter(Test.course_id == course_id).all()
    lectures = db.session.query(Lecture).filter(Lecture.course_id == course_id).all()
    return render_template("course_control_panel.html", tests=tests, lectures=lectures, message=message,
                           course_id=course_id)


@app.route("/course<course_id>")
@login_required
def show_course_overview(course_id, message=""):
    tests = db.session.query(Test).filter(Test.course_id == course_id).all()
    lectures = db.session.query(Lecture).filter(Lecture.course_id == course_id).all()
    groups = db.session.query(UserGroup).filter(UserGroup.user_id==current_user.id).all()
    course= db.session.query(Course).filter(Course.id==course_id).first()
    if groups:
        groups_list=[]
        for i in groups:
            group = db.session.query(Group).filter(Group.id == i.group_id).first()
            groups_list.append(group)
        return render_template("course_overview.html", tests=tests, lectures=lectures, course=course,groups = groups_list,message = message)
    else:
        return render_template("course_overview.html", tests=tests, lectures=lectures, course=course,groups = [],message = message)


@app.route("/delete_question<question_id>", methods=['POST'])
@login_required
def delete_question(question_id, message=""):
    question = db.session.query(Question).filter(Question.id == question_id).first()
    part_id=question.part_id
    db.session.delete(question)
    db.session.commit()
    return show_part(part_id)
@app.route("/delete_part<part_id>", methods=['POST'])
@login_required
def delete_part(part_id, message=""):
    part = db.session.query(Part).filter(Part.id == part_id).first()
    test_id=part.test_id
    db.session.delete(part)
    db.session.commit()
    return show_test(test_id)

@app.route("/delete_course<course_id>", methods=['POST'])
@login_required
def delete_course(course_id, message=""):
    course = db.session.query(Course).filter(Course.id == course_id).first()
    groupcourse=db.session.query(GroupCourse).filter(GroupCourse.course_id == course_id).all()
    for gr in groupcourse:
        db.session.delete(gr)
    db.session.delete(course)
    db.session.commit()
    return show_course_panel()

@app.route("/delete_group<group_id>", methods=['POST'])
@login_required
def delete_group(group_id, message=""):
    group = db.session.query(Group).filter(Group.id == group_id).first()
    db.session.delete(group)
    db.session.commit()
    return show_groups_panel()

@app.route('/educate')
def show_educate_page():
    if current_user.is_authenticated:
        return render_template('course_panel.html')
    else:
        return index(message="Отказано в доступе")


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    user = db.session.query(User).filter(User.username == username).first()
    if user and user.check_password(password):
        login_user(user, remember=True)
        user.last_login_time = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        return show_course_panel()
    else:
        return render_template("login.html", message="Ошибка авторизации")


@app.route('/login_student', methods=['GET', 'POST'])
def login_student():
    if flask.request.method == 'POST':
        request_for_login = request.get_json()
        username = request_for_login['username']
        password = request_for_login['password']
        user = db.session.query(User).filter(User.username == username).first()

        """mark = db.session.query(Marks).filter(Marks.user_id == user.id).all()
        for m in mark:
            db.session.delete(m)
        db.session.commit()"""

        if user and user.check_password(password):
            user.last_login_time = datetime.datetime.now()
            db.session.add(user)
            db.session.commit()
            message = "Welcome"
            return jsonify(message=message,user_id=user.id)
        else:
            return jsonify({'message':'no such user'})
    else:
        return jsonify({'message':'not post'})


@app.route('/get_user_info', methods=['GET', 'POST'])
def get_user_info():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        user_id = request_info['user_id']
        user = db.session.query(User).filter(User.id == user_id).first()
        if user:
            usergroup = db.session.query(UserGroup).filter(UserGroup.user_id == user.id).first()
            group = db.session.query(Group).filter(Group.id == usergroup.group_id).first()
            studcoins = db.session.query(StudCoins).filter(StudCoins.user_id == user.id).first()
            groupcourse=db.session.query(GroupCourse).filter(GroupCourse.group_id == usergroup.group_id).all()
            score=-1
            for gr in groupcourse:
                if gr.active==True:
                    score=get_student_score(user_id,gr.course_id)
                    course= db.session.query(Course).filter(Course.id == gr.course_id).first()
            #score=get_student_score(user_id,groupcourse.course_id)
            if(studcoins.coins>120 and studcoins.kredit>0):#набрал монетки, списываем 1 кредит
                i = db.session.query(StudCoins).filter(StudCoins.user_id == user_id).first()
                i.coins -= 75
                i.kredit-=1
                db.session.add(i)
                db.session.commit()
            studcoins_new = db.session.query(StudCoins).filter(StudCoins.user_id == user.id).first()
            return jsonify(message = "success",name = user.name, surname = user.surname, group_name = group.name,studcoins=studcoins_new.coins,score=round(score,1),max_score=course.max_score,kredit=studcoins_new.kredit)
        else:
            return jsonify({'message':'error:('})
    else:
        return jsonify({'message':'not POST'})

@app.route('/get_lectures<course_active>', methods=['GET', 'POST'])
def get_lectures(course_active):
    if flask.request.method == 'POST':
        request_info = request.data
        request_info = request_info.decode()
        user_id = request_info.strip("[]\"")
        user = db.session.query(User).filter(User.id == user_id).first()        
        if user:
            usergroup = db.session.query(UserGroup).filter(UserGroup.user_id == user.id).first()
            group = db.session.query(Group).filter(Group.id == usergroup.group_id).first()
            groupcourse = db.session.query(GroupCourse).filter(GroupCourse.group_id == group.id).all()
            resultlections = []
            for gs in groupcourse:
                if gs.active==int(course_active):
                    course = db.session.query(Course).filter(Course.id == gs.course_id).first()
                    if course:
                        lections = db.session.query(Lecture).filter(Lecture.course_id==course.id).all()
                        for l in lections:
                            resultlections.append(l.to_dict())                
            return jsonify(resultlections)
        else:
            return jsonify({'message':'no such user'})
    else:
        return jsonify({'message':'not POST'})

@app.route('/recieve_result', methods=['GET', 'POST'])
def recieve_result():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        user_id = request_info['user_id']
        part_id = request_info['part_id']
        mark = request_info['result']
        date =datetime.datetime.now()
        mark = Marks(user_id = user_id, part_id = part_id, mark = mark, date = date)
        db.session.add(mark)
        db.session.commit()
        return jsonify({'message':'success'})
    else:
        return jsonify({'message':'not POST'})


@app.route('/get_test<test_id>', methods=['GET', 'POST'])
def get_test_info(test_id):
    #if(exists(app.config['XML_FOLDER']+"/"+test_id+".xml")):
    create_XML_Test(test_id)
    return send_from_directory(app.config['XML_FOLDER'], test_id+".xml", as_attachment=True)


@app.route('/get_tests<user_id>/active<active>', methods=['GET', 'POST'])
def get_tests(user_id,active):
    if flask.request.method == 'POST':
        user = db.session.query(User).filter(User.id == user_id).first()
        if user:
            usergroup = db.session.query(UserGroup).filter(UserGroup.user_id == user.id).first()
            group = db.session.query(Group).filter(Group.id == usergroup.group_id).first()
            groupcourse = db.session.query(GroupCourse).filter(GroupCourse.group_id == group.id).all()
            resulttests= []
            for gs in groupcourse:
                if gs.active==int(active):
                    course = db.session.query(Course).filter(Course.id == gs.course_id).first()
                    if course:
                        tests = db.session.query(Test).filter(Test.course_id==course.id).all()
                        for t in tests:
                            resulttests.append(t.id)
            stringresult = ','.join(str(e) for e in resulttests)
            return stringresult
        else:
            return jsonify({'message':'no such user'})
    else:
        return jsonify({'message':'not POST'})

@app.route('/get_type_test', methods=['GET', 'POST'])
def get_type_test():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        part_id = request_info['part_id']
        user_id=request_info['user_id']
        usergroup=db.session.query(UserGroup).filter(UserGroup.user_id == user_id).first()
        group_id=usergroup.group_id
        part = db.session.query(Part).filter(Part.id == part_id).first()
        test=db.session.query(Test).filter(Test.id == part.test_id).first()
        grcourse = db.session.query(GroupCourse).filter(GroupCourse.group_id==group_id,GroupCourse.course_id==test.course_id).first()
        if grcourse.active==True:
            active="active"
        else:
            active="noactive"

        if test:
            if test.type==0:
                type=0#grammar
            if test.type==20 or test.type==15:
                type=1#по текстам и речевому этикету
            return jsonify(message = "success",type =type,course_id=test.course_id,active=active)
        else:
            return jsonify({'message':'error:('})
    else:
        return jsonify({'message':'not POST'})

@app.route('/edit_coins', methods=['GET', 'POST'])
def edit_coins():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        user_id = request_info['user_id']
        coins = request_info['coins']
        usergroup=db.session.query(UserGroup).filter(UserGroup.user_id == user_id).first()
        group_id=usergroup.group_id
        part_id = request_info['part_id']
        coinsDeadline=0
        if part_id:
                part = db.session.query(Part).filter(Part.id == part_id).first()
                test=db.session.query(Test).filter(Test.id == part.test_id).first()
                grcourse = db.session.query(GroupCourse).filter(GroupCourse.group_id==group_id,GroupCourse.course_id==test.course_id).first()
                if grcourse.active==True:#только при активном курсе добавляем/вычитаем монеты по срокам
                    mark=db.session.query(Marks).filter(Marks.part_id == part_id,Marks.user_id==user_id).all()
                    if len(mark)==1:
                        deadline = db.session.query(Deadline).filter(Deadline.test_id == part.test_id,Deadline.group_id==group_id).first()
                        if deadline:
                            days_in_month = calendar.monthrange(deadline.date.year, deadline.date.month)[1]
                            date1plus1month=deadline.date+datetime.timedelta(days=days_in_month)
                            days_in_month2 = calendar.monthrange(date1plus1month.year, date1plus1month.month)[1]
                            date1plus2month=date1plus1month+datetime.timedelta(days=days_in_month2)
            
                            if(datetime.datetime.now()+datetime.timedelta(days=7)<deadline.date):
                                coinsDeadline=5
                            if date1plus1month<datetime.datetime.now()and date1plus2month>datetime.datetime.now():
                                coinsDeadline=-10
                            if date1plus2month<datetime.datetime.now():
                                coinsDeadline=-20
        i = db.session.query(StudCoins).filter(StudCoins.user_id == user_id).first()
        coins+=coinsDeadline
        i.coins += coins
        db.session.add(i)
        db.session.commit()
        return jsonify(message = "success",coins=coins)
    else:
        return jsonify({'message':'not POST'})
@app.route('/edit_coins_lection', methods=['GET', 'POST'])
def edit_coins_lection():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        user_id = request_info['user_id']
        coins = request_info['coins']
        i = db.session.query(StudCoins).filter(StudCoins.user_id == user_id).first()
        i.coins += coins
        db.session.add(i)        
        db.session.commit()
        return jsonify(message = "success",coins=coins)
    else:
        return jsonify({'message':'not POST'})
@app.route('/get_lection_by_part', methods=['GET', 'POST'])
def get_lection_by_part():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        part_id = request_info['part_id']
        part = db.session.query(Part).filter(Part.id == part_id).first()
        if part:
            lecture= db.session.query(Lecture).filter(Lecture.id == part.lecture_id).first()
            return jsonify(message = "success",lection_id = part.lecture_id,theme=lecture.title,subtheme=lecture.sub_title,filename=lecture.path_to_file)
        else:
            return jsonify({'message':'error:('})
    else:
        return jsonify({'message':'not POST'})

@app.route('/get_kredit', methods=['GET', 'POST'])
def get_kredit():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        user_id = request_info['user_id']
        i = db.session.query(StudCoins).filter(StudCoins.user_id == user_id).first()
        i.coins += 75
        i.kredit+=1
        db.session.add(i)
        db.session.commit()
        return jsonify({'message' : "success"})     
    else:
        return jsonify({'message':'not POST'})
    


def get_student_score(user_id,course_id):
    usergroup=db.session.query(UserGroup).filter(UserGroup.user_id == user_id).first()
    group_id=usergroup.group_id
    course=db.session.query(Course).filter(Course.id == course_id).first()
    deadlines=db.session.query(Deadline).filter(Deadline.group_id==group_id).all()
    tests=db.session.query(Test).filter(Test.course_id == course_id).all()
    parts=db.session.query(Part).all()
    marks=db.session.query(Marks).filter(Marks.user_id == user_id).all()
    questions=db.session.query(Question).all()
    #сроки сдачи тестов
    deadlines=db.session.query(Deadline).filter(Deadline.group_id==group_id).all()
    results=[]
    for test in tests:            
        for part in parts:
            if(part.test_id==test.id):
                result1 = UserMarks(user_id,test.title,test.id,part.text,part.id,"0/0",datetime.datetime.now(),0)
                results.append(result1)
                        
    """ считаем количество разделов тестов в курсе """
    count_parts=0
    for test in tests:
        for part in parts:
            if(part.test_id==test.id):
                count_parts+=1

    for mark in marks:
        for test in tests:
            for part in parts:
                if(mark.part_id==part.id):
                    if(part.test_id==test.id):
                        result = UserMarks(user_id,test.title,test.id,part.text,part.id,mark.mark,mark.date,1)
                        results.append(result)                 
    #уже не бред
    best_marks=[]
    for p in parts:
        user_marks = [x for x in results if x.part_id == p.id]
        sorting_params = [('mark', False), ('date', True)]
        sorted_user_marks = multisort(user_marks, sorting_params)
        if sorted_user_marks:
            user_best_mark = sorted_user_marks[0]
            user_best_mark.tries=len(user_marks)-1
            best_marks.append(user_best_mark)
   
    numberQuestions=0 #сколько вопросов по грамматике и по текстам в курсе
    numberQuestionsTexts=0
    numberQuestionsEtiquettes=0
    for test in tests:            
        for part in parts:
            if(test.type==0 and part.test_id==test.id):
                numberQuestion = [x for x in questions if part.id==x.part_id]
                numberQuestions+=len(numberQuestion)
            if(test.type==20 and part.test_id==test.id):
                numberQuestionsText = [x for x in questions if part.id==x.part_id]
                numberQuestionsTexts+=len(numberQuestionsText)
            if(test.type==15 and part.test_id==test.id):
                numberQuestionsEtiquette = [x for x in questions if part.id==x.part_id]
                numberQuestionsEtiquettes+=len(numberQuestionsEtiquette)
    #сколько баллов за грамматику
    countTexts = len([x for x in tests if x.type==20])
    countEtiquette= len([x for x in tests if x.type==15])
    scoreGrammar=course.max_score-countTexts*20-countEtiquette*15
    #сколько баллов у студентов по данной системе выдачи баллов
    fullscore=0
    scoreGram=0
    scoreText=0
    scoreEtiquette=0
    penalty=0
    for test in tests:       
        for best in best_marks:
            if test.type==0 and test.id==best.theme_id:
                mark=str(best.mark).split("/")[0]
                scoreGram+=int(mark)
            if test.type==20 and test.id==best.theme_id:
                mark=str(best.mark).split("/")[0]
                scoreText+=int(mark)
            if test.type==15 and test.id==best.theme_id:
                mark=str(best.mark).split("/")[0]
                scoreEtiquette+=int(mark)
    checkPenalty20=False
    checkPenalty10=False
    checkPenalty30=False
    for test in tests:        
        if deadlines:
            for d in deadlines:
                if(d.test_id==test.id):
                    for best in best_marks:
                        if d.test_id==best.theme_id:
                            days_in_month = calendar.monthrange(d.date.year, d.date.month)[1]
                            date1plus1month=d.date+datetime.timedelta(days=days_in_month)
                            days_in_month2 = calendar.monthrange(date1plus1month.year, date1plus1month.month)[1]
                            date1plus2month=date1plus1month+datetime.timedelta(days=days_in_month2)
                            date1plus1year=d.date+datetime.timedelta(days=365)
                            if date1plus1year<best.date:
                                checkPenalty30=True
                            if date1plus1month<best.date and date1plus2month>=best.date:
                                checkPenalty10=True
                            if date1plus2month<best.date and best.date<=date1plus1year:
                                checkPenalty20=True
    if checkPenalty30:
        penalty+=30
    else:
        if checkPenalty20:
            penalty+=20
        else:
            if checkPenalty10:
                penalty+=10
    if numberQuestions!=0:
        fullscore+=scoreGram*scoreGrammar/numberQuestions
    if numberQuestionsTexts!=0:
        fullscore+=scoreText*countTexts*20/numberQuestionsTexts
    if numberQuestionsEtiquettes!=0:
        fullscore+=scoreEtiquette*countEtiquette*15/numberQuestionsEtiquettes
    fullscore-=penalty
    
    return fullscore


def sort_key(s):
    
    return int(s.mark.split("/")[0])

    # функция сортировки по нескольким полям
def multisort(sort_list, params):
    for key, param in reversed(params):
        
        sort_list.sort(key=attrgetter(key), reverse=not param)
    for s in sort_list:
        print(s.mark.split("/")[0])
    sort_list = sorted(sort_list, key=sort_key,reverse=True)
    # sort_list=sorted(sort_list,key=lambda sort_list:sort_list['mark'].split("/")[0], reverse=True) 
    return sort_list

@app.route('/get_group_rating', methods=['GET', 'POST'])
def get_group_rating():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        user_id = request_info['user_id']
        usergroup=db.session.query(UserGroup).filter(UserGroup.user_id == user_id).first()
        group_id=usergroup.group_id
        group=db.session.query(Group).filter(Group.id == group_id).first()
        usersgroup=db.session.query(UserGroup).filter(UserGroup.group_id == group_id).all()
        students=[]
        for user in usersgroup:
            students.append(db.session.query(User).filter(User.id == user.user_id).first())
        coins=db.session.query(StudCoins).filter().all()
        rating=[]
        for stud in students:
            for coin in coins:
                if stud.id==coin.user_id:
                    name=str(stud.surname + " "+ stud.name)
                    rating.append({"name":name,"coins":coin.coins})
        rating=sorted(rating,key=lambda x:x['coins'], reverse=True)        
        return jsonify(message = "success",rating=rating,groupname=group.name)     
    else:
        return jsonify({'message':'not POST'})

@app.route('/get_deadlines', methods=['GET', 'POST'])
def get_deadlines():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        user_id = request_info['user_id']
        usergroup=db.session.query(UserGroup).filter(UserGroup.user_id == user_id).first()
        group_id=usergroup.group_id
        groupcourse=db.session.query(GroupCourse).filter(GroupCourse.group_id == group_id,GroupCourse.active==1).first()
        deadlines=db.session.query(Deadline).filter(Deadline.group_id==group_id).all()
        tests=db.session.query(Test).filter(Test.course_id == groupcourse.course_id).all()
        deadline=[]
        for test in tests:
            for mark in best_marks(user_id):
                part=db.session.query(Part).filter(Part.id==mark.get('part_id')).first()
                if int(mark.get('mark').split("/")[1])!=0:
                    percent=int(mark.get('mark').split("/")[0])*100/int(mark.get('mark').split("/")[1])
                if(mark.get('mark')=="0/0" or percent<72):                   
                        if(part.test_id==test.id):
                            for d in deadlines:
                                if d.test_id==test.id:
                                    date=datetime.datetime.date(d.date).strftime("%d.%m.%Y")
                                    deadline.append({"title":test.title,"date": date})
                            break  


            
        # for test in tests:
        #     for d in deadlines:
        #         if d.test_id==test.id:
        #             date=datetime.datetime.date(d.date).strftime("%d.%m.%Y")
        #             deadline.append({"title":test.title,"date": date})           
        print(deadline)
        return jsonify(message = "success",deadline=deadline)     
    else:
        return jsonify({'message':'not POST'})



@app.route('/get_student_mark', methods=['GET', 'POST'])
def get_student_mark():
    if flask.request.method == 'POST':
        request_info = request.get_json()
        user_id = request_info['user_id']
        return jsonify(message = "success",best_marks=best_marks(user_id))
    else:
        return jsonify({'message':'not POST'})


def best_marks(user_id):
    tests=db.session.query(Test).all()
    parts=db.session.query(Part).all()
    marks=db.session.query(Marks).filter(Marks.user_id == user_id).all()   
    results=[]
    for test in tests:            
        for part in parts:
            if(part.test_id==test.id):
                result1 = UserMarks(user_id,test.title,test.id,part.text,part.id,"0/0",datetime.datetime.now(),0)
                results.append(result1)

    for mark in marks:
        for test in tests:
            for part in parts:
                if(mark.part_id==part.id):
                    if(part.test_id==test.id):
                        result = UserMarks(user_id,test.title,test.id,part.text,part.id,mark.mark,mark.date,1)
                        results.append(result)                 
    #уже не бред
    best_marks=[]
    for p in parts:
        user_marks = [x for x in results if x.part_id == p.id]
        sorting_params = [('mark', False), ('date', True)]
        sorted_user_marks = multisort(user_marks, sorting_params)
        if sorted_user_marks[0].part_id==74:

            for s in sorted_user_marks:
                print(s.mark," ",s.date)
        if sorted_user_marks:
            user_best_mark = sorted_user_marks[0]
            user_best_mark.tries=len(user_marks)-1
            best_marks.append({"part_id":user_best_mark.part_id,"mark":user_best_mark.mark})
    return best_marks