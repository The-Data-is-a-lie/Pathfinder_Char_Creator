import random
from utils.class_func.race_func import * 

def favored_class_option(character):
    race_data = full_race_data(character)
    favored_class_list = []
    favored_class_string = race_data.get(character.chosen_race.capitalize(), {}).get(character.c_class.capitalize(), "").strip()
    favored_class_list.append(favored_class_string)
    favored_class_list.extend(['health', 'skill ranks'])
    return favored_class_list

def favored_class_option_chooser(character, favored_class_list, human_flag):
    if human_flag == True:
        favored_class = ['health', 'skill ranks']
    else:
        favored_class = random.sample(favored_class_list, k=1)
    return favored_class

def favored_class_calculator(character, favored_classes):
    skill_ranks = 0
    favored_class_chosen = []

    for favored_class in favored_classes:
        if favored_class == 'health':
            character.Total_HP += character.c_class_level
        elif favored_class == 'skill ranks':
            skill_ranks += character.c_class_level
        favored_class_chosen.append(favored_class)

    return skill_ranks, favored_class_chosen