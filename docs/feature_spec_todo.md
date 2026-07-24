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
