from flask import Flask
from instance.config import SECRET_KEY
from flask_cors import CORS
from flask_session import Session

def check_origin(origin):
    # Check if the origin contains "http://localhost:9000"
    return "http://localhost:9000" in origin


def create_app():
    app = Flask(__name__)

    # Additional configurations or extensions if needed

    return app
