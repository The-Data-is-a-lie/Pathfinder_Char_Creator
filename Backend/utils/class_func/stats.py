import random
from math import floor
from utils.util import roll_dice
from utils.class_func import luck

def roll_stats(character, num_dice, num_sides, inherent_flag='Y'):
    if not isinstance(num_dice, int) or num_dice <= 0:
        try:
            num_dice = int(num_dice)
        except:
            num_dice = 4
    if not isinstance(num_sides, int) or num_sides <= 0:
        try:
            num_sides = int(num_sides)
        except:
            num_sides = 6     

    main_stat = character.class_data[character.c_class]['main_stat']
    main_stat_2 = character.class_data[character.c_class].get('main_stat_2', None)

    if '/' in main_stat:
        main_stat_parts = main_stat.split('/')
        main_stat = random.choice(main_stat_parts)

    character.main_stat = main_stat
    character.main_stat_2 = main_stat_2

    # Roll stats for all attributes
    orig_stats = {attr: roll_dice(num_dice, num_sides) for attr in ['str', 'dex', 'con', 'int', 'wis', 'cha']}


    # Identify the original main stat
    orig_stats = swap_stats(character, main_stat, orig_stats)

    if main_stat_2 != None:
        main_stat_parts_2 = main_stat_2.split('/')
        main_stat_2 = random.choice(main_stat_parts_2)      
        orig_stats = swap_stats(character, main_stat_2, orig_stats, new=True)   

    stats = orig_stats.copy()

    inherent_flag = inherent_flag.lower()
    # (if flagged) Distribute the inherents
    if inherent_flag != 'n':
        inherents = roll_inherents_func(character)
        create_inherents_func(character, stats, inherents)
        # stats = distribute_inherents_func(inherents, stats, orig_stats)
    else:
        # Inherents disabled -> still publish a zeroed {stat: 0} dict of the SAME shape
        # create_inherents_func produces. The Foundry module builds an "Inherents" buff straight from
        # this, and the payload exports it; leaving the attribute unset crashed export with
        # AttributeError: 'Character' object has no attribute 'inherents'.
        character.inherents = {stat: 0 for stat in stats}

    level_up_stats(stats, character)
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
    amount = floor(character.level / 2)
    random_number = 0
    for _ in range(amount):
        random_number += random.randint(0, 5)
    return random_number

def create_inherents_func(character, stats, inherents=0):
    print("pre stats", stats)
    inherent_stats = stats.copy()
    #cap at 60 can never go above +10 each stat currently
    inherents = min(inherents, 60) 
    attributes = list(inherent_stats.keys())
    # Set = 0, so we can create a dictionary of 0s -> create a buff later on
    for stat in inherent_stats:
        inherent_stats[stat] = 0

    while inherents > 0:
        if len(attributes) == 0:
            break

        # Randomly pick an attribute
        attribute = random.choice(attributes)
        
        # Calculate the maximum allowable increase for the selected attribute
        max_increase = 10 - inherent_stats[attribute]
        
        if max_increase > 0:
            # Allocate a random amount of inherents to this attribute, up to the maximum allowable increase
            allocation = min(inherents, random.randint(1, max_increase))
            inherent_stats[attribute] += allocation
            inherents -= allocation
        else:
            # Remove the attribute if it can't be increased further
            attributes.remove(attribute)

    character.inherents = inherent_stats
    return None

def level_up_stats(stats, character, main_stat=None):
    level_up_stats = stats.copy()
    for stat in level_up_stats:
        level_up_stats[stat] = 0


    num_of_stats = floor(character.level / 4)
    # Luck (oks/pathfinder/house-rules/luck.md) trades against this pool in both directions: a buyer
    # converts bumps to luck 1:1, a seller gains "an additional attribute point for -5 luck". The
    # deduction happens HERE, where the real pool size is known, rather than in phase_luck_stake --
    # so what the character actually paid is recorded and can never exceed what it had.
    stake = luck.stake_of(character)
    _before = num_of_stats
    _spent = luck.settle(stake, luck.CURRENCY_LEVEL_UP_POINTS, num_of_stats)
    num_of_stats -= _spent
    # THE PAYOUT IS NO LONGER FOLDED INTO THE LEVEL-UP BUMPS. Those bumps are uniform across the six
    # abilities and reach Foundry as the "Level-up Stats" buff; a luck-bought point is a different
    # thing and is delivered as its own pf1 ability change on the Negative Luck Payout item, where
    # it is attributable instead of vanishing into a pool of ordinary level-up increases.
    #
    # It is also weighted rather than uniform (luck.roll_attribute_payout): half the draw goes to
    # the character's main stat, so a bought point usually lands where the character plays.
    _received = luck.payout(stake, luck.PAYOUT_ATTRIBUTE_POINTS)
    character.luck_attribute_bumps = luck.roll_attribute_payout(
        _received, getattr(character, 'main_stat', None))
    luck.record_audit(character, 'attribute_points', _before, _spent, _received, max(0, num_of_stats))
    for i in range(max(0, num_of_stats)):
        attribute = random.choice(list(level_up_stats.keys()))
        level_up_stats[attribute] += 1

    character.level_up_stats = level_up_stats
    return


