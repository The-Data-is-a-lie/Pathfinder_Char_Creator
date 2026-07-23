#Custom Made Imports
import os, sys
# Pin the absolute Backend dir on sys.path so `utils.*` imports resolve no matter where the process
# was launched from. This used to be followed by os.chdir(repo_root), because the data paths were
# written relative to the CWD; they are now anchored to __file__ via utils.paths.repo_path, so the
# chdir is gone -- importing this module no longer changes the working directory of the process.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
	sys.path.insert(0, _BACKEND_DIR)
# Load .env so direct CLI runs (python Backend/main_test.py) pick up OLLAMA_* like the Flask app does
# (app.py / start_py.py already call load_dotenv()). Guarded so a missing python-dotenv never breaks the CLI.
try:
	from dotenv import load_dotenv
	load_dotenv()
except Exception:
	pass
from utils.createACharacter 						import CreateNewCharacter, Load_when_needed
from utils 											import data
from utils.data 									import version
from utils.util 									import  (select_classes, region_chooser, race_chooser,  name_chooser,
										  					gender_chooser)
import random
import numpy as np   # seeded alongside `random` for reproducibility -- pandas .sample() uses numpy's RNG
import json

# Bump on every generator-logic change. Printed at startup (app.py) + in the per-generation log, and
# stamped onto each result (data_dict['generator_version']) so a running backend's freshness is verifiable
# at a glance: a restart shows the new version, and any exported actor reveals which build produced it
# (the recurring "I restarted but it's still wrong" was a stale backend serving old code).
GENERATOR_VERSION = "2026-07-15 racial-stats"


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
from utils.class_func.extra_combat_feats 			import extra_combat_feats, extra_teamwork_feats, class_bonus_feat_slots, teamwork_feat_slots, bloodline_bonus_feat_levels
from utils.class_func.favored_class 				import favored_class_calculator, favored_class_option, favored_class_option_chooser
from utils.class_func.family_func 					import randomize_siblings, randomize_parents
from utils.class_func.feats 						import (build_selector, chooseable_list, chooseable_list_stats,
                                                  			chooseable_list_class_features, feat_spell_searcher, generic_multi_chooser,
                                                            simple_list_chooser, generic_feat_chooser, bloodline_feat_chooser, teamwork_pool_size,
                                                            capitalize_feats, dedupe_feats_case_insensitive, topup_feat_chooser)
from utils.class_func.feats_to_chooseable 			import add_feats_to_chooseable
from utils.class_func.feat_tax 						import feat_tax_func, feat_spell_searcher
from utils.class_func.feat_skill_choice 			import FREE_AT_BAB1, filter_free_feats, specialize_skill_choice_feats
from utils.class_func.weapon_focus_buffs import weapon_focus_changes
from utils.class_func.buff_match					import match as match_buffs, sections as buff_sections, format_gaps
from utils.class_func.spheres 						import randomize_spheres_num, choose_spheres_attr, add_overflow_talents, MAX_EXTRA_TALENT_FEATS, mentor_sphere_summary
from utils.class_func.flag_assign 					import human_flag_assigner, druidic_flag_assigner
from utils.class_func.flaws 						import flaw_chooser
from utils.class_func.generic_func 					import generic_class_option_chooser, get_data_without_prerequisites, no_prereq_prep#, no_prereq_loop, chosen_set_append
from utils.class_func.grand_discovery 				import grand_discovery_chooser
from utils.class_func.gunslinger 					import choose_gun_func
from utils.class_func.hero_point_generator 			import hero_point_generator
from utils.class_func.hp_rolls 						import roll_hp, total_hp_calc, hit_dice_calc
from utils.class_func.item_and_price 				import item_chooser
from utils.class_func.language 						import language_chooser
from utils.class_func.level_and_bab 				import randomize_level
# from utils.class_func.luck_and_mythic 				import randomize_luck, randomize_mythic
from utils.class_func.path_of_war 					import randomize_path_of_war_num, choose_path_of_war_attr, martial_training_depth
from utils.class_func.backstory 					import generate_backstory, structured_bio
from utils.class_func.build_archetype 				import choose_build_archetype

from utils.class_func.modded_char_sheet 			import modded_char_sheet_func
# from utils.class_func.path_of_war_funcs				import select_disciplines

from utils.class_func.personality 					import randomize_personality_attr
from utils.class_func.profession_chooser 			import profession_chooser, apply_always_improving_ranks
from utils.class_func.profession_abilities 			import build_profession_ability_items
from utils.class_func.trainers 						import select_trainer_feats, CALIBER_NAMES, roll_caliber
from utils.class_func.skill_unlocks 				import choose_skill_unlock
from utils.class_func.race_func 					import apply_racial_stats
# from utils.class_func.race_func 					import (race_ability_score_changes, race_ability_split,
#                                                      		race_traits_chooser, subrace_chooser)#, full_race_data
from utils.class_func.randomize_flaw 				import randomize_flaw_amount
from utils.class_func.skill_ranks 					import skills_selector
from utils.class_func.spells 						import (extra_spells_divine, spells_known_attr,
										   					spells_known_extra_roll, spells_known_selection,
                                                   	        spells_per_day_attr, spells_per_day_from_ability_mod,
                                                            class_for_spells_attr, caster_formula,
                                                            casting_stat_for,
                                                            spell_themes, sync_legacy_spell_fields,
                                                            spell_conditionals_selection)#, alignment_spell_limits
from utils.class_func.spell_alphabetize_and_dedupe 	import spell_alphabetize_and_dedupe_func
from utils.class_func.stats 						import roll_stats, assign_stats, calc_ability_mod 
from utils.class_func.separate_feats_func 			import separate_feats_func
from utils.class_func.feat_level_assignment import assign_feats_to_levels
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

	# Path of War section (forward slashes + exact on-disk casing -- backslash literals and
	# 'martial_disciplines.json' lowercase would break on the Linux/Render deploy)
	'path_of_war_classes': Load_when_needed('Backend/json/class_data/path_of_war/path_of_war_classes.json'),
	# 'path_of_war_archetypes': Load_when_needed('Backend/json/class_data/path_of_war/path_of_war_archetypes.json'),
	'martial_disciplines': Load_when_needed('Backend/json/class_data/path_of_war/Martial_Disciplines.json'),
	'path_of_war_maneuvers_known': Load_when_needed('Backend/json/class_data/path_of_war/path_of_war_maneuvers_known.json'),
	'martial_training_progression': Load_when_needed('Backend/json/class_data/path_of_war/martial_training_progression.json'),
}

def strip_labeled_bucket(feat_list, label_list, children):
	'''Filter a feat list and its parallel label list in lockstep, dropping feats whose
	lower() is in `children` (feats now bundled onto a feat-tax primary).'''
	lbls = list(label_list) + [None] * (len(feat_list) - len(label_list))
	kept = [(f, lbl) for f, lbl in zip(feat_list, lbls) if str(f).lower() not in children]
	return [f for f, _ in kept], [lbl for _, lbl in kept if lbl is not None]

