# Road to 1.0 — table-ready finish line for the PF1e generator stack

> **This is the live 1.0 roadmap.** To continue in a fresh session, prompt:
> `Read docs/plan_1.0_finish.md and continue the 1.0 plan`. Update the checkboxes here as phases
> complete; log bugs found in Phase 4 under the "Bug list" heading it creates.

## Context — decisions locked in the 2026-07-29 grilling

The stack (backend generator, FoundryVTT module, conditional applier, web sheet) is near finish.
Grilling settled what "finish" means and what's in/out:

1. **Finish line = table-ready**: generate → inject → run a session with zero hand-fixing for any
   class the campaign actually uses. Spec-completeness and curation-completeness are post-1.0.
2. **Two-step workflow is blessed**: the applier macro is THE delivery mechanism for class-feature
   conditionals (idempotent, handles retarget/labels). No creation-time consumer gets built;
   document the workflow instead.
3. **House numbers must be verified**: HP (Foundry seems to grant full HP natively — confirm why,
   and confirm the generator's rolled-HP path is right for other players), **skill ranks are
   suspected wrong vs house rules**, feat counts "almost exact" — all three need confirmation, not
   assumption.
4. **Invariant sweep** is the test shape: ~all classes × level ladder (1/5/10/15/20) × a few seeds
   (~450 generations), asserting the house-rule *formulas* — not pinned sheets.
5. **Repo hygiene first**: the applier repo's ~2,900 uncommitted lines (7 days old) + this
   session's core-features work get chunked atomic commits before further feature work.
6. **Structured bug hunt**: ~10 NPCs across class buckets, generate → inject → apply, log every
   anomaly as the seed bug list.
7. **Curation scope for 1.0**: correctness pass (fix every orphan/mismatch the gap report finds)
   + top ~20 highest-frequency core candidates. Bulk worklists → persistent to-do (below).
8. **Metzofitz homebrew feats are IN for 1.0** (backlog #1): uncomment/wire the selection in
   `Backend/utils/class_func/feats.py` behind the homebrew flag.
9. **Full release train seals 1.0**: tag all three repos, deploy backend to Render, publish the
   module release, changelog states the deliberate exclusions.

## Phase 0 — plan file + repo hygiene (do first)

- [x] Write this plan to `docs/plan_1.0_finish.md` in the main repo (the physical, session-portable
      copy; keep checkboxes updated there).
- [x] **Applier repo** (`~/Documents/GitHub/pf1-conditional-applier`): review the 7-day-old delta
      (`feat_conditionals.json` +2,151, `src/apply-conditionals.macro.js` +93, `build/build_data.py`
      +49, README) and commit in atomic chunks (curation / macro / build / docs), then commit this
      session's work (core_features data + `build/verify_specs.mjs` chassis specs + rebuilt bundle).
- [x] **Main repo**: commit the core-features audit + curation session (candidate slicer `core`
      family, `core_features` overrides, validator export-check, changelog, docs) per
      `commit-conventions`.
- [x] Log the applier commits in the main repo `changelog.md` (central-changelog convention).

## Phase 1 — house-rule numbers: write down, verify, fix (the suspected wrongness)

- [x] **Write the expected formulas down first** — taken from the bundle (`skills-and-hp.md`,
      `feat-economy.md`): skill ranks = per-class max(1, points(2→4 floor) + best final mental mod)
      × class level + background 2/level + favored; per-skill cap 3×level; feats = ceil(L/2) + 2
      creation + 1/flaw + (1 + L//5) story + 1 flavor; HP = max die every level + final Con mod × L.
      Foundry's full HP comes from pf1's `healthConfig` world setting (System Settings → Health
      Configuration: auto-HP with maximized levels/rate) — documented in `docs/homebrew_rules.md`.
- [x] Diff + fix (2026-07-30): skill ranks lacked all three house rules (floor/cap/background) —
      added in `skill_ranks.py`; flaw feats used a `floor(n/2+1)` clamp (wrong at 0/3/4 flaws) and
      creation +2 was missing — fixed in `level_and_bab.py`; HP was rolled, Con mod floored
      before halving and ignored inherent/level-up Con — fixed in `hp_rolls.py`. All homebrew-flag
      gated; goldens regenerated in the same commit.
- [x] **New invariant sweep test** `Backend/scripts/test_house_invariants.py`: 43 classes ×
      1/5/10/15/20 × 3 seeds = 645 generations, 6,450 checks, green in ~4 min (payload buff-gap
      assertions deferred to Phase 3 where the gap report gets fixed).

## Phase 2 — Metzofitz homebrew feats in (backlog #1)

- [x] Metzofitz selection wired (2026-07-30): `feats.py::metzofitz_feat_frame` concats the
      General/Combat rows (~490 of 1,735 — subsystem/style rows excluded by the chooser's exact
      type match; styles keep coming via Martial Training) into `generic_feat_chooser` behind the
      homebrew flag.
- [x] Prereqs go through the existing `get_feats_without_prerequisites` loop; name collisions
      resolve to AoN (`drop_duplicates(keep='first')` after concat); no new label needed — picks
      render like normal feats, with rules text from `metzofitz_description` (the module's
      description fallback keeps the row).
- [x] Invariant sweep extended: every placed Metzofitz-only feat must be described +
      pool-existence check (1,773 picks across the 645-generation sweep); goldens regenerated
      (homebrew flag is on in the golden configs).
- [x] Changelog entry.

## Phase 3 — conditional correctness pass + top-20 curation

- [ ] Generate a batch (reuse sweep output), collect `buff_gaps` from payloads +
      `Backend/scripts/report_buff_coverage.py`; **fix every orphan/mismatch** (casing, labels,
      suffixes) — validator-style where possible so regressions fail tests, per the
      orphaned-conditionals lesson.
- [ ] From `Backend/scripts/_conditional_candidates/A/core-*.json`, curate the ~20 candidates that
      actually appear on generated NPCs most often (bloodline claws/rays, oracle mystery attack
      revelations, warpriest sacred weapon, etc. — rank by frequency across the generated batch,
      don't guess). Same pipeline as this session: overrides `core_features` →
      `build_class_feature_changes.py` → validator → applier `build_data.py` + `bundle_macro.py` →
      `verify_specs.mjs`.
- [ ] Re-run the report; append remaining counts to the curation to-do below.

## Phase 4 — structured bug hunt (10 NPCs, cross-bucket)

- [ ] Generate ~10 NPCs covering: core caster, core martial, PoW initiator, MT martial-path user,
      Spheres dabbler, rogue/precision, paladin/smite-style, multiclass, low level (1–2), high
      level (15+).
- [ ] For each: inject into Foundry, run the applier, then check — sheet numbers (AC/saves/HP/
      ranks), items attached with no orphan/gap rows, PoW tab readied, toggles roll correctly on a
      weapon, backstory/lore sane.
- [ ] Log every anomaly into `docs/plan_1.0_finish.md` under a "Bug list" heading; fix, adding a
      regression test per fix where the harnesses allow (golden, verify_specs, validators).

## Phase 5 — docs + release train (seals 1.0)

- [ ] Document the blessed two-step workflow (generate → inject → Apply Conditionals macro) where
      a user will find it (module README + `docs/CODEBASE_MAP.md` pointer).
- [ ] Changelog: roll `[Unreleased]` → `1.0.0`, including a **deliberate exclusions** note pointing
      at the curation to-do.
- [ ] Release: tag main repo; backend `deploy.ps1` (Docker Hub → Render hook); module
      `release.ps1` (GitLab + Foundry publish — irreversible, dry-run first); applier repo tag +
      deployed bundle refresh. Matching version numbers across repos.

## Persistent curation to-do (post-1.0 backlog — keep this list alive in the repo copy)

Deferred by decision Q7; counts as of 2026-07-29 (re-derive with
`build_conditional_candidates.py` / the spell worklist tooling, don't trust these numbers later):

- [ ] Core chassis features, tier A: **~905** minus Phase-3's top-20 (batches
      `_conditional_candidates/A/core-NN.json`); tier B: ~497.
- [ ] Choice-pool powers, tier A: **~178** (rage powers, arcana, hexes, talents…); tier B: ~247.
- [ ] Feats, tier A: **~45**; tier B: ~139.
- [ ] Spell conditionals: **~355** gated compendium-present drafts + de-dup buff-vs-conditional +
      the 19 legacy B restatements (feature_spec_todo §7).
- [ ] Post-1.0 homebrew backlog: skill alternate abilities (#3), feat-tax prereq relaxation (#6),
      custom races Loxo/Kalyptran/Dolistani (#7), remaining flaws/traits flow (#8 leftovers).
- [ ] Creation-time conditional attach (superseded unless the two-step workflow ever chafes).

## Verification

- Phase 1/2: `test_house_invariants.py` green across the full sweep; existing suite
  (`test_golden_payload`, `test_buff_match`, `test_skill_ranks`, validators) green.
- Phase 3: buff-gap report empty (or every remaining row annotated as known-deferred);
  `verify_specs.mjs` green; applier run on a generated rogue/paladin shows the new toggles.
- Phase 4: bug list in the repo plan file fully checked off.
- Phase 5: Render endpoint returns a generated character; released module version injects it; a
  fresh actor + applier macro run matches the Phase-4 checklist.
