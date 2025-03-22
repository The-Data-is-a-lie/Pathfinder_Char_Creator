# This file will handle all class specific feats possible
import random
# Start of class specific feats chooser
def class_specific_feats_chooser(character, c_class, name_1, name_2, name_3=None, class_level = None):
    if character.c_class == c_class and (class_level == None or character.c_class_level >= class_level):
        try:
            if name_3 != None:
                extra_feat_list = getattr(character, character.c_class, {}).get(name_1, {}).get(name_2, {}).get(name_3, [])
            else:
                extra_feat_list = getattr(character, character.c_class, {}).get(name_1, {}).get(name_2, [])
            
        except AttributeError:
            extra_feat_list = []

        character.total_feats.extend(extra_feat_list)
    return []

def ranger_feats_chooser(character):
    if character.c_class == 'ranger':
        ranger_feats = [2,6,10,14,18,22,26,30,34,38,42]              
        choice = list(character.ranger.keys())   
        random_combat_style = random.choice(choice)
        ranger_feats_chosen_list=set()     
        i=0


        while ranger_feats[i] <= character.c_class_level:
            ranger_feats_list=character.ranger[random_combat_style]["2"]
            
            if ranger_feats[i]>=6:
                ranger_feats_list=(character.ranger[random_combat_style]["2"] + character.ranger[random_combat_style]["6"])
            elif ranger_feats[i]>=10:
                ranger_feats_list=(character.ranger[random_combat_style]["2"] + character.ranger[random_combat_style]["6"] + character.ranger[random_combat_style]["10"])


            ranger_feats_chosen=random.choice(ranger_feats_list)
            ranger_feats_chosen_list.add(ranger_feats_chosen)
                
            i=len(ranger_feats_chosen_list)

            if ranger_feats_chosen_list == 7:
                break

        character.feats.extend(ranger_feats_chosen_list)
        return ranger_feats_chosen_list

def monk_feats_chooser(character):
    if character.c_class == 'monk' or character.c_class == 'unchained_monk':
        monk_feats = [1,2,6,10,14,18,22,26,30,34,38,42]   
        #using set + .add makes sure we don't have any repeats in our list           
        monk_feats_chosen_list=set()     
        i=0

        while monk_feats[i] <= character.c_class_level:
            monk_feats_list=character.monk['feats']["2"]
            
            if monk_feats[i]>=6:
                monk_feats_list=(character.monk['feats']["2"] + character.monk['feats']["6"])
            elif monk_feats[i]>=10:
                monk_feats_list=(character.monk['feats']["2"] + character.monk['feats']["6"] + character.monk['feats']["10"])


            monk_feats_chosen=random.choice(monk_feats_list)
            monk_feats_chosen_list.add(monk_feats_chosen)
                
            i=len(monk_feats_chosen_list)

        character.feats.extend(monk_feats_chosen_list)
        return monk_feats_chosen_list