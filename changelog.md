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
- **Combat-maneuver & rider text on spell and maneuver conditionals (the "Inheritor's Smite"
  pattern).** A weapon conditional can now carry a structured attack/damage bonus **and** `[[ ]]`
  rider text (a save, condition, or a rollable combat maneuver) in its name at once. (1) Spell
  conditionals gained a `rider` channel: `addSpellConditionals` in the FoundryVTT module appends an
  entry's `rider` to the toggle name, so e.g. **Inheritor's Smite** now shows both `+[[5]] sacred
  attack` and `on hit, free bull rush [[ d20 + @attributes.cmb.total + 5 ]] vs CMD (no AoO)`
  (Rock Whip likewise gains its caster-level bull rush). (2) **44 Path of War maneuvers** that
  described a grapple / trip / disarm / sunder / bull rush with no rollable check now carry a
  `[[ d20 + @attributes.cmb.total … ]] vs CMD` roll (flat bonuses folded in, IL-scaling via
  `@pow.initLevel`, `@INITMOD`-based CMB for Solar Wind, and Escape Artist for The World's Greatest
  Trick). (3) The `build_spell_conditionals.py` / `build_maneuver_changes.py` draft builders now
  detect combat-maneuver / save / condition clauses, and the `foundry-conditionals` skill +
  `docs/pow_conditional_decision_rules.md` document the pattern and the three CMB-roll forms (plain,
  skill-in-place-of-CMB, caster-level-in-place-of-BAB).
- **Spells now carry pf1 conditionals/riders into the Foundry actor.** A generated NPC's chosen
  spells that buff attack/damage or are themselves a touch-attack are wired into the export so the
  FoundryVTT module can attach mechanics instead of leaving them description-only. Two new
  name-keyed dicts ship in the character JSON: `spell_changes_dict` — Bucket A buffs (Bless, Divine
  Favor, True Strike, Magic Weapon, Flame Arrow) as a default-off conditional toggle / always-on
  change on the wielder's **weapon**; and `spell_riders_dict` — Bucket B damaging attack-spells
  (Chill Touch, Frigid Touch, Acid Arrow) as the save block + non-damage riders ([[ ]] inline text)
  on the **spell's own** action (its attack + damage already come from the compendium). Classified
  across all 2,827 spells by the new `Backend/scripts/build_spell_conditionals.py`
  (→ `spell_conditionals.draft.json`) and curated into `Backend/json/spells/spell_changes.json`
  (121 entries) + `spell_riders.json` (19); selected per-NPC by `spell_conditionals_selection()` in
  `spells.py`. The curated data is auto-derived from spell text and flagged for ongoing review;
  consuming it requires a matching update to the (separate-repo) `pf1e_random_char_generator` module.
