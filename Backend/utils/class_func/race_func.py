import json
import os
import random

STAT_KEYS = ('str', 'dex', 'con', 'int', 'wis', 'cha')

# Curated race -> ability-modifier side-map (same convention as feat_changes.json).
# "any" marks the floating "+2 to One Ability Score" races (Human, Half-Elf, Half-Orc),
# resolved onto the class main stat at generation time.
_RACIAL_STATS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'json', 'racial_stat_changes.json')
_racial_stat_changes = None

def load_racial_stat_changes():
    global _racial_stat_changes
    if _racial_stat_changes is None:
        try:
            with open(_RACIAL_STATS_PATH, encoding='utf-8') as f:
                _racial_stat_changes = {str(k).lower(): v for k, v in json.load(f).items()}
        except (OSError, ValueError):
            # Fail open: no file -> no racial mods, generation still works.
            print("WARNING: racial_stat_changes.json missing or invalid; racial stats skipped")
            _racial_stat_changes = {}
    return _racial_stat_changes

def racial_stat_mods(character):
    """Six-key {str/dex/con/int/wis/cha: int} dict for character.chosen_race."""
    mods = {stat: 0 for stat in STAT_KEYS}
    entry = load_racial_stat_changes().get(str(character.chosen_race).lower())
    if entry is None:
        print(f"WARNING: no racial stat entry for race '{character.chosen_race}'")
        return mods
    for stat, val in entry.items():
        if stat == 'any':
            mods[character.main_stat] += val
        elif stat in mods:
            mods[stat] += val
    return mods

def apply_racial_stats(character, stats):
    """Add racial modifiers into the rolled stats dict; remember the split for export."""
    mods = racial_stat_mods(character)
    for stat, val in mods.items():
        if stat in stats:
            stats[stat] += val
    character.racial_stats = mods
    return stats

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