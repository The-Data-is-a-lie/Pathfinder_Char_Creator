# 01 — How does a bonded creature render?

Type: prototype
Status: open
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

_Unresolved._
