# Map: Class choices

Wayfinder map. Tickets are the files in `issues/`; the **frontier** is every ticket that is
`Status: open`, unclaimed, and whose `Blocked by:` list is entirely `resolved`.

**Charted 2026-08-03. Five tickets.** Structurally, **01 and 02 are unblocked** and the other three
chain off them — but see the two gates below: the frontier is **parked**, not takeable.

> **Sequencing gate 1 — bonded creatures.** This map is not worked until the
> [Map: Companion sheets](../companion-sheets/map.md) finish line is met: all three of its gates —
> the backend `stats` block (met 2026-08-03), a two-Actor Foundry import, and a pre-filled web-sheet
> Companions tab. Charting happens now so the questions are captured; nothing here starts until the
> animal-companion system is landed and we are happy with it.

> **Sequencing gate 2 — the class list. CLEARED 2026-08-03.**
> [Map: Class pool](../class-pool/map.md) is **closed**: the six Occult Adventures classes are in the
> random pool and the stalker and zealot are held out with a named blocker, so the class list this
> map audits is final at **61 rollable classes**. The six new entries arrive with choice pools
> already gated by `validate_occult_data.py`, but with two deliberate degradations (§10) that the
> audit must read as intended rather than as bugs: the kineticist's **burn** is unmodelled and the
> medium's **spirit** is rolled once and frozen.

## Destination

Every class in the generator's random pool makes its class-specific choices — rogue talents, rage
powers, aegis customizations, oracle revelations, and the rest — **the right number of them, at the
right levels, legally, and visibly on both sheets** — landed as **§11 Class choices** in
[`docs/feature_spec_todo.md`](../../feature_spec_todo.md), with a **validator** that keeps it true.

The validator is part of the destination, not a follow-up. Per `CLAUDE.md`, a hard convention belongs
in a `Backend/scripts/validate_*.py` or a house invariant, not only in a sentence — a spec paragraph
saying "the magus gets six arcana" decays the moment someone edits a divisor.

## Notes

- **Domain:** Pathfinder 1e, this repo's generator backend, the `pf1e_random_char_generator`
  FoundryVTT module, and the standalone web sheet.
- **Format to match:** §8 (Bonded creatures) and §9 (Psionics) in `docs/feature_spec_todo.md`.
- **Skills every session should consult:** the OKF `pathfinder` bundle via the user-level
  `oks-bundles` skill — the PF1e rules area is the authority for what RAW grants, and the house-rules
  area for where this table deliberately departs from it. `/grilling` and `/domain-modeling` for the
  conversation tickets.
- **RAW is the baseline, not the authority.** Where the house rules override a progression, "Sieg's
  Guide" wins and the departure gets written down. Several of these tables may already be house
  rulings nobody recorded — treat a mismatch as a question, not automatically as a bug.
- **Docs doctrine:** code owns behaviour. §11 records *decisions and not-yet-code*; the schedules
  themselves live in a symbol the code reads, and the spec names that symbol rather than restating it.
- **Scope is the pool, not the rulebook.** Only classes that can actually be rolled. Whatever
  [Map: Class pool](../class-pool/map.md) adds is in; whatever it holds out is out.

### Starting state (established during charting, 2026-08-03)

**Coverage gaps — a class that makes no picks at all:**

| Class | Evidence |
| --- | --- |
| bard | `versatile_perfomance(character)` runs at `Backend/main_test.py:474`, rolls performances into `character.performance_chosen_list`, and **returns them to nobody** — the return value is discarded and no other module reads the attribute. The picks never reach `class features`, so nothing renders. |
| gunslinger | `Backend/json/gunslinger_deeds_dares.json` has no reader anywhere. `gunslinger.py:6` picks only the gun-training weapon category. |
| hunter | `class_data/hunter.json`'s only key, `aspects` (Animal Focus), has no consumer. Its teamwork feats *are* chosen, via the shared feat chooser. |
| shifter | no aspect chooser exists in `class_func/`; the class appears only in `animal_companions.py` and `data.py`. |
| summoner | eidolon evolutions — **not this map's**; owned by the closed [companions map](../companions/map.md) ticket 07, deferred to v1.1. |
| swashbuckler | no chooser — but deeds are automatic in RAW, so this may be correct rather than a gap. |

