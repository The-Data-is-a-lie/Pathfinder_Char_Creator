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

# A payload carrying psionics (or Path of War, or any other extracted mechanics) is Distribution
# under section 10 of the Open Game License, which obliges us to ship a copy of the licence with it.
# The payload carries a POINTER rather than the licence text: embedding ~9 KB of legal boilerplate in
# every character would dwarf several of the blocks that are actually about the character. app.py
# rewrites this to an absolute URL for HTTP consumers, which cannot resolve a bare path against the
# backend's host. See Backend/json/class_data/psionics/NOTICE.md and LICENSE-OGL.txt.
LICENSE_PATH = "/license"


# Importing custom functions
from utils.class_func.adding_bonus_spells			import add_bonus_spells, add_bonus_spells_from_dict
from utils.class_func.alignment_and_deity 			import randomize_deity, choose_alignment
from utils.class_func.animal_companions 			import resolve_bonded_creatures
from utils.class_func.companion_feats 			import companion_feats
from utils.class_func.companion_stats 			import stat_bonded_creatures
from utils.class_func.familiars 				import stat_familiars
from utils.class_func.appearance 					import randomize_apperance_attr, randomize_body_feature, get_racial_attr
from utils.class_func.armor_and_enhancements 		import plan_enhancements, enhancement_chooser#, enhancement_limits
from utils.class_func.armor_and_weapon_chooser 		import (armor_chooser, weapon_chooser, list_selection, shield_chooser, 
                                                                 shield_flag_func, ac_bonus_calculator, weapon_type_flag_func)
from utils.class_func.chooseable 					import chooseable_list, chooseable_list_race, chooseable_list_archetypes#, chooseable_list_class
from utils.class_func.class_abilities 				import get_class_abilities, get_class_abilties_desc  
from utils.class_func.class_specific_feats 			import class_specific_feats_chooser, monk_feats_chooser, ranger_feats_chooser
from utils.class_func.domain_inquisition 			import domain_chance, domain_chooser#, inquisition_chooser
from utils.class_func.extra_combat_feats 			import extra_combat_feats, extra_teamwork_feats, class_bonus_feat_slots, teamwork_feat_slots, bloodline_bonus_feat_levels
from utils.class_func.favored_class 				import favored_class_calculator, favored_class_option, favored_class_option_chooser
from utils.class_func.family_func 					import randomize_siblings, randomize_parents
from utils.class_func.feats 						import (build_selector, chooseable_list, chooseable_list_stats,
                                                  			chooseable_list_class_features, feat_spell_searcher, generic_multi_chooser,
                                                            simple_list_chooser, generic_feat_chooser, bloodline_feat_chooser, teamwork_pool_size,
                                                            capitalize_feats, dedupe_feats_case_insensitive, topup_feat_chooser,
                                                            metzofitz_description, e_kat_feat_chooser,
                                                            e_kat_feat_table, e_kat_description,
                                                            luck_trait_table, luck_trait_chooser,
                                                            luck_trait_description, luck_feat_table,
                                                            held_luck_feats, luck_sheet_sections,
                                                            e_kat_exchange_rows)
from utils.class_func.feats_to_chooseable 			import add_feats_to_chooseable
from utils.class_func.feat_tax 						import feat_tax_func, feat_spell_searcher
from utils.class_func.feat_skill_choice 			import FREE_AT_BAB1, filter_free_feats, specialize_skill_choice_feats
from utils.class_func.weapon_focus_buffs import weapon_focus_changes
from utils.class_func.buff_match					import match as match_buffs, sections as buff_sections, format_gaps, keep_tier_a
from utils.class_func.pipeline					import phase, seal, require_sealed, PhaseRecord
from utils.class_func.power_role				import phase_power_role
from utils.payload							import build_payload, gear_display, PAYLOAD_KEYS
from utils.class_func.spheres 						import randomize_spheres_num, choose_spheres_attr, add_overflow_talents, MAX_EXTRA_TALENT_FEATS, mentor_sphere_summary, mentor_feat_worth, roll_talent_budget
from utils.class_func.flag_assign 					import human_flag_assigner, druidic_flag_assigner
from utils.class_func.flaws 						import flaw_chooser
from utils.class_func.generic_func 					import generic_class_option_chooser, get_data_without_prerequisites, no_prereq_prep, levels_for#, no_prereq_loop, chosen_set_append
from utils.class_func.grand_discovery 				import grand_discovery_chooser
from utils.class_func.gunslinger 					import choose_gun_func
from utils.class_func.hero_point_generator 			import hero_point_generator
from utils.class_func.hp_rolls 						import roll_hp, total_hp_calc, hit_dice_calc
from utils.class_func.item_and_price 				import item_chooser
from utils.class_func.language 						import language_chooser
from utils.class_func.level_and_bab 				import randomize_level
from utils.class_func 								import luck
from utils.class_func 								import mythic
# randomize_luck() is gone (see luck.py): it implemented a DIFFERENT rule -- a 5% roll of +-1..40,
# where the Doc's luck is bought and caps at +25/-50. randomize_mythic (luck_and_mythic.py's other
# half) is gone too: mythic is granted by the named `mythic` input (mythic.py), never by a roll.
from utils.class_func.path_of_war 					import randomize_path_of_war_num, choose_path_of_war_attr, martial_training_depth
from utils.class_func.psionics 						import choose_psionics_attr, mind_blade
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
from utils.class_func.skill_ranks 					import skills_selector, misc_homebrew_enabled, homebrew_enabled
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
from utils.class_func.feat_level_assignment import assign_feats_to_levels, normal_feat_slot_levels
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
	'bard': Load_when_needed('Backend/json/class_data/bard.json'),	
	'bloodlines': Load_when_needed('Backend/json/bloodlines.json'),
	'class_features': Load_when_needed('Backend/json/class_features.json'),	
	# 'classes': Load_when_needed('Backend/json/class.json'),
	'class_data': Load_when_needed('Backend/json/class_data.json'),
	'class_choice_schedule': Load_when_needed('Backend/json/class_choice_schedule.json'),
	'companion_archetypes': Load_when_needed('Backend/json/companion_archetypes.json'),
	'companion_grantors': Load_when_needed('Backend/json/companion_grantors.json'),
	'cleric_domains': Load_when_needed('Backend/json/cleric_domains.json'),				
	'deity': Load_when_needed('Backend/json/deity.json'),	
	'druid_domains': Load_when_needed('Backend/json/druid_domains.json'),
	'familiar_choices': Load_when_needed('Backend/json/familiar_choices.json'),
	'familiar_master_bonus': Load_when_needed('Backend/json/familiar_master_bonus.json'),
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
	'hunter': Load_when_needed('Backend/json/class_data/hunter.json'),
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
	'shifter': Load_when_needed('Backend/json/class_data/shifter.json'),
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

	# Psionics section. The per-class option files (aegis.json, cryptic.json, ...) are GENERATED
	# from the scrape by Backend/scripts/build_psionic_class_data.py and are registered under the
	# class's own name, because generic_class_option_chooser reads them as getattr(character,
	# <class name>). TEN of the twelve have one; the voyager's choice feature grants bonus feats
	# rather than options, and the wilder chooses powers instead.
	#
	# The psion was left out of that count and should not have been (class-choices ticket 02): its
	# discipline is a real 1st-level pick that gates which powers are legal. A missing registration
	# here is not a quiet no-op -- the chooser reads getattr(character, 'psion', {}) and calls
	# random.choice on an empty list, so the omission crashes rather than under-delivering.
	'aegis': Load_when_needed('Backend/json/class_data/aegis.json'),
	'psion': Load_when_needed('Backend/json/class_data/psion.json'),
	'cryptic': Load_when_needed('Backend/json/class_data/cryptic.json'),
	'dread': Load_when_needed('Backend/json/class_data/dread.json'),
	'highlord': Load_when_needed('Backend/json/class_data/highlord.json'),
	'marksman': Load_when_needed('Backend/json/class_data/marksman.json'),
	'psychic warrior': Load_when_needed('Backend/json/class_data/psychic warrior.json'),
	'soulknife': Load_when_needed('Backend/json/class_data/soulknife.json'),
	'tactician': Load_when_needed('Backend/json/class_data/tactician.json'),
	'vitalist': Load_when_needed('Backend/json/class_data/vitalist.json'),
	'psionic_classes': Load_when_needed('Backend/json/class_data/psionics/psionic_classes.json'),
	'psionic_powers_known': Load_when_needed('Backend/json/class_data/psionics/psionic_powers_known.json'),
	'psionic_power_lists': Load_when_needed('Backend/json/class_data/psionics/psionic_power_lists.json'),
	'psionic_powers': Load_when_needed('Backend/json/class_data/psionics/psionic_powers.json'),
	'psionic_name_map': Load_when_needed('Backend/json/class_data/psionics/psionic_name_map.json'),

	# Occult Adventures section. Same convention as psionics: GENERATED files, registered under the
	# class's own name because generic_class_option_chooser reads them as getattr(character,
	# <class name>). Rebuild with Backend/scripts/build_occult_class_data.py after any pf1 or
	# pf-content update -- the pools are harvested out of those compendia, not hand-maintained.
	'occultist': Load_when_needed('Backend/json/class_data/occultist.json'),
	'kineticist': Load_when_needed('Backend/json/class_data/kineticist.json'),
	'medium': Load_when_needed('Backend/json/class_data/medium.json'),
	'mesmerist': Load_when_needed('Backend/json/class_data/mesmerist.json'),
	'psychic': Load_when_needed('Backend/json/class_data/psychic.json'),
	'spiritualist': Load_when_needed('Backend/json/class_data/spiritualist.json'),

	# Paizo collab classes. Same convention again: GENERATED files (by
	# Backend/scripts/build/build_collab_class_options.py), registered under the class's own name.
	'vampire hunter': Load_when_needed('Backend/json/class_data/vampire hunter.json'),
	'omdura': Load_when_needed('Backend/json/class_data/omdura.json'),
}

def strip_labeled_bucket(feat_list, label_list, children):
	'''Filter a feat list and its parallel label list in lockstep, dropping feats whose
	lower() is in `children` (feats now bundled onto a feat-tax primary).'''
	lbls = list(label_list) + [None] * (len(feat_list) - len(label_list))
	kept = [(f, lbl) for f, lbl in zip(feat_list, lbls) if str(f).lower() not in children]
	return [f for f, _ in kept], [lbl for _, lbl in kept if lbl is not None]

# --------------------------------------------------------------------------------------------- #
# Pipeline phases. Each declares what it needs on the character and what it is responsible for
# setting, so an ordering mistake raises instead of quietly producing a worse NPC -- see
# utils/class_func/pipeline.py. Extraction is staged and these are declared in pipeline order:
# identity -> alignment/level -> stats -> professions/skills. Everything from the HP roll onward is
# still inline in generate_random_char; the feat / Path of War / Spheres block is last on purpose,
# because it rebuilds its feat lists across ~600 lines of backfill and trim loops.
# --------------------------------------------------------------------------------------------- #

@phase(requires=[], provides=['chosen_gender', 'region', 'chosen_race',
                              'f_name', 'l_name', 'full_name', '_class_picks', 'c_class'])
def phase_bootstrap_identity(character, userInput_gender, userInput_region, userInput_race,
                             class_choice, chosen_BAB, chosen_caster_level, multi_class):
	'''Who this NPC is before it has any levels: gender, region, race, name, and which classes.

	requires NOTHING, and that is not laziness -- this is the first phase, so there is no earlier
	phase whose output could be missing. Ticket 05's rule is "name what crosses IN from outside the
	phase"; here nothing does. The character arrives freshly constructed with its JSON loaded, which
	is a precondition of the constructor rather than of the ordering.

	THE SEAM IS ONE LINE LOWER THAN IT LOOKS. The obvious boundary starts at `CreateNewCharacter`,
	but a `@phase` takes the character as its first argument and checks `requires` against it -- so
	the phase cannot be the thing that creates it. Construction stays at the call site and the phase
	begins with the already-built object. Worth recording: every later block has a natural first line;
	this one is the only phase whose boundary is set by the decorator rather than by the work.

	`provides` is exhaustive per ticket 05 -- it is checked on the way OUT, so an over-declared name
	fails loudly on the first run rather than drifting. `region` is set inside `region_chooser`
	(util.py:76) rather than returned, which is exactly the kind of invisible write `provides` is for.

	Returns (f_name, l_name): the two locals the rest of the function still reads. `full_name` is
	on the character, so it is declared rather than returned.
	'''
	# prep variables
	no_prereq_prep(character)
	character.processed_feats = set()
	character.cached_dataset_without_prerequisites = []
	character.cached_prereq_list = set()
	character.chooseable_talents = []

	character.chosen_gender = gender_chooser(character, userInput_gender)

	region_chooser(character, userInput_region)
	race_chooser(character, userInput_race)
	f_name, l_name = name_chooser(character)
	select_classes(character, class_choice, chosen_BAB, chosen_caster_level, multi_class)
	return f_name, l_name


@phase(requires=['region', 'chosen_race', '_class_picks'],
	   provides=['alignment', 'alignment_display', 'mini_alignment', 'deity_choice',
				 'age', 'height', 'weight', 'flaw', 'flaw_effects',
				 'background_traits', 'mannerisms', 'personality_traits',
				 'level', 'classes', 'feat_amounts'])
def phase_alignment_and_level(character, alignment_input, deity_flag, low_level, high_level):
	'''Everything rolled off a finished identity but before any levels are spent: alignment, deity,
	body, flaws, personality flavour -- and then the level itself.

	requires `region`: randomize_deity biases ~70% toward the homeland's canon faiths
	(alignment_and_deity._region_affinity_deity reads it through a getattr default), so running this
	before region_chooser would quietly drop the setting flavour instead of failing.
	requires `chosen_race`: randomize_body_feature indexes the race's age/height/weight dice.
	requires `_class_picks`: both the rogue(unchained)/vigilante level floor below and
	randomize_level's own truncation of the pick list read it.

	THE LEVEL BELONGS IN THIS PHASE rather than in one of its own. `flaw_amount` is rolled here and
	crosses straight into `update_level`'s feat economy (flaw feats diminish, see
	level_and_bab.update_level) and nowhere else -- splitting the two would promote a local into a
	sixteenth exported attribute to serve exactly one reader.

	`provides` is exhaustive per ticket 05, with one honest weakness worth naming: `age`, `height`
	and `weight` are initialised to None in the constructor (createACharacter.py:167-169) and
	`deity_choice` is pre-set from `deity_flag` at the call site, so `hasattr` passes for those four
	whether this phase ran or not. They are declared anyway -- the check is weaker there, not absent,
	and a name left out of `provides` is invisible rather than merely unproven.
	'''
	# TRAP 1 -- the two alignment strings are NOT interchangeable. choose_alignment stores the
	# lowercased form on the character (the deity table is keyed that way, and spells.py:179
	# re-lowercases it deliberately); the payload exports the title-cased form. Both are live, so
	# each gets its own name rather than one being derived from the other at a distant call site.
	_alignment, mini_alignment = choose_alignment(character, 'alignments', alignment_input)
	character.alignment_display = _alignment.title()
	character.mini_alignment = mini_alignment

	# TRAP 2 -- `character.deity` is already taken, and not by this: it is the deity data TABLE
	# keyed by alignment (`self.deity[self.alignment]`). The chosen deity lives at
	# `character.deity_choice`, which randomize_deity both sets and returns; giving the choice an
	# attribute named `deity` would overwrite the table and break domain selection.
	if deity_flag.lower() == 'random':
		randomize_deity(character, random_flag=True)
	else:
		randomize_deity(character, random_flag=False, deity_choice=deity_flag)

	character.age = randomize_body_feature(character, 'age')
	character.height = randomize_body_feature(character, 'height')
	character.weight = randomize_body_feature(character, 'weight')

	# We don't use subrace data in foundryVTT (comment these out if we want to (will need to fix their issues first))
	# chosen_subrace, subrace_description = subrace_chooser(character)
	# race_traits_list, race_traits_description_list = race_traits_chooser(character)
	# split_race_traits_list = race_ability_split(character, race_traits_list)

	flaw_amount = randomize_flaw_amount()
	# Mechanical flaws replace the old personality-flaw strings: same 0-4 roll, but the
	# flaws now come from json/flaws/flaw_effects.json with pf1 changes/contextNotes
	# (1st flaw minor, 2nd major, extras 80% minor / 20% major).
	flaw_chooser(character, flaw_amount)		# sets character.flaw and character.flaw_effects
	character.background_traits = randomize_personality_attr(character, "background_traits",1,4)
	# TRAP 3 -- this roll's RESULT IS DEAD, and it is kept for its dice, not its value. The local it
	# used to fill was overwritten 240 lines later by phase_professions_and_skills, which returns
	# TRAINER professions; every reader downstream was reading that one. Deleting the call would
	# still be wrong -- it draws from the shared RNG, so removing it shifts every later roll and
	# changes the character. Dropping the flavour list is a behaviour change and belongs to the
	# class-choices work, not to a pure move.
	randomize_personality_attr(character, "professions",1, 3)
	character.mannerisms = randomize_personality_attr(character, "mannerisms",2,4)
	character.personality_traits = randomize_personality_attr(character, "personality_traits",3,6)
	# Flaws chosen earlier in it's own function

	# I don't know why, but these keep breaking the game (if low enough level and stats)
	if any(pick in ('rogue (unchained)', 'vigilante') for pick in character._class_picks):
		if low_level <= 1:
			low_level = 2
		if high_level <= 1:
			high_level = 2
	randomize_level(character, low_level, high_level, flaw_amount)


