"""Regression checks for the pipeline phase contracts (run directly; this repo has no pytest
harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    .venv/Scripts/python.exe Backend/scripts/tests/test_pipeline_phases.py

The point of utils/class_func/pipeline.py is that an ordering mistake RAISES instead of silently
producing a worse character. A guard that never fires is worth nothing, so these tests deliberately
violate each contract and assert the error, then assert the correct order is accepted.

The four ordering hazards these protect (each was previously only a comment in main_test.py):
  * stats must run after randomize_level -- inherents and level-up bumps scale off total level
  * profession_chooser must run before skills_selector -- the Always Improving gate reads
    character.profession_feats
  * the class-features bucket must be finished before the bonus-spell lookups read it
  * a phase that stops setting what it declares is caught at its own boundary
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report  # noqa: E402

from utils.class_func.pipeline import (  # noqa: E402
    PhaseOrderError, phase, seal, is_sealed, require_sealed)

REPORT = Report('test_pipeline_phases')


def check(label, condition):
    if condition:
        print(f'  ok    {label}')
    else:
        print(f'  FAIL  {label}')
    REPORT.check(condition, label)


def raises(label, func, *args, **kwargs):
    """Assert func raises PhaseOrderError, and that the message names the missing thing."""
    try:
        func(*args, **kwargs)
    except PhaseOrderError as exc:
        print(f'  ok    {label}  -> {exc}')
        return str(exc)
    except Exception as exc:                                   # noqa: BLE001 - report the wrong type
        check(f'{label} (raised {type(exc).__name__}, expected PhaseOrderError)', False)
        return ''
    check(f'{label} (did not raise)', False)
    return ''


class Stub:
    """Minimal stand-in: the contract only looks at attribute presence."""


# --------------------------------------------------------------------------------------------- #

def test_requires_missing_raises():
    @phase(requires=['level'], provides=[])
    def needs_level(character):
        return 'ran'

    msg = raises('a phase missing its requirement raises', needs_level, Stub())
    check('the error names the phase', 'needs_level' in msg)
    check('the error names the missing attribute', 'level' in msg)

    ok = Stub()
    ok.level = 12
    check('the same phase runs once the requirement is set', needs_level(ok) == 'ran')


def test_falsy_requirement_counts_as_set():
    """A level of 0 or an empty list is SET. The check is 'has this phase run', not 'is it truthy' --
    testing truthiness would make a legitimately-empty value look like a missing one."""
    @phase(requires=['classes', 'bab_total'], provides=[])
    def needs_both(character):
        return 'ran'

    stub = Stub()
    stub.classes = []
    stub.bab_total = 0
    check('falsy-but-set attributes satisfy requires', needs_both(stub) == 'ran')


def test_provides_is_checked_on_exit():
    @phase(requires=[], provides=['skill_rank_budget'])
    def forgets_to_set(character):
        return 'ran'

    msg = raises('a phase that does not set what it provides raises', forgets_to_set, Stub())
    check('the exit error names the attribute', 'skill_rank_budget' in msg)

    @phase(requires=[], provides=['skill_rank_budget'])
    def sets_it(character):
        character.skill_rank_budget = 264
        return 'ran'

    check('a phase that sets what it provides passes', sets_it(Stub()) == 'ran')


def test_sealing():
    stub = Stub()
    check('a bucket starts unsealed', not is_sealed(stub, 'class features'))
    raises('reading an unsealed bucket raises', require_sealed, stub, 'class features', 'a reader')
    seal(stub, 'class features')
    check('the bucket reads as sealed after seal()', is_sealed(stub, 'class features'))
    require_sealed(stub, 'class features', 'a reader')          # must not raise
    check('reading a sealed bucket is allowed', True)
    check('sealing one bucket does not seal another', not is_sealed(stub, 'spellbooks'))


def test_real_phases_declare_their_hazards():
    """The two extracted phases must actually carry the contracts, not just be plain functions --
    otherwise the guard silently disappears the next time someone edits main_test."""
    import main_test

    stats_phase = main_test.phase_roll_and_assign_stats
    check('stats phase requires level (inherents scale off total level)',
          'level' in getattr(stats_phase, 'requires', ()))
    check('stats phase requires chosen_race (racial stat table)',
          'chosen_race' in getattr(stats_phase, 'requires', ()))

    prof_phase = main_test.phase_professions_and_skills
    check('professions phase provides profession_feats (the Always Improving gate)',
          'profession_feats' in getattr(prof_phase, 'provides', ()))
    check('professions phase provides skill_rank_budget',
          'skill_rank_budget' in getattr(prof_phase, 'provides', ()))

    # The real hazard: running the stats phase before randomize_level has set `level`.
    raises('the real stats phase raises when run before level exists',
           stats_phase, Stub(), '4', '6', 'Y')


def main():
    for test in (test_requires_missing_raises,
                 test_falsy_requirement_counts_as_set,
                 test_provides_is_checked_on_exit,
                 test_sealing,
                 test_real_phases_declare_their_hazards):
        print(f'{test.__name__}:')
        test()

    print()
    return REPORT.finish('phase contracts enforced')


if __name__ == '__main__':
    sys.exit(main())
