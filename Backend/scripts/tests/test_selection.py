"""Selection mode: pins are honoured, unmet pins are reported, and no pin means no change.

    .venv/Scripts/python.exe Backend/scripts/tests/test_selection.py

WHAT THIS ASSERTS
-----------------
Selection mode (utils/class_func/selection.py) makes one promise per pin -- "this is in the
character" -- and one for the whole feature -- "ask for nothing and nothing changes". Both are
claims about generated characters, so both are checked on generated characters:

1. **Classes and levels** -- the pinned classes are the character's classes, the first one is the
   primary, pinned levels are exact, and unpinned levels fill from the rolled range (A3/A4).
2. **Schools** -- a pinned specialty is the wizard's school in whichever of the four tables it
   lives; pinned opposition schools are the wizard's opposition AND are absent from every spell
   the character picked, wizard or not (A7/A8).
3. **Spheres** -- every pinned sphere arrives with a talent in it, with the Spheres flag off, and
   past the three-sphere roll (A6).
4. **Path of War** -- pinned disciplines reach a Martial Training user as their own chains and an
   initiator as part of its specialization; a pinned path count is the count (A5).
5. **Stat priority** -- rolled scores and inherent bonuses both fall down the pinned order (A9).
6. **Optimize + pins** -- the pins survive optimized mode (A10).
7. **Unmet pins** -- a pin that cannot be honoured is dropped, the character still generates,
   and `selection_report` names the pin (A2).
7b. **Feats** -- a pinned feat is on the sheet, its feat prerequisites are taken with it, it
   costs a slot like any other feat (the feat rows do not grow), and a pin that cannot be met --
   a base attack bonus the class does not have, more pins than slots -- is reported.
8. **Nothing pinned** -- `selection=None`, `{}` and a selection of empty lists all produce the
   same payload as each other, with an empty report. (That this payload is also the one the
   generator produced BEFORE selection mode existed is test_golden_payload's job: the goldens
   moved by the one new key and nothing else.)

SABOTAGE-PROVEN. A sweep that asserts "the pin is there" passes vacuously if the checks never
look at the right field. So every run finishes by breaking the resolver on purpose -- the
accessors are patched to forget their pins -- and re-running the class, sphere, discipline and
school checks against a scratch report. Each must FAIL. A check that still passes with the pins
thrown away is reported as an error in its own right.
"""
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND, Report                                                # noqa: E402

sys.path.insert(0, str(BACKEND))
from utils.class_func import backstory as _bs                                       # noqa: E402
_bs.OLLAMA_AVAILABLE = False
_bs._try_ollama = lambda *a, **k: ''
import main_test                                                                    # noqa: E402
from utils.class_func import selection, spells, stats                               # noqa: E402
from utils.class_func.level_and_bab import MAX_CHARACTER_LEVEL                      # noqa: E402

REPORT = Report('test_selection')
SEEDS = (61001, 61002, 61003)
GENERATED = [0]


# What the last generated character PICKED, spell by spell, lower-cased. Captured where the pick
# is made (spells.spells_known_selection) rather than read off the payload, because the payload's
# spell lists also hold what was GRANTED -- bloodline, patron, domain and school bonus spells are
# spliced into the same lists afterwards -- and a ban is on the pick, not on the grant.
LAST_PICKED = set()
_pick_spells = main_test.spells_known_selection


def _spy_on_picks(character, class_entry, *args, **kwargs):
    result = _pick_spells(character, class_entry, *args, **kwargs)
    for level in class_entry.get('spell_list_choose_from') or []:
        LAST_PICKED.update(str(name).lower() for name in level)
    return result


main_test.spells_known_selection = _spy_on_picks