@phase(requires=['level', 'feat_amounts'], provides=['luck_stake', 'e_kat_feat_slots'])
def phase_luck_stake(character):
	'''Decide this character's INTENT toward luck, before a single budget has been allocated.

	Luck is bought (oks/pathfinder/house-rules/luck.md), and the three currencies it can be bought
	with here -- level-up attribute bumps, skill ranks, HP -- are all allocated by phases that run
	after this one. So this phase spends nothing. It records what the character wants, and each pool
	settles its own share at its own site (luck.settle), where the real budget is known and the
	house-rule floors can be respected.

	THE SPLIT IS NOT COSMETIC. A seller trades luck for feat slots, and feat slots have to exist
	before phase_feat_selection sizes its draw off character.feat_amounts. But the E-Kat feats feed
	luck BACK -- +1 per positive luck feat, +4 for Ass Pull / It Just Works / Luck God -- and which
	feats a character ends up with is not final until phase_feat_tax_and_swaps has had its say. One
	phase cannot be both before feat counting and after feat swapping, so there are two:
	this one, and phase_luck_resolution at the far end.

	requires `feat_amounts`: the seller's bonus slots are added to it here, so update_level must
	already have set the feat economy (phase_alignment_and_level).

	Gated on misc_homebrew_rules -- the house-rule catch-all, now an exposed input -- rather than on
	the feat flag. A character generated with house rules off carries NO luck state at all, rather
	than a half-built one; `provides` still holds because both attributes are set either way.
	'''
	character.luck_stake = None
	character.e_kat_feat_slots = 0
	if not misc_homebrew_enabled(character):
		return

	stake = luck.plan_stake(character.level, getattr(character, 'luck_direction', None))
	character.luck_stake = stake
	if not stake:
		return

	# "You may gain a feat for -5 luck." These are genuinely NEW slots -- the character sold
	# something for them -- unlike the E-Kat reservation below, which is carved out of the budget.
	#
	# BOTH budgets move, and that is not optional. `feat_amounts` is the pool the choosers draw
	# from, but `normal_feat_amount` is the GUARANTEE TARGET the final feat-count cap trims to
	# ("house rule: cap to exact"), and the two are documented as moving together so that
	# feat_amounts == normal + flaw + story + flavor stays true. Raising only the pool left the cap
	# unaware of the extra slots, so it trimmed them straight back off the tail -- and because the
	# profession/PoW reservations LOWER the target, a level-1 seller's target reached zero and the
	# cap wiped every general feat it had.
	character.feat_amounts += stake['bonus_feat_slots']
	character.normal_feat_amount += stake['bonus_feat_slots']

	# E-Kat feats are reachable only through reserved slots, and now for SELLERS TOO.
	#
	# Sellers used to be excluded here, for a reason a generated character had proved: one sold 2
	# luck for skill points, then drew Ass Pull and It Just Works and finished at +8. Selling was
	# free money, and "negative luck" was a label almost nothing wore. But the exclusion was the
	# wrong instrument -- it closed the loop by denying sellers the FEATS, which also denied them
	# the E-Kat reserve, which is the only currency Luck Traits can be bought with ("Luck Traits may
	# only be purchased with E-Kats"). The consequence was that all ten NEGATIVE Luck Traits were
	# unreachable by any generated character: eligible_luck_traits opens that category at score < 0,
	# and nothing could ever afford one.
	#
	# The loop is now closed at its source instead -- phase_luck_resolution credits a seller ZERO
	# luck from feats -- so the feats can come back without the free money coming with them. See the
	# suppression block there; the two are a pair, and neither is safe alone.
	# The reservation itself is taken in phase_feat_selection, out of the budget, not on top of it.
	if homebrew_enabled(character):
		character.e_kat_feat_slots = luck.e_kat_slots(character.level, len(e_kat_feat_table()))


@phase(requires=['level'], provides=['mythic_rank'])
def phase_mythic_stake(character):
	'''Resolve the mythic request into a tier, before a single budget has been allocated.

	Sits beside phase_luck_stake for the same reason luck's stake does: downstream phases size
	budgets off what the character IS, and mythic tier is part of that. trainers.py already reads
	character.mythic_rank into its slot formula (1 + hit_dice//3 + mythic_rank), and the mythic
	abilities phase will reserve feat-economy room the same way PoW does -- both need the tier to
	exist before they run, not while they run.

	THE INPUT IS THE GATE (ticket 02): character.mythic_request is the only source of mythic.
	Absent -> mythic_rank 0 and NO RNG draw, so every non-mythic generation -- which is every
	golden and every replayed seed that predates this phase -- is byte-identical by construction.
	'''
	if mythic.resolve_mythic_tier(character):
		# The parallel-axis schedule (ticket 03), loaded only when a tier exists: levels_for reads
		# it by attribute, and a non-mythic character deliberately has NO mythic state at all.
		character.mythic_schedule = mythic.mythic_schedule()


@phase(requires=['classes', 'mythic_rank', 'feats'], provides=['mythic_path'], returns=['mythic'])
def phase_mythic_abilities(character, pw, ft):
	'''The mythic build: path, tier-1 feature choice, per-tier path abilities, mythic feats.

	Runs LATE -- after phase_feat_tax_and_swaps -- for two reasons that are both about feats. The
	mythic feat allowance is SEPARATE from the feat economy (RAW: tiers 1/3/5/7/9, never an
	ordinary slot), so the grants append to ft.feats after the feat-count guarantee has already
	trimmed to target, exactly the profession-feat pattern -- the cap neither counts nor trims
	them. And mythic feats mostly require their non-mythic namesake (mythic Power Attack wants
	Power Attack), which is only knowable once the swaps have settled the final list.

	Path abilities land in data_dict['class features'] with owner `mythic` and TIER stamps
	(ticket 03), so both renderers show them through the machinery they already read; the `mythic`
	record this returns is chassis + provenance for the payload block.

	Descriptions register in pw.homebrew_feat_desc_dict (profession-feat precedent): the display
	names ("Dodge (Mythic)") deliberately match no data/feats.csv row -- that miss is what keeps
	the 139 name collisions out of every name-keyed lookup -- so the CSV backfill must never be
	their description source.
	'''
	character.mythic_path = None
	tier = getattr(character, 'mythic_rank', 0) or 0
	if not tier:
		return PhaseRecord(mythic=None)

	path_key, feature_choice = mythic.choose_mythic_path(character)
	character.mythic_path = path_key

	# Sphere masteries (house scope: sphere users only) are RAW universal path abilities, so they
	# join the CANDIDATE POOL of a sphere-using mythic character -- filtered to spheres actually
	# held -- rather than being a bonus grant. pw.spheres_chosen is PhaseRecord-only state, which
	# is why this phase takes pw explicitly.
	_sphere_names = [s.get('sphere') for s in (pw.spheres_chosen or []) if isinstance(s, dict)]
	mastery_pool = mythic.sphere_mastery_pool(_sphere_names)
	abilities = mythic.choose_path_abilities(character, path_key, tier, extra_pool=mastery_pool)
	mythic.record_mythic_choices(character, path_key, feature_choice, abilities, tier)

	# The tradition (house scope: EVERY mythic character rolls one; decaying counts, so none at
	# all is the common case). Rolled after the abilities so Mythic Exemplar can see what is
	# already taken.
	tradition = mythic.roll_mythic_tradition(character, tier, _sphere_names, path_key,
											 [a['name'] for a in abilities])
	mythic.record_tradition(character, tradition)

	feat_slot_tiers = levels_for(character, 'mythic', 'mythic_feats', tier,
								 schedule_attr='mythic_schedule')
	mythic_feats_granted = mythic.choose_mythic_feats(character, tier, feat_slot_tiers)
	ft.feats.extend(g['name'] for g in mythic_feats_granted)
	for g in mythic_feats_granted:
		pw.homebrew_feat_desc_dict[g['name']] = g['description']

	return PhaseRecord(mythic={
		'tier': tier,
		'path': path_key,
		'path_display': mythic.path_ability_data()[path_key]['display'],
		'tier1_feature': feature_choice,
		'path_abilities': abilities,
		'tradition': tradition,
		'mythic_feats': mythic_feats_granted,
	})


@phase(requires=['level', 'classes', 'chosen_race'], provides=['inherents', 'level_up_stats'])
def phase_roll_and_assign_stats(character, num_dice, num_sides, inherents):
	'''Roll the ability scores, fold in racial modifiers, and derive the modifiers.

	requires `level`: roll_stats rolls inherents and level-up bumps off TOTAL character level, so
	running this before randomize_level silently under-rolls both (it used to be a bare comment,
	"stats after level (because we roll inherents which depend on level)").
	requires `chosen_race`: apply_racial_stats reads the race's stat table.
	'''
	stats = roll_stats(character, num_dice, num_sides, inherents)
	# Racial modifiers go into the base scores here (before assign/mod/HP/spell
	# calcs) so they propagate everywhere; the split is exported as racial_stats.
	apply_racial_stats(character, stats)
	assign_stats(character, stats)
	calc_ability_mod(character)
	return stats


@phase(requires=['level', 'classes', 'stats'],
	   provides=['Hit_dice1', 'total_hp_rolls', 'sheet_health', 'Total_HP',
				 'spellbooks', 'spells_per_day_list', 'spells_known_list'])
def phase_hp_and_spellbooks(character):
	'''Hit points, then one independent spellbook per class.

	requires `stats`: total_hp_calc reads the FINAL Con score (final_ability_mod), so inherent
	bonuses and level-up bumps have to have landed -- running this before the stats phase gives
	every character the HP of a Con-10 one, silently and with no exception.
	requires `level` and `classes`: hit dice, HP and every caster formula are per-class-level.

	NO LOCALS CROSS OUT OF HERE, which is why this block is the third one done rather than the
	tenth. All three names that used to leave it were already aliases of character attributes --
	`total_rolled_hp` is `roll_hp`'s return value, which it sets as `total_hp_rolls` on the way past,
	and `day_list`/`known_list` were bare aliases bound one line after sync_legacy_spell_fields set
	them. Zero new attributes; the export just names the attribute instead of the alias.

	THE ALIASES ARE SAFE TO DROP ONLY BECAUSE THAT WAS MEASURED. `sync_legacy_spell_fields` runs a
	SECOND time much later, after the spell lists are deduped, and re-points the same two attributes
	-- so an alias captured here and an attribute read at export are not the same read, and a
	rebinding in between would have made this substitution a silent payload change. Checked by
	asserting the two agree at the export site across 68 classes at three levels: no drift, and the
	probe was confirmed able to fire before the result was believed.
	'''
	#hp calculations
	hit_dice_calc(character)
	roll_hp(character)
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


@phase(requires=['stats', 'bab_total', 'Total_HP', 'casting_level_num'],
	   provides=['skill_rank_level', 'chosen_school', 'chosen_opposing_school',
				 'archetype_info', 'archetypes_per_class', 'bloodline_sorc', 'bloodline_rager',
				 'chosen_bloodline', 'bonded_creatures', 'chosen_domain',
				 'animal_companion_feats'])
def phase_class_options(character):
	'''Every class-specific choice: schools, archetypes, bloodlines, domains, bonded creatures, and
	the thirty-odd option buckets the choosers fill.

	THE TWENTY-PLUS-`requires` CASE the ticket warned about -- and it did not turn out to be one. The
	block reads a great deal, but nearly all of it is state this block itself produced a few lines
	earlier. Ticket 05's test is "could a reordering make this absent?", not "does this code touch
	it?", and only four names answer yes.

	requires `stats`: chooseable_list_stats seeds the prerequisite strings ("str 13", "dex 15") that
	every talent pool is then filtered against, straight off the final ability scores. Run this before
	the stats phase and the pools silently narrow to whatever a blank character qualifies for -- no
	error, just a worse character.
	requires `bab_total` and `casting_level_num`: the same seeding, for the "base attack bonus +6" and
	"caster level 5th" prerequisite forms. `casting_level_num` is set by caster_formula, which makes
	the HP/spellbook phase a hard predecessor rather than a conventional one.
	requires `Total_HP`: favored_class_calculator does `character.Total_HP += character.level`. That
	is the one true write-after-write in the pipeline -- run the HP phase afterwards and the favoured
	class bonus is silently overwritten instead of loudly lost.

	EIGHT NAMES CROSS OUT, and this is where they get homes. Two already had one: `archetypes_per_class`
	was being written to the character mid-block anyway, and `full_domain` was a bare alias of
	`character.chosen_domain` -- safe to drop here because domain_chooser is its only writer and runs
	exactly once, which is precisely what was NOT true of the spell aliases in phase_hp_and_spellbooks.
	Identical code, opposite verdicts, and the discriminator is the WRITER COUNT rather than anything
	visible at the alias site -- so it is checked rather than remembered:
	`scripts/gates/validate_alias_invariants.py` fails if either call count moves.

	THREE LOCALS ARE DEAD and stay only for their draws: `favored_class_chosen` has no reader anywhere
	in the repo, and pre_oracle_mystery/oracle_mystery are consumed inside the block. The reason each
	survives is recorded AT the line, not here, because that is where someone will be standing when
	they consider deleting it.

	`chosen_school` IS SEEDED TO None ON PURPOSE. The local it replaces was conditionally bound --
	only a wizard ever reached the assignment -- which is why the export site read it inside a
	`try/except NameError`. An attribute cannot raise NameError, so those handlers were unreachable;
	they have since been deleted in their own commit, and the None seeding is what keeps the
	non-wizard path landing on "N/A" exactly as it did before. Removing the seeding would not raise
	either -- it would put `None` where "N/A" belongs, on the sheet, silently. That is why
	`chosen_school` and `chosen_opposing_school` are declared in `provides`.
	'''
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
	# `_favored_class_chosen` has NO reader anywhere in the repo -- it is unpacked and discarded. Do
	# not "clean up" by dropping the call: favored_class_calculator is what sets skill_rank_level and
	# does the `Total_HP += level` write-after-write this phase requires. Only the second element of
	# the tuple is dead, and it stays unpacked rather than becoming `_` so that the name still says
	# what was thrown away.
	character.skill_rank_level, _favored_class_chosen = favored_class_calculator(character, favored_class)

	# domain_chance still drives the inquisitor's inquisitions-vs-domains gate; the druid's
	# companion-vs-domain flip moved to the bonded-creature resolver (see below).
	domain_chance(character)
	versatile_perfomance(character)


	character.chosen_school = None
	character.chosen_opposing_school = None
	if any(c['name'] == 'wizard' for c in character.classes):
		character.chosen_school = wizard_school_chooser(character)
		character.chosen_opposing_school = wizard_opposing_school(character, character.chosen_school)

	character.archetype_info = character.archetype_data()
	# One archetype per rolled class for the Foundry module. The primary reuses the legacy pick
	# above (which also strips " (unchained)" off c_class for later data lookups), so
	# archetype_info and its class entry always agree; {} for classes with no archetypes.
	archetypes_per_class = [
		character.archetype_info if i == character.primary_class_index
		else character.archetype_data(entry['name'])
		for i, entry in enumerate(character.classes)]
	# The rolled archetypes join the prerequisite pool HERE, before the first chooser below, because
	# 144 of the hunter's aspects are gated on an archetype name and the prereq engine can already
	# check that -- it just never had the name. Anything after this line can see it; the choosers
	# start on the next line, so "before the choosers" and "after the archetypes are rolled" is a
	# one-line window.
	chooseable_list_archetypes(character, archetypes_per_class)

	# generic single choices (the choosers gate themselves on any matching class entry)
	character.bloodline_sorc = generic_class_option_chooser(character, "sorcerer", "bloodline")
	character.bloodline_rager = generic_class_option_chooser(character, "bloodrager", "bloodline")
	character.chosen_bloodline = (next(iter(character.bloodline_sorc), '')
								  if character.bloodline_sorc else '')

	# Bonded creatures, and the domains that are their alternative.
	#
	# This block CANNOT sit where the old druid-only check did (before domain_chooser, above).
	# The resolver reads the rolled archetype and the rolled sorcerer bloodline, and both are
	# chosen further down the pipeline than animal_chooser used to run -- archetypes just above,
	# the bloodline on the line before this one. #38 specified "run the resolver ahead of
	# domain_chooser"; that is still true, and both now run here instead.
	character.archetypes_per_class = archetypes_per_class
	resolve_bonded_creatures(character)
	domain_chooser(character)
	character.animal_companion_feats = companion_feats(character)
	# #31: the numbers, last -- the merge reads the post-stack chassis and the feats are already
	# on the entry by here. D14 makes that ordering load-bearing rather than incidental: the
	# stat block FOLDS the feats and flaws chosen on the line above, so it cannot run first.
	stat_bonded_creatures(character)

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
	
	# The patron -- a real 1st-level build choice that nothing made until class-choices ticket 02.
	# witch_patrons.json sat with no reader at all, and the witch's filled `hexes` row hid the gap,
	# which is why the sweep had to cover classes that already had buckets. Its spells DO join the
	# witch's list, level-gated, in phase_class_features_and_bonus_spells below -- closing the
	# "need to add patron spells to the witch spell list" TODO that lived on this line.
	generic_class_option_chooser(character,"witch", "patrons", dict_name = 'patron')
	generic_class_option_chooser(character,"witch", dataset_name="basic", dataset_name_2="greater", dataset_name_3="grand", multiple='yes', level=10, level_2=18, dict_name = 'hexes')

	generic_class_option_chooser(character,"shaman", "spirits", dict_name = 'spirits')
	generic_class_option_chooser(character,"shaman", dataset_name="hexes", dataset_name_2 = "basic", multiple='yes', alternate_dataset = True, level = 99, dict_name = 'hexes')

	# Psionics subsystems (ticket 08). Nine of the twelve classes carry a choice-bearing
	# subsystem and every one of them is the same shape the choosers above already handle --
	# pick 1 or N from a {name: description} list -- so no new chooser module exists. The pick
	# schedules live in data.amount; the option lists are generated per class by
	# Backend/scripts/build_psionic_class_data.py. The voyager is absent on purpose (its
	# Voyager Knowledge feature grants bonus feats, not options) and so is the wilder, which
	# chooses powers rather than a subsystem.
	#
	# The psion was in that "chooses powers" list too, and should not have been (class-choices
	# ticket 02). Its discipline is a real 1st-level pick, and not a cosmetic one: the discipline
	# decides which powers are legal, so a psion that never chose one had 39 powers nothing could
	# check. The pool is derived from psionic_powers.json's own discipline tags by
	# build_psionic_class_data.py, so the pick and the powers it gates read one source.
	generic_class_option_chooser(character, "psion", "disciplines", dict_name = 'psion_discipline')
	generic_class_option_chooser(character, "vitalist", "methods", dict_name = 'vitalist_method')
	generic_class_option_chooser(character, "psychic warrior", "warrior paths", dict_name = 'warrior_path')
	generic_class_option_chooser(character, "marksman", "combat styles", dict_name = 'combat_style')
	generic_class_option_chooser(character, "aegis", dataset_name="customizations", multiple='yes', dict_name = 'customizations')
	generic_class_option_chooser(character, "cryptic", dataset_name="insights", multiple='yes', dict_name = 'insights')
	generic_class_option_chooser(character, "dread", dataset_name="terrors", multiple='yes', dict_name = 'terrors')
	generic_class_option_chooser(character, "highlord", dataset_name="decrees", multiple='yes', dict_name = 'decrees')
	generic_class_option_chooser(character, "soulknife", dataset_name="blade skills", multiple='yes', dict_name = 'blade_skills')
	generic_class_option_chooser(character, "tactician", dataset_name="strategies", multiple='yes', dict_name = 'strategies')

	# Occult Adventures subsystems (class-pool map, ticket 03). Every one of them is the same
	# "pick 1 or N from a {name: description} list" the choosers above already handle, so no
	# new chooser module exists here either. Option lists are generated per class by
	# Backend/scripts/build_occult_class_data.py; the multi-pick schedules live in data.amount.
	#
	# Two subsystems DEGRADE rather than being modelled, per section 10:
	#   kineticist burn -- an HP-priced resource with no analogue in the generator. Its wild
	#       talents and infusions are still picked; burn is described, never tracked.
	#   medium spirit   -- a *daily* choice, and the generator emits a static snapshot. Rolling
	#       one seance and freezing it is a house ruling, recorded as such.
	generic_class_option_chooser(character, "occultist", dataset_name="implements", multiple='yes', dict_name = 'implements')
	generic_class_option_chooser(character, "occultist", dataset_name="focus powers", multiple='yes', dict_name = 'focus_powers')
	generic_class_option_chooser(character, "kineticist", "elemental focus", dict_name = 'elemental_focus')
	generic_class_option_chooser(character, "kineticist", dataset_name="wild talents", multiple='yes', dict_name = 'wild_talents')
	generic_class_option_chooser(character, "kineticist", dataset_name="infusions", multiple='yes', dict_name = 'infusions')
	# 'medium_spirit', not 'spirit': the shaman already owns a bucket called 'spirits', and two
	# buckets one letter apart is a trap for every renderer that has to register them by name.
	generic_class_option_chooser(character, "medium", "spirits", dict_name = 'medium_spirit')
	generic_class_option_chooser(character, "mesmerist", dataset_name="mesmerist tricks", multiple='yes', dict_name = 'mesmerist_tricks')
	generic_class_option_chooser(character, "mesmerist", dataset_name="bold stare", multiple='yes', dict_name = 'bold_stare')
	generic_class_option_chooser(character, "psychic", "disciplines", dict_name = 'psychic_discipline')
	generic_class_option_chooser(character, "psychic", dataset_name="phrenic amplifications", multiple='yes', dict_name = 'phrenic_amplifications')
	generic_class_option_chooser(character, "spiritualist", "emotional focus", dict_name = 'emotional_focus')

	# Paizo collab classes (class-choices ticket 02). Both were generating NOTHING: their defining
	# choice existed only as prose in class_data.json naming options the repo did not have. The
	# pools are harvested by Backend/scripts/build/build_collab_class_options.py.
	#
	# The vampire hunter is the only one of the seven gaps that is NOT a single pick -- its own
	# rules text says "at 8th and 16th level, the vampire hunter learns an additional vampiric
	# focus", so the schedule is [1, 8, 16].
	generic_class_option_chooser(character, "vampire hunter", dataset_name="vampiric foci", multiple='yes', dict_name = 'vampiric_foci')
	# The omdura's invocation is a PER-USE choice -- she re-selects a type every time she calls the
	# power, and may swap it as a swift action. The generator emits a static snapshot, so one is
	# rolled and frozen, exactly as the medium's daily seance already is (section 10). Ticket 02
	# made that the general rule rather than the medium's one-off.
	generic_class_option_chooser(character, "omdura", "invocations", dict_name = 'invocation')



	# generic multi choices (with pre-reqs)
	get_data_without_prerequisites(character, class_1="rogue",dataset_name="basic", level=10, dataset_name_2="advanced", dict_name = 'rogue_talents')
	get_data_without_prerequisites(character, class_1="ninja",dataset_name="basic", level=10, dataset_name_2="advanced", dict_name = 'ninja_talents')
	get_data_without_prerequisites(character, class_1="slayer",dataset_name="basic", level=10, dataset_name_2="advanced", dict_name = 'slayer_talents')
	get_data_without_prerequisites(character, class_1="alchemist",dataset_name="basic", dict_name = 'discoveries')
	get_data_without_prerequisites(character, class_1="investigator",dataset_name="basic", dict_name = 'investigator_talents')
	get_data_without_prerequisites(character, class_1="vigilante",dataset_name="basic", dict_name = 'vigilante_talents')
	get_data_without_prerequisites(character, class_1="vigilante",dataset_name="social", dict_name = 'social_talents')
	get_data_without_prerequisites(character, class_1="barbarian",dataset_name="basic", dict_name = 'rage_powers')
	get_data_without_prerequisites(character, class_1="skald",dataset_name="basic", dict_name = 'rage_powers')
	get_data_without_prerequisites(character, class_1="magus",dataset_name="basic", dict_name = 'arcana')
	# Animal Focus. PREREQUISITE-AWARE on purpose, which is why it sits with the talent choosers
	# rather than the single-pick ones above: 143 of the hunter's 155 aspects are gated on an
	# archetype, named in the option's own `prerequisites`, and chooseable_list_archetypes seeds
	# the rolled archetypes so no_prereq_loop can honour that. A plain hunter therefore draws from
	# the 12 base aspects and a Verminous Hunter also reaches its own.
	#
	# Two picks, both at 1st, and both frozen: the aspect is re-chosen per use, but the hunter
	# applies one to HERSELF and one to her ANIMAL COMPANION, so a snapshot legitimately holds two.
	get_data_without_prerequisites(character, class_1="hunter", dataset_name="aspects", dict_name = 'animal_focus')
	# Shifter aspects -- the class's defining feature, and unlike the hunter's these are a PERMANENT
	# build choice rather than a per-use one, so nothing is frozen here. Also prerequisite-aware:
	# three of the 27 (dragon, fey, swarm) are archetype-only, and the pool records that as a real
	# `prerequisites` field so the same engine gates them.
	get_data_without_prerequisites(character, class_1="shifter", dataset_name="aspects", dict_name = 'shifter_aspects')

	grand_discovery_chooser(character) #fix this later

	# Adding class specific feats


	# >2 Choices based on level
	generic_multi_chooser(character,"paladin", "mercy")
	generic_multi_chooser(character,"antipaladin", "cruelty")
	ki_powers = generic_multi_chooser(character,"monk", "ki_powers")


	# feat + spell searcher
	feat_spell_searcher(character, "monk", ki_powers, "feats", "benefit")
	feat_spell_searcher(character, "monk", ki_powers, "spells", "description")
	feat_spell_searcher(character, "bloodrager", character.bonus_feats , "feats", "benefit")
	# feat_spell_searcher(character, "bloodrager", character.bonus_spells, "spells", "description")
	# feat_spell_searcher(character, "sorcerer", character.bonus_spells, "spells", "description")

	# Choosing guns for gunslinger
	choose_gun_func(character, character.c_class)


