"""Blank mode: a blank sheet has nothing rolled on it, and is owed what a real character is.

    .venv/Scripts/python.exe Backend/scripts/tests/test_blank.py

WHAT THIS ASSERTS
-----------------
A blank sheet (utils/class_func/blank.py) is made by generating a character and emptying it, so
its two failure modes are both silent: something rolled survives the emptying, or a slot count
drifts from what the generator actually gives. Each is checked on generated sheets:

1. **Nothing rolled survives.** The same request under two seeds produces the SAME sheet, key for
   key, for every rollable class at four levels, a multiclass and a second race. A sheet is its
   request and nothing else -- whatever differs between two seeds was rolled.
2. **Nothing is chosen.** Every ability is 10, every feat / trait / spell / gear list is empty,
   and the only keys with anything in them are the ones blank.py keeps or rebuilds.
3. **The shape is the payload's.** The keys are ``payload.PAYLOAD_KEYS``, in order, and every
   ordinary generated character carries ``slots: []``.
4. **The slots are the generator's own counts.** A blank sheet has as many class bonus feat,
   teamwork feat and story feat slots as a generated character of the same class and level has
   feats in those rows, and a slot for every class choice that character made a pick in.
5. **House rules follow the request.** With the house feat economy and the misc house rules off,
   there is no story, flavor or flaw-feat slot and no flaw slot; the PF1 feats remain.

PROVEN BY BREAKING IT. The sweep ends by making ``blank._empty`` return its argument unchanged --
the emptying switched off -- and re-running check 1 against a scratch report. It must FAIL.
"""
import io
import json
import sys
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND, Report                                                # noqa: E402

sys.path.insert(0, str(BACKEND))
from utils.class_func import backstory as _bs                                       # noqa: E402
_bs.OLLAMA_AVAILABLE = False
_bs._try_ollama = lambda *a, **k: ''
import main_test                                                                    # noqa: E402
from utils.class_func import blank                                                  # noqa: E402
from utils.createACharacter import CreateNewCharacter                               # noqa: E402
from utils.payload import PAYLOAD_KEYS                                              # noqa: E402
from utils.util import _available_class_pool                                        # noqa: E402

REPORT = Report('test_blank')
SEEDS = (64001, 64002)
LEVELS = (1, 5, 10, 20)
GENERATED = [0]

# The keys blank.apply rebuilds rather than keeps or empties (blank.py::apply).
REBUILT = {'str', 'dex', 'con', 'int', 'wis', 'cha', 'inherents', 'level_up_stats', 'racial_stats',
           'classes', 'spellbooks', 'main_stat', 'character_full_name', 'total_rolled_hp', 'Total_HP',
           'sheet_health', 'feat_budget', 'slots'}
EMPTY = ([], {}, '', 0, None, False)


def generate(seed, classes, race='Human', blank_request='Y', **overrides):
    args = dict(class_choice='random', chosen_BAB='random', multi_class='N',
                userInput_race=race, userInput_region='Tal-Falko', alignment_input='random',
                userInput_gender='random', high_level=12, low_level=6, gold_num="",
                num_dice='4', num_sides='6', use_backstory_api='N', spheres_flag='N', seed=seed)
    args.update(overrides)
    GENERATED[0] += 1
    with redirect_stdout(io.StringIO()):
        return main_test.generate_random_char(selection_request={'classes': classes},
                                              blank_request=blank_request, **args)


def rollable_classes():
    return sorted(_available_class_pool(CreateNewCharacter(main_test.character_json_config)))


def requests():
    """(label, classes, race) for the sweep: every rollable class at every level, plus the two
    shapes a single class does not cover."""
    for name in rollable_classes():
        for level in LEVELS:
            yield f'{name} {level}', [{'name': name, 'level': level}], 'Human'
    yield 'wizard 5 / rogue 3', [{'name': 'wizard', 'level': 5}, {'name': 'rogue', 'level': 3}], 'Elf'
    yield 'cleric 4 / fighter 4 / monk 2', [{'name': 'cleric', 'level': 4}, {'name': 'fighter', 'level': 4},
                                           {'name': 'monk', 'level': 2}], 'Dwarf'


def check_same_under_any_seed(report):
    """Checks 1-3 over the whole sweep."""
    for label, classes, race in requests():
        sheets = [generate(seed, classes, race) for seed in SEEDS]
        where = f'blank [{label}]'
        if not report.check(all('error' not in sheet for sheet in sheets),
                            f'{where}: generation failed: {[s.get("error") for s in sheets]}'):
            continue
        first, second = sheets
        differ = [key for key in first
                  if json.dumps(first[key], sort_keys=True, default=str)
                  != json.dumps(second.get(key), sort_keys=True, default=str)]
        report.check(not differ, f'{where}: differs between two seeds, so it was rolled: {differ}')
        report.check(tuple(first) == PAYLOAD_KEYS, f'{where}: the keys are not PAYLOAD_KEYS in order')
        report.check(all(first[ability] == blank.BLANK_ABILITY for ability in blank.ABILITIES),
                     f'{where}: an ability is not {blank.BLANK_ABILITY}')
        filled = {key for key, value in first.items() if value not in EMPTY}
        stray = sorted(filled - set(blank.KEEP) - REBUILT - set(blank.NEUTRAL))
        report.check(not stray, f'{where}: keys blank.py neither keeps nor rebuilds still hold something: {stray}')
        report.check([(c['name'], c['level']) for c in first['classes']]
                     == [(c['name'], c['level']) for c in classes],
                     f'{where}: the classes are {first["classes"]}')
        report.check(all(c['archetype'] == {} for c in first['classes']), f'{where}: an archetype survived')
        rows = first['slots']
        report.check(rows and all(set(row) == {'section', 'kind', 'label', 'class', 'level', 'bucket'}
                                  and row['label'] for row in rows),
                     f'{where}: slots is empty or a row is malformed')
        for book in first['spellbooks']:
            report.check(not book.get('spell_list_choose_from'), f'{where}: a spellbook still lists spells')


