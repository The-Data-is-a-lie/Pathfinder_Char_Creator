---
name: trainers-and-professions
description: How this Pathfinder 1e generator creates homebrew "trainers" and "professions" for NPCs — trainer slots (weighted-caliber, feat-taxed bonus feats grouped as "(Trainer N)") and the profession sub-system (rank pool 5 + level + 10/profession-feat, per-profession cap 10 with one 15 via True Calling, associate-skill unlocks, assigned traits at rank 5/15). Use when adding/refining trainer or profession generation, tuning the rules, or fixing how they render in the character sheet's class-features section.
---

# Trainers & Professions (homebrew progression) — IMPLEMENTED

Two homebrew growth sources layered onto every generated NPC beyond class/race/level:
**trainers** (mentors who teach feats) and **professions** (vocations with ranks + tiered abilities).
Both are generated backend-side and render at the **bottom of the Feats tab** (NOT class-features):
trainers go through the module's normal feat pipeline, professions through a dedicated
`processProfessionAbilities` path. Only the **Skill Unlock** still uses the class-features renderer.
Source rules: the campaign Google Doc (`docs/...` / the "Professions" doc) and
`docs/homebrew_rules.md §2b`. Reference actor exports that fix the desired on-sheet format:
**Lok'nathal, Giuseppe, Bogdan, Ghog** (the hand-made sheets).

## Professions — `Backend/utils/class_func/profession_chooser.py`

`profession_chooser(character, "professions", truly_random_feats)` builds the sub-system and records
it on the character; it returns the legacy list of profession display names.

- **Rank pool** = `5 + character level + 10 × (profession feats taken)`.
- **Per-profession cap = 10**, EXCEPT one (the primary/index-0 vocation) reaches **15 only when
  True Calling is taken**. The pool is distributed greedily — primary filled first, then cap-10
  professions are added until the pool is absorbed (bounded by `_MAX_PROFESSIONS`). So a big pool
  naturally yields several professions (matching the reference sheets, which carry 4-5).
- **Profession feats** (homebrew; hardcoded in `PROFESSION_FEATS`, not in any CSV): **True Calling**
  (one profession's cap → 15), **Multi Talented** (more total ranks — i.e. feeds the +10/feat pool),
  **Always Improving** (spend ordinary skill ranks in the profession). Taken top-to-bottom so
  prerequisites resolve. **≥2 are taken when `truly_random_feats == "N"`** (curated builds); randomized
  builds usually take 0-1. Each profession feat adds +10 to the pool.
- **Per-profession data** (`character.profession_data`, one dict each):
  `{name, skill_label, ranks, cap, associate_skills, ability_theme, ability_tier, rank5_abilities,
  rank15_abilities}`.
  - `associate_skills`: one skill per rank threshold reached among **1/4/7/10** (sampled from
    `_ASSOCIATE_SKILLS`).
  - `rank5_abilities` / `rank15_abilities`: lists of resolved abilities `{name, desc, changes,
    contextNotes, uses}` from the **tiered ability system** (see below). rank5 for any profession at
    ranks ≥ 5; rank15 only the True Calling profession (ranks ≥ 15). The single random trait grant
    (old `rank5_trait`/`rank15_trait`) is **gone**.
- Also sets `character.profession_chosen` (names), `profession_feats`, `profession_feat_desc`,
  `profession_pool`.

## Profession abilities — `Backend/utils/class_func/profession_abilities.py` (+ `Backend/json/profession_abilities.json`)

`assign_profession_abilities(character)` (called at the end of `profession_chooser`) populates
`rank5_abilities`/`rank15_abilities`; `build_profession_ability_items(character)` (called in
`main_test.py`) turns them into the `profession_ability_items` export.

- **Tier** is fixed by the profession **name's prestige** (`_tier_for`, ordered keyword rules,
  word-boundary matched so "chandler" never hits the word "hand"): garbage → bad → average → good →
  high → top. **Theme** by the same name (`_theme_for`, substring rules; catch-all = `craft`): one of
  martial / ki / divine / arcane / alchemy / skill / craft / scholar / nature / medical / menial.
  **Exception:** for **high/top tier** professions the theme is swapped to the character's **class
  theme** (`_class_theme`) when known, so the strongest professions supercharge the real build.
- The JSON library is keyed by **theme → a power-tagged ladder (0-5)**. Selection picks abilities near
  a target power: **rank 15** (chosen first) targets the tier index; **rank 5** targets `tier−1`
  (weaker). Each entry takes 2-4 abilities, deduped across the character via a shared `used_global`.
  `{class}/{level}/{half_level}` placeholders are filled from the real character.
- Each ability may carry pf1 `changes` / `contextNotes` / `uses` (validated targets only — e.g.
  `attack`, `damage`, `ac`, `acpA`, `allSavingThrows`, `skill.<key>`, `cl`). When an entry bundles
  several abilities, their `changes`/`contextNotes` are concatenated onto the one item; a `uses` pool
  is attached only when exactly one ability in the entry has one.

## Trainers — `Backend/utils/class_func/trainers.py`

`select_trainer_feats(character, casting_level_str)` rolls the mentors and the feats they teach.

- **Max slots** = `1 + (hit dice // 3) + mythic_rank` (mythic = 0 for now); **actual trainers** =
  `random.randint(0, max)`.
- **Caliber** per trainer = weighted `random.choices([1,2,3,4], weights=[15,40,30,15])` →
  1 terrible / 2 average / 3 excellent / 4 mythical = how many feats that trainer teaches
  (`CALIBER_NAMES`).
