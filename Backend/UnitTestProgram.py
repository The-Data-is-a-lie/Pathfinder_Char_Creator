import  unittest
import  time
import  json
from    main_test import generate_random_char

class TestGenerateRandomChar(unittest.TestCase):

    def setUp(self):
        # Define default values for each parameter
        self.default_values = {
            'create_new_char': 'Y',
            'userInput_region': 1,
            'userInput_race': 'human',
            'class_choice': 'fighter',
            'multi_class': 'N',
            'alignment_input': 'N',
            'userInput_gender': 'male',
            'truly_random_feats': 'Y',
            'num_dice': 1,
            'num_sides': 1,
            'high_level': 1,
            'low_level': 1,
            'gold_num': 1000
        }

        # Define options to test for each parameter
        self.test_options = {
            'userInput_region': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20, 'ABAC', 0, -100, 'N/A', None],
            'userInput_race': ["Random", "Dwarf", "Elf", "Gnome", "Half-Elf", "Halfling", "Half-orc", "Human", "Aasimar", "Catfolk", "Dhampir", "Drow", "Fetchling", "Goblin", "Hobgoblin", "Ifrit", "Kitsune", "Kobold", "Monkey Goblin", "Orc", "Oread", "Ratfolk", "Sylph", "Tengu", "Tiefling", "Wayang", 'ABAC', 0, -100, 'N/A', None],
            'class_choice': ['cleric', 'druid', 'fighter', 'gunslinger', 'hunter', 'inquisitor', 'investigator', 'kineticist', 'magus', 'medium', 'mesmerist', 'monk', 'monk (unchained)', 'ninja', 'occultist', 'oracle', 'paladin', 'psychic', 'ranger', 'rogue', 'rogue (unchained)', 'samurai', 'shaman', 'shifter', 'skald', 'slayer', 'sorcerer', 'spiritualist', 'summoner', 'summoner (unchained)', 'swashbuckler', 'vigilante', 'warpriest', 'witch', 'wizard', 'harbinger', 'mystic', 'stalker', 'warder', 'warlord', 'zealot', 'ABAC', 0, -100, 'N/A', None],
            'multi_class': ['N'],
            'alignment_input': ['LG', 'LN', 'LE', 'NG', 'TN', 'NE', 'CG', 'CN', 'CE', 'ABAC', 0, -100, 'N/A', None],
            'userInput_gender': ['male', 'female', 'ABAC', 0, -100, 'N/A', None],
            'num_dice': [1, 100, 'ABAC', 0, -100, 'N/A', None],
            'num_sides': [1, 100, 'ABAC', 0, -100, 'N/A', None],
            'high_level': [1, 40, 'ABAC', 0, -100, 'N/A', None],
            'low_level': [1, 40, 'ABAC', 0, -100, 'N/A', None],
            'gold_num': [1000, 0, '', 'asdfasd', 'Null', 'N/A', None]
        }
        self.failures = {}
        self.addCleanup(self.write_failures_to_file)  # Ensure this runs after tests

    def test_generate_random_char_combinations(self):
        i = 0
        for _ in range(25):
            for param, options in self.test_options.items():
                for option in options:
                    try:
                        with self.subTest(f"Testing {param} with {option}"):
                            args = self.default_values.copy()
                            args[param] = option  # Set the current parameter to the test option
                            start_time = time.time()
                            generate_random_char(**args)  # Pass arguments as keyword arguments
                            end_time = time.time()
                            execution_time = end_time - start_time
                            self.assertLess(execution_time, 10, "Execution took too long")
                            i += 1
                    except Exception as e:
                        # Record the failure
                        self.failures[f"{param}_{option}"] = str(e)
        print(f"Total loops executed: {i}")                        

    def write_failures_to_file(self):
        # Save the collected failures to a JSON file
        if self.failures:
            with open('UnitTestFailures.json', 'w') as f:
                json.dump(self.failures, f, indent=2)
            print("Failures have been written to UnitTestFailures.json")

if __name__ == '__main__':
    unittest.main()
