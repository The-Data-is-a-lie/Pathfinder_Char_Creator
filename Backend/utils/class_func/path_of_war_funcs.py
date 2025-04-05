import random

def select_disciplines(character):
    try:
        path_of_war_class_info = character.path_of_war_classes.get('base', {}).get(character.c_class, [])
    except:
        path_of_war_class_info = character.path_of_war_classes.get('metzofitz', {}).get(character.c_class, [])
    
    if not path_of_war_class_info:
        print("Class not found in path_of_war_classes")
        return None

    disciplines_string = path_of_war_class_info.get('Maneuvers', '')
    disciplines_list = clean_disciplines_string_func(disciplines_string)
    return disciplines_list

def clean_disciplines_string_func(disciplines_string):
    disciplines_string = disciplines_string.replace("and", "").replace(".", "")
    disciplines = [disc.strip() for disc in disciplines_string.split(",") if disc.strip()]
    
    for i, discipline in enumerate(disciplines):
        if "or" in discipline:
            options = [opt.strip() for opt in discipline.split("or")]
            disciplines[i] = random.choice(options)  # Randomly select one option
    
    return disciplines
