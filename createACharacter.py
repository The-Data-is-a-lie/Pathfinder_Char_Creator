#Internal Imports
from utils import data
from utils.util import RollStat, chooseClass, printAttributes, appendAttr, appendAttrData
from utils.markdown import style

#Extention Modules:
from modules.currency import Currency
from modules.deities import Deities
from modules.extraDetail import ExtraDetail

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
    c_abilities = ['Placeholder']
    c_spells = ['None']
    c_hp = 1

    c_langs = ['Common']
    c_saving_throws = []
    c_racial_traits = []
    c_size = 'Medium'
    c_traits = []
    c_bg = 'outlander'

    def __str__(self):
        return f'Name: {self.c_name} ({self.c_race} {self.c_class})'

def CreateNewCharacter():
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

    firstnames = []
    lastnames = []

    if new_char.c_race == 'Human':
        types = []

        for type in data.races['Human']['first names']:
            types.append(type)

        type = types[randrange(0,len(types))]

        appendAttr(firstnames, data.races[new_char.c_race]['first names'][type])
        appendAttr(lastnames, data.races[new_char.c_ract]['last names'][type])

    elif new_char.c_race == 'Half-Elf':
        types = []

        for type in data.races['Human']['first names']:
            types.append(type)

        type = types[randrange(0,len(types))]

        appendAttr(firstnames, data.races['Human']['first names'][type])
        appendAttr(lastnames, data.races['Human']['last names'][type])
        appendAttr(firstnames, data.races['Elf']['first names'])
        appendAttr(lastnames, data.races['Elf']['last names'])

    else:
        for name in data.races[new_char.c_race]['first names']:
            firstnames.append(name)

        if new_char.c_race == 'Half-Orc':
            pass
        else:
            for name in data.races[new_char.c_race]['last names']:
                lastnames.append(name)

    new_char.c_name = firstnames[randrange(0,len(firstnames))]

    if new_char.c_race != 'Half-Orc':
        new_char.c_surname = lastnames[randrange(0,len(lastnames))]

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

    if 'spells' in data.classes[new_char.c_class]:
        new_char.c_spells =  data.classes[new_char.c_class]['spells']

    new_char.c_abilities = data.classes[new_char.c_class]['abilities']
    new_char.c_langs = ['Common']
    new_char.c_langs += data.races[new_char.c_race]['languages']
    new_char.c_racial_traits = data.races[new_char.c_race]['traits']
    new_char.c_background = data.classes[new_char.c_class]['background']

    mannerisms = []
    appendAttrData(mannerisms, new_char.c_mannerisms)

    traits = []
    appendAttrData(traits, new_char.c_traits)

    talents = []
    appendAttrData(talents, new_char.c_talent)

    appearances = []
    appendAttrData(appearances, new_char.c_appearance)

    deityList = []
    appendAttrData(deityList, new_char.c_deity)

    match new_char.c_race:
        case 'Half-Orc':
            print(f'Name: {new_char.c_name} ({new_char.c_race} {new_char.c_class})')

        case 'Elf':
            print(f'Name: {new_char.c_name} {new_char.c_surname} ({new_char.c_race} {new_char.c_class})')

        case 'Dragonborn':
            print(f'Name: {new_char.c_name} of the clan {new_char.c_surname} ({new_char.c_race} {new_char.c_class})')

        case _:
            print(f'Name: {new_char.c_name} {new_char.c_surname} ({new_char.c_race} {new_char.c_class})')

    print(f'Strength: {new_char.c_str}\nDexterity: {new_char.c_dex}\n')
    print(f'Constitution: {new_char.c_const} \nIntelligence: {new_char.c_intelligence}\n')
    print(f'Wisdom: {new_char.c_wisdom}\nCharisma: {new_char.c_charisma}')

    print(f'\nBackground: {new_char.c_background}\n')

    printAttributes('Languages', new_char.c_langs)
    printAttributes('Skills', new_char.c_skills)
    printAttributes('Abilities', new_char.c_abilities)
    printAttributes('Spells', new_char.c_spells)
    printAttributes('Traits', new_char.c_racial_traits)

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