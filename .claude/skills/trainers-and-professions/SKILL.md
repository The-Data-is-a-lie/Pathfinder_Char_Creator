---
name: trainers-and-professions
description: Homebrew "trainers" and "professions" as character-progression sources in this Pathfinder 1e generator — trainers grant a tier of bonus feats (2 common / 3 rare / 4 mythical); professions grant abilities and sometimes feats. Use when adding or refining trainer feat grants or profession abilities, or wiring them into NPC generation. WORK IN PROGRESS — captures the current rough model, to be refined later.
---

# Trainers & Professions (homebrew progression) — WORK IN PROGRESS

> **Status:** This is the rough, current understanding only — the general idea to build on. It is
> **not yet implemented** in the generator and **will be refined substantially later**. Treat the
> numbers below as the starting model, not final rules.

Two homebrew sources of character growth beyond class/race/level: **trainers** (who teach feats)
and **professions** (who confer abilities). Both should eventually layer onto the generated NPC.

## Trainers

A **trainer** grants **bonus feats**, with the count scaled by how exceptional the trainer is:

| Trainer caliber | Bonus feats |
|---|---|
| Ordinary (most common) | **2** |
| Exceptional (rare) | **3** |
| Mythical / legendary | **4** |

- These stack **on top of** normal feat progression — same spirit as the homebrew creation/flaw
  bonus feats in `docs/homebrew_rules.md §1` (e.g. "+2 bonus feats at character creation").
- A trainer's feats are usually **themed** to what they teach (a weapons master → combat feats,
  etc.), and may form a small chain. The precedent for injecting extra feats *plus* a hand-built
  feat-tax bundle (so prerequisite chains resolve) is the Path of War wiring — see the
  **path-of-war** skill (`mt_feat_tax` / `style_feat_tax`).

## Professions

A **profession** grants **cool abilities** — sometimes a bonus feat, sometimes a unique ability
tailored to that character/profession. The existing campaign model
(`docs/homebrew_rules.md §2b`):

- Profession is an expanded sub-system: **rank cap 5 + CR** (individual cap **10**), **income** =
  ½ Profession check in gp/week.
- **Associate-skill unlocks** at ranks **1 / 4 / 7 / 10**; a **GM trait at rank 5**; a **hero point
  at rank 15**.
- A **"Trainer" profession** specifically "can grant feats/traits/stats" — i.e. the trainer concept
  above is one profession among many.
- "Gather Information" = a Cha-based subcategory of Knowledge (Local), +½ Know. (Local) ranks.
- Related feats: **True Calling**, **Multi Talented**, **Always Improving** (in
  `data/Metzofitz_Feats.csv`).
- If Profession would already be a class skill, instead get **+1 to all Professions**
  (`docs/homebrew_rules.md §2`).

## Where this will plug in (pointers — do not wire yet)

- `Backend/json/profession.json` — ~538 profession names (already includes trainer roles like
  "Animal Trainer", "Horse trainer", "Master of arms").
- `Backend/utils/class_func/profession_chooser.py` — current **stub** (randomly samples 1–3
  profession names; comment flags it for a rewrite). The natural home for selecting a
  trainer/profession and its caliber.
- Feat budget: `character.feat_amounts` is assembled in `Backend/utils/class_func/level_and_bab.py`
  and consumed by `Backend/utils/class_func/feats.py`. Trainer bonus feats would be **added to that
  budget** (or appended like the PoW paid picks in `Backend/main_test.py`).
- Specs: `docs/homebrew_rules.md §2b` (profession sub-system) and `docs/feature_spec_todo.md §5`
  (free-feats backlog, awaiting design input).

## Open questions for later

- How is a trainer's **caliber** rolled / selected, and how often does an NPC have a trainer at all?
- Do trainer-granted feats **ignore prerequisites** (like a feat-tax grant), or must they be legal?
- How do professions map to **concrete abilities** — a curated table per profession, or generic
  "pick a themed feat/ability"?
- How do trainer/profession grants interact with the per-level feat assignment and the Foundry
  export?
