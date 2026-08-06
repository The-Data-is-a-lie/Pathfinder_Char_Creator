"""Per-class psionics sweep: all twelve classes x a level ladder, with a readable table.

    C:\\Python310\\python.exe Backend/scripts/tests/test_psionics_sweep.py
    C:\\Python310\\python.exe Backend/scripts/tests/test_psionics_sweep.py --classes psion,aegis
    C:\\Python310\\python.exe Backend/scripts/tests/test_psionics_sweep.py --levels 1,20 --quiet

Why this exists alongside test_house_invariants.py, which already asserts most of the same
formulas: that sweep answers "did anything break" across 50-odd classes and prints pass/fail. This
one answers "is EACH psionic class right", per class, in a table you can read. The defect that
prompted it was invisible to a pass/fail gate -- the aegis and soulknife generated their subsystem
picks correctly and put them somewhere no renderer looked, so every assertion passed and the tab was
empty. A per-class table makes "generated but invisible" visible.

Columns, one row per class x level:

  powers   -- count == the class table's powers_known at that level, all distinct, none above max
  talents  -- count == psionics.FREE_TALENTS, all level 0, named grants present (psion's
              Detect Psionics)
  max_lvl  -- == min(class table, key ability score - 10); no power exceeds it
  pp       -- == table + floor(mod x ML / 2); caster_type names the table its column matches
  subsys   -- subsystem_bucket names a class_features bucket holding the picks due at this level
  desc     -- every emitted name has a powers_desc_dict entry carrying rules text
  foundry  -- every emitted name is either matched in psionic_name_map or recorded as
              Metzofitz-only; an unmatched name is SILENTLY DROPPED by the pf1-psionics module, so
              this is how "it appears in Foundry" is tested without launching Foundry

Exit code is non-zero on any failure, and every failure names class + level + replay seed.
"""
import argparse
import io
import json
import sys
import traceback
from contextlib import redirect_stdout
from math import floor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND, Report, choice_schedule, schedule_levels  # noqa: E402

# The pick schedule, read from disk rather than through the generator's resolver.
SCHEDULE = choice_schedule()

from utils import data  # noqa: E402
from utils.class_func import backstory as _bs  # noqa: E402

# Sever Ollama the way the other gates do: build_archetype reaches for it to break scoring ties.
_bs._try_ollama = lambda *a, **k: ''

import main_test  # noqa: E402
from utils.class_func.psionics import FREE_TALENTS, MANDATED_TALENTS, SUBSYSTEM_BUCKET  # noqa: E402

LEVELS = [1, 5, 10, 20]
SEED = 4242

PSIONICS = BACKEND / 'json' / 'class_data' / 'psionics'
with open(PSIONICS / 'psionic_powers_known.json', encoding='utf-8') as f:
    TABLES = json.load(f)
with open(PSIONICS / 'psionic_power_lists.json', encoding='utf-8') as f:
    POWER_LISTS = json.load(f)
with open(PSIONICS / 'psionic_name_map.json', encoding='utf-8') as f:
    NAME_MAP = json.load(f)

CLASSES = list(getattr(data, 'psionic_class', []))
# Every name the pf1-psionics module will recognise, plus the ones we know it never will. A name in
# neither set is the silent-drop failure -- it reaches Foundry and vanishes with no error.
MODULE_KNOWS = set(NAME_MAP['matched']['powers'].values()) | set(NAME_MAP['matched']['chain_variants'].values())
METZ_ONLY = set(NAME_MAP['metzofitz_only']['powers']) | set(NAME_MAP['metzofitz_only']['chain_variants'])

# Every power's level, per power list, so a chosen power can be checked against max_power_level.
# Keyed by list name because psionic_powers.json keys levels by LIST, not by class.
LEVEL_OF = {}
for _list, _entry in POWER_LISTS.items():
    _levels = _entry.get('levels') or {}
    for _block in (_entry.get('disciplines') or {}).values():
        for _k, _v in (_block.get('levels') or {}).items():
            _levels.setdefault(_k, []).extend(_v)
    for _k, _names in _levels.items():
        if _k.isdigit():
            for _n in _names:
                LEVEL_OF.setdefault(_n, set()).add(int(_k))

