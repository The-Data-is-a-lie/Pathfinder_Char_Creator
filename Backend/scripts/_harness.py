"""Shared scaffolding for the Backend/scripts gates.

WHY THIS EXISTS
---------------
Nineteen `validate_*.py` and twelve `test_*.py` scripts each hand-rolled the same four things: an
error list, a warning list, a pass/fail print, and an exit code. That is roughly a third of every
file, and it had already drifted -- the same failing run printed `FAILED: N problem(s)`,
`FAILED: N problem(s) across N modifier(s)` and `FAILED -- N problems` depending on which gate
tripped, so "did it fail?" could not be answered by looking at the output shape.

The drift is the mild symptom. The real cost is that a new data file's gate opened with ~40 lines
of ceremony before its first actual rule, which is the tax that makes a validator feel expensive
enough to skip -- and `validate_all.py` exists precisely because eleven of them had been skipped.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
No argparse. The flags in this directory are genuinely per-gate (`--print`, `--review`, `--runs`,
`--strict`, `--compendium`, `--module-root`), and a shared parser would either accept all of them
everywhere or grow a registration API bigger than the parsers it replaced. `validate_all.py` owns
`--list`/`--skip`/`--quiet` because those are ITS flags, not every validator's.

No pytest. The standalone-script convention here is deliberate and documented
(`test_golden_payload.py`); this is a harness for that convention, not a migration away from it.

USAGE
-----
    from _harness import Report

    report = Report('validate_flaw_effects')
    report.check(entry.get('description'), f'{owner}: missing description')
    report.warn(f'{owner}: duplicate name')
    report.skip('web sheet: not checked out here')
    sys.exit(report.finish(f'{n} entries validated'))

Importing this module also puts `Backend/` and `Backend/scripts/` on `sys.path`, so a gate can
`from utils.class_func.companion_stats import MODIFIER_TARGETS` without repeating the three-line
path dance. Importing the owner of a rule is how this repo avoids restating it; that should not
cost boilerplate.

It also exports the four directories a gate actually needs -- `REPO`, `BACKEND`, `JSON_DIR`,
`DATA_DIR`, `GOLDEN_DIR` -- resolved by searching upward for the repo's markers rather than by
counting parent directories. See `_find_repo_root`.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find_repo_root(start):
    """Walk up from ``start`` until a directory carrying the repo's markers turns up.

    Deliberately NOT ``HERE.parent.parent``. Thirty-odd gates each recomputed the root from their
    own nesting depth (`parents[1]`, `parents[2]`), which means the directory layout is encoded
    thirty times and moving a script one level down breaks it thirty times -- silently, because a
    wrong-but-existing path just reads the wrong file. Anchoring on a marker instead makes depth a
    non-fact: `Backend/scripts/gates/validate_x.py` resolves the same root as
    `Backend/scripts/validate_x.py` did before the bucket split.

    Both markers are required together. `.git` alone would resolve to the wrong repo when this one
    is vendored or a worktree is nested; `CLAUDE.md` alone appears in other checkouts on this
    machine.
    """
    for candidate in (start, *start.parents):
        if (candidate / 'CLAUDE.md').is_file() and (candidate / '.git').exists():
            return candidate
    raise SystemExit(
        f'{__file__}: could not find the repo root above {start} -- no ancestor has both '
        'CLAUDE.md and .git. Is this file outside the repository?')


REPO = _find_repo_root(HERE)
BACKEND = REPO / 'Backend'
JSON_DIR = BACKEND / 'json'
DATA_DIR = REPO / 'data'
GOLDEN_DIR = BACKEND / 'scripts' / 'golden'

SCRIPTS = BACKEND / 'scripts'

GATES = SCRIPTS / 'gates'
TESTS = SCRIPTS / 'tests'
BUILD = SCRIPTS / 'build'
ATTIC = SCRIPTS / 'attic'

# So `import validate_quality_effects` (sibling gates own the shared whitelists) and
# `from utils import data` both work from any working directory. `SCRIPTS` is listed separately
# from `HERE` because they stop being the same directory the moment gates move into a subfolder --
# a gate in `scripts/gates/` still imports its shared checkers from `scripts/`.
#
# Every bucket is on the path because scripts are ALSO libraries and are imported ACROSS buckets:
# `validate_quality_effects` exports its whitelist and bracket checker to three other gates,
# `validate_talent_conditionals.is_cost_only` to five callers including
# `tests/test_talent_conditionals.py`, `build_item_changes` to `build_class_feature_changes` and
# `build_spell_buffs`, `reconcile_psionics_names` to four builders -- and `build_companion_archetypes`
# reaches into `attic/repair_animal_choices`, which is the one edge that says the attic is not yet
# archaeology. Ticket 03 chose not to extract any of them into a lib/ first, on the grounds that
# separating a rule from its only enforcement is the arrangement this whole effort is undoing -- so
# the buckets have to stay mutually importable, and this is the single place that is arranged.
# Adding a bucket means adding it here and nowhere else.
for _entry in (str(HERE), str(SCRIPTS), str(GATES), str(TESTS), str(BUILD), str(ATTIC), str(BACKEND)):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)


class Report:
    """Accumulates findings, then prints them and yields an exit code.

    Three severities, and the difference between them is what the runner does about it:

    - **error**  -> printed, counted, exit 1. The gate failed.
    - **warn**   -> printed as `WARN:`, counted, exit 0. Real but not fatal -- Sojoria's surname
      list legitimately repeats names, and failing on that would mean 90 false failures and a
      validator nobody runs.
    - **skip**   -> printed as `SKIPPED:`, exit 0. A check that could not run at all, usually
      because a cross-repo client is not checked out on this machine. Kept separate from `warn`
      on purpose: a check that quietly stops running is the exact failure this directory exists
      to prevent, so it is always printed even when everything passed.

    ``errors`` may be an existing list, which is how a gate joins the accumulator that shared
    checkers already write to -- `validate_quality_effects.check_brackets` appends to its own
    module-level list, and `validate_flaw_effects` reuses that checker rather than copying it.
    """

    def __init__(self, name, errors=None, warnings=None):
        self.name = name
        self.errors = errors if errors is not None else []
        self.warnings = warnings if warnings is not None else []
        self.skipped = []
        self.checks = 0

    def check(self, condition, message):
        """Record an error unless ``condition`` holds. Returns the condition as a bool, so a
        caller can stop descending into something it just proved malformed."""
        self.checks += 1
        if not condition:
            self.errors.append(message)
            return False
        return True

    def error(self, message):
        """Record a failure that wasn't phrased as a condition."""
        self.checks += 1
        self.errors.append(message)
        return False

    def warn(self, message):
        self.warnings.append(message)

    def skip(self, message):
        self.skipped.append(message)

    def finish(self, summary='', max_errors=None):
        """Print everything collected and return the process exit code (0 pass, 1 fail).

        Callers do `sys.exit(report.finish(...))` rather than having this raise, so a gate that
        wants to do something after reporting still can.

        ``max_errors`` caps the printed list and says how many were withheld. The sweeps want it --
        one bad rule in `apply_modifiers` can fail all 392 species stat blocks at once, and 392
        near-identical lines bury the count that actually tells you what happened. It is opt-in
        because for a gate that normally reports a handful, a truncated list would hide work.
        """
        for message in self.skipped:
            print(f'SKIPPED: {message}')
        for message in self.warnings:
            print(f'WARN: {message}')
        if self.errors:
            shown = self.errors if max_errors is None else self.errors[:max_errors]
            print()
            for message in shown:
                print(f'  {message}')
            withheld = len(self.errors) - len(shown)
            if withheld:
                print(f'  ... and {withheld} more')
            print(f'\nFAILED: {len(self.errors)} problem(s)')
            return 1
        tail = f' ({len(self.warnings)} warning(s))' if self.warnings else ''
        print(f'OK: {summary or self.name}{tail}.')
        return 0


