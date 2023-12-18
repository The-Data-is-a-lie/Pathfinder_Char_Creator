    # def _load_jsons(self, json_config):
    #     with open(json_config['race']) as f:
    #         self.races = json.load(f)
    #         self.unique_races = self.races.keys()

    #     with open(json_config['class']) as f:
    #         self.classes = json.load(f)

    #     with open(json_config['traits']) as f:
    #         self.traits_abilities = json.load(f)
    #         random.shuffle(self.traits_abilities)

    #     with open(json_config['profession']) as f:
    #         self.professions = json.load(f)
    #         random.shuffle(self.professions)

    #     with open(json_config['last_names_regions']) as f:
    #         self.last_names_regions = json.load(f)
    #     self.regions = [k for k in self.last_names_regions.keys()]

    #     with open(json_config['first_names_regions']) as f:
    #         self.first_names_regions = json.load(f)
        
    #     with open(json_config['flaws']) as f:
    #         self.flaws = json.load(f)  

    #     with open(json_config['archetypes']) as f:
    #         self.archetypes = json.load(f)             

    #     with open(json_config['spells_known']) as f:
    #         self.spells_known = json.load(f)      

    #     with open(json_config['spells_per_day']) as f:
    #         self.spells_per_day = json.load(f)      

    #     with open(json_config['spells_from_ability_mod']) as f:
    #         self.spells_from_ability_mod = json.load(f)                                          
             
    #     with open(json_config['ranger_combat_styles']) as f:
    #         self.ranger_combat_styles = json.load(f)                 

    #     with open(json_config['monk_choices']) as f:
    #         self.monk_choices = json.load(f)               

    #     with open(json_config['class_features']) as f:
    #         self.class_features = json.load(f)  

    #     with open(json_config['bloodlines']) as f:
    #         self.bloodlines = json.load(f)               

    #     with open(json_config['cleric_domains']) as f:
    #         self.cleric_domains = json.load(f) 

    #     with open(json_config['druid_domains']) as f:
    #         self.druid_domains = json.load(f)                       

    #     with open(json_config['deity']) as f:
    #         self.deity = json.load(f)            

    #     with open(json_config['items']) as f:
    #         self.items_best = json.load(f)                   

    #     with open(json_config['bard_choices']) as f:
    #         self.bard_choices = json.load(f) 

    #     with open(json_config['animal_companion']) as f:
    #         self.animal_companion = json.load(f)                  

    #     with open(json_config['animal_choices']) as f:
    #         self.animal_choices = json.load(f)          

    #     with open(json_config['wizard_schools']) as f:
    #         self.wizard_schools = json.load(f)                

    #     with open(json_config['class_data']) as f:
    #         self.class_data = json.load(f)               

    #     with open(json_config['gunslinger_deeds_dares']) as f:
    #         self.gunslinger_deeds_dares = json.load(f)             

    #     with open(json_config['antipaladin']) as f:
    #         self.antipaladin = json.load(f)    

    #     with open(json_config['arcanist']) as f:
    #         self.arcanist = json.load(f)    

    #     with open(json_config['fighter']) as f:
    #         self.fighter = json.load(f)                    

    #     with open(json_config['barbarian']) as f:
    #         self.barbarian = json.load(f)   

    #     with open(json_config['skald']) as f:
    #         self.skald = json.load(f)               

    #     with open(json_config['cavalier']) as f:
    #         self.cavalier = json.load(f)                                                     

    #     with open(json_config['inquisitor']) as f:
    #         self.inquisitor = json.load(f) 

    #     with open(json_config['investigator']) as f:
    #         self.investigator = json.load(f)           

    #     with open(json_config['paladin']) as f:
    #         self.paladin = json.load(f)   

    #     with open(json_config['ninja']) as f:
    #         self.ninja = json.load(f)                             

    #     with open(json_config['warpriest']) as f:
    #         self.warpriest = json.load(f) 

    #     with open(json_config['rogue']) as f:
    #         self.rogue = json.load(f)          

    #     with open(json_config['alchemist']) as f:
    #         self.alchemist = json.load(f)        

    #     with open(json_config['witch']) as f:
    #         self.witch = json.load(f)      

    #     with open(json_config['oracle']) as f:
    #         self.oracle = json.load(f)         

    #     with open(json_config['vigilante']) as f:
    #         self.vigilante = json.load(f)                                

    #     with open(json_config['samurai']) as f:
    #         self.samurai = json.load(f)    

    #     with open(json_config['slayer']) as f:
    #         self.slayer = json.load(f)    
            
    #     with open(json_config['shaman']) as f:





        # def randomize_alignment(self, alignments):
    #     #pulling alignments from data.py and picking one
    #     alignment_data = getattr(data,alignments)
    #     print(random_alignment_code)

    #     return self.alignment






   # def alignment_spell_limits(self, spell_data, i):
    #     """
    #     Creates flags to limit spell choices to only be within the character's alignment for all classes 
    #     (not just cleric to make characters more thematic)

    #     return: query_i 
    #     params: spell_data (pandas file), i (number)
    #     """
    #     alignment = self.alignment.lower()
    #     print(alignment)
    #     extraction_list = ['name', self.c_class_for_spells, 'lawful', 'chaotic', 'evil','good']   

    #     condition_chaotic = "chaotic" in alignment
    #     condition_good = "good" in alignment
    #     condition_lawful = "lawful" in alignment
    #     condition_evil = "evil" in alignment

    #     if condition_chaotic and condition_good:
    #         condition = (spell_data['lawful'] == 0) & (spell_data['evil'] == 0)

    #     elif condition_chaotic and condition_evil:
    #         condition = (spell_data['lawful'] == 0) & (spell_data['good'] == 0)

    #     elif condition_lawful and condition_evil:
    #         condition = (spell_data['chaotic'] == 0) & (spell_data['good'] == 0)

    #     elif condition_lawful and condition_good:
    #         condition = (spell_data['chaotic'] == 0) & (spell_data['evil'] == 0)

    #     elif condition_lawful:
    #         condition = (spell_data['chaotic'] == 0)

    #     elif condition_evil:
    #         condition = (spell_data['good'] == 0)

    #     elif condition_chaotic:
    #         condition = (spell_data['lawful'] == 0)

    #     elif condition_good:
    #         condition = (spell_data['evil'] == 0)

    #     else:
    #         condition = None



    #     if condition is not None:
    #         print(condition)
    #         print(self.c_class_for_spells)
    #         query_i = spell_data.loc[(spell_data[self.c_class_for_spells] == i) & condition, extraction_list]
    #     else:
    #         query_i = spell_data.loc[(spell_data[self.c_class_for_spells] == i) & condition, extraction_list]            

    #     return query_i         
    # 



    # def monk_ki_power_chooser(self):
    #     ki_powers = [4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50]
    #     #using set + .add makes sure we don't have any repeats in our list           
    #     ki_powers_chosen_list=set()     
    #     i=0
    #     ki = str(4)
    #     if self.c_class == 'unchained_monk':

    #         while ki_powers[i] <= self.c_class_level:
    #             ki_powers_list=self.monk_choices['ki_powers'][ki]

    #             ki_powers_chosen=random.choice(ki_powers_list)
    #             ki_powers_chosen_list.add(ki_powers_chosen)
                   
    #             i+=1
    #             ki = str(min(ki_powers[i],20))

    #             if ki_powers[i] == 30:
    #                 ki = str(16)
                    
    #             if ki_powers[i] == 40:
    #                 ki = str(14)                  

    #     if self.c_class_2 == 'unchained_monk':

    #         while ki_powers[i] <= self.c_class_2_level:
    #             ki_powers_list=self.monk_choices['ki_powers'][ki]

    #             ki_powers_chosen=random.choice(ki_powers_list)
    #             ki_powers_chosen_list.add(ki_powers_chosen)
                   
    #             i+=1
    #             ki = str(min(ki_powers[i],20))

    #             if ki_powers[i] == 30:
    #                 ki = str(16)
                    
    #             if ki_powers[i] == 40:
    #                 ki = str(14)                          
                


    #         print(ki_powers_chosen_list)            


    # def fighter_armor_train_chooser(self):
    #     armor_train = [7,11,15,19,23,27,31,35,39,43,47,51]
    #     #using set + .add makes sure we don't have any repeats in our list           
    #     self.armor_chosen_list=set()   
    #     self.armor_chosen_list_description=[]   
    #     i=0



    #     if self.c_class == 'fighter':
    #         while armor_train[i] <= self.c_class_level:
    #             armor_train_list=self.fighter_options['armor_train']

    #             armor_train_chosen=random.choice(list(armor_train_list))
    #             armor_train_chosen_description=armor_train_list[armor_train_chosen]
    #             print(armor_train_chosen)
    #             print(armor_train_chosen_description)
    #             self.armor_chosen_list_description.append(armor_train_chosen_description)
    #             self.armor_chosen_list.add(armor_train_chosen)
    #             i=len(self.armor_chosen_list)

    #     print(self.armor_chosen_list)
    #     return self.armor_chosen_list, self.armor_chosen_list_description
    
    
    # def fighter_weapon_train_chooser(self):

    #     weapon_train = [9,13,17,21,25,29,33,37,41,45,49,53]
    #     #using set + .add makes sure we don't have any repeats in our list           
    #     self.weapon_chosen_list=set()     
    #     self.weapon_chosen_list_description=[]       
    #     i=0



        # if self.c_class == 'fighter':
        #     while weapon_train[i] <= self.c_class_level:
        #         weapon_train_list=self.fighter_options['weapon_train']

        #         weapon_train_chosen=random.choice(list(weapon_train_list))
        #         weapon_train_chosen_description=weapon_train_list[weapon_train_chosen]
        #         print(weapon_train_chosen)
        #         print(weapon_train_chosen_description)
        #         self.weapon_chosen_list_description.append(weapon_train_chosen_description)
        #         self.weapon_chosen_list.add(weapon_train_chosen)
        #         i=len(self.weapon_chosen_list)

        # print(self.weapon_chosen_list)
        # print(f"this is your fighter weapon group: {self.weapons[1]}")
        # return self.weapon_chosen_list, self.weapon_chosen_list_description    




    # def arcanist_exploits_chooser(self):
    #     self.exploit_chosen_list=set() 
    #     amount = ceil(self.c_class_level / 2)
    #     i=0      
    #     k=0           
    #     normal = list(self.arcanist_exploits['normal'])
    #     greater = list(self.arcanist_exploits['greater'])
    #     outer = list(self.arcanist_exploits['outer'])
    #     combined = normal + outer

    #     if self.c_class == 'arcanist':
    #         while i < amount and i < 5:
    #             exploit = random.choice(combined)
    #             self.exploit_chosen_list.add(exploit)
    #             i = len(self.exploit_chosen_list)

    #         while i < amount and i >= 5:
    #             exploit = random.choice(greater)
    #             self.exploit_chosen_list.add(exploit)
    #             i = len(self.exploit_chosen_list)

    #         print(self.exploit_chosen_list)                


    # def paladin_mercy_chooser(self):

    #     self.mercy_chosen_list=set()        
    #     i=0      
    #     k=0   

    #     list_3 = list(self.mercies["mercy"]["3"].keys())
    #     list_6 = list(self.mercies["mercy"]["6"].keys())
    #     list_9 = list(self.mercies["mercy"]["9"].keys())
    #     list_12 = list(self.mercies["mercy"]["12"].keys())


    #     if self.c_class == 'paladin':
    #         paladin_list = floor(self.c_class_level/3)
    #     elif self.c_class_2 == 'paladin':
    #         paladin_list = floor(self.c_class_2_level/3) 
    #     else:
    #         paladin_list = 0

                
    #     if self.c_class == 'paladin':
    #         while i < (paladin_list):
    #             if i == 0:
    #                 mercy_list = list_3
    #             elif i == 1:
    #                 mercy_list = list_3 + list_6
    #             elif i == 2:
    #                 mercy_list = list_3 + list_6 + list_9
    #             else:
    #                 mercy_list = list_3 + list_6 + list_9 + list_12
                
    #             #Need to remove these from the selectable list until we have the pre-reqs, we can do manually with an if statement
    #             if i >= 2:
    #                 if 'fatigued' not in self.mercy_chosen_list:
    #                     mercy_list.remove('exhausted')
    #                 if 'shaken' not in self.mercy_chosen_list:
    #                     mercy_list.remove('frightened')
    #                 if 'sickened' not in self.mercy_chosen_list:
    #                     mercy_list.remove('nauseated')
    #                 if 'enfeebled' not in self.mercy_chosen_list:
    #                     mercy_list.remove('restorative')
    #                 if i >= 3 and 'injured' not in self.mercy_chosen_list:
    #                     mercy_list.remove('amputated')

    #             print(f'This is your mercy list {mercy_list}')

    #             mercy_chosen=random.choice(mercy_list)
    #             self.mercy_chosen_list.add(mercy_chosen)


    
    #             #need to find a better way to grab all mercies, if it selects one multiple times you have 1 less mercy
    #             k+=1
    #             print(self.mercy_chosen_list)
    #             i = min(len(self.mercy_chosen_list),k)       

    #         return self.mercy_chosen_list  


    # def anti_paladin_cruelty_chooser(self):

    #     self.cruelty_chosen_list=set()        
    #     i=0      
    #     k=0   

    #     list_3 = list(self.cruelties["cruelty"]["3"].keys())
    #     list_6 = list(self.cruelties["cruelty"]["6"].keys())
    #     list_9 = list(self.cruelties["cruelty"]["9"].keys())
    #     list_12 = list(self.cruelties["cruelty"]["12"].keys())


    #     if self.c_class == 'antipaladin':
    #         anti_paladin_list = floor(self.c_class_level/3)
    #     elif self.c_class_2 == 'antipaladin':
    #         anti_paladin_list = floor(self.c_class_2_level/3) 
    #     else:
    #         anti_paladin_list = 0

                
    #     if self.c_class == 'antipaladin':
    #         while i < (anti_paladin_list):
    #             if i == 0:
    #                 cruelty_list = list_3
    #             elif i == 1:
    #                 cruelty_list = list_3 + list_6
    #             elif i == 2:
    #                 cruelty_list = list_3 + list_6 + list_9
    #             else:
    #                 cruelty_list = list_3 + list_6 + list_9 + list_12
                
    #             #Need to remove these from the selectable list until we have the pre-reqs, we can do manually with an if statement
    #             if i >= 2:
    #                 if 'fatigued' not in self.cruelty_chosen_list:
    #                     cruelty_list.remove('exhausted')
    #                 if 'shaken' not in self.cruelty_chosen_list:
    #                     cruelty_list.remove('frightened')
    #                 if 'sickened' not in self.cruelty_chosen_list:
    #                     cruelty_list.remove('nauseated')

    #             print(f'This is your cruelty list {cruelty_list}')

    #             cruelty_chosen=random.choice(cruelty_list)
    #             self.cruelty_chosen_list.add(cruelty_chosen)


    
    #             #need to find a better way to grab all cruelties, if it selects one multiple times you have 1 less cruelty
    #             k+=1
    #             print(self.cruelty_chosen_list)
    #             i = min(len(self.cruelty_chosen_list),k)       

    #         return self.cruelty_chosen_list     
            
           

