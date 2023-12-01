#Internal Imports
from utils import data
import json
from utils.data import regions, weapon_groups_region, skills,  languages, hair_colors, hair_types, appearance, eye_colors#, path_of_war_class,evil_deities, good_deities, neutral_deities,
#from utils.data import archetypes
from utils.util import   roll_dice#,format_text, chooseClass, appendAttrData,  Roll_Level#,roll_4d6, roll_dice #printAttributes,
from utils.markdown import style
import random
import sys

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
        self.capped_level_1=None
        self.capped_level_2=None
    

        #Spell list variables
        #change these to prepared spells
        self.spells_list_1=None
        self.spells_list_2=None   
        self.spells_known_list=None      
        self.spells_per_day_list=None
        self.highest_spell_known1=None
        self.highest_spell_known2=None
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





        #feat selector variables
        self.feats=None
        self.combat_feats=None
        self.magic_feats=None
        self.BAB=None
        self.level=None
        self.feat_list=None
        self.monk_feats=None



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
             
        with open(json_config['ranger_combat_styles']) as f:
            self.ranger_combat_styles = json.load(f)                 

        with open(json_config['monk_choices']) as f:
            self.monk_choices = json.load(f)               

        with open(json_config['class_features']) as f:
            self.class_features = json.load(f)  

        with open(json_config['bloodlines']) as f:
            self.bloodlines = json.load(f)               

        with open(json_config['mercies']) as f:
            self.mercies = json.load(f)  

        with open(json_config['rogue_talents']) as f:
            self.rogue_talents = json.load(f)             

        with open(json_config['rage_powers']) as f:
            self.rage_powers = json.load(f)       

        with open(json_config['cleric_domains']) as f:
            self.cleric_domains = json.load(f) 

        with open(json_config['druid_domains']) as f:
            self.druid_domains = json.load(f)                       

        with open(json_config['deity']) as f:
            self.deity = json.load(f)            

        with open(json_config['items']) as f:
            self.items = json.load(f)                   

        with open(json_config['fighter_options']) as f:
            self.fighter_options = json.load(f)        

        with open(json_config['bard_choices']) as f:
            self.bard_choices = json.load(f) 

        with open(json_config['animal_companion']) as f:
            self.animal_companion = json.load(f)                  

        with open(json_config['animal_choices']) as f:
            self.animal_choices = json.load(f)          

        with open(json_config['wizard_schools']) as f:
            self.wizard_schools = json.load(f)                

        with open(json_config['alchemist_choices']) as f:
            self.alchemist_choices = json.load(f)  

        with open(json_config['class_data']) as f:
            self.class_data = json.load(f)               

        with open(json_config['cruelties']) as f:
            self.cruelties = json.load(f)    

        with open(json_config['arcanist_exploits']) as f:
            self.arcanist_exploits = json.load(f)             

        with open(json_config['cavalier_orders']) as f:
            self.cavalier_orders = json.load(f)            

        with open(json_config['gunslinger_deeds_dares']) as f:
            self.gunslinger_deeds_dares = json.load(f)                                             

        with open(json_config['inquisitions']) as f:
            self.inquisitions = json.load(f) 

    #should this be update feats, since we're updating feat amount [it 100% depends on level]
    def update_level(self, level, c_class_level, c_class_2_level):
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
        self.con = roll_dice(num_dice, num_sides)
        self.int = roll_dice(num_dice, num_sides)
        self.wis = roll_dice(num_dice, num_sides)
        self.cha = roll_dice(num_dice, num_sides)
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

    def randomize_deity(self):
        # Might want to revamp the way we randomly select deities 
        # (we could make it abit more complex and have chances to 
        # pick Lawful + Chaotic deities as well)
        # Gathering a dictionary of all deities to randomly select one
        self.deity_choice = random.choice(list(self.deity[self.alignment]))

        # deity_list = getattr(data,all_deities) 
        # if 'good' in self.alignment:
        #     return  random.choice(deity_list["good_deities"])
        # elif 'evil' in self.alignment:
        #     return  random.choice(deity_list["evil_deities"])
        # else:
        #     return  random.choice(deity_list["neutral_deities"])

        return self.deity_choice


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
        else:
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

    def choose_caster_formula_1(self): 
        self.highest_spell_known2=0        
        casting_level_1 = str(self.classes[self.c_class]["casting level"].lower())                   
        if casting_level_1 == 'high':
            self.highest_spell_known1 = self.high_caster_formula(self.c_class_level)
        elif casting_level_1 == 'mid':
            self.highest_spell_known1 = self.mid_caster_formula(self.c_class_level)
        elif casting_level_1 == 'low':
            self.highest_spell_known1 = self.low_caster_formula(self.c_class_level)  
        else:
            print('No caster_1 level')
        return self.highest_spell_known1

    def choose_caster_formula_2(self):  
        self.highest_spell_known2=0                         
        if self.c_class_2 != '':
            casting_level_2 = str(self.classes[self.c_class_2]["casting level"].lower())              
            if casting_level_2 == 'high':
                self.highest_spell_known2 = self.high_caster_formula(self.c_class_level)
            elif casting_level_2 == 'mid':
                self.highest_spell_known2 = self.mid_caster_formula(self.c_class_level)
            elif casting_level_2 == 'low':
                self.highest_spell_known2 = self.low_caster_formula(self.c_class_level)    
            else:
                print('No caster_2 level')
        
        return self.highest_spell_known2
    
