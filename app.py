# # To run this you either need to go into CMD or terminal (after typing C:\Python312) and enter this set PYTHONPATH=C:\Python312\Lib\site-packages (because it makes sure we use the right location)

from flask import Flask, render_template, request, jsonify, session, abort
from flask_cors import CORS
from flask_session import Session
import os
from Backend.start_py import create_app, SECRET_KEY


app = create_app()
# app = Flask(__name__)
# app.secret_key = SECRET_KEY
CORS(app, supports_credentials=True, origins="*")  # Allow all origins
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = True  # Mark the cookie as secure
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
        from main import generate_random_char
        global character_data
        character_data = generate_random_char(create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, userInput_gender, truly_random_feats, num_dice, num_sides, high_level, low_level, gold_num)


        return character_data 
    except ValueError as ve:
        return {"error": str(ve)}
    except IndexError as ie:
        return {"error": str(ie)}
    except Exception as e:
        return {"error": str(e)}

# Define execute route
@app.route('/execute', methods=['GET','POST'])
def execute():
    input_values = list(request.form.get(f'input{i}') for i in range(1, 14))



    results = process_input_values(input_values)
    return jsonify(results)

# Define get_character_data route
@app.route('/get_character_data', methods=['GET', 'POST'])
def get_character_data():
    try:
        response = jsonify(character_data)
    except Exception as e:
        response = jsonify({'error': str(e)})
    return response

# @app.route('/update_character_data', methods=['POST'])
# def update_character_data():
#     try:
#         # Ensure the request is JSON
#         if not request.is_json:
#             return jsonify({'error': 'Invalid content type, expected application/json'}), 400

#         # Parse the incoming JSON data
#         data = request.json
#         print("Received JSON data:", data)

#         # Process the data
#         non_input_data = [
#             int(data.get(k, 0)) if k in ('input2', 'input9', 'input10', 'input11', 'input12', 'input13')
#             else data.get(k, '').strip()
#             for k in data
#         ]
#         print("Processed data:", non_input_data)

#         # Process the input values
#         results = process_input_values(non_input_data)
#         return jsonify({'message': 'Success', 'results': results})
#     except ValueError as ve:
#         return jsonify({'error': 'Invalid JSON: ' + str(ve)}), 400
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


@app.route('/update_character_data', methods=['POST'])
def update_character_data():
    try:
        data = request.get_json()  # Get JSON data from the request
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Create a list from the JSON data in the expected order
        non_input_data = [
            # we always need to have a 'Y' at the start of this
            'Y',
            data.get('region', ''),
            data.get('race', ''),
            data.get('class', ''),
            data.get('multiclass', ''),
            data.get('alignment', ''),
            data.get('gender', ''),
            data.get('randomFeats', ''),
            data.get('diceRolls', 0),
            data.get('diceSides', 0),
            data.get('highestLevel', 0),
            data.get('lowestLevel', 0),
            data.get('goldAmount', 0)
        ]

        # Ensure numeric fields are converted to integers
        for i in [7, 8, 9, 10, 11]:  # Indices for diceRolls, diceSides, highestLevel, lowestLevel, goldAmount
            if isinstance(non_input_data[i], str) and non_input_data[i].isdigit():
                non_input_data[i] = int(non_input_data[i])
            else:
                non_input_data[i] = 0

        print("Received JSON data:", data)
        print("Processed data:", non_input_data)

        results = process_input_values(non_input_data)
        print(results)
        return jsonify({'message': 'Success', 'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500





# Define main block to run the app
if __name__ == '__main__':
    # Get port from environment variable PORT or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Run the app with host as 0.0.0.0 to allow connections from outside
    app.run(host='0.0.0.0', port=port, debug=True)
