#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.markdown import style
from utils.data import version
from utils.util import  chooseClass, region_chooser, race_chooser, weapon_chooser, name_chooser, dip_function, format_text, isBool#, skills, mythic, Archetype_Assigner, flaws, path_of_war_chance, Roll_Level, Total_Hitpoint_Calc, inherent_stats, age_weight_height, various_racial_attr, appearnce_func, personality_and_profession, path_of_war, alignment_and_deities #chooseClass Roll_Level_40, Roll_Level_30, Roll_Level_20, Roll_Level_10, Roll_Level_5,
import random
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
	'race': 'json/race.json',
	'class': 'json/class.json',
	'traits': 'json/traits_abilities.json',
	'profession': 'json/profession.json',
	'last_names_regions': 'json/last_names_regions.json',
	'first_names_regions': 'json/first_names_regions.json',
	'flaws': 'json/flaws.json',
	'archetypes': 'json/archetypes.json',
	'spells_known': 'json/spells_known.json',
	'spells_per_day': 'json/spells_per_day.json',
	'spells_from_ability_mod': 'json/spells_from_ability_mod.json',
	'ranger_combat_styles': 'json/ranger_combat_styles.json',				
	'monk_choices': 'json/monk_choices.json',
	'class_features': 'json/class_features.json',	
	'bloodlines': 'json/bloodlines.json',
	'mercies': 'json/mercies.json',
	'rogue_talents': 'json/rogue_talents.json',
	'rage_powers': 'json/rage_powers.json',
	'cleric_domains': 'json/cleric_domains.json',				
	'druid_domains': 'json/druid_domains.json',		
	'deity': 'json/deity.json',	
	'items': 'json/items.json',
	'fighter_options': 'json/fighter_options.json',	
	'bard_choices': 'json/bard_choices.json',	
	'animal_companion': 'json/animal_companion.json',	
	'animal_choices': 'json/animal_choices.json',
	'wizard_schools': 'json/wizard_schools.json',	
	'alchemist_choices': 'json/alchemist_choices.json',
	'class_data': 'json/class_data.json',			
	'cruelties': 'json/cruelties.json',	
	'arcanist_exploits': 'json/arcanist_exploits.json',	
	'cavalier_orders': 'json/cavalier_orders.json',					
	'gunslinger_deeds_dares': 'json/gunslinger_deeds_dares.json',					

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
		
		region_chooser(character)
		race_chooser(character)
		weapon_chooser(character)
		name_chooser(character)
		chooseClass(character)
		dip_function(character, 'base_classes')

		#add an optional flaws rule function	
		print(f"This is your randomly selected alignment: {character.randomize_alignment('alignments')}")
		print(f"This is your randomly selected deity: {character.randomize_deity()}")

		character.randomize_body_feature('age')
		character.randomize_body_feature('height')
		character.randomize_body_feature('weight')			
		num_dice = int(input("How many dice would you like to roll? "))
		num_sides = int(input("How many sides should each die have? "))
		character.roll_stats(num_dice, num_sides)
		character.calc_ability_mod()

		character.randomize_flaw()

		max_num = int(input("Enter the highest level you want the char to be: "))
		min_num = int(input("Enter the lowest level (minimum 2) you want the char to be: "))
		character.randomize_level(min_num, max_num)

		#hp calculations
		character.hit_dice_calc()
		character.roll_hp()
		character.total_hp_calc()

		print(f'This is your class for spells{character.class_for_spells_attr()} ')

		# Some spellcasters get 0th level spells (all high + most mid)
		# Also 0th spells = infinite casting 
		# Wizards + Clerics know all 0th level spells (wizards know all except opposing school)
		# as long as spells known list has a '0th' spell column (even if it isn't 0) 
		# it won't pull any 0th spells for casters with orisons/cantrips
		character.choose_caster_formula_1()
		character.choose_caster_formula_2()

		#Divine Casters have all spells known (don't make this function for them)
		print(f'This is your spells known list {character.spells_known_attr("base_classes", "divine_casters")}')
		print(f'This is your spells per day {character.spells_per_day_attr("base_classes")}')
		print(f'This is your spells per day from ability mods {character.spells_per_day_from_ability_mod("caster_mod")}')
		print(f'Spells known + extra randomized spells known [spell book learners only] {character.spells_known_extra_roll()}')		
		print(f"This is your spells list you can choose from {character.spells_known_selection('base_classes','divine_casters')}")


		print(f'This is your wizard schools {character.wizard_school_chooser()}')


		# Extra class choices:
		character.extra_combat_feats()
		character.class_abilities_amount()


		print(f"This is your selected feats: {character.feats_selector()}")

		#this is to allow for talent choice stat pre-reqs (self.chooseable)
		character.chooseable_list() 		
		character.chooseable_list_stats(character.str, 'str')
		character.chooseable_list_stats(character.dex, 'dex')
		character.chooseable_list_stats(character.con, 'con')
		character.chooseable_list_stats(character.int, 'int')
		character.chooseable_list_stats(character.wis, 'wis')
		character.chooseable_list_stats(character.cha, 'cha')	
	



		#decides if druids go animal companion or domain
		character.druid_domain_chance()

		#class specific choices
		character.monk_ki_power_chooser()
		character.sorcerer_bloodline_chooser()

		character.fighter_armor_train_chooser()
		character.fighter_weapon_train_chooser()	
		character.rogue_talent_chooser()
		character.rage_power_chooser()
		character.domain_chooser()	
		character.versatile_perfomance()	
		character.animal_chooser()
		character.animal_feats()	
		character.wizard_school_chooser()
		character.wizard_opposing_school()	
		character.discovery_chooser()
		character.grand_discovery_chooser()
		character.anti_paladin_cruelty_chooser()
		character.paladin_mercy_chooser()		
		character.arcanist_exploits_chooser()
		character.cavalier_order_chooser()							
		print(f"This is your favored attributes {character.ranger_favored_groups('favored_terrains','favored_enemies')}")

		#class specific feats choosers
		character.ranger_feats_chooser()
		character.monk_feats_chooser()
		character.sorcerer_feats_chooser()


		character.archetype_data()

		# background info
		character.skills_selector('skills')
		print(f'This is your chosen professions {character.profession_chooser("professions")}')



		# character.armor_chooser()

		# print(f'This is your gold pre items {character.assign_gold("gold")}')
		# character.item_chooser()
		# print(f'This is your gold post items {character.gold}')	





							