@phase(requires=['level', 'classes', 'class_data', 'craft_chosen'],
	   provides=['profession_data', 'profession_feats', 'skill_rank_budget'])
def phase_professions_and_skills(character, truly_random_feats, skill_rank_level, professions_enabled=True):
	'''Professions sub-system, then ordinary skill ranks, then fold one back into the other.

	The order inside here is the constraint: ordinary skill ranks may only be spent in a Profession
	when the character has the 'Always Improving' profession feat, and skill_ranks.has_always_improving
	reads character.profession_feats -- which only profession_chooser sets. Run the other way round
	and the gate reads an unset attribute, silently allocating zero Profession ranks.

	`professions_enabled=False` is the client's opt-out. It skips ONLY profession_chooser, never the
	whole phase: skills_selector still has to run, and it reads the same profession attributes through
	has_always_improving -- so they are zeroed here rather than left unset, which is also what this
	phase's declared `provides` requires.

	requires `craft_chosen`: a profession can be themed around the character's Craft specialization.
	'''
	# Rank pool is 5 + level + 10/Multi-Talented feat. Returns the legacy list of profession names;
	# the rich data and the profession feats are recorded on the character.
	if professions_enabled:
		professions = profession_chooser(character, "professions", truly_random_feats)
	else:
		professions = []
		character.profession_chosen = []
		character.profession_data = []
		character.profession_feats = []
		character.profession_feat_desc = {}
		character.profession_pool = 0
	skill_ranks = skills_selector(character, 'skills', skill_rank_level)
	# ... and the ranks that DID go to Profession are folded back onto the professions themselves.
	apply_always_improving_ranks(character, skill_ranks)
	return professions, skill_ranks


@phase(requires=['armor_type', 'gold'],
	   provides=['armor_dict', 'weapon_type', 'weapon_dict', 'shield_flag', 'shield_dict',
				 'mind_blade'],
	   returns=['weapon_name', 'equipment_list', 'equip_descrip', 'armor_ac', 'shield_ac',
				'weapon_enhancement_chosen_list', 'weapon_enhancement_bonus',
				'armor_enhancement_chosen_list', 'armor_enhancement_bonus',
				'shield_enhancement_chosen_list', 'shield_enhancement_bonus'])
def phase_gear_and_equipment(character):
	'''Pick what the character wears and carries, then spend the purse on it.

	The order inside here is the constraint, and it is one the file already got wrong once:
	`item_chooser` used to run before `plan_enhancements` and drained the purse, so no character
	could ever afford an enhancement tier and enhancement_effects_dict was empty for every
	realistically funded NPC. Enhancements now take their reserved share FIRST and ordinary gear
	spends what is left. `shield_flag` has to be known before that split, so a shieldless character
	is charged nothing for a shield.

	requires `armor_type` (armor_chooser sets it, and list_selection limits on it) and `gold`
	(assign_gold fills the purse every spender below draws down).
	'''
	character.armor_dict = list_selection(character, 'armor', limits=character.armor_type)

	# required to set up weapon_type
	weapon_chooser(character)
	character.weapon_dict = list_selection(character, 'weapons_data', limits=character.weapon_type)

	weapon_name = list(character.weapon_dict.keys())[0]
	limits = shield_chooser(character, character.weapon_dict)
	character.shield_flag = shield_flag_func(character, limits=limits)
	# OPTIMIZED MODE (V4 wall pass, 2026-08-13): the one_handed_shield weapon policy PROMISES a
	# shield -- but shield_chooser only returns on its Tower branch and shield_flag_func
	# mutates-then-returns None, so in fact NO character has ever worn one (every golden:
	# shield_ac 0, shield_flag None). The global fix moves every random golden and is a ruling
	# for Daniel (ticketed as a live finding); HERE the promise is kept only for the roles that
	# declared it, which no golden pins. Guarded off two-handed/ranged draws the policy fallback
	# can still produce.
	_shield_role = getattr(character, 'role', None)
	if (_shield_role and _shield_role.get('weapon_policy') == 'one_handed_shield'
			and not any(_w in str((_e or {}).get('category') or '')
						for _e in (character.weapon_dict or {}).values()
						for _w in ('Two-Handed', 'Ranged'))):
		limits = limits or 'Shield'
		character.shield_flag = True
	character.shield_dict = list_selection(character, 'armor', limits=limits, shield_flag = character.shield_flag)

	# Magic enhancements get first claim on a reserved share of the purse (utils/class_func/
	# armor_and_enhancements.py: ENHANCEMENT_SHARE / ENHANCEMENT_SPLIT). Runs here, after
	# shield_flag is known, so a shieldless character is charged nothing for a shield.
	_enhancements = plan_enhancements(character)
	armor_enhancement = _enhancements['armor']
	weapon_enhancement = _enhancements['weapon']
	shield_enhancement = _enhancements['shield']

	# ... and ordinary gear spends whatever is left.
	# Pre-loading JSON data (so we only do it 1x per item and not multiple times)
	# Open JSON file to see if name is in that list, otherwise reroll and document
	# This breaks perm server if Double \\
	foundry_item_names = character.foundry_item_names
	equipment_list, equip_descrip = item_chooser(character, foundry_item_names)

	armor_ac = ac_bonus_calculator(character, character.armor_dict)
	shield_ac = ac_bonus_calculator(character, character.shield_dict)

	weapon_type_flag = weapon_type_flag_func(character, character.weapon_dict)

	weapon_enhancement_chosen_list, weapon_enhancement_bonus = enhancement_chooser(character, character.weapon_qualities,weapon_enhancement, weapon_type_flag)

	# The soulknife wields a mind blade, which is a weapon SHAPE rather than a purchase: the
	# rolled weapon keeps its damage dice, crit range and groups, but it is renamed for what it
	# is and its enhancement bonus comes from the class table. The class table REPLACES the
	# purse's number rather than raising it -- a mind blade is manifested, not bought, so no
	# amount of gold buys a +5 one at 1st level. The special abilities enhancement_chooser
	# picked still stand: that is the Enhanced Mind Blade feature spending its own grant.
	_mind_blade = mind_blade(character, melee=(weapon_type_flag == 'Melee'))
	# Stashed for choose_psionics_attr further down, which puts it on the soulknife's manifester
	# entry. Passed rather than recomputed so the equipped weapon and the psionics tab cannot
	# disagree about which blade this is.
	character.mind_blade = _mind_blade
	if _mind_blade:
		weapon_name = _mind_blade['name']
		weapon_enhancement_bonus = _mind_blade['max_enhancement_bonus']
	armor_enhancement_chosen_list, armor_enhancement_bonus = enhancement_chooser(character, character.armor_qualities,armor_enhancement, 'Armor')
	shield_enhancement_chosen_list, shield_enhancement_bonus = enhancement_chooser(character, character.armor_qualities,shield_enhancement, 'Shield', character.shield_flag)

	return PhaseRecord(
		weapon_name=weapon_name,
		equipment_list=equipment_list,
		equip_descrip=equip_descrip,
		armor_ac=armor_ac,
		shield_ac=shield_ac,
		weapon_enhancement_chosen_list=weapon_enhancement_chosen_list,
		weapon_enhancement_bonus=weapon_enhancement_bonus,
		armor_enhancement_chosen_list=armor_enhancement_chosen_list,
		armor_enhancement_bonus=armor_enhancement_bonus,
		shield_enhancement_chosen_list=shield_enhancement_chosen_list,
		shield_enhancement_bonus=shield_enhancement_bonus,
	)


@phase(requires=['chosen_race', 'skill_rank_budget'],
	   returns=['selected_traits', 'hero_points', 'hair_color', 'hair_type', 'eye_color',
				'appearance', 'language_text'])
def phase_appearance_and_traits(character, skill_ranks):
	'''The flavour rolls: traits, hero points, colouring, and the languages the character speaks.

	Nothing downstream branches on any of this -- every output is read once, by the export. That is
	precisely why it is a record rather than seven more character attributes.

	These are RNG draws, so this phase's position in the file is load-bearing in a way its
	`requires` cannot express: moving it changes the draw order and every golden fixture with it.
	What `requires` CAN express is the one real dependency -- language_chooser is handed the skill
	ranks, so `skill_rank_budget` (which only phase_professions_and_skills sets) forces this to run
	after the skills are spent. Without it, the languages are chosen against an empty rank sheet.

	requires `chosen_race`: the appearance tables and the racial language list are keyed by race.
	'''
	selected_traits = trait_selector(character, 8)
	# pre export data manip start
	hero_points = hero_point_generator()


	hair_color = randomize_apperance_attr(character, "hair_colors")
	hair_type = randomize_apperance_attr(character, "hair_types")
	eye_color = randomize_apperance_attr(character, "eye_colors")
	appearance = randomize_apperance_attr(character, "appearance")
	language_text = language_chooser(character, skill_ranks)
	return PhaseRecord(
		selected_traits=selected_traits,
		hero_points=hero_points,
		hair_color=hair_color,
		hair_type=hair_type,
		eye_color=eye_color,
		appearance=appearance,
		language_text=language_text,
	)


@phase(requires=['classes', 'chosen_race'],
	   returns=['class_ability', 'class_ability_desc', 'older_brothers', 'younger_brothers',
				'older_sisters', 'younger_sisters', 'parents'])
def phase_class_abilities_and_family(character):
	'''The class-ability summary and the family the character was born into.

	Two adjacent things that share one property: both are read ONLY by the export, so neither is
	character state. The class-ability text is a rendering of `character.classes` rather than a
	choice, and the siblings/parents are flavour rolls nothing downstream branches on.

	`actual_class_abilities` stays a local -- it is the raw lookup that feeds the description call
	two lines later and has no reader outside this phase.
	'''
	actual_class_abilities = get_class_abilities(character)
	class_ability_desc, class_ability =get_class_abilties_desc(character, actual_class_abilities)

	older_brothers, younger_brothers, older_sisters, younger_sisters = randomize_siblings(character)
	parents = randomize_parents(character)
	return PhaseRecord(
		class_ability=class_ability,
		class_ability_desc=class_ability_desc,
		older_brothers=older_brothers,
		younger_brothers=younger_brothers,
		older_sisters=older_sisters,
		younger_sisters=younger_sisters,
		parents=parents,
	)


