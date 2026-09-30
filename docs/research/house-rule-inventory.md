# House-rule inventory: what a strict-RAW profile must switch off

Question: which Sieg's Guide house rules does the generator apply to a generated character, and is each
GATED (by which request key) or ALWAYS ON? Method: code read of `Backend/` (primary source), cross-checked
against `docs/homebrew_rules.md` and the OKF leaves `oks/pathfinder/house-rules/*` (read-only clone).
Where they disagree the code wins.

## Headline finding

**`house_rules` is NOT the house-rule master switch.** `app.py` pops it from the request and
`power_role.phase_power_role` lands it as `role['_house']`. It only gates the *V4 optimized-wall AC kickers*,
and is inert unless `optimize` produced a role. Nearly every other house rule hangs off a different gate,
or off none:

| Real gate | Request key / default | Read via |
|---|---|---|
| `homebrew_feat_amount` | positional input #14, "Y" = on | `skill_ranks.homebrew_enabled(character)` |
| `misc_homebrew_rules` | named key, default "y" | `skill_ranks.misc_homebrew_enabled(character)` |
| `house_rules` | named key, default None (off) | `power_role` -> `role['_house']` (needs `optimize`) |
| `professions` / `trainers` | named keys, default "y" | `professions_enabled` / `trainers_enabled` in `main_test.generate_random_char` |
| `spheres_of_power` | named key, default "n" (opt-in) | `character.spheres_flag` |
| `mythic` | named key, absent = never | `character.mythic_request` |
| `inherents` | positional input, "Y" = on | `stats.roll_stats(inherent_flag)` |

Legend: **G:hr** = gated by `house_rules`; **G:hfa** = `homebrew_feat_amount`; **G:misc** =
`misc_homebrew_rules`; **G:other** = another named gate; **ALWAYS** = no gate.

## Inventory

