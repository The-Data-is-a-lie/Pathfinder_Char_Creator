# Codebase map — "where do I find X?"

Read this BEFORE grepping around. Anchors are function/key names (grep those), never line
numbers. **Keep this file updated whenever files, pools, or pipelines move.**

## Pipeline (one character, end to end)

`Backend/main_test.py :: generate_random_char()` — the whole pipeline in one function, in order:
1. `CreateNewCharacter` (state object: `Backend/utils/createACharacter.py`; export via
   `export_list_dict` / `export_list_non_dict` into `character.data_dict`).
2. gender → region → race → name → `select_classes` (multiclass) → alignment → deity → body →
   mechanical flaws (`flaw_chooser`) → personality → `randomize_level`.
3. Stats: `roll_stats` → `apply_racial_stats` → `assign_stats` → HP.
4. Spells: per class entry `caster_formula` / `spells_known_*` / `spells_per_day_*` → spellbooks.
5. Prereq pool prep: `chooseable_list*` (stats, class levels, class features, race → `character.chooseable`).
6. Class choices: `domain_chooser`, `wizard_school_chooser`, archetypes, then the generic
   choosers (see table below) → `character.data_dict['class features']`.
7. Feats (`feats.py`, trainers/professions bonus feats, feat-count guarantee), PoW + Spheres
   selection (house rule guarantees), gunslinger, gear (`armor_chooser`, `item_chooser`),
   skills/professions/skill unlock, traits, backstory.
8. Foundry buff export: feat/equipment/class-feature `*_changes_dict` + `*_conditionals_dict`
   built from the `effects`/`changes` JSONs (grep `_load_buffmap`).

Flask: `Backend/app.py` (`POST /update_character_data`, legacy `/sheet`); factory
`Backend/start_py.py`. Static data loading: `Backend/utils/data.py`. Race data: `Backend/utils/race.py`.

## Class-choice buckets (talents/powers/hexes/...)

Choosers live in `Backend/utils/class_func/generic_func.py`; calls are grouped in
`generate_random_char()` (grep `generic_class_option_chooser`).

| Bucket (`data_dict['class features']` key) | Chooser | Data: `Backend/json/class_data/` |
|---|---|---|
| rage_powers | `get_data_without_prerequisites` | barbarian.json `basic`; skald.json `basic` (shared bucket) |
| rogue/ninja/slayer_talents | same | rogue/ninja/slayer.json `basic` + `advanced` |
| discoveries (+ grand) | same / `grand_discovery_chooser` | alchemist.json `basic`,`grand` |
| investigator/vigilante/social_talents | same | investigator.json `basic`; vigilante.json `basic`,`social` |
| arcana | same | magus.json `basic` |
| hexes | `generic_class_option_chooser(multiple)` | witch.json `basic/greater/grand`; shaman.json `hexes.basic` |
| exploits | same | arcanist.json `basic`,`greater` |
| bloodline / orders / blessing / inquisitions / spirits | `generic_class_option_chooser` | sorcerer, bloodrager, cavalier, samurai, warpriest, inquisitor, shaman .json |
| mysteries / curses | same | oracle.json `mysteries.<mystery>.revelations`, `curses` |
| armor_training / weapon_training | same | fighter.json `armor_train`,`weapon_train` |
| mercy / cruelty / ki_powers | `generic_multi_chooser` (level-keyed) | paladin, antipaladin, monk .json |

Canonical pool list + walker: `SECTIONS` / `dig()` / `entry_text()` / `norm_name()` in
`Backend/scripts/build_class_feature_changes.py`. Audit for missing descriptions:
`Backend/scripts/audit_class_choice_descriptions.py`.

**Gotchas**
- `character.chooseable` = satisfied-prereq name pool; `character.chooseable_talents`
  ACCUMULATES across chooser calls (feat cross-pollination in `feats.py::choosing_feats`
  depends on it). `choosing_talents` must pick only names in ITS dataset; `spheres.py` clears
  the list around sphere picks — see comments there before "fixing" either.
- Bucket metadata: `record_bucket_owner` (`class feature owners`) and `_record_choice_level`
  (`class feature levels`) drive the Foundry sheet's per-class dividers/level tags.
- Lookup keys are normalized: lowercase, `(Su)/(Ex)/(Sp)` stripped (`norm_name`).

## Data directory map

`Backend/json/` (webscraped: Archive of Nethys, d20SRD, Metzofitz):
- `class_data/<class>.json` — per-class features + choice pools. `all_class_abiltiies.json`
  (sic) = flat name→{prerequisites,benefits} reference.
- `class_data/effects/` — class_feature_effects.json (**GENERATED** by
  `build_class_feature_changes.py`) + `_overrides.json` (curated, hand-edit this one).
