from random import randrange
from math import floor
import random
from utils import data

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


        print("this is the character level ")
        print(level)
        print("this is the character level ", file=f)
        print(level, file=f)        
        feats = (5 + floor(level/2) + floor(level/5))
       
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

def chooseClass():
    """
    Gives the Character a random Class 
    - Returns
    - Class (String)
    """
    
    classes = []

    for _class in data.classes: classes.append(_class)
    
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