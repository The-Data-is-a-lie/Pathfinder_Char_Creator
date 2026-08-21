"""The generator's output contract, declared once instead of implied by a dict literal.

WHY THIS MODULE EXISTS
----------------------
The payload is what TWO OTHER REPOSITORIES read -- the `pf1e_random_char_generator` FoundryVTT
module and the standalone web character sheet -- and both read it POSITIONALLY. `app.py` sets
`JSON_SORT_KEYS = False` deliberately for that reason. Until now the contract was expressed as the
insertion order of a dict literal in the middle of a 2,700-line file, so inserting a key in the
wrong place breaks nothing here and breaks somebody's character sheet in another repository.

`PAYLOAD_KEYS` states that order, and `scripts/gates/validate_payload_shape.py` fails when the built
payload stops matching it -- making the contract greppable from the consuming repos rather than
inferred from a diff.

WHAT build_payload DERIVES RATHER THAN RECEIVES
----------------------------------------------
Bucket 2 of the phase-output rule in `class_func/pipeline.py`: values that are a pure unpacking of
state the character already carries are computed HERE and stored nowhere. `armor_name` and its five
siblings fall out of `character.armor_dict`; `deity_name` out of `deity_choice`;
`school`/`opposing_school` out of the chosen-school attributes; `archetype_info` is `json.dumps` of
the attribute. Promoting those would have added ~15 names to an object already carrying ~200, for
values nothing but the export reads.

THE FOUR QUIRKS, NOW FIXED (gear-legality plan, step 3)
-------------------------------------------------------
This module used to record two quirks it had deliberately preserved through the extraction, on the
grounds that fixing them was a behaviour change owed its own commit. That commit is `gear_display`
below, and pulling the thread found two more of the same shape -- a lookup that misses and yields a
falsy default, which is the failure mode the whole gear-legality plan is about:

  * `spell_failure` (twice) -- `armor.json`'s key is `arcane spell failure chance`, so arcane
    spell failure was `0` on every character ever generated, armour and shield alike.
  * `shield check penalty` -- the key is `armor check penalty` for shields too.
  * `shield_max_dex_bonus` read `armor_dict`, not the shield's, so `optimized_wall`'s shield
    reported the Full plate's `1`. Every shield in `armor.json` has an empty max-dex, correctly.
  * `armor_dict` was bound only inside the armour branch, so a character with no armour but a
    shield raised NameError. That was unreachable while every character wore armour; step 4 of the
    plan makes `armor_type = None` mean NO ARMOUR, which reaches it.

Emitted values are the ITEM's printed values, as raw strings, exactly like `max dex bonus` and
`armor check penalty` already were -- `'35%'`, not `35` and not a character-level number. Per
ruling D4 the arcane-spell-failure EXEMPTIONS some classes carry (bard, bloodrager, magus, skald,
summoner; see `armor_proficiency.json`) are deliberately NOT folded in here: an exemption belongs
to the character and cannot survive a multiclass caster, while this field describes the item.
"""
import json

from utils import data
from utils.class_func.spells import casting_stat_for

