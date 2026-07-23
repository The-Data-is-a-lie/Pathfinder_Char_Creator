import random
from utils.class_func.race_func import * 

def favored_class_option(character):
    race_data = full_race_data(character)
    favored_class_list = []
    favored_class_string = race_data.get(character.chosen_race.capitalize(), {}).get(character.c_class.capitalize(), "").strip()
    # Only offer the racial option when the race/class pair actually HAS one. Uncovered pairs used to
    # contribute an empty string that still occupied a slot in the sample below, so ~1 in 3 non-humans
    # rolled a favored-class bonus that did nothing at all.
    if favored_class_string:
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
    """Favored-class bonus: +1 HP or +1 skill rank per level.

    Scales off TOTAL character level, not ``c_class_level`` (which is an alias for the PRIMARY class's
    level, so a Monk 8 / Summoner 7 / Wizard 5 was paid for 8 of his 20 levels). Matches the same
    total-level treatment used for inherents and level-up stat bumps in stats.py.
    """
    skill_ranks = 0
    favored_class_chosen = []

    for favored_class in favored_classes:
        if favored_class == 'health':
            character.Total_HP += character.level
        elif favored_class == 'skill ranks':
            skill_ranks += character.level
        favored_class_chosen.append(favored_class)

    return skill_ranks, favored_class_chosen