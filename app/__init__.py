from flask import Flask
from dotenv import load_dotenv
from app.models import db
from app.startup import scan_and_insert_folders_and_files
import os
import logging

def create_app():
    app = Flask(__name__,instance_relative_config=True)
   

    logging.basicConfig(
    level=logging.INFO,  # Can be DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',)
    logger = logging.getLogger(__name__)

    load_dotenv(override=True)
    app.config.from_object('config')  # Load global config
    app.config.from_pyfile('config.py', silent=True)  # Override with local config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ENCRYPTION_KEY'] = os.environ.get('CRYPT_KEY')
    app.config['EXTERNAL_MEDIA_ROOT'] = os.environ.get('EXTERNAL_MEDIA_ROOT')
    app.config['INIT_DB'] = os.environ.get('INIT_DB')

    db.init_app(app)

    logger.info("Checking INIT_DB: %s", app.config.get("INIT_DB", "False"))

    if app.config.get("INIT_DB", "False") == "True":
        logger.info("INIT_DB is True: initializing DB...")
        with app.app_context():
            db.create_all()
            scan_and_insert_folders_and_files(app)
        logger.info("DB initialized successfully.")
    else:
        logger.info("INIT_DB is False. Skipping DB init.")

    from .routes import main
    app.register_blueprint(main)

    return app
