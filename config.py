# config.py

import os

# Base directory for the entire project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Folder paths
INSTANCE_FOLDER = os.path.join(BASE_DIR, 'instance')
PHOTO_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')      # For student profile photos
RECOGNITION_FOLDER = os.path.join(BASE_DIR, 'recognition')             # For face recognition resources
ENCODING_FOLDER = os.path.join(RECOGNITION_FOLDER, 'encodings')        # To store face encodings

# Ensure folders exist
for folder in [INSTANCE_FOLDER, PHOTO_UPLOAD_FOLDER, ENCODING_FOLDER]:
    os.makedirs(folder, exist_ok=True)

class Config:
    SECRET_KEY = 'supersecretkey'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(INSTANCE_FOLDER, 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload folders for use in the app
    UPLOAD_FOLDER = PHOTO_UPLOAD_FOLDER
    ENCODING_FOLDER = ENCODING_FOLDER
