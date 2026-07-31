# 06 — What is the `manifesters` payload shape?

Type: grilling
Status: resolved
Blocked by: 03, 05
Map: [Psionics](../map.md)

## Question

Design the export. The obvious model is the multiclass-safe `spellbooks` list at
`Backend/main_test.py:1733` — one entry per caster class carrying `casting_level_num`,
`casting_stat`, `spells_known_list`, `spells_per_day_list`, `spell_list_choose_from` and friends. A
`manifesters` list mirrors it with manifester level, PP/day, powers known, chosen powers, discipline,
and manifesting stat.

Settle:

- The exact key names and per-entry fields, and whether powers carry a `powers_desc_dict` the way
  maneuvers carry `maneuvers_desc_dict` for the module's synthesized-item fallback.
- Whether **augmentation** is a generation-time field at all. It is a use-time choice — spend more PP
  for a bigger effect — so the default position is that it is not, and the spec should say so
  explicitly rather than leave it ambiguous.
- Psionic focus: a payload field, a Foundry resource, or neither.
- Whether power points want an entry in the module's `CLASS_RESOURCE_POOLS` / `resource_pools.json`
  (`scripts/modify-abilities.js`, `addResourcePools()`) or whether pf1-psionics owns that surface.

Response keys are read by name everywhere, so adding keys is non-breaking — the constraint is
coherence with `spellbooks`, not ordering.

## Answer

**A `manifesters` list mirroring `spellbooks`, with `powers_desc_dict` as a sibling top-level key.**

`spellbooks` (`Backend/main_test.py:1733`) is built as a list comprehension over
`character.spellbooks`, pulling a fixed key tuple and computing `casting_stat` / `divine` at export
time. `manifesters` copies that shape exactly — one entry per psionic class, so multiclass is safe
by construction:

```
"manifesters": [{
    "name", "display", "level",       # class identity, as spellbooks
    "manifester_level",               # ↔ casting_level_num
    "manifesting_stat",               # ↔ casting_stat, computed at export
    "pp_per_day",                     # int, from the class table
    "max_power_level",                # ↔ highest_spell_known
    "powers_known_list",              # ↔ spells_known_list (per power level)
    "powers_chosen",                  # names grouped by power level
    "discipline"                      # psion's mandated pick; null elsewhere
}]
```

`powers_desc_dict` sits **beside** the list in the `payload.update({...})` block, not nested inside
it — the same placement `maneuvers_desc_dict` has relative to the Path of War keys. It exists for the
same reason: the module synthesizes an item from it when the compendium has no name match, which is
the fallback [ticket 10](10-name-reconciliation.md) depends on for Metzofitz-only powers.

Adding keys is non-breaking — the response is read by name everywhere — so the constraint was
coherence with `spellbooks`, not ordering. (The *request*, by contrast, is unpacked positionally;
nothing here touches it, per [ticket 04](04-class-pool-entry-trigger.md).)

**Three sub-questions, settled:**

- **Augmentation is not a generation-time field.** Spending extra power points for a bigger effect is
  a use-time choice made at the moment of manifesting, and `pf1-psionics` ships a visual augment
  editor with in-dialog selection for exactly that. The spec says so explicitly rather than leaving
  it ambiguous. Powers keep their scraped `augment` text in `powers_desc_dict` as reference.
- **Psionic focus is not a payload field.** `pf1-psionics` tracks current/max focus natively with
  feat and power integration. Emitting our own number would be a second, staler copy.
- **No `CLASS_RESOURCE_POOLS` entry while `pf1-psionics` is active.** It already auto-calculates
  power points from class and ability and auto-recharges them on rest; a parallel pool would render
  two PP trackers on the same sheet. `addResourcePools()` builds one from `pp_per_day` **only** when
  the module is inactive — see [ticket 03](03-division-of-labour.md).

Note for the shape: "manifester" is three categories, not one. **Aegis** has `pp_per_day` but no
`powers_known_list` / `powers_chosen`; **soulknife** has neither and appears in `manifesters` only if
it appears at all. Consumers must not assume every entry has powers.
