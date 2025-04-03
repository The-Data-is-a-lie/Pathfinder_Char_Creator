from math import floor
def saving_throw_calc(character, saving_throw):
    #update this to be for class_level then add up both options
    high_saving_throw = floor(2 + (character.level/2))
    low_saving_throw = floor((character.level/3))        
    if saving_throw in character.class_data[character.c_class]["saving throws"]: 
        character.saving_throw = high_saving_throw            
    else:
        character.saving_throw = low_saving_throw
    return character.saving_throw
