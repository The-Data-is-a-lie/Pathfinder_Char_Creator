# Map: Companion sheets

Wayfinder map. Tickets are the files in `issues/`; the **frontier** is every ticket that is
`Status: open`, unclaimed, and whose `Blocked by:` list is entirely `resolved`.

Successor to [Map: Bonded creatures](../companions/map.md), which is **closed**. That map produced
the spec — **§8 Bonded creatures** in [`docs/feature_spec_todo.md`](../../feature_spec_todo.md) — and
explicitly ruled the build out of scope. This map carries the same subject from *specified* to
*on screen*. **Do not reopen §8's D1–D10**; where a ticket here touches one, it says so and amends it.

**Charted 2026-08-03. Four tickets, none blocking another — the whole frontier is takeable now.**
01 and 04 both gate **#31**, 02 gates **#33**, 03 gates **#34**. Take **04 first**: `SESSION_PLAN.md`
already records it as blocking, and the evidence it needs (a 97-row WARN census) is sitting in
`validate_companion_data.py`.

**Updated 2026-08-03.** **01, 04 and 02 are resolved and #31/#32/#35 are built** — the backend now
emits `bonded_creatures` with a populated `stats` block, so the map's **first finish-line gate is
met**, and **#33 is unblocked** with a mechanical recipe (ticket 02 answered from the pf1 schema plus
a dump of all 205 `pf-companions` Actors; two narrow claims are flagged for slice 7's first live
import rather than gating it). The frontier is **03**, which gates **#34**.

## Destination

Every bonded creature the generator rolls arrives as a **sheet the player can actually use**:

- **FoundryVTT** — its own Actor document in the "Random Characters" folder, named
  `<Master>'s animal companion: <Name>` (or the matching label for a mount / familiar / eidolon).
- **Web sheet** — a pre-filled block in the existing Companions tab, still hand-editable.

Build sequencing (the slices themselves) is `SESSION_PLAN.md` §3 *"Then, in order"* — G/H/I/J/K =
**#31–#35**. This map owns the decisions those slices wait on, not the slices.

Finish line — three gates:

1. ✅ **MET 2026-08-03.** `Backend/main_test.py` emits `bonded_creatures` with a populated `stats`
   block per creature, and `test_golden_payload.py` (6 match) / `test_house_invariants.py` (15,560
   checks, 55 companions granted) / the companion validators (14 PASS) all pass.
2. A generated druid imports into Foundry as **two** Actors — the PC and its companion — with correct
   HP/AC/saves on the companion, and nothing silently dropped.
3. The same payload opens on the standalone web sheet with the Companions tab pre-filled.

## Notes

- **Domain:** Pathfinder 1e, this repo's generator backend, the `pf1e_random_char_generator`
  FoundryVTT module, and the standalone web sheet
  (`AppData/Local/FoundryVTT/Data/Pathfinder-Character-Sheet`).
- **§8 is the authority.** Read it before any ticket. This map decides only what §8 left open.
- **Skills every session should consult:** the OKF `pathfinder` bundle via the user-level
  `oks-bundles` skill; `/grilling` and `/domain-modeling` for the conversation tickets;
  `/prototype` for ticket 02.
- **Docs doctrine:** code owns behaviour. Record decisions and not-yet-code, never a restatement of a
  constant or formula that a symbol already owns.
- **1.0 scope:** this is the Bonded Creatures phase of
  [`docs/plan_1.0_finish.md`](../../plan_1.0_finish.md). Build slices live there; decisions live here.

### Starting state (established during charting, 2026-08-03)

Build slices 1–4 of §8 have landed; 5 is half-built and 6–9 are absent.

- `resolve_bonded_creatures()` (`Backend/utils/class_func/animal_companions.py:190`) reads
  `Backend/json/companion_grantors.json` and resolves every grantor into
  `character.bonded_creatures` — each entry carrying `type`, `grantor`, `effective_level`, `species`,
  `name`, `sex`, `kind`, `chassis`, `species_stats`, `feats`, `gear`, `gear_source`.
