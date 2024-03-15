# from math import ceil, floor

# def extra_magic_feats(character):
#     # wizard_feats = [1,5,10,15,20,25,30,35,40] 
#     sorcerer_feats = [7,13,19,25,31,37,43]
#     if character.c_class == 'wizard':
#         magic_feats =  1 + floor((character.c_class_level)/5)

#     if character.c_class_2 == 'wizard':
#         magic_feats_2 = character.feat_amounts + 1 + floor((character.c_class_2_level)/5)         

#     i=0
#     i_2=0        

#     if character.c_class == 'sorcerer':
#         while i < len(sorcerer_feats) and sorcerer_feats[i] <= character.c_class_level:
#             i += 1
#         magic_feats = i

#     if character.c_class_2 == 'sorcerer':
#         while i_2 < len(sorcerer_feats) and sorcerer_feats[i_2] <= character.c_class_level:
#             i_2 += 1
#         magic_feats = i_2
#         magic_feats_2 = i_2    

#     i=0
#     i_2=0        




#     character.magic_feats = magic_feats + magic_feats_2
#     return character.magic_feats  