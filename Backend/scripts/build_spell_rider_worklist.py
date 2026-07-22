"""Slice the curated spell_riders.json + data/spells.csv into per-batch WORKLIST files for the
detailed-effect re-authoring sweep (docs/spell_rider_detail_sweep_plan.md).

Each record hands an authoring agent everything it needs to write a maximally-verbose Effect body for
one spell, grounded ONLY in the spell's own text:

    { name, spell_level, range, saving_throw, spell_resistance, duration, targets,
      description, base_ref_description?,     # base spell text for "works like <X>" stubs
      current_rider, current_save, csv_save,  # what's there now + the real save from the CSV
      has_modifier_damage }                   # True (Bucket B) -> the primary dice roll as a modifier;
                                              # the agent must NOT restate them

Usage:
    C:\\Python310\\python.exe Backend/scripts/build_spell_rider_worklist.py [--out DIR] [--batch-size 30]
    C:\\Python310\\python.exe Backend/scripts/build_spell_rider_worklist.py --only "Unlock Flesh,Fireball" --out DIR
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_spell_conditionals import _save_block   # {type, dc:'', description, harmless} | None

REPO = Path(__file__).resolve().parents[2]
RIDERS = REPO / "Backend" / "json" / "spells" / "spell_riders.json"
CSV = REPO / "data" / "spells.csv"
# The applier only adds a damage MODIFIER for a touch spell when the spell has damage dice in this
# slim index (built from the compendium). A touch spell absent from it (ability-damage/penalty spells
# like Ray of Enfeeblement, Chill Touch) gets NO modifier, so its damage MUST stay in the rider text.
DAMAGE_INDEX = Path(
    r"C:\Users\Daniel\Documents\GitHub\pf1-conditional-applier\data\spell_damage_index.json")

# "functions/works like <spell>, except…" -> pull the referenced base spell's full text.
_REF_RE = re.compile(
    r'(?:works?|functions?|acts?)\s+(?:just\s+)?(?:like|as)\s+(?:the\s+)?([A-Za-z][A-Za-z ,\'-]+?)'
    r'(?:\s+spell)?(?:,|\.|;|\s+except|\s+but)', re.IGNORECASE)


def _load_csv():
    df = pd.read_csv(CSV, sep="|", on_bad_lines="skip", dtype=str, keep_default_na=False)
    return {str(r["name"]).lower(): r for _, r in df.iterrows()}


# The CSV mixes full and abbreviated save words ("Fort negates" vs "Fortitude negates"); _save_block
# only matches full words, so expand the abbreviations first for an accurate csv_save hint.
def _csv_save(saving_throw):
    s = re.sub(r'\bFort\b', 'Fortitude', saving_throw, flags=re.IGNORECASE)
    s = re.sub(r'\bRefl?\b', 'Reflex', s, flags=re.IGNORECASE)
    return _save_block(s)


def _base_ref(description, csv):
    """For a thin 'works like <X>' description, return the referenced base spell's description."""
    if len(description) >= 120:
        return None
    m = _REF_RE.search(description)
    if not m:
        return None
    ref = csv.get(m.group(1).strip().lower())
    if ref is None:
        return None
    return f"{m.group(1).strip()}: {str(ref['description'])}"


def build_records():
    riders = json.loads(RIDERS.read_text(encoding="utf-8"))
    csv = _load_csv()
    dmg_index = set()
    if DAMAGE_INDEX.exists():
        dmg_index = {k.lower() for k in json.loads(DAMAGE_INDEX.read_text(encoding="utf-8"))}
    records = []
    for name, entry in riders.items():
        row = csv.get(name.lower())
        desc = str(row["description"]) if row is not None else ""
        rec = {
            "name": name,
            "spell_level": str(row["spell_level"]) if row is not None else "",
            "range": str(row["range"]) if row is not None else "",
            "saving_throw": str(row["saving_throw"]) if row is not None else "",
            "spell_resistance": str(row["spell_resistence"]) if row is not None else "",
            "duration": str(row["duration"]) if row is not None else "",
            "targets": str(row["targets"]) if row is not None else "",
            "description": desc,
            "current_rider": "; ".join(entry.get("riders") or []),
            "current_save": entry.get("save"),
            "csv_save": _csv_save(str(row["saving_throw"])) if row is not None else None,
            # True only when the applier will actually add a damage modifier (touch spell WITH dice in
            # the index); ability-penalty touch spells get no modifier, so keep has_modifier_damage
            # False for them and let the agent restate the effect.
            "has_modifier_damage": entry.get("attack") is not None and name.lower() in dmg_index,
        }
        ref = _base_ref(desc, csv) if row is not None else None
        if ref:
            rec["base_ref_description"] = ref
        records.append(rec)
    return records


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True, help="directory for batch_NN.json files")
    ap.add_argument("--batch-size", type=int, default=30)
    ap.add_argument("--only", type=str, default=None,
                    help="comma-separated spell names -> a single pilot batch (batch_pilot.json)")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    records = build_records()

    if args.only:
        want = [n.strip().lower() for n in args.only.split(",")]
        picked = [r for r in records if r["name"].lower() in want]
        missing = set(want) - {r["name"].lower() for r in picked}
        (args.out / "batch_pilot.json").write_text(
            json.dumps({"batch": "pilot", "spells": picked}, indent=2, ensure_ascii=False),
            encoding="utf-8")
        print(f"pilot batch: {len(picked)} spells -> {args.out / 'batch_pilot.json'}")
        if missing:
            print(f"  WARNING not found in spell_riders.json: {sorted(missing)}")
        return

    n = args.batch_size
    batches = [records[i:i + n] for i in range(0, len(records), n)]
    for i, b in enumerate(batches):
        (args.out / f"batch_{i:02d}.json").write_text(
            json.dumps({"batch": i, "spells": b}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(batches)} batch file(s) ({len(records)} spells, ~{n}/batch) -> {args.out}")


if __name__ == "__main__":
    main()
