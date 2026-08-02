"""Gate the species names the generator emits against the `pf-content` Actors the module clones.

    C:\\Python310\\python.exe Backend/scripts/validate_companion_names.py
    C:\\Python310\\python.exe Backend/scripts/validate_companion_names.py --strict

Map #18, ticket #29. The Foundry module renders a bonded creature by cloning the `pf-content` Actor
whose name matches the species, and it attaches BY NAME. On a miss it degrades to a bare `npc` built
from the payload numbers -- legitimate by D3, but only if the miss is KNOWN. A silent one already
bit spell conditionals and psionics.

So a miss is a WARN by default and the count is printed every run; `--strict` turns misses into
failures for the day the roster is meant to be complete. What always fails is a name we cannot even
ask about: a curated `species_pool` naming a species that is not in `animal_choices.json` at all
(that is `validate_companion_archetypes.py`'s job) or a dump that has gone missing or empty.

Refresh the dump with `dump_pf_content_actors.py` -- Foundry must be closed.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DUMP = ROOT / "Backend/json/pf_content_companions.json"
SPECIES = ROOT / "Backend/json/animal_choices.json"
ALIASES = ROOT / "Backend/json/companion_species_aliases.json"

CREATURE_PACKS = ("pf-companions", "pf-familiars")
EIDOLON_PACK = "pf-eidolon-forms"

# "Bear, Grizzly" and "Grizzly Bear" are the same actor; so are "Owl, Giant" and "Giant Owl".
PUNCT_RE = re.compile(r"[^a-z0-9 ]+")

errors = []
warnings = []


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def norm(name):
    return re.sub(r"\s+", " ", PUNCT_RE.sub(" ", str(name).lower())).strip()


def variants(name):
    """Every spelling of a species this file might legitimately be written as."""
    low = str(name).strip().lower()
    out = {norm(low)}
    if "," in low:
        parts = [p.strip() for p in low.split(",")]
        out.add(norm(" ".join(reversed(parts))))
        out.add(norm(parts[0]))
    else:
        parts = low.split()
        if len(parts) == 2:
            out.add(norm(f"{parts[1]}, {parts[0]}"))
    return {v for v in out if v}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true",
                        help="treat an unmatched species as a failure, not a warning")
    args = parser.parse_args()

    if not DUMP.exists():
        print(f"{DUMP} does not exist -- run dump_pf_content_actors.py with Foundry closed")
        return 1

    dump = load(DUMP)
    species = load(SPECIES)
    alias_data = load(ALIASES) if ALIASES.exists() else {}
    aliases = {k.lower(): v.lower() for k, v in (alias_data.get("aliases") or {}).items()}

    actors = set()
    for pack in CREATURE_PACKS:
        names = dump.get(pack)
        if not names:
            errors.append(f"pf_content_companions.json: pack {pack!r} is missing or empty -- "
                          f"re-dump with Foundry closed")
            continue
        actors |= {norm(n) for n in names}

    if not dump.get(EIDOLON_PACK):
        errors.append(f"pf_content_companions.json: pack {EIDOLON_PACK!r} is missing or empty -- "
                      f"D4's degraded eidolon takes its base-form names from there")

    matched, missed = [], []
    for tier, entries in species.items():
        for name in entries:
            candidates = variants(name)
            alias = aliases.get(str(name).strip().lower())
            if alias:
                candidates |= variants(alias)
            if candidates & actors:
                matched.append(name)
            else:
                missed.append(f"{tier}/{name}")

    total = len(matched) + len(missed)
    if missed:
        message = (f"{len(missed)} of {total} species have no pf-content Actor to clone; the "
                   f"module will build a bare npc from the payload numbers (D3) and warn")
        (errors if args.strict else warnings).append(message)

    for message in warnings:
        print(f"WARN: {message}")
    if missed:
        print("      unmatched:")
        for one in missed:
            print(f"        {one}")

    if errors:
        print()
        for message in errors:
            print(message)
        print(f"FAILED: {len(errors)} problem(s)")
        return 1

    forms = len(dump.get(EIDOLON_PACK) or [])
    print(f"OK: {len(matched)} of {total} species match a pf-content Actor; "
          f"{forms} eidolon base forms available")
    return 0


if __name__ == "__main__":
    sys.exit(main())
