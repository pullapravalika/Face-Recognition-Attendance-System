# attendance_tracker.py
import os
import time
import json
import argparse
import requests
import numpy as np
import face_recognition
import cv2
from datetime import datetime, timedelta, date
from sqlalchemy.orm import sessionmaker
from app.models import ClassSession
from app import db
from app import create_app

app = create_app()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECOGNITION_DIR = os.path.join(BASE_DIR, "app", "recognition", "encodings")
API_URL = "http://localhost:5000/api/attendance/record"
PRESENCE_THRESHOLD = 0.75  # 75%

def load_known_encodings():
    encodings, student_ids = [], []
    for file in os.listdir(RECOGNITION_DIR):
        if file.endswith(".npy"):
            sid = file.split(".")[0]
            enc = np.load(os.path.join(RECOGNITION_DIR, file))
            student_ids.append(sid)
            encodings.append(enc)
    return encodings, student_ids

def get_session_details(session_id):
    return db.session.query(ClassSession).filter_by(id=session_id).first()

def run_tracker(session_id, subject):
    with app.app_context():
        known_encodings, known_ids = load_known_encodings()
        if not known_encodings:
            print("[ERROR] No face encodings found!")
            return

        print(f"[INFO] {len(known_ids)} students loaded for tracking.")

        class_session = get_session_details(session_id)
        if not class_session:
            print(f"[ERROR] No class session found with id {session_id}")
            return

        today = date.today()
        start_dt = datetime.combine(today, class_session.start_time)
        end_dt = datetime.combine(today, class_session.end_time)
        duration_seconds = (end_dt - start_dt).total_seconds()

        attendance_secs = {sid: 0.0 for sid in known_ids}
        cam = cv2.VideoCapture(0)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not cam.isOpened():
            print("[ERROR] Could not open webcam.")
            return

        print("[INFO] Tracking started for session", session_id)
        print("[INFO] Tracking will end at:", end_dt.strftime("%H:%M"))

        session_start = time.time()
        last_frame_stamp = session_start

        try:
            while True:
                current_time = time.time()
                elapsed = current_time - session_start

                if elapsed >= duration_seconds:
                    print("[INFO] Session duration reached.")
                    break

                ret, frame = cam.read()
                if not ret:
                    continue

                small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb = small[:, :, ::-1]

                face_locs = face_recognition.face_locations(rgb)
                face_encs = face_recognition.face_encodings(rgb, face_locs)

                now = time.time()
                dt = now - last_frame_stamp
                last_frame_stamp = now

                for enc in face_encs:
                    matches = face_recognition.compare_faces(known_encodings, enc, tolerance=0.5)
                    face_dist = face_recognition.face_distance(known_encodings, enc)
                    best_idx = np.argmin(face_dist)

                    if matches[best_idx]:
                        sid = known_ids[best_idx]
                        attendance_secs[sid] += dt

                for (top, right, bottom, left) in face_locs:
                    top, right, bottom, left = 4 * top, 4 * right, 4 * bottom, 4 * left
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

                cv2.imshow("Face Attendance Tracker", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            cam.release()
            cv2.destroyAllWindows()

        records = []
        for sid in known_ids:
            secs = attendance_secs.get(sid, 0.0)
            adjusted_secs = min(secs, duration_seconds)
            ratio = adjusted_secs / duration_seconds
            present = ratio >= PRESENCE_THRESHOLD
            print(f"[RESULT] {sid}: {secs:.1f}s ({ratio:.2%}) -> {'Present' if present else 'Absent'}")
            records.append({
                "student_id": sid,
                "class_session_id": session_id,
                "subject": subject,
                "start_time": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "present": present,
                "presence_seconds": round(secs, 2)
            })

        try:
            resp = requests.post(API_URL, json={"attendance": records}, timeout=10)
            if resp.ok:
                print("[INFO] Attendance successfully posted.")
            else:
                print(f"[ERROR] Post failed [{resp.status_code}]: {resp.text}")
        except requests.RequestException as e:
            print("[ERROR] Could not reach Flask API:", e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Face Attendance Tracker")
    parser.add_argument("--session_id", type=int, required=True, help="Class session ID")
    parser.add_argument("--subject", type=str, required=True, help="Subject name")
    args = parser.parse_args()
    with app.app_context():
        run_tracker(args.session_id, args.subject)
