import os
import face_recognition
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import User, Attendance, ClassSession
from datetime import datetime

attendance_bp = Blueprint('attendance_bp', __name__)

# Store encodings and matching student IDs
known_face_encodings = []
known_face_ids = []

def load_known_faces():
    known_faces_dir = os.path.join(current_app.root_path, 'known_faces')
    if not os.path.exists(known_faces_dir):
        current_app.logger.warning(f"'known_faces' directory does not exist: {known_faces_dir}")
        return

    # Clear any existing data to avoid duplicates
    known_face_encodings.clear()
    known_face_ids.clear()

    for filename in sorted(os.listdir(known_faces_dir)):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            img_path = os.path.join(known_faces_dir, filename)
            try:
                img = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(img)

                if not encodings:
                    current_app.logger.warning(f"No face found in image: {filename}")
                    continue

                encoding = encodings[0]
                student_id = os.path.splitext(filename)[0]  # remove .jpg/.png

                known_face_encodings.append(encoding)
                known_face_ids.append(student_id)

            except Exception as e:
                current_app.logger.error(f"Error processing file {filename}: {e}")

@attendance_bp.before_app_first_request
def setup():
    load_known_faces()

@attendance_bp.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    try:
        img = face_recognition.load_image_file(file)
    except Exception as e:
        return jsonify({'error': f'Invalid image format or corrupted image. {str(e)}'}), 400

    face_locations = face_recognition.face_locations(img)
    face_encodings = face_recognition.face_encodings(img, face_locations)

    if not face_encodings:
        return jsonify({'error': 'No face detected in image'}), 400

    face_encoding = face_encodings[0]
    matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)

    if True in matches:
        match_index = matches.index(True)
        student_id = known_face_ids[match_index]

        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({'error': 'User not found in database'}), 404

        today = datetime.today().date()
        session = ClassSession.query.filter_by(date=today).first()
        if not session:
            return jsonify({'error': 'No active class session found for today'}), 404

        existing_attendance = Attendance.query.filter_by(user_id=user.id, session_id=session.id).first()
        if existing_attendance:
            return jsonify({'message': f'Attendance already marked for {user.name}'}), 200

        new_attendance = Attendance(user_id=user.id, session_id=session.id, timestamp=datetime.now())
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({'message': f'Attendance marked for {user.name}'}), 200

    return jsonify({'error': 'Face not recognized'}), 401
