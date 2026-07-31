# Feature Spec TODO — awaiting design input

> **End goal:** click the generate button → a **fully playable** PF1e NPC, with nothing left to
> hand-finish before it hits the table.
>
> The six features below are **partially scaffolded** in the codebase but each needs **your spec on
> *how* you want it added** before it can be built. Under each, fill in the **`Your spec:`** line
> (the rules to follow, priorities, edge cases, and — importantly — *what the generated NPC / JSON
> export should contain*). I'll implement against whatever you write there.
>
> Related docs: campaign house rules → [homebrew_rules.md](homebrew_rules.md) ·
> unified feat pool → [`data/feats_new.csv`](../data/feats_new.csv).

---

## 1. Path of War — ✅ IMPLEMENTED (base classes + martial paths)
**Current state:** wired into generation and export. The six base PoW classes (`stalker, warlord,
warder, harbinger, mystic, zealot`) generate end-to-end and are **back in the random class pool**
(entries built into `Backend/json/class_data.json` by `Backend/scripts/build_pow_class_data.py`);
`Backend/utils/class_func/path_of_war.py` selects disciplines (via `select_disciplines()`),
maneuvers, stances, and readied sets.

**Spec (as agreed, 2026-06-11):**
- **Non-PoW characters** roll "martial paths": BAB `L` → 0–1 disciplines, `M`/`H` → 0–2 (casting
  level ignored); at level 20+ both bounds gain +1. Chain depth by `bab_total` (I needs BAB +3,
  III +7, V +11; below +3 → no paths). **Each rolled discipline is its OWN full Martial Training
  chain** (MT I..depth) drawing only from that discipline; **each chain costs its own paid feats**
  (I/III/V = `depth//2` per chain) and the chain count is **capped by available normal feat slots**
  — a feat-poor build gets fewer disciplines than it rolled. II/IV/VI arrive free via a hand-built
  tax bundle (the chain feats are discipline-labeled — "Martial Training I (Broken Blade)" — so
  repeats don't collapse; the base six rows in `data/feats.csv` carry sentinel `type = "Path of
  War"` so random pools never pick them).
- Counts mirror the spellcaster tables (known ≈ spells known, readied ≈ spells per day, **no
  ability-mod bonuses**): MT users read `martial_training_progression.json` (cumulative per chain
  depth, stance-preferred at V/VI) **per chain** — N disciplines ≈ N× the maneuvers; initiator
  classes read `path_of_war_maneuvers_known.json` at class level over one shared pool
  (Metzofitz-scraped tables are authoritative). **For MT users the FEAT TIER is the maneuver-level
  gate: max maneuver level = depth, and tier t grants level-t maneuvers** (per-tier deltas of the
  cumulative table). Initiators: max maneuver level = min(ceil(IL/2), 9). IL = class level for
  initiators, floor(level/2) for MT users (display / stance scaling only).
- **Export** (`/update_character_data`): `martial_disciplines`, `initiator_level`,
  `maneuvers_known_list` / `maneuvers_readied_list` (per-maneuver-level counts),
  `maneuvers_choose_from` / `maneuvers_readied_names` (names grouped by level),
  `stances_chosen`, `mt_feats`, `initiation_stat` (arg-max of FINAL Int/Wis/Cha — same calc as
  the skill-rank scaling; pf1-pow initiating ability), and `maneuvers_desc_dict` (per-maneuver
  description/type/level/discipline/action/range/duration — the Foundry module prefers the
  pf1-pow.disciplines compendium and falls back to this for unmatched names).

**Done since:** **Medic** (Metzofitz) is now fully wired (class_data + dropdown + metzofitz maneuver
table). The FoundryVTT side is live too — the 6 base classes + Medic are exported into
`every_class.json` from the everyClassPerson actor via `tools/export_every_class.macro.js`.
**Selection v2 (2026-06-12):** initiators specialize in randint(2,3) class disciplines; all
maneuver/stance picks are prerequisite-legal (same-discipline counts, stances count, bootstrap
for the three no-prereq-0 disciplines); initiators take 1..N(specialized) Metzofitz style feat
chains (base paid like MT, followers always feat-taxed through); homebrew feats are synthesized
from `homebrew_feat_desc_dict`. See the OKF `pathfinder` bundle, `oks/pathfinder/path-of-war/`.
**Native pf1-pow items (2026-06-12):** the Foundry module now creates native `pf1-pow.maneuver`
items (compendium-first from `pf1-pow.disciplines`, synthesized fallback), so maneuvers render in
pf1-pow's own Path of War tab — names prefixed `(Strike)/(Boost)/(Counter)/(Stance)`,
`system.class` = class item name for tab grouping, readied maneuvers start ready/charged. Martial
Training characters get `system.maneuverProgression = {archetype, regular, initiatorAttr:
initiation_stat}` on the class item + the `flags['pf1-pow'].maneuverAttr` actor flag (initiator
classes untouched — every_class.json already carries theirs). Each stance also becomes an
inactive temp buff under a "____ Path of War ____" buff divider; mechanical changes from
`stance_changes.json` (curated via `Backend/scripts/build_stance_changes.py`, `@pow.initLevel`
scaling with `ifelse()/gte()`), description-only otherwise. The PoW tab's `sortManeuvers` helper
is overridden (discipline → Strike/Boost/Counter/Stance → level inside each level section). With
pf1-pow disabled, the legacy "____ Path of War ____" feat-item section is the fallback.
**Stalker & Zealot are temporarily shelved** (`pow_classes_pending_foundry` in `data.py` + commented
dropdown entries): they generate on the backend but aren't in the pf1-pow Foundry compendium yet
(module not shipping them as of 2026-06 — maintainer may need a ping). Re-enable when they appear.

**Still open (follow-ups):** the other Metzofitz initiators (`epilektoi, parasite, rajah, voltaic`
— note rajah's nested JSON shape); PoW archetypes (`path_of_war_archetypes.json` is
loaded-but-unused); class-feature choosers (stalker arts / warder defenses / warlord gambits /
zealot convictions).
**Maneuver conditionals on the main weapon (2026-06-13, implemented):** each known
strike/boost/counter with a clean numeric combat effect is now a **pf1 conditional modifier on the
main weapon's attack action** (main weapon = the `weapon_name` export), named with the same
`(Strike)`/`(Boost)`/`(Counter)` prefix as its maneuver item, **default off** — toggled per-roll
from the attack dialog (e.g. "(Strike) Sting of the Rattler" → +1d4 damage). `formula` keeps real
dice (`2d6`), unlike buff changes which collapse to a flat maximized number. Data:
`Backend/scripts/build_maneuver_changes.py` (manual tool) drafts modifiers from
`Martial_Disciplines.json` Descriptions (conservative damage-dice / attack-bonus regexes) →
`maneuver_changes.draft.json`; the curated high-confidence subset lives in the Foundry module's
`templates/character_sheet_folder/maneuver_changes.json` and is attached by
`addManeuverConditionals()` in `modify-abilities.js`. **Stance dice damage stays description-only**
(buff `changes` can't roll per-hit dice). Non-numeric maneuvers (double damage, saves, conditions,
skill-replaces-attack) have no conditional — their pf1-pow item + description is the reference.

---

## 2. Spheres of Power / Spheres of Might
**Status: IMPLEMENTED (v1 — dabbling).** Chooser `Backend/utils/class_func/spheres.py`
(`randomize_spheres_num` / `choose_spheres_attr`), wired into `Backend/main_test.py` after the Path of
War block (feat-slot reservation) and exported as `magic_talent_items`, `combat_talent_items`,
`sphere_feats`, `sphere_feat_tax`, `sphere_mana_pool`, `spheres_chosen`, `sphere_counts`,
`casting_tradition`, `sphere_drawbacks`, `sphere_boons`, `sphere_traits`. Data is extracted from the
FoundryVTT `pf1spheres` compendium by `Backend/scripts/extract_spheres_talents.py`
(`spheres_of_power.json`, `spheres_of_might_enriched.json`, `sphere_feats.json`, `advanced_talents.json`,
plus harvested `spheres_traditions.json`). Still connects to
[homebrew_rules.md §1](homebrew_rules.md) (proficiency → Martial Tradition trade at
`armor_and_weapon_chooser.py`) and the Spheres systems in §5.

**Spec as built (locked with the user):**
- **Trigger:** opt-in `spheres_flag` (default off). Real spherecasting *classes* and Spheres of *Guile*
  are out of scope.
- **Who/how many:** a flagged normal NPC dabbles into **0–3 spheres**; per sphere, **Might vs Power**
  by caster level (none→Might; low→50/50; mid/¾→Power 75%; high/full→Power 90%).
- **Talents are feat-funded:** `Basic Magic Training` (magic entry: sphere + tradition + pool, 1 talent)
  and `Extra Magic|Combat Talent` feats (each = 2 talents via the HR1 `Extra Talent > Extra Talent`
  duplicate); reserved out of the normal feat budget like Path of War MT feats.
- **§8 advanced gate (hard invariant):** per sphere, advanced/legendary allowed =
  `(normal_talents + 2 × sphere_feats) // 7`, enforced at selection and re-asserted on the final list.
- **Casting tradition + HR4 mana pool** built for magic dabblers (CAM = highest mental stat; drawbacks →
  boons → bonus spell points on the triangular chart; pool = highest mental mod (min 1) + bonus SP).
- **Export shape:** talents as `{name, sphere, system, type, description, changes, contextNotes, uses}`
  item dicts (rendered like profession ability items); sphere feats join the feats section with the
  `sphere_feat_tax` HR1 bundle.

**Six-detail enrichment (2026-07-20):** talent riders now use the labeled-clause format (real
spell-point counts; a `Range:` clause where derivable) via `enrich_conditional_riders.py` +
`conditional_clauses.py`. See §7 and
[spheres_conditional_decision_rules.md](spheres_conditional_decision_rules.md#the-six-detail-labeled-clause-format-2026-07-20).

**Per-roll talent conditionals (2026-07, implemented — mirrors the Path of War maneuver-conditionals
pipeline).** Attack-relevant talents become **default-off conditional toggles** on the main weapon's
attack action (Might + non-Destruction Power) or on a synthesized **Destructive Blast** attack item
(Destruction), toggled per-roll like maneuvers. Clean on-hit damage/attack numbers are structured
`modifiers[]` (auto source-labeled); saves/DCs/conditions/durations/bleed ride the conditional NAME
with `[[ ]]` inline rolls. See [spheres_conditional_decision_rules.md](spheres_conditional_decision_rules.md).
- **Draft + worklist:** `Backend/scripts/build_talent_conditionals.py` (regex seeds + `--dump-worklist`
  per-sphere slices).
- **Curation:** gitignored `Backend/scripts/_spheres_generator/` (per-sphere `curated_might/`,
  `curated_power/` files; `promote_talents_to_module.py` merges + validates them).
- **Module data:** `<module>/…/combat_talent_conditionals.json` + `magic_talent_conditionals.json`
  (nested `{Sphere:{Talent:{modifiers,rider}}}`); attached by `addSphereTalentConditionals()` /
  `addDestructiveBlastAttack()` in `modify-abilities.js`. Dabbler tokens (`@spheres.cl.total → 1`,
  `@spheres.cam/pam → @abilities.*.mod`) substituted at attach time; `flags.pf1spheres.castingAbility/
  practitionerAbility` stamped on the actor. **Passive** self-buffs stay in the backend
  `combat_talent_changes.json` (Changes tab) — a separate file from the per-roll conditionals.
- **Palette:** `build_pow_template_actor.py --spheres {none,curated,all}` bundles per-sphere weapons +
  the Destructive Blast onto the importable actor (native `@spheres.*` tokens so copies scale on a real
  PC; a "Palette: Sphere CL 10" toggle for local testing).

**Deferred (v2):** real spherecasting base classes (front-end / everyClass), Spheres of Guile, a
**martial-focus resource pool** (`@resources`) for combat talents (v1 states "expend martial focus" in
rider text only), and richer combat-legendary classification (`advanced_talents.json["might"]` is the
editable registry).

---

## 3. Weapon attacks
**Current state (verified):** `Backend/utils/class_func/armor_and_weapon_chooser.py` picks a weapon,
but only the weapon's **name** is exported (`weapon_name = list(character.weapon_dict.keys())[0]`,
`Backend/main_test.py:425`). `Backend/json/weapons_data.json` has the weapon stats. **No computed
attack routine** — no to-hit, ability mod, iterative attacks, or damage string.

**Needs from you:** the formula for a full attack line (BAB + ability mod + size + enhancements →
iteratives), how to fold in the homebrew Weapon Finesse / weapon-group rules
([homebrew_rules.md §4](homebrew_rules.md)), and the export format (e.g. `+11/+6 (1d8+4, 19–20/×2)`).

**Your spec:**

---

## 4. Weapon conditionals
**Current state (verified):** nothing yet — no data, no code. This is the *conditional* layer on top
of #3: crit ranges/multipliers, conditional or special-property damage (e.g. bane, elemental, sneak
attack riders), and Called Shots ([homebrew_rules.md §5](homebrew_rules.md)).

