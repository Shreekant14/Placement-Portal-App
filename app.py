from flask import Flask, render_template, request,redirect, session, url_for 
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "supersecretkey"

db = SQLAlchemy(app)

# -----------------------
# TABLE MODELS
# -----------------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200) , nullable=False)
    email = db.Column(db.String(120),nullable=False,unique=True)
    password = db.Column(db.String(200), nullable=False)
    
    role = db.Column(db.String(20), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student_profile = db.relationship("StudentProfile",back_populates="user", uselist=False)
    company_profile = db.relationship("CompanyProfile",back_populates="user", uselist=False)
    notifications = db.relationship("Notification",back_populates="user")
    

class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    department = db.Column(db.String (100))
    cgpa = db.Column(db.Float)
    resume = db.Column(db.String(290))

    user = db.relationship("User", back_populates="student_profile")
    applications = db.relationship("Application", back_populates="student")
    placements = db.relationship("Placement", back_populates="student")

class CompanyProfile(db.Model):
    __tablename__= "company_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    company_name = db.Column(db.String (150))
    industry = db.Column(db.String (100))
    website = db.Column(db.String(150))

    user = db.relationship("User", back_populates="company_profile")
    jobs = db.relationship("Job", back_populates="company")
    placements = db.relationship("Placement", back_populates="company")
    
class Job(db.Model):
    __tablename__= "jobs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company_profiles.id"), nullable=False)

    title = db.Column(db.String(150))
    skills = db.Column(db.String(200))
    salary = db.Column(db.String(50))

    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    company = db.relationship("CompanyProfile", back_populates="jobs")
    applications = db.relationship("Application", back_populates="job")
    placements = db.relationship("Placement", back_populates="job")
    
class Application(db.Model):
    __tablename__= "applications"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)

    status = db.Column(db.String(50), default="Applied")
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job", back_populates="applications")
    student = db.relationship("StudentProfile", back_populates="applications")
    status_logs = db.relationship("ApplicationStatusLog", back_populates="application")

class ApplicationStatusLog(db.Model):
    __tablename__= "application_status_logs"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)

    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    application = db.relationship("Application", back_populates="status_logs")

class Placement(db.Model):
    __tablename__ = "placements"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("company_profiles.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)

    offer_date = db.Column(db.DateTime, default=datetime.utcnow)
    salary_offered = db.Column(db.String(50))
    status = db.Column(db.String(50), default="Placed")

    student = db.relationship("StudentProfile", back_populates="placements")
    company = db.relationship("CompanyProfile", back_populates="placements")
    job = db.relationship("Job", back_populates="placements")

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")


# -----------------
# MAIN APPLICATION
# -----------------


@app.route('/')
def index( ):
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if not user:
            print('186 line')
            return "User not found"

        if not check_password_hash(user.password, password):
            return "Incorrect password"

        # Store session
        session["user_id"] = user.id
        session["role"] = user.role


        # Role-based redirect
        if user.role == "admin":
            return redirect(url_for('admin_dashboard'))

        elif user.role == "company":
            if not user.is_approved:
                return "Wait for admin approval"
            return redirect(url_for('company_dashboard'))

        else:
            return redirect(url_for('student_dashboard'))

    return render_template('login.html')

# -----------------
# DASHBOARDS
# -----------------

@app.route("/company_dashboard")
def company_dashboard():
    if "user_id" not in session:
        return redirect('/login')

    if session["role"] != "company":
        return "Access Denied"

    return render_template("company_dashboard.html")


@app.route("/student_dashboard")
def student_dashboard():
    if "user_id" not in session:
        return redirect('/login')

    if session["role"] != "student":
        return "Access Denied"

    return render_template("student_dashboard.html")


@app.route("/admin_dashboard")
def admin_dashboard():
    if "user_id" not in session:
        return redirect('/login')

    if session["role"] != "admin":
        return "Access Denied"

    companies = User.query.filter_by(role="company").all()

    return render_template("admin_dashboard.html", companies=companies)


@app.route("/approve_company/<int:id>")
def approve_company(id):
    if "user_id" not in session:
        return redirect('/login')

    if session["role"] != "admin":
        return "Access Denied"

    company = User.query.get(id)

    if not company:
        return "Company not found"

    company.is_approved = True
    db.session.commit()

    return redirect(url_for('admin_dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        if role=="admin":
            return "Admin can not register"
        if User.query.filter_by(email=email).first():
            return "Email already registered"
        
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role,
            is_approved=False if role == "company" else True
        )
        db.session.add(user)
        db.session.commit()

        print(name, email, password)

        return "Registered Successfully"

    return render_template('register.html')

if __name__=="__main__":

    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(email="admin@gmail.com").first()

        if not admin:
            admin_user = User(
                name="admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin"),
                role="admin",
                is_approved=True
            )
            db.session.add(admin_user)
            db.session.commit()

    app.run(debug=True)


