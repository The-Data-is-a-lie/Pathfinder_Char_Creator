# # To run this you either need to go into CMD or terminal (after typing C:\Python312) and enter this set PYTHONPATH=C:\Python312\Lib\site-packages (because it makes sure we use the right location)

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_session import Session

from Backend.start_py import create_app, SECRET_KEY


app = create_app()
# app = Flask(__name__)
# app.secret_key = SECRET_KEY
CORS(app)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


@app.route('/')

def index():
    return render_template('index.html')

def process_input_values(input_values):
    try:
        # Ensure input_values has at least 11 elements
        if len(input_values) < 11:
            raise IndexError("Not enough elements in input_values")

        # Convert specific elements to integers
        for i in [1, 6, 7, 8, 9, 10]:
            value = input_values[i]
            if value is not None and value != "":  # Check if not None and not empty string
                input_values[i] = int(value)
            else:
                # Handle the case where the value is None or an empty string
                input_values[i] = 0

        # ... rest of your code ...
        
        # Unpack input_values
        create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, num_dice, num_sides, high_level, low_level, gold_num = input_values

        # Import and call generate_random_char
        from Backend.main import generate_random_char
        global character_data
        character_data = generate_random_char(create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, num_dice, num_sides, high_level, low_level, gold_num)
        # sample_data = {
        #     "name": "this is your session pull"
        # }
        # session['character_data'] = sample_data
        return character_data 
    except ValueError as ve:
        return {"error": str(ve)}
    except IndexError as ie:
        return {"error": str(ie)}
    except Exception as e:
        return {"error": str(e)}





@app.route('/ex', methods=['GET', 'POST', 'OPTIONS'])
def execute():
    input_values = [request.form.get(f'input{i}') for i in range(1, 12)]
    # session['input_values'] = input_values  # Store input values in session
    results = process_input_values(input_values)
    return results

@app.route('/execute', methods=['GET', 'POST', 'OPTIONS'])
def execute_char_data():
    try:
        results = execute()

        return render_template('index.html', output=results)
    except Exception as e:
        return render_template('index.html', error=str(e))    

@app.route('/get_character_data', methods=['GET', 'POST', 'OPTIONS'])
def get_character_data():
    if request.method == 'OPTIONS':
        # Respond to preflight request
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    else:
        try:
            # can't use a .get request for data going to a completely different server

            # For testing, replace actual processing with returning sample data
            response = jsonify(character_data)
        except Exception as e:
            response = jsonify({'error': str(e)})

    # Set CORS headers for the main request
    response.headers.add('Access-Control-Allow-Credentials', 'true')

    return response
            

@app.route('/results', methods=['GET', 'POST', 'OPTIONS'])
def results():
    if request.method == 'OPTIONS':
        # Respond to preflight request
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    else:
        try:
            # Sample data for testing
            sample_data = {
                "age_number": 25,
                "character_alignment": "neutral good",
                "character_class": "wizard",
            }
            
            response = jsonify(sample_data)
        except Exception as e:
            response = jsonify({'error': str(e)})

    # Set CORS headers for the main request
    response.headers.add('Access-Control-Allow-Credentials', 'true')

    return response
    






@app.route('/test_html_get_request', methods=['GET', 'POST', 'OPTIONS'])
def test_url_get():

    try:
        results = execute()

        return render_template('index.html', output=results)
    except Exception as e:
        return render_template('index.html', error=str(e))    

if __name__ == '__main__':
    app.run(debug=True)
    