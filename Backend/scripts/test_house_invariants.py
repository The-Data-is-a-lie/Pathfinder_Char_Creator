"""House-rule invariant sweep: every generatable class x level ladder x seeds (run directly; this
repo has no pytest harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    C:\\Python310\\python.exe Backend/scripts/test_house_invariants.py
    C:\\Python310\\python.exe Backend/scripts/test_house_invariants.py --classes fighter,wizard
    C:\\Python310\\python.exe Backend/scripts/test_house_invariants.py --levels 1,20 --seeds 1

Asserts the house-rule FORMULAS (oks/pathfinder/house-rules/), not pinned sheets -- the golden
payload test owns exact-output regression. Per generated character (homebrew flag on, the
generator's default):

  * feats   -- normal == max(0, ceil(L/2) + 2 creation - profession-feat slots);
               story == 1 + L//5; flavor == 1; flaw feats diminish: min(flaws//2 + 1, 3), 0 at 0
               (first 2 flaws grant 1 each, the 4th grants the 3rd)
  * skills  -- sum(skill_ranks) == skill_rank_budget;
               budget == sum(max(1, points(2->4 floor) + best final mental mod) * class level)
                         + background 2L + favored-class {0, L};
               no skill above the 3-ranks-per-level cap; only renderable skills
  * HP      -- sheet_health == sum(max hit die x level) (full-HP house rule);
               Total_HP adds the FINAL Con mod x L, plus favored-class {0, L}
  * homebrew feats -- every placed Metzofitz-only feat carries rules text in
               homebrew_feat_desc_dict (else the Foundry module renders an empty row), and across
               a full sweep at least one Metzofitz pick appears at all
  * sanity  -- generation raises no exception

A failure prints the class/level/seed cell plus the replayable generation seed.
"""
import argparse
import io
import json
import sys
import traceback
from contextlib import redirect_stdout
from math import ceil, floor
from pathlib import Path

HERE = Path(__file__).resolve()
BACKEND = HERE.parents[1]
sys.path.insert(0, str(BACKEND))   # so `from utils...` resolves

from utils import data
from utils.class_func import backstory as _bs

# Sever Ollama like test_golden_payload.py: build_archetype reaches for it to break scoring ties.
_bs._try_ollama = lambda *a, **k: ''

import main_test

LEVELS = [1, 5, 10, 15, 20]
SEEDS = [1101, 2202, 3303]

with open(BACKEND / 'json' / 'class_data.json', encoding='utf-8') as f:
    CLASS_DATA = json.load(f)

FAILURES = []
CHECKS = [0]
METZ_PICKS = [0]

# Metzofitz-only pool names: what metzofitz_feat_frame offers minus every AoN name (collisions
# resolve to AoN, so only names absent from feats.csv prove a homebrew pick happened).
from utils.class_func import feats as _feats
_METZ_ONLY = ({str(n).lower() for n in _feats.metzofitz_feat_frame()['name']}
              - {str(n).lower() for n in _feats.grab_and_clean_feats('data/feats.csv')['name']})


def check(condition, message):
    CHECKS[0] += 1
    if not condition:
        FAILURES.append(message)


def generatable_classes():
    """Same pool as util._available_class_pool: class_data keys minus occult + pending-PoW."""
    excluded = {x.lower() for x in getattr(data, 'occult_classes', [])}
    excluded |= {x.lower() for x in getattr(data, 'pow_classes_pending_foundry', [])}
    return [name for name in CLASS_DATA if name not in excluded]


def hit_die(name):
    return int(str(CLASS_DATA[name]['hit die']).replace('.', '').replace('d', ''))


def skill_points(name):
    points = int(CLASS_DATA[name]['skill points at each level'])
    # the 2->4 rank floor: mirrors misc_homebrew_rules='Y', the generator's default
    return 4 if points == 2 else points


def final_mod(payload, stat):
    score = (payload[stat] + (payload.get('inherents') or {}).get(stat, 0)
             + (payload.get('level_up_stats') or {}).get(stat, 0))
    return floor((score - 10) / 2)


