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

Flask: `Backend/app.py` (`POST /update_character_data`, legacy `/sheet`, `GET /license` — the OGL
text payloads point at via `license_url`, required because serving extracted 3pp mechanics is
Distribution under OGL §10); factory
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
- `class_data/psionics/` — **GENERATED** by `scrape_psionics.py` from the Library of Metzofitz wiki
  (+ d20pfsrd for races); gated by `validate_psionics_data.py`. `psionic_classes.json` (12 classes,
  20-row tables, derived bab/hit-die/skills/saves), `psionic_powers_known.json` (20-int arrays,
  index = level − 1 — the PoW convention, not the 21-int spell one), `psionic_power_lists.json`,
  `psionic_powers.json` (660), `psionic_races.json` (10), `psionic_class_options.json` (9 classes'
  subsystem option lists), `psionic_name_map.json` (generated names → `pf1-psionics` pack names).
  `NOTICE.md` marks the whole subtree as Open Game Content. **Wired in** — `class_func/psionics.py`
  reads these; the twelve classes are in `class_data.json` and in the random pool.
  The per-class option files (`class_data/aegis.json`, `cryptic.json`, …) are **GENERATED** from
  this subtree by `build_psionic_class_data.py` and live one level up, under the class's own name,
  because `generic_class_option_chooser` looks them up that way.
- `feats/` — feat_changes.json, feat_conditionals.json (Foundry buffs). `items/` —
  item_changes.json (**GENERATED** by `build_item_changes.py`) + `_overrides.json`,
  quality_effects.json. `spells/` — spell_changes.json, spell_riders.json. `flaws/` —
  flaw_effects.json. `backstory_examples/` — few-shot examples for the backstory API.