**Correctness gaps — pick counts live in three competing conventions:**

- `data.amount` (`Backend/utils/data.py:314`) — explicit per-level schedules, but only for 13 classes.
- `get_data_without_prerequisites` (`generic_func.py:130`) — `floor(class_level / divisor)`, or `ceil`
  when `odd=True`.
- `generic_multi_chooser` (`generic_func.py:286`) — `floor((level - start_level) / divisor) + 1`.

At least two disagree with RAW. **Magus arcana** (`main_test.py:569`) takes the default `divisor=2` →
10 picks at level 20, where RAW grants 6 (3rd, then every 3 levels). **Investigator talents**
(`main_test.py:564`) → 10 where RAW grants 9, and `_record_choice_level` stamps them at even levels
when RAW's are odd. The aegis schedule declares its own approximation in `data.py` ("Modelled as one
pick per ~2.5 points… Tune this list, not the chooser"), and `grand_discovery_chooser` carries a
literal `#fix this later` at `main_test.py:571`.

**What already exists and must be reused, not reinvented:**

- `Backend/scripts/test_house_invariants.py:205-222` already asserts picks-vs-schedule — but only for
  psionic subsystems, via `SUBSYSTEM_BUCKET`. Its own comment names the failure mode the whole map is
  about: *"generated but invisible"*. Generalising it is the obvious shape of the gate.
- `Backend/scripts/audit_class_choice_descriptions.py` already audits pool **prose** across most
  buckets (empty/trivial descriptions, the scraper field-glue bug). The description audit exists; the
  *pick* audit does not.
- `Backend/json/companion_grantors.json` + one resolver is the repo's established "declarative table,
  not code" pattern (companions ticket 05) — the precedent any new schedule table should follow.
- `record_bucket_owner` / `_record_choice_level` (`generic_func.py:7-19`) already emit
  `class_feature_owners` and `class_feature_levels`, and both renderers already read them.

## Decisions so far

<!-- one line per resolved ticket: gist + link. Detail lives in the ticket, never here. -->

*(none yet — charted 2026-08-03)*

## Not yet specified

- **Archetypes that trade away a choice feature** — an archetype swapping out rage powers should
  remove the bucket, and nothing models that. The standing ruling is that archetype feature swaps
  stop at the companion bond, deliberately; whether that ruling extends here is a sub-question of
  ticket 03 and may graduate into its own ticket.
- **Favoured-class bonuses that grant extra picks** — some races/classes trade the +1 hp/skill for a
  fractional talent. `favored_class_option` exists; whether it can feed the schedule is unexplored.
- **Retraining / illegal-build repair.** If the audit finds a character whose picks are illegal, is
  the answer to re-roll, to repair, or to let it stand? Only sharp once ticket 03 says what "legal"
  means.
- Whether the choice buckets should carry **buffs / conditionals** the way feats and talents do.
  `build_class_feature_changes.py` already emits changes for some class features; the boundary
  between "chosen option" and "buffable feature" is undrawn.
- The **description quality** of pools that `audit_class_choice_descriptions.py` currently skips.

## Out of scope

- **Which classes are in the pool** — [Map: Class pool](../class-pool/map.md) owns that. This map
  audits whoever is in it.
- **Feats.** They are a choice, and a large one, but they have their own pipeline
  (`class_func/feats.py`), their own data (`data/Metzofitz_Feats.csv`), and their own 1.0 phase. Class
  *bonus* feats granted by a class feature are in; the general feat chooser is not.
- **Spells, powers and maneuvers.** Also per-level selections, also already specified — §1 (Path of
  War), §9 (Psionics) and the spell chooser own them. This map covers the "pick a class feature
  option" buckets only.
- **The eidolon** — companions map, ticket 07, v1.1.
- Rewriting the choosers for their own sake. The map decides what is correct; whether the three
  conventions collapse into one is ticket 01's call, not a premise.
