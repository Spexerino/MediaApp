from . import db
from flask import current_app
from cryptography.fernet import Fernet


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