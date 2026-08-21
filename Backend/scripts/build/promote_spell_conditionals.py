"""Bulk-promote reviewed DRAFT spell conditionals into the curated finals.

Reads Backend/json/spells/spell_conditionals.draft.json and merges eligible entries into:
  - spell_riders.json  (Buckets B damaging-touch + C offensive save/area/debuff)
  - spell_changes.json (Bucket A attack/damage buffs)

Curation WINS on a case-insensitive name clash -- an existing curated entry is never overwritten;
the draft only fills spells curation hasn't reached. Promotion applies the same gates the manual
curation batches and the palette's load_spell_conditional_sources() use:

  * strip all draft bookkeeping (`review`, `_*` keys);
  * DROP an entry whose save is `harmless` (the classifier misread a buff/cure as offensive);
  * DROP "(see spell description)" stub riders (they restate nothing the compendium save block
    doesn't already show);
  * for Bucket C, DROP the entry entirely if no real rider survives (a bare save is redundant with
    the pf1 compendium spell, which already carries the save);
  * for Bucket B, KEEP a rider-less entry ONLY when it still carries a save -- the formal save block
    on a damaging touch spell is the whole point (the module applies it when the compendium action
    lacks a save). A B entry with neither a save nor a rider is an empty shell (its damage already
    lives on the compendium spell) and is dropped.

A final prune drops any resulting entry that carries neither a save nor a rider, so the curated file
always satisfies the validator's "save and/or riders" rule even for pre-existing entries.

Run `python Backend/scripts/gates/validate_spell_conditionals.py` afterward to gate the result.

Usage:
    python Backend/scripts/promote_spell_conditionals.py [--dry-run]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import REPO   # noqa: E402
SPELLS = REPO / "Backend" / "json" / "spells"
DRAFT = SPELLS / "spell_conditionals.draft.json"
RIDERS = SPELLS / "spell_riders.json"
CHANGES = SPELLS / "spell_changes.json"

STUB = "(see spell description)"


def _clean(entry):
    """Draft entry minus review/_* bookkeeping keys."""
    return {k: v for k, v in entry.items() if not str(k).startswith("_") and k != "review"}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def promote(dry_run=False):
    draft = _load(DRAFT)
    riders = _load(RIDERS)
    changes = _load(CHANGES)

    rid_lc = {str(k).lower() for k in riders}
    chg_lc = {str(k).lower() for k in changes}

    added_riders = added_changes = 0
    skip_dup = skip_harmless = skip_stub_only = skip_empty = 0

    for name, entry in draft.items():
        if not isinstance(entry, dict):
            continue
        bucket = str(entry.get("_bucket", ""))
        lc = str(name).lower()
        clean = _clean(entry)

        if bucket.startswith("A"):
            if lc in chg_lc:
                skip_dup += 1
                continue
            changes[name] = clean
            chg_lc.add(lc)
            added_changes += 1
            continue

        if not bucket.startswith(("B", "C")):
            continue

        if lc in rid_lc:
            skip_dup += 1
            continue
        if (clean.get("save") or {}).get("harmless"):
            skip_harmless += 1
            continue
        clean["riders"] = [r for r in (clean.get("riders") or []) if STUB not in r]
        if not clean["riders"]:
            # No real rider survives. For Bucket C a bare save is redundant with the pf1 compendium
            # spell (which already carries the save) -> drop. For Bucket B a save on a damaging touch
            # spell is worth keeping; with neither save nor rider the entry is an empty shell -> drop.
            if bucket.startswith("C") or not clean.get("save"):
                skip_stub_only += 1
                continue
        riders[name] = clean
        rid_lc.add(lc)
        added_riders += 1

    # Prune any entry (freshly promoted OR pre-existing curation) that carries neither a save nor a
    # rider, so the curated file always satisfies the validator regardless of its prior state.
    for name in [k for k, v in riders.items()
                 if not (v.get("save") or [r for r in (v.get("riders") or []) if r])]:
        del riders[name]
        skip_empty += 1

    print(f"draft entries scanned:            {len(draft)}")
    print(f"  + promoted to spell_riders:     {added_riders}")
    print(f"  + promoted to spell_changes:    {added_changes}")
    print(f"  - skipped (already curated):    {skip_dup}")
    print(f"  - skipped (harmless save):      {skip_harmless}")
    print(f"  - skipped (stub/empty shell):   {skip_stub_only}")
    print(f"  - pruned (neither save/rider):  {skip_empty}")
    print(f"curated spell_riders total now:   {len(riders)}")
    print(f"curated spell_changes total now:  {len(changes)}")

    if dry_run:
        print("\n(dry run -- no files written)")
        return

    RIDERS.write_text(json.dumps(riders, indent=2, ensure_ascii=False), encoding="utf-8")
    CHANGES.write_text(json.dumps(changes, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {RIDERS.name} + {CHANGES.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report counts without writing")
    args = ap.parse_args()
    promote(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
