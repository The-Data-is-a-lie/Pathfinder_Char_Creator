# Map: Bonded creatures

Wayfinder map. Tickets are the files in `issues/`; the **frontier** is every ticket that is
`Status: open`, unclaimed, and whose `Blocked by:` list is entirely `resolved`.

## Destination

A locked, written spec for how the generator produces, computes, and renders bonded creatures —
animal companions, familiars, eidolons, and mounts/psicrystals — landed as **§8 Bonded Creatures**
in [`docs/feature_spec_todo.md`](../../feature_spec_todo.md). Spec only: no code, no JSON authoring.

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
- Payload key `animal_companion` exists at `Backend/main_test.py:1680` but **no consumer reads it** —
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

## Not yet specified

- `animal_feats` has no prerequisite logic and a degenerate selection loop (`i = len(set)`), plus an
  unguarded index that would break past its table. A real bug — unclear whether this spec pass owns
  it or it goes straight to the backlog.
- ~~Whether cavalier/paladin mounts are a variant of the animal-companion chassis or a separate
  one.~~ **Settled by ticket 04**: they reuse `animal_companion.json` verbatim; only the grantor rules
  and 5 missing species are new.
- Two gaps ticket 04 hit and could not close, both cheap but unverified — improved-familiar
  prerequisites (alignment / caster-level gates, on a separate PRD page) and the summoner's
  evolution-points-per-level class table. Neither is sharp enough to ticket until ticket 02 says the
  type is in v1.
- Companion token art / portraits.
- The psicrystal, which is structurally a companion but arrives through the psionics map — see
  [Map: Psionics](../psionics/map.md).
- Whether companions should carry buffs/conditionals the way weapons do (the PoW/Spheres pattern).
  Only visible after the rendering model is settled.

## Out of scope

- Any implementation code or JSON authoring — this map produces a spec.
- Sheet UI or theming beyond consuming payload keys.
- Live levelling/sync of a companion as the PC advances; the generator emits static snapshots.
- Reworking Path of War or Spheres; they are referenced only as format and pipeline precedent.
