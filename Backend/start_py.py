from flask import Flask
from config.config import SECRET_KEY


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # Additional configurations or extensions if needed

    return app
