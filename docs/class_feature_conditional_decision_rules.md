# Class-feature & feat conditional encoding — decision rules

When a **class-choice power** (rage power, magus arcana, ki power, hex, rogue/ninja/slayer talent, …)
or an **active feat** becomes a per-roll **conditional toggle** on a weapon's attack action
(`action.conditionals[]`), it is encoded exactly the way Path of War maneuvers and Spheres talents
are — see [`pow_conditional_decision_rules.md`](pow_conditional_decision_rules.md) and
[`spheres_conditional_decision_rules.md`](spheres_conditional_decision_rules.md):

- a **structured modifier** — `modifiers[] = {formula, target, subTarget, type, damageType, critical}`
  — for clean bonuses to *this attack's* damage or to-hit; or
- **inline `[[ ]]` text in the conditional `name`** — for everything the pf1 weapon-conditional model
  has no structured slot for (saves, DCs, conditions, durations, ability damage, bleed, ranges, …),
  written as the six labeled clauses `Cost: …; Activation: …; Range: …; Save: …; Effect: …` built by
  `Backend/scripts/conditional_clauses.py`.

Candidates are sliced into worklists by
[`Backend/scripts/build_conditional_candidates.py`](../Backend/scripts/build_conditional_candidates.py);
the readable list is [`conditional_candidates.md`](conditional_candidates.md).

## What becomes a conditional

Author it when the power changes **a roll you are about to make**: extra damage dice on a hit, an
attack or damage bonus you switch on, a rider the target must save against, bleed, a crit effect, a
combat-maneuver bonus. Skip it (mark `"skip": "<why>"` in the worklist) when the power is:

- **passive and always-on** — that is a `change` on the class-feature item, not a toggle. For feats
  this is the split between `feat_changes.json` (always-on) and `feat_conditionals.json` (toggle);
  authoring an always-on bonus as a toggle **double-applies** it.
- **a bonus feat grant** — the granted feat is the real candidate; these are tagged `bonus_feat`.
- **pure utility** — skills, movement, social, out-of-combat.
- **already automated by Foundry's compendium** — the report's closing table lists them; a compendium
  `change` is always-on, so a toggle on top stacks. Read both texts before authoring.

## Touch attacks and other self-contained attacks ARE conditionals

A power that delivers its own melee/ranged touch attack — an oracle's *touch of flame*, an
alchemist's bomb, a magus's pool strike — is authored, not skipped. It follows the same pattern the
applier already uses for Bucket-B touch spells (Shocking Grasp, Scorching Ray): a toggle whose
`modifiers[]` carry the power's own damage dice, with the delivery in a `Range:` clause
(`Range: melee touch`) and the usage limit in `Cost:`. Do not skip these on the grounds that they
are "a separate attack" — the toggle is how the roll gets its dice.

What *is* skipped is a power that conjures a whole weapon or creature whose statistics live on that
new item/creature (an oracle's *wooden weapon*, any summon), and a passive clause that applies
whether or not you use the power (that belongs in `changes`).

**A granted natural attack is not a touch attack.** A power that hands you a persistent new bite,
claw or gore (*animal fury*, *lesser beast totem*) becomes its own attack item on the sheet, and a
conditional on a weapon cannot represent it — skip it, as `class_feature_effects_overrides.json`
already does by keeping those as descriptive `contextNotes`. A power that *enhances* an attack you
already have (*bloody bite*, *disemboweling tusks*, *hive totem toxicity*) is authored normally. The
test is persistence: a one-off delivery you spend an action on is a conditional; a permanent addition
to your attack routine is not.

## Save DCs

A power's own text almost never states its DC (rage powers 0 of 173, ki powers 0 of 9, hexes 6 of 59,
arcana 17 of 122), so it comes from the **pool**, using PF1's `10 + ½ class level + key ability`. The
table lives in `conditional_clauses.CLASS_FEATURE_DC` and each worklist file ships its pool's
`dc_formula` ready to paste, with a `dc_confidence`:

