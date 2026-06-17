# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Categories (use only the ones you need, in this order):
  Added       — new features
  Changed     — changes to existing functionality
  Deprecated  — soon-to-be-removed features
  Removed     — now-removed features
  Fixed       — bug fixes
  Security    — vulnerability fixes
On release: rename "[Unreleased]" to "[x.y.z] - YYYY-MM-DD" and start a fresh Unreleased block.
-->

## [Unreleased]

### Added
- **Spheres of Power / Spheres of Might (dabbling).** A new opt-in input flag (`spheres_flag`, default
  off) lets a **normal, non-spherecasting NPC** dabble into the Spheres ecosystem (Drop Dead Studios
  3pp). A dabbler focuses on **0–3 spheres**; each sphere independently rolls **Spheres of Might vs
  Spheres of Power** off the character's caster level — *no caster → Might; low → 50/50; ¾ → Power 75%;
  full → Power 90%*. Talents are **feat-funded**: the `Basic Magic Training` feat opens the magic side
  (sphere base + a casting tradition + a "mana" pool), and `Extra Magic Talent` / `Extra Combat Talent`
  feats add talents — each **bundles a free duplicate** (house rule: one slot → two talents, rendered
  `Extra Talent > Extra Talent`). Talents render in new **Magic-Talent** and **Combat-Talent** sections
  (`magic_talent_items` / `combat_talent_items`), split by sphere and system. Taking any magic content
  builds a **casting tradition** (casting ability mod + drawbacks → boons → bonus spell points) and a
  **mana pool** = highest mental modifier (min 1) + tradition bonus points. The **advanced/legendary
  talent gate is a hard invariant**: per sphere, advanced talents allowed = `(normal talents + 2 ×
  sphere feats) // 7` — enforced during selection and re-asserted on the final list, so it can never be
  exceeded. Magic-talent, combat-talent, and sphere-feat data are extracted from the FoundryVTT
  `pf1spheres` compendium by `Backend/scripts/extract_spheres_talents.py`
  (`spheres_of_power.json`, `spheres_of_might_enriched.json`, `sphere_feats.json`,
  `advanced_talents.json`); the chooser lives at `Backend/utils/class_func/spheres.py`. Real
  spherecasting base classes and Spheres of Guile are intentionally out of scope for now.
- **Professions sub-system.** Every character now gets one or more themed professions (e.g. a smith
  tends toward a smithing vocation) modelled as `Profession (X)` skills with ranks. The rank pool
  follows the campaign heuristic `5 + level + 10 per profession feat` and is spread across as many
  professions as needed to absorb it (primary/backstory vocation first). **Each profession caps at 10
  ranks, except one that reaches 15 when True Calling is taken.** Profession feats (**True Calling /
  Multi Talented / Always Improving**) are bonus feats — at least **2 are taken when feats aren't
  randomized**. Each profession unlocks a set of **tiered abilities**: a profession's power tier
  (garbage → top) is fixed by its name's prestige (Pope/Royal → top, Bishop/Cardinal → high,
  Knight/Guard & skilled smiths → good, most artisans → average, Acolyte/Nun → bad,
  Custodian/Pool-cleaner → garbage) and its theme (martial / ki / divine / arcane / alchemy / skill /
  craft / scholar / nature / medical / menial) by the same name — except **high/top-tier professions
  supercharge the character's actual class/build**. The **rank-5 entry** grants a weaker band of
  abilities (with the associate-skills line folded in); the **rank-15 entry** (only the True Calling
  profession) grants the full tier band — the strongest items on the sheet. Abilities carry pf1
  `changes`/`contextNotes`/`uses` so passive bonuses and pools are mechanically wired. They render at
  the **bottom of the Feats tab** under a `____ Professions ____` divider as `Profession Rank 5: (X)` /
  `Profession Rank 15: (X)` ability entries. The **profession feats themselves** (True Calling / Multi
  Talented / Always Improving) are no longer listed separately — they're attributed to a **dedicated
  trainer slot** (a mentor) and render in the Trainers section as one `(Trainer N): True Calling >
  Multi Talented > …` entry. New
  `Backend/utils/class_func/profession_abilities.py` + curated `Backend/json/profession_abilities.json`;
  rewrites the `profession_chooser.py` stub; new exports `profession_ranks`, `profession_feats`,
  `profession_feat_desc`, `profession_pool`, `profession_ability_items`.
