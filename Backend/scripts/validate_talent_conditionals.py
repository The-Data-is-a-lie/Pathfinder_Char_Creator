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


_MODULE_CS = Path(
    r"C:\Users\Daniel\AppData\Local\FoundryVTT\Data\modules\pf1e_random_char_generator"
    r"\templates\character_sheet_folder")


def main():
    import json
    total = 0
    bad = []
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
    if bad:
        print(f"{len(bad)} invalid talent conditional(s) (cost-only and/or malformed token):")
        for b in bad[:60]:
            print(f"  {b}")
        sys.exit(1)
    print(f"OK: {total} talent conditionals, 0 cost-only, 0 malformed tokens.")


if __name__ == "__main__":
    main()