def check_character(cell, payload):
    L = payload['total_level']
    classes = payload['classes']

    # ---- feats ----
    prof_slots = len(payload.get('profession_feats') or [])
    want_normal = max(0, ceil(L / 2) + 2 - prof_slots)
    check(payload['normal_feat_amount'] == want_normal,
          f"{cell}: normal feats {payload['normal_feat_amount']} != ceil({L}/2)+2-{prof_slots} = {want_normal}")
    budget = payload['feat_budget']
    check(budget['story'] == 1 + L // 5,
          f"{cell}: story feats {budget['story']} != 1 + {L}//5 = {1 + L // 5}")
    check(budget['flavor'] == 1, f"{cell}: flavor feats {budget['flavor']} != 1")
    flaws = len(payload['flaw'])
    want_flaw = min(flaws // 2 + 1, 3) if flaws else 0
    check(budget['flaw'] == want_flaw,
          f"{cell}: flaw feats {budget['flaw']} != diminishing({flaws}) = {want_flaw} ({payload['flaw']})")

    # ---- skill ranks ----
    mental = max(final_mod(payload, s) for s in ('int', 'wis', 'cha'))
    base = sum(max(1, skill_points(c['name']) + mental) * c['level'] for c in classes)
    ranks = payload['skill_ranks']
    recorded = payload['skill_rank_budget']
    favored = recorded - base - 2 * L
    check(favored in (0, L),
          f"{cell}: skill budget {recorded} != base {base} + background {2 * L} + favored 0|{L}")
    check(sum(ranks.values()) == recorded,
          f"{cell}: spent {sum(ranks.values())} of skill budget {recorded}")
    over = {s: r for s, r in ranks.items() if r > 3 * L}
    check(not over, f"{cell}: skills above the 3-ranks-per-level cap ({3 * L}): {over}")
    bad = [s for s in ranks if s not in data.skills]
    check(not bad, f"{cell}: ranks on unrenderable skills: {bad}")

    # ---- Metzofitz homebrew feats ----
    placed = []
    for bucket in ('feats', 'story_feats', 'flaw_feats', 'flavor_feats', 'class_feats'):
        placed.extend(str(f) for f in (payload.get(bucket) or []))
    metz = [f for f in placed if f.lower() in _METZ_ONLY]
    METZ_PICKS[0] += len(metz)
    descs = {str(k).lower(): v for k, v in (payload.get('homebrew_feat_desc_dict') or {}).items()}
    undescribed = [f for f in metz if not descs.get(f.lower())]
    check(not undescribed, f"{cell}: Metzofitz feats with no rules text: {undescribed}")

    # ---- HP ----
    max_hd = sum(hit_die(c['name']) * c['level'] for c in classes)
    check(payload['sheet_health'] == max_hd,
          f"{cell}: sheet_health {payload['sheet_health']} != full-HP hit dice {max_hd}")
    want_hp = max_hd + final_mod(payload, 'con') * L
    check(payload['Total_HP'] - want_hp in (0, L),
          f"{cell}: Total_HP {payload['Total_HP']} != {want_hp} (+favored 0|{L})")


def run(classes, levels, seeds):
    total = len(classes) * len(levels) * len(seeds)
    done = 0
    for name in classes:
        for level in levels:
            for seed in seeds:
                cell = f"{name} L{level} seed {seed}"
                done += 1
                try:
                    with redirect_stdout(io.StringIO()):
                        payload = main_test.generate_random_char(
                            class_choice=name, chosen_BAB='high', multi_class='N',
                            userInput_race='random', userInput_region='Tal-Falko',
                            alignment_input='random', userInput_gender='random',
                            high_level=level, low_level=level, gold_num=10000,
                            num_dice='4', num_sides='6', use_backstory_api='N',
                            spheres_flag='N', seed=seed)
                except Exception:
                    CHECKS[0] += 1
                    tail = traceback.format_exc().strip().splitlines()
                    FAILURES.append(f"{cell}: generation raised -- {tail[-1]} "
                                    f"(replay with seed={seed})")
                    continue
                check_character(f"{cell} (gen seed {payload.get('generation_seed')})", payload)
        print(f"  {name}: ok through L{levels[-1]} ({done}/{total})")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--classes', help='comma-separated subset (default: every generatable class)')
    parser.add_argument('--levels', help=f'comma-separated levels (default {LEVELS})')
    parser.add_argument('--seeds', type=int, default=len(SEEDS),
                        help=f'how many of the fixed seeds to run (default {len(SEEDS)})')
    args = parser.parse_args()

    classes = args.classes.split(',') if args.classes else generatable_classes()
    unknown = [c for c in classes if c not in CLASS_DATA]
    if unknown:
        print(f"unknown classes: {unknown}")
        return 2
    levels = [int(x) for x in args.levels.split(',')] if args.levels else LEVELS
    seeds = SEEDS[:max(1, args.seeds)]

    total = len(classes) * len(levels) * len(seeds)
    print(f"sweeping {len(classes)} classes x {levels} x {len(seeds)} seed(s) "
          f"= {total} generations")
    run(classes, levels, seeds)

    # Existence check only on a sweep big enough that zero picks means the wiring broke, not luck.
    if total >= 100:
        check(METZ_PICKS[0] > 0,
              f"no Metzofitz homebrew feat appeared in {total} generations -- pool wiring broken?")
    print(f"  Metzofitz picks across the sweep: {METZ_PICKS[0]}")

    print()
    if FAILURES:
        print(f"FAIL -- {len(FAILURES)} of {CHECKS[0]} checks failed:")
        for message in FAILURES:
            print("  *", message)
        return 1
    print(f"PASS -- {CHECKS[0]} checks")
    return 0


if __name__ == '__main__':
    sys.exit(main())
