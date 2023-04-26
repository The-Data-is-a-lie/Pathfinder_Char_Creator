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
    with open(filename, 'a') as f, open("utils/race.json", "r") as r, open("utils/class.json", "r") as c, open("utils/traits_abilities.json") as t, open("utils/profession.json") as p:
        profession_data = json.load(p)
        race_data = json.load(r)
        class_data = json.load(c)
        traits_data = json.load(t)

        new_char = Character()

        races = []
        classes = []

        for race in race_data:
            races.append(race)

        for _class in class_data:
            classes.append(_class)

        new_char.c_class = chooseClass(name)



                        #this is where we change the stat rolls:
        num_dice = int(input("How many dice would you like to roll? "))
        num_sides = int(input("How many sides should each die have? "))

        new_char.c_str = roll_dice(num_dice, num_sides, 'Strength', name)
        new_char.c_dex = roll_dice(num_dice, num_sides, 'Dexterity', name)
        new_char.c_const = roll_dice(num_dice, num_sides, 'Constitution', name)
        new_char.c_int = roll_dice(num_dice, num_sides, 'Intelligence', name)
        new_char.c_wisdom = roll_dice(num_dice, num_sides, 'Wisdom', name)
        new_char.c_char = roll_dice(num_dice, num_sides, 'Charisma', name)


        new_char.c_skills = class_data[new_char.c_class]['skills']
        new_char.c_langs = ['Common']
        c_bab = class_data[new_char.c_class]['BAB']

        #Printing out character traits, (mannerisms, traits, profession, appearances, alignment, + traits_Abilities)
        mannerisms = []
        new_char.c_mannerisms = appendAttrData(mannerisms, data.mannerisms)

        traits = []
        new_char.c_traits = appendAttrData(traits, data.traits)

        Alignment = []
        new_char.c_alignment = appendAttrData(Alignment, data.alignment)

        traits_abilities = []
        new_char.c_traits_abilities = appendAttrData(traits_abilities, traits_data)
    
        #prints stats
        print(f'Strength: {new_char.c_str}\nDexterity: {new_char.c_dex}', file=f)
        print(f'Constitution: {new_char.c_const} \nIntelligence: {new_char.c_int}', file=f)
        print(f'Wisdom: {new_char.c_wisdom}\nCharisma: {new_char.c_char}' + '\n', file=f )


        print(f'Skills' + '\n', new_char.c_skills, file=f)

        print(f'Strength: {new_char.c_str}\nDexterity: {new_char.c_dex}')
        print(f'Constitution: {new_char.c_const} \nIntelligence: {new_char.c_int}')
        print(f'Wisdom: {new_char.c_wisdom}\nCharisma: {new_char.c_char}')

        print(f'Skills' + '\n', new_char.c_skills)

        # Printing out additional 1-4 random class
        skill_list = random.choices(skills, k=4)
        print(f'Specialized Skills {skill_list}')
        print(f'Specialized Skills {skill_list}', file=f)




        #print out alignment + physical characteristics
        print(f'Alignment' + '\n', new_char.c_alignment)
        print(f'Alignment' + '\n', new_char.c_alignment, file=f)
      
        #Potentially add a charactersitics by region section
        hair_color_choice = random.choice(hair_colors)
        hair_type_choice = random.choice(hair_types)
        eye_color_choice = random.choice(eye_colors)
        random_app_number = random.randint(1,3)
        appearance_choice = random.sample(appearance,k=random_app_number)

        print(f'hair_colors' + '\n', hair_color_choice)
        print(f'hair_types' + '\n', hair_type_choice)
        print(f'eye_colors' + '\n', eye_color_choice)
        print(f'appearance' + '\n', appearance_choice)


        
        #deciding deity based off of aligment
        if 'good' in new_char.c_alignment:
            chosen_deity = random.choice(good_deities)
            print(f"Deity \n {chosen_deity}",file=f)
            print(f"Deity \n {chosen_deity}") 
        elif 'evil' in new_char.c_alignment:
            chosen_deity = random.choice(evil_deities)            
            print(f"Deity \n {chosen_deity}",file=f)
            print(f"Deity \n {chosen_deity}")
        else:
            chosen_deity = random.choice(neutral_deities)            
            print(f"Deity \n {chosen_deity}",file=f)
            print(f"Deity \n {chosen_deity}")

        random_number = random.randint(1,5)
        extra_lang = random.sample(languages,k=random_number)
        print(f"These are the extra languages the character knows: {extra_lang}")
        print(f"These are the extra languages the character knows: {extra_lang}", file=f)


        # use random.sample to select 3 random professions 
        professions = profession_data['Profession']
        random_professions = random.sample(professions, 3)
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

        
        #printing out your class
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

            