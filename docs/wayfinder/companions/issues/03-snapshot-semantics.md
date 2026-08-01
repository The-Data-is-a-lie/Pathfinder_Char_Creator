# 03 — What exactly is a companion snapshot at master level N?

Type: grilling
Status: resolved
Blocked by: —
Map: [Bonded creatures](../map.md)

## Question

This is a one-shot NPC generator, not a levelling tracker, so a companion is a **static snapshot**.
Lock what that snapshot contains.

Specifically:

- Each species in `Backend/json/animal_choices.json` has a `"<N>th-level advancement"` block whose
  trigger level varies per species (allosaurus at 7th, amargasaurus at 4th). **Nothing in the code
  checks whether the companion has crossed it**, so the deltas are never merged. What is the merge
  rule — replace, add, or per-field?
- Which level drives the lookup? Today it is the raw druid class level, which breaks on multiclass
  and would `KeyError` past the table's end.
- Do house rules touch the companion the way they touch the PC (maximised HP, the skill-rank floor,
  the feat economy)? See `docs/homebrew_rules.md` and the OKF `pathfinder` bundle.
- What happens to a companion whose effective level is 0 or whose master multiclassed out?

## Answer

**Resolved 2026-08-01.** A companion is a **static snapshot at the master's resolved effective
level** — the same posture the generator already takes for spells known, maneuvers readied and
manifester level. Nothing tracks levelling.

The unexpected part: the snapshot could not be specified without first admitting that
`animal_choices.json` **cannot be merged as written**. That repair is now in scope for this effort
(decision D5), not a backlog item.

### The advancement merge rule

The shape is tractable. Exactly **one** advancement block per species (180 of 182), triggering at
level **4** (93 species), **7** (85) or **9** (2). Species counts: `normal` 145, `plant` 14,
`vermin` 23 — keyed lowercase and comma-inverted (`"ant, giant"`).

Trigger when **effective level ≥ the block's trigger level**. Then, per field:

- `size`, `attack`, `speed` → **replace** (`ac` aside, every observed value is absolute — a new size
  category, a new attack routine, a new speed or movement mode)
- `ac` — always the string `"+N natural armor"` — and **ability scores** → **add**
- `special qualities`, `special attacks`, and one-off keys (`sudden charge (ex)`, `bonus feat`,
  `climb`, `fly`, …) → **append**

This is not a design choice so much as a reading of the data: the field-by-field rule is whatever
makes the 182 species come out as PF1e describes them.

### The data defect that forced D5

`animal_choices.json` has three problems, and the first is not cosmetic:

- **Sign loss.** Of 120 bare-int `dex` values in advancement blocks, **109 sit on a size increase**,
  where PF1e mandates the fixed package Str +8 / Dex −2 / Con +4 / natural armor +2. Sixteen rows in
  the identical situation record `-2` correctly — which is the proof, not a guess: `"+8"` and `"+4"`
  survived the original scrape as strings, and `-2` did not survive as an int. Merging as written
  inflates every advanced companion by **+4 Dex → +2 AC, +2 Ref, +2 initiative**. Allosaurus is the
  visible case: medium → large with `"dex": 2`.
- **Key drift.** `ability_scores` (×14) and `special_attacks` (×8) shadow the spaced spellings, so a
  lookup on `"ability scores"` silently misses those species — a silent-drop bug of exactly the kind
  ticket 01 gates against on the rendering side.
- **Field bleed.** Three ability-score slots hold `'medium'`, `'40 ft. '`, `'bite (1d6)'`.

Repair is **scripted and narrow** (`repair_animal_choices.py`) and backed by a validator
(`validate_companion_data.py`) asserting that every size-up row matches the PF1e package and that no
bare-int ability value survives. Hand-editing 109 rows is how this defect got here.

### Which level drives the lookup

The **resolved effective level** from [ticket 05](05-master-class-coverage.md), never the raw class
level the code reads today (`animal_companions.py:20`). The current lookup breaks on multiclass and
ignores every non-druid grantor. The chassis table in `animal_companion.json` runs to level **40**,
so the feared `KeyError` past level 20 does not actually fire — but the value it returns is still
wrong whenever anything other than a single-classed druid is involved.

### House rules

**Yes for HP and skill ranks, no for feats.** Maximised HP and the 2→4 skill-rank floor live in
`hp_rolls.py` / `skill_ranks.py` and are already class-name-agnostic; a companion is a creature at
the table like any other, and it should get the campaign's HP treatment. The **feat economy does
not** transfer — a companion's feat count is the chassis row's own `feats` value, which is why
`animal_feats()` reading a hard-coded ladder instead of that field is a bug (decision D8) rather
than a house-rule question.

### Degenerate cases

- **Effective level 0, or below the grantor's threshold** → **no entry at all**. Not a level-1
  companion. A paladin 3 has no mount because a paladin 3 has no Divine Bond.
- **Master multiclassed out** → the companion stays at the granting class's level, because that is
  what the effective-level expression reads. A druid 5 / fighter 10 has a 5th-level companion.
- **Master died / companion released** → out of scope; this is a one-shot generator.
