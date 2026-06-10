# Feature Spec TODO — awaiting design input

> **End goal:** click the generate button → a **fully playable** PF1e NPC, with nothing left to
> hand-finish before it hits the table.
>
> The six features below are **partially scaffolded** in the codebase but each needs **your spec on
> *how* you want it added** before it can be built. Under each, fill in the **`Your spec:`** line
> (the rules to follow, priorities, edge cases, and — importantly — *what the generated NPC / JSON
> export should contain*). I'll implement against whatever you write there.
>
> Related docs: campaign house rules → [homebrew_rules.md](homebrew_rules.md) ·
> unified feat pool → [`data/feats_new.csv`](../data/feats_new.csv).

---

## 1. Path of War
**Current state (verified):** data is fully scraped — `Backend/json/class_data/path_of_war/`
(`Martial_Disciplines.json`, `path_of_war_classes.json`, `path_of_war_archetypes.json`,
`path_of_war_maneuvers_known.json`). `Backend/utils/class_func/path_of_war_funcs.py` defines
`select_disciplines()` (+ `clean_disciplines_string_func()`), but **nothing calls it**. The PoW
classes (`warder, harbinger, mystic, warlord, zealot, stalker`) are deliberately **filtered out of
random class selection** (`Backend/utils/util.py:120-146`), and the PoW imports/data-loads are
**commented out** in `Backend/main_test.py` (L42–45, L143–146). → not wired into generation or export.
Reference: [homebrew_rules.md §5](homebrew_rules.md).

**Needs from you:** how to choose disciplines, maneuvers-known, and stances per class + level; whether
PoW classes should re-enter the random pool; and what the NPC export should include (maneuver list?
readied vs known? stances?).

**Your spec:**

---

## 2. Spheres of Power / Spheres of Might
**Current state (verified):** data exists under `Backend/json/class_data/spheres/`
(`spheres_of_might.json`). **No chooser code, nothing exported.** Connects to
[homebrew_rules.md §1](homebrew_rules.md) (proficiency rule: *one free weapon proficiency, or trade
all base proficiencies for a Martial Tradition*) — that trade lives at
`Backend/utils/class_func/armor_and_weapon_chooser.py` — and to the Spheres systems listed in §5.

**Needs from you:** which characters get Spheres (casters → Spheres of Power talents; martials →
Spheres of Might / Martial Traditions?); how many talents/spheres by level; and the export shape.

**Your spec:**

---

## 3. Weapon attacks
**Current state (verified):** `Backend/utils/class_func/armor_and_weapon_chooser.py` picks a weapon,
but only the weapon's **name** is exported (`weapon_name = list(character.weapon_dict.keys())[0]`,
`Backend/main_test.py:425`). `Backend/json/weapons_data.json` has the weapon stats. **No computed
attack routine** — no to-hit, ability mod, iterative attacks, or damage string.

**Needs from you:** the formula for a full attack line (BAB + ability mod + size + enhancements →
iteratives), how to fold in the homebrew Weapon Finesse / weapon-group rules
([homebrew_rules.md §4](homebrew_rules.md)), and the export format (e.g. `+11/+6 (1d8+4, 19–20/×2)`).

**Your spec:**

---

## 4. Weapon conditionals
**Current state (verified):** nothing yet — no data, no code. This is the *conditional* layer on top
of #3: crit ranges/multipliers, conditional or special-property damage (e.g. bane, elemental, sneak
attack riders), and Called Shots ([homebrew_rules.md §5](homebrew_rules.md)).

**Needs from you:** which conditionals matter for a ready-to-play NPC, how they should be expressed
(precomputed alternate lines? notes the GM applies?), and their priority vs. #3.

**Your spec:**

---

## 5. Free feats
**Current state (verified):** the story-feat cadence is implemented —
`story_feat_amount = 1 + floor(level/5)` in `Backend/utils/class_func/level_and_bab.py` (1/2/3/4/5
feats at L1/5/10/15/20, per [homebrew_rules.md §1](homebrew_rules.md)). **Not yet implemented:** the
**+2 feats at character creation** and the **per-flaw bonus feats** (§1, backlog #2). Distinct from,
but overlapping with, the feat-tax auto-grants in #6.

**Needs from you:** confirm the creation-feat / flaw-feat counts and how flaws are rolled/assigned for
an NPC, and whether "free" weapon-proficiency-style grants belong here or under #2/#3.

**Your spec:**

---

## 6. Feat taxes
**Status — chain taxes implemented (2026-06):** `feat_tax_func` (`Backend/utils/class_func/feat_tax.py`)
grants a primary feat's progression chain (from `Backend/json/feat_tax.json`) for free when prereqs
are met, **1 feat per 2 levels** since the primary was gained; "Extra …" feats grant a free
self-duplicate; Mythic feats never tax. The FoundryVTT module renders them bundled on the primary
entry as `"<Label> Primary > Tax1 > Tax2"`.

**Still pending (needs your spec / blocked):**
- **Auto-granted "free" feats** when you simply qualify (e.g. *Raging Vitality* for
  barbarians/bloodragers) plus the always-free / removed-prerequisite / baked-in-Weapon-Finesse rules
  from [homebrew_rules.md §4](homebrew_rules.md) — a *different* mechanic from chain taxes; give me
  the authoritative lists and I'll drive them from data. (Overlaps #5.)
- **Martial Training taxes once free** — blocked on Path of War (#1).
- **Sphere of Power talent → +1 talent** — blocked on Spheres (#2).
- Expanding / verifying the chain data in `feat_tax.json` against your Feat Tax Google Doc.

**Your spec:**
