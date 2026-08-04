# 02 — Which classes make no choices at all, and which of those are real gaps?

Type: grilling
Status: open
Blocked by: —
Map: [Class choices](../map.md)

*Parked behind both of the map's sequencing gates — bonded creatures, then
[Map: Class pool](../../class-pool/map.md) ticket 03.*

## Question

Ticket 01 asks whether classes pick the right *number*. This one asks the cruder question first:
**which classes pick nothing, and is that wrong?**

"No chooser" is not automatically a bug — some classes genuinely have nothing to choose. The
deliverable is a per-class verdict, not a fix list.

### The candidates found during charting

| Class | What is missing | Verdict needed |
| --- | --- | --- |
| **bard** | Versatile performances are **rolled and then discarded.** `versatile_perfomance(character)` runs at `main_test.py:474`, fills `character.performance_chosen_list`, returns it — and the return value is assigned to nothing, with no other reader anywhere in `Backend/`. The work is done and thrown away. | Almost certainly a real gap, and the cheapest of them: the picker exists and is correct-looking; only the wiring into `class features` is absent. |
| **gunslinger** | `Backend/json/gunslinger_deeds_dares.json` has **no reader**. `gunslinger.py:6` picks the gun-training weapon *category* and nothing else. | Deeds are largely automatic in RAW (granted by level, not chosen) — so is the orphaned file a gap, a *reference* pool, or dead data to delete? |
| **hunter** | `class_data/hunter.json`'s only key is `aspects` (Animal Focus) and **nothing reads it**. Teamwork feats *are* chosen, via the shared feat chooser. | Animal Focus is a real per-use choice. Does a static snapshot pick one, list the pool, or say nothing? |
| **shifter** | No aspect chooser exists anywhere in `class_func/`; the class appears only in `animal_companions.py` (as a non-grantor) and `data.py`. | Shifter aspects are the class's defining feature. Likely a real gap. |
| **swashbuckler** | No chooser. | Deeds are automatic in RAW — this may be **correct**, and the verdict is "not a gap", which is a valuable answer to write down so nobody re-opens it. |
| **summoner** | Eidolon evolutions. | **Not this map's.** Owned by the [companions map](../../companions/map.md) ticket 07, deferred to v1.1. Listed only so the sweep is visibly complete. |

### Do the sweep, don't trust this table

The six above came from a charting pass, not an exhaustive audit. The ticket's first job is to
**enumerate every class in the pool and check it has a chooser call**, because the sweep is what makes
the answer trustworthy — the bard was found by accident. Whatever [Map: Class pool](../../class-pool/map.md)
adds is included.

Two useful cross-checks:

- **Orphaned data files are a tell.** `gunslinger_deeds_dares.json`, `witch_patrons.json` and the
  top-level `spirits.json` are all present-but-never-loaded (the shaman reads its spirits from
  `class_data/shaman.json` instead). A pool with no reader is either a missing chooser or dead weight,
  and both need a verdict.
- **The reverse tell:** a chooser whose bucket ends up empty at low level. `get_data_without_prerequisites`
  returns `None` when `amount == 0`, which is right; but `choosing_talents` also breaks out when the
  pool runs dry (`generic_func.py:180`), which silently under-delivers at high level. Whether that is
  acceptable is this ticket's to say.

### The framing question underneath

**What counts as a "class-specific choice" at all?** The bard's performances, the hunter's animal
focus and the gunslinger's gun training are three quite different things: a build choice, a per-use
choice, and a one-off category pick. The generator emits a **static snapshot**, so a per-use choice
has no natural home — the same problem §8 hit with the companion snapshot and the class-pool map will
hit with the medium's daily spirit. A shared ruling here would serve all three.

### What "resolved" looks like

A per-class verdict — *real gap* / *correct as-is* / *belongs to another effort* — with the reason,
plus a ruling on how a per-use choice is represented in a static snapshot. Real gaps become §11 build
slices; "correct as-is" entries are written down so the question stays closed.