- **Trainer slots.** Characters roll the trainers they studied under — up to `1 + (hit dice ÷ 3) +
  mythic rank` (mythic = 0 for now), rolled `0..max`. Each trainer has a weighted caliber
  (1 terrible → 4 mythical) that sets how many feat-taxed bonus feats they teach. They render at the
  **bottom of the Feats tab** under a `____ Trainers ____` divider, **just like normal feats** — one
  item per taught feat-tax chain (`(Trainer N): Base Feat > granted > granted`), with each feat's full
  compendium text under `<hr>` separators and **no caliber line**. New
  `Backend/utils/class_func/trainers.py`; exports `trainer_feats`, `trainer_feat_labels`,
  `trainer_feat_tax_dict`, `trainer_calibers`.
- **Free skill unlock.** Every character gains one Pathfinder Unchained skill unlock, chosen at
  random from a skill they have ranks in (Knowledge specializations map to the shared Knowledge
  unlock; Craft/Profession show their specialization). Appears as a `Skill Unlock: <skill>` class
  feature and a new `skill_unlock` export. New data file `Backend/json/skill_unlocks.json` (all 24
  skills at 5/10/15/20 ranks, scraped from Archive of Nethys) and picker
  `Backend/utils/class_func/skill_unlocks.py`.
- **Generated character backstory.** Characters now get a coherent 1-2 paragraph prose backstory
  (new `backstory` export) woven from their identity, homeland, alignment/deity, a build summary
  (class/level/role + Path of War + notable feats), their **traits (now with descriptions)**,
  personality, and family. Generated by an Ollama model when reachable — **local** (default
  `http://localhost:11434`, model `gpt-oss:20b`) or **Ollama Cloud** (set `OLLAMA_API_KEY` → host
  defaults to `https://ollama.com`, model `gpt-oss:20b-cloud`; `OLLAMA_THINK` defaults to a low
  reasoning level so gpt-oss doesn't spend the token budget "thinking") — with a deterministic template
  fallback when none is reachable (e.g. the deployed backend, or while a model is downloading).
  New `Backend/utils/class_func/backstory.py` (stdlib HTTP, no new dependency); `traits.py` now
  also captures trait descriptions (`selected_traits_desc`). The FoundryVTT module shows the
  backstory in the Biography tab (the raw field-by-field details moved to Notes).
- **Size-based damage scaling on generated FoundryVTT sheets.** Every actor now gets a
  `sizefordamage` feature (exposes `@resources.sizefordamage`, default 0) plus a generated
  **attack** item (pf1 "Create Attack" equivalent) carrying a "Scaling Weapon Damage" script call
  and two actions — "Attack" (the rollable copy, with any maneuver conditionals) and "Don't Touch"
  (the pristine base-damage reference the script scales from by size). The original weapon item is
  left untouched and stays in the Combat list alongside the attack. Needs the `ckl-roll-bonuses`
  module at runtime. (FoundryVTT module `modify-abilities.js` + new `sizefordamage_feature.json` /
  `scaling_weapon_damage.json` templates.)
- `Backend/scripts/build_maneuver_changes.py` — manual tool that drafts pf1 conditional modifiers
  for Path of War strikes/boosts/counters from `Martial_Disciplines.json` (conservative damage-dice
  / attack-bonus regexes → `maneuver_changes.draft.json`, flagged for hand-curation). The curated
  subset drives default-off conditional toggles on the generated character's main weapon in the
  FoundryVTT module (per-hit dice live here because buff changes can't roll dice; stance dice stay
  description-only).

### Changed
- **Feat selection: "free at BAB ≥ 1" combat feats are no longer spent.** Per the campaign feat-tax
  rules (`docs/homebrew_rules.md §4`), **Combat Expertise, Power Attack, Deadly Aim, and Piranha
  Strike** are free for anyone with BAB ≥ 1, so the generator never picks them as a chosen feat — they
  are seeded into `character.chooseable` before feat selection (so every chooser skips them) while
  feats that list them as a *prerequisite* still qualify (treated as owned). New
  `Backend/utils/class_func/feat_skill_choice.py`.
- **Skill-choosing feats now point at the character's professions.** Feats that require choosing a
  skill (**Skill Focus**, **Prodigy**) target the character's professions, **highest-rank profession
  first** (spreading across professions, then doubling up), e.g. `Skill Focus (Profession (Warlord))`.
  Each one's numeric bonus (**+3/+6** for Skill Focus, **+2/+4** for Prodigy, improved at ≥ 10 ranks)
  is applied to that profession — folded into its `Profession Rank 5: (X)` item as a `skill.pro`
  change plus a `Skill Focus: +N to Profession (X)` line. Surplus picks fall back to the
  highest-ranked (profession-relevant) regular skill.
- **Dev server: disabled the Flask auto-reloader (`use_reloader=False` in `Backend/app.py`).** Under
  the project's `.venv` (which redirects to the base `C:\Python310` interpreter), Werkzeug's debug
  reloader spawned a runaway cascade of nested processes that fought over port 5001 and served stale
  code. The debugger is kept; restart the server manually after code edits.
- **Backstory: "use API" toggle and stronger vocation focus.** A new `use_backstory_api` input
  (optional 20th field on `POST /update_character_data`, default on; older 19-field clients still
  work) decides whether the Ollama call runs at all — when off, the deterministic template is used
  with no network attempt. The prompt and template now also dedicate a substantial chunk of the
  story to the character's **professions, notable craft, and the trainers who taught them**, since
  those define the NPC's everyday life.
- **Path of War maneuvers now cover every available maneuver level.** Selection guarantees at
  least **2 maneuvers of each available level** (falling back to **1 each** when the class's fixed
  maneuvers-known total can't afford 2× every level), then fills any remainder randomly — so
  initiators no longer skew toward high-level maneuvers and low levels are no longer starved.
  Class/chain totals are unchanged (no power inflation). New `path_of_war.py` helper
  `_level_floor_counts`, applied in `_constrained_pick` (initiators) and `_build_martial_training`
  (Martial Training).
- **Martial Training (non-initiator Path of War) redesign.** Each rolled martial discipline (1–3)
  is now its **own full Martial Training chain** drawing maneuvers only from that discipline, so a
  multi-discipline character gets a separate set per discipline (≈ N× the maneuvers) instead of one
  shared 13-maneuver pool. **The feat tier is now the maneuver-level gate** — `max_lvl = depth`
  (the old initiator-level cap is gone), and each tier grants maneuvers of its matching level
  (MT I → level 1 … MT VI → level 6), spreading picks across levels instead of clustering high.
  **Each chain costs its own paid feats** (MT I/III/V per chain), capped by available normal feat
  slots, and the chain feats are discipline-labeled ("Martial Training I (Broken Blade)") with a
  hand-built feat-tax bundle granting II/IV/VI per chain. New `path_of_war.py` helpers
  `_build_martial_training` / `_pick_chain` / `_deltas` (replacing `_martial_training_counts`); new
  `mt_feat_tax` bundle key. Initiator classes are unchanged.

### Added
- **`initiation_stat` export** — the pf1-pow initiating ability ("int"/"wis"/"cha"), arg-max of
  the FINAL mental scores (base roll + inherents + level-up bumps, ties int > wis > cha) — the
  same calculation that drives homebrew skill-rank scaling. New shared helpers
  `final_ability_score`/`final_ability_mod` in `skill_ranks.py` (`highest_mental_mod` now sits on
  top, behavior unchanged); `initiation_stat()` in `path_of_war.py` rides the export bundle for
  every character.
- **Native pf1-pow maneuvers in FoundryVTT** (module repo): `processPathOfWar()` now creates real
  `pf1-pow.maneuver` items — cloned from the `pf1-pow.disciplines` compendium when the name
  matches (clean text/icons), synthesized from `maneuvers_desc_dict` otherwise — so maneuvers
  land in pf1-pow's own **Path of War tab**, grouped under the class, names prefixed
  `(Strike)/(Boost)/(Counter)/(Stance)`, readied maneuvers pre-readied with a charge. Martial
  Training characters get `maneuverProgression = archetype` (initiatorAttr = `initiation_stat`)
  on their class item + the pf1-pow `maneuverAttr` actor flag; initiator classes keep their
  compendium progression untouched. Each stance also becomes an inactive **temporary buff** under
  a "____ Path of War ____" buff divider — mechanical changes from a curated
  `stance_changes.json` (22 stances seeded; `@pow.initLevel` scaling via `ifelse()/gte()`),
  description-only otherwise. The tab's sort is overridden to discipline →
  Strike/Boost/Counter/Stance → level within each level section. Legacy feat-item section remains
  as the fallback when pf1-pow is disabled.
- `Backend/scripts/build_stance_changes.py` — manual tool that drafts pf1 buff `changes` for PoW
  stances from `Martial_Disciplines.json` (conservative flat-bonus + IL-scaling regexes; output
  flagged for hand-curation into the module's `stance_changes.json`).
- **Path of War selection v2.** Initiator classes now **specialize in 2-3** of their class
  disciplines (all maneuvers, stances, and style chains draw only from those); maneuver/stance
  selection is **prerequisite-legal** (a pick like Snapping Turtle Rush — 6th-level Iron Tortoise
  strike, "Two Iron Tortoise maneuvers" — is only taken once 2 same-discipline picks precede it;
  stances count, per PoW); and initiators always take **1 to N(specialized) style feat chains**
  from the Metzofitz catalogue — the base style feat consumes a normal feat slot like Martial
  Training, both followers always bundle free ("Iron Tortoise Style > Shell > Snap"). New exports:
  `style_feat_tax` rides the normal feat-tax dict; `homebrew_feat_desc_dict` carries descriptions
  for feats absent from the Foundry template (style chains + Martial Training I–VI).
- **FoundryVTT Path of War sheet section** (module repo): a "____ Path of War ____" separator
  followed by one item per known maneuver — charges 0/1, readied ones pre-charged 1/1, stances
  passive with a "(Stance)" suffix — under the modded sheet's **Combat Talents** (subType
  `combatTalent`) or pf1-pow's native **Martial Disciplines** section (subType
  `martialDiscipline`) on stock sheets.
- `.claude/skills/path-of-war` skill — Path of War rules + this repo's full implementation map
  (tables, prereq quirks, style-chain derivation, feat-tax interplay, Foundry integration).
- **Medic** (Metzofitz homebrew Path of War initiator) is now generatable like the base PoW classes:
  added to `class_data.json` (Wis / M BAB / d8 / 4 skill ranks, via `build_pow_class_data.py` which
  now also reads the `metzofitz` tree), the `path_of_war_class` list, and the front-end dropdowns.
  Its maneuvers/disciplines resolve from the `metzofitz` branch of `path_of_war_maneuvers_known.json`
  (`path_of_war.py` initiator-counts now falls back to that tree).
- `Backend/scripts/fix_foundry_change_formulas.py` — one-off migration tool for the FoundryVTT
  module's bundled item JSONs (`every_feat/trait/class_feature/class[.|_MODS].json`). Foundry v13's
  pf1 system (v11) dropped JS-ternary change formulas (`@skills.per.rank>=10?4:2` → `Unresolved
  StringTerm`); the script's recursive-descent parser rewrites every ternary in `formula`/duration
  `value` fields and `[[…]]` inline rolls to the new function syntax (`ifelse(gte(…), 4, 2)`), with
  `.bak` backups. Also a reusable `tools/export_every_class.macro.js` (in the module) that rebuilds
  `every_class.json` from the `everyClassPerson` actor so Path of War classes (and any future module
  classes) resolve on the Foundry sheet, plus a `collectItems` type-guard fixing the Stalker
  class-vs-Slayer-talent name collision. (FoundryVTT module repo only; backend generation unchanged.)
- **Path of War** (Dreamscarred Press) generation. The six base initiator classes — stalker,
  warlord, warder, harbinger, mystic, zealot — generate end-to-end (class entries built into
  `class_data.json` from the scraped Metzofitz data) and are **back in the random class pool**;
  they pick their disciplines, maneuvers known/readied and stances from their own class tables
  (`path_of_war_maneuvers_known.json`). **Any other character can roll "martial paths"** (BAB L:
  0–1 disciplines, M/H: 0–2; +1 to both bounds at level 20+): access rides the Martial Training
  I–VI feat chain taken as deep as BAB allows (I/III/V consume normal feat slots, II/IV/VI arrive
  free via the existing feat-tax pairs), with counts from a new cumulative
  `martial_training_progression.json` — mirroring the spells-known / spells-per-day concept with
  **no ability-modifier bonuses**. Actual maneuvers and stances are drawn from the chosen
  disciplines' lists, level-gated by initiator level (class level for initiators, half level for
  Martial Training users, further capped by chain depth). New exports: `martial_disciplines`,
  `initiator_level`, `maneuvers_known_list`/`maneuvers_readied_list`,
  `maneuvers_choose_from`/`maneuvers_readied_names`, `stances_chosen`, `mt_feats`, and
  `maneuvers_desc_dict` (full per-maneuver text for the sheet), plus a `PoW ->` audit line.
  (Metzofitz homebrew initiator classes and PoW archetypes are noted follow-ups in
  `docs/feature_spec_todo.md` §1.)