- Feats are picked via `topup_feat_chooser` (combat/metamagic-aware, registers picks in
  `character.chooseable` so nothing is re-picked) and are **additive** bonus feats (on top of the
  normal budget, like bloodline/teamwork — NOT reserved from it).
- Returns `(trainer_feats, trainer_feat_labels, trainer_calibers)`; `trainer_feat_labels` are
  `"(Trainer N)"` tags parallel to `trainer_feats` (feats from the same trainer share a tag).
- In `main_test.py` the trainer feats are **feat-taxed** like every other bucket
  (`feat_tax_func(..., trainer_feats, feat_levels=[1]*len, already_granted=<shared set>)` →
  `trainer_feat_tax_dict`), so taking a base feat also bundles its chain.

## How they reach the sheet — Feats-section rendering

Trainers and professions render at the **bottom of the Feats tab** (sort band ≥ 3600, above Path of
War at 4010), built in `main_test.py` right after the feat section and emitted as feat-subType items
by the FoundryVTT module (`modify-abilities.js` → `Feats_n_Traits()`):

- **Trainers** → `processFeatTrait(everyFeatPath, trainer_feats, 'feat', 3610, "Trainer", …,
  trainer_feat_labels, trainer_feat_tax_dict)`, under an inline `____ Trainers ____` divider (sort
  3600). Same path as story/regular feats: each base feat → one item named `(Trainer N): Base > child
  > …` with full compendium descriptions (`<hr>`-separated) pulled from `every_feat.json` /
  `homebrew_feat_desc_dict`. **No caliber line.** Feats from one trainer share the `(Trainer N)` label
  and sort adjacently. **The profession feats** (True Calling / Multi Talented / Always Improving) ride
  this same path as a **dedicated extra trainer slot**: `main_test.py` (after `trainer_feat_tax_dict` is
  built) appends `profession_feats[0]` to `trainer_feats` with the next `(Trainer N)` label, sets
  `trainer_feat_tax_dict[base] = profession_feats[1:]`, and registers each profession feat in
  `homebrew_feat_desc_dict` — so they render as one `(Trainer N): True Calling > Multi Talented` entry.
- **Professions** → new `processProfessionAbilities(profession_ability_items, 3910)`, under an inline
  `____ Professions ____` divider (sort 3900). Each backend item is `{name, description, changes,
  contextNotes, uses}`; the module builds a `synthesizeFeatItem`, fills the pf1 ChangeModel defaults
  the backend omits (`_id`/`value`), applies `contextNotes`/`uses`, and preserves the rich HTML body
  verbatim. Items: `Profession Rank 5: (Name)` (with the associate-skills line in its header) and the
  primary's `Profession Rank 15: (Name)`. The profession feats are **not** listed here — see Trainers.

**Skill Unlock still rides the class-features renderer** (`updateClassFeatures` /
`convertToStringSimple`): `class_features["Skill Unlock: <skill>"] = {"5 Ranks": …, …}` — a dict whose
`{k: v}` pairs render as `<li><strong>k:</strong> v</li>` bullets (an empty dict `{}` would render as a
divider). The OLD rule that trainers/professions also went through this path (and the
list-renders-as-`0:` / string-gets-dropped traps) **no longer applies** to them.

## Export (`main_test.py` export lists, both kept length-balanced)

`trainer_feats`, `trainer_feat_labels`, `trainer_feat_tax_dict`, `trainer_calibers`,
`profession_feats`, `profession_feat_desc`, `profession_ranks` (= `profession_data`),
`profession_pool`, **`profession_ability_items`**, `skill_unlock`. `feat_budget` carries
`"trainer"`/`"profession"` counts for the `feat rows ->` audit print.

## Gotchas

- Reuse the existing feat machinery: `feat_tax_func` / `feat_spell_searcher` (`feat_tax.py`),
  `add_feats_to_chooseable`, `topup_feat_chooser` (`feats.py`). Don't hand-roll feat selection.
- Build the trainer/profession exports **after** the feat section (so `trainer_feat_tax_dict` and
  `profession_data` exist).
- Two-repo change: placement/rendering lives in the **module** (`modify-abilities.js`,
  `…\AppData\Local\FoundryVTT\Data\modules\pf1e_random_char_generator`), a **separate git repo** — the
  backend only supplies the payload. Adding a new sort band or item path means editing both.
- Mechanical `changes`/`contextNotes` must use **real pf1 v11 targets** (verify against
  `every_feat.json`) and `ifelse()/gte()` formula syntax; an invalid target silently no-ops. See the
  `foundry-sheet-references` / `foundry-conditionals` skills.

## Verify

`C:\Python310\python.exe Backend\main_test.py` from the **repo root** (see the
`python-interpreter-windows` memory — only that interpreter has deps; the relative `Backend/json/…`
loads need CWD = repo root). Run a curated build (`truly_random_feats="N"`) to force ≥2 profession
feats + a True Calling profession, and confirm: caps are 10 with exactly one 15; rank sum =
`5 + level + 10×profession-feats`; the payload carries `profession_ability_items` with `Profession
Rank 5: (…)` (every prof ≥ 5, associate-skills line in the header) and a single `Profession Rank 15:
(…)`, each with multiple tier-appropriate abilities; trainers/professions are **gone from
`class_features`** (only `Skill Unlock: …` remains there). The export assert
`len(export_list_non_dict) == len(string_export_list_non_dict)` must hold.