#start of rogue talent pre-req section

#     def get_talents_without_prerequisites(self):
#         talents_without_prerequisites = []
#         if (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level >= 10:
#             talent_groups = [self.rogue_talents["basic"]]    
#         elif (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level < 10:
#             talent_groups = [self.rogue_talents["advanced"], self.rogue_talents["basic"]]               
#         elif (self.c_class == 'barbarian' or self.c_class == 'unchained_barbarian'):
#             talent_groups = [self.rage_powers["basic"]]
#         elif (self.c_class == 'alchemist' or self.c_class == 'alchemist'):
#             talent_groups = [self.alchemist_choices["basic"]]            
#         else:
#             print("!!!!! no class abilties chosen !!!!")
#             return

#         for talent_group in talent_groups:
#             for talent_name, talent_info in talent_group.items():
#                 prerequisites_string = talent_info.get("prerequisites", "")
#                 if not prerequisites_string:
#                     talents_without_prerequisites.append(talent_name)

# #        print(talents_without_prerequisites)
#         return talents_without_prerequisites



    # def cavalier_order_chooser(self):
    #     """
    #     Picks out a random Cavalier Order
    #     Return
    #     - String
    #     - Dictionary
    #     """
    #     if self.c_class == 'cavalier' or self.c_class_2 == 'cavalier':
    #         orders_list = list(self.cavalier.keys())
    #         self.order_chosen = random.choice(orders_list)
    #         self.order_description = self.cavalier[self.order_chosen]

    #         print(self.order_chosen)
    #         print(self.order_description)


    #         return self.order_chosen, self.order_description

