"""Regression checks for the Spheres talent-conditional two-prong rule (run directly; no pytest, per
the repo convention -- mirrors test_spell_conditionals.py).

    C:\\Python310\\python.exe Backend/scripts/tests/test_talent_conditionals.py

Seams under test (agreed):
  A. validate_talent_conditionals -- the structural "cost-only" predicate.
  B/C. the applier match (Python port) against vendored slim actor fixtures -- the real characters end
       up with exactly the right conditionals attached.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import JSON_DIR, Report  # noqa: E402

import validate_talent_conditionals as vtc  # noqa: E402
import talent_conditional_match as tcm  # noqa: E402

REPORT = Report('test_talent_conditionals')


# --- Slice 1: the validator (Seam A) ---------------------------------------------------------------
def test_validator_flags_cost_only():
    """A conditional with empty modifiers whose rider is ONLY a cost/contingency has no payload ->
    must be flagged. An entry with a modifier, or a rider carrying a real effect, must NOT be."""
    cost_only = [
        {"modifiers": [], "rider": "expend martial focus"},
        {"modifiers": [], "rider": "spend [[1]] spell point"},
        {"modifiers": [], "rider": "expend martial focus; special attack action"},
        {"modifiers": [], "rider": "special attack action"},
        {"modifiers": [], "rider": "as a swift action"},
    ]
    has_payload = [
        # a real damage/attack modifier -> payload, regardless of rider
        {"modifiers": [{"formula": "2d6", "target": "damage"}], "rider": "expend martial focus"},
        # cost + a real on-target effect -> payload
        {"modifiers": [], "rider": "expend martial focus; target is battered for [[1]] round"},
        # a save + condition -> payload
        {"modifiers": [], "rider": "Reflex Save [[ 10 + floor(@spheres.cl.total / 2) + "
                                   "max(@abilities.int.mod, @abilities.wis.mod, @abilities.cha.mod) ]] negates"},
        # a reroll/miss-chance rider -> payload
        {"modifiers": [], "rider": "vs a concealed target, roll the miss chance twice, use the better"},
    ]
    for e in cost_only:
        REPORT.check(vtc.is_cost_only(e), f"should be flagged cost-only: {e['rider']!r}")
    for e in has_payload:
        REPORT.check(not vtc.is_cost_only(e), f"should NOT be flagged: {e.get('rider')!r}")
    # find_violations rolls it up over a nested {Sphere:{Talent:entry}} dict
    d = {"Berserker": {"Berserking": cost_only[2], "Brutal Strike": has_payload[0]}}
    viol = vtc.find_violations(d)
    REPORT.check([v[1] for v in viol] == ["Berserking"], f"expected only Berserking flagged, got {viol}")
    print(f"  validator checked (flags {len(cost_only)} cost-only, passes {len(has_payload)} with payload)")


# --- Slice 2: the applier match port (Seam C) ------------------------------------------------------
def test_matcher_attaches_expected():
    """The Python port of the applier's norm-match: a talent attaches iff its (sphere,name) is in the
    magic or combat dict; case/apostrophe-insensitive; a "(source)"-tagged talent name still matches
    its base key; reports whether the attached conditional carries a damage/attack modifier."""
    magic = {"Weather": {"Black Ice": {"modifiers": [], "rider": "Reflex negates"}}}
    combat = {"Berserker": {"Brutal Strike": {"modifiers": [{"formula": "2*@attributes.bab.total",
                                                             "target": "damage"}], "rider": "battered"}},
              "Fencing": {"Ragdoll Swing": {"modifiers": [], "rider": "precision"}}}
    actor = [{"name": "black ice", "sphere": "weather"},          # case-insensitive
             {"name": "Brutal Strike", "sphere": "berserker"},
             {"name": "Ragdoll Swing (impale)", "sphere": "fencing"},   # source-tag stripped
             {"name": "Does Not Exist", "sphere": "berserker"}]
    res = {r["name"]: r for r in tcm.match_actor(actor, magic, combat)}
    REPORT.check(res["black ice"]["matched"] and not res["black ice"]["has_modifier"],
                f'black ice: expected matched=True, has_modifier=False, got {res["black ice"]}')
    REPORT.check(res["Brutal Strike"]["matched"] and res["Brutal Strike"]["has_modifier"],
                f'Brutal Strike: expected matched=True, has_modifier=True, got {res["Brutal Strike"]}')
    REPORT.check(res["Ragdoll Swing (impale)"]["matched"], "source-tagged name should match base key")
    REPORT.check(not res["Does Not Exist"]["matched"],
                f'Does Not Exist: expected matched=False, got {res["Does Not Exist"]}')
    print("  matcher checked (case/apostrophe/source-tag; modifier detection)")


# --- Slice 3: fixture acceptance + the real-data invariant (Seams A + B via C) ----------------------
_FIXTURES = JSON_DIR / "test_fixtures"


def _load_module_dicts():
    magic = vtc._MODULE_CS / "magic_talent_conditionals.json"
    combat = vtc._MODULE_CS / "combat_talent_conditionals.json"
    if not magic.exists() or not combat.exists():
        return None, None
    return json.loads(magic.read_text(encoding="utf-8")), json.loads(combat.read_text(encoding="utf-8"))


def _matched(fixture_slug, magic, combat):
    fx = json.loads((_FIXTURES / f"{fixture_slug}.talents.json").read_text(encoding="utf-8"))
    return {r["name"]: r for r in tcm.match_actor(fx["talents"], magic, combat)}


def test_no_cost_only_in_real_dicts():
    magic, combat = _load_module_dicts()
    if magic is None:
        print("  real-dict invariant SKIPPED (module not checked out)"); return
    viol = vtc.find_violations(magic) + vtc.find_violations(combat)
    REPORT.check(not viol, f"{len(viol)} cost-only conditional(s) remain, e.g. {viol[:5]}")
    print(f"  real-dict invariant checked ({len(viol)} cost-only)")


def test_pascal_warner_expected_set():
    magic, combat = _load_module_dicts()
    if magic is None:
        print("  Pascal fixture SKIPPED (module not checked out)"); return
    m = _matched("pascal-warner", magic, combat)
    for gone in ("Swift Guardian", "Battle Ready Armor", "Berserking"):
        # Guard: `m[gone]` below would KeyError if the fixture doesn't carry this talent at all.
        if not REPORT.check(gone in m, f"fixture missing {gone!r}"):
            continue
        REPORT.check(not m[gone]["matched"], f"{gone} must NOT attach a conditional (defensive/utility)")
    REPORT.check(m["Brutal Strike"]["matched"] and m["Brutal Strike"]["has_modifier"],
                "Brutal Strike must attach WITH a damage modifier")
    print("  Pascal Warner checked (3 defensive/utility talents, Brutal Strike)")


def test_abebe_regression():
    magic, combat = _load_module_dicts()
    if magic is None:
        print("  Abebe fixture SKIPPED (module not checked out)"); return
    m = _matched("abebe-astuti", magic, combat)
    # foe-debuff (Black Ice: shroud, halve speed + Reflex-or-fall) + attack effect (Mirage Sight:
    # reroll miss chance vs concealment) -> keepers.
    for keep in ("Black Ice", "Mirage Sight"):
        REPORT.check(m.get(keep, {}).get("matched"), f"{keep} regressed (should still attach)")
    # Mantle grants the weather-mantle to allies -> an ally-buff, NOT a weapon conditional -> removed.
    REPORT.check(not m.get("Mantle", {}).get("matched"), "Mantle is an ally-buff; must NOT attach")
    print("  Abebe regression checked (Black Ice + Mirage Sight, Mantle)")


# --- Slices 4 & 5: regression guards (drafter + promote gate) --------------------------------------
def test_drafter_emits_no_cost_only():
    import build_talent_conditionals as btc
    draft = btc.build_draft("might")          # smaller source; the fix applies to both systems
    bad = [(s, t) for s, tt in draft.items() for t, e in tt.items() if vtc.is_cost_only(e)]
    REPORT.check(not bad, f"drafter emitted {len(bad)} cost-only seed(s), e.g. {bad[:5]}")
    print(f"  drafter checked ({sum(len(v) for v in draft.values())} seeds, {len(bad)} cost-only)")


def test_promote_rejects_cost_only():
    import promote_talent_conditionals as ptc
    import tempfile
    draft = {"TestSphere": {
        "Keeper": {"modifiers": [{"formula": "1d6", "target": "damage"}], "rider": "", "review": True},
        "Garbage": {"modifiers": [], "rider": "expend martial focus", "review": True}}}
    with tempfile.TemporaryDirectory() as td:
        dp, cp = Path(td) / "d.json", Path(td) / "c.json"
        dp.write_text(json.dumps(draft), encoding="utf-8")
        ptc.promote("test", dp, cp, dry_run=False)
        curated = json.loads(cp.read_text(encoding="utf-8"))
        names = {t for tt in curated.values() for t in tt}
    REPORT.check("Keeper" in names, "promote dropped a valid entry")
    REPORT.check("Garbage" not in names, "promote gate let a cost-only entry through")
    print("  promote gate checked (cost-only rejection, keeper promotion)")


def main():
    for fn in (test_validator_flags_cost_only,
               test_matcher_attaches_expected,
               test_no_cost_only_in_real_dicts,
               test_pascal_warner_expected_set,
               test_abebe_regression,
               test_drafter_emits_no_cost_only,
               test_promote_rejects_cost_only):
        fn()
    return REPORT.finish(f'{REPORT.checks} checks')


if __name__ == "__main__":
    sys.exit(main())
