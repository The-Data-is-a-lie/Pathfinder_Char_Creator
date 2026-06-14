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

## Decision guide

| The effect is… | Encode as… |
|---|---|
| a clean flat/dice bonus to **damage** or **attack** | a real `modifiers[]` entry (`formula`, `target`, `damageType`, `critical`) |
| a **saving throw** rider on a strike | name text + `[[ DC formula ]]`, `modifiers: []` |
| **ability damage/drain** | name text + `[[ dice ]]` (no structured ability-damage modifier exists) |
| **ignore DR/hardness, a condition, a maneuver, temp HP, etc.** | name text + `[[ numbers ]]`, `modifiers: []` |
| a whole **spell/action** that allows a save | the formal `save` block (not a conditional) |

## Authoring checklist

- Every conditional and modifier needs a **unique `_id`** (8+ chars; any unique string).
- `default: false` for optional strikes so they don't auto-apply; `true` only for always-relevant riders.
- Pull DCs/dice references (`@abilities.*`, `@attributes.hd.total`, `@classes.<tag>.level`, …) from
  the **foundry-sheet-references** skill.
- Keep the `[[ ]]` brackets — they make the save DC / damage a clickable inline roll on the card.
- `formula` in a modifier may use real dice (`2d6`); a buff `change` may not (it maximizes). When a
  strike adds rollable dice, prefer a conditional over a buff. See **foundry-sheet-references**.
