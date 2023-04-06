#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.markdown import style
from utils.data import version
from utils.util import isBool, Roll_Level_40, Roll_Level_30, Roll_Level_20, Roll_Level_10, Roll_Level_5, chooseClass
import random

print(style.BOLD + f'Welcome to the D&D Random Character Generator ({version})' + style.END)

isTrue = True


while isTrue:
	character_name = random.randint(0,10000000)
	filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{character_name}_character_sheet.txt"
	with open(filename, 'a') as f:
		print('===============================================================',file=f)
		userInput = input('Create a new character? (y/n): ').lower()
		isTrue = isBool(userInput)

		if isTrue:
			print('===============================================================', file=f)
			CreateNewCharacter(character_name)
			user_input = input("Do you want levels to be weighted lower (if n then they are weighted higher)? (y/n) ")
			level_40 = Roll_Level_40(user_input)
			level_30 = Roll_Level_30(user_input)
			level_20 = Roll_Level_20(user_input)
			level_10 = Roll_Level_10(user_input)
			level_5 = Roll_Level_5(user_input)

			print('Character level 1-40' + '\n', level_40, file=f)
			print('Character level 1-30' + '\n', level_30, file=f)
			print('Character level 1-20' + '\n', level_20, file=f)
			print('Character level 1-10' + '\n', level_10, file=f)
			print('Character level 1-5' + '\n', level_5, file=f)

			bonus_feats_40 = (5 + level_40//5 + level_40//2)
			bonus_feats_30 = (5 + level_30//5 + level_30//2)
			bonus_feats_20 = (5 + level_20//5 + level_20//2)
			bonus_feats_10 = (5 + level_10//5 + level_10//2)
			bonus_feats_5 = (5 + level_5//5 + level_5//2)
			
			print('Number of bonus feats (1-40):' + '\n', bonus_feats_40, file=f)
			print('Number of bonus feats (1-30):' + '\n', bonus_feats_30, file=f)
			print('Number of bonus feats (1-20):' + '\n', bonus_feats_20, file=f)
			print('Number of bonus feats (1-10):' + '\n', bonus_feats_10, file=f)									
			print('Number of bonus feats (1-5):' + '\n', bonus_feats_5, file=f)			


			print('Character level 1-40' + '\n', level_40)
			print('Character level 1-30' + '\n', level_30)
			print('Character level 1-20' + '\n', level_20)
			print('Character level 1-10' + '\n', level_10)
			print('Character level 1-5' + '\n', level_5)
			print('Number of bonus feats 1-40' + '\n', bonus_feats_40)
			print('Number of bonus feats 1-30' + '\n', bonus_feats_30)
			print('Number of bonus feats 1-20' + '\n', bonus_feats_20)
			print('Number of bonus feats 1-10' + '\n', bonus_feats_10)									
			print('Number of bonus feats 1-5' + '\n', bonus_feats_5)	
			
			
				
				#need to devise a way to randomly pick good feats

		else: 
			print('Exiting Character Generator...')
			break