- `class_data/path_of_war/` — PoW classes, Martial_Disciplines.json, maneuvers-known,
  martial-training progression, stance_auras. See `path-of-war` skill.
- `class_data/spheres/` — Spheres of Power/Might pools, talent changes, traditions. See
  `spheres-of-power` skill.
- `feats/` — feat_changes.json, feat_conditionals.json (Foundry buffs). `items/` —
  item_changes.json (**GENERATED** by `build_item_changes.py`) + `_overrides.json`,
  quality_effects.json. `spells/` — spell_changes.json, spell_riders.json. `flaws/` —
  flaw_effects.json. `backstory_examples/` — few-shot examples for the backstory API.
- Loose files: races (races.json, PlayableRaces.json, racial_stat_changes.json), deity.json,
  archetypes.json, cleric/druid_domains.json, wizard_schools.json, bloodlines.json,
  witch_patrons.json, spirits.json, items.json/items_best.json, weapons_data.json,
  armor/weapon_qualities.json, feat_tax.json, profession_*.json, campaign_lore.json,
  foundry_item_names.json, spells_known/per_day.json.

`data/` — CSVs: feats.csv / feats_new.csv (main feat data), Metzofitz_Feats.csv (homebrew),
spells.csv, traits.csv, class_ability.csv.

## `Backend/utils/class_func/` module index (grep the function, not the file)

feats.py (feat selection + `bonus_searcher`, `no_prereq_loop` consumers) · generic_func.py
(all generic choosers) · class_abilities.py (fixed per-level abilities + descriptions) ·
spells.py / adding_bonus_spells.py · stats.py · hp_rolls.py · level_and_bab.py ·
skill_ranks.py / skill_unlocks.py · armor_and_weapon_chooser.py / armor_and_enhancements.py /
item_and_price.py · path_of_war.py / path_of_war_funcs.py · spheres.py · wizard_school.py ·
domain_inquisition.py · gunslinger.py · animal_companions.py · versatile_performance.py ·
traits.py · flaws.py / randomize_flaw.py · feat_tax.py · trainers.py / profession_chooser.py /
profession_abilities.py · backstory.py / build_archetype.py (Ollama build→archetype classifier,
heuristic fallback) / personality.py / appearance.py / family_func.py ·
alignment_and_deity.py · race_func.py · favored_class.py · language.py · chooseable.py /
feats_to_chooseable.py / flag_assign.py · luck_and_mythic.py · hero_point_generator.py ·
class_specific_feats.py / extra_combat_feats.py / extra_magic_feats.py · grand_discovery.py

## `Backend/scripts/` index

- `build_*.py` → GENERATE the `*_changes.json` / effects files (item, feat, spell, class
  feature, maneuver, stance, talent). Never hand-edit generated output; edit the
  `*_overrides.json` and rerun the build script.
- `build_spell_buffs.py` → writes `spell_buffs.json` into the MODULE repo
  (`templates/character_sheet_folder/`), not `Backend/json/`. Reuses the sentence classifier
  from `build_item_changes.py` (item-style buckets: changes / contextNotes / unplaced;
  unplaced-only spells get no Buffs-tab buff), layers curated `json/spells/spell_changes.json`
  on top (curated wins per target). Spell-conditionals plan: `docs/feature_spec_todo.md` §7.
- `validate_*.py` → CI-style checks (class_feature_effects, flaw_effects, quality_effects).
- `audit_class_choice_descriptions.py` → flags choice-pool entries with empty/trivial text.
- `fix_*.py`, `scrape_*.py`, `_smoke_*.py`, `compile_feats_new.py` — one-off converters,
  scrapers, smoke tests.

## Consumers / deploys (details in auto-memory + skills)

- FoundryVTT module `pf1e_random_char_generator`: repo in `%LOCALAPPDATA%`-adjacent
  `FoundryVTT\Data\modules` (NOT Documents\GitHub); GitLab MRs; release via its `release.ps1`.
- Web sheet: standalone `Pathfinder-Character-Sheet` repo in `FoundryVTT\Data`
  (Flask `/sheet` is the legacy copy).
- Backend deploy: Docker Hub image + Render, via `deploy.ps1`.

## Docs & rules

`docs/homebrew_rules.md` (house rules — source of truth) · `docs/feature_spec_todo.md` (PoW
spec) · `docs/pow_conditional_decision_rules.md` / `spheres_conditional_decision_rules.md` ·
project skills in `.claude/skills/` (path-of-war, spheres-of-power, trainers-and-professions,
foundry-conditionals, multi-buff-distributor, changelog, commit-conventions).
