# 04 — Where does data for familiars, eidolons and mounts come from?

Type: research
Status: resolved
Blocked by: —
Map: [Bonded creatures](../map.md)

## Question

Only the animal companion has data (`Backend/json/animal_companion.json`,
`Backend/json/animal_choices.json`). Familiars, eidolons and mounts have none.

Find the best source for each, and report the shape it would land in. Candidates, in the order this
repo has historically preferred:

1. **An installed Foundry compendium** — `pf-content` and `statblock-library` are installed. Spheres
   set the precedent that extracting from a compendium beats scraping
   (`Backend/scripts/extract_spheres_talents.py`).
2. **A scrape** of Archive of Nethys / d20pfsrd, as the existing companion JSON was built.
3. **Hand-authored JSON** mirroring `animal_companion.json`'s level-chassis shape.

Report per type: the source, roughly how many records, whether the level-progression table is
structured or prose, and what is *missing* from that source. Familiars in particular need a
master-level-keyed special-ability table (improved evasion, SR, and so on trigger at different
levels per familiar type), which is a different shape from the animal companion's chassis row.

## Answer

**Resolved 2026-07-31.** Each of the three types wants a *different* source, and the compendium-first
preference only pays off as a cross-check — not as the primary source for any of them.

### Familiars — scrape d20pfsrd; `pf-content` cannot help

The master-ability table is **not in any installed compendium**. An exhaustive grep across every
`pf-content` pack for `Alertness`, `Improved Evasion`, `Share Spells`, `Speak with Animals`,
`Spell Resistance`, `Empathic Link` and `Deliver Touch Spells` as item names returned **zero hits**;
the `pf-rules` journal page "1.6. Familiars" is an index stub with none of the table in it.

What the compendium *does* have is creature stat blocks: `pf-familiars` (Actor, ~2.4 MB) holds the
core familiar animals plus ~90 named improved familiars (Almiraj, Cassisian, Dweomercat Cub,
Brownie…), and `statblock-library/packs/sb-familiars` adds 56 prose statblocks (CR 0–1/2). Good for
the *name list*, useless for progression.

[d20pfsrd's familiar page](https://www.d20pfsrd.com/classes/core-classes/wizard/familiar/) carries
**two structured HTML tables**, which is the best shape found anywhere in this research:

1. Master level → `Natural Armor Adj. | Int | Special`, cumulative across 10 rows.
2. "Familiars and Special Abilities" — each familiar type → its static master bonus (Bat → +3 Fly,
   Cat → +3 Stealth, Rat → +2 Fort, Weasel → +2 Reflex…).

That maps cleanly onto the two axes this repo already uses:

- `familiar_master_table.json` — level-keyed, same axis as `animal_companion.json["companion"]`:
  `{"master_abilities": {"<1-20>": {"natural armor adj": int, "int": int, "special": [keys…]}},
  "abilities": {"alertness": "…", …}}`
- `familiar_choices.json` — type-keyed, same axis as `animal_choices.json`, with an `"improved"`
  tier standing in for the vermin/plant split:
  `{"standard": {"Bat": {"bonus": "+3 Fly checks"}, …}, "improved": {"Agathion, Silvanshee":
  {"prerequisites": "…", "bonus": "…"}}}`

**Missing:** improved-familiar prerequisites (alignment / caster level gates) are on a separate PRD
page, not verified this pass.

### Eidolons — scrape d20pfsrd; the compendium is roughly half-complete

[d20pfsrd summoner/eidolons](https://www.d20pfsrd.com/classes/base-classes/summoner/eidolons/) has
**7 base forms × 2 sizes** (aberrant, aquatic, avian, biped, quadruped, serpentine, tauric) and
**~76 evolutions** (≈28 @1 EP, 27 @2, 11 @3, 10 @4).

`pf-eidolon-evolutions` (Item, 93 KB) has only **~36** — about half — though it embeds cost in the
item name (`"Blindsight (4 EP)"`), which is a useful hint for the scraper's field extraction.
`pf-eidolon-forms` (Actor, 347 KB) has all 7 forms in both sizes, assembled from sub-items (Limbs,
Natural Armor Bonus, Eidolon Saves, Link, Share Spells, Evasion). **Use the packs as a completeness
cross-check, not the source.**

Evolutions are **prose with one heading per entry**, not an HTML table — extractable, but it needs a
new scraper. `extract_spheres_talents.py` is the right *pattern* (normalize → name → `{prerequisites,
benefit}` → sorted JSON dump) but not reusable code: it targets Foundry LevelDB, not raw HTML.

Base-form "Starting Statistics" blocks are structurally near-identical to `animal_choices.json`.
Proposed: `eidolon_base_forms.json` mirroring `animal_choices.json`, and `eidolon_evolutions.json`
as a flat `{name: {cost, prerequisites, base form restriction, benefit}}`.

**Missing:** the summoner class table of evolution points per level — presumed a standard structured
class table, not verified this pass.

### Mounts — no creature source needed at all

Cavalier Mount and Paladin Divine Bond are **prose class features**, not tables, and both delegate:
the mount "functions as a druid's animal companion, using the [cavalier's/paladin's] level as
effective druid level." So the existing `animal_companion.json` chassis is reused verbatim.

Of the 19 mount-eligible species named across both classes, **13 already exist** in
`animal_choices.json["normal"]` (horse, pony, camel, wolf, elk, zebra, antelope, wolfdog, ram, stag,
kangaroo, boar, dog, capybara). Only **5 are missing** — giant seahorse, giant tortoise, axebeak,
reindeer, giant weasel — and none is in `pf-companions` either, so they want a small scrape in the
existing "starting statistics" shape.

Proposed: a thin `mount_choices.json` holding only the grantor rules —
`{"cavalier": {"effective companion level": …, "by size": {"medium": […], "small": […]},
"level gained": 1}, "paladin": {…, "level gained": 5}}`. No chassis file.

**⚠ Verify before implementing:** the paladin's effective-level offset was not confirmed — the fetch
did not settle whether it is `paladin level` or `paladin level − 3`. Ticket 05 owns this.

### Bottom line

Compendium-first lost this one. Familiars and eidolons both want a d20pfsrd scrape (familiars from
structured tables, eidolons from prose headings); mounts want no creature data at all, just five
species additions and a level-offset rule.
