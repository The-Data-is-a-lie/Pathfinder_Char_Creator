def druidic_flag_assigner(character):
    character.druidic_flag = any(c['name'] == 'druid' for c in character.classes)

def human_flag_assigner(character):
    character.human_flag = False
    if character.chosen_race.lower() == 'human':
        character.feat_amounts += 1
        character.human_flag = True