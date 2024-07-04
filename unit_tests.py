# Import necessary modules
from main_test import generate_random_char
import unittest

# Define a test class to group related test cases
class TestGenerateRandomChar(unittest.TestCase):

    # Define a test function with a descriptive name
    def test_generate_random_char_with_specific_inputs(self):

        # Define specific inputs for each parameter (potential error source: invalid input values)
        inputs = {
            'create_new_char': ['Y', 'N', 'ASDFASDFWEAF', 7, 84],
            'userInput_region': ["Random", "Tal-falko", "Dolestan", "Sojoria", "Ieso", "Spire", "Feyador", "Esterdragon", "Grundykin Damplands", "Dust Cairn", "Kaeru no Tochi", 0, "r", "asdfasdfasd"],
            'userInput_race': ["", "Random", "Dwarf", "Elf", "Gnome", "Half-Elf", "Halfling", "Half-Orc", "Human", "Aasimar", "Catfolk", "Dhampir", "Drow", "Fetchling", "Goblin", "Hobgoblin", "Ifrit", "Kitsune", "Kobold", "Monkey Goblin", "Orc", "Oread", "Ratfolk", "Sylph", "Tengu", "Tiefling", "Wayang", "0", "r", 999],
            'class_choice': ["", "Random", "alchemist", "antipaladin", "arcanist", "barbarian", "bloodrager", "cavalier", "fighter", "inquisitor", "investigator", "magus", "monk", "ninja", "oracle", "paladin", "ranger", "rogue", "shifter", "shaman", "skald", "slayer", "samurai", "sorcerer", "vigilante", "warpriest", "witch", "wizard"],
            'multi_class': ['N'],
            'alignment_input': ["", "LG", "LN", "LE", "NG", "N", "NE", "CG", "CN", "CE", 999, "drop_table"],
            'userInput_gender': ["", "Male", "Female", "Random", 999],
            'truly_random_feats': ["", "LG", "LN", "LE", "NG", "N", "NE", "CG", "CN", "CE"],
            'num_dice': [2, 10, "Random", "drop_table", "", 50],
            'num_sides': [2, 10, "Random", "drop_table", "", 50],
            'high_level': [100000000, 100000000, 100000000, 100000000, 100000000, 100000000],
            'low_level': [2, 10, "Random", "drop_table", "", 100, 100000000],
            'gold_num': [20000000000000, 10, "Random", "drop_table", ""],

            #solo class choice test
            # 'class_choice': ["", "","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","", "","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","", "","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""]

        }

        iterations = 100
        error_list = []
        # Iterate over each parameter and its specific inputs
        for i in range(iterations):
            for param, param_inputs in inputs.items():
                for input_value in param_inputs:
                    with self.subTest(param=param, input_value=input_value):
                        try:
                            result = generate_random_char(**{param: input_value})
                            print(f"this is the {i}th result {result}") 
                        except Exception as e:
                            print(f"Error occurred with input {input_value}: {e}")
                            error_list.append(f"Failed with input {param}={input_value}: {e}")
                            self_fail = self.fail(f"Failed with input {input_value}: {e}")

                            break 
            if error_list:
                print(f"Captured errors {error_list}")
                # All failures are collected in the list
                self.assertEqual([], error_list, msg="Test failures occurred:\n" + "\n".join(error_list))


# Run the tests if this script is executed directly
if __name__ == "__main__":
    unittest.main()
