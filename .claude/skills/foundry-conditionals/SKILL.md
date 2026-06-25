---
name: foundry-conditionals
description: How to author per-roll conditional modifiers and rider effects on a FoundryVTT pf1 attack/strike — the action.conditionals[] structure, plus the house convention for tagging non-damage riders. Use when an attack forces a saving throw, deals ability damage/drain, or has another important non-damage effect: add it as a conditional whose name carries the rule, with the relevant numbers (save DCs, dice) written in [[ ]] inline rolls. Modeled on Lok'Nathal's Feasting Wraith Strike / Headstone Breaking Strike.
---

# FoundryVTT pf1 — conditionals & rider effects on attacks

How to attach optional, per-roll effects to an attack/strike: clean damage/attack bonuses go in
structured **conditional modifiers**; saves, ability damage, and other rules riders go in the
conditional's **name** with the numbers in `[[ ]]`. For the `@…` references used inside formulas
and brackets, see the **foundry-sheet-references** skill.

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

**2. Conditional-name convention** — the **house style for weapon strikes**. Each strike/boost is a
conditional on the weapon's attack action; the *rule text and numbers* go in the conditional
`name`, with dice and save DCs wrapped in `[[ ]]` so they render as clickable inline rolls. This is
the preferred pattern for hand-built martial characters (Lok'Nathal). Details below.

## `conditionals[]` schema

An action carries `action.conditionals` = an array of conditional objects:

```jsonc
{
  "_id": "zp3qXHs3NpTr3nCl",     // unique id
  "name": "Ki Damage",            // toggle label; MAY embed [[ ]] inline rolls
  "default": true,                // true = on by default; false = opt-in toggle
  "modifiers": [ … ]              // structured modifiers — MAY be empty
}
```

Each entry in `modifiers`:

```jsonc
{
  "_id": "4KpxXXA5mx1JwWDq",
  "formula": "(@abilities.con.mod) + 3",  // flat or dice; keeps real dice like 2d6
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
  damage rider.
- **Darkened Axe Style** — `formula: "2d8"`, `damageType: ["negative"]`, `default: false`. An
  opt-in dice rider (`2d8` stays as real dice — unlike a buff change, which would maximize to 16).
- **Vital Strike** — `formula: "+2d6"`, `critical: "nonCrit"`. Extra dice that do **not** multiply
  on a crit.

## The rider rule (the important part)

> If a strike **forces a saving throw**, **deals ability damage/drain**, or has **another important
> non-damage effect** (ignores DR, inflicts a condition, grants a maneuver check, etc.), put it in
> the conditional **name** and write the relevant numbers in `[[ ]]`. Leave `modifiers: []` empty
> when the effect isn't a clean damage/attack number.

Why: pf1 has no structured "ability-damage" or "forces-a-save-and-halves" modifier on a weapon
conditional, so those effects are **text the GM reads**, with the dice/DC made rollable via `[[ ]]`.

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
    { "formula": "5[Inheritor's Smite]", "target": "attack", "subTarget": "allAttack",
      "type": "sacred", "damageType": [], "critical": "normal" }
  ]
}
```

- The **bonus** is a real modifier (`target:"attack"`); the **bull rush** is rider text with its
  roll in `[[ ]]`. Both live in one conditional.
- **`[label]` on an attack formula:** when the conditional name contains `[[ ]]` inline rolls, an
  attack modifier's formula must end in a `[label]` (e.g. `5[Inheritor's Smite]`) — otherwise pf1
  embeds the conditional name as the term's flavor, the brackets nest, and the d20 parser crashes.
  The generator module **auto-appends** this label at attach time, so author **plain** formulas
  (`"5"`) in the data. (Damage modifiers don't need it.)
- In the backend data the rider rides a **`rider`** field: maneuvers (`maneuver_changes.json`) and
  spells (`spell_changes.json`) both have the module append `rider` onto the conditional name.

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
| a clean flat/dice bonus to **damage** or **attack** | a real `modifiers[]` entry (`formula`, `target`, `damageType`, `critical`) |
| a **saving throw** rider on a strike | name text + `[[ DC formula ]]`, `modifiers: []` |
| **ability damage/drain** | name text + `[[ dice ]]` (no structured ability-damage modifier exists) |
| **ignore DR/hardness, a condition, a maneuver, temp HP, etc.** | name text + `[[ numbers ]]`, `modifiers: []` |
| a **combat maneuver** (bull rush / trip / disarm / grapple …) | name text + a CMB inline roll `[[ d20 + @attributes.cmb.total … ]] vs CMD` (see *Combat-maneuver roll forms*); `modifiers: []` unless there's also a clean bonus |
| a clean bonus **AND** a save / condition / combat maneuver | **one** conditional: the bonus as a `modifiers[]` entry **plus** rider text in the name (the Inheritor's Smite pattern) |
| a whole **spell/action** that allows a save | the formal `save` block (not a conditional) |

## Authoring checklist

- Every conditional and modifier needs a **unique `_id`** (8+ chars; any unique string).
- `default: false` for optional strikes so they don't auto-apply; `true` only for always-relevant riders.
- Pull DCs/dice references (`@abilities.*`, `@attributes.hd.total`, `@classes.<tag>.level`, …) from
  the **foundry-sheet-references** skill.
- Keep the `[[ ]]` brackets — they make the save DC / damage a clickable inline roll on the card.
- `formula` in a modifier may use real dice (`2d6`); a buff `change` may not (it maximizes). When a
  strike adds rollable dice, prefer a conditional over a buff. See **foundry-sheet-references**.
