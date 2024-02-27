from math import floor
def extra_combat_feats(character):
    #fighter_feats = [1,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40]
    monk_feats = [1,2,6,10,14,18,22,26,30,34,38,42]
    brawler_feats = [2,5,8,11,14,17,20,23,26,29,32,35,38,41] 
    ranger_feats = [2,6,10,14,18,22,26,30,34,38,42]       
    sorcerer_feats = [7,13,19,25,31,37,43,49]     
    #setting up extra feats + extra feats_2 as 0 so we don't get errors
    extra_feats = 0
    extra_feats_2 = 0    
    ranger_feats_list = 0
    ranger_feats_2_list = 0
    monk_feats_list = 0 
    monk_feats_2_list = 0
    character.combat_feats_list=0

    #fighter section
    if character.c_class == 'fighter':
        extra_feats +=  1 + floor((character.c_class_level)/2)

    # if character.c_class_2 == 'fighter':
    #     extra_feats_2 = character.feat_amounts + 1 + floor((character.c_class_2_level)/2)         

    i=0
    i_2=0

    #monk section
    if character.c_class == 'monk' or character.c_class == 'unchained_monk':
        while i < len(monk_feats) and monk_feats[i] <= character.c_class_level:
            i += 1
        extra_feats += i

    # if character.c_class_2 == 'monk' or character.c_class_2 == 'unchained_monk':
    #     while i_2 < len(monk_feats) and monk_feats[i_2] <= character.c_class_level:
    #         i_2 += 1

    #     extra_feats = i_2

    i=0
    i_2=0

    if character.c_class == 'brawler':
        while i < len(brawler_feats) and brawler_feats[i] <= character.c_class_level:
            i += 1
        extra_feats += i

    # if character.c_class_2 == 'brawler':
    #     while i_2 < len(brawler_feats) and brawler_feats[i_2] <= character.c_class_level:
    #         i_2 += 1

    #     extra_feats_2 = i_2        

    i=0
    i_2=0

    if character.c_class == 'ranger':
        while i < len(ranger_feats) and ranger_feats[i] <= character.c_class_level:
            i += 1
        extra_feats += i

    # if character.c_class_2 == 'ranger':
    #     while i_2 < len(ranger_feats) and ranger_feats[i_2] <= character.c_class_level:
    #         i_2 += 1

    #     extra_feats += i_2                    
        
    if character.c_class == 'sorcerer':
        while i < len(sorcerer_feats) and sorcerer_feats[i] <= character.c_class_level:
            i += 1
        extra_feats += i

    if character.c_class == 'wizard':
        i = floor(character.c_class_level / 5)
        extra_feats += i


    #currently we're just adding combat feats to total feats, 
    # but we may want to have them be their own separate entity
    character.class_feats = extra_feats 
    # character.class_feats = extra_feats + extra_feats_2
    # character.ranger_feats = ranger_feats_list + ranger_feats_2_list
    # character.monk_feats = monk_feats_list + monk_feats_2_list
            

    return character.class_feats   