"""Census the gear the generator actually hands out, class by class and level by level.

    C:\\Python310\\python.exe Backend/scripts/build/report_gear_census.py
    C:\\Python310\\python.exe Backend/scripts/build/report_gear_census.py --levels 1,20 --seeds 3
    C:\\Python310\\python.exe Backend/scripts/build/report_gear_census.py --classes druid,wizard -v

WHY THIS EXISTS
---------------
The gear-legality plan asks for a census before accepting each behaviour step, and it asks for it
because of what the goldens did NOT catch. Eleven committed goldens held a wizard in Full plate, a
druid in Half-plate and a monk in armour for the life of the repo, and every one of them PASSED --
a golden pins what the code does, so a uniformly wrong band is a uniformly green diff. The thing
that makes a wrong band visible is a distribution over all 68 rollable classes, read by a person.

It is a REPORT, not a gate. It prints and it exits 0. `validate_gear_legality.py` gates the table
and `test_house_invariants.py` gates the generated characters; this exists so a human can read the
shape of a change before the goldens are re-baselined, which is the step this plan keeps insisting
on and the one a green test run cannot do for you.

The BEFORE column is the rule this replaced, recomputed from the same generated character:
`armor_type_mapping` never matched (tuple keys, string lookup), so the band was 'H' for everyone
except a low-BAB character, who got None -- and None then drew a RANDOM armor.json section, Tower
shields included.
"""
import argparse
import io
import sys
import traceback
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report, read_json, JSON_DIR                               # noqa: E402

import main_test                                                               # noqa: E402
from utils import data as game_data                                            # noqa: E402
from validate_class_roster import HOLDBACK_LISTS                               # noqa: E402

REPORT = Report('report_gear_census')

DEFAULT_LEVELS = (1, 5, 10, 20)
BAND_LABEL = {None: 'none', 'L': 'light', 'M': 'medium', 'H': 'heavy'}
SECTION_BAND = {'Light': 'L', 'Medium': 'M', 'Heavy': 'H', 'Shields': 'shield', 'Tower': 'tower'}


def rollable_classes():
    pool = set(read_json(JSON_DIR / 'class_data.json'))
    for name in HOLDBACK_LISTS:
        pool -= {x.lower() for x in getattr(game_data, name, [])}
    return sorted(pool)


def worn_band(payload, sections):
    """The band the character is ACTUALLY wearing, read off the armour it ended up in.

    Deliberately not `character.armor_type` -- which is not a payload field anyway. A census that
    reported the generator's own idea of the band would agree with the generator by construction;
    reading the item back through armor.json's sections is a second opinion, and it is the one that
    would have caught a wizard in Full plate.
    """
    name = payload.get('armor_name')
    if not name or name == 0:
        return None
    return SECTION_BAND.get(sections.get(name))


def old_band(payload, class_data):
    """What `armor_type_mapping` would have produced for this character.

    Every tuple key missed, so the answer was the `(): 'H'` default -- unless BAB was low, the one
    branch that did fire, which handed `list_selection` a None it read as "draw any section".
    """
    primary = payload.get('c_class')
    bab = (class_data.get(primary) or {}).get('bab')
    return None if bab == 'L' else 'H'


