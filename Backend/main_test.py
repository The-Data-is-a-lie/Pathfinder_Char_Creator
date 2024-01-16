from flask import Flask, render_template, request, jsonify
import subprocess
from main_test_run import process_inputs
from main import generate_random_char

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    inputs = [request.form.get(f'input{i}') for i in range(1, 9)]

    try:
        # Use the process_inputs function from the processing module
        # results = process_inputs(inputs)
        # this runs the main.py program
        results = generate_random_char()

        # Join the results into a single string
        output = '\n'.join(results)

        return render_template('index.html', output=output)
    except Exception as e:
        return render_template('index.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)
