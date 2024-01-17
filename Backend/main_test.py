# # To run this you either need to go into CMD or terminal (after typing C:\Python312) and enter this set PYTHONPATH=C:\Python312\Lib\site-packages (because it makes sure we use the right location)

from flask import Flask, render_template, request
from main_test_run import process_inputs
from createACharacter import *


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    # Retrieve input values directly from the form
    input_values = [request.form.get(f'input{i}') for i in range(1, 12)]

    try:

        from main import generate_random_char

        # Assuming 'inputs' is a list containing the user inputs
        create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, num_dice, num_sides, high_level, low_level, gold_num = input_values

        # Call the generate_random_char function with the retrieved inputs
        results = generate_random_char(create_new_char, userInput_region, userInput_race, class_choice, multi_class, alignment_input, num_dice, num_sides, high_level, low_level, gold_num)

        #Don't think we need this, we don't want all our data to be strings (unless we need this, then we can modify the functions)
        results = str(results)
        # Join the results into a single string
        output = '\n'.join(results)

        return render_template('index.html', output=output)
    except Exception as e:
        return render_template('index.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)






# from flask import Flask, render_template, request, jsonify
# import subprocess
# from main_test_run import process_inputs
# from main import generate_random_char

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/execute', methods=['POST'])
# def execute():
#     inputs = [request.form.get(f'input{i}') for i in range(1, 10)]

#     try:
#         # Use the process_inputs function from the processing module
#         # results = process_inputs(inputs)
#         # this runs the main.py program
#         results = generate_random_char()

#         # Join the results into a single string
#         output = '\n'.join(results)

#         return render_template('index.html', output=output)
#     except Exception as e:
#         return render_template('index.html', error=str(e))

# if __name__ == '__main__':
#     app.run(debug=True)
