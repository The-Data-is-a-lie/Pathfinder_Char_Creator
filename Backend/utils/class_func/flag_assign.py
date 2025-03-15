from utils.data import languages
def druidic_flag_assigner(character):
    if character.c_class.lower() == 'druid':
        character.languages = languages.append('Druidic')

def human_flag_assigner(character):
    character.human_flag = False
    if character.chosen_race.lower() == 'human':
        print('this is your character.chosen_race ', character.chosen_race)
        character.feat_amounts += 1
        character.human_flag = True