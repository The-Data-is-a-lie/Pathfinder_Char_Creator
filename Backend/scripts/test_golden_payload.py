"""Golden-payload regression for the whole generator (run directly; this repo has no pytest
harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    .venv/Scripts/python.exe Backend/scripts/test_golden_payload.py
    .venv/Scripts/python.exe Backend/scripts/test_golden_payload.py --update
    .venv/Scripts/python.exe Backend/scripts/test_golden_payload.py --config spheres

Generates a fixed set of seeded characters and diffs each payload against a committed snapshot in
Backend/scripts/golden/. A refactor that changes generated output shows up here as a concrete list
of differing keys instead of being discovered weeks later on a Foundry sheet.

WHEN A DIFF IS INTENTIONAL: re-run with --update and commit the regenerated golden IN THE SAME
COMMIT as the code change, so the JSON diff in review shows exactly what the change did to
generated characters.

This only works because generation is reproducible. Three things make it so, and breaking any of
them breaks this test (see changelog):
  * generate_random_char(seed=...) seeds `random` AND numpy (pandas .sample() uses numpy's RNG).
  * feats.py::choosing_feats sorts its candidate pool and accumulates into an insertion-ordered
    dict -- a set of strings iterates in hash order, which Python randomizes per process.
  * Ollama is severed below, so the backstory/archetype paths can't vary with a live model.

The configs deliberately span code paths that would otherwise go uncovered: a martial with no
spellcasting, a prepared caster with domains/school buckets, a multiclass Spheres build, and a
Path of War initiator.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BACKEND = HERE.parents[1]
GOLDEN_DIR = HERE.parent / 'golden'
sys.path.insert(0, str(BACKEND))   # so `from utils...` resolves

from utils.class_func import backstory as _bs

# Sever Ollama outright: generate_backstory only calls it when use_backstory_api is on (we pass "N"),
# but build_archetype.py reaches for the same helper to break scoring ties. Without this the payload
# would depend on whether a model happens to be running locally.
_bs._try_ollama = lambda *a, **k: ''

import main_test


# Shared inputs; each config overrides what it needs. Backstory API off -- it is a network call and
# the prose is disabled in the generator anyway.
_BASE = dict(
    create_new_char='Y', userInput_region='Tal-Falko', chosen_caster_level='random',
    deity_flag='asdfasd', truly_random_feats='Y', inherents='Y', modded_char_sheet='n',
    homebrew_feat_amount='Y', num_dice='4', num_sides='6', gold_num=10000,
    use_backstory_api='N', spheres_flag='N',
)

# The four configs below were chosen so that their UNION populates every buff side-map the export
# builds -- feat/item/quality/class-feature/spell/talent changes AND conditionals. Several of those
# are rare enough that a arbitrary seed misses them (only 17 of 1,586 class_feature_effects entries
# carry conditionals), so the seeds here were selected by sweeping for coverage rather than picked at
# random. Check coverage with scripts/report_buff_coverage.py before changing a seed or config.
CONFIGS = {
    # Martial, no spellcasting: feats, gear, and the weapon/armor QUALITY path. Gold is 400,000
    # against a level-16 wealth-by-level of ~315,000 -- above the table, but only modestly. Named
    # qualities (flaming, keen, ...) are what populate enhancement_effects_dict, and
    # enhancement_chooser only spends on them once the budget exceeds +5, so a poorer character gets
    # a flat bonus and no qualities. This was 5,000,000 while enhancements ran AFTER item_chooser had
    # drained the purse; now that they take a reserved share first, the crutch is no longer needed.
    'martial': dict(_BASE, seed=3002, userInput_race='Human', class_choice='fighter',
                    chosen_BAB='high', multi_class='N', alignment_input='LG',
                    userInput_gender='male', high_level=16, low_level=16, gold_num=400000),
    # Multiclass divine caster + Spheres of Power: spellbooks, bonus spells, domains, spell changes
    # and riders, magic talents, mana pool, casting tradition.
    'caster': dict(_BASE, seed=5004, userInput_race='Human', class_choice='cleric',
                   chosen_BAB='medium', multi_class='Y', alignment_input='NG',
                   userInput_gender='female', high_level=15, low_level=15,
                   gold_num=40000, spheres_flag='Y'),
    # High-level rogue + Spheres of Might: the only config that reaches class-feature CONDITIONALS
    # (rogue talents are 4 of the 17 curated entries) and Spheres-of-Might combat talents.
    'rogue': dict(_BASE, seed=4003, userInput_race='Halfling', class_choice='rogue',
                  chosen_BAB='medium', multi_class='N', alignment_input='CN',
                  userInput_gender='female', high_level=18, low_level=18,
                  gold_num=3000000, spheres_flag='Y'),
    # Path of War initiator: disciplines, maneuvers, stances, initiator level, stance auras.
    'initiator': dict(_BASE, seed=1004, userInput_race='Half-Orc', class_choice='warlord',
                      chosen_BAB='high', multi_class='N', alignment_input='LN',
                      userInput_gender='male', high_level=10, low_level=10),
    # The 25% "trainer-backed" branch with BOTH mentors -- the only config that reaches it (the four
    # above all roll lean, so mentor funding was previously untested). This seed funds a whole
    # 3-feat Martial Training chain off-budget, so it pins the invariant that matters: mentor-funded
    # PoW feats appear in trainer_feats under "(Trainer N - Path of War)" and NOT in `feats`, while
    # the general track still lands at exactly normal_feat_amount.
    'mentor': dict(_BASE, seed=6009, userInput_race='Human', class_choice='fighter',
                   chosen_BAB='high', multi_class='N', alignment_input='LG',
                   userInput_gender='male', high_level=15, low_level=15,
                   gold_num=200000, spheres_flag='Y'),
}


def generate(name):
    """Run the generator for a named config and return its payload."""
    kwargs = dict(CONFIGS[name])
    return main_test.generate_random_char(**kwargs)


def canonical(payload):
    """Stable text form for comparison. sort_keys so payload key ORDER never fails the test (the
    Foundry module and web sheet both read by name); default=str so a stray non-JSON value is
    rendered rather than raising."""
    return json.dumps(payload, indent=1, sort_keys=True, default=str, ensure_ascii=False)


def golden_path(name):
    return GOLDEN_DIR / f'{name}.json'


def diff_keys(old, new):
    """[(key, kind)] for every key that differs, so a failure names what moved."""
    out = []
    for key in sorted(set(old) | set(new)):
        if key not in old:
            out.append((key, 'added'))
        elif key not in new:
            out.append((key, 'removed'))
        elif json.dumps(old[key], sort_keys=True, default=str) != \
                json.dumps(new[key], sort_keys=True, default=str):
            out.append((key, 'changed'))
    return out


def run(names, update):
    failures = []
    GOLDEN_DIR.mkdir(exist_ok=True)

    for name in names:
        payload = generate(name)
        path = golden_path(name)

        if update:
            path.write_text(canonical(payload), encoding='utf-8')
            print(f'  {name}: wrote {path.relative_to(BACKEND.parent)} ({len(payload)} keys)')
            continue

        if not path.exists():
            failures.append(f'{name}: no golden at {path} -- run with --update to create it')
            continue

        old = json.loads(path.read_text(encoding='utf-8'))
        changed = diff_keys(old, payload)
        if changed:
            failures.append(f'{name}: {len(changed)} key(s) differ from the golden')
            for key, kind in changed:
                print(f'    {name}: {key} ({kind})')
        else:
            print(f'  {name}: OK ({len(payload)} keys)')

    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update', action='store_true',
                        help='overwrite the goldens with current output (commit the result)')
    parser.add_argument('--config', action='append', choices=sorted(CONFIGS),
                        help='only run this config (repeatable); default is all')
    args = parser.parse_args()

    names = args.config or sorted(CONFIGS)
    failures = run(names, args.update)

    if args.update:
        print(f'\nUPDATED -- {len(names)} golden(s). Commit them with the change that caused the diff.')
        return 0

    if failures:
        print('\nFAIL')
        for line in failures:
            print(f'  {line}')
        print('\nIf the change is intentional, re-run with --update and commit the new golden.')
        return 1

    print(f'\nPASS -- {len(names)} golden payload(s) match')
    return 0


if __name__ == '__main__':
    sys.exit(main())
