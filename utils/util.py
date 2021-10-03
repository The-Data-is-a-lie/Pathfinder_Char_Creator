from random import randrange
from utils import data

def RollStat():
    """
    Rolls a series of random numbers between 1 - 7 and adds them together
    - Returns
    - Total (Integer)
    """
    dice = []
    for i in range(4):
        dice.append(randrange(1,7))

    total = 0
    lowest = dice[0]

    for num in dice:
        if num < lowest:
            lowest = num

    for num in dice:
        total += num

    return total - lowest

def chooseClass():
    """
    Gives the Character a random Class 
    - Returns
    - Class (String)
    """
    classes = []

    for _class in data.classes:
        classes.append(_class)
    
    c_class = classes[randrange(0,len(classes))]
    return c_class

def chooseRace():
    """
    Gives the Character a random Race
    - Returns
    - Race (String)
    """
    races = []
    for race in data.races:
        races.append(race)

    c_race = races[randrange(0,len(races))]
    return c_race


def isBool(strBool):
	if strBool == "yes" or strBool == "y":
		return True
	else:
		return False