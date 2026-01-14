from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------------
# APP CONFIG
# -------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nasila-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# -------------------------
# MODELS
# -------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    course = db.Column(db.String(120), nullable=False)

with app.app_context():
    db.create_all()

# -------------------------
# LOGIN MANAGER
# -------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------
# LOGIN (ADMIN ONLY)
# -------------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username != 'admin':
            flash("❌ Only admin can login", "danger")
            return redirect('/login')

        user = User.query.filter_by(username='admin').first()

        if not user:
            user = User(
                username='admin',
                password=generate_password_hash('1234')
            )
            db.session.add(user)
            db.session.commit()

        if check_password_hash(user.password, password):
            login_user(user)
            flash("✅ Login successful", "success")
            return redirect('/dashboard')
        else:
            flash("❌ Incorrect password", "danger")

    return render_template('login.html')

# -------------------------
# LOGOUT
# -------------------------
@app.route('/logout')
def logout():
    logout_user()
    flash("👋 Logged out successfully", "info")
    return redirect('/login')

# -------------------------
# DASHBOARD (SEARCH + FILTER + PAGINATION)
# -------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    search = request.args.get('search', '')
    course_filter = request.args.get('course', '')
    page = request.args.get('page', 1, type=int)
    per_page = 5

    query = Student.query

    if search:
        query = query.filter(
            (Student.name.contains(search)) |
            (Student.email.contains(search)) |
            (Student.course.contains(search))
        )

    if course_filter:
        query = query.filter_by(course=course_filter)

    students = query.paginate(page=page, per_page=per_page)

    all_courses = [c.course for c in Student.query.distinct(Student.course)]

    return render_template(
        'dashboard.html',
        students=students,
        search=search,
        course_filter=course_filter,
        all_courses=all_courses
    )

# -------------------------
# ADD STUDENT
# -------------------------
@app.route('/add-student', methods=['POST'])
@login_required
def add_student():
    student = Student(
        name=request.form['name'],
        email=request.form['email'],
        course=request.form['course']
    )
    db.session.add(student)
    db.session.commit()
    flash("✅ Student added successfully", "success")
    return redirect('/dashboard')

# -------------------------
# EDIT STUDENT
# -------------------------
@app.route('/edit-student/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)

    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.course = request.form['course']
        db.session.commit()
        flash("✏ Student updated successfully", "warning")
        return redirect('/dashboard')

    return render_template('edit_student.html', student=student)

# -------------------------
# DELETE STUDENT
# -------------------------
@app.route('/delete-student/<int:id>')
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash("🗑 Student deleted successfully", "danger")
    return redirect('/dashboard')

# -------------------------
# RUN
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
