from flask import Flask
import subprocess

app = Flask(__name__)

@app.route('/')
def hello_world():
    # Prompt for input
    user_input = input("Enter a number: ")

    # Provide user input to the test.py script using subprocess
    try:
        result = subprocess.run(['python', 'test.py'], input=f'{user_input}\n', capture_output=True, text=True)
        output = result.stdout
    except FileNotFoundError:
        output = 'test.py not found'
    except Exception as e:
        output = f'Error: {str(e)}'

    return output

if __name__ == '__main__':
    app.run(debug=True)




# from flask import Flask
# import subprocess

# app = Flask(__name__)

# @app.route('/')
# def hello_world():
#     # Read and execute the test.py file
#     try:
#         with open('test.py', 'r') as file:
#             # Using subprocess to run the Python script
#             result = subprocess.run(['python', '-c', file.read()], capture_output=True, text=True)
#             output = result.stdout
#     except FileNotFoundError:
#         output = 'test.py not found'
#     except Exception as e:
#         output = f'Error: {str(e)}'

#     return output

# if __name__ == '__main__':
#     app.run(debug=True)
