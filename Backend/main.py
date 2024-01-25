#Custom Made Imports
from createACharacter import CreateNewCharacter
from utils.markdown import style
from utils.data import version
from utils.util import  chooseClass, region_chooser, race_chooser, weapon_chooser, name_chooser, dip_function, format_text, isBool#, skills, mythic, Archetype_Assigner, flaws, path_of_war_chance, Roll_Level, Total_Hitpoint_Calc, inherent_stats, age_weight_height, various_racial_attr, appearnce_func, personality_and_profession, path_of_war, alignment_and_deities #chooseClass Roll_Level_40, Roll_Level_30, Roll_Level_20, Roll_Level_10, Roll_Level_5,
import random
from math import ceil, floor
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

# assuming we are creating new character
# character = Character()

character_json_config = {
	'races': 'Backend/json/races.json',
	'classes': 'Backend/json/class.json',
	'class_data': 'Backend/json/class_data.json',
	'traits': 'Backend/json/traits_abilities.json',
	'profession': 'Backend/json/profession.json',
	'last_names_regions': 'Backend/json/last_names_regions.json',
	'first_names_regions': 'Backend/json/first_names_regions.json',
	'flaws': 'Backend/json/flaws.json',
	'archetypes': 'Backend/json/archetypes.json',
	'spells_known': 'Backend/json/spells_known.json',
	'spells_per_day': 'Backend/json/spells_per_day.json',
	'spells_from_ability_mod': 'Backend/json/spells_from_ability_mod.json',
	'ranger_combat_styles': 'Backend/json/ranger_combat_styles.json',				
	'class_features': 'Backend/json/class_features.json',	
	'bloodlines': 'Backend/json/bloodlines.json',
	'cleric_domains': 'Backend/json/cleric_domains.json',				
	'druid_domains': 'Backend/json/druid_domains.json',		
	'deity': 'Backend/json/deity.json',	
	'items': 'Backend/json/items_best.json',
	'bard_choices': 'Backend/json/bard_choices.json',	
	'animal_companion': 'Backend/json/animal_companion.json',	
	'animal_choices': 'Backend/json/animal_choices.json',
	'wizard_schools': 'Backend/json/wizard_schools.json',	
	'gunslinger_deeds_dares': 'Backend/json/gunslinger_deeds_dares.json',					
	"feat_buckets": "Backend/json/feat_buckets.json",
	"armor": "Backend/json/armor.json",
	"weapons_data": "Backend/json/weapons_data.json",
	"weapon_qualities": "Backend/json/weapon_qualities.json",
	"armor_qualities": "Backend/json/armor_qualities.json",
	"PlayableRaces": "Backend/json/PlayableRaces.json",


	"alchemist": "Backend/json/class_data/alchemist.json",
	"antipaladin": "Backend/json/class_data/antipaladin.json",
	"arcanist": "Backend/json/class_data/arcanist.json",
	"barbarian": "Backend/json/class_data/barbarian.json",
	"bloodrager": "Backend/json/class_data/bloodrager.json",
	"cavalier": "Backend/json/class_data/cavalier.json",
	"fighter": "Backend/json/class_data/fighter.json",
	"inquisitor": "Backend/json/class_data/inquisitor.json",
	"investigator": "Backend/json/class_data/investigator.json",
	"magus": "Backend/json/class_data/magus.json",
	'monk': 'Backend/json/class_data/monk.json',
	"ninja": "Backend/json/class_data/ninja.json",
	"oracle": "Backend/json/class_data/oracle.json",
	"paladin": "Backend/json/class_data/paladin.json",
	"rogue": "Backend/json/class_data/rogue.json",
	"shaman": "Backend/json/class_data/shaman.json",
	"skald": "Backend/json/class_data/skald.json",
	"slayer": "Backend/json/class_data/slayer.json",
	"samurai": "Backend/json/class_data/samurai.json",
	"sorcerer": "Backend/json/class_data/sorcerer.json",
	"vigilante": "Backend/json/class_data/vigilante.json",
	"warpriest": "Backend/json/class_data/warpriest.json",
	"witch": "Backend/json/class_data/witch.json",



}