def generate(seed, pins, **overrides):
    LAST_PICKED.clear()
    args = dict(class_choice='random', chosen_BAB='random', multi_class='N',
                userInput_race='random', userInput_region='Tal-Falko', alignment_input='random',
                userInput_gender='random', high_level=12, low_level=6, gold_num="",
                num_dice='4', num_sides='6', use_backstory_api='N', spheres_flag='N', seed=seed)
    args.update(overrides)
    GENERATED[0] += 1
    with redirect_stdout(io.StringIO()):
        return main_test.generate_random_char(selection_request=pins, **args)


def class_levels(payload):
    return {entry['name']: entry['level'] for entry in payload.get('classes') or []}


def reported(payload, fragment):
    return any(fragment.lower() in row['pin'].lower() for row in payload.get('selection_report') or [])


def picked_spells(_payload):
    """Every spell the character just generated PICKED (see LAST_PICKED)."""
    return set(LAST_PICKED)


_SCHOOL_OF = None


def school_of(name):
    global _SCHOOL_OF
    if _SCHOOL_OF is None:
        frame = spells._load_spell_data()
        _SCHOOL_OF = {str(n).lower(): str(s) for n, s in zip(frame['name'], frame['school'])}
    return _SCHOOL_OF.get(name)


# --------------------------------------------------------------------------- #
# The checks. Each takes the report it writes to, so the sabotage pass can aim
# them at a scratch report and count what they catch.
# --------------------------------------------------------------------------- #
CLASS_CASES = (
    # (label, pins, {name: exact level} expected, generation overrides)
    ('one class', [{'name': 'fighter'}], {}, {}),
    ('slug spelling', ['Barbarian-(Unchained)'], {}, {}),
    ('two levelled', [{'name': 'warder', 'level': 8}, {'name': 'wizard', 'level': 3}],
     {'warder': 8, 'wizard': 3}, {}),
    ('primary is first, not biggest', [{'name': 'rogue', 'level': 2}, {'name': 'cleric', 'level': 9}],
     {'rogue': 2, 'cleric': 9}, {}),
    ('partly levelled', [{'name': 'paladin', 'level': 5}, {'name': 'bard'}, {'name': 'ranger'}],
     {'paladin': 5}, {}),
    ('four classes over a low roll', ['fighter', 'rogue', 'monk', 'barbarian'], {},
     {'low_level': 1, 'high_level': 2}),
    ('two initiators', [{'name': 'warder', 'level': 4}, {'name': 'stalker', 'level': 4}],
     {'warder': 4, 'stalker': 4}, {}),
    ('one pin plus a multiclass roll', [{'name': 'sorcerer', 'level': 6}], {'sorcerer': 6},
     {'multi_class': 'Y'}),
)


def check_classes(report):
    for label, pins, exact, overrides in CLASS_CASES:
        wanted = [selection._norm(p['name'] if isinstance(p, dict) else p) for p in pins]
        for seed in SEEDS:
            payload = generate(seed, {'classes': pins}, **overrides)
            where = f'classes [{label}] seed {seed}'
            if not report.check('error' not in payload, f'{where}: generation failed: {payload.get("error")}'):
                continue
            levels = class_levels(payload)
            missing = [name for name in wanted if name not in levels]
            report.check(not missing, f'{where}: pinned {missing} missing from {sorted(levels)}')
            if len(wanted) >= 2 or overrides.get('multi_class') != 'Y':
                report.check(sorted(levels) == sorted(wanted),
                             f'{where}: classes are {sorted(levels)}, pinned exactly {sorted(wanted)}')
            # The payload's c_class has " (unchained)" stripped for data lookups (archetype_data);
            # the class list keeps the full name, which is what the checks above read.
            primary = wanted[0].replace(' (unchained)', '')
            report.check(payload.get('c_class') == primary,
                         f'{where}: primary is {payload.get("c_class")!r}, first pin is {primary!r}')
            for name, level in exact.items():
                report.check(levels.get(name) == level,
                             f'{where}: {name} is level {levels.get(name)}, pinned {level}')
            report.check(all(level >= 1 for level in levels.values()),
                         f'{where}: a class has no level: {levels}')
            if exact and len(exact) == len(wanted) and overrides.get('multi_class') != 'Y':
                report.check(sum(levels.values()) == sum(exact.values()),
                             f'{where}: total {sum(levels.values())}, pinned levels sum to '
                             f'{sum(exact.values())} -- the level range must be ignored')
            report.check(not payload.get('selection_report'),
                         f'{where}: every pin was legal, yet: {payload.get("selection_report")}')


