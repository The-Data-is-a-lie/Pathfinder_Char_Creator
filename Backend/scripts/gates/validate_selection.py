"""Gate selection mode's contract: the option lists, the level arithmetic, and the request path.

    .venv/Scripts/python.exe Backend/scripts/gates/validate_selection.py

WHY THIS EXISTS
---------------
Selection mode (utils/class_func/selection.py) has two ends that must agree and no compiler
between them: `GET /selection_options` tells a client what it may pin, and `phase_selection`
decides what a pin means. If the endpoint offers a name the resolver cannot place, the picker
shows an option that silently does nothing -- the unmatched-string trap again, with a UI on top.

  1. OPTIONS ARE THE DATA   -- every list the endpoint publishes is read from the data the
                               generator reads (class_data, wizard_schools, spells.csv, the vetted
                               sphere lists, data.disciplines), not restated.
  2. OPTIONS ROUND-TRIP     -- every single option, sent back as a pin, resolves with no report
                               row. This is the check that would have caught a display-cased name
                               the resolver lower-cases differently.
  3. THE LEVEL ARITHMETIC   -- ruling A4's three cases (every class levelled / some / none), plus
                               the level ceiling's trim order.
  3b. THE ABILITY FLOORS    -- `stats.meet_ability_floors`, which places a rolled score where a
                               pinned feat needs one: it only swaps, takes the cheapest donor,
                               never robs a main stat, and leaves an impossible floor alone.
  4. THE PAYLOAD KEY        -- `selection_report` is declared, and sits before `generator_version`.
  5. THE REQUEST PATH       -- through Flask: `GET /selection_options` serves exactly
                               `selection.options()`, and a POST carrying a `selection` OBJECT
                               generates a character. The second half is not a formality:
                               `update_character_data` calls `.strip()` on every value it does not
                               pop first, so an unpopped object is a 500.

Whether a pin is HONOURED in a generated character is not this gate's question -- that needs
characters, and tests/test_selection.py generates them.
"""
import io
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
from utils import data                                                              # noqa: E402
from utils.class_func import build_steer, selection, spells, stats                  # noqa: E402
from utils.util import _available_class_pool                                        # noqa: E402
from utils.class_func.feats import pinnable_feat_index                              # noqa: E402
from utils.class_func import spheres as spheres_module                              # noqa: E402
from utils.class_func.level_and_bab import MAX_CHARACTER_LEVEL, _split_levels       # noqa: E402
from utils.createACharacter import CreateNewCharacter                               # noqa: E402
from utils.payload import PAYLOAD_KEYS                                              # noqa: E402

REPORT = Report('validate_selection')


def fresh_character():
    return CreateNewCharacter(main_test.character_json_config)


def resolve(pins):
    """Run the resolver alone and return (plan, report)."""
    character = fresh_character()
    selection.phase_selection(character, pins)
    return character.selection, character.selection_report


