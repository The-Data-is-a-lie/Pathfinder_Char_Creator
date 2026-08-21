"""Gate the identity and gear fields the resolver puts on a bonded-creature entry.

    C:\\Python310\\python.exe Backend/scripts/gates/validate_companion_identity.py
    C:\\Python310\\python.exe Backend/scripts/gates/validate_companion_identity.py --runs 500

Map #18, slice E (#37 grill, 2026-08-03). The grill settled seven things about what a bonded creature
is called and what it owns; six of them are shape, and shape rots silently. `bonded_creatures` is not
in the payload until #32, so neither the goldens nor `test_house_invariants.py` can see these fields
yet -- without this script the rules would exist only as sentences, which is exactly the failure the
docs doctrine names.

What it asserts:

- A creature that EXISTS has a `name` (from its master's region pool) and a `sex`, owns `gear: []`,
  and carries `GEAR_SOURCE_V1` -- imported, never restated, so the note has one owner.
- An ABSENCE entry (`species: None`) carries `name: None`, `sex: None` and NO gear key at all. A
  uniform key set with nulls would ship a null-named, empty-geared ghost that renderers draw.
- `species` is untouched and still resolves in `animal_choices.json`. It is the SOLE `pf-content`
  match key (D3/D4): if a name ever leaked into it, every named companion would miss its clone.
- The name is drawn from the master's region and sex pools, and avoids the master's own first name.

AND THAT BOTH BRANCHES WERE ACTUALLY REACHED. The sample fails if it never produced a granted entry
or never produced an absence one -- the #30 stack review's lesson, where "both=0, neither=0 over 400
generations" was measured by a sample that could not reach the broken path and so reported zero
forever.
"""
import argparse
import json
import random
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent

sys.path.insert(0, str(HERE.parent))
from _harness import REPO, Report                                       # noqa: E402

ROOT = REPO
# One owner for the posture: the resolver declares the constants, this file only checks them.
from utils.class_func.animal_companions import (                  # noqa: E402
    GEAR_SOURCE_V1, SEXES, resolve_bonded_creatures)
from utils.util import first_name_for                             # noqa: E402

GRANTORS = ROOT / "Backend/json/companion_grantors.json"
SPECIES = ROOT / "Backend/json/animal_choices.json"
CHASSIS = ROOT / "Backend/json/animal_companion.json"
NAMES = ROOT / "Backend/json/first_names_regions.json"

# A druid is the sample because its bond is a CHOICE: one class reaches both a granted creature and
# an absence entry, which is what makes the branch-coverage assertion below satisfiable.
SAMPLE_CLASS = "druid"
SAMPLE_LEVEL = 7

errors = []
REPORT = Report('validate_companion_identity', errors=errors)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    REPORT.error(message)


def make_character(data, region, first_name):
    """The narrow slice of a character the resolver actually reads."""
    return SimpleNamespace(
        classes=[{"name": SAMPLE_CLASS, "level": SAMPLE_LEVEL}],
        region=region,
        f_name=first_name,
        chosen_gender="Male",
        first_names_regions=data["names"],
        animal_choices=data["species"],
        animal_companion=data["chassis"],
        companion_grantors=data["grantors"],
    )


def check_entry(entry, character):
    """Every rule that holds for a single entry. Returns 'granted' or 'absent'."""
    label = f"{entry.get('grantor')}/{entry.get('type')}"

    if not entry.get("species"):
        for field in ("name", "sex"):
            if entry.get(field) is not None:
                fail(f"{label}: absence entry has {field}={entry[field]!r}; must be None")
        for field in ("gear", "gear_source"):
            if field in entry:
                fail(f"{label}: absence entry carries a {field!r} key; it must not have one")
        return "absent"

    if entry.get("sex") not in SEXES:
        fail(f"{label}: sex={entry.get('sex')!r} is not one of {SEXES}")
    if not entry.get("name"):
        fail(f"{label}: species {entry['species']!r} has no name")
    if entry.get("name") == character.f_name:
        fail(f"{label}: named {entry['name']!r}, the same as its master")
    if entry.get("gear") != []:
        fail(f"{label}: gear={entry.get('gear')!r}; v1 owns nothing, so it must be []")
    if entry.get("gear_source") != GEAR_SOURCE_V1:
        fail(f"{label}: gear_source does not match the resolver's constant")

    pool = pool_for(character, entry.get("sex"))
    if entry.get("name") and pool and entry["name"] not in pool:
        fail(f"{label}: name {entry['name']!r} is not in the {character.region}/{entry['sex']} pool")

    if not find_species(character, entry["species"]):
        fail(f"{label}: species {entry['species']!r} does not resolve in animal_choices.json; "
             "it is the sole pf-content match key and must stay a raw species name")
    return "granted"