#     def get_talents_without_prerequisites(self):
#         talents_without_prerequisites = []
#         if (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level >= 10:
#             talent_groups = [self.rogue_talents["basic"]]    
#         elif (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level < 10:
#             talent_groups = [self.rogue_talents["advanced"], self.rogue_talents["basic"]]               
#         elif (self.c_class == 'barbarian' or self.c_class == 'unchained_barbarian'):
#             talent_groups = [self.rage_powers["basic"]]
#         elif (self.c_class == 'alchemist' or self.c_class == 'alchemist'):
#             talent_groups = [self.alchemist_choices["basic"]]            
#         else:
#             print("!!!!! no class abilties chosen !!!!")
#             return

#         for talent_group in talent_groups:
#             for talent_name, talent_info in talent_group.items():
#                 prerequisites_string = talent_info.get("prerequisites", "")
#                 if not prerequisites_string:
#                     talents_without_prerequisites.append(talent_name)

# #        print(talents_without_prerequisites)
#         return talents_without_prerequisites

#     def mashing_keys(self):
#         """
        
#         """
#         if (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level >= 10:
#             talent_groups = [self.rogue_talents["basic"]]    
#         elif (self.c_class == 'rogue' or self.c_class == 'unchained_rogue') and self.c_class_level < 10:
#             talent_groups = [self.rogue_talents["advanced"], self.rogue_talents["basic"]]               
#         elif (self.c_class == 'barbarian' or self.c_class == 'unchained_barbarian'):
#             talent_groups = [self.rage_powers["basic"]]
#         elif (self.c_class == 'alchemist' or self.c_class == 'alchemist'):
#             talent_groups = [self.alchemist_choices["basic"]]
     

