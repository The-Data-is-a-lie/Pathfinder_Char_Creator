"""Standing validator for the six Occult Adventures classes.

Exists because their option pools are HARVESTED, not authored: `build_occult_class_data.py` buckets
694 compendium Items using the pack's own `tags` where they exist and a name pattern or a phrase
from the description where they do not (docs/wayfinder/class-pool/issues/04). A heuristic like that
is exactly what CLAUDE.md says belongs in a gate rather than a comment -- a pf1 or pf-content update
that retags an item would otherwise move it into the wrong bucket, or out of every bucket, and the
only symptom would be an occultist who quietly picks one fewer implement.

Three kinds of check, in rising order of how much they would have caught:

  1. SHAPE      -- every class has its datasets, none is empty, nothing is double-shelved.
  2. WIRING     -- every data.amount schedule names a dataset that exists, the five casters are in
                   base_classes and caster_mod and the spell tables, and the kineticist is in none
                   of them. This is the check that fails if someone adds a schedule and forgets the
                   pool, or a pool and forgets the schedule.
  3. CROSS-SOURCE -- the pick schedules must produce the maximum counts the classes' own feature
                   prose states ("a maximum of seven schools at 18th level", "a maximum of 11 tricks
                   at 20th level"). The prose in class_data.json and the schedule in data.py are
                   independently authored, so agreement is real evidence rather than a restatement.

Errors fail the run (exit 1).

    C:\\Python310\\python.exe Backend/scripts/validate_occult_data.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLASS_DIR = ROOT / "Backend/json/class_data"

sys.path.insert(0, str(ROOT / "Backend"))   # so `from utils...` resolves
from utils import data as _data             # noqa: E402  (path bootstrap must run first)

# class -> the datasets build_occult_class_data.py writes. Keep in step with its BUCKETS and with
# the generic_class_option_chooser calls in main_test.py -- these three are one convention.
DATASETS = {
    "occultist": ("implements", "focus powers"),
    "kineticist": ("elemental focus", "wild talents", "infusions"),
    "medium": ("spirits",),
    "mesmerist": ("bold stare", "mesmerist tricks"),
    "psychic": ("disciplines", "phrenic amplifications"),
    "spiritualist": ("emotional focus",),
}

# The five that cast psychic magic, and the `casting level` each must carry. The kineticist is
# absent on purpose and is checked separately -- it must be a non-caster everywhere.
CASTERS = {
    "occultist": "mid", "medium": "low", "mesmerist": "mid",
    "psychic": "high", "spiritualist": "mid",
}
TOP_SPELL_LEVEL = {"occultist": 6, "medium": 4, "mesmerist": 6, "psychic": 9, "spiritualist": 6}

# Closed sets small enough to state outright. Each is a count the published class states, so a
# harvest that gains or loses one is a defect and not a matter of taste.
EXACT = {
    ("occultist", "implements"): 8,        # the eight schools of magic
    ("kineticist", "elemental focus"): 8,  # aether, air, earth, fire, void, water, wood + universal
    ("medium", "spirits"): 6,              # archmage, champion, guardian, hierophant, marshal, trickster
}

# Maximum picks the class's own feature text promises, and the level it promises them by. Read off
# the prose in class_data.json; the schedule in data.amount must independently produce the same
# number. Only the subsystems whose prose states a maximum appear here.
PROMISED_MAX = {
    ("occultist", "implements"): (7, 18),
    ("mesmerist", "mesmerist tricks"): (11, 20),
}

# A name that unambiguously belongs to one bucket must not appear in any other. This is the guard
# on the description-phrase heuristics, which over-collect if a pf1 update changes wording.
NO_CROSS_SHELVING = {
    "psychic": ((" Discipline", "disciplines"),),
    "mesmerist": (("(Stare)", "bold stare"),),
}

errors: list[str] = []
notes: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load(name: str) -> dict:
    path = CLASS_DIR / f"{name}.json"
    if not path.exists():
        fail(f"{name}: {path.relative_to(ROOT)} is missing -- run build_occult_class_data.py")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check_shape(name: str, sections: dict) -> None:
    expected = set(DATASETS[name])
    if set(sections) != expected:
        fail(f"{name}: datasets {sorted(sections)} != expected {sorted(expected)}")
        return
    for dataset, options in sections.items():
        if not options:
            fail(f"{name}/{dataset} is EMPTY -- the class would pick nothing and say nothing")
        for option, description in options.items():
            if not str(description).strip():
                fail(f"{name}/{dataset}: {option!r} has no description "
                     f"(it would render as a blank line on both sheets)")
        want = EXACT.get((name, dataset))
        if want is not None and len(options) != want:
            fail(f"{name}/{dataset}: {len(options)} options, expected exactly {want}")

    seen: dict[str, str] = {}
    for dataset, options in sections.items():
        for option in options:
            if option in seen:
                fail(f"{name}: {option!r} is shelved in BOTH {seen[option]!r} and {dataset!r}")
            seen[option] = dataset

    for marker, owner in NO_CROSS_SHELVING.get(name, ()):
        for dataset, options in sections.items():
            if dataset == owner:
                continue
            strays = [o for o in options if o.endswith(marker)]
            if strays:
                fail(f"{name}/{dataset}: {len(strays)} option(s) ending {marker!r} belong in "
                     f"{owner!r} -- e.g. {strays[:3]}")


def check_schedules(name: str, sections: dict) -> None:
    schedules = getattr(_data, "amount", {}).get(name, {})
    for dataset in schedules:
        if dataset not in sections:
            fail(f"{name}: data.amount has a schedule for {dataset!r}, which is not a dataset "
                 f"({sorted(sections)}) -- the chooser would silently pick nothing")
    for dataset, levels in schedules.items():
        if list(levels) != sorted(levels):
            fail(f"{name}/{dataset}: schedule {levels} is not ascending; the chooser stops at the "
                 f"first level above the character's, so later picks would be unreachable")
        if levels and levels[-1] > 20:
            fail(f"{name}/{dataset}: schedule reaches level {levels[-1]}, past the level cap")

    for (cls, dataset), (count, by_level) in PROMISED_MAX.items():
        if cls != name:
            continue
        levels = schedules.get(dataset)
        if levels is None:
            fail(f"{name}/{dataset}: prose promises {count} picks by {by_level}th, "
                 f"but there is no data.amount schedule at all")
            continue
        granted = sum(1 for level in levels if level <= by_level)
        if granted != count:
            fail(f"{name}/{dataset}: schedule grants {granted} picks by level {by_level}, but the "
                 f"class's own feature text promises {count}")
        if len(sections.get(dataset, {})) < count:
            fail(f"{name}/{dataset}: only {len(sections.get(dataset, {}))} options for {count} "
                 f"picks -- the character would repeat itself")


def check_wiring() -> None:
    class_data = json.loads((ROOT / "Backend/json/class_data.json").read_text(encoding="utf-8"))
    known = json.loads((ROOT / "Backend/json/spells_known.json").read_text(encoding="utf-8"))
    per_day = json.loads((ROOT / "Backend/json/spells_per_day.json").read_text(encoding="utf-8"))
    abilities = {stat: set(_data.caster_mod[f"{stat}_casters"]) for stat in ("int", "wis", "cha")}

    for name in DATASETS:
        if name not in class_data:
            fail(f"{name}: no entry in class_data.json, so it cannot enter the random pool")
        if name in _data.occult_classes:
            notes.append(f"{name} is held out of the random pool by data.occult_classes")

    for name, casting in CASTERS.items():
        if class_data.get(name, {}).get("casting level") != casting:
            fail(f"{name}: casting level is "
                 f"{class_data.get(name, {}).get('casting level')!r}, expected {casting!r}")
        if name not in _data.base_classes:
            fail(f"{name}: casts, but is not in data.base_classes -- spells.py gates the whole "
                 f"spellbook on that list, so it would roll with no spells at all")
        if not any(name in names for names in abilities.values()):
            fail(f"{name}: casts, but is in none of caster_mod's int/wis/cha lists")
        for label, table in (("spells_known", known), ("spells_per_day", per_day)):
            if name not in table:
                fail(f"{name}: no row in {label}.json")
                continue
            top = max(int(level) for level in table[name])
            if top != TOP_SPELL_LEVEL[name]:
                fail(f"{name}: {label}.json tops out at spell level {top}, "
                     f"expected {TOP_SPELL_LEVEL[name]}")

    # The kineticist must be a non-caster in every one of the four places, not three of them.
    if class_data.get("kineticist", {}).get("casting level") != "none":
        fail("kineticist: casting level should be 'none' -- burn is a Constitution-priced "
             "resource and the pf1 class Item carries no casting block")
    if "kineticist" in _data.base_classes:
        fail("kineticist: must not be in base_classes; it would be handed a spellbook")
    if any("kineticist" in names for names in abilities.values()):
        fail("kineticist: must not be in caster_mod")
    for label, table in (("spells_known", known), ("spells_per_day", per_day)):
        if "kineticist" in table:
            fail(f"kineticist: has a row in {label}.json and should not")


def main() -> int:
    for name in sorted(DATASETS):
        sections = load(name)
        if sections:
            check_shape(name, sections)
            check_schedules(name, sections)
    check_wiring()

    for note in notes:
        print(f"  note: {note}")
    if errors:
        for message in errors:
            print(f"  ERROR {message}")
        print(f"\nFAIL -- {len(errors)} error(s)")
        return 1

    total = 0
    for name in sorted(DATASETS):
        sections = load(name)
        counts = ", ".join(f"{k} {len(v)}" for k, v in sorted(sections.items()))
        total += sum(len(v) for v in sections.values())
        print(f"  {name:14} {counts}")
    print(f"\nPASS -- {total} options across {len(DATASETS)} classes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