SCHOOL_CASES = (
    # (label, class pins, schools pin, expected wizard school or None)
    ('core school', [{'name': 'wizard', 'level': 9}],
     {'specialty': 'evocation', 'preferred': ['abjuration'], 'opposition': ['necromancy', 'enchantment']},
     'evocation'),
    ('subschool', [{'name': 'wizard', 'level': 9}],
     {'specialty': 'Admixture', 'opposition': ['illusion']}, 'admixture'),
    ('elemental school', [{'name': 'wizard', 'level': 7}], {'specialty': 'fire'}, 'fire'),
    ('non-wizard caster', [{'name': 'sorcerer', 'level': 10}],
     {'specialty': 'conjuration', 'opposition': ['evocation', 'necromancy']}, None),
    ('divine caster', [{'name': 'cleric', 'level': 10}],
     {'preferred': ['abjuration'], 'opposition': ['necromancy']}, None),
)


def check_schools(report):
    theme = set(selection.spell_schools())
    for label, classes, pin, wizard_school in SCHOOL_CASES:
        opposition = [s for s in pin.get('opposition', [])]
        for seed in SEEDS:
            payload = generate(seed, {'classes': classes, 'schools': pin})
            where = f'schools [{label}] seed {seed}'
            if not report.check('error' not in payload, f'{where}: generation failed: {payload.get("error")}'):
                continue
            if wizard_school is not None:
                report.check(str(payload.get('school')).lower() == wizard_school,
                             f'{where}: wizard school is {payload.get("school")!r}, pinned {wizard_school!r}')
                features = payload.get('class features') or payload.get('class_features') or {}
                report.check(wizard_school in {str(k).lower() for k in features},
                             f'{where}: {wizard_school!r} is not among the class features')
            specialty = selection._norm(pin.get('specialty'))
            if specialty in theme:
                report.check(payload.get('specialty_schools') == [specialty],
                             f'{where}: spell theme specialty is {payload.get("specialty_schools")}')
            for school in opposition:
                report.check(school in (payload.get('counter_schools') or []),
                             f'{where}: {school} is not in counter_schools {payload.get("counter_schools")}')
                if wizard_school in ('evocation', 'admixture'):
                    report.check(school in (payload.get('opposing_school') or []),
                                 f'{where}: {school} is not a wizard opposition school: '
                                 f'{payload.get("opposing_school")}')
            banned = sorted(name for name in picked_spells(payload) if school_of(name) in opposition)
            report.check(not banned, f'{where}: picked spells from a banned school: {banned[:6]}')
            report.check(picked_spells(payload) or not opposition,
                         f'{where}: found no picked spells to check the ban against')


SPHERE_CASES = (
    ('two, flag off', ['Destruction', 'Shield'], {'class_choice': 'fighter', 'low_level': 8, 'high_level': 8}),
    ('four, past the roll', ['Destruction', 'Life', 'Shield', 'Guardian'],
     {'class_choice': 'cleric', 'low_level': 12, 'high_level': 12}),
    ('one, flag on', ['warp'], {'class_choice': 'wizard', 'spheres_flag': 'Y', 'low_level': 6, 'high_level': 6}),
)