- `feat_budget` export (per-bucket feat-row targets: normal/story/flaw/flavor/class/teamwork/
  bloodline) plus a `feat rows -> actual/budget` audit line in the CLI output, so a generation
  that comes up short is visible at a glance.
- **Feat taxes** now resolve end-to-end. `feat_tax_func()` (`Backend/utils/class_func/feat_tax.py`)
  grants a primary feat's progression chain (from `Backend/json/feat_tax.json`) for free once its
  prerequisites are met, releasing **one chain feat per two levels** since the primary was gained;
  the FoundryVTT module bundles them onto the primary's sheet entry as
  `"<Label> Primary > Tax1 > Tax2"` (e.g. "Fighter 14: Net Adept > Net Maneuvering > Net and
  Trident"). Exceptions handled: "Extra …" feats grant one free self-duplicate, and Mythic feats
  never tax. (Path-of-War Martial Training and Sphere-of-Power talent taxes are deferred until those
  systems are integrated — see `docs/feature_spec_todo.md`.)
- `data/feats_new.csv` — a unified feat pool compiling every feat the project knows about into the
  canonical pipe-delimited schema plus a new trailing `source_dataset` provenance column: the official
  set (`AoN`, from `data/feats.csv`), the homebrew library (`Metzofitz`, from
  `data/Metzofitz_Feats.csv`), 91 net-new feats parsed from the campaign "Sieg's Guide" Feats Google
  Doc (`Sieg's Feats Doc`), and 8 net-new 3.5-only feats scraped from the d20 SRD (`d20srd`: Agile,
  Diligent, Extra/Improved Turning, Investigator, Negotiator, Nimble Fingers, Track). 3,306 feats
  total; AoN/Metzofitz rows are preserved exactly, so same-name entries like a base feat and its
  Mythic version are both kept.
- `Backend/scripts/compile_feats_new.py` — reusable, stdlib-only (+ pandas) compiler that builds
  `feats_new.csv`: maps the Metzofitz schema onto the canonical columns, best-effort-parses the
  freeform Google Doc, scrapes the d20 SRD feats page, dedupes the additive sources against existing
  names (the SRD via an order-insensitive token key, so "Armor Proficiency (Heavy)" matches "Heavy
  Armor Proficiency"), and verifies the output round-trips through the backend's
  `pd.read_csv(sep='|', on_bad_lines='skip')` loader.
- `docs/feature_spec_todo.md` — a TODO doc capturing six partially-scaffolded features awaiting design
  input (Path of War, Spheres of Power/Might, weapon attacks, weapon conditionals, free feats, feat
  taxes), each with its verified current state and a `Your spec:` prompt.
- `class_feat_labels` in the `/update_character_data` response: each class bonus feat is tagged with
  its granting class and level (e.g. "Fighter 1") via a new `class_bonus_feat_levels()` schedule
  helper, so the sheet can show class feats as "Fighter 1: Weapon Focus".
- `teamwork_feat_labels` does the same for teamwork feats (Hunter/Inquisitor every 3 levels;
  Cavalier/Samurai), via a `teamwork_feat_levels()` helper — e.g. "Inquisitor 3".
- `land_speed` (base race land speed) is now exported, consumed by the FoundryVTT custom-buffs feature.
- `bloodline_feats` and `bloodline_feat_labels` exports for Sorcerer & Bloodrager: bonus feats drawn
  from the character's own bloodline list, labeled by granting class and level (e.g. "Sorcerer 7",
  "Bloodrager 6"). New `bloodline_bonus_feat_levels()` schedule (Sorcerer 7/13/19/…; Bloodrager
  6/9/12/…, extending past level 20) and `bloodline_feat_chooser()` helper, which strips parenthetical
  specializations so names resolve in the pf1e compendium ("Skill Focus (Knowledge […])" → "Skill Focus").
- `craft_type` export — one Craft specialization rolled per character (new `crafts` list in `data.py`),
  so the sheet can show "Craft: <type>".
- `c_class_display` export — the class name in `every_class.json` format including the Unchained suffix
  (e.g. "Barbarian (Unchained)"), captured before the internal " (unchained)" strip. The FoundryVTT
  module uses it to create the correct class item.

### Changed
- **Stalker** and **Zealot** are temporarily excluded from selection (random + explicit) via a new
  `pow_classes_pending_foundry` list in `data.py` — they generate fine on the backend but the
  pf1-pow FoundryVTT compendium doesn't ship their class items yet, so the Foundry sheet can't
  resolve them. Re-enable by emptying that list and uncommenting the dropdown entries once the
  module includes them.
- The six Martial Training feats now live in `data/feats.csv` with sentinel type `Path of War`
  (visible to the feat-tax engine and description lookups, invisible to every random feat pool),
  and their `feat_tax.json` entries moved to `tax_chain_override` respelled in roman numerals
  ("martial training i" → "martial training ii", …) so they actually match the CSV names — the
  old arabic spellings ("martial training 1") could never resolve.
- Feat taxes gained **manual override knobs** in `feat_tax.json` (no code per caveat):
  `tax_chain_override` pins a primary's exact chain (e.g. Weapon Focus now taxes only to Greater
  Weapon Focus, Martial Focus, Weapon Specialization and Greater Weapon Specialization instead of its
  full ~31-feat derived tree), and `tax_exclude_grants` lists feats never granted as a tax child.
  **Critical feats no longer tax** — the `critical`-flagged feats (Blinding Critical, Staggering
  Critical, …) plus the Critical Focus gateway — matching the Mythic exclusion.
