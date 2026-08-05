"""Diff every psionics name the generator will emit against the pf1-psionics module's packs.

Why this exists (docs/wayfinder/psionics/issues/10-name-reconciliation.md): the module attaches
items to a generated actor by NAME MATCH and **silently drops** anything it has never heard of.
That is the exact failure mode that already bit spell conditionals -- nothing errors, the sheet is
just quietly missing an ability. So the names are reconciled ahead of time and the answer is
committed as data, not rediscovered by hand.

Two defences, per section 9 of docs/feature_spec_todo.md; this script is the first:
  1. this script emits `psionic_name_map.json` -- for every scraped name, either the module name it
     maps to, or an explicit record that it is Metzofitz-only content;
  2. `validate_psionics_data.py` then FAILS on any scraped name the map does not account for, so a
     re-scrape that invents a name cannot reach Foundry unnoticed.

The map is a decision record, not a cache. "Unmatched" is a legitimate, expected answer -- roughly
a tenth of the powers are genuine Metzofitz-only content that no normalisation will ever recover,
and those are exactly the population the payload synthesizes through `powers_desc_dict`. What must
never happen is a name whose status nobody has decided.

Normalisation is deliberately narrow -- casefold, curly apostrophe to straight, drop a trailing
"(power)" or ability-type suffix. The packs mix apostrophe characters internally (`Artificer's
Surge` with U+2019 sits beside `Reaper's Blade` with U+0027), so apostrophes must be folded; but
anything more aggressive starts inventing matches that the module will not actually make.

Foundry must not be running: LevelDB is single-writer and an open Foundry holds the pack lock.

    .venv/Scripts/python.exe Backend/scripts/reconcile_psionics_names.py
    .venv/Scripts/python.exe Backend/scripts/reconcile_psionics_names.py --module-root <dir>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BUILD, REPO as ROOT   # noqa: E402
DATA = ROOT / "Backend/json/class_data/psionics"
DUMPER = BUILD / "dump_foundry_pack.mjs"
OUT_NAME = "psionic_name_map.json"

# Default install location. Overridable because the module lives outside this repo, and CI/other
# machines will not have it -- see main() for the no-module fallback.
DEFAULT_MODULE_ROOT = (Path(os.environ.get("LOCALAPPDATA", "")) /
                       "FoundryVTT/Data/modules/pf1-psionics")
PACKS = ("classes", "powers", "races", "feats")

# Where to hunt for an installed classic-level, in order. This repo is Python and has no
# node_modules; the npx cache is where a previous `npx` run left a copy.
CLASSIC_LEVEL_GLOBS = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "npm-cache/_npx/*/node_modules/classic-level",
    ROOT / "node_modules/classic-level",
    Path.home() / "Documents/GitHub/pf1-conditional-applier/node_modules/classic-level",
)

TYPE_SUFFIX_RE = re.compile(r"\s*\((?:su|ex|sp|ps|power|psionic)\)\s*$", re.I)


def normalise(name: str) -> str:
    """Casefold, straighten apostrophes, drop a trailing (Su)/(Ex)/(power) marker."""
    name = (name or "").replace("’", "'").replace("‘", "'")
    name = name.replace(" ", " ")
    name = TYPE_SUFFIX_RE.sub("", name)
    return re.sub(r"\s+", " ", name).strip().casefold()


def find_classic_level(override: str | None) -> Path:
    if override:
        path = Path(override)
        if not (path / "index.js").exists():
            sys.exit(f"--classic-level {path} has no index.js")
        return path
    for pattern in CLASSIC_LEVEL_GLOBS:
        if "*" in str(pattern):
            matches = sorted(Path(pattern.anchor).glob(str(pattern.relative_to(pattern.anchor))))
        else:
            matches = [pattern] if pattern.exists() else []
        for match in matches:
            if (match / "index.js").exists():
                return match
    sys.exit("no classic-level found -- pass --classic-level <dir>, or run "
             "`npx classic-level` once to seed the npx cache")


def dump_packs(module_root: Path, classic_level: Path) -> dict:
    packs = [module_root / "packs" / name for name in PACKS]
    missing = [p for p in packs if not p.exists()]
    if missing:
        sys.exit(f"missing packs under {module_root}: {[p.name for p in missing]}")
    command = ["node", str(DUMPER), "--classic-level", str(classic_level),
               *[str(p) for p in packs]]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"pack dump failed:\n{result.stderr.strip()}")
    return json.loads(result.stdout)


def load(name: str):
    path = DATA / name
    if not path.exists():
        sys.exit(f"{name} is missing -- run Backend/scripts/scrape_psionics.py")
    return json.loads(path.read_text(encoding="utf-8"))


def scraped_names() -> dict[str, list[str]]:
    """Every name the generator can emit, grouped by the category it will be attached as."""
    classes = load("psionic_classes.json")
    powers = load("psionic_powers.json")
    options = load("psionic_class_options.json")

    features: list[str] = []
    for entry in classes.values():
        features.extend(entry.get("features", {}))
    option_names: list[str] = []
    for sections in options.values():
        for names in sections.values():
            option_names.extend(names)

    # Power chains: 29 wiki pages hold more than one power variant under separate headings
    # ("Metamorphosis, Minor" / "... Major"). Only the first variant gets its own record, so the
    # rest are reported here -- whether the module ships them as separate items decides whether
    # those pages have to be split (the open half of ticket 10).
    chain_variants: list[str] = []
    for record in powers.values():
        chain_variants.extend(record.get("chain_sections", []))

    return {
        "classes": sorted(classes),
        "class_features": sorted(set(features)),
        "class_options": sorted(set(option_names)),
        "powers": sorted(powers),
        "chain_variants": sorted(set(chain_variants)),
    }


def module_index(dump: dict) -> tuple[dict[str, str], dict[str, int]]:
    """normalised module name -> the module's own spelling, plus per-pack item counts."""
    index: dict[str, str] = {}
    counts: dict[str, int] = {}
    for pack, items in dump.items():
        documents = [i for i in items if i["key"].startswith("!items!")]
        counts[pack] = len(documents)
        for item in documents:
            key = normalise(item["name"])
            if key:
                index.setdefault(key, item["name"])
    return index, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--module-root", default=str(DEFAULT_MODULE_ROOT),
                        help="the pf1-psionics module directory")
    parser.add_argument("--classic-level", default=None,
                        help="directory of an installed classic-level package")
    args = parser.parse_args()

    module_root = Path(args.module_root)
    if not module_root.exists():
        sys.exit(f"pf1-psionics not found at {module_root}\n"
                 f"Pass --module-root, or install the module. This script needs the real packs; "
                 f"it deliberately does not guess.")

    classic_level = find_classic_level(args.classic_level)
    print(f"module:        {module_root}")
    print(f"classic-level: {classic_level}")

    dump = dump_packs(module_root, classic_level)
    index, counts = module_index(dump)
    print("packs: " + ", ".join(f"{pack} {n}" for pack, n in sorted(counts.items())))
    print(f"{len(index)} distinct normalised module names\n")

    scraped = scraped_names()
    matched: dict[str, dict[str, str]] = {}
    unmatched: dict[str, list[str]] = {}
    for category, names in scraped.items():
        hits, misses = {}, []
        for name in names:
            module_name = index.get(normalise(name))
            if module_name is None:
                misses.append(name)
            else:
                hits[name] = module_name
        matched[category] = hits
        unmatched[category] = misses
        total = len(names)
        print(f"  {category:15} {len(hits):4}/{total:<4} matched, {len(misses)} Metzofitz-only")

    payload = {
        "_comment": ("Generated by Backend/scripts/reconcile_psionics_names.py -- do not hand-edit. "
                     "'matched' maps a scraped name to the pf1-psionics name to emit; "
                     "'metzofitz_only' names have no module item and are synthesized into the "
                     "payload's description dicts instead. validate_psionics_data.py fails on any "
                     "scraped name absent from both."),
        "module": {"root": str(module_root), "pack_item_counts": counts},
        "matched": matched,
        "metzofitz_only": unmatched,
    }
    path = DATA / OUT_NAME
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote {path.relative_to(ROOT)}")

    # The open half of ticket 10: if the module ships chain variants as their own items, the 29
    # multi-variant wiki pages have to be split before the power diff above means anything.
    variants = scraped["chain_variants"]
    hits = len(matched["chain_variants"])
    print(f"\nchain variants: {hits} of {len(variants)} exist as separate module items "
          f"-- {'SPLIT the multi-variant pages' if hits else 'no split needed'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
