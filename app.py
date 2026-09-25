from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os, random, string, json

app = Flask(__name__)
app.secret_key = "ahmed-edu-2027"
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
    code = db.Column(db.String(50))
    payment_phone = db.Column(db.String(20))
    screenshot = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    url = db.Column(db.String(300))
    grade = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Homework(db.Model):
    __tablename__ = 'homework'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    grade = db.Column(db.String(20))
    due_date = db.Column(db.String(50))
    hw_type = db.Column(db.String(20), default='any')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer)
    student_id = db.Column(db.Integer)
    student_name = db.Column(db.String(100))
    text_answer = db.Column(db.Text)
    image_file = db.Column(db.String(255))
    draw_file = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    grade = db.Column(db.String(20))
    questions = db.Column(db.Text)
    duration = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExamResult(db.Model):
    __tablename__ = 'exam_results'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer)
    student_id = db.Column(db.Integer)
    student_name = db.Column(db.String(100))
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============ العميل ============
@app.route('/')
def home():
    return render_template('index.html', teacher=TEACHER, subject=SUBJECT, price=PRICE)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        parent = request.form.get('parent_phone', '').strip()
        grade = request.form.get('grade', '').strip()
        pay_phone = request.form.get('payment_phone', '').strip()

        if not all([name, phone, parent, grade, pay_phone]):
            return render_template('register.html', teacher=TEACHER, subject=SUBJECT, price=PRICE,
                                   vodafone=VODAFONE, error='اكمل كل البيانات')

        if Student.query.filter_by(phone=phone).first():
            return render_template('register.html', teacher=TEACHER, subject=SUBJECT, price=PRICE,
                                   vodafone=VODAFONE, error='الرقم ده مسجل بالفعل')

        fn = None
        if 'screenshot' in request.files:
            f = request.files['screenshot']
            if f and f.filename:
                ext = f.filename.rsplit('.', 1)[-1].lower()
                if ext in ('png', 'jpg', 'jpeg', 'gif', 'webp'):
                    fn = secure_filename(phone + "_" + str(int(datetime.now().timestamp())) + "." + ext)
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))

        db.session.add(Student(name=name, phone=phone, parent_phone=parent,
                                grade=grade, payment_phone=pay_phone, screenshot=fn))
        db.session.commit()
        return redirect(url_for('register_success'))

    return render_template('register.html', teacher=TEACHER, subject=SUBJECT, price=PRICE, vodafone=VODAFONE)


@app.route('/register/success')
def register_success():
    return render_template('success.html', teacher=TEACHER, subject=SUBJECT)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        code = request.form.get('code', '').strip().upper()
        if not phone or not code:
            return render_template('login.html', teacher=TEACHER, subject=SUBJECT, error='اكمل البيانات')
        s = Student.query.filter_by(phone=phone).first()
        if not s:
            return render_template('login.html', teacher=TEACHER, subject=SUBJECT, error='الرقم غير مسجل')
        if s.status == 'pending':
            return render_template('login.html', teacher=TEACHER, subject=SUBJECT, error='طلبك في انتظار الموافقة')
        if s.status == 'rejected':
            return render_template('login.html', teacher=TEACHER, subject=SUBJECT, error='تم رفض طلبك')
        if s.code != code:
            return render_template('login.html', teacher=TEACHER, subject=SUBJECT, error='الكود غلط')
        session['student_id'] = s.id
        return redirect(url_for('student_page'))
    return render_template('login.html', teacher=TEACHER, subject=SUBJECT)


