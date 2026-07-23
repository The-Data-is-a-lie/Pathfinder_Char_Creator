"""Validate + merge AUTHORED conditional drafts into the curated files (manual tool).

The curation sweep (build_conditional_candidates.py -> agents) writes one draft per worklist file to
Backend/scripts/_conditional_candidates/authored/<tier>/<name>.json:

    {"section": "rage_powers", "tier": "A", "entries": [
        {"key": "smasher", "sections": ["rage_powers"],
         "conditional": {"name": "Smasher: ...", "default": false, "tier": "A", "modifiers": []}},
        {"key": "animal fury", "skip": "grants a bite attack, not a toggle"}]}

This promotes them, mirroring promote_talent_conditionals.py:

    feats          -> Backend/json/feats/feat_conditionals.json           {Name: {name, default, modifiers, tier}}
    class features -> class_data/effects/class_feature_effects_overrides.json
                      {section: {power_key: {"conditionals": [...]}}}, then re-run
                      build_class_feature_changes.py to regenerate class_feature_effects.json

Gates (a rejected entry is reported and dropped, never silently written):
  * structural: reuses validate_quality_effects.check_conditional -- known keys, bracket balance,
    plain modifier formulas (no [label]/[[ ]]), valid target/subTarget/critical, tier in {A,B};
  * no payload: a cost-only rider with no modifiers (validate_talent_conditionals.is_cost_only);
  * CURATION WINS: an entry that already has conditionals -- in the curated file, in the overrides,
    or (for class features) in the generated effects file -- is never overwritten.
A power shared across pools fans out to every section in its `sections` list, which is what the
curated data already looks like for e.g. `bleeding attack`.

Usage:
    C:\\Python310\\python.exe Backend/scripts/promote_conditional_candidates.py [--dry-run]
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_quality_effects as vqe                      # noqa: E402  structural gate
import conditional_clauses as cc                            # noqa: E402  brackify (house number style)
from validate_talent_conditionals import is_cost_only       # noqa: E402  payload gate

REPO = Path(__file__).resolve().parents[2]
DRAFTS = REPO / "Backend" / "scripts" / "_conditional_candidates" / "authored"
FEATS_OUT = REPO / "Backend" / "json" / "feats" / "feat_conditionals.json"
CF_OUT = REPO / "Backend" / "json" / "class_data" / "effects" / "class_feature_effects_overrides.json"
CF_GENERATED = REPO / "Backend" / "json" / "class_data" / "effects" / "class_feature_effects.json"


def load(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


# A pool key is a power NAME. A few entries in the scraped class_data pools are corrupt — a sentence
# fragment, or two revelations mashed together ("should the bridge be attacked, treat it as a wall of
# force spray of shooting stars") — and a conditional keyed to one would render as nonsense on the
# roll card. Reject them here and report, so the fix happens upstream in the pool JSON.
PROSE_KEY = re.compile(r'\b(?:should|treat it as|the wearer|when the|you can)\b', re.IGNORECASE)


def bad_key(key):
    if len(key) > 45:
        return f"key looks like prose, not a power name ({len(key)} chars)"
    if PROSE_KEY.search(key):
        return "key contains sentence text — corrupt entry in the source pool"
    return None


def check(owner, cond):
    """[] when the conditional passes every gate, else the reasons."""
    vqe.errors.clear()
    vqe.check_conditional(owner, cond)
    problems = list(vqe.errors)
    vqe.errors.clear()
    if is_cost_only({"rider": cond.get("name", ""), "modifiers": cond.get("modifiers")}):
        problems.append(f"{owner}: no payload — cost/contingency only, nothing happens on the roll")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report the merge plan, write nothing")
    ap.add_argument("--drafts", type=Path, default=DRAFTS)
    args = ap.parse_args()

    files = sorted(Path(args.drafts).rglob("*.json"))
    if not files:
        raise SystemExit(f"no authored drafts under {args.drafts}")

    feats = load(FEATS_OUT, {})
    feats_lc = {k.lower() for k in feats}
    overrides = load(CF_OUT, {})
    generated = load(CF_GENERATED, {})

    added_feats, added_cf, skipped, rejected, held = 0, 0, 0, [], []
    for path in files:
        draft = load(path, None)
        if not isinstance(draft, dict) or not isinstance(draft.get("entries"), list):
            rejected.append(f"{path.name}: not a draft file (no entries[])")
            continue
        section = draft.get("section")
        for entry in draft["entries"]:
            key = str(entry.get("key", "")).strip()
            if not key:
                rejected.append(f"{path.name}: entry with no key")
                continue
            if entry.get("skip"):
                skipped += 1
                continue
            cond = entry.get("conditional")
            if not isinstance(cond, dict):
                rejected.append(f"{path.name}/{key}: no conditional and no skip")
                continue
            why = bad_key(key)
            if why:
                rejected.append(f"{path.name}/{key[:60]}…: {why}")
                continue
            # House style wants EVERY number in the rider inside [[ ]] so the roll card renders it as
            # a clickable inline roll. Agents miss some ("Range: 15-foot cone", "Cost: 1 of ..."), so
            # normalise here with the shared helper rather than hand-editing: it protects existing
            # [[ ]] spans and skips digits glued to a word (1st, the 4 in 2d4).
            if isinstance(cond.get("name"), str):
                cond["name"] = cc.brackify(cond["name"])
            problems = check(f"{path.name}/{key}", cond)
            if problems:
                rejected.extend(problems)
                continue

            if section == "feats":
                if key.lower() in feats_lc:
                    held.append(f"feats/{key}: already curated")
                    continue
                feats[key] = {"name": cond["name"], "default": bool(cond.get("default")),
                              "modifiers": cond.get("modifiers", []), "tier": cond.get("tier", "A")}
                feats_lc.add(key.lower())
                added_feats += 1
            else:
                for sec in (entry.get("sections") or [section]):
                    gen = ((generated.get(sec) or {}).get(key) or {})
                    if gen.get("conditionals"):
                        held.append(f"{sec}/{key}: already curated")
                        continue
                    slot = overrides.setdefault(sec, {}).setdefault(key, {})
                    if slot.get("conditionals"):
                        held.append(f"{sec}/{key}: already in overrides")
                        continue
                    slot["conditionals"] = [cond]       # keeps any existing changes/contextNotes
                    added_cf += 1

    print(f"  drafts read      {len(files)}")
    print(f"  feats added      {added_feats}")
    print(f"  class feats added{added_cf:>4}  (fanned out across sections)")
    print(f"  skipped by agent {skipped}")
    print(f"  held (curated)   {len(held)}")
    print(f"  REJECTED         {len(rejected)}")
    for r in rejected[:40]:
        print(f"     ! {r}")
    if len(rejected) > 40:
        print(f"     … and {len(rejected) - 40} more")

    if args.dry_run:
        print("\n  --dry-run: nothing written")
        return
    FEATS_OUT.write_text(json.dumps(feats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CF_OUT.write_text(json.dumps(overrides, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n  wrote {FEATS_OUT.name} ({len(feats)} feats) and {CF_OUT.name}")
    print("  next: python Backend/scripts/build_class_feature_changes.py"
          "  &&  python Backend/scripts/validate_class_feature_effects.py")


if __name__ == "__main__":
    main()
