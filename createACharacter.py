#Internal Imports
from utils import data
import json
from utils.data import regions, weapon_groups_region, skills,  languages, hair_colors, hair_types, appearance, eye_colors#, path_of_war_class,evil_deities, good_deities, neutral_deities,
#from utils.data import archetypes
from utils.util import  format_text, chooseClass, appendAttrData, roll_dice#,  Roll_Level#,roll_4d6, roll_dice #printAttributes,
from utils.markdown import style
import random
import sys
from math import floor

#External Imports
from random import randrange
import pandas

# # Base Character Traits
# class Character:
#     c_str = 10
#     c_dex = 10
#     c_const = 10
#     c_int = 10
#     c_wisdom = 10
#     c_char = 10

#     c_race = 'Placeholder'
#     c_class = 'Placeholder'

    
#     c_weapon = ['Dagger']
#     c_armor = ['Cloth shirt']
    
#     c_skills = ['Placeholder']
#     c_skills_2 = ['Placeholder']
#     c_spells = ['None']
#     c_hp = 1

#     c_langs = ['Common']
    
#     c_saving_throws = []
#     c_racial_traits = []
    
#     c_size = 'Medium'
#     c_traits = []
    
#     c_bg = 'outlander'
#     c_mannerisms = ''

#     def __str__(self): return f'Name: {self.c_name} ({self.c_race} {self.c_class})'

