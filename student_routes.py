# student_routes.py  ─────────────────────────────────────────────────────────────
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from app import db
from app.models import User, Attendance, ClassSession
import os, face_recognition, numpy as np

student_bp = Blueprint("student", __name__, url_prefix="/student")

# ---------------------------------------------------------------------
# Allowed photo extensions
# ---------------------------------------------------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
def _allowed(fname):
    return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------
# helper: save original photo + encode face
# ---------------------------------------------------------------------
def _save_and_encode(photo_file, student_id):
    if not _allowed(photo_file.filename):
        raise ValueError("Invalid image type. Allowed: png, jpg, jpeg, gif")

    # ---- 1. Save original photo -------------------------------------------------
    filename       = secure_filename(f"{student_id}.jpg")
    photo_path     = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    photo_file.save(photo_path)

    # ---- 2. Encode face & save .npy --------------------------------------------
    enc_dir        = current_app.config["ENCODING_FOLDER"]
    os.makedirs(enc_dir, exist_ok=True)

    img  = face_recognition.load_image_file(photo_path)
    encs = face_recognition.face_encodings(img)
    if not encs:
        # Clean up the saved photo if no face detected
        os.remove(photo_path)
        raise ValueError("No face detected in the uploaded photo. Please try another.")

    encoding_path = os.path.join(enc_dir, f"{student_id}.npy")
    np.save(encoding_path, encs[0])

    return filename  # photo_filename stored in DB


# ---------------------------------------------------------------------
# A)  Student registration
# ---------------------------------------------------------------------
@student_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # 1)  email uniqueness check
        email = request.form["email"]
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please log in or use another email.", "warning")
            return redirect(url_for("student.register"))

        # 2)  collect form data
        student_id  = request.form["student_id"]
        photo_file  = request.files.get("photo")
        if not photo_file:
            flash("Please upload a profile photo.", "warning")
            return redirect(url_for("student.register"))

        # 3)  save + encode
        try:
            photo_filename = _save_and_encode(photo_file, student_id)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("student.register"))

        # 4)  create user
        new_stu = User(
            name=request.form["name"],
            email=email,
            password=generate_password_hash(request.form["password"]),
            phone=request.form["phone"],
            role="student",
            photo_filename=photo_filename,
            cid=None,
            branch=request.form["branch"],
            year=request.form["year"],
            father_name=request.form["father_name"],
            student_id=student_id,
            dob=request.form["dob"],
            gender=request.form["gender"],
            address=request.form["address"],
        )
        
        db.session.add(new_stu)
        db.session.commit()

        flash("Student registered successfully! Please log in.", "success")
        return redirect(url_for("main.login"))

    # GET
    return render_template("student/register.html")


# ---------------------------------------------------------------------
# B)  Student dashboard
# ---------------------------------------------------------------------
@student_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "student":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("main.index"))

    # Attendance rows
    attendance = Attendance.query.filter_by(student_id=current_user.id)\
                                 .order_by(Attendance.timestamp.desc())\
                                 .all()

    # Class sessions matching branch & year
    sessions = ClassSession.query.filter_by(branch=current_user.branch,
                                            year=current_user.year)\
                                 .order_by(ClassSession.day)\
                                 .all()

    present_count = len(attendance)
    total_sessions = len(sessions)
    absent_count   = max(total_sessions - present_count, 0)

    return render_template(
        "student/dashboard.html",
        student=current_user,
        attendance=attendance,
        sessions=sessions,
        present_count=present_count,
        absent_count=absent_count,
    )


# ---------------------------------------------------------------------
# C)  Webcam attendance capture page (optional link)
# ---------------------------------------------------------------------
@student_bp.route("/attendance")
@login_required
def attendance_page():
    if current_user.role != "student":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("main.index"))
    return render_template("student/attendance.html")
# ────────────────────────────────────────────────────────────────────────────────
