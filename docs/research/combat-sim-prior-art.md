# Combat-simulator "judge": monster data and prior art

Question: what does a Monte Carlo PF1e combat judge need (solo character vs one CR = level-1
monster; and an "adventuring day" of several fights between rests), and what data and prior art exist?

Method: read this repo, read the FoundryVTT pf1 system packs and the `statblock-library` module
packs (copied to scratch, read with `classic-level`; read-only), plus web search. Claims marked
(unverified) come from search snippets or README pages only, not from reading source.

## 1. Monster data

### (a) In this repo
- `Backend/json/cr_benchmarks.json` is the only monster-by-CR data. Rows are the Bestiary
  "Monster Statistics by CR" table (CR 1/2-30 published, 31-39 flagged `extrapolated`).
  Columns (`_fields`): `hp, ac, attack_high, attack_low, damage_high, damage_low, dc_primary,
  dc_secondary, save_good, save_poor`. Consumed by `Backend/scripts/power_metric.py` (the scorer).
- No bestiary, stat blocks, DR/SR, speeds, or special abilities anywhere in `Backend/json/` or
  `data/` (checked the directory listings; `animal_companion.json`, `pf_content_companions.json`,
  `eidolon_*.json` are PC-side companions, not a monster list).

### (b) FoundryVTT pf1 system packs (`systems/pf1/packs`)
- `basic-monsters`: only **15 actors / 240 embedded items** (396 KB). Base creature shells for the
  system, not a bestiary. Useless as an opponent pool.
- `monster-abilities`, `monster-templates`, `racial-hd`, `template-abilities`: ability / template /
  racial-HD *items*, not whole creatures. Useful later for tier 2 (ability text, HD tables).
- The system ships **no bestiary**.

### (c) `statblock-library` module (already installed locally) - the real source
`Data/modules/statblock-library` (baileymh, v0.8.0, 33 MB, advertises ~10,000 statblocks from 200+
books). Packs are LevelDB **journals** (one journal per monster, title `Name (CR n)`), each with a
page of type `statblock-library.statblock` whose `content` is **HTML of the standard Paizo stat
block** (not Foundry actor data; meant to be imported via `pf1-statblock-converter`, "SBC").
Counts by journal title (includes a few non-monster / no-CR entries):

| Pack | Journals | Notes |
|---|---|---|
| `sb-bestiaries1-3` | 957 | CR 1/8..25; CR 1-12 have 35-93 each |
| `sb-bestiaries4-6` | 793 | CR 1..30; CR 1-18 have 24-53 each; 4-8 per CR at 22-30 |
| `sb-occult-bestiary` | 40 | |
| `sb-mythic-monsters` | 57 | titled `CR 9/MR 3` style; needs mythic rules |
| other packs | not counted | `sb-monsters-dragons`, `sb-npcs-and-villians`, adventure-path NPCs, PFS, ... |

So Bestiaries 1-6 alone give roughly **30-90 monsters per CR for CR 1-18**, thinning to ~5-20 at
CR 19-30. Enough to sample per CR with variety.

Record structure (verified on Giant Octopus, Cameroceras, Xulgath): labelled HTML `<strong>` fields
with stable, regexable text:
- `AC 18, touch 11, flat-footed 16 (+2 Dex, +7 natural, -1 size)`
- `hp 90 (12d8+36)` (fast healing / regeneration appended on the same line)
- `Fort +11, Ref +12, Will +7`; separate `DR 5/epic`, `SR`, `Immune`, `Resist`, `Defensive Abilities`
- `Melee bite +13 (1d8+5 plus poison), 8 tentacles +11 (1d4+2 plus grab)`, alternate routines after
  `or`; crit range/multiplier inline (`1d8+6/x3`, `4d8+9/19-20`)
- `Base Atk`, `CMB`, `CMD`, ability scores, feats, `Special Attacks`, spell-like abilities and spell
  blocks (`Psychic Magic (CL 6th; concentration +7) ...`), and a SPECIAL ABILITIES prose section

