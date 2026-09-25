from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "edu-ahmed-2027"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///edu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

VODAFONE = "01090933634"
TEACHER = "أحمد إبراهيم"
SUBJECT = "الفلسفة"
PRICE = 70
ADMIN_USER = "Mh"
ADMIN_PASS = "@2027"


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20), unique=True)
    grade = db.Column(db.String(20))  # "first" أو "second"
    code = db.Column(db.String(50), unique=True)
    activated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'phone': self.phone,
            'grade': self.grade, 'code': self.code or '',
            'activated': self.activated,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    grade = db.Column(db.String(20))
    screenshot = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending / approved / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'student_name': self.student_name,
            'phone': self.phone, 'grade': self.grade,
            'screenshot': self.screenshot, 'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    url = db.Column(db.String(300))
    grade = db.Column(db.String(20))
    lesson = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'url': self.url,
            'grade': self.grade, 'lesson': self.lesson or '',
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }


class Homework(db.Model):
    __tablename__ = 'homework'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    grade = db.Column(db.String(20))
    due_date = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'description': self.description or '',
            'grade': self.grade, 'due_date': self.due_date or '',
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }


class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    grade = db.Column(db.String(20))
    questions = db.Column(db.Text)  # JSON string
    duration = db.Column(db.Integer)  # minutes
    total_marks = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'grade': self.grade,
            'duration': self.duration, 'total_marks': self.total_marks,
            'active': self.active,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }


class ExamResult(db.Model):
    __tablename__ = 'exam_results'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer)
    student_phone = db.Column(db.String(20))
    student_name = db.Column(db.String(100))
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'exam_id': self.exam_id,
            'student_phone': self.student_phone, 'student_name': self.student_name,
            'score': self.score, 'total': self.total,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


# ===== صفحات =====
@app.route('/')
def home():
    return render_template('index.html', teacher=TEACHER, subject=SUBJECT, price=PRICE, vodafone=VODAFONE)


@app.route('/register')
def register_page():
    return render_template('register.html', teacher=TEACHER, subject=SUBJECT, price=PRICE, vodafone=VODAFONE)


@app.route('/login')
def login_page():
    return render_template('login.html', teacher=TEACHER, subject=SUBJECT)


@app.route('/student')
def student_page():
    if 'student_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('student.html', teacher=TEACHER, subject=SUBJECT)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password', '')
        if u == ADMIN_USER and p == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        return render_template('admin_login.html', error='بيانات غلط')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


@app.route('/admin')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin.html', teacher=TEACHER, subject=SUBJECT)


# ===== APIs =====
@app.route('/api/enroll', methods=['POST'])
def api_enroll():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    grade = request.form.get('grade', '').strip()
    if not name or not phone or not grade:
        return jsonify({'ok': False, 'msg': 'اكمل البيانات'}), 400
    if Enrollment.query.filter_by(phone=phone, status='pending').first():
        return jsonify({'ok': False, 'msg': 'فيه طلب معلق بالفعل'}), 400
    if Student.query.filter_by(phone=phone, activated=True).first():
        return jsonify({'ok': False, 'msg': 'الرقم ده مسجل بالفعل'}), 400

    fn = None
    if 'screenshot' in request.files:
        f = request.files['screenshot']
        if f and f.filename:
            ext = f.filename.rsplit('.', 1)[-1].lower()
            if ext in ('png', 'jpg', 'jpeg', 'gif', 'webp'):
                fn = secure_filename(phone + "_" + str(int(datetime.now().timestamp())) + "." + ext)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))

    db.session.add(Enrollment(student_name=name, phone=phone, grade=grade, screenshot=fn))
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'تم إرسال الطلب'})


@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.get_json() or {}
    phone = d.get('phone', '').strip()
    code = d.get('code', '').strip()
    if not phone or not code:
        return jsonify({'ok': False, 'msg': 'اكمل البيانات'}), 400
    s = Student.query.filter_by(phone=phone).first()
    if not s:
        return jsonify({'ok': False, 'msg': 'الرقم غير مسجل'}), 404
    if not s.activated:
        return jsonify({'ok': False, 'msg': 'لم يتم تفعيل حسابك بعد'}), 403
    if s.code != code:
        return jsonify({'ok': False, 'msg': 'كود التفعيل غلط'}), 403
    session['student_id'] = s.id
    session['student_phone'] = s.phone
    return jsonify({'ok': True, 'student': s.to_dict()})


