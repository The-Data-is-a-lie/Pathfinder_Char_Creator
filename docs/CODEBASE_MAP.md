# Codebase map — "where do I find X?"

Read this BEFORE grepping around. Anchors are function/key names (grep those), never line
numbers. **Keep this file updated whenever files, pools, or pipelines move.**

## Pipeline (one character, end to end)

`Backend/main_test.py :: generate_random_char()` — the whole pipeline in one function, in order:
1. `CreateNewCharacter` (state object: `Backend/utils/createACharacter.py`; export via
   `export_list_dict` / `export_list_non_dict` into `character.data_dict`).
2. gender → region → race → name → `select_classes` (multiclass) → alignment → deity → body →
   mechanical flaws (`flaw_chooser`) → personality → `randomize_level`.
   **Region and race resolve client input through `util.py::slug`** (alphanumerics only, lowercased)
   onto the data files' exact key, plus `data.py::REGION_ALIASES` for the one client label that is a
   different name (`Grundykin Damplands` → `Grundy`). The **canonical spelling is the JSON key** —
   `data.py::regions`, the keys of `first_names_regions.json` / `last_names_regions.json` /
   `campaign_lore.json` — and that is what `character.region` holds and the payload emits. Never
   `.title()` it: that produced `Tal-Falko` / `Kaeru No Tochi`, which key nothing, so those NPCs drew
   names from a random other region. `validate_name_data.py` gates reachability (all ten, by name
   and by random draw) and the in-repo clients' option lists (`sheet.js`, `index.html`).
3. Stats: `roll_stats` → `apply_racial_stats` → `assign_stats` → HP.
4. Spells: per class entry `caster_formula` / `spells_known_*` / `spells_per_day_*` → spellbooks.
5. Prereq pool prep: `chooseable_list*` (stats, class levels, class features, race → `character.chooseable`).
6. Class choices: `wizard_school_chooser`, archetypes, the generic choosers (see table below), then
   `resolve_bonded_creatures` → `domain_chooser` → `character.data_dict['class features']`.
   **Order matters:** the bonded-creature resolver reads the rolled archetype and sorcerer
   bloodline, and owns the druid flip that `domain_chooser` then honours.
7. Feats (`feats.py`, trainers/professions bonus feats, feat-count guarantee), PoW + Spheres
   selection (house rule guarantees), gunslinger, gear (`armor_chooser`, `item_chooser`),
   skills/professions/skill unlock, traits, backstory.
8. Foundry buff export: feat/equipment/class-feature `*_changes_dict` + `*_conditionals_dict`
   built from the `effects`/`changes` JSONs (grep `_load_buffmap`).

Flask: `Backend/app.py` (`POST /update_character_data`, `GET /license` — the OGL
text payloads point at via `license_url`, required because serving extracted 3pp mechanics is
Distribution under OGL §10 — plus `/backstory-stats` and a signpost `/`. The in-repo character
sheet and `/sheet` were deleted; the standalone sheet is the only web front end); factory
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
- **Occult Adventures** — `class_data/{occultist,kineticist,medium,mesmerist,psychic,spiritualist}.json`
  are **GENERATED** by `build_occult_class_data.py` straight from the Foundry compendia (`pf1`'s
  `classes` + `class-abilities`, and `pf-content`'s `pf-class-abilities` — the occultist's implements
  and the spiritualist's emotional foci live only in the latter). 449 options; same
  `{dataset: {name: description}}` shape as the psionics files, same lookup-by-class-name rule.
  Gated by `validate_occult_data.py`. The pick schedules are in `data.amount`, the chooser calls are
  in `main_test.py` after the psionics block, and all six are in the random pool
  (`data.occult_classes` is now empty). Spec: `docs/feature_spec_todo.md` §10.
- **The class roster — 68 rollable classes, five families.** The pool is the keys of
  `class_data.json` minus the holdback lists in `data.py` (`pow_classes_pending_foundry`,
  `psionic_classes_pending`, `occult_classes`, `classes_pending_foundry`); the families are
  `data.CLASS_GROUPS`, where `base` is *derived* as the remainder so a new Paizo class is a one-key
  change. Do not read `base_classes` as a category — `spells.py` overloads it as the spellcasting
  gate. `util.py::_group_pool` turns the dropdown's `random-<token>` into a one-family pool.
  The FoundryVTT module's single roster is `scripts/class-roster.js` (`CLASS_GROUPS` for display,
  `CLASS_ITEM_ORDER` for `collectItems()` boundaries); `validate_class_roster.py` gates both against
  this repo. The five NPC classes are **GENERATED** by `build_npc_class_data.py` and the omdura /
  vampire hunter by `build_collab_class_data.py`, both straight off the pf1 and `pf-collab-content`
  class Items. Spec: §12.
