# 06 — Who computes the companion's final numbers?

Type: grilling
Status: open
Blocked by: 01, 03
Map: [Bonded creatures](../map.md)

## Question

Right now nobody does. The payload dumps the raw level-chassis row plus the species block and leaves
every derivation — HP, final saves, attack bonus, final AC, skill ranks, size adjustment — to a
consumer that does not exist.

Two ends of the spectrum:

- **Backend computes**, the way it already does for the PC (`hp_rolls.py`, `level_and_bab.py`,
  `skill_ranks.py`), and emits a finished stat block. Works for every consumer including the web
  sheet, which has no game system to lean on. Costs a companion-shaped reimplementation of math that
  already exists for characters.
- **Foundry derives**, with the backend emitting chassis + deltas + items. Cheap, and correct by
  construction inside Foundry — but leaves the web sheet with nothing renderable.

Ticket 01 decides whether the second option is even available; ticket 03 fixes what the inputs are.
Decide where the line falls, and whether the answer differs per consumer.

If the backend computes, say explicitly which of the PC-side helpers are reusable against a
non-character stat block and which need a companion variant.

## Answer

_Unresolved._
