# # To run this you either need to go into CMD or terminal (after typing C:\Python312) and enter this set PYTHONPATH=C:\Python312\Lib\site-packages (because it makes sure we use the right location)

from flask import  render_template, request, jsonify, session
from start_py import create_app
from createACharacter import *



app = create_app()
# app = Flask(__name__)
# app.secret_key = SECRET_KEY
@app.route('/')
def index():
    return render_template('index.html')

def process_input_values(input_values):
    input_values[1] = int(input_values[1])  # region
    input_values[2] = int(input_values[2]) if input_values[2].isdigit() else input_values[2]  # num_sides
    input_values[6] = int(input_values[6])  # num_dice
    input_values[7] = int(input_values[7])  # num_sides
    input_values[8] = int(input_values[8])  # high_level
    input_values[9] = int(input_values[9])  # low_level
    input_values[10] = int(input_values[10])  # gold_num

    create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, num_dice, num_sides, high_level, low_level, gold_num = input_values
    from main import generate_random_char

    return generate_random_char(create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, num_dice, num_sides, high_level, low_level, gold_num)

@app.route('/execute', methods=['POST'])
def execute():
    try:
        input_values = [request.form.get(f'input{i}') for i in range(1, 12)]
        session['input_values'] = input_values  # Store input values in session
        results = process_input_values(input_values)
        output = results
        return render_template('index.html', output=output)
    except Exception as e:
        return render_template('index.html', error=str(e))

@app.route('/get_character_data')
def get_character_data():
    try:
        input_values = session.get('input_values', [])  # Retrieve input values from session
        results = process_input_values(input_values)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)})

    
@app.route('/results')
def results():
    # You can retrieve data for the results page here if needed
    # Example: result_data = retrieve_data_for_results_page()

    return render_template('results.html')    

if __name__ == '__main__':
    app.run(debug=True)
    