def choice_schedule():
    """Backend/json/class_choice_schedule.json, read straight from disk.

    Deliberately NOT `generic_func.levels_for` (class-choices ticket 01). A check that asked the
    generator to expand its own schedule would compare the generator with itself and confirm
    nothing -- the same trap scripts-ticket 12 named when it refused to derive the caster gate
    from the tables it was gating. So the expansion below is a SECOND implementation, and the
    checks that use it assert generated characters against the table rather than against code.
    """
    return read_json(JSON_DIR / 'class_choice_schedule.json').get('classes', {})


def schedule_levels(table, class_name, bucket, class_level):
    """The class levels at which `class_name` gains a pick in `bucket`, up to `class_level`.

    Returns None when the bucket has no row, which callers must distinguish from an empty list:
    "no schedule" means a single pick at 1st for the psionic/occult single-pick subsystems, while
    [] means "scheduled, but nothing due yet at this level".
    """
    row = (table.get(class_name) or {}).get('buckets', {}).get(bucket)
    if not row:
        return None
    if 'levels' in row:
        return [lvl for lvl in row['levels'] if lvl <= class_level]
    ceiling = min(class_level, row.get('until', class_level))
    return list(range(row['start'], ceiling + 1, row['every']))


def read_json(path):
    """Parse a UTF-8 JSON file, naming the file in the error when it does not parse.

    A bare `json.load` failure reports a line and column against an unnamed stream, which is
    useless when a gate reads four files.
    """
    path = Path(path)
    try:
        with open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f'{path}: not valid JSON -- {exc}') from exc
    except FileNotFoundError as exc:
        raise SystemExit(f'{path}: not found') from exc
