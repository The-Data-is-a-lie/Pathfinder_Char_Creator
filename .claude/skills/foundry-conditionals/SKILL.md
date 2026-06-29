---
name: foundry-conditionals
description: How to author per-roll conditional modifiers and rider effects on a FoundryVTT pf1 attack/strike/spell — the action.conditionals[] structure, the house convention for tagging non-damage riders, and the source-label convention that makes every damage roll show where it came from. Use when an attack/maneuver/spell grants a bonus, forces a saving throw, deals ability damage/drain, inflicts a condition, or has any other effect: encode clean numbers as modifiers and put the rest in the conditional name with EVERY number in [[ ]] inline rolls. Covers the full "what a conditional must describe" checklist (contingency, DC, range, targets, saves, damage, attack boosts, duration). Modeled on Lok'Nathal's Feasting Wraith Strike / Headstone Breaking Strike and the Inheritor's Smite pattern.
---

# FoundryVTT pf1 — conditionals & rider effects on attacks

How to attach optional, per-roll effects to an attack / strike / spell. Clean damage and attack
bonuses go in structured **conditional modifiers**; saving throws, ability damage, conditions, and
every other rules rider go in the conditional's **name** with every number written as a `[[ ]]`
inline roll. The generator **auto-labels every modifier's damage with its source**, so a rolled die
on the card always shows what produced it. For the `@…` references used inside formulas and brackets
(save DCs, `@attributes.cmb.total`, `@spells.primary.cl.total`, …) see the **foundry-sheet-references**
skill; for Path of War specifics see the **path-of-war** skill.

---

## The two bracket syntaxes — never conflate them

This is the single most important thing to get right. pf1 uses square brackets for **two completely
different** things:

| Syntax | What it is | Where it goes | Who writes it |
|---|---|---|---|
| `[[ formula ]]` | an **inline roll** — renders as clickable dice / a rolled number on the chat card | inside a conditional **name** and inside **rider / description text** | **you**, the author |
| `formula[Source]` | a **damage-part flavor / source label** — shows the source next to the dice in the roll breakdown (e.g. `8d6 (Circle of Razor Feathers)`) | inside a **damage or attack formula** string | the **module auto-appends it** — author plain formulas |

- **"Put every number in `[[ ]]`"** always means the *double-bracket inline roll* in name/rider text.
  Never the single-bracket source label.
- **You never hand-write the `formula[Source]` label.** The generator appends it at attach time from
  the conditional's clean source name (the maneuver name, the spell name, or the feat name before its
  `:`). Author the formula as plain dice/number (`8d6`, `5`, `(@abilities.con.mod) + 3`). If a
  formula already contains a `[label]`, the module leaves it alone (it never double-labels), so a
  hand-baked label is respected but unnecessary.
- **Net effect:** a conditional that rolls `8d6` shows `8d6 (Maneuver Name)` on the card; a `+5`
  attack shows `5 (Spell Name)`. Damage and attack rolls are always traceable to their source.

---

## Two ways an attack carries an effect

**1. Formal `save` block** — best for spells and standalone actions. Lives on the action:

```jsonc
"save": {
  "type": "will",            // "will" | "fortitude" | "reflex"
  "dc": "",                  // a formula; often blank and computed by the system
  "description": "Will negates",
  "harmless": true            // optional: beneficial effect
}
```
Real anchors: Invisibility `"Will negates or Will negates (object)"` (`harmless: true`),
Cause Fear `"Will partial"`, Death Ward `"Will negates"`.