@app.route('/student')
def student_page():
    if 'student_id' not in session:
        return redirect(url_for('login_page'))
    s = Student.query.get(session['student_id'])
    if not s:
        return redirect(url_for('login_page'))
    videos = Video.query.filter_by(grade=s.grade).order_by(Video.id.desc()).all()
    hws = Homework.query.filter_by(grade=s.grade).order_by(Homework.id.desc()).all()
    my_results = ExamResult.query.filter_by(student_id=s.id).all()
    submitted_hw_ids = [sub.homework_id for sub in Submission.query.filter_by(student_id=s.id).all()]
    exams = Exam.query.filter_by(grade=s.grade, active=True).order_by(Exam.id.desc()).all()
    taken_exam_ids = [r.exam_id for r in my_results]
    return render_template('student.html', student=s, videos=videos, homeworks=hws,
                           subject=SUBJECT, submitted_hw_ids=submitted_hw_ids,
                           exams=exams, taken_exam_ids=taken_exam_ids, my_results=my_results)


@app.route('/student/logout')
def student_logout():
    session.pop('student_id', None)
    return redirect(url_for('home'))


# ============ APIs الطالب ============
@app.route('/api/submit_homework/<int:hw_id>', methods=['POST'])
def api_submit_hw(hw_id):
    if 'student_id' not in session:
        return jsonify({'ok': False, 'msg': 'سجل دخول الأول'}), 401
    s = Student.query.get(session['student_id'])
    if not s:
        return jsonify({'ok': False}), 403
    if Submission.query.filter_by(homework_id=hw_id, student_id=s.id).first():
        return jsonify({'ok': False, 'msg': 'سلمت الواجب ده قبل كده'}), 400
    text = request.form.get('text_answer', '').strip()
    img_file = None
    draw_file = None
    if 'image' in request.files:
        f = request.files['image']
        if f and f.filename:
            ext = f.filename.rsplit('.', 1)[-1].lower()
            if ext in ('png', 'jpg', 'jpeg', 'gif', 'webp'):
                img_file = secure_filename("hw" + str(hw_id) + "_s" + str(s.id) + "_img_" + str(int(datetime.now().timestamp())) + "." + ext)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], img_file))
    if 'drawing' in request.files:
        f = request.files['drawing']
        if f and f.filename:
            draw_file = secure_filename("hw" + str(hw_id) + "_s" + str(s.id) + "_draw_" + str(int(datetime.now().timestamp())) + ".png")
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], draw_file))
    if not text and not img_file and not draw_file:
        return jsonify({'ok': False, 'msg': 'اكتب أو ارفع صورة أو ارسم'}), 400
    db.session.add(Submission(homework_id=hw_id, student_id=s.id, student_name=s.name,
                              text_answer=text, image_file=img_file, draw_file=draw_file))
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'تم تسليم الواجب'})


@app.route('/api/exam/<int:exam_id>/start', methods=['POST'])
def api_exam_start(exam_id):
    if 'student_id' not in session:
        return jsonify({'ok': False}), 401
    s = Student.query.get(session['student_id'])
    e = Exam.query.get(exam_id)
    if not e or not s:
        return jsonify({'ok': False}), 404
    if ExamResult.query.filter_by(exam_id=exam_id, student_id=s.id).first():
        return jsonify({'ok': False, 'msg': 'امتحنت قبل كده'}), 400
    questions = json.loads(e.questions or '[]')
    return jsonify({
        'ok': True,
        'exam': {
            'id': e.id, 'title': e.title, 'duration': e.duration,
            'questions': [{'q': q['q'], 'opts': q.get('opts', []), 'type': q.get('type', 'mcq')} for q in questions]
        }
    })


@app.route('/api/exam/<int:exam_id>/submit', methods=['POST'])
def api_exam_submit(exam_id):
    if 'student_id' not in session:
        return jsonify({'ok': False}), 401
    s = Student.query.get(session['student_id'])
    e = Exam.query.get(exam_id)
    if not e or not s:
        return jsonify({'ok': False}), 404
    if ExamResult.query.filter_by(exam_id=exam_id, student_id=s.id).first():
        return jsonify({'ok': False, 'msg': 'امتحنت قبل كده'}), 400
    answers = request.json.get('answers', [])
    questions = json.loads(e.questions or '[]')
    score = 0
    for i, q in enumerate(questions):
        if q.get('type', 'mcq') == 'mcq':
            if i < len(answers) and answers[i] == q.get('correct'):
                score += 1
    total = len(questions)
    db.session.add(ExamResult(exam_id=exam_id, student_id=s.id, student_name=s.name, score=score, total=total))
    db.session.commit()
    return jsonify({'ok': True, 'score': score, 'total': total})


