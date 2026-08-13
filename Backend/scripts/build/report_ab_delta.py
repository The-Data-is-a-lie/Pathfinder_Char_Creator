"""The A/B delta report: what changed between two generations of the same seed?

    C:/Python310/python.exe Backend/scripts/build/report_ab_delta.py --n 20

WHY THIS EXISTS
---------------
Two of this map's three witnesses are automated; the third is Daniel reading characters, and it only
works if reading one is cheap. Ticket 04's ruling: A/B delta report first, Foundry batch second --
because tuning an optimizer without a way to see what it changed is blind. Its exit condition is a
verdict that the report is readable AT VOLUME, not that it is right first time.

NO OPTIMIZER EXISTS YET. So the B side is currently just another random generation, and this runs as
a CHASSIS: it proves the diff, the scoring and the ordering work, and the day an optimizer lands the
only change is which generator produces side B (`--mode`).

THE PROBLEM THIS SOLVES, AND HOW
--------------------------------
Ticket 04 names the real technical problem: one changed draw re-rolls the whole downstream RNG
stream, so a same-seed diff is mostly incidental churn. The fix is `pipeline.enable_phase_streams`
-- one hook in the `phase()` decorator that reseeds from (seed, phase name) at each phase boundary,
so divergence is contained to the phase that changed plus its consumers. It is OFF by default and
the seven goldens are byte-identical without it; this report turns it on for BOTH sides, which is
the only configuration in which the comparison means anything.

Measured on a fighter: perturbing the stat roll moved the weapon from Mattock to Switchblade knife
under the default stream, and left it identical under substreams.

REGRESSIONS FIRST. The interesting cases are where side B scored WORSE, and a flat list of 200
buries them.
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
_bs.OLLAMA_AVAILABLE = False
import main_test                                                                   # noqa: E402
from utils.class_func import pipeline                                              # noqa: E402

# Payload keys worth showing in a delta. Everything else is noise for a build-quality judgement.
INTERESTING = ('str', 'dex', 'con', 'int', 'wis', 'cha', 'chosen_race', 'c_class_display',
               'weapon_name', 'weapon_enhancement_bonus', 'armor_name', 'armor_enhancement_bonus',
               'feats', 'class_feats', 'Total_HP', 'skill_rank_budget')
# dpr_raw, not dpr_expected: the delta below reads `.ratio or 0`, and a benchmark-less axis has
# ratio None on every character -- it would silently report 0.0 delta forever instead of erroring.
SCORE_AXES = ('to_hit', 'dpr_raw', 'burst_raw', 'ac', 'ac_combat', 'hp', 'fort', 'ref', 'will',
              'dc')


def generate(seed, level, sides='6', optimize=None):
    with redirect_stdout(io.StringIO()):
        return main_test.generate_random_char(
            class_choice='random', chosen_BAB='random', multi_class='N',
            userInput_race='random', userInput_region='Tal-Falko', alignment_input='random',
            userInput_gender='random', high_level=level, low_level=level, gold_num="",
            num_dice='4', num_sides=sides, use_backstory_api='N', spheres_flag='N', seed=seed,
            optimize=optimize)


def as_set(value):
    if isinstance(value, dict):
        return {str(k) for k in value}
    if isinstance(value, (list, tuple)):
        return {str(v[0]) if isinstance(v, (list, tuple)) and v else str(v) for v in value}
    return None


def diff(a, b):
    """Semantic per-key differences, collections compared as sets rather than as ordered lists."""
    rows = []
    for key in INTERESTING:
        left, right = a.get(key), b.get(key)
        ls, rs = as_set(left), as_set(right)
        if ls is not None and rs is not None:
            gone, came = sorted(ls - rs), sorted(rs - ls)
            if gone or came:
                rows.append((key, ', '.join(gone) or '--', ', '.join(came) or '--'))
        elif left != right:
            rows.append((key, str(left), str(right)))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--n', type=int, default=12, help='pairs (default 12)')
    parser.add_argument('--levels', default='5,10,15', help='comma-separated levels')
    parser.add_argument('--mode', choices=('chassis', 'optimized'), default='optimized',
                        help="side B: 'optimized' = the real optimizer on the same seed (the "
                             "report this file was built for); 'chassis' = the pre-optimizer "
                             "stand-in perturbation, kept so the substream containment stays "
                             "demonstrable")
    parser.add_argument('--no-substreams', action='store_true',
                        help='compare with the default global RNG stream, to SEE the churn this '
                             'report exists to remove')
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    levels = [int(x) for x in args.levels.split(',')]

    pairs = []
    for level in levels:
        for index in range(args.n):
            seed = 80000 + level * 100 + index
            sides = []
            for side in (0, 1):
                if args.no_substreams:
                    pipeline.disable_phase_streams()
                else:
                    # Both sides on the SAME substream base, so an unchanged phase is identical.
                    pipeline.enable_phase_streams(seed)
                try:
                    if args.mode == 'optimized':
                        # THE REAL COMPARISON: side A is random mode, side B the optimizer, same
                        # seed, same dice, wealth-by-level gold. This is ticket 04's report.
                        payload = generate(seed, level, '6', optimize=True if side else None)
                    else:
                        # STAND-IN chassis: side B perturbed at an EARLY decision (the stat roll
                        # draws a different number of times), kept because it is what makes the
                        # substream containment demonstrable: with substreams on, only the stat
                        # phase and its consumers move; with --no-substreams, everything churns.
                        payload = generate(seed, level, '8' if side else '6')
                except Exception as exc:                                # noqa: BLE001
                    print(f"  seed {seed} side {side}: {exc!r}", file=sys.stderr)
                    sides = []
                    break
                sides.append(payload)
            pipeline.disable_phase_streams()
            if len(sides) != 2:
                continue
            a, b = sides
            pa, pb = power_metric.profile_for(a), power_metric.profile_for(b)
            deltas = {axis: (pb['axes'][axis]['ratio'] or 0) - (pa['axes'][axis]['ratio'] or 0)
                      for axis in SCORE_AXES}
            pairs.append({'seed': seed, 'level': level,
                          'label': f"{a.get('chosen_race')} {a.get('c_class_display')} {level}",
                          'rows': diff(a, b), 'deltas': deltas,
                          'net': statistics.fmean(deltas.values())})

    pairs.sort(key=lambda p: p['net'])          # regressions first
    identical = sum(1 for p in pairs if not p['rows'])

    if args.mode == 'optimized':
        header = ('**Side A is random mode, side B the optimizer, same seed and dice.** A pair '
                  'where B scored WORSE on an axis the role floors is a finding; sorted '
                  'regressions-first so those lead.\n')
    else:
        header = ('**Side B is a second random generation** (the pre-optimizer chassis): the '
                  'numbers below are noise by construction and demonstrate the machinery -- '
                  'semantic diff, per-axis score delta, regressions sorted first.\n')
    out = [f'# A/B delta -- {len(pairs)} pairs, mode {args.mode}'
           f'{" (substreams OFF)" if args.no_substreams else ""}\n',
           header,
           f'**{identical} of {len(pairs)} pairs came back identical on the interesting keys.**\n']

    for pair in pairs[:20]:
        out.append(f"### seed {pair['seed']} | {pair['label']} | net {pair['net']:+.3f}")
        out.append('')
        out.append('  ' + '  '.join(f"{axis} {pair['deltas'][axis]:+.2f}" for axis in SCORE_AXES))
        out.append('')
        if not pair['rows']:
            out.append('_no differences on the interesting keys_')
        for key, left, right in pair['rows']:
            out.append(f'- **{key}**: `{left}` -> `{right}`')
        out.append('')

    text = '\n'.join(out)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
        print(f"wrote {args.out} ({len(pairs)} pairs, {identical} identical)")
    else:
        print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
