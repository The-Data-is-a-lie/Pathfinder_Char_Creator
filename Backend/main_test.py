#Custom Made Imports
from utils.createACharacter 						import CreateNewCharacter, Load_when_needed
from utils.data 									import version
from utils.util 									import  (chooseClass, region_chooser, race_chooser,  name_chooser, 
										  					dip_function, gender_chooser) 
import random
import json


# Importing custom functions
from utils.class_func.adding_bonus_spells			import add_bonus_spells, add_bonus_spells_from_dict
from utils.class_func.alignment_and_deity 			import randomize_deity, choose_alignment
from utils.class_func.animal_companions 			import animal_chooser, animal_feats
from utils.class_func.appearance 					import randomize_apperance_attr, randomize_body_feature, get_racial_attr
from utils.class_func.armor_and_enhancements 		import enhancement_calculator, enhancement_chooser#, enhancement_limits
from utils.class_func.armor_and_weapon_chooser 		import (armor_chooser, weapon_chooser, list_selection, shield_chooser, 
                                                                 shield_flag_func, ac_bonus_calculator, weapon_type_flag_func)
from utils.class_func.chooseable 					import chooseable_list, chooseable_list_race#, chooseable_list_class 
from utils.class_func.class_abilities 				import get_class_abilities, get_class_abilties_desc  
from utils.class_func.class_specific_feats 			import class_specific_feats_chooser, monk_feats_chooser, ranger_feats_chooser
from utils.class_func.domain_inquisition 			import domain_chance, domain_chooser#, inquisition_chooser
from utils.class_func.extra_combat_feats 			import extra_combat_feats, extra_teamwork_feats
from utils.class_func.favored_class 				import favored_class_calculator, favored_class_option, favored_class_option_chooser
from utils.class_func.family_func 					import randomize_siblings, randomize_parents
from utils.class_func.feats 						import (build_selector, chooseable_list, chooseable_list_stats, 
                                                  			chooseable_list_class_features, feat_spell_searcher, generic_multi_chooser, 
                                                            simple_list_chooser, generic_feat_chooser)
from utils.class_func.flag_assign 					import human_flag_assigner, druidic_flag_assigner
from utils.class_func.generic_func 					import generic_class_option_chooser, get_data_without_prerequisites, no_prereq_prep#, no_prereq_loop, chosen_set_append
from utils.class_func.grand_discovery 				import grand_discovery_chooser
from utils.class_func.gunslinger 					import choose_gun_func
from utils.class_func.hero_point_generator 			import hero_point_generator
from utils.class_func.hp_rolls 						import roll_hp, total_hp_calc, hit_dice_calc
from utils.class_func.item_and_price 				import item_chooser
from utils.class_func.language 						import language_chooser
from utils.class_func.level_and_bab 				import randomize_level
# from utils.class_func.luck_and_mythic 				import randomize_luck, randomize_mythic
# from utils.class_func.path_of_war 					import randomize_path_of_war_num, choose_path_of_war_attr

# from utils.class_func.path_of_war_funcs				import select_disciplines

from utils.class_func.personality 					import randomize_personality_attr
from utils.class_func.profession_chooser 			import profession_chooser
# from utils.class_func.race_func 					import (race_ability_score_changes, race_ability_split, 
#                                                      		race_traits_chooser, subrace_chooser)#, full_race_data
from utils.class_func.randomize_flaw 				import randomize_flaw_amount
from utils.class_func.skill_ranks 					import skills_selector
from utils.class_func.spells 						import (extra_spells_divine, spells_known_attr, 
										   					spells_known_extra_roll, spells_known_selection, 
                                                   	        spells_per_day_attr, spells_per_day_from_ability_mod,
                                                            class_for_spells_attr, caster_formula)#, alignment_spell_limits
from utils.class_func.stats 						import roll_stats, assign_stats, calc_ability_mod 
from utils.class_func.separate_feats_func 			import separate_feats_func
from utils.class_func.traits 						import trait_selector
from utils.class_func.versatile_performance 		import versatile_perfomance
from utils.class_func.wizard_school 				import wizard_school_chooser, wizard_opposing_school

#end of custom function import

#Making a Global Character Dictionary so we can reference it and create a HTML/CSS sheet based off of that

global character_data 
global filename
character_data = {}

