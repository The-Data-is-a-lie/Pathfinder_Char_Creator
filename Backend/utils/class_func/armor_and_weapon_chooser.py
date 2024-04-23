import random
from Backend.utils import data
# start of Armor + Weapon choosing
    
# Start of AC calculation
def ac_bonus_calculator(character, dictionary):
    if dictionary is None:
        return 0

    for _, value in dictionary.items():
        armor_bonus = value.get('armor bonus', 0)
    return armor_bonus

def shield_chooser(character, dictionary):
    shieldless_weapons = ["Two-Handed", "Ranged"]
    for item in dictionary.values():
        category = item.get('category', 'no shield')
        limits = 'Shield' if all(weapon not in category for weapon in shieldless_weapons) else 'no shield'
    if limits == 'Shield' and (character.armor_type == 'H' and random.randint(1,100)>90):
        limits = 'Tower'
        return limits
def shield_flag_func(character, limits):
    if limits == 'Shield' or limits == 'Tower':
        character.shield_flag = True
    else:
        character.shield_flag = False
    
def weapon_type_flag_func(character, dictionary):
    for item in dictionary.values():
        if item.get('category', 'no shield') == 'Ranged':
            weapon_type = 'Ranged'
        else:
            weapon_type = 'Melee'
    return weapon_type

def list_selection(character, name, limits=None, shield_flag=True):
    if shield_flag == True:
        if limits is not None:
            choice = list_selection_limits(character,name, limits)
        else:
            choice = random.choice(list(getattr(character, name).keys()))  

        result = list(getattr(character, name).get(choice, {}).keys())
        choice_2 = random.choice(result)
        result_2 = getattr(character, name).get(choice, {}).get(choice_2, {})   

        result_dict = {choice_2: result_2}
        print(f'This is your result: {result_dict}')
        
        return result_dict

def list_selection_limits(character, name, limits=None):
    skip_count = {'L': 0, 'S':0, 'M': 1, 'H': 2, 'Shield': 3, 'Tower': 4}.get(limits, 0)
    attribute_keys = iter(getattr(character, name))
    key = next(attribute_keys, None)            

    for _ in range(skip_count):
        key = next(attribute_keys, None)
        if key is None:
            break
    return key

# here to help create AC calculation
def armor_chooser(character):
    armor_type_data = getattr(data, 'armor_type_mapping')
    default_armor_type = 'H'  # Default armor type

    armor_type = armor_type_data.get(character.c_class, default_armor_type)
    if character.bab == 'L':
        armor_type = None

    magus_armor_chooser(character, character.c_class_level)

    character.armor_type = armor_type
    return character.armor_type   


def weapon_chooser(character):
    weapon_type_data = character.class_data.get(character.c_class, {}).get('weapon and armor proficiency')
    print(character.class_data.get(character.c_class, {}))
    print(weapon_type_data)
    character.weapon_type = 'M' if 'martial' in weapon_type_data else 'S'
    print(character.weapon_type)
    return character.weapon_type


def magus_armor_chooser(character, level):
    if character.c_class == 'magus':
        character.armor_type = 'L'
        if level >= 7:
            character.armor_type = 'M'
        elif level >= 13:
            character.armor_type = 'H'

        return character.armor_type
    
