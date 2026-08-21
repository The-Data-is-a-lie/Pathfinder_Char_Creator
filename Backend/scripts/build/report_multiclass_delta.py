"""Is a random multiclass character worse than a random single-class one? (map: optimal-builder, ticket 07)

    C:/Python310/python.exe Backend/scripts/build/report_multiclass_delta.py --n 60

WHY THIS EXISTS
---------------
Ticket 07 calls random multiclassing "the single largest source of bad builds in the generator" --
`select_classes` picks the count with `random.choices([2,3,4], weights=[50,35,15])` and the members
uniformly, then `_split_levels` scatters the levels with `random.randrange(count)`. That is an
assertion nobody has measured, and the ticket says so outright: score today's random multiclass
characters against today's random single-class characters at the same level. **If the gap is small,
this ticket is smaller than it looks; if it is large, it is the map's biggest single win.**

This needs its OWN generations: the invariant sweep drives one named class per cell and always
passes `multi_class='N'`, so the `--score` baseline contains no multiclass characters at all.

Deliberately paired: the same seed and the same level produce one single-class and one multiclass
character, so the comparison is not confounded by level or by luck of the draw on gold.
"""
import argparse
import io
import json
import statistics
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND                                                       # noqa: E402

sys.path.insert(0, str(BACKEND))
import power_metric                                                                # noqa: E402
from utils.class_func import backstory as _bs                                      # noqa: E402
_bs.OLLAMA_AVAILABLE = False        # sever Ollama, as the golden runner and the sweep both do
import main_test                                                                   # noqa: E402

LEVELS = (5, 10, 15, 20)
# dpr_raw, not dpr_expected: median_ratio drops None ratios, and a benchmark-less axis would
# render as a useless all-`--` row rather than fail.
AXES = ('to_hit', 'dpr_raw', 'ac', 'hp', 'fort', 'ref', 'will', 'dc')


def generate(seed, level, multi):
    with redirect_stdout(io.StringIO()):
        return main_test.generate_random_char(
            class_choice='random', chosen_BAB='random', multi_class=('Y' if multi else 'N'),
            userInput_race='random', userInput_region='Tal-Falko', alignment_input='random',
            userInput_gender='random', high_level=level, low_level=level, gold_num=10000,
            num_dice='4', num_sides='6', use_backstory_api='N', spheres_flag='N', seed=seed)


def median_ratio(rows, axis):
    values = [r['axes'][axis]['ratio'] for r in rows if r['axes'][axis]['ratio'] is not None]
    return statistics.median(values) if values else None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--n', type=int, default=40, help='pairs per level (default 40)')
    parser.add_argument('--out', default=None)
    args = parser.parse_args()

    single, multi, failures = [], [], 0
    for level in LEVELS:
        for index in range(args.n):
            seed = 70000 + level * 1000 + index
            for bucket, is_multi in ((single, False), (multi, True)):
                try:
                    payload = generate(seed, level, is_multi)
                    profile = power_metric.profile_for(payload)
                except Exception as exc:                                # noqa: BLE001
                    failures += 1
                    print(f"  seed {seed} L{level} multi={is_multi}: {exc!r}", file=sys.stderr)
                    continue
                profile['classes_n'] = len(payload.get('classes') or [])
                bucket.append(profile)
        print(f"  level {level}: {len(single)} single / {len(multi)} multi so far",
              file=sys.stderr)

    out = [f'# Multiclass vs single-class -- {len(single)} single, {len(multi)} multiclass\n',
           'Paired by seed and level. Ratios are against the CR row for the character\'s level '
           '(level - 1). A negative delta means the multiclass build scored WORSE.\n']
    header = ['axis'] + [f'L{level}' for level in LEVELS] + ['all']
    body = []
    for axis in AXES:
        row = [axis]
        for level in list(LEVELS) + [None]:
            s = [r for r in single if level is None or r['level'] == level]
            m = [r for r in multi if level is None or r['level'] == level]
            sv, mv = median_ratio(s, axis), median_ratio(m, axis)
            row.append('--' if (sv is None or mv is None) else f'{mv - sv:+.3f}')
        body.append(row)
    widths = [max(len(str(r[i])) for r in [header] + body) for i in range(len(header))]
    out.append('| ' + ' | '.join(h.ljust(w) for h, w in zip(header, widths)) + ' |')
    out.append('|' + '|'.join('-' * (w + 2) for w in widths) + '|')
    for row in body:
        out.append('| ' + ' | '.join(str(c).ljust(w) for c, w in zip(row, widths)) + ' |')
    out.append('')

    counts = {}
    for row in multi:
        counts[row['classes_n']] = counts.get(row['classes_n'], 0) + 1
    out.append('Class counts among the multiclass builds: '
               + ', '.join(f'{n} classes: {c}' for n, c in sorted(counts.items())) + '\n')
    if failures:
        out.append(f'{failures} generation(s) raised and were dropped.\n')

    text = '\n'.join(out)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
