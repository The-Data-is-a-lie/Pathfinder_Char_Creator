from random import randrange
from math import floor
#importing stats in case we want to work on them
import random
from Backend.utils import data
from Backend.utils.data import traits, mannerisms, regions, weapon_groups, weapon_groups_region, disciplines, skills,  languages, hair_colors, hair_types, appearance, eye_colors, path_of_war_class#evil_deities, good_deities, neutral_deities,
import json
import sys
from Backend.utils.class_func.race_func import *


character_data = {}

def roll_dice(num_dice, num_sides):
    if not isinstance(num_dice, int):
        num_dice = 3
    if not isinstance(num_sides, int):
        num_sides = 6
    num_dice = max(20, num_dice)
    num_sides = max(20, num_sides)
    rolls = []
    for _ in range(num_dice):
        rolls.append(random.randint(1, num_sides))
    total = sum(rolls)   
    #print(f"{stat} = {total}")
    return total

def roll_inherent(sides,size):
    return random.randint(sides,size)
    

# def Roll_Level(high_level, low_level):
#     from main import filename
#     with open(filename, 'a') as f, open("utils/class.json", 'r') as c:
#         class_data = json.load(c)
#         """
#         Rolls for a random character level
#         """
#         # Prompt user for level range
#         if isinstance(high_level, int) and isinstance(low_level, int):
#             max_num = int(high_level)
#             min_num = int(low_level)
#         else:
#             max_num = 20
#             min_num = 1
#         level = random.randint(min_num, max_num)
#         return level


		# #randomized NPC level generator
        # npcInput = input('enable npc class levels (y/n)').lower()
        # npcEnabled = False
        # global npc_level
        # for npc_level in range(1, level):
        #     if random.randint(1, 100) >= 75 and npcInput == 'y':
        #         if not npcEnabled:
        #             npcEnabled = True
        #         npc_level += 1
        #         character_class_level = (level - npc_level)
        # else:
        #     character_class_level = level - npc_level
        
        # if npcEnabled:
        #     print(f'This is your number of npc levels: {npc_level}')
        #     print(f'This is your non-npc levels: {character_class_level}')
        #     print(f'This is your number of npc levels: {npc_level}',file=f)
        #     print(f'This is your non-npc levels: {character_class_level}',file=f)
        # elif npcInput == 'n':
        #     character_class_level = level
        #     print('No NPC class levels')
        #     print('No NPC class levels',file=f)
        #     npc_level = 0
        # else:
        #     print('Invalid input. Please enter "y" or "n".')
        #     npc_level = 0

        # # Creating a BAB total for printing out
        # if BAB == 'L':
        #     BAB_total = floor(character_class_level *.5) #+ floor(npc_level * .5)
        # elif BAB == 'M':
        #     BAB_total = floor(character_class_level *.75) #+ floor(npc_level * .5)
        # else: 
        #     BAB_total = character_class_level * 1 #+ floor(npc_level * .5)

            # end of npc class level macro

            #adding flaws to help calculate total feats

    #     print("this is the total character level ")
    #     print(level)
    #     print("this is the total character level ", file=f)
    #     print(level, file=f)
    #     global feats      
    #     if len(flaw) == 2 or len(flaw) == 3:
    #         feats = (4 + floor(level/2) + floor(level/5))
    #     elif len(flaw) == 4:
    #         #add 1 extra feat because of 2 extra flaws
    #         feats = (4 + 1 + floor(level/2) + floor(level/5))
    #     elif len(flaw) == 1:
    #         #remove 1 extra feat because of 1 less flaw
    #         feats = (4 - 1 + floor(level/2) + floor(level/5))
    #     else:
    #         #remove 2 extra feats because of no flaws
    #         feats = (4 - 2 + floor(level/2) + floor(level/5))
    # return feats

