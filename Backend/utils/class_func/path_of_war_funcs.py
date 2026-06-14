import random
import re

def select_disciplines(character):
    '''Disciplines available to a Path of War initiator class, parsed from the class's
    "Maneuvers" entry in path_of_war_classes.json (base tree first, Metzofitz fallback).'''
    classes = getattr(character, 'path_of_war_classes', {}) or {}
    path_of_war_class_info = (classes.get('base', {}).get(character.c_class)
                              or classes.get('metzofitz', {}).get(character.c_class))
    if not path_of_war_class_info:
        print("Class not found in path_of_war_classes")
        return None

    disciplines_string = path_of_war_class_info.get('Maneuvers', '')
    disciplines_list = clean_disciplines_string_func(disciplines_string)
    return disciplines_list

def clean_disciplines_string_func(disciplines_string):
    '''Parse a "Maneuvers" string like "Broken Blade,Solar Wind, either Riven Hourglass or
    Tempest Gale." into discipline names, resolving "X or Y" alternatives randomly.
    Word-boundary aware: the old substring version corrupted "Cursed Razor"/"Iron Tortoise"
    (contain "or") and "Fools Errand" (contains "and").'''
    disciplines = []
    for part in str(disciplines_string).rstrip('.').split(','):
        part = re.sub(r'^(?:\s*(?:and|either)\b)*\s*', '', part.strip(), flags=re.IGNORECASE)
        if not part:
            continue
        options = [opt.strip() for opt in re.split(r'\s+or\s+', part, flags=re.IGNORECASE) if opt.strip()]
        if options:
            disciplines.append(random.choice(options))
    return disciplines
