import random
from math import ceil, floor
def hit_dice_calc(character):
    if character.c_class_2 != '':
        character.Hit_dice1 = character.classes[character.c_class]["hp"]
        character.Hit_dice2 = character.classes[character.c_class_2]["hp"]                    
    else:
        character.Hit_dice1 = character.classes[character.c_class]["hp"]         


def roll_hp(character):
    hp_rolls = []
    #Figure out how to loop this to calc for each class rather than just one
    for _ in range(character.c_class_level-1):
        hp_rolls.append(random.randint(1,character.Hit_dice1))
    character.total_hp_rolls = sum(hp_rolls)         

    if character.c_class_2 != '':
        for _ in range(character.c_class_2_level):
            hp_rolls.append(random.randint(1,character.Hit_dice2))
        character.total_hp_rolls = sum(hp_rolls)         

    return character.total_hp_rolls


def total_hp_calc(character):               
    character.Total_HP = character.total_hp_rolls + character.Hit_dice1 + (floor(character.con-10)/2 * character.level)
    character.sheet_health = character.total_hp_rolls + character.Hit_dice1
    character.Total_HP = floor(character.Total_HP)
    return character.Total_HP