print(
"*******************************************************************"
"*******************************************************************"
"*******************************************************************"
"********************	Character Generator		********************"
"*******************************************************************"
"*******************************************************************"
"*******************************************************************"
"*******************************************************************"
)

character_json_config = {
	'animal_companion': Load_when_needed('Backend/json/animal_companion.json'),	
	'animal_choices': Load_when_needed('Backend/json/animal_choices.json'),
	'archetypes': Load_when_needed('Backend/json/archetypes.json'),
	'armor_qualities': Load_when_needed('Backend/json/armor_qualities.json'),
	'armor': Load_when_needed('Backend/json/armor.json'),
	'bard_choices': Load_when_needed('Backend/json/bard_choices.json'),	
	'bloodlines': Load_when_needed('Backend/json/bloodlines.json'),
	'class_features': Load_when_needed('Backend/json/class_features.json'),	
	# 'classes': Load_when_needed('Backend/json/class.json'),
	'class_data': Load_when_needed('Backend/json/class_data.json'),
	'cleric_domains': Load_when_needed('Backend/json/cleric_domains.json'),				
	'deity': Load_when_needed('Backend/json/deity.json'),	
	'druid_domains': Load_when_needed('Backend/json/druid_domains.json'),		
	'feat_buckets': Load_when_needed('Backend/json/feat_buckets.json'),
	'feat_tax': Load_when_needed('Backend/json/feat_tax.json'),
	'first_names_regions': Load_when_needed('Backend/json/first_names_regions.json'),
	'firearms': Load_when_needed('Backend/json/firearms.json'),
	'flaws': Load_when_needed('Backend/json/flaws.json'),
	'foundry_item_names': Load_when_needed('Backend/json/foundry_item_names.json'),
	'items': Load_when_needed('Backend/json/items_best.json'),
	'last_names_regions': Load_when_needed('Backend/json/last_names_regions.json'),
	'PlayableRaces': Load_when_needed('Backend/json/PlayableRaces.json'),
	'profession': Load_when_needed('Backend/json/profession.json'),
	'races': Load_when_needed('Backend/json/races.json'),
	'spells_known': Load_when_needed('Backend/json/spells_known.json'),
	'spells_per_day': Load_when_needed('Backend/json/spells_per_day.json'),
	'spells_from_ability_mod': Load_when_needed('Backend/json/spells_from_ability_mod.json'),
	'traits': Load_when_needed('Backend/json/traits_abilities.json'),
	'weapons_data': Load_when_needed('Backend/json/weapons_data.json'),
	'weapon_qualities': Load_when_needed('Backend/json/weapon_qualities.json'),
	'wizard_schools': Load_when_needed('Backend/json/wizard_schools.json'),	

	# Class portion					
	'alchemist': Load_when_needed('Backend/json/class_data/alchemist.json'),
	'antipaladin': Load_when_needed('Backend/json/class_data/antipaladin.json'),
	'arcanist': Load_when_needed('Backend/json/class_data/arcanist.json'),
	'barbarian': Load_when_needed('Backend/json/class_data/barbarian.json'),
	'bloodrager': Load_when_needed('Backend/json/class_data/bloodrager.json'),
	'cavalier': Load_when_needed('Backend/json/class_data/cavalier.json'),
	'fighter': Load_when_needed('Backend/json/class_data/fighter.json'),
	'inquisitor': Load_when_needed('Backend/json/class_data/inquisitor.json'),
	'investigator': Load_when_needed('Backend/json/class_data/investigator.json'),
	'magus': Load_when_needed('Backend/json/class_data/magus.json'),
	'monk': Load_when_needed('Backend/json/class_data/monk.json'),
	'ninja': Load_when_needed('Backend/json/class_data/ninja.json'),
	'oracle': Load_when_needed('Backend/json/class_data/oracle.json'),
	'paladin': Load_when_needed('Backend/json/class_data/paladin.json'),
	'ranger': Load_when_needed('Backend/json/class_data/ranger.json'),				
	'rogue': Load_when_needed('Backend/json/class_data/rogue.json'),
	'shaman': Load_when_needed('Backend/json/class_data/shaman.json'),
	'skald': Load_when_needed('Backend/json/class_data/skald.json'),
	'slayer': Load_when_needed('Backend/json/class_data/slayer.json'),
	'samurai': Load_when_needed('Backend/json/class_data/samurai.json'),
	'sorcerer': Load_when_needed('Backend/json/class_data/sorcerer.json'),
	'vigilante': Load_when_needed('Backend/json/class_data/vigilante.json'),
	'warpriest': Load_when_needed('Backend/json/class_data/warpriest.json'),
	'witch': Load_when_needed('Backend/json/class_data/witch.json'),

	# Path of War section
	# 'path_of_war_classes': Load_when_needed('Backend\json\class_data\path_of_war\path_of_war_classes.json'),
	# 'path_of_war_archetypes': Load_when_needed('Backend\json\class_data\path_of_war\path_of_war_archetypes.json'),
	# 'martial_disciplines': Load_when_needed('Backend\json\class_data\path_of_war\martial_disciplines.json'),
	# 'path_of_war_maneuvers_known': Load_when_needed('Backend\json\class_data\path_of_war\path_of_war_maneuvers_known.json'),
}