- Feat-tax chains are now **derived from the feats.csv prerequisite graph** rather than only the
  hand-listed `feat_tax.json` entries. Any selected "base" feat (has dependents but no feat-prereq of
  its own) or base Style feat auto-grants every feat that transitively requires it — Mounted Combat →
  Mounted Archery / Ride-By Attack / Trample / Spirited Charge / …, Dragon Style → Dragon Ferocity /
  Dragon Roar, Weapon Focus → Greater Weapon Focus / … — gated by the 2-level timing. A tunable
  `tax_primary_blocklist` in `feat_tax.json` tames mega-hubs (Power Attack, Combat Expertise, Dodge,
  Weapon Finesse, Improved Unarmed Strike); the existing `feat_tax` chains remain an optional homebrew
  override layer. (`feat_spell_searcher` now caches the feats.csv read, keeping generation ~fast.)
- Bonus skill ranks now scale off the FINAL highest mental ability — base score plus inherent bonuses
  and level-up bumps — instead of the base roll, via a new `highest_mental_mod()` helper. An Int/Wis/Cha
  boosted by inherents or level-ups now grants the extra ranks it should.
- Bloodline (Sorcerer/Bloodrager), teamwork (Inquisitor/Hunter/Cavalier/Samurai), monk, and ranger
  bonus-feat slots that exceed the available special-feat pool are now reallocated to extra normal
  feats, so the total feat count is preserved instead of silently dropping the slots. Example: a
  level-40 Bloodrager whose ~7-feat bloodline list can't fill all 12 granted slots now gets the 5
  leftover slots as normal feats.
