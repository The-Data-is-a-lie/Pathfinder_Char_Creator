# 08 — Which bespoke class subsystems are v1?

Type: grilling
Status: resolved
Blocked by: 04
Map: [Psionics](../map.md)

## Question

Several of the twelve classes are not manifesters with a power list — they carry their own subsystem,
and each is a small feature in its own right:

- **Soulknife** — the mind blade: a conjured weapon with enhancement points spent on bonuses and
  weapon properties, plus blade skills. It fits nothing in the current pipeline, and it collides with
  `armor_and_weapon_chooser.py`, which assumes a purchased weapon.
- **Aegis** — customization points spent on an astral suit; structurally an evolution pool, so it
  cross-references the eidolon question on the companions map.
- **Cryptic** — insight and disciplines.
- **Tactician**, **Marksman**, **Vitalist**, **Dread**, **Voyager**, **Highlord** — collective,
  martial focus/style, collective healing, fear, and travel mechanics respectively.

Decide which are v1 and which are deferred, and for each v1 one, whether it fits an existing chooser
(`generic_class_option_chooser`, the Spheres feat-budget pattern) or needs its own module.

A class shipping without its subsystem is a class shipping without its identity — so "defer" here
should probably mean "hold the class back from the pool" rather than "ship it hollow". Say which.

## Answer

**All twelve are v1. Nine subsystems ride one existing chooser; the mind blade is the one special
case. No class ships hollow, and no class is held back unless the data forces it.**

The ticket framed these as nine separate features. They are not — eight of the nine, plus blade
skills, are the *same shape*: pick 1 or N from a `{name: description}` list, gated by class level.
That is precisely what `Backend/utils/class_func/generic_func.py::generic_class_option_chooser`
already does, and has done since bloodlines. It handles both the single-pick case (bloodline, order,
mystery, curse) and the multiple-pick case (blessings, inquisitions, revelations, weapon training),
merges into `character.data_dict['class features']` without clobbering earlier picks, and takes level
bounds. **No new chooser module is written.**

| Class | Subsystem | Route |
|---|---|---|
| Aegis | customization points → astral suit | `generic_class_option_chooser`, multiple |
| Cryptic | insights | `generic_class_option_chooser`, multiple |
| Vitalist | vitalist method | `generic_class_option_chooser`, single |
| Psychic warrior | warrior's path | `generic_class_option_chooser`, single |
| Marksman | combat style | `generic_class_option_chooser`, single + style abilities |
| Tactician | strategies | `generic_class_option_chooser`, multiple |
| Dread | terrors | `generic_class_option_chooser`, multiple |
| ~~Voyager~~ | ~~path skills~~ | **row withdrawn — see below** |
| Highlord | decrees | `generic_class_option_chooser`, multiple |
| Soulknife | blade skills | `generic_class_option_chooser`, multiple |
| **Soulknife** | **mind blade** | **special case — see below** |

**Correction (found while building the scraper extension): the Voyager row was wrong, and there are
nine subsystems, not ten.** "Path Skill" is a **psychic warrior** feature; the voyager has no option
list on the wiki at all. Its choice-bearing feature is **Voyager Knowledge**, which grants *bonus
feats* from a fixed list — a different shape that belongs to the feat machinery, not to
`generic_class_option_chooser`. Nothing was built for it, and `psionic_class_options.json` ships the
nine surviving classes. Picking voyager bonus feats is **not built** and is carried forward with the
rest of the deferred psionics work in `docs/feature_spec_todo.md` section 9.

**The real blocker was data, not code.** `scrape_psionics.py` captured a `features` list per class but
**not the option lists those features draw from**. So the enabling work is a scraper extension that
captures each class's option list as `{name: description}` — one change, unlocking all ten rows
above. That is the actual cost of this ticket, and it was invisible from the ticket's framing.

**The mind blade is the genuine exception.** It is a weapon, not a list, and the ticket is right that
it collides with `armor_and_weapon_chooser.py`'s assumption of a purchased weapon. Resolution: the
soulknife gets a **synthesized weapon** whose enhancement bonus comes from the class table at level,
reusing the existing `enhancement_effects_dict` machinery rather than inventing a parallel one, and
`armor_and_weapon_chooser.py` is special-cased so it does not also buy a mundane weapon. Blade skills
that grant weapon properties feed the same enhancement path.

**On "defer means hold the class back, not ship it hollow"** — agreed, and adopted as the standing
rule under [ticket 04](04-class-pool-entry-trigger.md): `data.psionic_classes_pending` exists for
exactly this, it starts empty, and **any class that lands in it must be recorded in §9 with the
specific subsystem it is waiting on**. A silently missing class is as bad as a hollow one.

Rejected: *hold the soulknife back* (lowest risk, but it is the most-played psionic class and the
mind blade turned out bounded); *ship whatever scrapes cleanly and hold back the rest* (honours the
rule, but makes the v1 class list unknowable until the scrape lands — the holdback list is meant to
be an exception, not the plan).

Cross-reference: the aegis's customization points are structurally an evolution pool, so whatever
`docs/wayfinder/companions/` settles for the eidolon should be checked against this row before the
aegis is built.
