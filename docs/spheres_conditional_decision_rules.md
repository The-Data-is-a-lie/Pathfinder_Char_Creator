# Spheres (of Power / Might) conditional encoding — decision rules

When a Spheres **talent** becomes a per-roll **conditional toggle** on a weapon's (or the Destructive
Blast's) attack action (`action.conditionals[]`), its effect is encoded the same two ways Path of War
maneuvers are (see [`pow_conditional_decision_rules.md`](pow_conditional_decision_rules.md) and the
[`foundry-conditionals`](../.claude/skills/foundry-conditionals/SKILL.md) skill):

- a **structured modifier** — `modifiers[] = {formula, target, subTarget, type, damageType, critical}`
  — for clean bonuses to *this attack's* damage or to-hit; or
- **inline `[[ ]]` text in the conditional `name`** — for everything the pf1 weapon-conditional model
  has no structured slot for (saves, DCs, conditions, durations, ability damage, bleed, ranges, …).

The generator (`addSphereTalentConditionals` in the module's `modify-abilities.js`), the palette
builder (`build_pow_template_actor.py --spheres`), and the promote validator all enforce it.

## File map (don't confuse the two "changes" files)

| File | Holds | Consumed by |
|---|---|---|
| `Backend/json/class_data/spheres/combat_talent_changes.json` | **PASSIVE** Might self-buffs (static `changes`/`contextNotes` on the talent item) | `_talent_item()` in `spheres.py` → the Foundry **Changes tab** |
| `<module>/…/combat_talent_conditionals.json` | **PER-ROLL** Might talent conditionals `{Sphere:{Talent:{modifiers,rider}}}` | `addSphereTalentConditionals()` → weapon attack toggles |
| `<module>/…/magic_talent_conditionals.json` | **PER-ROLL** Power talent conditionals (Destruction on the blast; others on the weapon) | `addSphereTalentConditionals()` |

Authoring/curation lives in the gitignored `Backend/scripts/_spheres_generator/`; the draft seeds +
worklist slicer is `Backend/scripts/build_talent_conditionals.py`; `promote_talents_to_module.py`
merges the curated per-sphere files into the three files above.

## What becomes a conditional (the coverage rule)

- **Strikes are always conditionals.** A "strike" talent applies its effect when you make an attack, so
  it maps directly onto a weapon/blast conditional — regardless of sphere. Detect by the talent **name**
  (`… Strike`) or the benefit phrasing: *"make a (single) weapon attack in conjunction with …"*,
  *"deliver … through a (melee/ranged) touch attack"*, *"as part of an attack"*, *"when you hit/strike/
  damage a target"*, *"make a melee/ranged/touch attack"*. Examples: Destruction *Energy Strike*, Death
  *Vampiric Strike*, Enhancement *Crippling Strike*.
- **Soft rule:** any base ability or talent that deals **single-target damage** or inflicts a
  **debuff / condition** on a target is *likely* a conditional (encode the damage as a modifier, the
  save/condition as a rider). Cast the net wide — it is better to author a togglable conditional the
  player can ignore than to bury an on-hit effect as description-only. A debuff need not *look*
  on-hit: a poison, a coating, or any targeted penalty can ride a thrown/ranged/feat-enabled attack.
- **Self-buffs that raise your attack or damage ARE conditionals** — a talent that grants you a to-hit
  or damage bonus (an energy-enhanced weapon, extra dice, a bleed rider, a crit-confirm bonus) becomes
  a default-off `modifiers[]` toggle (damage → `target:"damage"`, to-hit → `target:"attack"`; use a
  rider for anything unquantifiable like *keen*). Self-buffs that don't touch a combat roll (temp HP,
  movement, defenses) stay description-only.
- **An enemy AC-reduction debuff → an ATTACK modifier + rider** (the Inheritor's Smite pattern): a
  "-N to the target's AC" effect is modeled as `target:"attack"` `+N` (lowering their AC ≈ raising your
  to-hit) with the rider *explaining* it — "the target's AC is reduced by `[[N]]` (this attack bonus
  reflects that lowered AC; it applies to all attackers)". Same for "attackers gain +N against it".
  (A debuff to the enemy's *own* attacks/saves stays a rider — it isn't your to-hit.)