**2. Conditional-name convention** — the **house style for weapon strikes, maneuvers, and spell
riders**. Each strike/boost/spell is a conditional on the weapon's (or spell's) attack action; the
*rule text and numbers* go in the conditional `name`, with dice and save DCs wrapped in `[[ ]]` so
they render as clickable inline rolls. This is the preferred pattern for hand-built martial
characters (Lok'Nathal) and is what `maneuver_changes.json` / `spell_changes.json` / `spell_riders.json`
feed the generator. Details below.

## `conditionals[]` schema

An action carries `action.conditionals` = an array of conditional objects:

```jsonc
{
  "_id": "zp3qXHs3NpTr3nCl",     // unique id
  "name": "Ki Damage",            // toggle label; SHOULD embed [[ ]] inline rolls for every number
  "default": true,                // true = on by default; false = opt-in toggle
  "modifiers": [ … ]              // structured modifiers — MAY be empty
}
```

Each entry in `modifiers`:

```jsonc
{
  "_id": "4KpxXXA5mx1JwWDq",
  "formula": "(@abilities.con.mod) + 3",  // flat or dice; keeps real dice like 2d6; PLAIN (no [label])
  "target": "damage",                       // "damage" | "attack" | …
  "subTarget": "allDamage",                 // "allDamage" | "allAttack" | "attack_0" …
  "damageType": ["piercing"],               // pf1 damage types; [] for non-typed
  "critical": "normal",                     // "normal" | "nonCrit" | "onCrit"
  "type": "untyped"                          // bonus type for stacking
}
```

Worked examples (Lok'Nathal weapon, Pascal greatsword):

- **Ki Damage** — `formula: "(@abilities.con.mod) + 3"`, `target: "damage"`,
  `subTarget: "allDamage"`, `damageType: ["piercing"]`, `critical: "normal"`. A clean ability-scaled
  damage rider. On the card it rolls as `… (Ki Damage)`.
- **Darkened Axe Style** — `formula: "2d8"`, `damageType: ["negative"]`, `default: false`. An
  opt-in dice rider (`2d8` stays as real dice — unlike a buff change, which would maximize to 16).
- **Vital Strike** — `formula: "+2d6"`, `critical: "nonCrit"`. Extra dice that do **not** multiply
  on a crit.

## What every conditional must describe — the checklist

Err on the side of **more descriptive, not brief**. When you author a conditional's `name` / `rider`,
walk this checklist and include every item the ability actually has, with **every number in `[[ ]]`**:

| Item | What to write | Notes |
|---|---|---|
| **Contingency / prerequisite** | *when* the effect fires — "on hit", "if the target fails the save", "on a charge", "while raging", "only vs a flat-footed target", "expend [[1]] use" | see *Prerequisites* below; if the effect is unconditional, say nothing |
| **Attack boosts** | flat/dice bonus to-hit | a real `modifiers[]` entry (`target:"attack"`); name it in text too if it has a bonus *type* (`+[[2]] sacred attack`) |
| **Damage** | the damage dice | a real `modifiers[]` entry (`target:"damage"`). **Do NOT also restate it in the name/rider** — it's on the roll, with its source label |
| **Saving throw** | save type + DC | `Fortitude Save [[ 10 + @sl + @ablMod ]] negates/halves` — the DC always in `[[ ]]` |
| **DC(s)** | any other DCs (maneuver checks, secondary saves) | always `[[ ]]` |
| **Range** | reach / range / burst radius | `target within [[60]] ft`, `[[30]]-ft radius burst` — include when it's not an obvious melee strike |
| **Number of targets** | who it hits | `one creature`, `all creatures in the area`, `[[1d4+1]] creatures` |
| **Duration** | how long riders last | `sickened [[1d4]] rounds`, `for [[@pow.initLevel]] rounds` |
| **Secondary effects** | conditions, DR/hardness bypass, temp HP, forced movement, *secondary* damage with no modifier of its own | all numbers `[[ ]]`; e.g. `ignore DR/hardness up to [[@attributes.hd.total]]`, `the trail deals [[6d6]] to enemies entering it` |

If an item doesn't apply, omit it — but if it applies, include it. A reader of the toggle should be
able to run the ability from the name alone.

## Prerequisites — what is contingent for the effect to work

Many riders only matter *if something happens first*. State that trigger in the name so the GM knows
when to apply the conditional. Common forms:

- **On a hit** — implicit for most strike riders (the conditional only matters when the attack lands),
  but spell-out for anything that keys off the hit: `on hit, free bull rush [[ d20 + @attributes.cmb.total + 5 ]] vs CMD`.
- **On a failed save** — `Fortitude Save [[ 14 + @INITMOD ]] negates; on a failure, sickened [[1d4]] rounds`.
- **Resource / action cost** — `expend [[1]] use`, `costs [[1]] ki`, `(charge only, no AoO, -[[2]] AC)`.
- **State / positioning** — `while raging`, `only vs a flat-footed target`, `if you moved [[10]]+ ft this round`, `target must be within [[30]] ft`.
- **Stacking / once-per** — `[[1]]/round`, `does not stack with itself`.

Put the trigger first when it gates the whole conditional, e.g.
`"(Strike) Foo: on a charge — [[6d6]] is on the roll; Reflex Save [[ 16 + @INITMOD ]] or knocked prone for [[1]] round"`.

## The rider rule (the important part)

> If a strike/spell **forces a saving throw**, **deals ability damage/drain**, or has **another
> important non-damage effect** (ignores DR, inflicts a condition, grants a maneuver check, pushes a
> target, grants temp HP, etc.), put it in the conditional **name** and write every number in `[[ ]]`.
> Leave `modifiers: []` empty when the effect isn't a clean damage/attack number; add the bonus to
> `modifiers[]` when it is (the two coexist — see the Inheritor's Smite pattern).

Why: pf1 has no structured "ability-damage" or "forces-a-save-and-halves" modifier on a weapon
conditional, so those effects are **text the GM reads**, with the dice/DC made rollable via `[[ ]]`.

**Never restate rolled damage in the note.** If the conditional's `modifiers[]` already rolls the
damage (with its auto source label), the name/rider must **not** repeat it. The note carries only the
non-damage riders and any *secondary* damage that has no modifier of its own (e.g. `[[1d6]] to the
initiator`, `the trail deals [[6d6]]`). And **never bury the rolled dice or a bare "deals N damage"
in the toggle NAME** — the dice live on the roll; the name says the *source* and what's special. (The
old Firebelly / Ectoplasmic Eruption entries broke this — their names said "Deal 6d6 points of
damage" while the modifier already rolled the `6d6`.)

### Verbatim exemplars (Lok'Nathal) — copy these patterns

**Feasting Wraith Strike** — ability damage + a save, every number inline:
```jsonc
{
  "name": "Feasting Wraith Strike : Con Damage [[ 2d4 ]] and your victim becomes shaken for [[@abilities.wis.mod ]] rounds.  A successful Will save [[ 10 +  floor(@attributes.hd.total / 2) + @abilities.wis.mod ]] halves the Constitution damage and prevents the shaken condition.",
  "default": true,
  "modifiers": []
}
```

**Headstone Breaking Strike** — variable ability damage + an immunity-piercing note:
```jsonc
{
  "name": "Headstone Breaking Strike [[1d4]] Ability Damage to a physical stat of my choice. Ignores Undead immunity (except to Con damage)",
  "default": true,
  "modifiers": []
}
```

**Hexing Attack** — save-or-debuff, DC inline:
```jsonc
{
  "name": "Hexing Attack: Saving Throw [[ 10 + @attributes.hd.total + @abilities.wis.mod]]. or take a –2 penalty on attack rolls, saving throws, skill checks, or ability checks for 1 minute.",
  "default": true,
  "modifiers": []
}
```

More patterns from the same actor / Pascal (all `modifiers: []`, rule in the name):

- **Shrieking Shadow Axe** — `"… Strength Damage: [[+1d8]] (Target gains a negative level …). You gain temporary hit points equal to 2x Strength Damage"` — ability damage + extra riders.
- **Rotting Axe Style** — `"… ignore hardness and overcome an amount of damage reduction equal to [[@attributes.hd.total]] for [[1]] round"` — DR/hardness bypass scaled by HD.
- **Free Hand Maneuver / Strike and Seize** — `"… [[ @attributes.cmb.total ]] Dirty Trick/Disarm/Drag/Reposition/Steal Check"` (`default: false`) — a maneuver check option.
- **Skill used as an attack roll** (a maneuver that swaps a skill for the to-hit, vs AC) — include the actor's misc attack bonus: `"… attack uses [[ d20 + @attributes.attack.general + @skills.<id>.mod ]]"`. e.g. Piercing Thunder *Leaping Strike* (Acrobatics), Surging Shark *Sand Shark Rush* (Swim).
- **Skill in place of CMB vs CMD** (dirty trick / disarm / steal / trip via a skill) — keep CMB's size/misc, swap out BAB + ability: `"… [[ d20 + @attributes.cmb.total - @abilities.<str|dex>.mod - @attributes.bab.total + @skills.<id>.mod ]] vs CMD"`. Melee subtracts `str`, ranged subtracts `dex` (e.g. Roaring Mouse *Tricksy Strike* → str + Escape Artist; Tempest Gale *Disarming Shot* → dex + Sleight of Hand).

### New full-criteria exemplars (the target standard)

**A damage strike with a save + condition + duration** — main damage on the roll (auto-labeled
`8d6 (Abyssal Drive)`), everything else in the name with every number bracketed and the contingency
named:
```jsonc
"Abyssal Drive": {
  "modifiers": [
    { "formula": "8d6", "target": "damage", "subTarget": "allDamage",
      "type": "untyped", "damageType": [], "critical": "nonCrit" }
  ],
  "rider": "charge only (no AoO, -[[2]] AC); one creature; on hit, sickened [[1d4]] rounds; Fortitude Save [[ 16 + @INITMOD ]] negates the sickened"
}
```
Note: the `8d6` is **not** repeated in the rider — it's on the modifier, source-labeled automatically.

**A burst with range + targets + secondary damage** — the burst's own damage is the modifier; the
"trail" damage has no modifier so it stays in the rider as an inline roll:
```jsonc
"A Blink of the Universe": {
  "modifiers": [
    { "formula": "6d6", "target": "damage", "subTarget": "allDamage",
      "type": "untyped", "damageType": ["force"], "critical": "nonCrit" }
  ],
  "rider": "all creatures in a [[30]]-ft line; direct hit blinded [[1]] round; enemies entering the trail take [[6d6]] magical bludgeoning and are pinned; Fortitude Save [[ 18 + @INITMOD ]] halves and negates pinned"
}
```

## Attack/damage bonus + rider in ONE conditional (the Inheritor's Smite pattern)

A single conditional can carry **both** a structured attack/damage **modifier** *and* `[[ ]]` rider
text in its **name** — you don't have to choose. This is how a spell/maneuver that grants a clean
bonus *and* forces a save / inflicts a condition / triggers a combat maneuver is encoded. Real
anchor — the cleric spell **Inheritor's Smite** (+5 sacred to-hit, then "if the attack hits, free
bull rush at +5 sacred to the CMB check, no AoO"):

```jsonc
{
  "name": "Inheritor's Smite: +[[5]] sacred attack; on hit, free bull rush [[ d20 + @attributes.cmb.total + 5 ]] vs CMD (no AoO)",
  "default": false,
  "modifiers": [
    { "formula": "5", "target": "attack", "subTarget": "allAttack",
      "type": "sacred", "damageType": [], "critical": "normal" }
  ]
}
```

- The **bonus** is a real modifier (`target:"attack"`); the **bull rush** is rider text with its
  roll in `[[ ]]`. Both live in one conditional.
- **Author plain formulas (`"5"`), never bake the `[label]` yourself.** The generator module
  **auto-appends a source label to every modifier — attack AND damage** — at attach time, deriving
  it from the clean name (the maneuver/spell name, or a feat name before its `:`). So:
  - an attack formula becomes `5[Inheritor's Smite]` → shows `5 (Inheritor's Smite)` on the card.
  - a damage formula `8d6` becomes `8d6[Maneuver Name]` → shows `8d6 (Maneuver Name)`.
  - The label is **required** on attack formulas (without it, when the conditional name carries
    `[[ ]]` inline rolls, pf1 embeds the whole name as the term's flavor, the brackets nest, and the
    d20 parser crashes) and **desired** on damage formulas (so the roll shows its source). The module
    handles both; the `!/\[.*\]/` double-label guard means an already-bracketed formula is left alone.
- In the backend data the rider rides a **`rider`** field: maneuvers (`maneuver_changes.json`) and
  spells (`spell_changes.json`) both have the module append `rider` onto the conditional name, and
  the module appends the source label onto every modifier formula.

## Combat-maneuver roll forms

When a strike/boost/spell makes (or grants) a combat maneuver, write the check inline as one of
these (melee → `str`, ranged → `dex`). A bonus *type* can't ride an inline roll, so name it in text:

- **plain CMB** — the actor's own CMB, plus any flat bonus the effect grants:
  `[[ d20 + @attributes.cmb.total ]] vs CMD` (Inheritor's Smite adds its +5 → `[[ d20 + @attributes.cmb.total + 5 ]] vs CMD`).
- **skill in place of CMB** — a skill replaces the maneuver check (see the bullet above):
  `[[ d20 + @attributes.cmb.total - @abilities.<str|dex>.mod - @attributes.bab.total + @skills.<id>.mod ]] vs CMD`.
- **caster level in place of BAB** — spells like *Rock Whip* ("use your caster level in place of
  your base attack bonus"): `[[ d20 + @attributes.cmb.total - @attributes.bab.total + @spells.primary.cl.total ]] vs CMD`.

## Decision guide

| The effect is… | Encode as… |
|---|---|
| a clean flat/dice bonus to **damage** or **attack** | a real `modifiers[]` entry (`formula` PLAIN, `target`, `damageType`, `critical`) — the module adds the source label |
| a **saving throw** rider on a strike | name text + `[[ DC formula ]]`, `modifiers: []` |
| **ability damage/drain** | name text + `[[ dice ]]` (no structured ability-damage modifier exists) |
| **ignore DR/hardness, a condition, a maneuver, temp HP, forced movement, etc.** | name text + `[[ numbers ]]`, `modifiers: []` |
| **secondary damage** with no roll of its own (trail/aura/self-damage) | name text + `[[ dice ]]` (it has no modifier, so it stays in the note) |
| a **combat maneuver** (bull rush / trip / disarm / grapple …) | name text + a CMB inline roll `[[ d20 + @attributes.cmb.total … ]] vs CMD` (see *Combat-maneuver roll forms*); `modifiers: []` unless there's also a clean bonus |
| a clean bonus **AND** a save / condition / combat maneuver | **one** conditional: the bonus as a `modifiers[]` entry **plus** rider text in the name (the Inheritor's Smite pattern) |
| a whole **spell/action** that allows a save | the formal `save` block (not a conditional) |

## Authoring checklist

- **Walk the "what every conditional must describe" table** — contingency, attack boosts, damage,
  saves/DCs, range, targets, duration, secondary effects — and include every item that applies.
- **Every number in a name/rider goes in `[[ ]]`** so it renders as a clickable inline roll.
- **Never restate rolled damage in the note.** Damage that's on a `modifiers[]` entry is on the roll
  (with its auto source label); the note carries only non-damage riders and modifier-less secondary
  damage. Never put the rolled dice or a bare "deals N damage" in the toggle NAME.
- **Author plain formulas** in `modifiers[]` (`"8d6"`, `"5"`) — the module appends the `[Source]`
  label to attack *and* damage. Do not hand-bake `formula[Label]`.
- **No arbitrary length cap.** Write the full description; do not truncate to hit a character limit.
- Every conditional and modifier needs a **unique `_id`** (8+ chars; any unique string).
- `default: false` for optional strikes so they don't auto-apply; `true` only for always-relevant riders.
- Pull DCs/dice references (`@abilities.*`, `@attributes.hd.total`, `@classes.<tag>.level`,
  `@sl`/`@ablMod`/`@pow.initLevel`, …) from the **foundry-sheet-references** and **path-of-war** skills.
- `formula` in a modifier may use real dice (`2d6`); a buff `change` may not (it maximizes). When a
  strike adds rollable dice, prefer a conditional over a buff. See **foundry-sheet-references**.
