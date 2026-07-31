# 05 — Which classes grant a bonded creature, and under which house rules?

Type: grilling
Status: open
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

_Unresolved._