@app.route('/api/logout')
def api_logout():
    session.pop('student_id', None)
    session.pop('student_phone', None)
    return jsonify({'ok': True})


@app.route('/api/me')
def api_me():
    if 'student_id' not in session:
        return jsonify({'ok': False}), 401
    s = Student.query.get(session['student_id'])
    if not s:
        return jsonify({'ok': False}), 404
    return jsonify({'ok': True, 'student': s.to_dict()})


@app.route('/api/videos')
def api_videos():
    if 'student_id' not in session:
        return jsonify({'ok': False}), 401
    s = Student.query.get(session['student_id'])
    if not s:
        return jsonify({'ok': False}), 404
    vids = Video.query.filter_by(grade=s.grade).order_by(Video.id.desc()).all()
    return jsonify([v.to_dict() for v in vids])


@app.route('/api/homework')
def api_homework():
    if 'student_id' not in session:
        return jsonify({'ok': False}), 401
    s = Student.query.get(session['student_id'])
    if not s:
        return jsonify({'ok': False}), 404
    hw = Homework.query.filter_by(grade=s.grade).order_by(Homework.id.desc()).all()
    return jsonify([h.to_dict() for h in hw])


@app.route('/api/exams')
def api_exams():
    if 'student_id' not in session:
        return jsonify({'ok': False}), 401
    s = Student.query.get(session['student_id'])
    if not s:
        return jsonify({'ok': False}), 404
    ex = Exam.query.filter_by(grade=s.grade, active=True).order_by(Exam.id.desc()).all()
    results = ExamResult.query.filter_by(student_phone=s.phone).all()
    done_ids = [r.exam_id for r in results]
    return jsonify({
        'exams': [e.to_dict() for e in ex],
        'done': done_ids
    })


@app.route('/api/exam/<int:id>')
def api_exam_get(id):
    if 'student_id' not in session:
        return jsonify({'ok': False}), 401
    e = Exam.query.get(id)
    if not e:
        return jsonify({'ok': False, 'msg': 'الامتحان مش موجود'}), 404
    import json
    return jsonify({
        'ok': True,
        'exam': {
            'id': e.id, 'title': e.title, 'duration': e.duration,
            'total_marks': e.total_marks,
            'questions': json.loads(e.questions or '[]')
        }
    })


@app.route('/api/exam/<int:id>/submit', methods=['POST'])
def api_exam_submit(id):
    if 'student_id' not in session:
        return jsonify({'ok': False}), 401
    e = Exam.query.get(id)
    if not e:
        return jsonify({'ok': False}), 404
    s = Student.query.get(session['student_id'])
    if not s:
        return jsonify({'ok': False}), 404
    if ExamResult.query.filter_by(exam_id=id, student_phone=s.phone).first():
        return jsonify({'ok': False, 'msg': 'امتحنت قبل كده'}), 400

    import json
    data = request.get_json() or {}
    answers = data.get('answers', [])
    questions = json.loads(e.questions or '[]')
    score = 0
    for i, q in enumerate(questions):
        if i < len(answers) and answers[i] == q.get('correct'):
            score += 1
    db.session.add(ExamResult(exam_id=id, student_phone=s.phone,
                              student_name=s.name, score=score,
                              total=len(questions)))
    db.session.commit()
    return jsonify({'ok': True, 'score': score, 'total': len(questions)})


@app.route('/api/my-results')
def api_my_results():
    if 'student_id' not in session:
        return jsonify({'ok': False}), 401
    s = Student.query.get(session['student_id'])
    if not s:
        return jsonify({'ok': False}), 404
    rs = ExamResult.query.filter_by(student_phone=s.phone).order_by(ExamResult.id.desc()).all()
    return jsonify([r.to_dict() for r in rs])


# ===== Admin APIs =====
@app.route('/api/admin/enrollments')
def adm_enrollments():
    if not session.get('admin'): return jsonify({'ok': False}), 401
    return jsonify([e.to_dict() for e in Enrollment.query.order_by(Enrollment.id.desc()).all()])


