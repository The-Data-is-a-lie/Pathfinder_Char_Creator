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
- [ ] **Applier repo** (`~/Documents/GitHub/pf1-conditional-applier`): review the 7-day-old delta
      (`feat_conditionals.json` +2,151, `src/apply-conditionals.macro.js` +93, `build/build_data.py`
      +49, README) and commit in atomic chunks (curation / macro / build / docs), then commit this
      session's work (core_features data + `build/verify_specs.mjs` chassis specs + rebuilt bundle).
- [ ] **Main repo**: commit the core-features audit + curation session (candidate slicer `core`
      family, `core_features` overrides, validator export-check, changelog, docs) per
      `commit-conventions`.
- [ ] Log the applier commits in the main repo `changelog.md` (central-changelog convention).

## Phase 1 — house-rule numbers: write down, verify, fix (the suspected wrongness)

- [ ] **Write the expected formulas down first** (from Sieg's Guide via the OKF `pathfinder` bundle,
      `oks/pathfinder/house-rules/`; ask Daniel where the bundle is silent): skill ranks (rank
      boost, per-level cap, mental-ability pick, background ranks — backlog #4), feat count
      f(level, flaws, story feats, creation feats — backlog #2/#8 portions), HP policy (who rolls,
      who gets max; reconcile with pf1's native "maximum HP" health setting that Foundry appears to
      apply — find that setting and document why sheets show full HP).
- [ ] Diff the formulas against `skill_ranks.py` / `level_and_bab.py` behavior; **fix skill ranks**
      (the suspected mismatch) and any feat-count delta found.
- [ ] **New invariant sweep test** `Backend/scripts/test_house_invariants.py`: all generatable
      classes × levels 1/5/10/15/20 × 3 seeds; assert the three formulas + payload sanity (no
      exceptions, buff-gap list empty or known). Reuse the golden-payload harness's generation
      entry (`generate_random_char()` via `C:\Python310\python.exe`); runtime target < a few
      minutes, else trim seeds.

## Phase 2 — Metzofitz homebrew feats in (backlog #1)

- [ ] Un-comment and finish Metzofitz feat selection in `Backend/utils/class_func/feats.py`
      behind the homebrew/story-feats flag; source `data/Metzofitz_Feats.csv`.
- [ ] Prerequisite checks + name collisions vs the normal pool; label convention consistent with
      existing placement labels so the applier/module name-matching still works.
- [ ] Extend the invariant sweep: with the flag on, homebrew feats appear, counts still satisfy the
      Phase-1 formula; golden seed(s) for a flagged character.
- [ ] Changelog entry.

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
