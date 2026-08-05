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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import Report  # noqa: E402

from utils.class_func import buff_match as bm  # noqa: E402

REPORT = Report('test_buff_match')


def check(condition, message):
    return REPORT.check(condition, message)


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



# --------------------------------------------------------------------------------------------- #
# clean_bonus_spells -- canonical spell naming for domain/bloodline/school bonus spells
# --------------------------------------------------------------------------------------------- #
def test_bonus_spell_names_resolve_to_canon():
    """The scraped pools store these loosely and str.title() shipped 180 wrong names. Every case
    below must land on the exact spells.csv spelling, because the FoundryVTT module resolves a spell
    by NAME against every_spell.json -- a wrong name renders a synthesized stand-in, not the spell."""
    import pandas as pd
    from utils.paths import repo_path
    from utils.class_func.adding_bonus_spells import clean_bonus_spells

    csv_names = {str(n) for n in pd.read_csv(repo_path('data/spells.csv'), sep='|')['name'].dropna()}
    cases = {
        # apostrophe stripped in the source data
        'orders wrath': "Order's Wrath",
        'heroes feast': "Heroes' Feast",
        'bulls strength': "Bull's Strength",
        # str.title() used to uppercase after the apostrophe
        "bull's strength (5th)": "Bull's Strength",
        "summon nature's ally IV": "Summon Nature's Ally IV",
        # str.title() used to destroy Roman numerals
        'beast shape III': 'Beast Shape III',
        'elemental body iv': 'Elemental Body IV',
        # Paizo lowercases connecting words
        'breath of life': 'Breath of Life',
        'find the path': 'Find the Path',
        # qualifier written parenthesized by the pool, comma-suffixed by the CSV
        'command (greater)': 'Command, Greater',
        'cure critical wounds (mass)': 'Cure Critical Wounds, Mass',
        'confusion (lesser)': 'Confusion, Lesser',
        # ... or written as a prefix by the pool
        'greater command': 'Command, Greater',
        'mass fly': 'Fly, Mass',
        # descriptive parenthetical is a domain restriction, not part of the name
        'animal shapes (birds only)': 'Animal Shapes',
        # source tags and modified-spell asterisks
        'frightful aspectUC (17th)': 'Frightful Aspect',
        'burning hands* (3rd)': 'Burning Hands',
    }
    for stored, want in cases.items():
        got = clean_bonus_spells(stored)
        check(got == want, f'clean_bonus_spells({stored!r}) -> {got!r}, expected {want!r}')
        check(got in csv_names, f'clean_bonus_spells({stored!r}) -> {got!r}, absent from spells.csv')


def test_qualifier_never_degrades_to_the_base_spell():
    """Cure Critical Wounds, Mass is 8th level; Cure Critical Wounds is 4th. If the comma form
    cannot be resolved the name must fall back to safe casing, NEVER to the weaker base spell."""
    from utils.class_func.adding_bonus_spells import clean_bonus_spells
    for stored, forbidden in (('command (greater)', 'Command'),
                              ('cure critical wounds (mass)', 'Cure Critical Wounds'),
                              ('fly (mass)', 'Fly')):
        got = clean_bonus_spells(stored)
        check(got != forbidden,
              f'{stored!r} degraded to the base spell {forbidden!r} -- a different, weaker spell')


def test_unknown_spell_falls_back_safely():
    from utils.class_func.adding_bonus_spells import clean_bonus_spells
    got = clean_bonus_spells('a totally invented spell of the void')
    check(got == 'A Totally Invented Spell of the Void', f'bad fallback casing: {got!r}')


def main():
    for test in (test_feat_shape, test_class_feature_shape, test_bare_list_and_empties,
                 test_tier_is_case_and_space_insensitive, test_match_finds_a_real_curated_name,
                 test_uncurated_name_is_not_a_gap, test_punctuation_mismatch_is_a_gap,
                 test_unknown_kind_and_missing_section_raise,
                 test_bonus_spell_names_resolve_to_canon,
                 test_qualifier_never_degrades_to_the_base_spell,
                 test_unknown_spell_falls_back_safely):
        test()

    return REPORT.finish(f'{REPORT.checks} checks')


if __name__ == '__main__':
    sys.exit(main())