# simply create a new character
class Character:
    def __init__(self, json_config):
        # json_paths stores the paths to different json files
        self.feats=None
        self.BAB=None
        self.level=None
        # c_race
        self.weapons=None
        self.weaponz=None
        self.luck_score=None
        self.mythic_rank=None
        self.c_class=None,
        self.c_class_2=None, 
        # Sometimes this is a tuple, we'll need to update the code to handle that
        self.flaw=None
        self.proforce=None
        self.random_abilities=None
        self.random_personality=None
        self.random_mannerisms=None
        self.stats=None
        self.hair_color_choice =None
        self.hair_type_choice =None
        self.eye_color_choice =None
        self.appearance_choice=None
        self.chosen_deity=None

        self.region=None
        self.f_name=None
        self.l_name=None
        self.full_name=None
        self.Total_HP=None
        self.Hit_dice=None
        self.Hit_dice1=None
        # self.Hit_dice2=None                
        self.total_hp_rolls=None    
        # self.total_hp_rolls1=None
        # self.total_hp_rolls2=None                            
        self.total_Hit_dice=None
        self.extra_ability_score_levels=None
        self.npc_level=None
        self.BAB_total=None
        self.c_class=None
        self.flaw=None
        self.random_professions=None
        self.c_skills =None
        self.c_skills_2=None
        self.skill_list=None
        self.disciplines_choice=None
        # character_flaws
        # User Inputs
        self.userInput_race=None
        self.userInput_region=None
        #body features
        self.age=None
        self.height=None
        self.weight=None
        #alignment variable
        self.alignment=None

        #path of war variables
        self.path=None

        #archetype variables
        self.archetype1=None
        self.archetype2=None

        #gold + Item variables
        self.gold=None

        #Saving throw variables
        self.fort=None
        self.reflex=None
        self.will=None

        # replaced age_roll with age
        # self.age_roll =None
        # self.weight_roll =None
        # self.height_roll=None        

        # Removed, because data redunancy we can just pull from json later
        # self.racial_traits =None
        # self.racial_language, 
        # self.racial_size =None
        # self.racial_speed =None
        # self.racial_ability_scores=None

        self._load_jsons(json_config)
        
    def _load_jsons(self, json_config):
        with open(json_config['race']) as f:
            self.races = json.load(f)
            self.unique_races = self.races.keys()

        with open(json_config['class']) as f:
            self.classes = json.load(f)

        with open(json_config['traits']) as f:
            self.traits_abilities = json.load(f)
            random.shuffle(self.traits_abilities)

        with open(json_config['profession']) as f:
            self.professions = json.load(f)
            random.shuffle(self.professions)

        with open(json_config['last_names_regions']) as f:
            self.last_names_regions = json.load(f)
        self.regions = [k for k in self.last_names_regions.keys()]

        with open(json_config['first_names_regions']) as f:
            self.first_names_regions = json.load(f)
        
        with open(json_config['flaws']) as f:
            self.flaws = json.load(f)

        with open(json_config['archetypes']) as f:
            self.archetypes = json.load(f)      
             

    #should this be update feats, since we're updating feat amount [it 100% depends on level]
    def update_level(self, level):
        self.level = level
        if len(self.flaw) == 2 or len(self.flaw) == 3:
            self.feats = (4 + floor(self.level/2) + floor(self.level/5))
        elif len(self.flaw) == 4:
            #add 1 extra feat because of 2 extra flaws
            self.feats = (4 + 1 + floor(self.level/2) + floor(self.level/5))
        elif len(self.flaw) == 1:
            #remove 1 extra feat because of 1 less flaw
            self.feats = (4 - 1 + floor(self.level/2) + floor(self.level/5))
        else:
            #remove 2 extra self.feats because of no flaws
            self.feats = (4 - 2 + floor(self.level/2) + floor(self.level/5))
        self._update_BAB_total()

    def update_level_ability_score(self, level):
        self.level=level
        self.extra_ability_score_levels=floor(level/4)



    def _update_BAB_total(self):
        # self.class_level = {
        #     'class 1': {
        #         'level': 7,
        #         'BAB': 'H'
        #     },
        #     'class 2': {
        #         'level': 3,
        #         'BAB': 'L'
        #     }
        # }
        # self.BAB_total = 0
        # for _, data in self.class_level.items():
        #     # Creating a BAB total for printing out
        #     if data.BAB == 'L':
        #         self.BAB_total += floor(data.level *.5)
        #     elif data.BAB == 'M':
        #         self.BAB_total += floor(data.level *.75)
        #     else: 
        #         self.BAB_total += data.level * 1

        # set as an integer so our function beneath works
        self.BAB_total = 0
        if self.BAB == 'L':
            self.BAB_total += floor(self.level *.5)
        elif self.BAB == 'M':
            self.BAB_total += floor(self.level *.75)
        else: 
            self.BAB_total += self.level * 1
    
    def roll_stats(self, num_dice, num_sides):
        self.str = roll_dice(num_dice, num_sides)
        self.dex = roll_dice(num_dice, num_sides)
        self.const = roll_dice(num_dice, num_sides)
        self.int = roll_dice(num_dice, num_sides)
        self.wisdom = roll_dice(num_dice, num_sides)
        self.char = roll_dice(num_dice, num_sides)
    
    def randomize_flaw(self):
        flaw_chance = random.randint(0,100)
        if int(flaw_chance) <= 50:
            flaw = random.sample(list(self.flaws),2)
        elif 50 < int(flaw_chance) <= 65:
            flaw = random.sample(list(self.flaws),3)
        elif 65 < int(flaw_chance) <= 80:
            flaw = random.sample(list(self.flaws),1)
        elif 80 < int(flaw_chance) <= 95:
            flaw = random.sample(list(self.flaws),0)
        else:
            flaw = random.sample(list(self.flaws),4)
        self.flaw = flaw
    
    def randomize_level(self, min, max):
        level = random.randint(min, max)
        self.update_level(level)

    def hit_dice_calc(self):
        # Class Hit Dice + total Hit points
        self.Hit_dice1 = self.classes[self.c_class]["hp"]
        # character.Hit_dice2 = character.classes[character.c_class_2]["hp"]            


        print(f"hit dice {self.Hit_dice1}")
        # print(f"hit dice {self.Hit_dice2}")            

        # print(f"hit dice {Hit_dice2}")            
        print(f"This is your character's first class Hit dice: {self.Hit_dice1}")
        # print(f"This is your character's first class Hit dice: {self.Hit_dice2}")            

    def roll_hp(self):
        hp_rolls = []
        #Figure out how to loop this to calc for each class rather than just one
        for _ in range(self.level-1):
            hp_rolls.append(random.randint(1,self.Hit_dice1))
            print(hp_rolls) #working as expected
        self.total_hp_rolls = sum(hp_rolls)         
        return self.total_hp_rolls


    def total_hp_calc(self):        
        self.Total_HP = self.total_hp_rolls + self.Hit_dice1
        print(f'This is your total HP: {self.Total_HP}')

    #change age/height/weight string into useable array that contains (e.g.) 5d6 -> 5,6 (5 num_dice, 6 num_sides)
    def randomize_body_feature(self, body_attribute):
        print(f'??????????????????????????{self.races[self.userInput_race][body_attribute] }')
        [base_stat, dice_string] = self.races[self.userInput_race][body_attribute]        
        # print(self.)
        print(f'before setting attribute {body_attribute}', getattr(self, body_attribute))
        [num_dice, num_sides] = [int(c) for c in dice_string.split('d')]
        dice_roll = roll_dice(num_dice, num_sides)
        setattr(self, body_attribute, base_stat+dice_roll)
        print(f'after setting attribute {body_attribute}', getattr(self, body_attribute))

    
    def get_racial_attr(self, racial_attribute):
        if self.userInput_race in self.races:
            return self.races[self.userInput_race][racial_attribute]
        
    def randomize_apperance_attr(self, apperance_attribute, upper_limit=1):
        random_app_number = random.randint(1,upper_limit)
        potential_apperances = getattr(data,apperance_attribute)
        return random.sample(potential_apperances, k=random_app_number)


    def randomize_personality_attr(self, personality_attribute, upper_limit=1):
        # redundant, JAVASCRIPT has a CSV file with all of these
        random_pers_number = random.randint(1,upper_limit)
        potential_personality = getattr(data,personality_attribute)  
        return random.sample(potential_personality,k=random_pers_number)  
        

    def randomize_alignment(self, alignments):
        #pulling alignments from data.py and picking one
        random_alignment = getattr(data,alignments)
        self.alignment = random.choice(random_alignment)
        return self.alignment

    def randomize_deity(self, all_deities):
        # Might want to revamp the way we randomly select deities 
        # (we could make it abit more complex and have chances to 
        # pick Lawful + Chaotic deities as well)
        # Gathering a dictionary of all deities to randomly select one
        deity_list = getattr(data,all_deities) 
        if 'good' in self.alignment:
            return  random.choice(deity_list["good_deities"])
        elif 'evil' in self.alignment:
            return  random.choice(deity_list["evil_deities"])
        else:
            return  random.choice(deity_list["neutral_deities"])


    def randomize_path_of_war_num(self, path_of_war_class):
        path = None
        chance = random.randint(1,100)
        getattr(data,path_of_war_class)
        if self.c_class not in path_of_war_class:
            if self.BAB == 'H':
                if chance >= 25:
                    self.path = 1
                else:
                    self.path = 0

            elif self.BAB == 'M':
                if chance >= 50:
                    self.path = 1
                else:
                    self.path = 0                    

            else:
                if chance >= 90:
                    self.path = 1
        return self.path
    
    def choose_path_of_war_attr(self, disciplines):
        #choosing path of war discipline
        potential_disciplines = getattr(data, disciplines)
        if self.path > 0:
            return random.sample(potential_disciplines, k=self.path)
        else:
            return None
            

    def Archetype_Assigner(self):
        if self.c_class.lower() in self.archetypes.keys():
            archetype_list_1 = self.archetypes[self.c_class]
            self.archetype1 = random.choice(archetype_list_1)
            print(f'!!!!!!! {self.archetype1}')               
            # archetype_list_2 = self.archetypes[self.c_class]
            # self.archetype2 = random.choice(archetype_list_2)       
        else:
            self.archetype1 = None
            print(f'?????? {self.archetype1}')               
            # self.archetype2 = None    
     
        return self.archetype1#, self.archetype2


    def saving_throw_calc(self, saving_throw):
        #update this to be for class_level then add up both options
        high_saving_throw = floor(2 + (self.level/2))
        low_saving_throw = floor((self.level/3))        
        if saving_throw in self.classes[self.c_class]["saving throws"]: 
            self.saving_throw = high_saving_throw            
        else:
            self.saving_throw = low_saving_throw
        print(self.saving_throw)
        return self.saving_throw



    def assign_gold(self,gold):
        gold = getattr(data,gold)
        print(type(gold))     
        if self.level>20:
            self.gold = gold[-1]
        self.gold = gold[self.level-2]
        return self.gold



        # # use random.sample to select 8 random abilities
        # random_abilities = random.sample(traits_abilities, 8)
        # # loop through the random abilities and print out each element
        # for ability in random_abilities:
        #     print(f'(ability traits):',ability)

        # # use random.sample to select 5 random personality traits
        # random_personality = random.sample(traits, 5)
        # # loop through the random abilities and print out each element
        # for personality in random_personality:
        #     print(f'(personality traits):',personality)

        # # use random.sample to select 3 random mannerisms
        # random_mannerisms = random.sample(mannerisms, 3)
        # # loop through the random abilities and print out each element
        # for manners in random_mannerisms:
        #     print(f'(mannerisms):',manners)

        # for character_flaws in range(len(flaw)):
        #     print(f"(character_flaws): {flaw[character_flaws]}")
            
            # hair_color_choice = random.choice(hair_colors)
            # hair_type_choice = random.choice(hair_types)
            # eye_color_choice = random.choice(eye_colors)
            # random_app_number = random.randint(1,3)
            # appearance_choice = random.sample(appearance,k=random_app_number)

            # print(f'hair_colors' + '\n', hair_color_choice)
            # print(f'hair_types' + '\n', hair_type_choice)
            # print(f'eye_colors' + '\n', eye_color_choice)
            # print(f'appearance' + '\n', appearance_choice)

    # def randomize_profession_attr():

    #     # use random.sample to select 3 random professions 
    #     professions = profession_data['Profession']
    #     random_professions = random.sample(professions, 3)
    #     # loop through the random abilities and print out each element
    #     for proforce in random_professions:
    #         print(f'(profession):',proforce)

        # if userInput_race in race_data:
        #     racial_traits = race_data[userInput_race]["traits"]
        #     racial_language = race_data[userInput_race]["languages"]
        #     racial_size = race_data[userInput_race]["size"]
        #     racial_speed = race_data[userInput_race]["speed"]
        #     racial_ability_scores = race_data[userInput_race]["ability scores"]          
        


        # if isinstance(self.age[1], str):
        #     left, right = map(int, self.age[1].split('d'))
        #     age_roll = sum([random.randint(1, right) for i in range(left)]) + age[0]
        # else:
        #     age_roll = random.randint(self.age[0], self.age[1])
        #     left = self.age[0]
        # age_roll += left
        # print(f"Age: {age_roll}")





# setting up a new character
def CreateNewCharacter(character_json_config):
    new_char = Character(character_json_config)
    return new_char









def _CreateNewCharacter():
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



        #Print into Terminal
        print(formatted_strength)
        print(formatted_dexterity)
        print(formatted_constitution)
        print(formatted_intelligence)
        print(formatted_wisdom)
        print(formatted_charisma)









            
        print('===============================================================')

            