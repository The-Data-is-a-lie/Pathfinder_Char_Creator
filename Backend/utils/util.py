from random import randrange
from math import floor
#importing stats in case we want to work on them
import random
from utils import data
from utils.data import traits, mannerisms, regions, weapon_groups, weapon_groups_region, disciplines, skills,  languages, hair_colors, hair_types, appearance, eye_colors, path_of_war_class#evil_deities, good_deities, neutral_deities,
import json
import sys
from utils.class_func.race_func import *


character_data = {}

def roll_dice(num_dice, num_sides):
    if not (isinstance(num_dice, int)):
        num_dice = 4
    if not isinstance(num_sides, int):
        num_sides = 6
    rolls = []
    for _ in range(num_dice):
        rolls.append(random.randint(1, num_sides))
    total = sum(rolls)   
    return total

def roll_inherent(sides,size):
    return random.randint(sides,size)

def region_chooser(character, userInput_region):
    """
    Characters either choose a region or randomly select one
    Return
    - region
    """
    pre_regions = list(character.first_names_regions.keys())
    regions = []
    for region in pre_regions:
        regions.append(region.title())

    regions.remove(region)
    if isinstance(userInput_region, str) and userInput_region.title() in regions:
        region_selected = userInput_region.title()        
    else:
        region_selected = random.choice(regions).title()

    character.region = region_selected
    return character.region

def race_chooser(character, userInput_race):
    """
    Characters either choose a race, or randomly select one
    Return
    - userInput_race
    """
    race_data = full_race_data(character)
    # Match on an alphanumeric-only key so any client spelling resolves to the data files'
    # exact key: the web sheet / Foundry module send slugs ('monkey-goblin', 'half-elf'),
    # and the data keys mix casing ('Monkey goblin', 'Half-Elf'). Unknown input (incl.
    # 'Random') falls through to a random race.
    slug = lambda s: ''.join(ch for ch in str(s).lower() if ch.isalnum())
    canonical = {slug(r): r for r in race_data}
    chosen = canonical.get(slug(userInput_race)) if isinstance(userInput_race, str) else None
    character.chosen_race = chosen or random.choice(list(race_data.keys()))
    return character.chosen_race
        
def gender_chooser(character, userInput_gender):
    """
    Characters either choose a gender, or randomly select one
    Return
    - userInput_gender
    """
    genders = ("Male", "Female")
    if isinstance(userInput_gender, str):
        userInput_gender = userInput_gender.capitalize()
    if userInput_gender not in genders:
        userInput_gender = random.choice(genders).capitalize()
    character.chosen_gender = userInput_gender
    return character.chosen_gender

def name_chooser(character):
    """
    Randomly generates names by region
    Return
    - f_name, l_name, full_name
    """
    f_name_list = list(character.first_names_regions)
    l_name_list = list(character.last_names_regions)


    if character.region in f_name_list:
        f_names = character.first_names_regions.get(character.region, "Tal-Falko").get(character.chosen_gender, "Nameless")
        l_names = character.last_names_regions[character.region]        
        character.f_name = random.choice(f_names)
        character.l_name = random.choice(l_names) 
        character.full_name = character.f_name + character.l_name

    else:
        # wehave this section in case of an emergency and region isn't selected. But this should never occur
        region_list = (list(f_name_list))
        region = random.choice(region_list)
        f_names = character.first_names_regions.get(region, "Tal-Falko").get(character.chosen_gender, "Nameless")
        l_names = character.last_names_regions[region]      
        character.f_name = random.choice(f_names)
        character.l_name = random.choice(l_names) 
        character.full_name = character.f_name + character.l_name

    return character.f_name, character.l_name

    
def _available_class_pool(character):
    """The base random-class pool: every class_data key minus the occult classes (not ready yet)
    and the Path of War classes missing from the pf1-pow Foundry compendium (they'd generate fine
    here, but the Foundry sheet can't resolve a class item the module doesn't ship — re-enable by
    emptying pow_classes_pending_foundry in data.py once the module includes them)."""
    occult_classes = [x.lower() for x in getattr(data, 'occult_classes')]
    pending = [x.lower() for x in getattr(data, 'pow_classes_pending_foundry', [])]
    return [x for x in character.class_data.keys()
            if x not in occult_classes and x not in pending]