- **Stays description-only** (`skip`, or a Might `passive` if it's a static self-bonus): pure
  battlefield control / zone / wall effects, area effects with no single-target attack, buffs on allies
  or self, movement/utility/skill/crafting talents, and talents whose effect lands on a *separate*
  creature (a summon, cohort, companion) rather than the target of your attack.
- `build_talent_conditionals.py --dump-worklist` tags each talent with a `_hint`
  (`strike` / `damage` / `debuff` / `maybe-skip`) to speed triage — the hint is advisory, not binding.

## The decision table

| The effect is… | Encode as… |
|---|---|
| **On-hit HP damage** (extra dice / flat) added to the strike or blast | **damage modifier** — `target:"damage"`, `subTarget:"allDamage"`, plain `formula` (the module appends `[Talent]`), `critical:"nonCrit"` for dice (extra dice don't multiply on a crit), `"normal"` for a flat/`@`-only bonus |
| **Bonus to *this* attack's to-hit** | **attack modifier** — `target:"attack"`, `subTarget:"allAttack"`, `damageType:[]` |
| **Precision damage** (Fencing, Barrage, Scoundrel …) | damage modifier, `damageType:[]`, `critical:"nonCrit"`; keep the target-state contingency ("vs flat-footed/flanked/Dex-denied") + the word "precision" in the rider |
| **Bleed damage** (Duelist, Open Hand …) | **rider** text `[[NdM]] bleed damage` — bleed is ongoing, never a modifier |
| **Save + DC** | rider — Power `Reflex/Fortitude/Will Save [[ 10 + floor(@spheres.cl.total / 2) + @spheres.cam ]]`; Might `… [[ 10 + floor(@attributes.bab.total / 2) + @spheres.pam ]]` |
| **Conditions, durations, ranges, # targets, ability damage/drain** | rider text, every number `[[ ]]` |
| **Contingency / cost** — "expend martial focus", "special attack action", "attack action or AoO only", "spend [[1]] spell point", target-state | rider, stated **first** |
| **Blast damage-type swap** (Fire/Frost/Acid Blast …) | rider only (`modifiers:[]`): "blast deals fire damage instead of bludgeoning; …save/condition" — the base dice live on the Destructive Blast item |
| **Blast shape** (cone/line/wall …) | rider describing the new delivery (range, area, targets) |
| **Pure static self-bonus** (always-on AC/save/skill bonus) | a **passive** `{changes,contextNotes}` (Might only) → the backend passives file, NOT a conditional |
| **Utility / out-of-combat** (crafting, movement, skills) | **skip** — description-only, no conditional |

## Scaling shapes (computed dice count in parentheses)

- BAB: `"1d6 + (floor(@attributes.bab.total / 5))d6"` (Fatal Thrust, +1d6 / 5 BAB); flat `"1 + floor(@attributes.bab.total / K)"`.
- Caster level, odd: `"(ceil(@spheres.cl.total / 2))d6"` (destructive blast, 1d6 / odd CL).
- Caster level, each: `"(@spheres.cl.total)d6"`.

## Roll-data tokens & where they resolve

Author with the **native pf1spheres tokens** — `@spheres.cl.total`, `@spheres.cam` (casting ability
mod), `@spheres.pam` (practitioner mod), plus `@attributes.bab.total` / `@abilities.*.mod`. Never use
the Path-of-War tokens `@INITMOD` / `@SKILLCHECK` / `@ATTACKCHECK` (the promote check rejects them).

- **Generated NPCs are dabblers** (Basic Magic Training = effective caster level 1). The module's
  `subSpheres()` substitutes to concrete forms at attach time: `@spheres.cl.total → 1`,
  `@spheres.cam → @abilities.<cam>.mod`, `@spheres.pam → @abilities.<pam>.mod` (cam = the casting
  tradition's ability; pam = wis). The actor is stamped `flags.pf1spheres.castingAbility/
  practitionerAbility` and the "Spheres Casting" feat carries a `spherecl` +1 change so the pf1spheres
  tab shows CL 1.
- **The palette keeps the native tokens** so a conditional copied onto a real spherecasting PC scales
  with that PC's CL/CAM/PAM. The class-less template reads CL 0, so the palette ships a
  **"Palette: Sphere CL 10"** buff (a `spherecl` change) to toggle for testing.

## The Destructive Blast item

The Destruction sphere's base ability is a ranged/melee **touch** attack, so it can't live as a weapon
conditional — the generator/palette synthesize a dedicated **attack item** whose damage part is
`(ceil(@spheres.cl.total / 2))d6` bludgeoning (1d6 for a CL-1 dabbler). Blast-**type** talents (which
swap the damage type + add a save/condition) and blast-**shape** talents attach to *that* item as
default-off conditionals. The built-in **Empowered Blast** toggle (`(floor(@spheres.cl.total/2))d6`,
`critical:"nonCrit"`) is the "spend 1 spell point → one die per caster level" upgrade.

## Notes & limits

- **Built-in pf1 damage types** (anything else is best-effort + a text label): `bludgeoning · piercing ·
  slashing · fire · cold · acid · electricity · sonic · force · negative · positive · untyped`.
- A modifier `formula` is **plain** (no `[[ ]]`, no hand-baked `[label]`); the module labels it.
- **Martial focus** is text-only in v1 (no `@resources` pool for it yet) — state "expend martial focus"
  in the rider; the player tracks it manually.
