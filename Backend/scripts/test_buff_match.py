"""Regression checks for utils/class_func/buff_match.py (run directly; this repo has no pytest
harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    .venv/Scripts/python.exe Backend/scripts/test_buff_match.py

Covers the two contracts that are easy to break silently:

  * keep_tier_a() must handle BOTH curated shapes -- a feat entry IS a single conditional and carries
    `tier` directly, while a class-feature entry has a `conditionals` list whose members each carry
    their own -- and must return a falsy value when nothing survives, so an all-tier-B power stays
    out of the payload entirely rather than shipping as an empty toggle.
  * match() must preserve each kind's normalization exactly, and must report a gap ONLY when curated
    data exists and the kind's rule failed to reach it -- never for the ordinary "nothing curated for
    this name", which is the common case and would drown the signal.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BACKEND = HERE.parents[1]
sys.path.insert(0, str(BACKEND))

from utils.class_func import buff_match as bm

FAILURES = []
CHECKS = [0]


def check(condition, message):
    CHECKS[0] += 1
    if not condition:
        FAILURES.append(message)


# --------------------------------------------------------------------------------------------- #
# keep_tier_a
# --------------------------------------------------------------------------------------------- #
def test_feat_shape():
    """A feat entry is one conditional carrying its own tier."""
    a = {'name': 'X', 'default': False, 'modifiers': [], 'tier': 'A'}
    b = {'name': 'Y', 'default': False, 'modifiers': [], 'tier': 'B'}
    untiered = {'name': 'Z', 'default': False, 'modifiers': []}
    check(bm.keep_tier_a(a) == a, 'tier A feat entry was dropped')
    check(not bm.keep_tier_a(b), 'tier B feat entry survived')
    check(bm.keep_tier_a(untiered) == untiered, 'untiered feat entry was dropped (absent means A)')


def test_class_feature_shape():
    """A class-feature entry carries tier per conditional, inside a list."""
    entry = {'conditionals': [
        {'name': 'keep me', 'default': False, 'modifiers': [], 'tier': 'A'},
        {'name': 'drop me', 'default': False, 'modifiers': [], 'tier': 'B'},
        {'name': 'keep me too', 'default': False, 'modifiers': []},
    ]}
    kept = bm.keep_tier_a(entry)
    names = [c['name'] for c in (kept or [])]
    check(names == ['keep me', 'keep me too'], f'wrong survivors: {names}')

    all_b = {'conditionals': [{'name': 'n', 'default': False, 'modifiers': [], 'tier': 'B'}]}
    check(not bm.keep_tier_a(all_b),
          'an all-tier-B power returned something truthy -- it would ship as an empty toggle')


def test_bare_list_and_empties():
    raw_list = [{'name': 'a', 'tier': 'A'}, {'name': 'b', 'tier': 'B'}]
    check([c['name'] for c in bm.keep_tier_a(raw_list) or []] == ['a'],
          'a bare conditionals list was not filtered')
    for empty in (None, {}, [], {'conditionals': []}):
        check(not bm.keep_tier_a(empty), f'empty input {empty!r} returned something truthy')


def test_tier_is_case_and_space_insensitive():
    check(not bm.keep_tier_a({'name': 'x', 'tier': ' b '}), "tier ' b ' was not treated as B")
    check(not bm.keep_tier_a({'name': 'x', 'tier': 'b'}), "lowercase tier 'b' was not treated as B")


# --------------------------------------------------------------------------------------------- #
# match / gaps
# --------------------------------------------------------------------------------------------- #
def test_match_finds_a_real_curated_name():
    """Round-trip a name straight out of the curated data -- it must match its own kind."""
    for kind in ('feat', 'spell_rider', 'item'):
        data = bm.raw(kind)
        names = [k for k in data if not str(k).startswith('_')]
        if not names:
            continue
        sample = names[0]
        matched, gaps = bm.match(kind, [sample])
        check(sample in matched, f'{kind}: curated name {sample!r} did not match itself')
        check(gaps == [], f'{kind}: matching a curated name reported a gap: {gaps}')


def test_uncurated_name_is_not_a_gap():
    """The common case. A gap means curated data EXISTS but the rule missed it; a name with nothing
    curated is ordinary and must stay silent or the report is useless."""
    matched, gaps = bm.match('feat', ['Zzzz Not A Real Feat Name Zzzz'])
    check(matched == {}, f'a nonexistent feat matched something: {matched}')
    check(gaps == [], f'a nonexistent feat was reported as a gap: {gaps}')


def test_punctuation_mismatch_is_a_gap():
    """The bug this exists to surface: curated "Order's Wrath" vs the generator's "Orders Wrath"."""
    riders = bm.raw('spell_rider')
    apostrophed = next((k for k in riders if "'" in str(k)), None)
    if apostrophed is None:
        return
    stripped = str(apostrophed).replace("'", "")
    matched, gaps = bm.match('spell_rider', [stripped])
    check(matched == {}, f'{stripped!r} matched strictly, so it is not a gap case')
    check(len(gaps) == 1 and gaps[0]['curated_as'] == apostrophed,
          f'{stripped!r} vs curated {apostrophed!r} was not reported as a gap: {gaps}')


def test_unknown_kind_and_missing_section_raise():
    try:
        bm.match('not_a_kind', ['x'])
        check(False, 'an unknown kind did not raise')
    except KeyError:
        check(True, '')
    try:
        bm.match('class_feature', ['x'])          # nested, section omitted
        check(False, 'a sectioned kind without section= did not raise')
    except ValueError:
        check(True, '')


def main():
    for test in (test_feat_shape, test_class_feature_shape, test_bare_list_and_empties,
                 test_tier_is_case_and_space_insensitive, test_match_finds_a_real_curated_name,
                 test_uncurated_name_is_not_a_gap, test_punctuation_mismatch_is_a_gap,
                 test_unknown_kind_and_missing_section_raise):
        test()

    if FAILURES:
        print(f'FAIL -- {len(FAILURES)} of {CHECKS[0]} checks')
        for line in FAILURES:
            print(f'  {line}')
        return 1
    print(f'PASS -- {CHECKS[0]} checks')
    return 0


if __name__ == '__main__':
    sys.exit(main())
