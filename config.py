import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
UPLOAD_FOLDER = 'uploads/'