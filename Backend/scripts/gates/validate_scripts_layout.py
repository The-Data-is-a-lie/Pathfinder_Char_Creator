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

5. Nothing at the top level computes its own repo root. All four buckets exist now, so the top level
   is meant to be exactly "the shared vocabulary, plus the two entry points" -- and the thing that
   made the second half of ticket 04 dangerous was 43 files deriving REPO from their own nesting
   depth, which resolves SILENTLY WRONG one level down instead of raising. A new top-level file that
   reintroduces `parents[N]` is the start of that backlog reforming, so it fails here.
"""
import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import ATTIC, BUILD, GATES, SCRIPTS, TESTS, Report   # noqa: E402

REPORT = Report('validate_scripts_layout')

RUNNERS = {'validate_all.py', 'test_all.py'}
# All four buckets, as of ticket 04's second half. Only the two with a naming rule are glob-checked;
# build/ and attic/ hold whatever their names say and have no prefix to assert.
BUCKETS = {'gates': GATES, 'tests': TESTS}
POPULATED = {'gates': GATES, 'tests': TESTS, 'build': BUILD, 'attic': ATTIC}

# The depth math ticket 01 removed and ticket 04's second half finished removing. `_harness.py` is
# the one file allowed to compute it -- it is what everything else imports instead.
OWN_REPO_ROOT = re.compile(r'parents\[\d\]|os\.path\.dirname\(os\.path\.dirname\(')


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

    # 2 + 3. The top level is "the shared vocabulary, plus the two entry points", and as of ticket
    # 04's second half it actually is that. These were warnings while 43 files were queued to move;
    # now that the queue is empty they are errors, because the next file to land here would be the
    # start of the pile reforming.
    imported = imported_names()
    for path in top_level_modules():
        name = path.name
        if name in RUNNERS or name == '_harness.py':
            continue
        if defines_main(path):
            REPORT.error(f'{name}: defines main() at the top level -- a runnable script belongs in '
                         f'gates/, tests/, build/ or attic/, not in the library layer')
        elif path.stem not in imported:
            REPORT.error(f'{name}: no importer and no main() -- an unfiled script or a dead library')

    # 5. Nobody at the top level recomputes the repo root. Depth math is what made the 43-file move
    # dangerous, and it fails quietly rather than loudly, so it gets a check rather than a comment.
    for path in top_level_modules():
        if path.name == '_harness.py':
            continue
        for number, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
            if OWN_REPO_ROOT.search(line) and 'noqa: depth' not in line:
                REPORT.error(f'{path.name}:{number}: computes a path from its own nesting depth -- '
                             f'import REPO/BACKEND/JSON_DIR/GOLDEN_DIR from _harness instead')

    # 4. The runners' globs still find something. This is the check that would have caught a move
    # that quietly emptied a bucket, which reads as a smaller PASSING run.
    for label, directory in POPULATED.items():
        if not directory.is_dir():
            REPORT.error(f'{label}/ does not exist')
            continue
        if label in BUCKETS:
            prefix = 'validate_' if label == 'gates' else 'test_'
            found = [p for p in directory.glob(f'{prefix}*.py')]
            REPORT.check(found, f'{label}/: glob {prefix}*.py matched nothing -- the runner would '
                                f'report a PASS over zero scripts')
        else:
            REPORT.check(list(directory.glob('*.py')),
                         f'{label}/: empty -- an empty bucket is a move that lost its files')

    counts = ', '.join(f'{len(list(d.glob("*.py")))} in {label}/'
                       for label, d in POPULATED.items() if d.is_dir())
    return REPORT.finish(f'layout OK -- {counts}, '
                         f'{len(top_level_modules())} top-level module(s)')


if __name__ == '__main__':
    sys.exit(main())
