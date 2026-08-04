# 04 — Where does occult class data come from?

Type: research
Status: resolved (2026-08-03)
Blocked by: 01 (resolved)
Map: [Class pool](../map.md)

## Answer — compendium-first wins here; no scrape

The precedent this ticket expected to lose is the one that wins. §8 ticket 04 found `pf-content` too
thin to generate familiars from; **`pf1` 11.11's own `class-abilities` pack is not thin.** It carries
694 selectable options across the six classes, each a real Item with a description, tagged to its
class. Nothing needs scraping and nothing sits orphaned in the repo — `Backend/json/class_data/` has
no file for any of the six, and `data/class_ability.csv` is feature *prose* that was already ingested
into `class_data.json`.

### Per-class source table

| class | pool | how it is identified in the pack | count |
|---|---|---|---|
| occultist | implements | `tags` = `Occultist Implement` | 8 |
| occultist | focus powers | `tags` contains `Focus Power`, or untagged + description mentions *mental focus* | ~62 |
| kineticist | elements | `tags` = `Kineticist Element` | 8 |
| kineticist | utility wild talents | `tags` = `Utility Wild Talent` + `<Element> Element` | 142 |
| kineticist | infusions | `tags` = `Form Infusion` / `Substance Infusion` + element | ~80 |
| medium | spirits | name ends `" Spirit"` (the six legends) | 6 |
| medium | legendary / outsider spirits | `tags` = `Medium Legendary Spirit` / `Medium Outsider Spirit` | 25 / 9 |
| mesmerist | bold stares | name ends `"(Stare)"` | 18 |
| mesmerist | tricks | `tags` = `Mesmerist Trick` / `Mesmerist Masterful Trick`, plus untagged whose text says *this trick* | ~50 |
| psychic | disciplines | name ends `" Discipline"` | 23 |
| psychic | phrenic amplifications | untagged + description mentions *phrenic pool* (needs narrowing — the raw filter also catches discipline-granted powers) | ≤58 |
| spiritualist | emotional focus | `tags` = `Phantom Emotional Focus` | 18 |

**Spell lists need no source at all** — `data/spells.csv` already carries dedicated `occultist`,
`medium`, `mesmerist`, `psychic` and `spiritualist` columns, and the spell chooser filters on the
class's own column. Only the two progression tables (`spells_known.json`, `spells_per_day.json`) are
missing, and those are 20-number rows read off the class table.

### The one soft spot

Four of the twelve pools are identified by tag and are exact. The rest lean on a name pattern or a
description phrase, and the psychic's phrenic amplifications are the worst of them — the *phrenic
pool* filter over-collects, because discipline-granted powers spend from the same pool. Per
`CLAUDE.md`, that is exactly the kind of convention that belongs in a validator rather than a
comment: `validate_occult_data.py` owns the bucket contents, so a heuristic that drifts fails a gate
instead of quietly mis-shelving an option.

### Licensing

**No new OGL entry needed.** Occult Adventures is first-party Paizo, and the content is being read
from the `pf1` system's own compendium rather than redistributed from a third-party publisher.
`build_ogl_license.py`'s Dreamscarred Press machinery (§9 ticket 09) does not extend here.

### Method note

The pack was read with `dump_foundry_pack.mjs --full` against a scratch copy (Foundry was running;
`LOCK` dropped on the copy, originals untouched). The two fields that make the pack usable as a
*source* rather than just a renderer are `system.associations.classes` (the class tag) and the class
Item's `system.links.classAssociations` (the auto-granted list, whose complement is the selectable
pool). Both are documented in [ticket 01](01-foundry-availability-census.md).

## Question

Assuming some of the six occult classes ship, **where do their class tables and choice pools come
from** — and is any of it already in the repo or the installed compendia?

This is AFK reading, resolvable by a `/research` subagent. It surfaces the facts tickets 02 and 03
are deciding against; it does not decide anything itself.

### What to establish

1. **What the repo already has.** Does `Backend/json/class_data/` carry a file for any of the six?
   Is there occult data sitting orphaned the way `gunslinger_deeds_dares.json` and `witch_patrons.json`
   are — present, never loaded? Search before scraping.
2. **What the compendia carry** — read off ticket 01's census dump rather than re-dumping. A pack that
   holds every implement as an Item is a *data source*, not just a renderer.
3. **What is missing, and where it lives publicly.** For each gap: d20pfsrd, Archive of Nethys, or
   the Metzofitz homebrew library. Report the page shape, because that decides the cost — §8 ticket 04
   found familiars sat in two clean structured tables while eidolon evolutions were ~76 prose
   headings, and that difference was the whole answer.

### The three precedents to weigh

- **Compendium-first** — harvest from the installed packs. §8 ticket 04 tried this and it *lost*:
  `pf-content` had neither the familiar master-ability table nor more than half the evolutions. The
  lesson is that a pack can be complete enough to render and far too thin to generate from. Check,
  do not assume.
- **Generate the `class_data` tree from a build script** — `Backend/scripts/build_psionic_class_data.py`
  built twelve classes' worth of pools this way for §9, and it is the closest structural match: same
  problem, same output shape, one family later. Establish whether it is parameterisable or whether an
  occult sibling script is the honest answer.
- **Scrape** — the repo's original route (Archive of Nethys, d20SRD → `Backend/json/`). Slowest, and
  the field-glue bug `audit_class_choice_descriptions.py` exists to catch is a scrape artefact, so a
  scrape has a known tax attached.

### Licensing note

Unlike Path of War, Spheres and psionics, Occult Adventures is **first-party Paizo**. §9 needed an OGL
attribution ticket and a `build_ogl_license.py` entry for Dreamscarred Press content; check whether
that machinery needs a new entry here at all, and say so either way — a one-line answer is fine, but
it should be answered rather than assumed.

### What "resolved" looks like

A per-class, per-pool source table: *what we need · where it is · what shape it is in · what it costs*.
Findings land on a throwaway `research/occult-data-sourcing` branch with a pointer from this ticket,
per the map's research convention. No decision — tickets 02 and 03 make those.
