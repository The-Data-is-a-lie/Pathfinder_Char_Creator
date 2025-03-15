
from flask import Flask
from config.config import SECRET_KEY


def check_origin(origin):
    # Check if the origin contains "http://localhost:9000"
    return "http://localhost:9000" in origin


def create_app():
    app = Flask(__name__)


    


    # Additional configurations or extensions if needed

    return app
