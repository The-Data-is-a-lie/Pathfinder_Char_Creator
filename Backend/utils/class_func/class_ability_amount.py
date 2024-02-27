from math import floor
def class_abilities_amount(character):

    #rogues + ninja both can select rogue talents        
    if character.c_class == 'rogue' or character.c_class == 'unchained_rogue':
        rogue_talent_amount = floor(character.c_class_level/2)
    if character.c_class_2 == 'rogue' or character.c_class_2 == 'unchained_rogue':
        rogue_talent_amount = floor(character.c_class_2_level/2)  

    if character.c_class == 'ninja' :
        ninja_talent_amount = floor(character.c_class_level/2)
    if character.c_class_2 == 'ninja' :
        ninja_talent_amount = floor(character.c_class_2_level/2)               

    #skald + barbarians both select rage powers
    if character.c_class == 'barbarian' or character.c_class == 'unchained_barbarian':
        barbarian_talent_amount = floor(character.c_class_level/2)
    if character.c_class_2 == 'barbarian' or character.c_class_2 == 'unchained_barbarian':
        barbarian_talent_amount = floor(character.c_class_2_level/2)  

    if character.c_class == 'skald':
        skald_talent_amount = floor(character.c_class_level/3)
    if character.c_class_2 == 'skald':
        skald_talent_amount = floor(character.c_class_2_level/3)     