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


        while i < len(ranger_feats) and ranger_feats[i] <= character.c_class_level:
            ranger_feats_list=character.ranger[random_combat_style]["2"]

            if ranger_feats[i]>=6:
                ranger_feats_list=(character.ranger[random_combat_style]["2"] + character.ranger[random_combat_style]["6"])
            elif ranger_feats[i]>=10:
                ranger_feats_list=(character.ranger[random_combat_style]["2"] + character.ranger[random_combat_style]["6"] + character.ranger[random_combat_style]["10"])

            # Stop once this combat style's pool can't yield a new pick. Without this the loop
            # spins forever (i never advances) / IndexErrors at high level when the list is
            # exhausted. (Replaces the dead `== 7` check, which compared a set to an int.)
            if set(ranger_feats_list).issubset(ranger_feats_chosen_list):
                break

            ranger_feats_chosen=random.choice(ranger_feats_list)
            ranger_feats_chosen_list.add(ranger_feats_chosen)

            i=len(ranger_feats_chosen_list)

        # Track slots this combat style's pool couldn't fill so main_test can reallocate them to
        # normal feats. We no longer extend character.feats here: the caller merges the returned
        # feats once, after the normal-feat selection that would otherwise clobber them.
        scheduled = sum(1 for lvl in ranger_feats if lvl <= character.c_class_level)
        character.ranger_feat_surplus = scheduled - len(ranger_feats_chosen_list)
        return ranger_feats_chosen_list

def monk_feats_chooser(character):
    if character.c_class == 'monk' or character.c_class == 'unchained_monk':
        monk_feats = [1,2,6,10,14,18,22,26,30,34,38,42]   
        #using set + .add makes sure we don't have any repeats in our list           
        monk_feats_chosen_list=set()
        i=0

        while i < len(monk_feats) and monk_feats[i] <= character.c_class_level:
            monk_feats_list=character.monk['feats']["2"]

            if monk_feats[i]>=6:
                monk_feats_list=(character.monk['feats']["2"] + character.monk['feats']["6"])
            elif monk_feats[i]>=10:
                monk_feats_list=(character.monk['feats']["2"] + character.monk['feats']["6"] + character.monk['feats']["10"])

            # Stop once the bonus-feat pool can't yield a new pick, so the loop can't spin
            # forever (i never advances) / IndexError at high level when the list is exhausted.
            if set(monk_feats_list).issubset(monk_feats_chosen_list):
                break

            monk_feats_chosen=random.choice(monk_feats_list)
            monk_feats_chosen_list.add(monk_feats_chosen)

            i=len(monk_feats_chosen_list)

        # Track unfilled bonus-feat slots (list exhausted) for reallocation to normal feats.
        # The caller merges the returned feats into character.feats (no extend here).
        scheduled = sum(1 for lvl in monk_feats if lvl <= character.c_class_level)
        character.monk_feat_surplus = scheduled - len(monk_feats_chosen_list)
        return monk_feats_chosen_list