from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os, random, string

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ===== صفحات العميل =====
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
    return render_template('student.html', student=s, videos=videos, homeworks=hws, subject=SUBJECT)


@app.route('/student/logout')
def student_logout():
    session.pop('student_id', None)
    return redirect(url_for('home'))


# ===== صفحات الأدمن =====
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
        'homework': Homework.query.count()
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
        if title:
            db.session.add(Homework(title=title, description=desc, grade=grade, due_date=due))
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