def region_chooser(character, userInput_region):
    """
    Characters either choose a region or randomly select one
    Return
    - region
    """
    print(f"Please make sure below matches this list: {character.first_names_regions.keys()}")
    regions = list(character.first_names_regions.keys())
    # userInput_region = input('Select region [input the number for the region you want] from above list: (0 = Random, 1=Tal-Falko, 2=Dolestan, 3=Sojoria, 4=Ieso, 5=Spire, 6=Feyador, 7=Esterdragon, 8=Grundykin Damplands, 9=Dust Cairn, 10=Kaeru no Tochi ...)').lower()
    if isinstance(userInput_region, int):
        userInput_region = int(userInput_region)
    if userInput_region in character.first_names_regions.keys():
        userInput_region = map_region_to_number(userInput_region)
        print("uuserInput_region: ", userInput_region)
    else:
        userInput_region = 0
    

    if isinstance(userInput_region, int) and int(userInput_region) <= len(regions):
        region_index = int(userInput_region) - 1
        region_selected = regions[region_index]        
        print('You have selected this region: ' + region_selected)
    else:
        region_index = random.randint(0,len(regions)-1)
        region_selected = regions[region_index]
        print('You have randomly selected this region: ' + region_selected)

    character.region = region_selected
    return character.region

def map_region_to_number(userInput_region):
    region_map = {
        "Random": 0,
        "Tal-Falko": 1,
        "Dolestan": 2,
        "Sojoria": 3,
        "Ieso": 4,
        "Spire": 5,
        "Feyador": 6,
        "Esterdragon": 7,
        "Grundykin Damplands": 8,
        "Dust-Cairn": 9,
        "Kaeru no Tochi": 10

    }
    return int(region_map[userInput_region])

def race_chooser(character, userInput_race):
    """
    Characters either choose a race, or randomly select one
    Return
    - userInput_race
    """
    race_data = full_race_data_func(character)
    race_data = list(race_data.keys())
    print(f'this is your race keys {race_data}')
    print('Select race from the above list: (or 0 if random)')
    if isinstance(userInput_race, str):
        userInput_race = capitalize_race_with_string(userInput_race)
    if userInput_race in race_data: 
        userInput_race = capitalize_race_with_string(userInput_race)
        print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! assign userInput_race: {userInput_race}')
    else:
        userInput_race = random.choice(race_data)
        userInput_race = capitalize_race_with_string(userInput_race)
        print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! assign userInput_race: {userInput_race}')
    character.chosen_race = userInput_race
    return character.chosen_race

def capitalize_race_with_string(userInput_race):
    words = userInput_race.split("-")
    for word in words:
        word = word.capitalize()
    return "-".join(words)
        
def gender_chooser(character, userInput_gender):
    """
    Characters either choose a gender, or randomly select one
    Return
    - userInput_gender
    """
    genders = ("Male", "Female")
    print('Select gender from the above list: (or 0 if random)')
    if isinstance(userInput_gender, str):
        userInput_gender = userInput_gender.capitalize()
    if userInput_gender in genders:
        print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! assign userInput_gender: {userInput_gender}')
    else:
        userInput_gender = random.choice(genders).capitalize()
        print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! assign userInput_gender: {userInput_gender}')
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
        print(f"Name for {character.region}: {character.f_name} {character.l_name}")

    else:
        # wehave this section in case of an emergency and region isn't selected. But this should never occur
        region_list = (list(f_name_list))
        region = random.choice(region_list)
        f_names = character.first_names_regions.get(region, "Tal-Falko").get(character.chosen_gender, "Nameless")
        l_names = character.last_names_regions[region]      
        character.f_name = random.choice(f_names)
        character.l_name = random.choice(l_names) 
        character.full_name = character.f_name + character.l_name
        print(f"Name for {character.region}: {character.f_name} {character.l_name}")

    return character.f_name, character.l_name




