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
| Bonus feats at creation, flavor & story feats | `house-rules/feat-economy.md` | `level_and_bab.py` |
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
3. **Skill alternate abilities** — allowed-ability sets per skill plus a chooser in `skill_ranks.py`.
4. ~~**Skill rank changes**~~ — DONE 2026-07-30: 2→4 rank floor (behind `misc_homebrew_rules`),
   3-ranks-per-level cap, +2/level background-only ranks in `skill_ranks.py` (the mental-ability
   pick already existed); the alternate-ability table remains #3.
5. ~~**Full HP**~~ — DONE 2026-07-30: max hit die every level in `hp_rolls.py::roll_hp` behind the
   homebrew flag (racial HD N/A — the generator never emits racial hit dice).
6. **Feat-tax prereqs** — relax prerequisite checks and default Weapon Finesse behaviour.
7. **Custom races** — add Loxo / Kalyptran / Dolistani to `PlayableRaces.json` (needs stat blocks,
   which the feat library does not carry).
8. **Flaws/traits** — the flaw→feat grant and the 8-pick-4 trait flow.
9. **Expose `misc_homebrew_rules` as a user input if ever needed** — the catch-all flag for
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
| [Luck](https://docs.google.com/document/d/1po0ieGEU2efK9iyj2QNeG0eeEyS9mXgIf6ptHE8v1pU/edit) | ⏳ | Med (hero points / E-Kat feats) |
| [Techniques](https://docs.google.com/document/d/1j7mPSoMalZE5wLs9wmwRzycNpyfNwCRhqOiCP2tG-iA/edit) | ⏳ | Med (Path-of-War-like) |
| [Spellcrafting](https://docs.google.com/document/d/1h5-RPODN97x-cs5cNkz10d65xY5-r1Y2mdikQQBbKC8/edit) | ⏳ | Med |
| [Oaths](https://docs.google.com/document/d/1v3XJO4avOaKbCf5xosZ-BHcVy2vFJPPK6RmL7_VkoSs/edit) | ⏳ | Low/Med |
| [Conditions](https://docs.google.com/document/d/133CtoP6L7NoqyA8W0znU5EfBz42LOSiXjmVPfV3X5yU/edit) | ⏳ | Low |
| [Troops](https://docs.google.com/document/d/1iPutxTRGx4JgfbYwgFLg0GcFDiPu4NXjzhXXIbPiExY/edit) | ⏳ | Low |
| [Factions](https://docs.google.com/document/d/11_gE9xAKife4Ka4ORO6VuT_wxVllV_TlKFotdXGv4rA/edit) | ⏳ | Low |
| [Calendar](https://docs.google.com/document/d/1Oh2bl9dfPQfimwmjQdL0NQWI23n6t-DEJ59WXL76ClE/edit) | ⏳ | Low |
| [Character Sheet Macros](https://docs.google.com/document/d/1IX2yRzDgke-ux4UFvxINef-njjWRhL5v8SlCsqbBTnc/edit) | ⏳ | Low |
| [Maps (Dropbox)](https://www.dropbox.com/sh/km9anbv8zxvw209/AADd7pHWrwkoIaCSy-isbb2ia?dl=0) | ⏳ | None |
