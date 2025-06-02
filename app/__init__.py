from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__,instance_relative_config=True)
    
    load_dotenv(override=True)
    app.config.from_object('config')  # Load global config
    app.config.from_pyfile('config.py', silent=True)  # Override with local config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ENCRYPTION_KEY'] = os.environ.get('CRYPT_KEY')
    app.config['EXTERNAL_MEDIA_ROOT'] = os.environ.get('EXTERNAL_MEDIA_ROOT')

    db.init_app(app)

    with app.app_context():
        from .models import Camera
        db.create_all()

    from .routes import main
    app.register_blueprint(main)

    return app