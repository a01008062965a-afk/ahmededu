from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os, json, random, string

app = Flask(__name__)
app.secret_key = "ahmed-edu-2027-x"
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
    parent_phone = db.Column(db.String(20))
    grade = db.Column(db.String(20))
    code = db.Column(db.String(50), unique=True)
    payment_phone = db.Column(db.String(20))
    screenshot = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending / approved / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'phone': self.phone,
            'parent_phone': self.parent_phone or '',
            'grade': self.grade,
            'grade_name': 'أول ثانوي' if self.grade == 'first' else 'تانية ثانوي',
            'code': self.code or '',
            'payment_phone': self.payment_phone or '',
            'screenshot': self.screenshot,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M') if self.approved_at else ''
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
        return {'id': self.id, 'title': self.title, 'url': self.url,
                'grade': self.grade, 'lesson': self.lesson or '',
                'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''}


class Homework(db.Model):
    __tablename__ = 'homework'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    grade = db.Column(db.String(20))
    due_date = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'description': self.description or '',
                'grade': self.grade, 'due_date': self.due_date or '',
                'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''}


class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    grade = db.Column(db.String(20))
    questions = db.Column(db.Text)
    duration = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'grade': self.grade,
                'duration': self.duration, 'total': len(json.loads(self.questions or '[]')),
                'active': self.active,
                'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''}


class ExamResult(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer)
    student_id = db.Column(db.Integer)
    student_name = db.Column(db.String(100))
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {'id': self.id, 'exam_id': self.exam_id, 'student_id': self.student_id,
                'student_name': self.student_name, 'score': self.score, 'total': self.total,
                'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''}


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


# ========== APIs ==========
@app.route('/api/register', methods=['POST'])
def api_register():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    parent_phone = request.form.get('parent_phone', '').strip()
    grade = request.form.get('grade', '').strip()
    payment_phone = request.form.get('payment_phone', '').strip()

    if not all([name, phone, parent_phone, grade, payment_phone]):
        return jsonify({'ok': False, 'msg': 'اكمل كل البيانات'}), 400
    if Student.query.filter_by(phone=phone).first():
        return jsonify({'ok': False, 'msg': 'الرقم ده مسجل بالفعل'}), 400

    fn = None
    if 'screenshot' in request.files:
        f = request.files['screenshot']
        if f and f.filename:
            ext = f.filename.rsplit('.', 1)[-1].lower()
            if ext in ('png', 'jpg', 'jpeg', 'gif', 'webp'):
                fn = secure_filename(phone + "_" + str(int(datetime.now().timestamp())) + "." + ext)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))

    db.session.add(Student(name=name, phone=phone, parent_phone=parent_phone,
                            grade=grade, payment_phone=payment_phone,
                            screenshot=fn, status='pending'))
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'تم استلام طلبك'})


@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.get_json() or {}
    phone = d.get('phone', '').strip()
    code = d.get('code', '').strip().upper()
    if not phone or not code:
        return jsonify({'ok': False, 'msg': 'اكمل البيانات'}), 400
    s = Student.query.filter_by(phone=phone).first()
    if not s:
        return jsonify({'ok': False, 'msg': 'الرقم غير مسجل'}), 404
    if s.status == 'pending':
        return jsonify({'ok': False, 'msg': 'طلبك في انتظار الموافقة'}), 403
    if s.status == 'rejected':
        return jsonify({'ok': False, 'msg': 'تم رفض طلبك — كلم الأستاذ'}), 403
    if not s.code or s.code != code:
        return jsonify({'ok': False, 'msg': 'الكود غلط'}), 403
    session['student_id'] = s.id
    return jsonify({'ok': True})


@app.route('/api/logout')
def api_logout():
    session.pop('student_id', None)
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
    if 'student_id' not in session: return jsonify({'ok': False}), 401
    s = Student.query.get(session['student_id'])
    if not s: return jsonify({'ok': False}), 404
    return jsonify([v.to_dict() for v in Video.query.filter_by(grade=s.grade).order_by(Video.id.desc()).all()])


@app.route('/api/homework')
def api_homework():
    if 'student_id' not in session: return jsonify({'ok': False}), 401
    s = Student.query.get(session['student_id'])
    if not s: return jsonify({'ok': False}), 404
    return jsonify([h.to_dict() for h in Homework.query.filter_by(grade=s.grade).order_by(Homework.id.desc()).all()])


@app.route('/api/exams')
def api_exams():
    if 'student_id' not in session: return jsonify({'ok': False}), 401
    s = Student.query.get(session['student_id'])
    if not s: return jsonify({'ok': False}), 404
    ex = Exam.query.filter_by(grade=s.grade, active=True).order_by(Exam.id.desc()).all()
    done = [r.exam_id for r in ExamResult.query.filter_by(student_id=s.id).all()]
    return jsonify({'exams': [x.to_dict() for x in ex], 'done': done})