| # | Rule | Where in code | Gate | What RAW does instead |
|---|---|---|---|---|
| 1 | Full (max) hit die every level | `hp_rolls.py::roll_hp`; companions `companion_stats.py::_hit_points` | G:hfa | Roll each HD (first class level 1 maxed) |
| 2 | +2 creation feats | `level_and_bab.py::update_level` (folded into `normal_feat_amount`) | G:hfa | No bonus feats at creation |
| 3 | Story feats, `1 + level//5` | `level_and_bab.py::update_level` (`story_feat_amount`) | G:hfa | None |
| 4 | Backstory "flavor" feat (1) | `level_and_bab.py::update_level` (`flavor_feat_amount`) | G:hfa | None |
| 5 | Flaw -> bonus-feat grant, diminishing (0/1/2/2/3) | `level_and_bab.py::update_level` (`flaw_feat_amount`); `companion_feats.py` ~431 | G:misc | No flaw feats |
| 6 | Skill-rank floor 2 -> 4 per level | `skill_ranks.py::class_skill_points` | G:misc | Class value as printed |
| 7 | 3 ranks/level per-skill cap | `skill_ranks.py::per_skill_cap` | G:hfa | Max ranks = character level |
| 8 | +2 background-only ranks/level | `skill_ranks.py::assign_background_ranks` | G:hfa | None |
| 9 | Metzofitz homebrew feats join the General/Combat pool | `feats.py::generic_feat_chooser` + `metzofitz_feat_frame` | G:hfa | AoN/Paizo feat list only |
| 10 | Luck subsystem (score, E-Kat slots, E-Kat feats, Luck Traits, buyer/seller stake) | `main_test.py::phase_luck_stake`, `phase_luck_resolution`; `class_func/luck.py` | G:misc (stake+resolution); E-Kat reserve also G:hfa | No luck stat |
| 11 | Mythic grant | `mythic.py`; `main_test.py::phase_mythic_stake` | G:other (`mythic`) | Optional RAW system; request-only |
| 12 | Spheres of Power/Might dabbling (talent budget halved if trainers or feat economy off) | `spheres.py::randomize_spheres_num`; `main_test.py::phase_path_of_war_and_spheres` ~1366-1371 | G:other (`spheres_of_power`) | No Spheres |
| 14 | Professions (ranks, abilities, profession feats) | `profession_chooser.py`, `profession_abilities.py`; `main_test.py::phase_professions_and_skills` | G:other (`professions`) | Profession is an ordinary skill |
| 15 | Trainers/mentors (trainer feat slots, PoW and Spheres mentors) | `trainers.py`; `main_test.py::phase_feat_tax_and_swaps` | G:other (`trainers`) | No mentors |
| 16 | Strength of a Warrior (Con)/(Str) forced into the wall feat spine; baked natural-armor change | `power_roles.json::feat_spine_house`; `power_role.py::role_feat_spine`; bake at `main_test.py` ~3104-3117 | G:hr for the pick (bake unconditional but inert unless placed; see A2) | Not in RAW |
| 17 | Sword-and-board counts as two weapons: TWF + Two-Weapon Defense in wall spine | `power_roles.json::feat_spine_house`; `role_feat_spine` | G:hr | Shield does not count as a weapon |
| 18 | Cautious Warrior trait (+1 dodge defending) forced into wall traits | `traits.py::HOUSE_WALL_TRAIT`, `trait_selector` | G:hr | Not in `traits.csv`; never drawn |
| 19 | Defensive sphere forced onto the wall (talent floor 2) | `spheres.py::_house_wall`, `randomize_spheres_num`; `main_test.py` ~1376 | G:hr | No sphere unless `spheres_of_power` |
| 21 | Path of War base initiator classes in the random class pool + martial paths via Martial Training chain | `path_of_war.py`; `main_test.py::phase_path_of_war_and_spheres` | **ALWAYS** | Not Paizo RAW (3pp) |
| 22 | Free combat feats at BAB >= 1 (Power Attack, Deadly Aim, Combat Expertise, Piranha Strike): never spend a slot, treated as owned for prereqs | `feat_skill_choice.py::FREE_AT_BAB1`, `filter_free_feats`; seeded `main_test.py` ~1172 | **ALWAYS** | Must be bought; Str/Dex 13 + BAB prereqs |
| 23 | Feat-tax waiver: `tax_primary_blocklist` (power attack, combat expertise, dodge, weapon finesse, improved unarmed strike, critical focus) are not tax primaries and do not count as prereqs in chain derivation | `feat_tax.py::feat_tax_func`, `_is_primary`; data `json/feat_tax.json` | **ALWAYS** | Ordinary feats and ordinary prerequisites |
| 24 | Feat-tax chains: a primary bundles its prereq/follow-up feats free (one free chain feat per 2 levels held; "Extra X" gives a duplicate) | `feat_tax.py::feat_tax_func` (`_derive_chain`); call sites in `main_test.py::phase_feat_tax_and_swaps` incl. `pw.*_feat_tax` merges | **ALWAYS** (only budget size is G:hfa) | Every feat costs a slot |
| 25 | Prereq fragments auto-satisfied (`FILTER_WORDS`: ranks, skill, cast, proficiency, power attack, ...) | `generic_func.py::FILTER_WORDS`, `no_prereq_prep` | **ALWAYS** (see A1) | Prereqs enforced |
| 26 | Skill Focus / Prodigy pointed at professions; bonus recorded on the profession | `feat_skill_choice.py::specialize_skill_choice_feats` | G:other (only when a profession exists, i.e. `professions`) | Any skill; Skill Focus +3/+6 |
| 27 | Mechanical flaws (1st minor, 2nd major, extras 80/20) replacing personality flaws; emit pf1 changes | `flaws.py::flaw_chooser`, `json/flaws/flaw_effects.json`; `main_test.py` ~376-380 (`randomize_flaw_amount` 0-4) | **ALWAYS** (the feat grant, #5, is G:misc; the flaws are not) | Flaws are an Unchained opt-in; default none |
| 28 | 8-trait pool draw | `traits.py::trait_selector`; `main_test.py` ~1066 `trait_selector(character, 8)` | **ALWAYS** | 2 traits (APG) |
| 29 | Free Unchained Skill Unlock for one ranked skill | `skill_unlocks.py::choose_skill_unlock`; call `main_test.py` ~2650 | **ALWAYS** | Optional Unchained rule; none |
| 30 | Hero Points pool (random 0-3) | `hero_point_generator.py`; `main_test.py` ~1068 | **ALWAYS** (luck may add, G:misc) | Optional rule; starts at 1 |
| 31 | Stat inherents + level-up bumps on total level | `stats.py::roll_stats`, `roll_inherents_func`, `level_up_stats` | G:other (`inherents`, default Y) | None |
| 33 | Combined + low-3 caster level for spell riders | **Not in backend.** Authored `@spells.primary.cl.total`; expanded by `spellCLExpr()` in the Foundry module and applier repos (`changelog.md` ~3532-3657) | **ALWAYS** in those sibling repos | Per-class caster level |
| 34 | House trackers (`house_features.json`, e.g. Death HP Pool) | **Not in this repo** (no file, no `house_features` reference under `Backend/`); module/sheet side | **ALWAYS**, outside backend | No trackers |

Row numbers skip 13, 20, 32, 35, 36 deliberately (kept stable for cross-reference; excluded from tallies):
- 13: folded into row 12.
- 20: `power_roles.json::margins_house` band is a *measurement* (`power_metric.py`), not a character rule. Note
  `power_metric.py::waived_feats/ambient_feats` only *models* the waiver in row 23; it does not apply it.
- 32: optimized stat placement by role (`stats.py` + `power_role.stat_order`, G:other `optimize`) is a tool
  feature, not a house rule.
- 35: homebrew races (Loxo, Kalyptran, Dolistani) are NOT implemented (absent from `PlayableRaces.json`;
  `races.json` only has an unrelated "Loxophant"). Nothing to switch off.
- 36: alternate ability per skill; proficiency <-> Martial Tradition trade; Metzofitz initiator classes and PoW
  archetypes are backlog per `docs/homebrew_rules.md`; not implemented.

## Tally

Character-affecting implemented rules: **31** (rows 1-12, 14-19, 21-31, 33, 34).

- Gated by `house_rules` (G:hr): **4** (rows 16, 17, 18, 19).
- Gated by some other key: **16** (rows 1-12, 14, 15, 26, 31).
- **ALWAYS ON: 11** (rows 21, 22, 23, 24, 25, 27, 28, 29, 30, 33, 34; rows 33 and 34 live outside `Backend/`).

## Always-on rules: a RAW run cannot exist until these are gated

1. Free combat feats at BAB >= 1 (row 22): `FREE_AT_BAB1` seeded into `chooseable` unconditionally.
2. Feat-tax waiver blocklist (row 23): `feat_tax.json::tax_primary_blocklist`.
3. Feat-tax chains (row 24): `feat_tax_func` runs regardless of `homebrew_feat_amount`; turning the budget off
   still bundles chains.
4. Prereq auto-satisfaction list (row 25): `FILTER_WORDS`.
5. Mechanical flaws (row 27): `flaw_chooser` called unconditionally; only the feat grant is gated.
6. 8-trait draw (row 28).
7. Free skill unlock (row 29).
8. Hero points pool (row 30).
9. Path of War in the random class pool / martial paths (row 21): no request key at all.
10. Combined + low-3 caster level (row 33): Foundry module/applier, outside this repo.
11. House trackers (row 34): module/sheet side, outside this repo.

## Ambiguities and traps

- **A1. FILTER_WORDS mixes engine limitation and house waiver.** "cast", "ranks", "skill" are parser gaps,
  not rules; only "power attack", "combat expertise", "piranha strike" are deliberate waivers. A RAW profile
  needs the list split.
- **A2. Strength of a Warrior is a real Sieg's Guide feat, not only a wall kicker.** `house_rules` gates only
  the *forced spine pick*; whether the feat row is reachable by the ordinary chooser (with
  `homebrew_feat_amount=Y`, optimize off) is unverified, and if so the ~3104 bake applies. Needs a corpus check.
- **A3. `homebrew_feat_amount=N` does not give RAW feats.** It removes rows 1-4, 7-10 but NOT 22-25 (feat-tax
  machinery is independent).
- **A4. `house_rules` is inert without `optimize`** (role is None): `house_rules=true` alone changes nothing,
  and "house_rules off" says nothing about the feat economy. Default generation is house-on everywhere except
  the wall kickers.
- **A5. Luck (row 10) has two gates.** Stake/resolution follow `misc_homebrew_rules`; the E-Kat reserve follows
  `homebrew_feat_amount`. Setting only one yields a partial luck state.
- **A6. Path of War has no opt-out;** Spheres is opt-in. Both are 3pp, not RAW.
- **A7. Skill unlock level.** The OKF leaf says level 5+; `choose_skill_unlock` itself has no level check (a
  gate may sit at the call site; unverified).
- **A8. Not found in `Backend/`:** Stamina-for-fighters and Wound Thresholds/Death HP Pool (OKF
  `optional-systems.md`); treated as module/sheet side.
- **A9. Stale doc:** `CLAUDE.md` says Metzofitz feat selection is "still commented out" in `feats.py`; the code
  shows it live behind `homebrew_enabled` (`docs/homebrew_rules.md` backlog #1 says DONE 2026-07-30).

## Sources

`Backend/app.py` (`update_character_data`), `Backend/main_test.py` (`generate_random_char` + phases),
`Backend/utils/class_func/{power_role,level_and_bab,skill_ranks,hp_rolls,feats,feat_tax,feat_skill_choice,
generic_func,flaws,traits,stats,skill_unlocks,hero_point_generator,spheres,companion_stats}.py`,
`Backend/json/{power_roles,feat_tax}.json`, `Backend/scripts/power_metric.py` (measurement only),
`docs/homebrew_rules.md`, OKF `oks/pathfinder/house-rules/*`.