#need to create this for casting_level_2 as well
    def spells_known_attr(self,base_classes, divine_casters):     
        base_classes = getattr(data,base_classes)
        divine_casters=getattr(data, divine_casters)    
        casting_level_1 = str(self.classes[self.c_class]["casting level"].lower())         
        self.spells_known_list = []
        list = []    
 

        if self.c_class in base_classes and casting_level_1 == 'high' and self.c_class not in divine_casters:
            for i in range(0,self.highest_spell_known1+1):
                key = str(i)
                list=self.spells_known[self.c_class][key][self.capped_level_1-1]
                self.spells_known_list.append(list)
        elif self.c_class in base_classes and casting_level_1 == 'mid' and self.c_class not in divine_casters and self.c_class != 'alchemist':
            for i in range(0,self.highest_spell_known1+1):
                key = str(i)                
                list=self.spells_known[self.c_class][key][self.capped_level_1-1]
                self.spells_known_list.append(list)

        #Low casters + some mid casters don't have orisons/cantrips [but we just have 0 for spells known + spells per day so it doesn't select any]
        elif self.c_class == 'alchemist':
            for i in range(0,self.highest_spell_known1+1):
                key = str(i)                
                list=self.spells_known[self.c_class][key][self.capped_level_1-1]
                self.spells_known_list.append(list)

        elif self.c_class in base_classes and casting_level_1 == 'low' and self.c_class not in divine_casters:
            for i in range(0,self.highest_spell_known1+1):
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
            for i in range(0,self.highest_spell_known1 + 1):
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


    def alignment_spell_limits(self, spell_data, i):
        """
        Creates flags to limit spell choices to only be within the character's alignment for all classes 
        (not just cleric to make characters more thematic)

        return: query_i 
        params: spell_data (pandas file), i (number)
        """
        alignment = self.alignment.lower().replace(" ", "") 
        print(alignment)
        extraction_list = ['name', self.c_class_for_spells]#, 'lawful', 'chaotic', 'evil','good']   

        condition_chaotic = "chaotic" in alignment
        condition_good = "good" in alignment
        condition_lawful = "lawful" in alignment
        condition_evil = "evil" in alignment

        if condition_chaotic and condition_good:
            condition = (spell_data['lawful'] == 0) & (spell_data['evil'] == 0)

        elif condition_chaotic:
            condition = (spell_data['lawful'] == 0)

        elif condition_good:
            condition = (spell_data['evil'] == 0)

        elif condition_lawful and condition_evil:
            condition = (spell_data['chaotic'] == 0) & (spell_data['good'] == 0)

        elif condition_lawful:
            condition = (spell_data['chaotic'] == 0)

        elif condition_evil:
            condition = (spell_data['good'] == 0)

        else:
            condition = None



        if condition is not None:
            print(condition)
            print(self.c_class_for_spells)
            query_i = spell_data.loc[(spell_data[self.c_class_for_spells] == i) & condition, extraction_list]
        else:
            query_i = spell_data.loc[(spell_data[self.c_class_for_spells] == i) & condition, extraction_list]            

        return query_i               


    def spells_known_selection(self,base_classes,divine_casters):
        spell_data=pd.read_csv('data/spells.csv', sep='|')
        #extraction_list = ['name', self.c_class]                
        self.spell_list = []
        casting_level_1 = str(self.classes[self.c_class]["casting level"].lower())         
        base_classes=getattr(data,base_classes)
        divine_casters=getattr(data, divine_casters)
        i=0
        self.spell_list_choose_from=[]
        
        #separating the lists
        known_list = self.spells_known_list
        day_list = self.spells_per_day_list

        #we need to make sure we aren't grabbing null or our program will break
        if casting_level_1 != 'none' and self.c_class in base_classes and self.c_class not in divine_casters:
            while i <= self.highest_spell_known1:
                print(known_list)
                print(i)
                if known_list[i] != 'null':
                    select_spell=known_list[i]             

                    query_i = self.alignment_spell_limits(spell_data, i)
