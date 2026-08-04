# 01 — Which of the eight held-out classes actually exist in the installed Foundry compendia?

Type: task
Status: resolved (2026-08-03)
Blocked by: —
Map: [Class pool](../map.md)

## Answer — all six occult classes are fully present; the PoW pair is absent

Census taken 2026-08-03 against **system `pf1` 11.11**, **`pf-content` 11.4.0**, **`pf1-pow` 1.6.4**.
Foundry was running, so the packs were copied to a scratch directory and their `LOCK` dropped before
`dump_foundry_pack.mjs` read them; the originals were not touched.

| class | class Item | features | choice pools | source pack |
|---|---|---|---|---|
| occultist | ✅ `Occultist` | ✅ 15 granted | ✅ **89** selectable | `pf1.classes` / `pf1.class-abilities` |
| kineticist | ✅ `Kineticist` | ✅ 17 granted | ✅ **290** selectable | same |
| medium | ✅ `Medium` | ✅ 17 granted | ✅ **63** selectable | same |
| mesmerist | ✅ `Mesmerist` | ✅ 14 granted | ✅ **76** selectable | same |
| psychic | ✅ `Psychic` | ✅ 11 granted | ✅ **148** selectable | same |
| spiritualist | ✅ `Spiritualist` | ✅ 21 granted | ✅ **28** selectable | same |
| stalker | ❌ | ❌ | ❌ | — absent from `pf1-pow.classes` |
| zealot | ❌ | ❌ | ❌ | — absent from `pf1-pow.classes` |

**All six occult classes are first-party `pf1` system content, not `pf-content`.** The system's own
`classes` pack carries a rollable `class` Item for every one of them, and `class-abilities` carries
their features and options as `feat` Items.

### The two mechanisms that made the census answerable

1. **`system.associations.classes`** on each ability Item is the class tag — an exact list, no name
   matching. This is what produced the per-class counts above.
2. **`system.links.classAssociations`** on the class Item lists the *auto-granted* features by level.
   Subtracting those from the associated set is the granted-vs-**selectable** split, which is what
   column 3 actually measures. Without it the counts would have conflated "the class has features"
   with "the class has things to pick from" — exactly the trap this ticket warned about.

`pf1-pow` 1.6.4's `classes` pack holds five class Items — Harbinger, Medic, Mystic, Warder, Warlord.
No stalker, no zealot. The four `class-abilities` hits on "Stalker" are unrelated (`Stalker` →
Slayer, `Stalker Talent` → Rogue, `Stalker Sense` → Vigilante); "zealot" returns nothing anywhere.
→ [ticket 05](05-pow-pair-availability.md) reads these two rows.

**This census expires when any of the three versions above changes.**

## Question

Eight classes are held out of the random pool: the six Occult Adventures classes
(`occultist`, `kineticist`, `medium`, `mesmerist`, `psychic`, `spiritualist` —
`Backend/utils/data.py:2381`) and the two Path of War classes pending Foundry support
(`stalker`, `zealot` — `data.py:2337`). Both lists are filtered out at
`Backend/utils/util.py:180-184`.

**Which of the eight can Foundry actually render today, with the modules already installed?**

This is the gate for the whole map. Every other ticket asks what to *do* about a class, and none of
them can be answered before we know whether the renderer on the other end has anything to receive.
It is a **task**, not a decision: the work is a census, and the answer is a table.

### What the census must produce

One row per class, three columns:

1. **Class item present?** — is there a rollable class Item in a compendium, i.e. the thing
   `createCharacter.js` would attach to give the actor levels? This is the load-bearing column.
2. **Class features present?** — are the level-granted features there as Items (the `class-abilities`
   shape), so a generated character's features are more than name-only text?
3. **Choice pools present?** — are the *selectable* options there (implements, wild talents, spirits,
   mesmerist tricks, phrenic amplifications, phantom emotional focus; stalker/zealot maneuvers and
   their class-specific lists)? A class can be renderable and still have nothing to pick from.

### Where to look, and with what

Installed at charting: system `pf1` 11.11 (packs include `classes`, `class-abilities`) and modules
`pf-content` 11.4.0 (35 packs, including `pf-class-abilities`), `pf1-pow`, `pf1-psionics`,
`pf1spheres`, under `%LOCALAPPDATA%\FoundryVTT\Data`.

**No new tooling is needed.** `Backend/scripts/dump_foundry_pack.mjs` already dumps a Foundry LevelDB
pack, and `dump_pf_content_actors.py` is the precedent for consuming the dump. Note the LevelDB lock
gotcha recorded with the compendium-pack build work: Foundry must not be running, or the dump fails
to open the pack.

### Two traps to avoid

- **A `pf-content` hit on a class *ability* is not a rollable class.** `pf-class-abilities` holding an
  "Implement" item proves nothing about whether `occultist` exists as a class item. Grade the columns
  independently; do not let column 2 imply column 1.
- **`grep` on a pack directory is worthless.** LevelDB is compressed — a raw grep for `occultist`
  returns hits for classes that are absent and misses classes that are present. This was tried during
  charting and produced a table that was pure noise. Dump first, then search the dump.

### What "resolved" looks like

The `## Answer` carries the table itself (eight rows × three columns), the exact pack each hit came
from, and the module/version the census was taken against — later tickets cite it rather than
re-running it, and a module update invalidates it. Where a class is absent everywhere, the answer
names that as its **blocker**, which is what §10 will publish for any class that does not ship.

Ticket [05](05-pow-pair-availability.md) is the stalker/zealot half of this and will read straight off
these two rows; it exists separately because their disposition is a *decision* (do they enter now?)
while this is a *lookup*.