#         #our dynamic list we create, to help us isolate prereqs we meet
#         prerequisites_list = set(self.chooseable)
#         matching_keys = set()

#         # Iterate through the JSON data
#         for talent_group in talent_groups:
#             for key, value in talent_group.items():
#                 prerequisites = value.get("prerequisites", "")
# #                print(prerequisites)
#                 prerequisites_components = set(p.strip() for p in prerequisites.split(","))   
# #                print(prerequisites_components)             

# #                print(prerequisites_components.issubset(prerequisites_list))

#                 #this looks to see if each version of prerequisites_list is exactly in our dynamic prereq list
#                 if prerequisites_components.issubset(prerequisites_list) == True:
#                     matching_keys.add(key)

                 

#         #print(matching_keys)
#         return matching_keys    
# End of rogue talent pre-req section


# opportunities aplenty
# if god = trickery + rogue -> can select jaunter talents [talents with word jaunter in them], otherwise can't
# for 

    # def rogue_talent_chooser(self):
    #     """ If class = Rogue or Rogue (Unchained)
    #     First creates a list without prerequisites
    #     Then every even level it will add rogue talents + other pre-reqs into a big set which it checks to see
    #     which rogue talents are eligible to be taken

    #     Return
    #     - chosen rogue talents list + rogue talents descriptions"""
    #     self.rogue_talent_list=[]    
    #     talents_without_prerequisites = self.get_talents_without_prerequisites()     

    #     i=0
    #     even=2
    #     odd=1

    #     if self.c_class == 'rogue' or self.c_class == 'rogue_unchained':
    #         talent_list = floor(self.c_class_level/2)   
    #     elif self.c_class_2 == 'rogue' or self.c_class_2 == 'rogue_unchained':
    #         talent_list = floor(self.c_class_2_level/2)
    #     else:
    #         talent_list = 0
    #     talent_list_choice = talents_without_prerequisites
        
    #     while i < talent_list and talent_list != 0:
    #         talent_chosen = random.choice(talent_list_choice)
    #         print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! {talent_chosen}')
    #         self.rogue_talent_list.append(talent_chosen)
    #         set(self.rogue_talent_list)
    #         #assigning level values to the list, so we can select any talent with a level requirement
    #         rogue_k_even = "rogue " + str(even)
    #         rogue_k_odd = "rogue " + str(odd)
    #         self.chooseable.add(rogue_k_even)
    #         self.chooseable.add(rogue_k_odd)
            
    #         #adding the chosen talent to the list, so we can use it as a prerequisite for other talents
    #         self.chooseable.add(talent_chosen)            
    #         # using the mashing_keys function to cycle through all 
    #         # values with prerequsites [we have in self.chooseable] to add them to list
            
    #         ## the mashing keys function needs work, it only looks for 
    #         ## one word in each prerequisite vs many strings per each
    #         matching_keys = self.mashing_keys()
    #         talent_list_choice.extend(matching_keys)
        
    #         i = len(self.rogue_talent_list)     
    #         even += 2
    #         odd += 2



    #     print(self.rogue_talent_list)
    #     print(self.chooseable)
    #     return self.rogue_talent_list        
 

    # def rage_power_chooser(self):
    #     """ If class = Barbarian or Barbarian (Unchained)
    #     First creates a list without prerequisites
    #     Then every even level it will add rage powers + other pre-reqs into a big set which it checks to see
    #     which rage powers are eligible to be taken

    #     Return
    #     - chosen rage power list + rage power descriptions"""

    #     self.rage_power_list=[]  
    #     rage_powers_without_prerequisites = self.get_talents_without_prerequisites()     

    #     i=0
    #     even=2
    #     odd=1

    #     if self.c_class == 'barbarian' or self.c_class == 'barbarian_unchained':
    #         rage_power_list = floor(self.c_class_level/2)   
    #     elif self.c_class_2 == 'barbarian' or self.c_class_2 == 'barbarian_unchained':
    #         rage_power_list = floor(self.c_class_2_level/2)
    #     else:
    #         rage_power_list = 0

    #     rage_power_list_choice = rage_powers_without_prerequisites
        
    #     while i < rage_power_list and rage_power_list != 0:
    #         rage_power_chosen = random.choice(rage_power_list_choice)
    #         print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! {rage_power_chosen}')
    #         self.rage_power_list.append(rage_power_chosen)
    #         set(self.rage_power_list)

    #         #assigning level values to the list, so we can select any rage_power with a level requirement
    #         barbarian_k_even = "barbarian " + str(even)
    #         barbarian_k_odd = "barbarian " + str(odd)
    #         self.chooseable.add(barbarian_k_even)
    #         self.chooseable.add(barbarian_k_odd)
            
    #         #adding the chosen rage_power to the list, so we can use it as a prerequisite for other rage_powers
    #         self.chooseable.add(rage_power_chosen)            
    #         # using the mashing_keys function to cycle through all 
    #         # values with prerequsites [we have in self.chooseable] to add them to list
            
    #         ## the mashing keys function needs work, it only looks for 
    #         ## one word in each prerequisite vs many strings per each
    #         matching_keys = self.mashing_keys()
    #         rage_power_list_choice.extend(matching_keys)
        
    #         i = len(self.rage_power_list)     
    #         even += 2
    #         odd += 2







    # def discovery_chooser(self):
    #     """
    #     If class = Alchemist
    #     First creates a list without prerequisites
    #     Then every even level it will add discoveries + other pre-reqs into a big set which it checks to see
    #     which discoveries are eligible to be taken

    #     outputs: chosen discovery list + discovery descriptions
    #     """
    #     #probably want to add a function which auto adds class + str(even) and str(odd) to the 
    #     #prereqs list for all classes


    #     #looks like we might need to redo alchemist choices, so it shows full benefits, not just from the table
    #     discovery_amount = (floor(self.c_class_level/2))
    #     #print(f'this is your discovery amount {discovery_amount}')
    #     i = 0
    #     even=2
    #     odd=1       
    #     discovery_list_chosen = set()  
    #     alchemist_discoveries_without_prerequisites = self.get_talents_without_prerequisites()
    #     discovery_list = alchemist_discoveries_without_prerequisites
      
    #     basic = self.alchemist_choices['basic'] 

    #     if self.c_class == 'alchemist':

    #         # at level 20 alchemists get an extra 2 discoveries
    #         if self.c_class_level >= 20:
    #             discovery_amount += 2

    #         while i < discovery_amount and discovery_amount != 0 :      



    #             alchemist_k_even = "alchemist " + str(even)
    #             alchemist_k_odd = "alchemist " + str(odd)   
    #             self.chooseable.add(alchemist_k_even)
    #             self.chooseable.add(alchemist_k_odd)                                                     

    #             discovery_chosen = random.choice(discovery_list)
    #             discovery_description = basic[discovery_chosen]['benefits']
    #             discovery_list_chosen.add(discovery_chosen) 
    #             self.chooseable.add(discovery_chosen)


    #             matching_keys = self.mashing_keys()
    #             discovery_list.extend(matching_keys)

    #             print(f'This is the chosen discovery {discovery_chosen}')
    #             # print(f'This is the chosen discovery description {discovery_description}')
    #             print(f'This is your total discover list{discovery_list_chosen}')
    #             # print(f'chooseable list {discovery_list}')

    #             print(f'This is your I value {i}')
    #             i = len(discovery_list_chosen)
    #             even += 2
    #             odd += 2
                
    #             self.discovery_list_chosen = discovery_list_chosen
         
    #         return self.discovery_list_chosen






    # def bloodline_feats_chooser(self):
    #     """
    #     If class = Sorcerer or Bloodrager randomly chooses feats from each bloodline list
    #     Return
    #     - feat_list
    #     """
    #     print('Wubby Dubby 1st')
    #     print(f'sorc bloodline {self.chosen_s_bloodline}')
    #     print(f'blood bloodline {self.chosen_b_bloodline}')
    #     #probably want to reformat the data to have all bloodline powers in one area (like we have it for the newest additions)
        # sorc_amount = [7,13,19,25,31,37,43,49]
        # blood_amount = [7,10,13,16,19,22,25,28,31,34,37,40,43,46,49]

    #     feat_list = set ()
    #     i = 0
    #     if self.chosen_s_bloodline != None and self.c_class == 'sorcerer' and len(feat_list) <= 6:
    #         while sorc_amount[i] < self.c_class_level:
    #             print(self.chosen_s_bloodline)
    #             print(len(feat_list))
    #             bloodline_feats_list = []
    #             bloodline_feats_string = self.bloodlines["sorcerer"][self.chosen_s_bloodline]["bonus feats"]

    #             self.json_list_grabber(bloodline_feats_string, bloodline_feats_list, ',')

    #             print(bloodline_feats_list)

    #             chosen_feat = random.choice(bloodline_feats_list)
    #             feat_list.add(chosen_feat)
    #             i = len(feat_list)




    #     if self.chosen_b_bloodline is not None and self.c_class == 'bloodrager':
    #         while blood_amount[i] < self.c_class_level and len(feat_list) < 6:
    #             print(self.chosen_b_bloodline)
    #             print(len(feat_list))
    #             bloodline_feats_list = []
    #             bloodline_feats_string = self.bloodlines["bloodrager"][self.chosen_b_bloodline]["bonus feats"]

    #             self.json_list_grabber(bloodline_feats_string, bloodline_feats_list, ',')

    #             print(bloodline_feats_list)

    #             chosen_feat = random.choice(bloodline_feats_list)
    #             feat_list.add(chosen_feat)


    #         print(f'This is your {feat_list}')
    #         return feat_list









    # def bloodline_chooser(self):
    #     """
    #     If class = Sorcerer or Bloodrager randomly chooses a bloodline
    #     Return
    #     - chosen_bloodline
    #     """
    #     self.chosen_b_bloodline = None
    #     self.chosen_s_bloodline = None

    #     if self.c_class == 'sorcerer' or self.c_class_2 == 'sorcerer':   
    #         self.chosen_s_bloodline =  random.choice(list(self.bloodlines["sorcerer"].keys()))
    #         print(f'This is your selected bloodline {self.chosen_s_bloodline} + its info: \n{self.bloodlines["sorcerer"][self.chosen_s_bloodline]}')

    #     if self.c_class == 'bloodrager' or self.c_class_2 == 'bloodrager':
    #         b_bloodlines = (list(self.bloodlines["bloodrager"].keys()))
    #         self.chosen_b_bloodline =  random.choice(b_bloodlines)
    #         print(f'This is your selected bloodline {self.chosen_b_bloodline} + its info: \n{self.bloodlines["bloodrager"][self.chosen_b_bloodline]}')

    #         return self.chosen_s_bloodline, self.chosen_b_bloodline









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













