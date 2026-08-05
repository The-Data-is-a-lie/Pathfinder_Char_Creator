"""Gate the shape of Backend/scripts/ itself.

    C:\\Python310\\python.exe Backend/scripts/gates/validate_scripts_layout.py

WHY THIS EXISTS
---------------
Ticket 03 chose the bucket boundaries; this is what stops them drifting back. The argument is the
directory's own history: the `validate_*` naming rule was ALSO only a convention, and
`check_racial_stats.py` went years without ever running because nothing checked that the convention
held. A folder layout defended by a sentence in a doc decays the same way -- so the layout gets a
gate, per this repo's doctrine that a hard convention belongs in a validator rather than in prose.

WHAT IT CHECKS (ticket 03, point 5)

1. No `validate_*.py` outside `gates/`, no `test_*.py` outside `tests/` -- except the two runners,
   which stay at the top level because they are what you RUN, not what gets run.
2. Nothing runnable hiding in the library layer: a top-level module that defines `main()` and is not
   a runner is an unfiled script.
3. No orphan libraries: a top-level module nobody imports is an unfiled script too.
4. Both runners' globs still match a non-empty set. This checks the PATTERN rather than trusting it
   -- a glob that silently matches nothing is the exact failure `validate_all.py` exists to prevent,
   and a passing run over zero scripts reads like success.

DELIBERATELY NOT CHECKED: `build/` and `attic/` do not exist yet. Ticket 04 was executed for
`gates/` and `tests/` only, because the other 43 scripts still compute their own repo roots from
their nesting depth (`parents[2]`) and would resolve SILENTLY WRONG one level down rather than
raising. Finishing ticket 01's harness migration for those files is the prerequisite; until then
this gate must not demand a layout the repo has not adopted, or it becomes a failing gate people
learn to skip.
"""
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import GATES, SCRIPTS, TESTS, Report   # noqa: E402

REPORT = Report('validate_scripts_layout')

RUNNERS = {'validate_all.py', 'test_all.py'}
# Buckets that exist today. `build/` and `attic/` join this list when ticket 04's second half lands.
BUCKETS = {'gates': GATES, 'tests': TESTS}


def top_level_modules():
    return sorted(p for p in SCRIPTS.glob('*.py'))


def imported_names():
    """Every module name imported anywhere under scripts/, so an orphan library can be spotted."""
    names = set()
    for path in SCRIPTS.rglob('*.py'):
        try:
            tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
        except SyntaxError:
            REPORT.error(f'{path.relative_to(SCRIPTS)}: does not parse')
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split('.')[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(node.module.split('.')[0])
    return names


def defines_main(path):
    try:
        tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
    except SyntaxError:
        return False
    return any(isinstance(n, ast.FunctionDef) and n.name == 'main' for n in tree.body)


def main():
    # 1. Misfiled gates and tests, anywhere under scripts/ that is not their bucket.
    for path in SCRIPTS.rglob('*.py'):
        name = path.name
        if name in RUNNERS:
            continue
        parent = path.parent.name
        if name.startswith('validate_') and parent != 'gates':
            REPORT.error(f'{path.relative_to(SCRIPTS)}: a validate_*.py belongs in gates/')
        if name.startswith('test_') and parent != 'tests':
            REPORT.error(f'{path.relative_to(SCRIPTS)}: a test_*.py belongs in tests/')

    # 2 + 3. The top level is meant to be "the shared vocabulary, plus the two entry points".
    # It is not that yet: build/ and attic/ have not been split out, so ~43 builders and one-offs
    # legitimately still live there.
    #
    # Reported as ONE counted line rather than one warning per file, deliberately. Forty-three
    # near-identical warnings on a known, ticketed backlog is not information -- it is the noise
    # that teaches people to stop reading a gate's output, which is the same failure as a gate
    # nobody runs. The count is what changes when the backlog moves; the names are in the ticket.
    imported = imported_names()
    runnable, orphans = [], []
    for path in top_level_modules():
        name = path.name
        if name in RUNNERS or name == '_harness.py':
            continue
        if defines_main(path):
            runnable.append(name)
        elif path.stem not in imported:
            orphans.append(name)

    if runnable:
        REPORT.warn(f'{len(runnable)} top-level script(s) define main() and await ticket 04\'s '
                    f'second half (build/ + attic/); they still compute their own repo roots, so '
                    f'moving them is blocked on finishing the _harness migration. '
                    f'e.g. {", ".join(sorted(runnable)[:3])}')
    if orphans:
        REPORT.warn(f'{len(orphans)} top-level module(s) have no importer and no main() -- '
                    f'unfiled or dead: {", ".join(sorted(orphans))}')

    # 4. The runners' globs still find something. This is the check that would have caught a move
    # that quietly emptied a bucket, which reads as a smaller PASSING run.
    for label, directory in BUCKETS.items():
        prefix = 'validate_' if label == 'gates' else 'test_'
        if not directory.is_dir():
            REPORT.error(f'{label}/ does not exist')
            continue
        found = [p for p in directory.glob(f'{prefix}*.py')]
        REPORT.check(found, f'{label}/: glob {prefix}*.py matched nothing -- the runner would '
                            f'report a PASS over zero scripts')

    n_gates = len(list(GATES.glob('validate_*.py'))) if GATES.is_dir() else 0
    n_tests = len(list(TESTS.glob('test_*.py'))) if TESTS.is_dir() else 0
    return REPORT.finish(f'layout OK -- {n_gates} gate(s), {n_tests} test(s), '
                         f'{len(top_level_modules())} top-level module(s)')


if __name__ == '__main__':
    sys.exit(main())
