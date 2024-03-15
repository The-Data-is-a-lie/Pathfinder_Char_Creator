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


from Backend.utils.class_func.extra_combat_feats import *
from Backend.utils.class_func.generic_func import *
from Backend.utils.class_func.chooseable import *

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
        self.feats = []
        self.ranger_feats=None
        self.ranger_combat_styles=None

        self.bonus_feats=[]
        self.bonus_spells=[]


        # Extra Flags
        


        #feat selector variables
        self.feat_amounts=None
        self.combat_feats=None
        self.magic_feats=None
        self.bab=None
        self.level=None
        self.feat_list=None
        self.monk_feats=None
        self.result_dict={}
        self.total_feats = []



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

        return stats

    def assign_stats(self, stats):
        for attr, value in stats.items():
            setattr(self, attr, value)

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

    def calc_ability_mod(self):
        self.str_mod = floor((self.str-10)/2)
        self.dex_mod = floor((self.dex-10)/2)
        self.con_mod = floor((self.con-10)/2)
        self.int_mod = floor((self.int-10)/2)
        self.wis_mod = floor((self.wis-10)/2)
        self.cha_mod = floor((self.cha-10)/2)
               
        
    
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
        return self.Total_HP






    def randomize_personality_attr(self, personality_attribute, upper_limit=1):
        # redundant, JAVASCRIPT has a CSV file with all of these
        random_pers_number = random.randint(1,upper_limit)
        potential_personality = getattr(data,personality_attribute)  
        return random.sample(potential_personality,k=random_pers_number)  
        

    def choose_alignment(self, alignments, alignment_input):
        alignment_data = getattr(data,alignments)
        # alignment_input = input("If you want to choose an alignment, type: CG CN CE NG N NE LG LN LE ").upper()
        self.alignment = alignment_data.get(alignment_input, None)

        if self.alignment is None:
            print("Invalid alignment input. Randomizing alignment:")
            random_alignment_code = random.choice(list(alignment_data.keys()))
            print(alignment_data)
            print(random_alignment_code)
            self.alignment = alignment_data[random_alignment_code].lower()

            print(self.alignment)
        else:
            self.alignment = self.alignment.lower()

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



    def assign_gold(self,gold, gold_num):
        # gold_input = input("Please input a desired number for gold, otherwise we will use the amount suggest by Paizo's rules for a PC of that level")
        gold_input = gold_num
        if isinstance(gold_input, int):
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





    def json_list_grabber(self, string_list, separator, output_list=None):
        """
        Generic function used to grab elements from lists, you decide the separator that determines where the elemnent ends

        Return:
        - List
        """
        if output_list == None:
            output_list = []

        for string in string_list:
            print("string", string)
            elements = [element.strip() for element in string.split(separator)]
            print("elements", elements)
            stop_grabbing = False

            for element in elements:
                if '*' in element:
                    stop_grabbing = True
                    element = element.split('*')[0].strip()
                output_list.append(element)

            if stop_grabbing:
                break

        return output_list
    
    ################################# We're not actually using this

    # #need to implement all the restrictions to feats we want
    # def feats_selector(self):             
    #     self.feat_list = []   
    #     feat_data=pd.read_csv('data/feats.csv', sep='|', on_bad_lines='skip')
    #     # feat_data_combat = feat_data[feat_data['type']=='Combat'] 
    #     feat_data_combat = feat_data[feat_data['type'].str.contains('Combat')]
    #     feat_data_magic = feat_data[((feat_data['type'].isin(['Creation', 'Metamagic'])) | (feat_data.name.str.contains('Spell')))]
    #     # | = or
    #     # & = and
    #     print(feat_data.columns)
    #     extraction_list = ['name', 'prerequisites']                
    #     self.feat_list = []      
    #     i=0    
    #     c=0    
    #     s=0
    #     #potentially remove one feat to always select a weapon focus (or spell focus)
    #     while i<=self.feat_amounts and self.feat_amounts != None:          
    #         query_i = feat_data[extraction_list]
    #         #needed to use this to properly randomize (vs. random.shuffle)
    #         query_i = query_i.sample(frac=1.0)
    #         feat = query_i[:1]
    #         self.feat_list.append(feat)
    #         i += 1     

    #     if self.combat_feats is not None and self.c_class not in ('ranger', 'monk', 'unchained_monk'):
    #         while c<=self.combat_feats and self.combat_feats != None:          
    #             query_c = feat_data_combat[extraction_list]
    #             #needed to use this to properly randomize (vs. random.shuffle)
    #             query_c = query_c.sample(frac=1.0)
    #             feat = query_c[:1]
    #             self.feat_list.append(feat)
    #             c += 1                 

    #     if self.magic_feats is not None:
    #         while s<=self.magic_feats:
    #             query_s = feat_data_magic[extraction_list]
    #             #needed to use this to properly randomize (vs. random.shuffle)
    #             query_s = query_s.sample(frac=1.0)
    #             feat = query_s[:1]
    #             self.feat_list.append(feat)
    #             s += 1 

    #     return self.feat_list




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
            



    # the next 3 functions are all used together










    def full_data_dictionary(self, data_dict, key, value):
        data_dict[key] = value
        return data_dict

    def instantiate_full_data_dict(self):
        self.data_dict = {'class features': []}
        return self.data_dict
    
    def export_list_non_dict(self, export_list, string_export_list):
        chosen_dict = {string_key: variable_value for string_key, variable_value in zip(string_export_list, export_list)}
        self.data_dict.update(chosen_dict)
        return chosen_dict        
    
    def export_list_dict(self, export_list, string_export_list):
        chosen_dict = dict(zip(string_export_list, export_list))
        self.data_dict.update(chosen_dict)
        return chosen_dict

# setting up a new character
def CreateNewCharacter(character_json_config):
    new_char = Character(character_json_config)
    return new_char