def check_spheres(report):
    for label, pins, overrides in SPHERE_CASES:
        for seed in SEEDS:
            payload = generate(seed, {'spheres': pins}, **overrides)
            where = f'spheres [{label}] seed {seed}'
            if not report.check('error' not in payload, f'{where}: generation failed: {payload.get("error")}'):
                continue
            chosen = {str(row.get('sphere')).lower() for row in payload.get('spheres_chosen') or []}
            counts = {str(k).lower(): v for k, v in (payload.get('sphere_counts') or {}).items()}
            for name in pins:
                key = name.lower()
                if reported(payload, f'spheres: {name}'):
                    continue                      # dropped AND said so: that is A2 working
                report.check(key in chosen, f'{where}: {name} is not in spheres_chosen {sorted(chosen)}')
                tally = counts.get(key) or {}
                report.check((tally.get('normal') or 0) + (tally.get('advanced') or 0) >= 1,
                             f'{where}: {name} arrived with no talent in it and no report row')
            report.check(len(chosen) >= len(pins) or payload.get('selection_report'),
                         f'{where}: {len(chosen)} spheres for {len(pins)} pins')


PATH_CASES = (
    # (label, class pins, path_of_war pin, overrides, expected count or None)
    ('martial training, two chains', [{'name': 'fighter', 'level': 10}],
     {'disciplines': ['Primal Fury', 'Broken Blade']}, {}, None),
    ('forced count', [{'name': 'barbarian', 'level': 12}], {'paths': 3}, {}, 3),
    ('count above the pins', [{'name': 'ranger', 'level': 9}],
     {'disciplines': ["Fool's Errand"], 'paths': 2}, {}, 2),
    ('initiator, off-list discipline', [{'name': 'warder', 'level': 8}],
     {'disciplines': ['Veiled Moon']}, {}, None),
)


def check_paths(report):
    for label, classes, pin, overrides, count in PATH_CASES:
        wanted = [selection._norm(name) for name in pin.get('disciplines', [])]
        initiator = classes[0]['name'] == 'warder'
        for seed in SEEDS:
            payload = generate(seed, {'classes': classes, 'path_of_war': pin}, **overrides)
            where = f'path of war [{label}] seed {seed}'
            if not report.check('error' not in payload, f'{where}: generation failed: {payload.get("error")}'):
                continue
            have = [selection._norm(name) for name in payload.get('martial_disciplines') or []]
            for name in wanted:
                report.check(name in have, f'{where}: {name} is not in martial_disciplines {have}')
                if not initiator:
                    chain = [f for f in payload.get('mt_feats') or []
                             if selection._norm(f).endswith(f'({name})')]
                    report.check(chain, f'{where}: no Martial Training chain is labelled for {name}')
            if count is not None:
                report.check(len(have) == count, f'{where}: {len(have)} paths, pinned {count}')
            report.check(not payload.get('selection_report'),
                         f'{where}: every pin was legal, yet: {payload.get("selection_report")}')


def check_stat_priority(report):
    """Rolled scores are read where roll_stats hands them on (before race and level-ups touch
    them); inherent bonuses are read off the payload."""
    captured = {}
    original = stats.level_up_stats

    def spy(rolled, character, *args, **kwargs):
        captured['rolled'] = dict(rolled)
        return original(rolled, character, *args, **kwargs)

    stats.level_up_stats = spy
    try:
        for order in (['cha', 'dex', 'wis'], ['Strength', 'con', 'int', 'dex', 'wis', 'cha']):
            full = selection._resolve_stat_priority(None, order)
            for seed in SEEDS:
                captured.clear()
                payload = generate(seed, {'stat_priority': order}, low_level=14, high_level=14)
                where = f'stat priority {order} seed {seed}'
                if not report.check('error' not in payload, f'{where}: generation failed: {payload.get("error")}'):
                    continue
                rolled = [captured.get('rolled', {}).get(ability) for ability in full]
                report.check(None not in rolled and rolled == sorted(rolled, reverse=True),
                             f'{where}: rolled scores down the order are {rolled}, not descending')
                poured = [(payload.get('inherents') or {}).get(ability, 0) for ability in full]
                report.check(poured == sorted(poured, reverse=True) and poured[0] > 0,
                             f'{where}: inherents down the order are {poured}, not poured from the top')
    finally:
        stats.level_up_stats = original


