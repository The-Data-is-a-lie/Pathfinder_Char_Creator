"""Deterministic first pass of the two-prong re-curation: REMOVE an existing talent conditional whose
source benefit text has NO attack relevance at all (crafting/movement/utility/summon/transform —
e.g. Bear Form's `spend [[1]] spell point`). These are unambiguous false positives; the
relevance-PASS remainder (which may still be a defensive false positive, or a real talent the drafter
under-captured) is left for the agent audit to keep/fix/remove.

    C:\\Python310\\python.exe Backend/scripts/prune_talent_conditionals.py [--apply]

Writes the two module dicts in place (with --apply); dry-run otherwise. Reports, per system, removed
vs. relevance-pass-kept, and how many of the kept are still cost-only (the agent audit's worklist).
"""
import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPHERES = REPO / "Backend" / "json" / "class_data" / "spheres"
MODULE_CS = Path(
    r"C:\Users\Daniel\AppData\Local\FoundryVTT\Data\modules\pf1e_random_char_generator"
    r"\templates\character_sheet_folder")

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from talent_conditional_match import norm, strip_source          # reuse the applier-match normalizers
from validate_talent_conditionals import is_cost_only

# Attack-relevance signal (over-inclusive on purpose: a false keep just goes to the agent audit).
RELEVANT = re.compile(
    r"\d+d\d+|\bbleed\b|precision damage|saving throw|\bsave\b|attack roll|martial focus|"
    r"special attack action|attack of opportunity|\bblast\b|\bstrike\b|miss chance|reroll|conceal|"
    r"\bpenalt(?:y|ies)\b|sickened|staggered|shaken|dazed|dazzled|blinded|deafened|entangled|"
    r"fatigued|exhausted|nauseated|frightened|panicked|paralyzed|stunned|\bprone\b|confused|"
    r"place this shroud|when you (?:hit|strike|damage)|ability damage|ability drain|"
    r"half speed|cannot move|bull rush|\btrip\b|grapple|disarm|combat maneuver", re.IGNORECASE)

SYS = {  # module dict filename -> (power|might source, advanced-talents key)
    "magic_talent_conditionals.json": ("spheres_of_power.json", "magic"),
    "combat_talent_conditionals.json": ("spheres_of_might_enriched.json", "might"),
}


def benefit_index(src_file, adv_key):
    idx = {}
    src = json.loads((SPHERES / src_file).read_text(encoding="utf-8"))
    for sphere, talents in src.items():
        if not isinstance(talents, dict):
            continue
        for t, rec in talents.items():
            if isinstance(rec, dict):
                idx[norm(t)] = str(rec.get("benefit", "") or rec.get("description", ""))
    adv = json.loads((SPHERES / "advanced_talents.json").read_text(encoding="utf-8")).get(adv_key, {})
    for sphere, lst in adv.items():
        for x in lst:
            if isinstance(x, dict) and x.get("name"):
                idx.setdefault(norm(x["name"]), str(x.get("benefit", "") or x.get("description", "")))
    return idx


def run(apply):
    for fn, (src_file, adv_key) in SYS.items():
        p = MODULE_CS / fn
        if not p.exists():
            print(f"SKIP {fn}"); continue
        d = json.loads(p.read_text(encoding="utf-8"))
        idx = benefit_index(src_file, adv_key)
        removed = kept = kept_cost_only = no_source = 0
        for sphere in list(d):
            for talent in list(d[sphere]):
                benefit = idx.get(norm(talent)) or idx.get(norm(strip_source(talent)))
                if benefit is None:
                    no_source += 1; kept += 1; continue         # can't assess -> keep (agent may catch)
                if not RELEVANT.search(benefit):
                    del d[sphere][talent]; removed += 1          # utility false positive
                else:
                    kept += 1
                    if is_cost_only(d[sphere][talent]):
                        kept_cost_only += 1
            if not d[sphere]:
                del d[sphere]
        print(f"\n== {fn} ==")
        print(f"  removed (utility, relevance-fail): {removed}")
        print(f"  kept (relevance-pass):             {kept}   [no source match: {no_source}]")
        print(f"  ...of kept, still cost-only:       {kept_cost_only}  <- agent audit worklist")
        if apply:
            p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  wrote {fn}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    run(ap.parse_args().apply)
    print("\n(dry run)" if "--apply" not in __import__("sys").argv else "")


if __name__ == "__main__":
    main()
