import random
from math import floor
from utils.util import roll_dice

def roll_stats(character, num_dice, num_sides, inherent_flag=True):
    if not isinstance(num_dice, int) or num_dice <= 0: 
        num_dice = 4
    if not isinstance(num_sides, int) or num_sides <= 0:
        num_sides = 6     
    main_stat = character.class_data[character.c_class]['main_stat']
    main_stat_2 = character.class_data[character.c_class].get('main_stat_2', None)

    if '/' in main_stat:
        main_stat_parts = main_stat.split('/')
        main_stat = random.choice(main_stat_parts)



    # Roll stats for all attributes
    orig_stats = {attr: roll_dice(num_dice, num_sides) for attr in ['str', 'dex', 'con', 'int', 'wis', 'cha']}


    # Identify the original main stat
    orig_stats = swap_stats(character, main_stat, orig_stats)
    stats = orig_stats.copy()
    print("pre_stats", stats)

    # (if flagged) Distribute the inherents
    if inherent_flag == True:
        inherents = roll_inherents_func(character)
        inherents = 1000
        stats = distribute_inherents_func(inherents, stats, orig_stats)
    print("post_stats", stats)

    if main_stat_2 != None:
        main_stat_parts_2 = main_stat_2.split('/')
        main_stat_2 = random.choice(main_stat_parts_2)      
        stats = swap_stats(character, main_stat_2, stats, new=True)   

    return stats

def assign_stats(character, stats):
    for attr, value in stats.items():
        setattr(character, attr, value)

def swap_stats(character, main_stat, stats, new=None):
    original_main_stat = stats[main_stat]
    new_main_stat_key = max(stats, key=stats.get)        
    if new == None:
        stats[main_stat], stats[new_main_stat_key] = stats[new_main_stat_key], original_main_stat
    else:
        second_highest_stat_key = max(stats, key=lambda k: stats[k] if k != new_main_stat_key else float('-inf'))
        stats[main_stat], stats[second_highest_stat_key] = stats[second_highest_stat_key], original_main_stat
        

    return stats                    

def print_stats(character):
    print(f'STR {character.str}')
    print(f'DEX {character.dex}')
    print(f'CON {character.con}')
    print(f'INT {character.int}')
    print(f'WIS {character.wis}')
    print(f'CHA {character.cha}')

def calc_ability_mod(character):
    character.str_mod = floor((character.str-10)/2)
    character.dex_mod = floor((character.dex-10)/2)
    character.con_mod = floor((character.con-10)/2)
    character.int_mod = floor((character.int-10)/2)
    character.wis_mod = floor((character.wis-10)/2)
    character.cha_mod = floor((character.cha-10)/2)



def roll_inherents_func(character):
    amount = floor(character.c_class_level / 2)
    random_number = 0
    for _ in range(amount):
        random_number += random.randint(0, 5)
    return random_number

def distribute_inherents_func(inherents, stats, orig_stats):
    attributes = list(stats.keys())
    while inherents > 0:
        if len(attributes) == 0:
            break
        attribute = random.choice(attributes)
        if stats[attribute] < orig_stats[attribute] + 10:
            stats[attribute] += 1
            inherents -= 1
        elif stats[attribute] >= orig_stats[attribute] + 10:
            attributes.remove(attribute)
        elif len(attributes) == 0:
            break
        else:
            break
    return stats