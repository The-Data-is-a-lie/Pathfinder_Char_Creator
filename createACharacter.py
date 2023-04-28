#Internal Imports
from utils import data
import json
from utils.data import regions, weapon_groups_region, archetypes, skills, evil_deities, good_deities, neutral_deities, languages, hair_colors, hair_types, appearance, eye_colors, path_of_war_class
#from utils.data import archetypes
from utils.util import  chooseClass, appendAttrData, roll_dice#,  Roll_Level#,roll_4d6, roll_dice #printAttributes,
from utils.markdown import style
import random

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
        num_dice = int(input("How many dice would you like to roll? "))
        num_sides = int(input("How many sides should each die have? "))

        #declare con as global so we cna work with it
        
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
    
        #prints stats
        print(f'Strength: {new_char.c_str}\nDexterity: {new_char.c_dex}', file=f)
        print(f'Constitution: {new_char.c_const} \nIntelligence: {new_char.c_int}', file=f)
        print(f'Wisdom: {new_char.c_wisdom}\nCharisma: {new_char.c_char}' + '\n', file=f )
        print(f'Strength: {new_char.c_str}\nDexterity: {new_char.c_dex}')
        print(f'Constitution: {new_char.c_const} \nIntelligence: {new_char.c_int}')
        print(f'Wisdom: {new_char.c_wisdom}\nCharisma: {new_char.c_char}')


        # Randomly Assigning archetypes:
        #need to add an if statement like above to check if it's a tuple or not
       # char_class = c_class.lower()
       # selected_archetype = random.choice(archetypes[char_class])
       # print('this is the randomly selected archetype' +  '\n' + selected_archetype + '\n' + ' for this class' + '\n' + char_class)
        
            #selected_archetype = random.choice(archetypes.eval("archetypes_{new_char.c_class.lower()}"))


        #    print(f"This is the selected archetype for {new_char.c_class}: + {selected_archetype}")



            
        print('===============================================================')

            