# Non random feats sometiems break at 20+
# Make sure to make a flag for adding metzofitz feats later
# Make sure to add a flag for path of war feats later
def generate_random_char(create_new_char='Y', userInput_region="Tal-Falko", userInput_race='Orc', class_choice='wizard', chosen_BAB='low', chosen_caster_level = 'random', multi_class='N', 
						 alignment_input = 'LG' , deity_flag = 'asdfasd', userInput_gender='female', truly_random_feats = "Y", inherents = "Y", modded_char_sheet = 'n', 
						 homebrew_feat_amount="Y",num_dice="8", num_sides="8", high_level=15, low_level=15, gold_num=1000000, use_backstory_api="Y", spheres_flag="N", backstory_focus=None,
						 seed=None, ):

		print(create_new_char)
		print(userInput_region)
		print(userInput_race)
		print(class_choice)
		print(chosen_BAB)
		print(chosen_caster_level)
		print(multi_class)
		print(alignment_input)
		print(deity_flag)
		print(userInput_gender)
		print(truly_random_feats)
		print(inherents)
		print(modded_char_sheet)
		print(num_dice)
		print("Type num_dice", type(num_dice))
		print(num_sides)
		print("Type num_sides", type(num_sides))
		print(high_level)
		print(low_level)
		print(gold_num)
		print(homebrew_feat_amount)

		# Reproducibility. Seed BOTH RNGs: most of the generator draws from the `random` module, but
		# spell and trait selection go through pandas .sample(), which draws from numpy's global RNG --
		# seeding only `random` leaves those two nondeterministic. The resolved seed is exported as
		# `generation_seed`, so any character that comes out wrong can be replayed exactly by passing
		# it back in. (Feat selection also needed a fix to be replayable -- see the sorted() note in
		# class_func/feats.py::choosing_feats.)
		if seed is None:
			seed = random.randrange(2 ** 31)
		seed = int(seed)
		random.seed(seed)
		np.random.seed(seed)
		print("generation seed:", seed)

		casting_level_str_foundry = 'None'

		character = CreateNewCharacter(
			character_json_config)
		character.instantiate_full_data_dict()
		character.data_dict['class features'] = {}
		character.data_dict['class feature levels'] = {}

		# Flag that allows for homebrew feats to be added
		character.homebrew_feat_amount = homebrew_feat_amount
		# Instantitae character.class_feats_amount
		character.class_feats_amount = 0
		# Instantitae teamwork_feats
		teamwork_feats = 0
		# insantiate character.deity_choice
		character.deity_choice = deity_flag

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
		select_classes(character, class_choice, chosen_BAB, chosen_caster_level, multi_class)

		#add an optional flaws rule function	
		alignment, mini_alignment = choose_alignment(character, 'alignments', alignment_input)
		alignment = alignment.title()

		if deity_flag.lower() == 'random':
			deity = randomize_deity(character, random_flag=True)
		else:
			deity = randomize_deity(character, random_flag=False, deity_choice=deity_flag)

 
		age_number = randomize_body_feature(character, 'age')
		height_number = randomize_body_feature(character, 'height')
		weight_number = randomize_body_feature(character, 'weight')			

		# We don't use subrace data in foundryVTT (comment these out if we want to (will need to fix their issues first))
		# chosen_subrace, subrace_description = subrace_chooser(character)
		# race_traits_list, race_traits_description_list = race_traits_chooser(character)
		# split_race_traits_list = race_ability_split(character, race_traits_list)

		flaw_amount = randomize_flaw_amount()
		# Mechanical flaws replace the old personality-flaw strings: same 0-4 roll, but the
		# flaws now come from json/flaws/flaw_effects.json with pf1 changes/contextNotes
		# (1st flaw minor, 2nd major, extras 80% minor / 20% major).
		flaw, flaw_effects_dict = flaw_chooser(character, flaw_amount)
		background_traits = randomize_personality_attr(character, "background_traits",1,4)
		professions = randomize_personality_attr(character, "professions",1, 3)
		mannerisms = randomize_personality_attr(character, "mannerisms",2,4)
		personality_traits = randomize_personality_attr(character, "personality_traits",3,6)
		# Flaws chosen earlier in it's own function


		# I don't know why, but these keep breaking the game (if low enough level and stats)
		if any(pick in ('rogue (unchained)', 'vigilante') for pick in character._class_picks):
			if low_level <= 1:
				low_level = 2
			if high_level <= 1:
				high_level = 2
		randomize_level(character, low_level, high_level, flaw_amount)

		#stats after level (because we roll inherents which depend on level)
		stats = roll_stats(character, num_dice, num_sides, inherents)
		# Racial modifiers go into the base scores here (before assign/mod/HP/spell
		# calcs) so they propagate everywhere; the split is exported as racial_stats.
		apply_racial_stats(character, stats)
		assign_stats(character, stats)
		calc_ability_mod(character)


		#hp calculations
		hit_dice_calc(character)
		total_rolled_hp = roll_hp(character)
		character.Total_HP = total_hp_calc(character)

		# Choosing character class for spells (per class entry) + character-wide spell themes
		class_for_spells_attr(character)
		spell_themes(character)

		# Some spellcasters get 0th level spells (all high + most mid)
		# Also 0th spells = infinite casting
		# Wizards + Clerics know all 0th level spells (wizards know all except opposing school)
		# as long as spells known list has a '0th' spell column (even if it isn't 0)
		# it won't pull any 0th spells for casters with orisons/cantrips

		#Divine Casters have all spells known (don't make this function for them)

		# Each class builds its own spellbook — a multiclass cleric/wizard gets two independent
		# spell lists, each at its own class's caster level.
		character.spellbooks = []
		for class_entry in character.classes:
			caster_formula(character, class_entry['level'], class_entry)
			spells_known_attr(character, "base_classes", "divine_casters", class_entry)
			spells_per_day_attr(character, "base_classes", class_entry)
			spells_per_day_from_ability_mod(character, "caster_mod", class_entry)
			spells_known_extra_roll(character, class_entry)
			extra_spells_divine(character, class_entry)
			spells_known_selection(character, class_entry)
			if class_entry['casting_level_string'] in ('low', 'mid', 'high'):
				character.spellbooks.append(class_entry)

		# legacy scalar fields = the primary spellbook (primary class if it casts, else first caster)
		sync_legacy_spell_fields(character)
		day_list = character.spells_per_day_list
		known_list = character.spells_known_list


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
		if any(c['name'] == 'wizard' for c in character.classes):
			full_school = wizard_school_chooser(character)
			full_opposing_school = wizard_opposing_school(character, full_school)

		archetype_info = character.archetype_data()
		# One archetype per rolled class for the Foundry module. The primary reuses the legacy pick
		# above (which also strips " (unchained)" off c_class for later data lookups), so
		# archetype_info and its class entry always agree; {} for classes with no archetypes.
		archetypes_per_class = [
			archetype_info if i == character.primary_class_index
			else character.archetype_data(entry['name'])
			for i, entry in enumerate(character.classes)]

		# generic single choices (the choosers gate themselves on any matching class entry)
		bloodline_sorc = generic_class_option_chooser(character, "sorcerer", "bloodline")
		bloodline_rager = generic_class_option_chooser(character, "bloodrager", "bloodline")

		generic_class_option_chooser(character,"cavalier", "orders")
		generic_class_option_chooser(character,"samurai", "orders")
		generic_class_option_chooser(character,"warpriest", "blessing", multiple='yes', alternate_dataset=True)
		generic_class_option_chooser(character,"inquisitor", "inquisitions", multiple='yes', alternate_dataset=True)
		# Need to add revelations to oracle

		# Make this populate like how you want it to *********
		
		# Choose Oracle mystery
		if any(c['name'] == 'oracle' for c in character.classes):
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

		# One Craft specialization per character, displayed as "Craft: <type>" on the sheet.
		# Chosen before professions so a profession can be themed around it.
		character.craft_chosen = random.choice(data.crafts)
		# Professions sub-system (ranks 5 + level + 10/Multi-Talented feat). Returns the legacy list of
		# profession names; rich data + the profession feats are recorded on the character.
		# MUST run before skills_selector: ordinary skill ranks may only be spent in a Profession when
		# the character has the 'Always Improving' profession feat, and that gate reads
		# character.profession_feats.
		professions = profession_chooser(character, "professions", truly_random_feats)
		skill_ranks = skills_selector(character, 'skills', skill_rank_level)
		# ... and the ranks that DID go to Profession are folded back onto the professions themselves.
		apply_always_improving_ranks(character, skill_ranks)
		# Every character gets exactly one skill unlock, drawn from a skill they have ranks in.
		skill_unlock = choose_skill_unlock(character, skill_ranks)

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

		weapon_enhancement_chosen_list, weapon_enhancement_bonus = enhancement_chooser(character, character.weapon_qualities,weapon_enhancement, weapon_type_flag)
		armor_enhancement_chosen_list, armor_enhancement_bonus = enhancement_chooser(character, character.armor_qualities,armor_enhancement, 'Armor')
		shield_enhancement_chosen_list, shield_enhancement_bonus = enhancement_chooser(character, character.armor_qualities,shield_enhancement, 'Shield', character.shield_flag)


		selected_traits = trait_selector(character, 8)
		# pre export data manip start
		hero_points = hero_point_generator()


		hair_color = randomize_apperance_attr(character, "hair_colors")
		hair_type = randomize_apperance_attr(character, "hair_types")
		eye_color = randomize_apperance_attr(character, "eye_colors")
		appearance = randomize_apperance_attr(character, "appearance")
		language_text = language_chooser(character, skill_ranks)
		character_full_name = f_name + ' ' + l_name
		# deity.json "Name" is a LIST of aliases since the homebrew-deities rework (091da54) -- export
		# one string: pf1's details.deity is a StringField, and an array crashes the actor's data
		# preparation on import (sheet dies reading the underived encumbrance).
		deity_name = deity.get("Name", "") if isinstance(deity, dict) else deity
		if isinstance(deity_name, list):
			deity_name = deity_name[0] if deity_name else ""
		print("deity_name", deity_name)
		print("deity", deity)
		# skill_ranks = json.dumps(skill_ranks)  # disabled: ship the dict so Flask serializes it as a JSON object and the Foundry module parses it		

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


		# All spending is done by here. Every spender (item_chooser, enhancement_calculator) now checks
		# affordability before deducting, so this should hold by construction -- the guard exists so a
		# future spender can't quietly reintroduce negative purses (and negative platinum with them).
		if not isinstance(character.gold, int) or character.gold < 0:
			print(f"gold: WARNING ended at {character.gold!r}; clamping to 0")
			character.gold = max(0, int(character.gold or 0))
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
		# Campaign feat-tax rule (homebrew_rules.md §4): Combat Expertise / Power Attack / Deadly Aim /
		# Piranha Strike are FREE for anyone with BAB >= 1, so they're never spent as a chosen feat.
		# Seeding them into chooseable BEFORE any feat selection makes every chooser skip them, while
		# feats that list them as a prerequisite still qualify (no_prereq_loop treats chooseable as owned).
		if getattr(character, 'bab_total', 0) >= 1:
			add_feats_to_chooseable(character, FREE_AT_BAB1)
		# Bloodline bonus feats (Sorcerer & Bloodrager): drawn from this bloodline's own list and
		# labeled by granting class + level (e.g. "Sorcerer 7", "Bloodrager 6"); levels extend past 20.
		# Non-bloodline classes -> empty schedule -> empty lists, so the export stays well-formed.
		_bl_levels = bloodline_bonus_feat_levels(character.c_class, character.c_class_level)
		bloodline_feats = bloodline_feat_chooser(character, character.c_class, character.bloodline, len(_bl_levels))
		bloodline_feats = filter_free_feats(bloodline_feats)  # safety net (bonus lists may bypass chooseable)
		bloodline_feat_labels = [f"{character.c_class.title()} {lvl}" for lvl in _bl_levels][:len(bloodline_feats)]
		# If the bloodline list is too short to fill every granted slot (e.g. a high-level
		# Bloodrager whose ~7-feat list runs out), reallocate the unfilled slots to normal feats
		# so the total feat count is preserved. No-op when the list covers every slot.
		character.feat_amounts += max(len(_bl_levels) - len(bloodline_feats), 0)
		#class specific feats choosers (capture results; they are merged into character.feats after
		# the normal-feat selection below, which would otherwise reassign over them)
		ranger_style_feats = ranger_feats_chooser(character) or []
		monk_bonus_feats = monk_feats_chooser(character) or []
		# Reallocate monk/ranger bonus-feat slots their lists couldn't fill to normal feats (monk's
		# total is preserved; ranger now actually gains its combat-style feats). No-op otherwise.
		character.feat_amounts += getattr(character, 'ranger_feat_surplus', 0) + getattr(character, 'monk_feat_surplus', 0)
		# Register the class-granted picks (bloodline / ranger style / monk bonus) in
		# character.chooseable BEFORE the normal-feat selection: no_prereq_loop skips chooseable
		# members, so the general pool can no longer re-pick the same feat (duplicate Weapon
		# Focus etc.), and the feat-tax engine correctly sees them as owned.
		add_feats_to_chooseable(character, bloodline_feats, ranger_style_feats, monk_bonus_feats)
		# Determine extra teamwork feats
		extra_teamwork_feats(character)
		# determine extra combat feats
		extra_combat_feats(character)

	# ------------------- Path of War section -------------------#
		# Initiator classes (stalker/warlord/...) draw disciplines + maneuver counts from their
		# own class tables; everyone else may roll "martial paths" (house rule: BAB L 0-1,
		# M/H 0-2, +1 to both bounds at level 20+) accessed via the Martial Training feat chain
		# taken as deep as bab_total allows (I/III/V paid; II/IV/VI free via feat tax).
		# ----- PoW + Spheres selection guarantee (house rule) -----
		# Roll both systems' COUNTS uncapped, then guarantee delivery with feat-budget PRIORITY over
		# normal feats. 75% "lean": realize ceil(half) of the desired homebrew feats. 25%
		# "trainer-backed": realize >= half, with 2 dedicated trainers funding the rest off-budget
		# (their caliber rolls) and any surplus capacity becoming bonus sphere talents.
		randomize_path_of_war_num(character)
		character.spheres_flag = spheres_flag
		randomize_spheres_num(character)
		_is_initiator = any(c['name'] in data.path_of_war_class for c in character.classes)
		_sc = int(getattr(character, 'sphere_count', 0) or 0)
		desired_sphere = (_sc + random.randint(0, MAX_EXTRA_TALENT_FEATS)) if _sc > 0 else 0
		_mt_depth = martial_training_depth(character)
		_paid_per_chain = (_mt_depth // 2) if _mt_depth else 0
		_paths = int(getattr(character, 'path_of_war_paths', 0) or 0)
		desired_pow = (_paths * _paid_per_chain) if (not _is_initiator and _mt_depth and _paths) else 0
		if _is_initiator:
			pow_data = choose_path_of_war_attr(character)        # maneuvers/stances free from the class
			desired_style = len(pow_data.get('style_feats', []))
		else:
			pow_data = None
			desired_style = 0
		selected_amount = desired_pow + desired_style + desired_sphere
		dedicated_trainer_calibers, _overflow_n, _priority_reserve, _mentor_talents_n = [], 0, 0, 0
		realize_pow, realize_style, realize_sphere = desired_pow, desired_style, desired_sphere
		if selected_amount > 0:
			_half = (selected_amount + 1) // 2          # ceil(selected_amount / 2)
			if random.random() < 0.25:
				# ONE dedicated mentor of caliber 1-4 (8/45/45/2): it teaches `caliber` feats =
				# 2*caliber sphere talents off-budget (caps at the flat-8). No overflow -> the character's
				# total talents never bloat past the flat-8; the mentor just pays for 2*caliber of them.
				dedicated_trainer_calibers = [roll_caliber()]
				_capacity = dedicated_trainer_calibers[0]
				_rest = selected_amount - _half
				realize_total = _half + min(_capacity, _rest)
				_overflow_n = 0
				_mentor_talents_n = 2 * dedicated_trainer_calibers[0]
			else:
				realize_total = _half
			_priority_reserve = min(_half, realize_total)   # the budget-funded portion (rest is off-budget)
			if realize_total < selected_amount:
				_dpow = desired_pow + desired_style
				_rpow = max(0, min(round(realize_total * _dpow / selected_amount), _dpow))
				realize_sphere = max(0, min(realize_total - _rpow, desired_sphere))
				# Don't let the proportional split zero out a system that WAS selected: keep each
				# present system its minimum unit (1 sphere feat / one whole PoW chain or style feat)
				# when the realized budget can still cover it.
				if desired_sphere > 0 and realize_sphere == 0 and realize_total >= 1:
					realize_sphere = 1
				_rpow = max(0, min(realize_total - realize_sphere, _dpow))
				_pow_min = _paid_per_chain if (not _is_initiator and desired_pow > 0) else (1 if (_is_initiator and desired_style > 0) else 0)
				if _pow_min and _rpow < _pow_min and (realize_total - realize_sphere) >= _pow_min:
					_rpow = _pow_min
					realize_sphere = max(0, min(realize_total - _rpow, desired_sphere))
				realize_style, realize_pow = (_rpow, 0) if _is_initiator else (0, _rpow)
		if not _is_initiator:
			pow_data = choose_path_of_war_attr(
				character, max_chains=((realize_pow // _paid_per_chain) if _paid_per_chain else 0))
		martial_disciplines     = pow_data['martial_disciplines']
		initiator_level         = pow_data['initiator_level']
		maneuvers_known_list    = pow_data['maneuvers_known_list']
		maneuvers_readied_list  = pow_data['maneuvers_readied_list']
		maneuvers_choose_from   = pow_data['maneuvers_choose_from']
		maneuvers_readied_names = pow_data['maneuvers_readied_names']
		stances_chosen          = pow_data['stances_chosen']
		mt_feats                = pow_data['mt_feats']
		mt_feat_tax             = pow_data['mt_feat_tax']
		initiation_stat         = pow_data['initiation_stat']
		maneuvers_desc_dict     = pow_data['maneuvers_desc_dict']
		style_feats             = pow_data['style_feats']
		style_feat_tax          = pow_data['style_feat_tax']
		homebrew_feat_desc_dict = pow_data['homebrew_feat_desc_dict']
		# Cap initiator style chains to the realized amount decided by the guarantee block above
		# (PoW maneuvers are class-free; only the feat-funded style bases are scaled). Non-initiators
		# have no style feats. The feat-budget reservation now happens after the Spheres section.
		style_feats = style_feats[:realize_style]
		style_feat_tax = {k: v for k, v in style_feat_tax.items() if k in style_feats}

	# ------------------- Spheres (Power / Might) section -------------------#
		# Build the spheres: flat-8 talents + a feat slot per BUDGET-PAID talent (Extra Talent feats,
		# 2 talents each, HR1). trainer_backed (25% branch) -> only ~half the talents are budget-paid
		# (the rest ride the Spheres Mentor trainers below); lean chars pay for all their talents.
		sphere_data          = choose_spheres_attr(character, trainer_backed=bool(dedicated_trainer_calibers), mentor_talents=_mentor_talents_n)
		magic_talent_items   = sphere_data['magic_talent_items']
		combat_talent_items  = sphere_data['combat_talent_items']
		sphere_feats         = sphere_data['sphere_feats']
		sphere_feat_tax      = sphere_data['sphere_feat_tax']
		sphere_mana_pool     = sphere_data['sphere_mana_pool']
		spheres_chosen       = sphere_data['spheres_chosen']
		sphere_counts        = sphere_data['sphere_counts']
		casting_tradition    = sphere_data['casting_tradition']
		sphere_drawbacks     = sphere_data['sphere_drawbacks']
		sphere_boons         = sphere_data['sphere_boons']
		sphere_traits        = sphere_data['sphere_traits']
		homebrew_feat_desc_dict.update(sphere_data['homebrew_feat_desc_dict'])
		# 25% "trainer-backed" branch: surplus trainer capacity -> bonus sphere talents, and up to 2
		# dedicated mentors (rendered in the Trainers block). Only the Spheres Mentor NAMES genuinely
		# off-budget homebrew it funded (talents beyond the character's own budget); Path of War feats are
		# real feats on the sheet and always budget-paid, so they get no mentor (it would only re-list
		# feats already bought with the normal/class feat budget).
		dedicated_trainer_specs = []
		if dedicated_trainer_calibers:
			_overflow_talent_items = []
			if _overflow_n > 0 and sphere_data.get('_chosen'):
				_ov_magic, _ov_combat = add_overflow_talents(
					character, sphere_data['_chosen'], sphere_data['_counts'], _overflow_n)
				magic_talent_items = magic_talent_items + _ov_magic
				combat_talent_items = combat_talent_items + _ov_combat
				_overflow_talent_items = _ov_magic + _ov_combat
			_mentors = []
			# No "Path of War Mentor": a non-initiator's Martial Training feats and an initiator's style
			# feats MUST be real feats on the sheet (they grant the maneuvers), so they're always
			# budget-paid and appear in the normal/class Feats list. A PoW mentor would only re-list those
			# already-bought feats -- duplicate, misleading "funding" -- so PoW gets no mentor. (Unlike
			# Spheres, whose talents can be granted off-budget; see the Spheres Mentor just below.)
			# Off-budget talents the mentor funded (the non-budget-paid flat-8 portion = 2*caliber) -> HR1
			# Extra-Talent feats + the talent names (user's requested format). Only emit a Spheres Mentor
			# when it actually funded something off-budget; otherwise there is nothing for it to teach.
			_mentor_talents = list(sphere_data.get('mentor_funded_talents', [])) + _overflow_talent_items
			if _mentor_talents:
				_mentors.append(("Spheres Mentor", mentor_sphere_summary(spheres_chosen, _mentor_talents)))
			# Never pad to a fixed count and never add a content-free fallback mentor: a dedicated trainer
			# that funded nothing would render as a blank "(Continued Study)" / generic slot. Emit only the
			# mentors that have real off-budget content (0 or 1 here now that PoW gets no mentor).
			dedicated_trainer_specs = list(_mentors)
		# Priority funding (reserve EXACTLY the homebrew feats that get appended into the normal feat
		# list, so each one REPLACES a normal feat -- the "consume feat budget" house rule -- and the
		# track lands at precisely normal_feat_amount). Those appended feats are: paid Martial Training
		# picks (mt_feats) + initiator style-chain bases (style_feats), both extended into `feats` just
		# below, and the budget-paid sphere Extra-Talent / magic bonus feats (sphere_feats) appended
		# after the feat-tax pass. The previous formula reserved a proportional roll-estimate
		# (_priority_reserve + max(0, sphere_feat_budget_count - realize_sphere)) that drifted off this
		# true count: over-reserving silently dropped the top "(Feat N)" slots (the "missing feats"
		# bug), under-reserving spilled feats past the character's top level. trainer-backed/mentor
		# funding is already off-budget (those feats are not in these three lists), so it needs no term.
		_prof_feat_n = len(getattr(character, 'profession_feats', []) or [])
		character.feat_amounts = max(0, character.feat_amounts - len(mt_feats) - len(style_feats) - len(sphere_feats) - _prof_feat_n)
		# Profession feats (True Calling / Multi Talented / Always Improving) are appended into the feat
		# list AFTER the feat-count guarantee, so -- unlike the homebrew feats above -- they can't be
		# trimmed to fit. Reserve their slots by ALSO lowering the guarantee target (normal_feat_amount):
		# each profession feat then REPLACES a normal feat (the "feat cost" house rule), or, when the
		# budget is too small, takes over the track and clamps the normal feats down to 0.
		character.normal_feat_amount = max(0, character.normal_feat_amount - _prof_feat_n)

		# Cached dataset without prerequisites -> allows them to take rage powers / rogue talents / etc. without normal feats ()
		print("cached dataset without prereqs allows for feats to buy class specific talents ")
		print("character.cached_dataset_without_prerequisites", sorted(character.cached_dataset_without_prerequisites))

		# Feat Selector
		casting_level_str = character.class_data[character.c_class]['casting level'].lower()
		# If a class is granted more teamwork-feat slots than the (filtered) teamwork pool can
		# fill, reallocate the unfilled slots to normal feats. Normally a no-op (~53 teamwork
		# feats vs <=13 requested); fires only for filtered caster builds. Computed here because
		# teamwork feats themselves are chosen after the normal-feat selection below.
		if character.teamwork_feats > 0:
			character.feat_amounts += max(character.teamwork_feats - teamwork_pool_size(character, casting_level_str), 0)
		# print("character.chooseable", character.chooseable)
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

		# Merge the class-specific bonus feats selected above (monk bonus feats / ranger combat-style
		# feats) into the feat list. The truly-random branch reassigns character.feats, so we add them
		# here for BOTH paths so they survive (single merge point, replacing the choosers' old extend).
		# capitalize_feats normalizes names so they match Foundry's compendium lookup (as bloodline feats do).
		character.feats.extend(capitalize_feats(character, list(ranger_style_feats)))
		character.feats.extend(capitalize_feats(character, list(monk_bonus_feats)))
		# Belt-and-braces: same feat arriving from two sources with different casing would
		# otherwise survive to the sheet as a duplicate entry.
		character.feats = dedupe_feats_case_insensitive(character.feats)

		# Shared shortfall top-up (both feat paths): the type/caster-filtered pools can run dry
		# before the budget is met (and the dedupe above can drop a cross-source duplicate).
		# Target = the requested budget plus the class-granted ranger/monk merges, which sit on
		# top of character.feat_amounts (only their unfilled surplus was folded into it).
		_expected_feat_total = character.feat_amounts + len(ranger_style_feats) + len(monk_bonus_feats)
		if len(character.feats) < _expected_feat_total:
			character.feats.extend(topup_feat_chooser(character, casting_level_str, _expected_feat_total - len(character.feats)))

		# Free combat feats (homebrew §4) are seeded into chooseable above so no chooser picks them;
		# this is a belt-and-braces filter for class bonus-feat lists (ranger/monk) merged in that may
		# have bypassed the pool.
		character.feats = filter_free_feats(character.feats)
		# Skill-choosing feats (Skill Focus / Prodigy) -> point them at the character's professions
		# (highest rank first); their numeric bonus is recorded on the chosen profession.
		specialize_skill_choice_feats(character, character.feats, skill_ranks)

		# Teamwork feats selector
		if character.teamwork_feats > 0:
			teamwork_feats = generic_feat_chooser(character, character.c_class, casting_level_str, 'Null', info_column = 'description', override=True, special_type="teamwork", feat_amount = character.teamwork_feats)

		# Label teamwork feats with their granting class + level (e.g. "Inquisitor 3"), parallel to
		# teamwork_feats. Slots span every rolled class, same source as the count.
		teamwork_feat_labels = []
		if isinstance(teamwork_feats, list):
			teamwork_feat_labels = [f"{d} {lvl}" for d, lvl in teamwork_feat_slots(character)][:len(teamwork_feats)]

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
		# Level at which each class choice was picked (bucket -> choice -> level), for the sheet.
		class_feature_levels = character.data_dict.get('class feature levels', {})
		# Which class granted each bucket (bucket -> class name), for per-class feature dividers.
		class_feature_owners = character.data_dict.get('class feature owners', {})

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
		# NOTE: the homebrew Trainers / Professions / Skill Unlock entries are injected into
		# class_features further down (inject_homebrew_class_features), after the feat section has
		# computed the trainer feats + tax chains.


	#--------------- Spell addition options ---------------#
		# each addition targets the granting CLASS's own spellbook (multiclass-aware); for a
		# single-class character that book is the legacy scalar's object, so behavior is unchanged
		def _book_for(*names):
			return next((c for c in character.classes
						 if c['name'] in names and c.get('spell_list_choose_from')), None)
	# Bloodlines
		_bloodline_book = _book_for('sorcerer', 'bloodrager')
		if _bloodline_book is not None and bloodline != "N/A":
			bonus_spells = character.data_dict['class features'].get("Talents", {}).get(bloodline, {}).get("bonus spells", [])
			add_bonus_spells(character, bonus_spells, _bloodline_book['spell_list_choose_from'])
	# Domains
		_cleric_book = _book_for('cleric')
		if full_domain not in ([], None) and _cleric_book is not None:
			for i, domain in enumerate(full_domain):
				bonus_spells = character.data_dict.get('class features', {}).get(domain.title(), {}).get("bonus spells", {})
				add_bonus_spells(character, bonus_spells, _cleric_book['spell_list_choose_from'])

		_druid_book = _book_for('druid')
		if full_domain not in ([], None) and _druid_book is not None:
			for i, domain in enumerate(full_domain):
				bonus_spells = character.data_dict['class features'].get(domain, {}).get("bonus spells", [])
				add_bonus_spells(character, bonus_spells, _druid_book['spell_list_choose_from'])
	# Inquisitions
		# Don't get bonus spells
	# Schools
		# Schools spells are just recommended spells (not bonus spells), but we'll mnake sure wizards take them
		_wizard_book = _book_for('wizard')
		if full_school not in ([], None) and _wizard_book is not None:
			try:
				bonus_spells_dict = character.data_dict['class features'].get(full_school).get("spells", [])
				add_bonus_spells_from_dict(character, bonus_spells_dict, _wizard_book['spell_list_choose_from'])
				# print("bonus_spells_dict", bonus_spells_dict)
				# print("character.spell_list_choose_from", character.spell_list_choose_from)
			except:
				print("wizard, but wizard spell list has no bonus spells")


	# ------------------- Last minute Feat swapping process -------------------#
		story_feats, flaw_feats, flavor_feats, class_feats, feats = separate_feats_func(character, feats)
		# Paid Martial Training picks and style-chain bases join the normal bucket (their slots
		# were reserved out of the ask before the chooser ran); the feat-tax passes below bundle
		# the free partners/followers. Style children register as owned so nothing re-picks them.
		feats.extend(mt_feats)
		feats.extend(style_feats)
		# NOTE: sphere_feats are appended AFTER the feat-tax pass (below), not here -- they share a base
		# name ("Extra Combat Talent") that feat_tax_func would wrongly chain/strip together.
		add_feats_to_chooseable(character, story_feats, flaw_feats, flavor_feats, class_feats, feats)
		add_feats_to_chooseable(character, sphere_feats)
		add_feats_to_chooseable(character, [c for ch in style_feat_tax.values() for c in ch])

		# ------------------- Trainer & profession bonus feats (homebrew, additive) -------------------#
		# Trainers teach feats grouped under "(Trainer N)" tags; profession feats are named homebrew
		# feats (True Calling / Multi Talented / Always Improving). Both sit ON TOP of the normal
		# budget (like bloodline/teamwork) and are registered as owned so nothing re-picks them. Chosen
		# AFTER the normal feats are in chooseable, so trainer picks never duplicate the main list.
		trainer_feats, trainer_feat_labels, trainer_calibers = select_trainer_feats(character, casting_level_str)
		add_feats_to_chooseable(character, trainer_feats)
		profession_feats = list(getattr(character, 'profession_feats', []) or [])
		profession_feat_desc = dict(getattr(character, 'profession_feat_desc', {}) or {})
		profession_ranks = list(getattr(character, 'profession_data', []) or [])
		profession_pool = getattr(character, 'profession_pool', 0)
		add_feats_to_chooseable(character, profession_feats)

		# Label each class bonus feat with its granting class + level (e.g. "Fighter 1"), parallel to
		# class_feats. Slots span EVERY rolled class (same source as the class_feats count), so a
		# multiclass gunslinger dip labels as "(Gunslinger 4)" instead of the sheet's default counter.
		_class_feat_slots = class_bonus_feat_slots(character)
		_class_feat_levels = [lvl for _, lvl in _class_feat_slots]
		class_feat_labels = [f"{d} {lvl}" for d, lvl in _class_feat_slots][:len(class_feats)]
		# Per-bucket feat-row budget: what the sheet SHOULD show. Captured pre-tax-strip; normal
		# absorbs the human bonus, reallocated surpluses, and the ranger/monk merges.
		feat_budget = {
			"story": character.story_feat_amount,
			"flaw": character.flaw_feat_amount,
			"flavor": character.flavor_feat_amount,
			"class": character.class_feats_amount,
			"normal": character.feat_amounts - character.story_feat_amount - character.flaw_feat_amount
				- character.flavor_feat_amount - character.class_feats_amount
				+ len(ranger_style_feats) + len(monk_bonus_feats) + len(mt_feats) + len(style_feats),
			"teamwork": character.teamwork_feats,
			"bloodline": len(bloodline_feats),
			"trainer": len(trainer_feats),
			"profession": len(profession_feats),
		}
		# add all feats to character.chooseable (for feat taxing purposes)


		# Feat tax portion — pass per-feat acquisition levels so each progression chain releases
		# one free feat every two levels since the primary was gained (feat-tax rule e).
		# Normal feats land at L1,3,5,…; story feats at L1,5,10,15,…; flaw/flavor at creation (L1);
		# class bonus feats at their granting levels (_class_feat_levels, e.g. Fighter 1/2/4).
		_story_levels  = ([1] + [5 * k for k in range(1, len(story_feats) + 1)])[:len(story_feats)]
		_normal_levels = [2 * i + 1 for i in range(len(feats))]
		# One shared granted-set across all five calls: overlapping chains (e.g. riptide attack
		# under both Improved Drag and Improved Trip) bundle a child onto exactly one primary;
		# call order below decides which primary wins it.
		_tax_already_granted = set()
		story_feat_tax_dict  = feat_tax_func(character, story_feats,  feat_levels=_story_levels, already_granted=_tax_already_granted)
		flaw_feat_tax_dict   = feat_tax_func(character, flaw_feats,   feat_levels=[1] * len(flaw_feats), already_granted=_tax_already_granted)
		flavor_feat_tax_dict = feat_tax_func(character, flavor_feats, feat_levels=[1] * len(flavor_feats), already_granted=_tax_already_granted)
		class_feat_tax_dict  = feat_tax_func(character, class_feats,  feat_levels=_class_feat_levels[:len(class_feats)], already_granted=_tax_already_granted)
		feats_feat_tax_dict  = feat_tax_func(character, feats,        feat_levels=_normal_levels, already_granted=_tax_already_granted)
		# Trainer feats are feat-taxed too (a trainer who teaches a base feat also imparts its chain),
		# treated as learned early in the career ([1]*) like flaw/flavor feats.
		trainer_feat_tax_dict = feat_tax_func(character, trainer_feats, feat_levels=[1] * len(trainer_feats), already_granted=_tax_already_granted)
		# Profession feats (True Calling / Multi Talented / Always Improving) are named homebrew feats
		# (not in feats.csv). They are NOT attributed to a trainer and are never feat-taxed: each renders
		# as its own ordinary feat in the general feat track and costs a feat -- see the append AFTER the
		# feat-count guarantee below (the slot cost was reserved out of feat_amounts / normal_feat_amount
		# above).
		# Dedicated PoW/Spheres mentors (25% "trainer-backed" branch): up to 2 extra "(Trainer N)"
		# slots whose off-budget caliber rolls funded the homebrew training (the feats/talents/maneuvers
		# render in their own sections; these entries are the funding source + flavor). Descriptions
		# resolve from homebrew_feat_desc_dict.
		_next_trainer_n = len(trainer_calibers) + 1
		for _mentor_name, _mentor_desc in dedicated_trainer_specs:
			trainer_feats.append(_mentor_name)
			trainer_feat_labels.append(f"(Trainer {_next_trainer_n})")
			_next_trainer_n += 1
			trainer_feat_tax_dict.setdefault(_mentor_name, [])
			homebrew_feat_desc_dict[_mentor_name] = _mentor_desc
		# Martial Training chains are taken once PER DISCIPLINE and discipline-labeled (e.g.
		# "Martial Training I (Broken Blade)"), so they aren't in data/feats.csv and feat_tax_func
		# can't resolve them. Merge the hand-built bundle directly (paid I/III/V -> free II/IV/VI
		# per chain) and register the free partners in the shared granted-set, mirroring the
		# style-chain handling below.
		for _mt_children in mt_feat_tax.values():
			_tax_already_granted.update(str(c).lower() for c in _mt_children)
		feats_feat_tax_dict.update(mt_feat_tax)
		# Style-chain followers are ALWAYS granted in full ("feat tax all the way through").
		# They are Metzofitz homebrew absent from data/feats.csv, so feat_tax_func can't see
		# them -- merge the hand-built bundle directly; registering the children in the shared
		# granted-set keeps the strip/backfill/no-duplicate invariants intact.
		for _style_children in style_feat_tax.values():
			_tax_already_granted.update(str(c).lower() for c in _style_children)
		feats_feat_tax_dict.update(style_feat_tax)
		# Spheres Extra-Talent feats (HR1): one slot grants a free duplicate ("Extra Talent > Extra
		# Talent"), bundling 2 talents. Hand-built (homebrew, not in feats.csv) -> merge like style chains.
		for _sphere_children in sphere_feat_tax.values():
			_tax_already_granted.update(str(c).lower() for c in _sphere_children)
		feats_feat_tax_dict.update(sphere_feat_tax)

		# Strip feats now bundled as a tax-child onto a primary so they don't ALSO render as their
		# own standalone entry (children are granted cross-group via character.chooseable).
		_taxed_children = {
			c.lower()
			for d in (story_feat_tax_dict, flaw_feat_tax_dict, flavor_feat_tax_dict,
					  class_feat_tax_dict, feats_feat_tax_dict)
			for children in d.values() for c in children
		}
		if _taxed_children:
			story_feats  = [f for f in story_feats  if f.lower() not in _taxed_children]
			flaw_feats   = [f for f in flaw_feats   if f.lower() not in _taxed_children]
			flavor_feats = [f for f in flavor_feats if f.lower() not in _taxed_children]
			feats        = [f for f in feats        if f.lower() not in _taxed_children]
			# class_feats carries a parallel label list -> filter in lockstep
			class_feats, class_feat_labels = strip_labeled_bucket(class_feats, class_feat_labels, _taxed_children)
			# teamwork / bloodline lists are exported separately -> strip bundled children there
			# too (labels in lockstep), so a tax child never doubles as its own standalone entry.
			if isinstance(teamwork_feats, list) and teamwork_feats:
				teamwork_feats, teamwork_feat_labels = strip_labeled_bucket(teamwork_feats, teamwork_feat_labels, _taxed_children)
			if isinstance(bloodline_feats, list) and bloodline_feats:
				bloodline_feats, bloodline_feat_labels = strip_labeled_bucket(bloodline_feats, bloodline_feat_labels, _taxed_children)

		# Backfill: tax children are FREE under the house rule, so a slot freed by the strip (its
		# feat now renders bundled on its primary) is refilled with a fresh pick. Draws are sized
		# by budget distance rather than strip counts, so they also heal any residual selection
		# shortfall. Normal + class buckets only; other buckets stay visible in the budget log.
		# Granted children are NOT in character.chooseable -- register them first, or the draw
		# below could re-pick one (instant standalone+bundled duplicate).
		add_feats_to_chooseable(character, sorted(_tax_already_granted))
		need_class  = max(0, feat_budget["class"]  - len(class_feats))
		need_normal = max(0, feat_budget["normal"] - len(feats))
		if need_class + need_normal > 0:
			replacements = topup_feat_chooser(character, casting_level_str, need_class + need_normal)
			add_feats_to_chooseable(character, replacements)
			class_repl, normal_repl = replacements[:need_class], replacements[need_class:]
			class_feats.extend(class_repl)
			feats.extend(normal_repl)
			class_feat_labels = [f"{d} {lvl}" for d, lvl in _class_feat_slots][:len(class_feats)]
			# One feat-tax pass over the replacements only (same shared granted-set, so overlapping
			# chains still bundle a child exactly once); positional levels match the convention above.
			_repl_class_levels = [_class_feat_levels[i] if i < len(_class_feat_levels) else character.c_class_level
								  for i in range(len(class_feats) - len(class_repl), len(class_feats))]
			_repl_normal_levels = [2 * i + 1 for i in range(len(feats) - len(normal_repl), len(feats))]
			class_feat_tax_dict.update(feat_tax_func(character, class_repl, feat_levels=_repl_class_levels, already_granted=_tax_already_granted))
			feats_feat_tax_dict.update(feat_tax_func(character, normal_repl, feat_levels=_repl_normal_levels, already_granted=_tax_already_granted))
			# Second (terminal) strip round: a replacement can itself be a tax primary whose chain
			# bundles an EXISTING standalone feat. Strip those and draw once more WITHOUT another
			# tax pass (terminal draws never tax -> guaranteed convergence).
			_children_2 = {c for d in (class_feat_tax_dict, feats_feat_tax_dict)
						   for ch in d.values() for c in ch} - _taxed_children
			if _children_2:
				story_feats  = [f for f in story_feats  if f.lower() not in _children_2]
				flaw_feats   = [f for f in flaw_feats   if f.lower() not in _children_2]
				flavor_feats = [f for f in flavor_feats if f.lower() not in _children_2]
				feats        = [f for f in feats        if f.lower() not in _children_2]
				class_feats, class_feat_labels = strip_labeled_bucket(class_feats, class_feat_labels, _children_2)
				if isinstance(teamwork_feats, list) and teamwork_feats:
					teamwork_feats, teamwork_feat_labels = strip_labeled_bucket(teamwork_feats, teamwork_feat_labels, _children_2)
				if isinstance(bloodline_feats, list) and bloodline_feats:
					bloodline_feats, bloodline_feat_labels = strip_labeled_bucket(bloodline_feats, bloodline_feat_labels, _children_2)
				add_feats_to_chooseable(character, sorted(_children_2))
				need2_class  = max(0, feat_budget["class"]  - len(class_feats))
				need2_normal = max(0, feat_budget["normal"] - len(feats))
				if need2_class + need2_normal > 0:
					final_repl = topup_feat_chooser(character, casting_level_str, need2_class + need2_normal)
					add_feats_to_chooseable(character, final_repl)
					class_feats.extend(final_repl[:need2_class])
					feats.extend(final_repl[need2_class:])
					class_feat_labels = [f"{d} {lvl}" for d, lvl in _class_feat_slots][:len(class_feats)]

		# Reorder the surviving normal + class-bonus feats (one combined pool) onto their level slots so
		# each lands at a level whose prerequisites are actually met: prereq feats placed at earlier (lower)
		# levels, and BAB / class-level gates respected (e.g. Greater Feint never before Improved Feint nor
		# before its +6 BAB level). Done AFTER the tax-child strip because removing children reindexes the
		# positional normal-feat levels. class_feat_labels are rebuilt in lockstep. Falls back (except) to
		# the post-strip positional order if anything goes wrong, so a generation never crashes here.
		try:
			_post_class_slots = _class_feat_slots[:len(class_feats)]
			feats, class_feats, _normal_levels, _post_class_levels = assign_feats_to_levels(
				character, feats, class_feats,
				[2 * i + 1 for i in range(len(feats))], [lvl for _, lvl in _post_class_slots])
			# the returned class levels are the input multiset re-sorted ascending, so a stable
			# sort of the slot pairs by level re-pairs each level with its granting class
			_post_class_slots = sorted(_post_class_slots, key=lambda s: s[1])
			class_feat_labels = [f"{d} {lvl}" for d, lvl in _post_class_slots][:len(class_feats)]
		except Exception:
			pass

		# Story / flaw / flavor buckets are thinned by the same tax-child strip above but were never
		# refilled (only class/normal were), so a story feat that chained into another feat's tax left a
		# hole and dropped the top "(Story Feat N)" slot (e.g. the level-20 story feat). Top them back up
		# to their budgeted counts -- terminal draw, no further tax (convergence); fresh picks render
		# standalone, and the sheet labels these buckets positionally so restoring the COUNT brings the
		# high slots back.
		for _sb_list, _sb_key in ((story_feats, "story"), (flaw_feats, "flaw"), (flavor_feats, "flavor")):
			_sb_need = max(0, feat_budget[_sb_key] - len(_sb_list))
			if _sb_need:
				_sb_fill = topup_feat_chooser(character, casting_level_str, _sb_need)
				add_feats_to_chooseable(character, _sb_fill)
				_sb_list.extend(_sb_fill)

		# Row-count audit: actual/budget per bucket. Normal, class, story, flaw, and flavor are all
		# backfilled, so a deficit there means a regression; other buckets may legally run under (tax-bundled).
		print(f"feat rows -> normal {len(feats)}/{feat_budget['normal']}, story {len(story_feats)}/{feat_budget['story']}, "
			f"flaw {len(flaw_feats)}/{feat_budget['flaw']}, flavor {len(flavor_feats)}/{feat_budget['flavor']}, "
			f"class {len(class_feats)}/{feat_budget['class']}, teamwork {(len(teamwork_feats) if isinstance(teamwork_feats, list) else 0)}/{feat_budget['teamwork']}, "
			f"bloodline {len(bloodline_feats)}/{feat_budget['bloodline']}, "
			f"trainer {len(trainer_feats)}/{feat_budget['trainer']}, profession {len(profession_feats)}/{feat_budget['profession']}")
		if martial_disciplines or mt_feats or style_feats:
			print(f"PoW -> disciplines {martial_disciplines}, IL {initiator_level}, "
				f"known {sum(maneuvers_known_list)} by-level {maneuvers_known_list}, "
				f"readied {sum(maneuvers_readied_list)}, "
				f"stances {len(stances_chosen)}, mt {mt_feats}, styles {style_feats}")

		# Reorder the surviving normal + class-bonus feats (one combined pool) onto their level slots so
		# each lands at a level whose prerequisites are actually met: prereq feats placed at earlier (lower)
		# levels, and BAB / class-level gates respected (e.g. Greater Feint never before Improved Feint nor
		# before its +6 BAB level). Done AFTER the tax-child strip because removing children reindexes the
		# positional normal-feat levels. class_feat_labels are rebuilt in lockstep. Falls back (except) to
		# the post-strip positional order if anything goes wrong, so a generation never crashes here.
		try:
			_post_class_slots = _class_feat_slots[:len(class_feats)]
			feats, class_feats, _normal_levels, _post_class_levels = assign_feats_to_levels(
				character, feats, class_feats,
				[2 * i + 1 for i in range(len(feats))], [lvl for _, lvl in _post_class_slots])
			# the returned class levels are the input multiset re-sorted ascending, so a stable
			# sort of the slot pairs by level re-pairs each level with its granting class
			_post_class_slots = sorted(_post_class_slots, key=lambda s: s[1])
			class_feat_labels = [f"{d} {lvl}" for d, lvl in _post_class_slots][:len(class_feats)]
		except Exception:
			pass

		# Re-home feat-tax bundles to the bucket each primary ACTUALLY ended in -- done AFTER the FINAL
		# reorder above. assign_feats_to_levels treats normal + class-bonus feats as one pool, so a feat
		# can migrate between the two buckets; the sheet applies each bucket's tax dict only to its own
		# bucket, so a migrated primary (e.g. a Martial Training tier reseated as a class row) would lose
		# its "Primary > Child" chain unless its tax bundle moves with it. (Previously this ran after the
		# first of the two reorders, so the second reorder's migrations left tax in the wrong dict.)
		_feats_l = {str(f).lower() for f in feats}
		_class_l = {str(f).lower() for f in class_feats}
		for _moved in [k for k in feats_feat_tax_dict if str(k).lower() in _class_l and str(k).lower() not in _feats_l]:
			class_feat_tax_dict[_moved] = feats_feat_tax_dict.pop(_moved)
		for _moved in [k for k in class_feat_tax_dict if str(k).lower() in _feats_l and str(k).lower() not in _class_l]:
			feats_feat_tax_dict[_moved] = class_feat_tax_dict.pop(_moved)

		# Append the sphere Extra-Talent feats LAST -- after the level-assignment reorder so they keep
		# their hand-built HR1 tax (sphere_feat_tax, merged into feats_feat_tax_dict above) and aren't
		# migrated into the class-bonus pool / chained by feat_tax_func. They land at the end of the
		# Feats list (highest "(Feat N)" numbers). Their budget cost was already reserved out of
		# feat_amounts above, so the normal chooser/backfill left room for them.
		feats.extend(sphere_feats)

		# ---- Final feat-count guarantee: the general feat track == normal_feat_amount EXACTLY ----
		# The sheet labels feats positionally (1,3,5,…), so a list of length N renders feats at the
		# character's real feat levels with no gaps and nothing past their level. Never short (defensive
		# backfill -- RC1 should already prevent it) and never over: when homebrew (Martial Training +
		# sphere Extra-Talent feats) outnumbers the slots, trim the lowest-priority excess -- the sphere
		# Extra-Talent feat SLOTS first (their talents stay on the sheet as native combat/magic talents;
		# only the tracking feat is dropped), then any remaining tail. (House rule: cap to exact.)
		_feat_target = int(getattr(character, "normal_feat_amount", len(feats)) or 0)
		if len(feats) > _feat_target:
			_over = len(feats) - _feat_target
			_sphere_lower = {str(s).lower() for s in sphere_feats}
			_kept = []
			for _f in reversed(feats):                       # sphere Extra-Talent feats are the appended tail
				if _over > 0 and str(_f).lower() in _sphere_lower:
					_over -= 1
					continue
				_kept.append(_f)
			feats = list(reversed(_kept))
			if len(feats) > _feat_target:                    # rare: homebrew exceeds slots even after trimming sphere slots
				feats = feats[:_feat_target]
		elif len(feats) < _feat_target:                      # defensive guarantee against any future regression
			_fill = topup_feat_chooser(character, casting_level_str, _feat_target - len(feats))
			add_feats_to_chooseable(character, _fill)
			feats.extend(_fill)
		print(f"feat guarantee -> general {len(feats)}/{_feat_target}, story {len(story_feats)}/{feat_budget['story']}"
			f", class {len(class_feats)}/{feat_budget['class']} | generator {GENERATOR_VERSION}")

		# Now drop the profession feats into the general feat track -- AFTER the feat-tax passes and the
		# count guarantee, so they are never chained/taxed and never trimmed (their slots were reserved
		# out of feat_amounts / normal_feat_amount above, so each costs a feat). Each renders as its own
		# ordinary feat; register descriptions in homebrew_feat_desc_dict (case-insensitive) so the
		# module / description backfill resolve them instead of hitting the CSV.
		if profession_feats:
			feats.extend(profession_feats)
			for _pf_name, _pf_desc in profession_feat_desc.items():
				homebrew_feat_desc_dict[_pf_name] = _pf_desc



	# ------------------- Homebrew Trainers / Professions (feat section) + Skill Unlock (class features) -------------------#
		# Built here (after the feat section) so trainer feats + their tax chains exist.
		# Professions render their Rank 5 / Rank 15 ability items as their own feat-section items, each
		# carrying pf1 changes/contextNotes/uses -- see profession_abilities.build_profession_ability_items.
		# (The profession FEATS themselves render as ordinary feats in the general feat track -- see the
		# feats.extend(profession_feats) right after the feat-count guarantee above.)
		# Trainers render through the normal feat pipeline in the FoundryVTT module (trainer_feats +
		# trainer_feat_labels + trainer_feat_tax_dict) -> full feat text, no caliber line. Neither rides
		# the class-features renderer anymore; only the Skill Unlock still does.
		profession_ability_items = build_profession_ability_items(character)

		if isinstance(class_features, dict):

			# 3) Skill unlock: dict of "{N} Ranks" -> benefit (rendered as bold-labelled bullets).
			if skill_unlock:
				_unlock = skill_unlock.get("unlock") or {}
				_su_val = {f"{_r} Ranks": _unlock[_r] for _r in ("5", "10", "15", "20") if _unlock.get(_r)}
				class_features["Skill Unlock: " + skill_unlock["skill"]] = _su_val or {"Skill Unlock": skill_unlock["skill"]}

	# ------------------- Last minute Spell Alphabetize + dedupe process -------------------#
		# Per spellbook (multiclass): alphabetize + dedupe each book's final list, then re-derive
		# its per-level prepared count against the FINAL spell list (after domain/bonus spells
		# + dedupe), aligned 1:1 to spell_list_choose_from for the FoundryVTT sheet. Divine casters
		# prepare their whole daily loadout (incl. domain/bonus spells); spellbook casters (wizard,
		# witch, magus, arcanist, alchemist, investigator) prepare only spells/day out of a larger
		# spellbook, so keep the spells/day count from spells_known_selection (capped to the group).
		_divine_casters_list = getattr(data, 'divine_casters')
		for _book in character.spellbooks:
			_book['spell_list_choose_from'] = spell_alphabetize_and_dedupe_func(
				_book.get('spell_list_choose_from') or [])
			_spell_groups = _book['spell_list_choose_from'] or []
			if _book['name'] in _divine_casters_list:
				_book['spells_prepared_per_level'] = [len(g) for g in _spell_groups]
			else:
				_prep = _book.get('spells_prepared_per_level') or []
				_book['spells_prepared_per_level'] = [
					min(_prep[k] if k < len(_prep) else 0, len(g)) for k, g in enumerate(_spell_groups)
				]
		# re-point the legacy scalars at the (now deduped) primary spellbook
		sync_legacy_spell_fields(character)

		# pf1 conditional / rider data for the NPC's chosen spells (Bucket A weapon buffs ->
		# spell_changes_dict; Bucket B attack-spell save/riders -> spell_riders_dict). Exported below
		# for the FoundryVTT module to attach to the weapon / spell items.
		spell_changes_dict, spell_riders_dict = spell_conditionals_selection(character)


	# ------------------- Last minute modded char sheet -------------------#
		mod_char_sheet_var = modded_char_sheet_func(modded_char_sheet)
	#-------------------- Start of export process --------------------#
		archetype_info = json.dumps(archetype_info, indent=4)
		character.land_speed = character.races.get(character.chosen_race, {}).get('speed', 30)

	# ------------------- Build archetype (deterministic scorer; Ollama only breaks near-ties) -------------------#
		# Classify the ACTUAL build (weapon/armor/stats/feats/maneuvers/spells) into a roster
		# archetype (Reach Tripper, God Wizard, Switch Hitter, ...) -- the class name alone is not
		# enough: a fighter can be a skirmisher, sniper, brawler or tank depending on the rolled
		# gear. The scorer consumes the signal vocabulary in build_archetype.py, so every fact
		# below feeds a named signal; roster + weights live in Backend/json/build_archetypes.json.
		_wd = next(iter(character.weapon_dict.values()), {}) if isinstance(character.weapon_dict, dict) else {}
		# weapons_data.json glues the prose description onto the "weapon groups" field -- keep only the group names.
		_weapon_groups = str(_wd.get('weapon groups') or '').split('Description')[0].strip()
		_arch_casting, _arch_spells, _arch_spell_levels = [], [], []
		for _b in character.spellbooks:
			if not _b.get('casting_level_num'):
				continue
			_arch_casting.append(f"{_b['name']} (spells up to level {_b.get('highest_spell_known', 0)})")
			_arch_spell_levels.append(_b.get('highest_spell_known', 0))
			for _grp in reversed(_b.get('spell_list_choose_from') or []):
				if _grp:
					_arch_spells.extend(_grp[:4])   # a few highest-level spells: enough signal, small prompt
					break
		_build = {
			# prompt facts (also rendered for the Ollama near-tie arbiter)
			'classes': [f"{c['name']} {c['level']}" for c in character.classes],
			'main_stat': character.main_stat,
			'stats': f"{character.str}/{character.dex}/{character.con}/{character.int}/{character.wis}/{character.cha}",
			'weapon': weapon_name,
			'weapon_category': _wd.get('category'),
			'weapon_groups': _weapon_groups,
			'armor': armor_name if isinstance(armor_name, str) else '',
			'shield': shield_name if character.shield_flag else '',
			'feats': feats,
			'disciplines': martial_disciplines,
			'stances': stances_chosen,
			'maneuvers': [n for _grp in maneuvers_readied_names for n in (_grp if isinstance(_grp, list) else [_grp])],
			'spheres': spheres_chosen,
			'casting': _arch_casting,
			'spells': _arch_spells,
			# signal-extraction facts (see _signals() in build_archetype.py)
			'class_names': [c['name'] for c in character.classes],
			'class_entries': [{'name': c['name'], 'level': c['level']} for c in character.classes],
			'total_level': character.level,
			'primary_class': character.c_class,
			'bab_tier': str(character.class_data.get(character.c_class, {}).get('bab', 'M')),
			'spell_levels': _arch_spell_levels,
			'initiator_level': initiator_level,
			'armor_type': character.armor_type,
			'shield_flag': character.shield_flag,
			'weapon_special': _wd.get('special'),
			'weapon_critical': _wd.get('critical'),
			'stat_dict': {'str': character.str, 'dex': character.dex, 'con': character.con,
						  'int': character.int, 'wis': character.wis, 'cha': character.cha},
			'feat_buckets': character.feat_buckets,
			'class_feature_names': list(class_features) if isinstance(class_features, dict) else [],
			'companion': bool(getattr(character, 'chosen_animal', None)),
			'sphere_mana_pool': sphere_mana_pool,
		}
		# The "use backstory API" toggle gates the optional Ollama near-tie arbiter only; the
		# deterministic scorer runs (identically) either way.
		_arch_result = choose_build_archetype(_build, use_api=str(use_backstory_api).upper() == "Y")
		build_archetype = str(_arch_result)
		build_tactics = _arch_result.tactics
		print(f"build archetype -> {build_archetype} ({_arch_result.confidence} confidence, "
			  f"contenders {_arch_result.contenders})")

	# ------------------- Backstory (coherent prose via Ollama, template fallback) -------------------#
		# Richer profession + trainer context so the prose can give these vocations real weight.
		_bs_professions = [f"{p['name']} (Profession rank {p['ranks']})" for p in profession_ranks] or professions
		_trainer_groups = {}
		for _lbl, _ft in zip(trainer_feat_labels, trainer_feats):
			_trainer_groups.setdefault(_lbl, []).append(_ft)
		_bs_trainers = []
		for _fts in _trainer_groups.values():
			_cal_name = CALIBER_NAMES.get(len(_fts), "skilled") or "skilled"
			_article = "an" if _cal_name[0] in "aeiou" else "a"
			_bs_trainers.append(f"{_article} {_cal_name} trainer who taught them {', '.join(_fts)}")
		_bs_brief = {
			'name': character_full_name, 'race': character.chosen_race,
			'gender': character.chosen_gender, 'age': age_number, 'region': character.region,
			'alignment': alignment, 'deity': deity_name,
			'char_class': character.c_class_display,
			# all non-primary classes, e.g. "fighter and wizard" for a 3-class character
			'class_2': ' and '.join(
				c['name'] for i, c in enumerate(character.classes)
				if i != character.primary_class_index),
			'level': character.c_class_level, 'main_stat': character.main_stat,
			'martial_disciplines': martial_disciplines, 'notable_feats': feats,
			'traits': getattr(character, 'selected_traits_desc', None) or selected_traits,
			'personality_traits': personality_traits, 'mannerisms': mannerisms, 'flaw': flaw,
			'background_traits': background_traits, 'professions': _bs_professions,
			'craft': character.craft_chosen, 'trainers': _bs_trainers,
			'appearance': appearance, 'parents': parents,
			'siblings': [older_brothers, younger_brothers, older_sisters, younger_sisters],
			# structured_bio-only fields (the prose prompt keeps appearance as one field)
			'hair_type': hair_type, 'hair_color': hair_color, 'eye_color': eye_color,
			'build_archetype': build_archetype, 'build_tactics': build_tactics,
		}
		# Prose backstory disabled for now: the structured fact block below is meant to serve as a
		# prompt (for a GM or an AI), not a summary. generate_backstory stays wired for the website:
		# backstory = generate_backstory(_bs_brief, use_api=str(use_backstory_api).upper() == "Y", focus=backstory_focus)
		backstory = ""
		# Scannable fact block shown on the sheet's Biography tab (empty prose = no Backstory section).
		formatted_bio = structured_bio(_bs_brief)

		payload = {
				# The generated character, assembled as ONE ordered dict. This used to be four
				# parallel lists -- 146 values and 146 key strings, 80 lines apart, held in
				# alignment by nothing but position, with a length assert on one pair and none on
				# the other (a miscount there silently zip-truncated a key off the payload).
				# Insertion order here is the order the module and web sheet have always seen.
				"region": character.region,
				"chosen_race": character.chosen_race,
				"land_speed": character.land_speed,
				"character_full_name": character_full_name,
				"c_class": character.c_class,
				"c_class_display": character.c_class_display,
				"c_class_2": character.c_class_2,
				"alignment": alignment,
				"age_number": age_number,
				"height_number": height_number,
				"weight_number": weight_number,
				"dex": character.dex,
				"str": character.str,
				"con": character.con,
				"int": character.int,
				"wis": character.wis,
				"cha": character.cha,
				"inherents": character.inherents,
				"level_up_stats": character.level_up_stats,
				"racial_stats": character.racial_stats,
				"flaw": flaw,
				"Total_HP": character.Total_HP,
				"sheet_health": character.sheet_health,
				"bab_total": character.bab_total,
				"armor_ac": armor_ac,
				"shield_ac": shield_ac,
				"armor_name": armor_name,
				"armor_spell_failure": armor_spell_failure,
				"armor_weight": armor_weight,
				"armor_armor_check_penalty": armor_armor_check_penalty,
				"armor_max_dex_bonus": armor_max_dex_bonus,
				"shield_name": shield_name,
				"shield_spell_failure": shield_spell_failure,
				"shield_weight": shield_weight,
				"shield_armor_check_penalty": shield_armor_check_penalty,
				"shield_max_dex_bonus": shield_max_dex_bonus,
				# Saving throws are derived by the pf1 engine / the web sheet, not exported:
				# fort_saving_throw, reflex_saving_throw, wisdom_saving_throw.
				"spell_list_choose_from": character.spell_list_choose_from,
				"day_list": day_list,
				"known_list": known_list,
				"spells_prepared_per_level": character.spells_prepared_per_level,
				"martial_disciplines": martial_disciplines,
				"initiator_level": initiator_level,
				"maneuvers_known_list": maneuvers_known_list,
				"maneuvers_readied_list": maneuvers_readied_list,
				"maneuvers_choose_from": maneuvers_choose_from,
				"maneuvers_readied_names": maneuvers_readied_names,
				"stances_chosen": stances_chosen,
				"mt_feats": mt_feats,
				"initiation_stat": initiation_stat,
				"magic_talent_items": magic_talent_items,
				"combat_talent_items": combat_talent_items,
				"sphere_feats": sphere_feats,
				"sphere_feat_tax": sphere_feat_tax,
				"sphere_mana_pool": sphere_mana_pool,
				"spheres_chosen": spheres_chosen,
				"sphere_counts": sphere_counts,
				"casting_tradition": casting_tradition,
				"sphere_drawbacks": sphere_drawbacks,
				"sphere_boons": sphere_boons,
				"sphere_traits": sphere_traits,
				"deity_name": deity_name,
				"skill_ranks": skill_ranks,
				"weapon_enhancement_chosen_list": weapon_enhancement_chosen_list,
				"armor_enhancement_chosen_list": armor_enhancement_chosen_list,
				"shield_enhancement_chosen_list": shield_enhancement_chosen_list,
				"weapon_enhancement_bonus": weapon_enhancement_bonus,
				"armor_enhancement_bonus": armor_enhancement_bonus,
				"shield_enhancement_bonus": shield_enhancement_bonus,
				"selected_traits": selected_traits,
				"equipment_list": equipment_list,
				"level": character.c_class_level,
				# Subrace data (chosen_subrace, subrace_description) is deliberately not exported -- FoundryVTT
				# doesn't use it and the generator's subrace handling needs fixing first.
				"archetype1": character.archetype1,
				"hair_color": hair_color,
				"hair_type": hair_type,
				"eye_color": eye_color,
				"appearance": appearance,
				"language_text": language_text,
				"feats": feats,
				"teamwork_feats": teamwork_feats,
				"teamwork_feat_labels": teamwork_feat_labels,
				"story_feats": story_feats,
				"flaw_feats": flaw_feats,
				"class_feats": class_feats,
				"class_feat_labels": class_feat_labels,
				"flavor_feats": flavor_feats,
				"bloodline_feats": bloodline_feats,
				"bloodline_feat_labels": bloodline_feat_labels,
				"trainer_feats": trainer_feats,
				"trainer_feat_labels": trainer_feat_labels,
				"trainer_feat_tax_dict": trainer_feat_tax_dict,
				"trainer_calibers": trainer_calibers,
				"profession_feats": profession_feats,
				"profession_feat_desc": profession_feat_desc,
				"profession_ranks": profession_ranks,
				"profession_pool": profession_pool,
				"profession_ability_items": profession_ability_items,
				"skill_unlock": skill_unlock,
				"gold": character.gold,
				"platnium": character.platnium,
				"full_domain": full_domain,
				"school": school,
				"opposing_school": opposing_school,
				"bloodline": bloodline,
				"background_traits": background_traits,
				"professions": professions,
				"craft_type": character.craft_chosen,
				"mannerisms": mannerisms,
				"personality_traits": personality_traits,
				"hero_points": hero_points,
				"gender": character.chosen_gender,
				"class_ability_desc": class_ability_desc,
				"class_ability": class_ability,
				"class_features": class_features,
				"class_feature_levels": class_feature_levels,
				"archetype_info": archetype_info,
				"parents": parents,
				"older_brothers": older_brothers,
				"younger_brothers": younger_brothers,
				"older_sisters": older_sisters,
				"younger_sisters": younger_sisters,
				"weapon_name": weapon_name,
				"specialty_schools": character.specialty_schools,
				"counter_schools": character.counter_schools,
				"chosen_spell_descriptor": character.chosen_descriptors,
				"counter_spell_descriptor": character.counter_descriptors,
				"total_rolled_hp": total_rolled_hp,
				"mini_alignment": mini_alignment,
				"casting_level_str_foundry": casting_level_str_foundry,
				"main_stat": character.main_stat,
				"story_feat_tax_dict": story_feat_tax_dict,
				"flaw_feat_tax_dict": flaw_feat_tax_dict,
				"flavor_feat_tax_dict": flavor_feat_tax_dict,
				"class_feat_tax_dict": class_feat_tax_dict,
				"feats_feat_tax_dict": feats_feat_tax_dict,
				"feat_budget": feat_budget,
				"mod_char_sheet_var": mod_char_sheet_var,
				"backstory": backstory,
				"formatted_bio": formatted_bio,
				# --- multiclass (new keys; the legacy keys above keep their old semantics:
				#     "level" = primary-class level, "c_class"/"c_class_2" = primary/second class) ---
				"classes": [{'name': c['name'], 'display': c['display'], 'level': c['level'],
					'archetype': archetypes_per_class[i] if i < len(archetypes_per_class) else {}}
					for i, c in enumerate(character.classes)],
				"total_level": character.level,
				"save_bases": character.save_bases,
				"spellbooks": [{**{k: b.get(k) for k in (
					'name', 'display', 'level', 'capped_level', 'casting_level_string',
					'casting_level_num', 'highest_spell_known', 'spells_known_list',
					'spells_per_day_list', 'spell_list_choose_from', 'spells_prepared_per_level')},
					'casting_stat': casting_stat_for(b['name']),
					'divine': b['name'] in data.divine_casters}
					for b in character.spellbooks],
				"class_feature_owners": class_feature_owners,
				"build_archetype": build_archetype,
				"build_tactics": build_tactics,
				# Replay handle: pass this back as generate_random_char(seed=...) to reproduce this
				# exact character. See Backend/scripts/test_golden_payload.py.
				"generation_seed": seed,
				}
		
		# Feat buff side-maps (populated below, once the placed-feat list exists). Empty dicts here so the
		# export references stay stable; the populate block mutates these same objects in place.
		feat_changes_dict = {}
		feat_conditionals_dict = {}
		item_changes_dict = {}
		enhancement_effects_dict = {}
		class_feature_changes_dict = {}
		class_feature_conditionals_dict = {}
		payload.update({
				"spell_list_choose_from_dict": character.spell_list_choose_from,
				"equip_descrip": equip_descrip,
				"maneuvers_desc_dict": maneuvers_desc_dict,
				"homebrew_feat_desc_dict": homebrew_feat_desc_dict,
				"feat_changes_dict": feat_changes_dict,
				"feat_conditionals_dict": feat_conditionals_dict,
				"spell_changes_dict": spell_changes_dict,
				"spell_riders_dict": spell_riders_dict,
				"selected_traits_desc": getattr(character, 'selected_traits_desc', []) or [],
				"item_changes_dict": item_changes_dict,
				"enhancement_effects_dict": enhancement_effects_dict,
				"flaw_effects_dict": flaw_effects_dict,
				"class_feature_changes_dict": class_feature_changes_dict,
				"class_feature_conditionals_dict": class_feature_conditionals_dict,
				})

		# Make EVERY placed feat renderable by the FoundryVTT module. The module silently DROPS any feat
		# name it can't resolve against its every_feat.json compendium AND that has no description to
		# synthesize from -- and since it labels feats positionally, a dropped feat removes the TOP slot
		# (the "missing 1-2 feats" the sheet showed). every_feat.json is an incomplete export, so real
		# Paizo feats (Mighty Conditioning, Pet, Leg Slash, …) were being dropped. Supplying a description
		# entry for every rendered feat lets the module's existing fallback synthesize the row instead of
		# dropping it -> the visible count always equals what we exported. Descriptions are best-effort
		# from data/feats.csv; an empty entry is still enough to keep the row (name preserved). Feats
		# already described (homebrew / sphere / profession) are left untouched.
		_render_feat_names = []
		for _b in (feats, story_feats, flaw_feats, flavor_feats, class_feats,
				   trainer_feats, bloodline_feats, teamwork_feats):
			if isinstance(_b, list):
				_render_feat_names.extend(str(_x) for _x in _b)
		_have_desc = {str(_k).lower() for _k in homebrew_feat_desc_dict}
		_need_desc = [_n for _n in dict.fromkeys(_render_feat_names) if _n.lower() not in _have_desc]
		if _need_desc:
			_desc_info = feat_spell_searcher(character, character.c_class, list(_need_desc),
											 "feats", "description", None, {}) or {}
			_desc_ci = {str(_k).lower(): (_v.get("description", "") if isinstance(_v, dict) else "")
						for _k, _v in _desc_info.items()}
			for _n in _need_desc:
				homebrew_feat_desc_dict[_n] = _desc_ci.get(_n.lower(), "")

		# --- Feat numeric buffs (Foundry "Changes" tab) + active-feat toggle conditionals --------------
		# Curated, hand-vetted side-maps keyed by feat name. feat_changes.json -> always-on pf1 `changes`
		# (and situational contextNotes) the FoundryVTT module overlays onto the feat item; feat_conditionals
		# .json -> default-off toggle conditionals (Power Attack, Combat Expertise, Deadly Aim, ...) the
		# module attaches to the main weapon. We author ONLY feats Foundry's every_feat.json compendium does
		# not already automate, so nothing double-applies. Missing files -> empty maps (feature simply off).
		import json as _json, re as _re
		# Name matching + the gap report live in utils/class_func/buff_match.py; every curated map is
		# loaded and cached there (this block used to re-parse ~1.6 MB of JSON on every generation).
		_buff_gaps = []
		_curated_feat_changes, _g = match_buffs("feat", _render_feat_names);            _buff_gaps += _g
		_curated_feat_conds, _g = match_buffs("feat_conditional", _render_feat_names);  _buff_gaps += _g
		# Runtime-computed feat changes override the curated file, because they're keyed to a choice
		# this character made rather than to the bare feat name.
		_runtime_feat_changes = {}
		# Skill Focus / Prodigy: changes computed at generation time (keyed to the chosen
		# profession/skill, e.g. "Skill Focus (Profession (Sailor))").
		for _sk_name, _sk_entry in (getattr(character, "skill_focus_changes", {}) or {}).items():
			_runtime_feat_changes[str(_sk_name).lower()] = _sk_entry
		# Weapon Focus family: sum the tax-bundled chain (Greater Weapon Focus / Weapon Specialization /
		# Greater Weapon Specialization) onto the placed "Weapon Focus" primary -> one cumulative change.
		for _wf_name, _wf_entry in weapon_focus_changes(_render_feat_names,
				[feats_feat_tax_dict, class_feat_tax_dict, story_feat_tax_dict, flaw_feat_tax_dict,
				 flavor_feat_tax_dict, trainer_feat_tax_dict]).items():
			_runtime_feat_changes[str(_wf_name).lower()] = _wf_entry
		for _disp in dict.fromkeys(_render_feat_names):
			_entry = _runtime_feat_changes.get(str(_disp).lower())
			if _entry is None:
				_entry = _curated_feat_changes.get(_disp)
			if _entry is not None:
				feat_changes_dict[_disp] = _entry
			if _disp in _curated_feat_conds:
				feat_conditionals_dict[_disp] = _curated_feat_conds[_disp]

		# --- Equipment numeric buffs + context notes ----------------------------------------------------
		# item_changes.json is GENERATED from items_best.json descriptions by scripts/build_item_changes.py
		# (clean numeric bonuses -> pf1 `changes`, situational bonus text -> `contextNotes`), with
		# item_changes_overrides.json merged on top at build time. Keyed by lowercase backend item name; the
		# module overlays entries onto the matched/synthesized equipment item (deduped by change target, so
		# items every_item.json already automates don't double-apply).
		_matched_items, _g = match_buffs("item", equipment_list or []);   _buff_gaps += _g
		for _item_name, _ic_entry in _matched_items.items():
			if _ic_entry:
				item_changes_dict[_item_name] = _ic_entry

		# Weapon/armor/shield special abilities (flaming, keen, ...) -> curated quality_effects.json.
		# Sectioned because names collide across the lists with different rules (e.g. Ghost Touch):
		# weapon.* -> conditionals on the main weapon's attack action; armor.* (covers the Armor AND
		# Shield quality lists) -> changes/contextNotes overlaid on the armor/shield item.
		# Every shipped entry also carries the quality's rules text ("description") pulled from the
		# scraped qualities lists, so the module can render it under the item. Entries are shallow-
		# copied so the cached quality_effects data is never mutated; a quality missing from
		# quality_effects.json still ships description-only as a safety net.
		def _quality_descriptions(_qualities, _sections):
			_out = {}
			for _sec in _sections:
				for _k, _v in ((_qualities or {}).get(_sec) or {}).items():
					_text = _re.sub(r"\s+", " ", str((_v or {}).get("Description") or "")).strip()
					_text = _re.sub(r"\s*Construction\s*$", "", _text)
					if _text:
						_out.setdefault(str(_k).lower(), _text)
			return _out
		_wq_desc = _quality_descriptions(getattr(character, "weapon_qualities", {}), ("Melee", "Ranged"))
		_aq_desc = _quality_descriptions(getattr(character, "armor_qualities", {}), ("Armor", "Shield"))

		# The shield list is matched against the ARMOR section on purpose -- quality_effects.json keeps
		# one armor section covering both the Armor and Shield quality lists.
		for _section, _chosen, _qe_section, _desc_map in (
				("weapon", weapon_enhancement_chosen_list, "weapon", _wq_desc),
				("armor", armor_enhancement_chosen_list, "armor", _aq_desc),
				("shield", shield_enhancement_chosen_list, "armor", _aq_desc)):
			_matched_q, _g = match_buffs("quality", _chosen or [], section=_qe_section)
			_buff_gaps += _g
			for _q_name in dict.fromkeys(_chosen or []):
				_q_entry = dict(_matched_q.get(_q_name) or {})
				_q_desc = _desc_map.get(str(_q_name).lower())
				if _q_desc:
					_q_entry["description"] = _q_desc
				if _q_entry:
					enhancement_effects_dict.setdefault(_section, {})[_q_name] = _q_entry

		# --- Class-choice power effects (rage powers, ki powers, hexes, talents, arcana, ...) ----------
		# class_feature_effects.json is GENERATED by scripts/build_class_feature_changes.py (auto-drafts
		# parsed from the class_data pools + class_feature_effects_overrides.json curated on top).
		# Sections match the class_features buckets; keys are normalized power names (lowercase, no
		# (Su)/(Ex)/(Sp)). Curated entries ship changes/contextNotes (-> class_feature_changes_dict,
		# module overlays them on the class-feature item, toggled with the parent state for while-raging
		# style powers), weapon toggle conditionals (-> class_feature_conditionals_dict, feat pattern),
		# and tagBuff Multi-Buff-Distributor payloads for powers that affect OTHER creatures — their
		# @classes/@abilities refs are baked to this NPC's numbers since a recipient's sheet can't
		# resolve them. Auto-drafted entries ("review": true) ship contextNotes ONLY — never unvetted
		# changes or conditionals.
		_class_levels = {str(_c.get("name", "")).lower(): _c.get("level", 0) or 0
						 for _c in (character.classes or [])}
		_ability_mods = {"str": character.str_mod, "dex": character.dex_mod, "con": character.con_mod,
						 "int": character.int_mod, "wis": character.wis_mod, "cha": character.cha_mod}
		def _bake(_text):
			_text = _re.sub(r"@classes\.(\w+)\.level",
							lambda _m: str(_class_levels.get(_m.group(1).lower(), 0)), str(_text))
			return _re.sub(r"@abilities\.(str|dex|con|int|wis|cha)\.mod",
						   lambda _m: str(_ability_mods[_m.group(1)]), _text)
		# shared pools: formulas are authored against the canonical class (barbarian, witch, rogue);
		# when THIS character got the bucket from a sibling class (skald rage powers, shaman hexes,
		# ninja/slayer talents), retarget @classes.<canonical>.level to the class they actually have.
		_bucket_classes = {"rage_powers": ("barbarian", "skald"), "hexes": ("witch", "shaman"),
						   "ninja_talents": ("rogue", "ninja"), "slayer_talents": ("rogue", "slayer")}
		_cfe_buckets = set(buff_sections("class_feature"))
		for _bucket, _powers in (class_features or {}).items():
			if _bucket not in _cfe_buckets or not isinstance(_powers, dict):
				continue
			_owner = next((_c for _c in _bucket_classes.get(_bucket, ()) if _c in _class_levels), None)
			_matched_cf, _g = match_buffs("class_feature", list(_powers), section=_bucket)
			_buff_gaps += _g
			for _p_name in _powers:
				_cf_entry = _matched_cf.get(_p_name)
				if not _cf_entry:
					continue
				_cf_json = _json.dumps(_cf_entry)
				if _owner and "@classes." in _cf_json:
					_cf_entry = _json.loads(_re.sub(
						r"@classes\.(\w+)\.level",
						lambda _m: _m.group(0) if _m.group(1).lower() in _class_levels
						else "@classes.%s.level" % _owner, _cf_json))
				if _cf_entry.get("review"):
					if _cf_entry.get("contextNotes"):
						class_feature_changes_dict[_p_name] = {
							"changes": [], "contextNotes": _cf_entry["contextNotes"]}
					continue
				_cf_out = {"changes": _cf_entry.get("changes", []),
						   "contextNotes": _cf_entry.get("contextNotes", [])}
				_cf_tag = _cf_entry.get("tagBuff")
				if _cf_tag:
					_cf_out["tagBuff"] = {
						"onlyOthers": bool(_cf_tag.get("onlyOthers")),
						"auraRange": _cf_tag.get("auraRange"),
						"changes": [dict(_ch, formula=_bake(_ch.get("formula", "")))
									for _ch in _cf_tag.get("changes", [])],
						"contextNotes": [dict(_n, text=_bake(_n.get("text", "")))
										 for _n in _cf_tag.get("contextNotes", [])],
					}
				if _cf_out["changes"] or _cf_out["contextNotes"] or _cf_tag:
					class_feature_changes_dict[_p_name] = _cf_out
				if _cf_entry.get("conditionals"):
					class_feature_conditionals_dict[_p_name] = _cf_entry["conditionals"]

		# --- Buff gap report ----------------------------------------------------------------------------
		# A gap is NOT "nothing curated for this name" (that is the normal case for most feats and
		# spells). It means curated data for the name EXISTS but the kind's name-matching rule didn't
		# reach it -- a casing/punctuation/suffix mismatch that would otherwise drop the buff in total
		# silence. Shipped on the payload so it is visible in the API response and captured by the
		# golden payloads, which makes a regression here a test failure rather than a discovery weeks
		# later on a Foundry sheet.
		_spell_gaps = getattr(character, "spell_buff_gaps", None) or []
		_buff_gaps += _spell_gaps
		_buff_gaps += getattr(character, "talent_buff_gaps", None) or []
		_buff_gaps += getattr(character, "stance_buff_gaps", None) or []
		payload["buff_gaps"] = _buff_gaps
		if _buff_gaps:
			print(f"buff gaps: {len(_buff_gaps)} curated entr(y/ies) not matched")
			for _gap_line in format_gaps(_buff_gaps):
				print(f"  {_gap_line}")

		character.data_dict.update(payload)

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
		print("character.inherents", character.inherents)
		print("character.stats", stats)
		# print("character.level_up_stats", character.level_up_stats)
		# print("character.chooseable", sorted(list(character.chooseable)))
		# print("character.feats", sorted(list(feats)))
		# print("story_feats", sorted(list(story_feats)))
		# print("flaw_feats", sorted(list(flaw_feats)))
		# print("class_feats", sorted(list(class_feats)))
		# print("character.teamwork_feats", sorted(list(teamwork_feats)))
		# print("character.processed_feats", character.processed_feats)
		# print("character.chooseable_talents", sorted(character.chooseable_talents))




		# print("region", character.region)
		# print("character.chosen_race", character.chosen_race)
		# print("alignment", alignment)
		# print("mini_alignment", mini_alignment)
		# print("deity_name", deity_name)
		# print("race", character.races)

		print(".")
		print(".")
		print(".")
		print(".")
		# print("story_feat_tax_dict", story_feat_tax_dict)
		# print("flaw_feat_tax_dict", flaw_feat_tax_dict)
		# print("flavor_feat_tax_dict", flavor_feat_tax_dict)
		# print("class_feat_tax_dict", class_feat_tax_dict)
		# print("feats_feat_tax_dict", feats_feat_tax_dict)
		print("character.c_class", character.c_class)

		# Freshness stamp -- lets a restart (and any exported actor) reveal which backend build ran.
		character.data_dict['generator_version'] = GENERATOR_VERSION
		return character.data_dict

# CLI smoke test only: importing this module (e.g. app.py does `from main_test import ...`) must NOT
# run a full generation -- it just defines generate_random_char for the Flask request handler to call.
if __name__ == "__main__":
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