# ---------------------------------------------------------------------------------------------- #
# THE CONTRACT.
#
# The exact key order of a generated character, as the FoundryVTT module and the web sheet read it.
# `app.py` sets JSON_SORT_KEYS = False so this order survives serialization; both consumers rely on
# it. Adding a key means adding it HERE, in the position it is inserted -- and
# `scripts/gates/validate_payload_shape.py` fails until you do.
#
# Note the last three: `buff_gaps` is assigned after the buff-matching pass, and
# `generator_version`/`license_url` are stamped onto data_dict rather than onto the payload dict.
# Ticket 09 flagged that discrepancy and asked for it to be a STATED decision rather than an
# accident: they are part of the shipped contract, so the manifest covers them, and it covers them
# at the end because that is where they land.
#
# Generated from a real run rather than transcribed. Regenerate deliberately, never reflexively --
# a diff here is a change to what two other repositories parse.
PAYLOAD_KEYS = (
	'class features',
	'class feature levels',
	'class feature owners',
	'region',
	'chosen_race',
	'land_speed',
	'character_full_name',
	'c_class',
	'c_class_display',
	'c_class_2',
	'alignment',
	'age_number',
	'height_number',
	'weight_number',
	'dex',
	'str',
	'con',
	'int',
	'wis',
	'cha',
	'inherents',
	'level_up_stats',
	'racial_stats',
	'flaw',
	'Total_HP',
	'sheet_health',
	'bab_total',
	'armor_ac',
	'shield_ac',
	'armor_name',
	'armor_spell_failure',
	'armor_weight',
	'armor_armor_check_penalty',
	'armor_max_dex_bonus',
	'shield_name',
	'shield_spell_failure',
	'shield_weight',
	'shield_armor_check_penalty',
	'shield_max_dex_bonus',
	'spell_list_choose_from',
	'day_list',
	'known_list',
	'spells_prepared_per_level',
	'martial_disciplines',
	'initiator_level',
	'maneuvers_known_list',
	'maneuvers_readied_list',
	'maneuvers_choose_from',
	'maneuvers_readied_names',
	'stances_chosen',
	'mt_feats',
	'initiation_stat',
	'manifesters',
	'magic_talent_items',
	'combat_talent_items',
	'sphere_feats',
	'sphere_feat_tax',
	'sphere_mana_pool',
	'spheres_chosen',
	'sphere_counts',
	'casting_tradition',
	'sphere_drawbacks',
	'sphere_boons',
	'sphere_traits',
	'deity_name',
	'skill_ranks',
	'weapon_enhancement_chosen_list',
	'armor_enhancement_chosen_list',
	'shield_enhancement_chosen_list',
	'weapon_enhancement_bonus',
	'armor_enhancement_bonus',
	'shield_enhancement_bonus',
	'selected_traits',
	'equipment_list',
	'level',
	'archetype1',
	'hair_color',
	'hair_type',
	'eye_color',
	'appearance',
	'language_text',
	'feats',
	'teamwork_feats',
	'teamwork_feat_labels',
	'story_feats',
	'flaw_feats',
	'class_feats',
	'class_feat_labels',
	'flavor_feats',
	'bloodline_feats',
	'bloodline_feat_labels',
	'trainer_feats',
	'trainer_feat_labels',
	'trainer_feat_tax_dict',
	'trainer_calibers',
	'profession_feats',
	'profession_feat_desc',
	'profession_ranks',
	'profession_pool',
	'profession_ability_items',
	'skill_unlock',
	'gold',
	'platnium',
	'animal_companion',
	'bonded_creatures',
	'full_domain',
	'school',
	'opposing_school',
	'bloodline',
	'background_traits',
	'professions',
	'craft_type',
	'mannerisms',
	'personality_traits',
	'hero_points',
	'gender',
	'class_ability_desc',
	'class_ability',
	'class_features',
	'class_feature_levels',
	'archetype_info',
	'parents',
	'older_brothers',
	'younger_brothers',
	'older_sisters',
	'younger_sisters',
	'weapon_name',
	'specialty_schools',
	'counter_schools',
	'chosen_spell_descriptor',
	'counter_spell_descriptor',
	'total_rolled_hp',
	'mini_alignment',
	'casting_level_str_foundry',
	'main_stat',
	'story_feat_tax_dict',
	'flaw_feat_tax_dict',
	'flavor_feat_tax_dict',
	'class_feat_tax_dict',
	'feats_feat_tax_dict',
	'feat_budget',
	'mod_char_sheet_var',
	'backstory',
	'formatted_bio',
	'classes',
	'total_level',
	'save_bases',
	'spellbooks',
	'class_feature_owners',
	'build_archetype',
	'build_tactics',
	'generation_seed',
	'spell_list_choose_from_dict',
	'equip_descrip',
	'maneuvers_desc_dict',
	'powers_desc_dict',
	'homebrew_feat_desc_dict',
	'feat_changes_dict',
	'feat_conditionals_dict',
	'spell_changes_dict',
	'spell_riders_dict',
	'selected_traits_desc',
	'item_changes_dict',
	'enhancement_effects_dict',
	'flaw_effects_dict',
	'class_feature_changes_dict',
	'class_feature_conditionals_dict',
	'skill_rank_budget',
	'normal_feat_amount',
	'luck',
	# Mythic (mythic map, ticket 05): ONE namespaced block at the tail, the luck precedent --
	# tier, path, chassis numbers, path abilities, tradition, mythic feats, spell annotations.
	# None for a non-mythic character; the block's own shape is validate_mythic.py's to assert.
	'mythic',
	'buff_gaps',
	# Oversized weapons (gear-legality plan, D11). A MARKER, never scaled damage dice: three things
	# downstream already know how to scale and a fourth here could only disagree with them. The
	# FoundryVTT module writes `weapon_size_steps` straight into the `sizefordamage` resource it
	# already puts on every generated sheet; the web sheet pre-scales for display. `steps` is 0 on
	# an ordinary character, which makes the other three inert.
	'weapon_size',
	'weapon_size_steps',
	'weapon_size_source',
	'weapon_size_attack_penalty',
	'generator_version',
	'license_url',
)


