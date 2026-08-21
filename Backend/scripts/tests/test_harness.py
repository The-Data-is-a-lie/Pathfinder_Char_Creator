"""Gate for _harness.py itself.

Everything in this directory is about to route its pass/fail decision through `Report`, so a bug
here is a bug in every gate at once -- specifically the dangerous direction, a `finish()` that
returns 0 while errors are pending, which would turn the whole suite green and stay that way.

Written in the same standalone-script shape as the scripts it guards, deliberately: a harness that
needed a different test convention than the one it serves would be evidence it was the wrong shape.

Usage: python Backend/scripts/tests/test_harness.py
"""
import io
import os
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _harness import (  # noqa: E402
    Report, read_json, _find_repo_root, BACKEND, REPO, JSON_DIR, DATA_DIR, GOLDEN_DIR, SCRIPTS)

FAILURES = []
CHECKS = [0]


def check(condition, message):
    CHECKS[0] += 1
    if not condition:
        FAILURES.append(message)


def run(report, summary='', max_errors=None):
    """finish() with its output captured -> (exit_code, printed_text)."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = report.finish(summary, max_errors)
    return code, buffer.getvalue()


def test_clean_report_passes():
    report = Report('gate')
    report.check(True, 'never recorded')
    code, out = run(report, '3 things validated')
    check(code == 0, f'a clean report must exit 0, got {code}')
    check('OK: 3 things validated.' in out, f'clean summary line wrong: {out!r}')
    check(report.checks == 1, f'check() must count, got {report.checks}')


def test_error_fails_and_prints():
    report = Report('gate')
    report.check(False, 'the thing was wrong')
    code, out = run(report)
    check(code == 1, f'an error must exit 1, got {code}')
    check('the thing was wrong' in out, 'the error text must be printed')
    check('FAILED: 1 problem(s)' in out, f'failure line wrong: {out!r}')


def test_max_errors_truncates_but_still_counts():
    """One bad rule can fail all 392 species at once; the count must survive the truncation."""
    report = Report('gate')
    for i in range(10):
        report.error(f'problem number {i}')
    code, out = run(report, max_errors=3)
    check(code == 1, 'truncation must not change the verdict')
    check('problem number 2' in out, 'the first max_errors errors must be shown')
    check('problem number 9' not in out, 'errors past the cap must be withheld')
    check('... and 7 more' in out, f'the withheld count must be stated: {out!r}')
    check('FAILED: 10 problem(s)' in out, f'the TOTAL must be reported, not the shown count: {out!r}')


def test_no_cap_shows_everything():
    report = Report('gate')
    for i in range(10):
        report.error(f'problem number {i}')
    code, out = run(report)
    check('problem number 9' in out, 'without max_errors every error must print')
    check('more' not in out, 'without max_errors nothing is withheld')


def test_check_returns_condition():
    """Callers branch on it to avoid descending into something already proved malformed."""
    report = Report('gate')
    check(report.check(True, 'x') is True, 'check() must return True when it passes')
    check(report.check(False, 'y') is False, 'check() must return False when it fails')
    check(report.error('z') is False, 'error() must return False so it can be returned directly')


def test_warnings_are_not_fatal():
    report = Report('gate')
    report.warn('a duplicate name')
    code, out = run(report, 'all good')
    check(code == 0, f'warnings must not fail the gate, got exit {code}')
    check('WARN: a duplicate name' in out, 'warnings must be printed with a WARN: prefix')
    check('(1 warning(s))' in out, f'warning count must reach the OK line: {out!r}')


def test_skips_print_even_when_clean():
    """A check that quietly stops running is the failure mode this directory exists to prevent."""
    report = Report('gate')
    report.skip('web sheet: not checked out here')
    code, out = run(report, 'the rest validated')
    check(code == 0, 'a skip must not fail the gate')
    check('SKIPPED: web sheet: not checked out here' in out,
          f'skips must always print, even on a passing run: {out!r}')


def test_shared_error_list_is_adopted():
    """validate_flaw_effects reuses validate_quality_effects' checkers, which append to that
    module's own list. Binding it must make those errors count here."""
    shared = []
    report = Report('gate', errors=shared)
    shared.append('an error raised by a shared checker')
    code, out = run(report)
    check(code == 1, f'errors appended to the bound list must fail the gate, got {code}')
    check('an error raised by a shared checker' in out, 'bound errors must be printed')
    check(report.errors is shared, 'the bound list must be the same object, not a copy')


def test_paths_resolve():
    check(BACKEND.name == 'Backend', f'BACKEND resolved to {BACKEND}')
    check((REPO / 'CLAUDE.md').exists(), f'REPO resolved to {REPO}, which has no CLAUDE.md')
    check(JSON_DIR.is_dir(), f'JSON_DIR resolved to {JSON_DIR}, which is not a directory')
    check(SCRIPTS.is_dir(), f'SCRIPTS resolved to {SCRIPTS}, which is not a directory')
    check((DATA_DIR / 'Metzofitz_Feats.csv').is_file(),
          f'DATA_DIR resolved to {DATA_DIR}, which has no Metzofitz_Feats.csv')
    check((GOLDEN_DIR / 'caster.json').is_file(),
          f'GOLDEN_DIR resolved to {GOLDEN_DIR}, which has no caster.json')


def test_root_is_found_by_marker_not_by_depth():
    """The whole point of `_find_repo_root`: `Backend/scripts/` is about to become
    `Backend/scripts/gates/`, and a root computed as `parents[2]` would then silently resolve one
    directory too shallow -- reading real-but-wrong files rather than failing."""
    from pathlib import Path
    for start in (REPO, BACKEND, SCRIPTS, SCRIPTS / 'golden',
                  BACKEND / 'utils' / 'class_func'):
        check(_find_repo_root(Path(start)) == REPO,
              f'root from {start} resolved to {_find_repo_root(Path(start))}, expected {REPO}')

    # ...and it must refuse rather than guess when there is no repo above it.
    try:
        _find_repo_root(Path(REPO.anchor))
    except SystemExit as exc:
        check('could not find the repo root' in str(exc),
              f'a rootless start must say so, got {exc!r}')
    else:
        check(False, '_find_repo_root outside any repo must raise SystemExit, not return a guess')


def test_read_json_names_the_file():
    try:
        read_json(JSON_DIR / 'does_not_exist_at_all.json')
    except SystemExit as exc:
        check('does_not_exist_at_all.json' in str(exc),
              f'a missing file must be named in the error, got {exc!r}')
    else:
        check(False, 'read_json on a missing file must raise SystemExit')


def test_import_puts_backend_on_path():
    check(str(BACKEND) in sys.path, 'importing _harness must make utils.* importable')


def main():
    for test in (test_clean_report_passes,
                 test_error_fails_and_prints,
                 test_max_errors_truncates_but_still_counts,
                 test_no_cap_shows_everything,
                 test_check_returns_condition,
                 test_warnings_are_not_fatal,
                 test_skips_print_even_when_clean,
                 test_shared_error_list_is_adopted,
                 test_paths_resolve,
                 test_root_is_found_by_marker_not_by_depth,
                 test_read_json_names_the_file,
                 test_import_puts_backend_on_path):
        test()

    if FAILURES:
        for failure in FAILURES:
            print(failure)
        print(f'\nFAIL -- {len(FAILURES)} of {CHECKS[0]} checks failed')
        return 1
    print(f'PASS -- {CHECKS[0]} checks')
    return 0


if __name__ == '__main__':
    sys.exit(main())
