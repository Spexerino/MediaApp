from flask import Flask

def create_app():
    app = Flask(__name__)
    
    app.config.from_object('config')  # Load global config
    app.config.from_pyfile('../instance/config.py', silent=True)  # Override with local config

    from .routes import main
    app.register_blueprint(main)

    return app