- `data/feats.csv` is parsed once per run and cached (`grab_and_clean_feats`), instead of being
  re-parsed on every feat-selection call.

### Removed
- Every character no longer receives Two-Weapon Fighting + Two-Weapon Defense unconditionally —
  leftover test appends in `main_test.py` (from the BAB/caster-level selection work) gave the pair,
  plus their tax chains, to ~every generated character and could duplicate an organically selected
  copy. They now appear only when actually selected or class-granted.

### Fixed
- Martial Training feats are no longer silently dropped on the FoundryVTT sheet: they're absent
  from the module's `every_feat.json`, so `processFeatTrait` console-warned and lost the rows;
  the module now synthesizes items from the backend's `homebrew_feat_desc_dict` (same fallback
  covers style-chain feats and feat-tax children).
- `archetype_data()` no longer crashes (`KeyError`) for a class with no entry in `archetypes.json`
  (e.g. the Metzofitz Medic) — it now returns an empty archetype instead of indexing blindly.
- Warder and Mystic class bonus feats are no longer silently zero: `extra_combat_feats()` returned
  early without ever assigning `class_feats_amount`, so the two classes' bonus-feat schedules
  existed but never granted feats.
- Path of War discipline parsing no longer corrupts names: the old parser substring-matched "or"
  inside "Cursed Razor"/"Iron Tortoise" and stripped "and" out of "Fools Errand", and left
  "either …" prefixes behind; it now splits on word boundaries and resolves "X or Y" choices
  correctly. Also fixed the `harbringer` key typo in `path_of_war_maneuvers_known.json` and the
  backslash + wrong-case data paths in the (previously commented) Path of War config entries,
  which would have broken on the Linux deploy.
