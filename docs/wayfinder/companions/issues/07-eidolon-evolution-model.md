# 07 — Does the eidolon fit an existing chooser, or need a new mechanism?

Type: grilling
Status: open
Blocked by: 02
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

_Unresolved._