def weapon_chooser(character):
    """
    *** Probably want to change to generate based off of what weapons a class could actually use ***
    Characters are given random weapons selected by region and from all weapon groups
    Return
    - weaponz (by region random)
    - weapons (random)
    """
    # random.sample to select 2 random weapons
    weapons = random.sample(weapon_groups, 2)
    character.weapons = weapons
    print(f'weapons not dependent on region {weapons}')

    # loop through the random abilities and print out each element
    for reg in character.regions: #regions != region, they are very different, regions is defined in the data tab, region is the user input assigned as a number above
        if reg == character.region:
            weaponz = random.choice(weapon_groups_region[reg])
            character.weaponz = weaponz
            print(f"Weapon for {reg}: {weaponz}")

    
def chooseClass(character, class_choice):
    """
    Select a class or 
    Gives the Character a random class based off of BAB selection
    Returns
    - c_class (String)
    """
    # userInput_class = input(f'please type a class name to select a class, or type 0 for a random class: ').lower()
    all_classes = list(character.class_data.keys()) # + list(character.class_data["Path of War"].keys())
    # Temporarily removing psychic classes from random selection
    psychic_classes = ["psychic", "kineticist", "mediunm", "occultist", "spiritualist", "mesmerist"]
    for c in psychic_classes:
        if c in all_classes:
            all_classes.remove(c)

    print("this is the list of all classes", all_classes)
    if isinstance(class_choice, str) and class_choice.lower() in (all_classes):
        userInput_class = class_choice.lower()
    else:
        userInput_class = random.choice(all_classes)

    userInput_class = userInput_class.lower()

    character.c_class = userInput_class
    character.c_class_2 = ''

    # print(all_classes)

    character.c_class = not_in_classes(character, userInput_class, all_classes)

    return character.c_class

def not_in_classes(character, userInput_class, all_classes):
    if userInput_class not in all_classes:
        # old code from when we were doing random class by BAB
        # bab = input('Enter bab (H/M/L): ').capitalize()
    
        random_num = random.randint(1,3)
        if random_num == 1:
            bab = "H"
        elif random_num == 2:
            bab = "M"
        else:
            bab = "L"

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

    else:
        print(f"This is your only class: {character.c_class}")
            
    character.c_class_2 = c_class_2
    return character.c_class_2


def isBool(strBool: bool): return True if strBool == 'yes' or strBool == 'y' else False

def printAttributes(title: str, attributeList: list) -> None:
    print(f'\n{title}:', end=' ')
    
    for i in range(len(attributeList) - 1): print(f'{attributeList[i]}, ', end='')
    print(f'{attributeList[-1]}')

def appendAttr(attributeList: list, dataList: list):
    
    for attr in dataList: attributeList.append(attr)

def appendAttrData(attributeList: list, dataList):
    
    for attr in dataList: attributeList.append(attr)
    
    return attributeList[randrange(0, len(attributeList))]





def format_text(text, bold=False, color=None):
    """
    Format text with optional bold and color for HTML.
    
    Args:
        text (str): The input text.
        bold (bool): Whether to make the text bold.
        color (str): The color of the text (e.g., 'red', 'green', 'blue').

    Returns:
        str: The formatted HTML text.
    """
    style = []
    
    # Add CSS style for bold
    if bold:
        style.append('font-weight: bold')
    
    # Add CSS style for color
    if color:
        style.append(f'color: {color}')
    
    # Create HTML span element with inline style
    if style:
        return f'<span style="{"; ".join(style)}">{text}</span>'
    else:
        return text


    

#updating Character data

# character_data.update({"level": level})
# character_data.update({"feats": feats})
# character_data.update({"BAB": BAB})
# character_data.update({"race": c_race})
# character_data.update({"weapons_no_region": weapons})
# character_data.update({"weapons": weaponz})
# character_data.update({"luck": luck_score})
# character_data.update({"mythic": mythic_rank})
# character_data.update({"class": c_class})
# character_data.update({"class_secondary": c_class_2})
# character_data.update({"flaws": flaw})

#


