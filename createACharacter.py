#Internal Imports
from utils import data
import json
from utils.data import regions, weapon_groups_region, skills, evil_deities, good_deities, neutral_deities, languages, hair_colors, hair_types, appearance, eye_colors, path_of_war_class
#from utils.data import archetypes
from utils.util import  format_text, chooseClass, appendAttrData, roll_dice#,  Roll_Level#,roll_4d6, roll_dice #printAttributes,
from utils.markdown import style
import random
import sys


#External Imports
from random import randrange

# Base Character Traits
class Character:
    c_str = 10
    c_dex = 10
    c_const = 10
    c_int = 10
    c_wisdom = 10
    c_char = 10

    c_race = 'Placeholder'
    c_class = 'Placeholder'

    
    c_weapon = ['Dagger']
    c_armor = ['Cloth shirt']
    
    c_skills = ['Placeholder']
    c_skills_2 = ['Placeholder']
    c_spells = ['None']
    c_hp = 1

    c_langs = ['Common']
    
    c_saving_throws = []
    c_racial_traits = []
    
    c_size = 'Medium'
    c_traits = []
    
    c_bg = 'outlander'
    c_mannerisms = ''

    def __str__(self): return f'Name: {self.c_name} ({self.c_race} {self.c_class})'


def CreateNewCharacter():
    from main import filename
    with open(filename, 'a') as f, open("utils/race.json", "r") as r, open("utils/class.json", "r") as c, open("utils/traits_abilities.json") as t, open("utils/profession.json") as p:
        profession_data = json.load(p)
        race_data = json.load(r)
        class_data = json.load(c)
        traits_data = json.load(t)

        global c_const, c_str, c_dex, c_int, c_wisdom, c_char
        global traits_abilities
        global c_alignment
        global c_langs
        global c_skills, c_skills_2
        global new_char_c_class

        new_char = Character()

        races = []
        classes = []

        for race in race_data:
            races.append(race)

        for _class in class_data:
            classes.append(_class)

        new_char.c_class = chooseClass()
        new_char_c_class = new_char.c_class

                        #this is where we change the stat rolls:
        print(style.BLACK + f"drop the lowest roll for each one" + style.END)
        num_dice = int(input("How many dice would you like to roll? "))
        num_sides = int(input("How many sides should each die have? "))

        #declare con as global so we can work with it
        
        c_str = roll_dice(num_dice, num_sides, 'Strength')
        c_dex = roll_dice(num_dice, num_sides, 'Dexterity')
        c_const = roll_dice(num_dice, num_sides, 'Constitution')
        c_int = roll_dice(num_dice, num_sides, 'Intelligence')
        c_wisdom = roll_dice(num_dice, num_sides, 'Wisdom')
        c_char = roll_dice(num_dice, num_sides, 'Charisma')


        new_char.c_str = c_str
        new_char.c_dex = c_dex
        new_char.c_const = c_const
        new_char.c_int = c_int
        new_char.c_wisdom = c_wisdom                                
        new_char.c_char = c_char




        c_langs = ['Common']
        new_char.c_langs = c_langs
        #c_class is now a tuple sometimes, so we need to be able to work with if it is
        #c_bab = class_data[new_char.c_class[0]]['BAB']
        #c_bab = class_data[new_char.c_class[1]]['BAB']

        #Creating character traits, (mannerisms, traits, profession, appearances, alignment, + traits_Abilities so we can print them out later
        mannerisms = []
        new_char.c_mannerisms = appendAttrData(mannerisms, data.mannerisms)

        traits = []
        new_char.c_traits = appendAttrData(traits, data.traits)

        Alignment = []
        c_alignment = appendAttrData(Alignment, data.alignment)
        new_char.c_alignment = c_alignment

        traits_abilities = []
        new_char.c_traits_abilities = appendAttrData(traits_abilities, traits_data)
    

        #pre formatting stats:
        global formatted_charisma, formatted_constitution, formatted_dexterity, formatted_intelligence, formatted_strength, formatted_wisdom
        # formatted_strength = format_text(f'Strength: {new_char.c_str}', bold=True, color="red")
        # formatted_dexterity = format_text(f'Dexterity: {new_char.c_dex}', bold=True, color="red")
        # formatted_constitution = format_text(f'Constitution: {new_char.c_const}', bold=True, color="red")
        # formatted_intelligence = format_text(f'Intelligence: {new_char.c_int}', bold=True, color="red")
        # formatted_wisdom = format_text(f'Wisdom: {new_char.c_wisdom}', bold=True, color="red")
        # formatted_charisma = format_text(f'Charisma: {new_char.c_char}', bold=True, color="red")

        formatted_strength = new_char.c_str
        formatted_dexterity = new_char.c_dex
        formatted_constitution = new_char.c_const
        formatted_intelligence = new_char.c_int
        formatted_wisdom = new_char.c_wisdom
        formatted_charisma = new_char.c_char

        global character_data
        character_data = {}
        # #Adding stats to the overall Character Dictionary
        # #Physical stats
        character_data.update({"str": formatted_strength, "dex": formatted_dexterity, "con": formatted_constitution}) 
        # #Mental stats
        character_data.update({"int": formatted_intelligence, "wis": formatted_wisdom, "cha": formatted_charisma})



        #Print into Char Sheet
        print(formatted_strength,file=f)
        print(formatted_dexterity,file=f)
        print(formatted_constitution,file=f)
        print(formatted_intelligence,file=f)
        print(formatted_wisdom,file=f)
        print(formatted_charisma,file=f)
        #Print into Terminal
        print(formatted_strength)
        print(formatted_dexterity)
        print(formatted_constitution)
        print(formatted_intelligence)
        print(formatted_wisdom)
        print(formatted_charisma)









            
        print('===============================================================')

            