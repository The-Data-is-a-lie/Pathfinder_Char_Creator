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