#                    query_i = spell_data.loc[spell_data[self.c_class] == i, extraction_list]
                    #needed to use this to properly randomize (vs. random.shuffle)
                    query_i = query_i.sample(frac=1.0)
                    spells = query_i[:select_spell]
                    self.spell_list_choose_from.append(spells)
                    i += 1 
                else:
                    break     

        elif casting_level_1 != 'none' and self.c_class in divine_casters:   
            while i <= self.highest_spell_known1:
                print(f'this is i {i}')
                print(type(day_list[i]))
                print(f"i: {i}, len(day_list): {len(day_list)}")
                print(day_list)


                if day_list[i] != 'null':
                 
                    select_spell=day_list[i]         

                    query_i = self.alignment_spell_limits(spell_data, i)                        

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
        high_caster_level = self.high_caster_formula(self.c_class_level)
        mid_caster_level = self.mid_caster_formula(self.c_class_level)
        low_caster_level = self.low_caster_formula(self.c_class_level)  
        casting_level_1 = str(self.classes[self.c_class]["casting level"].lower())         
        base_classes = getattr(data,base_classes)  
        self.spells_per_day_list = []
        list = []            

        if self.c_class in base_classes and casting_level_1 == 'high':
            for i in range(0,high_caster_level+1):
                key = str(i)
                print(self.c_class)
                list=self.spells_per_day[self.c_class][key][self.capped_level_1-1]
                self.spells_per_day_list.append(list)
        elif self.c_class in base_classes and casting_level_1 == 'mid' and self.c_class != 'alchemist':
            for i in range(0,mid_caster_level+1):
                key = str(i)                
                list=self.spells_per_day[self.c_class][key][self.capped_level_1-1]
                self.spells_per_day_list.append(list)

        #adding an exception for alchemist (+ other classes that don't receive cantrips)
        elif self.c_class == 'alchemist':
            for i in range(0,mid_caster_level+1):
                key = str(i)                
                list=self.spells_per_day[self.c_class][key][self.capped_level_1-1]
                self.spells_per_day_list.append(list)        
        elif self.c_class in base_classes and casting_level_1 == 'low':
            for i in range(0,low_caster_level+1):
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
            for i in range (self.highest_spell_known1):
                i+=1
                spells= list[i]
                bonus_spells.append(spells)
        if self.c_class in caster_mod["wis_casters"]:
            list=dataset[wis_str]         
            for i in range (self.highest_spell_known1):
                i+=1
                spells= list[i]
                bonus_spells.append(spells)
        if self.c_class in caster_mod["cha_casters"]:
            list=dataset[cha_str]          
            for i in range (self.highest_spell_known1):
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
            extra_feats_2 = self.feats + 1 + floor((self.c_class_2_level)/2)         

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
            magic_feats_2 = self.feats + 1 + floor((self.c_class_2_level)/5)         

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

    def monk_ki_power_chooser(self):
        ki_powers = [4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50]
        #using set + .add makes sure we don't have any repeats in our list           
        ki_powers_chosen_list=set()     
        i=0
        ki = str(4)
        if self.c_class == 'unchained_monk':

            while ki_powers[i] <= self.c_class_level:
                ki_powers_list=self.monk_choices['ki_powers'][ki]

                ki_powers_chosen=random.choice(ki_powers_list)
                ki_powers_chosen_list.add(ki_powers_chosen)
                   
                i+=1
                ki = str(min(ki_powers[i],20))

                if ki_powers[i] == 30:
                    ki = str(16)
                    
                if ki_powers[i] == 40:
                    ki = str(14)                  

        if self.c_class_2 == 'unchained_monk':

            while ki_powers[i] <= self.c_class_2_level:
                ki_powers_list=self.monk_choices['ki_powers'][ki]

                ki_powers_chosen=random.choice(ki_powers_list)
                ki_powers_chosen_list.add(ki_powers_chosen)
                   
                i+=1
                ki = str(min(ki_powers[i],20))

                if ki_powers[i] == 30:
                    ki = str(16)
                    
                if ki_powers[i] == 40:
                    ki = str(14)                          
                


            print(ki_powers_chosen_list)            


    def fighter_armor_train_chooser(self):
        armor_train = [3,7,11,15,19,23,27,31,35,39,43,47,51]
        #using set + .add makes sure we don't have any repeats in our list           
        self.armor_chosen_list=set()   
        self.armor_chosen_list_description=[]   
        i=0



        if self.c_class == 'fighter':
            while armor_train[i] <= self.c_class_level:
                armor_train_list=self.fighter_options['armor_train']

                armor_train_chosen=random.choice(list(armor_train_list))
                armor_train_chosen_description=armor_train_list[armor_train_chosen]
                print(armor_train_chosen)
                print(armor_train_chosen_description)
                self.armor_chosen_list_description.append(armor_train_chosen_description)
                self.armor_chosen_list.add(armor_train_chosen)
                i=len(self.armor_chosen_list)

        print(self.armor_chosen_list)
        return self.armor_chosen_list, self.armor_chosen_list_description
    
    
    def fighter_weapon_train_chooser(self):

        weapon_train = [5,9,13,17,21,25,29,33,37,41,45,49,53]
        #using set + .add makes sure we don't have any repeats in our list           
        self.weapon_chosen_list=set()     
        self.weapon_chosen_list_description=[]       
        i=0



        if self.c_class == 'fighter':
            while weapon_train[i] <= self.c_class_level:
                weapon_train_list=self.fighter_options['weapon_train']

                weapon_train_chosen=random.choice(list(weapon_train_list))
                weapon_train_chosen_description=weapon_train_list[weapon_train_chosen]
                print(weapon_train_chosen)
                print(weapon_train_chosen_description)
                self.weapon_chosen_list_description.append(weapon_train_chosen_description)
                self.weapon_chosen_list.add(weapon_train_chosen)
                i=len(self.weapon_chosen_list)

        print(self.weapon_chosen_list)
        print(f"this is your fighter weapon group: {self.weapons[1]}")
        return self.weapon_chosen_list, self.weapon_chosen_list_description    
                         



    def wizard_opposing_school(self):
        elemental_list = ['metal', 'void', 'earth', 'air', 'water', 'fire']
        school_set = set()    
        i = 0    


        if self.c_class == 'wizard' or self.c_class_2 == 'wizard':
            random_school, description, associated, associated_school = self.wizard_school_chooser() 
            print(random_school)            
            if random_school in elemental_list:
                if random_school == 'metal':
                    opposing_school = 'wood'
                elif random_school == 'wood':
                    opposing_school = 'metal'
                elif random_school == 'fire':
                    opposing_school = 'water'
                elif random_school == 'water':
                    opposing_school = 'fire'
                elif random_school == 'earth':
                    opposing_school = 'air'
                elif random_school == 'air':
                    opposing_school = 'earth'                
                else:
                    opposing_school = random.choice(elemental_list)
            else:
                while i < 2:
                    opposing_school_list = list(self.wizard_schools["schools"].keys()) 
                    opposing_school = random.choice(opposing_school_list)

                    school_set.add(random_school)
                    school_set.add(opposing_school)

                    i = len(school_set)

            print(f"THIS IS YOUR OPPOSING SCHOOL SILLY BILLY {opposing_school}")

    def wizard_school_chooser(self):
        if self.c_class == 'wizard' or self.c_class_2 == 'wizard':        
            #some schools have a very different format, we may want to change that
            #add opposing schools function
            elemental = list(self.wizard_schools["elemental_schools"].keys())
            elemental_data = self.wizard_schools["elemental_schools"]
            schools = list(self.wizard_schools["schools"].keys())
            schools_data = self.wizard_schools["schools"]
            elemental_subschools = list(self.wizard_schools["elemental_subschools"].keys())
            elemental_subschools_data = self.wizard_schools["elemental_subschools"]
            subschools = list(self.wizard_schools["subschools"].keys())     
            subschools_data = self.wizard_schools["subschools"]

            random_choice = random.randint(1,4)
            random_choice = 4
            print(f"This is the random wizard school % chance {random_choice}")
            associated_school = []
            associated = None

            if random_choice == 1:
                random_school = random.choice(elemental)
                description = elemental_data[random_school]

            elif random_choice == 2:            
                random_school = random.choice(elemental_subschools)
                description = elemental_subschools_data[random_school]
                associated = elemental_subschools_data[random_school]["associated school"][1]
                associated_school = elemental_data[associated]

            elif random_choice == 3:
                random_school = random.choice(schools)
                description = schools_data[random_school]

            else:
                random_school = random.choice(subschools)
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


    def sorcerer_bloodline_chooser(self):
        if self.c_class == 'sorcerer' or self.c_class_2 == 'sorcerer':   
            self.chosen_bloodline =  random.choice(list(self.bloodlines.keys()))
            print(f'This is your selected bloodline {self.chosen_bloodline} + its info: \n{self.bloodlines[self.chosen_bloodline]}')

            return self.chosen_bloodline

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


            


    





    def arcanist_exploits_chooser(self):
        self.exploit_chosen_list=set() 
        amount = ceil(self.c_class_level / 2)
        i=0      
        k=0           
        normal = list(self.arcanist_exploits['normal'])
        greater = list(self.arcanist_exploits['greater'])
        outer = list(self.arcanist_exploits['outer'])
        combined = normal + outer

        if self.c_class == 'arcanist':
            while i < amount and i < 5:
                exploit = random.choice(combined)
                self.exploit_chosen_list.add(exploit)
                i = len(self.exploit_chosen_list)

            while i < amount and i >= 5:
                exploit = random.choice(greater)
                self.exploit_chosen_list.add(exploit)
                i = len(self.exploit_chosen_list)

            print(self.exploit_chosen_list)                






    def paladin_mercy_chooser(self):

        self.mercy_chosen_list=set()        
        i=0      
        k=0   

        list_3 = list(self.mercies["mercy"]["3"].keys())
        list_6 = list(self.mercies["mercy"]["6"].keys())
        list_9 = list(self.mercies["mercy"]["9"].keys())
        list_12 = list(self.mercies["mercy"]["12"].keys())


        if self.c_class == 'paladin':
            paladin_list = floor(self.c_class_level/3)
        elif self.c_class_2 == 'paladin':
            paladin_list = floor(self.c_class_2_level/3) 
        else:
            paladin_list = 0

                
        if self.c_class == 'paladin':
            while i < (paladin_list):
                if i == 0:
                    mercy_list = list_3
                elif i == 1:
                    mercy_list = list_3 + list_6
                elif i == 2:
                    mercy_list = list_3 + list_6 + list_9
                else:
                    mercy_list = list_3 + list_6 + list_9 + list_12
                
                #Need to remove these from the selectable list until we have the pre-reqs, we can do manually with an if statement
                if i >= 2:
                    if 'fatigued' not in self.mercy_chosen_list:
                        mercy_list.remove('exhausted')
                    if 'shaken' not in self.mercy_chosen_list:
                        mercy_list.remove('frightened')
                    if 'sickened' not in self.mercy_chosen_list:
                        mercy_list.remove('nauseated')
                    if 'enfeebled' not in self.mercy_chosen_list:
                        mercy_list.remove('restorative')
                    if i >= 3 and 'injured' not in self.mercy_chosen_list:
                        mercy_list.remove('amputated')

                print(f'This is your mercy list {mercy_list}')

                mercy_chosen=random.choice(mercy_list)
                self.mercy_chosen_list.add(mercy_chosen)


    
                #need to find a better way to grab all mercies, if it selects one multiple times you have 1 less mercy
                k+=1
                print(self.mercy_chosen_list)
                i = min(len(self.mercy_chosen_list),k)       

            return self.mercy_chosen_list  


    def anti_paladin_cruelty_chooser(self):

        self.cruelty_chosen_list=set()        
        i=0      
        k=0   

        list_3 = list(self.cruelties["cruelty"]["3"].keys())
        list_6 = list(self.cruelties["cruelty"]["6"].keys())
        list_9 = list(self.cruelties["cruelty"]["9"].keys())
        list_12 = list(self.cruelties["cruelty"]["12"].keys())


        if self.c_class == 'antipaladin':
            anti_paladin_list = floor(self.c_class_level/3)
        elif self.c_class_2 == 'antipaladin':
            anti_paladin_list = floor(self.c_class_2_level/3) 
        else:
            anti_paladin_list = 0

                
        if self.c_class == 'antipaladin':
            while i < (anti_paladin_list):
                if i == 0:
                    cruelty_list = list_3
                elif i == 1:
                    cruelty_list = list_3 + list_6
                elif i == 2:
                    cruelty_list = list_3 + list_6 + list_9
                else:
                    cruelty_list = list_3 + list_6 + list_9 + list_12
                
                #Need to remove these from the selectable list until we have the pre-reqs, we can do manually with an if statement
                if i >= 2:
                    if 'fatigued' not in self.cruelty_chosen_list:
                        cruelty_list.remove('exhausted')
                    if 'shaken' not in self.cruelty_chosen_list:
                        cruelty_list.remove('frightened')
                    if 'sickened' not in self.cruelty_chosen_list:
                        cruelty_list.remove('nauseated')

                print(f'This is your cruelty list {cruelty_list}')

                cruelty_chosen=random.choice(cruelty_list)
                self.cruelty_chosen_list.add(cruelty_chosen)


    
                #need to find a better way to grab all cruelties, if it selects one multiple times you have 1 less cruelty
                k+=1
                print(self.cruelty_chosen_list)
                i = min(len(self.cruelty_chosen_list),k)       

            return self.cruelty_chosen_list     
            
           

