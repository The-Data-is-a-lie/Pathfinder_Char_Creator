---
name: spheres-of-power
description: How the Spheres ecosystem (Spheres of Power magic, Spheres of Might, Spheres of Guile, Champions of the Spheres — Drop Dead Studios 3rd-party PF1e) works, plus this campaign's house rules. Use when working on spheres, magic/combat/skill talents, spell points / mana pool, casting traditions, drawbacks & boons, martial focus, practitioner modifier, Extra Magic/Combat/Skill Talent feats, martial traditions, or wiring Spheres into the generator. Mythic Spheres are out of scope.
---

# Spheres (of Power / Might / Guile / Champions) — rules + this campaign's house rules

A 3rd-party PF1e ecosystem by Drop Dead Studios. Everything is **talent-based**: instead of feats or
Vancian spell slots, you spend **talents** to buy into **spheres** (themed ability groups). Each sphere
grants a **base ability** the first time you take it, then individual **talents** refine/expand it.
Four sub-systems, same DNA:

- **Spheres of Power** — magic (replaces Vancian casting). Currency: *magic talents*. Resource: *spell points*.
- **Spheres of Might** — martial (augments/replaces the feat system). Currency: *combat talents*. Resource: *martial focus*.
- **Spheres of Guile** — skill/social/investigation. Currency: *skill talents*. Resource: *skill leverage*.
- **Champions of the Spheres** — the "unified system" capstone: blended base classes that mix the above.

> **Scope note:** Mythic Spheres / mythic rules are intentionally **out of scope** for this campaign right now.

## Spheres of Power (magic)

- **Spheres** (core magic spheres): Alteration, Conjuration, Creation, Dark, Death, Destruction,
  Divination, Enhancement, Fate, Illusion, Life, Light, Mind, Nature, Protection, Telekinesis, Time,
  War, Warp, Weather (more in expansions/Apocrypha). First talent in a sphere = its base ability;
  later talents = that sphere's specific talents.
- **Gaining magic talents:** you get **2 bonus magic talents the first time you take a level in a
  class with the casting class feature**, then more per level by class. Multiclassed casting classes
  **stack** their talents, caster levels, and spell points.
- **Caster level (CL):** High-caster = class level, Mid-caster = ¾ level, Low-caster = ½ level; CLs
  from multiple casting classes **add together**. CL sets range, duration, effective spell level
  (`CL/2`), and the save DC.
- **Casting Ability Modifier (CAM):** one of **Int / Wis / Cha**, fixed by your *casting tradition*.
  Drives: spell points, save DC, spell-resistance checks. Multiclass casters pick one CAM.
- **Spell points (the pool):** `spell points = class level + CAM` (sum class levels across all casting
  classes). Refreshes once/day after ~8h rest. Spent to empower abilities, sustain effects without
  concentration, or pay ability costs.
- **Save DC:** `10 + ½ CL + CAM`.
- **Magic Skill Bonus / Defense:** `MSB = total levels in spherecasting classes`; `MSD = 11 + MSB`.
  MSB replaces CL on caster-level checks/concentration (`1d20 + MSB + CAM`); MSD is the DC others hit
  to suppress/dispel your magic.
- **Casting traditions** = CAM + a set of **drawbacks**, which are the currency that buys **boons** and
  **bonus spell points**: **2 general drawbacks = 1 boon**; drawbacks not spent on boons convert to
  bonus spell points on a rising chart (1→1, 2→3, 3→6, 4→10, 5→15, …). Some drawbacks count as two.
  General drawbacks are locked in at creation; *sphere-specific* drawbacks (taken when you gain a
  sphere) instead grant bonus talents.
- **Non-caster access:** the **Basic Magic Training** feat grants a sphere + a small pool; **Extra
  Magic Talent** grants additional magic talents.
- **Spherecasting base classes** (examples): Incanter, Soul Weaver, Fey Adept (high); Symbiat,
  Eliciter (mid); Mageknight, Armorist (low); plus Hedgewitch, Elementalist, Shifter, Thaumaturge.

## Spheres of Might (martial)

- **Combat spheres** (~24): Alchemy, Athletics, Barrage, Barroom, Beastmastery, Berserker, Boxing,
  Brute, Dual Wielding, Duelist, Equipment, Fencing, Gladiator, Guardian, Lancer, Leadership, Open
  Hand, Scoundrel, Scout, Shield, Sniper, Trap, Warleader, Wrestling. Talents split into **basic**
  (gritty/low-magic) and **legendary** (wuxia/supernatural).
- **Martial focus:** you have **one** (you either have it or you don't). Regain it after **1 minute of
  rest** or by taking the **Total Defense** action — **never more than once per round**. While focused
  you may **expend focus on a Fortitude or Reflex save to treat the roll as a 13** (like take-10 but
  +13), or to fuel talents/class features that call for it. Lasts until expended, unconscious, or
  asleep/trance.
- **Practitioner modifier:** the ability mod used for your talents' DCs (defaults to **Wis** if you
  have no practitioner class; multiclass uses the highest). Sphere DC = `10 + ½ BAB + practitioner mod`.
