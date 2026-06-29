r"""One-time migration: normalize spell-name CASING in the generator's data to the FoundryVTT pf1
compendium's canonical Paizo casing (manual tool, never part of the generation pipeline).

Why: data/spells.csv over-title-cases articles/prepositions ("Shield Of The Dawnflower") while the
Foundry module's spell compendium every_spell.json uses canonical casing ("Shield of the Dawnflower").
The module's processSpell() lookup is now case-insensitive (so spells still build), but the source
data should be canonical so the names match everywhere -- this also fixes the display casing of the
attack-conditional TOGGLES the module derives from the selected name. ~250 names were affected.

What it does, using every_spell.json as the casing AUTHORITY (case-insensitive join):
  * data/spells.csv -- rewrites the FIRST column (name) only; every other column is left byte-for-byte
    unchanged (we split on '|' but only ever reassign field 0, so a stray '|' in a later field can't
    corrupt the row).
  * (--also-json) Backend/json/spells/spell_changes.json + spell_riders.json -- renames each top-level
    key to canonical casing and rewrites the leading "<Name>:" token of any `name` field. Matching in
    the backend (spells.py) and module is already case-insensitive, so this is cosmetic-only.

Names with no case-insensitive match in the compendium are left untouched and reported (they can't be
rendered as spell items regardless -- they're description-only).

Usage:
    C:\Python310\python.exe Backend/scripts/normalize_spell_name_casing.py [--dry-run] [--also-json]
        [--every-spell PATH] [--spells-csv PATH]
"""
import argparse
import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_SPELLS_CSV = REPO / "data" / "spells.csv"
DEFAULT_EVERY_SPELL = Path(os.path.expandvars(
    r"%LOCALAPPDATA%\FoundryVTT\Data\modules\pf1e_random_char_generator"
    r"\templates\character_sheet_folder\every_spell.json"))
SPELL_JSON = [REPO / "Backend" / "json" / "spells" / "spell_changes.json",
              REPO / "Backend" / "json" / "spells" / "spell_riders.json"]


def load_canonical(every_spell_path):
    """{lowercased name -> canonical name} from the compendium; first wins on a (rare) case clash."""
    data = json.loads(Path(every_spell_path).read_text(encoding="utf-8"))
    canon = {}
    for entry in data:
        name = (entry or {}).get("name")
        if name:
            canon.setdefault(name.lower(), name)
    return canon


def normalize_csv(csv_path, canon, dry_run):
    """Rewrite field 0 (name) of each data row to canonical casing. Returns (changed, unmatched)."""
    text = Path(csv_path).read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    changed, unmatched = [], []
    for i, line in enumerate(lines):
        if i == 0:
            continue  # header
        if not line.strip():
            continue
        parts = line.split("|")
        name = parts[0]
        if not name:
            continue
        lc = name.lower()
        if lc in canon:
            if canon[lc] != name:
                changed.append((name, canon[lc]))
                parts[0] = canon[lc]
                lines[i] = "|".join(parts)
        else:
            unmatched.append(name)
    if not dry_run and changed:
        Path(csv_path).write_text("".join(lines), encoding="utf-8")
    return changed, unmatched


def normalize_json(json_path, canon, dry_run):
    """Rename top-level keys + leading `name:` token to canonical casing. Returns list of changes."""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    changes, new = [], {}
    for key, entry in data.items():
        lc = key.lower()
        new_key = canon.get(lc, key)
        if new_key != key:
            changes.append((key, new_key))
        # Rewrite a leading "<OldName>:" / "<OldName>," token in the display name, if present.
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            entry["name"] = re.sub(r"^" + re.escape(key) + r"(?=[:,])", new_key, entry["name"])
        if new_key in new:
            print(f"  ! key collision, keeping first: {new_key!r}")
            continue
        new[new_key] = entry
    if not dry_run and changes:
        Path(json_path).write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n",
                                   encoding="utf-8")
    return changes


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spells-csv", type=Path, default=DEFAULT_SPELLS_CSV)
    ap.add_argument("--every-spell", type=Path, default=DEFAULT_EVERY_SPELL)
    ap.add_argument("--also-json", action="store_true",
                    help="also normalize spell_changes.json / spell_riders.json keys + name labels")
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    if not args.every_spell.exists():
        raise SystemExit(f"every_spell.json not found at {args.every_spell}\n"
                         f"Pass --every-spell PATH (the Foundry module's compendium).")
    canon = load_canonical(args.every_spell)
    print(f"canonical names loaded: {len(canon)}  (from {args.every_spell})")

    changed, unmatched = normalize_csv(args.spells_csv, canon, args.dry_run)
    print(f"\n{'DRY-RUN: ' if args.dry_run else ''}data/spells.csv name column:")
    print(f"  recased: {len(changed)}")
    for old, new in changed:
        print(f"    {old!r} -> {new!r}")
    print(f"  no compendium match (left as-is): {len(unmatched)}")
    for n in unmatched:
        print(f"    {n!r}")

    if args.also_json:
        for jp in SPELL_JSON:
            if not jp.exists():
                print(f"\n(skip) {jp.name} not present")
                continue
            jchanges = normalize_json(jp, canon, args.dry_run)
            print(f"\n{'DRY-RUN: ' if args.dry_run else ''}{jp.name}: {len(jchanges)} key(s) recased")
            for old, new in jchanges:
                print(f"    {old!r} -> {new!r}")


if __name__ == "__main__":
    main()
