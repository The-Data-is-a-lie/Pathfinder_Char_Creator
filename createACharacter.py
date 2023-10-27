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
        elif self.c_class in ['witch']:
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
                list=self.spells_known[self.c_class_for_spells][key][self.c_class_level-1]
                self.spells_known_list.append(list)
        elif self.c_class in base_classes and casting_level_1 == 'mid' and self.c_class not in divine_casters and self.c_class_for_spells != 'alchemist':
            for i in range(0,self.highest_spell_known1+1):
                key = str(i)                
                list=self.spells_known[self.c_class_for_spells][key][self.c_class_level-1]
                self.spells_known_list.append(list)

        #Low casters + some mid casters don't have orisons/cantrips [but we just have 0 for spells known + spells per day so it doesn't select any]
        elif self.c_class_for_spells == 'alchemist':
            for i in range(0,self.highest_spell_known1+1):
                key = str(i)                
                list=self.spells_known[self.c_class_for_spells][key][self.c_class_level-1]
                self.spells_known_list.append(list)

        elif self.c_class in base_classes and casting_level_1 == 'low' and self.c_class not in divine_casters:
            for i in range(0,self.highest_spell_known1+1):
                key = str(i)                
                list=self.spells_known[self.c_class_for_spells][key][self.c_class_level-1]
                self.spells_known_list.append(list)
        elif self.c_class in divine_casters:
            print('Divine Casters know all spells')
        else:
            print('Not an Arcane caster')

        return self.spells_known_list
    
    def spells_known_extra_roll(self):
        extra_spell_list = []        
        if self.c_class_for_spells in ['alchemist','wizard']:
            for i in range(0,self.highest_spell_known1+1):
                extra_spells = random.randint(1,10)
                i += 1
                extra_spell_list.append(extra_spells)
            self.spells_known_list=list( map(add, self.spells_known_list, extra_spell_list) )
        return self.spells_known_list



    def spells_known_selection(self,base_classes):
        spell_data=pd.read_csv('data/spells.csv', sep='|')
        extraction_list = ['name', self.c_class]                
        self.spell_list = []
        casting_level_1 = str(self.classes[self.c_class]["casting level"].lower())         
        base_classes=getattr(data,base_classes)
        i=0
        self.spell_list_choose_from=[]
        if casting_level_1 != 'none' and self.c_class in base_classes:
            print('baba booey')
            while i < len(self.spells_known_list) and i <= self.highest_spell_known1:
                select_spell=self.spells_known_list[i]             
                query_i = spell_data.loc[spell_data[self.c_class] == i, extraction_list]
                #needed to use this to properly randomize (vs. random.shuffle)
                query_i = query_i.sample(frac=1.0)
                spells = query_i[:select_spell]
                self.spell_list_choose_from.append(spells)
                i += 1                


        else:
            print('cannot select spells_known_selection')


        return self.spell_list_choose_from



        
    
    def spells_per_day_attr(self, base_classes):
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
                list=self.spells_per_day[self.c_class_for_spells][key][self.c_class_level-1]
                self.spells_per_day_list.append(list)
        elif self.c_class in base_classes and casting_level_1 == 'mid' and self.c_class_for_spells != 'alchemist':
            for i in range(0,mid_caster_level+1):
                key = str(i)                
                list=self.spells_per_day[self.c_class_for_spells][key][self.c_class_level-1]
                self.spells_per_day_list.append(list)

        #adding an exception for alchemist (+ other classes that don't receive cantrips)
        elif self.c_class_for_spells == 'alchemist':
            for i in range(1,mid_caster_level+1):
                key = str(i)                
                list=self.spells_per_day[self.c_class_for_spells][key][self.c_class_level-1]
                self.spells_per_day_list.append(list)        
        elif self.c_class in base_classes and casting_level_1 == 'low':
            for i in range(1,low_caster_level+1):
                key = str(i)                
                list=self.spells_per_day[self.c_class_for_spells][key][self.c_class_level-1]
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



    def wizard_school_chooser(self):
        if self.c_class == 'wizard' or self.c_class_2 == 'wizard':
            school_list = ['Abjuration', 'Banishment', 'Counterspell', 'Conjuration', 'Creation', 'Extradimension', 'Infernal Binder', 'Teleportation',
            'Divination', 'Prophecy', 'Foresight', 'Scryer', 'Enchantment', 'Controller', 'Manipulator', 'Evocation', 'Admixture',
            'Generation', 'Illusion', 'Deception', 'Mage of the Veil', 'Phantasm', 'Shadow', 'Necromancy', 'Life', 'Undead',
            'Sin Magic', 'Transmutation', 'Enhancement', 'Shapechange', 'Universalist', 'Arcane Crafter',
            'Aether', 'Air', 'Ice', 'Smoke', 'Earth', 'Magma', 'Mud', 'Fire', 'Magma', 'Smoke', 'Water', 'Ice', 'Mud', 'Metal', 'Void', 'Wood']
            #making school_list lower case
            school_list = [element.lower() for element in school_list]

            opposing_school_list = ['abjuration','conjuration','divination','enchantment', 'evocation', 'illusion','necromancy', 'transmutation', 'universalist', 'air','earth', 'fire', 'water',  'metal', 'void', 'wood']
            #Wizards tend to select a chosen school
            self.chosen_school = random.sample(school_list,k=1)

            #wizards that have one chosen school have 2 prohibited schools
            self.prohibited_schools = random.sample(opposing_school_list,k=2)        
            while self.chosen_school in self.prohibited_schools:
                self.prohibited_schools.remove(self.chosen_school)


            if self.chosen_school == 'universalist':
                self.prohibited_schools == None


            return self.chosen_school, self.prohibited_schools
    

    def sorcerer_bloodline_chooser(self):
        if self.c_class == 'sorcerer' or self.c_class_2 == 'sorcerer':   
            self.chosen_bloodline =  random.choice(list(self.bloodlines.keys()))
            print(f'This is your selected bloodline {self.chosen_bloodline} + its info: \n{self.bloodlines[self.chosen_bloodline]}')

            return self.chosen_bloodline


    def paladin_mercy_chooser(self):

        self.mercy_chosen_list=set()        
        i=0      
        k=0   


        if self.c_class == 'paladin':
            paladin_list = floor(self.c_class_level/3)
        elif self.c_class_2 == 'paladin':
            paladin_list = floor(self.c_class_2_level/3) 
        else:
            paladin_list = 0
        
        while i <= (paladin_list):
            if paladin_list >= 1:
                mercy_list = self.mercies["mercy"]["3"]
            elif paladin_list >= 2:
                mercy_list = self.mercies["mercy"]["3"] + self.mercies["mercy"]["6"]
            elif paladin_list >= 3:
                mercy_list = self.mercies["mercy"]["3"] + self.mercies["mercy"]["6"] + self.mercies["mercy"]["9"]
            else:
                mercy_list = self.mercies["mercy"]["3"] + self.mercies["mercy"]["6"] + self.mercies["mercy"]["9"] + self.mercies["mercy"]["12"]                                            
            
            mercy_chosen=random.choice(mercy_list)
            self.mercy_chosen_list.add(mercy_chosen) 
 
            #need to find a better way to grab all mercies, if it selects one multiple times you have 1 less mercy
            k+=1
            print(f'NEED TO FIND A BETTER WAY TO HANDLE THIS mercy chosen list length {len(self.mercy_chosen_list)}')
            i = max(len(self.mercy_chosen_list),k)
            
           

    def get_all_prerequisites(self):
        prerequisites = set()
        for talent_name, talent_info in self.rogue_talents["advanced"].items():
            prerequisites_string = talent_info["prerequisites"]
            prerequisites_list = prerequisites_string.split(",") if prerequisites_string else []
            prerequisites.update(prerequisites_list)

        return prerequisites

    def print_unique_prerequisites(self):
        unique_prerequisites = self.get_all_prerequisites()
        print("Unique prerequisites for rogue talents:")
        for prerequisite in unique_prerequisites:
            print(prerequisite)


# opportunities aplenty
# if god = trickery + rogue -> can select jaunter talents [talents with word jaunter in them], otherwise can't
# for 
    def rogue_talent_chooser(self):
        self.rogue_talent_list=set()       
        i=0

        if self.c_class == 'rogue' or self.c_class == 'rogue_unchained':
            talent_list = floor(self.c_class_level/2)   
        elif self.c_class_2 == 'rogue' or self.c_class_2 == 'rogue_unchained':
            talent_list = floor(self.c_class_2_level/2)
        else:
            talent_list = 0

        print(talent_list)


        while i <= talent_list and talent_list != 0:
            if talent_list >= 1:
                talent_list_choice = list(self.rogue_talents["basic"].keys())
            elif talent_list >= 5:
                talent_list_choice = list(self.rogue_talents["basic"].keys()) + list(self.rogue_talents["advanced"].keys())

            talent_chosen=random.choice(talent_list_choice)
            self.rogue_talent_list.add(talent_chosen)     
            i+= 1            


            print(self.rogue_talent_list)
        return self.rogue_talent_list        
 

        

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

