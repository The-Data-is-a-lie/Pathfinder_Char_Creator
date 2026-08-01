# 06 — Who computes the companion's final numbers?

Type: grilling
Status: resolved
Blocked by: 01 (resolved), 03 (resolved)
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

**Resolved 2026-08-01.** **The backend computes and emits a finished stat block; Foundry renders it.**
The answer does **not** differ per consumer — that was the tempting option and it is the wrong one.

### Why the backend

The deciding constraint is the one the ticket already named: **the standalone web sheet has no game
system to lean on.** If pf1 owned the derivation, the sheet's companion block would be chassis rows
and deltas with nothing to display, and the two consumers would show different numbers for the same
creature. Two further reasons:

- **The payload is the API contract.** Anything a consumer has to derive is a rule the consumer has
  to reimplement, and there are three of them (module, web sheet, and whatever reads the deployed
  endpoint next).
- **`test_house_invariants.py` needs something to assert on.** House-rule HP and the skill-rank floor
  (ticket 03) are only testable if a number reaches the payload. A companion whose HP exists solely
  inside a Foundry client is untested by construction.

§9 settled the identical question the same way for psionics: the payload carries manifester level and
power points as finished values even though `pf1-psionics` computes them itself. The two agree rather
than fight, and the agreement is what the invariant sweep checks.

### What Foundry keeps

Not math — **identity**. [Ticket 01](01-rendering-model.md) established that the module clones the
`pf-content` Actor for the species (art, natural attacks, senses, special qualities) and patches the
payload's numbers over it. That split is stable: the expensive-to-serialise, presentation-shaped
parts come from the compendium; every number comes from the payload.

*Rejected:* backend-for-the-sheet / pf1-for-Foundry. Two derivations of one creature is two places to
drift, and the drift would surface as the sheet and the Foundry actor disagreeing at the table —
exactly the hand-fixing that "table-ready" is supposed to eliminate.

### Which PC-side helpers are reusable

A companion is a **non-character stat block**: no class levels, no BAB progression to pick, no feat
economy, no skill-point pool. The chassis row in `animal_companion.json` supplies `hd`, `bab`, saves,
`skills`, `feats`, natural armor and the str/dex bonus directly, so most PC helpers are the wrong
shape.

- **Reusable as-is:** the house-rule primitives — maximised HP per die (`hp_rolls.py`) and the 2→4
  skill-rank floor (`skill_ranks.py`), both class-name-agnostic (ticket 03).
- **Needs a companion variant:** anything keyed on class entries — `level_and_bab.py` derives BAB and
  feat count from the class list, and a companion has neither. It reads the chassis row instead.
- **Genuinely new:** size-adjustment application (the advancement block changes size category, which
  moves Str/Dex/natural armor/CMB/CMD/AC), and assembling attacks from the species' `attack` string.

The emitted `stats` block — hp, ac, saves, bab, cmb/cmd, abilities, size, speed, attacks, skills — is
specified in [`feature_spec_todo.md` §8](../../../feature_spec_todo.md).
