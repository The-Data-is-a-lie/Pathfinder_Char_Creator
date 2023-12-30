#Internal Imports
from utils import data
import json
from utils.data import regions, weapon_groups_region, skills,  languages, hair_colors, hair_types, appearance, eye_colors#, path_of_war_class,evil_deities, good_deities, neutral_deities,
#from utils.data import archetypes
from utils.util import   roll_dice#,format_text, chooseClass, appendAttrData,  Roll_Level#,roll_4d6, roll_dice #printAttributes,
from utils.markdown import style
import random
import sys
import re
import numpy as np

#External Imports
from random import randrange
from math import floor, ceil
import pandas as pd
from operator import add


# simply create a new character
class Character:
    def __init__(self, json_config):
        # json_paths stores the paths to different json files

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
        self.Hit_dice2=None                
        self.total_hp_rolls=None    
        # self.total_hp_rolls1=None
        # self.total_hp_rolls2=None                            

        #ability_score
        self.str=None
        self.dex=None
        self.con=None
        self.int=None
        self.wis=None
        self.cha=None           

        self.str_mod=None
        self.dex_mod=None
        self.con_mod=None
        self.int_mod=None
        self.wis_mod=None
        self.cha_mod=None                                         

        #level dependent variables
        self.total_Hit_dice=None
        self.extra_ability_score_levels=None
        self.npc_level=None
        self.bab_total=None
        self.c_class=None
        self.c_class_2=None
        self.c_class_level=None
        self.c_class_2_level=None     
        self.c_class_for_spells=None
        self.c_class_2_for_spells=None  
        self.spells_1_known=None
        self.spells_2_known=None                        
        self.dip=None
        self.capped_level_1=None
        self.capped_level_2=None
    

        #Spell list variables
        #change these to prepared spells
        self.spells_list_1=None
        self.spells_list_2=None   
        self.spells_known_list=None      
        self.spells_per_day_list=None
        self.highest_spell_known_1=None
        self.highest_spell_known_2=None
        self.spell_list_choose_from=None        

        #class specific options
        self.wizard_chosen_school=None
        self.prohibited_schools=None
        self.chosen_bloodline=None
        self.mercy_chosen_list=None
        self.rogue_talent_list=None
        self.armor_chosen_list=None         
        self.armor_chosen_list_description=None       
        self.weapon_chosen_list=None
        self.weapon_chosen_list_description=None  


        #classes like monks + rangers can only select certain combat feats
        self.ranger_feats=None
        self.ranger_combat_styles=None

        self.bonus_feats=[]
        self.bonus_spells=[]





        #feat selector variables
        self.feat_amounts=None
        self.combat_feats=None
        self.magic_feats=None
        self.bab=None
        self.level=None
        self.feat_list=None
        self.monk_feats=None
        self.result_dict={}



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
            for key, file_path in json_config.items():
                with open(file_path) as f:
                    data = json.load(f)
                    setattr(self, key, data)
                    if isinstance(data, list):
                        random.shuffle(getattr(self, key))
                    if key == 'last_names_regions':
                        setattr(self, 'last_names_regions', data)
                        setattr(self, 'regions', [k for k in data.keys()])


    #         self.shaman = json.load(f)    
                                        

                                        

         

        

    #should this be update feats, since we're updating feat amount [it 100% depends on level]
    def update_level(self, level, c_class_level, c_class_2_level, flaw_flag=None, homebrew_amount=None):
        self.level = level
        self.c_class_level = c_class_level
        self.c_class_2_level = c_class_2_level              

        if flaw_flag == None:
            self.feat_amounts = (ceil(self.level/2) + min(len(self.flaw),3))
        else:
            self.feat_amounts = ( ceil(self.level/2) )

        if homebrew_amount != None:
            self.feat_amounts = (4 + ceil(self.level/2) + floor(self.level/5) + max((len(self.flaw)-2),0) )

        self._update_bab_total()


    def update_level_ability_score(self, level):
        self.level=level
        self.extra_ability_score_levels=floor(level/4)



    def _update_bab_total(self):
        self.bab = self.class_data[self.c_class]['bab']
        # set as an integer so our function beneath works
        self.bab_total = 0
        if self.bab == 'L':
            self.bab_total += floor(self.level *.5)
        elif self.bab == 'M':
            self.bab_total += floor(self.level *.75)
        else: 
            self.bab_total += self.level * 1


    
    def roll_stats(self, num_dice, num_sides):
        # Define the main stat for the class (replace 'main_stat' with the actual main stat for your class)
        main_stat = self.class_data[self.c_class]['main_stat']
        main_stat_2 = self.class_data[self.c_class].get('main_stat_2', None)

        if '/' in main_stat:
            main_stat_parts = main_stat.split('/')
            main_stat = random.choice(main_stat_parts)

        # Roll stats for all attributes
        stats = {attr: roll_dice(num_dice, num_sides) for attr in ['str', 'dex', 'con', 'int', 'wis', 'cha']}

        # Identify the original main stat
        stats = self.swap_stats(main_stat, stats)
        print(main_stat)

        if main_stat_2 != None:
            main_stat_parts_2 = main_stat_2.split('/')
            print(main_stat_parts_2)
            main_stat_2 = random.choice(main_stat_parts_2)      
            print(f'main_stat 2 {main_stat_2}')
            stats = self.swap_stats(main_stat_2, stats, new=True)   


        # Assign the rolled stats to the character's attributes
        for attr, value in stats.items():
            setattr(self, attr, value)

        # Print the rolled stats
        self.print_stats()

    def swap_stats(self, main_stat, stats, new=None):
        original_main_stat = stats[main_stat]
        new_main_stat_key = max(stats, key=stats.get)        
        if new == None:
            stats[main_stat], stats[new_main_stat_key] = stats[new_main_stat_key], original_main_stat
        else:
            second_highest_stat_key = max(stats, key=lambda k: stats[k] if k != new_main_stat_key else float('-inf'))
            stats[main_stat], stats[second_highest_stat_key] = stats[second_highest_stat_key], original_main_stat
         

        return stats                    

    def print_stats(self):
        print(f'STR {self.str}')
        print(f'DEX {self.dex}')
        print(f'CON {self.con}')
        print(f'INT {self.int}')
        print(f'WIS {self.wis}')
        print(f'CHA {self.cha}')

        # self.str = roll_dice(num_dice, num_sides)
        # self.dex = roll_dice(num_dice, num_sides)
        # self.con = roll_dice(num_dice, num_sides)
        # self.int = roll_dice(num_dice, num_sides)
        # self.wis = roll_dice(num_dice, num_sides)
        # self.cha = roll_dice(num_dice, num_sides)
        # print(f'STR {self.str}')
        # print(f'DEX {self.dex}')
        # print(f'CON {self.con}')
        # print(f'INT {self.int}')
        # print(f'WIS {self.wis}')
        # print(f'CHA {self.cha}')           


    def calc_ability_mod(self):
        self.str_mod = floor((self.str-10)/2)
        self.dex_mod = floor((self.dex-10)/2)
        self.con_mod = floor((self.con-10)/2)
        self.int_mod = floor((self.int-10)/2)
        self.wis_mod = floor((self.wis-10)/2)
        self.cha_mod = floor((self.cha-10)/2)
        print(self.str_mod)
        print(self.dex_mod)
        print(self.con_mod)                
        
    
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
    
    def randomize_level(self, min_num, max_num):
        if self.c_class_2 == '':
            print('this is is blank class_2')
            pre_level = random.randint(min_num, max(min_num, max_num))
            level = min(pre_level,40)
            c_class_level = level
            c_class_2_level = 0
            self.update_level(level, c_class_level, c_class_2_level)
        elif self.dip == True:
            pre_level = random.randint(min_num, max(min_num, max_num))
            level = min(pre_level,40)
            c_class_level = level-1
            c_class_2_level = 1
            self.update_level(level, c_class_level, c_class_2_level)
        else:
            pre_level = random.randint(min_num, max(min_num, max_num))
            level = min(pre_level,40)            
            pre_c_class_level = random.randint((min_num-1,level-1))
            c_class_level = min(pre_c_class_level,39)            
            c_class_2_level = level - c_class_level
            self.update_level(level, c_class_level, c_class_2_level)    

        self.capped_level_1 = min(c_class_level,20)
        self.capped_level_2 = min(c_class_2_level,20)     
        # we create capped levels for things like spells just in case we'll need it for many functions
        

    def hit_dice_calc(self):
        if self.c_class_2 != '':
            self.Hit_dice1 = self.classes[self.c_class]["hp"]
            self.Hit_dice2 = self.classes[self.c_class_2]["hp"]                    
      
            print(f"This is your character's first class Hit dice: {self.Hit_dice1}")
            print(f"This is your character's second class Hit dice: {self.Hit_dice2}")            
        else:
            self.Hit_dice1 = self.classes[self.c_class]["hp"]         
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

        if self.c_class_2 != '':
            for _ in range(self.c_class_2_level):
                print('#2 ?????????')
                hp_rolls.append(random.randint(1,self.Hit_dice2))
                print(hp_rolls) #working as expected
            self.total_hp_rolls = sum(hp_rolls)         

        return self.total_hp_rolls


    def total_hp_calc(self):               
        self.Total_HP = self.total_hp_rolls + self.Hit_dice1 + (floor(self.con-10)/2 * self.level)
        self.Total_HP = floor(self.Total_HP)
        print(f'This is your total HP: {self.Total_HP}')


    #change age/height/weight string into useable array that contains (e.g.) 5d6 -> 5,6 (5 num_dice, 6 num_sides)
    def randomize_body_feature(self, body_attribute):
        print(f'??????????????????????????{self.races[self.chosen_race][body_attribute] }')
        [base_stat, dice_string] = self.races[self.chosen_race][body_attribute]        
        # print(self.)
        print(f'before setting attribute {body_attribute}', getattr(self, body_attribute))
        [num_dice, num_sides] = [int(c) for c in dice_string.split('d')]
        dice_roll = roll_dice(num_dice, num_sides)
        setattr(self, body_attribute, base_stat+dice_roll)
        print(f'after setting attribute {body_attribute}', getattr(self, body_attribute))

    
    def get_racial_attr(self, racial_attribute):
        if self.chosen_race in self.races:
            return self.races[self.chosen_race][racial_attribute]
        
    def randomize_apperance_attr(self, apperance_attribute, upper_limit=1):
        random_app_number = random.randint(1,upper_limit)
        potential_apperances = getattr(data,apperance_attribute)
        return random.sample(potential_apperances, k=random_app_number)


    def randomize_personality_attr(self, personality_attribute, upper_limit=1):
        # redundant, JAVASCRIPT has a CSV file with all of these
        random_pers_number = random.randint(1,upper_limit)
        potential_personality = getattr(data,personality_attribute)  
        return random.sample(potential_personality,k=random_pers_number)  
        

    def choose_alignment(self, alignments):
        alignment_data = getattr(data,alignments)
        alignment_input = input("If you want to choose an alignment, type: CG CN CE NG N NE LG LN LE ").upper()
        self.alignment = alignment_data.get(alignment_input, None)

        if self.alignment is None:
            print("Invalid alignment input. Randomizing alignment:")
            random_alignment_code = random.choice(list(alignment_data.keys()))
            print(alignment_data)
            print(random_alignment_code)
            self.alignment = alignment_data[random_alignment_code].lower()

            print(self.alignment)
        else:
            self.alignment.lower()

        return self.alignment





    def randomize_deity(self):
        self.deity_choice = random.choice(list(self.deity[self.alignment]))
        return self.deity_choice


    def randomize_path_of_war_num(self, path_of_war_class):
        self.path = 0
        chance = random.randint(1,100)
        getattr(data,path_of_war_class)
        if self.c_class not in path_of_war_class:
            if self.bab == 'H':
                if chance >= 25:
                    self.path = 1
                else:
                    self.path = 0

            elif self.bab == 'M':
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
        gold_input = input("Please input a desired number for gold, otherwise we will use the amount suggest by Paizo's rules for a PC of that level")
        if gold_input.isnumeric():
            self.gold = gold_input            
        else:
            gold = getattr(data,gold)
            print(type(gold))     
            if self.level>20:
                self.gold = gold[-1]
            else:
                self.gold = gold[self.level-2]



        print(self.gold)
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
            self.feat_amounts += 1     

    def class_for_spells_attr(self):
        #currently we only know that skald spells aren't proper, but 
        # skalds use bard spell list -> just have an if statement for them
        # investigators use alchemists spells
        # + check others
                
        #This is a quick and easy function to make it so we search
        #for different spell lists than our current class
        if self.c_class in ['skald']:
            self.c_class_for_spells = 'bard'
        elif self.c_class in ['investigator']:
            self.c_class_for_spells = 'alchemist'
        elif self.c_class in ['witch', 'arcanist']:
            self.c_class_for_spells='wizard' 
        elif self.c_class in ['warpriest', 'oracle']:
            self.c_class_for_spells='cleric'                   
        else:
            self.c_class_for_spells = self.c_class     
        return self.c_class_for_spells

    # def high_caster_formula(self,n):
    #     if n % 2 == 0:
    #         self.cast_level=n // 2
    #     else:
    #         self.cast_level=(n + 1) // 2
    #     self.cast_level = min(self.cast_level,9)
    #     return self.cast_level
    
    # def mid_caster_formula(self,n):
    #     if n % 3 == 1:
    #         self.cast_level= ceil(n // 3)+1
    #     else:
    #         self.cast_level= ceil(n / 3)
    #     self.cast_level = min(n,6)
    #     return self.cast_level

    # def low_caster_formula(self,n):
    #     self.cast_level= ceil(n / 3)-1
    #     self.cast_level = min(self.cast_level,4)
    #     return self.cast_level


    def caster_formula(self,n, class_2 = None):
        self.casting_level_string = str(self.classes.get(self.c_class, "").get("casting level", "").lower())
        self.casting_level_num = self.c_class_level

        if self.casting_level_string == 'high':
            if n % 2 == 0:
                self.highest_spell_known_1=n // 2
            else:
                self.highest_spell_known_1=(n + 1) // 2
            self.highest_spell_known_1 = min(self.highest_spell_known_1,9)

        elif self.casting_level_string == 'mid':
            if n % 3 == 1:
                self.highest_spell_known_1= ceil(n // 3)+1
            else:
                self.highest_spell_known_1= ceil(n / 3)
            self.highest_spell_known_1 = min(n,6)           
       
        elif self.casting_level_string == 'low':
            self.highest_spell_known_1= ceil(n / 3)-1
            self.highest_spell_known_1 = min(self.highest_spell_known_1,4)           
            self.casting_level_num -= 3


        else:
            self.highest_spell_known_1 = 0 
            self.casting_level_num = 0

        if class_2 == None:
            return self.highest_spell_known_1    
        else:
            return self.highest_spell_known_2

    # def choose_caster_formula_1(self): 
    #     self.highest_spell_known_1=0        
    #     if self.casting_level_string == 'high':
    #         self.highest_spell_known_1 = self.high_caster_formula(self.c_class_level)
    #     elif self.casting_level_string == 'mid':
    #         self.highest_spell_known_1 = self.mid_caster_formula(self.c_class_level)
    #     elif self.casting_level_string == 'low':
    #         self.highest_spell_known_1 = self.low_caster_formula(self.c_class_level)  
    #     else:
    #         print('No caster_1 level')
    #     return self.highest_spell_known_1

    # def choose_caster_formula_2(self):  
    #     self.highest_spell_known_2=0                         
    #     if self.c_class_2 != '':
    #         casting_level_2 = str(self.classes[self.c_class_2]["casting level"].lower())              
    #         if casting_level_2 == 'high':
    #             self.highest_spell_known_2 = self.high_caster_formula(self.c_class_level)
    #         elif casting_level_2 == 'mid':
    #             self.highest_spell_known_2 = self.mid_caster_formula(self.c_class_level)
    #         elif casting_level_2 == 'low':
    #             self.highest_spell_known_2 = self.low_caster_formula(self.c_class_level)    
    #         else:
    #             print('No caster_2 level')
        
    #     return self.highest_spell_known_2
    
#need to create this for casting_level_2 as well
    def spells_known_attr(self,base_classes, divine_casters):     
        base_classes = getattr(data,base_classes)
        divine_casters=getattr(data, divine_casters)    
        self.casting_level_string = str(self.classes[self.c_class]["casting level"].lower())         
        self.spells_known_list = []
        list = []    
 

        if self.c_class in base_classes and self.casting_level_string == 'high' and self.c_class not in divine_casters:
            for i in range(0,self.highest_spell_known_1+1):
                key = str(i)
                list=self.spells_known[self.c_class][key][self.capped_level_1-1]
                self.spells_known_list.append(list)
        elif self.c_class in base_classes and self.casting_level_string == 'mid' and self.c_class not in divine_casters and self.c_class != 'alchemist':
            for i in range(0,self.highest_spell_known_1+1):
                key = str(i)                
                list=self.spells_known[self.c_class][key][self.capped_level_1-1]
                self.spells_known_list.append(list)

        #Low casters + some mid casters don't have orisons/cantrips [but we just have 0 for spells known + spells per day so it doesn't select any]
        elif self.c_class == 'alchemist':
            for i in range(0,self.highest_spell_known_1+1):
                key = str(i)                
                list=self.spells_known[self.c_class][key][self.capped_level_1-1]
                self.spells_known_list.append(list)

        elif self.c_class in base_classes and self.casting_level_string == 'low' and self.c_class not in divine_casters:
            for i in range(0,self.highest_spell_known_1+1):
                key = str(i)                
                list=self.spells_known[self.c_class][key][self.capped_level_1-1]
                self.spells_known_list.append(list)
        elif self.c_class in divine_casters:
            print('Divine Casters know all spells')
        else:
            print('Not an Arcane caster')

        return self.spells_known_list
    
    def spells_known_extra_roll(self):
        extra_spell_list = []        
        if self.c_class_for_spells in ['alchemist','wizard']:
            for i in range(0,self.highest_spell_known_1 + 1):
                extra_spells = random.randint(1,10)
                extra_spell_list.append(extra_spells)

                # Remove 'null' values and ensure both lists have the same number of non-null elements
                filtered_spells_known = [0 if x == 'null' else x for x in self.spells_known_list]
                filtered_extra_spells = extra_spell_list[:len(filtered_spells_known)]

                if filtered_spells_known[i] == 0:
                    filtered_extra_spells[i] = 0

                print(filtered_extra_spells)
                print(f'This is the spells known {filtered_spells_known}')

                # Add corresponding elements of both lists
                result = [x + y for x, y in zip(filtered_spells_known, filtered_extra_spells)]

            self.spells_known_list=result
            print(f'This is the spells known list {self.spells_known_list}')

        return self.spells_known_list

    def alignment_spell_limits(self, spell_data, i, alignment_exclusion):
        """
        Creates flags to limit spell choices to only be within the character's alignment for all classes 
        (not just cleric to make characters more thematic)

        return: query_i 
        params: spell_data (pandas file), i (number)
        """
        alignment = self.alignment.lower()
        extraction_list = ['name', self.c_class_for_spells, 'lawful', 'chaotic', 'evil', 'good']
        alignment_exclusion = getattr(data, alignment_exclusion)


        excluded_columns = set()

        for alignment_part in alignment.split(' '):
            print(f'This is your alignment part {alignment_part}')
            excluded_column = alignment_exclusion.get(alignment_part)
            if excluded_column:
                excluded_columns.add(excluded_column)

        condition = spell_data[self.c_class_for_spells] == i

        for col in excluded_columns:
            condition &= (spell_data[col] == 0)

        query_i = spell_data.loc[condition, extraction_list]

        return query_i



 


    def spells_known_selection(self,base_classes,divine_casters):
        spell_data=pd.read_csv('data/spells.csv', sep='|')
        #extraction_list = ['name', self.c_class]                
        self.spell_list = []
        self.casting_level_string = str(self.classes[self.c_class]["casting level"].lower())         
        base_classes=getattr(data,base_classes)
        divine_casters=getattr(data, divine_casters)
        i=0
        self.spell_list_choose_from=[]
        
        #separating the lists
        known_list = self.spells_known_list
        day_list = self.spells_per_day_list

        #we need to make sure we aren't grabbing null or our program will break
        if self.casting_level_string != 'none' and self.c_class in base_classes and self.c_class not in divine_casters:
            while i <= self.highest_spell_known_1:
                print(known_list)
                print(i)
                if known_list[i] != 'null':
                    select_spell=known_list[i]             

                    query_i = self.alignment_spell_limits(spell_data, i, "alignment_exclusion")
#                    query_i = spell_data.loc[spell_data[self.c_class] == i, extraction_list]
                    #needed to use this to properly randomize (vs. random.shuffle)
                    query_i = query_i.sample(frac=1.0)
                    spells = query_i[:select_spell]
                    self.spell_list_choose_from.append(spells)
                    i += 1 
                else:
                    break     

        elif self.casting_level_string != 'none' and self.c_class in divine_casters:   
            while i <= self.highest_spell_known_1:
                print(f'this is i {i}')
                print(type(day_list[i]))
                print(f"i: {i}, len(day_list): {len(day_list)}")
                print(day_list)


                if day_list[i] != 'null':
                 
                    select_spell=day_list[i]         

                    query_i = self.alignment_spell_limits(spell_data, i, "alignment_exclusion")                        

#                    query_i = spell_data.loc[(spell_data[self.c_class] == i) & (spell_data['chaotic']== 0), extraction_list]

                    #needed to use this to properly randomize (vs. random.shuffle)
                    query_i = query_i.sample(frac=1.0)
                    spells = query_i[:select_spell]
                    self.spell_list_choose_from.append(spells)
                    i += 1 
                else:
                    break                 

        else:
            print('cannot select spells_known_selection')


        return self.spell_list_choose_from



        
    
    def spells_per_day_attr(self, base_classes):
        # We have to use normal spell class, since certain classes like Arcanist or Witch have the same spells but diff progressions as wizard/sorc 
        base_classes = getattr(data,base_classes)  
        self.spells_per_day_list = []
        list = []            

        if self.c_class in base_classes and self.casting_level_string == 'high':
            for i in range(0,self.highest_spell_known_1+1):
                key = str(i)
                print(self.c_class)
                list=self.spells_per_day[self.c_class][key][self.capped_level_1-1]
                self.spells_per_day_list.append(list)
        elif self.c_class in base_classes and self.casting_level_string == 'mid' and self.c_class != 'alchemist':
            for i in range(0,mid_caster_level+1):
                key = str(i)                
                list=self.spells_per_day[self.c_class][key][self.capped_level_1-1]
                self.spells_per_day_list.append(list)

        #adding an exception for alchemist (+ other classes that don't receive cantrips)
        elif self.c_class == 'alchemist':
            for i in range(0,self.highest_spell_known_1+1):
                key = str(i)                
                list=self.spells_per_day[self.c_class][key][self.capped_level_1-1]
                self.spells_per_day_list.append(list)        
        elif self.c_class in base_classes and self.casting_level_string == 'low':
            for i in range(0,self.highest_spell_known_1+1):
                key = str(i)                
                list=self.spells_per_day[self.c_class][key][self.capped_level_1-1]
                self.spells_per_day_list.append(list)                



        else:
            print('Not an spell list caster')

        return self.spells_per_day_list            




    def spells_per_day_from_ability_mod(self, caster_mod):
        caster_mod = getattr(data,caster_mod)
        dataset = self.spells_from_ability_mod
        #for now we make sure it can't be above 17 -> otherwise breaks
        int_str = str(min(self.int_mod,17))
        wis_str = str(min(self.wis_mod,17))
        cha_str = str(min(self.cha_mod,17))
        i=0
        i_2=0
        bonus_spells = []
        if self.c_class in caster_mod["int_casters"]:
            list=dataset[int_str]          
            for i in range (self.highest_spell_known_1):
                i+=1
                spells= list[i]
                bonus_spells.append(spells)
        if self.c_class in caster_mod["wis_casters"]:
            list=dataset[wis_str]         
            for i in range (self.highest_spell_known_1):
                i+=1
                spells= list[i]
                bonus_spells.append(spells)
        if self.c_class in caster_mod["cha_casters"]:
            list=dataset[cha_str]          
            for i in range (self.highest_spell_known_1):
                i+=1
                spells= list[i]
                bonus_spells.append(spells)                                
        else:
            print('Not a caster sorry bucko')

        return bonus_spells
            






    def extra_combat_feats(self):
        #fighter_feats = [1,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40]
        monk_feats = [1,2,6,10,14,18,22,26,30,34,38,42]
        brawler_feats = [2,5,8,11,14,17,20,23,26,29,32,35,38,41] 
        ranger_feats = [2,6,10,14,18,22,26,30,34,38,42]            
        #setting up extra feats + extra feats_2 as 0 so we don't get errors
        extra_feats = 0
        extra_feats_2 = 0    
        ranger_feats_list = 0
        ranger_feats_2_list = 0
        monk_feats_list = 0 
        monk_feats_2_list = 0
        self.combat_feats_list=0

        #fighter section
        if self.c_class == 'fighter':
            extra_feats =  1 + floor((self.c_class_level)/2)

        if self.c_class_2 == 'fighter':
            extra_feats_2 = self.feat_amounts + 1 + floor((self.c_class_2_level)/2)         

        i=0
        i_2=0

        #monk section
        if self.c_class == 'monk' or self.c_class == 'unchained_monk':
            while i < len(monk_feats) and monk_feats[i] <= self.c_class_level:
                i += 1
            monk_feats_list = i

        if self.c_class == 'monk' or self.c_class == 'unchained_monk':
            while i_2 < len(monk_feats) and monk_feats[i_2] <= self.c_class_level:
                i_2 += 1

            monk_feats_2_list = i_2

        i=0
        i_2=0

        if self.c_class == 'brawler':
            while i < len(brawler_feats) and brawler_feats[i] <= self.c_class_level:
                i += 1
            extra_feats = i

        if self.c_class_2 == 'brawler':
            while i_2 < len(brawler_feats) and brawler_feats[i_2] <= self.c_class_level:
                i_2 += 1

            extra_feats_2 = i_2        

        i=0
        i_2=0

        if self.c_class == 'ranger':
            while i < len(ranger_feats) and ranger_feats[i] <= self.c_class_level:
                i += 1
            ranger_feats_list = i

        if self.c_class_2 == 'ranger':
            while i_2 < len(ranger_feats) and ranger_feats[i_2] <= self.c_class_level:
                i_2 += 1

            ranger_feats_2_list = i_2                    

        #currently we're just adding combat feats to total feats, 
        # but we may want to have them be their own separate entity
        self.combat_feats = extra_feats + extra_feats_2
        self.ranger_feats = ranger_feats_list + ranger_feats_2_list
        self.monk_feats = monk_feats_list + monk_feats_2_list
               

        return self.combat_feats          


    def extra_magic_feats(self):
        # wizard_feats = [1,5,10,15,20,25,30,35,40] 
        sorcerer_feats = [7,13,19,25,31,37,43]
        if self.c_class == 'wizard':
            magic_feats =  1 + floor((self.c_class_level)/5)

        if self.c_class_2 == 'wizard':
            magic_feats_2 = self.feat_amounts + 1 + floor((self.c_class_2_level)/5)         

        i=0
        i_2=0        

        if self.c_class == 'sorcerer':
            while i < len(sorcerer_feats) and sorcerer_feats[i] <= self.c_class_level:
                i += 1
            magic_feats = i

        if self.c_class_2 == 'sorcerer':
            while i_2 < len(sorcerer_feats) and sorcerer_feats[i_2] <= self.c_class_level:
                i_2 += 1
            magic_feats = i_2
            magic_feats_2 = i_2    

        i=0
        i_2=0        




        self.magic_feats = magic_feats + magic_feats_2
        return self.magic_feats      

    #same type of function as above, but for class abilities like
    #rogue talents, rage powers, ... 

    #Huge function for Spheres of power classes
    def class_abilities_amount(self):

        #rogues + ninja both can select rogue talents        
        if self.c_class == 'rogue' or self.c_class == 'unchained_rogue':
            rogue_talent_amount = floor(self.c_class_level/2)
        if self.c_class_2 == 'rogue' or self.c_class_2 == 'unchained_rogue':
            rogue_talent_amount = floor(self.c_class_2_level/2)  

        if self.c_class == 'ninja' :
            ninja_talent_amount = floor(self.c_class_level/2)
        if self.c_class_2 == 'ninja' :
            ninja_talent_amount = floor(self.c_class_2_level/2)               

        #skald + barbarians both select rage powers
        if self.c_class == 'barbarian' or self.c_class == 'unchained_barbarian':
            barbarian_talent_amount = floor(self.c_class_level/2)
        if self.c_class_2 == 'barbarian' or self.c_class_2 == 'unchained_barbarian':
            barbarian_talent_amount = floor(self.c_class_2_level/2)  

        if self.c_class == 'skald':
            skald_talent_amount = floor(self.c_class_level/3)
        if self.c_class_2 == 'skald':
            skald_talent_amount = floor(self.c_class_2_level/3)              



                               


    def ranger_favored_groups(self,favored_terrains,favored_enemies):
        favored_terrains=getattr(data, favored_terrains)
        favored_enemies=getattr(data, favored_enemies)
        terrains = []
        enemies = []

        if self.c_class == 'ranger':
            enemy_choice_num = 1 + floor(self.c_class_level/5)
            terrain_choice_num = ceil((self.c_class_level-2)/5) 
            terrains=random.sample(favored_terrains,k=terrain_choice_num)
            enemies=random.sample(favored_enemies,k=enemy_choice_num)            

        elif self.c_class_2 == 'ranger':
            enemy_choice_num = 1 + floor(self.c_class_2_level/5)
            terrain_choice_num = ceil((self.c_class_2_level-2)/5)      
            terrains=random.sample(favored_terrains,k=terrain_choice_num)
            enemies=random.sample(favored_enemies,k=enemy_choice_num)                     

        else:
            print('no ranger class levels')
    
        return terrains, enemies
    

    def ranger_feats_chooser(self):
        if self.c_class == 'ranger':
            ranger_feats = [2,6,10,14,18,22,26,30,34,38,42]              
            choice = list(self.ranger_combat_styles.keys())   
            random_combat_style = random.choice(choice)
            ranger_feats_chosen_list=set()     
            i=0


            while ranger_feats[i] <= self.c_class_level:
                ranger_feats_list=self.ranger_combat_styles[random_combat_style]["2"]
                
                if ranger_feats[i]>=6:
                    ranger_feats_list=(self.ranger_combat_styles[random_combat_style]["2"] + self.ranger_combat_styles[random_combat_style]["6"])
                elif ranger_feats[i]>=10:
                    ranger_feats_list=(self.ranger_combat_styles[random_combat_style]["2"] + self.ranger_combat_styles[random_combat_style]["6"] + self.ranger_combat_styles[random_combat_style]["10"])


                ranger_feats_chosen=random.choice(ranger_feats_list)
                ranger_feats_chosen_list.add(ranger_feats_chosen)
                   
                i=len(ranger_feats_chosen_list)

                if ranger_feats_chosen_list == 7:
                    break

            print(ranger_feats_chosen_list)


    def monk_feats_chooser(self):
        if self.c_class == 'monk' or self.c_class == 'unchained_monk':
            monk_feats = [1,2,6,10,14,18,22,26,30,34,38,42]   
            #using set + .add makes sure we don't have any repeats in our list           
            monk_feats_chosen_list=set()     
            i=0

            while monk_feats[i] <= self.c_class_level:
                monk_feats_list=self.monk_choices['feats']["2"]
                
                if monk_feats[i]>=6:
                    monk_feats_list=(self.monk_choices['feats']["2"] + self.monk_choices['feats']["6"])
                elif monk_feats[i]>=10:
                    monk_feats_list=(self.monk_choices['feats']["2"] + self.monk_choices['feats']["6"] + self.monk_choices['feats']["10"])


                monk_feats_chosen=random.choice(monk_feats_list)
                monk_feats_chosen_list.add(monk_feats_chosen)
                   
                i=len(monk_feats_chosen_list)

            print(monk_feats_chosen_list)


        
                         

    def wizard_opposing_school(self):
        """
        wizards choose a school of magic (elemental/other). If elemental, it always as an opposing school. If not, we grab 2 random opposing schools

        Return
        - opposing_school
        """
        elemental_list = ['metal', 'void', 'earth', 'air', 'water', 'fire']
        i = 0    

        if self.c_class == 'wizard' or self.c_class_2 == 'wizard':
            random_school, description, associated, associated_school = self.wizard_school_chooser() 
            print(random_school)            
            
            if random_school in elemental_list:
                elemental_opposing_schools = {'metal': 'wood', 'wood': 'metal', 'fire': 'water', 'water': 'fire', 'earth': 'air', 'air': 'earth'}
                opposing_school = elemental_opposing_schools.get(random_school, random.choice(elemental_list))
            else:
                school_list = (list(self.wizard_schools["schools"].keys()))
                school_list.remove('universalist')
                opposing_school = random.sample(school_list, k=2)

            print(f"THIS IS YOUR OPPOSING SCHOOL: {opposing_school}")

            return opposing_school


    def wizard_school_chooser(self):
        if self.c_class == 'wizard' or self.c_class_2 == 'wizard':        
            elemental_data = self.wizard_schools["elemental_schools"]
            schools_data = self.wizard_schools["schools"]
            elemental_subschools_data = self.wizard_schools["elemental_subschools"]
            subschools_data = self.wizard_schools["subschools"]

            associated_school = []
            associated = None

            random_choice = random.randint(1,4)
            print(f"This is the random wizard school % chance {random_choice}")


            if random_choice == 1:
                random_school = random.choice(list(elemental_data.keys()))
                description = elemental_data[random_school]

            elif random_choice == 2:            
                random_school = random.choice(list(elemental_subschools_data.keys()))
                description = elemental_subschools_data[random_school]
                associated = elemental_subschools_data[random_school]["associated school"][1]
                associated_school = elemental_data[associated]

            elif random_choice == 3:
                random_school = random.choice(list(schools_data.keys()))
                description = schools_data[random_school]

            else:
                random_school = random.choice(list(subschools_data.keys()))
                description = subschools_data[random_school]
                associated = subschools_data[random_school]["associated school"]
                associated_school = schools_data[associated]            

            print(random_school)
            print(description)
            print(associated)
            print(associated_school)

            return random_school, description, associated, associated_school
    
    def versatile_perfomance(self):
  
        choose_list = [2,6,10,14,18,22,26,30,34,38,42,46,50,54]
        self.performance_chosen_list = set()
        self.performance_chosen_description_list=[]
        self.martial_performance_choice=set()
        expanded_choice_check = set()         
        self.martial_performance_choice_description=[]  
        martial_set = set()      
        versatile_data = self.bard_choices["versatile_perfomances"]
        expanded_data = list(self.bard_choices["expanded_versatility"])
        martial_data = list(self.bard_choices["martial_performance"])

        random_chance = random.randint(1,100)
        performance_list = list(versatile_data.keys())  
        random_chance_martial=0      
        i=0


        if self.c_class == 'bard':
            performance_chosen=random.choice(performance_list)
            performance_chosen_description=versatile_data[performance_chosen]
            self.performance_chosen_description_list.append(performance_chosen_description)
            self.performance_chosen_list.add(performance_chosen)
            i=len(self.performance_chosen_list) 

            #sometimes a bard will just choose all instruments
            while choose_list[i] <= self.c_class_level and random_chance<=50:

                if len(martial_set)>=8:
                    break
                
                if len(self.performance_chosen_list)>=8:
                    break

                if random_chance_martial<=50:
                    performance_chosen=random.choice(performance_list)
                    performance_chosen_description=versatile_data[performance_chosen]
                    self.performance_chosen_list.add(performance_chosen)
                    self.performance_chosen_description_list.append(performance_chosen_description)                    
                    i=len(self.performance_chosen_list)
                    random_chance_martial = random.randint(1,100)

                if random_chance_martial>50:
                    
                    martial_choice = random.choice(martial_data)
                    martial_set.add(martial_choice)
                    print(f'This is your martial choice: {martial_choice}')
                    print(f'This is your martial choice: {martial_set}')                    
                    i=len(self.performance_chosen_list) + len(martial_set)
                    print(f'self.performance_chosen_list {self.performance_chosen_list}')
                    print(martial_set.issubset(self.performance_chosen_list))

                    if martial_set.issubset(self.performance_chosen_list) == True:
                        self.martial_performance_choice.add(martial_choice)
                        self.martial_performance_choice_description.append(self.bard_choices["martial_performance"][martial_choice])
                        random_chance_martial = random.randint(1,100)



                    #reroll random_chance martial
                    else:
                        random_chance_martial = random.randint(51,100)
                        martial_set.discard(martial_choice)
                        print(f'martial_set has bee removed {martial_set}')
                    #reroll performance
                else:
                    random_chance_martial=random.randint(1,50)


        #sometimes a bard will focus on one performance
            while choose_list[i] <= self.c_class_level and random_chance > 50:
                expanded_choice = random.choice(expanded_data)
                print(f'This is your expanded choice {expanded_choice}')                
                expanded_choice_check.add(expanded_choice)
                self.performance_chosen_description_list.append(expanded_choice)
                i=len(expanded_choice_check) + len(self.performance_chosen_list)
                print(f'the number of elements in expanded choices {i}')

                if len(expanded_choice_check)>7:
                    break
    

        print('!!!!!!!!!!!!versatile performance choices !!!!!!!!!!!!!!')
        print(self.performance_chosen_list) 
        print(self.performance_chosen_description_list)  
        print(self.martial_performance_choice)
        print(self.martial_performance_choice_description)     

        return self.performance_chosen_list, self.performance_chosen_description_list, self.martial_performance_choice, self.martial_performance_choice_description   


    # def sorcerer_bloodline_chooser(self):
    #     if self.c_class == 'sorcerer' or self.c_class_2 == 'sorcerer':   
    #         self.chosen_bloodline =  random.choice(list(self.bloodlines.keys()))
    #         print(f'This is your selected bloodline {self.chosen_bloodline} + its info: \n{self.bloodlines[self.chosen_bloodline]}')

    #         return self.chosen_bloodline

    #need to make sure cleric domain choices align with selected deity
    #inquisitors can also get domains
    def domain_chooser(self):
        self.chosen_domain = []
        if self.c_class == 'cleric' or self.c_class_2 == 'cleric':  
            deity_choice_list = list(self.deity_choice['Domains'])
            self.chosen_domain = random.sample(deity_choice_list,k=2)
            chosen_first = self.chosen_domain[0].capitalize()
            chosen_second = self.chosen_domain[1].capitalize()
#            this is randomly selecting from all without regard to Deity
#            self.chosen_domain =  random.choice(list(self.cleric_domains["domains"].keys()))
            print(f'This is your first selected domain {self.chosen_domain[0]} + its info: \n{self.cleric_domains["domains"][chosen_first]}')
            print(f'This is your second selected domain {self.chosen_domain[1]} + its info: \n{self.cleric_domains["domains"][chosen_second]}')  

        if (self.c_class == 'druid' or self.c_class_2 == 'druid' and self.domain_chance > 90):

            druid_domains_list = list(self.druid_domains.keys())
            chosen_domain = random.choice(druid_domains_list)
            print(chosen_domain)
            print(self.druid_domains[chosen_domain])
            self.chosen_domain.append(chosen_domain)

        if (self.c_class == 'inquisitor' or self.c_class_2 == 'inquisitor' and self.domain_chance > 90):

            deity_choice_list = list(self.deity_choice['Domains'])
            self.chosen_domain = random.sample(deity_choice_list,k=1)
            chosen_first = self.chosen_domain[0].capitalize()
            print(f'This is your first selected domain {self.chosen_domain[0]} + its info: \n{self.cleric_domains["domains"][chosen_first]}')

            return self.chosen_domain    


    def inquisition_chooser(self):
        if self.c_class == 'inquisitor' or self.c_class_2 == 'inquisitor' and self.domain_chance <= 90:
            inquisitions = self.inquisitions.get("inquisitions", {})
            chosen_deity = self.deity_choice['Name'][0].lower()

            print(f'this is your chosen deity!!!!! {chosen_deity}')

            valid_inquisitions = {
                inq: data for inq, data in inquisitions.items() if chosen_deity in data.get("deities", "")
            }

            if not valid_inquisitions:
                self.domain_chance = 100
                self.domain_chooser()

            else:
                self.inquisition_choice = random.choice(list(valid_inquisitions))
                print(self.inquisition_choice)

                return self.inquisition_choice



    
    #Want to make this a generic function that works for any class ability selection with complex prerequisites
    def chooseable_list(self):
        self.chooseable = set()
        #figure out how to add feats + anything else that could function as a pre-req

        return self.chooseable
    
    def chooseable_list_stats(self,attr,stat_name,base,th = None):
        while base <= int(attr):
            suffix = "th" if base >= 4 else {1: "st", 2: "nd", 3: "rd"}.get(base, "th")
            stat = str(stat_name) + str(base) + (suffix if th else "")
            self.chooseable.add(stat)
            base += 1

            print(self.chooseable)

            if base == 25:
                break

    
    def chooseable_list_class(self,i,class_1,attr,base,th = None):

        while base <= int(attr):
            even = f"{class_1} {2 * (i + 1)}"
            odd = f"{class_1} {2 * i + 1}"

            suffix = "th" if base >= 4 else {1: "st", 2: "nd", 3: "rd"}.get(base, "th")
            class_level_name = str(base) + (suffix if th else "") + " " + str(class_1) + " level" 
            class_level_name_2 = str(class_1) + " level " + str(base) + (suffix if th else "") 
            char_level_name = str(base) + (suffix if th else "") + " " + "character level" 
            char_level_name_2 = "character level " + str(base) + (suffix if th else "")  
            base += 1

            self.chooseable.update([even, odd, class_level_name, class_level_name_2, char_level_name, char_level_name_2])
            if base == 25:
                break            

    def chooseable_list_race(self):
        self.chooseable.add(self.chosen_race)

    def chooseable_list_class_features(self):
        remove_list = ["aphorite", "aquatic elf", "boggard", "dhampir", "drow", "duergar", "duskwalker", "dwarf", "elf", "fetchling", "gillman", "gnome", "half-elf", "halfling", "half-orc", "human", "kitsune", "nagaji", "oread", "ratfolk", "strix", "tengu", "wayang", "aasimar", "aquatic elf", "catfolk", "dwarf", "elf", "gathlain", "gnome", "goblin", "half-elf", "halfling", "half-orc", "hobgoblin", "human", "kitsune", "kobold", "locathah", "nagaji", "orc", "vanara", "source", "role", "alignment", "hit die", "parent class(es)", "starting wealth", "skill points at each level" ]
        class_keys_list = list(self.class_data.get(self.c_class, "").keys())
        class_keys_list = [key.strip() for key in class_keys_list if key not in remove_list]
        class_keys_list_class_feature = [key + " class feature" for key in class_keys_list]

        
        self.chooseable.update(class_keys_list)
        self.chooseable.update(class_keys_list_class_feature)
        print(self.chooseable)





    def grand_discovery_chooser(self):
        """
        At level 20 Alchemists get a grand discovery + 2 extra basic discoveries
        This function assigns a random grand discovery, unless there are the 2 basic discoveries needed for greater change alignment
        if it sees these discoveries it will auto assign greater change alignment

        outputs: chosen discovery list (appends to it)
        """
        if self.c_class == 'alchemist' and self.c_class_level >= 20:   
            discovery_list_chosen  = set()
            grand = self.alchemist['grand']
            grand_discoveries = list(grand.keys())  

            alignment_set = {"change alignment", "infusion"}

            if alignment_set.issubset(self.chooseable):
                grand_discovery_chosen = "greater change alignment"
            else:
                grand_discoveries.remove("greater change alignment")
                grand_discovery_chosen = random.choice(grand_discoveries)
                       
            discovery_list_chosen.add(grand_discovery_chosen)
            print(f'This is your chosen grand discovery {grand_discovery_chosen}')
            print(f'This is the description: {grand[grand_discovery_chosen]["benefits"]}')
            return discovery_list_chosen


        


        

    def domain_chance(self):
        """
        Some druids choose a domain, some choose an animal companion. This decides which they do
        Some inquisitors go domains instead of inquisitions
        """
        #chance to get a domain vs an animal companion
        self.domain_chance = random.randint(1,100)
        return self.domain_chance

    def animal_chooser(self):
        """
        if class = druid
        chooses between a plant, vermin, or normal animal companion for a druid
        prints out animal companion info after decidibg which companion to pick
        """
        if self.c_class == 'druid' and self.domain_chance <= 90:
            random_animal = random.randint(1,100)            
            # give all druids carry companion
            # or make it a subset of companions and make them based on region
            normal = list(self.animal_choices["normal"].keys())
            vermin = list(self.animal_choices["vermin"].keys())
            plant =list(self.animal_choices["plant"].keys())
            level = str(self.c_class_level)


            if random_animal <= 80:
                self.chosen_animal = random.choice(normal)
                self.chosen_animal_description = self.animal_choices["normal"][self.chosen_animal]
            elif random_animal <= 90:
                self.chosen_animal = random.choice(plant)
                self.chosen_animal_description = self.animal_choices["plant"][self.chosen_animal]                
            else:
                self.chosen_animal = random.choice(vermin)  
                self.chosen_animal_description = self.animal_choices["vermin"][self.chosen_animal]                


            self.companion_info = self.animal_companion["companion"][level]

            print(self.companion_info)
            print(self.chosen_animal)
            print(self.chosen_animal_description)
            return self.chosen_animal         


    def animal_feats(self):
        """
        randomly decides animal companion feats
        """
        #may want to expand animal companion feat selection later
        if self.c_class == 'druid':
            i = 0
            animal_chosen_feat_list = set()
            feats_choose = [1,3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,48,51]
            while feats_choose[i] < self.c_class_level:            
                animal_feats = list(self.animal_companion["feats"])
                chosen_feat = random.choice(animal_feats)
                animal_chosen_feat_list.add(chosen_feat)
                i = len(animal_chosen_feat_list)

                if i == 26:
                    break

            print(animal_chosen_feat_list)
            return animal_chosen_feat_list


    def json_list_grabber(self, string_list, output_list, separator):
        """
        Generic function used to grab elements from lists, you decide the separator that determines where the elemnent ends

        Return:
        - List
        """
        for string in string_list:
            elements = [element.strip() for element in string.split(separator)]
            stop_grabbing = False

            for element in elements:
                if '*' in element:
                    stop_grabbing = True
                    element = element.split('*')[0].strip()
                output_list.append(element)

            if stop_grabbing:
                break




    def brawler_manuever_chooser(self, level):
        if self.c_class == "brawler":
            amount = floor((level + 1)/4)
            manuevers = getattr(data,"manuevers")
            manuever_list = []

            i = 0
            while i < level:
                chosen = random.choice(list(manuevers))
                manuever_list.append(chosen)
                print(manuever)

                if len(manuevers) == 8:
                    break

            return manuever_list



    
    #need to implement all the restrictions to feats we want
    def feats_selector(self):             
        self.feat_list = []   
        feat_data=pd.read_csv('data/feats.csv', sep='|', on_bad_lines='skip')
        # feat_data_combat = feat_data[feat_data['type']=='Combat'] 
        feat_data_combat = feat_data[feat_data['type'].str.contains('Combat')]
        feat_data_magic = feat_data[((feat_data['type'].isin(['Creation', 'Metamagic'])) | (feat_data.name.str.contains('Spell')))]
        # | = or
        # & = and
        print(feat_data.columns)
        extraction_list = ['name', 'prerequisites']                
        self.feat_list = []      
        i=0    
        c=0    
        s=0
        #potentially remove one feat to always select a weapon focus (or spell focus)
        while i<=self.feat_amounts and self.feat_amounts != None:          
            query_i = feat_data[extraction_list]
            #needed to use this to properly randomize (vs. random.shuffle)
            query_i = query_i.sample(frac=1.0)
            feat = query_i[:1]
            self.feat_list.append(feat)
            i += 1     

        if self.combat_feats is not None and self.c_class not in ('ranger', 'monk', 'unchained_monk'):
            while c<=self.combat_feats and self.combat_feats != None:          
                query_c = feat_data_combat[extraction_list]
                #needed to use this to properly randomize (vs. random.shuffle)
                query_c = query_c.sample(frac=1.0)
                feat = query_c[:1]
                self.feat_list.append(feat)
                c += 1                 

        if self.magic_feats is not None:
            while s<=self.magic_feats:
                query_s = feat_data_magic[extraction_list]
                #needed to use this to properly randomize (vs. random.shuffle)
                query_s = query_s.sample(frac=1.0)
                feat = query_s[:1]
                self.feat_list.append(feat)
                s += 1 

        return self.feat_list




    def archetype_data(self):
        """
        Randomly selects an archetype + prints the description for the class
        Return
        - String (archetypes_choice)
        - dictionary (archetypes_description)
        """
        c_class = self.c_class.capitalize()
        json = self.archetypes[c_class]
        archetypes_list = list(json.keys())
        archetypes_choice = random.choice(archetypes_list)
        archetypes_description = json[archetypes_choice]


        print(archetypes_choice)
        print(archetypes_description)
        



    def convert_price(self,price,name):
        """
        Converts string prices to integer
        Return
        - price
        """
        
        number_pull = r'\d+'
        dynamic_variable = re.findall(number_pull, name)
        word_pull = r'\b(lesser|greater|superior|major|minor|normal|djinni|efreeti|marid|shaitan|destined|fey|abyssal|accursed|celestial|draconic|elemental|infernal|undead|aberrant)\b'
        dynamic_variable_word_pattern = re.compile(rf'(\d+){word_pull}')
        dynamic_variable_word = re.findall(word_pull, name)
        print(f'This is the dynamic variable {dynamic_variable}')
        print(f'This is the dynamic variable word {dynamic_variable_word}')
        if dynamic_variable: 
            pattern = rf'(\d{{1,3}}(?:,\d{{3}})*)\s*\(\s*\+{dynamic_variable}\)'
            print(f'1st case price {price}')
            price_list = re.findall(pattern,price)[0]
            price = int(price_list[0])
            print(f'1st case price {price}')
        elif dynamic_variable_word:
            print(f"Target word: {dynamic_variable_word[-1]}")
            price = self.find_number(price, dynamic_variable_word[-1])
            print(f"Matched price: {price}")
            price = int(price)
        else:
            if '(' in name:
                print(f'no price detected for {name} + {price}')
            price = int(price.replace(',', ''))

        if price<11:
            price = (price**2) * 1000
        return price

    def find_number(self, text, target_word):
        escaped_word = re.escape(target_word)
        pattern = r'(\d+)\D*' + escaped_word
        match = re.search(pattern, text)
        
        if match:
            return match.group(1)
        else:
            return None        


    def armor_chooser(self):
        if self.c_class in ('monk', 'unchained_monk') or self.bab == 'L':
            armor_type=None
        elif self.c_class in ('rogue', 'bard', 'brawler') or self.bab == 'M':
            armor_type='L'            
        elif self.c_class in ('barbarian', 'unchained_barbarian', 'ranger') or self.bab == 'M':
            armor_type='M'
        elif self.c_class in ('cleric'):
            armor_type='H'
        else:
            armor_type='H'

        self.armor_type = armor_type       

        return self.armor_type                           

    def item_chooser(self):    
        #we do this to skip shield (0) + armor (1) choices, since low casters typically don't use these
        if self.armor_type==None:
            i=2
        elif self.armor_type=='L' or self.weapons[1] in ('Axes', 'Blades, Heavy', 'Bows', 'Crossbows' ,'Double', 'Firearms', 'Polearms', 'Siege Engines'):
            i = 1
        else:
            i = 0

        select_from_list = list(self.items.keys())
        price_total = []
        equipment_list = []


        for i in range(i,len(select_from_list)):
            print(i)
            equipment_name = select_from_list[i]
            item_dict = self.items.get(str(select_from_list[i]))
            random_equip = random.choice(list(item_dict.keys()))
            print(random_equip)
            price = str(item_dict[random_equip]['price'])
            print(price)
            price=self.convert_price(price,random_equip)
            #removing each element form the total self gold value, to make sure people don't get too many items
            self.gold = self.gold-price
            print(f"Total Gold: {self.gold}")
            if self.gold <= 0:
                break

            print(f"Randomly selected equipment: {equipment_name} : {random_equip}")
            print("Price:", price)
            equipment_list.append(random_equip)
            price_total.append(price)

            i+=1





        print(equipment_list)
        print(price_total)




    def skills_selector(self, skills):
        """
        randomly grabs a subset of skills then assigns skill ranks to them (up to character level for each)
        to prevent any high stats characters from breaking the function, we max them out at character level for all in game skills

        param (skills list from the data section)
        return
        - skill ranks (Dictionary)
        """
        all_skills = getattr(data,skills)
        max_skill_ranks = self.c_class_level
        i=0
        
        #Quick check to make sure it doesn't break
        if self.c_class in self.class_data.keys():

            skill_points = self.class_data[self.c_class]["skill points at each level"]
            scaling = int(skill_points)+self.int_mod
            print(scaling)

        else:
            scaling= 2 + self.int_mod

        dummy_skill_ranks = scaling*self.c_class_level
        skill_number = scaling + random.randint(1,8)
        skill_number = min(skill_number,len(all_skills))
        selectable_skills = random.sample(all_skills,k=skill_number)
        skill_ranks = {}


        while i < dummy_skill_ranks:
            skill = random.choice(selectable_skills)
            ranks_to_assign = min(random.randint(1, 3), dummy_skill_ranks - i, max_skill_ranks)
            ranks_to_assign = min(ranks_to_assign, max_skill_ranks - skill_ranks.get(skill, 0))
            skill_ranks[skill] = skill_ranks.get(skill, 0) + ranks_to_assign
            i += ranks_to_assign

            if i >= dummy_skill_ranks:
                break

            if all(skill_ranks.get(skill, 0) >= max_skill_ranks for skill in selectable_skills):
                print('all skills are maxed')
                break            

        # print(skill_ranks) 
        # print(i)  
        # print(self.int_mod) 

        #confirm total ranks add up to skill ranks
        print(skill_ranks)
        print(f'This is your int mod {self.int_mod}')
        total_ranks = sum(skill_ranks.values())
        print("The total sum of ranks is:", total_ranks)

        return skill_ranks


    def profession_chooser(self,professions):
        """
        *** Will need to enhance the list, maybe redo it from scratch ***
        randomly selects a profession from the list in the data tab
        """
        n = random.randint(1,3)
        profession_data = getattr(data,professions)
        self.profession_chosen = random.sample(profession_data,k=n)

        return self.profession_chosen


    #def lore_attr(self):
    # def favored_class_bonus(self):
            


    def generic_class_option_chooser(self, class_1,  dataset_name, dataset_name_2 = None, dataset_name_3 = None, multiple = None, level=None, level_2 = None):
        if self.c_class == class_1: 
            if multiple != None:
                amount = getattr(data, 'amount', {}).get(self.c_class, {}).get(dataset_name, {})
                dataset = getattr(self, class_1, {}).get(dataset_name, {})
                dataset_list = list(dataset.keys())
                chosen_set = set()
                chosen_set_desc = []
                i = 0

                dataset_2 = getattr(self, class_1, {}).get(dataset_name_2, {})
                dataset_2_list = list(dataset_2.keys())
                # print(f'This is dataset {dataset}')    
 

                while amount[i] < self.c_class_level:
                    if dataset_name_2 != None and self.c_class_level >= level:
                        dataset_list.extend(dataset_2_list)
                        dataset.update(dataset_2)

                    if dataset_name_3 != None and self.c_class_level >= level_2:
                        dataset_list.extend(dataset_2_list)
                        dataset.update(dataset_2)                        

                    chosen = random.choice(dataset_list)
                    print(chosen)
                    chosen_set.add(chosen)
                    i = len(chosen_set)

                chosen_set_desc = [{desc: dataset[desc]} for desc in chosen_set]

                    
                print(chosen_set_desc)
                return chosen_set, chosen_set_desc





            else:
                dataset = getattr(self, class_1, {}).get(dataset_name, {}).keys()
                choice = random.choice(list(dataset))
                description = getattr(self, class_1, {None}).get(dataset_name, {None}).get(choice,{None})

                chosen_desc = {choice: description}

                print(chosen_desc)

                self.bonus_feats = self.bonus_searcher(choice, chosen_desc, 'feats')
                self.bonus_spells = self.bonus_searcher(choice, chosen_desc, 'spells')
                return chosen_desc



    # the next 3 functions are all used together

    def get_data_without_prerequisites(self, class_1, dataset_name, level= None, level_2 = None, dataset_name_2 = None, odd=None):

        if self.c_class != class_1:
            return None

        dataset_no_prereq = []
        base_no_prereq = []
        add_advanced_talents = False
        amount = floor(self.c_class_level/2)
        chosen_set = set()

        if odd == True:
            amount = ceil(self.c_class_level/2)

        
        if self.c_class == class_1:
            dataset = getattr(self, class_1, {}).get(dataset_name, {})
            base = dataset.copy()
            base_no_prereq = self.no_prereq_loop(base)
            # print(base_no_prereq)
            total_choices = base_no_prereq

            if level != None and self.c_class_level >= level:
                dataset.update( getattr(self, class_1, {}).get(dataset_name_2,{}) )
                dataset_no_prereq = self.no_prereq_loop(dataset)            

        for i in range(amount):
            chosen = random.choice(total_choices)
            even = f"{class_1} {2 * (i + 1)}"
            odd = f"{class_1} {2 * i + 1}"
            self.chooseable.update([even, odd, chosen])

            prereq_list = self.no_prereq_loop(base, "prereq_list")

            chosen_set.add(chosen.lower())
            i = len(chosen_set)

            print(f'This is your chosen set {chosen_set}')
            
            total_choices.append(chosen.lower()) 
            total_choices.extend(prereq_list)
            total_choices = self.remove_duplicates_list(total_choices)
            total_choices=list(set(total_choices))
            print(f"These are all your options to choose from: {total_choices}")


            if i>= 5 and self.c_class_level >= 10 and level == 10:
                add_advanced_talents = True
                total_choices.extend(dataset_no_prereq)                
                break


        return base_no_prereq, dataset_no_prereq, chosen_set


    def no_prereq_loop(self, dataset_type, return_choice=None):
        dataset_without_prerequisites = []
        prereq_list = set()
        # print(dataset_type.items())

        for name, info in dataset_type.items():
                prerequisites = str(info.get("prerequisites", "")).lower()
                # print(prerequisites)
                prerequisites = re.sub(r'\.', '', prerequisites)
                prerequisites_components = set(p.strip().lower() for p in prerequisites.split(","))
                # print(f'these are the components {prerequisites_components}')
                # removes both . and proficency

                if prerequisites_components.issubset(self.chooseable) == True:
                    prereq_list.add(name.lower())
                    # print(f'total prereq_list: {prereq_list}')

                if not prerequisites:
                    dataset_without_prerequisites.append(name.lower())

        if return_choice == 'prereq_list':
            return prereq_list
        else:
            return dataset_without_prerequisites                

    def generic_class_talent_chooser(self, class_1, dataset_name, dataset_name_2 = None):
        if self.c_class == class_1: 
            dataset = getattr(self, class_1, {}).get(dataset_name, {}).keys()
            choice = random.choice(list(dataset)).get(basic,{})
            description = getattr(self, class_1, {None}).get(dataset_name, {None}).get(choice,{None})

            print(choice)
            print(description)   

            return choice, description     


    def remove_duplicates_list(self, input_list):
        seen = set()
        result = []
        for item in input_list:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def generic_multi_chooser(self, class_1, dataset_name, n, n2=None):
        if self.c_class == class_1:
            dataset = getattr(self, class_1, {}).get(dataset_name, {})
            dataset_list = []
            chosen_set = set()
            chosen_list = []
            chosen_set_desc = []
            i = 0

            level = self.c_class_level   
            ii = level // 3         

            while i < ii:
                print(dataset)
                print(dataset.keys())
                if n2 != None:
                    level = (n // n2 * (i + 1))
                    string_level = str(max(level,4))
                else:
                    string_level = str((n * (i + 1)))

                dataset_list += dataset.get(string_level, [])
                print(f'This is your chooseable dataset {dataset_list}')
                chosen = random.choice(dataset_list)
                chosen_set.add(chosen)

                for condition, item in [('fatigued', 'exhausted'), ('shaken', 'frightened'),
                                        ('sickened', 'nauseated'), ('enfeebled', 'restorative'),
                                        ('injured', 'amputated')]:
                    if condition not in chosen_set:
                        chosen_set.discard(item)

                print(chosen_set)
                i = min(len(chosen_set),ii)
            return chosen_set  


    def print_metamagic(self):
        data = pd.read_csv(f'data/feats.csv', sep='|', on_bad_lines='skip')
        Metamagic_feats = data[data['type']=='Metamagic']
        extraction_list = ['name']        
        print(Metamagic_feats[extraction_list])



    # def feat_spell_searcher(self, class_1, chosen_set, types, info_column):
    #     if self.c_class == class_1:
    #         data = pd.read_csv(f'data/{types}.csv', sep='|', on_bad_lines='skip')
    #         extraction_list = ['name', info_column]


    #         # Convert chosen_set to uppercase
    #         chosen_set_upper = {i.upper() for i in chosen_set}
    #         print(f'This is your chosen set {chosen_set_upper}')

    #         # Filter DataFrame based on 'name' column
    #         if types == 'feats':
    #             query_result = data[(data['name'].str.upper().isin(chosen_set_upper)) & (data['type'] != 'Mythic')][extraction_list]
    #         else:
    #             query_result = data[(data['name'].str.upper().isin(chosen_set_upper)) & (data['mythic'] == 0)][extraction_list]



    #         result_dict = {}

    #         for index, row in query_result.iterrows():
    #             feat_name = row['name']
    #             feat_info = {f'{info_column}': row[f'{info_column}']}  # Add more fields if needed
    #             result_dict[feat_name] = feat_info

    #         self.result_dict.update(result_dict)
    #         print(self.result_dict)
            
    #         return self.result_dict            

    def feat_spell_searcher(self, class_1, chosen_set, types, info_column, info_column_2 = None):
        if self.c_class == class_1:
            data = pd.read_csv(f'data/{types}.csv', sep='|', on_bad_lines='skip')
            extraction_list = ['name', info_column, info_column_2]

            query_result = self.remove_mythic(types,data, chosen_set, extraction_list)

            result_dict = {}

            result_dict = self.remove_dots_dashes(result_dict, query_result, info_column)
            self.result_dict.update(result_dict)
            print(self.result_dict)
            
            return self.result_dict         

    def remove_mythic(self, types, data, chosen_set, extraction_list):

        chosen_set_upper = {i.upper() for i in chosen_set}
        print(f'This is your chosen set {chosen_set_upper}')

        if types == 'feats':
            query_result = data[(data['name'].str.upper().isin(chosen_set_upper)) & (data['type'] != 'Mythic')][extraction_list]
        else:
            query_result = data[(data['name'].str.upper().isin(chosen_set_upper)) & (data['mythic'] == 0)][extraction_list]  

        return query_result

    def remove_dots_dashes(self, result_dict, query_result, info_column, info_column_2=None):
        replace_dash = lambda x: re.sub(r'[-]', ' ', str(x))            
        replace_dot = lambda x: re.sub(r'[.]', '', str(x))            

        for index, row in query_result.iterrows():
            feat_name = row['name']
            if pd.isna(row[info_column]):
                row[info_column] = ''
            feat_info = {f'{info_column}': replace_dash(row[f'{info_column}'])}
            feat_info = {f'{info_column}': replace_dot(row[f'{info_column}'])}
            
            if info_column_2 is not None:
                if pd.isna(row[info_column_2]):
                    row[info_column_2] = ''
            feat_info = {f'{info_column}': replace_dash(row[f'{info_column}'])}
            feat_info = {f'{info_column}': replace_dot(row[f'{info_column}'])}

            result_dict[feat_name] = feat_info
        
        return result_dict



    def bonus_searcher(self, choice, chosen_desc, types):
        bonus_list = []
        bonus = chosen_desc.get(choice,{}).get(f"bonus {types}", {})
        self.json_list_grabber(bonus, bonus_list, ",")
        self.remove_parentheses(bonus_list)

        return bonus_list


    def remove_parentheses(self, text_list):
        result_list = []
        for text in text_list:
            pattern = r'\([^)]*\)'
            result = re.sub(pattern, '', text)
            result_list.extend(result)
        
        return result_list       
            

    def remove_duplicates_list(self,lst):
        seen = set()
        result = []
        for item in lst:
            # Convert lists to tuples for hashability
            item_tuple = tuple(item) if isinstance(item, list) else item
            if item_tuple not in seen:
                seen.add(item_tuple)
                result.append(item)
        return result

        if self.c_class == class_1: 
            options_data = self.class_data[class_1].get(data_name, {})
            print(options_data)
            if options_data:
                choice = random.choice(list(options_data.keys()))
                description = options_data.get(choice)

                print(choice)
                print(selected_value)


    def build_selector(self):
        casting_level=self.classes[self.c_class]['casting level'].lower()
        specialty_bucket = ['cleric','druid']
        type_chance = random.randint(1,100)
        feat_list = []

        if self.bab == 'H' or (self.bab == 'M' and casting_level not in ('low', 'mid', 'high')) :
            self.add_martial_feats(feat_list)

        if self.bab == 'L' and casting_level != 'none':
            self.add_magical_feats(feat_list)

        if self.bab == 'M' and casting_level != 'none' and type_chance >= 50:
            self.add_martial_feats(feat_list)
        elif self.bab == 'M' and casting_level != 'none' and type_chance < 50:
            self.add_magical_feats(feat_list)

        if self.c_class in specialty_bucket:
            self.add_specialty_feats(feat_list)

        result_dict_pre = self.feat_spell_searcher(self.c_class, feat_list, "feats", "prerequisites", "description")
        print(f'This is your result dict {result_dict_pre}')

        result_dict = self.transform_result_dict(result_dict_pre)
        print(f' post transform result_dict {result_dict}')
        chosen_feats = self.get_feats_without_prerequisites(self.c_class, result_dict, odd=True)

        print(chosen_feats)



    def add_martial_feats(self, feat_list):
        martial = self.feat_buckets['martial']
        universal = self.feat_buckets['universal']

        martial_choice = random.choice(list(martial.keys()))
        universal_choice = random.choice(list(universal.keys()))
        martial_choice_2 = random.choice(list((martial[martial_choice].keys())))
        list_2 = list(universal[universal_choice])
        list_1 = list(martial[martial_choice][martial_choice_2])
        feat_list.extend(list_1 + list_2)        

        if self.dex_mod >= self.str_mod +2:
            feat_list.append('weapon finesse')        

    def add_magical_feats(self, feat_list):
        magical = self.feat_buckets['magical']
        universal = self.feat_buckets['universal']

        magical_choice = random.choice(list(magical.keys()))
        universal_choice = random.choice(list(universal.keys()))
        list_2 = list(universal[universal_choice])
        list_1 = list(magical[magical_choice])
        feat_list.extend(list_1 + list_2)    

    def add_specialty_feats(self, feat_list):
        classes_choices = list(self.feat_buckets['classes'][self.c_class])
        feat_list.extend(classes_choices)       

    def transform_result_dict(self, result_dict):
        for feat in list(result_dict.keys()):
            feat_info = result_dict[feat]
            prereq_set = set()
            prerequisites = str(feat_info.get('prerequisites', None))

            if prerequisites is not None:
                prereq_set.add(prerequisites.lower())
                result_dict[feat]['prerequisites'] = prerequisites.lower()
                new_feat = feat.lower()

                if prerequisites.lower() == 'nan':
                    result_dict[feat]['prerequisites'] = ''
                    new_feat = ''

                if new_feat != feat:
                    result_dict[new_feat] = result_dict.pop(feat)     
        return result_dict


    def get_feats_without_prerequisites(self, class_1, dataset_name, level= None, level_2 = None, dataset_name_2 = None, odd=None):

        if self.c_class != class_1:
            return None

        dataset_no_prereq = []
        base_no_prereq = []
        add_advanced_talents = False
        amount = floor(self.c_class_level/2)
        chosen_set = set()

        if odd == True:
            amount = ceil(self.c_class_level/2)

        
        dataset = dataset_name
        base = dataset.copy()
        base_no_prereq = self.no_prereq_loop(base)
        total_choices = base_no_prereq
        i = 0
 
        while i < amount:
            print(f'This is your total choices {total_choices}')
            chosen = random.choice(total_choices)

            self.chooseable_list_class(i,self.c_class,self.c_class_level, base=0, th='th')

            prereq_list = self.no_prereq_loop(base, "prereq_list")

            chosen_set.add(chosen.lower())
            i = len(chosen_set)
            
            total_choices.append(chosen.lower()) 
            total_choices.extend(prereq_list)
            total_choices = self.remove_duplicates_list(total_choices)
            total_choices=list(set(total_choices))
            # print(f"this is total choices {total_choices}")
            # print(f'this is your chosen {chosen}')
            # print(f'This is your chosen set {chosen_set}')
            # print(f"These are all your options to choose from: {total_choices}")
            # print(f"this is your len {len(chosen_set)}")
            # print(f"this is your i {i}")
            # print(f"this is your amount {amount}")

            self.chooseable.add(chosen)

        return base_no_prereq, dataset_no_prereq, chosen_set


    def generic_feat_chooser(self, class_1,feat_type, info_column):
        if class_1 == self.c_class:
            feat_data = pd.read_csv(f'data/feats.csv', sep='|', on_bad_lines='skip')
            extraction_list = ['name', 'prerequisites', 'description']
            query_i = feat_data.loc[feat_data['type'] == feat_type.capitalize(), extraction_list]
            query_i = query_i.drop_duplicates(subset='name', keep='first')
            feat_result_dict = query_i.set_index('name')[['prerequisites', 'description']].to_dict(orient='index')
            # feat_result_dict = self.remove_mythic('feats',feat_data,query_i, info_column)   
            # feat_result_dict = self.remove_dots_dashes(feat_result_dict, query_i, info_column)
            feat_result_dict = self.transform_result_dict(feat_result_dict)

            feat_result_dict.update(feat_result_dict)

            print(f' post transform result_dict {feat_result_dict}')
            _, _, chosen_feats = self.get_feats_without_prerequisites(self.c_class, feat_result_dict, odd=True)

            print(f'These are your chosen feats {chosen_feats}')        




# setting up a new character
def CreateNewCharacter(character_json_config):
    new_char = Character(character_json_config)
    return new_char

