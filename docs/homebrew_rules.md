# Homebrew rules — generator mapping, backlog & coverage

> **The rules themselves are not here.** Their authority is
> [Sieg's Guide to Dungeons, Dragons, and Life](https://docs.google.com/document/d/1PLsqBzF_QB8QQsv5vBGHtMWTD4shc3E8IPfsbmGe82Q/edit)
> (the hub doc + its sub-docs), and they are catalogued in the **OKF `pathfinder` bundle** under
> `oks/pathfinder/house-rules/` — reach it via the `oks-bundles` skill.
>
> This file keeps only what the bundle should *not* own: **where each rule plugs into this
> codebase**, **what is still unimplemented**, and **which source sub-docs have been read**.
>
> Numbers were originally extracted with an automated summarizer — **verify against the live docs
> before implementing.**

## Rule → code map

Where each area of the house rules lands in the generator. Read the rule text in the bundle; read
the behaviour in the code. If the two disagree, the code wins and the bundle has a bug.

| Rule area | Bundle page | Plugs into |
|---|---|---|
| Ability scores, starting wealth | `house-rules/feat-economy.md` (context) | `stats.py`; the *starting gold* input |
| Full HP per level (incl. racial HD) | `house-rules/skills-and-hp.md` | `hp_rolls.py` (homebrew flag → max die/level; Foundry mirrors it via pf1's `healthConfig` world setting — System Settings → Health Configuration, auto-HP with maximized levels/rate) |
| Traits: 8-pick-4, +1 per minor flaw | `house-rules/flaws-and-traits.md` | trait selection + `data/traits.csv` |
| Flaws → bonus feats | `house-rules/flaws-and-traits.md` | feat counts (`level_and_bab.py`) |
| Proficiency ↔ Martial Tradition trade | `house-rules/skills-and-hp.md` | `armor_and_weapon_chooser.py` |
| Free Skill Unlock at 5+ | `house-rules/skills-and-hp.md` | `skill_ranks.py` |
| Bonus feats at creation, flavor & story feats | `house-rules/feat-economy.md` | `level_and_bab.py::update_level` builds both budgets (`normal_feat_amount` vs the `feat_amounts` sum); the subsystem reservation in `main_test.py` spends them, capped by `test_feat_budget.py` — backlog #4 |
| Skill ranks (+2→+4, 3/level cap, background ranks) | `house-rules/skills-and-hp.md` | `skill_ranks.py` |
| Alternate ability per skill | `house-rules/skills-and-hp.md` (full table) | `skill_ranks.py` + skill definitions |
| Professions & trainers | `house-rules/trainers-and-professions.md` | `profession_chooser.py`, `trainers.py` |
| Homebrew feat pool, custom races | `house-rules/homebrew-content.md` | `feats.py` (disabled branch), `data/Metzofitz_Feats.csv` |
| Feat tax / exemptions | `house-rules/feat-tax.md` | prerequisite checks in `feats.py`, `feat_tax.py` |
| Optional systems turned on | `house-rules/optional-systems.md` | Path of War, Spheres, Skill Unlocks … |

## Implementation backlog

Highest-value, most generation-relevant first:

1. ~~**Wire homebrew feats**~~ — DONE 2026-07-30: `feats.py::metzofitz_feat_frame` joins the
   General/Combat rows of `data/Metzofitz_Feats.csv` into `generic_feat_chooser`'s pool behind the
   homebrew flag (AoN wins name collisions; descriptions via `metzofitz_description`); swept by
   `scripts/tests/test_house_invariants.py`.
2. ~~**Homebrew feat counts**~~ — DONE 2026-07-30: +2 creation feats (folded into the normal
   bucket) and the diminishing flaw-feat schedule (first 2 flaws +1 each, 4th grants the 3rd;
   0 flaws → 0; behind `misc_homebrew_rules`) in `level_and_bab.py::update_level`; swept by
   `scripts/tests/test_house_invariants.py`.
3. **Verify every sphere's advanced talents are labelled** — UNVERIFIED, and the §8 hard gate
   depends on it. `spheres._is_advanced` decides advanced-vs-normal from `rec["type"] == "advanced"`
   OR membership in `_advanced_set(system, sphere)` (`advanced_talents.json`). Neither source has
   ever been checked for **coverage**: a sphere whose advanced talents are unlabelled in both would
   have them silently treated as normal, which both defeats the
   `(normal + 2*feats) // 7` gate and mislabels them on the sheet (the front-end reads this flag to
   print "(Advanced)" and to sort them last). The module docstring already warns that the pf1 prereq
   engine cannot be trusted here — `no_prereq_prep`'s `filter_pattern` matches the substring "cast",
   so a magic talent's "caster level Nth" gate auto-satisfies. **Wanted:** a
   `validate_spheres_advanced_labels.py` that, per sphere, reports how many talents each source
   marks advanced and fails on a sphere where BOTH are empty — that is the shape that cannot be
   right. Raised 2026-08-07 alongside the level-scaled talent budget.
4. ~~**Which feat budget do the subsystems size against — the normal amount or the homebrew one?**~~
   — **DECIDED 2026-08-07 (`edb3b9e`): the homebrew total, and the subsystems are capped to what it
   can actually pay.** Kept in full because it is the one place the two budgets are written down, and
   because the *answer* is not recoverable from any single symbol. Raised out of ticket 08
   (`tks/pathfinder-char-creator/architecture/scripts-and-phases/08-who-owns-the-feat-budget.md`);
   gate is `Backend/scripts/tests/test_feat_budget.py`, **green — 0 over-commits in 420 generations
   across levels 1/2/3/5/10/20**.

   **There are two budgets, and only one of them is the PF1 number.** `level_and_bab.update_level`
   builds them:

   | value | is | homebrew adds |
   |---|---|---|
   | `normal_feat_amount` | `ceil(level/2)` — the guarantee target the final trim at `main_test.py` enforces exactly | **+2 creation feats, folded in unlabelled** |
   | `flaw_feat_amount` | 0 | diminishing flaw grant (0→0, 1→1, 2→2, 3→2, 4→3) |
   | `story_feat_amount` | 0 | `1 + level//5` |
   | `flavor_feat_amount` | 0 | 1 (backstory) |
   | `feat_amounts` | — | the **sum**: the pool every chooser draws from |

   So at level 1 the RAW budget is 1 and the homebrew budget is **7**. Every subsystem reserves out
   of `feat_amounts` — i.e. out of the *homebrew* total, all four buckets, undifferentiated.

   **The evidence that forced the question.** 70 classes × 5 levels × 2 seeds = 700 generations: the
   `max(0, …)` reservation clamped in **16 (2.3%)**, **all of them at level 1**, worst overdraft
   **−2 feats**; the sibling clamp on `normal_feat_amount` never fired at all. Failing shape was
   always the same — ~5 sphere feats + 3 profession feats against a budget of 7. **The subsystems
   were sized as though the budget were a mid-level one.**

   **How each parameter resolved:**
   - **Sphere talents** — *were* a flat 8 at every level, a testing convenience that handed a 1st
     level the same eight as a 20th. Now **level-scaled**: `spheres.roll_talent_budget(level)` rolls
     0–8 under 5th, 0–12 under 10th, 0–16 under 20th, and `0–(level−4)` at 20th+ so the curve keeps
     climbing instead of flattening. The low end is a real 0 — rolling no talents is a legal outcome.
   - **Sphere feats** — the affordability the guarantee block already computed *was being thrown
     away*: `choose_spheres_attr` was never passed it, and its `max_feats` parameter was
     accepted-but-unused, so the feat count followed the talent count rather than the budget. It now
     takes **`max_budget_feats`** — what is left after PoW and professions take their share — and
     shrinks `budget_paid` until `feats_for_talents()` fits. **Talents nobody paid for are dropped,
     not granted**: HR1's whole point is that talents cost feats. Shrink-to-fit measures the actual
     magic/combat split rather than using a closed form, because 2 magic talents cost 2 feats (Basic
     Magic Training buys only one) while 2 combat talents cost 1 — a formula would assume the worst
     case and under-grant everyone to protect the edge.
   - **Profession feats** (True Calling / Multi Talented / Always Improving) — **on-budget**, and
     charged **once**, not twice: they are appended *after* the guarantee so they cannot be trimmed,
     which is why the reservation lowers `feat_amounts` *and* `normal_feat_amount` by the same count
     — the pool and the guarantee target move together, preserving `feat_amounts = normal + flaw +
     story + flavor`. `test_house_invariants.py` pins it: `normal_feat_amount == ceil(L/2)+2−prof`.
   - **PoW** — paid Martial Training picks and initiator style-chain bases are on-budget;
     mentor-funded ones (`_pow_funded_n`) are refunded because those feats move to the mentor's
     trainer group instead of the normal track. That split is the rule, not an accident.
   - **Rolls & ordering** — the magic-side bonus feats were rolled *after* the budget was spent, out
     of the same budget, so the budget was sized for the talents alone and then quietly overspent.
     They are now rolled **first** and dropped in favour of the talents when both will not fit:
     talents are the point of taking a sphere, the bonus feat is a flavour extra.
   - **Funding order, when the roll outruns the budget** — three levers, in order: what is left of
     the feat budget; then a *forced* Spheres Mentor when that falls short and trainers are on; then
     a halving when trainers are off, and another when the homebrew feat economy is off (both off
     quarters the roll). Measured at 20th: 6.9 talents → 3.6 → 3.4 → 1.6.

   **Still open — bucket earmarking.** `feat_amounts` is one undifferentiated pool, so a subsystem
   can spend a character's `story` / `flavor` / `flaw` feats as readily as its normal ones. Nothing
   currently says whether those buckets are *earmarked* for their own tracks. It stopped being urgent
   once the total fits, and it is invisible today because the trim only guarantees the general track
   — but it is the reason a heavily-subscribed character can end up with the right feat *count* and
   the wrong feat *mix*. No gate covers it.

   Note this was a genuine **behaviour** change — the only one on the scripts-and-phases map for
   which `--update` on the goldens was the correct response rather than a failure signal. Ticket 08
   chose option **C** (a gate, not a `FeatBudget` object) on the strength of the 2.3%/level-1
   measurement; the gate still prints `!! over-commits outside level 1` if the shape ever spreads,
   which is the evidence that would promote it to a real `FeatBudget` with `reserve()`/`grant()`.
5. **Skill alternate abilities** — allowed-ability sets per skill plus a chooser in `skill_ranks.py`.
6. ~~**Skill rank changes**~~ — DONE 2026-07-30: 2→4 rank floor (behind `misc_homebrew_rules`),
   3-ranks-per-level cap, +2/level background-only ranks in `skill_ranks.py` (the mental-ability
   pick already existed); the alternate-ability table remains #5.
7. ~~**Full HP**~~ — DONE 2026-07-30: max hit die every level in `hp_rolls.py::roll_hp` behind the
   homebrew flag (racial HD N/A — the generator never emits racial hit dice).
8. **Feat-tax prereqs** — relax prerequisite checks and default Weapon Finesse behaviour.
9. **Custom races** — add Loxo / Kalyptran / Dolistani to `PlayableRaces.json` (needs stat blocks,
   which the feat library does not carry).
10. **Flaws/traits** — the flaw→feat grant and the 8-pick-4 trait flow.
11. **Expose `misc_homebrew_rules` as a user input if ever needed** — the catch-all flag for
   homebrew rules too small for their own Yes/No question (currently: the 2→4 rank floor and the
   diminishing flaw-feat grant). Internal, defaults Y; owner: the `generate_random_char`
   signature + `skill_ranks.misc_homebrew_enabled`.

## Source coverage

**Deep-read** ✅ · **Indexed, not yet read** ⏳ — say which to expand and they can be pulled in.

| Sub-doc | Status | Relevance to generation |
|---|---|---|
| [Skills](https://docs.google.com/document/d/1laZ118hezgJ9AdwoXHPgKOnofRYYP7h-ciOSh54DrCE/edit) | ✅ | High |
| [Character Building](https://docs.google.com/document/d/1_OBzLlCCogTfzKdLOqhlHdQ-aZmWEXwiU3L68pV8yQI/edit) | ✅ | High |
| [Feats](https://docs.google.com/document/d/1H_5OzZSb5fd-tEkX7VYX85_aHrFjBsaESLlhwsoxJ3Q/edit) | ✅ | High |
| [Feat Tax / Exemptions](https://docs.google.com/document/d/1wv2IGBWFh4QUoCr_H5UtAsT1xxTVGNR1E_4sP-7_--w/edit) | ✅ | High |
| [Deities](https://docs.google.com/document/d/1uDLW8VEryGgC_YcvG58rn6ef0oLEtx3IhRGKkvqWFxM/edit) | ⏳ | Med (deity randomization) |
| [Rulesets/Fiats](https://docs.google.com/document/d/14EA3U5LZiBPIv0CzrcYv1--G368IcqaQ0lWSSVpXhOI/edit) | ⏳ | Med |
| [Combat References](https://docs.google.com/document/d/1ANXtDCF8-6gzV1GeRiMHHtRKFFbXA7i2SLZMCUv-zas/edit) | ⏳ | Med |
| [Luck](https://docs.google.com/document/d/1po0ieGEU2efK9iyj2QNeG0eeEyS9mXgIf6ptHE8v1pU/edit) | ✅ | **BUILT 2026-08-08** (generator side) — `class_func/luck.py`, spec §13; score, E-Kat feats, the 34 Luck Traits and the spent reserve; in-play d100 table still open |
| [Techniques](https://docs.google.com/document/d/1j7mPSoMalZE5wLs9wmwRzycNpyfNwCRhqOiCP2tG-iA/edit) | ⏳ | Med (Path-of-War-like) |
| [Spellcrafting](https://docs.google.com/document/d/1h5-RPODN97x-cs5cNkz10d65xY5-r1Y2mdikQQBbKC8/edit) | ⏳ | Med |
| [Oaths](https://docs.google.com/document/d/1v3XJO4avOaKbCf5xosZ-BHcVy2vFJPPK6RmL7_VkoSs/edit) | ⏳ | Low/Med |
| [Conditions](https://docs.google.com/document/d/133CtoP6L7NoqyA8W0znU5EfBz42LOSiXjmVPfV3X5yU/edit) | ⏳ | Low |
| [Troops](https://docs.google.com/document/d/1iPutxTRGx4JgfbYwgFLg0GcFDiPu4NXjzhXXIbPiExY/edit) | ⏳ | Low |
| [Factions](https://docs.google.com/document/d/11_gE9xAKife4Ka4ORO6VuT_wxVllV_TlKFotdXGv4rA/edit) | ⏳ | Low |
| [Calendar](https://docs.google.com/document/d/1Oh2bl9dfPQfimwmjQdL0NQWI23n6t-DEJ59WXL76ClE/edit) | ⏳ | Low |
| [Character Sheet Macros](https://docs.google.com/document/d/1IX2yRzDgke-ux4UFvxINef-njjWRhL5v8SlCsqbBTnc/edit) | ⏳ | Low |
| [Maps (Dropbox)](https://www.dropbox.com/sh/km9anbv8zxvw209/AADd7pHWrwkoIaCSy-isbb2ia?dl=0) | ⏳ | None |