- **Bonded creatures** — `animal_companion.json` (`companion` = the level chassis, rows `"1"`–`"40"`
  keyed by *effective* level, carrying that row's own `feats` count; `feats` = a flat 27-name bag) and
  `animal_choices.json` (`normal` 157 / `plant` 14 / `vermin` 23 / `magical_beast` 2 species →
  `starting statistics` plus one or more `"<N>th-level advancement"` delta blocks, keys lowercase and
  comma-inverted: `"ant, giant"`). Read by `class_func/animal_companions.py` (**druid-only today**, no
  stat-block math, advancement block never merged).
  - **`magical_beast` is not in the random roll.** `animal_chooser` reads only `normal` / `plant` /
    `vermin`, which is what keeps griffon and hippogriff reachable solely through a curated archetype
    species pool — their RAW availability.
  - **Ability values are typed by block:** `starting statistics` holds bare ints (absolute scores),
    advancement blocks hold signed strings (deltas). A bare int in an advancement block means a sign
    was lost — the defect `scripts/repair_animal_choices.py` fixed and
    `scripts/validate_companion_data.py` gates.
  - **The size package is NOT a constant.** PF1e's size-change table scales with the transition
    (Small→Medium Str +4/Con +2; Medium→Large Str +8/Con +4; Large→Huge natural armor +3), and 97 of
    153 published size-ups disagree with even that. The per-species entry is the authority; the
    validator reports the deviation as WARN and fails only on the impossible (positive Dex on a size
    increase, unsigned delta, malformed `ac`). `SIZE_CHANGE_TABLE` lives in the validator.
  - **The `outcome` / `effect` / `flags` closed vocabulary (D8, #38) is owned by
    `validate_companion_data.py`** as module constants — import from there, never restate. It
    validates `companion_grantors.json` / `companion_archetypes.json` against them once they exist.
  - `companion_species_aliases.json` maps the spellings archetype `species_pool` entries use
    (`"giant weasel"`, `"dire bat"`) onto this file's keys (`"weasel, giant"`, `"bat, dire"`), and
    records species PF1e has no companion stat block for (giant eagle). **Resolve through it before
    reporting a species as missing.**
  - Scripts: `scripts/repair_animal_choices.py` (idempotent scrape repair) ·
    `scripts/scrape_companion_species.py` (adds species from d20pfsrd).
  - `companion_archetypes.json` is **GENERATED** by `scripts/build_companion_archetypes.py` from
    archetype prose (206 archetypes across the ten grantor classes);
    `companion_archetypes_overrides.json` is hand-authored and **wins**;
    `scripts/validate_companion_archetypes.py` gates the pair. Sign-off worksheet:
    `docs/companion_archetype_signoff.md` (regenerate with `--review`; never hand-edit it).
    - Entries carry **`effects`, a list**, as well as the single-valued `effect` primary. 33
      archetypes genuinely have two (Devolutionist forces a species *and* suppresses the size step),
      which #38's one-effect vocabulary cannot express.
  - `pf_content_companions.json` is **GENERATED** by `scripts/dump_pf_content_actors.py` (Foundry
    must be closed — LevelDB is single-writer). `scripts/validate_companion_names.py` diffs our
    species against it; a miss is a WARN, because degrading to a bare `npc` is legitimate (D3) but
    a *silent* miss is not.
  - Still absent: `companion_grantors.json`, `familiar_master_table.json`, `familiar_choices.json`,
    `eidolon_base_forms.json`.
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
item_and_price.py · path_of_war.py / path_of_war_funcs.py · psionics.py (power selection, power
points, manifester level, the `manifesters` payload block, soulknife mind blade) · spheres.py ·
wizard_school.py ·
domain_inquisition.py · gunslinger.py · animal_companions.py (druid-only companion pick; the
grantor resolver, advancement merge and stat-block math are specced in `feature_spec_todo.md` §8 but
**not built**) · versatile_performance.py ·
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
  on top (curated wins per target).
- `build_spell_conditionals.py` → drafts `json/spells/spell_conditionals.draft.json` in three
  buckets: A (attack/damage buffs → curated `spell_changes.json`), B (touch-attack riders) and
  C (offensive non-touch: area/save damage, save-or-suffer, debuffs) → both curated into
  `spell_riders.json` (C uses `attack: null`; explicit save+effect riders, numbers in `[[ ]]`).
  Gate: `validate_spell_conditionals.py`. Status/curation state: `docs/feature_spec_todo.md` §7.
- `promote_spell_conditionals.py` → bulk-merges reviewed `spell_conditionals.draft.json` entries
  into curated `spell_riders.json` / `spell_changes.json` (curation wins; drops harmless-save
  misreads, `(see spell description)` C stubs, and save-less/rider-less B shells). Idempotent; run
  `validate_spell_conditionals.py` after. Grew riders 239 → 619.
- `build_spell_rider_worklist.py` + `merge_spell_riders.py` → the detailed-effect sweep tooling.
  The worklist slices `spell_riders.json` + `data/spells.csv` into per-batch files for LLM authoring
  (`has_modifier_damage` flags touch spells whose damage rolls as a modifier — checked against the
  applier's `spell_damage_index.json` — so the agent doesn't double-state it); the merge writes the
  authored `effect` back as the single rider + corrected save. Run `enrich_conditional_riders.py` +
  `validate_spell_conditionals.py` after. Samples: `docs/spell_rider_pilot_samples.md`.
- `conditional_clauses.py` + `enrich_conditional_riders.py` → the six-detail labeled-clause layer.
  `conditional_clauses.py` holds the shared idempotent builders (`Cost:`/`Activation:`/`Range:`/
  `Save:`/`Effect:`); `enrich_conditional_riders.py` appends only the *missing* clauses to the
  curated `spell_riders.json`/`spell_changes.json` (repo) + the module's `*_talent_conditionals.json`
  (CL-scaled range from the CSV `range` col, gp cost, spell save DC `[[ 10 + @slvl + @castMod ]]`,
  real talent spell-point counts). Re-runnable no-op; `build_*` reuse the helpers. See
  `docs/spheres_conditional_decision_rules.md`.
- The curated `spell_riders.json` / `spell_changes.json` are also consumed OUTSIDE this repo by the
  **`pf1-conditional-applier`** repo — a run-on-demand Foundry macro that scans an actor and, via a
  per-weapon review/edit pop-up (toggle on/off, edit clauses, persistent per-weapon overrides),
  attaches its Path of War + Spheres + spell (A/B/C) conditionals onto a chosen weapon (idempotent,
  with a gap report). It supersedes the removed **"Spell Conditionals (Rider Spells)"** LevelDB compendium
  pack (whose builder `build_spell_conditional_compendium.py` + `_compendium/` were deleted here and
  preserved in that repo's `build/`).
- `scrape_psionics.py` → GENERATES everything in `json/class_data/psionics/` from the Library of
  Metzofitz wiki + d20pfsrd. Idempotent; `--only classes|lists|powers|races`. **Access gotcha:**
  fandom's `/wiki/<Page>` URLs are behind a Cloudflare JS challenge (WebFetch → 402, curl → challenge
  page); `api.php` is not. Needs the repo venv (`.venv/Scripts/python.exe`) — `C:\Python310` has no
  `requests`. `lxml`/`html5lib` are absent, so tables are walked with bs4, not `pandas.read_html`.
- `build_psionic_class_data.py` → merges the scraped classes into `json/class_data.json` (adding the
  `manifesting_stat` key beside `main_stat`) and GENERATES the per-class option files
  `json/class_data/<class>.json` for the nine subsystem classes.
- `reconcile_psionics_names.py` → GENERATES `psionic_name_map.json`, mapping our scraped names onto
  the `pf1-psionics` pack names the Foundry module can actually resolve. Unmapped names fail
  `validate_psionics_data.py`. Pack contents are dumped by `dump_foundry_pack.mjs` (node).
- `build_ogl_license.py` → GENERATES root `LICENSE-OGL.txt` (verbatim OGL 1.0a copied from an
  on-disk source + a §15 curated for THIS project) and the psionics `NOTICE.md`. Never hand-edit
  either file; edit the script. It refuses to write a licence whose operative text is truncated.
- `validate_*.py` → data gates (class_feature_effects, flaw_effects, quality_effects, psionics_data,
  companion_data, companion_names, companion_archetypes, …).
  `validate_psionics_data.py` cross-checks every manifesting class's power-points
  column against the three progressions `pf1-psionics` hardcodes, so a scrape regression fails loudly.
  - **`validate_all.py` runs every one of them** (glob discovery — a new validator is covered the
    moment it exists), and `.github/workflows/validate.yml` runs *that* plus a trimmed
    `test_house_invariants.py` on push. Before this the eleven validators were manual and nothing
    invoked them.
- `audit_class_choice_descriptions.py` → flags choice-pool entries with empty/trivial text.
- `fix_*.py`, `scrape_*.py`, `_smoke_*.py`, `compile_feats_new.py` — one-off converters,
  scrapers, smoke tests.

## Consumers / deploys (details in auto-memory + skills)

- **The blessed table workflow is two-step**: (1) generate + inject an NPC with the
  `pf1e_random_char_generator` module, (2) run the `pf1-conditional-applier` macro on the actor to
  wire class-feature/PoW/Spheres/spell conditionals onto its weapons. There is deliberately no
  creation-time conditional consumer — the applier is idempotent and handles retargets/labels.
  User-facing walkthrough: the module repo's `README.md`.
- FoundryVTT module `pf1e_random_char_generator`: repo in `%LOCALAPPDATA%`-adjacent
  `FoundryVTT\Data\modules` (NOT Documents\GitHub); GitLab MRs; release via its `release.ps1`.
- Web sheet: standalone `Pathfinder-Character-Sheet` repo in `FoundryVTT\Data`
  (Flask `/sheet` is the legacy copy).
- Backend deploy: Docker Hub image + Render, via `deploy.ps1`.

## Docs & rules

`docs/homebrew_rules.md` (house rules — source of truth) · `docs/feature_spec_todo.md` (PoW
spec) · `docs/pow_conditional_decision_rules.md` / `spheres_conditional_decision_rules.md`.

**In-flight design efforts** live under `docs/wayfinder/<effort>/` — a `map.md` (destination,
locked decisions, decisions-so-far index, fog, out-of-scope) plus one file per decision ticket in
`issues/`. A ticket is a *question*, not a task; the **frontier** is every open, unclaimed ticket
whose `Blocked by:` list is fully resolved. Both efforts are **CLOSED** — `companions/` (bonded
creatures → `feature_spec_todo.md` §8, closed 2026-08-01, ticket 07 deferred to v1.1) and
`psionics/` (→ §9, closed 2026-07-31). A closed map is history; the live work list is
`docs/plan_1.0_finish.md`, and the spec section is the authority.

This repo no longer carries `.claude/skills/`. The domain knowledge that lived there (path-of-war,
spheres-of-power, trainers-and-professions, foundry-conditionals, foundry-sheet-references,
multi-buff-distributor, fantasy-expert, changelog, pull-requests, commit-conventions) now lives in
the **OKF `pathfinder` bundle** — reach it via the `oks-bundles` skill (local clone:
`C:/Users/Daniel/okf-bundles`, area indexes under `oks/pathfinder/`).