@app.route('/api/exam/<int:id>')
def api_exam_get(id):
    if 'student_id' not in session: return jsonify({'ok': False}), 401
    e = Exam.query.get(id)
    if not e: return jsonify({'ok': False}), 404
    s = Student.query.get(session['student_id'])
    if s.grade != e.grade: return jsonify({'ok': False}), 403
    if ExamResult.query.filter_by(exam_id=id, student_id=s.id).first():
        return jsonify({'ok': False, 'msg': 'امتحنت قبل كده'}), 400
    return jsonify({'ok': True, 'exam': {'id': e.id, 'title': e.title,
                      'duration': e.duration, 'questions': json.loads(e.questions or '[]')}})


@app.route('/api/exam/<int:id>/submit', methods=['POST'])
def api_exam_submit(id):
    if 'student_id' not in session: return jsonify({'ok': False}), 401
    e = Exam.query.get(id)
    if not e: return jsonify({'ok': False}), 404
    s = Student.query.get(session['student_id'])
    if ExamResult.query.filter_by(exam_id=id, student_id=s.id).first():
        return jsonify({'ok': False, 'msg': 'امتحنت قبل كده'}), 400
    d = request.get_json() or {}
    answers = d.get('answers', [])
    questions = json.loads(e.questions or '[]')
    score = sum(1 for i, q in enumerate(questions) if i < len(answers) and answers[i] == q.get('correct'))
    db.session.add(ExamResult(exam_id=id, student_id=s.id, student_name=s.name, score=score, total=len(questions)))
    db.session.commit()
    return jsonify({'ok': True, 'score': score, 'total': len(questions)})


@app.route('/api/my-results')
def api_my_results():
    if 'student_id' not in session: return jsonify({'ok': False}), 401
    return jsonify([r.to_dict() for r in ExamResult.query.filter_by(student_id=session['student_id']).order_by(ExamResult.id.desc()).all()])


# ========== Admin APIs ==========
@app.route('/api/admin/stats')
def adm_stats():
    if not session.get('admin'): return jsonify({'ok': False}), 401
    return jsonify({
        'students': Student.query.count(),
        'pending': Student.query.filter_by(status='pending').count(),
        'approved': Student.query.filter_by(status='approved').count(),
        'first': Student.query.filter_by(grade='first', status='approved').count(),
        'second': Student.query.filter_by(grade='second', status='approved').count(),
        'videos': Video.query.count(),
        'exams': Exam.query.count(),
        'results': ExamResult.query.count()
    })


@app.route('/api/admin/students')
def adm_students():
    if not session.get('admin'): return jsonify({'ok': False}), 401
    return jsonify([s.to_dict() for s in Student.query.order_by(Student.id.desc()).all()])


@app.route('/api/admin/approve/<int:id>', methods=['POST'])
def adm_approve(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    s = Student.query.get(id)
    if not s: return jsonify({'ok': False}), 404
    if s.status == 'approved': return jsonify({'ok': False, 'msg': 'معتمد بالفعل'}), 400
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    while Student.query.filter_by(code=code).first():
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    s.code = code
    s.status = 'approved'
    s.approved_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True, 'code': code})


@app.route('/api/admin/reject/<int:id>', methods=['POST'])
def adm_reject(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    s = Student.query.get(id)
    if s:
        s.status = 'rejected'
        db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/del_student/<int:id>', methods=['DELETE'])
def adm_del_student(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    s = Student.query.get(id)
    if s: db.session.delete(s); db.session.commit()
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
    if v: db.session.delete(v); db.session.commit()
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
    if h: db.session.delete(h); db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/exams', methods=['GET', 'POST'])
def adm_exams():
    if not session.get('admin'): return jsonify({'ok': False}), 401
    if request.method == 'POST':
        d = request.get_json() or {}
        db.session.add(Exam(title=d.get('title'), grade=d.get('grade'),
                             questions=json.dumps(d.get('questions', [])),
                             duration=int(d.get('duration', 30)), active=True))
        db.session.commit()
        return jsonify({'ok': True})
    return jsonify([e.to_dict() for e in Exam.query.order_by(Exam.id.desc()).all()])


@app.route('/api/admin/exam/<int:id>/toggle', methods=['POST'])
def adm_toggle_exam(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    e = Exam.query.get(id)
    if e: e.active = not e.active; db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/exam/<int:id>', methods=['DELETE'])
def adm_del_exam(id):
    if not session.get('admin'): return jsonify({'ok': False}), 401
    e = Exam.query.get(id)
    if e: db.session.delete(e); db.session.commit()
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