@phase(requires=['bloodline_sorc', 'bloodline_rager'], provides=['bloodline'])
def phase_bloodline_resolution(character):
	'''Collapse whichever bloodline table was filled into the one name the rest of the run uses.

	`phase_class_options` sets `bloodline_sorc` OR `bloodline_rager` (or neither); this reduces them
	to a single `character.bloodline` string, defaulting to "N/A". It has to run before
	`phase_class_bonus_feats`, whose bonus-feat list is drawn from that name -- and that ordering is
	a contract rather than a comment because getting it wrong does not raise: the list comes back
	empty and the refund silently converts the unfilled slots into ordinary feats.

	The `except (NameError, AttributeError)` is NOT the dead kind that was removed from the school
	reads. `bloodline_sorc`/`bloodline_rager` are only set for bloodline classes, so the
	AttributeError arm is live for everyone else -- which is exactly why both names are declared in
	`requires`, so a reordering fails loudly instead of falling into that arm and reading "N/A".
	'''
	try:
		if character.bloodline_sorc:
			bloodline_full = character.bloodline_sorc
			bloodline = next(iter(bloodline_full.keys()), "N/A")
		elif character.bloodline_rager:
			bloodline_full = character.bloodline_rager
			bloodline = next(iter(bloodline_full.keys()), "N/A")
		else:
			bloodline = "N/A"

	except (NameError, AttributeError):
		bloodline = "N/A"

	character.bloodline = bloodline


@phase(requires=['bab_total', 'bloodline', 'feat_amounts'],
	   provides=['teamwork_feats', 'combat_feats'],
	   returns=['bloodline_feats', 'bloodline_feat_labels', 'ranger_style_feats',
				'monk_bonus_feats'])
def phase_class_bonus_feats(character):
	'''The feats a class GRANTS, as opposed to the ones the character chooses.

	Everything here runs before the normal-feat selection, and the order is the whole point: the
	granted picks are registered in `character.chooseable` first, so no_prereq_loop skips them and
	the general pool cannot re-pick the same feat (duplicate Weapon Focus), while the feat-tax
	engine still sees them as owned.

	requires `bloodline`: the bonus-feat list is the bloodline's own, so running before the
	bloodline is resolved silently hands a Sorcerer an empty list -- and the refund below then
	quietly converts every unfilled slot into an ordinary feat, so the count still looks right.

	requires `feat_amounts` because this phase REFUNDS into it: a bonus list too short to fill its
	granted slots gives those slots back to the normal track. See ticket 08 -- the budget is
	mutated from six places and this is two of them.
	'''
	# Campaign feat-tax rule (homebrew_rules.md 4): Combat Expertise / Power Attack / Deadly Aim /
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
	return PhaseRecord(
		bloodline_feats=bloodline_feats,
		bloodline_feat_labels=bloodline_feat_labels,
		ranger_style_feats=ranger_style_feats,
		monk_bonus_feats=monk_bonus_feats,
	)


@phase(requires=['classes', 'bab_total', 'feat_amounts', 'profession_feats'],
	   provides=['path_of_war_paths', 'sphere_count', 'spheres_flag'],
	   returns=['_pow_funded_n', '_pow_mentor_feats', '_pow_mentor_names', '_sphere_mentor_talents', 'casting_tradition', 'combat_talent_items', 'dedicated_trainer_specs', 'homebrew_feat_desc_dict', 'initiation_stat', 'initiator_level', 'magic_talent_items', 'maneuvers_choose_from', 'maneuvers_desc_dict', 'maneuvers_known_list', 'maneuvers_readied_list', 'maneuvers_readied_names', 'manifesters', 'martial_disciplines', 'mt_feat_tax', 'mt_feats', 'powers_desc_dict', 'sphere_boons', 'sphere_counts', 'sphere_drawbacks', 'sphere_feat_tax', 'sphere_feats', 'sphere_mana_pool', 'sphere_traits', 'spheres_chosen', 'stances_chosen', 'style_feat_tax', 'style_feats'])
