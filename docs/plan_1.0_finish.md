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
      added in `skill_ranks.py`, with the 2→4 floor behind the new internal `misc_homebrew_rules`
      catch-all flag (defaults on; cap + background stay on the main homebrew flag); flaw feats
      keep the diminishing schedule (0→0, 1→1, 2→2, 3→2, 4→3 — the old clamp was right except the
      phantom feat at 0 flaws), also behind `misc_homebrew_rules`, and creation +2 was missing —
      fixed in `level_and_bab.py`; HP was
      rolled, Con mod floored before halving and ignored inherent/level-up Con — fixed in
      `hp_rolls.py`. Goldens regenerated in the same commit.
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

- [x] Correctness pass (2026-07-30): a 129-generation batch (43 classes × L5/12/18) reported
      **zero buff_gaps**, and `report_buff_coverage.py` still shows all 11 side-maps covered with
      no curated-name collisions — nothing to fix.
- [x] Top-20 curation (2026-07-30): ranked the core tier-A candidates by actual appearance across
      the batch (chassis features counted via `class_ability`, not just `class_features` buckets)
      and curated the 18 with a real on-attack payload — Stunning Fist, Quivering Palm, Quarry,
      Master Hunter, Master Strike, Debilitating Injury, Knockout, Cavalier's/Mighty/Supreme
      Charge, Gun Training, Judgment (Justice + Destruction), Greater Bane, True Judgment, Studied
      Combat/Strike, Inspiration, Sacred Weapon. High-frequency rejects (Uncanny Dodge, Trap
      Sense, rage/bloodrage chains, Flurry, Banner, Channel Energy…) are defensive/passive/buff/
      own-action features — no weapon toggle, per the cost-only-conditional invariant. Pipeline
      run end-to-end; `verify_specs.mjs` 97 passed.
- [x] Report re-run; counts updated in the curation to-do below.

## Phase 4 — structured bug hunt (10 NPCs, cross-bucket)

- [x] Generated (2026-07-30) — 10 cross-bucket NPCs, seeds fixed so every build replays exactly
      via `generate_random_char(seed=...)` with the config below. All 10 came back **clean** on
      the payload-level checklist (house formulas, exact skill spend, zero `buff_gaps`, every feat
      row describable, subsystem presence, non-empty gear/weapon/bio):

      | bucket | seed | build |
      |---|---|---|
      | core-caster | 90001 | wizard 9 |
      | core-martial | 90002 | fighter 8 |
      | pow-initiator | 90003 | warder 11 |
      | mt-martial-path | 90022 | barbarian 10 (Martial Training I/III, Piercing Thunder) |
      | spheres-dabbler | 90005 | cleric 10 (spheres flag on) |
      | rogue-precision | 90006 | rogue (unchained) 12 |
      | paladin-smite | 90007 | paladin 13 |
      | multiclass | 90008 | rogue 8 / shifter 6 |
      | low-level | 90009 | antipaladin 1 |
      | high-level | 90010 | oracle 17 |

      Shared config: region Tal-Falko, race/alignment/gender/deity random, homebrew Y,
      inherents Y, 4d6, gold 30,000, backstory API off. Non-obvious knobs per bucket:
      spheres-dabbler `spheres_flag='Y'`; multiclass `multi_class='Y'`,
      `class_choice='random'`; low-level `low_level=1, high_level=2`.
- [ ] **Daniel's half** — for each seed: regenerate through the local backend (or re-roll the
      same bucket live), inject into Foundry, then check the Foundry-only surface: sheet numbers
      (AC/saves/HP/ranks vs the payload), items attached with no orphan/gap rows, PoW tab
      readied, backstory/lore sane. *Applier checks are deferred* — running the Apply
      Conditionals macro and verifying the Phase-3 toggles roll belongs to the applier hammering
      session (persistent to-do below), not this bug hunt.
- [ ] Log every anomaly under the "Bug list" heading below; fix, adding a regression test per fix
      where the harnesses allow (golden, verify_specs, validators).

### Bug list (Phase 4 — append findings here)

_No entries yet. Payload-level sweep of the 10 builds found nothing; Foundry-side checks pending._

## Phase 4.5 — bonded creatures + psionics (pulled into 1.0, 2026-07-31)

Scope added after the original grilling: **bonded creatures** (animal companions, familiars,
eidolons, mounts/psicrystals) and the **psionics classes**. Both are being designed first as
wayfinder maps — decisions before code — and each ends at a spec section in
`docs/feature_spec_todo.md`. **The release train (Phase 5) waits on these.**

