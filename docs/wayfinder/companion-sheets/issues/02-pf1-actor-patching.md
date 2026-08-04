# 02 — Does pf1 accept patched numbers on a cloned `pf-content` Actor?

Type: prototype
Status: open
Blocked by: —
Map: [Companion sheets](../map.md)

## Question

§8 **D2** says the backend computes every number and the module **clones the `pf-content` Actor for
the body, then patches the payload's numbers over it** — Foundry supplies identity (art, natural
attacks, senses, special qualities), never math.

That decision was reached *without* prototyping. [Ticket 01 of the closed map](../../companions/issues/01-rendering-model.md)
framed exactly this experiment and then declared it *"the wrong question"*, because the web sheet has
no game system and therefore the backend had to own the numbers regardless. That reasoning is sound
for the **spec**. It does not survive contact with **slice 7**, which has to actually write the
patch.

The unknown: pf1 recomputes derived data from ability scores, size, class levels and items on every
update. Patch `hp`/`ac`/`saves`/`bab` onto a cloned `pf-companions` Actor and pf1 may honour them,
silently recompute over them, or produce a sheet where the header and the tabs disagree.

Prototype it — hand-build one companion Actor from a real generated entry and find out:

- Which fields **stick** after `actor.update()` and a sheet re-render, and which pf1 overwrites from
  its own derivation.
- Whether the numbers are better expressed as **Changes** (the mechanism the module already uses
  everywhere else — see the buff/conditional pipeline) rather than as raw attribute writes.
- Whether the **cloned body's own** natural attacks and abilities double up with anything the payload
  carries, and what happens to the clone's ability scores when ours differ.
- Whether the chassis row's **`feats`** (already resolved by `animal_feats()`,
  `Backend/utils/class_func/animal_companions.py:365-389`) attach as feat items, and whether the
  clone already has some of them — the double-apply problem the every_feat guard exists for on the PC.
- What the **D3 fallback** actually looks like in practice: a bare `npc` built from payload numbers
  alone, with no clone to fight, may be *more* correct than a patched clone. If so, say so — that
  would be an amendment to D2's rendering half, not to its "backend owns the numbers" half.

Answer with a working recipe the module can implement, not a verdict. `Actor` type is `npc` per D1
(`systems/pf1/template.json` registers only `character, npc, vehicle, haunt, trap`).

Note: `pf1-statblock-converter` was already evaluated and set aside by the closed map — its parser is
minified and UI-driven, a manual fallback only. Do not re-evaluate it.
