"""Standalone regression checks for gold spending and the inherents flag (run directly; this repo has
no pytest harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    C:\\Python310\\python.exe Backend/scripts/test_gold_and_stats.py
    C:\\Python310\\python.exe Backend/scripts/test_gold_and_stats.py --slow   # + one full generation

Guards two bugs:
  * characters bought items/enhancements they couldn't afford and finished with NEGATIVE gold
    (item_chooser subtracted before checking and then abandoned the rest of the batch;
    enhancement_calculator picked the price tier CLOSEST to its budget, i.e. the one just above it)
  * inherents="N" never assigned character.inherents, crashing payload assembly with AttributeError
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BACKEND = HERE.parents[1]
sys.path.insert(0, str(BACKEND))   # so `from utils...` resolves

from utils import data
from utils.class_func import item_and_price as ip
from utils.class_func.armor_and_enhancements import enhancement_calculator
from utils.class_func.stats import roll_stats

FAILURES = []
CHECKS = [0]


def check(condition, message):
    CHECKS[0] += 1
    if not condition:
        FAILURES.append(message)


class GoldCharacter:
    """The slice of createACharacter.Character that item_chooser / enhancement_calculator read."""

    def __init__(self, gold, items):
        self.gold = gold
        self.items = items


def _items(spec):
    """{slot: {item name: price}} -> the character.items shape item_chooser expects."""
    return {slot: {name: {'price': str(price), 'description': ''}
                   for name, price in entries.items()}
            for slot, entries in spec.items()}


# --------------------------------------------------------------------------------------------
# 1. item_chooser: never overspends, skips what it can't afford, keeps going.
# --------------------------------------------------------------------------------------------
def test_item_chooser_never_goes_negative():
    # 'expensive' cannot be afforded at any point; 'cheap' slots must still be bought AFTER it,
    # which is what proves the loop continues instead of breaking out.
    # NB: keep every price >= 11 -- adjust_price() treats a price under 11 as a "+N" enhancement tier
    # and rewrites it to (N**2)*1000, so a nominal 10 gp item really costs 100,000.
    spec = {
        'cheap_a':   {'Cheap A': 15},
        'expensive': {'Ruinous Thing': 999999},
        'cheap_b':   {'Cheap B': 20},
        'cheap_c':   {'Cheap C': 30},
    }
    names = [n for entries in spec.values() for n in entries]
    character = GoldCharacter(100, _items(spec))
    equipment_list, equip_dict = ip.item_chooser(character, names)

    check(character.gold >= 0, f"gold went negative: {character.gold}")
    check(character.gold == 100 - (15 + 20 + 30),
          f"expected 35 gold left (100 - 65 of affordable gear), got {character.gold}")
    check('Ruinous Thing' not in equipment_list,
          "an unaffordable item was added to the equipment list")
    check(len(equipment_list) == 3,
          f"the batch stopped early -- expected the 3 affordable items, got {equipment_list}")
    check('cheap_c' in equip_dict,
          "slots after the unaffordable one were skipped (loop broke instead of continuing)")


def test_item_chooser_pays_for_everything_it_lists():
    spec = {f'slot{i}': {f'Item {i}': (i + 1) * 25} for i in range(8)}
    names = [n for entries in spec.values() for n in entries]
    start = 300
    character = GoldCharacter(start, _items(spec))
    equipment_list, _ = ip.item_chooser(character, names)

    # every listed item was paid for, and nothing was paid for that wasn't listed
    prices = {f'Item {i}': (i + 1) * 25 for i in range(8)}
    spent = sum(prices[name] for name in equipment_list)
    check(character.gold >= 0, f"gold went negative: {character.gold}")
    check(start - spent == character.gold,
          f"ledger mismatch: started {start}, listed items cost {spent}, ended {character.gold}")


def test_item_chooser_broke_character():
    spec = {'a': {'A': 500}, 'b': {'B': 600}}
    names = ['A', 'B']
    character = GoldCharacter(0, _items(spec))
    equipment_list, _ = ip.item_chooser(character, names)
    check(character.gold == 0, f"a broke character's gold moved: {character.gold}")
    check(equipment_list == [], f"a broke character bought something: {equipment_list}")


# --------------------------------------------------------------------------------------------
# 2. enhancement_calculator: largest AFFORDABLE tier, never a negative purse.
# --------------------------------------------------------------------------------------------
def test_enhancement_never_goes_negative():
    mapping = data.enhancement_bonus_mapping
    cheapest = min(mapping)
    for gold in (0, 1, 500, 1999, 2000, 5999, 6000, 50000, 500000, 1000000):
        for divisor in (3, 2, 1):
            character = GoldCharacter(gold, {})
            bonus = enhancement_calculator(character, divisor)
            check(character.gold >= 0,
                  f"gold {gold} / divisor {divisor}: went negative ({character.gold})")
            check(character.gold <= gold,
                  f"gold {gold} / divisor {divisor}: gold increased to {character.gold}")
            budget = gold // divisor
            expected_keys = [k for k in mapping if k <= budget]
            want = mapping[max(expected_keys)] if expected_keys else 0
            check(bonus == want,
                  f"gold {gold} / divisor {divisor}: expected +{want}, got +{bonus}")
            if budget < cheapest:
                check(character.gold == gold,
                      f"gold {gold} / divisor {divisor}: spent {gold - character.gold} on nothing")


def test_enhancement_three_slots_in_sequence():
    """The real call pattern: armor (3), weapon (2), shield (1) off the same shrinking purse."""
    for gold in (0, 750, 3000, 25000, 400000):
        character = GoldCharacter(gold, {})
        for divisor in (3, 2, 1):
            enhancement_calculator(character, divisor)
            check(character.gold >= 0,
                  f"starting gold {gold}: negative after divisor {divisor} ({character.gold})")


# --------------------------------------------------------------------------------------------
# 3. inherents="N" leaves a usable, zeroed dict instead of an unset attribute.
# --------------------------------------------------------------------------------------------
ABILITIES = {'str', 'dex', 'con', 'int', 'wis', 'cha'}


class StatCharacter:
    """The slice of Character that roll_stats reads (it rolls the ability scores itself)."""

    def __init__(self, level=5):
        self.level = level
        self.classes = [{'name': 'fighter', 'level': level}]
        self.c_class = 'fighter'
        self.class_data = {'fighter': {'main_stat': 'str'}}


def test_inherents_disabled():
    character = StatCharacter()
    stats = roll_stats(character, 4, 6, 'n')

    check(hasattr(character, 'inherents'),
          "inherents='n' left character.inherents unset (this is the AttributeError at export)")
    check(isinstance(character.inherents, dict),
          f"inherents should be a dict, got {type(character.inherents).__name__}")
    check(set(character.inherents) == ABILITIES,
          f"inherents dict has the wrong shape: {character.inherents}")
    check(all(v == 0 for v in character.inherents.values()),
          f"inherents disabled but non-zero: {character.inherents}")
    check(isinstance(getattr(character, 'level_up_stats', None), dict),
          "level_up_stats missing after roll_stats")
    check(stats is not None and set(stats) == ABILITIES, f"roll_stats returned {stats!r}")


def test_inherents_enabled_still_works():
    character = StatCharacter(level=20)
    roll_stats(character, 4, 6, 'y')
    check(isinstance(character.inherents, dict) and set(character.inherents) == ABILITIES,
          f"inherents enabled produced a bad dict: {character.inherents}")
    check(all(0 <= v <= 10 for v in character.inherents.values()),
          f"inherent bonus outside the 0-10 per-stat cap: {character.inherents}")


def test_fresh_character_has_stat_dicts():
    """__init__ must publish both dicts so nothing can read them before roll_stats runs."""
    from utils.createACharacter import Character
    blank = Character({})   # json_config: paths dict, unused by the field initialisation
    check(isinstance(getattr(blank, 'inherents', None), dict),
          "a fresh Character has no inherents dict")
    check(isinstance(getattr(blank, 'level_up_stats', None), dict),
          "a fresh Character has no level_up_stats dict")


# --------------------------------------------------------------------------------------------
# 4. Optional end-to-end: --slow generates a real character with inherents off and a small purse.
# --------------------------------------------------------------------------------------------
def test_end_to_end():
    from main_test import generate_random_char
    payload = generate_random_char(class_choice='fighter', multi_class='N', high_level=5, low_level=5,
                                   userInput_race='Human', truly_random_feats="Y",
                                   use_backstory_api="N", inherents="N", gold_num=300)
    check(payload is not None, "generate_random_char returned nothing with inherents='N'")
    check(isinstance(payload.get('inherents'), dict),
          f"payload inherents is {payload.get('inherents')!r}")
    check(float(payload.get('gold', -1)) >= 0, f"payload gold is negative: {payload.get('gold')}")
    check(float(payload.get('platnium', -1)) >= 0,
          f"payload platinum is negative: {payload.get('platnium')}")


def main():
    tests = [test_item_chooser_never_goes_negative, test_item_chooser_pays_for_everything_it_lists,
             test_item_chooser_broke_character, test_enhancement_never_goes_negative,
             test_enhancement_three_slots_in_sequence, test_inherents_disabled,
             test_inherents_enabled_still_works, test_fresh_character_has_stat_dicts]
    if '--slow' in sys.argv:
        tests.append(test_end_to_end)

    for test in tests:
        test()

    print()
    if FAILURES:
        print(f"FAIL -- {len(FAILURES)} of {CHECKS[0]} checks failed:")
        for message in FAILURES:
            print("  *", message)
        return 1
    print(f"PASS -- {CHECKS[0]} checks" + ("" if '--slow' in sys.argv else "  (add --slow for the end-to-end run)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
