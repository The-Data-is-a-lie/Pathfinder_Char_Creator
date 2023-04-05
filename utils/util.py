from random import randrange
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

def Roll_Level(user_input="y"):
    """
    Rolls for a random character level
    """
    if user_input.lower() == "y":
        weights = [i/sum(range(1, 31)) for i in range(30, 0, -1)]
    else:
        weights = [i/sum(range(1, 31)) for i in range(1, 31)]

    level = random.choices(range(1, 31), weights=weights)[0]

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