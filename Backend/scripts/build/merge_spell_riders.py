"""Merge authored (verify-passed) Effect bodies back into Backend/json/spells/spell_riders.json for
the detailed-effect sweep (docs/spell_rider_detail_sweep_plan.md).

Input: one or more JSON files (or a directory of them), each either
    { "<Spell>": { "effect": "<; -joined body>", "save": {"type","result"[, "harmless"]} | null }, ... }
  or a list of { "name", "effect", "save" } objects.

For each spell it sets `entry.riders = [effect]` (consolidated to ONE rider) and, when an authored
`save` dict is given, rewrites `entry.save` (a null save is LEFT as-is, never destroying an existing
one). The Effect is brackified on write (self-heals a missed `[[ ]]`). It does NOT add Cost/Range/
Save-DC clauses — run `enrich_conditional_riders.py` afterward for those — then
`validate_spell_conditionals.py`.

    C:\\Python310\\python.exe Backend/scripts/merge_spell_riders.py --input DIR_OR_FILE [more...] [--dry-run]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import REPO   # noqa: E402
import conditional_clauses as cc

RIDERS = REPO / "Backend" / "json" / "spells" / "spell_riders.json"


def _load_authored(paths):
    """Flatten all inputs into {name: {effect, save}}."""
    out = {}
    files = []
    for p in paths:
        p = Path(p)
        files.extend(sorted(p.glob("*.json")) if p.is_dir() else [p])
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        items = data.values() if isinstance(data, dict) and "effect" not in data else data
        if isinstance(data, dict) and "effect" not in data:
            for name, rec in data.items():
                rec = dict(rec)
                rec.setdefault("name", name)
                out[rec["name"]] = rec
        else:
            for rec in items:
                if isinstance(rec, dict) and rec.get("name"):
                    out[rec["name"]] = rec
    return out


def _save_from(rec):
    s = rec.get("save")
    if not isinstance(s, dict) or str(s.get("type", "")).lower() not in ("fortitude", "reflex", "will"):
        return None
    return {"type": s["type"].lower(), "dc": "",
            "description": str(s.get("result") or "negates"),
            "harmless": bool(s.get("harmless", False))}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", nargs="+", required=True, help="authored JSON file(s) or dir(s)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    riders = json.loads(RIDERS.read_text(encoding="utf-8"))
    authored = _load_authored(args.input)
    merged = skipped = save_fixed = 0
    for name, rec in authored.items():
        entry = riders.get(name)
        if entry is None:
            print(f"  SKIP (not in spell_riders.json): {name!r}")
            skipped += 1
            continue
        effect = str(rec.get("effect") or "").strip()
        if not effect:
            print(f"  SKIP (empty effect): {name!r}")
            skipped += 1
            continue
        entry["riders"] = [cc.brackify(effect)]
        sv = _save_from(rec)
        if sv is not None:
            if entry.get("save") != sv:
                save_fixed += 1
            entry["save"] = sv
        merged += 1
    print(f"merged {merged} effect(s); save rewritten {save_fixed}; skipped {skipped}")
    if not args.dry_run:
        RIDERS.write_text(json.dumps(riders, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote -> {RIDERS}")
    else:
        print("(dry run -- no file written)")


if __name__ == "__main__":
    main()
