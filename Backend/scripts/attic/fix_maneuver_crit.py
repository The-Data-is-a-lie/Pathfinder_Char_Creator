"""Path of War maneuver conditionals: make dice damage riders non-multiplying.

Pathfinder rule: a maneuver's *extra* damage dice are not multiplied on a critical hit, so a
conditional damage modifier whose formula carries dice (1d6, 8d6, "4d6 + @INITMOD") must use the pf1
"Non-multiplying Bonus Formula" (`critical: "nonCrit"`). A flat / @-reference-only damage modifier
(no dice) stays `critical: "normal"` -- it scales with the crit like the weapon's other static
damage.

This rewrites `maneuver_changes`-shaped JSON in place: a top-level dict of
  { "<Maneuver>": { "modifiers": [ {formula, target, subTarget, type, damageType, critical}, ... ],
                    "rider": "..." }, ... }
Only `target == "damage"` modifiers are touched, and only when their `critical` is missing / "" /
"normal" (an intentional "crit"/"nonCrit" is preserved). Attack modifiers are left alone -- the
critical field is meaningless for them.

Idempotent: re-running reports 0 changes. Build-time emission applies the same rule in
build_maneuver_changes.py (`_crit_for`); this script fixes the hand-curated module copy that the
generator does not regenerate.

Usage:
    C:\\Python310\\python.exe Backend/scripts/fix_maneuver_crit.py <path-to-maneuver_changes.json> [more.json ...]
"""
import json
import re
import sys
from pathlib import Path

# A real dice term, e.g. 1d6 / 8d6 / the "4d6" in "4d6 + @INITMOD". Mirrors _DICE_RE in
# build_pow_template_actor.py / build_maneuver_changes.py.
_DICE_RE = re.compile(r"\d+d\d+")


def _crit_for(formula):
    """nonCrit if the damage formula carries dice (extra dice don't multiply on a crit), else normal."""
    return "nonCrit" if _DICE_RE.search(str(formula)) else "normal"


def fix_file(path):
    """Apply the dice -> nonCrit rule to one maneuver_changes JSON file. Returns the change count."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for entry in data.values():
        if not isinstance(entry, dict):
            continue
        for mod in entry.get("modifiers", []) or []:
            if mod.get("target") != "damage":
                continue
            # only auto-classify the default value; keep a deliberate crit/nonCrit
            if mod.get("critical", "normal") not in (None, "", "normal"):
                continue
            want = _crit_for(mod.get("formula", ""))
            if want != mod.get("critical", "normal"):
                mod["critical"] = want
                changed += 1
    if changed:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    for arg in argv:
        n = fix_file(arg)
        print(f"{arg}: {n} damage modifier(s) -> nonCrit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
