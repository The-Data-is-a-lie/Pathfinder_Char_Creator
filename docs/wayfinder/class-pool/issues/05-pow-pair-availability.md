# 05 — Do the stalker and zealot enter the pool now, or stay pending?

Type: grilling
Status: resolved (2026-08-03) — they stay pending; the original blocker is unchanged
Blocked by: 01 (resolved)
Map: [Class pool](../map.md)

## Answer — still absent from `pf1-pow`, so nothing to decide

The ticket's own first question was a lookup, and it settles the matter:
[ticket 01](01-foundry-availability-census.md)'s census found **no `stalker` and no `zealot` class
Item in `pf1-pow` 1.6.4**. Its `classes` pack holds five: Harbinger, Medic, Mystic, Warder, Warlord.
The "Stalker" hits elsewhere belong to other classes entirely (Slayer, Rogue, Vigilante), and
"zealot" appears nowhere in any installed pack.

So the reason recorded in `data.py:2337` when the list was created — *the Foundry sheet can't resolve
a class item the module doesn't ship* — is **still true**, and the two stay in
`pow_classes_pending_foundry`. This is not the degraded-subsystem case: the generator would build
them fine, but the renderer has nothing to attach, which is a different axis entirely.

**Blocker, in words §10 can publish verbatim:** *`pf1-pow` 1.6.4 ships no class Item for the stalker
or the zealot. Both remain generatable but unrenderable; empty `pow_classes_pending_foundry` and
uncomment the module's `button.js` / `html_dialog.js` dropdown entries once a `pf1-pow` release adds
them.*

They enter **together** — one list, one blocker, and no reason found to split them.

Because they do not enter the pool, they add no rows to
[Map: Class choices](../../class-choices/map.md)'s audit, and the generator-side readiness question
(do they ride `path_of_war.py`'s machinery?) goes unasked until the blocker clears.

## Question

`stalker` and `zealot` sit in `pow_classes_pending_foundry` (`Backend/utils/data.py:2337`) and are
filtered out of the random pool by the same two lines that hold the occult six
(`Backend/utils/util.py:180-184`). The list's own name states the reason: they were held back because
the **Foundry module could not render them**, not because the generator could not build them.

**Is that still true?**

### Ask availability first

This ticket's first question is a lookup, not a judgement: **do the stalker and zealot exist in
`pf1-pow` at all?** They may simply not be in the module, in which case there is nothing to decide —
the answer records the blocker and they stay pending. Ticket [01](01-foundry-availability-census.md)
produces those two rows; read them rather than re-dumping the pack.

Only if the census says they are present does the rest of this ticket have anything to chew on.

### If they are present

- **Is the generator side actually ready?** The other six Path of War initiators already roll, and
  §1 is marked implemented. Confirm that these two ride the same `path_of_war.py` machinery
  (`choose_path_of_war_attr` at `:103`) with data in `class_data/path_of_war/`, or find what is
  missing. `pow_classes_pending_foundry`'s docstring at `Backend/utils/util.py:174` says emptying the
  list is the whole switch — verify that claim rather than trusting it.
- **What do they choose that the other six do not?** Both are maneuver initiators, but each carries
  its own class-specific list. Whatever those are, they become rows in
  [Map: Class choices](../../class-choices/map.md)'s audit — so if these two enter, they enter *before*
  that audit runs.
- **Do they enter together?** They share one list and one blocker, so splitting them needs a reason.

### If they are absent

The answer is short and still valuable: record **what** is missing (class item? maneuvers?
disciplines?), so §10 can publish a named blocker instead of "pending", and so a future `pf1-pow`
update has something concrete to be checked against. Note that the module's item matching is a
**name** match — case-insensitive since the conditional-applier fix, but still a name match — so
"present under a different name" is a real outcome, not a hypothetical.

### What "resolved" looks like

A yes/no on each class with the census row as evidence, and either (a) the entry order and what they
add to the choices audit, or (b) the named blocker and what would clear it. Either way §10 gains two
rows.
