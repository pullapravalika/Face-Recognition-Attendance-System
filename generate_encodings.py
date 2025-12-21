import os
import cv2
import numpy as np
import face_recognition

KNOWN_FACES_DIR = os.path.join("app", "recognition", "known_faces")
ENCODINGS_DIR = os.path.join("app", "recognition", "encodings")

os.makedirs(ENCODINGS_DIR, exist_ok=True)

for filename in os.listdir(KNOWN_FACES_DIR):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    student_id = os.path.splitext(filename)[0]
    image_path = os.path.join(KNOWN_FACES_DIR, filename)
    output_path = os.path.join(ENCODINGS_DIR, f"{student_id}.npy")

    if os.path.exists(output_path):
        print(f"[SKIP] Encoding already exists for {student_id}")
        continue

    print(f"[INFO] Processing {student_id}...")

    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] Could not read image: {image_path}")
        continue

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb)

    if not encodings:
        print(f"[ERROR] No face found in {filename}")
        continue

    np.save(output_path, encodings[0])
    print(f"[DONE] Encoding saved for {student_id}")
