"""The two-prong rule's STRUCTURAL guard for Spheres talent conditionals: an entry must carry a
mechanical payload, never just a cost. A conditional with empty `modifiers` whose `rider` reduces to
nothing after removing contingency/cost phrases (expend martial focus, spend [[N]] spell point,
special attack action, attack action / AoO, "as a <X> action") is **cost-only** and INVALID.

(The other prong -- payload must be *attack-relevant*, not defensive/utility -- is a semantic call
made during curation and pinned by the actor-fixture tests; it can't be judged from the entry shape
alone. This module enforces the part that CAN be checked mechanically, and is reused as the promote
hard-gate + the test invariant.)

    C:\\Python310\\python.exe Backend/scripts/validate_talent_conditionals.py   # validates the module dicts
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from damage_types import classify_damage_type  # noqa: E402  the one owner of the type vocabulary

# Cost/contingency phrases that carry NO payload on their own.
_CONTINGENCY = re.compile(
    r"expend(?:s|ing)?\s+(?:your|their|his|her)?\s*martial\s+focus"
    r"|spend(?:s|ing)?\s+(?:\[\[)?\s*(?:a|\d+)\s*(?:\]\])?\s+spell\s+points?"
    r"|special\s+attack\s+action"
    r"|attack\s+action\s+or\s+(?:an?\s+)?attack\s+of\s+opportunity(?:\s+only)?"
    r"|attack\s+of\s+opportunity\s+only"
    r"|as\s+(?:a|an)\s+(?:swift|standard|immediate|free|move)\s+action"
    r"|^\s*on\s+(?:a\s+)?hit,?",
    re.IGNORECASE)


def is_cost_only(entry):
    """True if the entry has no mechanical payload: empty `modifiers` AND a rider that is empty or,
    once contingency phrases are stripped, has no meaningful effect text left."""
    if not isinstance(entry, dict):
        return True
    mods = entry.get("modifiers")
    if isinstance(mods, list) and len(mods) > 0:
        return False                                   # a real modifier is a payload
    rider = str(entry.get("rider", "") or "")
    remainder = _CONTINGENCY.sub(" ", rider)
    remainder = re.sub(r"[\[\];,.\-\s]+", " ", remainder).strip()   # drop separators + [[ ]] scaffolding
    return len(remainder) < 3


def find_violations(conditionals):
    """[(sphere, talent, rider), ...] for every cost-only entry in a nested {Sphere:{Talent:entry}}."""
    out = []
    for sphere, talents in (conditionals or {}).items():
        if not isinstance(talents, dict):
            continue
        for talent, entry in talents.items():
            if is_cost_only(entry):
                out.append((sphere, talent, str((entry or {}).get("rider", ""))[:60]))
    return out


# Only @spheres.cl takes ".total"; @spheres.cam / @spheres.pam are bare ability mods. A stray ".total"
# survives the module/applier substitution as "@abilities.<x>.mod.total" and silently resolves to 0.
_BAD_TOKEN = re.compile(r"@spheres\.(?:cam|pam)\.total", re.IGNORECASE)


def find_bad_tokens(conditionals):
    """[(sphere, talent, token), ...] for malformed @spheres.cam/.pam tokens carrying a stray '.total'."""
    out = []
    for sphere, talents in (conditionals or {}).items():
        if not isinstance(talents, dict):
            continue
        for talent, entry in talents.items():
            blob = str((entry or {}).get("rider", "") or "")
            for m in ((entry or {}).get("modifiers") or []):
                if isinstance(m, dict):
                    blob += " " + str(m.get("formula", "") or "")
            for tok in _BAD_TOKEN.findall(blob):
                out.append((sphere, talent, tok))
    return out


# pf1's action-model enum is exactly {NORMAL:"normal", CRITICAL:"crit", NON_CRITICAL:"nonCrit"}.
# An unknown value -- historically "onCrit" -- is DELETED by pf1 on the next sheet edit, silently
# dropping the modifier. That shipped once on six burst weapon qualities before
# validate_quality_effects.MOD_CRITICAL started guarding the quality data; talents were never
# covered, so the same typo could ride a Spheres conditional forever. This closes that gap.
MOD_CRITICAL = {"normal", "crit", "nonCrit"}


def find_bad_critical(conditionals):
    """[(sphere, talent, value), ...] for modifiers whose `critical` is not a real pf1 value."""
    out = []
    for sphere, talents in (conditionals or {}).items():
        if not isinstance(talents, dict):
            continue
        for talent, entry in talents.items():
            for m in ((entry or {}).get("modifiers") or []):
                if isinstance(m, dict) and "critical" in m and m.get("critical") not in MOD_CRITICAL:
                    out.append((sphere, talent, m.get("critical")))
    return out


# The Path-of-War roll-data tokens are meaningless on a Spheres talent (the sphere path substitutes
# its own tokens), so they must never appear here. The decision-rules doc long claimed "the promote
# check rejects them" -- nothing did, until this check.
_POW_TOKENS = re.compile(r"@INITMOD|@SKILLCHECK|@ATTACKCHECK", re.IGNORECASE)


def find_pow_tokens(conditionals):
    """[(sphere, talent, token), ...] for PoW-only tokens leaking into Spheres formulas/riders."""
    out = []
    for sphere, talents in (conditionals or {}).items():
        if not isinstance(talents, dict):
            continue
        for talent, entry in talents.items():
            blob = str((entry or {}).get("rider", "") or "")
            for m in ((entry or {}).get("modifiers") or []):
                if isinstance(m, dict):
                    blob += " " + str(m.get("formula", "") or "")
            for tok in _POW_TOKENS.findall(blob):
                out.append((sphere, talent, tok))
    return out


def find_bad_damage_type(conditionals):
    """[(sphere, talent, value, suggestion|None), ...] for damageType members that are not pf1 ids.

    A prose alias ("electricity" -- rules text; pf1's id is "electric") is provably wrong and breaks
    resistance matching silently; an unrecognised value is only suspicious. The caller errors on the
    first and warns on the second.
    """
    out = []
    for sphere, talents in (conditionals or {}).items():
        if not isinstance(talents, dict):
            continue
        for talent, entry in talents.items():
            for m in ((entry or {}).get("modifiers") or []):
                if not isinstance(m, dict):
                    continue
                for t in (m.get("damageType") or []):
                    state, suggestion = classify_damage_type(t)
                    if state != "ok":
                        out.append((sphere, talent, t, suggestion))
    return out


_DICE = re.compile(r"[\d)]d\d")


def find_untyped_damage(conditionals):
    """[(sphere, talent, formula), ...] WARN list: a dice DAMAGE modifier with an empty damageType
    renders "undefined" on the sheet (consumers coerce to untyped, but a real element is preferable)."""
    out = []
    for sphere, talents in (conditionals or {}).items():
        if not isinstance(talents, dict):
            continue
        for talent, entry in talents.items():
            for m in ((entry or {}).get("modifiers") or []):
                if not isinstance(m, dict) or m.get("target") != "damage":
                    continue
                dt = m.get("damageType")
                if _DICE.search(str(m.get("formula", ""))) and not (isinstance(dt, list) and dt):
                    out.append((sphere, talent, str(m.get("formula", ""))))
    return out


_MODULE_CS = Path(
    r"C:\Users\Daniel\AppData\Local\FoundryVTT\Data\modules\pf1e_random_char_generator"
    r"\templates\character_sheet_folder")


def main():
    import json
    total = 0
    bad = []
    warns = []
    for fn in ("magic_talent_conditionals.json", "combat_talent_conditionals.json"):
        p = _MODULE_CS / fn
        if not p.exists():
            print(f"SKIP {fn} (not found)")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        total += sum(len(v) for v in d.values())
        for sphere, talent, rider in find_violations(d):
            bad.append(f"{fn.split('_')[0]}/{sphere}/{talent}: cost-only -- {rider}")
        for sphere, talent, tok in find_bad_tokens(d):
            bad.append(f"{fn.split('_')[0]}/{sphere}/{talent}: malformed token {tok} (cam/pam take no .total)")
        for sphere, talent, val in find_bad_critical(d):
            bad.append(f"{fn.split('_')[0]}/{sphere}/{talent}: critical {val!r} is not a pf1 value "
                       f"{sorted(MOD_CRITICAL)} -- pf1 will delete it and drop the modifier")
        for sphere, talent, tok in find_pow_tokens(d):
            bad.append(f"{fn.split('_')[0]}/{sphere}/{talent}: Path-of-War token {tok} in a Spheres conditional")
        for sphere, talent, val, suggestion in find_bad_damage_type(d):
            where = f"{fn.split('_')[0]}/{sphere}/{talent}"
            if suggestion:
                bad.append(f"{where}: damageType {val!r} is rules prose, not a pf1 id -- use {suggestion!r}")
            else:
                warns.append(f"{where}: damageType {val!r} is not a known pf1 id "
                             f"(add it to damage_types.py if it is legitimate)")
        for sphere, talent, formula in find_untyped_damage(d):
            warns.append(f"{fn.split('_')[0]}/{sphere}/{talent}: dice damage, empty damageType "
                         f"(coerced to untyped; prefer a real element) -- {formula}")
    for w in warns:
        print(f"WARN: {w}")
    if bad:
        print(f"{len(bad)} invalid talent conditional(s) (cost-only and/or malformed token):")
        for b in bad[:60]:
            print(f"  {b}")
        sys.exit(1)
    print(f"OK: {total} talent conditionals, 0 cost-only, 0 malformed tokens ({len(warns)} untyped-damage warning(s)).")


if __name__ == "__main__":
    main()