def check_options_are_the_data(options):
    character = fresh_character()
    REPORT.check([row['name'] for row in options['classes']] == sorted(character.class_data),
                 'options.classes is not exactly the keys of class_data.json')
    groups = {token for token, _label, _roster in data.CLASS_GROUPS}
    stray = sorted({row['group'] for row in options['classes']} - groups)
    REPORT.check(not stray, f'options.classes names groups data.CLASS_GROUPS does not define: {stray}')
    REPORT.check(options['abilities'] == list(selection.ABILITIES),
                 'options.abilities is not selection.ABILITIES')
    for _branch, table in selection._WIZARD_TABLES:
        REPORT.check(options['schools']['specialty'].get(table) == sorted(character.wizard_schools[table]),
                     f'options.schools.specialty.{table} is not the keys of wizard_schools.json::{table}')
    counts = spells._load_spell_data()['school'].value_counts()
    themed = sorted(counts[counts > spells.THEME_SCHOOL_MIN_SPELLS].index.tolist())
    REPORT.check(options['schools']['spell_schools'] == themed,
                 f'options.schools.spell_schools {options["schools"]["spell_schools"]} is not the '
                 f'schools spells.spell_theme_func can roll {themed}')
    for system, vetted in (('power', data.magic_spheres), ('might', data.combat_spheres)):
        have = {name.lower() for name in options['spheres'][system]}
        available = {key.lower() for key in spheres_module._available_spheres(system)}
        REPORT.check(have == available,
                     f'options.spheres.{system} differs from spheres._available_spheres: '
                     f'{sorted(have ^ available)}')
        REPORT.check(have <= {name.lower() for name in vetted},
                     f'options.spheres.{system} offers a sphere data.py has not vetted')
    REPORT.check(set(options['disciplines']) <= set(data.disciplines),
                 'options.disciplines offers a name data.disciplines does not list')
    REPORT.check(options['disciplines'], 'options.disciplines is empty')
    REPORT.check(options['limits'] == {'max_classes': selection.MAX_PINNED_CLASSES,
                                       'max_caster_classes': selection.MAX_CASTER_CLASSES,
                                       'max_level': MAX_CHARACTER_LEVEL},
                 f'options.limits {options["limits"]} is not the constants the resolver enforces')
    index = pinnable_feat_index()
    REPORT.check([row['name'] for row in options['feats']] == [index[key]['name'] for key in sorted(index)],
                 'options.feats is not feats.pinnable_feat_index(), the index the resolver reads')
    REPORT.check(options['feats'] and not any('mythic' in row['type'].lower() for row in options['feats']),
                 'options.feats is empty or offers a Mythic row (mythic feats belong to the mythic phase)')
    REPORT.check(any(row['homebrew'] for row in options['feats'])
                 and not all(row['homebrew'] for row in options['feats']),
                 'options.feats should carry both printed and homebrew rows, told apart by `homebrew`')
    offered = build_steer.offered(character, sorted(_available_class_pool(character)))
    REPORT.check([row['name'] for row in options['builds']] == list(offered),
                 'options.builds is not build_steer.offered(), the builds some class can be')
    roster = build_steer.roster()
    for row in options['builds']:
        REPORT.check(row['classes'] == offered[row['name']][:selection.BUILD_CLASS_HINTS] and row['classes'],
                     f'options.builds[{row["name"]}].classes is not its best-fitting classes')
        REPORT.check(row['family'] == roster[row['name']].get('family')
                     and row['definition'] == roster[row['name']].get('definition'),
                     f'options.builds[{row["name"]}] restates family/definition instead of reading the roster')
    REPORT.check(build_steer.scorer._FALLBACK.label not in offered,
                 'the scorer\'s fallback label is offered as a build to pin')
    REPORT.check(options['keys'] == list(selection.REQUEST_KEYS),
                 'options.keys is not selection.REQUEST_KEYS')


def check_options_round_trip(options):
    """Every option, pinned alone, must resolve onto the plan and leave the report empty."""
    def expect(pins, landed, label):
        plan, report = resolve(pins)
        REPORT.check(not report, f'{label} is offered by the endpoint but reported: {report}')
        REPORT.check(plan is not None and landed(plan),
                     f'{label} is offered by the endpoint but did not land on the plan')

    for row in options['classes']:
        for spelling in (row['name'], row['label'], row['name'].replace(' ', '-')):
            expect({'classes': [spelling]}, lambda plan, n=row['name']: plan['classes'][0]['name'] == n,
                   f'class {spelling!r}')
    for ability in options['abilities']:
        expect({'stat_priority': [ability]}, lambda plan, a=ability: plan['stat_priority'][0] == a,
               f'ability {ability!r}')
    for table, names in options['schools']['specialty'].items():
        for name in names:
            expect({'schools': {'specialty': name}},
                   lambda plan, n=name: plan['schools']['specialty'] == n,
                   f'specialty {name!r} ({table})')
    for name in options['schools']['spell_schools']:
        expect({'schools': {'preferred': [name]}}, lambda plan, n=name: plan['schools']['preferred'] == [n],
               f'preferred school {name!r}')
        expect({'schools': {'opposition': [name]}}, lambda plan, n=name: plan['schools']['opposition'] == [n],
               f'opposition school {name!r}')
    for system, names in options['spheres'].items():
        for name in names:
            expect({'spheres': [name]},
                   lambda plan, n=name, sy=system: [(k.lower(), s) for k, s in plan['spheres']] == [(n.lower(), sy)],
                   f'{system} sphere {name!r}')
    for name in options['disciplines']:
        expect({'path_of_war': {'disciplines': [name]}},
               lambda plan, n=name: plan['path_of_war']['disciplines'] == [n], f'discipline {name!r}')
    for row in options['builds']:
        for spelling in (row['name'], row['name'].lower(), row['name'].replace(' ', '-')):
            expect({'build': spelling}, lambda plan, n=row['name']: plan['build'] == n, f'build {spelling!r}')
    # Feats in ONE request: there are well over a thousand, and resolution is per name, so pinning
    # them together asks the same question of each without building a character apiece.
    names = [row['name'] for row in options['feats']]
    expect({'feats': names}, lambda plan: plan['feats'] == names, f'the {len(names)} offered feats')
    # Other spellings of three feats whose own names carry no parenthetical (a few do -- "Ability
    # Focus (Malefactions)" -- and for those the parenthetical IS the name).
    plain = [name for name in names if '(' not in name][:3]
    expect({'feats': [plain[0].upper(), plain[1].lower(), f'{plain[2]} (anything)']},
           lambda plan: plan['feats'] == plain, 'a feat in other casing / with a parenthetical')


