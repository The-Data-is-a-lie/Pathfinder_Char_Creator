# 04 — Who owns the size increase: the advancement deltas, or the size-change buff?

Type: grilling
Status: resolved (2026-08-03)
Blocked by: —
Map: [Companion sheets](../map.md)

## Answer — the deltas own the stat half, the geometry is ours

**Neither of the two options below.** Both assumed the question was *how much to strip or top up*;
the census says the premise itself splits cleaner than that, because the two sources do not overlap
where they were assumed to.

**The evidence.** Over all 196 advancement blocks:

| measurement | figure |
|---|---|
| blocks that increase size | 153, **every one a single step** |
| of those, `str`/`dex`/`con` matching the size table exactly | 118 (77%) |
| ...Dex alone | 149 (97%) |
| ...natural armour matching | 76 (50%) |
| advancement blocks that do **not** change size carrying a negative Dex | **0** |

That last row is the proof, and it is the one the ticket did not anticipate. A Dex *penalty* has no
source in PF1e other than growing. It appears on 153 of 153 size-increasing rows and on none of the
43 others. The published deltas therefore **demonstrably contain the size package already** — the
question of whether they do is settled by data, not by preference.

So the table is split by what the data can be shown to hold:

- **The deltas own the stat half.** `str` / `dex` / `con` and the natural-armour delta apply
  **verbatim**. Nothing is stripped, nothing is topped up. The 77% / 50% raggedness never has to be
  reconciled, because the published entry is the authority for a companion — the ruling
  `validate_companion_data.py` already stands on when it WARNs rather than fails.
- **The geometry is ours.** The size-category modifiers — AC, attack, CMB/CMD, Stealth and space —
  appear **nowhere** in `animal_choices.json`, which records only the word `large`. They are supplied
  by `SIZE_GEOMETRY` in `Backend/utils/class_func/companion_stats.py`, keyed off the creature's
  **final** size rather than off the step it took, so a companion that was *born* Small gets its +1
  too. That is a case neither option in the ticket covered.

**`size_change` is provenance, not an instruction.** The record on the stat block names the from/to
and the modifier deltas the growth contributed, so a sheet can explain a number. The values are
already inside `ac`, `attacks[].atk`, `cmb`, `cmd` and `skills`. A renderer that re-applies it
double-counts the half we *do* own — which is why the record carries that sentence in its own `note`
field and why the payload comment in `main_test.py` repeats the prohibition.

**Reach is deliberately absent** from `SIZE_GEOMETRY`. It depends on whether a body is tall or long,
and `animal_choices.json` records neither. Guessing would have been worse than omitting.

**Enforced by `Backend/scripts/validate_companion_stats.py`** (validators 13 → 14), per the ticket's
closing instruction. It has teeth in both directions: a merge that added the table on top produces
447 failures when tried, and the file asserts that at least 30 published deltas still *disagree*
with the table — so if a future repair ever moved the data onto the table, the no-double-count check
could not go quietly meaningless.

*Rejected:* stripping the table out of the deltas (27 rows end with a **negative** Str residue, so
toggling the buff off yields a body that never existed); deltas-own-everything with no buff at all
(the size modifiers to AC / attack / CMB / CMD / Stealth would be missing from the sheet entirely,
since the published block never carries them).

## Question

Carried in from `SESSION_PLAN.md` §3 *"Needs the user"*, where it is recorded as **blocking #31**.

Already decided: when a companion's advancement block increases its size, that increase is modelled
as a **permanent buff** built from the PF1e size-change table, not baked into the base numbers.

Still open, and it is a double-count: **the published per-species advancement deltas already include
the size change.** `bear, grizzly` reads Str +4 at its advancement row — that +4 *is* the Medium →
Large adjustment, already applied by the source. Add the size-table buff on top and the companion
gets it twice.

Two ways out, and they push the complexity to opposite ends:

- **The buff owns the size portion**, and the merge **strips** it out of the deltas before applying
  them — so the deltas contribute only what is genuinely species-specific, and the size table is the
  single authority on size.
- **The deltas own it**, and the buff supplies only the **difference** between what the source baked
  in and what the table says — so the printed stat block is reproduced exactly, and the buff exists
  only to explain the part the source under-applied.

The evidence to decide on already exists: `Backend/scripts/validate_companion_data.py` emits a
**97-row WARN census**, which is precisely the list of rows where the two readings disagree. Work
from that census rather than from a sample — if the disagreement is systematic, the first option is
cheap; if it is ragged, the second may be the only honest one.

Note the D5 repair (`repair_animal_choices.py`) is upstream of this and is **done** — the 109
sign-lost `dex` values are corrected, so the numbers this ticket reasons over can be trusted. This is
a different defect from that one: D5 was data that was *wrong*, this is data that is *right* but
overlaps with a rule we also apply.

Whatever is chosen, the answer belongs in a validator, not only in a sentence — a size package that
silently drifts is exactly the class of bug the `MOD_CRITICAL` whitelist exists to prevent.
