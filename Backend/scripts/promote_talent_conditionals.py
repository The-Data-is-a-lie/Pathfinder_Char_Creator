"""Validate + bulk-promote reviewed DRAFT Spheres talent conditionals into the curated module dicts.

Reads the backend drafts and merges eligible entries into the FoundryVTT module's curated files
(the source of truth the live generator + the pf1-conditional-applier macro both read):

  Backend/json/class_data/spheres/magic_talent_conditionals.draft.json   -> <module>/magic_talent_conditionals.json
  Backend/json/class_data/spheres/combat_talent_conditionals.draft.json  -> <module>/combat_talent_conditionals.json

Both are nested {Sphere:{Talent:{modifiers,rider,default?}}}. Curation WINS on a case-insensitive
(sphere,talent) clash -- an existing curated entry is never overwritten; the draft only fills talents
curation hasn't reached. Gates per entry:
  * strip draft bookkeeping (`review`, `_*` keys);
  * KEEP only entries with a non-empty `rider` OR a non-empty `modifiers` list;
  * DROP (and report) an entry whose `rider` has unbalanced `[[ ]]`;
  * WARN (still promote) an entry whose `rider` has a bare unbracketed number (house style wants
    every number in `[[ ]]`) so it can be hand-fixed later.

Usage:
    C:\\Python310\\python.exe Backend/scripts/promote_talent_conditionals.py [--dry-run]
"""
import argparse
import json
import re
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_talent_conditionals import is_cost_only   # the two-prong structural gate

REPO = Path(__file__).resolve().parents[2]
SPHERES = REPO / "Backend" / "json" / "class_data" / "spheres"
MODULE_CS = Path(
    r"C:\Users\Daniel\AppData\Local\FoundryVTT\Data\modules\pf1e_random_char_generator"
    r"\templates\character_sheet_folder")

PAIRS = [
    ("magic", SPHERES / "magic_talent_conditionals.draft.json", MODULE_CS / "magic_talent_conditionals.json"),
    ("combat", SPHERES / "combat_talent_conditionals.draft.json", MODULE_CS / "combat_talent_conditionals.json"),
]


def norm(s):
    return re.sub(r"\s+", " ", str(s).lower().replace("'", "").replace("’", "").replace("`", "")).strip()


def clean_entry(e):
    return {k: v for k, v in e.items() if not str(k).startswith("_") and k != "review"}


def unbracketed_number(text):
    stripped = re.sub(r"\[\[.*?\]\]", "", str(text))
    m = re.search(r"(?<![\w])(\d[\d.d+]*)", stripped)
    return m.group(1) if m else None


def promote(label, draft_path, curated_path, dry_run):
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    curated = json.loads(curated_path.read_text(encoding="utf-8")) if curated_path.exists() else {}

    # index curated by (norm sphere, norm talent) -> actual sphere key
    sphere_key_by_norm = {norm(s): s for s in curated}
    cur_pairs = {(norm(s), norm(t)) for s, tt in curated.items() for t in (tt or {})}

    added = skip_dup = skip_empty = skip_unbalanced = warn_number = 0
    unbalanced, numbers = [], []

    for sph, talents in draft.items():
        if not isinstance(talents, dict):
            continue
        # merge into an existing curated sphere key of the same normalized name, else create it
        ck = sphere_key_by_norm.get(norm(sph), sph)
        curated.setdefault(ck, {})
        sphere_key_by_norm[norm(sph)] = ck
        for tname, entry in talents.items():
            if not isinstance(entry, dict):
                continue
            key = (norm(sph), norm(tname))
            if key in cur_pairs:
                skip_dup += 1
                continue
            clean = clean_entry(entry)
            if is_cost_only(clean):          # two-prong hard gate: an entry with no payload can't promote
                skip_empty += 1
                continue
            rider = str(clean.get("rider", "") or "").strip()
            mods = clean.get("modifiers") if isinstance(clean.get("modifiers"), list) else []
            if rider.count("[[") != rider.count("]]"):
                skip_unbalanced += 1
                unbalanced.append(f"{sph}/{tname}")
                continue
            bad = unbracketed_number(rider)
            if bad:
                warn_number += 1
                numbers.append(f"{sph}/{tname}: {bad!r}")
            curated[ck][tname] = clean
            cur_pairs.add(key)
            added += 1

    print(f"\n== {label} ==")
    print(f"  + promoted:              {added}")
    print(f"  - skipped (curated):     {skip_dup}")
    print(f"  - skipped (empty):       {skip_empty}")
    print(f"  - skipped (unbalanced):  {skip_unbalanced}" + (f"  {unbalanced[:6]}" if unbalanced else ""))
    print(f"  ! warn (bare number):    {warn_number}" + (f"  e.g. {numbers[:4]}" if numbers else ""))
    total = sum(len(v) for v in curated.values())
    print(f"  curated talents now:     {total}")
    if not dry_run:
        curated_path.write_text(json.dumps(curated, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  wrote {curated_path.name}")
    return added, warn_number


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    tot_added = tot_warn = 0
    for label, dpath, cpath in PAIRS:
        a, w = promote(label, dpath, cpath, args.dry_run)
        tot_added += a
        tot_warn += w
    print(f"\nTOTAL promoted: {tot_added}  (bare-number warnings: {tot_warn})")
    if args.dry_run:
        print("(dry run -- no files written)")


if __name__ == "__main__":
    main()