def pool_for(character, sex):
    pools = character.first_names_regions
    folded = {str(key).casefold(): key for key in pools}
    key = folded.get(str(character.region).casefold())
    return pools.get(key, {}).get(sex) if key else None


def find_species(character, name):
    return any(name in bucket for bucket in character.animal_choices.values())


def check_unit_draws(data):
    """`first_name_for` in isolation, where the guards can be checked deterministically."""
    stub = SimpleNamespace(first_names_regions={"Ashfen": {"Male": ["Bram", "Corvin"]}})

    drawn = {first_name_for(stub, "Ashfen", "Male", exclude="Bram") for _ in range(50)}
    if drawn != {"Corvin"}:
        fail(f"first_name_for: exclude did not hold; drew {sorted(drawn)}")

    one = SimpleNamespace(first_names_regions={"Ashfen": {"Male": ["Bram"]}})
    if first_name_for(one, "Ashfen", "Male", exclude="Bram") != "Bram":
        fail("first_name_for: a one-name pool must still return that name, not None")

    if first_name_for(stub, "Nowhere", "Male") is not None:
        fail("first_name_for: an unknown region must return None, not the 'Tal-Falko' default")
    if first_name_for(stub, "Ashfen", "Neither") is not None:
        fail("first_name_for: an unknown sex must return None, not the 'Nameless' default")

    # The two regions whose data key is not title-cased ('Tal-falko', 'Kaeru no Tochi') are the ones
    # a master actually carries, so a companion of theirs must not come out nameless.
    for key in data["names"]:
        titled = SimpleNamespace(first_names_regions=data["names"])
        if first_name_for(titled, key.title(), "Female") is None:
            fail(f"first_name_for: region {key.title()!r} (data key {key!r}) drew no name")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=300, help="resolver samples to draw")
    parser.add_argument("--seed", type=int, default=37, help="seed, so a failure reproduces")
    args = parser.parse_args()

    data = {
        "grantors": load(GRANTORS),
        "species": load(SPECIES),
        "chassis": load(CHASSIS),
        "names": load(NAMES),
    }
    check_unit_draws(data)

    random.seed(args.seed)
    regions = list(data["names"])
    seen = {"granted": 0, "absent": 0}
    sexes, names = set(), set()

    for index in range(args.runs):
        region = regions[index % len(regions)]
        pool = data["names"][region]["Male"]
        character = make_character(data, region.title(), pool[index % len(pool)])
        for entry in resolve_bonded_creatures(character):
            seen[check_entry(entry, character)] += 1
            if entry.get("species"):
                sexes.add(entry["sex"])
                names.add(entry["name"])

    for branch in ("granted", "absent"):
        if not seen[branch]:
            fail(f"the sample never produced a {branch} entry, so its rules were never checked -- "
                 f"raise --runs or fix the sample (a druid {SAMPLE_LEVEL} should reach both)")
    if seen["granted"] and set(sexes) != set(SEXES):
        fail(f"only {sorted(sexes)} was ever rolled over {args.runs} runs; the sex draw is stuck")
    if seen["granted"] and len(names) < 2:
        fail(f"every companion was named {sorted(names)}; the name draw is stuck")

    return REPORT.finish(
        f"{seen['granted']} granted, {seen['absent']} absence entries over {args.runs} runs "
        f"({len(names)} distinct names, sexes {sorted(sexes)}) "
        f"-- identity and gear fields hold on every entry",
        max_errors=25)


if __name__ == "__main__":
    sys.exit(main())