# ============ الأدمن ============
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password', '').strip()
        if u == ADMIN_USER and p == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin_home'))
        return render_template('admin_login.html', error='بيانات غلط')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


def require_admin():
    return session.get('admin')


@app.route('/admin')
def admin_home():
    if not require_admin(): return redirect(url_for('admin_login'))
    stats = {
        'pending': Student.query.filter_by(status='pending').count(),
        'approved': Student.query.filter_by(status='approved').count(),
        'first': Student.query.filter_by(grade='first', status='approved').count(),
        'second': Student.query.filter_by(grade='second', status='approved').count(),
        'videos': Video.query.count(),
        'homework': Homework.query.count(),
        'exams': Exam.query.count(),
        'submissions': Submission.query.count()
    }
    return render_template('admin_home.html', stats=stats, teacher=TEACHER, subject=SUBJECT)


@app.route('/admin/pending')
def admin_pending():
    if not require_admin(): return redirect(url_for('admin_login'))
    students = Student.query.filter_by(status='pending').order_by(Student.id.desc()).all()
    return render_template('admin_pending.html', students=students, teacher=TEACHER, subject=SUBJECT)


@app.route('/admin/students')
def admin_students():
    if not require_admin(): return redirect(url_for('admin_login'))
    students = Student.query.order_by(Student.id.desc()).all()
    return render_template('admin_students.html', students=students, teacher=TEACHER, subject=SUBJECT)


@app.route('/admin/approve/<int:id>')
def admin_approve(id):
    if not require_admin(): return redirect(url_for('admin_login'))
    s = Student.query.get(id)
    if s and s.status != 'approved':
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        while Student.query.filter_by(code=code).first():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        s.code = code
        s.status = 'approved'
        db.session.commit()
        return render_template('admin_approved.html', student=s, code=code, teacher=TEACHER, subject=SUBJECT)
    return redirect(url_for('admin_pending'))


@app.route('/admin/reject/<int:id>')
def admin_reject(id):
    if not require_admin(): return redirect(url_for('admin_login'))
    s = Student.query.get(id)
    if s:
        s.status = 'rejected'
        db.session.commit()
    return redirect(url_for('admin_pending'))


@app.route('/admin/del/<int:id>')
def admin_del(id):
    if not require_admin(): return redirect(url_for('admin_login'))
    s = Student.query.get(id)
    if s:
        db.session.delete(s)
        db.session.commit()
    return redirect(request.referrer or url_for('admin_students'))


