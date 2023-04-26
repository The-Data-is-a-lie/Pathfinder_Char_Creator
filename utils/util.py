from random import randrange
from math import floor
#importing stats in case we want to work on them

import random
from utils import data
from utils.data import traits, mannerisms, regions, weapon_groups, weapon_groups_region, archetypes, disciplines, skills, evil_deities, good_deities, neutral_deities, languages, hair_colors, hair_types, appearance, eye_colors, path_of_war_class
import json
#from utils.race import race

def roll_dice(num_dice, num_sides, stat, name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f:
        rolls = []
        for i in range(num_dice):
            rolls.append(random.randint(1, num_sides))
        total = sum(rolls)
        #print(f"{stat} = {total}")
        return total

def roll_inherent(sides,size):
    return random.randint(sides,size)
    

def Roll_Level(name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f, open("utils/class.json", 'r') as c:
        class_data = json.load(c)
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
        global level
        global feats
        global character_class_level
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
            character_class_level = level
            print('No NPC class levels')
        else:
            print('Invalid input. Please enter "y" or "n".')

            # end of npc class level macro
        print("this is the total character level ")
        print(level)
        print("this is the total character level ", file=f)
        print(level, file=f)        
        feats = (4 + floor(level/2) + floor(level/5))
                    
                                                                      
 
    
def chooseClass(name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f, open("utils/race.json", "r") as r, open("last_names_regions.json", "r") as a, open("first_names_regions.json", "r") as g, open("utils/class.json", "r") as c:
        """
        Gives the Character a random Class 
        - Returns
        - Class (String)
        """
        #grabbing race + class + region data from the json files
        race_data = json.load(r)
        class_data = json.load(c)
        first_names_region = json.load(a)
        last_names_region = json.load(g) 
        # Prompt the user to input BAB
        global BAB
        BAB = input('Enter BAB (H/M/L): ').capitalize()
        global userInput_race
        global userInput_region
        # Prompt the user to select a region
        print(f"Please make sure below matches this list: {first_names_region.keys()}")

        userInput_region = input('Select region [input the number for the region you want] from above list: (1=Tal-falko, 2=Dolestan, 3=Sojoria, 4=Ieso, 5=Spire, 6=Feyador, 7=Esterdragon, 8=Grundykin Damplands, 9=Dust Cairn, 10=Kaeru no Tochi ...)').lower()
        print(race_data.keys())
        userInput_race = input(f'Select race from the above list: ').capitalize()
        print(userInput_race)
        if userInput_region.isdigit() and int(userInput_region) in range(1, 30):
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
        for reg in regions: #regions != region, they are very different, regions is defined in the data tab, region is the user input assigned as a number above
                if reg == region:
                    weaponz = random.choice(weapon_groups_region[reg])
                    print(f"Weapon for {reg}: {weaponz}")
                    print(f"Weapon for {reg}: {weaponz}", file=f)  

        
  

        if region in first_names_region:
            f_names = first_names_region[region]
            f_name = random.choice(f_names)
            l_names = last_names_region[region]
            l_name = random.choice(l_names) 
            print(f"Name for {region}: {f_name} {l_name}")    
            print(f"Name for {region}: {f_name} {l_name}", file=f)        


        # Iterate through the classes and select the ones that meet the BAB requirement
        classes = []
        global class_name
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

 
        global c_class
        # Select a random class from the list of eligible classes
        print(f'These are the classes available to get {classes}')
        c_class = classes[randrange(0,len(classes))]
        return c_class

def path_of_war(name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f, open("utils/class.json", "r") as c:
        from utils.util import feats, c_class
        class_data = json.load(c)
        global path
        path=0
        chance = random.randint(1,100)
        chance_2 = random.randint(1,100)
        if c_class not in path_of_war_class:
                if class_data[class_name]["BAB"] == 'high':
                    if chance >= 25:
                        path = 1
                        print('this is how many path of war abiities they take ')
                        print('this is how many path of war abiities they take ', file = f)
                        print(path)
                        print(path, file = f)                    
                        if chance_2 >= 75:
                            path = 2
                            print('this is how many path of war abiities they take ')
                            print('this is how many path of war abiities they take ', file = f)
                            print(path)
                            print(path, file = f)
                        return path
                elif class_data[class_name]["BAB"] == 'mid':
                    if chance >= 50:
                        path = 1
                        print(path)
                        if chance_2 >= 90:
                            path = 2
                            print('this is how many path of war abiities they take ')
                            print('this is how many path of war abiities they take ', file = f)
                            print(path)
                            print(path, file = f)
                        return path            

                    else:
                        if chance >= 90:
                            path = 1
                            print('this is how many path of war abiities they take ')
                            print('this is how many path of war abiities they take ', file = f)
                            print(path)
                            print(path, file = f)
                            return path
                        
                #path of War section (calculates amount of path of war for later)
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


def various_racial_attr(name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f, open("utils/class.json", 'r') as c, open("utils/race.json", 'r') as r:
            race_data = json.load(r)
            if userInput_race in race_data:
                racial_traits = race_data[userInput_race]["traits"]
                racial_language = race_data[userInput_race]["languages"]
                racial_size = race_data[userInput_race]["size"]
                racial_speed = race_data[userInput_race]["speed"]
                ability_scores = race_data[userInput_race]["ability scores"]  

                print(f"Ability Scores for {userInput_race} {ability_scores}")
                print(f"Ability Scores for {userInput_race} {ability_scores}", file=f)
                print(f"Racial traits: {racial_traits}")
                print(f"Racial traits: {racial_traits}",file=f)
                print(f"racial languages: {racial_language}")
                print(f"racial languages: {racial_language}",file=f)
                print(f"racial size: {racial_size}")
                print(f"racial size: {racial_size}",file=f)
                print(f"racial speed: {racial_speed}")
                print(f"racial speed: {racial_speed}",file=f)
                


def age_weight_height(name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f, open("utils/class.json", 'r') as c, open("utils/race.json", 'r') as r:
            race_data = json.load(r)
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
        #random weight roll
            if "weight" in race_data[userInput_race]:
                weight = race_data[userInput_race]["weight"]
            if isinstance(weight[1], str):
                left, right = map(int, weight[1].split('d'))
                weight_roll = sum([random.randint(1, right) for i in range(left)]) + weight[0]
            else:
                weight_roll = random.randint(weight[0], weight[1])
                left = weight[0]
            weight_roll += left
            print(f"weight: {weight_roll}")
            print(f"weight: {weight_roll}", file=f)
        #random height roll
            if "height" in race_data[userInput_race]:
                height = race_data[userInput_race]["height"]
            if isinstance(height[1], str):
                left, right = map(int, height[1].split('d'))
                height_roll = sum([random.randint(1, right) for i in range(left)]) + height[0]
            else:
                height_roll = random.randint(height[0], height[1])
                left = height[0]
            height_roll += left
            print(f"height: {height_roll}")
            print(f"height: {height_roll}", file=f)


def inherent_stats(name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f, open("utils/class.json", 'r') as c:
        inherent = int(floor(level/2))
        global stats
        stats = 0
        for x in range(inherent):
            roll = random.randint(0, 100)
            if 10 >= roll >= 0:
                stats += roll_inherent(1,2) - 1
            elif 20 >= roll > 10:
                stats += 1
            elif 30 >= roll > 20:
                stats += roll_inherent(1,2)
            elif 40 >= roll > 30:
                stats += roll_inherent(1,2) + 1
            elif 50 >= roll > 40:
                stats += roll_inherent(1,3) + 1
            elif 60 >= roll > 50:
                stats += roll_inherent(1,4) + 1
            elif 70 >= roll > 60:
                stats += roll_inherent(2,2) + 1
            elif 80 >= roll > 70:
                stats += roll_inherent(2,3) + 1
            elif 90 >= roll > 80:
                stats += roll_inherent(2,4)
            elif 99 >= roll > 90:
                stats += roll_inherent(2,4) + 1
            elif roll == 100:
                stats += roll_inherent(2,4) + 2
        
        print(f"this is your total inherent stat buff: {stats}")
        print(f"this is your total inherent stat buff: {stats}",file=f)        
                #end of inherent stats roller   


def Total_Hitpoint_Calc(name):
    from createACharacter import c_const, c_str, c_dex, c_int, c_wisdom, c_char
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f, open("utils/class.json", 'r') as c:
        class_data = json.load(c)
                       # Class Hit Dice + total Hit points
        Hit_dice = class_data[c_class]["hp"]
        print(f"hit dice {Hit_dice}")
            #Total HP before NPC class
        Pre_NPC_HP = Hit_dice * (character_class_level)
        print(f"Pre-NPC HP {Pre_NPC_HP}")
        Post_NPC_HP = 6 * (level-character_class_level)
        global Total_HP
        Total_Class_level_HP = Pre_NPC_HP + Post_NPC_HP   
        print(f"This is your characters total HP based off of class levels + NPC LEVELS (no stats): {Total_Class_level_HP}")
        print(f"This is your characters total HP based off of class levels + NPC LEVELS (no stats): {Total_Class_level_HP}",file=f)         
        Total_HP = Total_Class_level_HP + (level * floor((c_const-10)/2))
        print(f"This is your characters total HP: {Total_HP}")




def appearnce_func(name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f, open("utils/class.json", 'r') as c:
        #Potentially add a charactersitics by region section
        hair_color_choice = random.choice(hair_colors)
        hair_type_choice = random.choice(hair_types)
        eye_color_choice = random.choice(eye_colors)
        random_app_number = random.randint(1,3)
        appearance_choice = random.sample(appearance,k=random_app_number)

        print(f'hair_colors' + '\n', hair_color_choice)
        print(f'hair_types' + '\n', hair_type_choice)
        print(f'eye_colors' + '\n', eye_color_choice)
        print(f'appearance' + '\n', appearance_choice)

        print(f'hair_colors' + '\n', hair_color_choice,file=f)
        print(f'hair_types' + '\n', hair_type_choice,file=f)
        print(f'eye_colors' + '\n', eye_color_choice,file=f)
        print(f'appearance' + '\n', appearance_choice,file=f)




def personality_and_profession(name):
        from createACharacter import traits_abilities
        from utils.data import mannerisms, traits
        filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
        with open(filename, 'a') as f, open("utils/race.json", "r") as r, open("utils/class.json", "r") as c, open("utils/traits_abilities.json") as t, open("utils/profession.json") as p:
            profession_data = json.load(p)
            traits_abilities = json.load(t)
            # use random.sample to select 3 random professions 
            professions = profession_data['Profession']
            random_professions = random.sample(professions, 3)
            # loop through the random abilities and print out each element
            for proforce in random_professions:
                print(f'(profession):',proforce)
                print(f'(profession):', proforce, file=f )


            # use random.sample to select 8 random abilities
            random_abilities = random.sample(traits_abilities, 8)
            # loop through the random abilities and print out each element
            for ability in random_abilities:
                print(f'(ability traits):',ability)
                print(f'(ability traits):',ability, file=f)

            # use random.sample to select 5 random personality traits
            random_personality = random.sample(traits, 5)
            # loop through the random abilities and print out each element
            for personality in random_personality:
                print(f'(personality traits):',personality)
                print(f'(personality traits):',personality, file=f)

            # use random.sample to select 3 random mannerisms
            random_mannerisms = random.sample(mannerisms, 3)
            # loop through the random abilities and print out each element
            for manners in random_mannerisms:
                print(f'(mannerisms):',manners)
                print(f'(mannerisms):',manners, file=f)



def alignment_deities_and_skills(name):
        from createACharacter import c_skills, c_alignment
        filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
        with open(filename, 'a') as f:
            print(f'Skills' + '\n', c_skills, file=f)
            print(f'Skills' + '\n', c_skills)

            # Printing out additional 1-4 random class
            skill_list = random.choices(skills, k=4)
            print(f'Specialized Skills {skill_list}')
            print(f'Specialized Skills {skill_list}', file=f)

            #print out alignment + physical characteristics
            print(f'Alignment' + '\n', c_alignment)
            print(f'Alignment' + '\n', c_alignment, file=f)
        
            #deciding deity based off of aligment
            if 'good' in c_alignment:
                chosen_deity = random.choice(good_deities)
                print(f"Deity \n {chosen_deity}",file=f)
                print(f"Deity \n {chosen_deity}") 
            elif 'evil' in c_alignment:
                chosen_deity = random.choice(evil_deities)            
                print(f"Deity \n {chosen_deity}",file=f)
                print(f"Deity \n {chosen_deity}")
            else:
                chosen_deity = random.choice(neutral_deities)            
                print(f"Deity \n {chosen_deity}",file=f)
                print(f"Deity \n {chosen_deity}")

            random_number = random.randint(1,5)
            extra_lang = random.sample(languages,k=random_number)
            print(f"These are the extra languages the character knows: {extra_lang}")
            print(f"These are the extra languages the character knows: {extra_lang}", file=f)



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
