import random
# Race_data section
def full_race_data(character):
    # if we want races to work, we need them in data.py/playableraces.json/races.json
    # all race data we can add is in races_json_missing_data 
    race_data = {}
    race_data.update(character.PlayableRaces['Core'])
    race_data.update(character.PlayableRaces['NonCore'])
    return race_data

def subrace_chooser(character):
    race_data = full_race_data(character)
    pre_subrace_list = race_data.get(character.chosen_race, {})

    if pre_subrace_list.get("Subraces", {}) not in (None, {}):
        subrace_list = pre_subrace_list.get("Subraces", {})
        subrace_list = list(subrace_list.keys())
        chosen_subrace = random.choice(subrace_list)
        subrace_description = race_data.get(character.chosen_race, None).get("Subraces", None).get(chosen_subrace, None)
    else:
        chosen_subrace = None
        subrace_description = None       
    return chosen_subrace, subrace_description

def race_traits_chooser(character):
    race_data = full_race_data(character)
    if race_data.get(character.chosen_race.capitalize(), None) == None:
            print(character.chosen_race + " has no traits")
            return '', ''
    
    data_list = list(race_data.get(character.chosen_race.capitalize(), None).keys())
    race_traits_list = []
    race_traits_description_list = []
    append_start = False
    for i in data_list:
        if '+' in i:
            append_start = True
        if append_start:
            race_traits_list.append(i)
        if 'Languages' in i:
            append_start = False

    for trait in race_traits_list:
        race_trait_description = race_data.get(character.chosen_race, None).get(trait)
        race_traits_description_list.append(race_trait_description)

    return race_traits_list, race_traits_description_list


def race_ability_split(character, race_traits_list):
    ability_string = race_traits_list[0]
    split_string = ability_string.split(",")
    return split_string

def race_ability_score_changes(character, split_race_traits_list, score, ability):
    for trait in split_race_traits_list:
        add_flag = '+' in trait

        for n in range(10):
            if ability.lower() in trait.lower() and str(n) in trait:
                score += n if add_flag else -n

    return score