def generate(name, level, seed):
    sink = io.StringIO()
    with redirect_stdout(sink):
        return main_test.generate_random_char(
            class_choice=name, chosen_BAB='high', multi_class='N',
            userInput_race='random', userInput_region='Tal-Falko',
            alignment_input='random', userInput_gender='random',
            high_level=level, low_level=level, gold_num=10000,
            num_dice='4', num_sides='6', use_backstory_api='N',
            spheres_flag='N', seed=seed)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--levels', default=','.join(str(n) for n in DEFAULT_LEVELS))
    parser.add_argument('--seeds', type=int, default=1, help='rolls per class/level cell')
    parser.add_argument('--classes', default='', help='comma-separated subset')
    parser.add_argument('-v', '--verbose', action='store_true', help='one line per cell')
    args = parser.parse_args()

    levels = [int(n) for n in args.levels.split(',') if n.strip()]
    names = ([n.strip() for n in args.classes.split(',') if n.strip()]
             or rollable_classes())

    table = read_json(JSON_DIR / 'armor_proficiency.json').get('classes', {})
    class_data = read_json(JSON_DIR / 'class_data.json')
    armor_json = read_json(JSON_DIR / 'armor.json')
    # weapons_data.json is keyed by proficiency group (Simple/Martial/Exotic/Special); flattened
    # here because the payload only reports a weapon NAME.
    weapons = {n: entry
               for group in read_json(JSON_DIR / 'weapons_data.json').values()
               for n, entry in group.items()}
    sections = {n: section for section, entries in armor_json.items() for n in entries}
    before, after = Counter(), Counter()
    per_class, capped, unarmoured, worn = {}, [], [], Counter()
    shields, shield_eligible, shield_carried = Counter(), Counter(), Counter()
    shield_two_handed = Counter()
    illegal_shields = []
    proficiency = table

    for name in names:
        bands = set()
        for level in levels:
            for seed in range(1, args.seeds + 1):
                cell = f'{name} L{level} s{seed}'
                try:
                    payload = generate(name, level, seed * 1000 + level)
                except Exception:
                    tail = traceback.format_exc().strip().splitlines()
                    REPORT.error(f'{cell}: generation raised -- {tail[-1]}')
                    continue
                band = worn_band(payload, sections)
                bands.add(band)
                before[old_band(payload, class_data)] += 1
                after[band] += 1
                armor = payload.get('armor_name')
                if band is None:
                    unarmoured.append(cell)
                else:
                    worn[armor] += 1
                # The cap is the interesting half of D5 and the one nobody would predict: it is
                # what puts a magus in leather and a wizard/fighter in nothing at all.
                expected = (table.get(name) or {}).get('armor')
                if band != expected:
                    capped.append(f'{cell}: table says {BAND_LABEL[expected]}, wore '
                                  f'{BAND_LABEL[band]}')
                # Shields (D6/D9). The RATE is the number that has to be read rather than
                # asserted: a gate can only say "more than zero", and the difference between 20%
                # of the proficient and 20% of everybody is invisible to it.
                shield_band = (proficiency.get(name) or {}).get('shield')
                # The payload carries the weapon's NAME, not its category, so the category is
                # looked back up in weapons_data.json. Needed for the denominator: D6's "~20%"
                # is 20% of the proficient characters who are not holding a bow, and measuring it
                # against every proficient character understates it by more than half.
                category = str((weapons.get(payload.get('weapon_name')) or {}).get('category') or '')
                ranged = 'Ranged' in category
                two_handed = 'Two-Handed' in category
                eligible = shield_band is not None
                if eligible and not ranged:
                    shield_eligible[name] += 1
                    if two_handed:
                        shield_two_handed[name] += 1
                shield = payload.get('shield_name')
                has_shield = bool(shield) and shield != ' '
                if has_shield:
                    shields[shield] += 1
                    shield_carried[name] += 1
                    if not eligible:
                        illegal_shields.append(f'{cell}: {shield} with no shield proficiency')
                    elif shield_band == 'buckler' and 'uckler' not in shield:
                        illegal_shields.append(f'{cell}: {shield} on a buckler-only class')
                    elif shield == 'Tower' and shield_band != 'tower':
                        illegal_shields.append(f'{cell}: Tower without tower proficiency')
                if args.verbose:
                    print(f'  {cell:<34} {BAND_LABEL[band]:<7} {str(armor):<24} '
                          f'{shield if has_shield else "-"}')
        per_class[name] = bands

    print(f'\n{len(names)} classes x {len(levels)} level(s) x {args.seeds} seed(s) = '
          f'{sum(after.values())} characters\n')
    print('band distribution')
    print(f'  {"band":<8} {"before":>8} {"after":>8}')
    for band in (None, 'L', 'M', 'H'):
        print(f'  {BAND_LABEL[band]:<8} {before[band]:>8} {after[band]:>8}')

    print(f'\nclasses whose band varies by level or seed: '
          f'{sorted(n for n, b in per_class.items() if len(b) > 1) or "none"}')
    print(f'unarmoured cells: {len(unarmoured)}')
    if capped:
        print(f'\ncells whose band differs from the class table (the D5 cap, or a taboo '
              f'walk-down) -- {len(capped)}:')
        for line in capped[:20]:
            print(f'  {line}')
        if len(capped) > 20:
            print(f'  ... and {len(capped) - 20} more')

    print(f'\nmost-worn armours: {", ".join(f"{n} x{c}" for n, c in worn.most_common(10))}')

    eligible_cells = sum(shield_eligible.values())
    carried = sum(shield_carried.values())
    total = sum(after.values())
    print(f'\nshields')
    two_h = sum(shield_two_handed.values())
    print(f'  shield-proficient and not ranged: {eligible_cells}/{total}'
          f'  (of which two-handed: {two_h})')
    print(f'  carrying a shield:       {carried}'
          f'{f" ({100.0 * carried / eligible_cells:.1f}% of the proficient)" if eligible_cells else ""}')
    print(f'  distribution: {", ".join(f"{n} x{c}" for n, c in shields.most_common()) or "none"}')
    if illegal_shields:
        print(f'  ILLEGAL -- {len(illegal_shields)}:')
        for line in illegal_shields[:15]:
            print(f'    {line}')
    unarmed_shield = sorted(n for n in shield_carried if not shield_eligible.get(n))
    if unarmed_shield:
        print(f'  classes carrying shields without proficiency: {unarmed_shield}')
    REPORT.finish(f'{sum(after.values())} characters censused')
    return 0


if __name__ == '__main__':
    sys.exit(main())
