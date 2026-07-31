# 03 — What does the backend compute, and what does the module?

Type: grilling
Status: resolved
Blocked by: 01
Map: [Psionics](../map.md)

## Question

`pf1-psionics` advertises auto-calculated manifester level, concentration and power points, and it
tracks psionic focus. That is a real offer — the same one `pf1-pow` makes for maneuvers, which the
generator accepted by emitting selections and letting the module render them natively.

But there are three consumers, not one:

- **Foundry with the module installed** — the module can do the math.
- **The standalone web sheet** — no game system, no module. It renders what the payload says.
- **The payload itself**, which is the API contract and is what `test_house_invariants.py` asserts
  against.

So: does the backend compute manifester level / PP-per-day / powers-known and emit finished numbers,
or emit only selections and defer? Path of War is the precedent for *both* answers — it emits
`initiator_level` and per-level counts **and** lets `pf1-pow` render the items.

Decide the line, and say what happens when the module is absent — Path of War has a documented
legacy-item fallback for exactly this case.

## Answer

**The backend computes and emits; the module renders.** The Path of War precedent, taken on the
`initiator_level` side rather than the defer side.

The payload carries `manifester_level`, `pp_per_day`, `powers_known_list` and the chosen powers as
finished numbers. Rationale, in the order that decided it: the payload *is* the API contract, so it
must be self-describing; the standalone web sheet has no game system and can only render what it is
given; and `test_house_invariants.py` needs something to assert against. Deferring to the module
would leave all three with nothing.

The usual objection — two engines that can disagree — does not bite here. [Ticket 01](01-inventory-packs-source.md)
established that **every manifesting class's PP column matches one of `pf1-psionics`' three
hardcoded progressions exactly**, so its auto-calc reaches the same numbers we do.

**Class items.** `tools/export_every_class.macro.js` harvests the twelve `pf1-psionics` class items
into `every_class.json` — the module builds class items from that harvest, not from a compendium at
attach time (`modify-abilities.js:1620`) — and **patches `system.bab` / `hd` / `skillsPerLevel` from
`psionic_classes.json`** on the way through. Harvesting keeps the module's own item identity, so its
Psionic Manifesting tab and PP auto-calc still bind; patching repairs the three fields
[ticket 02](02-data-quality-ogl.md) proved wrong.

Only one of those three actually mattered. Actor HP is already the backend's total
(`modify-abilities.js:292`) and extra class items have their HP zeroed (`:676-680`), so the
placeholder `hd: 6` was cosmetic. **`bab: low` was not** — pf1 derives BAB from class items, and
marksman, psychic warrior, soulknife and voyager are medium-BAB.

**Module absent.** `pf1-psionics` owns power points and psionic focus while it is active; we add no
parallel resource, which would double-count on the sheet. When it is missing, `addResourcePools()`
builds a plain PP resource from the payload's `pp_per_day` — the same legacy-fallback shape Path of
War already documents. Psionic focus is not a payload field; it is module-owned or absent.

Rejected: *emit selections only and let the module compute* (kills the web sheet and the invariant
test); *both compute, module authoritative in Foundry* (honest but invites silent drift, and a GM
seeing two different PP totals is exactly the bug class this effort exists to avoid).
