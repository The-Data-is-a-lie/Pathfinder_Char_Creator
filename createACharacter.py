#Internal Imports
from utils import data
from utils.util import RollStat, chooseClass,  appendAttr, appendAttrData #printAttributes,
from utils.markdown import style
import random

#Extension Modules:
from modules.extraDetail import ExtraDetail
from modules.currency import Currency
from modules.deities import Deities

#External Imports
from random import randrange
import sys

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
    c_name = 'Placeholder'
    c_surname = 'Placeholder'
    
    c_weapon = ['Dagger']
    c_armor = ['Cloth shirt']
    
    c_skills = ['Placeholder']
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



def CreateNewCharacter(name):
    filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
    with open(filename, 'a') as f:

        new_char = Character()

        races = []
        classes = []

        for race in data.races:
            races.append(race)

        for _class in data.classes:
            classes.append(_class)

        new_char.c_class = classes[randrange(0,len(classes))]

        new_char.c_race = races[randrange(0,len(races))]
        new_char.c_class = chooseClass()

        forenames = []
        surnames = []

        if new_char.c_race == 'Human':
            types = []

            for type in data.races['Human']['first names']:
                types.append(type)

            type = types[randrange(0,len(types))]

            appendAttr(forenames, data.races[new_char.c_race]['first names'][type])
            appendAttr(surnames, data.races[new_char.c_race]['last names'][type])

        elif new_char.c_race == 'Half-Elf':
            types = []

            for type in data.races['Human']['first names']:
                types.append(type)

            type = types[randrange(0,len(types))]

            appendAttr(forenames, data.races['Human']['first names'][type])
            appendAttr(surnames, data.races['Human']['last names'][type])
            appendAttr(forenames, data.races['Elf']['first names'])
            appendAttr(surnames, data.races['Elf']['last names'])

        else:
            for name in data.races[new_char.c_race]['first names']:
                forenames.append(name)

            if new_char.c_race == 'Half-Orc': pass
            else:
                for name in data.races[new_char.c_race]['last names']: 
                    surnames.append(name)

        new_char.c_name = forenames[randrange(0,len(forenames))]

        if new_char.c_race != 'Half-Orc': new_char.c_surname = surnames[randrange(0,len(surnames))]

        new_char.c_str = RollStat()
        new_char.c_dex =  RollStat()
        new_char.c_const = RollStat()
        new_char.c_int = RollStat()
        new_char.c_wisdom = RollStat()
        new_char.c_char = RollStat()

        weapons = []
        armors = []

        appendAttr(weapons, data.classes[new_char.c_class]['weapons'])
        appendAttr(armors, data.classes[new_char.c_class]['armor'])

        new_char.c_weapon = weapons[randrange(0,len(weapons))]
        new_char.c_armor = armors[randrange(0,len(armors))]
        new_char.c_skills = data.classes[new_char.c_class]['skills']
        new_char.c_langs = ['Common']
        new_char.c_langs += data.races[new_char.c_race]['languages']
        new_char.c_racial_traits = data.races[new_char.c_race]['traits']

        mannerisms = []
        new_char.c_mannerisms = appendAttrData(mannerisms, data.mannerisms)

        traits = []
        new_char.c_traits = appendAttrData(traits, data.traits)

        profession = []
        new_char.c_profession = appendAttrData(profession, data.profession)

        appearances = []
        new_char.c_appearance = appendAttrData(appearances, data.appearance)

        deityList = []
        new_char.c_deity = appendAttrData(deityList, data.deities)

        traits_abilities = []
        new_char.c_traits_abilities = appendAttrData(traits_abilities, data.traits_abilities)

        weapon_groups = []
        new_char.c_weapon_groups = appendAttrData(weapon_groups, data.weapon_groups)

        match new_char.c_race:
            case 'Half-Orc': print(f'Name: {new_char.c_name} ({new_char.c_race} {new_char.c_class})\n', file=f)
            case 'Half-Orc': print(f'Name: {new_char.c_name} ({new_char.c_race} {new_char.c_class})\n')            

            case 'Elf': print(f'Name: {new_char.c_name} {new_char.c_surname} ({new_char.c_race} {new_char.c_class})\n', file=f)
            case 'Elf': print(f'Name: {new_char.c_name} {new_char.c_surname} ({new_char.c_race} {new_char.c_class})\n')            

            case 'Dragonborn': print(f'Name: {new_char.c_name} of the clan {new_char.c_surname} ({new_char.c_race} {new_char.c_class})\n', file=f)
            case 'Dragonborn': print(f'Name: {new_char.c_name} of the clan {new_char.c_surname} ({new_char.c_race} {new_char.c_class})\n')

            case _: print(f'Name: {new_char.c_name} {new_char.c_surname} ({new_char.c_race} {new_char.c_class})\n', file=f)
            


        
        print(f'Strength: {new_char.c_str}\nDexterity: {new_char.c_dex}', file=f)
        print(f'Constitution: {new_char.c_const} \nIntelligence: {new_char.c_int}', file=f)
        print(f'Wisdom: {new_char.c_wisdom}\nCharisma: {new_char.c_char}' + '\n', file=f )

        print(f'Languages' + '\n', new_char.c_langs, file=f)
        print(f'Skills' + '\n', new_char.c_skills, file=f)
        print(f'Traits' + '\n', new_char.c_racial_traits, file=f)

        print(f'Strength: {new_char.c_str}\nDexterity: {new_char.c_dex}')
        print(f'Constitution: {new_char.c_const} \nIntelligence: {new_char.c_int}')
        print(f'Wisdom: {new_char.c_wisdom}\nCharisma: {new_char.c_char}')

        print(f'Languages' + '\n', new_char.c_langs)
        print(f'Skills' + '\n', new_char.c_skills)
        print(f'Traits' + '\n', new_char.c_racial_traits)



        # use random.sample to select 3 random professions 
        random_professions = random.sample(profession, 3)
        # loop through the random abilities and print out each element
        for proforce in random_professions:
            print(f'(profession):', proforce, file=f )


        # use random.sample to select 8 random abilities
        random_abilities = random.sample(traits_abilities, 8)
        # loop through the random abilities and print out each element
        for ability in random_abilities:
            print(f'(ability traits):',ability, file=f)

        # use random.sample to select 5 random personality traits
        random_personality = random.sample(traits, 5)
        # loop through the random abilities and print out each element
        for personality in random_personality:
            print(f'(personality traits):',personality, file=f)

        # use random.sample to select 3 random mannerisms
        random_mannerisms = random.sample(mannerisms, 3)
        # loop through the random abilities and print out each element
        for manners in random_mannerisms:
            print(f'(mannerisms):',manners, file=f)

        # yse random.sample to select 2 random weapons
        weapons = random.sample(weapon_groups, 2)
        # loop through the random abilities and print out each element
        for weapun in weapons:
            print(f'(weapon groups):',weapun, file=f)        

                # Copy + paste so it prints to the terminal as well as the output file
                
        # use random.sample to select 3 random professions 
        random_professions = random.sample(profession, 3)
        # loop through the random abilities and print out each element
        for proforce in random_professions:
            print(f'(profession):',proforce)

        # use random.sample to select 8 random abilities
        random_abilities = random.sample(traits_abilities, 8)
        # loop through the random abilities and print out each element
        for ability in random_abilities:
            print(f'(ability traits):',ability)

        # use random.sample to select 5 random personality traits
        random_personality = random.sample(traits, 5)
        # loop through the random abilities and print out each element
        for personality in random_personality:
            print(f'(personality traits):',personality)

        # use random.sample to select 3 random mannerisms
        random_mannerisms = random.sample(mannerisms, 3)
        # loop through the random abilities and print out each element
        for manners in random_mannerisms:
            print(f'(mannerisms):',manners)

        # yse random.sample to select 2 random weapons
        weapons = random.sample(weapon_groups, 2)
        # loop through the random abilities and print out each element
        for weapun in weapons:
            print(f'(weapon groups):',weapun)  
        print('===============================================================')

        match sys.modules:
            case 'modules.extraDetail':
                print(style.BOLD+'Extra Details Module:\n'+style.END)
                ExtraDetail()

            case 'modules.currency':
                print(style.BOLD+'Currency Module:\n'+style.END)
                Currency()
                
            case 'modules.deities':
                print(style.BOLD+'Deities Module:\n'+style.END)
                Deities()

            case _:
                pass

            