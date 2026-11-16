"""Gate blank mode's contract: the key manifest, the request vocabulary, and the request path.

    .venv/Scripts/python.exe Backend/scripts/gates/validate_blank.py

WHY THIS EXISTS
---------------
Blank mode (utils/class_func/blank.py) empties a generated payload and hands back a ``slots`` list
for the Blank Character Generator in the FoundryVTT module. Three things have to line up with no
compiler between them:

  1. THE MANIFEST      -- ``slots`` is a declared payload key, and every key blank.py names (the
                          ones it keeps, the ones it gives a stated neutral value) is a real one. A
                          renamed payload key would otherwise stop being kept, silently.
  2. THE VOCABULARY    -- what counts as asking for a blank sheet, and that a blank request carries
                          forward the class pins and nothing else.
  3. THE REQUEST PATH  -- through Flask: ``GET /selection_options`` says the backend answers blank
                          requests (a client must check before sending the key), a POST with
                          ``blank`` returns the pinned classes with nothing rolled and a ``slots``
                          list, and a POST without it still carries ``slots == []``.

Whether a blank sheet is EMPTY, and owed the right things, is not this gate's question -- that
needs sheets, and tests/test_blank.py generates them.
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
import main_test                                                                    # noqa: E402,F401
from utils.class_func import blank, selection                                       # noqa: E402
from utils.createACharacter import CreateNewCharacter                               # noqa: E402
from utils.payload import PAYLOAD_KEYS                                              # noqa: E402

REPORT = Report('validate_blank')


def check_manifest():
    REPORT.check('slots' in PAYLOAD_KEYS, "'slots' is not declared in payload.PAYLOAD_KEYS")
    if 'slots' in PAYLOAD_KEYS and 'generator_version' in PAYLOAD_KEYS:
        REPORT.check(PAYLOAD_KEYS.index('slots') < PAYLOAD_KEYS.index('generator_version'),
                     "'slots' must sit before 'generator_version', which closes the manifest")
    for label, keys in (('KEEP', blank.KEEP), ('NEUTRAL', blank.NEUTRAL)):
        unknown = sorted(set(keys) - set(PAYLOAD_KEYS))
        REPORT.check(not unknown, f'blank.{label} names keys the payload does not have: {unknown}')
    REPORT.check(not set(blank.KEEP) & set(blank.NEUTRAL),
                 'a key cannot be both kept and given a neutral value')
    REPORT.check('slots' not in blank.KEEP, "'slots' is computed for a blank sheet, never kept")


def check_vocabulary():
    for value in (True, 'Y', 'y', 'yes', 'TRUE', '1'):
        REPORT.check(blank.requested(value), f'blank.requested({value!r}) should be a blank request')
    for value in (None, '', False, 'N', 'no', 0, 'false'):
        REPORT.check(not blank.requested(value), f'blank.requested({value!r}) should not be a blank request')
    classes = [{'name': 'fighter', 'level': 10}]
    REPORT.check(blank.selection_for({'classes': classes, 'spheres': ['Destruction'], 'build': 'Bruiser'})
                 == {'classes': classes},
                 'a blank request must carry forward its class pins and nothing else')
    REPORT.check(blank.selection_for(None) is None and blank.selection_for({}) is None
                 and blank.selection_for({'feats': ['Toughness']}) is None,
                 'a blank request with no class pin carries no selection at all')
    options = selection.options(CreateNewCharacter(main_test.character_json_config))
    REPORT.check(options.get('blank') is True,
                 'selection.options() must say `blank: True` so a client knows the key is understood')


def check_request_path():
    try:
        with redirect_stdout(io.StringIO()):
            import app as flask_app
    except Exception as exc:                                            # noqa: BLE001
        REPORT.skip(f'the Flask request path was not checked: importing app failed ({exc!r}). '
                    f'Run under the repo .venv, which has Flask.')
        return
    client = flask_app.app.test_client()
    served = client.get('/selection_options').get_json() or {}
    REPORT.check(served.get('blank') is True, 'GET /selection_options does not advertise blank support')

    body = {
        'spheres_of_power': 'n', 'seed': 4242, 'blank': 'Y',
        'selection': {'classes': [{'name': 'fighter', 'level': 6}, {'name': 'rogue', 'level': 4}],
                      'spheres': ['Destruction']},
        'create_new_char': 'Y', 'region': 'Tal-Falko', 'race': 'half-elf', 'class': 'random',
        'bab': 'random', 'caster_level': 'random', 'multi_class': 'N', 'alignment': 'random',
        'deity': 'random', 'gender': 'random', 'truly_random_feats': 'Y', 'inherents': 'Y',
        'modded_char_sheet': 'n', 'homebrew_feat_amount': 'Y',
        'num_dice': '4', 'num_sides': '6', 'high_level': '9', 'low_level': '3', 'gold': '',
    }
    with redirect_stdout(io.StringIO()):
        answer = client.post('/update_character_data', json=body)
    payload = answer.get_json() or {}
    if not REPORT.check(answer.status_code == 200 and 'error' not in payload,
                        f'POST with blank failed: {answer.status_code} {payload.get("error")}'):
        return
    REPORT.check([(c['name'], c['level']) for c in payload.get('classes') or []] == [('fighter', 6), ('rogue', 4)],
                 f'POST with blank produced classes {payload.get("classes")}')
    REPORT.check(payload.get('slots') and payload.get('feats') == [] and payload.get('str') == blank.BLANK_ABILITY,
                 'POST with blank did not answer with an empty sheet and a slots list')
    REPORT.check(str(payload.get('chosen_race', '')).lower().replace('-', ' ') == 'half elf',
                 f'POST with blank did not keep the requested race: {payload.get("chosen_race")!r}')
    REPORT.check(not payload.get('spheres_chosen') and payload.get('selection_report') == [],
                 'POST with blank honoured a pin other than the classes')
    body.pop('blank')
    with redirect_stdout(io.StringIO()):
        plain = client.post('/update_character_data', json=body).get_json() or {}
    REPORT.check(plain.get('slots') == [] and plain.get('feats'),
                 f'POST without blank must be an ordinary character with slots == [], got '
                 f'slots={plain.get("slots")!r}')


def main():
    check_manifest()
    check_vocabulary()
    check_request_path()
    return REPORT.finish(f'{len(blank.KEEP)} kept and {len(blank.NEUTRAL)} stated-neutral keys are in '
                         f'the manifest; request vocabulary; request path')


if __name__ == '__main__':
    sys.exit(main())
