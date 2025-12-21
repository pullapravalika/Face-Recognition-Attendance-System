import cv2
import face_recognition
import os
import pickle

def register_student(name):
    cam = cv2.VideoCapture(0)
    print("Press 's' to capture photo...")

    while True:
        ret, frame = cam.read()
        cv2.imshow("Register Face", frame)
        if cv2.waitKey(1) & 0xFF == ord('s'):
            break

    cam.release()
    cv2.destroyAllWindows()

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    if not face_locations:
        print("No face found. Try again.")
        return

    encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
    with open(f"known_faces/{name}.pkl", "wb") as f:
        pickle.dump(encoding, f)

    print(f"{name} registered successfully!")

if __name__ == "__main__":
    student_name = input("Enter student name: ")
    register_student(student_name)
