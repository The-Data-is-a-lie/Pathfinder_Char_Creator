"""Validate racial_stat_changes.json against PlayableRaces.json.

Run from the repo root: python Backend/scripts/validate_racial_stats.py
Asserts every playable race has an entry, and every entry is either the
floating {"any": 2} bonus or fixed even modifiers in the -4..+4 range.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _harness import JSON_DIR, Report, read_json               # noqa: E402

STAT_KEYS = {'str', 'dex', 'con', 'int', 'wis', 'cha'}

REPORT = Report('validate_racial_stats')


def load(name):
    return read_json(JSON_DIR / name)


def main():
    races_data = load('PlayableRaces.json')
    changes = load('racial_stat_changes.json')
    changes_ci = {k.lower(): v for k, v in changes.items()}

    playable = list(races_data['Core']) + list(races_data['NonCore'])

    for race in playable:
        entry = changes_ci.get(race.lower())
        if entry is None:
            REPORT.error(f"missing entry for playable race '{race}'")
            continue
        if entry == {'any': 2}:
            continue
        for stat, val in entry.items():
            if stat not in STAT_KEYS:
                REPORT.error(f"{race}: unknown stat key '{stat}'")
            elif not (isinstance(val, int) and val % 2 == 0 and -4 <= val <= 4 and val != 0):
                REPORT.error(f"{race}: bad modifier {stat}={val!r}")

    playable_ci = {r.lower() for r in playable}
    for race in changes:
        # Lookups are case-insensitive (race_chooser title-cases input, e.g.
        # 'Monkey Goblin' vs the data file's 'Monkey goblin').
        if race.lower() not in playable_ci:
            REPORT.error(f"entry '{race}' matches no playable race")

    return REPORT.finish(f"{len(playable)} playable races all have valid racial stat entries")


if __name__ == '__main__':
    sys.exit(main())
