#Internal Imports
from utils import data
from utils.util import RollStat, chooseClass
from utils.markdown import style

#Extention Modules:
from modules.currency import runCurrency
from modules.deities import runDeities
from modules.extraDetail import runExtraDetail

#External Imports
from random import randrange
import sys

# Base Character Traits
class Character:
    c_strength = 10
    c_dexterity = 10
    c_constitution = 10
    c_intelligence = 10
    c_wisdom = 10
    c_charisma = 10

    c_race = "Placeholder"
    c_class = "Placeholder"
    c_firstname = "Placeholder"
    c_lastname = "Placeholder"
    c_weapon = ["Dagger"]
    c_armor = ["Cloth shirt"]
    c_skills = ["Placeholder"]
    c_abilities = ["Placeholder"]
    c_spells = ["None"]
    c_hp = 1

    c_languages = ["Common"]
    c_saving_throws = []
    c_racial_traits = []
    c_size = "Medium"
    c_traits = []
    c_background = "outlander"

    def __str__(self):
        return f"Name: {self.c_firstname} ({self.c_race} {self.c_class})"

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

        for name in data.races[new_char.c_race]['first names'][type]:
            firstnames.append(name)

        for name in data.races[new_char.c_race]['last names'][type]:
            lastnames.append(name)

    elif new_char.c_race == "Half-Elf":
        types = []

        for type in data.races['Human']['first names']:
            types.append(type)

        type = types[randrange(0,len(types))]

        for name in data.races['Human']['first names'][type]:
            firstnames.append(name)

        for name in data.races['Elf']['first names']:
            firstnames.append(name)

        for name in data.races['Human']['last names'][type]:
            lastnames.append(name)

        for name in data.races['Elf']['last names']:
            lastnames.append(name)

    else:
        for name in data.races[new_char.c_race]['first names']:
            firstnames.append(name)

        if new_char.c_race == "Half-Orc":
            pass
        else:
            for name in data.races[new_char.c_race]['last names']:
                lastnames.append(name)

    new_char.c_firstname = firstnames[randrange(0,len(firstnames))]

    if new_char.c_race != "Half-Orc":
        new_char.c_lastname = lastnames[randrange(0,len(lastnames))]

    new_char.c_strength = RollStat()
    new_char.c_dexterity =  RollStat()
    new_char.c_constitution = RollStat()
    new_char.c_intelligence = RollStat()
    new_char.c_wisdom = RollStat()
    new_char.c_charisma = RollStat()

    weapons = []
    armors = []

    for weapon in data.classes[new_char.c_class]['weapons']:
        weapons.append(weapon)

    new_char.c_weapon = weapons[randrange(0,len(weapons))]

    for armor in data.classes[new_char.c_class]['armor']:
        armors.append(armor)

    new_char.c_armor = armors[randrange(0,len(armors))]

    new_char.c_skills = data.classes[new_char.c_class]['skills']

    if 'spells' in data.classes[new_char.c_class]:
        new_char.c_spells =  data.classes[new_char.c_class]['spells']

    new_char.c_abilities =  data.classes[new_char.c_class]['abilities']
    new_char.c_languages = ["Common"]
    new_char.c_languages += data.races[new_char.c_race]['languages']
    new_char.c_racial_traits = data.races[new_char.c_race]['traits']
    new_char.c_background = data.classes[new_char.c_class]['background']

    mannerisms = []
    for mannerism in mannerisms:
        mannerisms.append(mannerism)
    new_char.c_mannerisms = data.mannerisms[randrange(0,len(data.mannerisms))]

    traits = []
    for trait in traits:
        traits.append(trait)
    new_char.c_traits = data.traits[randrange(0,len(data.traits))]

    talents = []
    for talent in talents:
        talents.append(talent)
    new_char.c_talent = data.talents[randrange(0,len(data.talents))]

    appearances = []
    for appearance in data.appearance:
        appearances.append(appearance)
    new_char.c_appearance = appearances[randrange(0,len(appearances))]

    deityList = []
    for deity in data.deities:
      deityList.append(deity)
    new_char.c_deity = deityList[randrange(0,len(deityList))]

    if new_char.c_race == "Half-Orc":
        print(f"Name: {new_char.c_firstname} ({new_char.c_race} {new_char.c_class})")

    elif new_char.c_race == "Elf":
        print(f"Name: {new_char.c_firstname} {new_char.c_lastname} ({new_char.c_race} {new_char.c_class})")

    elif new_char.c_race == "Dragonborn":
      print(f"Name: {new_char.c_firstname} of the clan {new_char.c_lastname} ({new_char.c_race} {new_char.c_class})")
    else:
        print(f"Name: {new_char.c_firstname} {new_char.c_lastname} ({new_char.c_race} {new_char.c_class})")

    print(f"Strength: {new_char.c_strength}\nDexterity: {new_char.c_dexterity}\nConstitution: {new_char.c_constitution} \nIntelligence: {new_char.c_intelligence}\nWisdom: {new_char.c_wisdom}\nCharisma: {new_char.c_charisma}")

    print(f"\nBackground: {new_char.c_background}\n")

    print(f"Languages: ", end='')
    for i in range(len(new_char.c_languages)):
    	print(f"{new_char.c_languages[i]}, ", end='')

    print(f"\nWeapon: {new_char.c_weapon}\nArmor: {new_char.c_armor}\n")

    print("Skills: ", end='')
    for i in range(len(new_char.c_skills)):
    	print(f"{new_char.c_skills[i]}, ", end='')

    print("\nAbilities: ", end='')
    for i in range(len(new_char.c_abilities)):
      print(f"{new_char.c_abilities[i]}, ", end='')

    print(f"\nSpells: ", end='')
    for i in range(len(new_char.c_spells)):
      print(f"{new_char.c_spells[i]}, ", end='')

    print("\nTraits: ", end='')
    for i in range(len(new_char.c_racial_traits)):
      print(f"{new_char.c_racial_traits[i]}, ", end='')
    print(f"\n")

    print("===============================================================")

    moduleChecking = "modules.extraDetail"
    if moduleChecking in sys.modules:
        print(style.BOLD+"Extra Details Module:\n"+style.END)
        runExtraDetail()
    else:
        pass

    moduleChecking = "modules.currency"
    if moduleChecking in sys.modules:
        print(style.BOLD+"Currency Module:\n"+style.END)
        runCurrency()
    else:
        pass

    moduleChecking = "modules.deities"
    if moduleChecking in sys.modules:
        print(style.BOLD+"Deities Module:\n"+style.END)
        runDeities()
    else:
        pass
