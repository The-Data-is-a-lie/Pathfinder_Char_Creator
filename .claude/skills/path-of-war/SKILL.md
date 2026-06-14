---
name: path-of-war
description: How Path of War (Dreamscarred Press 3rd-party PF1e) works and how this repo implements it. Use when working on Path of War, maneuvers, disciplines, stances, strikes/boosts/counters, martial training, initiators, initiator level, style feats, the maneuvers-known tables, or the pf1-pow FoundryVTT integration.
---

# Path of War — rules + this repo's implementation

## Core rules (as this campaign runs them)

- **Maneuvers** are per-encounter combat techniques (kinds: **strike**, **boost**, **counter**); a
  **stance** is a passive, never-expended maneuver kind. Maneuvers must be *readied* to use
  (expended on use, recoverable). **Stances count as maneuvers known** for prerequisites.
- **Initiator level (IL)**: initiator classes = class level; everyone else = `floor(level / 2)`
  (MT users only export IL for display / stance `@pow.initLevel` scaling — it does NOT gate
  their maneuver level).
- **Max learnable maneuver level**: initiators `min(ceil(IL / 2), 9)`. **Martial Training users:
  the FEAT TIER is the gate** — `max_lvl = depth` (depth 2/4/6 by BAB), so MT III grants access to
  maneuver levels 1–3, MT VI to 1–6. (The old `min(ceil(IL/2), …)` cap was wrong and is gone.)
- **Maneuver prerequisites** are same-discipline counts ("Two Iron Tortoise maneuvers" — e.g.
  Snapping Turtle Rush, a 6th-level Iron Tortoise strike, needs 2 prior Iron Tortoise picks).