- A feat-tax bundle now follows its feat when the level reorder reseats the feat between the
  normal and class-bonus buckets — previously the bundle stayed filed under the pre-reorder
  bucket's tax dict, so the sheet lost the "Primary > Child" chain for migrated feats.
- Feat-tax chains with ability-score prerequisites now grant. "Dex 13"-style gates matched neither
  prerequisite filter, so chain links like Rapid Shot, Manyshot and the whole Improved/Greater
  Two-Weapon Fighting and Two-Weapon Defense lines could never release as free tax feats; stat
  gates are now auto-satisfied like BAB/level gates (selection already guaranteed final-level
  legality). Point-Blank Shot now bundles its archery line instead of leaving Precise/Rapid Shot
  as separate rows.
- Feat-tax name matching is punctuation-normalized (hyphens/underscores read as spaces, curly as
  straight apostrophes) on every comparison — config keys, prerequisite parts, owned-feat checks,
  Mythic detection — so `feat_tax.json` spellings like "point blank shot"/"blind fight" fire for
  the CSV-spelled feats ("Point-Blank Shot"/"Blind-Fight") and vice versa; granted chain names
  keep their feats.csv spelling so the sheet strip and FoundryVTT compendium lookups still match.
- Characters no longer generate with fewer feat rows than their level grants. Three causes:
  `generic_feat_chooser` silently selected one fewer feat than requested (an internal `-1` that two
  call sites compensated for and the truly-random path didn't, leaving every truly-random character
  at least one feat short); the truly-random path had no shortfall top-up when the filtered feat
  pools ran dry (the curated path's top-up is now shared by both, widening the pool until the
  budget is met); and a slot freed by the feat-tax child strip (the feat renders bundled on its
  primary instead) was never refilled — normal and class-bonus slots are now backfilled with fresh
  picks, which get their own feat-tax pass so bundles stay consistent.
