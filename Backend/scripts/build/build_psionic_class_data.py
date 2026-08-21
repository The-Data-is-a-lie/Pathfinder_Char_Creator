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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import REPO as ROOT   # noqa: E402
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


# The psion's seven disciplines, DERIVED rather than harvested (class-choices ticket 02).
#
# The psion was the one psionic class with no entry in psionic_class_options.json, so it reached
# 20th level with 39 powers and no discipline -- which is not cosmetic, because the discipline is
# what decides which powers are legal. The scrape never carried the list, and neither does the
# pf1-psionics compendium: it has a single `Discipline` feature item and no options behind it.
#
# But psionic_powers.json tags all 660 powers with their discipline, so the roster is already here.
# Deriving it from that file rather than authoring it means the discipline a psion picks and the
# powers that pick is supposed to gate can never disagree -- they are read from one source.
#
# Sub-disciplines and descriptors are stripped: the data carries "Metacreativity (Creation)" and
# "Telepathy [Mind-Affecting]", which are the same seven disciplines with extra tagging.
# The ROSTER comes from the class's own prose, which names all seven in one sentence; the COUNTS
# come from the powers. Deriving the roster from the powers' own tags was tried first and produced
# 22, because that field carries case variants, alternatives ("Psychokinesis or clairsentience"),
# comma lists, and a stray `telekinesis` -- a set union over dirty tags is not a roster. Taking the
# roster from the prose and matching the tags against it keeps both halves honest: an unmatched tag
# is invisible, but a discipline the prose names and no power carries is a hard failure below.
DISCIPLINE_SENTENCE = re.compile(r"seven disciplines are (.+?)\.", re.I | re.S)
DISCIPLINE_BLURB = ("{count} powers belong to this discipline. A psion who specializes in it gains "
                    "its restricted powers and its discipline abilities, and can no longer learn "
                    "powers restricted to any other discipline.")


def psion_disciplines() -> dict:
    prose = json.loads(CLASS_DATA.read_text(encoding="utf-8"))["psion"]["psionic disciplines"]
    match = DISCIPLINE_SENTENCE.search(prose)
    if not match:
        raise SystemExit("the psion's `psionic disciplines` prose no longer names the seven "
                         "disciplines -- the roster has no other source in the repo")
    roster = [part.strip().strip(".").capitalize()
              for part in re.split(r",|\band\b", match.group(1)) if part.strip()]
    if len(roster) != 7:
        raise SystemExit(f"parsed {len(roster)} disciplines from the psion's prose, expected 7: "
                         f"{roster}")

    powers = load("psionic_powers.json")
    counts = {name: 0 for name in roster}
    for power in powers.values():
        tag = (power.get("discipline") or "").lower()
        for name in roster:
            # substring, not equality: a power's tag is "Metacreativity (Creation)" or
            # "Psychometabolism or telepathy", and both genuinely belong to the discipline named.
            if name.lower() in tag:
                counts[name] += 1
    empty = sorted(n for n, c in counts.items() if not c)
    if empty:
        raise SystemExit(f"disciplines with no powers: {empty} -- the prose and "
                         f"psionic_powers.json disagree, and a psion could specialize into nothing")
    return {name: DISCIPLINE_BLURB.format(count=counts[name]) for name in sorted(roster)}


def main() -> int:
    classes = load("psionic_classes.json")
    options = load("psionic_class_options.json")
    # Merged in rather than written back into psionic_class_options.json: that file is the scrape's
    # own shape and the psion's list is not scraped, it is derived from the powers beside it.
    options["psion"] = {"disciplines": psion_disciplines()}

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