#start of rogue talent pre-req section

    def get_talents_without_prerequisites(self):
        talents_without_prerequisites = []
        if (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level >= 10:
            talent_groups = [self.rogue_talents["basic"]]    
        elif (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level < 10:
            talent_groups = [self.rogue_talents["advanced"], self.rogue_talents["basic"]]               
        elif (self.c_class == 'barbarian' or self.c_class == 'unchained_barbarian'):
            talent_groups = [self.rage_powers["basic"]]
        elif (self.c_class == 'alchemist' or self.c_class == 'alchemist'):
            talent_groups = [self.alchemist_choices["basic"]]            
        else:
            print("!!!!! no class abilties chosen !!!!")
            return

        for talent_group in talent_groups:
            for talent_name, talent_info in talent_group.items():
                prerequisites_string = talent_info.get("prerequisites", "")
                if not prerequisites_string:
                    talents_without_prerequisites.append(talent_name)

#        print(talents_without_prerequisites)
        return talents_without_prerequisites
    
    #Want to make this a generic function that works for any class ability selection with complex prerequisites
    def chooseable_list(self):
        self.chooseable = set()
        #figure out how to add feats + anything else that could function as a pre-req

        return self.chooseable
    
    def chooseable_list_stats(self,attr,stat_name):
        base = 10
        while base <= int(attr):
            stat = str(stat_name) + " " + str(base)
            self.chooseable.add(stat)
            base += 1

            if base == 24:
                break


    def cavalier_order_chooser(self):
        """
        Picks out a random Cavalier Order
        Return
        - String
        - Dictionary
        """
        if self.c_class == 'cavalier' or self.c_class_2 == 'cavalier':
            orders_list = list(self.cavalier_orders.keys())
            self.order_chosen = random.choice(orders_list)
            self.order_description = self.cavalier_orders[self.order_chosen]

            print(self.order_chosen)
            print(self.order_description)


            return self.order_chosen, self.order_description


    def mashing_keys(self):
        """
        
        """
        if (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level >= 10:
            talent_groups = [self.rogue_talents["basic"]]    
        elif (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level < 10:
            talent_groups = [self.rogue_talents["advanced"], self.rogue_talents["basic"]]               
        elif (self.c_class == 'barbarian' or self.c_class == 'unchained_barbarian'):
            talent_groups = [self.rage_powers["basic"]]
        elif (self.c_class == 'alchemist' or self.c_class == 'alchemist'):
            talent_groups = [self.alchemist_choices["basic"]]
     

        #our dynamic list we create, to help us isolate prereqs we meet
        prerequisites_list = set(self.chooseable)
        matching_keys = set()

        # Iterate through the JSON data
        for talent_group in talent_groups:
            for key, value in talent_group.items():
                prerequisites = value.get("prerequisites", "")
#                print(prerequisites)
                prerequisites_components = set(p.strip() for p in prerequisites.split(","))   
#                print(prerequisites_components)             

#                print(prerequisites_components.issubset(prerequisites_list))

                #this looks to see if each version of prerequisites_list is exactly in our dynamic prereq list
                if prerequisites_components.issubset(prerequisites_list) == True:
                    matching_keys.add(key)

                 

        #print(matching_keys)
        return matching_keys    
# End of rogue talent pre-req section


# opportunities aplenty
# if god = trickery + rogue -> can select jaunter talents [talents with word jaunter in them], otherwise can't
# for 

    def rogue_talent_chooser(self):
        """ If class = Rogue or Rogue (Unchained)
        First creates a list without prerequisites
        Then every even level it will add rogue talents + other pre-reqs into a big set which it checks to see
        which rogue talents are eligible to be taken

        Return
        - chosen rogue talents list + rogue talents descriptions"""
        self.rogue_talent_list=[]    
        talents_without_prerequisites = self.get_talents_without_prerequisites()     

        i=0
        even=2
        odd=1

        if self.c_class == 'rogue' or self.c_class == 'rogue_unchained':
            talent_list = floor(self.c_class_level/2)   
        elif self.c_class_2 == 'rogue' or self.c_class_2 == 'rogue_unchained':
            talent_list = floor(self.c_class_2_level/2)
        else:
            talent_list = 0
        talent_list_choice = talents_without_prerequisites
        
        while i < talent_list and talent_list != 0:
            talent_chosen = random.choice(talent_list_choice)
            print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! {talent_chosen}')
            self.rogue_talent_list.append(talent_chosen)
            set(self.rogue_talent_list)
            #assigning level values to the list, so we can select any talent with a level requirement
            rogue_k_even = "rogue " + str(even)
            rogue_k_odd = "rogue " + str(odd)
            self.chooseable.add(rogue_k_even)
            self.chooseable.add(rogue_k_odd)
            
            #adding the chosen talent to the list, so we can use it as a prerequisite for other talents
            self.chooseable.add(talent_chosen)            
            # using the mashing_keys function to cycle through all 
            # values with prerequsites [we have in self.chooseable] to add them to list
            
            ## the mashing keys function needs work, it only looks for 
            ## one word in each prerequisite vs many strings per each
            matching_keys = self.mashing_keys()
            talent_list_choice.extend(matching_keys)
        
            i = len(self.rogue_talent_list)     
            even += 2
            odd += 2



        print(self.rogue_talent_list)
        print(self.chooseable)
        return self.rogue_talent_list        
 

    def rage_power_chooser(self):
        """ If class = Barbarian or Barbarian (Unchained)
        First creates a list without prerequisites
        Then every even level it will add rage powers + other pre-reqs into a big set which it checks to see
        which rage powers are eligible to be taken

        Return
        - chosen rage power list + rage power descriptions"""

        self.rage_power_list=[]  
        rage_powers_without_prerequisites = self.get_talents_without_prerequisites()     

        i=0
        even=2
        odd=1

        if self.c_class == 'barbarian' or self.c_class == 'barbarian_unchained':
            rage_power_list = floor(self.c_class_level/2)   
        elif self.c_class_2 == 'barbarian' or self.c_class_2 == 'barbarian_unchained':
            rage_power_list = floor(self.c_class_2_level/2)
        else:
            rage_power_list = 0

        rage_power_list_choice = rage_powers_without_prerequisites
        
        while i < rage_power_list and rage_power_list != 0:
            rage_power_chosen = random.choice(rage_power_list_choice)
            print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! {rage_power_chosen}')
            self.rage_power_list.append(rage_power_chosen)
            set(self.rage_power_list)

            #assigning level values to the list, so we can select any rage_power with a level requirement
            barbarian_k_even = "barbarian " + str(even)
            barbarian_k_odd = "barbarian " + str(odd)
            self.chooseable.add(barbarian_k_even)
            self.chooseable.add(barbarian_k_odd)
            
            #adding the chosen rage_power to the list, so we can use it as a prerequisite for other rage_powers
            self.chooseable.add(rage_power_chosen)            
            # using the mashing_keys function to cycle through all 
            # values with prerequsites [we have in self.chooseable] to add them to list
            
            ## the mashing keys function needs work, it only looks for 
            ## one word in each prerequisite vs many strings per each
            matching_keys = self.mashing_keys()
            rage_power_list_choice.extend(matching_keys)
        
            i = len(self.rage_power_list)     
            even += 2
            odd += 2


    def grand_discovery_chooser(self):
        """
        At level 20 Alchemists get a grand discovery + 2 extra basic discoveries
        This function assigns a random grand discovery, unless there are the 2 basic discoveries needed for greater change alignment
        if it sees these discoveries it will auto assign greater change alignment

        outputs: chosen discovery list (appends to it)
        """
        if self.c_class == 'alchemist' and self.c_class_level >= 20:    
            grand = self.alchemist_choices['grand']
            grand_discoveries = list(grand.keys())  

            alignment_set = {"change alignment", "infusion"}

            if alignment_set.issubset(self.discovery_list_chosen):
                grand_discovery_chosen = "greater change alignment"
            else:
                grand_discoveries.remove("greater change alignment")
                grand_discovery_chosen = random.choice(grand_discoveries)
                       
            self.discovery_list_chosen.add(grand_discovery_chosen)
            print(f'This is your chosen grand discovery {grand_discovery_chosen}')
            print(f'This is the description: {grand[grand_discovery_chosen]["benefits"]}')
            return self.discovery_list_chosen


        



    def discovery_chooser(self):
        """
        If class = Alchemist
        First creates a list without prerequisites
        Then every even level it will add discoveries + other pre-reqs into a big set which it checks to see
        which discoveries are eligible to be taken

        outputs: chosen discovery list + discovery descriptions
        """
        #probably want to add a function which auto adds class + str(even) and str(odd) to the 
        #prereqs list for all classes


        #looks like we might need to redo alchemist choices, so it shows full benefits, not just from the table
        discovery_amount = (floor(self.c_class_level/2))
        #print(f'this is your discovery amount {discovery_amount}')
        i = 0
        even=2
        odd=1       
        discovery_list_chosen = set()  
        alchemist_discoveries_without_prerequisites = self.get_talents_without_prerequisites()
        discovery_list = alchemist_discoveries_without_prerequisites
      
        basic = self.alchemist_choices['basic'] 

        if self.c_class == 'alchemist':

            # at level 20 alchemists get an extra 2 discoveries
            if self.c_class_level >= 20:
                discovery_amount += 2

            while i < discovery_amount and discovery_amount != 0 :      



                alchemist_k_even = "alchemist " + str(even)
                alchemist_k_odd = "alchemist " + str(odd)   
                self.chooseable.add(alchemist_k_even)
                self.chooseable.add(alchemist_k_odd)                                                     

                discovery_chosen = random.choice(discovery_list)
                discovery_description = basic[discovery_chosen]['benefits']
                discovery_list_chosen.add(discovery_chosen) 
                self.chooseable.add(discovery_chosen)


                matching_keys = self.mashing_keys()
                discovery_list.extend(matching_keys)

                print(f'This is the chosen discovery {discovery_chosen}')
                # print(f'This is the chosen discovery description {discovery_description}')
                print(f'This is your total discover list{discovery_list_chosen}')
                # print(f'chooseable list {discovery_list}')

                print(f'This is your I value {i}')
                i = len(discovery_list_chosen)
                even += 2
                odd += 2
                
                self.discovery_list_chosen = discovery_list_chosen
         
            return self.discovery_list_chosen
        

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


    def sorcerer_feats_chooser(self):
        """
        If class = Sorcerer randomly chooses feats from each bloodline list
        Return
        - feat_list
        """
        #probably want to reformat the data to have all bloodline powers in one area (like we have it for the newest additions)
        feat_amount = [7,13,19,25,31,37,43,49]
        feat_list = set ()
        i = 0
        if self.chosen_bloodline != None:
            while feat_amount[i] < self.c_class_level:
                print(self.chosen_bloodline)
                bloodline_feats = list(self.bloodlines[self.chosen_bloodline]["bonus feats"])
                chosen_feat = random.choice(bloodline_feats)
                feat_list.add(chosen_feat)
                i = len(feat_list)

                if i >= 6:
                    break
            print(feat_list)
            return feat_list


    def sorcerer_bloodline_chooser(self):
        """
        If class = Sorcerer randomly chooses a bloodline
        Return
        - chosen_bloodline
        """
        if self.c_class == 'sorcerer' or self.c_class_2 == 'sorcerer':   
            self.chosen_bloodline =  random.choice(list(self.bloodlines.keys()))
            print(f'This is your selected bloodline {self.chosen_bloodline} + its info: \n{self.bloodlines[self.chosen_bloodline]}')

            return self.chosen_bloodline

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
        while i<=self.feats and self.feats != None:          
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


# need to scrape the data to make this better (we want pre-reqs)
    # def archetype_data(self):
    #     """
    #     Randomly selects an archetype + gives its data
    #     Return
    #     - query_ii 
    #     """
    #     #looks like we also have dupes
    #     class_string = str(self.c_class).capitalize()
    #     extraction_list = ['Archetype',  'Level',
    #    'Class Ability', 'Description']
    #     #archetype data works + reads csv correctly
    #     archetype_data = pd.read_csv(f'data/archetype_csv/{class_string}.csv', sep=',')

    #     #list of columns
    #     print(archetype_data.columns)
    #     query_i = archetype_data['Archetype']
    #     #needed to use this to properly randomize (vs. random.shuffle)
    #     query_i = query_i.sample(frac=1.0)
    #     selected_archetype = query_i[:1]
    #     index = selected_archetype.index[0]
    #     selected_archetype = selected_archetype[index]
    #     print(type(selected_archetype))
    #     print(selected_archetype)


    #     query_ii = archetype_data.loc[archetype_data["Archetype"] == selected_archetype, extraction_list]
    #     print(query_ii)


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
        



    def convert_price(self,price):
        """
        Converts string prices to integer
        Return
        - price
        """
        price = int(price.replace(',', ''))
        if price<11:
            price = (price**2) * 1000
        return price


    def armor_chooser(self):
        if self.c_class in ('monk', 'unchained_monk') or self.BAB == 'L':
            armor_type=None
        elif self.c_class in ('rogue', 'bard', 'brawler') or self.BAB == 'M':
            armor_type='L'            
        elif self.c_class in ('barbarian', 'unchained_barbarian', 'ranger') or self.BAB == 'M':
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
            dict = self.items.get(str(select_from_list[i]))
            random_equip = random.choice(list(dict.keys()))
            price = str(dict[random_equip])

            price=self.convert_price(price)
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
            






    






# Probably Delete, but not sure yet





#     def get_all_prerequisites(self):
#         prerequisites = set()
#         talent_groups = [self.rogue_talents["advanced"], self.rogue_talents["basic"]]

#         for talent_group in talent_groups:
#             for talent_info in talent_group.values():
#                 prerequisites_string = talent_info.get("prerequisites", "")
#                 prerequisites_list = [req.strip() for req in prerequisites_string.split(",") if prerequisites_string]
#                 prerequisites.update(prerequisites_list)
    
# #        print(prerequisites)
#         return prerequisites     

#     def get_talents_with_prerequisites(self):
#         talents_with_prerequisites = []
#         if (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level >= 5:
#             talent_groups = [self.rogue_talents["basic"]]    
#         else:
#             talent_groups = [self.rogue_talents["advanced"], self.rogue_talents["basic"]]

#         for talent_group in talent_groups:
#             for talent_name, talent_info in talent_group.items():
#                 prerequisites_string = talent_info.get("prerequisites", "")
#                 if prerequisites_string:
#                     talents_with_prerequisites.append(talent_name)

# #        print(talents_with_prerequisites)
#         return talents_with_prerequisites    



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

