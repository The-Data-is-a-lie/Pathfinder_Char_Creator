from math import floor
def process_inputs(inputs):
    results = []
    for input_value in inputs:
        try:
            # Convert the input to a float
            input_number = float(input_value)

            # Calculate the result
            result = floor(input_number/2)

            # Append the result to the list
            results.append(f"This is 2x your input: {result}")
        except ValueError:
            # Handle the case where the input is not a valid number
            results.append("Invalid input, please enter a number.")

    return results