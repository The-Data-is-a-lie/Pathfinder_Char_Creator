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
    pre_races = list(race_data.keys())
    races = []
    for race in pre_races:
        races.append(race.title())
        
    if not isinstance(userInput_race, str) or not userInput_race.title() in races: 
        userInput_race = random.choice(races).capitalize()
    else:
        userInput_race = userInput_race.title()
    character.chosen_race = userInput_race
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

    
def chooseClass(character, class_choice, chosen_BAB, chosen_caster_level=None):
    """
    Select a class or 
    Gives the Character a random class based off of BAB selection
    Returns
    - c_class (String)
    """
    # temporarily removing occult classes (they aren't ready yet)
    occult_classes = [x.lower() for x in getattr(data, 'occult_classes')]
    path_of_war_class = [x.lower() for x in getattr(data, 'path_of_war_class')]
    available_classes = list(character.class_data.keys())
    #remove occult classes
    available_classes = [x for x in available_classes if x not in occult_classes]
    available_classes = [x for x in available_classes if x not in path_of_war_class]

    if isinstance(class_choice, str):
        # To handle incorrectly cased class names
        class_choice = class_choice.lower()

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
    while (class_choice in occult_classes or class_choice in path_of_war_class) and class_choice not in available_classes:
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

def dip_function(character, base_classes, multi_class = False):
    """
    Determines if you want to have multiple classes for a character, or only one
    Returns 
    -c_class_2 (string)
    """
    available_classes = getattr(data,base_classes)
    classes = list(character.class_data.keys())
    # userInput_multiclass = input('Do you want to multiclass Y/N')
    userInput_multiclass = multi_class
    
    c_class_2 = ''
    if userInput_multiclass.lower() == 'y' or userInput_multiclass == 'yes':
        chance_dip = random.randint(0,100)
        if chance_dip >= 50:
            c_class_2 = random.choice(classes.lower())
        else:
            c_class_2 = random.choice(classes.lower())
            character.dip = True
            
    character.c_class_2 = c_class_2
    return character.c_class_2