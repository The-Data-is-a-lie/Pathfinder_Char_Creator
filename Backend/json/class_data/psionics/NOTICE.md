# Open Game Content notice

**Everything in this directory is Open Game Content**, declared under section 8 of the Open Game
License Version 1.0a. The full licence, including the section 15 copyright notice naming every work
this content derives from, is in [`LICENSE-OGL.txt`](../../../../LICENSE-OGL.txt) at the repository
root.

## What is Open Game Content

The five generated data files here — `psionic_classes.json`, `psionic_class_options.json`,
`psionic_power_lists.json`, `psionic_powers.json`, `psionic_powers_known.json` — carry game
mechanics (class tables, power descriptions, power point progressions, class option lists) derived
from the Dreamscarred Press psionics line as republished by the Library of Metzofitz wiki. Those
mechanics are Open Game Content and are redistributed as such.

`psionic_races.json` likewise carries Open Game Content, sourced from d20pfsrd.

## What is not

The **Python source of this repository is not Open Game Content** — the scrapers, validators,
builders and generation modules are the project's own work and are not released under the OGL.
`psionic_name_map.json` is a reconciliation artifact of this project, not game content.

Product Identity of Paizo Inc. and of Dreamscarred Press is not used, and no compatibility with any
trademark is claimed. `pf1-psionics` is credited in section 15's lineage as an intermediate
compiled source. Dreamscarred Press does not endorse this project.

## Section 10

Serving these mechanics in an HTTP response is Distribution under section 10 of the licence, so the
backend exposes the licence at the `/license` route and every generated payload carries a
`license_url` pointer to it rather than embedding the text.