# armor.json's own key names. Spelled out here because three of the four bugs this function used to
# have were a lookup guessing at one of them and getting a falsy default instead of an error.
_ASF_KEY = 'arcane spell failure chance'
_ACP_KEY = 'armor check penalty'
_MAX_DEX_KEY = 'max dex bonus'


def _worn_item(entry):
	"""({name, stats}) for a `{name: {...}}` slot dict, or None when nothing is worn.

	One reader for both slots: a shield is an `armor.json` row like any other and its stats live
	under the same keys, which is precisely what the old `'shield check penalty'` lookup assumed
	otherwise.
	"""
	if not isinstance(entry, dict) or not entry:
		return None
	name = next(iter(entry))
	stats = entry.get(name)
	return (name, stats) if isinstance(stats, dict) else None


def gear_display(character):
	"""Unpack the equipped armour and shield into the flat fields the sheets read."""
	armor = _worn_item(character.armor_dict)
	if armor is not None:
		armor_name, armor_stats = armor
		armor_spell_failure = armor_stats.get(_ASF_KEY, 0)
		armor_armor_check_penalty = armor_stats.get(_ACP_KEY, 0)
		armor_weight = armor_stats.get('weight', 0)
		armor_max_dex_bonus = armor_stats.get(_MAX_DEX_KEY, 0)
		if armor_max_dex_bonus is None:
			armor_max_dex_bonus = 0
	else:
		armor_name = 0
		armor_spell_failure = 0
		armor_armor_check_penalty = 0
		armor_weight = 0
		armor_max_dex_bonus = 0

	shield = _worn_item(character.shield_dict)
	if shield is not None:
		shield_name, shield_stats = shield
		shield_spell_failure = shield_stats.get(_ASF_KEY, 0)
		shield_armor_check_penalty = shield_stats.get(_ACP_KEY, 0)
		shield_weight = shield_stats.get('weight', 0)
		# The SHIELD's own max dex, which every shield in armor.json leaves empty -- correctly, a
		# shield imposes no Dex cap. This used to read `armor_dict` and hand the sheet the body
		# armour's number.
		shield_max_dex_bonus = shield_stats.get(_MAX_DEX_KEY, 0)
		if shield_max_dex_bonus is None:
			shield_max_dex_bonus = 0
	else:
		shield_name = " "
		shield_spell_failure = " "
		shield_armor_check_penalty = " "
		shield_weight = " "
		shield_max_dex_bonus = " "
	return dict(
		armor_name=armor_name,
		armor_spell_failure=armor_spell_failure,
		armor_armor_check_penalty=armor_armor_check_penalty,
		armor_weight=armor_weight,
		armor_max_dex_bonus=armor_max_dex_bonus,
		shield_name=shield_name,
		shield_spell_failure=shield_spell_failure,
		shield_armor_check_penalty=shield_armor_check_penalty,
		shield_weight=shield_weight,
		shield_max_dex_bonus=shield_max_dex_bonus,
	)


def _deity_name(character):
	"""deity.json "Name" is a LIST of aliases since the homebrew-deities rework (091da54). Export ONE
	string: pf1's details.deity is a StringField, and an array crashes the actor's data preparation
	on import -- the sheet dies reading the underived encumbrance."""
	deity_choice = character.deity_choice
	deity_name = deity_choice.get("Name", "") if isinstance(deity_choice, dict) else deity_choice
	if isinstance(deity_name, list):
		deity_name = deity_name[0] if deity_name else ""
	return deity_name