- **Gaining combat talents:** by class, on the **Expert / Adept / Proficient** progression (Expert
  ≈ 1/level → 20; Adept → ~15; Proficient → ~10 by level 20). **Extra Combat Talent** feat = +1 talent.
- **Non-practitioner access:** the **Combat Training** class feature, the **Extra Combat Talent** feat,
  or feat-to-talent conversion (trade standard feats at fixed levels → Proficient/Adept progression),
  or trade spellcasting for a progression. Any of these also lets you achieve martial focus.
- **Martial traditions:** the martial analog of casting traditions — a pre-built level-1 package of
  talents/benefits. **A non-practitioner may trade all base weapon/armor proficiencies for a martial
  tradition** (this campaign's proficiency rule — see Repo section).

## Spheres of Guile (skill)

- **Skill spheres** (~15): Artifice, Bluster, Body Control, Communication, Faction, Herbalism,
  Infiltration, Investigation, Navigation, Performance, Spellhacking, Study, Subterfuge, Survivalism,
  Vocation. A sphere's base ability grants **5 ranks in its associated skill(s), +5 per further talent
  in that sphere (max = your Hit Dice)**, then individual talents.
- **Skill leverage:** the resource pool — spend it to impose penalties / raise DCs on NPCs' rolls
  (stackable). GM rules it as a daily pool or a per-action improvisation pool.
- **Gaining skill talents:** by class progression, trade traditions, or the **Extra Skill Talent**
  feat (+1 talent). Operative ability modifier sets DCs (Guile's analog of the practitioner modifier).

## Champions of the Spheres (unified)

The capstone "unified system" book for using Power + Might (+ Guile) on one character. Adds blended
base classes — **Prodigy, Sage, Troubadour** — and rules for caster/practitioner hybrids. Key
mechanical point: **spell points and martial focus stay SEPARATE pools** — a blended character is a
caster *and* a practitioner at once, drawing magic talents/spell points and combat talents/martial
focus independently. (Spheres of Might also ships its own base classes — e.g. Armiger, Conscript,
Sentinel, Striker — **verify the full roster against the book**; the wiki page was unreachable.)

## This campaign's house rules (AUTHORITATIVE)

1. **Extra-talent feats feat-tax once.** Taking **Extra Magic Talent / Extra Combat Talent / Extra
   Skill Talent** bundles a **second copy** of the same feat — rendered as a chain `Extra Talent >
   Extra Talent` — so **one feat slot grants 2 talents**, and the feat-tax chain **stops there** (no
   further taxing).
2. **Same system, two spheres.** The 2 talents from a single Extra-Talent feat must both belong to the
   **same main system** (both Spheres of Power, OR both Might, OR both Guile — **no mixing systems on
   one feat**). They **may** come from **2 different spheres/subsections** within that system (e.g. one
   Destruction talent + one Alteration talent).
3. **Unlimited drawbacks in a casting tradition.** No cap on the number of **drawbacks ("negatives")**
   a **casting tradition** may take — stack as many as you want, converting them to boons (2 drawbacks
   = 1 boon) and bonus spell points (the rising chart). Applies to **casting traditions (Spheres of
   Power)**; martial traditions are fixed packages and don't use this economy.
4. **Mana pool for SoP-dabblers.** A character whose class is **not** a Spheres-of-Power casting class
   gains a spell-point ("mana") pool **as soon as they pick up anything Spheres-of-Power-related** (a
   magic talent via Basic Magic Training / Extra Magic Talent, a casting tradition, etc.). That pool =
   their **highest mental ability modifier** (the larger of Int/Wis/Cha mod; **min 1**; refreshes
   daily) — replacing the tiny default pool Basic Magic Training would give. A character who never
   touches Spheres of Power gets **no** pool.

> **Mythic** Spheres/rules are **ignored** for now.

## Repo status & where it plugs in (IMPLEMENTED — v1 "dabbling")

A normal, **non-spherecasting** NPC can now dabble into Spheres. Real spherecasting **base classes** and
**Spheres of Guile** remain out of scope (the user adds classes via the FoundryVTT compendium /
everyClass). Decisions locked with the user: **opt-in flag**, **feat-funded talents**, **casting
traditions in v1**, **enrich combat data from the Foundry compendium**.

- **Chooser:** `Backend/utils/class_func/spheres.py` — mirrors `path_of_war.py`:
  - `randomize_spheres_num(character)` — gated on `character.spheres_flag` (default `'N'`); rolls **0–3**
    spheres (`SPHERE_COUNT_WEIGHTS`), capped by the post-PoW feat budget.
  - `choose_spheres_attr(character)` — orchestrator returning the export bundle (empty when count 0).
  - `_system_for_sphere` — per-sphere **Might vs Power** by caster level (none→Might; low→50/50; mid→75%
    Power; high→90% Power), read via `character.class_data[c_class]['casting level']`.
  - `_pick_talents_in_sphere` — reuses `generic_func.no_prereq_loop` for prereq-legal picks and enforces
    the **§8 gate**. ⚠ `no_prereq_prep`'s `filter_pattern` matches the substring **"cast"**, so a magic
    talent's `caster level Nth` prereq is auto-satisfied — the prereq engine alone WILL leak advanced
    talents, so the talent's `type` is the authoritative guard.
  - `_advanced_quota(normal, feats)` = `(normal + 2*feats) // 7` — **HR §8 hard invariant** (precondition
    during selection + defensive post-condition drop). A sphere **feat counts as 2** normal talents.
  - `_build_sphere_feats` / feat handling — `Basic Magic Training` (magic entry) + `Extra Magic|Combat
    Talent` feats; the HR1 `Extra Talent > Extra Talent` duplicate is a hand-built `sphere_feat_tax`
    merged in `main_test.py` exactly like the style/MT chains (registers children in
    `_tax_already_granted`). HR7 record-keeping: the feat's `homebrew_feat_desc_dict` entry lists the
    talents it granted.
  - `_choose_casting_tradition` / `_mana_pool` — magic dabblers get a CAM (highest mental stat), drawbacks
    → boons (2:1) → bonus spell points (triangular chart), and the **HR4 mana pool** = `highest_mental_mod`
    (reused from `skill_ranks.py`, min 1) + bonus SP. `casting_tradition.drawbacks`/`boons` stay **name
    strings** (kept `.join()`-safe so a stale/older front-end never renders `[object Object]`); the rich
    text rides parallel `casting_tradition.drawbacks_detail`/`boons_detail` keys — `{name, description,
    counts_as}` dicts (sourced from `spheres_traditions.json` / `_FALLBACK_TRADITIONS`) that the sheet
    reads to spell out what each does and how the drawback→boon→bonus-SP math worked out. The flat
    `sphere_drawbacks`/`sphere_boons`/`sphere_traits` exports are the same name strings.
- **Data + extractor:** `Backend/scripts/extract_spheres_talents.py` unpacks the FoundryVTT `pf1spheres`
  ClassicLevel packs (`magic-talents`, `combat-talents`, `sphere-feats`) via
  `npx @foundryvtt/foundryvtt-cli package unpack` (copy the pack out first — Foundry locks the live DB;
  drop the `LOCK` file). Sphere = `flags.pf1spheres.sphere` (camelCase, e.g. `dualWielding`/`fallenFey`);
  `system.subType` = `magicTalent`/`combatTalent`. Outputs under `Backend/json/class_data/spheres/`:
  `spheres_of_power.json`, `spheres_of_might_enriched.json` (scraped selection truth + Foundry
  description/type), `sphere_feats.json`, `advanced_talents.json`. **No structured advanced flag exists**
  in the pack, so: **magic advanced** = `caster level Nth` prereq ∪ `(advanced)` cross-ref (~256, solid);
  **combat legendary** = `(legendary)` / "legendary talent" cross-refs (sparse — `advanced_talents.json`
  ["might"] is the editable override registry). `spheres_traditions.json` (CAM/drawbacks/boons/chart) is
  **harvested separately** (the wiki is unreachable via WebFetch — http↔https 301 loop — so a built-in
  fallback in `spheres.py` keeps the feature runnable until the harvest lands).
- **Integration (`Backend/main_test.py`):** `spheres_flag='N'` param (backward-compatible — `app.py`'s
  positional unpack + the CLI run still work; front-end wiring deferred to the user). Block sits **after
  the Path of War section** (feat-slot reservation), appends `sphere_feats` to the normal bucket, merges
  `sphere_feat_tax` + `homebrew_feat_desc_dict`, and exports: `magic_talent_items`, `combat_talent_items`,
  `sphere_feats`, `sphere_feat_tax`, `sphere_mana_pool`, `spheres_chosen`, `sphere_counts`,
  `casting_tradition`, `sphere_drawbacks`, `sphere_boons`, `sphere_traits`.
- `docs/feature_spec_todo.md §2` is now **IMPLEMENTED**; `docs/homebrew_rules.md §1`'s
  proficiency→martial-tradition trade stays in `armor_and_weapon_chooser.py`.
- **Foundry render:** talent items use the profession-item shape (`{name, description, changes,
  contextNotes, uses}` + `sphere`/`system`/`type`); `changes`/`uses` are empty in v1 (description-only).
  The single **Spheres Casting** summary feat (`processSpheres` in the module's `modify-abilities.js`)
  now renders a fully self-explanatory block: the casting ability + mana-pool breakdown, and Drawbacks /
  Boons as description lists (each drawback shows its 1-/2-point weight) followed by a "tradition math"
  line. It reads `drawbacks_detail`/`boons_detail` and falls back to the name-string `drawbacks`/`boons`
  arrays, so it degrades to clean names (never `[object Object]`) against an older backend payload.
  **Note:** the module JS loads once at Foundry startup — after editing `modify-abilities.js` you must
  hard-refresh (Ctrl+Shift+R / reload the world) and generate a *new* actor (old actors bake the HTML in).
  The mana pool maps to a pf1 resource (`@resources.<tag>.max` = highest mental mod) — see
  `foundry-sheet-references`.
- **Per-roll talent conditionals (mirrors Path of War):** attack-relevant talents become **default-off
  conditional toggles** on the main weapon (Might + non-Destruction Power) or on a synthesized
  **Destructive Blast** attack item (Destruction, base `(ceil(@spheres.cl.total/2))d6`). Clean numbers →
  structured `modifiers[]` (auto `[Talent]`-labeled); saves/DCs/conditions/durations/bleed → `[[ ]]`
  rider text. DCs: Power `10 + floor(@spheres.cl.total/2) + @spheres.cam`, Might `10 +
  floor(@attributes.bab.total/2) + @spheres.pam`. The module's `addSphereTalentConditionals()` /
  `addDestructiveBlastAttack()` substitute the dabbler tokens (`@spheres.cl.total→1`,
  `@spheres.cam/pam→@abilities.*.mod`) and stamp `flags.pf1spheres.castingAbility/practitionerAbility`.
  Data files: module `combat_talent_conditionals.json` / `magic_talent_conditionals.json` (nested
  `{Sphere:{Talent:{modifiers,rider}}}`) — authored via `Backend/scripts/build_talent_conditionals.py`
  (`--dump-worklist`) + gitignored `Backend/scripts/_spheres_generator/` (per-sphere curated files +
  `promote_talents_to_module.py`). **PASSIVE** Might self-buffs stay in the separate backend
  `combat_talent_changes.json` (Changes tab) — don't confuse the two. Rules:
  [`docs/spheres_conditional_decision_rules.md`](../../docs/spheres_conditional_decision_rules.md). The
  palette (`build_pow_template_actor.py --spheres`) bundles per-sphere weapons + the blast, keeping
  **native** `@spheres.*` tokens (+ a "Palette: Sphere CL 10" toggle) so copies scale on a real PC.
- **Affects-others talents → distributable buffs, not conditionals:** a talent whose bonus lands on an
  ally / companion / summon / aura recipient is authored as a `buff` curation entry
  (`{aura_range, only_others, changes, contextNotes, description}`), promoted to the module's
  `talent_aura_buffs.json`, and rendered as an inactive temp buff named `<Talent> (TAG)` per the
  [`multi-buff-distributor`](../multi-buff-distributor/SKILL.md) skill — `(UNAMED)` on the palette, the
  NPC's name-prefix tag on generated characters (`addSphereAuraBuffs`). Enemy-debuff auras use
  `only_others: true`.
- **What becomes a conditional (curation rule):** **anything usable as a _strike_ can be a
  conditional** — a strike applies its effect on *any* attack roll, so it maps directly onto a weapon/
  blast conditional (e.g. Destruction *Energy Strike*, Death *Vampiric Strike*, Enhancement *Crippling
  Strike*; detect by the name or "make a weapon attack in conjunction with…" / "deliver … through a
  touch attack"). **Soft rule:** any base ability or talent that deals **single-target damage** or
  inflicts a **debuff/condition** on a target is *likely* a conditional too. Only genuine
  battlefield-control / area / self-buff / out-of-combat utility talents stay description-only (or a
  `passive` self-buff). This applies to **both** Power and Might; Power especially (its strikes were
  easy to miss). `build_talent_conditionals.py --dump-worklist` tags each talent with a `_hint`
  (`strike`/`damage`/`debuff`/`maybe-skip`) to guide curation.

## Sources & gotchas

- Primary: the Spheres of Power wiki — `start`, `using-spheres-of-power`, `using-spheres-of-might`,
  `using-spheres-of-guile`, `using-champions-of-the-spheres` (spheresofpower.wikidot.com).
- The Champions page kept failing via fetch (http↔https 301 redirect loop); its class roster was
  confirmed from secondary sources (opengamingstore / dropdeadstudios). Re-verify class names against
  the book before relying on them in generation.
- Numbers above are the campaign's working values; **verify exact spell-point/drawback charts and
  per-class talent counts against the live wiki before coding them into the generator** (same caveat
  `docs/homebrew_rules.md` flags for all Spheres data).
