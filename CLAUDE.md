# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this project is
**Pathfinder 1E Randomized Character Generator** — a Python/Flask backend that generates complete,
random Pathfinder 1E NPCs from 12 inputs (region, race, class, multiclass, alignment, feat
randomization, gender, stat dice count/size, level range, starting gold) and returns them as JSON.

- **Entry points:** `Backend/main_test.py` (`generate_random_char()`, CLI smoke test) ·
  `Backend/app.py` (Flask `POST /update_character_data`) · `Backend/start_py.py` (app factory).
- **Generation logic:** ~55 modules in `Backend/utils/class_func/` (feats, spells, stats, class
  abilities, armor/weapon chooser, skill ranks, …); character state in
  `Backend/utils/createACharacter.py`; static data in `Backend/utils/data.py`.
- **Game data:** webscraped from Archive of Nethys, d20SRD, and the Metzofitz homebrew library →
  JSON in `Backend/json/` and CSVs in `data/` (incl. `data/Metzofitz_Feats.csv`).
- **Consumers:** the FoundryVTT module `pf1e_random_char_generator` POSTs to the deployed backend
  (Render) and injects the result as a Foundry Actor; the "awesome sheet" frontend renders sheets.
- **Homebrew status:** a story-feats flag exists; Metzofitz feat selection is still commented out in
  `Backend/utils/class_func/feats.py`; Path of War / Spheres / Mythic / homebrew races are in progress.

## Run / test
```
pip install -r requirements.txt
python Backend/main_test.py     # CLI smoke test — generate a character
python Backend/app.py           # Flask server (HTML/JSON view)
```

## Working conventions
- **Session goals:** at the start of each coding session, (re)write `SESSION_PLAN.md` with this
  session's goals. It is ephemeral and git-ignored — delete and recreate it each session.
- **Changelog:** record every user/developer-visible change in `changelog.md` under `## [Unreleased]`.
  See the `changelog` skill (`.claude/skills/changelog/`).
- **Commits:** follow the `commit-conventions` skill (`.claude/skills/commit-conventions/`) —
  Conventional Commits, atomic commits, GitHub Flow, no secrets. Only commit/push when asked;
  branch off `main` first.
- **Homebrew rules:** `docs/homebrew_rules.md` catalogs this campaign's house rules (from "Sieg's
  Guide") and maps each to where it plugs into the generator — treat it as the source of truth for the
  homebrew feats / skills / races this project targets. It also lists sub-docs not yet deep-read.
