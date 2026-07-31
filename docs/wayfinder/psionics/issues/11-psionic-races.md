# 11 — Do the psionic races enter the race pool?

Type: grilling
Status: resolved (re-scoped)
Blocked by: 01
Map: [Psionics](../map.md)

Graduated out of the fog by [ticket 01](01-inventory-packs-source.md), which landed the data.

## Question

`Backend/json/class_data/psionics/psionic_races.json` now holds the ten *Psionics Unleashed* races
— Blue, Dromite, Duergar, Elan, Forgeborn, Half-Giant, Maenad, Noral, Ophiduan, Xeph — scraped from
d20pfsrd with their full page text. The user's call was **scrape now, wire later**; this ticket is
the "later".

Deciding it needs more than "yes": the generator's race data is spread across four files with
different shapes, and the psionic races collide with two of them.

- **`Backend/json/racial_stat_changes.json`** drives the ability-score math. A race missing here
  gets all-zero mods and a printed warning — silent-ish failure, exactly the class of bug this
  effort has been avoiding.
- **`Backend/json/PlayableRaces.json`** feeds `race_func.py::race_traits_chooser`, which walks the
  entry's keys *positionally* — from the first key containing `+` through `Languages` — rather than
  by field name. Landing a race here means matching that fragile shape, not just supplying data.
- **`Backend/json/races.json`** carries age/height/weight roll formulas that d20pfsrd's race pages
  do not obviously supply.

Settle:

- **Are these in scope for 1.0 at all**, or does psionics ship classes-only and races follow? The
  companions map and the release train are both already waiting on this map.
- **Duergar already exists in Pathfinder core** as a monster race, and the psionic Duergar is a
  different stat block. Which one wins, and does the generator need both?
- **Is a psionic race gated on rolling a psionic class**, or freely rollable? Free rolling puts
  Xephs and Elans into every party regardless of setting; gating makes race a consequence of class,
  which nothing else in the generator does.
- **Where does the campaign stand?** `docs/homebrew_rules.md` backlog item 7 already wants custom
  races (Loxo / Kalyptran / Dolistani) added, and `races.json` already carries `Loxophant` /
  `D-ziriak` / `Tortugan` keys ahead of the other two files. If psionic races land, they should land
  by the same route those will — this ticket may be the one that settles the route.
- **Noral has no speed line** on its d20pfsrd page (the validator warns). Source it or drop the race.
- **`pf1-psionics` ships a races pack**, so the same name-reconciliation question as
  [ticket 10](10-name-reconciliation.md) applies to whatever we emit.

## Answer

**No — not in psionics v1. And this ticket is re-scoped: it becomes the *custom-race route* ticket
for every homebrew race, not just the psionic ten.**

**Are they in scope for 1.0?** Not as part of this effort. The psionics finish line is that twelve
classes roll legally and import into Foundry with `pf1-psionics` showing their powers. Races are
orthogonal to all three of those gates — a psion works exactly as well as a human as it does as an
elan. Bundling them in would add the positional-shape risk below to an effort that is already the
largest in the 1.0 plan, for no gain against the gate.

**Why re-scoped rather than simply deferred.** The ticket already identified that this is not a
psionics question wearing a race costume — it is the general question of how *any* homebrew race
enters the generator. `races.json` already carries `Loxophant` / `D-ziriak` / `Tortugan` keys that the
other two files do not, and `docs/homebrew_rules.md` backlog item 7 wants Loxo / Kalyptran /
Dolistani added. Whatever route those take, the psionic ten should take. Solving it twice would be
the mistake; solving it for psionics only, and shaping the route around ten d20pfsrd races, would be
worse.

The route has to answer three shapes at once, which is the real work:
- **`racial_stat_changes.json`** — a race missing here gets all-zero mods and a printed warning. That
  near-silent failure is exactly the bug class this whole effort has been avoiding, so the route needs
  a validator gate, not just a convention.
- **`PlayableRaces.json`** — `race_func.py::race_traits_chooser` walks entries **positionally**, from
  the first key containing `+` through `Languages`, not by field name. Landing a race here means
  matching a fragile shape. This is the piece that most needs designing rather than filling in.
- **`races.json`** — age/height/weight roll formulas that d20pfsrd race pages do not supply at all.
  Where do they come from for a homebrew race? Unanswered, and it blocks Loxo just as much as Xeph.

**The sub-questions, answered as far as they can be without the route:**
- **Duergar collision** — core Duergar (monster race) and psionic Duergar are different stat blocks
  and cannot share a key. The psionic one is *Psionics Unleashed* content and would need a distinct
  key; this is a concrete instance of the naming problem the route must settle, and a reason not to
  rush it.
- **Gated on class, or freely rollable?** Freely rollable, if they land — gating race on class would
  make race a consequence of class, which nothing else in the generator does, and it would be the
  wrong precedent to set inside a deferred ticket. Setting-appropriateness is a region concern, and
  the generator already has a region input to hang it on.
- **Noral** — no speed line on its d20pfsrd page (the validator warns). Source it or drop the race;
  do not guess a speed. Not urgent while the races are data-only.
- **`pf1-psionics` ships a races pack** (161 items — race items plus racial traits), so
  [ticket 10](10-name-reconciliation.md)'s reconciliation applies to races too when they land. The
  name map should cover the races pack from the start so this is not re-litigated.

**What happens now:** `Backend/json/class_data/psionics/psionic_races.json` stays exactly where it is,
data-only and unwired — the "scrape now, wire later" call stands, and this is still the "later", just
aimed at a bigger target. §9 records races as deferred; `docs/homebrew_rules.md` backlog item 7 gains
a pointer here so the two do not drift apart.
