"""The feat budget must be spent, not silently clamped (ticket 08).

    C:/Python310/python.exe Backend/scripts/tests/test_feat_budget.py [--levels 1,5,20] [--seeds N]

WHY THIS GATE EXISTS
--------------------
`character.feat_amounts` is the most-mutated value in the generator: assigned once in
`level_and_bab.py`, then `+=`'d from four "refund" sites and REASSIGNED once through a
`max(0, ...)` that reserves budget for Path of War, Spheres and professions.

That `max(0, ...)` is the whole ticket. It exists because the subtraction can go negative, and its
response to going negative is to clamp to zero -- so an over-committed budget produces a character
with quietly fewer feats than the rules allow, and nobody finds out. The golden fixtures cannot see
it either: they record whatever the clamp produced, so a clamped character is "correct" forever.

WHAT THE MEASUREMENT FOUND
--------------------------
Instrumented across the full roster (70 classes x 5 levels x 2 seeds = 700 generations, spheres on):

  * the feat_amounts clamp fires in 16/700 (2.3%) of generations
  * every single one is at LEVEL 1 -- 0 occurrences at 5, 10, 15 or 20
  * the worst overdraft is -2 feats
  * the sibling clamp on `normal_feat_amount` never fires at all (0/700)

So this is not a pervasive over-commitment, and it is not dead code either. It is a narrow,
reproducible level-1 bug with a named cause: a 1st-level character's budget is 7, and the homebrew
subsystems ask for more than that -- typically 5 sphere feats plus 3 profession feats against a
budget of 7. The subsystems are sized as though the budget were a mid-level one.

WHY A GATE AND NOT A `FeatBudget` OBJECT
----------------------------------------
Ticket 08 offered three answers. Option A (`provides=['feat_amounts']`) was already ruled out by the
phase contract's own semantics: `@phase` checks EXISTENCE, and feat_amounts exists from
`randomize_level` onward, so the contract would be satisfied by every phase and catch nothing --
presence is the wrong question for a value whose bug is arithmetic.

Option B -- a `FeatBudget` with `reserve()`/`grant()` methods that refuse to go negative -- is real
leverage, and it is what this should become IF the over-commit turns out to be structural. The
measurement says it is not: it is one edge, at one level, in 2.3% of runs. Inventing an interface
for one value, to prevent a bug that occurs in that band, buys less than it costs and risks becoming
a framework -- which the map explicitly warns against.

So: option C. The arithmetic stays; the SILENCE goes. This gate turns a clamp nobody sees into a
failure with the over-drawer named. If the failures ever spread beyond level 1, that is the evidence
that promotes this to option B, and it will arrive as a test failure rather than as a bug report
from a Foundry sheet.

WHAT IT CHECKS
--------------
1. The budget is never over-committed -- the raw (pre-clamp) reservation must not go negative.
   This currently FAILS at level 1, deliberately: the bug is real and naming it is the point.
2. The clamp, when it fires, is reported with the arithmetic that caused it, so the finding says
   who over-drew rather than that something was wrong.
3. Census: the reservation block must actually be REACHED. A run where no generation reaches it
   proves nothing, and would otherwise look like a pass.
"""
import argparse
import ast
import io
import json
import sys
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report, BACKEND, REPO  # noqa: E402

from utils.class_func import backstory as _bs  # noqa: E402
# Sever Ollama exactly as the other sweeps do: build_archetype reaches for it to break scoring ties,
# and a gate whose result depends on whether a local model is running is not a gate.
_bs._try_ollama = lambda *a, **k: ''

import main_test  # noqa: E402

REPORT = Report('test_feat_budget')

# The trace points are located by CONTENT, not by line number. This file would otherwise need
# editing every time ticket 07 extracts another phase and shifts main_test.py -- and a gate that
# silently traces the wrong line is worse than no gate.
SRC = (BACKEND / 'main_test.py').read_text(encoding='utf-8').splitlines()

PRE_MARK = "_prof_feat_n = len(getattr(character, 'profession_feats'"
CLAMP_MARK = "character.normal_feat_amount = max(0, character.normal_feat_amount - _prof_feat_n)"


def _line_of(needle, start=0):
    for i in range(start, len(SRC)):
        if needle in SRC[i]:
            return i + 1
    return None


PRE_LINE = _line_of(PRE_MARK)
CLAMP_LINE = _line_of(CLAMP_MARK)


def _enclosing_function(lineno):
    """Which function currently CONTAINS the reservation.

    Not hardcoded, and that matters: ticket 07 moved this block out of `generate_random_char` and
    into `phase_path_of_war_and_spheres`, which would have left a tracer keyed on the old name
    matching no frame at all. The census check below turns that into a loud failure rather than a
    silent pass, but resolving the name from the source means it does not fail in the first place.
    """
    if lineno is None:
        return None
    tree = ast.parse('\n'.join(SRC))
    best = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.lineno <= lineno <= (node.end_lineno or 0):
            if best is None or node.lineno > best.lineno:      # innermost wins
                best = node
    return best.name if best else None


TARGET_FUNC = _enclosing_function(CLAMP_LINE)