def check_optimize(report):
    pins = {'classes': [{'name': 'fighter'}, {'name': 'wizard', 'level': 2}],
            'schools': {'opposition': ['necromancy']}}
    for seed in SEEDS:
        payload = generate(seed, pins, optimize='y', low_level=10, high_level=10)
        where = f'optimize + pins seed {seed}'
        if not report.check('error' not in payload, f'{where}: generation failed: {payload.get("error")}'):
            continue
        levels = class_levels(payload)
        report.check(sorted(levels) == ['fighter', 'wizard'], f'{where}: classes are {sorted(levels)}')
        report.check(levels.get('wizard') == 2, f'{where}: wizard is level {levels.get("wizard")}, pinned 2')
        report.check(payload.get('c_class') == 'fighter', f'{where}: primary is {payload.get("c_class")!r}')
        report.check('necromancy' in (payload.get('counter_schools') or []),
                     f'{where}: the opposition pin did not survive optimize')


UNMET_CASES = (
    # (label, pins, overrides, fragment each report must contain)
    ('unknown class', {'classes': ['wizzard']}, {}, ['wizzard']),
    ('duplicate class', {'classes': ['fighter', 'Fighter']}, {}, ['classes[1]']),
    ('five classes', {'classes': ['fighter', 'rogue', 'monk', 'barbarian', 'ranger']}, {}, ['ranger']),
    ('four casters', {'classes': ['wizard', 'cleric', 'druid', 'sorcerer']}, {}, ['sorcerer']),
    ('levels past the ceiling', {'classes': [{'name': 'fighter', 'level': 30},
                                             {'name': 'rogue', 'level': 30}]}, {}, ['total level']),
    ('bad level', {'classes': [{'name': 'fighter', 'level': 'lots'}]}, {}, ['.level']),
    ('unknown ability', {'stat_priority': ['luck', 'str']}, {}, ['luck']),
    ('unknown school', {'schools': {'specialty': 'chronomancy', 'opposition': ['bogus']}}, {},
     ['chronomancy', 'bogus']),
    ('opposition is the specialty', {'schools': {'specialty': 'evocation', 'opposition': ['evocation']}},
     {}, ['schools.opposition']),
    ('unknown sphere', {'spheres': ['Nope']}, {}, ['Nope']),
    ('unknown discipline', {'path_of_war': {'disciplines': ['Soggy Biscuit']}}, {}, ['Soggy Biscuit']),
    ('no way into Martial Training',
     {'classes': [{'name': 'wizard', 'level': 2}], 'path_of_war': {'disciplines': ['Primal Fury']}},
     {}, ['Primal Fury']),
    ('path count on an initiator',
     {'classes': [{'name': 'warder', 'level': 6}], 'path_of_war': {'paths': 2}}, {}, ['path_of_war.paths']),
    ('unknown feat', {'feats': ['Totally Fake Feat', 'Toughness']}, {}, ['Totally Fake Feat']),
    ('a feat past the class', {'classes': [{'name': 'wizard', 'level': 3}], 'feats': ['Improved Critical']},
     {}, ['Improved Critical']),
    ('unknown key', {'clases': ['fighter']}, {}, ['clases']),
    ('not an object', ['fighter'], {}, ['selection']),
)


def check_unmet(report):
    for label, pins, overrides, fragments in UNMET_CASES:
        payload = generate(SEEDS[0], pins, **overrides)
        where = f'unmet [{label}]'
        if not report.check('error' not in payload,
                            f'{where}: an unmet pin must not cost the character: {payload.get("error")}'):
            continue
        rows = payload.get('selection_report')
        report.check(isinstance(rows, list) and all(set(row) == {'pin', 'reason'} and row['reason']
                                                    for row in rows or []),
                     f'{where}: selection_report is not a list of {{pin, reason}}: {rows}')
        for fragment in fragments:
            report.check(reported(payload, fragment),
                         f'{where}: nothing in the report names {fragment!r}: {rows}')
    capped = generate(SEEDS[0], {'classes': [{'name': 'fighter', 'level': 30}, {'name': 'rogue', 'level': 30}]})
    report.check(sum(class_levels(capped).values()) == MAX_CHARACTER_LEVEL,
                 f'unmet [levels past the ceiling]: total is {sum(class_levels(capped).values())}, '
                 f'the ceiling is {MAX_CHARACTER_LEVEL}')
    report.check(class_levels(capped).get('fighter') == 30,
                 'unmet [levels past the ceiling]: levels must come off the LAST class first')