| confidence | meaning | pools |
|---|---|---|
| `stated` | the pool's own text spells the ability out | arcana, investigator talents, exploits, mysteries |
| `varies` | the pool mixes abilities — **check the power's own words first** | rage powers (Str, Cha, Con), hexes (holds shaman hexes, Wis not Int), rogue/ninja/slayer/vigilante talents, curses |
| `rules` | no DC in the pool text, but the ability is fixed by the governing subsystem's own rules (not a guess) | ki powers (Wis), discoveries (Int), mercy/cruelty (Cha), social talents (Cha) |
| `assumed` | no DC anywhere in the pool **and** no governing rule; the class's key ability, a genuine guess to confirm on use | *(currently none — kept for a future such pool)* |
| `none` | the pool states no DCs at all | armor training, weapon training |

When a record carries `dc_stated`, that sentence is the power's own DC — it always beats the pool
default.

## Level scaling and the sibling-class trap

Scale off `@classes.<class>.level` using the pool's canonical class (`SECTION_CLASS` in
`build_class_feature_changes.py`), which each worklist file carries as `class`.

**pf1 tags Unchained variants separately** — `Barbarian (Unchained)` → `barbarianUnchained`,
`Rogue (Unchained)` → `rogueUnchained` — and the shared pools are reached by sibling classes
(skald rage powers; ninja/slayer talents). An authored `@classes.rogue.level` therefore reaches an
Unchained Rogue *only* through the retarget in `main_test.py` (`_bucket_classes`) and in the applier
macro (`retargetClassLevel`), which swaps the token for a sibling the actor actually has and
gap-lists the row when none matches. Write the canonical token and let the retarget do its job —
do not hand-write `@classes.rogueUnchained.level`.

A power shared across pools (41 span rogue/ninja/slayer) is authored **once**: the worklist record
lists every `sections` entry, and promotion fans the identical text out to each, which is what the
curated file already looks like for `bleeding attack`.

## Landing zones (this is a live trap)

| Family | Author into | Then |
|---|---|---|
| Class features (choice pools) | `Backend/json/class_data/effects/class_feature_effects_overrides.json` | re-run `build_class_feature_changes.py` |
| Core (chassis) features | same file, `core_features` section — no scraped pool exists, so keys must match a classFeat **item name** in `every_class_feature.json` (validator-enforced; a non-matching key is a silent orphan). Labeled variants (`sneak attack (sla)`) are separate entries when progressions differ — the applier matches the raw name before the label-stripped one. | re-run `build_class_feature_changes.py` |
| Feats | `Backend/json/feats/feat_conditionals.json` (hand-curated, flat `{name: {name, default, modifiers}}`) | nothing |

Core-feature candidates come from `build_conditional_candidates.py --family core`, which sweeps the
module export (choice-pool members excluded, so the families never overlap).

**Never** edit `class_feature_effects.json` — it is generated, says so in its own `_readme`, and the
next build wipes hand edits. Curated entries drop the `review` flag and may carry `conditionals`,
`changes`/`contextNotes`, and `tagBuff`.

## Reaching a sheet

`Backend/main_test.py` exports both families (`feat_conditionals_dict`,
`class_feature_conditionals_dict`). The FoundryVTT module consumes the feat one
(`addFeatConditionals`) but **not** the class-feature one — no consumer exists — so newly curated
class features reach the **applier macro** (via `pf1-conditional-applier/build/build_data.py`, which
copies `feat_conditionals.json` and derives `class_feature_conditionals.json` from entries that are
not `review`) but not generation-time sheets until that gap is closed.

## Format checklist

- Every number in `[[ ]]`, including DCs and durations.
- Clean this-hit damage/attack → `modifiers[]` with a plain formula (the consumer appends a
  `[Source]` label); everything else → the rider text.
- `default: false` unless the effect is genuinely always-on while the power is active.
- Damage modifiers that should not multiply on a crit use `critical: "nonCrit"`; bonus weapon dice
  that should take the weapon's own type use `damageType: ["as-weapon"]`.
- A cost with no payload (`Cost: 1 ki`) is not a conditional — the same gate
  `validate_talent_conditionals.is_cost_only` applies here.
