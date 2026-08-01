# Map: Bonded creatures — CLOSED (2026-08-01)

Wayfinder map. Tickets are the files in `issues/`; the **frontier** is every ticket that is
`Status: open`, unclaimed, and whose `Blocked by:` list is entirely `resolved`.

**Closed 2026-08-01.** Six of seven tickets resolved; **§8 Bonded Creatures** is landed in
[`docs/feature_spec_todo.md`](../../feature_spec_todo.md) and is now the authority. Ticket 07
(eidolon evolutions) stays open and unblocked, deferred to **v1.1** by ticket 02's answer — it is a
v1.1 work item, not a live frontier. This map is history, not a work queue: build work is tracked as
the Bonded Creatures phase in [`docs/plan_1.0_finish.md`](../../plan_1.0_finish.md).

## Destination

A locked, written spec for how the generator produces, computes, and renders bonded creatures —
animal companions, familiars, eidolons, and mounts/psicrystals — landed as **§8 Bonded Creatures**
in [`docs/feature_spec_todo.md`](../../feature_spec_todo.md).

**Amended 2026-08-01:** no longer spec-only. Ticket 03 found that `animal_choices.json` cannot be
merged as written, so the effort also owns the **scripted data repair** and the **two validators**
(`repair_animal_choices.py`, `validate_companion_data.py`, `validate_companion_names.py`) — see D5
and D3 in §8. Everything else remains build work for a later session.

## Notes

- **Domain:** Pathfinder 1e, this repo's generator backend, the `pf1e_random_char_generator`
  FoundryVTT module, and the standalone web sheet.
- **Skills every session should consult:** the OKF `pathfinder` bundle via the user-level
  `oks-bundles` skill (house rules, PF1e rules, stack architecture); `/grilling` and
  `/domain-modeling` for the conversation tickets; `/prototype` for ticket 01.
- **Format to match:** §1 (Path of War) and §2 (Spheres) in `docs/feature_spec_todo.md` are the
  house spec format — status line, locked spec bullets, explicit export shape, deferred list.
- **Docs doctrine:** code owns behaviour. The spec records *decisions and not-yet-code*, never a
  restatement of a constant or formula that a symbol already owns.
- **1.0 scope:** this effort was pulled into 1.0, so `docs/plan_1.0_finish.md` gains a phase once
  the spec lands.

### Starting state (established during charting, 2026-07-31)

- `Backend/utils/class_func/animal_companions.py` is the only companion code. Druid-only, gated on
  `class_entry_for(character, 'druid')` and `character.domain_chance <= 90`.
- It does **no** stat-block math — no HP, saves, attack bonus, AC, skill ranks, or size adjustment,
  and nothing merges a species' `"<N>th-level advancement"` delta block when the companion crosses
  that threshold. `companion_info` is a straight level-row lookup.
- Data: `Backend/json/animal_companion.json` (level chassis + a flat feat bag) and
  `Backend/json/animal_choices.json` (species → starting statistics + advancement deltas).
- Payload key `animal_companion` exists at `Backend/main_test.py:1747` but **no consumer reads it** —
  not the Foundry module, not the web sheet.
- Familiars, mounts and eidolons have zero support. `summoner` and `summoner (unchained)` are
  rollable today and generate no eidolon at all.
- The Foundry module has **no code anywhere that creates a second Actor document**.
- No tests or validators touch companions.

## Decisions so far

<!-- one line per resolved ticket: gist + link. Detail lives in the ticket, never here. -->

- [04 — Where does data for familiars, eidolons and mounts come from?](issues/04-data-sourcing.md) —
  compendium-first lost: familiars and eidolons both want a d20pfsrd scrape (familiars from two
  structured tables, eidolons from ~76 prose headings — `pf-content` has neither the familiar
  master-ability table nor more than half the evolutions), while mounts need no creature data at all,
  just 5 species added to `animal_choices.json` and a level-offset rule.
- [01 — How does a bonded creature render?](issues/01-rendering-model.md) — one payload, **N Actors**
  of type `npc`; the backend owns every number and the module clones a `pf-content` Actor for the
  body, degrading to a bare `npc` plus a CI name-gate on a miss. Compendium-**as-renderer** is an
  addition to 04, not a reopening of it.
- [02 — Which types ship in v1, and in what order?](issues/02-v1-type-scope.md) — companion + mount +
  familiar at full stat block; the **eidolon degrades rather than suppressing summoner**; psicrystal
  stays with psionics.
- [03 — What is a companion snapshot at master level N?](issues/03-snapshot-semantics.md) — static
  snapshot at the resolved effective level, with a per-field advancement merge rule; forced a scripted
  repair of `animal_choices.json`, whose size-up rows lost their minus signs.
- [05 — Which classes grant a bonded creature?](issues/05-master-class-coverage.md) — declarative
  grantor table + one resolver; sources stack, capped at character level, nothing below threshold.
  Paladin mount = paladin level at 5th; **shifter, antipaladin and unconditional sorcerer are not
  grantors**.
- [06 — Who computes the companion's final numbers?](issues/06-statblock-math-ownership.md) — the
  backend, for every consumer; Foundry supplies identity, not math (the web sheet has no game system).

## Not yet specified

- Ticket **07** (eidolon evolutions), open and unblocked, deferred to v1.1 — including the still
  unverified summoner evolution-points-per-level class table.
- Improved-familiar prerequisites (alignment / caster-level gates, on a separate PRD page) —
  unverified by ticket 04 and not needed for the v1 familiar.
- The **antipaladin's** Fiendish Boon servant: a permanent `summon monster III+`, a different
  subsystem from the companion chassis (ticket 05).
- Region-flavoured companion pools — the standing TODO in `animal_companions.py`, dropped from v1 by
  ticket 05 as a species-pool question; the grantor table's `species pool` column is its hook.
- Companion token art / portraits.
- The psicrystal, which is structurally a companion but arrives through the psionics map — see
  [Map: Psionics](../psionics/map.md).
- Whether companions should carry buffs/conditionals the way weapons do (the PoW/Spheres pattern).
  Answerable only once the rendering model has actually run against a real actor.

## Out of scope

- Generation, rendering and payload code — the *build*. The map produced the spec; §8's build slices
  are the work list. **Amended 2026-08-01:** the scripted `animal_choices.json` repair and its
  validators are **in** scope (D5/D3), because ticket 03 showed the merge rule cannot be specified
  against data that is wrong.
- Sheet UI or theming beyond consuming payload keys.
- Live levelling/sync of a companion as the PC advances; the generator emits static snapshots.
- Reworking Path of War or Spheres; they are referenced only as format and pipeline precedent.
