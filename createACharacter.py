#Internal Imports
from utils import data
from utils.data import regions, weapon_groups_region
#from utils.data import archetypes
from utils.util import RollStat, chooseClass,  appendAttr, appendAttrData, roll_dice#,  Roll_Level#,roll_4d6, roll_dice #printAttributes,
from utils.markdown import style
import random

#Extension Modules:
from modules.extraDetail import ExtraDetail
from modules.currency import Currency
from modules.deities import Deities

#External Imports
from random import randrange
import sys


path_of_war_class = ['Warder', 'Harbinger', 'Mystic', 'Zealot', 'Stalker']
archetypes = {

'fighter': ['Tribal Defender', 'Biathlete', 'Road Warrior', 'Aether Soldier', 'Warmachine', 'Harrier', 'Knife Fighter', 'Man-at-Arms', 'Berserker', 'Chain Lasher', 'Challenger', 'Bonded Pet', 'Blade Shifter', 'Technique Master', 'Ironborn', 'Myrmidon', 'Silverblade Hunter', 'Swordsmith', 'Chakram Dervish', 'Quickblade', 'Spellscorn Fighter', 'Coachman', 'Tjuman', 'Pugilist', 'Ructioneer', 'Warrior of the Path', 'Scrapper', 'Aerial Assaulter', 'Spear Fighter', 'Skirmisher', 'Tribal Fighter', 'Venomblade', 'Viking', 'Aquanaut', 'Armiger', 'Defender', 'Lore Warden', 'High Guardian', 'Opportunist Fighter', 'Cyber-Soldier', 'Unbreakable', 'Phalanx Soldier', 'Gladiator', 'Gloomblade', 'Archer', 'Armor Master', 'Blackjack', 'Border Defender', 'Brawler', 'Buckler Duelist', 'Cad', 'Child of War', 'Corsair', 'Crossbowman', 'Dervish of Dawn', 'Dragonheir Scion', 'Dragoon', 'Drill Sergeant', 'Eldritch Guardian', 'Free Hand Fighter', 'Free-Style Fighter', 'Learned Duelist', 'Titan Fighter', 'Seasoned Commander', 'Martial Master', 'Mobile Fighter', 'Mutation Warrior', 'Pack Mule', 'Polearm Master', 'Relic Master', 'Roughrider', 'Savage Warrior', 'Sensate', 'Shielded Fighter', 'Siegebreaker', 'Steelbound Fighter', 'Swordlord', 'Tactician', 'Thunderstriker', 'Tower Shield Specialist', 'Trench Fighter', 'Two-Handed Fighter', 'Two-Weapon Warrior', 'Unarmed Fighter', 'Vengeful Hunter', 'Viking', 'Weapon Bearer Squire', 'Weapon Master', 'Warshade', 'Kappa-Bushi', 'Peltast', 'Tengubushi', 'Yakuza Bushi', 'Dragon Warrior']
,
#
'barbarian': ['Armored Hulk','Beastkin Berserker','Blooded Arcanist','Breaker','Brutal Pugilist','Cannibal','Chaos Totem','Dreadnought','Elemental Kin','Fated Champion','Feral Gnasher','Flesheater','Furyborn','Goliath Druid','Hateful Rager','Hurler','Invulnerable Rager','Lion Blade','Marauder','Mooncursed','Mounted Fury','Pack Rager','Primal Hunter','Primalist','Raging Cannibal','Raging Cyclone','Raging Drunk','Raging Flame','Raging Hurler','Raging Tactician','Savage Barbarian','Scarred Rager','Sea Reaver','Shaman','Skeletal Champion','Spell Sunderer','Steel-Breaker','Superstitious','Survivor','Titan Mauler','Totem Warrior','True Primitive','Unchained Rager','Urban Barbarian','Wild Rager']
,
#
'druid': ['Agathiel', 'Animal Shaman', 'Aquatic Druid', 'Arboreal Grappler', 'Archdruid', 'Blacksnake', 'Blazoned Tracker', 'Blight Druid', 'Blind Singer', 'Blightwarden', 'Child of the Moon', 'Cleric of the Green', 'Death Druid', 'Defender of the True World', 'Dragon Shaman', 'Dreamspeaker', 'Elemental Ally', 'Elemental Ascetic', 'Elemental Druid', 'Emberkin', 'Enlightened Druid', 'Fanglord', 'Feral Child', 'Fey Caller', 'Fist of the Forest', 'Flame Keeper', 'Frostburn Warden', 'Geisha', 'Geomancer', 'Green Faith Acolyte', 'Green Scourge', 'Greenstalker', 'Guardian of the Wild', 'Harrow Warden', 'Hedge Witch', 'Hooded Champion', 'Ice Sentinel', 'Infiltrator', 'Inquisitor of the Elk', 'Inquisitor of the Raven', 'Inquisitor of the Water', 'Jungle Druid', 'Lion Shaman', 'Lithic', 'Mad Prophet', 'Mammoth Rider', 'Master of Many Forms', 'Master of Storms', 'Mooncaller', 'Mooncursed', 'natures Fang', 'natures Whispers', 'Nature-Bonded Magus', 'Necrologist', 'Pack Lord', 'Pain Taster', 'Pale Stranger', 'Plant Master', 'Polar Midnight', 'Powerful Shapechanger', 'Rage Prophet', 'Ravenlord', 'Reincarnated Druid', 'River Druid', 'Saurian Shaman', 'Sea Reaver', 'Serpent-Fire Adept', 'Serpentfire', 'Shark Shaman', 'Shapeshifter', 'Shark Shaman', 'Storm Druid', 'Stormwalker', 'Street Shaman', 'Swamp Druid', 'Tamer of Beasts', 'Teisatsu', 'Theologian', 'Thornwarden', 'Thundercaller', 'Totemic Demonslayer', 'Tribal Shaman', 'Tunnel Rat', 'Undead Lord', 'Urban Druid', 'Verdant Lord', 'Verminous Hunter', 'Visionary Seeker', 'Volcano Priest', 'Vulture Shaman', 'Warshaper', 'Wild Rager', 'Wild Whisperer', 'Wildfire Heart', 'Winter Witch', 'Wolf Shaman', 'Woodland Skirmisher', 'World Walker', 'Wyrm Singer' ]
,
#
'cleric': ['Angelfire Apostle',  'Aquatic Druid', 'Arcanist', 'Atheist', 'Battle Priest', 'Chaos Channeler', 'Cloistered Cleric', 'Crusader', 'Divine Strategist', 'Evangelist', 'Exalted', 'Feral Hunter', 'Inheritors Crusader', 'Liturgical Mage', 'Merciful Healer', 'Necromancer', 'Planar Oracle', 'Ravener Hunter', 'Sanguine Angel', 'Separatist', 'Shaman', 'Theologian', 'Undead Lord', 'Varisian Pilgrim', 'Visionary Prophet']
,
#
'rogue':  ['Acrobat', 'Bandit', 'Beastmaster', 'Beguiler', 'Burglar', 'Charlatan', 'Chirurgeon', 'Circus Performer', 'Cloaked Dancer', 'Cloistered Cleric', 'Commando', 'Con Artist', 'Counterfeit Mage', 'Court Fool', 'Cutpurse', 'Daggermark Poisoner', 'Dandy', 'Dark Delver', 'Deep Walker', 'Demagogue', 'Dervish of Dawn', 'Eldritch Scoundrel', 'False Medium', 'Fast Hands', 'Gang Leader', 'Gloomblade', 'Guerrilla', 'Guild Agent', 'Guild Poisoner', 'Hidden Priest', 'Highwayman', 'Hooded Champion', 'Infiltrator', 'Knife Master', 'Liberator', 'Master Spy', 'Mouser', 'Natural Alchemist', 'Noble Fencer', 'Phantom Thief', 'Pilferer', 'Pirate', 'Poisoner', 'Rake', 'Rapscallion', 'Ratcatcher', 'Ringleader', 'Saboteur', 'Sandman', 'Sapper', 'Savage Skirmisher', 'Scavenger', 'Scout', 'Shadowdancer', 'Shadow Rager', 'Sleuth', 'Sniper', 'Spy', 'Stalker', 'Streetfighter', 'Survivalist', 'Swordmaster', 'Thief Acrobat', 'Thug', 'Trapsmith', 'Underground Chemist', 'Vexing Dodger', 'Vigilante', 'Wasp', 'Watersinger', 'Wild Child', 'Zealot']
,
#
'ranger':  ['Airborne Ambusher', 'Arboreal Ranger', 'Battle Scout', 'Beastmaster', 'Blightwarden', 'Bow Nomad', 'Cavalier', 'Child of Acavna and Amaznen', 'Deep Walker', 'Divine Marksman', 'Dragon Hunter', 'Duskwarden', 'Falconer', 'Favored Enemy (aquatic)', 'Favored Enemy (dungeon)', 'Favored Enemy (forest)', 'Favored Enemy (giant)', 'Favored Enemy (magical beast)', 'Favored Enemy (plant)', 'Favored Enemy (undead)', 'Frost Tusk', 'Geomancer', 'Ghost Hunter', 'Giant Killer', 'Guide', 'Harrow Warden', 'Hooded Champion', 'Horse Lord', 'Horizon Walker', 'Infiltrator', 'Initiate of the Hunt', 'Liberator', 'Lion Blade', 'Living Monolith', 'Master of Many Forms', 'Natural Warrior', 'Nature Warden', 'Pack Lord', 'Pathfinder Chronicler', 'Polearm Master', 'Reaper of Secrets', 'Sable Company Marine', 'Savage Skirmisher', 'Sea Dog', 'Skirmisher', 'Stormwalker', 'Strider', 'Swift Hunter', 'Terramancer', 'Thundercaller', 'Trapper', 'Treantmonk (Druid/Ranger)', 'Trick Shot', 'Trickster', 'Two-Handed Fighter', 'Urban Ranger', 'Verdant Sorcerer', 'Wild Shadow', 'Wild Stalker', 'Witch Hunter', 'Woodland Skirmisher', 'World Walker']
,
#
#
'paladin' : ['Angelic', 'Blade of Mercy', 'Chosen One', 'Divine Defender', 'Divine Guardian', 'Divine Hunter', 'Divine Paragon', 'Divine Scion', 'Divine Servitor', 'Divine Strategist', 'Enlightened Paladin', 'Eternal Hope', 'Gray Paladin', 'Holy Gun', 'Hospitaler', 'Oathbound Paladin', 'Oath of Vengeance', 'Paladin of Freedom', 'Sacred Servant', 'Shining Knight', 'Templar']

#
#
}



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
        new_char.c_class = chooseClass(name)

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

                                #this is where we change the stat rolls:
        num_dice = int(input("How many dice would you like to roll? "))
        num_sides = int(input("How many sides should each die have? "))

        new_char.c_str = roll_dice(num_dice, num_sides, 'Strength', name)
        new_char.c_dex = roll_dice(num_dice, num_sides, 'Dexterity', name)
        new_char.c_const = roll_dice(num_dice, num_sides, 'Constitution', name)
        new_char.c_int = roll_dice(num_dice, num_sides, 'Intelligence', name)
        new_char.c_wisdom = roll_dice(num_dice, num_sides, 'Wisdom', name)
        new_char.c_char = roll_dice(num_dice, num_sides, 'Charisma', name)

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
        c_bab = data.classes[new_char.c_class]['BAB']

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

        Alignment = []
        new_char.c_alignment = appendAttrData(Alignment, data.alignment)

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

