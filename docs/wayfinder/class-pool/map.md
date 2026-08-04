# Map: Class pool — CLOSED 2026-08-03

Wayfinder map. Tickets are the files in `issues/`; the **frontier** is every ticket that is
`Status: open`, unclaimed, and whose `Blocked by:` list is entirely `resolved`.

> **CLOSED.** The destination is reached: all six Occult Adventures classes roll with their choice
> pools, and the stalker and zealot carry a named blocker. Landed as
> **§10 Class pool** in [`docs/feature_spec_todo.md`](../../feature_spec_todo.md), gated by
> `Backend/scripts/validate_occult_data.py` and the occult invariants in `test_house_invariants.py`.
> Tickets **02 and 03 were answered by the build rather than by grilling** — the census made the
> onboarding checklist a matter of record (`class_data` file, `data.amount` schedule, chooser call,
> `base_classes` for casters, a renderer bucket) and the disposition table is in §10. Remaining work
> is listed under §10's *Deferred*; the **web sheet has no occult presentation yet**.
>
> This unblocks [Map: Class choices](../class-choices/map.md), whose audit now has its final class
> list — 61 rollable classes.
>
> **Superseded on the class-list count, 2026-08-04.** `feature_spec_todo.md` **§12** added seven
> more first-party Paizo classes (the five NPC classes, the omdura and the vampire hunter) and the
> grouped selector, so the pool is **68**, not 61. This map's destination still holds — every class
> the generator knows about rolls or carries a named blocker — and the only class still held out is
> the `stalker`/`zealot` pair. §12 also found the omdura and vampire hunter in
> `pf-content.pf-collab-content`, which [ticket 01](issues/01-foundry-availability-census.md)'s
> three-pack census would have missed: **grade a renderability census against every installed pack.**

**Charted 2026-08-03. Five tickets.** **Updated 2026-08-03: 01, 04 and 05 are resolved** — the census
found all six occult classes fully present in `pf1` 11.11 and the PoW pair absent from `pf1-pow`
1.6.4, and the same dump turned out to be a complete data source. **02 and 03 are the frontier**, and
both are grilling tickets.

> **Sequencing gate — LIFTED 2026-08-03 by the user**, who unparked this map to start the occult
> build while [Map: Companion sheets](../companion-sheets/map.md) still has two of its three
> finish-line gates open (a two-Actor Foundry import and the pre-filled web-sheet Companions tab).
> The one practical cost is that both efforts regenerate the same goldens, so expect a second
> regeneration pass when the companion work lands.

This map **runs before** [Map: Class choices](../class-choices/map.md), which audits every rollable
class's choice-making. That audit must not run against a class list that is about to change, so its
tickets 01 and 03 block on this map's 01 and 03.

## Destination

Every class the generator knows about is either **rollable with full support**, or **documented as
unavailable with a named blocker** — landed as **§10 Class pool** in
[`docs/feature_spec_todo.md`](../../feature_spec_todo.md).

"Knows about" means the eight classes the generator carries data for but filters out of the random
pool: the six Occult Adventures classes and the two Path of War classes held pending Foundry support.
A class that ships must roll, must make its class-specific choices, and must render on both sheets;
a class that does not ship must say *why* in the spec, naming what would unblock it.

## Notes

- **Domain:** Pathfinder 1e, this repo's generator backend, the `pf1e_random_char_generator`
  FoundryVTT module, and the standalone web sheet.
- **Format to match:** §8 (Bonded creatures) and §9 (Psionics) in `docs/feature_spec_todo.md` are the
  house spec format — status line, locked spec bullets, explicit export shape, deferred list.
- **§9 Psionics is the closest precedent in every direction.** It is the most recent case of a whole
  class family being brought into the pool: twelve classes, a generated `class_data` tree
  (`Backend/scripts/build_psionic_class_data.py`), a subsystem-picks convention that reused the
  existing choosers rather than writing new ones, and a house invariant to keep it true. Read §9 and
  [Map: Psionics](../psionics/map.md) before answering 02, 03 or 04 — most of these questions have a
  psionics answer already, and the job is to decide whether it transfers.
- **Skills every session should consult:** the OKF `pathfinder` bundle via the user-level
  `oks-bundles` skill (house rules, PF1e rules, stack architecture); `/grilling` and
  `/domain-modeling` for the conversation tickets.
- **Docs doctrine:** code owns behaviour. The spec records *decisions and not-yet-code*, never a
  restatement of a constant or formula that a symbol already owns.
- **Occult Adventures is Paizo, not 3pp.** Unlike Path of War, Spheres and psionics, these six are
  first-party Paizo classes, so the OGL/attribution work §9 needed (ticket 09) may not apply — but
  the *homebrew* status of any Metzofitz variant still does.

