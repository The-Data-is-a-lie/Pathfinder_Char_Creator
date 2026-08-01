# 02 — Which bonded-creature types ship in v1, and in what order?

Type: grilling
Status: resolved
Blocked by: —
Map: [Bonded creatures](../map.md)

## Question

All five types are in scope for the effort — animal companion, familiar, eidolon, mount, psicrystal —
but they are wildly unequal in cost. The animal companion is half-built; familiars need a new
per-type ability table; eidolons need an evolution-point subsystem that resembles nothing in the
codebase; mounts may be a reskin of the companion chassis or may not.

Decide the v1 set and the order, and say what "done" means for each — a full stat block, or a named
creature with descriptive text.

The forcing question: **`summoner` and `summoner (unchained)` are rollable today and generate no
eidolon at all**, so a summoner NPC is currently missing its entire class identity. Does that make
the eidolon urgent, or does it argue for suppressing summoner from the class pool (the
`pow_classes_pending_foundry` pattern in `Backend/utils/data.py`) until it works?

## Answer

**Resolved 2026-08-01.** v1 is **animal companion + mount + familiar at a full stat block**, with the
**eidolon degraded rather than suppressed**, and the psicrystal left where it already lives.

### The set, and why it is that set

| type | v1 status | "done" means | cost driver |
|---|---|---|---|
| animal companion | **in** | full stat block | already half-built; needs the merge + the math |
| mount | **in** | full stat block | reuses the companion chassis verbatim (ticket 04) |
| familiar | **in** | full stat block | ~20-row master table; bodies come from `pf-familiars` |
| eidolon | **degraded** | named base form + descriptive text | evolutions are a new subsystem |
| psicrystal | **out** | — | arrives through the psionics map, not this one |

Two findings moved the line. Ticket 04 established that a **mount is not a new chassis** — cavalier
and paladin both delegate to "functions as a druid's animal companion", so mounts cost five missing
species and a grantor row, not a subsystem. And [ticket 01](01-rendering-model.md) established that
**bodies can be cloned from `pf-content`**, which collapsed the familiar from "a creature library" to
"a master-bonus table"; `pf-familiars` already ships the core animals plus ~90 improved familiars.

That leaves the eidolon as the only genuinely expensive type, because it is *built* from an
evolution-point budget rather than picked from a list.

### The forcing question: summoner

**Degrade, do not suppress.** A summoner emits a named base form plus descriptive text, and rides the
D3 bare-`npc` fallback from ticket 01. Evolutions land in v1.1 ([ticket 07](07-eidolon-evolution-model.md)).

*Rejected:* holding `summoner` / `summoner (unchained)` out of the class pool with the
`data.pow_classes_pending_foundry` pattern. That pattern is right when a class would generate
**hollow** — Stalker and Zealot had nothing to render into. A summoner is not hollow: it has spells,
class features, gear and a named eidolon, and the only missing piece is the eidolon's evolution
list. Suppressing it removes two of 38 rollable classes from the campaign to avoid an incomplete
block on one creature, which is the worse trade for a table-ready 1.0.

The degraded eidolon is also honest in a way suppression is not — the sheet says what the creature
is and that its evolutions are not yet generated, rather than silently having no summoner at all.

### Order

1. companion (repair the data first — see [ticket 03](03-snapshot-semantics.md)), 2. mount (grantor
rows + five species), 3. familiar (master table + clone), 4. eidolon degraded. The eidolon is last
because it is the only one whose *quality* is capped by a deferred subsystem rather than by effort.
