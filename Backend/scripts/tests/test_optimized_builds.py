"""The optimizer's margin gate (spec 15, ruling 9): floors hold, primaries beat the twin.

    C:/Python310/python.exe Backend/scripts/tests/test_optimized_builds.py

WHAT THIS ASSERTS, AND WHY THIS LITTLE
--------------------------------------
Ruling 9 is measure-first: no margin number is enshrined before the optimized distribution exists.
So until power_roles.json carries measured per-role `margins`, this gate asserts only what needs no
tuning:

1. **The floors hold** -- every axis a role floors scores at least that ratio. Floors are
   provisional data (power_roles.json `_floors_note`) and absorb race variance by ruling, so a
   failure here is a tuning signal with a file to edit, never a mystery.
2. **The primaries beat the same-seed random twin** -- direction, not magnitude. Each optimized
   character is compared to the random character grown from the SAME seed, dice and gold; a small
   tolerance absorbs draw-order noise on axes no spine chooser touches yet (skill_breadth, until
   the leaf-scoring slice lands).
3. When a role row carries `margins` (written from the measured A/B distribution, Phase D), each
   named axis must clear it.

THE TAUTOLOGY GUARD. The optimizer never reads a ratio -- it follows the role table's ladders and
priorities; the METRIC computes ratios from the CR table. Asserting ratios here therefore tests
composed behaviour against an external benchmark, not a maximizer against itself. The A/B report
(build/report_ab_delta.py --mode optimized) stays the human witness.

Sampling: for every role, the first two classes whose class_roles row lists it, at two levels,
one seed -- role coverage without a full-roster sweep. ~56 generations, so it stays runnable in
test_all's default pass.
"""
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND, JSON_DIR, Report, read_json                           # noqa: E402

sys.path.insert(0, str(BACKEND))
import power_metric                                                                 # noqa: E402
from utils.class_func import backstory as _bs                                       # noqa: E402
_bs.OLLAMA_AVAILABLE = False
_bs._try_ollama = lambda *a, **k: ''
import main_test                                                                    # noqa: E402

REPORT = Report('test_optimized_builds')

LEVELS = (5, 15)
SEED_BASE = 91000
# Ratio slack for beat-the-twin on primaries. 0.15 by measurement, not taste: at L5 a single
# attack's weapon-dice draw dominates the damage axes, and a top-percentile twin (1.41 vs the
# random median 0.72) beat a strong optimized 1.21 by exactly this band. The tolerance dies when
# measured per-role margins land -- an absolute bar needs no twin.
TWIN_TOLERANCE = 0.15


def generate(cls, level, seed, optimize):
    with redirect_stdout(io.StringIO()):
        return main_test.generate_random_char(
            class_choice=cls, chosen_BAB='random', multi_class='N',
            userInput_race='random', userInput_region='Tal-Falko', alignment_input='random',
            userInput_gender='random', high_level=level, low_level=level, gold_num="",
            num_dice='4', num_sides='6', use_backstory_api='N', spheres_flag='N',
            seed=seed, optimize=optimize)


def sample_cells(table):
    """(role, class) pairs: the first two classes listing each role. Deterministic."""
    cells = []
    for role in sorted(k for k in table['roles'] if not k.startswith('_')):
        classes = sorted(cls for cls, roles in table['class_roles'].items() if role in roles)
        for cls in classes[:2]:
            cells.append((role, cls))
    return cells


def axis_value(profile, axis):
    """The comparable number for an axis: the benchmark ratio when one exists, else raw."""
    entry = profile['axes'].get(axis) or {}
    return entry['ratio'] if entry.get('ratio') is not None else (entry.get('raw') or 0)


def main():
    table = read_json(JSON_DIR / 'power_roles.json')
    cells = sample_cells(table)
    generated = 0
    for index, (role, cls) in enumerate(cells):
        row = table['roles'][role]
        for level in LEVELS:
            seed = SEED_BASE + index * 100 + level
            try:
                optimized = generate(cls, level, seed, role)
                twin = generate(cls, level, seed, None)
            except Exception as exc:                                    # noqa: BLE001
                REPORT.error(f'{role}/{cls} L{level} seed {seed}: generation raised {exc!r}')
                continue
            generated += 2
            prof = power_metric.profile_for(optimized)
            twin_prof = power_metric.profile_for(twin)

            for axis, floor in (row.get('floors') or {}).items():
                ratio = (prof['axes'].get(axis) or {}).get('ratio')
                if ratio is None:
                    REPORT.error(f'{role}/{cls} L{level}: floored axis {axis!r} has no ratio')
                    continue
                REPORT.check(ratio >= floor,
                             f'{role}/{cls} L{level} seed {seed}: {axis} ratio {ratio} is under '
                             f'the role floor {floor} -- tune power_roles.json floors or fix the '
                             f'chooser, but never ignore it')

            # Per-primary: the MEASURED margin is the bar wherever one exists -- ruling 9's twin
            # test was scaffolding until the optimized distribution was measured, and an absolute
            # bar cannot be flaked by a hot twin (the ambient-feat fold armed the twins with free
            # Power Attack and immediately proved the point). Axes without a margin keep the
            # twin-with-tolerance comparison.
            margins = row.get('margins') or {}
            deltas = []
            for axis in row.get('primaries') or []:
                if axis in margins:
                    continue          # the absolute bar below is this axis's assertion
                ours, theirs = axis_value(prof, axis), axis_value(twin_prof, axis)
                deltas.append(ours - theirs)
                REPORT.check(ours >= theirs - TWIN_TOLERANCE * max(1.0, abs(theirs)),
                             f'{role}/{cls} L{level} seed {seed}: primary {axis} {ours} lost to '
                             f'the same-seed random twin {theirs} beyond tolerance -- the '
                             f'optimizer made this axis WORSE (and no measured margin covers it)')
            # >= 0, not > 0: an unmargined primary can be pure CHASSIS (an adept's caster_tier,
            # an aristocrat's dc) which the optimizer cannot move -- equality with the twin is
            # correct there. Forward motion is asserted by the measured margins above; this line
            # only forbids moving BACKWARD.
            REPORT.check(not deltas or sum(deltas) >= 0,
                         f'{role}/{cls} L{level} seed {seed}: unmargined primaries net '
                         f'{sum(deltas):+.3f} vs the twin -- optimized mode moved the role '
                         f'backward')

            for axis, margin in margins.items():
                value = axis_value(prof, axis)
                REPORT.check(value >= margin,
                             f'{role}/{cls} L{level} seed {seed}: {axis} {value} under the '
                             f'measured margin {margin}')
    return REPORT.finish(f'{len(cells)} role/class cells x {len(LEVELS)} levels, '
                         f'{generated} generations')


if __name__ == '__main__':
    sys.exit(main())
