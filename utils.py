# utils.py
import face_recognition
import cv2
import os
import numpy as np

def load_known_faces(upload_folder):
    known_faces = []
    known_names = []
    for filename in os.listdir(upload_folder):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            image = face_recognition.load_image_file(os.path.join(upload_folder, filename))
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_faces.append(encodings[0])
                known_names.append(filename.split('_')[1])
    return known_faces, known_names


def recognize_face(known_faces, known_names, frame):
    rgb_frame = frame[:, :, ::-1]
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_faces, face_encoding)
        name = "Unknown"
        if True in matches:
            match_index = matches.index(True)
            name = known_names[match_index]
        return name
    return None

