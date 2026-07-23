"""Measure curated-buff name mismatches across many generated characters (run directly; this repo
has no pytest harness).

    .venv/Scripts/python.exe Backend/scripts/sweep_buff_gaps.py
    .venv/Scripts/python.exe Backend/scripts/sweep_buff_gaps.py --runs 120

A *gap* is not "nothing curated for this name" -- that is the ordinary case for most feats and
spells. It means curated data for the name EXISTS but the kind's name-matching rule didn't reach it:
a casing, apostrophe, hyphen or suffix difference that silently drops the buff. `buff_match.match()`
detects these by retrying a strict miss with a conservative loose key and reporting the hit.

The four golden payloads only exercise four characters, which is far too thin to decide whether a
kind's matching rule should be widened -- some kinds have thousands of curated keys and a given
character touches a handful. This sweeps many randomized characters and ranks what actually misses,
so a rule change can be justified by count rather than by one anecdote.

Read the output before editing `_REGISTRY` in utils/class_func/buff_match.py. Exits 0 always: it is
a measurement, not a gate.
"""
import argparse
import collections
import contextlib
import io
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BACKEND = HERE.parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(HERE.parent))

from utils.class_func import backstory as _bs

# Same reasoning as test_golden_payload: build_archetype reaches for this helper to break scoring
# ties, so leaving it live would make the sweep depend on whether a model happens to be running.
_bs._try_ollama = lambda *a, **k: ''

import main_test                                    # noqa: E402
import test_golden_payload as tgp                   # noqa: E402  (reuse its config shapes)

RACES = ['Human', 'Orc', 'Elf', 'Dwarf', 'Halfling', 'Half-Orc', 'Gnome', 'Half-Elf']
CLASSES = ['fighter', 'wizard', 'cleric', 'rogue', 'ranger', 'barbarian', 'bard', 'monk',
           'paladin', 'druid', 'sorcerer', 'alchemist', 'magus', 'inquisitor', 'oracle',
           'witch', 'summoner', 'warlord', 'stalker', 'zealot']
BABS = ['low', 'medium', 'high']


def build_configs(runs, rng):
    """Randomized generator inputs, seeded so a reported gap can be reproduced."""
    out = []
    for i in range(runs):
        level = rng.choice([3, 6, 8, 10, 12, 15, 18, 20])
        out.append(dict(
            tgp._BASE,
            userInput_race=rng.choice(RACES),
            class_choice=rng.choice(CLASSES),
            chosen_BAB=rng.choice(BABS),
            multi_class=rng.choice(['N', 'Y']),
            alignment_input=rng.choice(['LG', 'NG', 'CN', 'LN', 'CE']),
            userInput_gender=rng.choice(['male', 'female']),
            high_level=level, low_level=level,
            # Enough gold that gear and enhancements both engage (the quality kind is only
            # exercised once the enhancement budget clears the named-quality threshold).
            gold_num=rng.choice([20000, 60000, 150000, 400000]),
            spheres_flag=rng.choice(['N', 'Y']),
            seed=1_000_000 + i,
        ))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=int, default=60, help='characters to generate (default 60)')
    parser.add_argument('--seed', type=int, default=20260723, help='seed for the config sweep')
    args = parser.parse_args()

    rng = random.Random(args.seed)
    configs = build_configs(args.runs, rng)

    by_kind = collections.Counter()
    by_pair = collections.Counter()
    seeds_for = {}
    failures = 0

    for i, cfg in enumerate(configs, 1):
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                payload = main_test.generate_random_char(**cfg)
        except Exception as exc:                      # noqa: BLE001 - a crash is data, keep sweeping
            failures += 1
            print(f'  run {i} ({cfg["class_choice"]} {cfg["high_level"]}, seed {cfg["seed"]}) '
                  f'raised {type(exc).__name__}: {exc}')
            continue
        for gap in (payload.get('buff_gaps') or []):
            kind = gap.get('kind')
            pair = (kind, gap.get('name'), gap.get('curated_as'))
            by_kind[kind] += 1
            by_pair[pair] += 1
            seeds_for.setdefault(pair, cfg['seed'])
        if i % 10 == 0:
            print(f'  ... {i}/{len(configs)} generated', file=sys.stderr)

    print(f'\nSwept {len(configs) - failures} characters '
          f'({failures} failed to generate).\n')

    if not by_pair:
        print('No gaps found. Every curated entry these characters touched matched its kind\'s '
              'current rule -- no evidence for widening anything.')
        return 0

    print(f'{"kind":<20}{"gaps":>7}   distinct name pairs')
    print('-' * 60)
    for kind, count in by_kind.most_common():
        distinct = len({p for p in by_pair if p[0] == kind})
        print(f'{kind:<20}{count:>7}   {distinct}')

    print(f'\n{"count":>6}  kind / selected name  ->  curated name  (repro seed)')
    print('-' * 90)
    for (kind, name, curated), count in by_pair.most_common():
        print(f'{count:>6}  {kind}: {name!r}\n'
              f'{"":>8}-> curated {curated!r}   (seed {seeds_for[(kind, name, curated)]})')

    print('\nEach line above is a buff that exists but is being dropped. Widen the kind\'s rule in '
          '_REGISTRY\n(utils/class_func/buff_match.py) one kind at a time, regenerating goldens '
          'per kind so each\ndiff is attributable.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