- The same feat can no longer be generated twice (e.g. "Weapon Focus" appearing two times on one
  sheet). Class-granted picks — ranger combat-style feats, monk bonus feats, bloodline feats — are
  now registered as owned **before** the general feat pool draws, so the pool can't re-pick them; a
  case-insensitive dedup of the merged feat list backstops any remaining same-name collisions.
- Teamwork-feat selection (Inquisitor/Hunter/Cavalier/…) can no longer re-pick a feat the main pool
  already chose (e.g. Dodge appearing under both feats and teamwork feats): `choosing_feats` now
  drops already-owned feats from its candidate pool, which accumulates across selection passes.
- **Greater combat-maneuver feats are now granted.** Improved Drag/Trip/Disarm/Bull Rush/Sunder/
  Overrun/Dirty Trick/Steal/Grapple/Feint (plus Mobility, Stunning Fist, …) were never recognized
  as feat-tax primaries because their only feat prerequisite is itself a house-waived free feat
  (Power Attack / Combat Expertise / Improved Unarmed Strike — the `tax_primary_blocklist`); waived
  prereqs no longer disqualify a feat from heading its chain, so a held Improved Drag now releases
  Greater Drag (then Quick Drag, …) on the 2-level cadence. The "Greater X" variant is hoisted to
  the front of an "Improved X" chain so it wins the first free slot instead of losing to
  alphabetically earlier siblings (e.g. Drag Down before Greater Trip).
- A chain feat shared by two primaries' trees no longer bundles under both (e.g. Craft Construct
  under both Craft Magic Arms and Armor and Craft Wondrous Item; Riptide Attack under both Improved
  Drag and Improved Trip): the five feat-tax passes now share one granted-set, and earlier grants
  count as owned for later links' prerequisites.
- The tax-child strip now also covers the separately-exported `teamwork_feats` and `bloodline_feats`
  lists (labels kept in lockstep), so a feat bundled onto a primary can't simultaneously render as
  its own teamwork/bloodline entry.
- Ranger mounted-combat style could offer the unmatchable `" Trick Riding"` (leading space) and the
  monk bonus list `gorgons fist` / `medusas wrath` (missing apostrophes vs `feats.csv`); the JSON
  data now uses the canonical names, and feat-name registration strips stray whitespace.
