from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    load_dotenv()
    app.config.from_object('config')  # Load global config
    app.config.from_pyfile('../instance/config.py', silent=True)  # Override with local config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cameras.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ENCRYPTION_KEY'] = os.environ.get('CRYPT_KEY')

    db.init_app(app)

    with app.app_context():
        from .models import Camera
        db.create_all()

    from .routes import main
    app.register_blueprint(main)

    return app