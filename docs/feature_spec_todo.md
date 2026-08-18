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
(entries built into `Backend/json/class_data.json` by `Backend/scripts/build/build_pow_class_data.py`);
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
`stance_changes.json` (curated via `Backend/scripts/build/build_stance_changes.py`, `@pow.initLevel`
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
`Backend/scripts/build/build_maneuver_changes.py` (manual tool) drafts modifiers from
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
FoundryVTT `pf1spheres` compendium by `Backend/scripts/build/extract_spheres_talents.py`
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
- **Draft + worklist:** `Backend/scripts/build/build_talent_conditionals.py` (regex seeds + `--dump-worklist`
  per-sphere slices).
- **Curation:** gitignored `Backend/scripts/build/_spheres_generator/` (per-sphere `curated_might/`,
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
`Backend/scripts/build/build_spell_conditionals.py` classifies every spell in `data/spells.csv` into:
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
class lists / lowest level first. Validator: `Backend/scripts/gates/validate_spell_conditionals.py`.

**Remaining (batch 2+):**
- [ ] Curate the rest of the gated worklist (~355 more compendium-present draft entries; the
  palette already carries them draft-gated, generated NPCs only get curated entries).
- [ ] **De-duplicate vs the buff.** When a spell gains a weapon conditional, drop the redundant
  contextNote from its Buffs-tab buff (same rule as the stance dice-damage escape hatch).
- [ ] Optional: restate damage explicitly on the 19 legacy B entries for uniformity with C.

---

## 8. Bonded creatures (animal companions, mounts, familiars, eidolons)
**Status: SPEC LOCKED (2026-08-01) — build slices 1–4 landed, 5–9 open.** Charted in
`tickets: feature/companions` (closed); this section is that map's destination. The **build** is
charted separately in
[`tickets: feature/companion-sheets`](https://github.com/The-Data-is-a-lie/tickets/blob/main/tks/pathfinder-char-creator/feature/companion-sheets/map.md)
(open) — it decides only what this section left open and does not reopen D1–D10. §1 (Path of War)
and §9 (Psionics) are the governing precedents: the backend owns the numbers, a Foundry-side renderer
owns the presentation, and every holdback is named here rather than left implicit.

**Current state:** `Backend/utils/class_func/animal_companions.py` resolves **every** grantor —
`resolve_bonded_creatures()` reads the declarative `Backend/json/companion_grantors.json`, honours
archetype bonds, stacks same-type sources under the character-level cap, and emits D9 identity
(`name`, `sex`, `gear`, `gear_source`) onto `character.bonded_creatures`. `animal_feats()` reads the
chassis row's own `feats` count.

**The numbers and the export landed 2026-08-03 (#31, #32, #35).**
`Backend/utils/class_func/companion_stats.py` merges the advancement block and computes the whole
stat block; `main_test.py` emits `bonded_creatures` beside the frozen `animal_companion` alias;
`validate_companion_stats.py` (validators 13 → 14) gates the arithmetic species-by-species and
`test_house_invariants.py` gates the emitted shape and the druid flip.

**Familiars landed 2026-08-13 — the v1 debt paid.** The `species_pool: ["familiar"]` grantor rows
resolve from `Backend/json/familiar_choices.json` (the ten Core Rulebook base familiars) and scale
by `Backend/json/familiar_master_bonus.json` (the 20-row master table). Because every number keys
off the **master** — half HP, master BAB, best-of base saves, the master's skill ranks overlaid,
HD = master level — the stat block is computed by a **late pass**
(`Backend/utils/class_func/familiars.py::stat_familiars`, called after luck resolution) rather
than in `stat_bonded_creatures`, where those inputs are not yet final; a familiar entry therefore
carries **no chassis**. The `master_abilities` export field ships the accumulated table abilities
with rules text plus the species perk, as prose, never folded into the master's math. Gated by
`validate_familiar_data.py`, the names gate (all ten match `pf-familiars`), the invariant sweep's
familiar branch, and the `witch` golden. Familiar feats (Weapon Finesse et al.) are not modeled —
same simplification as companions; improved familiars stay in Deferred.

What is **not** built, and what the remaining sheets wait on:

- **No renderer.** `createCharacter.js` creates exactly one Actor (#33); the web sheet's Companions
  tab is hand-typed (#34). Both wait on tickets 02 and 03 of the companion-sheets map.
- **`progression_override` is carried, not applied.** It is prose; the entry reports it under
  `stats.unapplied` rather than implying otherwise (D12).

`summoner` and `summoner (unchained)` are rollable today and generate no eidolon at all, so a
summoner NPC is still missing its entire class identity.

### The twelve locked decisions

- **D1 — one payload, N Actors** *(ticket 01)*. The backend still emits **one** character. The
  Foundry module loops and creates one extra Actor of type `npc` per bonded creature, in the existing
  "Random Characters" folder (`createCharacter.js:2` creates the PC today; folder assignment at
  `:32-47` and `:157`). **Not** a second `generate_random_char()` run. pf1 has no companion actor
  type — `systems/pf1/template.json` registers only `character, npc, vehicle, haunt, trap`.
  *Rejected:* items-on-the-owner's-actor, and sheet-text-only.
- **D2 — the backend owns the numbers; the module clones the body** *(tickets 01, 06)*. The backend
  computes HP, saves, BAB, AC, ability scores, size and skills so the **standalone web sheet works
  with no game system to lean on**, exactly as §9 emits finished manifester numbers even though
  `pf1-psionics` could derive them. The module clones the `pf-content` Actor matching the species for
  identity, art, natural attacks, senses and special qualities, then patches the payload's numbers
  over it. *Rejected:* letting pf1 derive everything from chassis + items.
- **D3 — graceful degrade + validator gate** *(ticket 01)*. A compendium miss yields a bare `npc`
  Actor built from the payload numbers plus a `console.warn`; a CI validator diffs species names
  against a checked-in dump of `pf-content` actor names. This is the §9 name-reconciliation lesson
  applied early — the module attaches by name match and **silently drops** what it cannot match.
  *Rejected:* a curated name map, which would have shrunk the species pool to whatever matched.
- **D4 — v1 is companion + mount + familiar at full stat block; the eidolon is degraded, not
  suppressed** *(tickets 02, 07)*. Summoner emits a named base form plus descriptive text and rides
  the D3 bare-`npc` fallback, so a summoner reads as a summoner; evolutions are v1.1. *Rejected:*
  holding summoner out of the class pool via the `data.pow_classes_pending_foundry` pattern — a
  playable-but-incomplete summoner beats an absent one. The **psicrystal** stays with the psionics
  map (§9 Deferred).
- **D5 — this effort owns the `animal_choices.json` repair** *(ticket 03)*, scripted and narrow,
  with validators. The data cannot be merged as written (see *The data defect* below).
- **D6 — a declarative grantor table and a PF1e stacking cap** *(tickets 03, 05)*. One shared
  resolver replaces the hard-coded druid check. Sources **stack**, capped at character level. Below a
  grantor's own threshold there is **no creature at all** — no clamp to level 1.
- **D7 — `bonded_creatures` (a list) replaces the single `animal_companion` dict** *(ticket 01)*.
  The old key survives as a **deprecated alias** to the first companion-type entry. A druid 5 /
  wizard 5 legitimately gets a companion **and** a familiar — three Actors on import.
- **D8 — v1 also owns four adjacent fixes** *(ticket 05)*: the `animal_feats` bug, archetype
  companion swaps, the wizard/sorcerer arcane-bond coin flip, and **adding the Boon Companion feat**,
  which is absent from the feat data entirely (it appears only inside Spheres talent prose).
- **D9 — identity is emitted, gear is a stated absence** *(slice E, the #37 grill, 2026-08-03)*. A
  creature that exists carries a **`name`** drawn from its master's region pool (never the master's
  own name) and a rolled **`sex`**, because `animal_choices.json` has no sex and the pool is keyed by
  one. **`species` stays the sole `pf-content` match key** — a named companion must never be able to
  miss its clone. It owns nothing: **`gear: []`** plus a **`gear_source`** note saying so *and* that
  the gear will be **funded from `character.gold`** when v1.1 adds it (PF1e gives companions no
  wealth-by-level, so the master pays; expect the PC's own armour/weapon picks to shift for the same
  seed on that day). An **absence entry carries `name: None`, `sex: None` and no gear key at all**.
  The backend emits atoms — **no composed label**; each renderer builds its own (D2).
  *Rejected:* mount tack as a v1 special case (barding's AC math pulls stat-block work forward); no
  gear key at all (the omission this slice exists to prevent); a new curated animal-name list
  (curation is deferred); reusing the master's sex (every companion would match its master);
  a uniform key set with nulls (a null-named, empty-geared ghost still renders); mirroring the new
  fields onto the `animal_companion` alias (a deprecated key that is never worse than its
  replacement never dies).
  **The house rules are silent here.** `oks/pathfinder/house-rules/` mentions animals twice — Handle
  Animal's stat swap and Mounted Combat in the feat-tax list — and says nothing about companion gold,
  gear or ownership. This decision *is* the house rule; do not go re-read those pages expecting one.
  Enforced by `Backend/scripts/gates/validate_companion_identity.py`, because `bonded_creatures` is not in
  the payload until #32 and neither the goldens nor `test_house_invariants.py` can see these fields
  yet.
- **D10 — the two renderers take different shapes, and neither gets a composed title from us**
  *(charting of [Map: Companion sheets](https://github.com/The-Data-is-a-lie/tickets/blob/main/tks/pathfinder-char-creator/feature/companion-sheets/map.md), 2026-08-03)*. D1's "N
  Actors" is a **Foundry** statement: there, each bonded creature is a genuinely separate Actor
  document. On the **standalone web sheet** the creature instead **auto-fills the existing nested
  Companions tab** (`_sheet.companions[]`), which is hand-typed today. That upholds the ruling
  already recorded in that repo — *"linked roster characters were ruled out by portability"* — while
  removing the typing. Each renderer **composes its own title** from atoms it already has
  (`character_full_name` on the payload, `name` and `type` on the entry): `<Master>'s animal
  companion: <Name>` for `companion`, and the matching noun for `mount` / `familiar` / `eidolon`. An
  entry with no species has no title, because it has no creature. *Rejected:* a second roster
  character on the web sheet (portability — the sheet's whole export is one JSON); a backend
  `label`/`title` field (D9 rejected composed labels once already, and two renderers with different
  headers would inherit one phrasing that suits neither); a thin chassis-only sheet shipped ahead of
  the stat-block math — **#31 lands before any sheet work**, because D2 makes the backend the only
  source of numbers and a sheet of placeholder values teaches nobody anything.

- **D11 — the published deltas already own the size package; only the geometry is ours**
  *(ticket 04 of [Map: Companion sheets](https://github.com/The-Data-is-a-lie/tickets/blob/main/tks/pathfinder-char-creator/feature/companion-sheets/map.md), 2026-08-03)*. When an
  advancement block grows a companion, the PF1e size-change table and the per-species deltas overlap,
  and applying both counts the increase twice. The census settles which one holds it: a Dex **penalty**
  appears on all **153** size-increasing blocks and on **none** of the other 43, and a Dex penalty has
  no source but growing. So `str`/`dex`/`con` and the natural-armour delta apply **verbatim** — never
  stripped, never topped up to the table — and the 77% / 50% raggedness needs no reconciling, because
  the published entry is the authority (the standing ruling that makes `validate_companion_data.py`
  WARN rather than fail). What the data does **not** contain is the size-category geometry — AC,
  attack, CMB/CMD, Stealth, space — which appears nowhere in `animal_choices.json`; that comes from
  `companion_stats.SIZE_GEOMETRY`, keyed off the creature's **final** size so a companion *born* Small
  gets its +1 too. The `size_change` record on a stat block is **provenance, not an instruction**: its
  values are already totalled into `ac`, `attacks[].atk`, `cmb`, `cmd` and `skills`, and a renderer
  that re-applies it double-counts. **Reach is deliberately absent** (tall vs long is not in the data;
  `space` is emitted). Enforced by `Backend/scripts/gates/validate_companion_stats.py`.
  *Rejected:* stripping the table out of the deltas (27 rows end with a negative Str residue, so the
  un-buffed body never existed); no size buff at all (the AC/attack/CMB/CMD/Stealth modifiers would be
  missing from the sheet entirely).
- **D12 — the stat block names a source for every number, and reuses the PC's rules but not its code**
  *(ticket 01, same map, 2026-08-03)*. `Backend/utils/class_func/companion_stats.py` owns the merge
  and the math; its docstring is the field-by-field table. Two findings worth keeping: **none of the
  PC's machinery was reusable** — `hp_rolls.roll_hp` and `skill_ranks.skill_rank_budget` both iterate
  `character.classes`, which a companion has none of — so only the maximised-HP *rule* is shared, via
  an imported `homebrew_enabled`. And **the house skill-rank floor does not carry over**: it floors a
  *2-ranks-per-level class* to 4, and the chassis row gives one absolute total rather than a rate, so
  there is nothing to key off. The per-skill cap is RAW (HD) for the same reason. That matches the
  stance `animal_feats` already took on the feat economy. Attacks parse out of the `attack` prose at
  **full BAB** (every natural attack in a printed routine is primary), with PF1e's 1.5x Str for a
  creature with exactly one, **rounded down**. Skill allocation follows the RAW Int 1–2 list, drops
  movement-gated skills the creature has no speed for, and draws its one random choice from a
  **per-creature `random.Random`** rather than the global stream, so a companion's skills never churn
  the rolls made after it. *Holdbacks, all named on the entry rather than implied:*
  `progression_override` is prose, not a structured veto, so it is reported `unapplied` (SESSION_PLAN
  §3's scope boundary forbids a classifier for it); reach and the quadruped +4 CMD vs trip are not
  modelled because the data cannot say.

- **D14 — feats and flaws FOLD into the stat block; buffs stay inactive and do not**
  *(the parity grill, 2026-08-04)*. A companion's feats and flaws always apply, so
  `companion_stats.apply_modifiers` resolves their `changes` into `stats` and records
  `stats.applied_changes` / `stats.context_notes` as provenance; `createCompanions.js` attaches the
  matching feat and flaw items with **`system.changes` stripped**, so pf1 cannot apply what the
  payload already counted. Buffs are the opposite case: situational, never folded, changes intact,
  shipped **inactive** — an inactive buff contributes nothing until a player asks for it, so it can
  never double-count. This preserves D2 rather than amending it: the web sheet has no game system,
  so `stats` must already be finished. An effect the fold cannot place is reported on
  `stats.unapplied`, never dropped — the same holdback discipline D12 set.
  The feat data lives in **`Backend/json/feats/companion_feat_changes.json`**, deliberately NOT the
  shared `feat_changes.json`: the pf1 compendium already automates 12 of the pool's feats and a PC
  keeps its compendium item's changes, so one shared file would double-apply on every PC sheet.
  *Rejected:* letting pf1 derive from intact changes (the web sheet would then be wrong by exactly
  the feat bonuses); curating the pool down to mechanically inert feats (that rules out Toughness,
  Improved Natural Armor and Weapon Focus — most of what makes a companion feel built).

- **D15 — the companion feat economy: a canonical pool, a prerequisite gate, dated slots, and taxed
  children behind a curated allowlist** *(same grill)*. `Backend/utils/class_func/companion_feats.py`
  owns it. The 27-name bag stays the legality list — it *is* the PF1e animal-companion list — but is
  canonicalised against `data/feats.csv` (the fake `armor proficiency (light, medium, and heavy)`
  became the three real feats, 29 names). Picks are prerequisite-gated against the creature's own
  merged abilities and BAB, one at a time so a chain can build itself (Dodge → Mobility → Spring
  Attack). The chassis table's `feats` column **dates every slot** (effective levels 1, 2, 5, 8, 10,
  13, …), which is both the label number and the tax cadence anchor; labels read
  `Animal Companion 5: Weapon Focus`, parallel to the PC's `Fighter 1: Weapon Focus`, and ride a
  **`feat_labels`** list beside `feats` — `feats` stays a bare list of names because the frozen
  `animal_companion` alias reads the same object (D9).
  **Feat tax runs**, through `feat_tax_func` on a four-attribute adapter. Its children pass two
  gates: `legal_for_companion`, which fails CLOSED on any prerequisite it cannot read (that is what
  drops `greater weapon focus` and `martial focus` without a hand-written blocklist), and the curated
  **`tax_children`** allowlist in `animal_companion.json`. The allowlist is not optional: the 29 pool
  feats open **128** distinct chain children, and a prerequisite reader cannot refuse Drunken
  Brawler, Wand Dancer or Sword and Pistol, because their prerequisites are genuinely met.
  *Rejected:* the whole feat DB behind a derived predicate (PF1e legality for animals is a curated
  list precisely because it cannot be derived); tax confined to the pool (only `endurance → diehard`
  would ever fire); labelling by HD or by species.

- **D16 — parity sections, an animal flaw catalogue, and the per-creature RNG** *(same grill)*. A
  companion Actor gets the PC's furniture: a `Class Features (Animal Companion)` band with its
  species abilities promoted **out of the description into real items**, the `Variable Modifiers` /
  `Natural AC` / `Death HP` tracker groups at the PC's own `CF_SORTS` values, a Traits-tab `Flaws`
  divider, a Feats-tab Background band, and **all eleven** `custom_buffs.json` buffs verbatim under
  the same `addCustomBuffs` gate. `Natural AC` is unconditional here, unlike the PC's
  `characterHasNaturalArmor()` gate — every bonded creature has natural armour. **Resource Pools is
  not included**: an animal has no Hero Points.
  Flaws come from a new **`Backend/json/flaws/animal_flaw_effects.json`** (12 minor / 10 major) and
  follow the PC ladder exactly — the creature's own `randomize_flaw_amount()` roll, 1st minor / 2nd
  major / 80-20 thereafter, and the diminishing flaw-feat grant (0→0, 1→1, 2→2, 3→2, 4→3) behind
  `misc_homebrew_enabled`, drawn from the same gated pool.
  **All companion randomness now draws from the per-creature `random.Random`**, salted per consumer,
  which extends `companion_stats`' skill-allocation ruling to the much larger draw the feat economy
  makes. That was a one-time re-baseline of the `companion` golden — and only that golden, because
  the other six roll no bonded creature and so never paid the old cost.
  *Rejected:* a filtered buff subset (the user's call — `Combat Expertise` is unusable at Int 1–2 but
  arrives inactive, so it is a toggle to leave alone rather than a number on the sheet); reusing the
  PC's 44 flaws behind an `animal_ok` tag (about eight survive, so companions would repeat
  constantly); flaws without flaw feats; keeping the global RNG stream.
  Scope: `companion` and `mount` only. Familiars use their master's feats (RAW) and eidolons are
  evolution-driven; neither resolves to an entry today.

### Grantors and effective level (D6)

The grantor set is a **data file**, `Backend/json/companion_grantors.json`, not a code table; the
resolver reuses `generic_func.py::class_entry_for`, whose docstring already states the
scaled-by-that-class's-own-level rule that every grantor needs. Columns:

`grantor` (class name or talent) · `creature type` (`companion` / `mount` / `familiar` / `eidolon`) ·
`level gained` · `effective level expression` · `conditional` (what else must be true) ·
`species pool` (which `animal_choices.json` buckets, or a familiar/eidolon list).

Rules the resolver enforces:

- **Effective level is the grantor's own class level**, transformed by that row's expression — never
  the character level and never the total of all classes.
- **Multiple sources stack**, and the stacked total is **capped at character level** (PF1e's general
  rule; it is what keeps a druid 5 / ranger 8 from out-levelling itself).
- **Below `level gained`, nothing is emitted.** A paladin 3 has no mount; it does not get a level-1
  one.
- A grantor whose class feature is a **choice** only fires when the choice came up — the wizard and
  Arcane-bloodline sorcerer arcane bond (familiar *vs* bonded object), the ranger's Hunter's Bond
  (companion *vs* bond with companions), and the druid's existing domain-vs-companion flip. These are
  coin flips at generation time, recorded on the entry so the sheet can explain the absence.
- **Archetypes** that trade a companion away or swap its species list are honoured
  (`Backend/json/archetypes.json` is already loaded); **Boon Companion** raises effective level once
  the feat exists.

**The fifth grantor is not a class.** The Spheres of Might *Beastmastery* talent
(`Backend/json/class_data/spheres/spheres_of_might.json`, the `animal companion` talent) grants a
full druid companion at `max(BAB, Handle Animal ranks, Ride ranks) − 3`, minimum 1 **by the talent's
own text** — that per-source floor is RAW and is not the clamp D6 rejects, which is about grantors
whose threshold was never met. It stacks and is capped like every other source.

**Amended 2026-08-01 — three grantor rows from the grill do not survive RAW.** The chart's list read
"14 of 38 rollable base classes"; the verified figure is **13 touched, 10 at full stat block**.

- **`shifter` is not a grantor.** Its progression (shifter aspect, shifter claws, wild empathy,
  defensive instinct, wild shape, shifter's fury, chimeric aspect…) contains no animal companion.
  Verified on Archive of Nethys.
- **`antipaladin` is a different subsystem.** Fiendish Boon's servant is a permanent
  `summon monster III`, scaling one spell level every two class levels to IX at 17th, with the
  advanced template at 11th — **not** a druid's animal companion, so it does not ride the chassis.
  Moved to *Deferred*.
- **`sorcerer` is conditional on bloodline.** Arcane Bond arrives from the **Arcane** bloodline
  ("as a wizard equal to your sorcerer level"); the Ancient variant grants a bonded **object** only.
  The resolver must read the rolled bloodline, not the class name.

**Settled, closing the carry-in from ticket 04:** the paladin's bonded mount uses **the paladin's
level** as effective druid level — *not* level − 3 — and arrives at **5th**. Cavalier and samurai
both use their own class level at **1st**.

### The snapshot (ticket 03)

A companion is a **static snapshot at the master's level**, never a levelling tracker — the same
posture the generator takes everywhere else. What the snapshot resolves:

- **Which level drives the lookup:** the resolved effective level from D6, not the raw druid level
  the code uses today.
- **The advancement merge**, which nothing does today. Each species carries exactly one
  `"<N>th-level advancement"` block (180 of 182 species; triggers at level 4, 7 or 9). Merge when
  effective level ≥ the trigger, then **per field**: `size`, `attack` and `speed` **replace**; `ac`
  (always `"+N natural armor"`) and ability scores **add**; `special qualities`, `special attacks`
  and one-off keys (`sudden charge (ex)`, `bonus feat`, `climb`, `fly`, …) **append**.
- **House rules apply to the companion the way they apply to the PC** — maximised HP and the
  skill-rank floor are class-name-agnostic in `hp_rolls.py` / `skill_ranks.py` and should stay that
  way. The **feat economy does not**: a companion's feat count is the chassis row's `feats` value,
  not the PC formula.
- **Degenerate cases:** effective level 0 or below the threshold → no entry at all (D6); a master who
  multiclassed out keeps the companion at the granting class's level, since that is what the
  expression reads.

**The data defect this pass must repair (D5).** `animal_choices.json` cannot be merged as written:

- **Sign loss.** Of 120 bare-int `dex` values in advancement blocks, **109 sit on a size increase**,
  where PF1e mandates the fixed Str +8 / Dex −2 / Con +4 / natural armor +2 package. Sixteen rows in
  the identical situation record `-2` correctly, which is what proves the rest lost their minus sign
  (`+8` and `+4` survived as strings; `-2` did not survive as an int). Merging as written inflates
  every advanced companion by **+4 Dex → +2 AC, +2 Ref, +2 initiative**.
- **Key drift.** `ability_scores` (×14) and `special_attacks` (×8) shadow the spaced spellings, so a
  lookup on `"ability scores"` silently misses those species.
- **Field bleed.** Three ability-score slots hold `'medium'`, `'40 ft. '`, `'bite (1d6)'`.

### Rendering (D1–D3)

`pf-content` ships Actor compendia — `pf-companions` (2.8 MB), `pf-familiars` (2.4 MB, core familiars
plus ~90 named improved familiars) and `pf-eidolon-forms` (348 KB, all 7 base forms in both sizes).
Ticket 04 ruled "compendium-first lost" while answering **data sourcing**, and that stands; this is
the separate question of a **rendering** source, and there the packs win — cloning a finished Actor
is what makes familiars cheap enough for v1, leaving only a ~20-row master-bonus table to author.
`pf1-statblock-converter` is installed but its parser is minified and UI-driven
(`SBC.parseInput({characterData, input.text})`) — fallback only, not the plan.

The payload lands whole in `localStorage` via `deliver-data.js` with **no key filtering**, so a new
top-level key needs no plumbing on the module side.

### Export (`/update_character_data`)

`bonded_creatures`, a list beside the existing class blocks, one entry per creature:

`type` · `grantor` · `effective_level` (post-stack, post-cap) · `species` · `name` · `sex` ·
`gear` · `gear_source` (the last four are D9; `name`/`sex` are `None` and `gear`/`gear_source` are
absent entirely on an entry with no species) · `kind`
(`normal`/`plant`/`vermin`, companions only) · `species_stats` (**raw**, see below) ·
`chassis` (the level row from `animal_companion.json`) · `feats` · `stats` (the computed block: hp,
ac, saves, bab, cmb/cmd, abilities, size, speed, attacks, skills) · `master_abilities` (familiars
only) · `description` (the eidolon's base form and text) · `pf_content` (the compendium Actor name to
clone, or `null` → D3 fallback).

**Amended 2026-08-03 (#31):** this section originally called for `species_stats` to be
advancement-**merged** on the entry. It cannot be. That key is one of the five the `animal_companion`
alias is frozen at (D9) and both read the same object, so swapping raw for merged would silently
change what the sheet repo's #15 consumer renders. `species_stats` therefore stays **raw** and the
merge's output lands in `stats`, which is lossless: every derived number has a named field, and
`stats.other` carries the one-off merged keys nothing else enumerates (`climb`, `fly`, `bonus feat`,
`cmd trip`, `sudden charge (ex)`, …). `stats.merge_notes` records which advancement blocks fired.

`animal_companion` **remains** as a deprecated alias carrying the old dict shape for the first
`type == "companion"` entry, so the sheet repo's issue #15 consumer does not break. It is **frozen**
at those five keys (D9): the new identity and gear fields never appear on it, because a deprecated
key that is never worse than its replacement is never migrated away from.

**"Done" per type:** full stat block for **companion, mount and familiar**; **named base form plus
descriptive text** for the eidolon.

### Build slices (dependency order — next session, not the spec session)

1. `Backend/scripts/attic/repair_animal_choices.py` — negate bare-int `dex` on size-up rows, normalise the
   `ability_scores` / `special_attacks` key variants, hand-fix the three bled values.
2. `Backend/scripts/gates/validate_companion_data.py` — assert every size-up row matches the PF1e package
   and that no bare-int ability value survives.
3. `Backend/scripts/dump_pf_content_actors.mjs` → `Backend/json/pf_content_companions.json`, plus
   `Backend/scripts/gates/validate_companion_names.py` gating species names against it (D3).
4. `Backend/json/companion_grantors.json` + the resolver in `animal_companions.py`.
5. Advancement merge + stat-block math; fix `animal_feats` to read the chassis row's `feats` count.
6. Payload: emit `bonded_creatures`, keep `animal_companion` as the alias.
7. Foundry module: loop `Actor.create` in `createCharacter.js`, clone from `pf-content`, patch the
   numbers, degrade on a miss.
8. Web sheet: consume `bonded_creatures`.
9. Extend `Backend/scripts/tests/test_house_invariants.py` with companion invariants.
10. Canonicalise the feat pool + author `companion_feat_changes.json` +
    `Backend/scripts/gates/validate_companion_feats.py` (D14/D15).
11. `class_func/companion_feats.py` — gated selection, dated slots, `feat_labels`, feat tax behind
    the `tax_children` allowlist, and the animal flaw roll (D15/D16).
12. `companion_stats.apply_modifiers` — fold the feats and flaws, emit `applied_changes` /
    `context_notes`, extend the invariants (D14).
13. Module: `scripts/companion-sections.js` — dividers, labelled feats, promoted class features,
    tracker groups, Flaws, the eleven buffs (D16).

**Deferred (not built in v1):** **eidolon evolutions** — 7 base forms × 2 sizes and ~76 evolutions
(≈28 @1 EP, 27 @2, 11 @3, 10 @4) scraped from d20pfsrd's prose headings, with
`pf-eidolon-evolutions` (~36 entries) as a completeness cross-check only; the summoner's
evolution-points-per-level table is still unverified. Ticket 07 owns the point-budget-vs-count
question — whether an evolution pool fits `generic_class_option_chooser` or wants the Spheres
funding pattern · the **antipaladin's fiendish servant** (a `summon monster` subsystem, see the
amendment above) · **improved-familiar prerequisites** (alignment / caster-level gates, on a separate
PRD page, unverified) · the five mount species missing from `animal_choices.json` (giant seahorse,
giant tortoise, axebeak, reindeer, giant weasel — absent from `pf-companions` too, so they want a
small scrape) · **region-flavoured companion pools**, the standing TODO in `animal_companions.py` ·
companion **token art / portraits** · whether companions should carry buffs/conditionals the way
weapons do (§1/§4 pattern), only answerable once the rendering model has run · live levelling or
sync of a companion as the PC advances · the **psicrystal** (§9) · **companion gear** — barding, a
mount's tack, and the body-slot model an animal needs (no hands, barding not armour); D9 fixes the
signature (`gear`, funded from `character.gold`) so this is a ticket with a shape, not a rediscovery.

---

## 9. Psionics (Dreamscarred Press / Library of Metzofitz)
**Status: SPEC LOCKED (2026-07-31) — implementation in progress on `feat/psionics-v1`.**
Twelve base classes: `aegis, cryptic, dread, highlord, marksman, psion, psychic warrior, soulknife,
tactician, vitalist, voyager, wilder`. Charted in `tickets: feature/psionics`; this section is that
map's destination. §1 (Path of War) is the governing precedent throughout — a 3pp system whose
mechanics are scraped into `Backend/json/` while a third-party Foundry module renders the result.

**Sources and the split (locked):**
- The **[Library of Metzofitz wiki](https://libraryofmetzofitz.fandom.com/wiki/Psionic_Classes) is
  the source of truth for mechanics** — same authority as `data/Metzofitz_Feats.csv`. Scraped by
  `Backend/scripts/build/scrape_psionics.py` (via `api.php`; plain `/wiki/` hits Cloudflare) into
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
- **Class items:** `Backend/scripts/build/build_every_class.mjs` harvests the twelve `pf1-psionics` class
  items into `every_class.json` (as PoW classes were harvested from pf1-pow) and **patches
  `system.bab` / `hd` / `skillsPerLevel` from `class_data.json`** during harvest. Keeping the
  module's own item
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
classes are ~12 of 55 pool entries.

**Amended during the build (was: "manifesting ability gets its own map in `data.py`").** It is a
`manifesting_stat` key in each class's **`class_data.json`** entry, beside `main_stat`. Ticket 04
settled this question against `data.caster_mod` — power points are not spells-per-day — but it never
weighed `class_data.json`, and that is the better owner: the entry already exists and already carries
the class's other key ability, so one row owns both facts where a separate map would be a second
place to drift. It has to be its own key rather than a reuse of `main_stat` because the two questions
differ — a psychic warrior manifests off Wisdom but plays off Strength, and a soulknife manifests off
nothing at all. Read by `utils/class_func/psionics.py::manifesting_stat`.

**Twelve is the target (tickets 04/08).** A class may be held out of the pool, but **every holdback
is recorded here with the subsystem it waits on**. No class ships hollow. Nine of the twelve carry a
choice-bearing subsystem — aegis customizations, cryptic insights, vitalist methods, psychic warrior
paths, marksman styles, tactician strategies, dread terrors, highlord decrees,
soulknife blade skills — and **all nine ride the existing
`generic_func.py::generic_class_option_chooser`**, the same one that drives bloodlines, orders,
mysteries and weapon training. No new chooser module. The one genuine exception is the **soulknife's
mind blade**, which is a weapon rather than a list: it becomes a synthesized weapon whose enhancement
bonus comes from the class table, reusing `enhancement_effects_dict` and special-cased against
`armor_and_weapon_chooser.py`.

*Amended during the build:* this list and ticket 08's table both counted the **voyager** among the
choice-bearing classes, on a row reading "voyager | path skills". That was wrong — "Path Skill" is a
*psychic warrior* feature, and the voyager has no option list at all. Its choice-bearing feature is
**Voyager Knowledge**, which grants bonus feats from a fixed list; that is feat machinery, not
`generic_class_option_chooser`, and it is **not built** (see Deferred). The count of nine was right
by accident — the list under it named ten. `psionic_class_options.json` ships the nine that survive.

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
`Backend/scripts/build/reconcile_psionics_names.py` reads the module's LevelDB packs and emits
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

**Deferred (not built):** web-sheet rendering of manifesters · **Voyager Knowledge** bonus feats,
the voyager's only choice-bearing feature (see the amendment above; it is feat machinery, not a
`generic_class_option_chooser` list, so the voyager currently generates with no picks of its own) ·
**psionic races** — the ten scraped
*Psionics Unleashed* races stay data-only; ticket 11 is re-scoped as the **custom-race route** ticket
covering Loxo/Kalyptran/Dolistani too, because `PlayableRaces.json` is walked *positionally* by
`race_func.py::race_traits_chooser` and psionic Duergar collides with core Duergar · the six v2
classes (Genesis, Skipper, Thug, Warpmind, psionic Zealot — note `zealot` is taken by the PoW class —
Soulknife (High Psionics)) and the Gifted NPC class · the **psicrystal**, structurally a companion
(see `tickets: feature/companions`) · turning on the **311 psionic feats already in
`data/Metzofitz_Feats.csv`** (gated by `_METZ_TYPES` in `feats.py`; the data is there, the eligibility
rules are not decided) · power **conditionals** on the main weapon, mirroring §4/§7 · psionic items
(cognizance crystals, dorjes, power stones) in the gear chooser · multiclass manifester-level
stacking · reporting upstream's incomplete §15 and placeholder class fields to SoxMax and the wiki
editors.

## 10. Class pool — Occult Adventures
**Status: BUILT (2026-08-03).** All six Occult Adventures classes — `occultist`, `kineticist`,
`medium`, `mesmerist`, `psychic`, `spiritualist` — are in the random pool. `data.occult_classes` is
empty; it stays as the one-line lever for pulling a class back out. Charted in
`tickets: feature/class-pool`; this section is that map's destination. §9 (Psionics) is the governing
precedent — a whole class family entering the pool with **no new chooser module**.

**Why this was a completion job, not a cold start.** `class_data.json` already carried all six
chassis (main stat, BAB, hit die, wealth, skill ranks, feature prose, favoured-class races), and
`data.py` already carried their casting stat and good saves. `data/spells.csv` already had a spell
column per caster. What did not exist anywhere was the **selectable option pools**.

**Sources (ticket 04) — compendium-first, and it wins here.**
- The option pools are **harvested from the installed Foundry compendia** by
  `Backend/scripts/build/build_occult_class_data.py` into `Backend/json/class_data/<class>.json`, in the
  `{dataset: {name: description}}` shape `generic_class_option_chooser` already consumes. **449
  options across the six.** Both packs are required: `pf1.class-abilities` carries most of it, but
  the occultist's eight implement schools and the spiritualist's phantom emotional foci exist only
  in `pf-content.pf-class-abilities`.
- Two pack fields make it a *source* rather than just a renderer: `system.associations.classes` (the
  class tag — an exact list, not a name match) and the class Item's `system.links.classAssociations`
  (the auto-granted features, whose complement is the selectable pool).
- **Spell progressions are read out of pf1 itself**, not typed from the book:
  `config.casterProgression` in `pf1.js.map`'s `sourcesContent`. Cross-check that this is right —
  the derived occultist row reproduces the repo's existing `bard` spells-known row exactly, and the
  derived psychic row reproduces `sorcerer` in *both* files.
- **No new OGL entry.** Occult Adventures is first-party Paizo read out of the system's own pack;
  §9's Dreamscarred Press machinery does not extend here.

**Per-class disposition (ticket 03).** All six roll and render. Two degrade, in the sense §8 fixed
for the eidolon — the class stays rollable and its unmodelled feature is named and described rather
than suppressing the class:
| class | picks | notes |
|---|---|---|
| occultist | implements (8 schools), focus powers | full |
| mesmerist | mesmerist tricks, bold stare | full |
| psychic | discipline, phrenic amplifications | full |
| spiritualist | phantom emotional focus | full; the phantom itself is **not** a bonded creature — see below |
| kineticist | elemental focus, wild talents, infusions | **degraded: burn** |
| medium | channeled spirit | **degraded: the spirit is frozen** |

- **Kineticist — burn is not modelled.** It is an HP-priced resource with no analogue in the
  generator, and `caster_mod`'s own comment already recorded that the caster map cannot express a
  Constitution-priced class. Its wild talents and infusions *are* picked; burn is described, never
  tracked. The class is also a **non-caster in all four tables** (`casting level: none`, absent from
  `base_classes`, `caster_mod`, and both spell tables) — `validate_occult_data.py` checks all four,
  because being wrong in one of them silently hands it a spellbook.
- **Medium — one séance, frozen.** The spirit is a *daily* choice and the generator emits a static
  snapshot. Rolling one spirit and keeping it is a **house ruling**, recorded here deliberately
  rather than presented as a rendering decision. Only the six base legends are rollable; the pack's
  25 legendary and 9 outsider spirits are held out of v1 rather than diluting the roll toward a
  named NPC.
- **The spiritualist's phantom gets no row in `companion_grantors.json`.** §8's grantor table is for
  creatures with a chassis and a stat block; the phantom's emotional focus is a choice from a list,
  which is the shape the existing chooser already serves. Revisit if the phantom ever needs a sheet
  of its own.

**Two data corrections found on the way in**, both from the pack disagreeing with `class_data.json`:
the kineticist's `casting level` was `mid` (now `none`) and the medium's was `mid` (now `low`).
`spells.py` branches on that field, so `mid` would have handed the kineticist a spellbook and the
medium two spell levels it never gets. `build_occult_class_data.py` now reconciles the field from
the pack rather than leaving it hand-maintained.

**Export shape.** No new payload key. Each class's picks land in `class features` under their own
bucket — `implements`, `focus_powers`, `elemental_focus`, `wild_talents`, `infusions`,
`medium_spirit`, `mesmerist_tricks`, `bold_stare`, `psychic_discipline`,
`phrenic_amplifications`, `emotional_focus` — and all eleven are registered in the FoundryVTT
module's `CLASS_FEATURE_BUCKETS`. The bucket is `medium_spirit`, not `spirit`, because the shaman
already owns `spirits`. Registration is not cosmetic: for the kineticist those buckets are the whole
sheet.

**Gates.** `Backend/scripts/gates/validate_occult_data.py` (validator 15) owns the data — pool shape, no
double-shelving, every `data.amount` schedule naming a real dataset, the caster/non-caster split, and
the **cross-source check** that each schedule produces the maximum pick count the class's own feature
prose promises (seven implements by 18th, eleven tricks by 20th). `test_house_invariants.py` owns the
output — pick counts per class level, every pick present in its pool, no pick without rules text, the
spellbook split — with a branch-coverage guard that fails if the sweep never rolled an occult class,
never exercised a multi-pick bucket, or never hit both sides of the caster split.

**Stalker and zealot stay pending (ticket 05).** `pf1-pow` 1.6.4 ships no class Item for either —
its `classes` pack holds Harbinger, Medic, Mystic, Warder and Warlord. They remain generatable but
unrenderable, so they stay in `pow_classes_pending_foundry`. Empty that list and uncomment the
module's `button.js` / `html_dialog.js` dropdown entries once a `pf1-pow` release adds them.

**Open rules question — the medium's spell table.** pf1's `low` spontaneous progression is shaped for
the bloodrager, whose first 1st-level spell lands at class level 4, and pf1 applies it to the medium
unchanged. RAW has the medium casting from 1st. We take pf1's numbers so the payload and the Foundry
sheet agree rather than disagreeing in opposite directions; if it is ruled a bug, fix `CASTERS` in
`build_occult_class_data.py` and re-run.

**Web-sheet rendering — labels, no tab.** The eleven buckets already rendered on the standalone
sheet through `classChoiceLabels`'s unknown-key fallback; they are now registered in
`CLASS_CHOICE_BUCKETS` (`scripts/tabs/features.js`) with the module's labels verbatim, so the two
sheets name the same pick the same way. **Rejected: a dedicated Occult tab** beside `path-of-war.js`
and `psionics.js` — those two earned a tab by owning a tracker the Features tab cannot show (power
points, readied maneuvers). Six occult engines share nothing with each other and need no such
tracker; the kineticist's burn would be the one candidate, and it is unmodelled by decision above.

**Deferred (not built):** occult **archetypes** (the existing archetype pipeline is untested against
these six, though `Backend/json/archetypes.json` already carries 8–24 entries each) · **Metzofitz
occult variants**, unread · kineticist **burn** as a tracked resource · the medium's **legendary and
outsider spirits** · **buffs/conditionals** for occult picks, mirroring §4/§7 · a live Foundry import
check of all six.

## 11. Class choices — ⚙️ BACKEND BUILT (2026-08-07), rendering outstanding
**Status: the backend half is built, gated, and the seven known gaps are closed; the renderer half is not.** Every rollable class
either makes its class-specific choices — rogue talents, rage powers, aegis customizations,
bloodlines, orders and 47 other buckets — the right number of them at the right class levels, or
carries a written verdict saying why it makes none. Charted in `tickets: feature/class-choices`;
this section is that map's destination. Tickets 01, 02, 03 and 05 are resolved; **04 (what
"reaches the sheet" means per bucket) is open and owns everything below the line.**

**The schedules are not in this document.** Per the docs doctrine, prose must not restate a tuning
constant — it names the symbol that owns it. That symbol is
**`Backend/json/class_choice_schedule.json`**: one row for every one of the 68 rollable classes,
each bucket declaring either a compact `{start, every}` rule or an explicit `{levels: [...]}`, with
`generic_func.levels_for()` the generator's only reader. See `docs/CODEBASE_MAP.md` for its shape.

**What the table replaced: five pick-count conventions, not three.** Ticket 01 found and migrated
three. Ticket 02's sweep found two more — `data.formulas` + `eval()` behind `simple_list_chooser`,
and an inline `floor((level-1)/4)` in `choose_gun_func`. Neither was reachable from `data.amount`
or from the three known call sites, and **only generating a character for all 68 classes found
them**. That is the section's governing lesson: this subsystem's failures are invisible to reading.

**Every row is a verdict.** 41 rows carry buckets; the other 27 are empty and say why —
`none-by-design` (the four NPC classes, and the swashbuckler, whose deeds are granted by level in
RAW so *no chooser is correct*), `other-subsystem` (the cleric's and druid's domains, the wizard's
school, the five Path of War classes, the psionic power-pickers — their notes name the owning
symbol), `other-effort` (the summoner's eidolon, §8's), `aliased` (the unchained variants, which
pick through their base class's row), and `gap`.

**The seven gaps are BUILT (2026-08-07).** Every class ticket 02 found generating an empty
class-features dict now makes its choice:

| Class | Bucket(s) | Schedule |
| --- | --- | --- |
| bard | `versatile_performances`, `martial_performance`, `expanded_versatility` | 2nd, then every 4 — each bucket on its own row |
| hunter | `animal_focus` | two at 1st (herself + companion), frozen |
| shifter | `shifter_aspects` | 1st, 9th, 14th, 20th |
| psion | `psion_discipline` | 1st |
| vampire hunter | `vampiric_foci` | 1st, 8th, 16th |
| omdura | `invocation` | 1st, frozen |
| witch | `patron` | 1st — **and its spells join her list**, level-gated |

The witch's patron is the one worth remembering: it **hid inside a non-empty row**. The witch
already had a `hexes` row, so a sweep that only inspected empty rows would have missed it — which
is why ticket 02 swept classes that already had buckets.

**Archetype prerequisites are honoured; archetype SWAPS still are not.** 144 of the hunter's
aspects and 3 of the shifter's are gated on an archetype named in the option's own `prerequisites`,
and `no_prereq_loop` could already check that — it just never had the archetype. Rolled archetype
names are seeded into `character.chooseable` by `chooseable_list_archetypes`, minus 18 that are
also the name of a selectable option (`brawler` is both an archetype and a rage power, and a prereq
string cannot say which it meant). An archetype that trades a bucket *away* still leaves it in
place; that non-guarantee is unchanged.

**Three schedules are `unverified` and owed a Sieg's Guide check:** the shifter's (its own text
implies five aspects by 20th where the levels it names yield four), and the bard's
`martial_performance` and `expanded_versatility`. `martial_performance` is **undocumented house
content** — it maps Perform categories to weapon groups, which is not RAW and is written down
nowhere. It was kept and made visible rather than deleted.

**Per-use choices are rolled once and frozen.** A feature re-chosen at every use or every day has
no home in a static snapshot. The medium's daily seance (§10) was the one-off precedent; it is now
the general rule and governs the hunter, shifter and omdura gaps above. *Rejected:* emitting the
whole pool as a reference bucket — a new bucket kind both renderers would have to learn.

**What the generator guarantees about legality — narrowly, on purpose.** It enforces prerequisites
the string engine can evaluate (option names, class levels, ability/BAB/caster thresholds — 93.9%
of prerequisite parts), no duplicates in a bucket, and no cross-bucket bleed. It **knowingly does
not** enforce the other 6.1%: disjunctive prose, `"any two X"` counting, mutual exclusion,
once-only, or buckets an archetype trades away. Archetype feature swaps remain modelled **for the
companion bond only** — the standing ruling extends here unchanged, and is stated as an explicit
non-guarantee rather than left unsaid. Under-delivery is legal exactly when the pool is provably
dry: `min(scheduled, |pool|, max_num)`.

**`character.chooseable` stays shared across classes**, on measured grounds: the only pools whose
prerequisites name a foreign class are ninja→rogue, slayer→rogue and skald→barbarian — all RAW
interop — so a rage power cannot be unlocked by a rogue level. The gate fails if a fourth appears.

**What keeps it true.** Two layers that share no code, both run by CI:
`Backend/scripts/gates/validate_class_choices.py` (config: the table vs the roster, the call sites,
the datasets) and `check_class_choices` in `Backend/scripts/tests/test_house_invariants.py`
(behaviour: characters vs the table). Neither imports `levels_for` — a table cannot be its own
witness, which the build demonstrated: perturbing the table and re-running the behaviour check
*passes*, because the generator reads the same file.

---

**Open, and owned by ticket 04 (rendering).** Four defects are known, documented per row, and
deliberately unfixed here because each moves a shipped payload:

- **Six call sites omit `dict_name=`**, so sorcerer and bloodrager bloodlines and cavalier and
  samurai orders land in the default bucket `Talents`, shared with warpriest blessings and
  inquisitor inquisitions. A warpriest/inquisitor multiclass merges them.
- **`manuevers` is a typo** — spelled that way in `data.py`, at the call site, and on both sheets.
- **The oracle's mystery shares the `mysteries` bucket with its revelations**, so neither count can
  be read alone.
- **Three buckets hold a list, not a `{choice: description}` dict** (ranger favoured
  terrains/enemies, brawler maneuvers), and mercies, cruelties and ki powers carry no level stamp
  at all.

The behaviour gate skips seven class/bucket pairs for these reasons, prints the skip count every
run, and **fails if a skip is deleted before its cause is**.

## 12. Class roster and the selector — ✅ BUILT (2026-08-04)
**Status: BUILT.** 68 rollable classes, in five families the FoundryVTT dropdown groups by. This
section owns *who is in the pool and how you pick them*; §10 owned the occult six specifically, and
`tickets: feature/class-choices` (still parked) owns whether everyone in the pool picks correctly.

> **§11 is reserved**, deliberately, for *Class choices* —
> [that map](https://github.com/The-Data-is-a-lie/tickets/blob/main/tks/pathfinder-char-creator/feature/class-choices/map.md) names §11 as its destination and is only parked, not
> abandoned. Numbering this one 12 keeps that promise rather than quietly taking its slot.
>
> **That map's "class list is final at 61" gate needs re-stamping**: this section makes it 68, and
> its audit must cover the seven new arrivals — four of which (aristocrat, commoner, expert,
> warrior) make no class-specific choices *by design*, which the audit must read as intended rather
> than as the coverage gap it looks identical to.

**The bug this started from.** §10 put the six Occult Adventures classes in the random pool on
2026-08-03 and the module could already render them — but the dropdown never got them, so for a day
the only way to roll an occultist was to pick Random. The roster existed **three times by hand**:
`button.js`'s dropdown, a dead byte-identical copy in `html_dialog.js`, and `modify-abilities.js`'s
`collectItems()` boundary list. The occult classes reached two of the three.

**One roster, one gate.** The module now keeps `scripts/class-roster.js` — `CLASS_GROUPS` (display
order, grouped) and `CLASS_ITEM_ORDER` (every_class.json order). Two exports because the two orders
are different contracts: the first drives the dropdown, the second is what `collectItems()` slices
on, where a name out of place makes one class swallow the next one's features.
`Backend/scripts/gates/validate_class_roster.py` is the gate; `html_dialog.js` is deleted.

**Groups are derived, not listed twice.** `data.CLASS_GROUPS` names five families; `base` carries no
roster of its own and is *the remainder* of `class_data.json`, so a new Paizo class stays a one-key
change. `base_classes` could not be reused as the category — `spells.py` overloads it as the
spellcasting gate, so five occult classes are in it and the kineticist is not. Hence the separate
`occult_class` roster beside the (empty, and differently-purposed) `occult_classes` exclusion lever.

**Random within a family.** Each `<optgroup>` opens with `Random <group>`, sending `random-<token>`.
`util.py::_group_pool` narrows the pool to that family; BAB and caster-level filters still compose
on top, and an empty group falls through to the whole pool rather than failing — the behaviour every
unmatched class string has always had here.

**The seven new classes.**
| class | source pack | notes |
|---|---|---|
| adept | `pf1.classes` | the only NPC caster; `spells.csv` already had an `adept` column |
| aristocrat, commoner, expert, warrior | `pf1.classes` | no features by design |
| omdura | `pf-content.pf-collab-content` | 12 features |
| vampire hunter | `pf-content.pf-collab-content` | 15 features |

- **All seven roll** (user decision, 2026-08-04). *Rejected:* selector-only NPC classes. NPC classes
  are ~7% of random draws; the lever if that is wrong is `data.classes_pending_foundry`.
- **Chassis is read from the pack, never typed.** `build_npc_class_data.py` and
  `build_collab_class_data.py` take hit die, BAB, skill ranks, saves, class skills, proficiencies
  and feature prose off the class Items, and both refuse to write if `data.good_saves` disagrees.
- **The census that nearly held two classes out.** `pf1.classes` has 49 class Items and carries
  neither the omdura nor the vampire hunter; the first sweep read three likely-sounding packs and
  concluded both were unrenderable. Sweeping **every installed pack** found both in
  `pf-collab-content`, with full feature chains. Grade a renderability census against every pack.
- **The adept's spell table is RAW's, not pf1's.** pf1 tags it `med`, the cleric's six-level
  progression, but `spells.csv`'s adept column runs 1st–5th (62 spells, plus 10 orisons).
  `casting level` stays `mid` so the two sheets agree on the tier, and the 6th-level row is entirely
  `null` — the data enforces the cap, so no branch in `spells.py` had to learn about the adept. That
  row is load-bearing: `spells_per_day_attr` indexes the JSON by key over
  `range(0, highest_spell_known + 1)`, so a 16th-level adept `KeyError`s without it.

**The omdura and the vampire hunter cast.** RAW gives the omdura spontaneous Charisma casting off
the cleric/inquisitor lists to 6th, and the vampire hunter Wisdom casting off the inquisitor list
from 4th. Their `pf-collab-content` class Items carry **no casting block**, so
`build_collab_class_data.CASTING_OVERRIDE` asserts the tier — `mid` and `low` — and
`check_casting_overrides()` fails the build the moment upstream ships a real one.

- **Neither needed a new `spells.csv` column,** which is what an earlier reading of this had wrong.
  `spells.py::class_for_spells_attr` already aliases warpriest and oracle to the cleric column and
  witch/arcanist to the wizard one; the omdura joins the first and the vampire hunter reads
  `inquisitor`. Their `spells_per_day.json` rows are the standard six- and four-level tables, copied
  from `inquisitor` and `ranger` — nothing was typed from a book.
- **Nor does the Foundry sheet derive its spellbook from the class Item,** the other premise that
  didn't hold. `configureSpellbook` writes `inUse`, `class`, `casterType`, `ability` and `kind`
  straight off the payload, which is how `psion` and `aegis` get books while sitting at
  `casting level: none`. (The §10 medium was never precedent for shipping a non-caster either — the
  medium is `casting level: low` and casts; §10 shrank its table.)
- **Remaining fidelity gap, narrow:** RAW builds the omdura's list as the **union** of the cleric's
  and the inquisitor's, and nobody has written that union down. It reads the **cleric** column — the
  superset at every level a `mid` caster reaches, and the omdura is a cleric alternate class.
  *Rejected:* deriving a real union column in `spells.csv`.

**Accepted divergence — the backend's spell table stops at the payload.** `configureSpellbook`
sends pf1 only `casterType`, so pf1 fills slots from its own tables and ignores
`spells_per_day_list`. For 29 of the 30 declared casters the two agree. The adept is the exception:
at 16th+ the Foundry sheet offers a 6th-level slot that no adept spell can fill, and the web sheet
correctly withholds it.

**Ruled: leave it** (user decision, 2026-08-04). *Rejected:* the module change that would fix it —
`autoSpellLevels = false` plus writing `spellN.max` from the payload. It makes the generator
authoritative for **every** caster's slots at once, thirty classes of arithmetic pf1 already does
right, to correct one empty row on a class that will rarely be rolled; and it would surface whatever
other backend/pf1 table drift exists as a side effect of a cosmetic fix.

If it is ever revisited, the non-obvious part: write **N = 1..9 only**. Level 0 must stay on auto —
the `"0"` row is all zeros for 27 of 28 classes (the magus alone carries real counts, and nothing
reads them) and means *orisons are at-will, not tracked*, not *no orisons*. Writing it verbatim
would strip cantrips from every Foundry caster in the game.

**Gates.** `validate_class_roster.py` (validator 17) checks five things: the roster is exactly the
rollable pool, every class is in exactly one group, `CLASS_ITEM_ORDER` matches `every_class.json`,
every rostered class has a class Item, and the group tokens match the backend's. An absent module is
a SKIP, not a failure — the module lives outside this repo. `test_house_invariants.py` sweeps all 68.
`validate_caster_data.py` (validator 18) gates the four places a class declares that it casts —
`class_data.json`'s tier, `base_classes`, `caster_mod`/`divine_casters` and its `spells_per_day`
row — plus that every `class_for_spells` alias resolves to a real `spells.csv` column. Each of the
adept, omdura and vampire hunter had to be walked through those four by hand.

**Stalker and zealot are unchanged** — still `pow_classes_pending_foundry`, still blocked on
`pf1-pow` shipping a class Item (§10).

### GAP: the Spheres base classes are not in the pool (named 2026-08-10)

The generator bolts Spheres **talents** onto existing classes behind the `spheres_of_power` flag,
and that is all it does. The **Spheres of Power** casting classes, the **Spheres of Might**
practitioner classes and the **Champions of the Spheres** hybrids are not rollable at all — so a
subsystem the stack otherwise supports end to end has no native chassis. The sweep already found
**26 of them** in `pf1spheres.classes`; `data.spheres_classes` is still empty and nothing consumes
the list.

This section owns *who is in the pool*, so the gap is named here rather than left implied by a
clause in the deferred list. What it would take, roughly in dependency order: a data source for the
class chassis (progressions, proficiencies, the per-class talent economy — `pf1spheres` is the
obvious candidate and would need the same census treatment §10 gave `pf-content`); rows in
`class_data.json` and `class_choice_schedule.json`; a verdict per class for §11's audit; and class
Items both renderers can resolve, the same blocker that still holds `stalker` and `zealot`.

**Deliberately not charted as a wayfinder map yet** — a map is for work about to be worked, and
there are already two open (mythic, optimal-builder). Chart it when it is taken up.

**Deferred (not built):** **prestige classes**, ruled out deliberately — 100+ classes needing an
entry-prerequisite engine and base-class-level gating the generator has no model for · archetypes
for the seven new classes · the Spheres base classes above · a live Foundry import check of the
seven.

---

## 13. Inherent luck — ✅ GENERATOR BUILT (2026-08-08), in-play half outstanding
**Status: the generator-side subsystem is built and gated; the table-side half is not.** Every
generated character carries a full luck state — a bought score, one of three luck types, a luck mod,
an E-Kat reserve, a Vault ceiling and hero points — earned through a modelled purchase and fed by
the ten E-Kat feats. Charted in `tickets: feature/inherent-luck`; this section is that map's
destination. Tickets 01, 02, 03, 04 and 06 are resolved; **05 (where the in-play d100 table lives)
is open** and owns the danger-level shift, the outcome table and the DR pool as a tracked resource.

**The rule is not in this document.** The authority is Sieg's Guide's Luck sub-doc, extracted to
**`oks/pathfinder/house-rules/luck.md`** in the OKF `pathfinder` bundle. Read the leaf, not this
section, for anything you intend to implement.

**The numbers are not in this document either.** Per the docs doctrine, prose must not restate a
tuning constant — it names the symbol that owns it. That symbol is
**`Backend/utils/class_func/luck.py`**: caps, the mod divisor and its rounding, all six exchange
rates, the propensity and type weightings, the per-pool ceilings, the Vault and the E-Kat reserve
formula. Nothing else in the tree holds a luck constant.

**Luck needed TWO phases, and that is the section's governing lesson.** The feedback loop has both
ends: a seller trades luck for **feat slots**, which must exist before `phase_feat_selection` sizes
its draw, while the E-Kat feats feed luck **back** (+1 per positive luck feat, +4 for Ass Pull,
It Just Works and Luck God) and which feats a character keeps is not final until
`phase_feat_tax_and_swaps` has run its tax chains and child strip. One phase cannot be both before
feat counting and after feat swapping. So `phase_luck_stake` records *intent* and each pool settles
its own share at its own allocation site, where the real budget is known; `phase_luck_resolution`
computes the final state at the far end. Same shape as `phase_bloodline_resolution`.

**The deduction is declared, never silent.** `test_house_invariants` already asserts the 2→4 rank
floor, the 3-ranks-per-level cap and the full-HP house rule. A luck spend that quietly violated any
of them would put the two gate layers in conflict, so skill ranks come off the **budget** (leaving
`sum(ranks) == skill_rank_budget` true) and HP comes off **`Total_HP`** and never off
`sheet_health`, which *is* the full-HP house rule. Both invariants were taught about luck rather
than weakened.

**Two findings the map did not predict.** Re-reading the Doc mid-build corrected the bundle leaf in
four places — the three *selectable* types are Default, Proximity and **Dimorphic** (Negative Luck
is a **sign on the score**, not a type), Dimorphic's cap is **40**, the negative-luck exchange has
explicit rates, and Twist Fate is a real mechanic the Vault exists to fuel. And a generated
character exposed a design hole no reading would have: a seller who then drew E-Kat feats got the
luck straight back and finished **positive**, making the lossy exchange rates pointless. Sellers are
now excluded from the E-Kat feat economy — that is what selling means.

**The E-Kat feats are new machinery, not repair.** They are *not* Metzofitz feats: none of the ten
appears in `data/Metzofitz_Feats.csv`. They live in `data/feats_new.csv` typed `E-Kat`, a file **no
runtime module reads**, and two of the four prerequisite chains are unsatisfiable *as data*
(`"Asspull"` glued; `"All of the above"`, a summarising phrase). They reach a character through
`Backend/json/feats/e_kat_feats.json` — ten curated rows with corrected prerequisites and
machine-readable effects, because the CSV's effects are prose and the feedback loop cannot be
computed from prose. They never join the generic pool: `no_prereq_loop` appends to a **shared**
accumulator later choosers read, so they get their own chooser and slots **carved out of** the feat
budget, the way Path of War, spheres and professions reserve theirs.

**Luck is not a pf1 `change`.** Default Luck applies to percentile rolls and the daily DR pool, not
to d20 rolls, so the score and mod stay displayed numbers. The one real modifier is **Luck God's**
flat +2 to saves, attacks, ability checks, skill checks, AC and caster-level checks, which rides
`Backend/json/feats/feat_changes.json` like every other feat buff, typed `luck` so it does not stack.

**It reaches the sheet.** The E-Kat spend table (`Backend/json/feats/e_kat_exchange.json`, nine rows
verbatim) renders as an **E-Kat Exchange** section at the **top of class features**, led by the
character's carried reserve, with a **Luck Traits** section beneath listing what the reserve bought
(stacks shown as `(x2)`). Both are spliced in at the call site after `phase_luck_resolution`, by
rebuilding `data_dict['class features']` **in place** — `cf.class_features` is the same dict object,
captured before luck resolved, so rebinding would leave the payload reading the old one with the
sections silently absent. Shown only to characters actually in the E-Kat economy; three quarters of
generated NPCs have no luck at all and do not need a nine-row reference table. Labels are ASCII
because they become class-feature **keys**, and keys travel through the module's name matching.

**Gates.** Two layers, sharing no code, because the class-choices map proved a table can never be
its own witness. `validate_luck.py` gates the **data** with no generation — the roster against the
Doc, every prerequisite resolvable and acyclic, the no-double-count rule, the constants' arithmetic
relationships (including that buying must cost more than selling returns, or the exchange is a
free-money loop), and the payload block's position. `check_luck` in `test_house_invariants.py` gates
**behaviour**, hung on the existing `check_character` sweep for **zero** new generations, and
restates the Doc's numbers as literals rather than importing them — importing `LUCK_CAP_POSITIVE`
would make the assertion `25 == 25` no matter what the constant became.

**The Luck Traits are a separate economy, and the first pass got it wrong.** The Doc:
*"25 Permanent E-Kats can be used to purchase a Luck Trait"*, and decisively *"Luck Traits may only
be purchased with E-Kats. These Traits do not grant 1 extra luck."* They are **not** character
traits — an earlier pass put two of them in `data/traits.csv` where `trait_selector` would hand them
out, which is a rules error, and both were removed. There are **34** in three categories
(19 standard / 10 negative / 5 Dimorphic), curated in **`Backend/json/feats/luck_traits.json`**,
with machine-readable effects on the only five that move a computed number — Expanded Luck (cap),
Increase Luck (score), Enhanced Luck Storage (E-Kat store cap), Extra Spin (Twist of Fate/day) and
Big Savings (Vault cap). Category is an **eligibility gate**, not a label.

**The starting reserve is a budget, not a balance** — *"These points must be spent"* — so
`phase_luck_resolution` buys `floor(earned ÷ 25)` traits, variety-first, and carries the remainder.

**The reserve formula is a table ruling, not a reading, and it took three attempts.** "Long Rest
E-Kats" and "Discovery E-Kats" are never defined anywhere in the Doc. Each per-level term is gated
on the feat that produces that kind of E-Kat, and Double Down doubles the **rate of both** — never
the `feats × 5`:

```
long_rest = 2 if Double Down else 1,  but only with Sweet Dreams    (else 0)
discovery = 2 if Double Down else 1,  but only with Stream of Luck  (else 0)
earned    = level×long_rest + level×discovery + (E-Kat feats × 5)   ... ×2 if Dimorphic
```

**A character with no E-Kat feats earns none.** The first implementation gave everyone `level × 2`
regardless, which handed a 20th-level character uninvolved with luck 40 free E-Kats — enough, once
traits landed, to buy one. **The gate encodes the table's own worked examples** (L10 Sweet Dreams +
Lucky Boy = 20; + Stream of Luck = 30; + Double Down = 55, *not* 59; L20 all ten = 130; each
doubling if Dimorphic), because a ruling can only be witnessed by worked examples — two earlier
readings each produced plausible arithmetic and both were wrong. The 99 is a *storage* cap and
bounds only what is carried, never the computation.

**What grants +1 Luck is wider than the E-Kat feats.** *"Every positive luck based feat grants a +1
Luck"*, and *"every e-kat and hero point feat grant an extra luck point"* — so hero point feats
count too. Six such feats already exist in `data/feats.csv` and are already selectable, so they
needed **recognising, not reaching**: Blood of Heroes, Hero's Fortune, Luck of Heroes, Defiant Luck,
Fortunate One and Adaptive Fortune, curated in `Backend/json/feats/luck_feats.json` because nothing
in the CSV marks a feat as luck-related. **Aristeia feats also qualify — and none exists in the
repo's data**, so that rule is recorded and unattached. Because these ride the ordinary pool, a
character with *no* luck stake can still finish with a positive score, and a seller's negative score
can be partially offset.

**The ten Negative Luck traits are unreachable, and the gate asserts it rather than assuming it.**
Negative luck comes only from selling; sellers take no E-Kat feats; no feats means no reserve; no
reserve means no purchase. Each link is a deliberate ruling and the dead end is their product — the
same unsatisfiable-tail shape as the feat prereqs, arriving from a different direction.

**Deferred (not built):** the **in-play half** — the twelve-band d100 outcome table, the
danger-level quartile shift and luck-as-DR as a tracked pf1 resource (ticket 05, and it lands in the
two *consumer* repos, not this one) · the **99-E-Kat "Destined" template**, a once-per-player
capstone with no meaning for a generated NPC · the **attacker/defender luck combination** on attack
rolls, which is a two-character computation unlike anything else on either sheet · **Vaulted
Interest as live state** (generated characters start with an empty Vault; it banks in play) · the
`misc_homebrew_rules` **UI toggle** in the FoundryVTT module and the web sheet — the backend accepts
the input, but nothing sends it yet · the **Negative Luck traits' pf1 modifiers** (Tough Luck's DR/−,
Tough Skin's natural AC, the three Hardened saves, Seen it all) — marked `pf1_change_candidate` in
the curated table but not wired into `feat_changes.json`, because nothing can currently buy them ·
the **`E-Kat Exchange: Rotten Luck`** cost formula, which did not survive extraction · **spending the
carried remainder** in play (the sub-25 leftover is exported, never used).

## 14. Mythic — ✅ BACKEND + GATES BUILT (2026-08-14)

**Status: a generated character can be mythic** — tier, path, per-tier path abilities, mythic
feats, the power/surge chassis, a tradition — legally generated, gated, and carried on the payload.
The [map](https://github.com/The-Data-is-a-lie/tickets/blob/main/tks/pathfinder-char-creator/feature/mythic/map.md)
ruled every design question; this section names the symbols that own the behaviour. **Rendering
(ticket 06, both sheets) is the follow-up effort** — the class-features side-tables already carry
everything, so a mythic character is visible today; the module/web-sheet treatment of the `mythic`
payload block is what remains.

**The grant (ticket 02): the input is the gate.** A `mythic` key beside `seed`/`optimize` —
absent → never (no rarity roll, eleven goldens differ by one `"mythic": null` line and nothing
else), int 1–10 → exactly that tier, `true` → a rolled tier decaying toward the low end
(`mythic.TIER_ROLL_WEIGHTS`). No level gate. `phase_mythic_stake` resolves it beside luck's stake,
before any budget; `phase_mythic_abilities` builds the rest after the feat economy settles.
`'1'` is deliberately not a synonym for `true` — the tier-1 forced cell caught that collision.

**The schedule (ticket 03): a parallel axis file.** `Backend/json/mythic_schedule.json`, same
schema as the class table, keyed by TIER, expanded by the same `levels_for()` (new
`schedule_attr` kwarg). Buckets: `Mythic Path` (single pick, role-weighted draw — casters lean
Archmage/Hierophant, martials Champion/Guardian, skill classes Trickster; weights in
`mythic.path_weights`), `Mythic Path Abilities` (1/tier), `mythic_feats` (1/3/5/7/9). Pools:
`mythic_path_abilities.json`, scraped whole from AoN by `build/build_mythic_path_abilities.py` —
~53–62 per path plus the 43 universal merged in at build time, plus each path's tier-1 feature
options and capstone. Curation flags are load-bearing (the chooser skips them). Owners stamp
`mythic` + the TIER.

**Feats (ticket 04): the filter stays, the chooser is new.** `remove_mythic()` was never a pool
filter — it disambiguates the 139 shared names — so it is untouched for everyone.
`mythic.choose_mythic_feats` reads `type=='Mythic'` explicitly, tier-gates outside the string
prereq engine, and appends post-trim like profession feats: a separate allowance, never an
ordinary slot, never taxed. Collision names wear `(Mythic)`; Dual Path and Extra Path Ability are
recorded v1 exclusions (`V1_EXCLUDED_MYTHIC_FEATS`).

**The chassis (ticket 05), five ways:** power pool = resource (tracked, not enforced; traditions
can buy more), surge = number + prose, Amazing Initiative = tier as a change-to-be, tier HP folds
into `Total_HP` (after luck, before familiars), ability increases ride as an attributable
`{stat: +2}` dict like `level_up_stats`. Mythic spells are an **annotation** on spells already
known (`mythic.spell_annotations`, the 247 `data/spells.csv` modes) — the sampler untouched.
Payload: ONE namespaced `mythic` block at the tail, `None` when non-mythic.

**House carve-outs from Mythic Spheres (2026-08-14)** — the system stays out of scope except:
**traditions for every mythic character** (0–3 drawbacks decaying toward none, each buying a boon
or +1 MP/day, ≤1 quality; `mythic_traditions.json` via `build/build_mythic_traditions.py`;
**Boon: Expertise is Sieg-inverted** — a qualified-but-unselected option from the character's OWN
classes at their levels, never a class they lack) and **sphere masteries for sphere users** (RAW
universal path abilities, merged into the candidate pool for spheres actually held, with a
draw-weight lean). The power metric sees the chassis (`power_adders.json::mythic`, surge as nova
EV, bumps through `ability_scores`); per-path-ability adders are deferred in `_blind.mythic`.

**Witnesses, both layers, both sabotage-proven:** `gates/validate_mythic.py` (config — schedule
schema, six-path roster, universal-merge drift, tradition overrides, ast call sites, payload key;
caught a dropped path and an orphaned schedule row) and `check_mythic` +'s per-character leak
tripwire in `tests/test_house_invariants.py` (behaviour — forced cells at tiers 1/5/6/10 incl.
L40 and spheres-on, the tier axis via a same-tier-different-level twin, chassis formulas, trainer
wiring at the unit; the tripwire runs over all 1,020 non-mythic generations; a sabotaged chooser
trips 8 checks).

**Deferred (recorded, not silent):** rendering (ticket 06) · Dual/Hard Path · mythic archetypes,
templates and monsters · mythic above 20th beyond what the tier cap already implies · the
optimizer reaching for mythic · per-path-ability metric adders · archetype-traded features in the
Expertise pool.

## 15. Optimal builds — ✅ OPTIMIZER V1 BUILT (2026-08-11), L1–20

**Status: the metric, the design rulings AND the v1 optimizer all exist.** The destination
(`tickets: feature/optimal-builder`) is an opt-in mode where every choice the user did not
explicitly make is made well. The measurement phase (2026-08-10) built the metric and baselined
random output; the design was then grilled decision-by-decision against those numbers (the rulings
below), and v1 shipped the same day: the `optimize` named input, the **power-role table**
(`Backend/json/power_roles.json` — seven roles, a 68-class candidate map, floors, **measured
margins**, gear ladders, feat spines, dips; vocabularies owned by
`utils/class_func/power_role.py`), the role phase (`phase_power_role`, right after the classes),
and the spine choosers (gear ladder, six-slot stat placement + bumps/inherents, policy weapon and
armor picks, the feat spine through the legality machinery, dip-shaped multiclass). Random mode is
byte-identical — seven random goldens unmoved, two optimized fixtures added
(`optimized_striker`/`optimized_controller`, forced roles, coverage predicates).

**Witnesses, all three:** `gates/validate_power_roles.py` (config),
`tests/test_optimized_builds.py` (behaviour: floors + beat-the-same-seed-twin + margins —
sabotage-proven: a do-nothing optimizer trips 50 checks), and the A/B report
(`build/report_ab_delta.py --mode optimized`) for the eyeball. **The role table was tuned by its
own gates**: the first runs added the sniper role (alpha's finesse policy was forcing gunslingers
onto melee), cut the blaster role (kineticist's blast is metric-blind, so the role lost to its
random twin), narrowed alpha to the sneak-attack classes, put the attack stat above the casting
stat in every martial role's priority, and surfaced the ambient-feat defect below.

**The score is a profile, never a scalar.** Collapsing the axes needs weights, weights are ticket
01's to set, and a scalar hard-wires the tautology ticket 09 names: an optimizer that maximises X,
gated by a check that X went up, tests only that a maximiser maximises. Each axis is a ratio against
the *Monster Statistics by CR* row for the character's CR — **CR = level − 1**, PF1e's own published
offset for PC-classed NPCs, so a 1st-level NPC lands on CR 1/2 exactly where the table starts. No
tuned correction sits on top; calibrating one would make us the benchmark.

**The payload holds components, not totals**, which is the fact that sized this phase. There is no
AC, save, attack or damage total anywhere in it, and deflection and natural armour sit unfolded
inside `item_changes_dict` — so the metric *computes* PF1e math and is the third implementation of
it in the stack. `build/check_derive_parity.mjs` is the insurance and it passes: seven goldens × six
axes agree with the web sheet's `derive.js`, AC differing by exactly the enhancement bonus below.

**The symbols that own the numbers** (per the docs doctrine, named not restated):
`Backend/scripts/power_metric.py` (the scorer), `Backend/json/cr_benchmarks.json` (the CR table,
CR 1/2–30 published plus CR 31–39 extrapolated and flagged), `Backend/json/power_adders.json` (the
feat allowlist, the structural rules, the assumption set and the blind list),
`Backend/scripts/gates/validate_power_metric.py` and `check_power_metric` in
`test_house_invariants.py` (the two layers, sharing no code).

**Path of War and Spheres are modelled as rules, not name lists.** PoW ships 1,033 maneuvers across
59 disciplines (473 Strikes) and neither subsystem carries a structured damage field — only prose.
Authoring one entry per maneuver is not a measurement job. A readied strike adds the initiation
modifier; a destructive blast is 1d6 per 2 caster levels; everything else is declared blind and
printed on every profile.

### What the baseline found (1,637 characters, 64 classes, levels 1–40)

- **WITHDRAWN (2026-08-11): the original headline measured a bug, not the generator.** "Characters
  fall progressively behind the CR curve — AC 1.73 → 0.37, DPR 1.03 → 0.05" was the product of
  three defects found when Daniel asked whether the numbers could be real: the item chooser
  Title-Cased names against a lowercase-`of` list so a third of the catalogue (the entire big six)
  was silently unbuyable; the sweep funded every level 1–40 with the same 10,000 gp (~7× wealth at
  L1, ~1% at L40); and the dpr axis divided hit-weighted damage by the table's all-hits column,
  double-counting misses. All three are fixed (see the changelog's repair entry) and the baseline
  re-measured on the same seeds.
- **Re-measured (2026-08-11, same 1,637-character band, wealth-by-level gold, after the pricing
  fix below):** overall medians `to_hit` 0.91, `dpr_raw` 0.55, `ac` 0.76, `hp` 0.77, saves
  0.67–0.77. Martial classes sit **at or above benchmark on accuracy** (barbarian/cavalier/samurai
  to_hit 1.08–1.12) with `dpr_raw` 0.65–0.82 against a benchmark that assumes a monster's
  multi-attack routine. **The real remaining gap is high-level and structural:** AC 1.64 at L1 →
  0.44 at L40 and HP → 0.57, because the CR rows grow linearly forever while a PC chassis caps
  out — 12 wondrous slots, +5 enhancement ceilings — which the new median-unspent-gold column
  makes visible (L5–15: the purse is spent to within ~1k; L20: 281k unspent; L40: **4.1M of
  4.78M**, nothing left to buy under uniform draws). Closing THAT gap is what optimized mode, the
  `_target_multipliers` bar, and the luck/mythic fog exist for; the generator itself is no longer
  artificially crippled.
- **The re-measurement's own review caught a fourth defect the first three had masked:** with "+N"
  items finally rollable, they were being sold for **0 gp** (and multi-variant blobs for pennies) —
  both variant-price extractors in `convert_price` were broken, and unparseable fell back to free.
  A golden bought a 50,000 gp ring for nothing. Fixed the same day (prices parse by the
  parenthetical tag the item's own name carries; unpriceable items are refused, never free) and
  the sweep re-run; `gates/validate_item_names.py` now prices the entire pool and fails on any
  windfall shape. The lesson is §15's method in miniature: every number was challenged, and every
  challenge found something.
- **`build_archetype` predicts profile shape only partially** — median η² 0.123, a medium effect,
  with 3 of 8 axes clearing the large threshold. Ticket 01 may use per-archetype weights but must
  not assume the archetype alone defines what good looks like; level and class need controlling for
  first. The coarser **family** grouping is consistently weaker (median η² 0.058), so weight on the
  archetype, not the family.
- **Ticket 07's premise is not supported.** It calls random multiclassing "the single largest source
  of bad builds"; measured over 100 seed-paired pairs it is neutral-to-better — will +0.163, fort
  +0.095 (PF1e stacks a +2 good-save base per class and the generator reproduces it), to_hit/AC/DPR
  flat. The one real cost is caster-level fragmentation, visible as `dc` going negative at L15
  (−0.091) and L20 (−0.116). The ticket said "if the gap is small, this ticket is smaller than it
  looks."

### Bugs this phase found, owned elsewhere

- **The web sheet renders every enhanced character's AC low.** `armor_enhancement_bonus` and
  `shield_enhancement_bonus` are separate payload keys that produce no `ac` change, and
  `derive.js` reads only `data.armor_ac` — so **1,637 of 1,637** scored characters would display 1–5
  AC short. Foundry is unaffected (the module builds real armour Items and pf1 does the maths). The
  metric counts them and the parity harness asserts the delta equals exactly that sum, which makes
  it a regression test for the sheet.
- **Small races never get their size bonus on the web sheet.** `derive.js`'s `sizeInfo` reads
  `data.race` / `data.c_race`; the payload key is `chosen_race`. Neither exists, so every generated
  character renders as Medium. The metric matches, so parity holds and both are wrong the same way.
- **`derive.js` applies no pf1 typed-bonus non-stacking** — `sumParts` is a plain sum, so two
  same-typed bonuses to one target both count. The metric matches deliberately, so the harness
  compares like with like.
- **16 weapon names do not resolve in `weapons_data.json`** — every `Mind Blade` variant — so
  soulknife and psion mind blades score zero weapon damage.
- **The invariant sweep fails at levels 25/30/40**, which it had never run before (the default band
  stops at 20). 263 failures: 254 of them are L30 seed 2202 across all 68 classes, every one off by
  exactly one feat with matching skill-budget and HP mismatches and a violated
  "a seller must gain no luck from feats" invariant — one luck-subsystem bug at high level, not 254
  problems. **Owned by §13, not by this section.**

### The design rulings (2026-08-11 — grilled against the re-measured baseline; detail in the tickets)

Tickets 01/02/07/08 are resolved and 06/09 partially (`tickets: feature/optimal-builder` holds the
argument; this list is what the code will be built to):

- **Scope: the optimizer targets levels 1–20.** L21–40 stays measured-but-unoptimized until the
  mythic map rules — its measured gap is unspendable gold against unbounded CR rows, not chooser
  quality. Mythic, when it comes, is granted *build-aware*, keyed off the role vocabulary below.
- **Objective (01): a small power-role vocabulary.** `Backend/json/power_roles.json` (to be built):
  ~6–9 roles, each naming 2–3 **primary axes plus floors** for the rest, with a
  class→candidate-roles map. **Floors + unbounded primaries**, lexicographic — never a scalar, no
  AC-vs-DPR exchange rate; subject to floors, primaries are pushed as hard as the rules allow.
  Target numbers live only in the gate. Roles dissolve the face-vs-combat collision; survival folds
  into the defensive floors; a role may only name a primary **the metric measures**.
- **The metric grows first:** DR/energy-resist folded from the always-on ledger as a raw axis, and
  a **nova round-shape** (charge, pre-cast self-buffs, alpha strike) beside the round-2 model —
  both ruled into v1 so tank and burst roles are expressible from the start.
- **Arrow (02): plan the spine, score the leaves.** The role is the plan object — a `@phase`
  `provides` chosen after `select_classes`, read by stat placement, weapon, the feat spine, the
  gear ladder and multiclass composition. Leaves (talents/skills/traits/spells) extend
  `build_selector`'s local-scoring shape. `choose_build_archetype` keeps its post-hoc arrow in both
  modes; under optimization its label is a report-side consistency signal. Build order runs in
  lever order, gear first (the biggest measured lever).
- **Gear (08): role-variation only.** Each role carries 2–3 alternative ladders (big six and the
  typed AC stack first); no flavour reserve — variety comes from build divergence. **Typed-bonus
  non-stacking is enforced in the chooser**, never the metric (which keeps its deliberate
  derive.js-parity plain sum). The .5/.35/.15 enhancement split becomes per-role data on the
  optimized path; unspent gold becomes a gate bound.
- **Stats (08): honour the dice, place optimally** — full six-slot priority per role, dump logic
  with a Con floor, level-up bumps and inherents pointed at primaries. No reroll, no elite array.
  **Race stays random even optimized** (the gate's margins absorb the variance).
- **Multiclass (07): role-aware.** Single-class by default; combination knowledge is curated
  **dip lists in the role table**; casting/manifesting roles carry none (the one measured cost is
  CL fragmentation); explicit `multi_class='Y'` is honoured as least-hurt.
- **Contract (06, partial):** a named `optimize: true|"<role>"` key (the `seed` precedent; unknown
  role = error); a nested payload `optimize` block **only when the mode is on** (the `luck` block
  precedent); optimized mode gets its own golden fixtures — the seven random ones never move.
- **Gate (09, policy): measure first, then fix.** Until the optimized A/B distribution exists the
  gate asserts floors plus primaries-beat-the-same-seed-twin; per-role margins are then fixed from
  that distribution, in the role table, under its validator.
- **Luck stays random in v1** — optimal play would converge on always-sell-for-stats and flatten a
  variance subsystem; revisit with a measurement once the optimizer baseline exists.

**v2 — the sweaty pass (2026-08-11, grilled same-day):** the 3pp offense layer is no longer
blind. The metric parses PoW bonus dice from held prose (stances into both rounds, the best
readied strike once), folds haste/ki extra attacks, a vital-strike standard-action alpha, spheres
talent `changes`, and the curated `power_adders.json::spell_buffs` table in two duration tiers
(persistent in both rounds, combat in the nova, no action-economy cap — a declared upper bound;
size buffs step the weapon dice). Defensive buff values live in `ac_buffed`/`saves_buffed`
diagnostics — the base axes stay derive.js-parity-locked. The optimizer exploits the same tables:
dice-greedy PoW picks, ×1000 buff weighting in spell selection for martial-role casters, Boots of
Speed in martial ladders, and striker candidacy for the buff-capable divine chassis (the Gorum
war-priest). Stated upper-bound edges: castability is list-membership (no casting-stat minimum),
talent prose is unparsed, ~12/1,033 maneuvers fail the dice parse.

**v3 — the wall pass (2026-08-12):** fight-state defense joins the metric as the benchmarked
`ac_combat` axis (posture at RAW numbers by ruling — FD +2/+3-with-Acrobatics, ambient CE
1+BAB/4, Crane +1 — plus stance AC parsed-or-curated, monk Wis-to-AC unarmored, style feats,
ambient Dodge, wild-shape natural armor, defensive buffs, held-text AC) and the raw `cmd` axis;
base `ac` stays sheet-state and parity-locked. Stoneskin lands as buff DR. The optimizer builds
walls: AC-greedy stance picks, the Crane/Snapping Turtle spine (unlocked by the optimize-gated
or-clause prereq relaxation and the ambient-prereq seed), 3 banked Acrobatics ranks, the jingasa,
druid wall candidacy, and the half-purse ladder cap (spread before upgrading). Measured wall at
L11: ac_combat 1.71×. Stated edges: Snapping Turtle's free hand unchecked, wild shape is
defense-only (natural-attack routines stay blind), armor materials remain unbuilt.

**v4 — the full house-rules wall pass (2026-08-13, grilled decision-by-decision):** a second
optimizer version behind the named `house_rules` key beside `optimize` — absent/false is
yesterday's optimizer exactly (all ten prior goldens byte-identical), true builds the house AC
kickers the v3 ruling deliberately skipped. Rulings: target is **fight-state AC as a multiplier
anchored at L10** (median ~1.8–2.0×, i.e. 40–50 at L10–12, growing after); **Strength of a
Warrior** is two real spine picks (Str + Con variants, prereq BAB+1 and Str/Con 20+, verified
against Sieg's Feats Doc; two Armor-type `data/feats.csv` rows unreachable by any random pool,
each baking its modifier as a numeric `nac` ledger change — parity-safe in base `ac`);
**sword-and-board counts as wielding two weapons**, so TWF+TWD spine in and +2-while-FD scores;
the **Cautious Warrior** trait (+1 dodge while FD) is the wall's trait pick, injected at
selection (never in traits.csv); every full-house wall **always dabbles one defensive sphere**
(shield / guardian / dual wielding / open hand, shield-weighted, curated-first talent picks, RAW
values per talent — `power_adders.json::sphere_defense`, Active Defense = 2 + BAB/4 with a
shield); **walls are not maximal by ruling** — levers gate naturally (stats, Dex, sphere and
stance draws) and the sweep proves spread (26/80 with any SoaW, 56/80 with TWD, four spheres).
The metric keys every house row off what the SHEET carries (feat/trait/talent held), never the
request flag. Measured (80 walls, 10 classes × L10/12/15/20): ac_combat min 1.59× / med 2.07× /
max 2.80×, raw 40/51/70 at L10–12; gated as `margins_house` (ac_combat 1.5) in the same sweep,
pinned by the `optimized_wall` golden (seed 5150: every lever on one sheet). Escaped finding,
ticketed (optimal-builder 11): `shield_chooser` has never given ANY character a shield — fixed
role-gated for `one_handed_shield` roles only; the global fix moves every golden and awaits
Daniel's ruling. Stated edges: guardian/dual-wielding/open-hand talents render unscored (curation
backlog like stances), apostrophe-spelled stance names still miss the curated match.

**The QC workflow (fastest human path, in escalation order):** (1) CI runs both gate layers free
— a red `test_optimized_builds.py` names the exact role/class/seed/axis. (2)
`build/qc_optimized.py --flags-only` renders machine-verdicted cards and prints only the ones
worth a human's time; a card's seed replays it exactly. (3)
`build/report_ab_delta.py --mode optimized` sorts same-seed pairs regressions-first — read from
the top, stop at the first few net-positive pairs. (4) Only characters that survive to a real
table get the Foundry two-step (inject + applier) and one played round. The Foundry module cannot
send `optimize` yet — until that one-field MR lands, table-QC characters come from the CLI or a
direct POST.

**Deferred (not built), post-v1:** the payload `optimize` block — the payload-shape manifest makes
a mode-dependent key a breaking change, so it waits on the web sheet's positional key-order
coordination the ruling itself required · leaf scoring (talents/skills/spell picks — the specialist
role's `skill_breadth` primary currently moves only via stats and breadth staying intact) · a DR
purchase lever (adamantine armor, a Stalwart spine; then `dr` returns as a wall primary) · a
burst-caster role (needs a kineticist blast rule or destruction-sphere leaf scoring) · 06's
remaining explicit/unset/unmatched truth table (`truly_random_feats` is ruled by construction:
`optimize` forces the build-aware path) · the Foundry batch (10) · **whether the score ships in
the payload for every character** — still left out so no golden moves for a number not yet fully
trusted.

---

## 16. Gear legality — ✅ BUILT (2026-08-17)

**Plan:** `docs/plan_gear_legality.md` (rulings, censuses, and a per-step "found along the way").
**Origin:** [`tickets: feature/optimal-builder/11`](https://github.com/The-Data-is-a-lie/tickets/blob/main/tks/pathfinder-char-creator/feature/optimal-builder/11-shield-chooser-never-shields.md),
which asked about `shield_chooser` and turned out to be one of five instances of the same fault.

### The fault, once, in five places
A lookup that misses and yields a **falsy default**, so nothing ever fails loudly:

| where | what missed | what everyone got |
|---|---|---|
| `data.armor_type_mapping` | tuple keys, string lookup | `'H'` — a wizard in Full plate, a druid in Half-plate |
| `list_selection` | `limits=None` meant "no limit" | a **random draw over all five** `armor.json` sections |
| `shield_chooser` | returned only on its ~10% Tower branch | `None` — **no character ever wore a shield** |
| `shield_flag_func` | mutated, then returned `None` | the caller assigned that `None` back over it |
| `payload.gear_display` ×4 | `spell_failure`, `shield check penalty`, the armour's max-dex | `0` arcane spell failure for every character |

### What replaced it
- **`Backend/json/armor_proficiency.json`**, DERIVED by `scripts/build/build_armor_proficiency.py`
  from `class_data.json`'s own proficiency prose. Rejected: flattening the tuple keys (a
  hand-authored 68-class list with nothing checking it is the arrangement that failed) and runtime
  prose parsing (a regex that stops matching yields the same falsy default).
- **Bands (D3/D5):** heaviest band any rolled class grants, ∩ every rolled class's taboo, then
  capped so a rolled **arcane caster** is never broken — which is why a wizard/fighter goes
  unarmoured and the magus stays in light armour (`magus_armor_chooser` is deleted; its 7th/13th
  promotions are moot under the cap, and its heavy branch sat behind an unreachable `elif`).
- **Shields (D6/D9):** ~20% of every shield-proficient character, ranged excluded outright, from a
  curated **ten** of fourteen; tower only for the four classes whose prose grants it, at ~10%.
- **The two-hander ladder (D7/D8):** polearm/spear → a free `Pikemans Training`; a 2nd-level Titan
  Mauler keeps its jotungrip; otherwise the **shield drops** (never the weapon — re-drawing it
  would bias the weapon distribution).
- **Oversized weapons (D10/D11/D12):** a payload **marker**, never scaled dice. See §16.1.

### 16.1 The oversize marker
`weapon_size`, `weapon_size_steps`, `weapon_size_source`, `weapon_size_attack_penalty`, at the tail
of `PAYLOAD_KEYS`. Computed at the **end** of the pipeline — three of the five sources are feats,
chosen two phases after gear. Sources never stack (take the best); the step caps at 1 unless the
whole Titan Slayer chain is held; the penalty is the **source's own** stated value (−4 for
*massive weapons*, none for `Bigfolk Training`), reduced by *incredible heft* or `Titan Grip`.
The damage ladder itself is Daniel's `Base_Weapon_Damage_Dice.JS` (resource `sizefordamage`, two
positions per size category), copied into `weapon_size_damage.json` **in the macro's own order** —
including two pairs that are not sorted by average, because a re-sorted copy would disagree with
the source silently. The gate warns about them.

### Gates
Two layers sharing no code, sabotage-proven to fail independently:
- **Config** — `gates/validate_gear_legality.py`: coverage, a re-parse for staleness, and a
  **second implementation** (token adjacency, not regex) re-reading each row's recorded evidence
  sentence. A parser that drifts self-consistently passes the staleness check and fails that one.
- **Behaviour** — `check_gear_legality` in `tests/test_house_invariants.py`, re-implementing the
  band union, the caster cap and the taboo intersection rather than importing them. Its coverage
  counters are part of the gate: making shields unreachable again now fails with *"every shield
  assertion passed vacuously"* rather than passing.

### Outstanding
- **Rendering.** Both sheets ignore the four `weapon_size_*` fields today; the FoundryVTT module
  already carries the `sizefordamage` resource that `weapon_size_steps` writes into, so its half is
  setting one value. The web sheet pre-scales. Separate PRs in their own repos.
- **Sweep blind spots**, printed as `0` on every run rather than hidden: tower shields, the
  multiclass caster cap, and oversized weapons (every source is a Metzofitz feat, a race-gated feat
  or a rolled archetype). All three are exercised directly instead.
- **Two absent enablers** stay flagged not-in-pool and proved absent on every gate run: Lighten
  Weapon, and the Equipment sphere advanced talent.
- **The shifter's taboo** names no allowlist and `armor.json` has no material column, so it borrows
  the druid's — a ruling, reported as a SKIP on every run.
