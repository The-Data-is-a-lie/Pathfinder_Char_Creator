#Custom Made Imports
from Backend.createACharacter import CreateNewCharacter
from Backend.utils.markdown import style
from Backend.utils.data import version
from Backend.utils.util import  chooseClass, region_chooser, race_chooser, weapon_chooser, name_chooser, dip_function, gender_chooser, format_text, isBool#, skills, mythic, Archetype_Assigner, flaws, path_of_war_chance, Roll_Level, Total_Hitpoint_Calc, inherent_stats, age_weight_height, various_racial_attr, appearnce_func, personality_and_profession, path_of_war, alignment_and_deities #chooseClass Roll_Level_40, Roll_Level_30, Roll_Level_20, Roll_Level_10, Roll_Level_5,
import random
from math import ceil, floor
from flask import jsonify
import json
import traceback


# Importing custom functions
from Backend.utils.class_func.alignment_and_deity import randomize_deity, choose_alignment
from Backend.utils.class_func.animal_companions import animal_chooser, animal_feats
from Backend.utils.class_func.appearance import randomize_apperance_attr, randomize_body_feature, get_racial_attr
from Backend.utils.class_func.armor_and_enhancements import enhancement_calculator, enhancement_chooser#, enhancement_limits
from Backend.utils.class_func.armor_and_weapon_chooser import armor_chooser, weapon_chooser, list_selection, shield_chooser, shield_flag_func, ac_bonus_calculator, weapon_type_flag_func
from Backend.utils.class_func.chooseable import chooseable_list, chooseable_list_race#, chooseable_list_class 
from Backend.utils.class_func.class_ability_amount import class_abilities_amount
from Backend.utils.class_func.class_abilities import get_class_abilities, get_class_abilties_desc  
from Backend.utils.class_func.class_specific_feats import class_specific_feats_chooser, feat_chooser, monk_feats_chooser, ranger_feats_chooser
from Backend.utils.class_func.domain_inquisition import domain_chance, domain_chooser#, inquisition_chooser
from Backend.utils.class_func.extra_combat_feats import extra_combat_feats
from Backend.utils.class_func.favored_class import favored_class_calculator, favored_class_option, favored_class_option_chooser
from Backend.utils.class_func.feats import build_selector, chooseable_list, chooseable_list_stats, chooseable_list_class_features, feat_spell_searcher, generic_multi_chooser, simple_list_chooser, generic_feat_chooser
from Backend.utils.class_func.flag_assign import human_flag_assigner, druidic_flag_assigner
from Backend.utils.class_func.generic_func import generic_class_option_chooser, get_data_without_prerequisites#, no_prereq_loop, chosen_set_append
from Backend.utils.class_func.grand_discovery import grand_discovery_chooser
from Backend.utils.class_func.hero_point_generator import hero_point_generator
from Backend.utils.class_func.hp_rolls import roll_hp, total_hp_calc, hit_dice_calc
from Backend.utils.class_func.item_and_price import item_chooser
from Backend.utils.class_func.language import language_chooser#, random_language_chooser ,language_splitter, remove_word ,random_language_chooser
from Backend.utils.class_func.level_and_bab import randomize_level
from Backend.utils.class_func.luck_and_mythic import randomize_luck, randomize_mythic
from Backend.utils.class_func.path_of_war import randomize_path_of_war_num, choose_path_of_war_attr
from Backend.utils.class_func.personality import randomize_personality_attr
from Backend.utils.class_func.profession_chooser import profession_chooser
from Backend.utils.class_func.race_func import  race_ability_score_changes, race_ability_split, race_traits_chooser, subrace_chooser#, full_race_data
from Backend.utils.class_func.randomize_flaw import randomize_flaw
from Backend.utils.class_func.saving_throws import saving_throw_calc
from Backend.utils.class_func.skill_ranks import skills_selector
from Backend.utils.class_func.spells import spells_known_attr, spells_known_extra_roll, spells_known_selection, spells_per_day_attr, spells_per_day_from_ability_mod, class_for_spells_attr, caster_formula #, alignment_spell_limits
from Backend.utils.class_func.stats import roll_stats, print_stats, assign_stats, calc_ability_mod 
from Backend.utils.class_func.traits import trait_selector
from Backend.utils.class_func.versatile_performance import versatile_perfomance
from Backend.utils.class_func.wizard_school import wizard_school_chooser, wizard_opposing_school

