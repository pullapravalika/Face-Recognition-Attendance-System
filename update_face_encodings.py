# scripts/update_face_encodings.py

import os
import face_recognition
from app import create_app, db
from app.models import User
from flask import current_app

app = create_app()
app.app_context().push()

updated = 0
for user in User.query.filter_by(role='student').all():
    if user.face_encoding is None and user.photo_filename:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], user.photo_filename)
        if os.path.exists(photo_path):
            try:
                image = face_recognition.load_image_file(photo_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    user.face_encoding = encodings[0]
                    db.session.commit()
                    updated += 1
                    print(f"[✓] Updated encoding for {user.email}")
                else:
                    print(f"[!] No face found for {user.email}")
            except Exception as e:
                print(f"[X] Error processing {user.email}: {e}")

print(f"Finished. Updated {updated} users.")