@app.route('/api/admin/enrollment/<int:id>/approve', methods=['POST'])
def adm_approve_enrollment(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    d = request.get_json() or {}
    code = d.get('code', '').strip()
    if not code:
        return jsonify({'ok': False, 'msg': 'اكتب كود التفعيل'}), 400
    e = Enrollment.query.get(id)
    if not e:
        return jsonify({'ok': False}), 404
    if Student.query.filter_by(code=code).first():
        return jsonify({'ok': False, 'msg': 'الكود مستخدم'}), 400
    s = Student.query.filter_by(phone=e.phone).first()
    if s:
        s.code = code
        s.activated = True
        s.name = e.student_name
        s.grade = e.grade
    else:
        db.session.add(Student(name=e.student_name, phone=e.phone,
                                grade=e.grade, code=code, activated=True))
    e.status = 'approved'
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/enrollment/<int:id>/reject', methods=['POST'])
def adm_reject_enrollment(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    e = Enrollment.query.get(id)
    if e:
        e.status = 'rejected'
        db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/students')
def adm_students():
    if not session.get('admin'): return jsonify({'ok': False}), 401
    return jsonify([s.to_dict() for s in Student.query.order_by(Student.id.desc()).all()])


@app.route('/api/admin/student/<int:id>', methods=['DELETE'])
def adm_del_student(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    s = Student.query.get(id)
    if s:
        db.session.delete(s)
        db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/videos', methods=['GET', 'POST'])
def adm_videos():
    if not session.get('admin'): return jsonify({'ok': False}), 401
    if request.method == 'POST':
        d = request.get_json() or {}
        db.session.add(Video(title=d.get('title'), url=d.get('url'),
                              grade=d.get('grade'), lesson=d.get('lesson', '')))
        db.session.commit()
        return jsonify({'ok': True})
    return jsonify([v.to_dict() for v in Video.query.order_by(Video.id.desc()).all()])


@app.route('/api/admin/video/<int:id>', methods=['DELETE'])
def adm_del_video(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    v = Video.query.get(id)
    if v:
        db.session.delete(v)
        db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/homework', methods=['GET', 'POST'])
def adm_homework():
    if not session.get('admin'): return jsonify({'ok': False}), 401
    if request.method == 'POST':
        d = request.get_json() or {}
        db.session.add(Homework(title=d.get('title'), description=d.get('description'),
                                 grade=d.get('grade'), due_date=d.get('due_date', '')))
        db.session.commit()
        return jsonify({'ok': True})
    return jsonify([h.to_dict() for h in Homework.query.order_by(Homework.id.desc()).all()])


@app.route('/api/admin/homework/<int:id>', methods=['DELETE'])
def adm_del_homework(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    h = Homework.query.get(id)
    if h:
        db.session.delete(h)
        db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/exams', methods=['GET', 'POST'])
def adm_exams():
    if not session.get('admin'): return jsonify({'ok': False}), 401
    if request.method == 'POST':
        import json
        d = request.get_json() or {}
        db.session.add(Exam(
            title=d.get('title'), grade=d.get('grade'),
            questions=json.dumps(d.get('questions', [])),
            duration=int(d.get('duration', 30)),
            total_marks=len(d.get('questions', [])),
            active=d.get('active', False)
        ))
        db.session.commit()
        return jsonify({'ok': True})
    return jsonify([e.to_dict() for e in Exam.query.order_by(Exam.id.desc()).all()])


@app.route('/api/admin/exam/<int:id>/toggle', methods=['POST'])
def adm_toggle_exam(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    e = Exam.query.get(id)
    if e:
        e.active = not e.active
        db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/exam/<int:id>', methods=['DELETE'])
def adm_del_exam(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    e = Exam.query.get(id)
    if e:
        db.session.delete(e)
        db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/results')
def adm_results():
    if not session.get('admin'): return jsonify({'ok': False}), 401
    return jsonify([r.to_dict() for r in ExamResult.query.order_by(ExamResult.id.desc()).all()])


@app.route('/uploads/<filename>')
def uploaded(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.before_request
def init_db():
    if not getattr(app, '_init', False):
        db.create_all()
        app._init = True


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