def build_payload(character, *, gear, look, kin, cf, pw, grants, ft, lk, professions, skill_ranks,
				  skill_unlock, seed, backstory, formatted_bio, build_archetype, build_tactics,
				  mod_char_sheet_var, profession_ability_items, f_name, l_name):
	"""Assemble the ordered payload. Key ORDER is the contract -- see PAYLOAD_KEYS."""
	_g = gear_display(character)
	armor_name = _g['armor_name']
	armor_spell_failure = _g['armor_spell_failure']
	armor_armor_check_penalty = _g['armor_armor_check_penalty']
	armor_weight = _g['armor_weight']
	armor_max_dex_bonus = _g['armor_max_dex_bonus']
	shield_name = _g['shield_name']
	shield_spell_failure = _g['shield_spell_failure']
	shield_armor_check_penalty = _g['shield_armor_check_penalty']
	shield_weight = _g['shield_weight']
	shield_max_dex_bonus = _g['shield_max_dex_bonus']

	character_full_name = f_name + ' ' + l_name
	deity_name = _deity_name(character)
	school = character.chosen_school if character.chosen_school else "N/A"
	opposing_school = (character.chosen_opposing_school
					   if character.chosen_opposing_school else "N/A")
	archetype_info = json.dumps(character.archetype_info, indent=4)

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
			"alignment": character.alignment_display,
			"age_number": character.age,
			"height_number": character.height,
			"weight_number": character.weight,
			"dex": character.dex,
			"str": character.str,
			"con": character.con,
			"int": character.int,
			"wis": character.wis,
			"cha": character.cha,
			"inherents": character.inherents,
			"level_up_stats": character.level_up_stats,
			"racial_stats": character.racial_stats,
			"flaw": character.flaw,
			"Total_HP": character.Total_HP,
			"sheet_health": character.sheet_health,
			"bab_total": character.bab_total,
			"armor_ac": gear.armor_ac,
			"shield_ac": gear.shield_ac,
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
			"day_list": character.spells_per_day_list,
			"known_list": character.spells_known_list,
			"spells_prepared_per_level": character.spells_prepared_per_level,
			"martial_disciplines": pw.martial_disciplines,
			"initiator_level": pw.initiator_level,
			"maneuvers_known_list": pw.maneuvers_known_list,
			"maneuvers_readied_list": pw.maneuvers_readied_list,
			"maneuvers_choose_from": pw.maneuvers_choose_from,
			"maneuvers_readied_names": pw.maneuvers_readied_names,
			"stances_chosen": pw.stances_chosen,
			"mt_feats": pw.mt_feats,
			"initiation_stat": pw.initiation_stat,
			# Psionics: a list beside spellbooks, one entry per psionic class. Its sibling
			# pw.powers_desc_dict sits with the other description dicts further down, exactly as
			# pw.maneuvers_desc_dict does for Path of War.
			"manifesters": pw.manifesters,
			"magic_talent_items": pw.magic_talent_items,
			"combat_talent_items": pw.combat_talent_items,
			"sphere_feats": pw.sphere_feats,
			"sphere_feat_tax": pw.sphere_feat_tax,
			"sphere_mana_pool": pw.sphere_mana_pool,
			"spheres_chosen": pw.spheres_chosen,
			"sphere_counts": pw.sphere_counts,
			"casting_tradition": pw.casting_tradition,
			"sphere_drawbacks": pw.sphere_drawbacks,
			"sphere_boons": pw.sphere_boons,
			"sphere_traits": pw.sphere_traits,
			"deity_name": deity_name,
			"skill_ranks": skill_ranks,
			"weapon_enhancement_chosen_list": gear.weapon_enhancement_chosen_list,
			"armor_enhancement_chosen_list": gear.armor_enhancement_chosen_list,
			"shield_enhancement_chosen_list": gear.shield_enhancement_chosen_list,
			"weapon_enhancement_bonus": gear.weapon_enhancement_bonus,
			"armor_enhancement_bonus": gear.armor_enhancement_bonus,
			"shield_enhancement_bonus": gear.shield_enhancement_bonus,
			"selected_traits": look.selected_traits,
			"equipment_list": gear.equipment_list,
			"level": character.c_class_level,
			# Subrace data (chosen_subrace, subrace_description) is deliberately not exported -- FoundryVTT
			# doesn't use it and the generator's subrace handling needs fixing first.
			"archetype1": character.archetype1,
			"hair_color": look.hair_color,
			"hair_type": look.hair_type,
			"eye_color": look.eye_color,
			"appearance": look.appearance,
			"language_text": look.language_text,
			"feats": ft.feats,
			"teamwork_feats": ft.teamwork_feats,
			"teamwork_feat_labels": ft.teamwork_feat_labels,
			"story_feats": ft.story_feats,
			"flaw_feats": ft.flaw_feats,
			"class_feats": ft.class_feats,
			"class_feat_labels": ft.class_feat_labels,
			"flavor_feats": ft.flavor_feats,
			"bloodline_feats": grants.bloodline_feats,
			"bloodline_feat_labels": grants.bloodline_feat_labels,
			"trainer_feats": ft.trainer_feats,
			"trainer_feat_labels": ft.trainer_feat_labels,
			"trainer_feat_tax_dict": ft.trainer_feat_tax_dict,
			"trainer_calibers": ft.trainer_calibers,
			"profession_feats": ft.profession_feats,
			"profession_feat_desc": ft.profession_feat_desc,
			"profession_ranks": ft.profession_ranks,
			"profession_pool": ft.profession_pool,
			"profession_ability_items": profession_ability_items,
			"skill_unlock": skill_unlock,
			"gold": character.gold,
			"platnium": character.platnium,
			# Animal companion stat block (issue #15, sheet repo): everything the
			# generator already computed for a companion druid — species stats
			# (with the 7th-level advancement block), the level chassis row from
			# animal_companion.json, and the rolled ft.feats (previously discarded).
			# None when the druid went domain or there is no druid.
			# FROZEN, DELIBERATELY (#37 grill, 2026-08-03). This key is the deprecated
			# alias D7 keeps for the sheet repo's #15 consumer; `name`, `sex`, `gear`
			# and `gear_source` live only on `bonded_creatures` (#32). Do not "fix" the
			# missing name here — a deprecated key that is never worse than its
			# replacement never dies, and the name is the only reason to migrate.
			"animal_companion": ({
				"species": character.chosen_animal,
				"kind": getattr(character, "chosen_animal_kind", None),
				"species_stats": character.chosen_animal_description,
				"chassis": character.companion_info,
				"feats": sorted(character.animal_companion_feats) if character.animal_companion_feats else [],
			} if getattr(character, "chosen_animal", None) else None),
			# D7 / #32: the list that replaces the singular alias above. One entry per bonded
			# creature -- companion, mount, familiar, eidolon -- INCLUDING the absences, whose
			# `outcome` is the only record of why a druid has a domain instead of a wolf.
			# `stats` is the finished block from #31 and is FINAL: D2 makes this the sole source
			# of a companion's numbers, because the standalone web sheet has no game system to
			# derive them from. A renderer displays them; it never re-derives them, and it never
			# re-applies `stats.size_change`, which is provenance for numbers already totalled in.
			"bonded_creatures": getattr(character, "bonded_creatures", None) or [],
			"full_domain": character.chosen_domain,
			"school": school,
			"opposing_school": opposing_school,
			"bloodline": character.bloodline,
			"background_traits": character.background_traits,
			# NOT the personality flavour list rolled in phase_alignment_and_level -- these are
			# the TRAINER professions from phase_professions_and_skills, which used to overwrite
			# the same local 240 lines later. Two unrelated things shared one name; only this one
			# was ever read.
			"professions": professions,
			"craft_type": character.craft_chosen,
			"mannerisms": character.mannerisms,
			"personality_traits": character.personality_traits,
			# From the LUCK record, not the appearance one: phase_appearance_and_traits still rolls
			# the starting count, but "It Just Works" grants a free hero point per session and that
			# feat is not known until the feat tax and swap pass has finished. Same value on every
			# character without the feat.
			"hero_points": lk.hero_points,
			"gender": character.chosen_gender,
			"class_ability_desc": kin.class_ability_desc,
			"class_ability": kin.class_ability,
			"class_features": cf.class_features,
			"class_feature_levels": cf.class_feature_levels,
			"archetype_info": archetype_info,
			"parents": kin.parents,
			"older_brothers": kin.older_brothers,
			"younger_brothers": kin.younger_brothers,
			"older_sisters": kin.older_sisters,
			"younger_sisters": kin.younger_sisters,
			"weapon_name": gear.weapon_name,
			"specialty_schools": character.specialty_schools,
			"counter_schools": character.counter_schools,
			"chosen_spell_descriptor": character.chosen_descriptors,
			"counter_spell_descriptor": character.counter_descriptors,
			"total_rolled_hp": character.total_hp_rolls,
			"mini_alignment": character.mini_alignment,
			"casting_level_str_foundry": cf.casting_level_str_foundry,
			"main_stat": character.main_stat,
			"story_feat_tax_dict": ft.story_feat_tax_dict,
			"flaw_feat_tax_dict": ft.flaw_feat_tax_dict,
			"flavor_feat_tax_dict": ft.flavor_feat_tax_dict,
			"class_feat_tax_dict": ft.class_feat_tax_dict,
			"feats_feat_tax_dict": ft.feats_feat_tax_dict,
			"feat_budget": ft.feat_budget,
			"mod_char_sheet_var": mod_char_sheet_var,
			"backstory": backstory,
			"formatted_bio": formatted_bio,
			# --- multiclass (new keys; the legacy keys above keep their old semantics:
			#     "level" = primary-class level, "c_class"/"c_class_2" = primary/second class) ---
			"classes": [{'name': c['name'], 'display': c['display'], 'level': c['level'],
				'archetype': character.archetypes_per_class[i]
							 if i < len(character.archetypes_per_class) else {}}
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
			"class_feature_owners": cf.class_feature_owners,
			"build_archetype": build_archetype,
			"build_tactics": build_tactics,
			# Replay handle: pass this back as generate_random_char(seed=...) to reproduce this
			# exact character. See Backend/scripts/tests/test_golden_payload.py.
			"generation_seed": seed,
			}
	return payload
