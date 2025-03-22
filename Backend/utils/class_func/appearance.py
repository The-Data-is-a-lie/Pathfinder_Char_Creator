import random
from utils import data
from utils.util import roll_dice
def randomize_apperance_attr(character, apperance_attribute, upper_limit=1):
    random_app_number = random.randint(1,upper_limit)
    potential_apperances = getattr(data,apperance_attribute)
    return random.sample(potential_apperances, k=random_app_number)

    #change age/height/weight string into useable array that contains (e.g.) 5d6 -> 5,6 (5 num_dice, 6 num_sides)
def randomize_body_feature(self, body_attribute):
    [base_stat, dice_string] = self.races[self.chosen_race][body_attribute]        
    [num_dice, num_sides] = [int(c) for c in dice_string.split('d')]
    dice_roll = roll_dice(num_dice, num_sides)
    total_number = dice_roll + base_stat
    
    return body_attribute, total_number


def get_racial_attr(self, racial_attribute):
    if self.chosen_race in self.races:
        return self.races[self.chosen_race][racial_attribute]
    