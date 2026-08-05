"""Merge the twelve psionic classes into the generator's own data files.

The scrape (Backend/json/class_data/psionics/) is the master resource and stays in the shape the
wiki gave it. This script is the seam that turns it into the two shapes the *generator* reads:

  1. Backend/json/class_data.json   -- one canonical entry per class. Once a class has an entry
     here plus a data.good_saves row, it is in the random pool automatically
     (utils/util.py::_available_class_pool) and BAB/saves derive generically in
     class_func/level_and_bab.py. Nothing else has to know psionics exists.
  2. Backend/json/class_data/<class>.json -- the per-class option lists, in the
     {section: {name: description}} shape generic_class_option_chooser already consumes
     (see sorcerer.json / oracle.json). Ticket 08: no new chooser module is written.

Modelled on build_pow_class_data.py, which did the same job for Path of War.

Two things this deliberately does NOT do:
  - it does not "correct" the psychic warrior's good-Fort-only saves back to RAW's Fort+Will. That
    is a verified house divergence recorded in section 9 of docs/feature_spec_todo.md.
  - it does not touch data.caster_mod. Power points are not spells per day; the manifesting ability
    lives in each class entry as `manifesting_stat` (see below).

`manifesting_stat` sits beside the existing `main_stat` rather than in a map in data.py. The two
are genuinely different questions -- a psychic warrior manifests off Wisdom but plays off Strength,
and a soulknife manifests off nothing at all -- and the scraper already sources the answer, so a
key in the entry is one owner where a separate map would be two that can drift. This amends the
original ticket-04 decision, which was taken against data.caster_mod, not against class_data.json.

Idempotent: re-running replaces the twelve entries in place. Run from the repo root:
    .venv/Scripts/python.exe Backend/scripts/build_psionic_class_data.py
"""
from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PSIONICS = ROOT / "Backend/json/class_data/psionics"
CLASS_DATA = ROOT / "Backend/json/class_data.json"
CLASS_DIR = ROOT / "Backend/json/class_data"

# main_stat is the stat the class *plays* off, which the generator uses for stat assignment; it is
# not always the manifesting stat. Sourced from each class's own role prose and class skills:
#   aegis/soulknife/marksman  physical classes whose psionics are self-buffs
#   psychic warrior           Strength-first martial, manifests off Wisdom
#   psion/cryptic/tactician/voyager/vitalist/dread/highlord/wilder  manifester-first
MAIN_STAT = {
    "aegis": "con", "cryptic": "int", "dread": "cha", "highlord": "cha",
    "marksman": "dex", "psion": "int", "psychic warrior": "str", "soulknife": "str",
    "tactician": "int", "vitalist": "wis", "voyager": "dex", "wilder": "cha",
}

# Every psionic class is 3pp homebrew with no published starting-wealth line on its wiki page; the
# PoW merge hit the same gap and used the standard PF1 martial figure, so match it rather than
# invent a per-class number.
DEFAULT_WEALTH = "3d6 x 10 gp (average 105 gp)."

SUFFIX_RE = re.compile(r"\s*\((su|ex|sp|ps)\)\s*$", re.IGNORECASE)


def load(name: str):
    return json.loads((PSIONICS / name).read_text(encoding="utf-8"))


def build_entry(name: str, src: dict) -> OrderedDict:
    derived = src["derived"]
    out = OrderedDict()
    out["main_stat"] = MAIN_STAT[name]
    out["bab"] = derived["bab"]
    # Psionics is not spellcasting: no class here has a caster level, and giving one would put the
    # class into the spellbook pipeline (class_func/spells.py) that psionics deliberately bypasses.
    out["casting level"] = "none"
    out["manifesting_stat"] = derived.get("manifesting ability", "")
    out["role"] = src.get("role", "")
    out["alignment"] = src.get("alignment") or "Any."
    out["hit die"] = derived["hit die"]
    out["starting wealth"] = src.get("starting wealth") or DEFAULT_WEALTH
    out["skill points at each level"] = derived["skill points at each level"]
    out["weapon and armor proficiency"] = src.get("weapon and armor proficiency", "")
    # Feature keys must come AFTER 'weapon and armor proficiency' -- get_class_abilities slices
    # the entry there, so a feature placed above it is invisible to the generator.
    for key, value in src.get("features", {}).items():
        out[SUFFIX_RE.sub("", key).lower().strip()] = value
    return out


def main() -> int:
    classes = load("psionic_classes.json")
    options = load("psionic_class_options.json")

    target = json.loads(CLASS_DATA.read_text(encoding="utf-8"),
                        object_pairs_hook=OrderedDict)
    for name in sorted(classes):
        if name not in MAIN_STAT:
            raise SystemExit(f"{name!r} has no main_stat -- add it to MAIN_STAT")
        entry = build_entry(name, classes[name])
        target[name] = entry
        features = list(entry)[10:]
        print(f"  {name:16} bab={entry['bab']} hd={entry['hit die']:5} "
              f"skills={entry['skill points at each level']} "
              f"manifests={entry['manifesting_stat'] or '-':4} features={len(features)}")
    CLASS_DATA.write_text(json.dumps(target, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {CLASS_DATA.relative_to(ROOT)} ({len(classes)} psionic entries)")

    for name, sections in sorted(options.items()):
        path = CLASS_DIR / f"{name}.json"
        path.write_text(json.dumps(sections, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        counts = ", ".join(f"{k} {len(v)}" for k, v in sections.items())
        print(f"  wrote {path.relative_to(ROOT)} ({counts})")

    print("\nnow check Backend/utils/data.py carries a good_saves row for each of the twelve, "
          "then run Backend/scripts/tests/test_house_invariants.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