**Needs from you:** which conditionals matter for a ready-to-play NPC, how they should be expressed
(precomputed alternate lines? notes the GM applies?), and their priority vs. #3.

**Your spec:**

---

## 5. Free feats
**Current state (verified):** the story-feat cadence is implemented —
`story_feat_amount = 1 + floor(level/5)` in `Backend/utils/class_func/level_and_bab.py` (1/2/3/4/5
feats at L1/5/10/15/20, per [homebrew_rules.md §1](homebrew_rules.md)). **Not yet implemented:** the
**+2 feats at character creation** and the **per-flaw bonus feats** (§1, backlog #2). Distinct from,
but overlapping with, the feat-tax auto-grants in #6.

**Needs from you:** confirm the creation-feat / flaw-feat counts and how flaws are rolled/assigned for
an NPC, and whether "free" weapon-proficiency-style grants belong here or under #2/#3.

**Your spec:**

---

## 6. Feat taxes
**Status — chain taxes implemented (2026-06):** `feat_tax_func` (`Backend/utils/class_func/feat_tax.py`)
grants a primary feat's progression chain (from `Backend/json/feat_tax.json`) for free when prereqs
are met, **1 feat per 2 levels** since the primary was gained; "Extra …" feats grant a free
self-duplicate; Mythic feats never tax. The FoundryVTT module renders them bundled on the primary
entry as `"<Label> Primary > Tax1 > Tax2"`.

**Still pending (needs your spec / blocked):**
- **Auto-granted "free" feats** when you simply qualify (e.g. *Raging Vitality* for
  barbarians/bloodragers) plus the always-free / removed-prerequisite / baked-in-Weapon-Finesse rules
  from [homebrew_rules.md §4](homebrew_rules.md) — a *different* mechanic from chain taxes; give me
  the authoritative lists and I'll drive them from data. (Overlaps #5.)
- **Martial Training taxes once free** — blocked on Path of War (#1).
- **Sphere of Power talent → +1 talent** — blocked on Spheres (#2).
- Expanding / verifying the chain data in `feat_tax.json` against your Feat Tax Google Doc.

**Your spec:**

---

## 7. Spell conditionals
**Detailed-effect sweep (2026-07-20):** all 619 rider spells re-authored verbose + grounded from the
CSV descriptions (per-target splits, immunities, per-round saves, secondary targets/damage, SR,
computed CL-scaled values). Pipeline: `build_spell_rider_worklist.py` → Sonnet author→verify workflow
→ `merge_spell_riders.py` → `enrich_conditional_riders.py` → `validate_spell_conditionals.py`. Samples
in `docs/spell_rider_pilot_samples.md`. See also the plan `docs/spell_rider_detail_sweep_plan.md`.

**Six-detail enrichment (2026-07-20):** every curated rider now carries labeled `Cost:`/`Activation:`/
`Range:`/`Save:`/`Effect:` clauses (damage stays on `modifiers[]`). `enrich_conditional_riders.py`
(shared builders in `conditional_clauses.py`) appends only missing clauses idempotently — CL-scaled
range from the CSV `range` column, gp material cost, and the computed save DC `[[ 10 + @slvl +
@castMod ]]` (substituted by the module + the applier macro). The applier gained a per-weapon
review/edit pop-up with persistent per-weapon overrides. See
[spheres_conditional_decision_rules.md](spheres_conditional_decision_rules.md#the-six-detail-labeled-clause-format-2026-07-20).

**Status — ✅ Buckets A/B/C live end-to-end (2026-07-18).**
`Backend/scripts/build_spell_conditionals.py` classifies every spell in `data/spells.csv` into:
- **A** — attack/damage buffs → `spell_changes.json` (120 curated, fully covers the draft pool)
  → default-off toggles on the main weapon (`addSpellConditionals` / the palette's spell-buff
  weapon).
- **B** — touch-attack damage spells → `spell_riders.json` → save + `[[ ]]` riders on the spell
  item (`addSpellRiders` / the palette's `build_rider_spells`).
- **C (new)** — offensive **non-touch** spells: area/save damage (Fireball), save-or-suffer
  (Hold Person), debuffs/conditions (Bane, Slow). Same entry shape as B with `attack: null`, so
  it flows through the B plumbing untouched. Per the user's "always explicit" decision the riders
  restate the save clause + full effect (per-CL damage as computed-dice inline rolls) even when
  the compendium action already rolls it; harmless-save and stub-only entries are gated out
  (both in curation and in the palette's draft path).

Curation batch 1 (2026-07-18): **239 curated rider spells** (83 hand-authored gold classics +
137 vetted drafts + 19 pre-existing B), priority = NPC-learnable ∩ `every_spell.json`, widest
class lists / lowest level first. Validator: `Backend/scripts/validate_spell_conditionals.py`.

**Remaining (batch 2+):**
- [ ] Curate the rest of the gated worklist (~355 more compendium-present draft entries; the
  palette already carries them draft-gated, generated NPCs only get curated entries).
- [ ] **De-duplicate vs the buff.** When a spell gains a weapon conditional, drop the redundant
  contextNote from its Buffs-tab buff (same rule as the stance dice-damage escape hatch).
- [ ] Optional: restate damage explicitly on the 19 legacy B entries for uniformity with C.

---

## 9. Psionics (Dreamscarred Press / Library of Metzofitz)
**Status: SPEC LOCKED (2026-07-31) — implementation in progress on `feat/psionics-v1`.**
Twelve base classes: `aegis, cryptic, dread, highlord, marksman, psion, psychic warrior, soulknife,
tactician, vitalist, voyager, wilder`. Charted in `docs/wayfinder/psionics/`; this section is that
map's destination. §1 (Path of War) is the governing precedent throughout — a 3pp system whose
mechanics are scraped into `Backend/json/` while a third-party Foundry module renders the result.

**Sources and the split (locked):**
- The **[Library of Metzofitz wiki](https://libraryofmetzofitz.fandom.com/wiki/Psionic_Classes) is
  the source of truth for mechanics** — same authority as `data/Metzofitz_Feats.csv`. Scraped by
  `Backend/scripts/scrape_psionics.py` (via `api.php`; plain `/wiki/` hits Cloudflare) into
  `Backend/json/class_data/psionics/` — 12 classes, 615 powers, 12 power lists, 10 races.
- **[`pf1-psionics`](https://github.com/SoxMax/pf1-psionics) is adopted as the render target, not a
  data source.** We do not build our own module. Its *powers* are clean, but **all twelve of its
  class items carry placeholder `bab: low` / `hd: 6` / `skillsPerLevel: 2`** and powers-known exists
  nowhere in it — which is why the wiki, not the module, supplies mechanics.
- Independent cross-check that the scrape is right: **every manifesting class's PP column matches one
  of `pf1-psionics`' three hardcoded progressions exactly.**

**Division of labour (ticket 03) — the backend computes, the module renders.**
`pf1-psionics` auto-calculates manifester level, concentration and power points, but the payload
still carries them as finished numbers, exactly as §1 emits `initiator_level` alongside letting
pf1-pow render items. Rationale: the payload is the API contract, the standalone web sheet has no
game system to compute anything, and `test_house_invariants.py` needs something to assert on. The
two agree rather than fight because the PP tables are identical.
- **Class items:** `tools/export_every_class.macro.js` harvests the twelve `pf1-psionics` class items
  into `every_class.json` (as PoW classes were harvested from pf1-pow) and **patches `system.bab` /
  `hd` / `skillsPerLevel` from `psionic_classes.json`** during harvest. Keeping the module's own item
  identity keeps its Psionic Manifesting tab and PP auto-calc bound; patching fixes the three fields
  that are wrong upstream. Actor HP is already safe (`attributes.hp.base` is the backend total and
  class-item HP is zeroed), so the placeholder `hd` was cosmetic — **`bab: low` was not**. pf1 derives
  BAB from class items, and **only psion and vitalist are actually low**: aegis, marksman and
  soulknife are high, and the remaining seven are medium. Upstream's placeholder is wrong for **ten
  of the twelve**.
- **Power points and psionic focus are owned by `pf1-psionics`** when it is active — we add no
  parallel pool, which would double-count on the sheet. When it is **absent**, `addResourcePools()`
  builds a plain PP resource from the payload's `pp_per_day` (the §1 legacy-fallback shape). Focus is
  not a payload field.

**Class tables, verified (ticket 05).** The scrape was checked against d20pfsrd as a control sample —
not to audit the wiki, which wins by definition, but to catch parser errors. **Eleven of twelve match
RAW exactly and the parser is not at fault anywhere**, including the three rows that looked wrong
(voyager's d6-with-medium-BAB-and-6+Int, vitalist's d6/low-BAB, dread's 6+Int — all genuinely written
that way).

**One deliberate house divergence, recorded here as required:** the **psychic warrior** has **good
Fort only** on the wiki, where RAW gives it good Fort *and* Will (+6 rather than +12 at level 20), and
its feature track is rewritten wholesale into a Path system (Warrior's Path / Path Skill / Twisting
Path / Pathweaving / Eternal Warrior) with no RAW equivalent. Verified against the wiki's `api.php`
output, not merely our scrape. **This is not to be "fixed" back to RAW.**

**Manifesting ability** — Int: aegis, cryptic, psion, tactician, voyager · Wis: marksman, psychic
warrior, vitalist · Cha: dread, highlord, wilder · soulknife: none. **Bonus power points are a
formula, not a table:** `floor(key_ability_mod × manifester_level / 2)`, with a separate gate that a
key ability of **9 or lower cannot manifest at all**. No `spells_from_ability_mod.json` analogue is
needed. No psionics-specific house rule exists; the universal 2→4 skill-rank floor in
`skill_ranks.py` is class-name-agnostic and applies to psion and vitalist automatically.

**Class-pool entry (ticket 04) — no API flag.** The §1 precedent, not the Spheres one: the twelve
live in `Backend/json/class_data.json` with `data.good_saves` rows and are in the random pool by
default. Holdbacks go in `data.psionic_classes_pending` (mirrors `pow_classes_pending_foundry`, read
by `Backend/utils/util.py::_available_class_pool`). Psionics is *additive* like PoW, not a casting
replacement like Spheres, and a flag would mean threading a new key through `app.py`'s positional
unpack plus `generate.js::buildPayload` plus the module's `button.js`. Accepted consequence: psionic
classes are ~12 of 55 pool entries. Manifesting ability gets its **own** map in `data.py` — not
`caster_mod`, because power points are not spells-per-day.

**Twelve is the target (tickets 04/08).** A class may be held out of the pool, but **every holdback
is recorded here with the subsystem it waits on**. No class ships hollow. Nine of the twelve carry a
choice-bearing subsystem — aegis customizations, cryptic insights, vitalist methods, psychic warrior
paths, marksman styles, tactician strategies, dread terrors, voyager path skills, highlord decrees,
soulknife blade skills — and **all nine ride the existing
`generic_func.py::generic_class_option_chooser`**, the same one that drives bloodlines, orders,
mysteries and weapon training. No new chooser module. The one genuine exception is the **soulknife's
mind blade**, which is a weapon rather than a list: it becomes a synthesized weapon whose enhancement
bonus comes from the class table, reusing `enhancement_effects_dict` and special-cased against
`armor_and_weapon_chooser.py`.

**Power selection (ticket 07).** Modelled on `path_of_war.py` **minus the prerequisite machinery** —
psionic powers have no prerequisites, so `_constrained_pick`'s prereq graph has no analogue here.
Max power level comes from the class table at manifester level; the legal pool is that class's list
in `psionic_power_lists.json` at levels 0..max; the **psion's discipline is rules-mandated** and
picked first, while every other class takes a soft bias toward 2–3 disciplines so a build reads as a
concept rather than a grab bag; picks are weighted toward the highest available level, as §1 does.
"Manifester" is **three categories, not one**: full manifesters, the **aegis** (power points, no
powers known), and the **soulknife** (neither) — the payload models all three.

**Name reconciliation (ticket 10).** The module attaches by name match and **silently drops** an
unrecognised name — the failure mode that already bit spell conditionals. Two independent defences:
`Backend/scripts/reconcile_psionics_names.py` reads the module's LevelDB packs and emits
`psionic_name_map.json`, and `validate_psionics_data.py` **fails on any unmapped name**; separately
the module normalises apostrophes and case at attach time. The surface is larger than it looks — the
module's *classes* pack holds **419 items**, because every class feature ships as its own named item,
and its packs mix `’` (U+2019) with `'` (U+0027) internally. **The payload emits the module's name
where one matches, and the wiki's name plus a `powers_desc_dict` entry where it does not**, so
Metzofitz-only content is synthesized rather than lost.

**Export** (`/update_character_data`): a `manifesters` list beside `spellbooks`, one entry per
psionic class — `name`, `display`, `level`, `manifester_level`, `manifesting_stat`, `pp_per_day`,
`max_power_level`, `powers_known_list`, `powers_chosen`, `discipline` — plus `powers_desc_dict` as a
sibling top-level key, exactly as `maneuvers_desc_dict` sits beside the PoW block. **Augmentation is
not a generation-time field**: spending extra PP for a bigger effect is a use-time choice, and
`pf1-psionics` ships an in-dialog augment editor for it.

**Licensing (ticket 09).** Root `LICENSE-OGL.txt` carries OGL 1.0a plus a **hand-curated §15 built
from the `sources:` in our own scraped data** — upstream's §15 is incomplete (it omits *Psionics
Expanded: Advanced Psionics Guide*, which the aegis traces to) and is copy-pasted verbatim into
pf1-pow, so it cannot be reused. `Backend/json/class_data/psionics/NOTICE.md` marks that subtree as
Open Game Content and the Python as not (§8 marking). Because an HTTP response carrying extracted
mechanics is Distribution under §10, `Backend/app.py` serves a stable `/license` route and the
payload carries a pointer field rather than embedding the licence. `pf1-psionics` is credited as the
intermediate compiled source, alongside Paizo CUP and a DSP non-endorsement line.

**Deferred (not built):** web-sheet rendering of manifesters · **psionic races** — the ten scraped
*Psionics Unleashed* races stay data-only; ticket 11 is re-scoped as the **custom-race route** ticket
covering Loxo/Kalyptran/Dolistani too, because `PlayableRaces.json` is walked *positionally* by
`race_func.py::race_traits_chooser` and psionic Duergar collides with core Duergar · the six v2
classes (Genesis, Skipper, Thug, Warpmind, psionic Zealot — note `zealot` is taken by the PoW class —
Soulknife (High Psionics)) and the Gifted NPC class · the **psicrystal**, structurally a companion
(see `docs/wayfinder/companions/map.md`) · turning on the **311 psionic feats already in
`data/Metzofitz_Feats.csv`** (gated by `_METZ_TYPES` in `feats.py`; the data is there, the eligibility
rules are not decided) · power **conditionals** on the main weapon, mirroring §4/§7 · psionic items
(cognizance crystals, dorjes, power stones) in the gear chooser · multiclass manifester-level
stacking · reporting upstream's incomplete §15 and placeholder class fields to SoxMax and the wiki
editors.
