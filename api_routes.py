# app/api_routes.py
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Attendance, User, ClassSession
from datetime import datetime

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/attendance/record", methods=["POST"])
def record_attendance():
    data = request.get_json(silent=True)
    if not data or "attendance" not in data:
        return jsonify({"error": "Invalid request: missing 'attendance' list"}), 400

    records = data["attendance"]
    updated, skipped = 0, 0
    errors = []

    for rec in records:
        student_str_id = rec.get("student_id")
        class_session_id = rec.get("class_session_id")
        present = bool(rec.get("present", False))
        presence_seconds = float(rec.get("presence_seconds", 0))
        present_minutes = float(rec.get("present_minutes", presence_seconds / 60))

        subject_sent = rec.get("subject")
        start_time_sent = rec.get("start_time")
        end_time_sent = rec.get("end_time")

        if not student_str_id or not class_session_id:
            skipped += 1
            errors.append("Missing student_id or class_session_id")
            continue

        user = User.query.filter_by(student_id=student_str_id, role="student").first()
        if not user:
            skipped += 1
            errors.append(f"No student user found for ID {student_str_id}")
            continue

        session = ClassSession.query.get(class_session_id)
        if not session:
            skipped += 1
            errors.append(f"Invalid class_session_id={class_session_id}")
            continue

        if subject_sent and session.subject and subject_sent != session.subject:
            current_app.logger.warning(
                f"Subject mismatch: tracker={subject_sent} vs DB={session.subject}"
            )

        att = Attendance.query.filter_by(
            student_id=user.id,
            class_session_id=class_session_id
        ).first()

        if att:
            att.present = present
            att.presence_seconds = presence_seconds
            att.present_minutes = present_minutes
            att.timestamp = datetime.utcnow()
        else:
            att = Attendance(
                student_id=user.id,
                class_session_id=session.id,
                present=present,
                presence_seconds=presence_seconds,
                present_minutes=present_minutes,
                timestamp=datetime.utcnow(),
            )
            db.session.add(att)

        updated += 1

    db.session.commit()

    return jsonify({
        "message": "Attendance processed.",
        "received": len(records),
        "updated": updated,
        "skipped": skipped,
        "errors": errors
    }), 200
