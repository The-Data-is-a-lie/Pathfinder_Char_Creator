"""Gate the four places a class declares that it casts, which have to agree or it casts nothing.

    C:\\Python310\\python.exe Backend/scripts/validate_caster_data.py
    C:\\Python310\\python.exe Backend/scripts/validate_caster_data.py --print

WHY. A caster is declared in four files and no two of them know about each other:

    class_data.json   "casting level"      the tier -- caster_formula branches on it
    data.py           base_classes         the gate -- spells.py returns [] for anything absent
    data.py           caster_mod           the bonus-spell stat, and the payload's casting_stat
    spells_per_day.json  <class name>      the table -- indexed by the class's OWN name

Miss one and the failure is silent in the worst direction: a class declared `mid` but absent from
base_classes prints "Not a base class" and ships a caster with an empty spellbook; a class in
base_classes with no spells_per_day row raises KeyError deep in generation, on the seeds that
happen to roll it. Neither shows up until someone rolls that class.

Two more checks with the same shape -- something that looks like a rule but does nothing:

  * a class in TWO caster_mod buckets. Both readers test int, then wis, then cha and stop at the
    first hit, so the second listing never fires. The shaman was in wis and cha.
  * the alias. class_for_spells_attr points a class with no data/spells.csv column of its own at
    another class's column (warpriest -> cleric, omdura -> cleric, vampire hunter -> inquisitor).
    A typo there resolves to no column and the class picks from nothing.

Per CLAUDE.md: a hard convention belongs in a validator, not a sentence. This is the convention
that the adept, the omdura and the vampire hunter each had to be walked through by hand.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _harness import DATA_DIR, JSON_DIR, Report               # noqa: E402

from utils import data as _data                              # noqa: E402
from utils.class_func import spells as _spells               # noqa: E402

CLASS_DATA = JSON_DIR / "class_data.json"
SPELLS_PER_DAY = JSON_DIR / "spells_per_day.json"
SPELLS_CSV = DATA_DIR / "spells.csv"

REPORT = Report('validate_caster_data')

# The tiers caster_formula understands. Anything else falls through its else-branch to
# highest_spell_known = 0, which is "no spells" spelled in a way that looks like a typo.
TIERS = ("none", "low", "mid", "high")

# Classes that are IN base_classes but are not spells.csv casters. base_classes is overloaded --
# spells.py uses it as the spellbook gate, so a psychic-magic or point-based class can be listed
# there for other reasons. Each name here is a deliberate exemption from the spells_per_day check.
NOT_SPELL_LIST_CASTERS: tuple = ()


def _spell_columns() -> set:
    """The class columns of data/spells.csv -- what class_for_spells is allowed to resolve to."""
    with SPELLS_CSV.open(encoding="utf-8-sig", newline="") as handle:
        header = next(csv.reader(handle, delimiter="|"))
    return set(header)


class _Stub:
    """The minimum class_for_spells_attr reads: one entry per class, so its mapping is exercised
    rather than restated here. Restating it is exactly the drift this file exists to catch."""

    def __init__(self, names):
        self.classes = [{"name": name} for name in names]


def alias_of(names) -> dict:
    stub = _Stub(names)
    _spells.class_for_spells_attr(stub)
    return {entry["name"]: entry["class_for_spells"] for entry in stub.classes}


def check() -> list:
    class_data = json.loads(CLASS_DATA.read_text(encoding="utf-8"))
    per_day = json.loads(SPELLS_PER_DAY.read_text(encoding="utf-8"))
    columns = _spell_columns()
    base = [name.lower() for name in _data.base_classes]
    problems = []

    # 1. Every class declares a tier caster_formula knows.
    for name, entry in sorted(class_data.items()):
        tier = entry.get("casting level")
        if tier not in TIERS:
            problems.append(f"class_data.json[{name!r}] casting level is {tier!r}; "
                            f"caster_formula only branches on {TIERS}")

    casters = sorted(name for name, entry in class_data.items()
                     if entry.get("casting level") not in (None, "none"))

    # 2. A declared caster must be in base_classes, or spells.py gates its whole spellbook off.
    for name in casters:
        if name not in base:
            problems.append(f"{name!r} declares casting level "
                            f"{class_data[name]['casting level']!r} but is not in "
                            f"data.base_classes -- spells.py would give it no spellbook")

    # 3. ...and must have a spells_per_day row, indexed by its OWN name (not its alias).
    for name in casters:
        if name in NOT_SPELL_LIST_CASTERS:
            continue
        if name not in per_day:
            problems.append(f"{name!r} declares casting level "
                            f"{class_data[name]['casting level']!r} but spells_per_day.json has "
                            f"no {name!r} row -- spells_per_day_attr indexes by the class's own "
                            f"name and would raise KeyError")

    # 4. The reverse: nothing claims to be a caster in data.py that class_data.json says isn't.
    declared = {name for name in class_data}
    stat_of = {name: key for key, names in _data.caster_mod.items() for name in names}
    for name in sorted(set(_data.divine_casters) | set(stat_of)):
        where = []
        if name in _data.divine_casters:
            where.append("divine_casters")
        if name in stat_of:
            where.append("caster_mod")
        if name not in declared:
            problems.append(f"{name!r} is in data.{'/'.join(where)} but class_data.json has no "
                            f"such class")
        elif name not in base:
            problems.append(f"{name!r} is in data.{'/'.join(where)} but not in base_classes, "
                            f"which spells.py uses as the gate")

    # 5. No class sits in two caster_mod buckets. Both readers test int, then wis, then cha and
    #    stop at the first hit, so a duplicate is not an error -- it is a silent preference, and
    #    the losing entry reads like a rule that does nothing. The shaman was in wis and cha.
    for name in sorted({n for names in _data.caster_mod.values() for n in names}):
        buckets = [key for key, names in _data.caster_mod.items() if name in names]
        if len(buckets) > 1:
            first = min(buckets, key=lambda k: list(_data.caster_mod).index(k))
            problems.append(f"{name!r} is in {len(buckets)} caster_mod buckets "
                            f"({', '.join(buckets)}); both readers stop at the first match, so "
                            f"only {first} takes effect -- delete the others")

    # 6. Every alias resolves to a real spells.csv column.
    for name, alias in sorted(alias_of(casters).items()):
        if alias not in columns:
            problems.append(f"class_for_spells_attr maps {name!r} to {alias!r}, which is not a "
                            f"column in data/spells.csv")
    return problems


def print_casters() -> None:
    class_data = json.loads(CLASS_DATA.read_text(encoding="utf-8"))
    per_day = json.loads(SPELLS_PER_DAY.read_text(encoding="utf-8"))
    casters = sorted(name for name, entry in class_data.items()
                     if entry.get("casting level") not in (None, "none"))
    aliases = alias_of(casters)
    print(f"{len(casters)} declared casters\n")
    print(f"  {'class':<22} {'tier':<5} {'stat':<5} {'kind':<8} {'reads':<12} levels")
    for name in casters:
        tier = class_data[name]["casting level"]
        kind = "divine" if name in _data.divine_casters else "arcane"
        levels = len(per_day.get(name, {}))
        reads = aliases[name] if aliases[name] != name else "-- own --"
        # casting_stat_for, not a restated map -- restating it is the drift this file exists to
        # catch, and it is what resolves a class listed in more than one caster_mod bucket.
        stat = _spells.casting_stat_for(name) or "?"
        print(f"  {name:<22} {tier:<5} {stat:<5} {kind:<8} {reads:<12} {levels}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--print", action="store_true", dest="show",
                        help="print every declared caster and what it resolves to, then exit")
    args = parser.parse_args()

    if args.show:
        print_casters()
        return 0

    for problem in check():
        REPORT.error(problem)

    class_data = json.loads(CLASS_DATA.read_text(encoding="utf-8"))
    casters = [name for name, entry in class_data.items()
               if entry.get("casting level") not in (None, "none")]
    return REPORT.finish(
        f"{len(casters)} declared casters -- each has a tier caster_formula knows, a place "
        f"in base_classes, a spells_per_day row, and an alias that resolves to a real "
        f"data/spells.csv column")


if __name__ == "__main__":
    raise SystemExit(main())
