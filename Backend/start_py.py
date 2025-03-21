from flask                  import Flask
from dotenv                 import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret')
def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # Additional configurations or extensions if needed

    return app
