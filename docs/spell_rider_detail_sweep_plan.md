# Plan — Detailed spell-rider re-authoring sweep (six-detail conditionals, phase 2)

> Working plan for the detailed spell-effect sweep. Grilled 2026-07-20.

> **Caster-level standard.** Riders author caster-level scaling as the single token
> `@spells.primary.cl.total`; both consumers expand it at attach time into the homebrew *combined*
> caster level (`spellCLExpr()` in `modify-abilities.js`'s `subSpellTokens`, and `subSpell` in
> `pf1-conditional-applier`). Never author a raw multi-book sum — it over-counts low casters.
> **The rule and its rationale now live in the OKF `pathfinder` bundle**
> (`oks/pathfinder/conditionals/decision-rules.md`, "Scaling tokens"), and
> `validate_spell_conditionals.py` enforces it.

## Context

Phase 1 (already shipped) gave every conditional the six-detail **labeled-clause** rider format
(`Cost:`/`Activation:`/`Range:`/`Save:`/`Effect:`), a per-weapon editable apply pop-up in
`pf1-conditional-applier`, and `@slvl`/`@castMod` DC substitution in both the applier macro and the
generator module. The **infrastructure is done** — `Backend/scripts/conditional_clauses.py` +
`enrich_conditional_riders.py` maintain the Cost/Range/Save-DC clauses idempotently.

**What's still wrong:** the **Effect** text of most spell riders is far too thin. It was regex-seeded,
so it captures a fragment and drops the rest. Example — **Unlock Flesh** currently reads only
`Range: touch; [[(min(5,@cl))d6]] damage` + `target staggered`, but the real spell (per its full
`data/spells.csv` description) also: staggers **living** creatures 1 round/level with a **new save
each round** to end; deals the d6 damage only to **corporeal undead** (Fort **halves**); makes
**incorporeal creatures immune**; and has **SR: yes** — and it dropped the save entirely
(`save: null`). Across the 619 curated riders: ~116 have a <60-char effect, ~28 are fragmented into
multiple list-items, and even the "good" ones omit SR / immunities / per-round re-saves.

**Goal:** re-author every offensive spell rider's Effect from its full CSV description into a
**maximally verbose** rider — every mechanic a player needs, nothing dropped — while preserving
existing correct wording and reusing the phase-1 clause infra for Cost/Range/Save-DC.

Repo: the generator (`Pathfinder_Char_Creator`); the applier snapshot is refreshed at the end.

## Grounding facts (verified)

- All **619** curated riders are present in `data/spells.csv` — **0** have no groundable source.
- Only **3** have a thin (<80-char) "works like <base> spell, except…" description
  (Deep Slumber, Unprepared Combatant, Confusion Lesser); the agent resolves those by also reading the
  **referenced base spell's** CSV row.
- Only **~3** entries have `save: null` while the CSV names a real save (the merge fixes these).

## Decisions locked (grilled)

| # | Decision |
|---|---|
| Scope | **All ~619** `spell_riders.json` entries (uniform completeness; already-good ones augmented) |
| Verbosity | **Max verbose** — per-target-type effects, immunities, per-round re-saves, secondary targets/damage, durations, SR line, "no effect if already X", stacking/counters |
| Existing text | **Augment / superset** — keep correct wording, ADD the missing mechanics; **consolidate** fragmented multi-item riders into ONE |
| Source of truth | `data/spells.csv` `description` + `saving_throw`/`spell_resistence`/`duration`/`targets` (d20pfsrd-derived; complete) |
| Accuracy guard | **Author + adversarial verify pass** — a 2nd Sonnet agent re-reads each rider vs the description, flags *invented* numbers/effects and *dropped* mechanics |
| Flagged riders | **Re-author once** with the verifier's complaint fed back; if it still fails, **keep the existing rider (never degrade)** and add to a manual-review list |
| Where detail lives | **Full detail in the conditional NAME** (a pf1 conditional has no description field; weapon-mounted copies have no spell text to fall back on). Long toggle names accepted |
| B touch-damage | **Don't restate** the primary dice (it rolls as a labeled modifier); the Effect covers everything else |
| Method | **Pilot via the REAL pipeline** (~20 spells) → user sign-off → **workflow** scales the rest |
| Workflow | **~30 spells/batch, ~6 agents concurrent, Sonnet** (~21 author + ~21 verify agents, one pipelined run) |

## Division of labor (reuse phase-1 infra — don't duplicate)

The authoring produces **only the Effect body** + the primary save's `{type, result}`.
`enrich_conditional_riders.py` still owns the `Cost:`/`Range:`/primary `Save:` DC clauses. Pipeline
per spell:

```
author Effect body + save  ->  merge into spell_riders.json (riders=[effect]; fix save block)
  ->  enrich_conditional_riders.py (prepends Cost/Range, injects "Save: <Type> DC [[10+@slvl+@castMod]] <result>")
  ->  validate_spell_conditionals.py
```

