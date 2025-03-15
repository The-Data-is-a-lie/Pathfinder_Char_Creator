# from utils import data
# import random
# from math import ceil, floor
# def ranger_favored_groups(character,favored_terrains,favored_enemies):
#     favored_terrains=getattr(data, favored_terrains)
#     favored_enemies=getattr(data, favored_enemies)
#     terrains = []
#     enemies = []

#     if character.c_class == 'ranger':
#         enemy_choice_num = 1 + floor(character.c_class_level/5)
#         terrain_choice_num = ceil((character.c_class_level-2)/5) 
#         terrains=random.sample(favored_terrains,k=terrain_choice_num)
#         enemies=random.sample(favored_enemies,k=enemy_choice_num)            

#     elif character.c_class_2 == 'ranger':
#         enemy_choice_num = 1 + floor(character.c_class_2_level/5)
#         terrain_choice_num = ceil((character.c_class_2_level-2)/5)      
#         terrains=random.sample(favored_terrains,k=terrain_choice_num)
#         enemies=random.sample(favored_enemies,k=enemy_choice_num)                     

#     else:
#         print('no ranger class levels')

#     return terrains, enemies