Simulatability:
- **High (regex)**: AC (total/touch/flat-footed), HP, saves, BAB/CMB/CMD, melee and ranged
  full-attack strings with damage dice and crit range, DR, SR, speed, size/type/reach.
- **Medium**: riders after "plus" (poison, grab, bleed, energy dice) - a small vocabulary covers
  most (extra dice, grab -> grapple, poison -> ability damage vs save); long tail is prose.
- **Low**: spell-like abilities/spells (names + DCs; needs a spell-effect table) and special
  abilities (breath weapon, gaze, aura, swallow whole, rend ...).
- Parsing is **not done for us**: SBC converts to pf1 actors but needs a running Foundry. Offline we
  write our own HTML-to-dict parser (BeautifulSoup/regex). Licensing: stat blocks are OGL; check the
  module's shipped license before committing derived JSON (generate into a git-ignored file, or
  commit only aggregated per-CR profiles).

### (d) Public datasets (web)
- **c0d3rman/PathfinderMonsterDatabase** - "all monsters in Pathfinder 1e", parsed from aonprd.com,
  `data.json`; README describes structured fields (AC components, HP, saves, attacks as objects with
  bonus/damage, feats, skills, speeds). Broader than Bestiary 1-6 (NPCs, mythic). No license stated.
  (unverified: monster count, per-field accuracy; only the README summary was read.) Worth a spike if
  our own HTML parser proves painful.
- **PSRD-Data (Devon Jones)** - d20PFSRD scrape to JSON via PSRD-Parser (unverified detail). Older.
- **edwardloveall/bestiary** - Bestiary parser into a relational DB (unverified completeness).
- Archives of Nethys itself (JSON behind the site) was not evaluated; ToS unknown.

## 2. Prior art

Nothing found is reusable as our judge; several are shape references. Only landing pages were read,
so "models X" means advertised or visible in file layout, not audited.

| Project | Ruleset | What it visibly models |
|---|---|---|
| Idran/Pathfinder-Combat-Simulation | PF1e (Python, 83 commits) | combat, character, spells, special attacks, equipment, AI, battle map modules. Most complete PF1 attempt found; crit/iterative handling not confirmed (unverified) |
| dwwaite/dpr_simulator | D&D 5e / PF (Rust) | damage per round over a sweep of AC values; a round = a set of attacks. Closest to our `power_metric` DPR model |
| kenfar/CombatWiz | THAC0-era (Python 2) | 2-sided Monte Carlo from a creatures CSV (HP/AC/to-hit/damage); basic, dated |
| lewasaur, andrei-gorbatch, AndHilton | 5e | 1v1 / small-party encounter Monte Carlo with fixed attack routines; references for sample size and estimate stability |
| gradunza5/MCT | PF1 mass combat | army-level, not applicable |
| MrSWagner/Pathfinder | PF1 | "battle simulator" (no detail read) |
| Thunderhead blog, "Monte Carlo Simulations in Pathfinder" | PF1 | not read; background only |

What none of them is shown to give us (we must design it): save-or-lose spells against a
monster-side save table, summons/companions as extra actors, per-day resource depletion across a
multi-fight day (slots, rage rounds, PoW maneuvers/stances, limited items), and an action-economy
policy (full attack vs move vs buff round). Those decide caster-vs-martial ranking, so they cost the
most design effort.

## 3. Fallback: `cr_benchmarks.json` as a generic monster per CR

Yes, as **tier 0**, with caveats:
- Gives a complete generic body per CR: `hp`, `ac`, best/worst attack bonus, best/worst damage,
  `dc_primary/secondary`, `save_good/save_poor`. The table's attack/damage are **per-round totals**,
  not per hit, so the sim must choose a split (e.g. two attacks at `attack_high`, half damage each,
  or one attack with a flat hit chance) and assume which saves are good.
- Missing: attack count and iteratives, crit range/multiplier (assume 20/x2), DR, SR, touch and
  flat-footed AC, speed/reach, resistances, regeneration, any special ability, spellcasting. It is
  the Bestiary *average*; real monsters scatter widely around it (AC/HP roughly +/-30%, judgement).