# comment this out later

        print(f'Deities' + '\n', new_char.c_deity)
        print(f'Alignment' + '\n', new_char.c_alignment)
#        print(f'hair_colors' + '\n', new_char.c_hair_colors)
#        print(f'hair_types' + '\n', new_char.c_langs)
#        print(f'eye_colors' + '\n', new_char.c_skills)
#        print(f'appearance' + '\n', new_char.c_racial_traits)

        print(f'Deities' + '\n', new_char.c_deity, file=f)
        print(f'Alignment' + '\n', new_char.c_alignment, file=f)
#        print(f'hair_colors' + '\n', new_char.c_hair_colors)
#        print(f'hair_types' + '\n', new_char.c_langs)
#        print(f'eye_colors' + '\n', new_char.c_skills)
#        print(f'appearance' + '\n', new_char.c_racial_traits)




        # use random.sample to select 3 random professions 
        random_professions = random.sample(profession, 3)
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

        # random.sample to select 2 random weapons
        weapons = random.sample(weapon_groups, 2)
        print(f'weapons not weight by region {weapons}')
        # loop through the random abilities and print out each element
        for region in regions:
            weaponz = random.choice(weapon_groups_region[region])
            print(f"Weapon for {region}: {weaponz}")
            print(f"Weapon for {region}: {weaponz}", file=f)        

                # Copy + paste so it prints to the terminal as well as the output file
                
       

        print('this is your new class')
        print(new_char.c_class)
        print('this is your new class', file=f)
        print(new_char.c_class, file=f)

        chance = random.randint(1,100)
        chance_2 = random.randint(1,100)
        if new_char.c_class != '':   
            global path
            path=0 
            if new_char.c_class != path_of_war_class:
                if c_bab == 'high':
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
                        return 'Path of War'
                elif c_bab == 'mid':
                    if chance >= 50:
                        path = 1
                        print(path)
                        if chance_2 >= 90:
                            path = 2
                            print('this is how many path of war abiities they take ')
                            print('this is how many path of war abiities they take ', file = f)
                            print(path)
                            print(path, file = f)
                        return 'Path of War'            

                    else:
                        if chance >= 90:
                            path = 1
                            print('this is how many path of war abiities they take ')
                            print('this is how many path of war abiities they take ', file = f)
                            print(path)
                            print(path, file = f)
                            return 'Path of War '
                        



        # Randomly Assigning archetypes:

       # char_class = new_char.c_class.lower()
       # selected_archetype = random.choice(archetypes[char_class])
       # print('this is the randomly selected archetype' +  '\n' + selected_archetype + '\n' + ' for this class' + '\n' + char_class)
        
            #selected_archetype = random.choice(archetypes.eval("archetypes_{new_char.c_class.lower()}"))


        #    print(f"This is the selected archetype for {new_char.c_class}: + {selected_archetype}")



            
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

            