FEAT_LIST_KEYS = ('feats', 'story_feats', 'flaw_feats', 'flavor_feats', 'class_feats', 'trainer_feats')
FEAT_TAX_KEYS = ('feats_feat_tax_dict', 'story_feat_tax_dict', 'flaw_feat_tax_dict',
                 'flavor_feat_tax_dict', 'class_feat_tax_dict', 'trainer_feat_tax_dict')


def held_feats(payload):
    """Every feat on the sheet, lower-cased base names: the feat rows and the feat-tax children
    bundled onto them (a child is held, it just does not occupy a slot)."""
    held = set()
    for key in FEAT_LIST_KEYS:
        held.update(str(name).lower().split(' (')[0] for name in payload.get(key) or [])
    for key in FEAT_TAX_KEYS:
        for children in (payload.get(key) or {}).values():
            held.update(str(name).lower().split(' (')[0] for name in children or [])
    return held


FEAT_CASES = (
    # (label, class pins, feat pins, also held when the last pin is, overrides, every pin must land)
    ('one feat', [{'name': 'fighter', 'level': 10}], ['Toughness'], [], {}, True),
    ('three feats', [{'name': 'rogue', 'level': 8}], ['Iron Will', 'Great Fortitude', 'Alertness'], [], {}, True),
    ('a chain is pulled in', [{'name': 'fighter', 'level': 10}], ['Great Cleave'], ['cleave'], {}, False),
    ('a longer chain', [{'name': 'fighter', 'level': 12}], ['Spring Attack'], ['dodge', 'mobility'], {}, False),
    ('past the ordinary slots', [{'name': 'fighter', 'level': 10}],
     ['Toughness', 'Iron Will', 'Great Fortitude', 'Lightning Reflexes', 'Improved Initiative',
      'Alertness', 'Run', 'Athletic'], [], {}, True),
    ('a caster', [{'name': 'wizard', 'level': 9}], ['Spell Penetration', 'Toughness'], [], {}, True),
    ('without the house feats', [{'name': 'fighter', 'level': 6}], ['Toughness', 'Iron Will'], [],
     {'homebrew_feat_amount': 'N'}, True),
    ('with optimize', [{'name': 'fighter', 'level': 10}], ['Toughness', 'Iron Will'], [],
     {'optimize': 'y'}, True),
)