- Rows 31-39 are extrapolated and flagged; a judge must surface that flag.
- Precedent: `power_metric.py` already benchmarks against this table, so a tier-0 sim and the static
  scorer share a target and can cross-check each other (ordering by `dpr_expected` vs `ac`/`hp`
  should agree; disagreement is a bug in one of them).

## 4. Recommendation

**Monster source:** build a normalised `monsters_by_cr` JSON by parsing the Bestiary 1-6 (+ Occult)
journals in `statblock-library` (on disk, OGL, 30-90 monsters per CR for CR 1-18). Keep it out of git
or commit only derived per-CR aggregates. Keep `cr_benchmarks.json` as the tier-0 fallback and as the
CR 19-39 gap-filler. Spike c0d3rman's JSON as a parser substitute before writing our own.

**Fidelity tiers**
- **Tier 0 - benchmark row.** One generic monster per CR from `cr_benchmarks.json`. First win-rate
  signal; validates the sim loop against the static scorer. Smallest effort. Reuses `power_metric`
  AC/save/DPR helpers.
- **Tier 1 - sampled real stat blocks, melee/ranged only.** Parse AC/touch/FF, HP, saves, full-attack
  routines (iteratives from the monster's own list, crit range), DR, SR (ignored vs martials, matters
  for casters later), speed. Filter or down-weight monsters whose CR rests on abilities the sim
  cannot do (proxy: length of unparsed Special Attacks / spell-like text). Sample N monsters per CR,
  report win rate, rounds-to-kill, resources used. Recommended first real judge.
- **Tier 2 - abilities and spells.** Breath weapons, gaze/poison/disease, grab/constrict,
  regeneration, spell-like abilities via a small effect table; PC save-or-lose spells vs real monster
  saves; summons/companions as extra actors; the adventuring day (3-5 fights, resource depletion,
  rest rule). Needs the tier-1 parser plus a curated ability vocabulary.

**PC side (all tiers):** the generated payload already carries the pieces (`dpr_raw`, `burst_raw`,
`ac_combat`, buff toggles, conditionals). The judge needs an action-policy layer (full attack vs buff
vs nova) and must read the same buff state the scorer reads, not keep a second copy.

## 5. Gaps and risks
1. **No structured monster data in-repo.** A parser for the SBL HTML (or the c0d3rman JSON) is the
   critical-path task. Expect malformed blocks (templates, "or" routines, mythic variants); add a
   "parsed OK" percentage gate in the style of `Backend/scripts/validate_*.py`.
2. **Licence**: confirm OGL status of the SBL module and c0d3rman's source before committing data.
3. **CR is not difficulty.** Single-target melee fights under-rate casters; monsters with nasty
   abilities (save-or-die, flight, invisibility, swallow whole) are mis-rated by melee-only tier 1.
   Report per-archetype, not only a scalar score.
4. **Buff assumptions** must match how `power_metric` sets `dpr_raw` vs `burst_raw`, or the two
   judges disagree for reasons unrelated to the character.
5. **Mythic / Path of War / Spheres / homebrew** PC features need sim-side rules; PoW stances and
   maneuver readying are per-day resources that belong to the adventuring-day tier.
6. **Positioning, mounts, terrain** are out of scope; assume adjacent 1v1.
7. **Variance**: fix and record seed and N per (character, CR) for reproducible runs.
8. **Not verified here**: Idran's exact mechanics, the c0d3rman database size and accuracy, AoN JSON
   endpoints, the Thunderhead article.

## Sources
- https://github.com/c0d3rman/PathfinderMonsterDatabase
- https://github.com/baileymh/statblock-library (and the local module copy)
- https://github.com/Idran/Pathfinder-Combat-Simulation
- https://github.com/kenfar/CombatWiz
- https://github.com/dwwaite/dpr_simulator
- https://github.com/lewasaur/simplified-dnd-monte-carlo-combat-simulator
- https://github.com/andrei-gorbatch/monte_carlo
- https://github.com/gradunza5/MCT
- https://www2.thunderheadeng.com/2018/06/monte-carlo-simulations-in-pathfinder/
