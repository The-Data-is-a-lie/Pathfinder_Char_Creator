"""Standing validator for the scraped psionics master data.

Exists because the upstream data this replaces was silently wrong: every class in the
`pf1-psionics` Foundry module carries the same placeholder bab/hit-die/skill-points, correct only
for the psion by coincidence (docs/wayfinder/psionics/issues/02-data-quality-ogl.md). A wiki scrape
can regress the same way -- a renamed column header, a reformatted table -- so the convention lives
here rather than in a sentence in a doc.

The load-bearing check is CROSS-SOURCE: every manifesting class's power-points-per-day column must
equal one of the three progressions the Foundry module hardcodes in scripts/data/powerpoints.mjs.
Two independently-authored sources agreeing on twenty numbers is real evidence the scrape is right;
either one alone is not.

Errors fail the run (exit 1). Gaps in the source pages are reported as warnings and do not fail --
they are facts about the wiki, not defects in the scrape.

    .venv/Scripts/python.exe Backend/scripts/validate_psionics_data.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Backend/json/class_data/psionics"

sys.path.insert(0, str(ROOT / "Backend"))   # so `from utils...` resolves
from utils import data as _data             # noqa: E402  (path bootstrap must run first)

EXPECTED_CLASSES = {
    "aegis", "cryptic", "dread", "highlord", "marksman", "psion", "psychic warrior",
    "soulknife", "tactician", "vitalist", "voyager", "wilder",
}
LEVELS = 20

# Verbatim from pf1-psionics scripts/data/powerpoints.mjs (POINTS_PER_LEVEL), captured 2026-07-31.
# Hardcoded rather than fetched so this validator stays offline and deterministic; ticket 02
# verified the "high" row against the published psion table independently. It lives in data.py
# because class_func/psionics.py reads the same table to derive each manifester's `caster_type` for
# the Foundry module -- the check below is therefore also the gate on that derivation.
MODULE_PP = _data.psionic_pp_tables

# Level-20 base attack bonus -> the class_data.json 'bab' vocabulary.
BAB_AT_20 = {"H": 20, "M": 15, "L": 10}
# Level-20 base save by progression -- how a 'good saves' claim is checked against the table.
SAVE_AT_20 = {"good": 12, "poor": 6}

ERRORS: list[str] = []
WARNINGS: list[str] = []


def error(message: str) -> None:
    ERRORS.append(message)


def warn(message: str) -> None:
    WARNINGS.append(message)


def load(name: str):
    path = DATA / name
    if not path.exists():
        error(f"{name} is missing -- run Backend/scripts/scrape_psionics.py")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def first_number(value: str) -> int:
    match = re.search(r"\+?(\d+)", value or "")
    return int(match.group(1)) if match else -1


# --------------------------------------------------------------------------------------- classes

def check_classes(classes, progressions) -> None:
    if classes is None:
        return
    missing = EXPECTED_CLASSES - set(classes)
    extra = set(classes) - EXPECTED_CLASSES
    if missing:
        error(f"classes missing from psionic_classes.json: {sorted(missing)}")
    if extra:
        error(f"unexpected classes in psionic_classes.json: {sorted(extra)}")

    for name, entry in sorted(classes.items()):
        table = entry.get("table") or []
        derived = entry.get("derived") or {}

        if len(table) != LEVELS:
            error(f"{name}: {len(table)} table rows, expected {LEVELS}")
            continue

        if not re.fullmatch(r"d\d+\.", derived.get("hit die", "")):
            error(f"{name}: hit die {derived.get('hit die')!r} does not parse as 'dN.' "
                  f"(class_data.json format)")
        if not re.fullmatch(r"\d+", derived.get("skill points at each level", "")):
            error(f"{name}: skill points {derived.get('skill points at each level')!r} "
                  f"is not an integer")

        # BAB: recompute from the table rather than trusting the stored category.
        level20 = first_number(table[-1].get("bab", ""))
        category = derived.get("bab")
        if category not in BAB_AT_20:
            error(f"{name}: bab {category!r} is not one of H/M/L")
        elif BAB_AT_20[category] != level20:
            error(f"{name}: bab '{category}' implies +{BAB_AT_20[category]} at level 20 "
                  f"but the table says +{level20}")

        # Saves: the level-1 classification the scraper used must agree with the level-20 value.
        good = set(derived.get("good saves") or [])
        for save in ("fort", "ref", "will"):
            if save not in table[-1]:
                continue
            expected = "good" if save in good else "poor"
            actual = first_number(table[-1][save])
            if actual != SAVE_AT_20[expected]:
                error(f"{name}: {save} classified {expected} (+{SAVE_AT_20[expected]} at 20) "
                      f"but the table says +{actual}")

        # Level column must run 1..20 in order.
        levels = [first_number(row.get("level", "")) for row in table]
        if levels != list(range(1, LEVELS + 1)):
            error(f"{name}: level column is not 1..{LEVELS} in order")

    check_progressions(classes, progressions)


def check_progressions(classes, progressions) -> None:
    if progressions is None:
        return
    for name, entry in sorted(classes.items()):
        manifests = (entry.get("derived") or {}).get("manifests")
        if manifests and name not in progressions:
            error(f"{name}: table has a power-points column but no entry in "
                  f"psionic_powers_known.json")
        if not manifests:
            continue

        columns = progressions[name]
        pp = columns.get("pp_per_day") or []
        if len(pp) != LEVELS:
            error(f"{name}: pp_per_day has {len(pp)} entries, expected {LEVELS}")
        else:
            match = next((k for k, v in MODULE_PP.items() if v == pp), None)
            if match is None:
                error(f"{name}: pp_per_day matches none of the module's low/med/high "
                      f"progressions -- got {pp}")
            else:
                print(f"  {name:16} pp_per_day == module '{match}' progression")

        for column in ("powers_known", "max_power_level"):
            values = columns.get(column)
            if values is None:
                continue
            if len(values) != LEVELS:
                error(f"{name}: {column} has {len(values)} entries, expected {LEVELS}")
            elif any(b < a for a, b in zip(values, values[1:])):
                error(f"{name}: {column} decreases with level -- {values}")

        top = columns.get("max_power_level")
        if top and not 1 <= top[-1] <= 9:
            error(f"{name}: max_power_level tops out at {top[-1]}, expected 1-9")


# ----------------------------------------------------------------------------------- power lists

def check_powers(lists, powers) -> None:
    if lists is None or powers is None:
        return
    known = {name.lower() for name in powers}
    for record in powers.values():
        for alias in record.get("aliases", []):
            known.add(alias.lower())

    unresolved = set()
    for title, entry in sorted(lists.items()):
        buckets = {}
        if "levels" in entry:
            buckets[title] = entry["levels"]
        for discipline, block in entry.get("disciplines", {}).items():
            buckets[f"{title} / {discipline}"] = block["levels"]
        if not buckets:
            error(f"{title}: no power levels captured")
        for label, levels in buckets.items():
            if not levels:
                error(f"{label}: no power levels captured")
            for level, names in levels.items():
                if not re.fullmatch(r"\d", level):
                    error(f"{label}: level key {level!r} is not a single digit")
                for name in names:
                    if name.lower() not in known:
                        unresolved.add(name)
    if unresolved:
        warn(f"{len(unresolved)} listed powers have no wiki page (red links): "
             f"{', '.join(sorted(unresolved))}")

    for field in ("discipline", "level_by_class", "text"):
        gaps = [name for name, record in powers.items() if not record.get(field)]
        if gaps:
            error(f"{len(gaps)} powers have no {field}: {', '.join(sorted(gaps)[:10])}")
    for field in ("manifesting time", "range", "duration", "power points", "display"):
        gaps = [name for name, record in powers.items() if not record.get(field)]
        if gaps:
            warn(f"{len(gaps)} powers have no '{field}' on their wiki page: "
                 f"{', '.join(sorted(gaps))}")

    orphans = [name for name, record in powers.items() if not record.get("level_by_class")]
    print(f"  {len(powers)} powers, {len(orphans)} with no class/level line")


# ---------------------------------------------------------------------------------- class options

# Nine of the twelve carry a choice-bearing subsystem; the voyager deliberately has none (its
# Voyager Knowledge feature grants bonus feats, not options), and the psion and wilder pick powers
# rather than a subsystem. See OPTION_PAGES in scrape_psionics.py.
EXPECTED_OPTION_SECTIONS = {
    "aegis": "customizations", "cryptic": "insights", "dread": "terrors",
    "highlord": "decrees", "marksman": "combat styles", "psychic warrior": "warrior paths",
    "soulknife": "blade skills", "tactician": "strategies", "vitalist": "methods",
}


def check_options(options) -> None:
    """The option lists ticket 08 needs. A silently empty list is the failure mode that matters --
    the chooser would just never offer that class anything, with nothing raising."""
    if options is None:
        return
    missing = set(EXPECTED_OPTION_SECTIONS) - set(options)
    if missing:
        error(f"psionic_class_options.json is missing classes: {sorted(missing)}")
    for name, section in sorted(EXPECTED_OPTION_SECTIONS.items()):
        entry = (options.get(name) or {}).get(section)
        if entry is None:
            error(f"{name}: no '{section}' option list")
        elif not entry:
            error(f"{name}: '{section}' option list is empty")
        else:
            for option, description in entry.items():
                if not description or len(description) < 40:
                    error(f"{name}/{section}: option {option!r} has no usable description")
    total = sum(len(s) for e in options.values() for s in e.values())
    print(f"  {len(options)} classes carry option lists, {total} options total")


# -------------------------------------------------------------------------------------- name map

def check_name_map() -> None:
    """Every name the generator can emit must have a decided status in psionic_name_map.json.

    The pf1-psionics module attaches by name match and silently drops what it does not recognise,
    so an unrecognised name produces no error anywhere -- just an ability quietly missing from the
    sheet. This is the second of the two defences in section 9: reconcile_psionics_names.py records
    the decision, and this fails the build if a name has no decision.

    "Metzofitz-only" is a perfectly good decision -- around a tenth of the powers are homebrew the
    module has never shipped, and the payload synthesizes those through its description dicts. What
    fails here is a name nobody has classified, which is what a fresh scrape produces.
    """
    path = DATA / "psionic_name_map.json"
    if not path.exists():
        error("psionic_name_map.json is missing -- run "
              "Backend/scripts/reconcile_psionics_names.py")
        return
    name_map = json.loads(path.read_text(encoding="utf-8"))

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from reconcile_psionics_names import scraped_names          # noqa: PLC0415

    matched = name_map.get("matched", {})
    only = name_map.get("metzofitz_only", {})
    for category, names in scraped_names().items():
        decided = set(matched.get(category, {})) | set(only.get(category, []))
        undecided = sorted(set(names) - decided)
        if undecided:
            error(f"{len(undecided)} {category} name(s) absent from psionic_name_map.json -- "
                  f"re-run reconcile_psionics_names.py: {', '.join(undecided[:8])}")
    total = sum(len(v) for v in matched.values())
    print(f"  name map: {total} names matched to pf1-psionics, "
          f"{sum(len(v) for v in only.values())} Metzofitz-only")


# ----------------------------------------------------------------------------------------- races

def check_races(races) -> None:
    if races is None:
        return
    if len(races) != 10:
        error(f"psionic_races.json has {len(races)} races, expected the 10 Psionics Unleashed ones")
    for name, record in sorted(races.items()):
        if not record.get("paragraphs"):
            error(f"{name}: no page content captured")
        for field in ("ability", "size", "speed", "languages"):
            if not record.get(field):
                warn(f"race {name}: no '{field}' line found on its d20pfsrd page")


# ------------------------------------------------------------------------------------------ main

def main() -> int:
    print("validating psionics data...")
    classes = load("psionic_classes.json")
    progressions = load("psionic_powers_known.json")
    lists = load("psionic_power_lists.json")
    powers = load("psionic_powers.json")
    races = load("psionic_races.json")

    check_classes(classes, progressions)
    check_powers(lists, powers)
    check_options(load("psionic_class_options.json"))
    check_name_map()
    check_races(races)

    for message in WARNINGS:
        print(f"WARNING: {message}")
    for message in ERRORS:
        print(f"ERROR:   {message}")

    if ERRORS:
        print(f"\nFAILED -- {len(ERRORS)} error(s), {len(WARNINGS)} warning(s)")
        return 1
    print(f"\nOK -- 0 errors, {len(WARNINGS)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
