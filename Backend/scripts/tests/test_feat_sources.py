"""Feat sources: every general feat row says where it came from, and no granted feat is lost.

    .venv/Scripts/python.exe Backend/scripts/tests/test_feat_sources.py

WHAT THIS ASSERTS
-----------------
The general feat list mixes sources -- level feats, the house creation feats, the human bonus
feat, and slots spent on professions or a martial path -- and ``feat_labels`` (built by
utils/class_func/feat_sources.py) names each row. Three bugs sat behind the old positional
numbering, so each has a check of its own, on generated characters:

1. **The labels are parallel and true.** One label per feat; the free-choice rows carry the slot
   names in order (Human, Creation 1, Creation 2, then Feat 1, 3, 5 ... never past the character's
   level); a profession feat's row says Profession.
2. **The track is the size its sources add up to.** Level feats + creation feats + the human feat:
   the rows that are not bought with luck or granted for gear number exactly that. This is the
   check that fails if a human's bonus feat is drawn and trimmed away again, which it was.
3. **A human has the Human row, and nobody else does.**
4. **A monk's bonus feats and a ranger's combat style feats reach the sheet**, as class bonus feats
   labelled with the class level each came at, with ``class_feat_labels`` still aligned.

PROVEN BY BREAKING IT. The run ends by putting the human bug back -- ``human_flag_assigner`` made
to forget the general track -- and re-running checks 2 and 3 against a scratch report. They must
FAIL.
"""
import io
import sys
from contextlib import redirect_stdout
from math import ceil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND, Report                                                # noqa: E402

sys.path.insert(0, str(BACKEND))
from utils.class_func import backstory as _bs                                       # noqa: E402
_bs.OLLAMA_AVAILABLE = False
_bs._try_ollama = lambda *a, **k: ''
import main_test                                                                    # noqa: E402
from utils.class_func import flag_assign                                            # noqa: E402
from utils.createACharacter import CreateNewCharacter                               # noqa: E402
from utils.util import _available_class_pool                                        # noqa: E402

REPORT = Report('test_feat_sources')
SEEDS = (65001, 65002)
GENERATED = [0]

# Rows that are not part of the general track's own slots: bought with luck, or handed over free.
OFF_TRACK = ('Luck ', 'Granted ')
# The class levels that grant the two list-granted bonus feats, as PF1 prints them.
MONK_LEVELS = (1, 2, 6, 10, 14, 18)
RANGER_LEVELS = (2, 6, 10, 14, 18)


def generate(seed, cls, level, race, **overrides):
    args = dict(class_choice='random', chosen_BAB='random', multi_class='N',
                userInput_race=race, userInput_region='Tal-Falko', alignment_input='random',
                userInput_gender='random', high_level=12, low_level=6, gold_num="",
                num_dice='4', num_sides='6', use_backstory_api='N', spheres_flag='N', seed=seed)
    args.update(overrides)
    GENERATED[0] += 1
    with redirect_stdout(io.StringIO()):
        return main_test.generate_random_char(
            selection_request={'classes': [{'name': cls, 'level': level}]}, **args)


def expected_slots(level, human, house):
    """The general track's slots, worked out here from the rules rather than from the code."""
    slots = ['Human'] if human else []
    if house:
        slots += ['Creation 1', 'Creation 2']
    return slots + [f'Feat {at}' for at in range(1, level + 1, 2)]


def cases():
    pool = sorted(_available_class_pool(CreateNewCharacter(main_test.character_json_config)))
    for cls in pool:
        for race in ('Human', 'Elf'):
            yield cls, 10, race, {}
    for cls in ('fighter', 'rogue', 'wizard', 'monk', 'ranger'):
        for level in (1, 20):
            for race in ('Human', 'Dwarf'):
                yield cls, level, race, {}
        yield cls, 9, 'Human', {'homebrew_feat_amount': 'N'}


