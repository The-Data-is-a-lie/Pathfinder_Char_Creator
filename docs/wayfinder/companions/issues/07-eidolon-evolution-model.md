# 07 — Does the eidolon fit an existing chooser, or need a new mechanism? (v1.1)

Type: grilling
Status: open
Blocked by: 02 (resolved) — unblocked, deferred to v1.1
Map: [Bonded creatures](../map.md)

## Question

An eidolon is not a creature picked from a list — it is *built*: a base form (biped/quadruped/
serpentine) plus evolutions bought from a level-scaled evolution pool, with prerequisites and
per-evolution point costs.

The repo has a generic budgeted-choice pattern already: `generic_class_option_chooser` /
`get_data_without_prerequisites` in `Backend/utils/class_func/generic_func.py`, backed by
`Backend/json/class_data/<class>.json` pools and registered in
`Backend/scripts/build_class_feature_changes.py::SECTIONS`. Rage powers, discoveries, hexes and
talents all ride it.

Does an evolution pool fit that pattern, or does the point-cost budget (rather than a count) make it
a genuinely new mechanism — closer to how Spheres funds talents from a feat budget
(`Backend/utils/class_func/spheres.py`)?

Decide the model, and whether the base form is a separate choice that constrains the pool. Only worth
resolving if ticket 02 puts the eidolon in v1.

**Carried in from [ticket 04](04-data-sourcing.md):** the shape is now known — 7 base forms × 2 sizes
and ~76 evolutions (≈28 @1 EP, 27 @2, 11 @3, 10 @4), sourced by scraping d20pfsrd's prose headings.
The `pf-eidolon-evolutions` compendium has only ~36, so it is a cross-check, not the source. The
summoner's evolution-points-per-level table was **not** verified and is still needed.

## Answer

_Unresolved — **open and unblocked**, deliberately deferred to v1.1._

**Status after [ticket 02](02-v1-type-scope.md) (2026-08-01).** 02 resolved, so this ticket's blocker
is gone, and 02's answer is what defers it: the eidolon ships in v1 **degraded** — a named base form
plus descriptive text, riding the bare-`npc` fallback — because it is the only bonded-creature type
whose cost is a *subsystem* rather than data plus math. The summoner therefore stays in the rollable
class pool and is not hollow, which removes the urgency that made this ticket look like v1 work.

What v1.1 has to decide is unchanged and still sharp:

- **Point budget vs. count.** `generic_class_option_chooser` picks *N of a list*; evolutions are
  *bought from a pool of points* at 1–4 EP each. Nearest precedent is `spheres.py`, which funds
  talents from a feat budget — but that is a budget of feats, not of a class-table resource.
- **Whether the base form is a separate choice that constrains the pool** (7 forms × 2 sizes, and
  several evolutions are form-restricted).
- **The still-missing input:** the summoner's **evolution-points-per-level class table**, which
  ticket 04 flagged as unverified and nothing has verified since. Presumed a standard structured
  class table. Resolve this *before* the design question — the budget shape is an input to it.

Data shape is already known and does not need re-deriving (ticket 04): ~76 evolutions
(≈28 @1 EP, 27 @2, 11 @3, 10 @4) scraped from d20pfsrd's prose headings, with
`pf-eidolon-evolutions` (~36 entries) as a completeness cross-check only, and
`eidolon_base_forms.json` mirroring `animal_choices.json`.