# Non random feats sometiems break at 20+
# Make sure to make a flag for adding metzofitz feats later
# Make sure to add a flag for path of war feats later
def generate_random_char(create_new_char='Y', userInput_region="Tal-Falko", userInput_race='Half-Orc', class_choice='fighter', multi_class='N', 
						 alignment_input = 'LG' , deity_flag = 'Pharasma', userInput_gender='female', truly_random_feats = "Y", inherents = "Y", num_dice=4, num_sides=6, 
						 high_level=15, low_level=15, gold_num=1000000, homebrew_feat_amount="Y"):
		
		print(create_new_char)
		print(userInput_region)
		print(userInput_race)
		print(class_choice)
		print(multi_class)
		print(alignment_input)
		print(deity_flag)
		print(userInput_gender)
		print(truly_random_feats)
		print(inherents)
		print(num_dice)
		print(num_sides)
		print(high_level)
		print(low_level)
		print(gold_num)
		print(homebrew_feat_amount)
		casting_level_str_foundry = 'None'
		
		character = CreateNewCharacter(
			character_json_config)
		character.instantiate_full_data_dict()
		character.data_dict['class features'] = {}

		# Flag that allows for homebrew feats to be added
		character.homebrew_feat_amount = homebrew_feat_amount
		# Instantitae character.class_feats_amount
		character.class_feats_amount = 0
		# Instantitae teamwork_feats
		teamwork_feats = 0

		# prep variables
		no_prereq_prep(character)
		character.processed_feats = set()
		character.cached_dataset_without_prerequisites = []
		character.cached_prereq_list = set()
		character.chooseable_talents = []
				
		character.chosen_gender = gender_chooser(character, userInput_gender)
		 
		region_chooser(character,userInput_region)
		race_chooser(character,userInput_race)
		f_name, l_name =name_chooser(character)
		chooseClass(character,class_choice)
		dip_function(character,'base_classes', multi_class)

		#add an optional flaws rule function	
		alignment, mini_alignment = choose_alignment(character, 'alignments', alignment_input)
		alignment = alignment.title()

		if deity_flag.lower() == 'random':
			deity = randomize_deity(character, random_flag=True)
			print("deity 1", deity)
		else:
			deity = randomize_deity(character, random_flag=False, deity_choice=deity_flag)
			print("deity 2", deity)

 
		age_number = randomize_body_feature(character, 'age')
		height_number = randomize_body_feature(character, 'height')
		weight_number = randomize_body_feature(character, 'weight')			

		# We don't use subrace data in foundryVTT (comment these out if we want to (will need to fix their issues first))
		# chosen_subrace, subrace_description = subrace_chooser(character)
		# race_traits_list, race_traits_description_list = race_traits_chooser(character)
		# split_race_traits_list = race_ability_split(character, race_traits_list)

		flaw_amount = randomize_flaw_amount()
		flaw = randomize_personality_attr(character, "flaws", flaw_amount,flaw_amount)
		background_traits = randomize_personality_attr(character, "background_traits",1,4)
		professions = randomize_personality_attr(character, "professions",1, 3)
		mannerisms = randomize_personality_attr(character, "mannerisms",2,4)
		personality_traits = randomize_personality_attr(character, "personality_traits",3,6)
		# Flaws chosen earlier in it's own function


		# I don't know why, but these keep breaking the game (if low enough level and stats)
		if character.c_class in ('rogue (unchained)', 'vigilante') and low_level <= 1:
			low_level = 2
		if character.c_class == ('rogue (unchained)', 'vigilante') and high_level <= 1:
			high_level = 2
		randomize_level(character, low_level, high_level, flaw_amount)

		#stats after level (because we roll inherents which depend on level)
		stats = roll_stats(character, num_dice, num_sides, inherents)
		assign_stats(character, stats)
		calc_ability_mod(character)


		#hp calculations
		hit_dice_calc(character)
		total_rolled_hp = roll_hp(character)
		character.Total_HP = total_hp_calc(character)

		# Choosing character class for spells
		class_for_spells_attr(character)

		# Some spellcasters get 0th level spells (all high + most mid)
		# Also 0th spells = infinite casting 
		# Wizards + Clerics know all 0th level spells (wizards know all except opposing school)
		# as long as spells known list has a '0th' spell column (even if it isn't 0) 
		# it won't pull any 0th spells for casters with orisons/cantrips
		character.highest_spell_known_1 = caster_formula(character, character.c_class_level)
		character.highest_spell_known_2 = caster_formula(character, character.c_class_2_level, character.c_class_2)

		#Divine Casters have all spells known (don't make this function for them)

		
		spells_known_attr(character, "base_classes", "divine_casters")
		day_list = spells_per_day_attr(character, "base_classes")
		spells_per_day_from_ability_mod(character, "caster_mod")
		spells_known_extra_roll(character)
		extra_spells_divine(character)

		character.spell_list_choose_from, day_list, known_list = spells_known_selection(character)


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
		domain_chooser(character)	
		full_domain = character.chosen_domain
		versatile_perfomance(character)	
		animal_chooser(character)
		animal_feats(character)	


		full_school = None
		if character.c_class.lower() == 'wizard':
			full_school = wizard_school_chooser(character)
			full_opposing_school = wizard_opposing_school(character, full_school)	

		archetype_info = character.archetype_data()
		character.archetype_data()

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
		generic_class_option_chooser(character,"warpriest", "blessing", multiple='yes', alternate_dataset=True)
		generic_class_option_chooser(character,"inquisitor", "inquisitions", multiple='yes', alternate_dataset=True)
		# Need to add revelations to oracle

		# Make this populate like how you want it to *********
		
		# Choose Oracle mystery
		if character.c_class.lower() == 'oracle':
			pre_oracle_mystery = generic_class_option_chooser(character, "oracle", "mysteries", dict_name = 'mysteries')
			oracle_mystery = list(pre_oracle_mystery.keys())[0]
			generic_class_option_chooser(character,"oracle", dataset_name="mysteries", dataset_name_2=oracle_mystery, dataset_name_3="revelations", multiple='yes', alternate_dataset = True, level = 99, level_2 = 99, dict_name = 'mysteries')

		generic_class_option_chooser(character, "oracle", "curses", dict_name = "curses")


		generic_class_option_chooser(character,"fighter",  dataset_name="armor_train", multiple='yes', dict_name = 'armor_training')
		generic_class_option_chooser(character,"fighter", dataset_name="weapon_train", multiple='yes', dict_name = 'weapon_training')
		generic_class_option_chooser(character,"arcanist", dataset_name="basic", dataset_name_2="greater", multiple='yes', level=10, dict_name = 'exploits')
		
		#need to add patron spells to the witch spell list (like how clerics + druids + s
		# orcs get their own added)
		generic_class_option_chooser(character,"witch", dataset_name="basic", dataset_name_2="greater", dataset_name_3="grand", multiple='yes', level=10, level_2=18, dict_name = 'hexes')

		generic_class_option_chooser(character,"shaman", "spirits", dict_name = 'spirits')
		generic_class_option_chooser(character,"shaman", dataset_name="hexes", dataset_name_2 = "basic", multiple='yes', alternate_dataset = True, level = 99, dict_name = 'hexes')



		# generic multi choices (with pre-reqs)
		get_data_without_prerequisites(character, class_1="rogue",dataset_name="basic", level=10, dataset_name_2="advanced", dict_name = 'rogue_talents')
		get_data_without_prerequisites(character, class_1="ninja",dataset_name="basic", level=10, dataset_name_2="advanced", dict_name = 'ninja_talents')
		get_data_without_prerequisites(character, class_1="slayer",dataset_name="basic", level=10, dataset_name_2="advanced", dict_name = 'slayer_talents')
		get_data_without_prerequisites(character, class_1="alchemist",dataset_name="basic", dict_name = 'discoveries')
		get_data_without_prerequisites(character, class_1="investigator",dataset_name="basic", dict_name = 'investigator_talents')
		get_data_without_prerequisites(character, class_1="vigilante",dataset_name="basic", dict_name = 'vigilante_talents')
		get_data_without_prerequisites(character, class_1="vigilante",dataset_name="social",odd=True, dict_name = 'social_talents')
		get_data_without_prerequisites(character, class_1="barbarian",dataset_name="basic", dict_name = 'rage_powers')
		get_data_without_prerequisites(character, class_1="skald",dataset_name="basic", divisor = 3, dict_name = 'rage_powers')
		get_data_without_prerequisites(character, class_1="magus",dataset_name="basic", dict_name = 'arcana')

		grand_discovery_chooser(character) #fix this later

		# Adding class specific feats


		# >2 Choices based on level
		generic_multi_chooser(character,"paladin", "mercy", n2=3, start_level=3)
		generic_multi_chooser(character,"antipaladin", "cruelty",n2=3, start_level=3)
		ki_powers = generic_multi_chooser(character,"monk", "ki_powers",n2=2,start_level=4)


		# feat + spell searcher
		feat_spell_searcher(character, "monk", ki_powers, "feats", "benefit")
		feat_spell_searcher(character, "monk", ki_powers, "spells", "description")
		feat_spell_searcher(character, "bloodrager", character.bonus_feats , "feats", "benefit")
		# feat_spell_searcher(character, "bloodrager", character.bonus_spells, "spells", "description")
		# feat_spell_searcher(character, "sorcerer", character.bonus_spells, "spells", "description")

		# Choosing guns for gunslinger
		choose_gun_func(character, character.c_class)






		### Need to change up the item_chooser function ###

		armor_chooser(character)
		character.assign_gold("gold", gold_num)

		# Pre-loading JSON data (so we only do it 1x per item and not multiple times)
		# Open JSON file to see if name is in that list, otherwise reroll and document
		
		# This breaks perm server if Double \\ 
		foundry_item_names = character.foundry_item_names
		
		equipment_list, equip_descrip = item_chooser(character, foundry_item_names)#, foundry_item_names)

		#calculating savings throws based off of class levels
		# fort_saving_throw = saving_throw_calc(character, 'Fortitude')
		# reflex_saving_throw = saving_throw_calc(character, 'Reflex')
		# wisdom_saving_throw = saving_throw_calc(character, 'Will')	

		skill_ranks = skills_selector(character, 'skills', skill_rank_level)
		professions = profession_chooser(character, "professions")		

		simple_list_chooser(character, 'ranger','favored_terrains', 'favored_enemies')
		simple_list_chooser(character, 'brawler','manuevers',max_num=8)


		character.armor_dict = list_selection(character, 'armor', limits=character.armor_type)
		
		# required to set up weapon_type
		weapon_chooser(character)
		character.weapon_dict = list_selection(character, 'weapons_data', limits=character.weapon_type)

		weapon_name = list(character.weapon_dict.keys())[0]
		limits = shield_chooser(character, character.weapon_dict)
		character.shield_flag = shield_flag_func(character, limits=limits)
		character.shield_dict = list_selection(character, 'armor', limits=limits, shield_flag = character.shield_flag)

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


		selected_traits = trait_selector(character, 8)
		# pre export data manip start
		hero_points = hero_point_generator()


		hair_color = randomize_apperance_attr(character, "hair_colors")
		hair_type = randomize_apperance_attr(character, "hair_types")
		eye_color = randomize_apperance_attr(character, "eye_colors")
		appearance = randomize_apperance_attr(character, "appearance")
		language_text = language_chooser(character)
		language_chooser(character)
		character_full_name = f_name + ' ' + l_name
		deity_name = deity["Name"]
		print("deity_name", deity_name)
		print("deity", deity)
		skill_ranks = json.dumps(skill_ranks)		

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
	
		# try:
		# 	domain = next(iter(full_domain.keys()), "N/A")
		# except (NameError, AttributeError):
		# 	domain = "N/A"



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

		character.bloodline = bloodline


	# end of pre export data manip

		# Start of Extra feats list generation section
		class_specific_feats_chooser(character, "sorcerer", "bloodline", character.bloodline, name_3="bonus feats")
		class_specific_feats_chooser(character, "bloodrager", "bloodline", character.bloodline, name_3="bonus feats")
		#class specific feats choosers
		ranger_feats_chooser(character)
		monk_feats_chooser(character)
		# Determine extra teamwork feats
		extra_teamwork_feats(character)
		# determine extra combat feats
		extra_combat_feats(character)


		# Cached dataset without prerequisites -> allows them to take rage powers / rogue talents / etc. without normal feats ()
		print("cached dataset without prereqs allows for feats to buy class specific talents ")
		print("character.cached_dataset_without_prerequisites", sorted(character.cached_dataset_without_prerequisites))

		# Feat Selector
		casting_level_str = character.class_data[character.c_class]['casting level'].lower()
		print("character.chooseable", character.chooseable)
		character.feat_amounts += character.class_feats_amount
		if truly_random_feats.upper() == "Y":
		# Truly Random Feats
		# full casters + mid casters with low BAB
			if character.bab == "L" and casting_level_str in ("mid", "high"):
					character.feats = generic_feat_chooser(character, character.c_class, casting_level_str,'metamagic',info_column = 'description', feat_amount = character.feat_amounts)

			# full casters + mid casters with med BAB
			elif character.bab == "M" and casting_level_str in ("mid", "high"):
				random_dice = random.randint(1, 100)
				if random_dice <= 50:
					character.feats = generic_feat_chooser(character, character.c_class, casting_level_str,'metamagic',info_column = 'description', feat_amount = character.feat_amounts)					
				else:
					character.feats = generic_feat_chooser(character, character.c_class, casting_level_str,'combat',info_column = 'description', feat_amount = character.feat_amounts)
			else:
				character.feats = generic_feat_chooser(character, character.c_class, casting_level_str,'combat', info_column = 'description', feat_amount = character.feat_amounts)

		else:
			# Curated List of feats
			# build selector can potentially grab high level feats at a lower level (so a 9th rogue can take vital strike any level)
			# because we run get_data_without_prerequisites before build_selector -> updating character.chooseable
			build_selector_feats = build_selector(character)
			character.feats.extend(build_selector_feats)

		# Teamwork feats selector
		if character.teamwork_feats > 0:
			character.teamwork_feats += 1
			teamwork_feats = generic_feat_chooser(character, character.c_class, casting_level_str, 'Null', info_column = 'description', override=True, special_type="teamwork", feat_amount = character.teamwork_feats)

		# Add later -> to allow for specialized class feats
		# if character.class_feats_amount > 0:
		# 	class_feats = generic_feat_chooser(character, character.c_class, casting_level_str, 'Null', info_column = 'description', override=True, special_type="teamwork", feat_amount = character.teamwork_feats)

		feats = character.feats 



		actual_class_abilities = get_class_abilities(character)
		class_ability_desc, class_ability =get_class_abilties_desc(character, actual_class_abilities)

		older_brothers, younger_brothers, older_sisters, younger_sisters = randomize_siblings(character)
		parents = randomize_parents(character)		

		# For some reason class_features is being created as a dict inside a list, rather than a dict
		class_features = character.data_dict['class features']

		# Prep casting level string for foundry:
		if casting_level_str.lower() in ("low", "high"):
			casting_level_str_foundry = casting_level_str.lower()
		elif casting_level_str == "mid":
			casting_level_str_foundry = "med"

		

		# Start of turning class_features into a dictionary for oracle
		
		if isinstance(class_features, list) and len(class_features) > 0:
			combined_dict = {}
			for i, feature in enumerate(class_features):
				if not isinstance(feature, dict):
					continue
				combined_dict.update(feature)

			# Assign the merged dictionary back to class_features
			class_features = combined_dict

		# print("class features 1st check", class_features)
		#End of turning class_features into a dictionary for oracle


	#--------------- Spell addition options ---------------#
	# Bloodlines
		if character.c_class.lower() in ('sorcerer', 'bloodrager'):
			bonus_spells = character.data_dict['class features'].get("Talents").get(bloodline).get("bonus spells", [])
			add_bonus_spells(character, bonus_spells)
	# Domains
		if full_domain not in ([], None) and character.c_class.lower() in ("cleric"):
			for i, domain in enumerate(full_domain):
				bonus_spells = character.data_dict.get('class features', {}).get(domain.title(), {}).get("bonus spells", {})
				add_bonus_spells(character, bonus_spells)

		if full_domain not in ([], None) and character.c_class.lower() in ("druid"):
			for i, domain in enumerate(full_domain):
				bonus_spells = character.data_dict['class features'].get(domain).get("bonus spells", [])
				add_bonus_spells(character, bonus_spells)
	# Inquisitions
		# Don't get bonus spells
	# Schools
		# Schools spells are just recommended spells (not bonus spells), but we'll mnake sure wizards take them
		if full_school not in ([], None) and character.c_class.lower() in ("wizard"):
			try:
				bonus_spells_dict = character.data_dict['class features'].get(full_school).get("spells", [])
				add_bonus_spells_from_dict(character, bonus_spells_dict)
				# print("bonus_spells_dict", bonus_spells_dict)
				# print("character.spell_list_choose_from", character.spell_list_choose_from)
			except:
				print("wizard, but wizard spell list has no bonus spells")


	# ------------------- Last minute Feat swapping process -------------------#
		story_feats, flaw_feats, flavor_feats, class_feats, feats = separate_feats_func(character, feats)

	#-------------------- Start of export process --------------------#
		archetype_info = json.dumps(archetype_info, indent=4)
		export_list_non_dict = [
				character.region, character.chosen_race,
				character_full_name, character.c_class, character.c_class_2, 
				alignment,  age_number, 
				height_number, weight_number, character.dex, character.str, 
				character.con, character.int, character.wis, character.cha, 
				flaw, character.Total_HP, character.sheet_health,
				character.bab_total,
				armor_ac, shield_ac,
				armor_name, armor_spell_failure, armor_weight, armor_armor_check_penalty, armor_max_dex_bonus,
				shield_name, shield_spell_failure, shield_weight, shield_armor_check_penalty, shield_max_dex_bonus,
				# fort_saving_throw, reflex_saving_throw, wisdom_saving_throw,
				character.spell_list_choose_from,
				day_list, known_list,
				deity_name, skill_ranks,
				weapon_enhancement_chosen_list, armor_enhancement_chosen_list, 
				shield_enhancement_chosen_list,
				selected_traits, equipment_list, character.c_class_level,
			#  we don't use these in foundry, comment out if we do (all instances (but will need to fix program issue))
			#  chosen_subrace, subrace_description, 
				character.archetype1,
				hair_color, hair_type, eye_color, appearance,
				language_text, 
				feats, teamwork_feats, story_feats, flaw_feats, class_feats, flavor_feats,
				character.gold, character.platnium,
				full_domain, school, opposing_school,
				bloodline,
				background_traits, professions, mannerisms, 
				personality_traits,
				hero_points, character.chosen_gender, 
				class_ability_desc, class_ability,
				class_features, archetype_info,				
				parents, 
				older_brothers, younger_brothers, 
				older_sisters, younger_sisters,				 
				weapon_name,
				character.specialty_schools, character.counter_schools,
				character.chosen_descriptors, character.counter_descriptors,
				total_rolled_hp, mini_alignment, 
				casting_level_str_foundry, character.main_stat,

				 
				 ]
		
		string_export_list_non_dict = [
					"region", "chosen_race", "character_full_name", 
					"c_class", "c_class_2", 
					"alignment", "age_number", 
					"height_number", "weight_number", "dex", "str", 
					"con", "int", "wis", "cha", 
					"flaw", "Total_HP", "sheet_health",
					"bab_total",
					"armor_ac", "shield_ac",
					"armor_name", "armor_spell_failure", "armor_weight", "armor_armor_check_penalty", "armor_max_dex_bonus",
					"shield_name", "shield_spell_failure", "shield_weight", "shield_armor_check_penalty", "shield_max_dex_bonus",				
					# "fort_saving_throw", "reflex_saving_throw", "wisdom_saving_throw",
					"spell_list_choose_from",
					"day_list", "known_list",
					"deity_name", "skill_ranks",
					"weapon_enhancement_chosen_list", "armor_enhancement_chosen_list", 
					"shield_enhancement_chosen_list",
					"selected_traits", "equipment_list", "level",
					# We don't use subrace data in foundryVTT (comment these out if we want to (will need to fix their issues first))
					# "chosen_subrace", "subrace_description", 
					"archetype1",
					"hair_color", "hair_type", "eye_color", "appearance",
					"language_text", 
					"feats", "teamwork_feats", "story_feats", "flaw_feats", "class_feats", "flavor_feats",
					"gold", "platnium",
					"full_domain", "school", "opposing_school",
					"bloodline",
					"background_traits", "professions", "mannerisms",
					"personality_traits",
					"hero_points", "gender",
					"class_ability_desc", "class_ability",
					"class_features", "archetype_info",
					"parents",
					"older_brothers", "younger_brothers", 
					"older_sisters", "younger_sisters",	
					"weapon_name",
					"specialty_schools", "counter_schools",
					"chosen_spell_descriptor", "counter_spell_descriptor",
					"total_rolled_hp", "mini_alignment",
					"casting_level_str_foundry", "main_stat",
				]
		
		export_list_dict = [ 
				character.spell_list_choose_from, equip_descrip,
				 ] 

		string_export_list_dict = [ 
				"spell_list_choose_from_dict", "equip_descrip",
				 ] 

		character.export_list_non_dict(export_list_non_dict, string_export_list_non_dict)		
		character.export_list_dict(export_list_dict, string_export_list_dict)		

		# ----- debugging section ----- #
		# print("character.c_class_level", character.c_class_level)
		# print("character.c_class", character.c_class)
		# print("character.c_class_2", character.c_class_2)
		# # print(f'this is your character data {character.data_dict}')

		# print("character.specialty_schools", character.specialty_schools)
		# print("character.counter_schools", character.counter_schools)
		# print("character.chosen_descriptors", character.chosen_descriptors)
		# print("character.counter_descriptors", character.counter_descriptors)

		# print("character.feats", character.feats)
		# print("this is your character feat amount", character.feat_amounts)
		# print("this is your character flaws feat amount", character.flaw_feat_amount)
		# print("this is your character feat amount", character.normal_feat_amount)
		# print("this is your character teamwork_feats", character.teamwork_feats)


		# print("character.spell_list_choose_from", character.spell_list_choose_from)
		# print("chosen_feats", feats)


		# print("alignment", alignment)
		# print("deity_name", deity_name)
		# print("character.region", character.region)
		# print("flaw", flaw)
		# print("personality_traits", personality_traits)
		# print("skill_ranks", skill_ranks)
		# print("archetype_info", archetype_info)
		# print("character.c_class", character.c_class)

		# print("character.spell_list_choose_from", character.spell_list_choose_from)
		# print("character.feats", character.feats)
		# # Why are character.feats different from feats??????????? -> B/c cached dataset without prereqs allows for feats to buy class specific talents (rage powers / rogue talents / etc.)
		# print("feats", feats)
		# print("class_features", class_features)
		# print("character.chooseable", character.chooseable)
		# print("character.skipped_feats", character.skipped_feats)
		# for key in class_features["rage_powers"].keys():
		# 	print("key", key, "prereqs", class_features["rage_powers"][key])

		# print(sorted(list(class_features["rage_powers"].keys())))

		print(".")
		print(".")
		print(".")
		print(".")
		# print("character.chooseable", sorted(list(character.chooseable)))
		print("character.feats", sorted(list(feats)))
		print("story_feats", sorted(list(story_feats)))
		print("flaw_feats", sorted(list(flaw_feats)))
		print("class_feats", sorted(list(class_feats)))
		# print("character.teamwork_feats", sorted(list(teamwork_feats)))
		# print("character.processed_feats", character.processed_feats)
		# print("character.chooseable_talents", sorted(character.chooseable_talents))




		print("region", character.region)
		print("character.chosen_race", character.chosen_race)
		print("alignment", alignment)
		print("mini_alignment", mini_alignment)
		print("deity_name", deity_name)
		# print("race", character.races)

		return character.data_dict

generate_random_char()

# ----- Planned add ons  ----- #
	# Stuff to add later
		# Inherents option
		# path of war
		# Spheres of power
		# Mythic
		# Luck
		# Attack Macros???
		# Subrace???
