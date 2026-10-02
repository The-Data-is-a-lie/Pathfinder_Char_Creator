"""The default is plain Pathfinder 1e: with the master `homebrew` switch absent, no house rule fires.

    .venv/Scripts/python.exe Backend/scripts/gates/validate_homebrew_off.py

WHY THIS EXISTS
---------------
Ruling (Daniel, 2026-10-02): Sieg's Guide house rules are opt-in behind one `homebrew` key, default
off (utils/house_rules.py). The switch has two layers -- a fold of five legacy flags and a gate on
the rules that never had one -- and a house rule reached by a path that skips both would leak into
every default character without any golden noticing, because the pf1e_* goldens pin three seeds.
This sweeps classes and levels with the switch absent and asserts each house rule's FOOTPRINT on
the payload is empty.

It also generates a few characters WITH the switch on and asserts the footprints are present there.
That half is not decoration: a gate that only checks "empty" passes on a generator that broke the
house rules entirely, so this proves each assertion can fail.

WHAT IT DOES NOT CHECK
----------------------
Combined caster level is a renderer rule (the backend's per-class CL is already RAW), so it is
asserted in the module's and the web sheet's own tests, not here. The sphere `Extra ... Talent`
entries in the feat-tax dicts are display labels on PAID feats, not free grants, and are excluded.
"""
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report  # noqa: E402

from utils.class_func import backstory as _bs  # noqa: E402
_bs._try_ollama = lambda *a, **k: ''

import main_test  # noqa: E402

REPORT = Report('validate_homebrew_off')

# Spread on purpose: a martial, a full caster with Spheres, an initiator, a skill monkey, a
# companion class -- low and high level. Seeds are fixed so a failure replays.
SWEEP = [
    ('fighter', 1), ('fighter', 16), ('wizard', 9), ('cleric', 14), ('rogue', 5),
    ('warlord', 10), ('stalker', 17), ('ranger', 12), ('druid', 7), ('bard', 20),
]
HOUSE_SAMPLES = [('fighter', 12), ('wizard', 11), ('warlord', 13)]

_SPHERE_LABEL = ('extra combat talent', 'extra magic talent')
_TAX_KEYS = ('story_feat_tax_dict', 'flaw_feat_tax_dict', 'flavor_feat_tax_dict',
             'class_feat_tax_dict', 'feats_feat_tax_dict', 'trainer_feat_tax_dict')


def generate(cls, level, seed, homebrew):
    kwargs = dict(class_choice=cls, chosen_BAB='random', multi_class='N', userInput_race='Human',
                  userInput_region='Tal-Falko', alignment_input='random', userInput_gender='random',
                  high_level=level, low_level=level, gold_num=20000, num_dice='4', num_sides='6',
                  use_backstory_api='N', spheres_flag='Y', seed=seed)
    if homebrew:
        kwargs['homebrew'] = True
    with redirect_stdout(io.StringIO()):
        return main_test.generate_random_char(**kwargs)


def footprints(p):
    """Each house rule's visible footprint on one payload, as {rule: evidence or falsy}."""
    free_tax = {k: v for key in _TAX_KEYS for k, v in (p.get(key) or {}).items()
                if v and not str(k).lower().startswith(_SPHERE_LABEL)}
    unlock = [k for k in (p.get('class_features') or {}) if str(k).startswith('Skill Unlock')]
    return {
        'luck block': p.get('luck'),
        'mechanical flaws': p.get('flaw_effects_dict'),
        'story feats': p.get('story_feats'),
        'flavor feats': p.get('flavor_feats'),
        'flaw feats': p.get('flaw_feats'),
        'trainer feats': p.get('trainer_feats'),
        'profession feats': p.get('profession_feats'),
        'skill unlock': unlock or p.get('skill_unlock'),
        'free feat-tax grants': free_tax,
        'inherent bonuses': {k: v for k, v in (p.get('inherents') or {}).items() if v},
        'martial-training feats': p.get('mt_feats'),
        # PF1e grants two traits; anything beyond is the house 8-pick count.
        'traits beyond two': (p.get('selected_traits') or [])[2:],
    }


def main():
    for i, (cls, level) in enumerate(SWEEP):
        seed = 4100 + i
        try:
            p = generate(cls, level, seed, homebrew=False)
        except Exception as exc:                                  # noqa: BLE001
            REPORT.error(f'{cls} {level} seed {seed}: generation raised {type(exc).__name__}: {exc}')
            continue
        REPORT.check(p.get('homebrew') is False,
                     f'{cls} {level} seed {seed}: payload homebrew is {p.get("homebrew")!r}, '
                     f'expected False with the switch absent')
        for rule, evidence in footprints(p).items():
            REPORT.check(not evidence,
                         f'{cls} {level} seed {seed}: house rule "{rule}" fired with homebrew off '
                         f'-- {str(evidence)[:160]}')

    # The other half: the same footprints must APPEAR under homebrew, or the checks above prove
    # nothing. Not every rule fires on every character (flaws roll 0-4), so these are the ones
    # that fire for everybody: luck block, story feats, skill unlock, inherents.
    always = ('luck block', 'story feats', 'skill unlock', 'inherent bonuses', 'traits beyond two')
    for i, (cls, level) in enumerate(HOUSE_SAMPLES):
        seed = 4200 + i
        try:
            p = generate(cls, level, seed, homebrew=True)
        except Exception as exc:                                  # noqa: BLE001
            REPORT.error(f'{cls} {level} seed {seed} (homebrew): generation raised {exc!r}')
            continue
        fp = footprints(p)
        for rule in always:
            REPORT.check(fp[rule], f'{cls} {level} seed {seed}: house rule "{rule}" did NOT fire '
                                   f'with homebrew on -- the off-checks above cannot fail for it')

    return REPORT.finish(f'{len(SWEEP)} plain-PF1e characters, {len(HOUSE_SAMPLES)} homebrew '
                         f'controls')


if __name__ == '__main__':
    sys.exit(main())
