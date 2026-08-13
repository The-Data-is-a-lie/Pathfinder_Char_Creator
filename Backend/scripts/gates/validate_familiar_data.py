"""Gate on the familiar data pair -- familiar_choices.json + familiar_master_bonus.json.

    C:\\Python310\\python.exe Backend/scripts/gates/validate_familiar_data.py

Companions ticket 02's v1 ruling: familiars ship at a full stat block, numbers keyed off the
MASTER over a species body (`class_func/familiars.py`). That split makes the data pair load-bearing
in a way a bad row would hide well: a species block that fails to parse degrades the creature
silently, and a master-table row that drifts mis-states every familiar at that level.

What this asserts:
- the species pool is exactly the ten PF1e Core Rulebook base familiars, every block shaped like an
  `animal_choices.json` starting-statistics block and nothing else -- a familiar never advances on
  its own chassis, so an advancement key here means someone pasted a companion;
- every size is Tiny or smaller. `familiars.py` models the Dex-for-CMB rule on that basis
  (`DEX_CMB_SIZES`), so a Small familiar would silently get the wrong CMB, not an error;
- geometry/attack/armor lines parse through `companion_stats`' own parsers -- imported, not
  restated, so this fails when the parser and the data disagree, wherever the fault sits;
- the master table covers levels 1-20 with cumulative (never decreasing) columns, every named
  special has rules text in `ability_notes` and vice versa, and spell resistance arrives at 11
  exactly (it is computed in code as master level + 5; the table only names the gain);
- `species_perks` and the species pool name the same ten creatures, both ways.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _harness import JSON_DIR, Report, read_json                        # noqa: E402

from utils.class_func.companion_stats import (                          # noqa: E402
    SIZE_GEOMETRY, _natural_armor, _parse_attacks,
)
from utils.class_func.familiars import DEX_CMB_SIZES                    # noqa: E402

CHOICES = JSON_DIR / 'familiar_choices.json'
MASTER = JSON_DIR / 'familiar_master_bonus.json'

# The PF1e Core Rulebook base familiar list (the wizard Familiar class feature). External rules,
# so the gate states them -- the data file cannot be its own authority on completeness.
RAW_FAMILIARS = {'bat', 'cat', 'hawk', 'lizard', 'owl', 'rat', 'raven', 'toad', 'viper', 'weasel'}

STAT_KEYS = {'size', 'speed', 'ac', 'attack', 'ability scores', 'special qualities',
             'special attacks'}
ABILITIES = ('str', 'dex', 'con', 'int', 'wis', 'cha')

REPORT = Report('validate_familiar_data')


def check_species(name, block):
    keys = set(block)
    REPORT.check(keys == {'starting statistics'},
                 f"{name}: keys {sorted(keys)} -- a familiar carries ONLY 'starting statistics'; "
                 f"an advancement block means a companion entry was pasted in")
    stats = block.get('starting statistics') or {}
    REPORT.check(set(stats) <= STAT_KEYS,
                 f"{name}: unknown stat keys {sorted(set(stats) - STAT_KEYS)}")

    size = str(stats.get('size') or '').strip().lower()
    REPORT.check(size in SIZE_GEOMETRY, f"{name}: size {size!r} not in SIZE_GEOMETRY")
    REPORT.check(size in DEX_CMB_SIZES,
                 f"{name}: size {size!r} is larger than Tiny -- familiars.py assumes Dex-for-CMB "
                 f"for the whole pool")

    REPORT.check(isinstance(stats.get('speed'), str) and stats['speed'].strip(),
                 f"{name}: speed is missing or empty")
    REPORT.check(_natural_armor(stats.get('ac')) >= 0,
                 f"{name}: ac {stats.get('ac')!r} did not parse as a natural armor line")

    attack = stats.get('attack')
    if attack is not None:
        parsed = _parse_attacks(attack, 0, 0, 0, True)
        REPORT.check(parsed, f"{name}: attack {attack!r} produced no parsed attacks")

    scores = stats.get('ability scores') or {}
    REPORT.check(set(scores) == set(ABILITIES),
                 f"{name}: ability scores carry {sorted(scores)}, expected all six")
    for stat, score in scores.items():
        REPORT.check(isinstance(score, int) and 1 <= score <= 30,
                     f"{name}: {stat} = {score!r} is not an int in 1..30")


def check_master_table(table, species):
    rows = table.get('levels') or {}
    notes = table.get('ability_notes') or {}
    REPORT.check(set(rows) == {str(n) for n in range(1, 21)},
                 f"levels: keys are {sorted(rows)}, expected exactly '1'..'20'")

    named, sr_levels = [], []
    previous = (0, 0)
    for step in range(1, 21):
        row = rows.get(str(step)) or {}
        armor, intelligence = row.get('natural_armor_adj'), row.get('int_score')
        ok = REPORT.check(isinstance(armor, int) and isinstance(intelligence, int),
                          f"level {step}: natural_armor_adj/int_score must both be ints")
        if ok:
            REPORT.check((armor, intelligence) >= previous,
                         f"level {step}: ({armor}, {intelligence}) decreased from {previous} -- "
                         f"columns are CUMULATIVE values in effect, not deltas")
            previous = (armor, intelligence)
        for special in row.get('special') or []:
            named.append(special)
            REPORT.check(special in notes,
                         f"level {step}: special {special!r} has no ability_notes entry")
            if special == 'spell resistance':
                sr_levels.append(step)

    REPORT.check(sr_levels == [11],
                 f"spell resistance is gained at {sr_levels or 'no level'}, RAW says 11 exactly")
    REPORT.check(len(named) == len(set(named)),
                 f"a special ability is named at two levels: "
                 f"{sorted({n for n in named if named.count(n) > 1})}")
    orphans = set(notes) - set(named)
    REPORT.check(not orphans,
                 f"ability_notes entries never granted by any level: {sorted(orphans)}")

    perks = table.get('species_perks') or {}
    REPORT.check(set(perks) == species,
                 f"species_perks names {sorted(set(perks) ^ species)} out of step with the pool")
    for name, perk in perks.items():
        REPORT.check(isinstance(perk, str) and perk.strip(),
                     f"species_perks/{name}: empty perk")


def main():
    pool = read_json(CHOICES).get('familiar') or {}
    REPORT.check(set(pool) == RAW_FAMILIARS,
                 f"species pool is {sorted(pool)}, expected the ten Core Rulebook familiars "
                 f"(difference: {sorted(set(pool) ^ RAW_FAMILIARS)})")
    for name, block in pool.items():
        check_species(name, block or {})

    check_master_table(read_json(MASTER), set(pool))
    return REPORT.finish(f"{len(pool)} familiar species and the 20-level master table validated")


if __name__ == "__main__":
    sys.exit(main())