- Explicit feat-tax chain entries in `feat_tax.json` written with curly apostrophes (’) could never
  resolve against `data/feats.csv` (straight `'`) and were silently skipped: Scorpion Style's chain
  now names `gorgon's fist` / `medusa's wrath`, and the dead `serpent's lash` entry is renamed to
  the CSV's actual feat names (`serpent lash` → `greater serpent lash`). Entries for feats genuinely
  absent from `feats.csv` (Believer's Boon, Marksman's Utility, Possessed Hand's children) are left
  flagged until the feat data exists.
- Feats are now acquired at levels where their prerequisites are actually met. Selected feats (already
  legal at the character's final level) were dropped onto acquisition levels by list position, so a feat
  could surface before its prerequisite feat or before the required base attack bonus — e.g. a Fighter
  showing Greater Feint at level 4 (needs Improved Feint **and** BAB +6) ahead of Improved Feint. A new
  `assign_feats_to_levels()` (`Backend/utils/class_func/feat_level_assignment.py`) reorders the normal
  and class-bonus feats as one pool so each lands at a level slot that satisfies its BAB / class-level
  gates and follows its prerequisite feats; `class_feat_labels` (e.g. "Fighter 6") follow suit. Runs
  after the feat-tax child strip (which reindexes the positional levels) and reuses the cached
  prerequisite graph, so generation time is unchanged (sub-millisecond per character).
- Feat-tax chains are now ordered by a **stable topological sort** (each feat after all its in-chain
  prerequisites) instead of BFS shortest-path depth, fixing chains that rendered "Greater X > Improved
  X" (e.g. Two-Weapon Fighting, whose Greater feat lists the base feat directly and so tied with
  Improved and lost the alphabetical tiebreak). Two-Weapon Fighting, Two-Weapon Defense and Vital
  Strike also got `tax_chain_override` entries so they tax only to their improved/greater line instead
  of their full derived tree.
- Feat-tax resolution no longer stops at the first ineligible chain link. A link whose prerequisites
  aren't met (e.g. the Spheres-of-Might side-feat "Martial Focus" that sat in the Weapon Focus chain)
  is now skipped instead of blocking the rest, so "Weapon Focus > Greater Weapon Focus" bundles.
  Level / BAB prerequisites are treated as satisfied by the 2-level release cadence.
- Feat-tax chains whose feat also has a Mythic same-name variant (Iron Will, Lightning Reflexes, …)
  now bundle. `feat_tax.py` treated any feat with a Mythic row in `feats.csv` as Mythic (and Mythic
  feats don't tax), so those primaries were silently skipped; it now skips only feats that are
  Mythic-*only*.
- Independently-selected chain children no longer render as their own standalone feat — they're
  stripped from the feat lists and bundled onto the primary entry (e.g. "Iron Will > Improved Iron
  Will"). An already-owned child bundles regardless of the 2-level timing, which now gates only
  genuinely-free grants.
- The FoundryVTT module merges each bundled feat's benefit text into the primary feat's description
  (under a labeled separator) and clones template items before editing them, so the shared compendium
  template is no longer mutated across generations.
- Feat-tax eligibility no longer keeps only the LAST primary feat's chain. `feat_tax_func` overwrote
  its candidate list each iteration (`pre_eligible_feat_taxed_list = …` at `feat_tax.py:21`), so
  every primary feat but the last had its granted feats stripped; each primary is now resolved
  independently.
- Unchained classes (Barbarian/Monk/Rogue/Summoner) selected in the FoundryVTT dialog no longer
  produce a random class. The dialog sends a slug (e.g. `barbarian-(unchained)`, spaces→hyphens) but
  `chooseClass` only matched the space-separated `class_data` keys, so the four space-named classes
  fell through to a random pick; `chooseClass` now converts hyphens back to spaces. (As before, they
  resolve to their base class for data/archetype lookup.)
- `skill_ranks` is no longer double-JSON-encoded in the `/update_character_data` response, so the
  FoundryVTT module can read the generated skill ranks (they previously arrived as an un-parseable string).
- Sorcerer & Bloodrager bloodline bonus feats now actually reach the response. They were appended to
  `character.total_feats`, which is never exported, so they were silently dropped; they are now selected
  into the dedicated `bloodline_feats` export.
- High-level (>20) generation is no longer extremely slow. Feat-eligibility (`no_prereq_loop`) was
  O(n²) over ~1478 feats and re-run once per requested feat, so cost exploded as feat counts grew with
  level; it's now a single O(n) pass and `choosing_feats` no longer rebuilds its candidate list each
  pick. A level-40 character of any class now generates in ~0.2s.
- Fixed loops that could hang or crash at high level once a candidate pool was exhausted:
  `choosing_talents` (rogue/slayer/etc. talents) could spin or hit `random.choice([])`, and
  `monk_feats_chooser`/`ranger_feats_chooser` could loop forever (ranger's `== 7` break compared a set
  to an int and never fired). Each now stops when its pool runs out.
- Ranger combat-style feats and monk bonus feats were silently discarded in the default (truly-random)
  feat path: `character.feats` was reassigned by the normal-feat selector right after the choosers
  populated it. They now survive (merged once after selection and name-normalized to match the Foundry
  compendium), so rangers actually receive combat-style feats.
- Monks no longer double-count their bonus feats. The allotment was added both by `extra_combat_feats`
  (as labeled class feats) and `monk_feats_chooser`; monk bonus feats now come solely from
  `monk_feats_chooser`, with unfilled slots reallocated to normal feats, keeping the total the same.
- Fighter/Brawler (and other high-bonus-feat classes) no longer crash with "list index out of range"
  when using non-random (curated) feats. `separate_feats_func` popped `story+flaw+flavor+class_feats`
  from the front with unguarded indexing while the curated `build_selector` pool under-produced; it now
  pops from the front bounded by what's available (also fixing a latent every-other selection bug). The
  curated path additionally tops up from the general feat pool when its buckets come up short, so a
  level-40 curated character gets its full feat count instead of a stub.
- Unchained classes now display as their Unchained variant on the FoundryVTT sheet (via the new
  `c_class_display` export) instead of their base class.