def check_counts_are_the_generators(report):
    """Check 4: a blank sheet is owed what a generated character of the same class and level has."""
    for name in rollable_classes():
        classes = [{'name': name, 'level': 10}]
        sheet = generate(SEEDS[0], classes)
        real = generate(SEEDS[0], classes, blank_request=None)
        where = f'counts [{name} 10]'
        if not report.check('error' not in sheet and 'error' not in real, f'{where}: generation failed'):
            continue
        report.check(real.get('slots') == [], f'{where}: an ordinary character must carry slots == []')
        sections = Counter(row['section'] for row in sheet['slots'])
        for section, key in (('class_feats', 'class_feats'), ('teamwork_feats', 'teamwork_feats'),
                             ('story_feats', 'story_feats')):
            report.check(sections[section] == len(real.get(key) or []),
                         f'{where}: {sections[section]} {section} slots, but a generated {name} 10 '
                         f'has {len(real.get(key) or [])} {key}')
        # Every class choice the generated character picked in has a slot bucket on the blank one.
        # (Not the reverse: an archetype can trade a bucket away, and a blank sheet has none.)
        offered = {str(row['bucket']).replace('_', ' ').lower() for row in sheet['slots']
                   if row['section'] == 'class_features'}
        archetyped = any(c.get('archetype') for c in real.get('classes') or [])
        picked = {str(bucket).replace('_', ' ').lower()
                  for bucket, picks in (real.get('class_feature_levels') or {}).items() if picks}
        report.check(archetyped or picked <= offered or not offered,
                     f'{where}: a generated {name} 10 picked in {sorted(picked - offered)}, '
                     f'which the blank sheet offers no slot for')


def check_house_rules_follow_the_request(report):
    """Check 5."""
    classes = [{'name': 'fighter', 'level': 10}]
    plain = generate(SEEDS[0], classes, homebrew_feat_amount='N', misc_homebrew_rules='N')
    house = generate(SEEDS[0], classes)
    if not report.check('error' not in plain and 'error' not in house, 'house rules: generation failed'):
        return
    plain_sections = Counter(row['section'] for row in plain['slots'])
    house_sections = Counter(row['section'] for row in house['slots'])
    for section in ('story_feats', 'flavor_feats', 'flaw_feats', 'flaws'):
        report.check(plain_sections[section] == 0,
                     f'house rules off: {plain_sections[section]} {section} slot(s) on a PF1 sheet')
        report.check(house_sections[section] > 0, f'house rules on: no {section} slot at all')
    report.check(plain_sections['feats'] == 6,
                 f'house rules off: a human fighter 10 is owed 5 level feats and 1 human feat, '
                 f'not {plain_sections["feats"]}')
    report.check(plain_sections['class_feats'] == 6,
                 f'house rules off: a fighter 10 is owed 6 bonus feats, not {plain_sections["class_feats"]}')
    report.check(plain_sections['traits'] == blank.BLANK_TRAITS and plain_sections['abilities'] == 2,
                 f'house rules off: traits / ability increases are {plain_sections["traits"]} / '
                 f'{plain_sections["abilities"]}')
    # A blank request ignores every pin but the classes.
    with redirect_stdout(io.StringIO()):
        pinned = main_test.generate_random_char(
            selection_request={'classes': classes, 'spheres': ['Destruction'], 'feats': ['Toughness']},
            blank_request='Y', seed=SEEDS[0], userInput_race='Human', use_backstory_api='N')
    GENERATED[0] += 1
    report.check('error' not in pinned and pinned.get('selection_report') == []
                 and pinned.get('feats') == [] and not pinned.get('spheres_chosen'),
                 f'a blank request must honour only the class pins: {pinned.get("selection_report")}')


def prove_the_sweep_can_fail():
    """Switch the emptying off and demand that check 1 notices (see the docstring)."""
    original = blank._empty
    scratch = Report('broken:blank')
    blank._empty = lambda value: value
    try:
        with redirect_stdout(io.StringIO()):
            check_same_under_any_seed(scratch)
    finally:
        blank._empty = original
    REPORT.check(scratch.errors,
                 'blank._empty was made to keep everything and the sweep still passed -- it is not '
                 'looking at what was rolled')


def main():
    check_same_under_any_seed(REPORT)
    check_counts_are_the_generators(REPORT)
    check_house_rules_follow_the_request(REPORT)
    prove_the_sweep_can_fail()
    return REPORT.finish(f'{GENERATED[0]} generations; nothing rolled survives, slot counts are the '
                         f"generator's own, house rules follow the request, proven by breaking it",
                         max_errors=40)


if __name__ == '__main__':
    sys.exit(main())