def chooseClass(character, class_choice, chosen_BAB, chosen_caster_level=None):
    """
    Select a class or
    Gives the Character a random class based off of BAB selection
    Returns
    - c_class (String)
    """
    occult_classes = [x.lower() for x in getattr(data, 'occult_classes')]
    available_classes = _available_class_pool(character)

    if isinstance(class_choice, str):
        # Lower-case for case-insensitivity, and turn the frontend's slug form (spaces -> hyphens,
        # e.g. "barbarian-(unchained)") back into the space-separated keys used in class_data
        # ("barbarian (unchained)"). No class name contains a hyphen, so this is safe. Without this
        # the four space-named classes (the Unchained variants) never matched and fell back to a
        # random class.
        class_choice = class_choice.lower().replace('-', ' ')

    if not class_choice in available_classes:
        available_classes_manip = ensure_BAB_and_caster_level(character, available_classes, "bab", chosen_BAB)
        available_classes_manip = ensure_BAB_and_caster_level(character, available_classes_manip, "casting level", chosen_caster_level)
        try:
            class_choice = random.choice(available_classes_manip)
        except:
            print("No classes available for the given BAB and caster level. Defaulting to a random class.")
            class_choice = random.choice(available_classes)

    # if no class is specified, allow for people to specify BAB and caster level

    # looping to ensure we don't have a class we don't want included
    while class_choice in occult_classes and class_choice not in available_classes:
        class_choice = random.choice(available_classes)

    # userInput_class = input(f'please type a class name to select a class, or type 0 for a random class: ').lower()
    userInput_class = class_choice.lower()
    character.c_class = userInput_class
    character.c_class_2 = ''

    all_classes = list(character.class_data.keys()) # + list(character.class_data["Path of War"].keys())

    if userInput_class not in all_classes:
        bab = random.choice(('H','M','L'))
        # bab = input('Enter bab (H/M/L): ').capitalize()
        character.bab = bab
        userInput_class = None

        if bab not in ('H','M','L'):
            bab = 'H'
            character.bab = 'H'

        classes = []
        for class_name in all_classes:
                if bab == "H" and character.class_data[class_name]["bab"] == "H":
                    classes.append(class_name)
                elif bab == "M" and character.class_data[class_name]["bab"] == "M":
                    classes.append(class_name)
                elif bab == "L" and character.class_data[class_name]["bab"] == "L":
                    classes.append(class_name)
    
        classes = list(all_classes)
        character.c_class = classes[randrange(0,len(classes))]
    # Display name for the FoundryVTT class item, captured BEFORE archetype_data() later strips
    # " (unchained)" for data lookups. .title() matches every_class.json exactly, e.g.
    # "barbarian (unchained)" -> "Barbarian (Unchained)", "fighter" -> "Fighter".
    character.c_class_display = character.c_class.title()
    return character.c_class


def ensure_BAB_and_caster_level(character, available_classes, BAB_or_caster_level, pre_chosen_bab = ['H', 'M', 'L']):
    chooseable_classes_bab = []
    if not isinstance(pre_chosen_bab, list):
        chosen_bab = [pre_chosen_bab.upper()]

    # print("chosen_bab", chosen_bab)
    if not isinstance(pre_chosen_bab, list) and BAB_or_caster_level not in ('bab'):
        pre_chosen_bab = ['none', 'low', 'mid', 'high']

    # print("pre_chosen_bab", pre_chosen_bab)

    for c in available_classes:
        # print("c.lower()", c.lower())
        if not character.class_data[c.lower()][str(BAB_or_caster_level)].upper() in chosen_bab:
            continue
        chooseable_classes_bab.append(c.lower())

    return chooseable_classes_bab

def _prune_class_pool(pool, picked):
    """Remove a picked class from the pool, plus its whole restricted group when the pick belongs
    to one (max 1 Path of War initiator class and max 1 Spheres class per character)."""
    pool = [c for c in pool if c != picked]
    for group in (data.path_of_war_class, getattr(data, 'spheres_classes', [])):
        if picked in group:
            pool = [c for c in pool if c not in group]
    return pool


def select_classes(character, class_choice, chosen_BAB, chosen_caster_level=None, multi_class='N'):
    """
    Pick the character's class NAMES. Slot 0 honors class_choice / chosen_BAB /
    chosen_caster_level exactly like the single-class path; when multiclassing, the class count is
    rolled with weights 2->50% / 3->35% / 4->15% and the extra slots draw unconstrained from the
    remaining pool (no duplicates, max 1 PoW initiator, max 1 Spheres class).

    Levels are NOT assigned here — randomize_level splits the rolled total level across
    character._class_picks (truncating the picks if the total is smaller than the count) and
    builds character.classes there.
    Returns
    - _class_picks (list of class-name strings, pick order preserved)
    """
    chooseClass(character, class_choice, chosen_BAB, chosen_caster_level)
    picks = [character.c_class]

    want_multi = isinstance(multi_class, str) and multi_class.lower() in ('y', 'yes')
    if want_multi:
        count = random.choices([2, 3, 4], weights=[50, 35, 15], k=1)[0]
        pool = _prune_class_pool(_available_class_pool(character), picks[0])
        while len(picks) < count and pool:
            picked = random.choice(pool)
            picks.append(picked)
            pool = _prune_class_pool(pool, picked)

    character._class_picks = picks
    return picks