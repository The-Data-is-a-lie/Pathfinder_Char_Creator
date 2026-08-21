"""The payload's key set AND key order must match the declared manifest (ticket 09).

    C:/Python310/python.exe Backend/scripts/gates/validate_payload_shape.py
    C:/Python310/python.exe Backend/scripts/gates/validate_payload_shape.py --print
    C:/Python310/python.exe Backend/scripts/gates/validate_payload_shape.py --module-root <dir>

WHY THIS GATE EXISTS
--------------------
The generated payload is the contract TWO OTHER REPOSITORIES read -- the
`pf1e_random_char_generator` FoundryVTT module and the standalone web character sheet -- and both
read it POSITIONALLY. `app.py` sets `JSON_SORT_KEYS = False` deliberately so the order survives
serialization.

Until ticket 09 that order was expressed as the insertion order of a dict literal in the middle of a
2,700-line file. Insert a key in the wrong place and NOTHING fails here: it fails later, in another
repository, on somebody's character sheet. `utils/payload.py::PAYLOAD_KEYS` states the order; this
gate is what makes the statement load-bearing.

The goldens already diff seven seeded characters key by key, so why this too? Because they answer a
different question. A golden says "this character did not change"; it cannot say "the contract is
what we think it is", and re-baselining a golden silently accepts an order change. This gate has no
--update.

WHAT IT CHECKS
--------------
1. Key SET -- nothing missing, nothing unexpected. A key present in one and not the other is named.
2. Key ORDER -- the first position where the built payload diverges from the manifest, with the
   neighbours on both sides, because "key 84 differs" is not an actionable message.
3. Stability across characters: a second character with a different class/level must produce the
   SAME key order. A payload whose shape depends on the character is not a contract at all, and
   conditionally-inserted keys are exactly the failure this catches.
"""
import argparse
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report  # noqa: E402

from utils.payload import PAYLOAD_KEYS  # noqa: E402
from utils.class_func import backstory as _bs  # noqa: E402
_bs._try_ollama = lambda *a, **k: ''

import main_test  # noqa: E402

REPORT = Report('validate_payload_shape')

# Two deliberately different characters: a full caster and a martial, at opposite ends of the level
# range. If the payload's SHAPE depends on what was generated, these two disagree.
SAMPLES = (
    dict(label='wizard L15', class_choice='wizard', high_level=15, low_level=15, seed=12345),
    dict(label='fighter L1', class_choice='fighter', high_level=1, low_level=1, seed=999),
)


def generate(sample):
    kwargs = {k: v for k, v in sample.items() if k != 'label'}
    with redirect_stdout(io.StringIO()):
        return main_test.generate_random_char(
            chosen_BAB='high', multi_class='N', userInput_race='Human',
            userInput_region='Tal-Falko', alignment_input='LG', userInput_gender='female',
            gold_num=10000, num_dice='4', num_sides='6', use_backstory_api='N',
            spheres_flag='N', **kwargs)


def compare(label, keys):
    declared = list(PAYLOAD_KEYS)

    missing = [k for k in declared if k not in keys]
    extra = [k for k in keys if k not in declared]
    REPORT.check(not missing,
                 f'{label}: {len(missing)} key(s) in PAYLOAD_KEYS but NOT in the built payload: '
                 f'{", ".join(missing[:8])}{" ..." if len(missing) > 8 else ""} -- either the '
                 f'builder stopped emitting them or the manifest is stale')
    REPORT.check(not extra,
                 f'{label}: {len(extra)} key(s) in the built payload but NOT declared: '
                 f'{", ".join(extra[:8])}{" ..." if len(extra) > 8 else ""} -- add them to '
                 f'PAYLOAD_KEYS *in the position they are inserted*, since both consumers read '
                 f'this positionally')

    if missing or extra:
        return                                  # order comparison is meaningless against a different set

    for i, (built, want) in enumerate(zip(keys, declared)):
        if built != want:
            lo = max(0, i - 2)
            REPORT.error(
                f'{label}: key order diverges at position {i}. Expected {want!r}, built {built!r}.\n'
                f'         declared: ...{declared[lo:i + 3]}\n'
                f'         built:    ...{keys[lo:i + 3]}\n'
                f'         Order is the contract -- the FoundryVTT module and the web sheet read '
                f'this positionally, so a swap here lands on a character sheet, not in a test.')
            return
    print(f'  ok    {label}: {len(keys)} keys, order matches the manifest')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--print', action='store_true', dest='show',
                    help='print the declared key order and exit')
    args = ap.parse_args()

    if args.show:
        for i, k in enumerate(PAYLOAD_KEYS):
            print(f'  {i:>3}  {k}')
        return 0

    shapes = {}
    for sample in SAMPLES:
        label = sample['label']
        try:
            payload = generate(sample)
        except Exception as exc:                                  # noqa: BLE001
            REPORT.error(f'{label}: generation raised -- {type(exc).__name__}: {exc}')
            continue
        keys = list(payload.keys())
        shapes[label] = keys
        compare(label, keys)

    # (3) the shape must not depend on the character
    if len(shapes) == 2:
        (la, ka), (lb, kb) = shapes.items()
        if ka != kb:
            only_a = [k for k in ka if k not in kb]
            only_b = [k for k in kb if k not in ka]
            detail = ''
            if only_a or only_b:
                detail = (f' Keys only in {la}: {only_a[:6]}. Keys only in {lb}: {only_b[:6]}.'
                          ' A conditionally-inserted key is not a contract -- emit it always, '
                          'with an empty value.')
            REPORT.error(f'{la} and {lb} produced DIFFERENT payload shapes.{detail}')
        else:
            print(f'  ok    both sample characters produced the same {len(ka)}-key shape')

    return REPORT.finish(f'{len(PAYLOAD_KEYS)} declared payload keys')


if __name__ == '__main__':
    sys.exit(main())