#		character.get_all_prerequisites()
#		character.get_talents_without_prerequisites()
#		character.get_talents_with_prerequisites()
		#Create a prepared spell list (dependent on spells known)


		# inherent_stats() [Skip for now, make OOP later]
		# add a spontaneous caster option as well (so sorcs + wizs get spells known at right level)


		# print(f"Racial traits: {character.get_racial_attr('traits')}")	

		# print(f"racial languages: {character.get_racial_attr('languages')}")
		# print(f"racial size: {character.get_racial_attr('size')}")
		# print(f"racial speed: {character.get_racial_attr('speed')}")					
		# print(f"Ability Scores for {character.get_racial_attr('ability scores')}")												
		
		# print(f'This is your hair_colors {character.randomize_apperance_attr("hair_colors")}')
		# print(f'This is your hair_types {character.randomize_apperance_attr("hair_types")}')
		# print(f'This is your eye_colors {character.randomize_apperance_attr("eye_colors")}')
		# print(f'This is your appearance {character.randomize_apperance_attr("appearance", 3)}')									

		# print(f'This is your background_traits {character.randomize_personality_attr("background_traits",4)}')
		# print(f'This is your professions {character.randomize_personality_attr("professions", 3)}')
		# print(f'This is your mannerisms {character.randomize_personality_attr("mannerisms", 3)}')
		# print(f'This is your flaws {character.randomize_personality_attr("flaws", 3)}')									


		# print(f' This is your alignment {character.randomize_alignment("alignments")}')

		# print(f'This is your Deity {character.randomize_deity("all_deities")}')

		# # skill rank generator (class ranks + int)*level



		# character.Archetype_Assigner()
		# print(f'This is your gold {character.assign_gold("gold")}')
		# #use gold to randomly select items



		# #calculating savings throws based off of class levels
		# character.saving_throw_calc('Fortitude')
		# character.saving_throw_calc('Reflex')
		# character.saving_throw_calc('Will')			

		# print(f'This is your mythic rank {character.randomize_mythic()}')

		# #creating quick race/class specific flags 
		# character.druidic_flag()
		# character.human_flag()

		# #3PP Content Only
		# # Path of War Content
		# character.randomize_path_of_war_num("path_of_war_class")
		# print(f'This is your Path of War Path {character.choose_path_of_war_attr("disciplines")}')

		# #Luck Content
		# print(f'this is your luck score {character.randomize_luck()}')



							# Want to Add:
		# Find a way to print all main class info


		# Add a note (everything is calculated off of base classes, will need to 
		## add archetype changes manually) [e.g. skills, spells, feats]

		# create a list for feats chosen to export over to Javascript					
		# randomize_feats() -> probably create baby buckets per BAB to make it 
		## simple yet not garbage randomly assigned feats

		# Create a List for spells chosen to export over to Javascript
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