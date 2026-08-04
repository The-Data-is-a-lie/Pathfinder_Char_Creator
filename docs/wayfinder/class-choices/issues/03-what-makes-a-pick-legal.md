# 03 — What makes a pick legal, and how strict should the generator be?

Type: grilling
Status: open
Blocked by: 01
Map: [Class choices](../map.md)

## Question

The right *number* of picks (ticket 01) can still be the wrong *picks*. **What does the generator
guarantee about a chosen option's legality, and how hard does it try?**

### What the code does today

`no_prereq_loop` (`generic_func.py:213`) is the whole legality engine, and it works on **prose**:

- It reads an option's `prerequisites` string (`determine_prerequisite_name`, `:241`), strips periods,
  splits on commas, and drops any part matching `character.filter_pattern`.
- An option is selectable if the remaining parts are a subset of `character.chooseable` — a set of
  strings accumulated as the character is built.
- As each talent is picked, `choosing_talents` seeds `character.chooseable` with the talent's own name
  plus two synthetic class-level strings (`"rogue 4"`, `"rogue 3"` — `:190-191`), so later options
  whose prereq names a class level unlock.

That is a string-matching approximation of a rules engine, and it is doing more work than it looks
like. Some known rough edges:

- A prereq that does not comma-split cleanly, or that names an ability score, a feat, or "any two
  X", cannot be satisfied — it is either dropped by `filter_pattern` or blocks the option forever.
- The synthetic class-level strings assume picks are gained in level order and one at a time, which
  the divisor arithmetic makes true today but a schedule table might not.
- `character.chooseable_talents` **accumulates across chooser calls** by design (the feat pipeline
  relies on it), and `choosing_talents` has to re-filter by `dataset_keys` to stop a rage-power slot
  drawing a lingering ninja trick (`:171-179`). That guard exists because the bug happened.

### The decision

**How strict is strict enough?** Three defensible positions:

1. **Best-effort, as now.** A random NPC is not a tournament character; an occasional illegal talent
   is invisible at the table. Cheapest, and the status quo.
2. **Strict on what is checkable, honest about the rest.** Enforce prereqs the string engine can
   actually evaluate, and record which pools contain options it cannot — so the *unknown* is bounded
   and the validator can assert the bound.
3. **A real prerequisite model.** Structured prereqs in the data instead of prose. Expensive, and the
   pools are scraped, so it implies a parsing pass over every pool — the same field-glue territory
   `audit_class_choice_descriptions.py` already patrols.

### Sub-questions

- **Mutual exclusion and once-only.** Duplicates are prevented (`chosen_set`), but nothing models
  "these two rage powers are alternatives" or "this may be taken twice, no more". Do those exist in
  the pools in a machine-readable form, or only in prose?
- **Cross-class prereqs on a multiclass character.** The prereq keys name the *granting* class
  (`class_name`, `:189`) — correct — but `character.chooseable` is shared across every class. Can a
  ninja trick's prereq be satisfied by a rogue level? Sometimes that is right (the two lists
  interoperate in RAW); sometimes it is not.
- **Archetypes that trade the feature away.** An archetype that swaps out rage powers should remove
  the bucket, and nothing models that. The standing ruling is that archetype feature swaps are modelled
  **for the companion bond only** — deliberately, because the prose-only archetype corpus makes
  generalising cost more than the generator did. Does that ruling extend here, or is a *choice bucket*
  removal cheap enough to be the exception? If this needs its own session, graduate it from the map's
  fog into a ticket rather than answering it here.
- **The empty-pool degradation.** `choosing_talents` breaks out when candidates run dry
  (`:180-181`) — deliberately, to avoid an `IndexError` — so a high-level character can silently
  receive fewer picks than the schedule promises. Is that legal, and should the validator distinguish
  "under-delivered because the pool was exhausted" from "under-delivered because of a bug"?

### What "resolved" looks like

A stated strictness level with its reason, a list of the legality rules the generator *does* enforce
and those it knowingly does not, and a ruling on the empty-pool case. Ticket 05's validator asserts
whatever this ticket says is guaranteed — so an honest, narrow guarantee is worth more here than an
ambitious one.