- `feats/` — feat_changes.json, feat_conditionals.json (Foundry buffs). `items/` —
  item_changes.json (**GENERATED** by `build_item_changes.py`) + `_overrides.json`,
  quality_effects.json. `spells/` — spell_changes.json, spell_riders.json. `flaws/` —
  flaw_effects.json. `backstory_examples/` — few-shot examples for the backstory API.
- **Bonded creatures** — `animal_companion.json` (`companion` = the level chassis, rows `"1"`–`"40"`
  keyed by *effective* level, carrying that row's own `feats` count; `feats` = the 29-name legality
  pool; `tax_children` = the 23 feat-tax children a creature may be granted free) and
  `animal_choices.json` (`normal` 157 / `plant` 14 / `vermin` 23 / `magical_beast` 2 species →
  `starting statistics` plus one or more `"<N>th-level advancement"` delta blocks, keys lowercase and
  comma-inverted: `"ant, giant"`). Read by `class_func/animal_companions.py` (every grantor since
  #30 — see `companion_grantors.json` below) and then by `class_func/companion_stats.py`, which owns
  the advancement merge and every derived number (#31, landed 2026-08-03).
  - **`companion_stats.py` is the only place a companion's numbers exist.** `SIZE_GEOMETRY` and the
    merge rules live there; `SKILL_ABILITY` (skill → keying ability) is in `data.py` beside
    `SKILL_IDS`. `scripts/validate_companion_stats.py` imports all of them — never restate one.
    The size ruling it enforces is spec §8 **D11**: the published deltas already contain the size
    package, so they apply verbatim and only the *geometry* (AC / attack / CMB / CMD / Stealth /
    space) is added, keyed off the creature's **final** size. `stats.size_change` is provenance for
    numbers already totalled in — **never re-apply it in a renderer**.
  - **The feat economy is `class_func/companion_feats.py`,** not `animal_companions.py` (which keeps
    a shim) and not `companion_stats.py`. It owns the prerequisite gate (`legal_for_companion`, which
    fails CLOSED on any prerequisite it cannot read), the chassis-dated slot levels behind
    `feat_labels`, feat tax via a four-attribute adapter over `feat_tax_func`, and the animal flaw
    roll. Spec §8 **D15/D16**. Gated by `scripts/validate_companion_feats.py`.
  - **Two feat-effect files, and mixing them is a PC bug.** `feats/companion_feat_changes.json` is
    the companion's; `feats/feat_changes.json` is the PC's. The pf1 compendium already automates 12
    of the pool's feats and a PC *keeps* its compendium item's changes, so a companion effect added
    to the shared file double-applies on every PC sheet. `validate_companion_feats.py` fails on any
    pool feat carrying numeric `changes` in both.
  - **`companion_stats.apply_modifiers` folds feats and flaws into `stats` (§8 D14),** last, on top
    of the chassis numbers, and records `stats.applied_changes` / `stats.context_notes`; anything it
    cannot place joins `stats.unapplied`. `MODIFIER_TARGETS`, `SKILL_TARGET_PREFIX` and
    `eval_formula`'s mini-language (`@str`…`@hd`, `max(a, b)`) live there and are imported by both
    `validate_companion_feats.py` and `validate_flaw_effects.py` — never restated.
  - **Flaws: two catalogues, one validator.** `flaws/flaw_effects.json` (PC) and
    `flaws/animal_flaw_effects.json` (bonded creatures, 12 minor / 10 major). `flaws.pick_flaws`
    takes the filename and an RNG; `flaw_chooser` is the PC wrapper. `validate_flaw_effects.py`
    sweeps both, and additionally requires every animal change to be one `apply_modifiers` can place.
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
  - `companion_grantors.json` is the **declarative grantor table** (D6) — read its `_readme` before
    changing resolver behaviour. `animal_companions.py::resolve_bonded_creatures` is the **single
    path** to a bonded creature; the old druid-only check is gone.
  - **Identity and gear (D9)** live on the entry: a creature with a species gets a `name` (via
    `util.py::first_name_for`, the master's region pool) plus a rolled `sex`, `gear: []` and the
    `GEAR_SOURCE_V1` note — all owned by `animal_companions.py`, never restated. An entry with no
    species gets `name`/`sex` of `None` and **no gear key**. `species` stays the sole `pf-content`
    match key. Gated by `scripts/validate_companion_identity.py`, which the payload cannot yet cover
    (`bonded_creatures` ships with #32).
    - **The resolver owns the druid's companion-vs-domain flip**, and `domain_inquisition.py` reads
      its `character.bond_outcomes` rather than comparing `domain_chance` itself. Rolling the
      question in both places would give ~9% of druids both and ~9% neither.
    - **It must run after the archetype pick and the sorcerer bloodline**, which is why the whole
      domain/companion block sits below the bloodline choosers in `main_test.py` rather than where
      `animal_chooser` used to be. Moving it back breaks archetype effects and Arcane-bloodline
      familiars.
    - Rows whose species data is not authored yet (`familiar`, `eidolon`) carry a `species_data`
      note and resolve to **no entry**, so the table stays complete while the resolver stays honest.
  - Still absent: `familiar_master_table.json`, `familiar_choices.json`, `eidolon_base_forms.json`.
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
domain_inquisition.py · gunslinger.py · animal_companions.py (the grantor resolver — every grantor,
stacking, archetype bonds, D9 identity) · companion_feats.py (the companion feat economy — gated
picks, dated slots, feat tax, animal flaws) · companion_stats.py (the advancement merge, the whole
stat block, and the D14 fold of feats/flaws; runs after `companion_feats`, writes `entry['stats']`
and nothing else) ·
versatile_performance.py ·
traits.py · flaws.py / randomize_flaw.py · feat_tax.py · trainers.py / profession_chooser.py /
profession_abilities.py · backstory.py / build_archetype.py (Ollama build→archetype classifier,
heuristic fallback) / personality.py / appearance.py / family_func.py ·
alignment_and_deity.py · race_func.py · favored_class.py · language.py · chooseable.py /
feats_to_chooseable.py / flag_assign.py · luck_and_mythic.py · hero_point_generator.py ·
class_specific_feats.py / extra_combat_feats.py / extra_magic_feats.py · grand_discovery.py

## `Backend/scripts/` index

**81 files under one name, and the name is a false category.** Until the split lands
(`tickets: architecture/scripts-and-phases`, ticket 03) the prefix is the only signal of what a file
*is*. Read this table first:

| prefix | role | run by | count |
| --- | --- | --- | --- |
| `validate_*.py` | **gate** — checks data at rest, or a resolver over stubs. Fails the build. | `validate_all.py`, and CI | 19 |
| `test_*.py` | **regression test** — generates characters, so it is deliberately outside the validator glob | `test_all.py`, and CI | 11 |
| `build_*`, `scrape_*`, `compile_*`, `extract_*`, `dump_*` | **generator** — writes a JSON/CSV artefact. Never hand-edit its output; edit the `*_overrides.json` and rerun. | by hand, plus one CI staleness check | ~20 |
| `fix_*`, `repair_*`, `normalize_*`, `promote_*`, `prune_*`, `merge_*`, `enrich_*` | **one-off / manual tool** — migrations and curation passes. Many say "one-time" or "THROWAWAY" in their own docstring. | by hand | ~20 |
| `_harness.py`, `validate_all.py`, `test_all.py` | **infrastructure** | — | 3 |
| `damage_types.py`, `conditional_clauses.py`, `talent_conditional_match.py` | **shared library, not a script** — no `main()`, never run, imported by 6–7 scripts each | — | 3 |

Two traps this table exists to flag. **Several gates are also libraries**:
`validate_quality_effects.py` exports `PF1_CHANGE_TARGETS` / `valid_target` / `check_brackets` and
its `errors` accumulator to three other gates, and `validate_talent_conditionals.is_cost_only` is
imported by five scripts — changing those signatures ripples. And **non-code lives here too**:
`golden/` (7 fixtures), `_conditional_candidates/`, `_spheres_scratch/`, plus the `_pow_generator/`
and `_spheres_generator/` sub-toolkits.

**Every gate routes its verdict through `_harness.Report`** (`check` / `error` / `warn` / `skip` /
`finish`), which also owns `read_json` and the path constants `REPO` / `BACKEND` / `JSON_DIR` /
`DATA_DIR` / `SCRIPTS` / `GOLDEN_DIR`. Those are resolved by searching upward for a directory with
both `CLAUDE.md` and `.git` — **not** by counting parents — so a script does not know its own depth
and does not break when it moves. Importing `_harness` also puts `Backend/` and `Backend/scripts/`
on `sys.path`. A new gate should open with its first rule, not with path math.

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
- `build_occult_class_data.py` → GENERATES the six occult per-class option files, reconciles their
  `casting level` in `class_data.json` against the pack, and writes the five casters' rows into
  `spells_known.json` / `spells_per_day.json` from pf1's own `config.casterProgression` (read out of
  `pf1.js.map`'s `sourcesContent`). **Foundry may be running** — it copies each pack to a scratch
  dir and drops the copy's `LOCK`, unlike `dump_pf_content_actors.py`, which requires Foundry closed.
  Runs on `C:\Python310`; needs node + a `classic-level` (found by `reconcile_psionics_names.py`'s
  hunt). The spell-table writes are surgical text inserts, not `json.dump`, so the diff stays small.
- `reconcile_psionics_names.py` → GENERATES `psionic_name_map.json`, mapping our scraped names onto
  the `pf1-psionics` pack names the Foundry module can actually resolve. Unmapped names fail
  `validate_psionics_data.py`. Pack contents are dumped by `dump_foundry_pack.mjs` (node).
- `build_npc_class_data.py` → GENERATES the five NPC-class entries in `class_data.json` (adept,
  aristocrat, commoner, expert, warrior) plus the adept's `spells_known`/`spells_per_day` rows.
  Chassis is read off the `pf1.classes` class Items; only prose is hand-supplied. **Refuses to write
  if `data.good_saves` disagrees with the pack.** The adept's per-day table is RAW's, not pf1's —
  see §12 for why.
- `build_collab_class_data.py` → GENERATES the `omdura` and `vampire hunter` entries, harvested from
  **`pf-content`'s `pf-collab-content`** pack (NOT `pf1.classes`, which carries neither) with
  `pf1.class-abilities` alongside it, because four of their granted features are `@UUID`s into that
  second pack. Same good-saves refusal.
- `build_every_class.mjs` (node) → splices classes the exported `everyClassPerson` actor never had
  into the **module repo's** `every_class.json` + `every_class_MODS.json`, reading the compendium
  LevelDB directly: the twelve `pf1-psionics` classes, Path of War's Stalker/Zealot (once upstream
  ships them), the five NPC classes from the pf1 *system* pack (`--system`), and the omdura/vampire
  hunter from `pf-collab-content` (whose entry uses `also:` to resolve features across two packs).
  Needs `--classic-level <dir>` (borrow the copy in `pf1-conditional-applier/node_modules/`);
  `--dry-run` first. It **patches `bab`/`hd`/`skillsPerLevel` from `class_data.json`** — upstream
  ships one placeholder progression for all twelve psionic classes — and refuses to write if a
  harvested class is missing there. Every name it prints must also be in the module's
  `CLASS_ITEM_ORDER`, in this order; `validate_class_roster.py` is what checks that.
- `build_ogl_license.py` → GENERATES root `LICENSE-OGL.txt` (verbatim OGL 1.0a copied from an
  on-disk source + a §15 curated for THIS project) and the psionics `NOTICE.md`. Never hand-edit
  either file; edit the script. It refuses to write a licence whose operative text is truncated.
- `validate_*.py` → data gates (class_feature_effects, flaw_effects, quality_effects, psionics_data,
  companion_data, companion_names, companion_archetypes, companion_identity, companion_stats,
  companion_feats, class_roster, caster_data, …).
  `caster_data` gates the four unconnected places a class declares that it casts — `class_data.json`'s
  `casting level`, `data.base_classes` (which `spells.py` uses as the spellbook gate),
  `data.caster_mod`/`divine_casters`, and its own-name row in `spells_per_day.json` — plus that every
  `class_for_spells_attr` alias resolves to a real `data/spells.csv` column. Miss one and the class
  ships with an empty spellbook or `KeyError`s only on the seeds that roll it. `--print` tabulates
  every declared caster with the column it actually reads.
  `class_roster` is the cross-repo one: it reads the FoundryVTT module's `scripts/class-roster.js`
  and fails if the dropdown, the class groups or the `collectItems()` boundary order disagree with
  this repo's rollable class list. An uninstalled module is a **SKIP**, not a failure.
  `companion_identity` and `companion_stats` are the odd ones out: they drive the **resolver** and
  the **merge** over stub characters rather than checking a file at rest. `companion_feats` is a
  third shape again: it runs every feat's declared effect through `apply_modifiers` on two probe
  stat blocks (Str-heavy and Dex-heavy, because a conditional formula lands in only one), and fails
  a feat that claims a change but moves nothing. It also proves each `tax_children` entry is
  reachable from a real chain and grantable to a real body, so the allowlist cannot accumulate
  entries that look plausible and never fire. `companion_stats` sweeps
  all 392 species-level stat blocks and is the gate on §8 **D11**'s no-double-count ruling; it also
  asserts that at least 30 published deltas still disagree with the size table, so the check cannot
  quietly become vacuous if the data ever moves.
  `validate_psionics_data.py` cross-checks every manifesting class's power-points
  column against the three progressions `pf1-psionics` hardcodes, so a scrape regression fails loudly.
- `test_psionics_sweep.py` → the **per-class** psionics gate, one table row per class per level
  (powers, free talents, ability-capped max level, points, subsystem picks, rules text, and whether
  `pf1-psionics` will keep each emitted name). Named `test_*` rather than `validate_*` on purpose:
  it generates characters, so it is deliberately outside `validate_all.py`'s glob, alongside
  `test_house_invariants.py` and `test_golden_payload.py`. Use it when the question is "is *this
  class* right", not "did anything break".
- `test_golden_payload.py` → seven seeded characters diffed against `scripts/golden/*.json`. Three
  of them (`caster`, `companion`, `manifester`) also carry a **`COVERAGE` predicate** naming the
  payload *shape* they exist to pin — a stacked bond beside an archetype-removed one, an arcane
  spellbook beside a divine one, a manifester with powers beside a points-only one. Multiclass draws
  realign whenever the class pool changes, so those shapes evaporate silently; the predicates are
  checked on `--update` too, because a re-seed is exactly when the coverage gets written away. When
  re-seeding, **sweep on the predicate, not on a class list** — the class list is only ever how the
  coverage happened to arrive last time.
  - **Two glob runners, both in CI.** `validate_all.py` runs every `validate_*.py` and
    `test_all.py` runs every `test_*.py`; a new gate of either kind is covered the moment it exists,
    with nothing to register. `.github/workflows/validate.yml` runs both on push, plus the
    generated-file staleness check. Before this, the validators were manual, and of the eleven tests
    CI ran exactly one — `test_golden_payload.py`, the gate a refactor depends on, was not among them.
  - ⚠ **The glob makes the filename load-bearing.** `check_racial_stats.py` was a real gate that had
    never once run, purely because it was not named `validate_*`; it is now
    `validate_racial_stats.py`. A gate whose name does not match a runner's pattern is invisible, and
    nothing reports its absence.
  - `test_all.py` **trims** the full-roster sweeps by default (`TRIMMED`, currently
    `test_house_invariants --levels 1,20 --seeds 1`) and prints a `NOTE:` saying so. `--full` before
    a release.
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
  - `scripts/createCharacter.js` builds the PC Actor; `scripts/createCompanions.js` builds one Actor
    per `bonded_creatures` entry (spec §8 D1/D2/D10 — its header owns the pf1 patching rules that
    [`tickets: feature/companion-sheets` 02](https://github.com/The-Data-is-a-lie/tickets/blob/main/tks/pathfinder-char-creator/feature/companion-sheets/02-pf1-actor-patching.md)
    settled). `scripts/skills-dict.js` holds skill name → pf1 id and must stay in lockstep with
    `utils/data.py::SKILL_IDS`; ⚠ `modify-abilities.js` still declares its own identical copy —
    the dedupe is pending, and its header says so.
- Web sheet: standalone `Pathfinder-Character-Sheet` repo in `FoundryVTT\Data` — the only web front
  end (the Flask copy at `/sheet` was deleted and will not be revived). One file per tab under
  `scripts/tabs/`, each exposing `window.SheetTab<Name>`; register a new one in the `TABS` array in
  `scripts/sheet.js` and add its `<script>` to `index.html`. A tab that returns `null` for an
  irrelevant character gets an `emptyState(...)` from its `TABS` entry (`path-of-war.js`,
  `psionics.js`).
- Backend deploy: Docker Hub image + Render, via `deploy.ps1`.

## Docs & rules

`docs/homebrew_rules.md` (house rules — source of truth) · `docs/feature_spec_todo.md` (PoW
spec) · `docs/pow_conditional_decision_rules.md` / `spheres_conditional_decision_rules.md`.

**In-flight design efforts moved out of this repo** on 2026-08-05 — they increasingly span the
backend, the Foundry module and the web sheet at once, so a tracker living inside one of the three
was the wrong home. They now live in the **`tickets` repo**
(<https://github.com/The-Data-is-a-lie/tickets>) under
`tks/pathfinder-char-creator/<problem-type>/<effort>/`, in the okf-bundles format. See
[`docs/wayfinder.md`](wayfinder.md).

Each effort is a `map.md` (destination, notes, decisions-so-far index, fog, out-of-scope) plus one
flat file per decision ticket beside it. A ticket is a *question*, not a task; the **frontier** is
every open, unclaimed ticket whose `Blocked by:` list is fully resolved.

`architecture/scripts-and-phases` is the newest, and the one that touches this file: finishing the
three mechanisms this repo built and stopped applying — `@phase` (2 of ~11 orderable blocks),
`_harness` (done, 2026-08-05) and the payload manifest (not yet). Its ticket 03 owns the
`Backend/scripts/` split described at the top of this doc.

Of the five `feature/` efforts, three are **OPEN**:

- `companion-sheets/` — every bonded creature arrives as its own usable sheet: a Foundry Actor, a
  pre-filled web-sheet Companions tab. Charted 2026-08-03, four tickets, **01, 02 and 04 resolved**;
  the frontier is 03, which gates the web-sheet slice. **Succeeds** `companions/` and does not reopen
  §8's D1–D10.
- `class-pool/` — every class the generator knows about either rolls with full support or carries a
  named blocker (→ §10). **CLOSED 2026-08-03**: all six Occult Adventures classes entered the pool
  (`data.occult_classes` is empty); only `stalker`/`zealot` are still held out, by
  `data.pow_classes_pending_foundry`, filtered at `util.py::_available_class_pool`.
- `class-choices/` — every rollable class picks the right number of class options, at the right
  levels, legally, and visibly on both sheets, with a validator to keep it true (→ §11). Charted
  2026-08-03, five tickets. **Its "class list is final at 61" gate is stale** — §12 made it 68.

**Both new maps are parked**, by decision: neither is worked until `companion-sheets/` reaches its
finish line, and `class-choices/` additionally waits on `class-pool/` so its audit covers the final
class list. Two are **CLOSED** — `companions/` (bonded creatures →
`feature_spec_todo.md` §8, closed 2026-08-01, ticket 07 deferred to v1.1) and `psionics/` (→ §9,
closed 2026-07-31). A closed map is history; the live work list is `docs/plan_1.0_finish.md`, and the
spec section is the authority.

This repo no longer carries `.claude/skills/`. The domain knowledge that lived there (path-of-war,
spheres-of-power, trainers-and-professions, foundry-conditionals, foundry-sheet-references,
multi-buff-distributor, fantasy-expert, changelog, pull-requests, commit-conventions) now lives in
the **OKF `pathfinder` bundle** — reach it via the `oks-bundles` skill (local clone:
`C:/Users/Daniel/okf-bundles`, area indexes under `oks/pathfinder/`).
