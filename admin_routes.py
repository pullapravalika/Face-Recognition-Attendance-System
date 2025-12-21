# ── admin_routes.py ────────────────────────────────────────────────────────────
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from app import db
from app.models import User, ClassSession, Attendance
from datetime import datetime
from sqlalchemy import func
# remove face_recognition / numpy here unless you need them later

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ONE decorator only
@admin_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # ------------- form data -----------------
        name         = request.form.get('name')
        email        = request.form.get('email')
        password_raw = request.form.get('password')
        phone        = request.form.get('phone')
        cid          = request.form.get('cid')
        branch       = request.form.get('branch')
        year         = request.form.get('year')
        photo        = request.files.get('photo')

        # ------------- validation ----------------
        if not all([name, email, password_raw, phone, cid, branch, year]):
            flash("Please fill out all fields.", "warning")
            return redirect(url_for('admin.register'))

        if not photo or not allowed_file(photo.filename):
            flash("Please upload a valid photo (png, jpg, jpeg, gif).", "warning")
            return redirect(url_for('admin.register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for('admin.register'))

        # ------------- save photo ----------------
        filename = secure_filename(photo.filename)
        photo_filename = f"admin_{email}_{filename}"
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_filename)

        try:
            photo.save(photo_path)
        except Exception as e:
            flash(f"Failed to save photo: {e}", "danger")
            return redirect(url_for('admin.register'))

        # ------------- save admin ----------------
        password_hash = generate_password_hash(password_raw)  # PBKDF2‑SHA256 by default

        new_admin = User(
            name=name,
            email=email,
            password=password_hash,
            phone=phone,
            cid=cid,
            role='admin',
            branch=branch,
            year=year,
            photo_filename=photo_filename
        )

        try:
            db.session.add(new_admin)
            db.session.commit()
            flash("Admin registered successfully.", "success")
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Database error: {e}", "danger")
            return redirect(url_for('admin.register'))

    # GET
    return render_template('admin/register.html')


# ────────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))
    students = User.query.filter(
    User.role == "student",
    func.lower(User.branch) == func.lower(current_user.branch),
    User.year == current_user.year).all()
    sessions = ClassSession.query.filter(
    func.lower(ClassSession.branch) == func.lower(current_user.branch),
    ClassSession.year == current_user.year).order_by(ClassSession.day).all()

    return render_template('admin/dashboard.html', admin=current_user, students=students, sessions=sessions)


@admin_bp.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if current_user.role != 'admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))

    student = User.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.phone = request.form['phone']
        student.branch = request.form['branch']
        student.year = request.form['year']
        student.student_id = request.form['student_id']
        db.session.commit()
        flash("Student profile updated.", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/edit_student.html', student=student)
@admin_bp.route('/student/<int:student_id>/attendance')
@login_required
def view_attendance(student_id):
    if current_user.role != 'admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))

    student = User.query.get_or_404(student_id)
    if student.branch != current_user.branch or student.year != current_user.year:
        flash("You cannot view attendance for students from other branches or years.", "danger")
        return redirect(url_for('admin.dashboard'))

    attendance_records = student.attendances  # from relationship
    return render_template("admin/view_attendance.html", student=student, attendance=attendance_records)



@admin_bp.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role != 'admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))

    student = User.query.get_or_404(student_id)
    try:
        db.session.delete(student)
        db.session.commit()
        flash("Student deleted successfully.", "success")
    except:
        db.session.rollback()
        flash("Error deleting student.", "danger")

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/class_sessions/add', methods=['POST'])
@login_required
def add_class_session():
    if current_user.role != 'admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))
    subject = request.form.get("subject")
    day = request.form.get('day')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')

    if not all([day, start_time_str, end_time_str]):
        flash("All fields are required for class session.", "warning")
        return redirect(url_for('admin.dashboard'))

    # Convert string times (e.g., '14:30') to time objects
    try:
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
    except ValueError:
        flash("Invalid time format. Please use HH:MM.", "warning")
        return redirect(url_for('admin.dashboard'))

    session = ClassSession(
        subject=subject,
        day=day,
        start_time=start_time,
        end_time=end_time,
        branch=current_user.branch,
        year=current_user.year
    )

    try:
        db.session.add(session)
        db.session.commit()
        flash("Class session added.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to add class session: {str(e)}", "danger")

    return redirect(url_for('admin.dashboard'))


@admin_bp.route("/class_sessions/<int:session_id>/delete", methods=["POST"])
@login_required
def delete_class_session(session_id):

    session = ClassSession.query.get_or_404(session_id)

    # ① make sure admin is allowed (you already have that check)
    if session.branch != current_user.branch or session.year != current_user.year:
        flash("You cannot delete class sessions from other branches or years.", "danger")
        return redirect(url_for("admin.dashboard"))

    try:
        # --- NEW: remove all attendance rows tied to this session ----------
        Attendance.query.filter_by(class_session_id=session.id).delete(synchronize_session=False)

        # --- now delete the session itself ---------------------------------
        db.session.delete(session)
        db.session.commit()
        flash("Class session deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete class session: {e}", "danger")

    return redirect(url_for("admin.dashboard"))
