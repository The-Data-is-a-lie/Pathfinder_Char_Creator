# 05 — Which classes grant a bonded creature, and under which house rules?

Type: grilling
Status: resolved
Blocked by: —
Map: [Bonded creatures](../map.md)

## Question

Today the trigger is a single hard-coded check: a druid entry, 90% of the time
(`character.domain_chance <= 90`). Real PF1e has many more grantors — ranger, hunter, cavalier,
samurai, paladin, sacred huntsmaster, wizard, witch, sorcerer (arcane bond), summoner — several at
reduced effective level.

Decide the grantor → creature-type → effective-level mapping, and settle three things the current
code gestures at but does not do:

- **Archetype swaps.** `Backend/json/archetypes.json` is loaded; archetypes routinely trade a
  companion away or swap its list (Order of the Beast, aquatic/exotic companions). In or out?
- **Boon Companion** and similar feats that raise effective companion level — does the feat chooser
  need to know about companions, or is this ignored?
- **The existing TODO** in `animal_companions.py`: *"give all druids carry companion / or make it a
  subset of companions and make them based on region"*. Region-flavoured companion lists are a
  campaign-fit idea already written down — wanted, or dropped?

**Carried in from ticket 04:** the paladin's Divine Bond mount effective-level offset is unconfirmed —
`paladin level` or `paladin level − 3`. Settle it here. Cavalier's mount is confirmed as
"cavalier level as effective druid level", gained at 1st; paladin's arrives at 5th.

## Answer

**Resolved 2026-08-01.** The hard-coded druid check is replaced by a **declarative grantor table plus
one shared resolver**, and the effective-level rule is stacking-with-a-cap rather than a per-class
special case.

### The table is data, not code

`Backend/json/companion_grantors.json`, with these columns:

`grantor` · `creature type` (`companion` / `mount` / `familiar` / `eidolon`) · `level gained` ·
`effective level expression` · `conditional` · `species pool`

The resolver reuses `generic_func.py::class_entry_for`, whose docstring already states the rule every
grantor needs: *a chooser fires for whichever class grants it, scaled by THAT class's own level*.
Per the docs doctrine the numbers live in the JSON; what belongs here is the behaviour around them.

### Effective level

- The grantor's **own class level**, transformed by that row's expression. Never character level,
  never the sum of all classes.
- **Sources stack, capped at character level.** That cap is PF1e's general rule and it is what stops
  a druid 5 / ranger 8 from producing a 10th-level companion on a 13th-level character.
- **Below `level gained`, emit nothing.** No clamp to 1. A paladin 3 has no mount at all — the class
  feature has not arrived.
- The one **per-source floor** that survives is the Spheres *Beastmastery* talent's own
  "(minimum 1)", which is that source's RAW text, not a clamp on an unmet threshold.

### Conditional grantors — the coin flips

Several grantors are a *choice*, and the choice has to be rolled and then recorded on the entry so
the sheet can explain an absence rather than look broken:

- **wizard** and **Arcane-bloodline sorcerer** — arcane bond is familiar **or** bonded object.
- **ranger** — Hunter's Bond is an animal companion **or** bond with companions (the party buff).
- **druid** — the existing domain-vs-companion flip (`domain_inquisition.py`, `domain_chance <= 90`),
  which already works and is simply absorbed into the table.

### Carried-in question, settled

**The paladin's bonded mount uses the paladin's level as effective druid level — not level − 3.**
Verified against the Divine Bond text: *"This mount functions as a druid's animal companion, using
the paladin's level as her effective druid level."* Gained at **5th**. The −3 in circulation is the
**ranger's** Hunter's Bond offset, not the paladin's. Cavalier and samurai both use their own class
level, at 1st — samurai confirmed on Archive of Nethys (*"using the samurai's level as his effective
druid level"*).

### Three grantor rows from the chart do not survive RAW

The charting pass listed 14 grantors inside the 38-class rollable pool (`data.py::base_classes`).
Verified count: **13 touched, 10 at a full stat block.**

- **`shifter` grants nothing.** Its progression is shifter aspect, shifter claws, wild empathy,
  defensive instinct, track, woodland stride, wild shape, trackless step, shifter's fury, chimeric
  aspect, greater chimeric aspect, a thousand faces, timeless body, final aspect — no animal
  companion anywhere. Verified on Archive of Nethys. Drop the row.
- **`antipaladin` is a different subsystem.** Fiendish Boon's servant is a permanent
  `summon monster III`, rising one spell level every two class levels to IX at 17th, with the
  advanced template at 11th and SR at 15th. It is **not** a druid's animal companion and does not
  ride the chassis, so it moves to *Deferred* rather than into the mount bucket.
- **`sorcerer` is bloodline-conditional.** Arcane Bond comes from the **Arcane** bloodline —
  *"you gain an arcane bond, as a wizard equal to your sorcerer level"* — while the Ancient variant
  grants a bonded **object** only. Both are already in `Backend/json/class_data/sorcerer.json`. The
  resolver must read the **rolled bloodline**, not the class name.

Net grantor set: `druid, ranger, hunter` (companion) · `cavalier, samurai, paladin` (mount) ·
`wizard, sorcerer*, witch, shaman` (familiar / spirit animal) · `summoner ×2` (eidolon, degraded).

### The fifth grantor is not a class

The Spheres of Might **Beastmastery** sphere's `animal companion` talent
(`Backend/json/class_data/spheres/spheres_of_might.json`) grants a full druid companion at
`max(BAB, Handle Animal ranks, Ride ranks) − 3` (minimum 1), and — with the Broad Skills talent — may
choose a plant or vermin companion. It stacks and is capped like every other source. This matters
because the Spheres flag is a normal generation option, so any flagged NPC can acquire a companion
with no companion-granting class at all.

### The three things the code gestures at

- **Archetypes: in.** `Backend/json/archetypes.json` is already loaded, and archetypes routinely
  trade a companion away or swap its list (Order of the Beast, aquatic/exotic companions). A grantor
  table that ignores archetypes would hand a companion to a class that traded it off — a visible
  wrongness, not a missing nicety.
- **Boon Companion: in, and it has to be authored first.** The feat is **absent from the feat data
  entirely** — it appears only inside Spheres talent prose. So this is "add the feat, then let the
  resolver read it", not "teach the feat chooser about companions". Other effective-level feats can
  follow the same row once it exists.
- **Region-flavoured companion pools: dropped from v1**, kept in *Deferred*. It is a campaign-fit
  idea worth having, but it is a **species-pool** question and every other decision here is a
  **grantor** question; mixing them would have the resolver reaching into region data before the
  grantor table has proven itself. The `species pool` column is the hook it will attach to later.