- **Path of War maneuvers & stances — full mechanical automation in generated NPCs.** Every PoW
  strike/boost/counter and stance a generated NPC knows now renders rich mechanics in Foundry instead
  of description-only text. The FoundryVTT module's curated data was greatly expanded —
  `templates/character_sheet_folder/maneuver_changes.json` **581 → 846** entries,
  `stance_changes.json` **19 → 159** — so that, per the new
  [foundry-conditionals](.claude/skills/foundry-conditionals/SKILL.md) /
  `docs/pow_conditional_decision_rules.md` convention: on-hit **and** area/burst/cone/line damage are
  real **damage modifiers** (with damage types) that roll in the damage section; saves / conditions /
  durations ride the conditional name as `[[ ]]` inline rolls; skill / demoralize / feint checks
  resolve to the **discipline's main skill** (`[[ d20 + @skills.<id>.mod ]]`); and the
  formerly-description-only stances gained pf1 buff `changes` (always-on flat self-buffs) +
  `contextNotes` where expressible (per-die / aura / ally effects stay description-only by design). A
  1-line `addStanceBuffs` tweak in `scripts/modify-abilities.js` substitutes `@INITMOD` in stance
  contextNotes (parity with maneuver riders). The expanded data is **LLM-generated** from the scraped
  maneuver descriptions — review before relying on it. Produced by gitignored personal tooling under
  `Backend/scripts/_pow_generator/` (which also builds an importable per-discipline "palette" actor
  and a `promote_to_module.py` that pushes the data into the module's curated files).
- **Tunable, example-driven Ollama backstories.** The backstory generator
  (`Backend/utils/class_func/backstory.py`) now uses a proper chat `system` role and supports three new
  controls without code edits: (1) an editable **`Backend/json/backstory_config.json`** (system prompt,
  temperature, length, focus phrases — partial/missing file falls back to baked-in defaults);
  (2) **few-shot examples** — drop `.txt`/`.json` backstories into **`Backend/json/backstory_examples/`**
  and 1–3 are shown to the model as example turns (optionally matched to the character's class/race/etc.
  via `smart_match`); an empty folder reproduces the old behavior exactly; (3) an optional
  **`backstory_focus`** input (comma/space-separated aspects: `combat`, `profession`, `faith`, `family`,
  `personality`, `appearance`, `region`) that emphasizes chosen facets — threaded through
  `generate_random_char` and the Flask `update_character_data` endpoint (optional 21st input), and also
  honored by the deterministic offline template fallback.
- **Backstory house style — prose + closing list, vocation/family/homeland focus.** The default
  backstory prompt now centers the prose on **profession → family & upbringing → homeland/where they
  are from**, deliberately **stops reciting feats and game mechanics**, and ends with a short labeled
  list (`Personality:` / `Mannerisms:` / `Appearance:` / `Flaws:`); the facts block and offline
  template were reordered to match. Example backstories now ship as `.json` with `tags`
  (`Backend/json/backstory_examples/`) so `smart_match` feeds the 2 closest to each NPC, and the
  default length was raised to 220–400 words (`max_tokens` 1100) to fit the richer prose + closing list.
- **Numerical feat buffs on the Foundry "Changes" tab.** Selected feats now carry their mechanical
  effect onto the generated actor instead of being text-only. Two new curated, hand-vetted side-maps
  keyed by feat name ride the export: **`Backend/json/feats/feat_changes.json`** — always-on pf1
  `changes` (e.g. Advanced Defensive Combat Training +4 CMD, Tribal Scars +6 HP, scaling skill feats
  via `ifelse(gte(@skills.X.rank,10),4,2)`) plus situational `contextNotes` for conditional feats
  (vs undead / while charging / when adjacent to an ally, etc.); and
  **`Backend/json/feats/feat_conditionals.json`** — default-off **toggle conditionals** for active
  feats (Power Attack, Deadly Aim, Piranha Strike, Combat Expertise, …) the player ticks per attack.
  Exported as `feat_changes_dict` / `feat_conditionals_dict` (new keys in `export_list_dict`); the
  FoundryVTT module overlays the changes onto each feat item (deduped by target) and attaches the
  toggles to the main weapon's attack action. **Double-apply guard:** buffs are authored ONLY for
  feats Foundry's `every_feat.json` compendium does not already automate, so nothing stacks twice.
  Spheres-of-Power magic talents stay text-only by design (they cast effects, not passive self-buffs).
- **Numerical buffs on combat talents (Spheres of Might).** The previously-empty `changes` /
  `contextNotes` slots on combat-talent items are now filled from
  **`Backend/json/class_data/spheres/combat_talent_changes.json`** (e.g. Greater Disarm/Trip/Sunder
  competence bonuses to CMB/CMD, Compact Frame's situational dodge AC), injected by `_talent_item`
  in `spheres.py` and honored by the FoundryVTT module's talent builder. (Alchemy "flask/bomb"
  talents that create separate thrown weapons are deferred — they need their own weapon items.)
- **Buff authoring tooling.** New manual draft-builders mirroring the Path-of-War pattern:
  `Backend/scripts/build_feat_changes.py` (text-mines `data/feats.csv`, joins `every_feat.json` for
  the double-apply guard) and `Backend/scripts/build_talent_changes.py` (`--system might|power`).
  They emit `*.draft.json` drafts that are classified/verified and hand-curated into the production
  maps above.
- **Skill-feat coverage + Skill Focus actually works now.** Added always-on skill `changes` for
  un-automated fixed skill feats (e.g. **Sea Legs** +2 Acrobatics/Climb/Swim, **Sharp Senses** +4
  Perception) and situational `contextNotes` for conditional ones (Altitude Affinity, Stone-Faced,
  Divine Deception/Denouncer, Improved Stonecunning, Casual Illusionist). **Skill Focus / Prodigy**
  (which `feat_skill_choice.py` points at the NPC's professions) previously recorded a bonus that was
  never consumed — now `specialize_skill_choice_feats` emits the resolved pf1 change
  (`skill.pro` +3/+6, or a regular-skill fallback `skill.<id>`) which `main_test.py` folds into
  `feat_changes_dict`, so the bonus finally lands on the sheet.
- **Situational combat feats are now default-off toggles.** 41 feats whose bonus only applies under a
  condition (Bloody Vengeance, Demon Hunter, Ferocious Loyalty, Giant Killer, Moonlight Stalker,
  Death from Above, …) moved from informational `contextNotes` to **default-off weapon toggle
  conditionals** in `feat_conditionals.json` — the player ticks them in the attack dialog and the
  bonus applies numerically, with the trigger spelled out in the conditional name (`[[ ]]` inline
  rolls where relevant). Non-combat riders (e.g. Demon Hunter's Knowledge (planes) bonus) stay as
  context notes.
- **Weapon Focus / Weapon Specialization line.** When an NPC takes Weapon Focus (the feat-tax
  *primary* that bundles Greater Weapon Focus / Weapon Specialization / Greater Weapon Specialization
  into one merged item), the chain's bonuses are now summed onto the feat — +1 attack per focus tier
  and +2 weapon damage per specialization tier (full chain = +2 attack / +4 weapon damage) — via a
  new `Backend/utils/class_func/weapon_focus_buffs.py` folded into `feat_changes_dict`. The bonus is
  global to weapon attacks, matching the single main weapon the generator equips.
- **Five new profession genres + a curated profession catalog.** Added the themes **`noble`** (royalty,
  courtiers, regents), **`occult`** (witches, necromancers, cultists, warlocks), **`wayfarer`** (sellswords,
  treasure-hunters, monster-slayers), **`elementalist`** (fire/ice/storm/earth specialists), and
  **`villain`** (brigands, terrorists, tyrants, torturers) — each with its own ~20-ability power-0..5
  ladder (now 19 themes / 380 abilities). A new curated catalog (`Backend/json/profession_catalog.json`,
  359 professions tagged with an explicit genre + power tier) feeds the generation pool and is consulted
  before the keyword heuristics, so new/epic/low-tier names classify deterministically. Tier-4/5
  professions now have epic titles (Royal Bloodline, Divine Vessel, Avatar of the Storm, Necromancer-Lord,
  Thousand Fists Champion, …). (`profession_abilities.json`, `profession_catalog.json`,
  `profession_abilities.py`.)
- **`fantasy-expert` skill.** A reusable D&D/Pathfinder/fantasy-lore skill (`.claude/skills/fantasy-expert/`)
  encoding the profession genre roster, fantasy-commonality weights, the tier ladder, and epic naming
  conventions — used to drive the genre/name/ability authoring above.
- **Profession abilities are far more varied (98 → 279 abilities, 11 → 14 themes).** The tiered
  Rank 5 / Rank 15 profession-ability library (`Backend/json/profession_abilities.json`) roughly tripled
  — every theme now carries ~16-21 abilities across the full power 0-5 ladder (was 4-9), so professions
  no longer repeat the same handful of abilities across the generated population, and a character with
  several same-theme professions gets distinct picks instead of draining a tiny ladder. Three new themes
  were added — **`trade`** (merchants/mongers/peddlers: haggling, appraisal, contacts, gold from wares),
  **`performance`** (bards/minstrels/dancers/jesters: inspire, fascinate, demoralize, fame), and
  **`service`** (innkeepers/cooks/brewers/butchers: food-and-drink buffs, rumors, hospitality) — and
  these vocations were pulled out of the overloaded catch-all `skill`/`craft` themes so dissimilar
  professions (e.g. Embroiderer vs Fishmonger, now `craft` vs `trade`) stop sharing one pool. New
  abilities carry real pf1 v11 `changes`/`contextNotes`/`uses` where the effect is mechanical.
  Every ability is **specific**: limited-use abilities state their exact per-day count in the text (no
  "a few times"), and none are flavor-only — each grants a concrete, defined effect (e.g. a crafter's
  *Honest Materials* gives crafted objects hardness equal to half the relevant Craft ranks; a merchant's
  *Coin From Wares* earns gold equal to Profession ranks × 10).
  (`profession_abilities.json` data; `profession_abilities.py` theme routing.)
- **Spheres now render natively on the Foundry sheet.** Sphere talents are placed in the pf1spheres
  module's **Combat/Magic Talents** section (grouped by sphere, with the real compendium icons and
  text) — exactly as if dragged in from the pf1spheres compendium — instead of as plain feats in the
  Features list. Each talent is cloned from the `pf1spheres.combat-talents` / `magic-talents` pack by
  name (or synthesized as a `combatTalent`/`magicTalent` feat tagged with its sphere when the module is
  off or a talent is missing). Magic dabblers still get a casting-tradition / mana-pool summary feat;
  the sphere *feats* ride the normal feat pipeline. (`modify-abilities.js` → `processSpheres`.)
- **Magic-side bonus sphere feat.** A Spheres-of-Power dabbler now has a 50% chance to pick up a
  sphere-specific feat tied to their most-taken sphere (favoring exactly one), drawn prereq-aware from
  `sphere_feats.json`. (`spheres.py` → `_roll_magic_sphere_feats`.)
- **Advanced sphere talents are labeled and sorted last.** On the sheet, an advanced talent now shows
  as `(Advanced) <Name>` and sorts to the bottom of its sphere, with the normal talents alphabetical
  above it. The backend marks each talent's advanced status (`_talent_item`); the FoundryVTT module
  applies the `(Advanced)` prefix and orders each sphere (normals alphabetical, advanced last) via the
  item `sort` field. (`spheres.py`, `modify-abilities.js` → `processSpheres`.)
- **Only real compendium talents are picked.** The combat (Spheres of Might) talent data is now built
  directly from the pf1spheres **combat-talents compendium** instead of a wiki scrape, so non-talent
  entries that used to leak in (e.g. "Optional Rule: Vehicles as Mounts", variant-rule sidebars, empty
  stubs) are gone, and previously thin/mismatched spheres are complete (Equipment went 16→103 talents,
  Warleader 6→54). A committed allowlist (`compendium_talent_names.json`, emitted by
  `extract_spheres_talents.py`) backs a defensive filter in `spheres.py` so only compendium talents are
  ever selected. (Magic data was already compendium-sourced and is unchanged.)

### Changed
- **Path of War maneuver damage dice no longer multiply on a critical hit.** A maneuver conditional
  whose damage formula carries dice (e.g. Ravaging Blow `1d6`, Razor Tempest `8d6`, `4d6 + @INITMOD`)
  is now emitted as a pf1 **"Non-multiplying Bonus Formula"** (`critical:"nonCrit"`) — extra effect
  dice aren't multiplied on a crit, per the Pathfinder rules. Flat / `@`-only damage modifiers (no
  dice) stay `critical:"normal"` and scale with the crit like static damage; attack modifiers are
  untouched. Applied across all PoW maneuver data: the module's curated `maneuver_changes.json`
  (362 modifiers), the regenerated `maneuver_changes.draft.json`, and the palette's
  `_pow_generator/maneuver_overrides.json` (123 modifiers) — so both the auto-attached weapon
  conditionals and the rebuilt PoW palette now read `nonCrit` for dice damage. Enforced going forward
  by `_crit_for()` in `Backend/scripts/build_maneuver_changes.py` and re-runnable via the new
  idempotent `Backend/scripts/fix_maneuver_crit.py`. An audit of all 370 dice-bearing maneuvers
  against their rules text found exactly one genuine crit-tied case — **Doom Talon** (Thrashing
  Dragon), whose 4d6 fires only on a confirmed critical and isn't doubled — now encoded as the pf1
  **"On-critical Bonus Formula"** (`critical:"crit"`) in the curated data + palette override. Spheres
  talents and feat conditionals are intentionally left as-is.
  (`docs/pow_conditional_decision_rules.md` updated.)
- **Path of War skill-based attacks & combat maneuvers now roll correctly.** Maneuvers that resolve
  via a skill emit literal inline `[[ ]]` rolls following three conventions: a skill used **as an
  attack roll** adds the actor's misc attack bonus (`[[ d20 + @attributes.attack.general +
  @skills.<id>.mod ]]`); a skill **in place of CMB vs CMD** keeps CMB's size/misc and swaps out
  BAB + ability (`[[ d20 + @attributes.cmb.total - @abilities.<str|dex>.mod - @attributes.bab.total +
  @skills.<id>.mod ]] vs CMD`, melee→str / ranged→dex); a plain skill check stays
  `[[ d20 + @skills.<id>.mod ]]`. Fixed the **Roaring Mouse** discipline skill map (`acr` → `esc`,
  Escape Artist) and retrofitted 22 affected maneuvers (Roaring Mouse, all of Tempest Gale, Surging
  Shark's charges, Piercing Thunder leaps, Fool's Errand, Mithral Current, Sleeping Goddess) into the
  module's `maneuver_changes.json` + palette via the new
  `Backend/scripts/_pow_generator/apply_skill_rolls.py` → `promote_to_module.py`.
  (`docs/pow_conditional_decision_rules.md` + `foundry-conditionals` skill updated.)
- **Path of War stances: IL-scaling damage now mechanical, plus aura markers.** The eight stances that
  add initiator-level-scaling damage to the wielder's attacks (Savage Stance, Snapping Turtle Stance,
  Reaching Blade Stance, Stance of Aggression, Scarlet Einhander, Stance of Piercing Rays, Outer
  Sphere Stance, Phalanx Lancer) now emit that damage as a **rolled-dice, default-on weapon damage
  conditional** (`critical:"nonCrit"`) whose dice count scales off `@attributes.hd.total` — instead of
  passive `contextNotes` text (a buff `change` would maximize the dice). New
  `apply_stance_damage.py` authors them; the module's `addManeuverConditionals` and the palette attach
  them for known stances; the redundant `wdamage` contextNote was removed from each buff. Separately,
  ~20 aura / affects-others stances now carry `AuraRange: <feet-or-formula>` (and `onlyOthers;` when
  the wielder gains nothing) marker lines prepended to their buff description — driven by the new
  `Backend/json/class_data/path_of_war/stance_auras.json` — for downstream aura/buff-distributor
  tooling. (Data-only; a stance whose runtime description comes from the pf1-pow compendium won't show
  the markers — the palette always does.)
- **The Spheres Mentor now funds far fewer, caliber-scaled talents (~2.5 feats, was ~4.5).** A dedicated
  Spheres Mentor was funded by the **sum of two** caliber rolls plus overflow, so it could teach ~9
  off-budget talents (≈ 4.5 feats) and bloat a character past the flat-8. Now a single mentor of caliber
  C (one roll) teaches exactly **2·C talents** = C feats off-budget (C = 1/2/3/4 → 2/4/6/8 talents),
  capped at the flat-8, with no overflow — so the character's total talents never exceed 8 and the mentor
  averages ~2.5 feats. Trainer caliber weights were also retuned from `15/40/30/15` to **`8/45/45/2`**
  (mean ~2.4): mostly average/excellent, with the occasional terrible and a rare mythical.
  (`trainers.py` `roll_caliber`, `main_test.py` trainer-backed branch, `spheres.py` `choose_spheres_attr`.)
- **Generated professions now follow tunable power-tier and genre distributions.** Previously 85% of
  professions were "average" tier and 61% fell into the catch-all `craft` genre. Profession selection
  (`profession_chooser._themed_profession_names`) now rolls a target **tier** then **genre** from weight
  tables: tiers land at ~**5% / 35% / 35% / 20% / 3% / 2%** (garbage→top), and `craft` stays the single
  most common but drops to ~**15%**, with the rest spread across the other genres by how common each
  archetype is in fantasy. Implemented as weighted selection over a cached `(tier, genre)` index of the
  pool (so the marginals are precise and easy to retune via `_TIER_WEIGHTS` / `_GENRE_WEIGHTS`); the raw
  master list is unchanged. (`profession_chooser.py`.)
- **Profession feats now cost a feat and each render as their own feat (no more "feat-tax" chain).**
  The three homebrew profession feats (True Calling / Multi Talented / Always Improving) used to be
  attributed to a fake trainer slot and bundled as one `(Trainer N): True Calling > Multi Talented >
  Always Improving` feat-tax chain *on top of* the normal budget (free). Each now renders as its **own
  ordinary feat** in the Feats list and **consumes a normal feat slot** (like the Path of War / Spheres
  feats): the profession-feat count is reserved out of both `feat_amounts` and `normal_feat_amount`, so
  each one replaces a normal feat — or, at very low level, the profession feats take over the general
  feat track and clamp the normal feats down to 0. They are appended after every `feat_tax_func` pass
  and the feat-count guarantee, so they are never chained or trimmed. (`main_test.py`. No front-end
  change — they ride the normal feat pipeline.)
- **Dedicated mentor trainers now list what they funded.** In the 25% "trainer-backed" branch, the
  "Path of War Mentor" and "Spheres Mentor" trainer entries previously showed only generic flavor text.
  Now each names the off-budget homebrew it taught: the **Path of War Mentor** lists every PoW feat
  (style feats + Martial Training tiers) with its description, written like a normal PoW feat; the
  **Spheres Mentor** lists the spheres funded plus the off-budget talents it provided — presented as HR1
  `Extra Combat/Magic Talent > Extra Combat/Magic Talent` feats (one per 2 talents) followed by the
  talent names — i.e. only the talents *beyond* what the character paid for themselves (no duplication of
  the budget-paid Extra-Talent feats already in the main Feats list). Single-type characters now get one
  correctly-named mentor (padded to two with a uniquely-named "(Continued Study)" entry when needed) so
  the per-name descriptions never collide. (`spheres.py` → `mentor_sphere_summary` + `mentor_funded_talents`;
  `main_test.py` mentor block. No front-end change — the module synthesizes the trainer row from the
  description.)
- **Budget-paid sphere talents now show a feat slot for tracking.** Each talent paid from the feat
  budget is bundled onto an HR1 `Extra Combat Talent > Extra Combat Talent` feat (2 talents per slot;
  the first magic talent rides `Basic Magic Training`), listed in the Feats tab with the talents it
  paid for in the description — like any other feat-taxed feat. Talents funded by the 25% Spheres
  Mentor trainers stay tracked by that trainer entry (no Extra-Talent feat). The feats consume feat
  budget. (`spheres.py` → `choose_spheres_attr`, `main_test.py`.)
- **Path of War & Spheres are now guaranteed when selected, with priority over normal feats.** Previously
  their counts were capped by whatever feat budget remained after everything else, so a feat-heavy NPC
  (e.g. a PoW-loaded martial) could silently lose them entirely. Now, when an NPC is rolled to have PoW
  and/or Spheres, those selections are funded **first** and the normal feat chooser takes whatever
  remains (down to zero). The realized amount scales per character: a **75%** chance to take a "lean"
  dose (about half the rolled homebrew feats), and a **25%** chance to be "trainer-backed" — keeping at
  least the lean half and gaining **2 dedicated mentor trainers** whose off-budget rolls fund the rest,
  with any surplus becoming bonus sphere talents. (`main_test.py`, `spheres.py`, `path_of_war.py`.)
- **Sphere talent count is now a flat 8 (7 normal + 1 advanced)** for a spheres-selected NPC,
  prerequisite-legal (decoupled from the feat count; backfills a normal if no advanced qualifies).
  Trainer-backed NPCs still get overflow talents on top. For testing, a `SINGLE_SPHERE_TESTING` flag
  (on) forces all 8 talents to come from **one** sphere so the 7 normals satisfy the same-sphere
  prerequisites that gate advanced talents. Both are testing values — a level-scaled model (groups of
  two, capped at 16) is planned later. (`spheres.py` → `_pick_flat_talents` / `randomize_spheres_num`.)

- **Spheres of Power/Might toggle in the generator UI.** The FoundryVTT character-generator dialog now
  has a "Do you want Spheres of Power/Might" yes/no option (default No). Choosing **Yes** activates the
  existing Spheres dabbling logic, so generated NPCs can now actually pick up sphere feats and talents
  (and, for casters, a casting tradition + mana pool) — previously the feature was backend-only and the
  flag always defaulted off, leaving every character with empty sphere data. The flag is read by name in
  the backend (`spheres_of_power` in the POST body) and threaded through `app.py` to
  `generate_random_char`'s `spheres_flag`.
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

### Fixed
- **Path of War skill-based attack & counter checks now include the general attack bonus.** When a
  maneuver rolls a skill *in place of an attack roll* (vs AC) or opposes the *triggering attack
  roll* (a counter), the inline roll now adds `@attributes.attack.general` — e.g. Primal Fury's
  *Shrug It Off* counter is `[[ d20 + @skills.sur.mod + @attributes.attack.general ]]` instead of
  `[[ d20 + @skills.sur.mod ]]` — so these to-hit rolls are on equal footing with the enemy's
  attack. 41 maneuvers were corrected (incl. Leaden Hyena feints rolled vs Sense Motive *or AC*);
  pure skill checks (vs a DC), combat maneuvers (vs CMD), and Perception-opposed counters (Veiled
  Moon) are unchanged. The canonical source gained an `@ATTACKCHECK` token (sibling to
  `@SKILLCHECK`) resolved by `promote_to_module.py` / the palette builder; the new idempotent
  `Backend/scripts/_pow_generator/apply_attack_general.py` performs the conversion. Re-curates the
  (separate-repo) module's `maneuver_changes.json`.
- **No more blank dedicated-trainer slots.** A trainer-backed NPC could show a content-free trainer like
  `(Trainer 5): Spheres Mentor (Continued Study)` (generic text, teaches nothing) — an artefact of
  padding the dedicated mentors to a fixed count of two. Dedicated mentors are now emitted only when they
  actually funded off-budget content (the Spheres Mentor appears only with a non-empty funded-talent
  list), and the pad-to-two loop and the generic "Homebrew Mentor" fallback are gone. A trainer-backed
  PoW-only build simply shows no dedicated mentor rather than a blank one. (`main_test.py`.)
- **The "Path of War Mentor" trainer no longer re-lists feats the character already paid for.** In the
  25% "trainer-backed" branch, a dedicated **Path of War Mentor** trainer listed every Martial Training /
  style feat as though it had *funded* them — but those feats are real feats on the sheet (they grant the
  maneuvers), so they're always paid from the normal/class feat budget and already appear in the Feats
  list. The mentor was pure duplication. Unlike sphere talents (which can be granted off-budget, so the
  **Spheres Mentor** legitimately lists only what it funded), Path of War has nothing genuinely
  off-budget, so it now gets **no mentor**. Trainer-backed builds keep the Spheres Mentor; a PoW-only
  trainer-backed build shows a generic "Homebrew Mentor" that lists no feats. (`main_test.py`.)
- **Sphere talents no longer leak in as bare feats.** Intermittently a sphere talent (e.g. Hurricane
  Kick, Yoga Strikes, Fragmenting Shot) was being chosen as a normal/flaw/class/trainer feat and rendered
  as an empty-description row. Cause: `character.chooseable_talents` accumulates across selection passes
  and feeds the feat chooser, and the sphere-talent picker left its **unpicked** eligible talents in that
  list — which the chooser's "drop owned" guard didn't catch (they were never added to `chooseable`). The
  sphere picker now clears `chooseable_talents` when it finishes (in `choose_spheres_attr` and
  `add_overflow_talents`), so leftover talents can't bleed into the feat pool. (These leaked talents used
  to be silently dropped by the front-end — part of the earlier "missing feats"; the synthesize-on-unmatched
  change exposed them, and it correctly stays for genuine feats missing from `every_feat.json`.) Verified
  0 leaks across 40 generations.
- **Martial Training feat-tax chains render consistently again.** Within one discipline some tiers showed
  their free partner (e.g. `Martial Training III > Martial Training IV`) while others didn't. `assign_feats_to_levels`
  runs twice but the tax-bucket rehoming ran only after the first pass; the second pass re-migrated some
  feats between the normal/class buckets, leaving their tax bundle in the wrong dict so the sheet (which
  applies each bucket's tax dict only to its own bucket) dropped the chain. The rehoming now runs after
  the **final** reorder. Verified 0 mis-homed Martial Training primaries across 99 of them; feat/story
  counts unchanged. (`main_test.py`, `spheres.py`.)
- **Feats are no longer silently dropped on the sheet (the real cause of "missing 1-2 feats").** The
  backend exported the correct number of feats, but the FoundryVTT module's `processFeatTrait` silently
  dropped any feat name it couldn't resolve against its `every_feat.json` compendium (an incomplete
  export missing many real Paizo feats — Mighty Conditioning, Pet, Leg Slash, …) — and because feats are
  labeled positionally, a dropped feat removed the **top** slot (e.g. Feat 19 / Story Feat 20). Measured:
  every one of 20 generated Fighters dropped 1-4 feats across buckets. (It was not the feat-tax system —
  `applyFeatTax` only decorates a parent's name with `> Child`, never removes rows.) Fix: the backend now
  supplies a description entry for **every** placed feat (`homebrew_feat_desc_dict`, best-effort from
  `data/feats.csv`), so the module's existing fallback **synthesizes** any compendium-missing feat instead
  of dropping it — backend restart only, no Foundry reload needed. The module was also hardened
  (`modify-abilities.js`): `every_feat.json` matching is now case/punctuation-insensitive (compendium
  feats that differ only by casing now resolve to their real item), and an unmatched feat is synthesized
  rather than dropped as a final safety net. Verified: **0 would-be-dropped feats across 45 generations**
  (Fighter/Warder/Wizard), down from 1-4 per character, with bucket counts still exact.
- **Feat counts are now guaranteed exact, and the running backend's version is visible.** A final
  reconciliation pass (`main_test.py`, just before export) forces the general feat track to exactly
  `normal_feat_amount` (feats at the character's real levels 1,3,…,19 — no gaps, nothing past their
  level): it backfills any shortfall (locking in the earlier reservation/strip fixes against future
  regressions) and, in the rare case where homebrew (Path-of-War Martial Training + Sphere Extra-Talent
  feats) outnumbers the slots, caps to exact by trimming the lowest-priority excess — sphere Extra-Talent
  *tracking* feats first (the talents themselves stay on the sheet as native Combat/Magic talents), then
  any remaining tail. Verified exact (general 10/10, story 5/5) across 90 generations spanning
  Fighter/Warder/Wizard × both feat-randomization modes, with zero failures. Also added a
  `GENERATOR_VERSION` stamp: printed in a startup banner by `app.py`, logged per generation, returned on
  each result, and written by the FoundryVTT module to a hidden actor flag
  (`flags.pf1e_random_char_generator.version`) — so a restart visibly loads the new code and any exported
  sheet reveals which backend build produced it (the recurring "I restarted but it's still wrong" was a
  stale `:5001` backend serving old code).
- **NPCs with Spheres no longer lose high-level feats (and story feats are no longer dropped).** A
  Spheres-selected NPC could come out missing the top entries of its feat tracks — e.g. a level-20
  Fighter showing `(Feat 1…11)` but nothing at 13/15/17/19, and missing the level-20 story feat. Two
  causes: (1) the sphere/PoW feat-budget **reservation** (`main_test.py`) subtracted a *rolled estimate*
  (`_priority_reserve + max(0, sphere_feat_budget_count − realize_sphere)`) that drifted off the real
  number of homebrew feats appended to the list, so it over-reserved (dropping the top "(Feat N)" slots —
  the bug) or under-reserved (spilling feats past the top level); it now reserves **exactly**
  `len(mt_feats) + len(style_feats) + len(sphere_feats)` — the Martial-Training, style, and sphere
  Extra-Talent feats that actually get appended — so the normal track lands at exactly
  `normal_feat_amount` every time. (2) The tax-child **strip** removed story/flaw/flavor feats that
  happened to be feat-chain children but, unlike the class/normal buckets, never **backfilled** them, so
  the story list shrank and its top level slot (15/20) was orphaned; story/flaw/flavor are now topped
  back up to their budgeted counts after the strip. Verified over 80+ generations (Fighter & Warder,
  level 20, both feat-randomization modes): no track ever comes up short. (Trainers were ruled out —
  they're funded off-budget and never consumed the feat allotment.)
- **Advanced / legendary sphere talents are now reliably labeled, and the registry is comprehensive.**
  Advanced talents (especially combat *legendary* talents like Bomb Jump) were silently never flagged,
  so they never showed `(Advanced)` on the sheet and weren't treated as advanced by the §8 picker. Root
  cause: the `advanced_talents.json` registry stores wiki names with their variant suffix (e.g.
  `"bomb jump (leap)"`) but the talent datasets are keyed by the clean name (`"bomb jump"`), and the
  three advanced-matching sites normalized with `_norm` — which strips `[source]` tags but not a
  trailing `(variant)` — so the names never matched. Now they normalize with `_talent_match_norm` (the
  same suffix-stripping the compendium filter already uses) in `_advanced_set`, `_is_advanced`, and
  `_talent_item`. Separately, the registry was rebuilt comprehensively from the Spheres wiki by the new
  `Backend/scripts/scrape_advanced_talents.py` (every magic sphere's *Advanced … Talents* section + every
  combat sphere's *Legendary Talents* section), adding 213 names — including whole combat spheres that
  were missing entirely (Equipment, Warleader) — merged so curated/homebrew-only keys with no wiki page
  (e.g. power → `bear`) are preserved. Verified end-to-end: advanced talents are now flagged across 15
  combat spheres and the magic side is unchanged. (`spheres.py`, `advanced_talents.json`,
  `scrape_advanced_talents.py`.)

### Changed
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
