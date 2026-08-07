"""Every pipeline phase must declare its contract, and declare it in the right place.

    C:/Python310/python.exe Backend/scripts/gates/validate_phase_contracts.py
    C:/Python310/python.exe Backend/scripts/gates/validate_phase_contracts.py --print

WHY THIS GATE EXISTS
--------------------
`utils/class_func/pipeline.py` decides where a phase's outputs go, and the decision has three
buckets (see its WHERE A PHASE'S OUTPUTS GO section):

  1. character state      -> declared in `provides`
  2. derivable at export  -> stored nowhere, computed in the payload builder
  3. everything else      -> a `PhaseRecord` field, declared in `returns`

That rule is written down, and this repo's doctrine is explicit that a rule which is only written
down is the same kind of rule as a comment: `CLAUDE.md` -- "Hard conventions belong in a validator
[...] a stale `critical: "onCrit"` in a doc silently broke six weapons."

The specific drift this catches is cheap to commit and expensive to find. A phase that returns a
bare tuple reintroduces exactly the positional soup the record exists to prevent, and it does so
invisibly -- the call site still works, right up until someone inserts a value in the middle and
every reader after it silently shifts by one. That is the failure mode that reaches a Foundry sheet.

WHAT IT CHECKS
--------------
1. Every function named `phase_*` in main_test.py actually carries the `@phase` decorator. A phase
   that loses its decorator keeps working and stops checking anything, which is the worst outcome
   available: the guard is gone and nothing says so.
2. No name is declared in BOTH `provides` and `returns`. One value, one home -- a value in both is
   two sources of truth for the same fact, and readers will disagree about which is current.
3. A phase declaring `returns` must actually construct a `PhaseRecord`. This is what stops the
   slide back to tuples.
4. `requires` stays small (ticket 05: 2-4 names, or 0 for the first phase). The rule is that
   `requires` names only what crosses IN; a decorator that grows past four is rebuilding the
   unreadable wall it replaced -- except now it fails at import time when it drifts.
5. Anything a phase declares in `returns` must be read as `<record>.<field>` somewhere, or it is
   dead weight riding the record.

KNOWN DEBT, NAMED RATHER THAN HIDDEN
------------------------------------
Three phases predate the record rule and still return bare tuples (`TUPLE_RETURN_DEBT`). They are
warnings, not errors, because converting them is ticket 07 work and a gate that fails on the day it
lands is a gate people disable. The list is the point: it shrinks as ticket 07 proceeds, and a NEW
tuple-returning phase is an error rather than joining the list.
"""
import argparse
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report, BACKEND  # noqa: E402

REPORT = Report('validate_phase_contracts')

TARGET = BACKEND / 'main_test.py'

# Phases extracted before the PhaseRecord rule was decided. Each still returns a bare tuple.
# Shrink this list as ticket 07 converts them; never add to it.
TUPLE_RETURN_DEBT = {
    'phase_bootstrap_identity',        # returns (f_name, l_name)
    'phase_roll_and_assign_stats',     # returns stats
    'phase_professions_and_skills',    # returns (professions, skill_ranks)
}

MAX_REQUIRES = 4


def _decorator_kwargs(node):
    """Return {kwarg: [str, ...]} for the @phase decorator, or None if there isn't one."""
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        name = dec.func.id if isinstance(dec.func, ast.Name) else getattr(dec.func, 'attr', None)
        if name != 'phase':
            continue
        out = {}
        for kw in dec.keywords:
            values = []
            if isinstance(kw.value, (ast.List, ast.Tuple)):
                values = [e.value for e in kw.value.elts if isinstance(e, ast.Constant)]
            out[kw.arg] = values
        return out
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--print', action='store_true', dest='show',
                    help='print each phase and its declared contract')
    args = ap.parse_args()

    source = TARGET.read_text(encoding='utf-8')
    tree = ast.parse(source)

    phases = [n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name.startswith('phase_')]
    if not phases:
        REPORT.error(f'no phase_* functions found in {TARGET.name} -- either the pipeline was '
                     'dismantled or this gate is looking at the wrong file')
        return REPORT.finish('phase contracts')

    for fn in sorted(phases, key=lambda n: n.lineno):
        kwargs = _decorator_kwargs(fn)

        # (1) the decorator itself
        if kwargs is None:
            REPORT.error(
                f'{fn.name} (line {fn.lineno}): named phase_* but carries no @phase decorator -- '
                'it will run and check nothing, which is worse than not being a phase at all')
            continue

        requires = kwargs.get('requires', [])
        provides = kwargs.get('provides', [])
        returns = kwargs.get('returns', [])

        if args.show:
            print(f'  {fn.name}')
            print(f'      requires {requires or "-"}')
            print(f'      provides {provides or "-"}')
            print(f'      returns  {returns or "-"}')

        # (2) one value, one home
        both = sorted(set(provides) & set(returns))
        if both:
            REPORT.error(
                f'{fn.name}: {", ".join(both)} declared in BOTH provides and returns. A value lives '
                'on the character OR on the record, never both -- two homes means two readers that '
                'can disagree about which is current')

        # (3) no slide back to tuples
        body_src = ast.get_source_segment(source, fn) or ''
        builds_record = 'PhaseRecord(' in body_src
        if returns and not builds_record:
            REPORT.error(
                f'{fn.name}: declares returns={returns} but never constructs a PhaseRecord. A bare '
                'tuple reintroduces the positional soup the record exists to prevent -- inserting a '
                'value in the middle silently shifts every reader after it')
        if not returns and not builds_record:
            has_value_return = any(isinstance(n, ast.Return) and n.value is not None
                                   for n in ast.walk(fn))
            if has_value_return:
                if fn.name in TUPLE_RETURN_DEBT:
                    REPORT.warn(
                        f'{fn.name}: returns a bare tuple (pre-record phase, ticket 07 debt). '
                        'Convert it to a PhaseRecord when ticket 07 next touches this block.')
                else:
                    REPORT.error(
                        f'{fn.name}: returns a value but declares no `returns` and builds no '
                        'PhaseRecord. New phases hand outputs back on a record -- see '
                        'pipeline.py, WHERE A PHASE OUTPUTS GO')

        # (4) requires stays small
        if len(requires) > MAX_REQUIRES:
            REPORT.error(
                f'{fn.name}: requires {len(requires)} names ({", ".join(requires)}), over the '
                f'{MAX_REQUIRES} the rule allows. `requires` names only what crosses IN from another '
                'phase -- a value the block computes then consumes is a local, not a dependency')

        # (5) declared record fields must actually be read
        for field in returns:
            if f'.{field}' not in source.replace(f'{field}=', ''):
                REPORT.warn(f'{fn.name}: declares returns {field!r} but nothing reads '
                            f'<record>.{field} -- dead weight on the record')

    checked = len([n for n in phases if _decorator_kwargs(n) is not None])
    if TUPLE_RETURN_DEBT:
        print(f'\n  ticket 07 debt: {len(TUPLE_RETURN_DEBT)} phase(s) still returning bare tuples')
    return REPORT.finish(f'{checked} phase contract(s) validated')


if __name__ == '__main__':
    sys.exit(main())
