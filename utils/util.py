from random import randrange
from math import floor
import random
from utils import data
from utils.data import regions, weapon_groups_region, weapon_groups, archetypes, disciplines
import json
#from utils.race import race

def RollStat():
    """
    Rolls a series of random numbers between 1 - 7 and adds them together
    - Returns
    - Total (Integer)
    """
    
    dice = []
    for i in range(4): dice.append(randrange(1,7))

    total = 0
    lowest = dice[0]

    for num in dice:
        if num < lowest: lowest = num

    for num in dice: total += num

    return total - lowest

def roll_dice(num_dice, num_sides, stat, name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f:
        rolls = []
        for i in range(num_dice):
            rolls.append(random.randint(1, num_sides))
        total = sum(rolls)
        #print(f"{stat} = {total}")
        return total


def Roll_Level(name):
    from createACharacter import path
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f:
        """
        Rolls for a random character level
        """
        # Prompt user for level range
        max_num = int(input("Enter the highest level you want the char to be: "))
        min_num = int(input("Enter the lowest level you want the char to be: "))

        # Calculate weights based on level range
        user_input = input("this is the weights: y = higher levels, n = lower levels (y/n): ")
        if user_input.lower() == "y":
            weights = [i/sum(range(min_num, max_num+1)) for i in range(max_num, min_num-1, -1)]
            weights = [round(i/sum(weights)*len(weights)) for i in weights]
        else:
            weights = [1 for i in range(min_num, max_num+1)]

        # Roll for level using weights
        level = random.choices(range(min_num, max_num+1), weights=weights)[0]

		#randomized NPC level generator
        npcInput = input('enable npc class levels (y/n)').lower()
        npcEnabled = False
        for x in range(1, level):
            if random.randint(1, 100) >= 75 and npcInput == 'y':
                if not npcEnabled:
                    npcEnabled = True
                x += 1
                character_class_level = (level - x)
        else:
            character_class_level = level - x

        if npcEnabled:
            print(f'This is your number of npc levels: {x}')
            print(f'This is your non-npc levels: {character_class_level}')
            print(f'This is your number of npc levels: {x}',file=f)
            print(f'This is your non-npc levels: {character_class_level}',file=f)
        elif npcInput == 'n':
            print('No NPC class levels')
        else:
            print('Invalid input. Please enter "y" or "n".')

            # end of npc class level macro
        print("this is the total character level ")
        print(level)
        print("this is the total character level ", file=f)
        print(level, file=f)        
        feats = (4 + floor(level/2) + floor(level/5))
                    
        if path == 0:
            feats = feats - 0
        elif 7 > level >= 3 and path == 1:
            feats = feats-1
        elif 11 > level >= 7 and path == 1:
            feats = feats-2
        elif level >= 11 and path == 1:
            feats = feats-3        
        elif 7 > level >= 3 and path == 2:
            feats = feats-2
        elif 11 > level >= 7 and path == 2:
            feats = feats-4 
        elif level >= 11 and path == 2:
            feats = feats-6           

        #adding an additional option where we print disciplines for the people to get (we can add functionality so it's based off of region later)
        #to make it based off of region, we simply just do what we did with weapons_region_group, ...
        if path == 1:
            disciplines_choice = random.choice(disciplines)
            print(disciplines_choice)
            print(disciplines_choice,file=f)
        elif path == 2:
            disciplines_choice=random.sample(disciplines,k=2)
            print(disciplines_choice)
            print(disciplines_choice,file=f)

        extra_ability_score_levels = floor(level/4)
        print ("This is the number of bonus feats per level ")
        print(feats)
        print ("This is the number of bonus feats per level ", file=f)        
        print(feats, file=f)
        print ("number of bonus ability scores from levels ")        
        print(extra_ability_score_levels)
        print ("number of bonus ability scores from levels ", file=f)        
        print(extra_ability_score_levels, file=f)        
        return level                 
        # end of npc level generator

    

def chooseClass(name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f, open("utils/race.json", "r") as r, open("first_names_regions.json", "r") as a, open("first_names_regions.json", "r") as g, open("utils/class.json", "r") as c:
        """
        Gives the Character a random Class 
        - Returns
        - Class (String)
        """
        # Prompt the user to input BAB
        BAB = input('Enter BAB (H/M/L): ').capitalize()
        
        # Prompt the user to select a region
        userInput_region = input('Select region [input the number for the region you want] (1=Tal-falko, 2=Dolestan, 3=Sojoria, 4=Ieso, 5=Spire, 6=Feyador, 7=Esterdragon, 8=Grundykin Damplands, 9=Dust Cairn, 10= ...)').lower()
        userInput_race = input('Select race (e.g. Goblin, Human, Drow, ...)').capitalize()
        print(userInput_race)
        if userInput_region.isdigit() and int(userInput_region) in range(1, 10):
            # make sure max range = the number of regions we have
            region_index = int(userInput_region) - 1
            # if you want to add regions, make sure to add them in the data section as well
            region = regions[region_index]
            print('You have selected this region: ' + region)
            print('You have selected this region: ' + region, file=f)
        else:
            print('You have selected no region.')
            print('You have selected no region.', file=f)

        if userInput_race == 'Human':
            print('Humans get an extra feat ')  

        # random.sample to select 2 random weapons
        weapons = random.sample(weapon_groups, 2)
        print(f'weapons not dependent on region {weapons}')
        print(f'weapons not dependent on region {weapons}', file=f)
        # loop through the random abilities and print out each element
        for reg in regions:
                if reg == region:
                    weaponz = random.choice(weapon_groups_region[reg])
                    print(f"Weapon for {reg}: {weaponz}")
                    print(f"Weapon for {reg}: {weaponz}", file=f)  

        
        first_names_region = json.load(a)
        last_names_region = json.load(g)   

        if region in first_names_region:
            f_names = first_names_region[region]
            f_name = random.choice(f_names)
            l_names = last_names_region[region]
            l_name = random.choice(l_names) 
            print(f"Name for {region}: {f_name} {l_name}")    
            print(f"Name for {region}: {f_name} {l_name}", file=f)        


        # Iterate through the classes and select the ones that meet the BAB requirement
        classes = []
        race_data = json.load(r)
        class_data = json.load(c)
        for class_name in class_data.keys():
            if region in class_data[class_name]["regions"] and userInput_race in class_data[class_name]["race"]:
                # Check BAB input + region input
                if BAB == "H" and class_data[class_name]["BAB"] == "high":
                    classes.append(class_name)
                elif BAB == "M" and class_data[class_name]["BAB"] == "mid":
                    classes.append(class_name)
                elif BAB == "L" and class_data[class_name]["BAB"] == "low":
                    classes.append(class_name)
                else:
                    # Ignore classes that don't meet the BAB requirement
                    continue

        # added this in to print out ability score adjustments per race
        
        if userInput_race in race_data:
            ability_scores = race_data[userInput_race]["ability scores"]
            print(f"Ability Scores for {userInput_race}")
            print(f"Ability Scores for {userInput_race}", file=f)
            
            for score, value in ability_scores.items():
                print(f"{score}: {value}")

         #added this in to print out a random age for the character
            if "age" in race_data[userInput_race]:
                age = race_data[userInput_race]["age"]
            if isinstance(age[1], str):
                left, right = map(int, age[1].split('d'))
                age_roll = sum([random.randint(1, right) for i in range(left)]) + age[0]
            else:
                age_roll = random.randint(age[0], age[1])
                left = age[0]
            age_roll += left
            print(f"Age: {age_roll}")
            print(f"Age: {age_roll}", file=f)
           
 
        
        

        # Select a random class from the list of eligible classes
        print(f'These are the classes available to get {classes}')
        c_class = classes[randrange(0,len(classes))]
        return c_class

def chooseRace():
    """
    Gives the Character a random Race
    - Returns
    - Race (String)
    """
    
    races = []
    for race in data.races: races.append(race)

    c_race = races[randrange(0,len(races))]
    return c_race

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









# we don't use these anymore:

def Roll_Level_40(user_input="y"):
    """
    Rolls for a random character level
    """
    "1-40"
    if user_input.lower() == "y":
        weights = [i/sum(range(1, 41)) for i in range(40, 0, -1)]
    else:
        weights = [i/sum(range(1, 41)) for i in range(1, 41)]

    level = random.choices(range(1, 41), weights=weights)[0]

    return level

def Roll_Level_30(user_input="y"):
    """
    Rolls for a random character level
    """
    "1-30"
    if user_input.lower() == "y":
        weights = [i/sum(range(1, 31)) for i in range(30, 0, -1)]
    else:
        weights = [i/sum(range(1, 31)) for i in range(1, 31)]

    level = random.choices(range(1, 31), weights=weights)[0]

    return level

def Roll_Level_20(user_input="y"):
    """
    Rolls for a random character level
    """
    "1-20"
    if user_input.lower() == "y":
        weights = [i/sum(range(1, 21)) for i in range(20, 0, -1)]
    else:
        weights = [i/sum(range(1, 21)) for i in range(1, 21)]

    level = random.choices(range(1, 21), weights=weights)[0]

    return level

def Roll_Level_10(user_input="y"):
    """
    Rolls for a random character level
    """
    "1-10"
    if user_input.lower() == "y":
        weights = [i/sum(range(1, 11)) for i in range(10, 0, -1)]
    else:
        weights = [i/sum(range(1, 11)) for i in range(1, 11)]

    level = random.choices(range(1, 11), weights=weights)[0]

    return level

def Roll_Level_5(user_input="y"):
    """
    Rolls for a random character level
    """
    "1-5"
    if user_input.lower() == "y":
        weights = [i/sum(range(1, 6)) for i in range(5, 0, -1)]
    else:
        weights = [i/sum(range(1, 6)) for i in range(1, 6)]

    level = random.choices(range(1, 6), weights=weights)[0]

    return level