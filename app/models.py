from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from cryptography.fernet import Fernet

db = SQLAlchemy()

class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(100), nullable=False)
    port = db.Column(db.Integer, default=554)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)  # Encrypt in production
    stream_path = db.Column(db.String(200), nullable=False)

    def get_rtsp_url(self):
        fernet = Fernet(current_app.config["ENCRYPTION_KEY"])
        return f"rtsp://{self.username}:{fernet.decrypt(self.password.encode()).decode()}@{self.ip_address}:{self.port}/{self.stream_path}"
    

class Folder(db.Model):
    __tablename__ = 'folders'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('year', 'month', 'day', name='uq_year_month_day'),
    )

    files = db.relationship('File', backref='folder', cascade='all, delete-orphan')


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('filename', 'folder_id', name='uq_filename_folder'),
    )

