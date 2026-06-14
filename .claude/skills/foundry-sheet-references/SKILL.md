---
name: foundry-sheet-references
description: How to reference a FoundryVTT pf1 actor's own data from inside formulas and text — roll-data @ paths (e.g. @abilities.con.mod in a buff change, @attributes.hd.total, @classes.<tag>.level, @spells.primary.cl.total) and resource pools/charges (@resources.<tag>.value/.max). Use when writing buff/change formulas, attack or conditional damage formulas, [[ ]] inline rolls, save DCs, or when defining or spending a resource pool (charges, ki, a warleader/initiation pool) on an item.
---

# FoundryVTT pf1 — referencing actor data (`@…` roll data + resources)

How to pull a number off the character sheet from inside a formula or a piece of text. Every
example below is verbatim from a real actor (Dar'geth, Pascal Warner, Lok'Nathal).

## What roll data is

Anywhere the pf1 system evaluates a **formula** or an inline roll, the string `@path.to.value`
is replaced by that value from the actor's roll data. The same `@…` syntax works in:

- buff / feature `system.changes[].formula` (always-on bonuses),
- an action's damage parts and `save.dc`,
- conditional `modifiers[].formula` (per-roll bonuses — see the **foundry-conditionals** skill),
- and `[[ … ]]` **inline rolls** embedded in any item name, conditional name, or description
  (Foundry renders these as clickable dice on the chat card).

`@` always refers to the **actor that owns the item**. Build the path by mirroring the data
model (`actor.system.abilities.con.mod` → `@abilities.con.mod`).

## Reference catalog

Each row is a real path with a verbatim example of where it appeared.

### Abilities — `@abilities.<abbr>.<field>`
`<abbr>` = `str|dex|con|int|wis|cha`. `<field>` = `mod` (modifier) or `total` (the score).

| Path | Real example |
|---|---|
| `@abilities.con.mod` | buff formula `"@abilities.con.mod"` |
| `@abilities.con.total` | HP formula `"2*(@abilities.con.total) + 4*(@attributes.hd.total )"` |
| `@abilities.wis.mod` | aura formula `"@abilities.wis.mod + @classes.mythicGuardian.level"` |
| `@abilities.int.mod` | `"-(@abilities.int.mod)*(@attributes.hd.total)"` |

### Attributes — `@attributes.<x>.total` (combat / movement / defense)

| Path | Meaning / example |
|---|---|
| `@attributes.hd.total` | total Hit Dice — `"(@attributes.hd.total + 5)+ 10 + ( @details.mythicTier)"` |
| `@attributes.bab.total` | base attack bonus — `"@attributes.bab.total + @abilities.con.mod"` |
| `@attributes.cmb.total` | combat maneuver bonus — `"[[ @attributes.cmb.total ]] Disarm Check"` |
| `@attributes.ac.natural.total` | natural-armor AC bonus |
| `@attributes.speed.land.total`, `@attributes.speed.fly.total` | movement, e.g. `"floor(@attributes.speed.fly.total/10)-1"` |
| `@attributes.encumbrance.level` | 0/1/2 load — `"@armor.type < 1 && @attributes.encumbrance.level < 1 ? 1 : 0"` |

### Classes & character level — `@classes.<tag>.level`
`<tag>` is the **class item's `system.tag`**, NOT its display name. Multiclass and homebrew
classes each get their own tag: `fighter`, `monk`, `monkUnchained`, `sageSpheres`,
`mythicGuardian`, `mythicChampion`, etc. Example: `"1 + floor((@classes.monk.level + 2) / 4)"`.
Also `@details.mythicTier` for mythic tier.

### Skills — `@skills.<abbr>.<field>`
`<field>` = `rank` or `mod`. Example: `"4 + if(gte(@skills.acr.rank, 3), 2)"`. Subskills nest:
`@skills.pro.subSkills.pro4.mod` (Profession #4's modifier).

### Spellcasting — `@spells.<book>.cl.total`
Caster level of a spellbook, e.g. `"12d6 + @spells.primary.cl.total"`.

### Armor / AC checks (for conditional bonuses)
`@armor.type`, `@shield.type` (0 = none/light … higher = heavier), `@ac.natural.total`.
Used in monk-style ternaries: `"@armor.type>=2 ? 1 : 0"`.

### Custom / Path-of-War shorthands
`@sl` (spell/maneuver level), `@ablMod` (the feature's governing ability mod), `@cl` (class
level), `@formulaicAttack`, and `@pow.initLevel` (initiator level, for stance scaling). The PoW
base save DC is `"10 + @sl + @ablMod"`. See the **path-of-war** skill for the full set.

## Resource pools & charges

A **resource pool** (`@resources.<tag>.value` / `.max`) is the right tool for anything that is
*spent and tracked* — ki, a warleader/initiation pool, AoO charges, per-day uses.

**A pool is created by an item, not declared on the actor.** Give the item a `system.tag`; the
system then exposes a matching `@resources.<tag>` entry. Make it a real countable pool by setting
its `uses` block. Verbatim anchor from Pascal Warner (Weapon Training):

```jsonc
"tag": "classFeat_weaponTraining",
"uses": { "value": 2, "per": "charges", "maxFormula": "2", "rechargeFormula": "" }
// → readable anywhere as @resources.classFeat_weaponTraining.value  and  .max
```

So `tag` = the pool key, `uses.maxFormula` = pool size (a formula, can use `@…`), `uses.value` =
current charges, `uses.per: "charges"` = a generic pool (vs `"day"`, etc.).

**Spending / reading the pool:**

- The *granting* item self-deducts when used (the action's charge cost / `autoDeductChargesCost`).
- *Any other* item reads the pool inside a formula or `[[ ]]` inline roll. Real examples:
  - Dar'geth: `"[[@resources.feat_combatReflexes.value]] AoO available."` (reminder text)
  - Pascal: `"+ [[ @resources.warps.max ]] warps bonus"` (inline roll in a name)
  - Lok'Nathal: `"(@resources.chiGongDamage.max)d6"` (pool size scales a damage formula)

That last pattern — `@resources.<pool>.value`/`.max` driving a roll — is exactly the
"spend from / scale by the pool" case (e.g. `@resources.warleader.value`).

## Formula syntax notes

- Math/functions available in formulas and inline rolls: `floor() ceil() round() abs()
  min() max()`, the conditionals `if(cond, then)`, `ifelse(cond, a, b)`, comparators
  `gte() lte() eq()`, and JS-style ternaries `cond ? a : b`.
- **Dice live in conditionals/attacks, not buffs.** A buff `system.changes[].formula` is
  evaluated **once and maximized to a flat number**, so `2d6` in a buff becomes a static `12`.
  Put rollable dice on an attack damage part or a conditional modifier instead.
- pf1 v11+ dropped raw JS ternaries in some *change* contexts — prefer `ifelse()/gte()`. See the
  **path-of-war** skill and the `foundry-v13-pf1-formula-syntax` note; converter at
  `Backend/scripts/fix_foundry_change_formulas.py`.

## Where to put each reference — quick map

| You want… | Put it in… |
|---|---|
| an always-on stat bonus | a buff/feature `system.changes[]` (flat number, no dice) |
| a per-roll, toggleable bonus | an action **conditional** (`foundry-conditionals` skill) |
| a save DC, dice, or rules reminder shown on the card | a `[[ … ]]` inline roll inside a name / note |
| something spent & counted | a **resource pool** (`tag` + `uses`), read via `@resources.<tag>.*` |
