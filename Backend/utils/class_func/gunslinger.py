from math import floor, ceil
import random
from utils import data
from utils.class_func.generic_func import class_entry_for

def choose_gun_func(character, c_class):
    gunslinger_entry = class_entry_for(character, 'gunslinger')
    if gunslinger_entry is None:
        return []

    x = floor((gunslinger_entry['level'] - 1) / 4)
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
        
