"""Regression checks for utils/loot.py -- the encounter-treasure endpoint's engine (sheet #81).

    C:\\Python310\\python.exe Backend/scripts/tests/test_loot.py

The failure modes worth gating are all about money, and this repo has been burned by every one of
them before:

  * **A parcel must never exceed its budget.** The fill subtracts as it goes, and a single
    off-by-one in the affordability test hands a CR 1 encounter a CR 10 payday.
  * **An unpriceable item must be skipped, not freed.** `convert_price` returns None for a blob it
    cannot read; the windfall that `item_and_price`'s header documents came from reading that as 0.
  * **Mundane costs must not go through `convert_price`.** Its `adjust_price` reads any int under 11
    as a +N enhancement bonus (N^2 x 1000), so a 2 gp dagger would price at 4,000 gp and a low-CR
    parcel would be one absurd knife.
  * **The two gp curves must stay apart.** `treasure_value` (per encounter) is not
    `data.wealth_by_level` (per character, cumulative); if they ever agree at a level, someone has
    crossed them.
  * **A seed must reproduce a parcel exactly**, because that is the only handle a GM has on a roll
    they liked.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils import loot  # noqa: E402
from utils import data as gamedata  # noqa: E402

REPORT = Report('test_loot')


def check(condition, message):
    return REPORT.check(condition, message)


def parcel_value(parcel):
    """What the parcel is really worth, recomputed from its parts rather than trusting `value`."""
    coins = parcel['coins']
    total = coins['pp'] * 10 + coins['gp'] + coins['sp'] / 10 + coins['cp'] / 100
    total += sum(g['value'] for g in parcel['gems'])
    total += sum(i['price'] for i in parcel['items'])
    return total


# --------------------------------------------------------------------------------------------- #
# the curve
# --------------------------------------------------------------------------------------------- #
def test_table_is_complete_and_monotonic():
    for cr in range(loot.MIN_CR, loot.MAX_CR + 1):
        check(cr in loot.TREASURE_PER_ENCOUNTER, f'CR {cr} missing from the treasure table')
    for cr in range(loot.MIN_CR + 1, loot.MAX_CR + 1):
        for idx, speed in enumerate(loot.SPEEDS):
            lo = loot.TREASURE_PER_ENCOUNTER[cr - 1][idx]
            hi = loot.TREASURE_PER_ENCOUNTER[cr][idx]
            check(hi > lo, f'{speed} treasure does not rise from CR {cr - 1} ({lo}) to {cr} ({hi})')
    for cr, row in loot.TREASURE_PER_ENCOUNTER.items():
        check(row[0] < row[1] < row[2], f'CR {cr} speeds are not slow < medium < fast: {row}')


def test_tail_extrapolates_instead_of_raising():
    at20 = loot.treasure_value(20, 'medium')
    at21 = loot.treasure_value(21, 'medium')
    check(at21 > at20, f'CR 21 ({at21}) is not above CR 20 ({at20})')
    check(loot.treasure_value(0, 'medium') == loot.treasure_value(1, 'medium'),
          'CR 0 should clamp to CR 1, not raise or return 0')
    check(loot.treasure_value(5, 'nonsense') == loot.treasure_value(5, 'medium'),
          'an unknown speed should fall back to medium')


def test_encounter_curve_is_not_the_wealth_curve():
    """The one mix-up that would silently make every parcel wrong by an order of magnitude."""
    for level in (1, 5, 10, 15, 20):
        encounter = loot.treasure_value(level, 'medium')
        career = gamedata.wealth_by_level(level)
        check(encounter != career,
              f'per-encounter treasure at CR {level} equals wealth-by-level ({encounter}) -- '
              'the two curves have been crossed')
        # Level 1 is legitimately inverted and must stay excluded: Paizo gives a CR 1 encounter
        # 260 gp (medium) while a level-1 PC starts on class wealth (150 gp here). One good fight
        # really is worth more than everything a first-level character owns.
        if level > 1:
            check(encounter < career,
                  f'one CR {level} encounter ({encounter}) is worth more than a whole '
                  f'level-{level} career ({career})')


# --------------------------------------------------------------------------------------------- #
# the pool
# --------------------------------------------------------------------------------------------- #
def test_pool_is_priced_and_sane():
    pool = loot._pool()
    check(len(pool) > 200, f'item pool is only {len(pool)} entries -- a source stopped loading')
    check(all(isinstance(i['price'], (int, float)) and i['price'] > 0 for i in pool),
          'an item in the pool has a non-positive or non-numeric price')
    names = [i['name'] for i in pool]
    check(len(names) == len(set(names)), 'the pool contains duplicate names')
    kinds = {i['kind'] for i in pool}
    check('magic' in kinds, 'no magic items in the pool')
    check(kinds & {'weapon', 'armor'}, 'no mundane weapons or armor in the pool')


def test_mundane_prices_are_not_read_as_enhancement_bonuses():
    check(loot._mundane_price('2 gp') == 2, 'a 2 gp item did not price at 2 gp')
    check(loot._mundane_price('15 gp') == 15, 'a 15 gp item did not price at 15 gp')
    check(loot._mundane_price('1 sp') == 0.1, 'silver prices are not converted to gp')
    check(loot._mundane_price('5 cp') == 0.05, 'copper prices are not converted to gp')
    check(loot._mundane_price('1,500 gp') == 1500, 'thousands separators break mundane pricing')
    check(loot._mundane_price('') is None and loot._mundane_price('see text') is None,
          'an unreadable cost must be None (unbuyable), never 0 (free)')
    # The exact trap: convert_price would answer 4000 for this, being a +2 bonus in its world.
    from utils.class_func.item_and_price import convert_price
    check(convert_price(None, '2', 'dagger') != loot._mundane_price('2 gp'),
          'the mundane parser has started agreeing with convert_price on small integers -- one of '
          'them is now wrong for its own dataset')


# --------------------------------------------------------------------------------------------- #
# the parcel
# --------------------------------------------------------------------------------------------- #
def test_every_cr_and_speed_produces_something_within_budget():
    for cr in range(1, 21):
        for speed in loot.SPEEDS:
            parcel = loot.generate_loot(cr, speed, seed=cr * 100 + len(speed))
            budget = parcel['budget']
            actual = parcel_value(parcel)
            check(actual <= budget + 1,
                  f'CR {cr} {speed}: parcel is worth {actual} against a {budget} budget')
            # A parcel that hands back a tenth of the budget is a fill that gave up.
            check(actual >= budget * 0.9,
                  f'CR {cr} {speed}: parcel is worth only {actual} of a {budget} budget')
            check(abs(parcel['value'] - actual) <= 1,
                  f"CR {cr} {speed}: reported value {parcel['value']} != recomputed {actual}")
            check(parcel['coins']['gp'] >= 0 and parcel['coins']['pp'] >= 0,
                  f'CR {cr} {speed}: negative coins {parcel["coins"]}')


def test_items_are_unique_and_named():
    for cr in (1, 6, 12, 20):
        parcel = loot.generate_loot(cr, 'medium', seed=cr)
        names = [i['name'] for i in parcel['items']]
        check(len(names) == len(set(names)),
              f'CR {cr} parcel repeats an item: {names}')
        check(all(n and n.strip() for n in names), f'CR {cr} parcel has a blank item name')
        mundane = sum(1 for i in parcel['items'] if not i['magic'])
        check(mundane <= loot.MAX_MUNDANE,
              f'CR {cr} parcel carries {mundane} mundane items, over the {loot.MAX_MUNDANE} cap')


def test_seed_reproduces_the_parcel():
    a = loot.generate_loot(9, 'fast', seed=20260814)
    b = loot.generate_loot(9, 'fast', seed=20260814)
    check(a == b, 'the same seed produced two different parcels')
    c = loot.generate_loot(9, 'fast', seed=20260815)
    check(a != c, 'two different seeds produced identical parcels')
    check(isinstance(loot.generate_loot(3, 'slow')['seed'], int),
          'a seedless call must still report the seed it rolled')


def test_capabilities_shape():
    caps = loot.capabilities()
    check(caps.get('ok') is True, 'capabilities() must report ok:true -- the sheet probes on it')
    check(list(caps.get('speeds') or []) == list(loot.SPEEDS), 'capabilities() speeds drifted')
    check(caps.get('cr') == [loot.MIN_CR, loot.MAX_CR], 'capabilities() CR range drifted')


def main():
    for test in (test_table_is_complete_and_monotonic,
                 test_tail_extrapolates_instead_of_raising,
                 test_encounter_curve_is_not_the_wealth_curve,
                 test_pool_is_priced_and_sane,
                 test_mundane_prices_are_not_read_as_enhancement_bonuses,
                 test_every_cr_and_speed_produces_something_within_budget,
                 test_items_are_unique_and_named,
                 test_seed_reproduces_the_parcel,
                 test_capabilities_shape):
        test()

    return REPORT.finish(f'{REPORT.checks} checks')


if __name__ == '__main__':
    sys.exit(main())
