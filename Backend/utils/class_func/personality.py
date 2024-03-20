import random
from Backend.utils import data

def randomize_personality_attr(self, personality_attribute, upper_limit=1):
    # redundant, JAVASCRIPT has a CSV file with all of these
    random_pers_number = random.randint(1,upper_limit)
    potential_personality = getattr(data,personality_attribute)  
    return random.sample(potential_personality,k=random_pers_number)  