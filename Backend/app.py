# External imports
from flask import Flask, render_template, request, jsonify, session, abort
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from datetime import timedelta
import os

# Custom function imports
from start_py import create_app
from main_test import generate_random_char

# Load environment variables
load_dotenv()
# Access redis URL
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

app = create_app()
app.config['JSON_SORT_KEYS'] = False  # Disable sorting of JSON keys
app.json.sort_keys = False  # Disable sorting of JSON keys

# Initialize Flask-Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "500 per hour", "60 per minute"],
    storage_uri=redis_url  # Set the Redis URL as the storage backend
)

# Flask Configuration
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis.from_url(redis_url)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_PERMANENT'] = False
# Needs enough time or multiple workers break
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=60)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

Session(app)

# allowing many routes:
# For allowing all origins
CORS(app, 
     supports_credentials=True, 
     origins=["http://192.168.1.164:30000", 
             "http://72.180.6.78:30000", 
             "http://localhost:3000",
             "http://localhost:30000",
             "http://127.0.0.1:30000",
             "http://127.0.0.1:3000",
             "http://localhost:4000",
             "http://localhost:5000",
             "http://localhost:6000",
             "http://localhost:7000",
             "http://localhost:8000",
             "http://localhost:9000"], 
             
     methods=["GET", "POST", "PUT", "DELETE"], 
     allow_headers=["Content-Type", "Authorization"]
     )

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

def process_input_values(input_values):
    try:
        if len(input_values) < 15:
            raise IndexError("Not enough elements in input_values")
        
        # Convert specific elements to integers
        for i in [1, 10, 11, 12, 13, 14]:
            value = input_values[i]
            if value is not None and value != "":
                input_values[i] = int(value)
            else:
                input_values[i] = 0

        # Unpack input_values
        create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, deity, userInput_gender, truly_random_feats, inherents, num_dice, num_sides, high_level, low_level, gold_num = input_values
        session['character_data'] = generate_random_char(create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, deity, inherents, userInput_gender, truly_random_feats, num_dice, num_sides, high_level, low_level, gold_num)
        return session['character_data']

    except ValueError as ve:
        return {"error": str(ve)}
    except IndexError as ie:
        return {"error": str(ie)}
    except Exception as e:
        return {"error": str(e)}

@app.route('/update_character_data', methods=['GET', 'POST'])
@limiter.limit("60 per minute")
def update_character_data():
    data = request.json
    non_input_data = []
    for key, value in data.items():
        if key in ('input2', 'input11', 'input12', 'input13', 'input14', 'input15'):
            value = int(value)
        else:
            value = value.strip()
        non_input_data.append(value)

    results = process_input_values(non_input_data)
    session['character_data'] = results

    return jsonify(session['character_data'])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # debug when production = dangerous