#end of custom function import

#Making a Global Character Dictionary so we can reference it and create a HTML/CSS sheet based off of that

global character_data 
global filename
character_data = {}
#Adding in Text to PDF Imports
# import fillpdf        
# from fillpdf import fillpdfs
# from Backend.utils.Text_to_pdf_Best_Version_9_28_23

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
	'ranger': 'Backend/json/class_data/ranger.json',				
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
def generate_random_char(create_new_char='Y', userInput_region=10, userInput_race='orc', class_choice='wizard', multi_class='N', alignment_input = 'N' , userInput_gender='', truly_random_feats = "N", num_dice=3, num_sides=6, high_level=10, low_level=10, gold_num=1000000):

	try:
			# userInput = input('Create a new character? (y/n): ').lower()
			userInput = create_new_char
			print(f'Create a new character? ({create_new_char.lower()})')

			#end of region macro
			# format_text(text, bold=False, color=None)
			character = CreateNewCharacter(
				character_json_config)
			character.instantiate_full_data_dict()

			character.chosen_gender = gender_chooser(character, userInput_gender)
			
			
			region = region_chooser(character,userInput_region)
			chosen_race = race_chooser(character,userInput_race)
			# weapon_chooser(character) # We don't use this anymore, but leave it uncommented for now
			f_name, l_name =name_chooser(character)
			c_class = chooseClass(character,class_choice.lower())
			c_class_2 = dip_function(character,'base_classes', multi_class)

			#add an optional flaws rule function	
			alignment = choose_alignment(character, 'alignments', alignment_input)
			alignment = alignment.title()
			print(f"This is your randomly selected alignment: {alignment}")
			
			deity = randomize_deity(character)
			print(f"This is your randomly selected deity: {deity}")

			age, age_number = randomize_body_feature(character, 'age')
			height, height_number = randomize_body_feature(character, 'height')
			weight, weight_number = randomize_body_feature(character, 'weight')			
			# num_dice = int(input("How many dice would you like to roll? "))
			# num_sides = int(input("How many sides should each die have? "))
			stats = roll_stats(character, num_dice, num_sides)
			assign_stats(character, stats)

			chosen_subrace, subrace_description = subrace_chooser(character)
			print(f'this is your chosen subrace {chosen_subrace}')
			race_traits_list, race_traits_description_list = race_traits_chooser(character)
			print(race_traits_list, race_traits_description_list)

			split_race_traits_list = race_ability_split(character, race_traits_list)
			character.dex = race_ability_score_changes(character, split_race_traits_list, character.dex, 'dex')
			character.str = race_ability_score_changes(character, split_race_traits_list, character.str, 'str')
			character.con = race_ability_score_changes(character, split_race_traits_list, character.con, 'con')
			character.int = race_ability_score_changes(character, split_race_traits_list, character.int, 'int')
			character.wis = race_ability_score_changes(character, split_race_traits_list, character.wis, 'wis')
			character.cha = race_ability_score_changes(character, split_race_traits_list, character.cha, 'cha')
			print_stats(character)

			calc_ability_mod(character)

			flaw = randomize_flaw(character)

			# max_num = int(input("Enter the highest level you want the char to be: "))
			# min_num = int(input("Enter the lowest level (minimum 2) you want the char to be: "))
			# character.randomize_level(min_num, max_num)
			randomize_level(character, low_level, high_level)

			#hp calculations
			hit_dice_calc(character)
			roll_hp(character)
			character.Total_HP = total_hp_calc(character)

			print(f'This is your class for spells: {class_for_spells_attr(character)} ')

			# Some spellcasters get 0th level spells (all high + most mid)
			# Also 0th spells = infinite casting 
			# Wizards + Clerics know all 0th level spells (wizards know all except opposing school)
			# as long as spells known list has a '0th' spell column (even if it isn't 0) 
			# it won't pull any 0th spells for casters with orisons/cantrips
			character.highest_spell_known_1 = caster_formula(character, character.c_class_level)
			character.highest_spell_known_2 = caster_formula(character, character.c_class_2_level, character.c_class_2)
			print(type(character.c_class_2))
			print(character.c_class_2)

			#Divine Casters have all spells known (don't make this function for them)
			print(f'This is your spells known list {spells_known_attr(character, "base_classes", "divine_casters")}')
			print(f'This is your spells per day {spells_per_day_attr(character, "base_classes")}')
			print(f'This is your spells per day from ability mods {spells_per_day_from_ability_mod(character, "caster_mod")}')
			print(f'Spells known + extra randomized spells known [spell book learners only] {spells_known_extra_roll(character )}')		

			character.spell_list_choose_from, day_list, known_list = spells_known_selection(character, 'base_classes','divine_casters')
			print(f"This is your spells list you can choose from {character.spell_list_choose_from}")




			# Extra class choices:
			extra_combat_feats(character)
			class_abilities_amount(character)


			# print(f"This is your selected feats: {character.feats_selector()}")

			#this is to allow for talent choice stat pre-reqs (self.chooseable)
			chooseable_list(character) 		
			chooseable_list_stats(character, character.str, 'str ', base=10)
			chooseable_list_stats(character, character.dex, 'dex ', base=10)
			chooseable_list_stats(character, character.con, 'con ', base=10)
			chooseable_list_stats(character, character.int, 'int ', base=10)
			chooseable_list_stats(character, character.wis, 'wis ', base=10)
			chooseable_list_stats(character, character.cha, 'cha ', base=10)	
			chooseable_list_stats(character, character.bab_total, 'base attack bonus +', base=0 )
			chooseable_list_stats(character, character.casting_level_num, 'caster level ', base=0, th='th')	
			chooseable_list_class_features(character)
			chooseable_list_race(character)

			druidic_flag_assigner(character) 
			human_flag_assigner(character)
			favored_class_list = favored_class_option(character, )
			favored_class = favored_class_option_chooser(character, favored_class_list, character.human_flag)
			skill_rank_level, favored_class_chosen = favored_class_calculator(character, favored_class)		

			#decides if druids go animal companion or domain
			# or if inquisitors go inquisitions or domains
			domain_chance(character)

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

			domain_chooser(character)	
			full_domain = character.chosen_domain
			versatile_perfomance(character)	
			animal_chooser(character)
			animal_feats(character)	

			if character.c_class.lower() == 'wizard':
				full_school, school_desc, associaed_desc, associaed_school = wizard_school_chooser(character)
				full_opposing_school = wizard_opposing_school(character)	
				
			# character.anti_paladin_cruelty_chooser()
			# character.paladin_mercy_chooser()		
			character.archetype_data()

			# background info


			# character.bloodline_feats_chooser()

			#generic single choices (adds spells?)
			generic_class_option_chooser(character,"shaman", "spirits")


			# generic single choices
			if character.c_class == 'sorcerer':
				bloodline_sorc = generic_class_option_chooser(character, "sorcerer", "bloodline")
			else:
				bloodline_sorc = None
			if character.c_class == 'bloodrager':
				bloodline_rager = generic_class_option_chooser(character, "bloodrager", "bloodline")
			else:
				bloodline_rager = None


			generic_class_option_chooser(character,"cavalier", "orders")
			generic_class_option_chooser(character,"samurai", "orders")
			generic_class_option_chooser(character,"warpriest", "blessing")
			generic_class_option_chooser(character,"inquisitor", "inquisitions")
			print("line 316")
			generic_class_option_chooser(character,"oracle", "curses")
			generic_class_option_chooser(character,"fighter",  dataset_name="armor_train", multiple='yes')
			generic_class_option_chooser(character,"fighter", dataset_name="weapon_train", multiple='yes')
			generic_class_option_chooser(character,"arcanist", dataset_name="basic", dataset_name_2="greater", multiple='yes', level=10)
			
			#need to add patron spells to the witch spell list (like how clerics + druids + s
			# orcs get their own added)
			generic_class_option_chooser(character,"witch", dataset_name="basic", dataset_name_2="greater", dataset_name_3="grand", multiple='yes', level=10, level_2=18)

			print("line 326")


			# generic multi choices (with pre-reqs)
			get_data_without_prerequisites(character, class_1="rogue",dataset_name="basic", level=10, dataset_name_2="advanced")
			get_data_without_prerequisites(character, class_1="ninja",dataset_name="basic", level=10, dataset_name_2="advanced")
			get_data_without_prerequisites(character, class_1="slayer",dataset_name="basic", level=10, dataset_name_2="advanced")
			get_data_without_prerequisites(character, class_1="alchemist",dataset_name="basic")
			get_data_without_prerequisites(character, class_1="investigator",dataset_name="basic")
			get_data_without_prerequisites(character, class_1="vigilante",dataset_name="basic")
			get_data_without_prerequisites(character, class_1="vigilante",dataset_name="social",odd=True)
			get_data_without_prerequisites(character, class_1="barbarian",dataset_name="basic")
			get_data_without_prerequisites(character, class_1="skald",dataset_name="basic")
			get_data_without_prerequisites(character, class_1="magus",dataset_name="basic")

			grand_discovery_chooser(character) #fix this later

			# Adding class specific feats


			# >2 Choices based on level
			generic_multi_chooser(character,"paladin", "mercy", n=3)
			generic_multi_chooser(character,"antipaladin", "cruelty",n=3)
			ki_powers = generic_multi_chooser(character,"monk", "ki_powers",n=4,n2=2)


			# feat + spell searcher
			feat_spell_searcher(character, "monk", ki_powers, "feats", "benefit")
			feat_spell_searcher(character, "monk", ki_powers, "spells", "description")
			feat_spell_searcher(character, "bloodrager", character.bonus_feats , "feats", "benefit")
			feat_spell_searcher(character, "bloodrager", character.bonus_spells, "spells", "description")
			feat_spell_searcher(character, "sorcerer", character.bonus_spells, "spells", "description")

			### Need to change up the item_chooser function ###

			armor_chooser(character)
			print(f'This is your gold pre items {character.assign_gold("gold", gold_num)}')
			print(f'This is your armor type {character.armor_type}')
			equipment_list, equip_descrip = item_chooser(character)
			print(f'This is your gold post items {character.gold}')	

			#calculating savings throws based off of class levels
			fort_saving_throw = saving_throw_calc(character, 'Fortitude')
			reflex_saving_throw = saving_throw_calc(character, 'Reflex')
			wisdom_saving_throw = saving_throw_calc(character, 'Will')	

			skill_ranks = skills_selector(character, 'skills', skill_rank_level)
			professions = profession_chooser(character, "professions")		
			print(f'This is your chosen professions {professions}')		

			simple_list_chooser(character, 'ranger','favored_terrains', 'favored_enemies')
			simple_list_chooser(character, 'brawler','manuevers',max_num=8)


			character.armor_dict = list_selection(character, 'armor', limits=character.armor_type)
			weapon_chooser(character)
			character.weapon_dict = list_selection(character, 'weapons_data', limits=character.weapon_type)
			limits = shield_chooser(character, character.weapon_dict)
			character.shield_flag = shield_flag_func(character, limits=limits)
			character.shield_dict = list_selection(character, 'armor', limits=limits, shield_flag = character.shield_flag)
			print("line 393")

		# Maybe change these
			armor_enhancement = enhancement_calculator(character, 3)
			weapon_enhancement = enhancement_calculator(character, 2)
			shield_enhancement = enhancement_calculator(character, 1)

			armor_ac = ac_bonus_calculator(character, character.armor_dict)
			shield_ac = ac_bonus_calculator(character, character.shield_dict)

			weapon_type_flag = weapon_type_flag_func(character, character.weapon_dict)

			weapon_enhancement_chosen_list = enhancement_chooser(character, character.weapon_qualities,weapon_enhancement, weapon_type_flag)
			armor_enhancement_chosen_list = enhancement_chooser(character, character.armor_qualities,armor_enhancement, 'Armor')
			shield_enhancement_chosen_list = enhancement_chooser(character, character.armor_qualities,shield_enhancement, 'Shield', character.shield_flag)

			print('these are your chosen enhancements **************************')
			print(weapon_enhancement_chosen_list, armor_enhancement_chosen_list, shield_enhancement_chosen_list)

			selected_traits = trait_selector(character, 8)
			print(f"These are your selected traits {selected_traits}")


			print(character.Total_HP)
			print(favored_class_chosen)

			print("line 416")

			# pre export data manip start
			hero_points = hero_point_generator()


			hair_color = randomize_apperance_attr(character, "hair_colors")
			hair_type = randomize_apperance_attr(character, "hair_types")
			eye_color = randomize_apperance_attr(character, "eye_colors")
			appearance = randomize_apperance_attr(character, "appearance")
			language_text = language_chooser(character)


			print(f'this is your language list {language_chooser(character)}')

			character_full_name = f_name + ' ' + l_name

			deity_name = deity["Name"]

			print("this is your skill ranks", skill_ranks)


			skill_ranks = json.dumps(skill_ranks)		
			print("this is your items list", character.items.keys())
			print("this is your equipment list length", len(equipment_list))
			print("this is your equipment list length", len(character.items.keys()))

			print("this is your armor dict", character.armor_dict)
			print("this is your shield dict", character.shield_dict)


			if isinstance(character.armor_dict, dict):
				armor_name = list(character.armor_dict.keys())[0]
				armor_dict = character.armor_dict.get(next(iter(character.armor_dict), 0), 0)
				armor_spell_failure = armor_dict.get('spell_failure', 0)
				armor_armor_check_penalty = armor_dict.get('armor check penalty', 0)
				armor_weight = armor_dict.get('weight', 0)
				armor_max_dex_bonus = armor_dict.get('max dex bonus', 0)
				if armor_max_dex_bonus == None:
					armor_max_dex_bonus = 0
			else:
				armor_name = 0
				armor_spell_failure = 0
				armor_armor_check_penalty = 0
				armor_weight = 0
				armor_max_dex_bonus = 0

			print("This is your armor variables: ",armor_name, armor_spell_failure, armor_weight, armor_armor_check_penalty)
			print(character.armor_dict.keys())


			if isinstance(character.shield_dict, dict) and character.shield_dict != None:
				shield_name = list(character.shield_dict.keys())[0]
				shield_dict = character.shield_dict.get(next(iter(character.shield_dict), 0), 0)
				shield_spell_failure = shield_dict.get('spell_failure', 0)
				shield_armor_check_penalty = shield_dict.get('shield check penalty', 0)
				shield_weight = shield_dict.get('weight', 0)			
				shield_max_dex_bonus = armor_dict.get('max dex bonus', 0)

			else:
				shield_name = " "
				shield_spell_failure = " "
				shield_armor_check_penalty = " "
				shield_weight = " "
				shield_max_dex_bonus = " "


			character.platnium = character.gold / 10
		
			try:
				domain = next(iter(full_domain.keys()), "N/A")
			except (NameError, AttributeError):
				domain = "N/A"



			try:
				if bloodline_sorc:
					bloodline_full = bloodline_sorc
					bloodline = next(iter(bloodline_full.keys()), "N/A")
				elif bloodline_rager:
					bloodline_full = bloodline_rager
					bloodline = next(iter(bloodline_full.keys()), "N/A")
				else:
					bloodline = "N/A"

			except (NameError, AttributeError):
				bloodline = "N/A"


			try:
				school = full_school if full_school else "N/A"
			except NameError:
				school = "N/A"

			try:
				opposing_school = full_opposing_school if full_opposing_school else "N/A"
			except NameError:
				opposing_school = "N/A"


			print("line 516")

			print('school + domain + bloodline + opposing school')
			print(school)
			print(opposing_school)
			print(bloodline)
			character.bloodline = bloodline
			print(full_domain)


		# end of pre export data manip

			# Start of Extra feats list generation section
			
			class_specific_feats_chooser(character, "sorcerer", "bloodline", character.bloodline, name_3="bonus feats")
			class_specific_feats_chooser(character, "bloodrager", "bloodline", character.bloodline, name_3="bonus feats")
			# class_specific_feats_chooser(character, "monk", "feats", "2", class_level= 2)
			# class_specific_feats_chooser(character, "monk", "feats", "6", class_level= 6)
			# class_specific_feats_chooser(character, "monk", "feats", "10", class_level= 10)
			

			#End of Extra feats list generation section

			# Start of Extra feats selection Section
   
			extra_feats = feat_chooser(character, character.total_feats, character.class_feats)
			character.feats.extend(extra_feats)

			#class specific feats choosers
			ranger_feats_chooser(character)
			monk_feats_chooser(character)
				
			# feat selector
			print(f"this is your chosen feat amount {character.feat_amounts}")
			
			# feat selector(s)
			print("this is the value of truly random feats", truly_random_feats.upper())
			if truly_random_feats.upper() == "Y":
			# Truly Random Feats
			# full casters + mid casters with low BAB
				casting_level_str = character.classes[character.c_class]['casting level'].lower()
				if character.bab == "L" and casting_level_str in ("mid", "high"):
						character.feats = generic_feat_chooser(character, character.c_class,'metamagic',info_column = 'description')

				# full casters + mid casters with med BAB
				elif character.bab == "M" and casting_level_str in ("mid", "high"):
					random_dice = random.randint(1, 100)
					if random_dice <= 50:
						character.feats = generic_feat_chooser(character, character.c_class,'metamagic',info_column = 'description')					
					else:
						character.feats = generic_feat_chooser(character, character.c_class,'combat',info_column = 'description')

			else:
				print("build selector is being activated")
				# Curated List of feats
				build_selector_feats = build_selector(character)
				print("these are your extra feats", build_selector_feats)
				chosen_feats = random.sample(build_selector_feats,k=character.feat_amounts)
				character.feats.extend(chosen_feats)

				print("this is your giga chosen feats", chosen_feats)
				character.feats.extend(chosen_feats)
		


			print(f"this is your chosen feats {character.feats}")

			print("this is your language text", language_text)

			feats = character.feats
			print("these are your feats being sent", feats)
			print(hero_points)


			background_traits = randomize_personality_attr(character, "background_traits",4)
			professions = randomize_personality_attr(character, "professions", 3)
			mannerisms = randomize_personality_attr(character, "mannerisms", 3)
			flaws = randomize_personality_attr(character, "flaws", 3)

			actual_class_abilities = get_class_abilities(character)
			class_ability_desc = get_class_abilties_desc(character, actual_class_abilities)
						
			export_list_non_dict = [character.region, character.chosen_race,
					character_full_name, character.c_class, character.c_class_2, 
					alignment,  age_number, 
					height_number, weight_number, character.dex, character.str, 
					character.con, character.int, character.wis, character.cha, 
					flaw, character.Total_HP, character.total_hp_rolls,
					character.bab_total,
					armor_ac, shield_ac,
					armor_name, armor_spell_failure, armor_weight, armor_armor_check_penalty, armor_max_dex_bonus,
					shield_name, shield_spell_failure, shield_weight, shield_armor_check_penalty, shield_max_dex_bonus,
					fort_saving_throw, reflex_saving_throw, wisdom_saving_throw,
					character.spell_list_choose_from,
					day_list, known_list,
					deity_name, skill_ranks,
					weapon_enhancement_chosen_list, armor_enhancement_chosen_list, 
					shield_enhancement_chosen_list, professions,
					selected_traits, equipment_list, character.c_class_level,
					chosen_subrace, subrace_description, character.archetype1,
					hair_color, hair_type, eye_color, appearance,
					language_text, feats, 
					character.gold, character.platnium,
					full_domain, school, opposing_school,
					bloodline,
					background_traits, professions, mannerisms, flaws,
					hero_points, character.chosen_gender,
					class_ability_desc,					
					]
			
			string_export_list_non_dict = [
					"region", "chosen_race", "character_full_name", 
					"c_class", "c_class_2", 
					"alignment", "age_number", 
					"height_number", "weight_number", "dex", "str", 
					"con", "int", "wis", "cha", 
					"flaw", "Total_HP", "total_hp_rolls",
					"bab_total",
					"armor_ac", "shield_ac",
					"armor_name", "armor_spell_failure", "armor_weight", "armor_armor_check_penalty", "armor_max_dex_bonus",
					"shield_name", "shield_spell_failure", "shield_weight", "shield_armor_check_penalty", "shield_max_dex_bonus",				
					"fort_saving_throw", "reflex_saving_throw", "wisdom_saving_throw",
					"spell_list_choose_from",
					"day_list", "known_list",
					"deity_name", "skill_ranks",
					"weapon_enhancement_chosen_list", "armor_enhancement_chosen_list", 
					"shield_enhancement_chosen_list", "professions",
					"selected_traits", "equipment_list", "level",
					"chosen_subrace", "subrace_description", "archetype1",
					"hair_color", "hair_type", "eye_color", "appearance",
					"language_text", "feats", 
					"gold", "platnium",
					"full_domain", "school", "opposing_school",
					"bloodline",
					"background_traits", "professions", "mannerisms", "flaws",
					"hero_points", "gender",
					"class_ability_desc",


					]
			
			export_list_dict = [ 
					character.spell_list_choose_from, equip_descrip,
					] 

			string_export_list_dict = [ 
					"spell_list_choose_from_dict", "equip_descrip",
					] 

			character.export_list_non_dict(export_list_non_dict, string_export_list_non_dict)		
			character.export_list_dict(export_list_dict, string_export_list_dict)		

			print(f'this is your character data {character.data_dict}')

			return character.data_dict
	except Exception as e:
		traceback.print_exc()		


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
		
							



		# print(f' This is your alignment {character.randomize_alignment("alignments")}')

		# print(f'This is your Deity {character.randomize_deity("all_deities")}')

		# # skill rank generator (class ranks + int)*level



		# Archetype_Assigner(character)
		# print(f'This is your gold {character.assign_gold("gold")}')
		# #use gold to randomly select items



		

		# print(f'This is your mythic rank {randomize_mythic(character)}')

		# #creating quick race/class specific flags 


		# #3PP Content Only
		# # Path of War Content
		# randomize_path_of_war_num(character, "path_of_war_class")
		# print(f'This is your Path of War Path {choose_path_of_war_attr(character, "disciplines")}')

		# #Luck Content
		# print(f'this is your luck score {randomize_luck(character)}')



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
		