@app.route('/admin/videos', methods=['GET', 'POST'])
def admin_videos():
    if not require_admin(): return redirect(url_for('admin_login'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        url = request.form.get('url', '').strip()
        grade = request.form.get('grade', 'first')
        if title and url:
            db.session.add(Video(title=title, url=url, grade=grade))
            db.session.commit()
        return redirect(url_for('admin_videos'))
    videos = Video.query.order_by(Video.id.desc()).all()
    return render_template('admin_videos.html', videos=videos, teacher=TEACHER, subject=SUBJECT)


@app.route('/admin/video/del/<int:id>')
def admin_del_video(id):
    if not require_admin(): return redirect(url_for('admin_login'))
    v = Video.query.get(id)
    if v:
        db.session.delete(v)
        db.session.commit()
    return redirect(url_for('admin_videos'))


@app.route('/admin/homework', methods=['GET', 'POST'])
def admin_homework():
    if not require_admin(): return redirect(url_for('admin_login'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        desc = request.form.get('description', '').strip()
        grade = request.form.get('grade', 'first')
        due = request.form.get('due_date', '').strip()
        hw_type = request.form.get('hw_type', 'any')
        if title:
            db.session.add(Homework(title=title, description=desc, grade=grade, due_date=due, hw_type=hw_type))
            db.session.commit()
        return redirect(url_for('admin_homework'))
    hws = Homework.query.order_by(Homework.id.desc()).all()
    return render_template('admin_homework.html', homeworks=hws, teacher=TEACHER, subject=SUBJECT)


@app.route('/admin/homework/del/<int:id>')
def admin_del_homework(id):
    if not require_admin(): return redirect(url_for('admin_login'))
    h = Homework.query.get(id)
    if h:
        db.session.delete(h)
        db.session.commit()
    return redirect(url_for('admin_homework'))


@app.route('/admin/submissions')
def admin_submissions():
    if not require_admin(): return redirect(url_for('admin_login'))
    subs = Submission.query.order_by(Submission.id.desc()).all()
    hws = {h.id: h.title for h in Homework.query.all()}
    return render_template('admin_submissions.html', submissions=subs, hws=hws, teacher=TEACHER, subject=SUBJECT)


@app.route('/admin/submission/del/<int:id>')
def admin_del_submission(id):
    if not require_admin(): return redirect(url_for('admin_login'))
    sub = Submission.query.get(id)
    if sub:
        db.session.delete(sub)
        db.session.commit()
    return redirect(url_for('admin_submissions'))


@app.route('/admin/exams', methods=['GET', 'POST'])
def admin_exams():
    if not require_admin(): return redirect(url_for('admin_login'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        grade = request.form.get('grade', 'first')
        duration = int(request.form.get('duration', 30))
        q_texts = request.form.getlist('q[]')
        q_types = request.form.getlist('qtype[]')
        q_opts_a = request.form.getlist('opta[]')
        q_opts_b = request.form.getlist('optb[]')
        q_opts_c = request.form.getlist('optc[]')
        q_opts_d = request.form.getlist('optd[]')
        q_corrects = request.form.getlist('correct[]')

        questions = []
        for i in range(len(q_texts)):
            q = q_texts[i].strip()
            if not q: continue
            if q_types[i] == 'mcq':
                questions.append({
                    'type': 'mcq', 'q': q,
                    'opts': [q_opts_a[i], q_opts_b[i], q_opts_c[i], q_opts_d[i]],
                    'correct': int(q_corrects[i] or 0)
                })
            else:
                questions.append({'type': 'essay', 'q': q, 'opts': []})

        if title and questions:
            db.session.add(Exam(title=title, grade=grade,
                                questions=json.dumps(questions, ensure_ascii=False),
                                duration=duration, active=True))
            db.session.commit()
        return redirect(url_for('admin_exams'))

    exams = Exam.query.order_by(Exam.id.desc()).all()
    return render_template('admin_exams.html', exams=exams, teacher=TEACHER, subject=SUBJECT)


@app.route('/admin/exam/toggle/<int:id>')
def admin_toggle_exam(id):
    if not require_admin(): return redirect(url_for('admin_login'))
    e = Exam.query.get(id)
    if e:
        e.active = not e.active
        db.session.commit()
    return redirect(url_for('admin_exams'))


@app.route('/admin/exam/del/<int:id>')
def admin_del_exam(id):
    if not require_admin(): return redirect(url_for('admin_login'))
    e = Exam.query.get(id)
    if e:
        db.session.delete(e)
        db.session.commit()
    return redirect(url_for('admin_exams'))


@app.route('/admin/results')
def admin_results():
    if not require_admin(): return redirect(url_for('admin_login'))
    results = ExamResult.query.order_by(ExamResult.id.desc()).all()
    return render_template('admin_results.html', results=results, teacher=TEACHER, subject=SUBJECT)


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
