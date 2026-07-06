---
name: multi-buff-distributor
description: How to author a FoundryVTT pf1 buff that can/does affect OTHER creatures (allies, animal companions, cohorts, summons, aura recipients) so it works with this campaign's Multi-Buff Distributor + Aura Distributor macros. Use whenever a talent/feat/spell/stance grants a bonus to someone other than (or in addition to) the wielder — encode it as an inactive temp buff named "<Buff> (TAG)" with "Aura Range: N" / "onlyOthers;" description markers, NOT as a weapon conditional. Covers the (TAG) naming convention (UNAMED for the uploadable palette actor; first-5-letters-of-name for generated NPCs), the aura-range/onlyOthers markers, the pf1 temp-buff item shape, and where it plugs into the generator + palette.
---

# Multi-Buff Distributor — affects-others buffs

This campaign drives shared/aura buffs with two FoundryVTT macros (source:
<https://github.com/The-Data-is-a-lie/Foundry-VTT-Multi-Buff-Distributer-Macro>):

- **`multi-buff-distributor.js`** (the picker) — groups a source token's buffs by a trailing
  **`(TAG)`** and distributes them to matching/targeted tokens. It reads `TAG_RE = /\([A-Z]+\)/`
  (uppercase letters in parens), strips the trailing tag (`/\s*\([^)]*\)\s*$/`), and matches the
  cleaned buff name against token names. Buffs whose name contains **"counter"** are excluded.
- **`aura-distributor.js`** (the range backend) — reads the buff **description** for
  `Aura Range: N` and applies the buff to tokens within `N` feet; `onlyothers` (anywhere in the
  name/description) suppresses the buff on the caster (a negating "Host Counter" is placed on the
  source so others still get it).

## When to use this (vs. a weapon conditional)

Route the effect to an **affects-others temp buff** — never a weapon `action.conditionals[]` — when the
bonus lands on a creature **other than** the wielder's own attack:

- an **animal companion / mount / cohort / eidolon / summon** gets the bonus (its own attacks, not yours);
- an **ally aura** ("allies within 30 ft gain +1 morale to attack");
- an **enemy-debuff aura** placed as an emanation (use `onlyOthers;`);
- any "grant a target/ally the ability to …" effect.

(A bonus to *your own* to-hit/damage is a weapon conditional or self-buff — see
[`foundry-conditionals`](../foundry-conditionals/SKILL.md) and
[`spheres_conditional_decision_rules.md`](../../../docs/spheres_conditional_decision_rules.md). A
static self-only bonus is a plain buff with no `(TAG)`.)

## Buff name format

```
<Buff Name> (TAG)
```

- `(TAG)` is **uppercase letters only** (`[A-Z]+`), at the **end** of the name, and identifies the
  **source actor** so the distributor can group that actor's shareable buffs.
- **Derive the TAG:**
  - **Uploadable palette / template actor** (no meaningful character name): use **`(UNAMED)`**.
  - **Generated NPCs:** the **first 5 letters of the character's name, uppercased, stopping at the
    first non-letter (space, apostrophe, digit, hyphen)**. Take fewer if the name is shorter.
    Algorithm: `re.match(r"[A-Za-z]{1,5}", name).group().upper()` (fallback `UNAMED` if empty).
    Examples: `Alexander the Great → ALEXA`, `Bob → BOB`, `Za'thak → ZA`, `T'char → T`.
- Do **not** put `counter` in the name (the picker drops those).

## Description markers (in the buff's description HTML)

| Marker | Syntax | Effect |
|---|---|---|
| Aura range | `Aura Range: 30` | distribute to tokens within 30 ft (integer feet; the parser reads `/Aura\s*Range\s*:\s*(\d+)/i`, so `AuraRange: 30` also works) |
| Caster excluded | `onlyOthers;` | the caster does **not** receive the buff (enemy-debuff auras, ally-only buffs) |

Put these near the **top** of the description (that's where this repo's tooling already writes them —
see the PoW `stance_auras.json` path). Omit `Aura Range` for a buff that is hand-distributed to
specific targets rather than an emanation.

## pf1 temp-buff item shape

An inactive `buff` item, identical to the stance/aura buffs the palette already emits
(`make_buff` in `build_pow_template_actor.py`; `addStanceBuffs` in the module):

```jsonc
{
  "name": "Inspiring Command (UNAMED)",
  "type": "buff",
  "img": "icons/svg/aura.svg",
  "system": {
    "description": { "value": "<p>Aura Range: 30</p><p>Allies within range gain +[[1]] morale to attack.</p>" },
    "subType": "temp",
    "active": false,
    "changes": [ { "formula": "1", "target": "attack", "type": "morale", "operator": "add", "priority": 0, "value": 0 } ],
    "contextNotes": [],
    "duration": { "value": "", "units": "" }
  }
}
```

- **`changes`** carry the mechanical bonus (buff changes are evaluated **maximized** — no rollable
  dice; use a flat/`@`-scaled formula, or put dice in the description as a `[[ ]]` note).
- Keep it **inactive** (`active: false`) — the player toggles it and the macro distributes it.
- Text numbers use `[[ ]]` inline rolls, same house convention as conditionals.

## Where it plugs into this repo

- **Curation data** (`_spheres_generator/curated_*/…`): an affects-others talent is authored as a
  `buff` entry — `{"buff": {"aura_range": 30, "only_others": false, "changes": [...],
  "contextNotes": [...], "description": "..."}}` — NOT `{modifiers,rider}` and NOT `skip`.
- **Promote** routes `buff` entries to the module's affects-others buff table; the **palette builder**
  emits them as temp buffs tagged **`(UNAMED)`**; the **generator** emits them tagged with the NPC's
  derived tag and stamps `Aura Range` / `onlyOthers;` from the data.
- Existing **PoW aura stances** already use the `Aura Range:` / `onlyOthers;` markers
  (`stance_auras.json`, `_aura_marker_html`); they should also carry the `(TAG)` suffix under this
  convention.
- **Buff spells** are also generated this way: `Backend/scripts/build_spell_buffs.py` parses
  `every_spell.json` → `spell_buffs.json` ({Spell: {changes, aura_range, only_others, description}});
  the palette emits every one as `<Spell> (UNAMED)`, and `addSpellBuffs()` (module) emits `<Spell>
  (TAG)` for each spell the NPC knows. Personal/Self spells are included (hand-distributed).

## Gotchas

- TAG must be `[A-Z]+` — uppercase, letters only. A tag with a digit or lowercase won't match `TAG_RE`.
- The picker matches the cleaned buff name against **token names** too; keep buff names distinct from
  token names unless you intend a name-match.
- Range is integer feet; a scaling range must be pre-resolved to a number when the buff is built
  (the class-less palette reads level-scaled formulas as 0 — bake a concrete number for the palette).
