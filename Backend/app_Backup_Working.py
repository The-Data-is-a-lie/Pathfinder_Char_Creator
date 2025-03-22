# # To run this you either need to go into CMD or terminal (after typing C:\Python312) and enter this set PYTHONPATH=C:\Python312\Lib\site-packages (because it makes sure we use the right location)

from flask import Flask, render_template, request, jsonify, session, abort
from flask_cors import CORS
from flask_session import Session
import os
from start_py import create_app, SECRET_KEY


app = create_app()
# app = Flask(__name__)
# app.secret_key = SECRET_KEY
CORS(app, supports_credentials=True, origins="*", methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"])
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = False  # Mark the cookie as secure
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Set SameSite attribute to None

Session(app)


@app.route('/', methods=['GET', 'POST'])

def index():
    # Render the template for both GET and POST requests
    return render_template('index.html')

def process_input_values(input_values):
    try:
        # Ensure input_values has at least 11 elements
        if len(input_values) < 13:
            raise IndexError("Not enough elements in input_values")
        

        # Convert specific elements to integers
        for i in [1, 8, 9, 10, 11 ,12]:
            value = input_values[i]
            if value is not None and value != "":  # Check if not None and not empty string
                input_values[i] = int(value)
            else:
                # Handle the case where the value is None or an empty string
                input_values[i] = 0

        # Unpack input_values
        create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, userInput_gender, truly_random_feats, num_dice, num_sides, high_level, low_level, gold_num = input_values



        # Import and call generate_random_char
        # uncomment below if you want to use permanent website
        # from main import generate_random_char

        # Need to use main_test for localhost testing
        # Need to use Backend.main for permanent websites
        from main_test import generate_random_char
        # global character_data
        # character_data = generate_random_char(create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, userInput_gender, truly_random_feats, num_dice, num_sides, high_level, low_level, gold_num)

        session['character_data'] = generate_random_char(create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, userInput_gender, truly_random_feats, num_dice, num_sides, high_level, low_level, gold_num)
        print("correct session_dta", session['character_data'])

        return session['character_data'] 

    except ValueError as ve:
        return {"error": str(ve)}
    except IndexError as ie:
        return {"error": str(ie)}
    except Exception as e:
        return {"error": str(e)}

# Define execute route
@app.route('/execute', methods=['POST'])
def execute():
    input_values = list(request.form.get(f'input{i}') for i in range(1, 14))
    results = process_input_values(input_values)
    return jsonify(results)


# Define get_character_data route
@app.route('/get_character_data', methods=['GET', 'POST'])
def get_character_data():
    try:
        character_data = session.get('character_data', {})
        print('get character data ran', character_data)
        response = jsonify(character_data)
    except Exception as e:
        response = jsonify({'error': str(e)})
    return response



@app.route('/update_character_data', methods=['GET', 'POST'])
def update_character_data():
    data = request.json
    non_input_data = []
    for key, value in data.items():
        if key in ('input2', 'input9', 'input10', 'input11', 'input12', 'input13'):
            value = int(value)
        else:
            value = value.strip()
        non_input_data.append(value)

    results = process_input_values(non_input_data)
    session['character_data'] = results

    return session['character_data']

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)