# Add a function which allows warpriests to use their caster level + functions but grab cleric spells (possiby use class for spells)


# while userInput.lower() == 'y':
# 	isTrue = isBool(userInput)

# 	if userInput == 'y':

def generate_random_char(create_new_char='Y', userInput_region=10, userInput_race='orc', class_choice='wizard', multi_class='N', alignment_input = 'N' ,num_dice=3, num_sides=6, high_level=10, low_level=10, gold_num=1000000):

		# userInput = input('Create a new character? (y/n): ').lower()
		userInput = create_new_char.lower()
		print(f'Create a new character? ({create_new_char.lower()})')

		#end of region macro
		# format_text(text, bold=False, color=None)
		character = CreateNewCharacter(
			character_json_config)
		character.instantiate_full_data_dict()
		
		
		region = region_chooser(character,userInput_region)
		chosen_race = race_chooser(character,userInput_race)
		weapon_chooser(character) # We don't use this anymore, but leave it uncommented for now
		f_name, l_name =name_chooser(character)
		c_class = chooseClass(character,class_choice)
		c_class_2 = dip_function(character,'base_classes', multi_class)

		#add an optional flaws rule function	
		alignment = character.choose_alignment('alignments', alignment_input)
		print(f"This is your randomly selected alignment: {character.alignment}")
		
		deity_choice = character.randomize_deity()
		print(f"This is your randomly selected deity: {deity_choice}")

		age, age_number = character.randomize_body_feature('age')
		height, height_number = character.randomize_body_feature('height')
		weight, weight_number = character.randomize_body_feature('weight')			
		# num_dice = int(input("How many dice would you like to roll? "))
		# num_sides = int(input("How many sides should each die have? "))
		stats = character.roll_stats(num_dice, num_sides)
		character.assign_stats(stats)

		chosen_subrace, subrace_description = character.subrace_chooser()
		print(f'this is your chosen subrace {chosen_subrace}')
		race_traits_list, race_traits_description_list = character.race_traits_chooser()
		print(race_traits_list, race_traits_description_list)

		split_race_traits_list = character.race_ability_split(race_traits_list)
		character.dex = character.race_ability_score_changes(split_race_traits_list, character.dex, 'dex')
		character.str = character.race_ability_score_changes(split_race_traits_list, character.str, 'str')
		character.con = character.race_ability_score_changes(split_race_traits_list, character.con, 'con')
		character.int = character.race_ability_score_changes(split_race_traits_list, character.int, 'int')
		character.wis = character.race_ability_score_changes(split_race_traits_list, character.wis, 'wis')
		character.cha = character.race_ability_score_changes(split_race_traits_list, character.cha, 'cha')
		character.print_stats()

		character.calc_ability_mod()

		flaw = character.randomize_flaw()

		# max_num = int(input("Enter the highest level you want the char to be: "))
		# min_num = int(input("Enter the lowest level (minimum 2) you want the char to be: "))
		# character.randomize_level(min_num, max_num)
		character.randomize_level(low_level, high_level)

		#hp calculations
		character.hit_dice_calc()
		character.roll_hp()
		character.Total_HP = character.total_hp_calc()

		print(f'This is your class for spells: {character.class_for_spells_attr()} ')

		# Some spellcasters get 0th level spells (all high + most mid)
		# Also 0th spells = infinite casting 
		# Wizards + Clerics know all 0th level spells (wizards know all except opposing school)
		# as long as spells known list has a '0th' spell column (even if it isn't 0) 
		# it won't pull any 0th spells for casters with orisons/cantrips
		character.highest_spell_known_1 = character.caster_formula(character.c_class_level)
		character.highest_spell_known_2 = character.caster_formula(character.c_class_2_level, character.c_class_2)
		print(type(character.c_class_2))
		print(character.c_class_2)

		#Divine Casters have all spells known (don't make this function for them)
		print(f'This is your spells known list {character.spells_known_attr("base_classes", "divine_casters")}')
		print(f'This is your spells per day {character.spells_per_day_attr("base_classes")}')
		print(f'This is your spells per day from ability mods {character.spells_per_day_from_ability_mod("caster_mod")}')
		print(f'Spells known + extra randomized spells known [spell book learners only] {character.spells_known_extra_roll()}')		

		character.spell_list_choose_from = character.spells_known_selection('base_classes','divine_casters')
		print(f"This is your spells list you can choose from {character.spell_list_choose_from}")




		# Extra class choices:
		character.extra_combat_feats()
		character.class_abilities_amount()


		print(f"This is your selected feats: {character.feats_selector()}")

		#this is to allow for talent choice stat pre-reqs (self.chooseable)
		character.chooseable_list() 		
		character.chooseable_list_stats(character.str, 'str ', base=10)
		character.chooseable_list_stats(character.dex, 'dex ', base=10)
		character.chooseable_list_stats(character.con, 'con ', base=10)
		character.chooseable_list_stats(character.int, 'int ', base=10)
		character.chooseable_list_stats(character.wis, 'wis ', base=10)
		character.chooseable_list_stats(character.cha, 'cha ', base=10)	
		character.chooseable_list_stats(character.bab_total, 'base attack bonus +', base=0 )
		character.chooseable_list_stats(character.casting_level_num, 'caster level ', base=0, th='th')	
		character.chooseable_list_class_features()
		character.chooseable_list_race()

		character.druidic_flag_assigner() 
		character.human_flag_assigner()
		favored_class_list = character.favored_class_option()
		favored_class = character.favored_class_option_chooser(favored_class_list, character.human_flag)
		skill_rank_level, favored_class_chosen = character.favored_class_calculator(favored_class)		

		#decides if druids go animal companion or domain
		# or if inquisitors go inquisitions or domains
		character.domain_chance()

		#class specific choices
		# character.monk_ki_power_chooser()
		# character.bloodline_chooser()

		# character.fighter_armor_train_chooser()
		# character.fighter_weapon_train_chooser()	
		# character.rogue_talent_chooser()
		# character.rage_power_chooser()
		# character.discovery_chooser()
		# character.grand_discovery_chooser()
		# character.arcanist_exploits_chooser()

		character.domain_chooser()	
		character.versatile_perfomance()	
		character.animal_chooser()
		character.animal_feats()	
		character.wizard_school_chooser()
		character.wizard_opposing_school()	
		# character.anti_paladin_cruelty_chooser()
		# character.paladin_mercy_chooser()		


		#class specific feats choosers
		# character.ranger_feats_chooser()
		# character.monk_feats_chooser()


		character.archetype_data()

		# background info








		# character.bloodline_feats_chooser()

		#generic single choices (adds spells?)
		character.generic_class_option_chooser("shaman", "spirits")


		# generic single choices
		character.generic_class_option_chooser("sorcerer", "bloodline")
		character.generic_class_option_chooser("bloodrager", "bloodline")
		character.generic_class_option_chooser("cavalier", "orders")
		character.generic_class_option_chooser("samurai", "orders")
		character.generic_class_option_chooser("warpriest", "blessing")
		character.generic_class_option_chooser("inquisitor", "inquisitions")
		character.generic_class_option_chooser("oracle", "curses")
		character.generic_class_option_chooser("fighter",  dataset_name="armor_train", multiple='yes')
		character.generic_class_option_chooser("fighter", dataset_name="weapon_train", multiple='yes')
		character.generic_class_option_chooser("arcanist", dataset_name="basic", dataset_name_2="greater", multiple='yes', level=10)
		
		#need to add patron spells to the witch spell list (like how clerics + druids + s
		# orcs get their own added)
		character.generic_class_option_chooser("witch", dataset_name="basic", dataset_name_2="greater", dataset_name_3="grand", multiple='yes', level=10, level_2=18)



		# generic multi choices (with pre-reqs)
		character.get_data_without_prerequisites(class_1="rogue",dataset_name="basic", level=10, dataset_name_2="advanced")
		character.get_data_without_prerequisites(class_1="ninja",dataset_name="basic", level=10, dataset_name_2="advanced")
		character.get_data_without_prerequisites(class_1="slayer",dataset_name="basic", level=10, dataset_name_2="advanced")
		character.get_data_without_prerequisites(class_1="alchemist",dataset_name="basic")
		character.get_data_without_prerequisites(class_1="investigator",dataset_name="basic")
		character.get_data_without_prerequisites(class_1="vigilante",dataset_name="basic")
		character.get_data_without_prerequisites(class_1="vigilante",dataset_name="social",odd=True)
		character.get_data_without_prerequisites(class_1="barbarian",dataset_name="basic")
		character.get_data_without_prerequisites(class_1="skald",dataset_name="basic")
		character.get_data_without_prerequisites(class_1="magus",dataset_name="basic")

		character.grand_discovery_chooser() #fix this later


		# >2 Choices based on level
		character.generic_multi_chooser("paladin", "mercy", n=3)
		character.generic_multi_chooser("antipaladin", "cruelty",n=3)
		ki_powers = character.generic_multi_chooser("monk", "ki_powers",n=4,n2=2)


		# feat + spell searcher
		character.feat_spell_searcher("monk", ki_powers, "feats", "benefit")
		character.feat_spell_searcher("monk", ki_powers, "spells", "description")
		character.feat_spell_searcher("bloodrager", character.bonus_feats , "feats", "benefit")
		character.feat_spell_searcher("bloodrager", character.bonus_spells, "spells", "description")
		character.feat_spell_searcher("sorcerer", character.bonus_spells, "spells", "description")

		# character.print_metamagic()
		# character.build_selector()


		character.generic_feat_chooser(character.c_class,'combat',info_column = 'description')


		### Need to change up the item_chooser function ###

		character.armor_chooser()
		print(f'This is your gold pre items {character.assign_gold("gold", gold_num)}')
		print(f'This is your armor type {character.armor_type}')
		equipment_list, equip_descrip = character.item_chooser()
		print(f'This is your gold post items {character.gold}')	

		#calculating savings throws based off of class levels
		fort_saving_throw = character.saving_throw_calc('Fortitude')
		reflex_saving_throw = character.saving_throw_calc('Reflex')
		wisdom_saving_throw = character.saving_throw_calc('Will')	

		skill_ranks = character.skills_selector('skills', skill_rank_level)
		professions = character.profession_chooser("professions")		
		print(f'This is your chosen professions {professions}')		

		character.simple_list_chooser('ranger','favored_terrains', 'favored_enemies')
		character.simple_list_chooser('brawler','manuevers',max_num=8)


		character.armor_dict = character.list_selection('armor', limits=character.armor_type)
		character.weapon_chooser()
		character.weapon_dict = character.list_selection('weapons_data', limits=character.weapon_type)
		limits = character.shield_chooser(character.weapon_dict)
		character.shield_flag = character.shield_flag_func(limits=limits)
		character.shield_dict = character.list_selection('armor', limits=limits, shield_flag = character.shield_flag)

	# Maybe change these
		armor_enhancement = character.enhancement_calculator(3)
		weapon_enhancement = character.enhancement_calculator(2)
		shield_enhancement = character.enhancement_calculator(1)

		armor_ac = character.ac_bonus_calculator(character.armor_dict)
		shield_ac = character.ac_bonus_calculator(character.shield_dict)

		weapon_type_flag = character.weapon_type_flag_func(character.weapon_dict)

		weapon_enhancement_chosen_list = character.enhancement_chooser(character.weapon_qualities,weapon_enhancement, weapon_type_flag)
		armor_enhancement_chosen_list = character.enhancement_chooser(character.armor_qualities,armor_enhancement, 'Armor')
		shield_enhancement_chosen_list = character.enhancement_chooser(character.armor_qualities,shield_enhancement, 'Shield', character.shield_flag)

		print('these are your chosen enhancements **************************')
		print(weapon_enhancement_chosen_list, armor_enhancement_chosen_list, shield_enhancement_chosen_list)

		selected_traits = character.trait_selector(8)
		print(f"These are your selected traits {selected_traits}")


		print(character.Total_HP)
		print(favored_class_chosen)

		hair_color = character.randomize_apperance_attr("hair_colors")
		hair_type = character.randomize_apperance_attr("hair_types")
		eye_color = character.randomize_apperance_attr("eye_colors")
		appearance = character.randomize_apperance_attr("appearance")
		language_text = character.language_chooser()


		print(f'this is your language list {character.language_chooser()}')


		export_list_non_dict = [character.region, character.chosen_race, character.f_name, 
				 character.l_name, character.c_class, character.c_class_2, 
				 character.alignment,  age_number, 
				 height_number, weight_number, character.dex, character.str, 
				 character.con, character.int, character.wis, character.cha, 
				 flaw, character.Total_HP,
				 armor_ac, shield_ac,
				 fort_saving_throw, reflex_saving_throw, wisdom_saving_throw,
				 character.spell_list_choose_from,
				 deity_choice, skill_ranks,
				 weapon_enhancement_chosen_list, armor_enhancement_chosen_list, 
				 shield_enhancement_chosen_list, professions,
				 selected_traits, equipment_list, character.c_class_level,
				 chosen_subrace, subrace_description, character.archetype1,
				 hair_color, hair_type, eye_color, appearance,
				 language_text,
				 
				 ]
		
		string_export_list_non_dict = [
				"character.region", "character.chosen_race", "character.f_name", 
				"character.l_name", "character.c_class", "character.c_class_2", 
				"character.alignment", "age_number", 
				"height_number", "weight_number", "character.dex", "character.str", 
				"character.con", "character.int", "character.wis", "character.cha", 
				"flaw", "character.Total_HP",
				"armor_ac", "shield_ac",
				"fort_saving_throw", "reflex_saving_throw", "wisdom_saving_throw",
				"character.spell_list_choose_from",
				"deity_choice", "skill_ranks",
				"weapon_enhancement_chosen_list", "armor_enhancement_chosen_list", 
				"shield_enhancement_chosen_list", "professions",
				"selected_traits", "equipment_list", "level",
				 "chosen_subrace", "subrace_description", "archetype1",
				 "hair_color", "hair_type", "eye_color", "appearance",
				"language_text",

				]
		
		export_list_dict = [ 
				character.spell_list_choose_from, equip_descrip,
				 ] 

		string_export_list_dict = [ 
				"character.spell_list_choose_from", "equip_descrip",
				 ] 

		character.export_list_non_dict(export_list_non_dict, string_export_list_non_dict)		
		character.export_list_dict(export_list_dict, string_export_list_dict)		

		print(f'this is your character data {character.data_dict}')


		# Need to add a good way to export spells


		# We want this to ouput data we want in json format, so we can send it over to the frontend
		return character.data_dict
	


generate_random_char()

# Add a Subrace Chooser (+ race benefits -> webscrape race data)
# Add an attack macro section (so we know what attack macros someone will get (like +22/+22/+17/+17/+12/+12/+7/+7/+2/ or similar))









							

# choose from the following


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



		

		# print(f'This is your mythic rank {character.randomize_mythic()}')

		# #creating quick race/class specific flags 


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
		