def check_ability_floors():
    rolled = {'str': 16, 'dex': 9, 'con': 14, 'int': 8, 'wis': 13, 'cha': 11}
    meet = stats.meet_ability_floors
    # Nothing asked, or already met: the scores are returned as rolled.
    REPORT.check(meet(rolled, {}) == rolled, 'ability floors: no floor must change nothing')
    REPORT.check(meet(rolled, {'str': 13}, keep=('str',)) == rolled,
                 'ability floors: a floor already met must change nothing')
    # A short ability trades with the LOWEST score that is high enough (wis 13, not con 14).
    placed = meet(rolled, {'dex': 13}, keep=('str',))
    REPORT.check(placed['dex'] == 13 and placed['wis'] == 9 and placed['con'] == 14,
                 f'ability floors: dex 13 should take the 13 off wis and leave con alone: {placed}')
    # Only what was rolled is placed -- the six scores are the same six.
    REPORT.check(sorted(placed.values()) == sorted(rolled.values()),
                 'ability floors: a floor must swap scores, never raise one')
    # A main stat never gives its score up, even when it is the only one high enough.
    REPORT.check(meet(rolled, {'int': 15}, keep=('str',)) == rolled,
                 'ability floors: the class main stat must not be traded away')
    # Two floors: both are met, and neither undoes the other.
    both = meet(rolled, {'dex': 13, 'int': 13}, keep=('str',))
    REPORT.check(both['dex'] >= 13 and both['int'] >= 13,
                 f'ability floors: dex 13 and int 13 are both reachable here: {both}')
    # No score is high enough: nothing moves (the feat that needed it is reported downstream).
    REPORT.check(meet(rolled, {'cha': 18}, keep=('str',)) == rolled,
                 'ability floors: an unreachable floor must leave the scores alone')


def check_level_arithmetic():
    def even(total, count):
        """A deterministic splitter with _split_levels' contract: at least 1 each, sums to total."""
        base = [1] * count
        for index in range(total - count):
            base[index % count] += 1
        return base

    # 1. Every class levelled: exactly those levels, and the roll is ignored outright.
    for rolled in (0, 1, 15, 40):
        REPORT.check(selection.resolve_levels([8, 3], rolled, even) == [8, 3],
                     f'A4 case 1: all-levelled picks must ignore the rolled total ({rolled})')
    # 2. Some levelled: they take theirs first; the rest split what is left of the roll...
    REPORT.check(selection.resolve_levels([5, None, None], 12, even) == [5, 4, 3],
                 'A4 case 2: 5 pinned of a rolled 12 leaves 7 for the two unlevelled classes')
    #    ...with at least 1 each, so the total rises when the pins leave less than that.
    REPORT.check(selection.resolve_levels([10, None, None], 6, even) == [10, 1, 1],
                 'A4 case 2: unlevelled classes get 1 each even when the roll is already spent')
    REPORT.check(selection.resolve_levels([None, 4], 9, even) == [5, 4],
                 'A4 case 2: an unlevelled FIRST class takes what the levelled one leaves')
    # 3. None levelled: the rolled total, raised to one level per class -- never truncated.
    REPORT.check(selection.resolve_levels([None, None, None], 7, even) == [3, 2, 2],
                 'A4 case 3: unlevelled picks split the rolled total')
    REPORT.check(selection.resolve_levels([None] * 4, 2, even) == [1, 1, 1, 1],
                 'A4 case 3: four pinned classes on a rolled 2 keep all four, one level each')
    # The real splitter honours the same contract resolve_levels leans on.
    for total, count in ((1, 1), (4, 4), (9, 2), (40, 4)):
        shares = _split_levels(total, count)
        REPORT.check(len(shares) == count and sum(shares) == total and min(shares) >= 1,
                     f'_split_levels({total}, {count}) = {shares} breaks "sum to total, 1 each"')
    # The ceiling trims from the LAST class first and never below 1.
    REPORT.check(selection.cap_total([30, 30], 40) == [30, 10], 'cap_total must trim the last class first')
    REPORT.check(selection.cap_total([39, 5, 5], 40) == [38, 1, 1],
                 'cap_total must leave every class a level and then reach back up the list')
    REPORT.check(selection.cap_total([8, 3], 40) == [8, 3], 'cap_total must not touch a legal total')