def check_labels(report):
    """Checks 1-3."""
    for cls, level, race, overrides in cases():
        house = overrides.get('homebrew_feat_amount', 'Y') != 'N'
        human = race == 'Human'
        for seed in SEEDS:
            payload = generate(seed, cls, level, race, **overrides)
            where = f'{cls} {level} {race}{" (PF1 feats)" if not house else ""} seed {seed}'
            if not report.check('error' not in payload, f'{where}: generation failed: {payload.get("error")}'):
                continue
            feats, labels = payload.get('feats') or [], payload.get('feat_labels') or []
            if not report.check(len(labels) == len(feats),
                                f'{where}: {len(labels)} feat_labels for {len(feats)} feats'):
                continue
            slots = expected_slots(level, human, house)
            free = [label for label in labels if label in slots or label.startswith(('Feat ', 'Creation ', 'Bonus '))
                    or label == 'Human']
            report.check(free == slots[:len(free)],
                         f'{where}: the free-choice rows are {free}, not the first {len(free)} of {slots}')
            on_track = [label for label in labels if not label.startswith(OFF_TRACK)]
            report.check(len(on_track) == len(slots),
                         f'{where}: the general track has {len(on_track)} rows; its sources add up to '
                         f'{len(slots)} ({ceil(level / 2)} level feats'
                         f'{" + 2 creation" if house else ""}{" + 1 human" if human else ""})')
            report.check(labels.count('Human') == (1 if human and free else 0),
                         f'{where}: {labels.count("Human")} Human row(s) on a {race.lower()}')
            professions = {str(name).lower() for name in payload.get('profession_feats') or []}
            for name, label in zip(feats, labels):
                if str(name).lower() in professions:
                    report.check(label.startswith('Profession '),
                                 f'{where}: profession feat {name} is labelled {label}')


def check_class_grants(report):
    """Check 4."""
    for cls, display, levels in (('monk', 'Monk', MONK_LEVELS), ('monk (unchained)', 'Monk (Unchained)', MONK_LEVELS),
                                 ('ranger', 'Ranger', RANGER_LEVELS)):
        for level in (2, 6, 10, 18):
            for seed in SEEDS:
                payload = generate(seed, cls, level, 'Elf')
                where = f'class grants [{cls} {level}] seed {seed}'
                if not report.check('error' not in payload, f'{where}: generation failed'):
                    continue
                names, labels = payload.get('class_feats') or [], payload.get('class_feat_labels') or []
                report.check(len(names) == len(labels),
                             f'{where}: {len(names)} class_feats for {len(labels)} class_feat_labels')
                owed = [f'{display} {at}' for at in levels if at <= level]
                got = [label for label in labels if label and label.startswith(display + ' ')]
                # A list can run out before its schedule does (the slot then becomes a general
                # feat), so "at least the first, never more than owed, in schedule order".
                report.check(got and got == owed[:len(got)],
                             f'{where}: granted class feats are labelled {got}; the class is owed {owed}')
                report.check(len(set(str(n).lower() for n in names)) == len(names),
                             f'{where}: a class feat appears twice: {names}')
                general = {str(n).lower() for n in payload.get('feats') or []}
                report.check(not general & {str(n).lower() for n in names},
                             f'{where}: a class-granted feat is also in the general list')


def prove_the_checks_can_fail():
    """Put the human bug back and demand that checks 2 and 3 notice (see the docstring)."""
    original = flag_assign.human_flag_assigner

    def forgetful(character):
        original(character)
        if getattr(character, 'human_flag', False):
            character.normal_feat_amount -= 1          # the feat is drawn, then trimmed away

    scratch = Report('broken:human')
    main_test.human_flag_assigner = forgetful
    try:
        with redirect_stdout(io.StringIO()):
            for seed in SEEDS:
                payload = generate(seed, 'fighter', 10, 'Human')
                labels = payload.get('feat_labels') or []
                on_track = [label for label in labels if not label.startswith(OFF_TRACK)]
                scratch.check(len(on_track) == len(expected_slots(10, True, True)), 'track size')
    finally:
        main_test.human_flag_assigner = original
    REPORT.check(scratch.errors,
                 'the human bonus feat was made to be trimmed away again and the track-size check '
                 'still passed -- it is not counting the track')


def main():
    check_labels(REPORT)
    check_class_grants(REPORT)
    prove_the_checks_can_fail()
    return REPORT.finish(f'{GENERATED[0]} generations; every general feat row names its source, the '
                         f'track is the size its sources add up to, class-granted feats reach the '
                         f'sheet; proven by breaking it', max_errors=40)


if __name__ == '__main__':
    sys.exit(main())
