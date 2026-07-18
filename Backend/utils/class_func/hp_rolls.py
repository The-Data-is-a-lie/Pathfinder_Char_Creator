import random
from math import ceil, floor


def hit_dice_calc(character):
    for entry in character.classes:
        entry['hit_die'] = extract_num(character.class_data[entry['name']]["hit die"])
    # Legacy alias: the primary class's die is the auto-maxed level-1 die in total_hp_calc.
    character.Hit_dice1 = character.classes[character.primary_class_index]['hit_die']


def extract_num(hit_die):
    hit_die = hit_die.replace(".", "").replace("d", "")
    return int(hit_die)


def roll_hp(character):
    hp_rolls = []
    for i, entry in enumerate(character.classes):
        # The primary class's first level is the maxed die (added in total_hp_calc), so it rolls
        # level-1 dice; every other class rolls all of its levels.
        dice = entry['level'] - 1 if i == character.primary_class_index else entry['level']
        for _ in range(dice):
            hp_rolls.append(random.randint(1, entry['hit_die']))
    character.total_hp_rolls = sum(hp_rolls)
    return character.total_hp_rolls


def total_hp_calc(character):
    character.Total_HP = character.total_hp_rolls + character.Hit_dice1 + (floor(character.con-10)/2 * character.level)
    character.sheet_health = character.total_hp_rolls + character.Hit_dice1
    character.Total_HP = floor(character.Total_HP)
    return character.Total_HP
