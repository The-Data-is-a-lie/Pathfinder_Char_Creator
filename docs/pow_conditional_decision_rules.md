# Path of War conditional encoding — decision rules

When a Path of War maneuver becomes a **conditional toggle** on a weapon's attack action
(`action.conditionals[]`), every part of its effect is encoded in one of two ways:

- **a structured modifier** — `modifiers[] = {formula, target, subTarget, type, damageType, critical}`
  — for clean bonuses to *this attack's* damage or to-hit; or
- **inline `[[ ]]` text in the conditional `name`** — for everything the pf1 weapon-conditional model
  has no structured slot for (saves, skill checks, conditions, durations, healing, etc.).

This mirrors the repo's house convention in the
[`foundry-conditionals`](../.claude/skills/foundry-conditionals/SKILL.md) skill. The builder
(`Backend/scripts/build_pow_template_actor.py`) and the override-generation pass enforce it.

## The decision table

| The effect is… | Encode as… | Example |
|---|---|---|
| **Unconditional HP damage to enemies** — on-hit, **area / burst / cone / line / "to surrounding foes"**, on-collision, on-landing | **damage modifier** — `target:"damage"`, `subTarget:"allDamage"`, `formula:"NdM"` (`+ @INITMOD`/`+ @pow.initLevel` if the text adds them), `critical:"nonCrit"` (extra dice don't multiply on a crit; a *flat* / `@`-only damage modifier with no dice stays `critical:"normal"`). In the name, **keep the damage-type descriptor but drop the dice number** ("`[[16d6]]` profane damage" → "profane damage") | Apocalyptic Strike → `16d6` modifier + name "…burst; profane damage; …" · Shadow Feather → `4d6 + @INITMOD` modifier + "ranged touch attack; profane damage" |
| **Bonus to *this* attack's to-hit** | **attack modifier** — `target:"attack"`, `subTarget:"allAttack"`; the builder appends a `[label]` so an inline `[[ ]]` in the name can't crash the parser | "+2 to attack rolls" |
| **Ongoing / per-round / delayed damage dealt by the hit** | damage modifier for the dice **+** keep the duration as inline text | Void Seraph Strike → `6d6` modifier **+** "per round for `[[1d4]]` rounds" |
| **Save DC** | inline name text — `"<Type> Save [[ DC + @INITMOD ]] <result>"` | "Fortitude Save `[[ 16 + @INITMOD ]]` negates" |
| **Plain skill / demoralize / feint / opposed-vs-DC check** | inline name token **`@SKILLCHECK`** → `[[ d20 + @skills.<discipline-skill>.mod ]]` (builder fills the discipline's skill from `discipline_skills.json`). **Exception:** when a maneuver explicitly uses a *different* skill than its discipline's (e.g. Roaring Mouse's **Escape Artist**), author a **literal** `[[ d20 + @skills.<id>.mod ]]` naming that skill — see *Skill-based attack & combat-maneuver rolls* below | demoralize / feint vs Sense Motive / counter vs a fixed DC |
| **Skill as an attack / counter check** — rolled vs AC, in place of an attack roll, or opposed **vs the triggering attack roll** | inline name token **`@ATTACKCHECK`** → `[[ d20 + @skills.<discipline-skill>.mod + @attributes.attack.general ]]` (the general attack bonus makes it a fair to-hit roll). Same `@skills`/literal rules as `@SKILLCHECK`. Counters opposed vs a non-attack-roll defense (e.g. the attacker's **Perception**) stay `@SKILLCHECK` | Intimidating Force → `@ATTACKCHECK vs the triggering attack roll`; Shrug It Off; Leaden Hyena feints (vs Sense Motive **or AC**) |
| **Healing dice / temp HP** | inline `[[ ]]` text — **never** a damage modifier | Silver Crane's Mercy → "heal `[[9d6]]`" |
| **Damage to the initiator / self / recoil** | inline `[[ ]]` text (would hit the wrong creature as a modifier) | Inner Demon Strike → "`[[1d6]]` damage to initiator" |
| **Conditional / situational extra damage** ("if cursed/flanked/vs undead +`NdM`") · ongoing **bleed / per-round-maintain** extras | inline `[[ ]]` text (an always-on modifier would over-apply it) — the maneuver's PRIMARY damage is still a modifier | "if cursed extra damage increases to `[[3d6]]`" |
| **Ability damage / drain · negative levels** | inline `[[ ]]` text (no structured ability-damage modifier exists) | "Con damage `[[2d4]]`", "`[[2d4]]` negative levels" |
| **Conditions, durations, counts, miss-chance %** | inline `[[ ]]` text | "sickened `[[1d4]]` rounds", "`[[50]]`% miss chance" |
| **Non-built-in damage type** (profane, holy, unholy, divine…) | `damageType:["profane"]` best-effort (pf1 may drop unknown types) **+** keep the word "profane" as a label in the name | Black Seraph profane strikes |
| **Attack-based counter** ("make an attack at full BAB") | **no** separate modifier — the GM uses the weapon's own attack roll | Vengeful Riposte |

## Notes & limits

- **Weapon enhancement bonus** cannot be referenced from a conditional formula — there is no
  actor-scope roll-data path to the equipped weapon's `system.enh`, so inline attack/skill rolls do
  **not** include it.
- **Built-in pf1 damage types:** `bludgeoning · piercing · slashing · fire · cold · acid ·
  electricity · sonic · force · negative · positive · untyped · good · evil · lawful · chaotic`.
  Anything else (profane, etc.) is best-effort + a text label.
- **Tokens** the builder substitutes: `@INITMOD` → `@abilities.<initAttr>.mod` (the actor's PoW
  initiating ability, `wis` on the template); `@SKILLCHECK` → `[[ d20 + @skills.<id>.mod ]]` and
  `@ATTACKCHECK` → `[[ d20 + @skills.<id>.mod + @attributes.attack.general ]]` (attack/counter
  check) from `discipline_skills.json`. Damage-modifier formulas keep real dice (`6d6`) and use `@INITMOD`
  directly; buff `changes` (stances) may **not** carry dice (pf1 maximizes them) and use
  `@pow.initLevel` instead.
- **Crit multiplication:** a damage modifier whose formula carries **dice** (`1d6`, `8d6`,
  `4d6 + @INITMOD`) uses `critical:"nonCrit"` ("Non-multiplying Bonus Formula" — extra dice are not
  multiplied on a critical hit); a **flat / `@`-only** damage modifier (no dice) stays
  `critical:"normal"` and scales with the crit like static damage. Enforced in the data
  (`maneuver_changes.json`, regenerable via `Backend/scripts/fix_maneuver_crit.py`) and at draft
  build time by `_crit_for()` in `Backend/scripts/build_maneuver_changes.py`.
- **Skill-based attack & combat-maneuver rolls** — when a maneuver resolves an attack or a combat
  maneuver with a **skill**, write the roll as a literal inline `[[ ]]` formula naming that skill
  (authored in `maneuver_overrides.json` by `Backend/scripts/_pow_generator/apply_skill_rolls.py`):
  - *skill as an attack roll* (vs AC) — include misc attack bonuses:
    `[[ d20 + @attributes.attack.general + @skills.<id>.mod ]]` (e.g. Piercing Thunder *Leaping
    Strike*; Surging Shark's charge "Rush" maneuvers).
  - *skill as a counter check* (opposed **vs the triggering attack roll**) — same as an attack
    roll, it is a to-hit roll and **must include `@attributes.attack.general`**:
    `[[ d20 + @skills.<id>.mod + @attributes.attack.general ]]` (e.g. Primal Fury *Shrug It Off*;
    Iron Tortoise *The Best Weapon is Theirs*' counter clause). Leaden Hyena feints rolled "vs
    Sense Motive **or AC**" count here too. Counters opposed vs a **non-attack-roll** defense
    (e.g. Veiled Moon vs the attacker's **Perception**, or a counter vs a fixed **DC**) do **not**.
    For discipline-skill checks the canonical source uses the `@SKILLCHECK` / `@ATTACKCHECK`
    tokens; `Backend/scripts/_pow_generator/apply_attack_general.py` flips `@SKILLCHECK` →
    `@ATTACKCHECK` (and bare `[[ d20 + @skills.<id>.mod ]]` literals → the `attack.general` form)
    for every attack/counter clause, idempotently.
  - *plain combat maneuver* (no skill — the actor's own CMB, plus any flat bonus the maneuver/spell
    grants) — `[[ d20 + @attributes.cmb.total ]] vs CMD` (e.g. a +5 bonus → `[[ d20 + @attributes.cmb.total + 5 ]] vs CMD`).
  - *skill in place of CMB* (dirty trick / disarm / steal / trip / grapple, **vs CMD**) —
    `[[ d20 + @attributes.cmb.total - @abilities.<str|dex>.mod - @attributes.bab.total + @skills.<id>.mod ]] vs CMD`
    (e.g. Roaring Mouse *Tricksy Strike*; all of Tempest Gale).
  - *caster level in place of BAB* (spells like *Rock Whip*) —
    `[[ d20 + @attributes.cmb.total - @attributes.bab.total + @spells.primary.cl.total ]] vs CMD`.
  - *plain skill check vs a DC* ("DC = the target's CMD") — `[[ d20 + @skills.<id>.mod ]] vs CMD`.
- **Attack bonus + rider coexist** — a conditional may carry a structured attack/damage modifier
  **and** `[[ ]]` rider text (a save, condition, or combat maneuver) in its name at once. The module
  auto-appends a `[label]` to a bracket-less attack formula so the inline rolls don't crash the
  parser, so author plain formulas. This is the same convention spells now follow — see the
  [`foundry-conditionals`](../.claude/skills/foundry-conditionals/SKILL.md) skill (*Inheritor's
  Smite pattern*).
  - **Ability default:** melee → `@abilities.str.mod`, ranged → `@abilities.dex.mod`; this also
    chooses the **subtracted** ability in the CMB formula (ranged maneuvers like Tempest Gale's
    *Disarming Shot* subtract `dex`). "Initiation modifier" durations use `@INITMOD`.

## Stances

Stances are pf1 **buffs** (`changes` + `contextNotes`), not weapon conditionals — with two exceptions:

- **IL-scaling self-damage stances** (Savage Stance, Snapping Turtle Stance, Reaching Blade Stance,
  Stance of Aggression, Scarlet Einhander, Stance of Piercing Rays, Outer Sphere Stance, Phalanx
  Lancer). A buff `change` **maximizes dice** (1d8 → 8), so the bonus damage is emitted instead as a
  **rolled-dice weapon damage conditional**, `default: true` (on while the stance is active),
  `critical: "nonCrit"`, with the dice **count scaled off `@attributes.hd.total`** (reliable level
  proxy; `@pow.initLevel` reads 0 on class-less/non-initiator actors). Examples:
  `(ifelse(gte(@attributes.hd.total,17),3,ifelse(gte(@attributes.hd.total,9),2,1)))d8` (Savage),
  `(1 + floor((@attributes.hd.total - 1) / 8))d6` (+1d6 / 8 IL). Authored by
  `Backend/scripts/_pow_generator/apply_stance_damage.py` into `maneuver_overrides.json`; attached by
  the module's `addManeuverConditionals` stance pass (and the palette weapon) for any known stance;
  the redundant `wdamage` `contextNote` is dropped from the buff. (Note: `(expr)dN` computed dice
  counts must be verified in Foundry; `default:true` assumes the NPC is in that stance.)
- **Aura / affects-others stances** carry marker lines at the top of the buff **description** for the
  aura/buff-distributor tooling: `AuraRange: <feet-or-formula>` and, when the wielder gains nothing
  (enemy-debuff auras, ally-only buffs), `onlyOthers;`. Data lives in
  `Backend/json/class_data/path_of_war/stance_auras.json`; prepended by `_aura_prefix()` in
  `path_of_war.py` (runtime) and `_aura_marker_html()` in `build_pow_template_actor.py` (palette).
  This is data-only — no aura application is performed here, and a stance whose description is taken
  from the pf1-pow compendium at runtime will not show the markers (the palette always does).