REPORT = Report('test_psionics_sweep')


def fail(cell, message):
    REPORT.error(f"{cell}: {message}")


def final_score(payload, stat):
    return (payload[stat] + (payload.get('inherents') or {}).get(stat, 0)
            + (payload.get('level_up_stats') or {}).get(stat, 0))


def check_manifester(cell, payload, name, m, class_level):
    """Returns the row of column verdicts for the table; appends to FAILURES on any miss."""
    row = min(max(m['manifester_level'], 1), 20) - 1
    table = TABLES.get(name, {})
    verdict = {}

    def col(key, ok, detail):
        verdict[key] = detail if ok else f"!{detail}"
        if not ok:
            fail(cell, f"{key}: {detail}")

    # ---- subsys: the "generated but invisible" check ----
    want_bucket = SUBSYSTEM_BUCKET.get(name, '')
    picks = (payload.get('class_features') or {}).get(want_bucket) or {} if want_bucket else {}
    if want_bucket:
        schedule = schedule_levels(SCHEDULE, name, want_bucket, class_level)
        want_picks = len(schedule) if schedule is not None else 1
        col('subsys', m['subsystem_bucket'] == want_bucket and len(picks) == want_picks,
            f"{want_bucket}={len(picks)}/{want_picks}")
    else:
        col('subsys', not m['subsystem_bucket'], 'none')

    # ---- the soulknife: a mind blade is the whole of its psionics ----
    if not m['manifesting_stat']:
        blade = m['mind_blade']
        col('powers', isinstance(blade, dict) and blade.get('name') == payload.get('weapon_name'),
            f"blade={(blade or {}).get('name')!r}")
        for key in ('talents', 'max_lvl', 'pp', 'desc', 'foundry'):
            verdict[key] = '-'
        return verdict

    score = final_score(payload, m['manifesting_stat'])
    if score < 10:
        # Cannot manifest at all: the whole record legitimately reads zero.
        col('pp', not m['pp_per_day'] and not m['powers_chosen'],
            f"score {score} < 10, zeroed")
        for key in ('powers', 'talents', 'max_lvl', 'desc', 'foundry'):
            verdict.setdefault(key, '-')
        return verdict

    # ---- pp ----
    base = (table.get('pp_per_day') or [0] * 20)[row]
    want_pp = base + max(0, floor(((score - 10) // 2) * m['manifester_level'] / 2))
    want_type = next((k for k, v in data.psionic_pp_tables.items()
                      if v == table.get('pp_per_day')), '')
    col('pp', m['pp_per_day'] == want_pp and m['caster_type'] == want_type,
        f"{m['pp_per_day']}/{want_pp} {m['caster_type'] or '-'}")

    if name in {x.lower() for x in getattr(data, 'psionic_pp_only_classes', [])}:
        col('powers', not m['powers_chosen'], 'pp-only')
        for key in ('talents', 'max_lvl', 'desc', 'foundry'):
            verdict[key] = '-'
        return verdict

    # ---- max_lvl: the class table capped by "10 + the power's level" ----
    want_max = max(0, min((table.get('max_power_level') or [0] * 20)[row], score - 10))
    col('max_lvl', m['max_power_level'] == want_max, f"{m['max_power_level']}/{want_max}")

    # ---- talents (free) and powers (counted) ----
    want_talents = FREE_TALENTS.get(name, 0)
    buckets = m['powers_by_level']
    got_talents = len(buckets[0]) if buckets else 0
    named_ok = all(t in m['powers_chosen'] for t in MANDATED_TALENTS.get(name, []))
    col('talents', m['talents_known'] == want_talents and got_talents == want_talents and named_ok,
        f"{m['talents_known']}/{want_talents}" + ('' if named_ok else ' NAMED-MISSING'))

    want_known = (table.get('powers_known') or [0] * 20)[row]
    got = m['powers_chosen']
    # No power above the cap, per the LEVEL_OF index rather than the emitted buckets: the buckets
    # are what we are trying to verify, so checking them against themselves proves nothing.
    over = [p for p in got if LEVEL_OF.get(p) and min(LEVEL_OF[p]) > want_max]
    col('powers', len(got) == want_known + want_talents and len(set(got)) == len(got) and not over,
        f"{len(got)}/{want_known + want_talents}" + (f" OVER:{over[:2]}" if over else ''))

    # ---- desc: a name with no rules text renders as an empty row ----
    descs = payload.get('powers_desc_dict') or {}
    undescribed = [p for p in got if not (descs.get(p) or {}).get('text')]
    col('desc', not undescribed, f"{len(got) - len(undescribed)}/{len(got)}"
        + (f" {undescribed[:2]}" if undescribed else ''))

    # ---- foundry: would the module keep these names, or silently drop them? ----
    unknown = [p for p in got if p not in MODULE_KNOWS and p not in METZ_ONLY]
    synthesized = [p for p in got if p in METZ_ONLY]
    col('foundry', not unknown,
        f"{len(got) - len(synthesized)}pack+{len(synthesized)}synth"
        + (f" DROP:{unknown[:2]}" if unknown else ''))
    return verdict


COLUMNS = ['powers', 'talents', 'max_lvl', 'pp', 'subsys', 'desc', 'foundry']


def run(classes, levels, quiet):
    header = f"{'class':<16}{'lvl':>4}  " + "".join(f"{c:<22}" for c in COLUMNS)
    if not quiet:
        print(header)
        print('-' * len(header))
    for name in classes:
        for level in levels:
            cell = f"{name} L{level} seed {SEED}"
            try:
                with redirect_stdout(io.StringIO()):
                    payload = main_test.generate_random_char(
                        class_choice=name, chosen_BAB='high', multi_class='N',
                        userInput_race='random', userInput_region='Tal-Falko',
                        alignment_input='random', userInput_gender='random',
                        high_level=level, low_level=level, gold_num=10000,
                        num_dice='4', num_sides='6', use_backstory_api='N',
                        spheres_flag='N', seed=SEED)
            except Exception:
                fail(cell, f"generation raised -- {traceback.format_exc().strip().splitlines()[-1]}")
                continue

            m = next((x for x in (payload.get('manifesters') or []) if x['name'] == name), None)
            if m is None:
                fail(cell, "no manifesters entry -- a psionic class absent from the payload is "
                           "indistinguishable from a bug")
                continue
            verdict = check_manifester(cell, payload, name, m, level)
            if not quiet:
                print(f"{name:<16}{level:>4}  "
                      + "".join(f"{verdict.get(c, '?'):<22}" for c in COLUMNS))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--classes', help=f'comma-separated subset (default: all {len(CLASSES)})')
    parser.add_argument('--levels', help=f'comma-separated levels (default {LEVELS})')
    parser.add_argument('--quiet', action='store_true', help='verdicts only on failure')
    args = parser.parse_args()

    classes = [c.strip() for c in args.classes.split(',')] if args.classes else CLASSES
    levels = [int(x) for x in args.levels.split(',')] if args.levels else LEVELS
    unknown = [c for c in classes if c not in CLASSES]
    if unknown:
        print(f"not psionic classes: {unknown}", file=sys.stderr)
        return 2

    print(f"psionics sweep: {len(classes)} classes x {levels} = {len(classes) * len(levels)} "
          f"generations (seed {SEED})\n")
    run(classes, levels, args.quiet)

    print()
    return REPORT.finish(f'{len(classes) * len(levels)} manifesters, all columns green')


if __name__ == '__main__':
    raise SystemExit(main())
