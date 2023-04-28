#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.markdown import style
from utils.data import version
from utils.util import isBool, skills, mythic, flaws, path_of_war_chance, Roll_Level, Total_Hitpoint_Calc, inherent_stats, age_weight_height, various_racial_attr, appearnce_func, personality_and_profession, path_of_war, alignment_and_deities #chooseClass Roll_Level_40, Roll_Level_30, Roll_Level_20, Roll_Level_10, Roll_Level_5,
import random
global filename
name = random.randint(0,100000000000)
character_name = name
#only location you need to specify where you want text files to be created at
filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"

print(style.BOLD + f'Welcome to the D&D Random Character Generator ({version})' + style.END)

isTrue = True




while isTrue:
	with open(filename, 'a') as f, open("last_names_regions.json", "r") as a, open("first_names_regions.json", "r") as g:
		print('===============================================================',file=f)
		userInput = input('Create a new character? (y/n): ').lower()
		isTrue = isBool(userInput)

		if isTrue:
			#end of region macro
			CreateNewCharacter()
			flaws()
			Roll_Level()
			Total_Hitpoint_Calc()
			inherent_stats()
			age_weight_height()
			various_racial_attr()
			appearnce_func()
			personality_and_profession()
			alignment_and_deities()
			path_of_war_chance()
			path_of_war()
			skills()
			mythic()

			#need to devise a way to randomly pick good feats		

		else: 
			print('Exiting Character Generator...')
			break

# Add Extra race stats (Tortugan, Loxophant, ...)
# Have forest give me extra race info (Tortugan, Loxophant, ...)

								#notes
#Might not do below:
#using a list of all regions, weight weapon groups