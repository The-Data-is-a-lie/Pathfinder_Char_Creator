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
  `Backend/utils/class_func/feats.py`; **Path of War is wired in** (six base initiator classes in the
  random pool + "martial paths" via the Martial Training chain for everyone else —
  `Backend/utils/class_func/path_of_war.py`, spec in `docs/feature_spec_todo.md` §1; Metzofitz
  initiator classes & PoW archetypes pending); Spheres / Mythic / homebrew races are in progress.

## Run / test
```
pip install -r requirements.txt
python Backend/main_test.py     # CLI smoke test — generate a character
python Backend/app.py           # Flask server (HTML/JSON view)
```

## Working conventions
- **Codebase map:** `docs/CODEBASE_MAP.md` is the "where do I find X" appendix (pipeline order,
  class-choice bucket → data-file table, JSON/module/script indexes, gotchas). Read it BEFORE
  searching the codebase, and update it whenever files, pools, or pipelines move.
- **Session goals:** at the start of each coding session, (re)write `SESSION_PLAN.md` with this
  session's goals. It is ephemeral and git-ignored — delete and recreate it each session.
- **Issue tracker:** issues, PRDs and `/wayfinder` maps live as **GitHub issues** on
  `The-Data-is-a-lie/Pathfinder_Char_Creator`, not as markdown files. Operations (map, child
  tickets, native blocking, frontier query) are in `docs/agents/issue-tracker.md`. `gh` is portable
  at `$env:LOCALAPPDATA\Programs\gh\bin\gh.exe`, not on PATH.
- **Domain knowledge:** this repo has **no `.claude/skills/`** — the Pathfinder/generator knowledge
  that used to live there (Path of War, Spheres, trainers & professions, conditionals, buffs/sheet
  references, profession genres, changelog & PR conventions) was consolidated into the **OKF
  `pathfinder` bundle**. Reach it via the user-level `oks-bundles` skill, which routes to
  `oks/pathfinder/index.md` (local clone: `C:/Users/Daniel/okf-bundles`; the repo is private, so
  `WebFetch` on its raw URLs fails — read the clone or use `gh api`).
- **Changelog:** record every user/developer-visible change in `changelog.md` under `## [Unreleased]`,
  Keep a Changelog format (Added/Changed/Deprecated/Removed/Fixed/Security), written from the
  reader's perspective. Details: `oks/pathfinder/contributing/changelog.md`.
- **Commits:** Conventional Commits, atomic commits, GitHub Flow, no secrets. Only commit/push when
  asked; branch off `main` first. Full rules live in the user-level `commit-conventions` skill and the
  OKF `git-best-practices` bundle; PR conventions in `oks/pathfinder/contributing/pull-requests.md`.
- **Homebrew rules:** the house rules themselves live in the OKF bundle
  (`oks/pathfinder/house-rules/`); their authority is the "Sieg's Guide" Google Docs, not this repo.
  `docs/homebrew_rules.md` keeps only the **rule → code map**, the implementation **backlog**, and
  which source sub-docs are still unread.
- **Docs doctrine — code owns behaviour.** When a doc and the code disagree, the code is right and
  the doc is a bug. A doc earns its place only when it holds what code cannot: **where** things are
  (`docs/CODEBASE_MAP.md`), **why** a choice was made (`changelog.md`), **external rules** (PF1e,
  Sieg's Guide, 3pp systems → the bundle), or **not-yet-code** (TODOs, open questions). Never restate
  a tuning constant, formula, or enum in prose — name the symbol that owns it. Hard conventions
  belong in a validator (`Backend/scripts/validate_*.py`), not only in a sentence: a stale
  `critical: "onCrit"` in a doc silently broke six weapons, and a `MOD_CRITICAL` whitelist fixed it.