**Authoring standard (the gold rule):**
- Restate ONLY what the CSV description says (ground truth — no invented numbers); every number in
  `[[ ]]`; caster-level scaling as `@spells.primary.cl.total` (e.g. `[[ (min(5,@spells.primary.cl.total))d6 ]]`).
- Split effects **by target type** as separate `; `-clauses: `living: staggered [[1]] round/level, new
  save each round to end`; `corporeal undead: [[…]]d6, Fort halves`; `incorporeal: immune`.
- Include: per-round/repeat saves, immunities & "no effect if already X", secondary targets/damage
  (own `[[ ]]` + any secondary-DC delta), duration, a `spell resistance: yes` note, stacking/counters.
- Do NOT restate Range/Cost/primary-Save-DC (enrich adds them). Do NOT restate the primary damage
  dice for a B touch spell whose damage rolls as a `modifiers[]`/`spell_damage_index` entry
  (`has_modifier_damage`); DO restate per-CL/area damage that lives only in the description (C spells).
- Consolidate to a single rider string (one conditional). Multi-save spells: primary save in the
  `{type,result}` return, the secondary save inside the Effect. No-save spells stay save-less
  ("no save" in the Effect). No PoW tokens (`@INITMOD` etc.).

**Verify standard (2nd agent):** given the description + the authored rider, return
`{ok: bool, invented: [...], dropped: [...]}` — `invented` = a number/effect in the rider not
supported by the description; `dropped` = a mechanic in the description (or the old rider) missing from
the new one. Any non-empty list ⇒ flagged.

## Steps

1. **Worklist builder** (new) `Backend/scripts/build_spell_rider_worklist.py` — one record per rider
   joined to the CSV: `{name, spell_level, range, saving_throw, spell_resistance, duration, targets,
   description, base_ref_description?, current_rider, current_save, has_modifier_damage}`. Sliced into
   ~30-spell batch files under a scratch dir. Reuse `_save_block` from `build_spell_conditionals.py`.
2. **Merge script** (new) `Backend/scripts/merge_spell_riders.py` — input `{name:{effect, save:{type,
   result}|null}}`; sets `entry.riders=[effect]` and corrects `entry.save`; only writes riders that
   **passed verify**. Then caller runs `enrich_conditional_riders.py` + `validate_spell_conditionals.py`.
3. **Pilot (real pipeline)** — run the Sonnet author+verify agents on ~20 representative spells
   (Unlock Flesh incl.), merge → enrich → validate, and show the user before/after **plus** what the
   verifier flagged. Tune the authoring/verify prompts and re-run the cheap pilot until the output is
   good, THEN scale.
4. **Scale — workflow** — `Workflow` pipelines the ~21 batches: per batch `author (Sonnet) → verify
   (Sonnet) → re-author-once-if-flagged`; ~6 concurrent. Collect passed riders + the manual-review
   list; merge all → enrich → validate.
5. **Manual-review finish** — hand-author the held (twice-flagged) riders; re-validate.
6. **Refresh applier snapshot** — `build/build_data.py` then `build/bundle_macro.py`.

## Files

- **New:** `Backend/scripts/build_spell_rider_worklist.py`, `Backend/scripts/merge_spell_riders.py`.
- **Regenerated:** `Backend/json/spells/spell_riders.json` (Effect bodies rewritten; save blocks fixed)
  → re-run `enrich_conditional_riders.py`.
- **Reused as-is:** `conditional_clauses.py`, `enrich_conditional_riders.py`,
  `validate_spell_conditionals.py`; applier `build/build_data.py` + `build/bundle_macro.py`.
- Docs/changelog: note the detailed-effect sweep in `changelog.md` + `docs/feature_spec_todo.md` §7.

## Verification

1. **Pilot review:** before/after for the ~20 (esp. Unlock Flesh — living-staggered + per-round save,
   corporeal-undead damage + Fort-halves, incorporeal immunity, SR) + the verifier's flags → user OK.
2. **Validators:** `validate_spell_conditionals.py` clean after every merge; `enrich_conditional_riders.py`
   still a no-op on a second run (idempotent).
3. **Coverage report:** count of passed / re-authored / held-for-manual; the held list is finished by hand.
4. **Live Foundry:** rebuilt bundled macro on `C:\Users\Daniel\Downloads\fvtt-Actor-stefan-andersdotter-kcYfJPVYV9thQxwZ.json`
   — confirm a swept spell's conditional shows the full six-detail rider with per-target-type effects.

## Out of scope

- `spell_changes.json` Bucket-A self-buff toggles (buffs; less detail needed) — a later pass if wanted.
- Talent conditionals (phase-1 format already applied).
- The per-weapon applier UI (shipped in phase 1).