### Starting state (established during charting, 2026-08-03)

Onboarding is a **completion job, not a cold start** — the generator already carries partial data for
all eight classes.

- The six occult classes are declared at `Backend/utils/data.py:2381` (`occult_classes`) and filtered
  out of the random pool at `Backend/utils/util.py:180-184`; `chooseClass` re-filters them so a caller
  cannot force one in. Stalker and zealot are the same shape at `data.py:2337`
  (`pow_classes_pending_foundry`), filtered by the same two lines.
- `data.py` **already** carries: casting stat (`int_casters`/`wis_casters`/`cha_casters`,
  `:285-287` — occultist and psychic are Int, spiritualist is Wis, medium and mesmerist are Cha) and
  the good-save table (`:2393-2400`, all eight present). The kineticist is *deliberately* unmapped as
  a caster — its own comment at `:288` says burn is Constitution-based, which the caster map cannot
  express.
- What is **not** known: whether `Backend/json/class_data/` holds an entry per occult class, whether
  the choice pools (implements, wild talents, spirits, tricks, phrenic amplifications, phantom
  emotional focus) exist as data at all, and whether the Foundry module can render them.
- Installed Foundry content at charting: system `pf1` 11.11 (ships a `classes` compendium and a
  `class-abilities` compendium) plus modules `pf-content` 11.4.0 (35 packs, including
  `pf-class-abilities`), `pf1-pow`, `pf1-psionics`, `pf1spheres`. Whether any of them carries the
  eight classes is a LevelDB question `grep` cannot answer — that is ticket 01.

## Decisions so far

<!-- one line per resolved ticket: gist + link. Detail lives in the ticket, never here. -->

- **All six occult classes are fully present in `pf1` 11.11 — class Item, features and choice pools —
  and the PoW pair is absent from `pf1-pow` 1.6.4.** Renderability was never the occult blocker; it
  is still the stalker's and zealot's. → [ticket 01](issues/01-foundry-availability-census.md)
- **Compendium-first wins: no scrape.** The system's own `class-abilities` pack carries 694 selectable
  options across the six, tagged by `system.associations.classes`, with the class Item's
  `classAssociations` giving the granted-vs-selectable split. Spell *lists* already exist as columns
  in `data/spells.csv`; only the two progression tables are missing. No new OGL entry — this is
  first-party Paizo read from the system pack. → [ticket 04](issues/04-occult-data-sourcing.md)
- **Stalker and zealot stay pending, together, with the original blocker unchanged** — `pf1-pow` 1.6.4
  ships no class Item for either, so they are generatable but unrenderable. Not the degraded case:
  a missing renderer is a different axis from an unmodelled subsystem. →
  [ticket 05](issues/05-pow-pair-availability.md)

### Carried in from the build decision (2026-08-03, user decisions — not tickets)

- **All six occult classes ship in one pass.** *Rejected:* the four tractable classes first, holding
  the kineticist and medium back.
- **A subsystem the generator cannot model degrades rather than holding the class out** — named and
  described, nothing chosen, reusing §8's eidolon ruling. Every degradation is published in §10 so
  [Map: Class choices](../class-choices/map.md)'s audit does not read it as a bug.

## Not yet specified

- Whether the occult classes need **archetypes** at all in v1, and if so whether the existing
  archetype pipeline (`character.archetype_data()`, `build_companion_archetypes.py`) already covers
  them or needs a harvest.
- **Metzofitz occult variants** — the house library may carry its own occult content the way it does
  for psionics and Path of War. Unread; a `docs/homebrew_rules.md` question once the base six land.
- Whether any occult class grants a **bonded creature** (the spiritualist's phantom is companion-
  shaped) and therefore needs a row in `Backend/json/companion_grantors.json`. §8's grantor table is
  the hook; the phantom is not in it today.
- The kineticist's **burn** mechanic — an HP-cost resource with no analogue anywhere in the generator.
  Sharp enough to name, not sharp enough to ticket until 02 says whether the kineticist ships.
- How the **web sheet** tabs its occult subsystems. Path of War and psionics each got a dedicated tab
  (`scripts/tabs/path-of-war.js`, `psionics.js`); six classes with six different engines may not
  deserve six tabs.

## Out of scope

- **Auditing the choices of classes that already roll** — that is
  [Map: Class choices](../class-choices/map.md). This map decides who is *in the pool*; that one
  decides whether everyone in it picks correctly. The two touch at the class list and nowhere else.
- **The bonded-creature work** — §8 and the companion-sheets map own it. This map waits on it.
- Reworking Path of War, Spheres or psionics. They are referenced only as precedent.
- Writing the onboarding code. This map produces §10; the build slices are a later work list, as they
  were for §8 and §9.