- [x] Work `docs/wayfinder/companions/` to done → `feature_spec_todo.md` §8. **Effort closed
      2026-08-01**: six of seven tickets resolved, map marked CLOSED, §8 landed. Locked: **one
      payload, N `npc` Actors**; the **backend owns every number** and the module clones a
      `pf-content` Actor for the body (the web sheet has no game system, so pf1 cannot own the math);
      v1 = **companion + mount + familiar** at a full stat block with the **eidolon degraded, not
      suppressed** — `summoner`/`summoner (unchained)` stay rollable and emit a named base form.
      `animal_companion` becomes the deprecated alias of a new `bonded_creatures` list.
      Ticket 07 (eidolon evolutions) is open, unblocked, deferred to v1.1.
      **Three grantor rows from the chart failed RAW verification** and were corrected in the spec:
      `shifter` grants nothing, `antipaladin`'s fiendish servant is a `summon monster` subsystem, and
      `sorcerer` is Arcane-bloodline-conditional — 13 classes touched, 10 at a full stat block.
- [x] Work `docs/wayfinder/psionics/` to done → `feature_spec_todo.md` §9. **Effort closed
      2026-07-31**: all eleven tickets resolved, map marked CLOSED. Locked: adopt
      [`pf1-psionics`](https://github.com/SoxMax/pf1-psionics) rather than build a module, but source
      the **mechanics from the Library of Metzofitz wiki** — the module's class fields are
      placeholders and it has no powers-known table (ticket 02). The module is the render target
      only, so emitted names must reconcile against its packs. Scope: 12 classes.
- [x] **Psionics backend is built and green (2026-07-31, branch `feat/psionics-v1`).** All twelve
      classes generate with manifester level, power points, powers and subsystem picks; the payload
      carries `manifesters` + `powers_desc_dict`; OGL artifacts ship (`LICENSE-OGL.txt`, the psionics
      `NOTICE.md`, `GET /license`, `license_url` on every payload).
      `test_house_invariants.py` extended with psionics invariants — **275 generations / 4561 checks
      pass across all 55 classes**, and `validate_psionics_data.py` is at 0 errors.
      **Still open, deliberately:** Foundry-side import (gate 3) spans the module repo and is a later
      branch; voyager bonus feats, psionic races and the other deferred items are listed in §9.
- [ ] Implement the **companions** spec (§8 build slices, in dependency order — each is a commit).
      The remaining slices are charted as
      [`docs/wayfinder/companion-sheets/`](wayfinder/companion-sheets/map.md), whose destination is
      *every bonded creature arrives as a usable sheet*. **Slices 1–6 and 9 are done (2026-08-03);
      the backend half of this phase is finished** and the map's first finish-line gate is met. What
      is left is the two renderers: **7 is unblocked** (ticket 02 resolved), **8 still waits on
      ticket 03**.
      - [x] 1. `repair_animal_choices.py` — the sign-loss/key-drift/field-bleed repair (D5). **Done
            first**: 109 advancement rows were inflating every advanced companion by +4 Dex.
      - [x] 2. `validate_companion_data.py` — assert the PF1e size-up package, no surviving bare ints.
      - [x] 3. `dump_pf_content_actors.py` → `pf_content_companions.json` + `validate_companion_names.py`
            (the D3 silent-drop gate). Landed as Python, not `.mjs` — it reuses `dump_foundry_pack.mjs`.
      - [x] 4. `companion_grantors.json` + the resolver in `animal_companions.py` (reuses
            `class_entry_for`), plus archetype-bond classification, stacking and D9 identity.
      - [x] 5. Advancement merge + stat-block math (**#31**) — `class_func/companion_stats.py`,
            2026-08-03. Both gating tickets resolved first:
            [01](wayfinder/companion-sheets/issues/01-attack-skill-derivation.md) (spec §8 **D12** —
            every number's source; none of the PC's code reusable, only the maximised-HP *rule*; the
            house skill floor does **not** carry over) and
            [04](wayfinder/companion-sheets/issues/04-size-change-double-count.md) (spec §8 **D11** —
            the published deltas already contain the size package, so only the geometry is ours).
      - [x] 6. Payload: emit `bonded_creatures`, keep `animal_companion` as the deprecated alias
            (**#32**), 2026-08-03. All six goldens regenerated; five differ by exactly the one added
            key. ⚠ **The `companion` golden was re-seeded (7275 → 7323)** — the region fix had
            realigned the RNG and 7275 had quietly stopped rolling a stack at all, so the golden that
            exists to pin the stacking math had stopped pinning it. 7323 stacks **three** grantors
            (hunter 7 / ranger 4 / druid 3 → effective 11). **Not done until `./deploy.ps1` runs.**
      - [ ] 7. (**#33**) Foundry module: loop `Actor.create`, clone from `pf-content`, patch numbers,
            degrade on miss; title composed module-side per D10. **Unblocked 2026-08-03** —
            [ticket 02](wayfinder/companion-sheets/issues/02-pf1-actor-patching.md) is resolved and
            carries the mechanical recipe: pf1 keeps stored fields and rebuilds every `.total`, the
            clone's `Animal Companion` class item is driven at the creature's **HD count** (not its
            effective level), and the two change-bearing items every `pf-content` Actor ships must be
            deleted or the companion table lands twice. Two narrow claims (re-render persistence,
            `healthConfig` on a cloned character) are checked on the first live import.
      - [ ] 8. (**#34**) Web sheet: auto-fill the nested Companions tab from `bonded_creatures` (D10 —
            **not** a second roster character). *Gated on
            [ticket 03](wayfinder/companion-sheets/issues/03-web-sheet-autofill-ownership.md) — that
            tab is user-owned and hand-typed today.*
      - [x] 9. (**#35**) Companion invariants, 2026-08-03, split across two gates by what each can
            actually see. `scripts/validate_companion_stats.py` (validators 13 → 14) owns the
            arithmetic, sweeping all **392** species-level stat blocks — it is where D11's
            no-double-count ruling is enforced, and it re-fails on **447** counts if the size table is
            put back on top. `test_house_invariants.py` owns what needs a whole generated character:
            the emitted shape, absence entries carrying no stats, `stats.hd` agreeing with the
            post-stack chassis, `size_change` present exactly when the creature grew, and the **druid
            flip** (both=0, neither=0 — the regression test for F's rewire). It counts branches
            reached and **fails if the sweep never produced a bonded creature at all**, so the run
            cannot report success having asserted nothing. Full sweep: **15,560 checks / 825
            generations**, 55 granted, 39 absence entries, 15 druid flips.
      Psionics has already done its half of the invariant work.

## Phase 5 — docs + release train (seals 1.0)

- [x] Document the blessed two-step workflow (2026-07-30): user-facing walkthrough in the module
      repo's root `README.md`; developer pointer in `docs/CODEBASE_MAP.md` (Consumers section);
      stale applier-README count fixed per the docs doctrine.
- [ ] Changelog: roll `[Unreleased]` → `1.0.0`, including a **deliberate exclusions** note pointing
      at the curation to-do.
- [ ] Release: tag main repo; backend `deploy.ps1` (Docker Hub → Render hook); module
      `release.ps1` (GitLab + Foundry publish — irreversible, dry-run first); applier repo tag +
      deployed bundle refresh. Matching version numbers across repos.

## Persistent curation to-do (post-1.0 backlog — keep this list alive in the repo copy)

Deferred by decision Q7; counts as of 2026-07-29 (re-derive with
`build_conditional_candidates.py` / the spell worklist tooling, don't trust these numbers later):

- [ ] **Conditional-applier hammering session** (deferred from Phase 4 by decision 2026-07-30):
      run the Apply Conditionals macro across the 10-NPC bug-hunt batch, verify the Phase-3
      toggles (Stunning Fist, Quarry, Judgment, Sacred Weapon…) attach and roll correctly on
      weapons, and fix whatever falls out of the applier.
- [ ] Core chassis features, tier A: **905 candidates, 28 curated** (10 in the core-features
      session + 18 in Phase 3; batches `_conditional_candidates/A/core-NN.json` — most of the
      remainder are defensive/passive rows that will never take a weapon toggle); tier B: ~497.
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
- Phase 4.5: psionics — `validate_psionics_data.py` at 0 errors and the full `test_house_invariants.py`
  sweep green (done). Companions — `validate_companion_data.py` / `validate_companion_names.py` green,
  the invariant sweep extended, and a generated druid/wizard/cavalier importing as multiple Foundry
  actors with numbers matching the payload.
- Phase 5: Render endpoint returns a generated character; released module version injects it; a
  fresh actor + applier macro run matches the Phase-4 checklist.
