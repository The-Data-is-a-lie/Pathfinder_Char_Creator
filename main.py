#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.markdown import style
from utils.data import version
from utils.util import  chooseClass, format_text, isBool#, skills, mythic, Archetype_Assigner, flaws, path_of_war_chance, Roll_Level, Total_Hitpoint_Calc, inherent_stats, age_weight_height, various_racial_attr, appearnce_func, personality_and_profession, path_of_war, alignment_and_deities #chooseClass Roll_Level_40, Roll_Level_30, Roll_Level_20, Roll_Level_10, Roll_Level_5,
import random
from utils.data_dict import initialize_character_data, character_data_to_json, convert_character_json_to_html
from html_editor_best import html_builder
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
# assuming we are creating new character
# character = Character()

character_json_config = {
	'race': 'utils/race.json',
	'class': 'utils/class.json',
	'traits': 'utils/traits_abilities.json',
	'profession': 'utils/profession.json',
	'last_names_regions': 'last_names_regions.json',
	'first_names_regions': 'first_names_regions.json',
	'flaws': 'utils/flaws.json',
	'archetypes': 'utils/archetypes.json'
}


while userInput.lower() == 'y':
	name = random.randint(0,100000000000)
	character_name = name
	# filename = f"C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_{name}_character_sheet.txt"

	isTrue = isBool(userInput)

	if userInput == 'y':
		#end of region macro
		# format_text(text, bold=False, color=None)
		character = CreateNewCharacter(
			character_json_config)
		

		chooseClass(character)
		character.randomize_body_feature('age')
		character.randomize_body_feature('height')
		character.randomize_body_feature('weight')			
		# num_dice = int(input("How many dice would you like to roll? "))
		# num_sides = int(input("How many sides should each die have? "))
		# character.roll_stats(num_dice, num_sides)

		# character.randomize_flaw()

		# max_num = int(input("Enter the highest level you want the char to be: "))
		# min_num = int(input("Enter the lowest level (minimum 2) you want the char to be: "))
		# character.randomize_level(min_num, max_num)

		# character.hit_dice_calc()
		# character.roll_hp()
		# character.total_hp_calc()

		# inherent_stats() [Skip for now, make OOP later]


		print(f"Racial traits: {character.get_racial_attr('traits')}")	
		#add a druid flag function, if druid append 'Druidic' onto languages known		
		#add a human flag function, if human feats = feats+1
		print(f"racial languages: {character.get_racial_attr('languages')}")
		print(f"racial size: {character.get_racial_attr('size')}")
		print(f"racial speed: {character.get_racial_attr('speed')}")					
		print(f"Ability Scores for {character.get_racial_attr('ability scores')}")												
		
		print(f'This is your hair_colors {character.randomize_apperance_attr("hair_colors")}')
		print(f'This is your hair_types {character.randomize_apperance_attr("hair_types")}')
		print(f'This is your eye_colors {character.randomize_apperance_attr("eye_colors")}')
		print(f'This is your appearance {character.randomize_apperance_attr("appearance", 3)}')									

		print(f'This is your background_traits {character.randomize_personality_attr("background_traits",4)}')
		print(f'This is your professions {character.randomize_personality_attr("professions", 3)}')
		print(f'This is your mannerisms {character.randomize_personality_attr("mannerisms", 3)}')
		print(f'This is your flaws {character.randomize_personality_attr("flaws", 3)}')									


		print(f' This is your alignment {character.randomize_alignment("alignments")}')

		print(f'This is your Deity {character.randomize_deity("all_deities")}')

		#3PP Content Only
		# Needs to be in front of chooser
		character.randomize_path_of_war_num("path_of_war_class")
		print(f'This is your Path of War Path {character.choose_path_of_war_attr("disciplines")}')

		character.Archetype_Assigner()

		# skills()
		# mythic()

							# Want to Add:
		# randomize_feats() -> probably create baby buckets per BAB to make it 
		## simple yet not garbage randomly assigned feats

		# randomize_spells() -> will be a bit complex, need to assign per 
		## full caster, mid caster, low caster 
		### (Can pull spells per class and assign them truly randomly)
		#### + add spontaneous caster function + prepared caster function

		#randomly generate armor + ?Shield?
		#randomly generate consumables
		#randomly generate magic items
		#create gold assigned per level (based off of 1 of 3 pathfinder gold progressions)
		#use gold assigned per level to randomly assign magic items (buckets? or true random?)

		#auto add saving throws
		#auto add exp (based off of random level (just set it to fresh level))
		#auto add CMD
		#auto add CMB
		#auto add DR
		#auto add SR
		#auto add Resource Pool
		#auto add Resistances

		# human_feat()
		# druidic_language()
		




							# HTML Sections
		# initialize_character_data()
		# character_data_to_json()
		# convert_character_json_to_html()
		# html_builder()



		#update character data:
		


		#need to devise a way to randomly pick good feats		

	else: 
		print('Exiting Character Generator...')
		break

# Revamp code so it becomes a dictionary -> we can make homemade HTML/CSS code to print out exactly what we want

# Add a calculation for BAB (instead of just posting L,M,H)
# Add Extra race stats (Tortugan, Loxophant, ...)
# Have forest give me extra race info (Tortugan, Loxophant, ...)

# Remove Path of War auto subtraction from total Feats
# Have feats per class (e.g level 5 Fighter gets 3 feats)
# Add spheres per class