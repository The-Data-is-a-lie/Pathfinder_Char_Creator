from random import randrange
from math import floor
#importing stats in case we want to work on them
import random
from utils import data
from utils.data import traits, mannerisms, regions, weapon_groups, weapon_groups_region, disciplines, skills,  languages, hair_colors, hair_types, appearance, eye_colors, path_of_war_class#evil_deities, good_deities, neutral_deities,
import json
import sys
#from utils.race import race
character_data = {}

def roll_dice(num_dice, num_sides):
    rolls = []
    for _ in range(num_dice):
        rolls.append(random.randint(1, num_sides))
    total = sum(rolls)   
    #print(f"{stat} = {total}")
    return total

def roll_inherent(sides,size):
    return random.randint(sides,size)
    

def Roll_Level():
    from main import filename
    with open(filename, 'a') as f, open("utils/class.json", 'r') as c:
        class_data = json.load(c)
        """
        Rolls for a random character level
        """
        # Prompt user for level range
        max_num = int(input("Enter the highest level you want the char to be: "))
        min_num = int(input("Enter the lowest level (minimum 2) you want the char to be: "))
        level = random.randint(min_num, max_num)


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

def region_chooser(character):
    """
    Characters either choose a region or randomly select one
    Return
    - region
    """
    print(f"Please make sure below matches this list: {character.first_names_regions.keys()}")
    userInput_region = input('Select region [input the number for the region you want] from above list: (0 = Random, 1=Tal-falko, 2=Dolestan, 3=Sojoria, 4=Ieso, 5=Spire, 6=Feyador, 7=Esterdragon, 8=Grundykin Damplands, 9=Dust Cairn, 10=Kaeru no Tochi ...)').lower()
    character.userInput_region = userInput_region
    

    if userInput_region.isdigit() and int(userInput_region) in range(1, 30):
        region_index = int(userInput_region) - 1
        region = character.regions[region_index]        
        print('You have selected this region: ' + region)
    elif int(userInput_region) == 0:
        region_index = random.randint(0,9)
        region = character.regions[region_index]
        print('You have randomly selected this region: ' + region)
    else:
        print('You have selected no region.')
        region = ''
    character.region = region

def race_chooser(character):
    """
    Characters either choose a race, or randomly select one
    Return
    - userInput_race
    """
    races = list(character.races.keys())
    print(races)
    userInput_race = input(f'Select race from the above list: (or 0 if random)').capitalize()
    if userInput_race in races:
        print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! assign userInput_race: {userInput_race}')
        character.chosen_race = userInput_race
    else:
        userInput_race = random.choice(races)
        character.chosen_race = userInput_race
        print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! assign userInput_race: {userInput_race}')
        

def name_chooser(character):
    """
    Randomly generates names by region
    Return
    - f_name, l_name, full_name
    """
    f_name_list = list(character.first_names_regions)
    l_name_list = list(character.last_names_regions)

    if character.region in f_name_list:
        f_names = character.first_names_regions[character.region]
        l_names = character.last_names_regions[character.region]        
        character.f_name = random.choice(f_names)
        character.l_name = random.choice(l_names) 
        character.full_name = character.f_name + character.l_name
        print(f"Name for {character.region}: {character.f_name} {character.l_name}")

    else:
        # wehave this section in case of an emergency and region isn't selected. But this should never occur
        region_list = (list(f_name_list.keys()))
        region = random.choice(region_list)
        f_names = random.choice(f_name_list(region))
        l_names = random.choice(l_name_list(region))
        character.f_name = random.choice(f_names)
        character.l_name = random.choice(l_names) 
        character.full_name = character.f_name + character.l_name
        print(f"Name for {character.region}: {character.f_name} {character.l_name}")        




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

    
def chooseClass(character):
    """
    Select a class or 
    Gives the Character a random class based off of BAB selection
    Returns
    - c_class (String)
    """
    userInput_class = input(f'please type a class name to select a class, or type 0 for a random class: ').lower()
    print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! assign userInput_class: {userInput_class}')
    character.c_class = userInput_class
    character.c_class_2 = ''

    if userInput_class not in character.class_data.keys():
        bab = input('Enter bab (H/M/L): ').capitalize()
        character.bab = bab
        userInput_class = None

        if bab not in ('H','M','L'):
            bab = 'H'
            character.bab = 'H'

        classes = []
        for class_name in character.class_data.keys():
                if bab == "H" and character.class_data[class_name]["bab"] == "H":
                    classes.append(class_name)
                elif bab == "M" and character.class_data[class_name]["bab"] == "M":
                    classes.append(class_name)
                elif bab == "L" and character.class_data[class_name]["bab"] == "L":
                    classes.append(class_name)
    
        classes = list(character.class_data.keys())
        character.c_class = classes[randrange(0,len(classes))]



def dip_function(character, base_classes):
    """
    Determines if you want to have multiple classes for a character, or only one
    Returns 
    -c_class_2 (string)
    """
    available_classes = getattr(data,base_classes)
    classes = list(character.class_data.keys())
    userInput_multiclass = input('Do you want to multiclass Y/N')
    c_class_2 = ''
    if userInput_multiclass.lower() == 'y' or userInput_multiclass == 'yes':
        chance_dip = random.randint(0,100)
        if chance_dip >= 50:
            c_class_2 = random.choice(classes)
        else:
            c_class_2 = random.choice(classes)
            character.dip = True

    else:
        print(f"This is your only class: {character.c_class}")
            
    character.c_class_2 = c_class_2


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