def _tracer_for(bucket):
    """Capture the budget on the line before the reservation, and its inputs on the line after."""
    state = {}

    def tracer(frame, event, arg):
        if frame.f_code.co_name != TARGET_FUNC:
            return None
        if event == 'call':
            return tracer
        if event != 'line':
            return tracer
        character = frame.f_locals.get('character')
        if character is None:
            return tracer
        if frame.f_lineno == PRE_LINE and 'pre' not in state:
            state['pre'] = character.feat_amounts
        elif frame.f_lineno == CLAMP_LINE and 'post' not in state:
            local = frame.f_locals
            state['post'] = character.feat_amounts
            state['mt'] = len(local.get('mt_feats') or [])
            state['style'] = len(local.get('style_feats') or [])
            state['funded'] = local.get('_pow_funded_n') or 0
            state['spheres'] = len(local.get('sphere_feats') or [])
            state['prof'] = local.get('_prof_feat_n') or 0
            bucket.update(state)
        return tracer

    return tracer


def measure(name, level, seed):
    bucket = {}
    with redirect_stdout(io.StringIO()):
        sys.settrace(_tracer_for(bucket))
        try:
            main_test.generate_random_char(
                class_choice=name, chosen_BAB='high', multi_class='N',
                userInput_race='random', userInput_region='Tal-Falko',
                alignment_input='random', userInput_gender='random',
                high_level=level, low_level=level, gold_num=10000,
                num_dice='4', num_sides='6', use_backstory_api='N',
                spheres_flag='Y', professions_flag='Y', trainers_flag='Y', seed=seed)
        finally:
            sys.settrace(None)
    if 'post' not in bucket:
        return None
    bucket['raw'] = (bucket['pre'] - (bucket['mt'] + bucket['style'] - bucket['funded'])
                     - bucket['spheres'] - bucket['prof'])
    return bucket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--levels', default='1,5,20',
                    help='comma-separated character levels to sweep')
    ap.add_argument('--seeds', default='1101',
                    help='comma-separated seeds; more seeds widen the sample')
    ap.add_argument('--classes', default='', help='restrict the roster (debugging)')
    args = ap.parse_args()

    if PRE_LINE is None or CLAMP_LINE is None or TARGET_FUNC is None:
        REPORT.error(
            'could not locate the feat-budget reservation in main_test.py -- the marker lines '
            f'moved. Looked for {PRE_MARK!r} and {CLAMP_MARK!r}. This gate traces by content so '
            'that phase extraction cannot silently point it at the wrong line; update the markers.')
        return REPORT.finish('feat budget')

    with open(BACKEND / 'json' / 'class_data.json', encoding='utf-8') as f:
        roster = sorted(json.load(f))
    if args.classes:
        roster = [c.strip() for c in args.classes.split(',')]
    levels = [int(x) for x in args.levels.split(',')]
    seeds = [int(x) for x in args.seeds.split(',')]

    print(f'sweeping {len(roster)} classes x {len(levels)} levels x {len(seeds)} seeds, '
          f'spheres on (tracing {TARGET_FUNC}() at main_test.py:{PRE_LINE} and :{CLAMP_LINE})')

    reached = 0
    over = []
    for name in roster:
        for level in levels:
            for seed in seeds:
                cell = f'{name} L{level} seed {seed}'
                try:
                    row = measure(name, level, seed)
                except Exception as exc:                          # noqa: BLE001
                    REPORT.error(f'{cell}: generation raised -- {type(exc).__name__}: {exc}')
                    continue
                if row is None:
                    continue
                reached += 1
                if row['raw'] < 0:
                    over.append((cell, row))

    # (3) Census first: a sweep that never reached the reservation proves nothing, and without this
    #     an empty run reads as a clean pass.
    REPORT.check(
        reached > 0,
        f'the feat-budget reservation was never reached in {len(roster) * len(levels) * len(seeds)} '
        'generations -- this gate proved nothing. Check that spheres/professions are enabled.')
    print(f'  reservation reached in {reached} generation(s)')

    # (2) Report each over-commit with the arithmetic that caused it, so the finding names the
    #     over-drawer instead of just asserting a number is wrong.
    for cell, row in over:
        REPORT.error(
            f'{cell}: feat budget over-committed by {-row["raw"]} -- budget {row["pre"]}, '
            f'reserved {row["mt"]} martial-training + {row["style"]} style '
            f'(- {row["funded"]} mentor-funded) + {row["spheres"]} sphere + {row["prof"]} profession '
            f'= {row["pre"] - row["raw"]}. The max(0, ...) clamped it to {row["post"]}, so this '
            f'character silently has {-row["raw"]} fewer feat(s) than the rules allow.')

    # (1) The invariant itself, plus the shape of the failures -- because "which levels" is the
    #     fact that decides whether this stays option C or becomes option B.
    if over:
        by_level = Counter(int(c.split(' L')[1].split(' ')[0]) for c, _ in over)
        worst = min(r['raw'] for _, r in over)
        print(f'\n  over-commits by level: {dict(sorted(by_level.items()))}, worst {worst}')
        if set(by_level) == {1}:
            print('  (still level-1 only -- the narrow bug ticket 08 measured, not a structural '
                  'over-commit. If other levels appear here, promote to a FeatBudget object.)')
        else:
            print('  (!! over-commits outside level 1 -- this is the evidence that promotes '
                  'ticket 08 from option C to option B, a real FeatBudget with reserve()/grant().)')

    return REPORT.finish(f'{reached} generation(s) checked for feat-budget over-commitment')


if __name__ == '__main__':
    sys.exit(main())
