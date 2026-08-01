# 01 — How does a bonded creature render?

Type: prototype
Status: resolved
Blocked by: —
Map: [Bonded creatures](../map.md)

## Question

A companion has to end up somewhere the player can use it. Three candidate models: a **second Actor
document** owned by the same player, **items on the owner's actor** (the way class features and
maneuvers already arrive), or **sheet-text-only** on the web sheet with nothing in Foundry.

There is no precedent for any of them — the Foundry module has **no code that creates a second Actor**
(grepped `companion` / `animal` / `pet` / `minion`), and the `animal_companion` payload key is read by
nothing today.

Prototype the second-Actor path first, because it is both the most useful and the only one whose
feasibility is genuinely unknown: hand-build a companion Actor from a real generated payload and find
out whether pf1's own derived-data pipeline (AC, attacks, saves, skills) produces correct numbers once
chassis stats are dropped in as attributes and items — or whether it fights us. That answer decides
ticket 06 (who owns the stat-block math) and constrains everything downstream.

Worth checking while prototyping: how `pf1-statblock-converter` and `statblock-library` (both
installed) build creature actors — they may already solve most of this.

## Answer

**Resolved 2026-08-01.** The second-Actor path wins, but the prototype question it was framed around
— "does pf1 derive correct numbers once chassis stats are dropped in?" — turned out to be the *wrong*
question, because the answer does not have to be the same on both consumers.

### One payload, N Actors

The backend still emits **one** character. The Foundry module loops over a new payload list and
creates one extra Actor per bonded creature. Not a second `generate_random_char()` call.

- **Actor type is `npc`.** pf1 has no companion type — `systems/pf1/template.json` registers exactly
  `character, npc, vehicle, haunt, trap`.
- **Folder:** the existing "Random Characters" folder. The module already creates and reuses it
  (`createCharacter.js:32-47`, assigned at `:157`); the PC is created at `createCharacter.js:2`, and
  that call becomes a loop.
- **Plumbing cost is zero.** `deliver-data.js` writes the payload to `localStorage` whole, with no key
  filtering, so a new top-level key arrives on the module side for free.

Items-on-the-owner's-actor and sheet-text-only both lose: a companion has its own AC, saves, HP and
attacks, and folding those into the master's sheet either fights pf1's derived data or throws the
numbers away.

### The backend computes; the module clones the body

This is the half that made the prototype unnecessary. **The web sheet has no game system to lean
on** — it renders what the payload contains. If pf1 owned the math, the standalone sheet would have
an empty companion block, and `test_house_invariants.py` would have nothing to assert against. So the
backend emits finished numbers, and Foundry is a *renderer*, not a calculator. §9 already set this
precedent: the payload carries manifester level and power points as finished values even though
`pf1-psionics` computes them itself, and the two agree rather than fight.

What Foundry adds on top is **identity**, which the payload cannot cheaply carry: art, natural
attacks, senses, special qualities. The module clones the `pf-content` Actor matching the species and
patches the payload's numbers over it.

### The compendium finding — a rendering-side amendment to ticket 04

`pf-content` ships Actor compendia at
`C:\Users\Daniel\AppData\Local\FoundryVTT\Data\modules\pf-content\packs\`: `pf-companions` (2.8 MB),
`pf-familiars` (2.4 MB — core familiars plus ~90 named improved familiars), `pf-eidolon-forms`
(348 KB — all 7 base forms in both sizes).

[Ticket 04](04-data-sourcing.md) concluded "compendium-first lost", and that conclusion **stands as
written** — it was answering *where mechanics data comes from*, and the packs genuinely lack the
familiar master-ability table and half the evolutions. This ticket is the different question of a
**rendering** source, and there the packs win outright. **Do not reopen 04**; this is an addition to
it, and it is what made the familiar cheap enough to make v1 (only a ~20-row master-bonus table needs
authoring, not a creature library).

### Degrade gracefully, and gate the names

A species with no compendium match yields a **bare `npc` Actor built from the payload numbers**, plus
a `console.warn`. Silence is the failure mode that already bit spell conditionals and psionics
(§9 ticket 10): the module attaches by name match and silently drops what it cannot match. So the
runtime fallback is backed by a **CI validator** diffing species names against a checked-in dump of
`pf-content` actor names — `dump_pf_content_actors.mjs` → `validate_companion_names.py`.

*Rejected:* a curated name map. It would shrink the species pool to whatever happened to match, which
is a data decision hiding inside a rendering fix.

`pf1-statblock-converter` was evaluated and set aside — its parser is minified and UI-driven
(`SBC.parseInput({characterData, input.text})`), usable as a manual fallback but not as a pipeline.

### Payload consequence

The single `animal_companion` dict cannot express N creatures, so it becomes **`bonded_creatures`, a
list**, with `animal_companion` kept as a deprecated alias to the first companion-type entry (the
sheet repo's issue #15 consumer reads it). A druid 5 / wizard 5 gets a companion **and** a familiar —
three Actors on import. Shape in [`feature_spec_todo.md` §8](../../../feature_spec_todo.md).
