#Internal Imports
from utils import data
import json
from utils.data import regions, weapon_groups_region, skills,  languages, hair_colors, hair_types, appearance, eye_colors#, path_of_war_class,evil_deities, good_deities, neutral_deities,
#from utils.data import archetypes
from utils.util import  format_text, chooseClass, appendAttrData, roll_dice#,  Roll_Level#,roll_4d6, roll_dice #printAttributes,
from utils.markdown import style
import random
import sys

#External Imports
from random import randrange
from math import floor, ceil
import pandas as pd

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

        #level dependent variables
        self.total_Hit_dice=None
        self.extra_ability_score_levels=None
        self.npc_level=None
        self.BAB_total=None
        self.c_class=None
        self.c_class_2=None
        self.c_class_level=None
        self.c_class_2_level=None     
        self.c_class_for_spells=None
        self.c_class_2_for_spells=None  
        self.spells_1_known=None
        self.spells_2_known=None                        
        self.dip=None

        #Spell list variables
        #change these to prepared spells
        self.spells_list_1=None
        self.spells_list_2=None   
        self.spells_known_list=None      


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

        with open(json_config['spells_known']) as f:
            self.spells_known = json.load(f)      

        with open(json_config['spells_per_day']) as f:
            self.spells_per_day = json.load(f)      

        with open(json_config['spells_from_ability_mod']) as f:
            self.spells_from_ability_mod = json.load(f)                                          
             

    #should this be update feats, since we're updating feat amount [it 100% depends on level]
    def update_level(self, level, c_class_level, c_class_2_level):
        if self.c_class == '':
            self.level = level
            self.c_class_level = c_class_level
        else:  
            self.level = level
            self.c_class_level = c_class_level
            self.c_class_2_level = c_class_2_level              

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
        print(f'STR {self.str}')
        print(f'DEX {self.dex}')
        print(f'CON {self.const}')
        print(f'INT {self.int}')
        print(f'WIS {self.wisdom}')
        print(f'CHA {self.char}')                                        
        
    
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
    
    def randomize_level(self, min, max_num):
        if self.c_class_2 == '':
            level = random.randint(min, max(min, max_num))
            c_class_level = level
            c_class_2_level = 0
            self.update_level(level, c_class_level, c_class_2_level)
        if self.dip == True:
            level = random.randint(min, max(min, max_num))
            c_class_level = level-1
            c_class_2_level = 1
            self.update_level(level, c_class_level, c_class_2_level)
        else:
            level = random.randint(min, max(min, max_num))
            c_class_level = random.randint(min-1,level-1)
            c_class_2_level = level - c_class_level
            self.update_level(level, c_class_level, c_class_2_level)            

    def hit_dice_calc(self):
        if self.c_class_2 != '':
            self.Hit_dice1 = self.classes[self.c_class]["hp"]
            self.Hit_dice2 = self.classes[self.c_class_2]["hp"]            

            print(f"hit dice {self.Hit_dice1}")
            print(f"hit dice {self.Hit_dice2}")            
      
            print(f"This is your character's first class Hit dice: {self.Hit_dice1}")
            print(f"This is your character's second class Hit dice: {self.Hit_dice2}")            
        else:
            self.Hit_dice1 = self.classes[self.c_class]["hp"]
            print(f"hit dice {self.Hit_dice1}")            
            print(f"This is your character's first class Hit dice: {self.Hit_dice1}")                        


    def roll_hp(self):
        print(f' This is your first class level {self.c_class_level}')        
        print(f' This is your second class level {self.c_class_2_level}')
        hp_rolls = []
        #Figure out how to loop this to calc for each class rather than just one
        for _ in range(self.c_class_level-1):
            print('#1 !!!!!!!!!')
            hp_rolls.append(random.randint(1,self.Hit_dice1))
            print(hp_rolls) #working as expected
        self.total_hp_rolls = sum(hp_rolls)         

        for _ in range(self.c_class_2_level):
            print('#2 ?????????')
            hp_rolls.append(random.randint(1,self.Hit_dice2))
            print(hp_rolls) #working as expected
        self.total_hp_rolls = sum(hp_rolls)         

        return self.total_hp_rolls


    def total_hp_calc(self):               
        self.Total_HP = self.total_hp_rolls + self.Hit_dice1 + (floor(self.const-10)/2 * self.level)
        self.Total_HP = floor(self.Total_HP)
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
        self.path = 0
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

    def randomize_mythic(self):
        self.mythic_rank = 0
        if random.randint(1, 1000) >= 995:
            self.mythic_rank = 1					
            for j in range(2, 11):
                roll = random.randint(1, 100)
                if roll >= 90:
                    self.mythic_rank += 1
        else:
            self.mythic_rank = 0
        return self.mythic_rank


    def randomize_luck(self):
        if random.randint(1, 100) >= 95:
            self.luck_score = random.randint(1, 40)
        #using a -40 to make it a negative luck score when you roll low
        elif random.randint(1, 100) <= 5:
            self.luck_score = random.randint(1, 40) - 40
        else:
            self.luck_score = 0
        return self.luck_score

    def druidic_flag(self):
        if self.c_class.lower() == 'druid':
            self.languages = languages.append('Druidic')

    def human_flag(self):
        if self.c_class.lower() == 'human':
            self.feats += 1     

    def class_for_spells(self):
        #currently we only know that skald spells aren't proper, but 
        # skalds use bard spell list -> just have an if statement for them
        # investigators use alchemists spells
        # + check others
                
        #This is a quick and easy function to make it so we search
        #for different spell lists than our current class
        if self.c_class == 'skald':
            self.c_class_for_spells = 'bard'
        if self.c_class == 'investigator':
            self.c_class_for_spells = 'alchemist'   
        else:
            self.c_class_for_spells = self.c_class     
        return self.c_class_for_spells

    def high_caster_formula(self,n):
        if n % 2 == 0:
            cast_level=n // 2
        else:
            cast_level=(n + 1) // 2
        cast_level = min(cast_level,9)
        return cast_level
    
    def mid_caster_formula(self,n):
        if n % 3 == 1:
            cast_level= ceil(n // 3)+1
        else:
            cast_level= ceil(n / 3)
        cast_level = min(n,6)
        return cast_level

    def low_caster_formula(self,n):
        cast_level= ceil(n / 3)-1
        cast_level = min(cast_level,4)
        return cast_level
    

    def spells_known_attr(self,base_classes, divine_casters):
        high_caster_level = self.high_caster_formula(self.c_class_level)
        mid_caster_level = self.mid_caster_formula(self.c_class_level)
        low_caster_level = self.low_caster_formula(self.c_class_level)  
        casting_level_1 = str(self.classes[self.c_class]["casting level"].lower())         
        base_classes = getattr(data,base_classes)
        divine_casters=getattr(data, divine_casters)    
        self.spells_known_list = []
        list = []    
 

        if self.c_class in base_classes and casting_level_1 == 'high' and self.c_class not in divine_casters:
            for i in range(1,high_caster_level+1):
                print(high_caster_level)
                key = str(i)
                list=self.spells_known[self.c_class_for_spells][key][self.c_class_level-1]
                self.spells_known_list.append(list)
        elif self.c_class in base_classes and casting_level_1 == 'mid' and self.c_class not in divine_casters:
            for i in range(1,mid_caster_level+1):
                key = str(i)                
                list=self.spells_known[self.c_class_for_spells][key][self.c_class_level-1]
                self.spells_known_list.append(list)
        elif self.c_class in base_classes and casting_level_1 == 'low' and self.c_class not in divine_casters:
            for i in range(1,low_caster_level+1):
                key = str(i)                
                list=self.spells_known[self.c_class_for_spells][key][self.c_class_level-1]
                self.spells_known_list.append(list)
        elif self.c_class in divine_casters:
            print('Divine Casters know all spells')
        else:
            print('Not an Arcane caster')

        return self.spells_known_list
    
    def spells_per_day(self, base_classes, divine_casteres):




    # def spells_known(self, divine_casters):
    #     self.spells_1_known = []   
    #     divine_casters=getattr(data, divine_casters)

    #     casting_level_1 = str(self.classes[self.c_class]["casting level"].lower())  
    #     spell_data=pd.read_csv('data/spells.csv', sep='|')
    #     extraction_list = ['name', self.c_class]         
    #     high_caster_formula = high_caster_formula(self.c_class_level)
    #     mid_caster_formula = mid_caster_formula(self.c_class_level)
    #     low_caster_formula = low_caster_formula(self.c_class_level)                 
    #     # we are just trying to grab all spells in their lists, since they know all of them
    #     if self.c_class in divine_casters and casting_level_1 == 'high':
    #             # range = 0 because divine casters know all cantrips as well
    #             for i in range(1, high_caster_formula+1):              
    #                 self.spells_1_known = spell_data.loc[spell_data[self.c_class] == i, extraction_list]
    #     elif self.c_class in divine_casters and casting_level_1 == 'high':
    #             for i in range(1, mid_caster_formula):              
    #                 self.spells_1_known = spell_data.loc[spell_data[self.c_class] == i, extraction_list]            




    # def spells_known_divine_caster(self, divine_casters):
    #     self.spells_1_known = []        
    #     getattr(data, divine_casters)
    #     casting_level_1 = str(self.classes[c_class]["casting level"].lower())         
    #     spell_data=pd.read_csv('data/spells.csv', sep='|')
    #     extraction_list = ['name', self.c_class]      
    #     high_caster_formula = high_caster_formula(self.c_class_level)
    #     mid_caster_formula = mid_caster_formula(self.c_class_level)
    #     low_caster_formula = low_caster_formula(self.c_class_level)

    #     # we are just trying to grab all spells in their lists, since they know all of them
    #     if self.c_class in divine_casters and casting_level_1 == 'high':
    #             # range = 0 because divine casters know all cantrips as well
    #             for i in range(0, high_caster_formula):              
    #                 self.spells_1_known = spell_data.loc[spell_data[self.c_class] == i, extraction_list]
    #     elif self.c_class in divine_casters and casting_level_1 == 'high':
    #             for i in range(1, mid_caster_formula):              
    #                 self.spells_1_known = spell_data.loc[spell_data[self.c_class] == i, extraction_list]            


            


    # def randomize_spells_known_1(self):
    #     if self.c_class_for_spells in 

    # def randomize_spells_known_1(self,base_classes):

    #     self.spells_list_1 = []
    #     c_class = self.c_class
    #     casting_level_1 = str(self.classes[c_class]["casting level"].lower())   
    #     base_classes = getattr(data,base_classes)
    #     spell_data=pd.read_csv('data/spells.csv', sep='|')
    #     extraction_list = ['name', c_class]
    #     self.spell_list = []

    #     if casting_level_1 in ('low') and c_class in base_classes:

    #         for i in range(self.c_class_level):
    #             query_i = spell_data.loc[spell_data[c_class] == i, extraction_list] 
    #             random.shuffle(query_i.to_numpy())
    #             spells = query_i[:3]
    #             self.spells_list_1.append(spells)

    #     if casting_level_1 in ('mid') and c_class in base_classes:

    #         for i in range(self.c_class_level):
    #             query_i = spell_data.loc[spell_data[c_class] == i, extraction_list] 
    #             random.shuffle(query_i.to_numpy())
    #             spells = query_i[:3]
    #             self.spells_list_1.append(spells)

    #     if casting_level_1 in ('high') and c_class in base_classes:

    #         for i in range(self.c_class_level):
    #             query_i = spell_data.loc[spell_data[c_class] == i, extraction_list] 
    #             random.shuffle(query_i.to_numpy())
    #             spells = query_i[:3]
    #             self.spells_list_1.append(spells)                                

          
    #     else:
    #         print('Not a base Caster_class_1')

    #     # Print the list of strings
    #     print(self.spells_list_1)            
    



    # def randomize_spells_known_2(self,base_classes):
    #     self.spells_list_2 = []
    #     c_class = self.c_class
    #     casting_level_2 = str(self.classes[c_class]["casting level"].lower())   
    #     base_classes = getattr(data,base_classes)
    #     spell_data=pd.read_csv('data/spells.csv', sep='|')
    #     extraction_list = ['name', c_class]

    #     self.spell_list = []
    #     if casting_level_2 in ('low', 'mid', 'high') and c_class in base_classes:


    #         for i in range(self.c_class_level):
    #             query_i = spell_data.loc[spell_data[c_class] == i, extraction_list] 
    #             random.shuffle(query_i.to_numpy())
    #             spells = query_i[:3]
    #             self.spells_list_2.append(spells)

    #         # Print the list of strings
    #         print(self.spells_list_2)            
          
    #     else:
    #         print('Not a base Caster_class_2')        


# setting up a new character
def CreateNewCharacter(character_json_config):
    new_char = Character(character_json_config)
    return new_char

