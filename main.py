#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.markdown import style
from utils.data import version
from utils.util import isBool, Roll_Level, Total_Hitpoint_Calc, inherent_stats, age_weight_height, various_racial_attr, appearnce_func, personality_and_profession, path_of_war, alignment_deities_and_skills #chooseClass Roll_Level_40, Roll_Level_30, Roll_Level_20, Roll_Level_10, Roll_Level_5,
import random

print(style.BOLD + f'Welcome to the D&D Random Character Generator ({version})' + style.END)

isTrue = True




while isTrue:
	character_name = random.randint(0,10000000)
	# write the location of where you want it to export here:
	filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{character_name}_character_sheet.txt"
	with open(filename, 'a') as f, open("last_names_regions.json", "r") as a, open("first_names_regions.json", "r") as g:
		print('===============================================================',file=f)
		#

		
		userInput = input('Create a new character? (y/n): ').lower()
		isTrue = isBool(userInput)
		#User selects the region to start from (if they want to)
		

		if isTrue:
			#end of region macro
			CreateNewCharacter(character_name)
			Roll_Level(character_name)
			Total_Hitpoint_Calc(character_name)
			inherent_stats(character_name)
			age_weight_height(character_name)
			various_racial_attr(character_name)
			appearnce_func(character_name)
			personality_and_profession(character_name)
			alignment_deities_and_skills(character_name)
			path_of_war(character_name)
			#need to devise a way to randomly pick good feats
			for i in range(1, 11):
				if random.randint(1, 10000) == 10000:
					print(f'Character is mythic {i}')
					print(f'Character is mythic {i}',file=f)					
					for j in range(2, 11):
						roll = random.randint(1, 100)
						if roll >= 90:
							print(f'Character is mythic {j}')
							print(f'Character is mythic {j}',file=f)
						else:
							break
				else:
					print('didnt get mythic ')
					print('didnt get mythic ', file=f)
					break			

			if random.randint(1,100) == 100:
				print('character is extremely lucky, make it a luck build rather than everything else ')
				print('character is extremely lucky, make it a luck build rather than everything else ', file=f)				
			elif random.randint(1,100) <= 5:
				print('you need to take negative luck feats as well as normal feats ')
				print('you need to take negative luck feats as well as normal feats ', file = f)
				
				

		else: 
			print('Exiting Character Generator...')
			break

# Add a multi-class option + dip option (you can either multi-class or dip, no in between)
# Adjust inherent stat roller (if Forest wants it adjusted)
# Add Extra race stats (Tortugan, Loxophant, ...)
# Have forest give me extra race info (Tortugan, Loxophant, ...)
#

								#notes
#Might not do below:
#using a list of all regions, weight weapon groups