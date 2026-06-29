"""Standalone regression checks for the spell-conditional pipeline (run directly; this repo has no
pytest harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    C:\\Python310\\python.exe Backend/scripts/test_spell_conditionals.py

Covers: the classifier buckets the canonical exemplars correctly (and the True-Strike word-order fix
+ the AC / other-subject guard hold), the curated runtime files load and are well-shaped, and the
runtime selector filters them down to an NPC's chosen spells (case-insensitively, rider-bearing B
only).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPTS, BACKEND = HERE.parent, HERE.parents[1]
sys.path.insert(0, str(SCRIPTS))   # so `import build_spell_conditionals` resolves
sys.path.insert(0, str(BACKEND))   # so `from utils...` resolves

import build_spell_conditionals as bsc
import normalize_spell_name_casing as nsc
from utils.class_func.spells import (spell_conditionals_selection,
                                      _spell_change_buffs, _spell_rider_buffs)


def test_bucketing():
    draft = bsc.build_draft()
    expect = {"True Strike": "A-toggle", "Divine Favor": "A", "Flame Arrow": "A-toggle",
              "Shocking Grasp": "B-melee", "Vampiric Touch": "B-melee", "Scorching Ray": "B-ranged",
              # Mirror Strike's "+2 ... attack roll (and confirmation attack roll)" is a real general
              # to-hit bonus -- the crit-confirm guard must NOT mistake its NOUN for the verb idiom.
              "Mirror Strike": "A"}
    for name, bucket in expect.items():
        got = draft.get(name, {}).get("_bucket")
        assert got == bucket, f"{name}: expected {bucket}, got {got!r}"
    # The disqualifier guard must keep AC-bonus / bonus-to-opponent false positives out, and a
    # crit-CONFIRMATION-only bonus ("+N on attack rolls to confirm a critical hit") is not a general
    # attack buff -- Unerring Weapon must stay description-only, not become an always-on to-hit change.
    for name in ("Judgment Light", "Mantle Of Calm", "Unerring Weapon"):
        assert name not in draft, f"{name} should have been filtered out"
    # Flat bonuses must NOT pick up an unrelated "per N levels" clause (locality fix).
    hf = draft.get("Heroes' Feast", {})
    assert all("@spells" not in c["formula"] for c in hf.get("changes", [])), \
        "Heroes' Feast flat bonus was wrongly scaled"
    print(f"  bucketing OK ({len(draft)} drafted)")


def test_curated_files_load():
    chg, rid = _spell_change_buffs(), _spell_rider_buffs()
    assert isinstance(chg, dict) and chg, "spell_changes.json empty/missing"
    assert isinstance(rid, dict) and rid, "spell_riders.json empty/missing"
    for n, e in chg.items():
        assert ("modifiers" in e) or ("changes" in e), f"spell_changes[{n}]: bad shape"
    for n, e in rid.items():
        assert e.get("riders"), f"spell_riders[{n}]: missing riders"
    print(f"  curated files OK (changes={len(chg)}, riders={len(rid)})")


def test_selection():
    class _Char:
        pass
    c = _Char()
    # lower/mixed case + a B-spell with no riders (Scorching Ray) that must NOT appear in riders.
    c.spell_list_choose_from = [["true strike"], ["Magic Weapon", "Mage Armor"],
                                ["Chill Touch", "Scorching Ray"]]
    chg, rid = spell_conditionals_selection(c)
    assert {k.lower() for k in chg} == {"true strike", "magic weapon"}, sorted(chg)
    assert {k.lower() for k in rid} == {"chill touch"}, sorted(rid)
    # Non-caster -> empty, no crash.
    empty = _Char(); empty.spell_list_choose_from = []
    assert spell_conditionals_selection(empty) == ({}, {})
    print("  selection OK")


def test_no_uncapped_scaling():
    """Every caster-level-scaling buff must be bounded by min(...): a bare floor(@CL/N) grows forever,
    which is the Divine-Favor / Aroden / Unerring class of bug (rules cap the bonus at a maximum)."""
    offenders = []
    for src, buffs in (("spell_changes", _spell_change_buffs()),
                       ("spell_riders", _spell_rider_buffs())):
        for name, entry in buffs.items():
            for coll in ("modifiers", "changes"):
                for m in (entry.get(coll) or []):
                    f = str(m.get("formula", ""))
                    if ("cl.total" in f or "hd.total" in f) and "min(" not in f:
                        offenders.append(f"{src}[{name}]: {f}")
    assert not offenders, "uncapped scaling formula(s): " + "; ".join(offenders)
    print("  scaling caps OK")


def test_csv_casing_canonical():
    """data/spells.csv names match the Foundry compendium's canonical casing, so the module's
    processSpell() builds them as spell items instead of silently dropping them (~250-spell bug).
    Skips when every_spell.json isn't present (e.g. CI without the Foundry module checked out)."""
    every = nsc.DEFAULT_EVERY_SPELL
    if not every.exists():
        print(f"  csv casing SKIPPED (no compendium at {every})")
        return
    canon = nsc.load_canonical(every)
    changed, _ = nsc.normalize_csv(nsc.DEFAULT_SPELLS_CSV, canon, dry_run=True)
    assert not changed, f"{len(changed)} csv name(s) mis-cased vs compendium, e.g. {changed[:3]}"
    print(f"  csv casing OK (0 mismatches vs {len(canon)} compendium names)")