def phase_path_of_war_and_spheres(character, spheres_flag, trainers_enabled):
	'''Path of War, psionics and Spheres of Power -- the three homebrew subsystems, and the
	feat-budget reservation that pays for all of them.

	This is the block ticket 08 is about. It rolls each system's desired size, decides how much of
	that the character can actually afford, and then RESERVES the cost out of `character.feat_amounts`
	through a `max(0, ...)` that clamps silently when the reservation exceeds the budget.
	`scripts/tests/test_feat_budget.py` is what makes that clamp audible; see ticket 08 for why the
	arithmetic was left alone rather than replaced with a FeatBudget object.

	Thirty-two values cross out of here and not one of them is character state -- they are the
	subsystem bundles the export and the feat-tax block read. That is why they ride a record: as
	character attributes they would be thirty-two more names on an object already carrying ~200, and
	as a tuple they would be thirty-two positions nobody can read.

	requires `profession_feats` because the reservation subtracts them, so running this before
	`phase_professions_and_skills` would reserve nothing for professions and over-fill the feat track.
	requires `feat_amounts` for the same reason `phase_class_bonus_feats` does: this phase mutates the
	budget rather than merely reading it.
	'''
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
	_sphere_mentor_cal, _pow_mentor_cal, _overflow_n, _priority_reserve, _mentor_talents_n = 0, 0, 0, 0, 0
	realize_pow, realize_style, realize_sphere = desired_pow, desired_style, desired_sphere
	if selected_amount > 0:
		_half = (selected_amount + 1) // 2          # ceil(selected_amount / 2)
		# The draw happens even when trainers are switched off, so a replayed seed still lines up
		# with the same character minus its mentors; opting out just lands in the ordinary 75%
		# branch, where the character funds this training out of the normal feat budget. Gating
		# here rather than only at select_trainer_feats is what makes "Trainers: No" mean it --
		# these mentors render as "(Trainer N - Path of War)" / "(Trainer N - Spheres)" rows too.
		if random.random() < 0.25 and trainers_enabled:
			# "trainer-backed": ONE dedicated mentor PER SYSTEM the character actually has content in,
			# each rolling its own caliber 1-4 (8/45/45/2). A mentor funds `caliber` FEATS' worth of the
			# training that lies beyond the character's own half-share -- 2*caliber sphere talents (capped
			# at the flat-8, so total talents never bloat) or `caliber` Martial Training / style feats.
			# Whatever it funds leaves the normal feat track and renders under its own "(Trainer N)" slot
			# instead, so a funded feat is never listed twice. Rolling per system is what finally lets a
			# pure-martial NPC have a mentor at all: the old single roll was spent raising the PoW
			# realization while line ~848 still billed the character for it, then suppressed itself.
			_sphere_mentor_cal = roll_caliber() if desired_sphere > 0 else 0
			_pow_mentor_cal = roll_caliber() if (desired_pow + desired_style) > 0 else 0
			_mentor_talents_n = 2 * _sphere_mentor_cal
		realize_total = _half
		_priority_reserve = _half                       # the budget-funded portion (mentor funding is off-budget)
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
		# The PoW mentor tops up ITS OWN system beyond that half-share (the Spheres Mentor's capacity
		# rides `_mentor_talents_n` instead -- sphere talents are a flat 8 either way, so its caliber
		# only moves who pays). Non-initiator capacity buys WHOLE chains: a part-paid chain grants
		# nothing, so `caliber % paid_per_chain` falls through to refunding already-realized feats
		# below. Initiator style bases cost one feat each, so they top up one at a time.
		if _pow_mentor_cal:
			if _is_initiator:
				realize_style = min(desired_style, realize_style + _pow_mentor_cal)
			elif _paid_per_chain:
				realize_pow = min(desired_pow, realize_pow + (_pow_mentor_cal // _paid_per_chain) * _paid_per_chain)
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
	# Psionics rides alongside Path of War rather than inside it: the two systems are
	# independent, and a character can be an initiator, a manifester, both or neither. The
	# bundle is empty for a non-manifester, so this is unconditional.
	psionics_data           = choose_psionics_attr(character)
	manifesters             = psionics_data['manifesters']
	powers_desc_dict        = psionics_data['powers_desc_dict']
	style_feats             = pow_data['style_feats']
	style_feat_tax          = pow_data['style_feat_tax']
	homebrew_feat_desc_dict = pow_data['homebrew_feat_desc_dict']
	# Cap initiator style chains to the realized amount decided by the guarantee block above
	# (PoW maneuvers are class-free; only the feat-funded style bases are scaled). Non-initiators
	# have no style feats. The feat-budget reservation now happens after the Spheres section.
	style_feats = style_feats[:realize_style]
	style_feat_tax = {k: v for k, v in style_feat_tax.items() if k in style_feats}
	# Which PoW feats the mentor paid for. Chains / style bases are realized in order, so the TRAILING
	# ones are precisely what its capacity bought; once the top-up is exhausted the leftover caliber
	# keeps paying, refunding feats the character's own half-share had realized (mirroring the Spheres
	# Mentor, which at caliber 4 funds all 8 talents and leaves the character paying for none). Capped
	# at the PoW that actually exists. These feats stay OUT of the normal feat track from here on:
	# they are excluded from the budget reservation and from `feats`, and render under the mentor's
	# "(Trainer N - Path of War)" label instead, so the freed slots refill with ordinary feats.
	_pow_all_feats = mt_feats + style_feats
	_pow_funded_n = min(_pow_mentor_cal, len(_pow_all_feats))
	_pow_mentor_feats = _pow_all_feats[len(_pow_all_feats) - _pow_funded_n:] if _pow_funded_n else []
	_pow_mentor_names = set(_pow_mentor_feats)

# ------------------- Spheres (Power / Might) section -------------------#
	# Build the spheres: a LEVEL-SCALED roll of talents (spheres.roll_talent_budget) plus a feat slot
	# per BUDGET-PAID talent (Extra Talent feats, 2 talents each, HR1). The flat 8 this replaces was a
	# testing convenience: it gave a 1st-level character the same eight talents as a 20th, which cost
	# more feats than a 1st-level budget holds -- the over-commit ticket 08 measured.
	#
	# THE RULE IS "NO FREEBIES": every talent is paid for, by the feat budget or by a Spheres Mentor.
	# What the character cannot fund is not granted, it is dropped. Three levers, applied in order:
	#
	#   1. What is left of the feat budget after PoW and professions have taken their share. This is
	#      the same arithmetic the reservation below performs, computed BEFORE the talents are picked
	#      instead of after -- which is the whole fix. The guarantee block already worked out what the
	#      character could afford; nothing ever passed it to the sphere builder.
	#   2. No trainers (trainers_flag != Y) -> a mentor cannot be forced, so the roll HALVES. With
	#      trainers on, a mentor is forced when the budget alone cannot cover the roll.
	#   3. No feat taxing (homebrew_feat_amount = N) -> the character has no creation/story/flavour
	#      feats to spend, so the roll HALVES again. Neither lever -> quartered, as two halvings.
	_sphere_affordable = max(0, character.feat_amounts
							 - (len(mt_feats) + len(style_feats) - _pow_funded_n)
							 - len(getattr(character, 'profession_feats', []) or []))
	_talent_roll = roll_talent_budget(character.level)
	_feat_tax_on = str(getattr(character, 'homebrew_feat_amount', 'Y')) not in ('N', 'n')
	if not trainers_enabled:
		_talent_roll //= 2
	if not _feat_tax_on:
		_talent_roll //= 2
	# V4 wall pass: the full-house wall's defensive sphere is by design, and a sphere with zero
	# talents is an empty grant -- floor the roll at 2 (one Extra Combat Talent feat's worth), so
	# the sphere always arrives with content. Only this population; every other roll is untouched.
	_role = getattr(character, 'role', None)
	if (_role and _role.get('_house') and 'ac_combat' in (_role.get('primaries') or [])):
		_talent_roll = max(_talent_roll, 2)
	# A mentor is forced only to cover a shortfall the budget genuinely cannot meet. `_sphere_mentor_cal`
	# may already be set by the 25% trainer-backed branch above; forcing raises it rather than replacing
	# it, and it stays inside the 1-4 caliber range a mentor can roll.
	_talents_from_budget = 2 * _sphere_affordable - 1 if _sphere_affordable else 0
	if _talent_roll > _talents_from_budget and trainers_enabled:
		_needed = _talent_roll - max(0, _talents_from_budget)
		_sphere_mentor_cal = max(_sphere_mentor_cal, min(4, -(-_needed // 2)))
		_mentor_talents_n = 2 * _sphere_mentor_cal
	sphere_data          = choose_spheres_attr(character, trainer_backed=bool(_sphere_mentor_cal),
											   mentor_talents=_mentor_talents_n,
											   talent_budget=_talent_roll,
											   max_budget_feats=_sphere_affordable)
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
	# 25% "trainer-backed" branch: the dedicated mentors, rendered in the Trainers block. The Spheres
	# Mentor needs a NAMED row of its own because the talents it funded render elsewhere (the magic /
	# combat talent sections), so this row is the only record of who paid for them. The PoW mentor
	# gets no such row -- its funded Martial Training / style feats ARE its content and render as its
	# "(Trainer N - Path of War)" group below, so a header row would be the content-free mentor this
	# block has always refused to emit.
	dedicated_trainer_specs = []
	_sphere_mentor_talents = []
	if _sphere_mentor_cal:
		_overflow_talent_items = []
		if _overflow_n > 0 and sphere_data.get('_chosen'):
			_ov_magic, _ov_combat = add_overflow_talents(
				character, sphere_data['_chosen'], sphere_data['_counts'], _overflow_n)
			magic_talent_items = magic_talent_items + _ov_magic
			combat_talent_items = combat_talent_items + _ov_combat
			_overflow_talent_items = _ov_magic + _ov_combat
		# Off-budget talents the mentor funded (the non-budget-paid flat-8 portion = 2*caliber) -> HR1
		# Extra-Talent feats + the talent names (user's requested format). Only emit a Spheres Mentor
		# when it actually funded something off-budget; otherwise there is nothing for it to teach.
		# Never pad to a fixed count and never add a content-free fallback mentor: a dedicated trainer
		# that funded nothing would render as a blank "(Continued Study)" / generic slot.
		_sphere_mentor_talents = list(sphere_data.get('mentor_funded_talents', [])) + _overflow_talent_items
		if _sphere_mentor_talents:
			dedicated_trainer_specs = [("Spheres Mentor", mentor_sphere_summary(spheres_chosen, _sphere_mentor_talents))]
	# Priority funding (reserve EXACTLY the homebrew feats that get appended into the normal feat
	# list, so each one REPLACES a normal feat -- the "consume feat budget" house rule -- and the
	# track lands at precisely normal_feat_amount). Those appended feats are: paid Martial Training
	# picks (mt_feats) + initiator style-chain bases (style_feats), both extended into `feats` just
	# below, and the budget-paid sphere Extra-Talent / magic bonus feats (sphere_feats) appended
	# after the feat-tax pass. The previous formula reserved a proportional roll-estimate
	# (_priority_reserve + max(0, sphere_feat_budget_count - realize_sphere)) that drifted off this
	# true count: over-reserving silently dropped the top "(Feat N)" slots (the "missing feats"
	# bug), under-reserving spilled feats past the character's top level. Sphere-mentor funding is
	# already off-budget (those talents produce no Extra-Talent feat at all, so they are not in
	# sphere_feats); PoW-mentor funding needs the explicit `_pow_funded_n` term because those feats
	# DO exist -- they just move to the mentor's trainer group instead of the normal track, which is
	# exactly what hands the character back that many ordinary feat slots.
	_prof_feat_n = len(getattr(character, 'profession_feats', []) or [])
	character.feat_amounts = max(0, character.feat_amounts - (len(mt_feats) + len(style_feats) - _pow_funded_n)
								 - len(sphere_feats) - _prof_feat_n)
	# Profession feats (True Calling / Multi Talented / Always Improving) are appended into the feat
	# list AFTER the feat-count guarantee, so -- unlike the homebrew feats above -- they can't be
	# trimmed to fit. Reserve their slots by ALSO lowering the guarantee target (normal_feat_amount):
	# each profession feat then REPLACES a normal feat (the "feat cost" house rule), or, when the
	# budget is too small, takes over the track and clamps the normal feats down to 0.
	character.normal_feat_amount = max(0, character.normal_feat_amount - _prof_feat_n)

	return PhaseRecord(
		_pow_funded_n=_pow_funded_n,
		_pow_mentor_feats=_pow_mentor_feats,
		_pow_mentor_names=_pow_mentor_names,
		_sphere_mentor_talents=_sphere_mentor_talents,
		casting_tradition=casting_tradition,
		combat_talent_items=combat_talent_items,
		dedicated_trainer_specs=dedicated_trainer_specs,
		homebrew_feat_desc_dict=homebrew_feat_desc_dict,
		initiation_stat=initiation_stat,
		initiator_level=initiator_level,
		magic_talent_items=magic_talent_items,
		maneuvers_choose_from=maneuvers_choose_from,
		maneuvers_desc_dict=maneuvers_desc_dict,
		maneuvers_known_list=maneuvers_known_list,
		maneuvers_readied_list=maneuvers_readied_list,
		maneuvers_readied_names=maneuvers_readied_names,
		manifesters=manifesters,
		martial_disciplines=martial_disciplines,
		mt_feat_tax=mt_feat_tax,
		mt_feats=mt_feats,
		powers_desc_dict=powers_desc_dict,
		sphere_boons=sphere_boons,
		sphere_counts=sphere_counts,
		sphere_drawbacks=sphere_drawbacks,
		sphere_feat_tax=sphere_feat_tax,
		sphere_feats=sphere_feats,
		sphere_mana_pool=sphere_mana_pool,
		sphere_traits=sphere_traits,
		spheres_chosen=spheres_chosen,
		stances_chosen=stances_chosen,
		style_feat_tax=style_feat_tax,
		style_feats=style_feats,
	)


@phase(requires=['classes', 'chosen_domain', 'chosen_school'],
	   returns=['class_features', 'class_feature_levels', 'class_feature_owners',
				'casting_level_str_foundry'])
def phase_class_features_and_bonus_spells(character, casting_level_str):
	'''Close the class-features bucket, then spend the bonus spells that read out of it.

	The seal is the whole point of the ordering. `data_dict['class features']` exists from the first
	line of generation, so a presence check cannot tell "no chooser ran" from "this class has no
	choices" -- and the bonus-spell lookups below would quietly return {} rather than raise. `seal`
	and `require_sealed` bracket that: every chooser has run by the time this phase starts, and a
	chooser added after it fails loudly instead of being silently missed.

	`casting_level_str_foundry` is CONDITIONALLY BOUND and seeded here to 'None' for the same reason
	`chosen_school` is seeded in phase_class_options: the branch only fires for low/high/mid casters,
	and the export needs the string to exist for everyone else. Seeding it inside the phase (rather
	than 900 lines earlier at the top of generate_random_char) is what lets `returns` check it.
	'''
	# Every class-choice chooser (domains, school, bloodline, hexes, talents, ...) has run by here,
	# so the bucket is closed. Sealing is what makes the two reads below safe to check: the key
	# always EXISTS from the first line of generation, so a presence test cannot tell "no chooser
	# ran" from "this class has no choices" -- and a chooser added AFTER this point would silently
	# leave both the snapshot here and the bonus-spell lookups below reading an unfinished dict.
	casting_level_str_foundry = 'None'
	seal(character, 'class features')
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
	# Bonus spells are looked up out of the class-features bucket below, so it must be finished.
	# This used to be an unguarded read: move a chooser after this point and every bonus-spell
	# lookup quietly returns {} instead of raising.
	require_sealed(character, 'class features', 'the bonus-spell section')
	# each addition targets the granting CLASS's own spellbook (multiclass-aware); for a
	# single-class character that book is the legacy scalar's object, so behavior is unchanged
	def _book_for(*names):
		return next((c for c in character.classes
					 if c['name'] in names and c.get('spell_list_choose_from')), None)
# Bloodlines
	_bloodline_book = _book_for('sorcerer', 'bloodrager')
	if _bloodline_book is not None and character.bloodline != "N/A":
		bonus_spells = character.data_dict['class features'].get("Talents", {}).get(character.bloodline, {}).get("bonus spells", [])
		add_bonus_spells(character, bonus_spells, _bloodline_book['spell_list_choose_from'])
# Patrons
	# LEVEL-GATED, unlike the bloodline above. A patron grants its nine spells at witch levels 2,
	# 4, 6 ... 18, and those are spell levels 1-9 in order -- which is exactly the positional
	# convention add_bonus_spells already uses (entry i goes to spell_groups[i+1]). So truncating
	# the list at the witch's own level hands it the right spells at the right levels, and a 3rd-
	# level witch gets `jump` rather than `shapechange`.
	_witch_book = _book_for('witch')
	if _witch_book is not None:
		_witch_entry = next((c for c in character.classes if c['name'] == 'witch'), None)
		for _patron in (character.data_dict['class features'].get('patron') or {}).values():
			if not isinstance(_patron, dict):
				continue
			_levels = _patron.get('witch levels') or []
			_spells = _patron.get('bonus spells') or []
			_due = [s for lv, s in zip(_levels, _spells) if lv <= (_witch_entry or {}).get('level', 0)]
			add_bonus_spells(character, _due, _witch_book['spell_list_choose_from'])
# Domains
	_cleric_book = _book_for('cleric')
	if character.chosen_domain not in ([], None) and _cleric_book is not None:
		for i, domain in enumerate(character.chosen_domain):
			bonus_spells = character.data_dict.get('class features', {}).get(domain.title(), {}).get("bonus spells", {})
			add_bonus_spells(character, bonus_spells, _cleric_book['spell_list_choose_from'])

	_druid_book = _book_for('druid')
	if character.chosen_domain not in ([], None) and _druid_book is not None:
		for i, domain in enumerate(character.chosen_domain):
			bonus_spells = character.data_dict['class features'].get(domain, {}).get("bonus spells", [])
			add_bonus_spells(character, bonus_spells, _druid_book['spell_list_choose_from'])
# Inquisitions
	# Don't get bonus spells
# Schools
	# Schools spells are just recommended spells (not bonus spells), but we'll mnake sure wizards take them
	_wizard_book = _book_for('wizard')
	if character.chosen_school not in ([], None) and _wizard_book is not None:
		try:
			bonus_spells_dict = character.data_dict['class features'].get(character.chosen_school).get("spells", [])
			add_bonus_spells_from_dict(character, bonus_spells_dict, _wizard_book['spell_list_choose_from'])
			# print("bonus_spells_dict", bonus_spells_dict)
			# print("character.spell_list_choose_from", character.spell_list_choose_from)
		except:
			print("wizard, but wizard spell list has no bonus spells")


	return PhaseRecord(
		class_features=class_features,
		class_feature_levels=class_feature_levels,
		class_feature_owners=class_feature_owners,
		casting_level_str_foundry=casting_level_str_foundry,
	)


@phase(requires=['chooseable', 'feat_amounts', 'class_feats_amount'],
	   provides=['feats'],
	   returns=['casting_level_str', 'teamwork_feats', 'teamwork_feat_labels'])
def phase_feat_selection(character, grants, skill_ranks, truly_random_feats, teamwork_feats):
	'''Choose the character's ordinary feats, then its teamwork feats.

	Two of the six `character.feat_amounts` mutation sites ticket 08 catalogued live here: the
	teamwork-overflow refund and the class-bonus-feat fold-in. Both are `+=` refunds -- "give back
	slots something could not spend" -- and they must happen BEFORE the chooser runs, because
	`feat_amount=character.feat_amounts` is what sizes the selection.

	`teamwork_feats` arrives as the integer COUNT on the character and leaves as the chosen LIST, on
	the record. That shadowing is deliberate and pre-existing; the record is what finally makes the
	two distinguishable at the call site (`character.teamwork_feats` vs `fs.teamwork_feats`).

	requires `chooseable`: the free-at-BAB1 feats and every class-granted pick are seeded into it by
	phase_class_bonus_feats, and no_prereq_loop treats chooseable as owned. Run this first and the
	general pool happily re-picks feats the character already has.
	'''
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
	# Reserved E-Kat slots (homebrew luck). Carved OUT of the budget, exactly as path_of_war /
	# spheres / professions reserve theirs above -- never added on top, so a lucky character spends
	# its OWN feats on luck. Taken before the chooser because feat_amount=character.feat_amounts is
	# what sizes the draw. These feats never enter the generic pool: e_kat_feat_chooser resolves the
	# chains itself and leaves chooseable_talents alone (see feats.py).
	# Feats the character SOLD LUCK FOR ("You may gain a feat for -5 luck"), reserved and drawn HERE
	# -- FIRST, ahead of the E-Kat reservation below.
	#
	# phase_luck_stake adds these slots to feat_amounts, and that used to be the whole mechanism: the
	# general draw simply picked more, and phase_luck_resolution guessed WHICH of them the sale had
	# paid for by taking the tail of the feat list minus everything reserved by another subsystem.
	# Both halves of that were wrong once sellers gained E-Kat feats. The budget is a single pool, so
	# the E-Kat and profession reservations below were free to consume the very slots the sale had
	# just added -- a character sold luck for a feat and the feat became an E-Kat reservation. And the
	# guess had nothing left to name: on a measured 20th-level seller all twelve normal rows were
	# E-Kat, profession or Martial Training picks, so the ledger silently printed fewer "(-5 Luck)"
	# rows than the character had bought (6 of 39 sellers, and the reason this was reported as a bug).
	#
	# Reserving up front fixes both at once: the slots cannot be eaten, and the ledger names the exact
	# feats instead of inferring them. topup_feat_chooser is the established "draw N more ordinary
	# feats" helper -- it widens the pool as it goes and registers every pick in character.chooseable,
	# so the general draw below cannot re-pick one.
	luck_bought_feats = []
	_luck_stake = luck.stake_of(character)
	_luck_slots = (_luck_stake or {}).get('bonus_feat_slots', 0)
	if _luck_slots:
		# NOT clamped to the remaining budget, unlike the E-Kat reservation below. These slots are
		# ADDITIVE -- the character sold luck to GAIN a feat, so the feat must exist however little
		# budget the professions / Path of War / Spheres reservations left behind. Clamping made the
		# sale silently buy nothing on a low-level or heavily-subsystemed character (7 of 60 across a
		# class x level sweep). phase_luck_stake already added these to feat_amounts, so subtracting
		# them here returns the pool to its pre-sale size and the drawn feats are the net gain.
		character.feat_amounts = max(0, character.feat_amounts - _luck_slots)
		luck_bought_feats = topup_feat_chooser(character, casting_level_str, _luck_slots)
	character.luck_bought_feats = list(luck_bought_feats)

	e_kat_feats_chosen = []
	if getattr(character, 'e_kat_feat_slots', 0):
		_reserved = min(character.e_kat_feat_slots, max(0, character.feat_amounts))
		character.feat_amounts -= _reserved
		e_kat_feats_chosen = e_kat_feat_chooser(character, _reserved)
	# Recorded on the character so separate_feats_func can keep these out of the story / flaw /
	# flavour / class buckets -- an E-Kat feat is an ordinary feat and must render as one.
	character.e_kat_feats_chosen = list(e_kat_feats_chosen)
	# OPTIMIZED MODE (spec 15, ticket 06's disposition): optimize SUBSUMES truly_random_feats and
	# forces the build-aware path -- build_selector is literally the build selector, and it is the
	# only route on which the role's feat spine can fire (the gate's first run caught optimized
	# gunslingers with no Deadly Aim because the default 'Y' path bypasses choosing_feats).
	if getattr(character, 'role', None):
		truly_random_feats = 'N'
		# The ambient-prereq unlock (wall pass): the house-waived feats are held by rule but
		# invisible to the prereq vocabulary, so a spine could never chain through Dodge /
		# Improved Unarmed Strike / Combat Expertise (Crane Style was legal and unpoolable).
		# Optimize-gated, so random mode's prereq world is untouched.
		from utils.class_func.power_role import ambient_feat_names
		character.chooseable.update(ambient_feat_names())
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
	character.feats.extend(capitalize_feats(character, list(grants.ranger_style_feats)))
	character.feats.extend(capitalize_feats(character, list(grants.monk_bonus_feats)))
	# E-Kat picks join here, in canonical casing straight from the curated table -- the Foundry
	# module and the resolution phase both match on these names, and capitalize_feats would re-case
	# them. They ride the same dedupe and the same feat-tax/swap pass as everything else, which is
	# precisely why phase_luck_resolution counts feats at the far end instead of trusting this list.
	character.feats.extend(e_kat_feats_chosen)
	# The luck-bought feats join the same list: they ARE ordinary feats, just ones whose slot was
	# paid for by selling luck rather than earned at a level. They ride the same dedupe, feat-tax and
	# swap passes as everything else -- which is why phase_luck_resolution intersects this list with
	# the FINAL feats before billing it, rather than trusting what was drawn here.
	character.feats.extend(luck_bought_feats)
	# Belt-and-braces: same feat arriving from two sources with different casing would
	# otherwise survive to the sheet as a duplicate entry.
	character.feats = dedupe_feats_case_insensitive(character.feats)

	# Shared shortfall top-up (both feat paths): the type/caster-filtered pools can run dry
	# before the budget is met (and the dedupe above can drop a cross-source duplicate).
	# Target = the requested budget plus the class-granted ranger/monk merges, which sit on
	# top of character.feat_amounts (only their unfilled surplus was folded into it).
	_expected_feat_total = character.feat_amounts + len(grants.ranger_style_feats) + len(grants.monk_bonus_feats)
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

	return PhaseRecord(
		casting_level_str=casting_level_str,
		teamwork_feats=teamwork_feats,
		teamwork_feat_labels=teamwork_feat_labels,
	)


@phase(requires=['feat_amounts', 'normal_feat_amount', 'chooseable'],
	   returns=['feats', 'story_feats', 'flaw_feats', 'flavor_feats', 'class_feats', 'feat_budget', 'story_feat_tax_dict', 'flaw_feat_tax_dict', 'flavor_feat_tax_dict', 'class_feat_tax_dict', 'feats_feat_tax_dict', 'trainer_feat_tax_dict', 'class_feat_labels', 'trainer_feats', 'trainer_feat_labels', 'trainer_calibers', '_trainer_group_meta', 'profession_feats', 'profession_feat_desc', 'profession_ranks', 'profession_pool', 'teamwork_feats', 'teamwork_feat_labels'])
def phase_feat_tax_and_swaps(character, feats, grants, pw, casting_level_str,
							teamwork_feats, teamwork_feat_labels, trainers_enabled):
	'''The feat-tax engine, the trainer rows, and the count guarantee -- the last and hardest block.

	Ticket 07 called this one out to be done last, and the reason holds: 320-odd lines containing six
	`feat_tax_func` calls, two near-duplicated `assign_feats_to_levels` reorder passes, trainer-row
	synthesis for two different subsystems, a tax-child strip with a two-round backfill, and the final
	count guarantee. It reads `character.feat_amounts` roughly 250 lines after the last thing that
	mutated it.

	What makes it EXTRACTABLE rather than merely long is that every one of those mutations now happens
	upstream, inside a phase that declares it -- so this block only ever READS the budget. That is why
	it takes no `provides` on the budget and why ticket 08 had to be settled first: the six
	non-adjacent mutation sites are exactly what used to stop this block being contiguous.

	Twenty-three values cross out, all of them to the export. `feats` arrives as the merged list and
	leaves split five ways by `separate_feats_func`, which is why it appears in both the parameters
	and the record -- the same name, deliberately, because the split IS the block's job.
	'''
# ------------------- Last minute Feat swapping process -------------------#
	story_feats, flaw_feats, flavor_feats, class_feats, feats = separate_feats_func(character, feats)
	# Paid Martial Training picks and style-chain bases join the normal bucket (their slots
	# were reserved out of the ask before the chooser ran); the feat-tax passes below bundle
	# the free partners/followers. Style children register as owned so nothing re-picks them.
	# The PoW mentor's feats are deliberately NOT here -- they render under its "(Trainer N)"
	# group instead, which is what keeps them off the normal track and out of a second listing.
	feats.extend([f for f in pw.mt_feats if f not in pw._pow_mentor_names])
	feats.extend([f for f in pw.style_feats if f not in pw._pow_mentor_names])
	# NOTE: pw.sphere_feats are appended AFTER the feat-tax pass (below), not here -- they share a base
	# name ("Extra Combat Talent") that feat_tax_func would wrongly chain/strip together.
	add_feats_to_chooseable(character, story_feats, flaw_feats, flavor_feats, class_feats, feats)
	add_feats_to_chooseable(character, pw.sphere_feats)
	add_feats_to_chooseable(character, [c for ch in pw.style_feat_tax.values() for c in ch])

	# ------------------- Trainer & profession bonus feats (homebrew, additive) -------------------#
	# Trainers teach feats grouped under "(Trainer N)" tags; profession feats are named homebrew
	# feats (True Calling / Multi Talented / Always Improving). Both sit ON TOP of the normal
	# budget (like bloodline/teamwork) and are registered as owned so nothing re-picks them. Chosen
	# AFTER the normal feats are in chooseable, so trainer picks never duplicate the main list.
	if trainers_enabled:
		trainer_feats, trainer_feat_labels, trainer_calibers = select_trainer_feats(character, casting_level_str)
	else:
		# Empty lists, not a skipped variable: every downstream reader already tolerates empty
		# trainer data (a Yes-run can legitimately roll 0 trainer slots), so opting out is just
		# the zero case made deliberate.
		trainer_feats, trainer_feat_labels, trainer_calibers = [], [], []
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
			+ len(grants.ranger_style_feats) + len(grants.monk_bonus_feats)
			+ len(pw.mt_feats) + len(pw.style_feats) - pw._pow_funded_n,
		"teamwork": character.teamwork_feats,
		"bloodline": len(grants.bloodline_feats),
		# The mentor rows are appended after the feat-tax pass below, so count them here or the
		# "feat rows ->" audit reports a phantom trainer deficit.
		"trainer": len(trainer_feats) + len(pw.dedicated_trainer_specs) + pw._pow_funded_n,
		"profession": len(profession_feats),
	}
	# add all feats to character.chooseable (for feat taxing purposes)


	# Feat tax portion — pass per-feat acquisition levels so each progression chain releases
	# one free feat every two levels since the primary was gained (feat-tax rule e).
	# Normal feats land at L1,3,5,…; story feats at L1,5,10,15,…; flaw/flavor at creation (L1);
	# class bonus feats at their granting levels (_class_feat_levels, e.g. Fighter 1/2/4).
	_story_levels  = ([1] + [5 * k for k in range(1, len(story_feats) + 1)])[:len(story_feats)]
	_normal_levels = normal_feat_slot_levels(character, len(feats))
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
	# Dedicated PoW/Spheres mentors (25% "trainer-backed" branch): extra "(Trainer N)" slots whose
	# caliber rolls funded homebrew training the character's own half-share couldn't reach. The label
	# names the system ("(Trainer 3 - Path of War)") so the Feats tab says which mentor taught what;
	# both the module and the web sheet print the label verbatim, so no JS change is needed.
	# `_trainer_group_meta` records each group's true FEATS' WORTH for the backstory rank -- inferring
	# it from the row count only works for ordinary trainers (see the backstory section below).
	_next_trainer_n = len(trainer_calibers) + 1
	_trainer_group_meta = {}
	# The PoW mentor has no row of its own: the Martial Training / style feats it paid for ARE its
	# content, sharing one label so they group. Their tax chains move here from feats_feat_tax_dict
	# (below) since these feats are no longer in the normal track.
	if pw._pow_mentor_feats:
		_pow_mentor_label = f"(Trainer {_next_trainer_n} - Path of War)"
		_next_trainer_n += 1
		for _pow_feat in pw._pow_mentor_feats:
			trainer_feats.append(_pow_feat)
			trainer_feat_labels.append(_pow_mentor_label)
			trainer_feat_tax_dict[_pow_feat] = list(pw.mt_feat_tax.get(_pow_feat) or pw.style_feat_tax.get(_pow_feat) or [])
		_trainer_group_meta[_pow_mentor_label] = (len(pw._pow_mentor_feats), "Path of War", list(pw._pow_mentor_feats))
	for _mentor_name, _mentor_desc in pw.dedicated_trainer_specs:
		_sphere_mentor_label = f"(Trainer {_next_trainer_n} - Spheres)"
		trainer_feats.append(_mentor_name)
		trainer_feat_labels.append(_sphere_mentor_label)
		_next_trainer_n += 1
		trainer_feat_tax_dict.setdefault(_mentor_name, [])
		pw.homebrew_feat_desc_dict[_mentor_name] = _mentor_desc
		# Rank by the Extra-Talent feats the funded talents bundle into, and name the TALENTS it
		# taught -- the row name ("Spheres Mentor") is the funding record, not the lesson.
		_trainer_group_meta[_sphere_mentor_label] = (
			mentor_feat_worth(pw._sphere_mentor_talents), "Spheres",
			[str(_t.get('name', '')) for _t in pw._sphere_mentor_talents if _t.get('name')])
	# Martial Training chains are taken once PER DISCIPLINE and discipline-labeled (e.g.
	# "Martial Training I (Broken Blade)"), so they aren't in data/feats.csv and feat_tax_func
	# can't resolve them. Merge the hand-built bundle directly (paid I/III/V -> free II/IV/VI
	# per chain) and register the free partners in the shared granted-set, mirroring the
	# style-chain handling below.
	# Every child registers in the granted-set no matter who funded its parent, or the backfill
	# re-picks a partner that was already granted; only the DICT merge is split by funder, since a
	# mentor-funded parent now lives in trainer_feat_tax_dict.
	for _mt_children in pw.mt_feat_tax.values():
		_tax_already_granted.update(str(c).lower() for c in _mt_children)
	feats_feat_tax_dict.update({k: v for k, v in pw.mt_feat_tax.items() if k not in pw._pow_mentor_names})
	# Style-chain followers are ALWAYS granted in full ("feat tax all the way through").
	# They are Metzofitz homebrew absent from data/feats.csv, so feat_tax_func can't see
	# them -- merge the hand-built bundle directly; registering the children in the shared
	# granted-set keeps the strip/backfill/no-duplicate invariants intact.
	for _style_children in pw.style_feat_tax.values():
		_tax_already_granted.update(str(c).lower() for c in _style_children)
	feats_feat_tax_dict.update({k: v for k, v in pw.style_feat_tax.items() if k not in pw._pow_mentor_names})
	# Spheres Extra-Talent feats (HR1): one slot grants a free duplicate ("Extra Talent > Extra
	# Talent"), bundling 2 talents. Hand-built (homebrew, not in feats.csv) -> merge like style chains.
	for _sphere_children in pw.sphere_feat_tax.values():
		_tax_already_granted.update(str(c).lower() for c in _sphere_children)
	feats_feat_tax_dict.update(pw.sphere_feat_tax)

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
		if isinstance(grants.bloodline_feats, list) and grants.bloodline_feats:
			grants.bloodline_feats, grants.bloodline_feat_labels = strip_labeled_bucket(grants.bloodline_feats, grants.bloodline_feat_labels, _taxed_children)

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
		# Tail of the full schedule -- the levels are no longer a pure function of the index (the
		# surplus seats at level 1), so the slice comes off the whole list rather than a range().
		_repl_normal_levels = normal_feat_slot_levels(character, len(feats))[len(feats) - len(normal_repl):]
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
			if isinstance(grants.bloodline_feats, list) and grants.bloodline_feats:
				grants.bloodline_feats, grants.bloodline_feat_labels = strip_labeled_bucket(grants.bloodline_feats, grants.bloodline_feat_labels, _children_2)
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
			normal_feat_slot_levels(character, len(feats)), [lvl for _, lvl in _post_class_slots])
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
		f"bloodline {len(grants.bloodline_feats)}/{feat_budget['bloodline']}, "
		f"trainer {len(trainer_feats)}/{feat_budget['trainer']}, profession {len(profession_feats)}/{feat_budget['profession']}")
	if pw.martial_disciplines or pw.mt_feats or pw.style_feats:
		print(f"PoW -> disciplines {pw.martial_disciplines}, IL {pw.initiator_level}, "
			f"known {sum(pw.maneuvers_known_list)} by-level {pw.maneuvers_known_list}, "
			f"readied {sum(pw.maneuvers_readied_list)}, "
			f"stances {len(pw.stances_chosen)}, mt {pw.mt_feats}, styles {pw.style_feats}")

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
			normal_feat_slot_levels(character, len(feats)), [lvl for _, lvl in _post_class_slots])
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
	# their hand-built HR1 tax (pw.sphere_feat_tax, merged into feats_feat_tax_dict above) and aren't
	# migrated into the class-bonus pool / chained by feat_tax_func. They land at the end of the
	# Feats list (highest "(Feat N)" numbers). Their budget cost was already reserved out of
	# feat_amounts above, so the normal chooser/backfill left room for them.
	feats.extend(pw.sphere_feats)

	# ---- Final feat-count guarantee: the general feat track == normal_feat_amount EXACTLY ----
	# The sheet labels feats positionally (1,3,5,…), so a list of length N renders feats at the
	# character's real feat levels with no gaps and nothing past their level. Never short (defensive
	# backfill -- RC1 should already prevent it) and never over: when homebrew (Martial Training +
	# sphere Extra-Talent feats) outnumbers the slots, trim the lowest-priority excess -- the sphere
	# Extra-Talent feat SLOTS first (their talents stay on the sheet as native combat/magic talents;
	# only the tracking feat is dropped), then any remaining tail. (House rule: cap to exact.)
	_feat_target = int(getattr(character, "normal_feat_amount", len(feats)) or 0)
	if len(feats) > _feat_target:
		# TRIM IN PRIORITY ORDER, cheapest slot first. This used to trim sphere feats and then slice
		# the head (`feats[:target]`), which dropped whatever sat at the END of the list -- and the
		# end is exactly where the separately-paid-for picks are appended. A seller lost the feats it
		# had just sold luck for, and a lucky character lost E-Kat picks its reservation had bought.
		#
		# At low level the budget is genuinely oversubscribed (a 1st-level character has 3 normal
		# slots and can owe 3 professions, an E-Kat pick and 2 luck-bought feats), so something MUST
		# go. The order says which: sphere tracking feats first (their talents stay on the sheet
		# regardless), then ordinary picks, then E-Kat picks, and the luck-bought feats last of all,
		# because those are the only ones the character spent a currency for.
		_sphere_lower = {str(s).lower() for s in pw.sphere_feats}
		_ekat_lower = {str(n).lower() for n in (getattr(character, 'e_kat_feats_chosen', None) or [])}
		_luck_lower = {str(n).lower() for n in (getattr(character, 'luck_bought_feats', None) or [])}

		def _trim_by(predicate):
			"""Drop feats matching `predicate` from the TAIL until the target is met."""
			over = len(feats) - _feat_target
			if over <= 0:
				return feats
			kept = []
			for _f in reversed(feats):
				if over > 0 and predicate(str(_f).lower()):
					over -= 1
					continue
				kept.append(_f)
			return list(reversed(kept))

		feats = _trim_by(lambda f: f in _sphere_lower)
		feats = _trim_by(lambda f: f not in _ekat_lower and f not in _luck_lower)
		feats = _trim_by(lambda f: f in _ekat_lower)
		feats = _trim_by(lambda f: f in _luck_lower)
	elif len(feats) < _feat_target:                      # defensive guarantee against any future regression
		_fill = topup_feat_chooser(character, casting_level_str, _feat_target - len(feats))
		add_feats_to_chooseable(character, _fill)
		feats.extend(_fill)
	print(f"feat guarantee -> general {len(feats)}/{_feat_target}, story {len(story_feats)}/{feat_budget['story']}"
		f", class {len(class_feats)}/{feat_budget['class']} | generator {GENERATOR_VERSION}")

	# Now drop the profession feats into the general feat track -- AFTER the feat-tax passes and the
	# count guarantee, so they are never chained/taxed and never trimmed (their slots were reserved
	# out of feat_amounts / normal_feat_amount above, so each costs a feat). Each renders as its own
	# ordinary feat; register descriptions in pw.homebrew_feat_desc_dict (case-insensitive) so the
	# module / description backfill resolve them instead of hitting the CSV.
	if profession_feats:
		feats.extend(profession_feats)
		for _pf_name, _pf_desc in profession_feat_desc.items():
			pw.homebrew_feat_desc_dict[_pf_name] = _pf_desc

	return PhaseRecord(
		feats=feats,
		story_feats=story_feats,
		flaw_feats=flaw_feats,
		flavor_feats=flavor_feats,
		class_feats=class_feats,
		feat_budget=feat_budget,
		story_feat_tax_dict=story_feat_tax_dict,
		flaw_feat_tax_dict=flaw_feat_tax_dict,
		flavor_feat_tax_dict=flavor_feat_tax_dict,
		class_feat_tax_dict=class_feat_tax_dict,
		feats_feat_tax_dict=feats_feat_tax_dict,
		trainer_feat_tax_dict=trainer_feat_tax_dict,
		class_feat_labels=class_feat_labels,
		trainer_feats=trainer_feats,
		trainer_feat_labels=trainer_feat_labels,
		trainer_calibers=trainer_calibers,
		_trainer_group_meta=_trainer_group_meta,
		profession_feats=profession_feats,
		profession_feat_desc=profession_feat_desc,
		profession_ranks=profession_ranks,
		profession_pool=profession_pool,
		teamwork_feats=teamwork_feats,
		teamwork_feat_labels=teamwork_feat_labels,
	)


def _luck_payout_changes(character, stake):
	"""The seller's payout as pf1 `changes`, for the Negative Luck Payout item to carry.

	The three pools no longer apply their payout themselves (see hp_rolls / skill_ranks / stats);
	this is what delivers it, and it is delivered on the Changes tab where a player can see the
	number and where it came from. HP in particular was never reaching the sheet at all: the module
	builds actor HP from `total_rolled_hp`, so everything the backend added to `Total_HP` was
	invisible in Foundry.

	Targets are pf1's own (`mhp`, `bonusSkillRanks`, and the six ability keys), typed `untyped` so
	they stack -- these are not luck bonuses in the pf1 sense, they are what the sale bought.
	"""
	if not stake or stake['direction'] != 'sell':
		return []
	pay = stake.get('payout', {})
	out = []
	def _add(formula, target, flavor):
		out.append({'formula': str(formula), 'target': target, 'type': 'untyped',
					'operator': 'add', 'priority': 0, 'flavor': flavor})
	if pay.get(luck.PAYOUT_HP):
		_add(pay[luck.PAYOUT_HP], 'mhp', 'Negative luck payout')
	if pay.get(luck.PAYOUT_SKILL_POINTS):
		_add(pay[luck.PAYOUT_SKILL_POINTS], 'bonusSkillRanks', 'Negative luck payout')
	# One change per ABILITY, not one per point: two points on the same ability read as a single +2
	# on the Changes tab, which is how pf1 shows every other stacked bonus.
	for _ability, _bumps in sorted((getattr(character, 'luck_attribute_bumps', None) or {}).items()):
		_add(_bumps, _ability, 'Negative luck payout')
	return out


def _luck_audit_rows(character, negative_feats):
	"""The per-pool luck audit, closed out against the numbers the SHEET finally shows.

	`luck.record_audit` captured before/spent/received/after at each pool's own site, which is the
	only place those exist. This adds `final` -- the value that reaches the sheet -- because later
	phases legitimately move the same budgets (`favored_class` adds +level HP, `skill_ranks` adds the
	background points). Without it the rows would look like they disagreed with the character sheet
	and the whole audit would read as broken rather than as evidence.

	NOTE the arithmetic: `before - spent == after`. `received` is NOT folded in, because the payout
	is no longer applied to these budgets at all -- it is delivered as pf1 changes (see
	`_luck_payout_changes`). The row therefore reads "here is the budget, here is what luck took from
	it, and here is what the sale is owed and where it arrives", which is the honest shape now.

	The feat row is built from the ledger rather than from the stake: the stake is the PLAN, and a
	plan cannot be evidence for itself.
	"""
	rows = dict(getattr(character, 'luck_audit', None) or {})
	# Feat slots are not a running budget, so `before`/`after` are both zero and only `received`
	# carries meaning. Keeping the same shape lets the same `before - spent == after` check run over
	# every row rather than special-casing this one out of the invariant.
	rows['feats'] = {'before': 0, 'spent': 0, 'received': len(negative_feats), 'after': 0}
	finals = {
		'hp': getattr(character, 'Total_HP', None),
		'skill_ranks': getattr(character, 'skill_rank_budget', None),
		'attribute_points': sum((getattr(character, 'level_up_stats', None) or {}).values()) or 0,
		'feats': len(negative_feats),
	}
	for name, row in rows.items():
		_final = finals.get(name)
		row['final'] = int(_final) if _final is not None else int(row['after'])
		# What this row COST in luck, inverting the Doc's rates. The four costs sum to the magnitude
		# sold, so the table closes against the luck score instead of being four unrelated numbers --
		# which is the whole reason to show a running total at all.
		row['luck_cost'] = luck.sell_cost(luck.AUDIT_POOL_TO_PAYOUT[name], row['received'])
	return rows


@phase(requires=['luck_stake', 'level'], returns=['luck', 'hero_points'])
def phase_luck_resolution(character, feats, hero_points, general_feats=(), reserved_feats=()):
	'''Turn the settled stake plus the feats the character ACTUALLY kept into its final luck state.

	This runs last for one reason: the E-Kat feats feed luck back into itself, and which ones a
	character holds is not final until phase_feat_tax_and_swaps has run its tax chains, its child
	strip and its two-round backfill. A swap can remove an E-Kat feat after the fact, so counting at
	selection time would credit luck for a feat that is no longer on the sheet -- the "generated but
	invisible" failure inverted. Same shape as phase_bloodline_resolution: resolve a value once all
	its inputs exist, not at the point the inputs are chosen.

	THE NO-DOUBLE-COUNT RULE is the subtle one. Every positive luck-based feat grants +1 Luck, but
	Ass Pull, It Just Works and Luck God state their own +4 and do NOT additionally collect the +1.
	The curated table encodes that as `grants_generic_luck`, and validate_luck.py asserts the two
	fields are never both set, so the rule cannot rot into a silent +5.

	Luck score is deliberately NOT a pf1 change: Default Luck applies to percentile rolls and the
	daily DR pool, not to d20 rolls, so it stays a displayed number. The one real modifier in the
	system is Luck God's flat +2, which rides feat_changes.json like every other feat buff.

	THE LUCK TRAITS ARE BOUGHT HERE, and this is the only place they can be. "25 Permanent E-Kats
	can be used to purchase a Luck Trait", the reserve that pays for them is feat-gated, and the
	feats are not final until the swap pass -- so the purchase cannot happen any earlier. Note they
	are NOT character traits: "Luck Traits may only be purchased with E-Kats", which is why
	trait_selector never draws them and data/traits.csv does not contain them.
	'''
	if not misc_homebrew_enabled(character):
		return PhaseRecord(luck=None, hero_points=hero_points)

	table = e_kat_feat_table()
	canonical = {name.lower(): name for name in table}
	# Dedupe while preserving order -- the same feat can arrive from two sources with different
	# casing, and counting it twice would inflate both the score and the reserve.
	held = list(dict.fromkeys(canonical[f.lower()] for f in feats if str(f).lower() in canonical))

	feat_luck = 0
	double_down = False
	bonus_hero_points = 0
	for name in held:
		effects = table[name]['effects']
		if effects['luck_bonus']:
			feat_luck += effects['luck_bonus']
		elif effects['grants_generic_luck']:
			feat_luck += luck.GENERIC_LUCK_FEAT_BONUS
		double_down = double_down or effects['doubles_acquisition']
		bonus_hero_points += effects['hero_points_per_session']

	# The luck-granting set is BROADER than the ten E-Kat feats: "every e-kat and hero point feat
	# grant an extra luck point", and Aristeia feats qualify too (none exist in the data). These are
	# ordinary Paizo rows already in the generic pool -- Blood of Heroes, Hero's Fortune, Luck of
	# Heroes, Defiant Luck, Fortunate One, Adaptive Fortune -- so they need recognising, not
	# reaching. Each grants the flat +1; none states a larger bonus, so none is exempt from it.
	luck_feats = held_luck_feats(feats)
	e_kat_luck = feat_luck                       # kept apart so the sheet can show the derivation
	other_luck = len(luck_feats) * luck.GENERIC_LUCK_FEAT_BONUS
	feat_luck += other_luck

	stake = character.luck_stake
	luck_type = stake['luck_type'] if stake else 'Default'
	dimorphic = luck_type == 'Dimorphic'

	# A SELLER CANNOT CLIMB BACK. Feats grant +1 Luck each and nothing in the Doc forbids a seller
	# holding them, but a character who sold its luck must not buy it back for free -- a -2 seller
	# who drew two luck feats used to finish at 0 and render as lucky, and with E-Kat slots now open
	# to sellers (phase_luck_stake) Ass Pull's +4 would make that routine rather than rare.
	#
	# The feats STAY on the sheet: Defiant Luck, Ass Pull and the rest carry real mechanics of their
	# own beyond the +1, and stripping them would deny a character abilities it legitimately bought
	# with its own feat slots. Only the luck they grant is withheld. e_kat_luck / other_luck stay
	# computed so the derivation can SAY that, rather than the score silently not adding up.
	selling = bool(stake) and stake['direction'] == 'sell'
	suppressed_luck = feat_luck if selling else 0
	if selling:
		feat_luck = 0

	# ---- the E-Kats this character EARNED, and what it spends them on -------------------------
	# Feat-gated: the two per-level terms only accrue if the character has the feat that produces
	# them, so a character with no E-Kat feats earns nothing. Uncapped -- the 99 governs storage,
	# and "These points must be spent."
	earned = luck.e_kat_reserve(character.level, held, dimorphic)
	# The score BEFORE traits decides which categories are eligible; only Increase Luck moves it
	# afterwards, and it can never flip a sign.
	base_score = luck.resolve_purchased_luck(stake) + feat_luck
	luck_traits = luck_trait_chooser(luck.luck_traits_afforded(earned), luck_type, base_score,
									 luck_feat_count=len(held) + len(luck_feats))

	# Stacks are counted by the EFFECT FIELD rather than by trait name, so renaming a trait in the
	# curated table cannot silently stop its bonus applying. Each trait grants exactly one step.
	trait_table = luck_trait_table()
	def _stacks(field):
		return sum(1 for name in luck_traits if trait_table[name]['effects'].get(field))
	expanded_stacks = _stacks('luck_cap_step')
	storage_stacks = _stacks('e_kat_store_step')
	vault_stacks = _stacks('vault_cap_step')
	twist_stacks = _stacks('twist_fate_bonus')
	# "These Traits do not grant 1 extra luck" -- no trait collects the generic +1 the way a feat
	# does. Increase Luck is the only one that touches the score, by its own stated amount.
	trait_luck = sum(trait_table[name]['effects'].get('luck_score_bonus', 0) for name in luck_traits)

	raw_score = base_score + trait_luck
	score = luck.clamp_luck(raw_score, luck_type, expanded_stacks)

	# The derivation, for the Personal Luck item's description -- the sheet shows WHY the number is
	# what it is, the way the hand-built reference sheets do ("13 Luck Skill Ranks / 12 Luck e-kat
	# feats"). Built from the parts already computed above rather than recomputed, so it can never
	# disagree with the score it explains.
	purchased = luck.resolve_purchased_luck(stake)
	derivation = []
	if stake and stake['direction'] == 'buy':
		_paid = stake.get('paid', {})
		_bits = [f"{_paid.get(k, 0)} {label}" for k, label in (
			(luck.CURRENCY_SKILL_RANKS, 'skill ranks'), (luck.CURRENCY_HP, 'HP'),
			(luck.CURRENCY_LEVEL_UP_POINTS, 'level-up points')) if _paid.get(k, 0)]
		derivation.append(f"Bought {purchased:+d} ({', '.join(_bits) or 'nothing spent'})")
	elif stake and stake['direction'] == 'sell':
		# Itemised from what the sale ACTUALLY bought. This used to name all four routes on every
		# seller regardless of which were drawn, which read as a fixed slogan rather than a ledger.
		_pay = stake.get('payout', {})
		_sold = [f"{_pay.get(k, 0)} {label}" for k, label in (
			(luck.PAYOUT_HP, 'HP'), (luck.PAYOUT_SKILL_POINTS, 'skill points'),
			(luck.PAYOUT_ATTRIBUTE_POINTS, 'attribute point(s)'),
			(luck.PAYOUT_FEATS, 'feat(s)')) if _pay.get(k, 0)]
		derivation.append(f"Sold {purchased:+d} luck for {', '.join(_sold) or 'nothing'}")
	if selling and suppressed_luck:
		# Say it out loud. A seller holding luck feats whose score ignores them is the one place the
		# arithmetic on this sheet does not visibly add up, so the sheet explains itself.
		derivation.append(f"{suppressed_luck:+d} from {len(held) + len(luck_feats)} luck feat(s) "
						  f"-- not applied (luck was sold)")
	if e_kat_luck and not selling:
		derivation.append(f"{e_kat_luck:+d} from {len(held)} E-Kat feat(s)")
	if other_luck and not selling:
		derivation.append(f"{other_luck:+d} from {len(luck_feats)} hero point / luck feat(s)")
	if trait_luck:
		derivation.append(f"{trait_luck:+d} from Increase Luck")
	if score != raw_score:
		derivation.append(f"= {raw_score}, clamped to {score} by the cap")
	else:
		derivation.append(f"= {score}")

	# Which feats the negative luck actually bought ("a feat for -5 luck"), labelled with the running
	# total the way the reference sheet does: (-5 Luck) X, (-10 Luck) Y. Feats inside a feat-tax chain
	# are skipped -- pulling a primary or a child into its own sheet section would orphan the chain,
	# so the ledger takes FEWER rows rather than break one.
	# The feats the sale actually bought, named EXACTLY rather than inferred. phase_feat_selection
	# reserves these slots before any other subsystem can take them and records what it drew on
	# `character.luck_bought_feats`; all this has to do is drop any that did not survive the feat-tax
	# and swap pass, which is precisely why the resolution runs at the far end of the pipeline.
	#
	# The old approach guessed -- "the tail of the feat list, minus everything another subsystem
	# reserved" -- and silently under-reported whenever the guess ran out of candidates. It did, on
	# 15% of sellers, because a 20th-level seller's normal track is mostly E-Kat, profession and
	# Martial Training picks. There is no filtering left to get wrong here.
	negative_feats = []
	if stake and stake['direction'] == 'sell' and stake['payout'].get(luck.PAYOUT_FEATS):
		# Matched on the BASE name. A chosen feat can reach the sheet renamed -- the specialization
		# choosers append their picks, so "Prodigy" becomes "Prodigy (Profession (Blacksmith),
		# Profession (Mob Kindler))" -- and an exact match silently drops it from the ledger.
		_base = lambda f: str(f).lower().split(' (')[0].strip()
		_held_now = {}
		for f in (general_feats or []):
			_held_now.setdefault(_base(f), f)
		_bought = [_held_now[_base(f)] for f in (getattr(character, 'luck_bought_feats', None) or [])
				   if _base(f) in _held_now]
		# A reserved pick can still be absorbed by the feat-tax strip: it becomes a CHILD of another
		# feat's chain, so the character keeps the feat but it renders inside that chain's row. Its
		# slot was still bought with luck, so the ledger must not shrink -- it falls back to the
		# marginal ordinary feats, skipping anything another subsystem already paid for. This is the
		# old inference, now a backstop for the rare absorbed pick rather than the primary mechanism.
		_short = stake['payout'][luck.PAYOUT_FEATS] - len(_bought)
		if _short > 0:
			_taken = {_base(f) for f in _bought}
			# Everything another subsystem already paid for. `reserved_feats` carries the Path of
			# War / Spheres picks, which live on that phase's record rather than the character --
			# without them the backstop billed "Martial Training I (Mithral Current)" to negative
			# luck, a slot the PoW reservation had bought.
			_spoken_for = {_base(f) for f in held}
			_spoken_for |= {_base(f) for f in (reserved_feats or [])}
			_spoken_for |= {_base(f) for f in (getattr(character, 'profession_feats', None) or [])}
			_spoken_for |= {_base(f) for f in (getattr(character, 'e_kat_feats_chosen', None) or [])}
			_spare = [f for f in (general_feats or [])
					  if _base(f) not in _taken and _base(f) not in _spoken_for]
			_bought += _spare[-_short:] if _spare else []
		negative_feats = [{'name': str(n), 'cumulative': -luck.SELL_LUCK_PER_FEAT * (i + 1)}
						  for i, n in enumerate(_bought)]
	luck_block = {
		'type': luck_type,
		'score': score,
		'values': luck.typed_values(score, luck_type),
		'mod': luck.luck_mod(score),
		'cap': luck.luck_cap(luck_type, expanded_stacks),
		'floor': luck.luck_floor(luck_type),
		# What the formula produced, before anything was spent -- exported so the derivation is
		# visible on the sheet instead of only the leftovers.
		'e_kat_earned': earned,
		# What is actually carried into play: the remainder after buying traits, under the store
		# cap. Under one trait's price by definition, so the cap only ever binds if a future change
		# stops spending.
		'e_kat_reserve': luck.carried_e_kats(earned, len(luck_traits), storage_stacks),
		'e_kat_store_cap': luck.e_kat_store_cap(storage_stacks),
		'traits': luck_traits,
		# Rules text for exactly the traits bought, so the FoundryVTT module can render an item per
		# trait without shipping its own copy of the 34-trait table (which would then drift).
		'trait_benefits': {name: trait_table[name]['benefit'] for name in set(luck_traits)},
		# The MECHANICS of those traits, in pf1's own change/contextNote shape, for the same reason.
		# Emitted only for traits that actually carry one, so the module can attach without probing.
		#
		# The formulas are LIVE (`-floor(@resources.personalLuck.value / 5)`) rather than numbers
		# baked here, so a GM editing the score mid-campaign moves every derived bonus with it. Note
		# the shape: `floor(abs(score)/5)` would be off by one for any score not divisible by 5 --
		# at -44 the true mod is -9 (magnitude 9) but floor(44/5) is 8 -- so the sign is negated
		# OUTSIDE the floor. luck.luck_mod() is the same rounding, and validate_luck asserts the two
		# agree on every score in range rather than trusting this comment.
		'trait_changes': {
			name: {
				'changes': trait_table[name].get('changes') or [],
				'contextNotes': trait_table[name].get('context_notes') or [],
				'death_hp_pool_bonus': trait_table[name].get('death_hp_pool_bonus') or '',
			}
			for name in set(luck_traits)
			if trait_table[name].get('changes') or trait_table[name].get('context_notes')
			or trait_table[name].get('death_hp_pool_bonus')
		},
		'vault': luck.VAULT_STARTING_BALANCE,
		'vault_cap': luck.vault_cap(vault_stacks),
		'dr_pool': luck.dr_pool(score),
		# Doc-native to Dimorphic, but exported for every type so the sheets read one shape.
		'twist_fate_per_day': (luck.twist_fate_per_day(score) + twist_stacks) if dimorphic else 0,
		'feats': held,
		# Non-E-Kat luck feats that contributed +1 each. Separate from `feats` because they are
		# ordinary Paizo feats the character reached through the normal pool, not reserved slots.
		'luck_feats': luck_feats,
		# Human-readable working, shown on the Personal Luck item so the score is auditable.
		'derivation': derivation,
		# Ordinary feats the negative luck paid for, with the running cost. Empty for buyers.
		'negative_feats': negative_feats,
		# WHAT EACH POOL ACTUALLY DID, recorded at the pool's own site as it happened
		# (luck.record_audit). The derivation above is the PLAN, read back from the same stake that
		# produced it -- it cannot prove the HP and skill budgets moved. This can: every row carries
		# the budget before, what luck took, what luck paid, and the budget after, so the sheet shows
		# arithmetic that either reconciles or visibly does not. The feat row has no budget site of
		# its own (feat slots are not a running total), so it is filled from the ledger actually
		# built above rather than from the stake -- which is the only reason it means anything.
		#
		# Each row also carries `final`: the number the SHEET ends up showing. It is not the same as
		# `after`, and the gap is the point -- favored_class adds +level HP and skill_ranks adds the
		# background points, both AFTER luck has been applied. A row that only showed the luck step
		# would look wrong against the sheet and get dismissed; showing `after` and `final` together
		# lets the reader see the luck movement AND watch it reconcile to the printed total.
		'audit': _luck_audit_rows(character, negative_feats),
		# The payout as pf1 changes, carried by the Negative Luck Payout item. This is the DELIVERY
		# mechanism, not a report: the three budgets above no longer apply it themselves.
		'payout_changes': _luck_payout_changes(character, stake),
		# Which abilities the attribute payout landed on, main-stat weighted. Exported alongside the
		# changes so the sheet can name them in prose as well as apply them.
		'attribute_bumps': dict(getattr(character, 'luck_attribute_bumps', None) or {}),
		'stake': stake,
	}
	# "Gain one free Hero Point per session" (It Just Works). Temporary by the Doc's own wording, so
	# it is also carried inside the block; the flat roll stays the starting count, and the 10-E-Kat
	# conversion remains an in-play spend the GM adjudicates, not a generation-time computation.
	return PhaseRecord(luck=luck_block, hero_points=hero_points + bonus_hero_points)


# Non random feats sometiems break at 20+
# Make sure to make a flag for adding metzofitz feats later
# Make sure to add a flag for path of war feats later
def generate_random_char(create_new_char='Y', userInput_region="Tal-Falko", userInput_race='Orc', class_choice='wizard', chosen_BAB='low', chosen_caster_level = 'random', multi_class='N', 
						 alignment_input = 'LG' , deity_flag = 'asdfasd', userInput_gender='female', truly_random_feats = "Y", inherents = "Y", modded_char_sheet = 'n', 
						 homebrew_feat_amount="Y",num_dice="8", num_sides="8", high_level=15, low_level=15, gold_num=1000000, use_backstory_api="Y", spheres_flag="N", backstory_focus=None,
						 seed=None, professions_flag="Y", trainers_flag="Y", misc_homebrew_rules="Y",
						 luck_direction=None, optimize=None, house_rules=None, mythic_request=None, ):

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

		# Professions and trainers are opt-OUTS: every character got both until the client could say
		# otherwise, so anything that isn't an explicit "no" keeps the old behaviour. Same string
		# shape as spheres_flag (see spheres.randomize_spheres_num), inverted because that one is
		# an opt-in.
		professions_enabled = str(professions_flag or "Y").upper() not in ("N", "NO", "FALSE", "0")
		trainers_enabled = str(trainers_flag or "Y").upper() not in ("N", "NO", "FALSE", "0")

		character = CreateNewCharacter(
			character_json_config)
		character.instantiate_full_data_dict()
		character.data_dict['class features'] = {}
		character.data_dict['class feature levels'] = {}
		# Seeded alongside its two siblings so the payload SHAPE never depends on the character.
		# It used to appear only when some chooser called generic_func's setdefault, so a character
		# with no class choices at all (fighter 1) shipped a payload one key shorter than everyone
		# else -- and both consumers read this contract positionally. Found by
		# validate_payload_shape.py comparing two different characters, which is the check that
		# exists precisely because a golden fixture can only say "this character didn't change".
		character.data_dict['class feature owners'] = {}

		# Flag that allows for homebrew feats to be added
		character.homebrew_feat_amount = homebrew_feat_amount
		# Catch-all flag for homebrew rules too small for their own input question (2->4 rank
		# floor, ...); internal-only, not an API input -- see skill_ranks.misc_homebrew_enabled.
		character.misc_homebrew_rules = misc_homebrew_rules
		# DEBUG override: 'buy' / 'sell' forces the luck branch and guarantees a stake. None (the
		# default, and what every real client sends) leaves the ordinary weighted rolls alone.
		character.luck_direction = luck_direction
		# The raw optimize request, readable by select_classes (which runs BEFORE the role phase
		# and needs the on/off bit for its multiclass posture -- ruling 8). phase_power_role is
		# what turns it into a role.
		character.optimize_request = optimize
		# The raw mythic request (mythic map, ticket 02). phase_mythic_stake is what turns it into
		# a tier; until then it is inert, and absent means NEVER mythic -- the input is the gate.
		character.mythic_request = mythic_request
		# Instantitae character.class_feats_amount
		character.class_feats_amount = 0
		# Instantitae teamwork_feats
		teamwork_feats = 0
		# insantiate character.deity_choice
		character.deity_choice = deity_flag

		f_name, l_name = phase_bootstrap_identity(
			character, userInput_gender, userInput_region, userInput_race,
			class_choice, chosen_BAB, chosen_caster_level, multi_class)

		# The optimizer's plan object (spec 15): off -> role None and every chooser takes its
		# existing path, which is what keeps the seven goldens byte-identical. Runs right after
		# the classes are picked, by ruling -- the role follows the class, never the reverse.
		# house_rules rides along (V4 wall pass): it only ever reads as role['house'], so it is
		# inert unless optimize already produced a role.
		phase_power_role(character, optimize, house_rules)

		#add an optional flaws rule function
		phase_alignment_and_level(character, alignment_input, deity_flag, low_level, high_level)

		# Luck's INTENT, before any budget exists to spend. Must follow the level (it scales the
		# magnitude) and the feat economy (a seller's bonus slots land on feat_amounts), and must
		# precede stats, HP and skill ranks -- each of those settles its own share.
		phase_luck_stake(character)

		# The mythic tier, resolved before any budget exists to size off it (mythic map, ticket
		# 02). Beside luck's stake by design: both are intent, not spending.
		phase_mythic_stake(character)

		stats = phase_roll_and_assign_stats(character, num_dice, num_sides, inherents)


		phase_hp_and_spellbooks(character)


		phase_class_options(character)






		### Need to change up the item_chooser function ###

		armor_chooser(character)
		character.assign_gold("gold", gold_num)

		# item_chooser has MOVED down, to just after the enhancement budget is spent (grep
		# plan_enhancements). It used to run here and drain the purse, so enhancement_calculator --
		# which ran ~30 lines later -- could never afford a tier and enhancement_effects_dict was
		# empty for every realistically funded NPC. Enhancements now take their reserved share first
		# and gear spends the rest.

		#calculating savings throws based off of class levels
		# fort_saving_throw = saving_throw_calc(character, 'Fortitude')
		# reflex_saving_throw = saving_throw_calc(character, 'Reflex')
		# wisdom_saving_throw = saving_throw_calc(character, 'Will')	

		# One Craft specialization per character, displayed as "Craft: <type>" on the sheet.
		# Chosen before professions so a profession can be themed around it.
		character.craft_chosen = random.choice(data.crafts)
		professions, skill_ranks = phase_professions_and_skills(character, truly_random_feats,
																character.skill_rank_level, professions_enabled)
		# Every character gets exactly one skill unlock, drawn from a skill they have ranks in.
		skill_unlock = choose_skill_unlock(character, skill_ranks)

		simple_list_chooser(character, 'ranger','favored_terrains', 'favored_enemies')
		simple_list_chooser(character, 'brawler','manuevers',max_num=8)


		gear = phase_gear_and_equipment(character)


		look = phase_appearance_and_traits(character, skill_ranks)
		character_full_name = f_name + ' ' + l_name
		# deity.json "Name" is a LIST of aliases since the homebrew-deities rework (091da54) -- export
		# one string: pf1's details.deity is a StringField, and an array crashes the actor's data
		# preparation on import (sheet dies reading the underived encumbrance).
		deity_choice = character.deity_choice
		deity_name = deity_choice.get("Name", "") if isinstance(deity_choice, dict) else deity_choice
		if isinstance(deity_name, list):
			deity_name = deity_name[0] if deity_name else ""
		print("deity_name", deity_name)
		print("deity", deity_choice)
		# skill_ranks = json.dumps(skill_ranks)  # disabled: ship the dict so Flask serializes it as a JSON object and the Foundry module parses it		



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



		phase_bloodline_resolution(character)

		# These two reads used to sit inside `try/except NameError`, because the locals they replaced
		# were CONDITIONALLY BOUND -- only a wizard ever reached the assignment, so on every other
		# class the name did not exist and the handler was the non-wizard path. phase_class_options
		# seeds both attributes to None precisely to preserve that, and an attribute lookup raises
		# AttributeError, never NameError -- so the handlers had become unreachable. They were left
		# standing while the extraction was in flight (a pure move must not fold in a cleanup) and
		# are removed here, once, now that it has landed. The `if ... else "N/A"` is what carries the
		# non-wizard path now, exactly as the handler did.
		# The equipped-kit display fields are a PURE derivation of character.armor_dict /
		# shield_dict, so they are owned by utils/payload.py rather than stored anywhere. Two of
		# them are read here as well, by the build-archetype scorer below; calling the same helper
		# is what keeps the scorer and the exported sheet from disagreeing about what is worn.
		_gd = gear_display(character)
		armor_name = _gd['armor_name']
		shield_name = _gd['shield_name']



	# end of pre export data manip

		# Start of Extra feats list generation section
		grants = phase_class_bonus_feats(character)

		pw = phase_path_of_war_and_spheres(character, spheres_flag, trainers_enabled)

		# Cached dataset without prerequisites -> allows them to take rage powers / rogue talents / etc. without normal feats ()
		print("cached dataset without prereqs allows for feats to buy class specific talents ")
		print("character.cached_dataset_without_prerequisites", sorted(character.cached_dataset_without_prerequisites))

		fs = phase_feat_selection(character, grants, skill_ranks, truly_random_feats, teamwork_feats)
		casting_level_str = fs.casting_level_str
		teamwork_feats = fs.teamwork_feats
		teamwork_feat_labels = fs.teamwork_feat_labels
		# `feats` is an alias of character.feats, not a separate value -- it lives on the character
		# (declared in the phase's `provides`) because choosers and no_prereq_loop read it there.
		feats = character.feats



		kin = phase_class_abilities_and_family(character)

		cf = phase_class_features_and_bonus_spells(character, casting_level_str)

		ft = phase_feat_tax_and_swaps(character, feats, grants, pw, casting_level_str,
								      teamwork_feats, teamwork_feat_labels, trainers_enabled)
		feats = ft.feats
		story_feats = ft.story_feats
		flaw_feats = ft.flaw_feats
		flavor_feats = ft.flavor_feats
		class_feats = ft.class_feats
		feat_budget = ft.feat_budget
		story_feat_tax_dict = ft.story_feat_tax_dict
		flaw_feat_tax_dict = ft.flaw_feat_tax_dict
		flavor_feat_tax_dict = ft.flavor_feat_tax_dict
		class_feat_tax_dict = ft.class_feat_tax_dict
		feats_feat_tax_dict = ft.feats_feat_tax_dict
		trainer_feat_tax_dict = ft.trainer_feat_tax_dict
		class_feat_labels = ft.class_feat_labels
		trainer_feats = ft.trainer_feats
		trainer_feat_labels = ft.trainer_feat_labels
		trainer_calibers = ft.trainer_calibers
		_trainer_group_meta = ft._trainer_group_meta
		profession_feats = ft.profession_feats
		profession_feat_desc = ft.profession_feat_desc
		profession_ranks = ft.profession_ranks
		profession_pool = ft.profession_pool
		teamwork_feats = ft.teamwork_feats
		teamwork_feat_labels = ft.teamwork_feat_labels

		# Luck resolves HERE, on the post-tax, post-swap feat list -- see phase_luck_resolution.
		# EVERY bucket, not just the general one: separate_feats_func front-pops the merged list into
		# story / flaw / flavor / class slots, so an E-Kat feat can land in any of them. Counting only
		# `feats` undercounted a wizard by 4 Luck and made It Just Works look like it had lost its
		# prerequisite, when Ass Pull was simply sitting in class_feats. The buckets are presentation
		# slots; the character holds all of them.
		_held_feat_names = [*feats, *story_feats, *flaw_feats, *flavor_feats, *class_feats,
							*trainer_feats]
		lk = phase_luck_resolution(character, _held_feat_names, look.hero_points,
								   general_feats=feats,
								   reserved_feats=list(pw.mt_feats or []) + list(pw.style_feats or [])
												  + list(pw.sphere_feats or []))

		# Put the E-Kat spend table and any purchased Luck Traits at the TOP of class features, so a
		# player sees what their reserve buys without opening the Doc. Done here rather than inside
		# the phase because it reaches into another phase's bucket, and that should be visible at the
		# call site rather than buried.
		#
		# Rebuilt IN PLACE (clear + reinsert) rather than reassigned: `cf.class_features` is the same
		# dict object, captured by phase_class_features_and_bonus_spells before luck resolved, and
		# that is what the payload exports. Binding a new dict here would leave the payload reading
		# the old one -- silently, with the sections simply absent.
		_luck_sections = luck_sheet_sections(lk.luck)
		if _luck_sections:
			_cf_bucket = character.data_dict['class features']
			_existing = dict(_cf_bucket)
			_cf_bucket.clear()
			_cf_bucket.update(_luck_sections)
			_cf_bucket.update(_existing)

		# Familiars stat LATE, here and not in stat_bonded_creatures: their numbers key off the
		# MASTER (half HP, master BAB/saves/ranks), and luck has only just settled Total_HP.
		# See familiars.py's module docstring.
		stat_familiars(character, skill_ranks)

		# Mythic lands HERE, after the feat economy has fully settled: the allowance is separate
		# (tiers 1/3/5/7/9) and the namesake prereqs read the final feat list. See the phase.
		myth = phase_mythic_abilities(character, pw, ft)



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

		if isinstance(cf.class_features, dict):

			# 3) Skill unlock: dict of "{N} Ranks" -> benefit (rendered as bold-labelled bullets).
			if skill_unlock:
				_unlock = skill_unlock.get("unlock") or {}
				_su_val = {f"{_r} Ranks": _unlock[_r] for _r in ("5", "10", "15", "20") if _unlock.get(_r)}
				cf.class_features["Skill Unlock: " + skill_unlock["skill"]] = _su_val or {"Skill Unlock": skill_unlock["skill"]}

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
			'weapon': gear.weapon_name,
			'weapon_category': _wd.get('category'),
			'weapon_groups': _weapon_groups,
			'armor': armor_name if isinstance(armor_name, str) else '',
			'shield': shield_name if character.shield_flag else '',
			'feats': feats,
			'disciplines': pw.martial_disciplines,
			'stances': pw.stances_chosen,
			'maneuvers': [n for _grp in pw.maneuvers_readied_names for n in (_grp if isinstance(_grp, list) else [_grp])],
			'spheres': pw.spheres_chosen,
			'casting': _arch_casting,
			'spells': _arch_spells,
			# signal-extraction facts (see _signals() in build_archetype.py)
			'class_names': [c['name'] for c in character.classes],
			'class_entries': [{'name': c['name'], 'level': c['level']} for c in character.classes],
			'total_level': character.level,
			'primary_class': character.c_class,
			'bab_tier': str(character.class_data.get(character.c_class, {}).get('bab', 'M')),
			'spell_levels': _arch_spell_levels,
			'initiator_level': pw.initiator_level,
			'armor_type': character.armor_type,
			'shield_flag': character.shield_flag,
			'weapon_special': _wd.get('special'),
			'weapon_critical': _wd.get('critical'),
			'stat_dict': {'str': character.str, 'dex': character.dex, 'con': character.con,
						  'int': character.int, 'wis': character.wis, 'cha': character.cha},
			'feat_buckets': character.feat_buckets,
			'class_feature_names': list(cf.class_features) if isinstance(cf.class_features, dict) else [],
			'companion': bool(getattr(character, 'chosen_animal', None)),
			'sphere_mana_pool': pw.sphere_mana_pool,
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
		# Rank every trainer by the FEATS' WORTH it actually delivered, never by its caliber roll -- a
		# mentor that could only fund two feats' worth should read "average", not "mythical". Ordinary
		# trainers deliver one feat per row, so the row count is their worth; the mentors need
		# _trainer_group_meta, because the Spheres Mentor is a SINGLE row funding up to four feats' worth
		# of talents (the old row-count formula read it as "terrible" every single time).
		_trainer_groups = {}
		for _lbl, _ft in zip(trainer_feat_labels, trainer_feats):
			_trainer_groups.setdefault(_lbl, []).append(_ft)
		_bs_trainers = []
		for _lbl, _fts in _trainer_groups.items():
			_worth, _kind, _taught = _trainer_group_meta.get(_lbl, (len(_fts), None, _fts))
			_cal_name = CALIBER_NAMES.get(min(max(_worth, 1), 4), "skilled") or "skilled"
			_article = "an" if _cal_name[0] in "aeiou" else "a"
			_kind_str = f" ({_kind})" if _kind else ""
			_bs_trainers.append(f"{_article} {_cal_name}{_kind_str} trainer who taught them {', '.join(_taught)}")
		_bs_brief = {
			'name': character_full_name, 'race': character.chosen_race,
			'gender': character.chosen_gender, 'age': character.age, 'region': character.region,
			'alignment': character.alignment_display, 'deity': deity_name,
			'char_class': character.c_class_display,
			# all non-primary classes, e.g. "fighter and wizard" for a 3-class character
			'class_2': ' and '.join(
				c['name'] for i, c in enumerate(character.classes)
				if i != character.primary_class_index),
			'level': character.c_class_level, 'main_stat': character.main_stat,
			'martial_disciplines': pw.martial_disciplines, 'notable_feats': feats,
			'traits': getattr(character, 'selected_traits_desc', None) or look.selected_traits,
			'personality_traits': character.personality_traits, 'mannerisms': character.mannerisms,
			'flaw': character.flaw,
			'background_traits': character.background_traits, 'professions': _bs_professions,
			'craft': character.craft_chosen, 'trainers': _bs_trainers,
			'appearance': look.appearance, 'parents': kin.parents,
			'siblings': [kin.older_brothers, kin.younger_brothers, kin.older_sisters, kin.younger_sisters],
			# structured_bio-only fields (the prose prompt keeps appearance as one field)
			'hair_type': look.hair_type, 'hair_color': look.hair_color, 'eye_color': look.eye_color,
			'build_archetype': build_archetype, 'build_tactics': build_tactics,
		}
		# Prose backstory disabled for now: the structured fact block below is meant to serve as a
		# prompt (for a GM or an AI), not a summary. generate_backstory stays wired for the website:
		# backstory = generate_backstory(_bs_brief, use_api=str(use_backstory_api).upper() == "Y", focus=backstory_focus)
		backstory = ""
		# Scannable fact block shown on the sheet's Biography tab (empty prose = no Backstory section).
		formatted_bio = structured_bio(_bs_brief)

		payload = build_payload(
			character, gear=gear, look=look, kin=kin, cf=cf, pw=pw, grants=grants, ft=ft, lk=lk,
			professions=professions, skill_ranks=skill_ranks, skill_unlock=skill_unlock, seed=seed,
			backstory=backstory, formatted_bio=formatted_bio, build_archetype=build_archetype,
			build_tactics=build_tactics, mod_char_sheet_var=mod_char_sheet_var,
			profession_ability_items=profession_ability_items, f_name=f_name, l_name=l_name)
		
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
				"equip_descrip": gear.equip_descrip,
				"maneuvers_desc_dict": pw.maneuvers_desc_dict,
				"powers_desc_dict": pw.powers_desc_dict,
				"homebrew_feat_desc_dict": pw.homebrew_feat_desc_dict,
				"feat_changes_dict": feat_changes_dict,
				"feat_conditionals_dict": feat_conditionals_dict,
				"spell_changes_dict": spell_changes_dict,
				"spell_riders_dict": spell_riders_dict,
				"selected_traits_desc": getattr(character, 'selected_traits_desc', []) or [],
				"item_changes_dict": item_changes_dict,
				"enhancement_effects_dict": enhancement_effects_dict,
				"flaw_effects_dict": character.flaw_effects,
				"class_feature_changes_dict": class_feature_changes_dict,
				"class_feature_conditionals_dict": class_feature_conditionals_dict,
				# Invariant handles for scripts/tests/test_house_invariants.py: the recorded skill-rank
				# budget (incl. the background grant) and the pre-merge normal feat count (the
				# feat_budget["normal"] export absorbs class merges/PoW funding, so it can't be
				# asserted against the house formula directly).
				"skill_rank_budget": getattr(character, 'skill_rank_budget', None),
				"normal_feat_amount": character.normal_feat_amount,
				# Inherent luck (oks/pathfinder/house-rules/luck.md) -- ONE nested block, appended at
				# the tail of the content keys so no existing key shifts position for the two
				# consumers that parse this order. None when misc_homebrew_rules is off, which is a
				# character with no luck state at all rather than a half-built one.
				# validate_payload_shape only guards the outer order; the block's own shape is
				# asserted by scripts/gates/validate_luck.py.
				"luck": lk.luck,
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
				   trainer_feats, grants.bloodline_feats, teamwork_feats):
			if isinstance(_b, list):
				_render_feat_names.extend(str(_x) for _x in _b)
		_have_desc = {str(_k).lower() for _k in pw.homebrew_feat_desc_dict}
		_need_desc = [_n for _n in dict.fromkeys(_render_feat_names) if _n.lower() not in _have_desc]
		if _need_desc:
			_desc_info = feat_spell_searcher(character, character.c_class, list(_need_desc),
											 "feats", "description", None, {}) or {}
			_desc_ci = {str(_k).lower(): (_v.get("description", "") if isinstance(_v, dict) else "")
						for _k, _v in _desc_info.items()}
			for _n in _need_desc:
				# Metzofitz picks are absent from data/feats.csv; their library supplies the text.
				# So are the E-Kat feats and Luck Traits -- they live in curated JSON, and without
				# this they reached the sheet as a bare name with no rules text at all (the module
				# synthesizes the row either way, so the failure was silent).
				pw.homebrew_feat_desc_dict[_n] = (_desc_ci.get(_n.lower(), "")
											   or metzofitz_description(_n)
											   or e_kat_description(_n)
											   or luck_trait_description(_n))

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
		# Strength of a Warrior (V4 wall pass, Sieg's Guide): each variant's value IS this
		# character's modifier, so the change is baked numeric at generation time (the same
		# convention as the @abilities bake below) -- a formula would break derive.js parity,
		# whose ledger fold only sums numbers. Type `untyped` on purpose: the doc's taken-twice
		# means the two variants stack, and pf1 would cap two same-typed natural bonuses.
		# Harmless when the feat wasn't placed: the fold below only applies entries whose name
		# is actually in _render_feat_names.
		for _soaw_name, _soaw_mod in (("Strength of a Warrior (Str)", character.str_mod),
									  ("Strength of a Warrior (Con)", character.con_mod)):
			if _soaw_mod and _soaw_mod > 0:
				_runtime_feat_changes[_soaw_name.lower()] = {
					"changes": [{"formula": str(int(_soaw_mod)), "operator": "add", "priority": 0,
								 "target": "nac", "type": "untyped"}],
					"contextNotes": []}
		for _disp in dict.fromkeys(_render_feat_names):
			_entry = _runtime_feat_changes.get(str(_disp).lower())
			if _entry is None:
				_entry = _curated_feat_changes.get(_disp)
			if _entry is not None:
				feat_changes_dict[_disp] = _entry
			if _disp in _curated_feat_conds:
				# Tier B is authored but filed "(NOT RECOMMENDED)" -- see buff_match.keep_tier_a.
				_kept = keep_tier_a(_curated_feat_conds[_disp])
				if _kept:
					feat_conditionals_dict[_disp] = _kept

		# --- Equipment numeric buffs + context notes ----------------------------------------------------
		# item_changes.json is GENERATED from items_best.json descriptions by scripts/build_item_changes.py
		# (clean numeric bonuses -> pf1 `changes`, situational bonus text -> `contextNotes`), with
		# item_changes_overrides.json merged on top at build time. Keyed by lowercase backend item name; the
		# module overlays entries onto the matched/synthesized equipment item (deduped by change target, so
		# items every_item.json already automates don't double-apply).
		_matched_items, _g = match_buffs("item", gear.equipment_list or []);   _buff_gaps += _g
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
				("weapon", gear.weapon_enhancement_chosen_list, "weapon", _wq_desc),
				("armor", gear.armor_enhancement_chosen_list, "armor", _aq_desc),
				("shield", gear.shield_enhancement_chosen_list, "armor", _aq_desc)):
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
		# Sections match the cf.class_features buckets; keys are normalized power names (lowercase, no
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
		for _bucket, _powers in (cf.class_features or {}).items():
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
				# Same tier filter as the feats above. Class-feature entries carry tier per
				# CONDITIONAL rather than on the entry, which keep_tier_a handles; before it was
				# applied here, 26 tier-B conditionals shipped as dialog toggles.
				_cf_conds = keep_tier_a(_cf_entry.get("conditionals"))
				if _cf_conds:
					class_feature_conditionals_dict[_p_name] = _cf_conds

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
		# Items the chooser rolled and rejected for not being in foundry_item_names.json.
		# This comment used to read "the retry loop working as intended, NOT a defect". That was
		# wrong, and believing it cost the generator a third of its item catalogue: the rejections
		# were a casing mismatch, not missing data, and every "X of Y" item -- the whole big six --
		# was unbuyable. See item_and_price.canonical_name_map. A NON-ZERO COUNT HERE IS A DATA
		# SIGNAL WORTH READING, not noise; gates/validate_item_names.py holds the floor.
		# Still summarized rather than folded into buff_gaps: listing every rejected roll would
		# bury the real mismatches. The names stay on character.unresolved_items.
		_unresolved = list(getattr(character, "unresolved_items", None) or {})
		if _unresolved:
			print(f"item names not in foundry_item_names.json: {len(_unresolved)} rejected roll(s), "
				  f"e.g. {', '.join(_unresolved[:3])}")
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
		# print("class_features", cf.class_features)
		# print("character.chooseable", character.chooseable)
		# print("character.skipped_feats", character.skipped_feats)
		# for key in cf.class_features["rage_powers"].keys():
		# 	print("key", key, "prereqs", cf.class_features["rage_powers"][key])

		# print(sorted(list(cf.class_features["rage_powers"].keys())))

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
		# OGL section 10 pointer -- see LICENSE_PATH. Unconditional: the payload's Open Game Content
		# is not confined to psionics, and a field that appears only for some characters would read
		# as "this one needs a licence and that one doesn't".
		character.data_dict['license_url'] = LICENSE_PATH
		return character.data_dict

# CLI smoke test only: importing this module (e.g. app.py does `from main_test import ...`) must NOT
# run a full generation -- it just defines generate_random_char for the Flask request handler to call.
if __name__ == "__main__":
	generate_random_char()

		# Mythic
		# Luck
