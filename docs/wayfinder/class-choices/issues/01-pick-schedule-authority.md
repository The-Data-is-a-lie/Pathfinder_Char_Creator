# 01 — What is the authoritative pick schedule, and where does it live?

Type: grilling
Status: open
Blocked by: —
Map: [Class choices](../map.md)

*Parked behind both of the map's sequencing gates — bonded creatures, then
[Map: Class pool](../../class-pool/map.md) ticket 03.*

## Question

**How many options does each class pick, at which levels — and what single symbol owns that answer?**

Today three different conventions answer it, and they disagree with each other and with RAW:

1. **`data.amount`** (`Backend/utils/data.py:314`) — explicit level schedules
   (`'cryptic': {'insights': [2,4,6,8,...]}`), read by `generic_class_option_chooser`
   (`generic_func.py:69`). Covers **13 classes**.
2. **`floor(class_level / divisor)`** — `get_data_without_prerequisites` (`generic_func.py:139`),
   `ceil` when `odd=True`. Covers rogue, ninja, slayer, alchemist, investigator, vigilante,
   barbarian, skald, magus.
3. **`floor((level - start_level) / divisor) + 1`** — `generic_multi_chooser` (`generic_func.py:296`).
   Covers paladin mercies, antipaladin cruelties, monk ki powers.

### The evidence that this is wrong, not merely untidy

- **Magus arcana** — `main_test.py:569` passes no `divisor`, so it defaults to 2 → **10 arcana at
  level 20**. RAW grants 6 (3rd, then every 3 levels). A four-arcanum overshoot, silently.
- **Investigator talents** — `main_test.py:564`, also the default divisor → **10**, where RAW grants 9
  (3rd, then every 2 levels). And because `_record_choice_level` derives the stamp from the same
  arithmetic (`generic_func.py:198`), each talent is labelled with an **even** level when RAW's are
  odd — so the count and the Foundry sheet's level stamp are wrong together.
- **The aegis** admits it in its own comment: customization *points* are modelled as "one pick per
  ~2.5 points", with the instruction "Tune this list, not the chooser".
- `grand_discovery_chooser(character) #fix this later` — `main_test.py:571`.

Two independent bugs found by inspection during charting, in a table nobody has ever swept, is the
argument for sweeping it.

### The decision

**Does one declarative table replace all three?** The repo already has the pattern: §8 ticket 05
replaced a hard-coded druid check with `Backend/json/companion_grantors.json` plus one resolver, and
the ruling was explicitly *"the table is data, not code"*. The analogue here is a
`class_choice_schedule.json` keyed **class → bucket → level list**, with the choosers reading it and
the arithmetic deleted.

Weigh against that:

- The divisor form is *compact* and correct for the classes it fits — "every 2 levels from 2nd" is 10
  numbers written as one. A table is 10 numbers per bucket per class, hand-maintained.
- Whatever wins must serve **all three** call sites, including `generic_multi_chooser`'s level-keyed
  pools (mercies, cruelties, ki powers), whose entries are terse spell/condition stubs rather than a
  flat option list.
- `data.amount`'s schedules are **class-level** lists, and the choosers are multiclass-aware
  (`class_entry_for`) — a rogue 4 / magus 6 must draw on each class's own level, and today does.
  Do not lose that.
- Whatever wins is what ticket 05's validator reads. A schedule the validator cannot see is a
  schedule the validator cannot check.

### Sub-questions

- **Sweep scope.** Every class in the pool, or only the ones under a convention known to drift?
  A full sweep is the only way to find the third magus, and it is a bounded, mechanical job.
- **RAW vs. house.** Where the code disagrees with RAW, is it a bug or an unrecorded house ruling?
  The map's Notes say Sieg's Guide wins where it speaks; the answer must say which mismatches are
  deliberate, and those become §11 lines rather than fixes.
- **The level stamp.** Should the schedule own the stamp too, or does the stamp stay derived? It
  reaches the Foundry sheet through `class_feature_levels`, so it is user-visible either way.

### What "resolved" looks like

A ruling on where the schedule lives, plus the swept table itself — class → bucket → levels, with a
RAW/house column and every mismatch flagged as *bug* or *deliberate*. That table is §11's core and
ticket 05's fixture.