- **No numbers exist.** No advancement merge, no `stats` key, no hp/ac/saves/bab/attacks/skills math
  anywhere in the module — deferred to **#31** by its own docstring (`animal_companions.py:41`).
  `progression_override` is stashed on each entry as the merge step's hook and read by nothing.
  The `animal_feats` fix (chassis row's own `feats` count) *did* land — `animal_companions.py:365-389`.
- **Nothing is exported.** `Backend/main_test.py:1764` still emits only the frozen singular
  `animal_companion` alias; `bonded_creatures` appears in no payload dict (**#32**).
- **Foundry creates exactly one Actor** — `createCharacter.js:1-9` hard-codes a single
  `Actor.create`, patched by `injectJsonDataIntoNewActor()` and folder-assigned in
  `createAndAssignActor()` (`:144-162`). No loop, no `pf-content` clone, no companion reference.
- **The web sheet's Companions tab is hand-typed.** `_sheet.companions[]` (`scripts/tabs/companions.js`)
  is a user-owned model wired field-by-field to `dblclickEditable` → `quietSave()`. It reads nothing
  from the payload. Its header comment records that *linked roster characters were ruled out by
  portability* — a separate companion sheet was already considered and rejected on that consumer.
- `test_house_invariants.py` has zero companion coverage.

*(All five bullets above were true at charting. The first three were fixed by #31/#32 and the last by
#35, all on 2026-08-03; the two renderer bullets still stand.)*

## Decisions so far

<!-- one line per resolved ticket: gist + link. Detail lives in the ticket, never here. -->

- **The published deltas already contain the size package; only the geometry is ours.** A Dex
  penalty appears on all 153 size-increasing advancement blocks and on none of the 43 others, so the
  deltas apply verbatim and `SIZE_GEOMETRY` supplies only AC / attack / CMB / CMD / Stealth / space,
  keyed off the creature's *final* size. → [ticket 04](issues/04-size-change-double-count.md), spec
  §8 **D11**.
- **Clone the body, delete its progression, drive the class item at HD.** pf1 honours stored fields
  and rebuilds every `.total`, so the numbers reach the sheet through the clone's own
  `Animal Companion` class item — set to the creature's **HD count**, not its effective level. The two
  change-bearing items every `pf-content` Actor ships (`STR/DEX Bonus`, `Natural Armor Bonus`) are the
  companion table re-applied, and must be deleted or the table lands twice; pf1's own
  `floor(level / 3)` is wrong at every third level anyway. Amends **D1**: a cloned body is a
  `character`, not an `npc`. → [ticket 02](issues/02-pf1-actor-patching.md)
- **Every number in the stat block has a named source, and none of the PC's code was reusable** —
  only the maximised-HP *rule*. The house skill-rank floor does not carry over, because it keys off a
  class the creature does not have. → [ticket 01](issues/01-attack-skill-derivation.md), spec §8
  **D12**.

### Carried in from charting (2026-08-03, user decisions — not tickets)

- **Two renderers, two shapes.** Foundry gets a genuinely separate Actor per creature (§8 **D1**,
  unchanged). The web sheet **auto-fills the existing nested Companions tab** rather than minting a
  roster character — upholding `companions.js`'s portability ruling while removing the hand-typing.
  *Rejected:* a second roster character on the web sheet.
- **#31 lands before any sheet work.** The backend owns the numbers (§8 **D2**), so the merge and
  stat-block math are the prerequisite, not a follow-up. *Rejected:* a thin chassis-only sheet first.
- **Each renderer composes the title.** §8 **D9**'s *"the backend emits atoms — no composed label"*
  stands; `character_full_name` is already on the payload and `name`/`type` on each entry, so both
  renderers have what they need. *Rejected:* a backend `label`/`title` field.

## Not yet specified

- Whether companions carry **buffs / conditionals** the way weapons do (the §1/§4 pattern). Carried
  over from the closed map. Ticket 02 establishes that a companion is an ordinary `character` Actor
  whose natural attacks are real attack items, so the applier has something to bite on; whether it
  *should* is still undecided.
- **Regeneration semantics on the Foundry side** — re-importing the same character: new Actors
  alongside the old, or an update in place? The module has no precedent for either.
- Whether the **master's sheet cross-references** its companion's sheet, and how (Foundry actor link,
  a payload id, or nothing at all).
- Companion **token art / portraits**.
- Whether the eidolon's degraded v1 output (§8 D4 — named base form plus text, no evolutions) is
  enough to render a sheet worth opening, or reads as broken next to a full companion.

## Out of scope

- **Eidolon evolutions** — v1.1, owned by [ticket 07](../companions/issues/07-eidolon-evolution-model.md)
  of the closed map.
- **Companion gear** — §8 Deferred. D9 fixed its signature (`gear`, `gear_source`, funded from
  `character.gold`), so it is a ticket with a shape, not a rediscovery.
- The **psicrystal** — arrives through [Map: Psionics](../psionics/map.md).
- **Live levelling / sync** of a companion as the PC advances; the generator emits static snapshots.
- Re-deciding §8's D1–D9. This map builds them.
