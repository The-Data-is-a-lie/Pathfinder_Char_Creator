from math import floor, ceil
import random
from utils import data

def choose_gun_func(character, c_class):
    if c_class.lower() != 'gunslinger':
        return []

    x = floor((character.c_class_level - 1) / 4)
    firearms = {**character.firearms.get('Siege', {}), **character.firearms.get('Firearm', {}) }
    sections = list(firearms.keys())
    chosen_weapons = set()
    useable_weapons = getattr(data, 'useable_weapons')

    while len(chosen_weapons) < x:
        choice = random.choice(sections)
        if choice in useable_weapons:
            chosen_weapons.add(choice)

    result = {"gun training": list(chosen_weapons)}

    character.data_dict.update({'class features': result})
    return result 
        
