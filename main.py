#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.markdown import style
from utils.data import version
from utils.util import  format_text, isBool, skills, mythic, Archetype_Assigner, flaws, path_of_war_chance, Roll_Level, Total_Hitpoint_Calc, inherent_stats, age_weight_height, various_racial_attr, appearnce_func, personality_and_profession, path_of_war, alignment_and_deities #chooseClass Roll_Level_40, Roll_Level_30, Roll_Level_20, Roll_Level_10, Roll_Level_5,
import random
from utils.data_dict import initialize_character_data, character_data_to_json, convert_character_json_to_html
#Making a Global Character Dictionary so we can reference it and create a HTML/CSS sheet based off of that

global character_data 
global filename
character_data = {}
#Adding in Text to PDF Imports
# import fillpdf        
# from fillpdf import fillpdfs
# from utils.Text_to_pdf_Best_Version_9_28_23

#only location you need to specify where you want text files to be created at
print(style.BOLD + f'Welcome to the D&D Random Character Generator ({version})' + style.END)

userInput = input('Create a new character? (y/n): ').lower()


while userInput.lower() == 'y':
	name = random.randint(0,100000000000)
	character_name = name
	filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"
	with open(filename, 'a') as f, open("last_names_regions.json", "r") as a, open("first_names_regions.json", "r") as g:
		print('===============================================================',file=f)

		isTrue = isBool(userInput)

		if userInput == 'y':
			#end of region macro
			# format_text(text, bold=False, color=None)
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
			Archetype_Assigner()
			skills()
			mythic()
			initialize_character_data()
			character_data_to_json()
			convert_character_json_to_html()



			#update character data:
			


			#need to devise a way to randomly pick good feats		

		else: 
			print('Exiting Character Generator...')
			break

# Revamp code so it becomes a dictionary -> we can make homemade HTML/CSS code to print out exactly what we want

# Add Extra race stats (Tortugan, Loxophant, ...)
# Have forest give me extra race info (Tortugan, Loxophant, ...)

# Remove Path of War auto subtraction from total Feats
# Have feats per class (e.g level 5 Fighter gets 3 feats)
# Add spheres per class