"""Structural guard for the Path of War change files (maneuvers + stances).

WHY THIS EXISTS
---------------
Every other curated conditional set had a structural validator; the PoW change files did not. That
mattered because `fix_maneuver_crit.py` deliberately treats any non-"normal" `critical` as an
intentional authoring choice and leaves it alone -- so a hand-typed `"onCrit"` (never a pf1 value;
pf1 deletes it on the next sheet edit and silently drops the modifier) would have survived here
forever. The same typo already shipped once on six burst weapon qualities.

Entries are a FLAT ``{name: {modifiers, rider, ...}}`` map, unlike the ``{conditionals: [...]}``
shape `validate_quality_effects.check_conditional` expects, so the checks are adapted rather than
reused wholesale -- but the whitelists themselves are imported, so there is still one owner per rule.

Run:  python Backend/scripts/gates/validate_maneuver_changes.py
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _harness import Report, REPO                 # noqa: E402
from damage_types import classify_damage_type      # noqa: E402  the type vocabulary
import validate_quality_effects as vqe             # noqa: E402  shared modifier whitelists

MODULE_CS = Path(os.path.expandvars(
    r"%LOCALAPPDATA%\FoundryVTT\Data\modules\pf1e_random_char_generator"
    r"\templates\character_sheet_folder"))

TARGETS = [
    REPO / "Backend" / "json" / "class_data" / "path_of_war" / "maneuver_changes.draft.json",
    REPO / "Backend" / "json" / "class_data" / "path_of_war" / "stance_changes.draft.json",
    MODULE_CS / "maneuver_changes.json",
    MODULE_CS / "stance_changes.json",
]

# Bookkeeping keys the builder writes alongside the real payload.
META_KEYS = {"review", "rider", "modifiers", "_discipline", "_kind", "_level", "_snippets",
             "_source", "_note", "name", "default", "conditionals", "changes", "contextNotes"}

errors, warnings = [], []
REPORT = Report('validate_maneuver_changes', errors=errors, warnings=warnings)


def check_modifier(owner, m):
    if not isinstance(m, dict):
        errors.append(f"{owner}: modifier is not an object")
        return
    unknown = set(m) - vqe.MOD_KEYS
    if unknown:
        errors.append(f"{owner}: unknown modifier key(s) {sorted(unknown)}")
    if m.get("target") not in vqe.MOD_TARGETS:
        errors.append(f"{owner}: bad modifier target {m.get('target')!r}")
    if "critical" in m and m.get("critical") not in vqe.MOD_CRITICAL:
        errors.append(f"{owner}: critical {m.get('critical')!r} is not a pf1 value "
                      f"{sorted(vqe.MOD_CRITICAL)} -- pf1 deletes it and drops the modifier")
    dt = m.get("damageType")
    if dt is not None and not isinstance(dt, list):
        errors.append(f"{owner}: damageType must be a list")
    for t in (dt or []):
        state, suggestion = classify_damage_type(t)
        if state == "alias":
            errors.append(f"{owner}: damageType {t!r} is rules prose, not a pf1 id "
                          f"-- use {suggestion!r}")
        elif state == "unknown":
            warnings.append(f"{owner}: damageType {t!r} is not a known pf1 id "
                            f"(add it to damage_types.py if it is legitimate)")
    # Formulas stay PLAIN: the consumers append the [Source] label, and an inline [[ ]] in a formula
    # nests into the flavor and crashes pf1's d20 parser.
    formula = str(m.get("formula", ""))
    if "[[" in formula or "]]" in formula:
        errors.append(f"{owner}: modifier formula must be plain, got {formula!r}")


def check_file(path):
    if not path.exists():
        print(f"SKIP {path.name} (not found)")
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        errors.append(f"{path.name}: top level must be an object")
        return 0
    n = 0
    for name, entry in data.items():
        if not isinstance(entry, dict):
            errors.append(f"{path.name}[{name}]: entry must be an object")
            continue
        unknown = set(entry) - META_KEYS
        if unknown:
            warnings.append(f"{path.name}[{name}]: unexpected key(s) {sorted(unknown)}")
        for i, m in enumerate(entry.get("modifiers") or []):
            check_modifier(f"{path.name}[{name}].modifiers[{i}]", m)
            n += 1
    return n


def main():
    total = 0
    for p in TARGETS:
        total += check_file(p)
    return REPORT.finish(f"{total} PoW modifiers validated")


if __name__ == "__main__":
    sys.exit(main())
