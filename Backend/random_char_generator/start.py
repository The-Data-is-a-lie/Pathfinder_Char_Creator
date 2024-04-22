
from flask import Flask
from instance.config import SECRET_KEY


def check_origin(origin):
    # Check if the origin contains "http://localhost:9000"
    return "http://localhost:9000" in origin


def create_app():
    app = Flask(__name__)
    app.config['SESSION_COOKIE_SECURE'] = True  # Mark the cookie as secure
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Set SameSite attribute to None

    


    # Additional configurations or extensions if needed

    return app