- **Initiator classes** (`data.path_of_war_class`): warder, harbinger, mystic, warlord, zealot,
  stalker (base six) + **medic** (Metzofitz homebrew). Stalker/zealot are temporarily excluded
  from generation via `pow_classes_pending_foundry` in `Backend/utils/data.py` (the pf1-pow
  Foundry compendium doesn't ship their class items yet).
- **Non-initiators** roll "martial paths" (house rule): BAB `L` → 0–1 disciplines, `M`/`H` → 0–2;
  +1 to both bounds at level 20+. **Each rolled discipline is its OWN full Martial Training chain**
  (MT I..depth), drawing maneuvers ONLY from that discipline; per-chain counts come from the
  progression table, so N disciplines ≈ N× the maneuvers (a 3-discipline depth-6 build = 3×13).
  **Each chain costs its own paid feats** (MT I/III/V = `depth//2` paid per chain), and the number
  of chains is **capped by available normal feat slots** (`(normal_feat_amount-1) // paid_per_chain`)
  — a feat-poor build gets fewer disciplines than it rolled. **Within a chain, tier t grants
  level-t maneuvers** (per-tier deltas of the cumulative table: known `[2,2,1,2,1,1]`, stances
  `[0,1,1,0,1,1]`), so picks spread across levels 1..depth instead of clustering high.
- **MT feats are discipline-labeled** ("Martial Training I (Broken Blade)") so repeated chains
  don't collapse under feat de-dup and the sheet shows which discipline each grants. I/III/V are
  **paid**; II/IV/VI ride a **hand-built tax bundle** (`mt_feat_tax`, like the style chains — the
  labeled names aren't in `data/feats.csv`, so `feat_tax_func` can't resolve them). The base six
  rows in `data/feats.csv` keep sentinel type `"Path of War"` so random pools never pick them.
- **Specialization**: initiators keep `random.randint(2, 3)` of their class disciplines (one shared
  selection). MT users instead get one chain per rolled discipline (above).
- **Style feat chains** (initiators only): `randint(1, len(specialized))` chains, each matching a
  specialized discipline. The base ("<X> Style") consumes a normal feat slot; both followers are
  ALWAYS granted free ("feat tax all the way through"), bundled as "X Style > X Shell > X Snap".

## Data files (authoritative, scraped from the Library of Metzofitz)

- `Backend/json/class_data/path_of_war/Martial_Disciplines.json` — ~1033 maneuvers under
  URL-encoded discipline keys (`Fool%27s_Errand`). Per entry: `Discipline` ("<name> <Kind>
  [tags];Level: N" — separator varies; some carry a separate `Level` key), `Prerequisites`
  (count text; also lowercase `prerequisites` always holding "None"), `Initiation`/`Initiation
  Action`, `Range`, `Target`, `Duration`, `Description`. Quirks: "Thee" = Three typo, one
  trailing `\`, one "strikes" noun; a handful of entries lack parseable level/kind (skipped).
- `Backend/json/class_data/path_of_war/path_of_war_maneuvers_known.json` — per-class
  known/readied/stances arrays (20 entries; epic levels read row 20 via `capped_level_1`).
  Trees: `base` (the six) + `metzofitz` (medic, epilektoi, parasite, rajah — nested! — voltaic).
- `Backend/json/class_data/path_of_war/martial_training_progression.json` — cumulative MT table
  by chain depth 1–6: known [2,4,5,7,8,9], stances [0,1,2,2,3,4], readied [1,2,3,4,5,6],
  max_maneuver_level [1..6] (stance-preferred at V/VI per campaign spec).
- `Backend/json/class_data/path_of_war/path_of_war_classes.json` — class definitions (`base` +
  `metzofitz`); the `Maneuvers` field lists available disciplines ("either X or Y" resolved
  randomly by `clean_disciplines_string_func`).
- `data/Metzofitz_Feats.csv` (pipe-delimited) — `Style == "1"` rows form **29 discipline style
  chains** of exactly 3 feats. Derivation: base = "<Discipline> Style"; members via transitive
  closure over prereq-text mentions (Brutal Crocodile Desolation names only the middle feat);
  tier = deepest mention; ties by max "<n> ranks" ascending (Radiant Dawn: Sunlight 7 before
  Daybreak 13). Spark of Battle has no chain. Apostrophes: compare via `_dnorm` ("Fool's Errand
  Style" ↔ "fools errand style").

## Backend implementation (`Backend/utils/class_func/path_of_war.py`)

- `randomize_path_of_war_num(character)` — the martial-path roll (0 for initiators).
- `martial_training_depth(character)` — 0/2/4/6 by `bab_total`.
- `choose_path_of_war_attr(character)` — orchestrator; bundle keys: `martial_disciplines`,
  `initiator_level`, `maneuvers_known_list`/`maneuvers_readied_list` (counts by maneuver level),
  `maneuvers_choose_from`/`maneuvers_readied_names` (names by level), `stances_chosen`,
  `mt_feats`, `mt_feat_tax`, `maneuvers_desc_dict`, `style_feats`, `style_feat_tax`,
  `initiation_stat`, `homebrew_feat_desc_dict`. Two branches: **initiators** →
  `_initiator_counts` + `_constrained_pick`; **non-initiators** → `_build_martial_training`.
- `_initiator_counts` + `_constrained_pick(pool, known_n, stances_n)` (initiators only) — ONE
  interleaved loop over the union pool fills both quotas; eligible = prereq count ≤ already-picked
  same-discipline picks (stances count); weights `(i+1)^2` over level-sorted candidates; bootstrap
  relaxation (smallest gap, logged) if a discipline has no prereq-free entries. Readied = top-N by
  level desc.
- `_build_martial_training(character)` (non-initiators) — ONE chain per rolled discipline, capped
  to whole affordable chains by `normal_feat_amount`. `max_lvl = depth` (feat tier = level gate);
  per-tier counts = `_deltas` of the cumulative table. Per discipline calls `_pick_chain`; builds
  the discipline-labeled `mt_feats`, hand-built `mt_feat_tax` (paid→[free] per chain), and
  `mt_descs` (labeled keys → `_mt_feat_descs()` base text). Returns an aggregate dict (not the
  7-tuple the initiator branch uses).
- `_pick_chain(character, discipline, depth, known_delta, stance_delta, max_lvl)` — tier-ordered
  (t = 1..depth), level-matched (prefer level == t, nearest fallback), prereq-legal single-discipline
  pick; low tiers first so same-discipline prereqs are met. Reuses the bootstrap relaxation.
- `_style_chains` / `_choose_style_chains` — chain derivation + pick; children keep CSV display
  casing. `_mt_feat_descs` — all six MT descriptions from the cached feats.csv read.
- Pool tuples are 6-wide: `(name, level, kind, entry, discipline_display, prereq_count)`.

## Pipeline wiring (`Backend/main_test.py`, TABS)

Paid picks (mt_feats / style_feats — mutually exclusive by branch) are reserved out of
`character.feat_amounts` BEFORE the chooser and appended to the normal `feats` bucket after
`separate_feats_func`, counted in `feat_budget["normal"]`. **`mt_feats` is NOT clamped in
main_test.py** — `_build_martial_training` already budget-caps it to whole affordable chains; only
`style_feats` keeps the starvation clamp. The hand-built `mt_feat_tax` (and `style_feat_tax`) are
merged into `feats_feat_tax_dict` directly with their children registered in `_tax_already_granted`
(`feat_tax_func` can't resolve the discipline-labeled / Metzofitz names). The level reorder
(`assign_feats_to_levels`) may migrate a labeled MT feat from the normal bucket into the
class-bonus bucket; the tax-dict re-homing (main_test ~891) moves its bundle in lockstep, so an MT
feat may legitimately appear in either `feats` or `class_feats` with its partner bundled there.
The audit line must stay exact. Exports: the PoW keys ride `export_list_non_dict`;
`maneuvers_desc_dict` + `homebrew_feat_desc_dict` ride the dict export lists.

## FoundryVTT side (module `pf1e_random_char_generator`, its own git repo in
## AppData\...\FoundryVTT\Data\modules)

- `processPathOfWar()` in `scripts/modify-abilities.js` creates **native `pf1-pow.maneuver`
  items** (pf1-pow module required; legacy feat-item path below is the fallback when it's
  disabled). Compendium-first: each known maneuver/stance is looked up by name in the
  `pf1-pow.disciplines` pack (`powNorm()` = apostrophe/case/whitespace-insensitive — the scrape
  loses apostrophes) and cloned (`doc.toObject()`, `_id` deleted); misses console-warn and fall
  back to `synthesizeManeuverItem()` built from `maneuvers_desc_dict`.
- Item fields set either way: name prefixed `(Strike)/(Boost)/(Counter)/(Stance)` (type from the
  pack doc's `system.maneuverType`, fallback backend `type`); `system.class = upper_case_class`
  (pf1-pow's tab groups by `item.system.class === classItem.name`); readied maneuvers get
  `system.ready = true` + `uses.value 1`; stances `ready/stanceActive = false`.
- **Maneuver progression**: Martial Training characters (`mt_feats` non-empty) get
  `system.maneuverProgression = {classType: "archetype", type: "regular", initiatorAttr:
  initiation_stat}` on their class item + actor flag `flags['pf1-pow'].maneuverAttr`
  (`applyManeuverProgression()`). Initiator classes are NOT touched — their every_class.json
  items already carry `maneuverProgression`, and pf1-pow prefers per-class `initiatorAttr` over
  the flag. `initiation_stat` = backend export (arg-max FINAL Int/Wis/Cha, ties int>wis>cha —
  `initiation_stat()` in path_of_war.py atop `skill_ranks.final_ability_score`); `resolveInitStat()`
  recomputes client-side for old payloads. The same export drives the Wis/Cha skill-ranks custom
  buff pick.
- **Stance buffs** (`addStanceBuffs()`): each chosen stance → inactive `type: "buff"`,
  `subType: "temp"` item named "(Stance) <name>" under the buff divider
  `space_Path_of_War_buffs.json` ("____ Path of War ____", sort 4000; buffs 4010+). Mechanical
  `changes`/`contextNotes` come from `templates/character_sheet_folder/stance_changes.json`
  (curated from `Backend/scripts/build_stance_changes.py`'s draft; formulas use `@pow.initLevel`
  with `ifelse()/gte()/floor()/max()` — pf1 v11 has NO JS ternaries); uncurated stances are
  description-only toggles. Ally-only/conditional effects stay description-only by design.
- **Tab ordering**: `scripts/pow-sort-override.js` re-registers pf1-pow's `sortManeuvers`
  Handlebars helper on `ready` (last write wins) → discipline → Strike/Boost/Counter/Stance →
  level → name. CONSTRAINT: pf1-pow.hbs loops per-class → per-LEVEL sections AROUND the helper,
  so level headers stay the outer grouping; the override only orders within each level section.
  Keep the helper's filter semantics identical to pf1-pow's when touching it.
- **Level-section visibility**: the same file also re-registers pf1-pow's `filteredLevelsArray`
  so the tab renders a section for every maneuver level PRESENT on the actor, not just up to
  pf1-pow's computed max. Needed because Martial Training grants maneuvers by feat tier
  (`max_lvl = depth`) but pf1-pow's archetype max-maneuver-level formula is lower at many class
  levels and would otherwise hide the top tier(s). Safe for normal actors (their maneuvers never
  exceed their own max → identical output); only over-cap maneuvers add sections.
- Legacy fallback `legacyProcessPathOfWarFeats()`: feat items under the
  `space_Path_of_War.json` feats-section separator, subType `combatTalent` (modded) /
  `martialDiscipline` (unmodded), charge-tracked via `uses`.
- `homebrewFeatDescs` (from `homebrew_feat_desc_dict`) powers synth fallbacks in
  `processFeatTrait` (unmatched feat names → synthesized items) and `applyFeatTax` (chain
  children absent from every_feat.json).
- Both class bundles now carry the PoW initiator classes: `every_class.json` (5: Harbinger,
  Medic, Mystic, Warder, Warlord) and `every_class_MODS.json` (backfilled from the former via
  `tools/backfill_pow_classes_into_mods.js`, idempotent). Stalker & Zealot are absent from both
  (backend-shelved via `pow_classes_pending_foundry`) until the pf1-pow compendium ships them.
- **Maneuver conditionals on the main weapon** (implemented): each known strike/boost/counter with
  a curated combat modifier becomes a DEFAULT-OFF conditional on the main weapon's attack action
  (`action.conditionals[]` = `{name:"(Type) Name", default:false, modifiers:[{formula, target
  "damage"/"attack", subTarget "allDamage"/"allAttack", type, damageType, critical}]}`), toggled
  per-roll. `formula` keeps real dice (`2d6`) — unlike buff changes, which pf1 evaluates once
  maximized to a flat number (so **stance dice damage stays description-only**). Data drafted by
  `Backend/scripts/build_maneuver_changes.py` (conservative regexes over `Martial_Disciplines.json`
  Descriptions, emits `maneuver_changes.draft.json`), hand-curated into the module's
  `templates/character_sheet_folder/maneuver_changes.json` (high-confidence "additional/extra NdM
  damage" + attack bonuses), attached by `addManeuverConditionals()` in `modify-abilities.js` after
  the weapon item exists. Only maneuvers with a clean attack/damage modifier get a conditional.

## Gotchas

- `feat_tax.py`'s `_norm()` does NOT bridge roman/arabic numerals — Martial Training names must
  stay roman everywhere ("martial training i", never "martial training 1").
- Never run MT names or maneuver names through `capitalize_feats` (`'iii'.capitalize()` → "Iii").
- Three disciplines (Roaring Mouse, Surging Shark, Unquiet Grave) are MT-rollable but live only
  in the discipline JSON, not in any class list.
- The level reorder (`assign_feats_to_levels`) may migrate a paid base into the class bucket;
  the tax-dict re-homing in main_test.py moves its bundle, and the Foundry synth fallback covers
  every feat section, so bundles follow the feat.