def check_payload_key():
    keys = list(PAYLOAD_KEYS)
    if REPORT.check('selection_report' in keys, "'selection_report' is not declared in PAYLOAD_KEYS"):
        REPORT.check(keys.index('selection_report') < keys.index('generator_version'),
                     "'selection_report' must sit before 'generator_version'")


def check_request_path(options):
    try:
        with redirect_stdout(io.StringIO()):
            import app as flask_app
    except Exception as exc:                                            # noqa: BLE001
        REPORT.skip(f'the Flask request path was not checked: importing app failed ({exc!r}). '
                    f'Run under the repo .venv, which has Flask.')
        return
    client = flask_app.app.test_client()
    served = client.get('/selection_options')
    REPORT.check(served.status_code == 200, f'GET /selection_options returned {served.status_code}')
    REPORT.check(served.get_json() == options,
                 'GET /selection_options does not serve selection.options() unchanged')

    # The nineteen positional fields, in the order process_input_values unpacks them, with the
    # named keys ahead of them as a real client sends them.
    body = {
        'spheres_of_power': 'n', 'seed': 4242,
        'selection': {'classes': [{'name': 'fighter', 'level': 4}, {'name': 'wizzard'}],
                      'schools': {'opposition': ['necromancy']}},
        'create_new_char': 'Y', 'region': 'Tal-Falko', 'race': 'random', 'class': 'random',
        'bab': 'random', 'caster_level': 'random', 'multi_class': 'N', 'alignment': 'random',
        'deity': 'random', 'gender': 'random', 'truly_random_feats': 'Y', 'inherents': 'Y',
        'modded_char_sheet': 'n', 'homebrew_feat_amount': 'Y',
        'num_dice': '4', 'num_sides': '6', 'high_level': '9', 'low_level': '3', 'gold': '',
    }
    with redirect_stdout(io.StringIO()):
        answer = client.post('/update_character_data', json=body)
    payload = answer.get_json() or {}
    if not REPORT.check(answer.status_code == 200 and 'error' not in payload,
                        f'POST with a selection object failed: {answer.status_code} {payload.get("error")}'):
        return
    levels = {entry['name']: entry['level'] for entry in payload.get('classes') or []}
    REPORT.check(levels == {'fighter': 4},
                 f'POST with a selection object produced classes {levels}, pinned fighter 4')
    REPORT.check(any('wizzard' in row.get('pin', '') for row in payload.get('selection_report') or []),
                 f'POST: the unmet pin did not come back in selection_report: '
                 f'{payload.get("selection_report")}')
    body.pop('selection')
    with redirect_stdout(io.StringIO()):
        plain = (client.post('/update_character_data', json=body).get_json() or {})
    REPORT.check(plain.get('selection_report') == [],
                 f'POST without a selection must still carry selection_report == [], got '
                 f'{plain.get("selection_report")!r}')


def main():
    options = selection.options(fresh_character())
    check_options_are_the_data(options)
    check_options_round_trip(options)
    check_level_arithmetic()
    check_ability_floors()
    check_payload_key()
    check_request_path(options)
    return REPORT.finish(
        f'{len(options["classes"])} classes, '
        f'{sum(len(v) for v in options["schools"]["specialty"].values())} arcane schools, '
        f'{sum(len(v) for v in options["spheres"].values())} spheres and '
        f'{len(options["disciplines"])} disciplines, {len(options["builds"])} builds and '
        f'{len(options["feats"])} feats round-trip; '
        f'A4 level arithmetic; ability floors; request path')


if __name__ == '__main__':
    sys.exit(main())
