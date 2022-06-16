#Internal Imports
from utils.data import *

#External Imports
from random import randrange

def charAge():
    '''
    Gives the Character a Random Age from 0 - 100
    - Returns
    - Age (Integer)
    '''
    age = randrange(0, 100)
    print(f'Age: {age}')

def randomTalent():
    '''
    Gives the Character a Random Talent
    - Returns
    - Talent (String)
    '''
    Talent = talents[randrange(0,len(talents))]
    print(f'Talents: {Talent}')

def hairType():
    '''
    Gives the Character a Random Hair Type
    - Returns
    - HairType (String)
    '''
    hair_type = hair_types[randrange(0,len(hair_types))]
    print(f'Hair Type: {hair_type}')

def hairColor():
    '''
    Gives the Character a Random Hair Color
    - Returns
    - HairColor (String)
    '''
    hair_color = hair_colors[randrange(0,len(hair_colors))]
    print(f'Hair Color: {hair_color}')

def eyeColor():
    '''
    Gives the Character a Random Eye Color
    - Returns
    - EyeColor (String)
    '''
    eye_color = eye_colors[randrange(0,len(eye_colors))]
    print(f'Eye Color: {eye_color}')

def randomManner():
    '''
    Gives the Character a Random Eye Color
    - Returns
    - EyeColor (String)
    '''
    manner = mannerisms[randrange(0,len(mannerisms))]
    print(f'Mannerism(s): {manner}\n')

def randomAppearance():
    '''
    Gives the Character a Random Appearance
    - Returns
    - EyeColor (String)
    '''
    Appearance = appearance[randrange(0,len(appearance))]
    print(f'Appearance: {Appearance}')

def ExtraDetail():
    '''
    Runs All Functions in a module
    '''
    charAge()
    randomTalent()
    hairType()
    hairColor()
    eyeColor()
    randomAppearance()
    randomManner()