import re

_MODULE_MANEUVERS = Path(
    r"C:\Users\Daniel\AppData\Local\FoundryVTT\Data\modules"
    r"\pf1e_random_char_generator\templates\character_sheet_folder\maneuver_changes.json")


def _bare_numbers(text):
    """Numbers in display text that are NOT inside a [[ ]] inline roll, an @ref, or the literal 'DC'.
    The foundry-conditionals convention requires every such number to be wrapped in [[ ]]."""
    t = re.sub(r'\[\[.*?\]\]', ' ', text)
    t = re.sub(r'@\w[\w.]*', ' ', t)
    t = re.sub(r'\bDC\b', ' ', t)
    return re.findall(r'(?<![\w/])[-+]?\d+(?:d\d+)?(?![\w])', t)


def _restated_dice(display_text, modifiers):
    """A modifier's MAIN dice term (e.g. 8d6) appearing in the display text OUTSIDE [[ ]] -- i.e. the
    rolled damage wrongly restated in the name/rider instead of living only on the (labeled) roll."""
    stripped = re.sub(r'\[\[.*?\]\]', ' ', display_text)
    for m in (modifiers or []):
        if m.get('target') != 'damage':
            continue
        for dd in re.findall(r'\d+d\d+', str(m.get('formula', ''))):
            if re.search(r'\b' + re.escape(dd) + r'\b', stripped):
                return dd
    return None


def _plain_formula_violations(modifiers, where):
    """Modifier formulas must be PLAIN (no baked [label]/[[ ]]) -- the module appends [Source]."""
    out = []
    for m in (modifiers or []):
        f = str(m.get('formula', ''))
        if '[' in f or ']' in f:
            out.append(f"{where}: {f}")
    return out


def test_spell_convention_compliance():
    """Curated spell conditionals obey the foundry-conditionals convention: every number in [[ ]],
    no rolled damage restated in a toggle name / rider, and plain modifier formulas."""
    bare, restate, badf = [], [], []
    chg = _spell_change_buffs()
    for name, e in chg.items():
        mods = e.get('modifiers') or []
        badf += _plain_formula_violations(mods, f"spell_changes[{name}]")
        nm = e.get('name')
        if nm:
            if _bare_numbers(nm):
                bare.append(f"spell_changes[{name}].name: {_bare_numbers(nm)} :: {nm[:80]}")
            dd = _restated_dice(nm, mods)
            if dd:
                restate.append(f"spell_changes[{name}].name restates {dd}")
    for name, e in _spell_rider_buffs().items():
        for rd in (e.get('riders') or []):
            if _bare_numbers(rd):
                bare.append(f"spell_riders[{name}]: {_bare_numbers(rd)} :: {rd[:70]}")
    assert not badf, "non-plain modifier formula(s): " + "; ".join(badf[:6])
    assert not restate, "rolled damage restated in a toggle name: " + "; ".join(restate[:6])
    assert not bare, "un-bracketed number(s) in display text: " + "; ".join(bare[:6])
    print(f"  spell convention OK ({len(chg)} changes, plain formulas, all numbers in [[ ]])")


def test_maneuver_convention_compliance():
    """The module's curated maneuver_changes.json obeys the same convention. Skips when the Foundry
    module isn't checked out (e.g. CI)."""
    import json
    if not _MODULE_MANEUVERS.exists():
        print(f"  maneuver convention SKIPPED (no module at {_MODULE_MANEUVERS})")
        return
    data = json.loads(_MODULE_MANEUVERS.read_text(encoding='utf-8'))
    bare, restate, badf = [], [], []
    for name, e in data.items():
        mods = e.get('modifiers') or []
        badf += _plain_formula_violations(mods, f"maneuver[{name}]")
        rider = e.get('rider', '') or ''
        if _bare_numbers(rider):
            bare.append(f"maneuver[{name}]: {_bare_numbers(rider)} :: {rider[:70]}")
        dd = _restated_dice(rider, mods)
        if dd:
            restate.append(f"maneuver[{name}] rider restates {dd}")
    assert not badf, "non-plain maneuver formula(s): " + "; ".join(badf[:6])
    assert not bare, "un-bracketed number(s) in a maneuver rider: " + "; ".join(bare[:6])
    # restated secondary damage is allowed (trail/aura/ongoing); report but do not fail.
    if restate:
        print(f"  (note: {len(restate)} maneuver rider(s) repeat a modifier dice -- verify secondary)")
    print(f"  maneuver convention OK ({len(data)} entries, plain formulas, all numbers in [[ ]])")


def main():
    for fn in (test_bucketing, test_curated_files_load, test_selection,
               test_no_uncapped_scaling, test_csv_casing_canonical,
               test_spell_convention_compliance, test_maneuver_convention_compliance):
        fn()
    print("ALL SPELL-CONDITIONAL CHECKS PASSED")


if __name__ == "__main__":
    main()