def check_feats(report):
    for label, classes, feats, parents, overrides, must_land in FEAT_CASES:
        for seed in SEEDS:
            payload = generate(seed, {'classes': classes, 'feats': feats}, **overrides)
            where = f'feats [{label}] seed {seed}'
            if not report.check('error' not in payload, f'{where}: generation failed: {payload.get("error")}'):
                continue
            held = held_feats(payload)
            for name in feats:
                if reported(payload, f'feats: {name}'):
                    report.check(not must_land, f'{where}: {name} has no prerequisite the class lacks, '
                                                f'yet it was dropped: {payload.get("selection_report")}')
                    continue                      # dropped AND said so: that is A2 working
                report.check(name.lower() in held, f'{where}: {name} is not on the sheet and not reported')
            if not reported(payload, f'feats: {feats[-1]}'):
                for parent in parents:
                    report.check(parent in held, f'{where}: {feats[-1]} is held without its prerequisite {parent}')
            # No free feats: the pins sit IN the feat rows the character was owed, so pinning must
            # not lengthen them. Same seed and classes, nothing pinned but the classes.
            if must_land:
                plain = generate(seed, {'classes': classes}, **overrides)
                for key in ('feats', 'class_feats', 'story_feats', 'flaw_feats', 'flavor_feats'):
                    report.check(len(payload.get(key) or []) == len(plain.get(key) or []),
                                 f'{where}: {key} has {len(payload.get(key) or [])} rows pinned and '
                                 f'{len(plain.get(key) or [])} unpinned -- a pin must cost a slot')
    # More pins than a 1st-level commoner has slots: some land, and every one that does not is named.
    many = ['Toughness', 'Iron Will', 'Great Fortitude', 'Lightning Reflexes', 'Improved Initiative',
            'Alertness', 'Run', 'Athletic', 'Acrobatic', 'Endurance', 'Deceitful', 'Persuasive']
    crowded = generate(SEEDS[0], {'classes': [{'name': 'commoner', 'level': 1}], 'feats': many})
    if report.check('error' not in crowded, f'feats [more pins than slots]: {crowded.get("error")}'):
        held = held_feats(crowded)
        dropped = [name for name in many if name.lower() not in held]
        report.check(dropped, 'feats [more pins than slots]: a 1st-level commoner held all twelve pinned feats')
        report.check(any(name.lower() in held for name in many),
                     'feats [more pins than slots]: not one pinned feat landed')
        for name in dropped:
            report.check(reported(crowded, f'feats: {name}'),
                         f'feats [more pins than slots]: {name} was dropped without a report row')


def check_nothing_pinned(report):
    for seed in SEEDS:
        for overrides in ({}, {'multi_class': 'Y', 'spheres_flag': 'Y'}, {'optimize': 'y'}):
            baseline = generate(seed, None, **overrides)
            where = f'nothing pinned seed {seed} {overrides or ""}'
            report.check(baseline.get('selection_report') == [],
                         f'{where}: selection_report is {baseline.get("selection_report")!r}, expected []')
            text = json.dumps(baseline, sort_keys=True, default=str)
            for empty in ({}, {'classes': [], 'spheres': [], 'schools': {}, 'path_of_war': {},
                               'feats': [], 'build': ''}):
                other = json.dumps(generate(seed, empty, **overrides), sort_keys=True, default=str)
                report.check(other == text,
                             f'{where}: selection={empty!r} changed the character -- an empty '
                             f'selection must be the same as none')


def sabotage():
    """Break the resolver on purpose and demand that the sweep notices (see the docstring)."""
    proofs = (
        ('classes', 'pinned_classes', lambda character: [], check_classes),
        ('class levels', 'pinned_class_levels', lambda character: None, check_classes),
        ('spheres', 'pinned_spheres', lambda character: [], check_spheres),
        ('disciplines', 'pinned_disciplines', lambda character: [], check_paths),
        ('path count', 'pinned_paths', lambda character: None, check_paths),
        ('schools', 'school_pins', lambda character: None, check_schools),
        ('feats', 'pinned_feats', lambda character: [], check_feats),
    )
    for label, accessor, broken, check in proofs:
        original = getattr(selection, accessor)
        scratch = Report(f'sabotage:{label}')
        setattr(selection, accessor, broken)
        try:
            check(scratch)
        finally:
            setattr(selection, accessor, original)
        REPORT.check(scratch.errors,
                     f'sabotage [{label}]: selection.{accessor} was made to forget its pins and '
                     f'the sweep still passed -- that check is not looking at the pin')


def main():
    check_classes(REPORT)
    check_schools(REPORT)
    check_spheres(REPORT)
    check_paths(REPORT)
    check_stat_priority(REPORT)
    check_optimize(REPORT)
    check_feats(REPORT)
    check_unmet(REPORT)
    check_nothing_pinned(REPORT)
    sabotage()
    return REPORT.finish(f'{GENERATED[0]} generations; pins honoured, unmet pins reported, '
                         f'no pin no change, seven sabotage proofs', max_errors=40)


if __name__ == '__main__':
    sys.exit(main())
