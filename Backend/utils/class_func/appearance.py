import random
from Backend.utils import data
from Backend.utils.util import roll_dice
from Backend.utils.class_func.race_func import full_race_data_func
def randomize_apperance_attr(character, apperance_attribute, upper_limit=1):
    random_app_number = random.randint(1,upper_limit)
    potential_apperances = getattr(data,apperance_attribute)
    return random.sample(potential_apperances, k=random_app_number)

    #change age/height/weight string into useable array that contains (e.g.) 5d6 -> 5,6 (5 num_dice, 6 num_sides)
def randomize_body_feature(self, body_attribute):
    race_data = full_race_data_func(self)
    print(race_data.keys())
    print("this is your chosen race", self.chosen_race)
    print(f'??????????????????????????{self.races[self.chosen_race][body_attribute] }')
    [base_stat, dice_string] = self.races[self.chosen_race][body_attribute]        
    print(f'before setting attribute {body_attribute}', getattr(self, body_attribute))
    [num_dice, num_sides] = [int(c) for c in dice_string.split('d')]
    dice_roll = roll_dice(num_dice, num_sides)
    total_number = dice_roll + base_stat
    print(f'after setting attribute {body_attribute}', total_number)
    
    return body_attribute, total_number


def get_racial_attr(self, racial_attribute):
    if self.chosen_race in self.races:
        return self.races[self.chosen_race][racial_attribute]
    