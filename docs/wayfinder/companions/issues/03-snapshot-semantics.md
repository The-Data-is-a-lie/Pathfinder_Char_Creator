# 03 — What exactly is a companion snapshot at master level N?

Type: grilling
Status: open
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

_Unresolved._
