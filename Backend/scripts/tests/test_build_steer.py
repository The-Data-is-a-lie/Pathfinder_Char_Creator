"""The build pin: a pinned build steers the character toward that build, and a miss is reported.

    .venv/Scripts/python.exe Backend/scripts/tests/test_build_steer.py

WHAT THIS ASSERTS
-----------------
A build pin (utils/class_func/build_steer.py) is the one pin that is a steer and not a guarantee:
the build name on the payload is MEASURED by build_archetype.choose_build_archetype, so the pin can
only move the choices that measurement reads. That makes two promises, and both are about generated
characters:

1. **It steers.** Across every build the endpoint offers, far more pinned characters come out as
   their build than the same seeds do unpinned -- at least ``MIN_HIT_SHARE`` of them overall, and
   at least ``MIN_LIFT`` times the unpinned count. Not "every build, every time": spheres,
   disciplines and companions are not steered, and the dice are still the dice.
2. **A miss is said out loud.** Every pinned character either carries its build's name or a
   ``selection_report`` row naming the build -- never neither, never both -- and always generates.

Plus the parts of the steer that are pure enough to pin down without a character: which classes
can be a build, what is offered, the score order, and that explicit pins outrank the build.

SABOTAGE-PROVEN. The sweep ends by making ``selection.pinned_build`` forget the pin and re-running
promise 1 against a scratch report. It must FAIL: if the hit share survives with the steer switched
off, the sweep was measuring the dice.
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
from utils.class_func import build_steer, power_role, selection                     # noqa: E402
from utils.createACharacter import CreateNewCharacter                               # noqa: E402
from utils.util import _available_class_pool                                        # noqa: E402

REPORT = Report('test_build_steer')
SEEDS = (63001, 63002, 63003)
GENERATED = [0]

# Promise 1's two bars. Measured 2026-11-15 over every offered build at four seeds each; the bars
# sit well under the measurement so a seed change does not trip them, and well over what the dice
# manage alone (an unpinned character matches a given build a few times in a hundred).
MIN_HIT_SHARE = 0.55
MIN_LIFT = 5


def generate(seed, pins, **overrides):
    args = dict(class_choice='random', chosen_BAB='random', multi_class='N',
                userInput_race='random', userInput_region='Tal-Falko', alignment_input='random',
                userInput_gender='random', high_level=12, low_level=8, gold_num="",
                num_dice='4', num_sides='6', use_backstory_api='N', spheres_flag='N', seed=seed)
    args.update(overrides)
    GENERATED[0] += 1
    with redirect_stdout(io.StringIO()):
        return main_test.generate_random_char(selection_request=pins, **args)


def fresh_character():
    return CreateNewCharacter(main_test.character_json_config)


def offered_builds():
    character = fresh_character()
    return build_steer.offered(character, sorted(_available_class_pool(character)))


def build_rows(payload, build):
    return [row for row in payload.get('selection_report') or [] if row['pin'] == f'build: {build}']


def check_steering(report):
    """Promises 1 and 2, over every offered build."""
    builds = offered_builds()
    hits = plain_hits = total = 0
    for build in builds:
        for seed in SEEDS:
            payload = generate(seed, {'build': build})
            where = f'build [{build}] seed {seed}'
            if not report.check('error' not in payload,
                                f'{where}: a build pin must not cost the character: {payload.get("error")}'):
                continue
            total += 1
            landed = payload.get('build_archetype') == build
            rows = build_rows(payload, build)
            report.check(landed != bool(rows),
                         f'{where}: came out as {payload.get("build_archetype")!r} with report rows {rows} '
                         f'-- a pinned build is either the label or a report row, never neither or both')
            report.check(all(row['reason'].startswith('came out as ') for row in rows),
                         f'{where}: a miss must say what the character came out as: {rows}')
            hits += landed
            plain_hits += generate(seed, None).get('build_archetype') == build
    if not report.check(total, 'no build was generated at all'):
        return
    share = hits / total
    report.check(share >= MIN_HIT_SHARE,
                 f'only {hits}/{total} pinned characters ({share:.0%}) came out as their build; '
                 f'the steer promises at least {MIN_HIT_SHARE:.0%}')
    report.check(hits >= MIN_LIFT * max(plain_hits, 1),
                 f'{hits} pinned characters matched their build against {plain_hits} unpinned on the '
                 f'same seeds -- the steer should be worth at least {MIN_LIFT}x the dice')
    print(f'  steering: {hits}/{total} pinned characters are their build ({share:.0%}); '
          f'{plain_hits}/{total} of the same seeds unpinned')


def check_classes(report):
    """Which classes can be a build, and what is offered."""
    character = fresh_character()
    pool = sorted(_available_class_pool(character))
    roster = build_steer.roster()
    offered = build_steer.offered(character, pool)
    report.check(build_steer.scorer._FALLBACK.label not in roster,
                 'the fallback label must not be a build that can be pinned')
    report.check(offered and set(offered) <= set(roster), 'offered() names a build outside the roster')
    for name in roster:
        ranked = build_steer.ranked_classes(character, name, pool)
        report.check(bool(ranked) == (name in offered),
                     f'{name}: offered() and ranked_classes() disagree on whether any class fits')
        report.check([fit for fit, _cls in ranked] == sorted((fit for fit, _cls in ranked), reverse=True),
                     f'{name}: ranked_classes() is not best-first')
    # A veto the class itself trips rules the class out; nothing later can fix it.
    for name, entry in roster.items():
        vetoes = {gate['signal'] for gate in entry.get('vetoes') or []}
        if 'caster_primary' in vetoes:
            report.check(build_steer.class_fit(character, 'wizard', name) is None,
                         f'{name} vetoes caster_primary, yet a wizard was judged able to be one')
    # No build pinned: no opinion anywhere, and no class list.
    report.check(build_steer.fitting_classes(character, pool) == [],
                 'fitting_classes() must be [] when no build is pinned')
    report.check(build_steer.stat_priority(character) is None and build_steer.wants_shield(character) is None
                 and build_steer.gate_feats(character) == []
                 and build_steer.next_feat_wish(character, [], set(), {}) is None
                 and build_steer.weapon_pick(character, {}, ['Longsword']) is None
                 and build_steer.armor_band(character, 'H', [None, 'L', 'M', 'H']) == 'H',
                 'an unpinned character must get "no opinion" from every steer function')
    # Every feat name the steer offers the scorer by literal string still moves a signal.
    effects = build_steer.feat_effects(character)
    for word in build_steer._SCORER_FEAT_WORDS:
        report.check(effects.get(word), f'_SCORER_FEAT_WORDS: {word!r} no longer moves any scorer signal')


def check_scores(report):
    """The order the rolled scores are placed in follows the entry."""
    def order_for(build, cls):
        character = fresh_character()
        selection.phase_selection(character, {'build': build})
        character._class_picks = [cls]
        return build_steer.stat_priority(character), character

    for build, entry in build_steer.roster().items():
        gates = [gate['signal'] for gate in entry.get('requires_any') or []]
        weights = entry.get('signals') or {}
        order, _character = order_for(build, 'fighter')
        report.check(sorted(order) == sorted(selection.ABILITIES),
                     f'{build}: stat_priority() is not the six abilities: {order}')
        if gates == ['con_focus']:
            report.check(order[0] == 'con', f'{build} is defined by con_focus, yet Con is not placed first: {order}')
        lean = weights.get('str_over_dex', 0.0) - weights.get('dex_over_str', 0.0)
        if lean > 0:
            report.check(order.index('str') < order.index('dex'), f'{build} leans Str over Dex, order is {order}')
        if lean < 0:
            report.check(order.index('dex') < order.index('str'), f'{build} leans Dex over Str, order is {order}')
    # An explicit stat priority is the caller's own answer and outranks the build.
    character = fresh_character()
    selection.phase_selection(character, {'build': next(iter(build_steer.roster())),
                                          'stat_priority': ['cha', 'int', 'wis', 'dex', 'con', 'str']})
    character._class_picks = ['fighter']
    report.check(power_role.stat_order(character) == ['cha', 'int', 'wis', 'dex', 'con', 'str'],
                 'a pinned stat_priority must outrank the pinned build')


def check_explicit_pins_win(report):
    """A build composes with the other pins and never overrides one."""
    for seed in SEEDS:
        payload = generate(seed, {'build': 'Bruiser', 'classes': [{'name': 'wizard', 'level': 9}]})
        where = f'build + class seed {seed}'
        if not report.check('error' not in payload, f'{where}: {payload.get("error")}'):
            continue
        report.check([c['name'] for c in payload['classes']] == ['wizard'],
                     f'{where}: the pinned class was not kept: {payload["classes"]}')
        report.check(payload.get('build_archetype') == 'Bruiser' or build_rows(payload, 'Bruiser'),
                     f'{where}: a build the pinned class cannot be was neither reached nor reported')
    for seed in SEEDS:
        payload = generate(seed, {'build': 'Bruiser', 'feats': ['Iron Will']},
                           class_choice='fighter')
        where = f'build + feat + class input seed {seed}'
        if not report.check('error' not in payload, f'{where}: {payload.get("error")}'):
            continue
        report.check(payload['classes'][0]['name'] == 'fighter',
                     f'{where}: an explicit class input must outrank the build: {payload["classes"]}')
        held = {str(name).lower() for key in ('feats', 'class_feats', 'story_feats', 'flaw_feats', 'flavor_feats')
                for name in payload.get(key) or []}
        report.check('iron will' in held or any(row['pin'] == 'feats: Iron Will'
                                                for row in payload.get('selection_report') or []),
                     f'{where}: the explicit feat pin was lost to the build')
    unknown = generate(SEEDS[0], {'build': 'Glass Cannon Of Doom'})
    report.check('error' not in unknown and any(row['pin'].startswith('build:') and 'no build' in row['reason']
                                                for row in unknown.get('selection_report') or []),
                 f'an unknown build must be reported, not fatal: {unknown.get("selection_report")}')


def sabotage():
    """Switch the steer off and demand that promise 1 notices (see the docstring)."""
    original = selection.pinned_build
    scratch = Report('sabotage:build')
    selection.pinned_build = lambda character: None
    try:
        with redirect_stdout(io.StringIO()):
            check_steering(scratch)
    finally:
        selection.pinned_build = original
    REPORT.check(scratch.errors,
                 'sabotage [build]: selection.pinned_build was made to forget the pin and the '
                 'steering sweep still passed -- it is measuring the dice, not the steer')


def main():
    check_classes(REPORT)
    check_scores(REPORT)
    check_explicit_pins_win(REPORT)
    check_steering(REPORT)
    sabotage()
    return REPORT.finish(f'{GENERATED[0]} generations; builds steer, misses are reported, '
                         f'explicit pins win, one sabotage proof', max_errors=40)


if __name__ == '__main__':
    sys.exit(main())
