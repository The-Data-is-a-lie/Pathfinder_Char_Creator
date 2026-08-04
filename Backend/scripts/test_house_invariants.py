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
               (first 2 flaws grant 1 each, the 4th grants the 3rd; behind misc_homebrew_rules,
               the generator's default)
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
# Bonded-creature branch coverage (#35). Counted rather than assumed, because the #30 stack review's
# "both=0, neither=0 over 400 generations" was measured by a sample that could not reach the path it
# claimed to clear.
BOND = {'granted': 0, 'absent': 0, 'both': 0, 'neither': 0, 'druid_flip': 0}

# Metzofitz-only pool names: what metzofitz_feat_frame offers minus every AoN name (collisions
# resolve to AoN, so only names absent from feats.csv prove a homebrew pick happened).
from utils.class_func import feats as _feats
_METZ_ONLY = ({str(n).lower() for n in _feats.metzofitz_feat_frame()['name']}
              - {str(n).lower() for n in _feats.grab_and_clean_feats('data/feats.csv')['name']})

# Psionics. The twelve are ordinary class_data entries, so the sweep above already rolls every one
# of them at every level -- these sets only say which of the three manifesting shapes each belongs
# to (see utils/class_func/psionics.py). Sourced from data.py so a class moving between shapes is a
# one-place edit.
_PSIONIC = {x.lower() for x in getattr(data, 'psionic_class', [])}
_PP_ONLY = {x.lower() for x in getattr(data, 'psionic_pp_only_classes', [])}   # aegis: PP, no powers
# The soulknife manifests nothing at all: no stat, no power points, no powers. It still gets a
# payload entry, because a class silently absent from `manifesters` is indistinguishable from a bug.
_NO_MANIFESTING = {'soulknife'}

# The published class tables, read straight from the data file rather than through psionics.py: the
# point of the check below is to catch the generator disagreeing with the source of truth, which it
# cannot do if both read through the same accessor.
with open(BACKEND / 'json' / 'class_data' / 'psionics' / 'psionic_powers_known.json',
          encoding='utf-8') as f:
    PSIONIC_TABLES = json.load(f)


def check(condition, message):
    CHECKS[0] += 1
    if not condition:
        FAILURES.append(message)


def generatable_classes():
    """Same pool as util._available_class_pool: class_data keys minus occult + pending PoW/psionic."""
    excluded = {x.lower() for x in getattr(data, 'occult_classes', [])}
    excluded |= {x.lower() for x in getattr(data, 'pow_classes_pending_foundry', [])}
    excluded |= {x.lower() for x in getattr(data, 'psionic_classes_pending', [])}
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

    # ---- psionics ----
    psionic = [c for c in classes if c['name'] in _PSIONIC]
    manifesters = payload.get('manifesters')
    descs = payload.get('powers_desc_dict')
    check(isinstance(manifesters, list) and isinstance(descs, dict),
          f"{cell}: payload is missing the manifesters / powers_desc_dict block")
    if isinstance(manifesters, list) and isinstance(descs, dict):
        # One entry per psionic class and nothing else -- an extra entry means a non-psionic class
        # leaked in, a missing one means a manifester vanished from the sheet.
        check(sorted(m['name'] for m in manifesters) == sorted(c['name'] for c in psionic),
              f"{cell}: manifesters {[m['name'] for m in manifesters]} "
              f"!= psionic classes {[c['name'] for c in psionic]}")
        # Powers only ever come from a manifester, so an empty pool must mean an empty dict.
        if not psionic:
            check(not descs, f"{cell}: powers_desc_dict is populated on a non-psionic character")

        for m in manifesters:
            name = m['name']
            tag = f"{cell}: {name}"
            entry = next((c for c in psionic if c['name'] == name), None)
            if entry is None:
                continue
            table = PSIONIC_TABLES.get(name, {})
            # Manifester level is the class level (no cross-class stacking in psionics), clamped at
            # 20 because the published tables stop there -- the payload exports the clamped value,
            # so it is recomputed here rather than read back from `classes`.
            check(m['level'] == entry['level'],
                  f"{tag}: manifester entry level {m['level']} != class level {entry['level']}")
            check(m['manifester_level'] == min(entry['level'], 20),
                  f"{tag}: manifester level {m['manifester_level']} != min({entry['level']}, 20)")
            row = min(max(m['manifester_level'], 1), 20) - 1

            if name in _NO_MANIFESTING:
                check(not m['manifesting_stat'] and not m['pp_per_day'] and not m['powers_chosen'],
                      f"{tag}: manifests nothing, but carries "
                      f"stat={m['manifesting_stat']!r} pp={m['pp_per_day']} "
                      f"powers={len(m['powers_chosen'])}")
                continue

            check(m['manifesting_stat'] in ('str', 'dex', 'con', 'int', 'wis', 'cha'),
                  f"{tag}: manifesting stat {m['manifesting_stat']!r} is not an ability")
            # A key ability of 9 or lower cannot manifest AT ALL -- not badly, at all -- so the
            # whole record legitimately reads zero. Everything below assumes the gate is passed.
            if final_mod(payload, m['manifesting_stat']) < 0:
                continue

            # Power points = the class table at manifester level, PLUS floor(mod x ML / 2). The
            # formula is restated rather than imported so a change to psionics.py has to be a
            # deliberate change here too -- that is the point of an invariant test.
            base_pp = table.get('pp_per_day', [0] * 20)[row]
            bonus = max(0, floor(final_mod(payload, m['manifesting_stat']) * m['manifester_level'] / 2))
            check(m['pp_per_day'] == base_pp + bonus,
                  f"{tag}: pp {m['pp_per_day']} != table {base_pp} + bonus {bonus}")

            if name in _PP_ONLY:
                check(not m['powers_chosen'],
                      f"{tag}: spends power points on class options, but knows "
                      f"{len(m['powers_chosen'])} power(s)")
                continue

            want_max = table.get('max_power_level', [0] * 20)[row]
            check(m['max_power_level'] == want_max,
                  f"{tag}: max power level {m['max_power_level']} != table {want_max}")
            want_known = table.get('powers_known', [0] * 20)[row]
            check(len(m['powers_chosen']) == want_known,
                  f"{tag}: knows {len(m['powers_chosen'])} powers != table {want_known}")
            # powers_known_list is how the sheet groups the same powers by level, so the two views
            # of one fact must agree.
            check(sum(m['powers_known_list']) == len(m['powers_chosen']),
                  f"{tag}: powers_known_list sums to {sum(m['powers_known_list'])} "
                  f"but {len(m['powers_chosen'])} powers were chosen")
            check(len(set(m['powers_chosen'])) == len(m['powers_chosen']),
                  f"{tag}: duplicate powers in powers_chosen")
            # Same failure the Metzofitz-feat check guards: a name with no rules text renders as an
            # empty row in Foundry and as nothing at all on the web sheet.
            missing = [p for p in m['powers_chosen'] if not descs.get(p)]
            check(not missing, f"{tag}: powers with no rules text: {missing[:5]}")
            if name == 'psion':
                # The discipline decides the psion's whole power list, so it cannot be blank.
                check(m['discipline'], f"{tag}: no discipline chosen")

    # ---- OGL section 10 ----
    # Serving extracted mechanics is Distribution, so every payload must point at the licence.
    check(payload.get('license_url'), f"{cell}: payload carries no license_url")

    # ---- HP ----
    max_hd = sum(hit_die(c['name']) * c['level'] for c in classes)
    check(payload['sheet_health'] == max_hd,
          f"{cell}: sheet_health {payload['sheet_health']} != full-HP hit dice {max_hd}")
    want_hp = max_hd + final_mod(payload, 'con') * L
    check(payload['Total_HP'] - want_hp in (0, L),
          f"{cell}: Total_HP {payload['Total_HP']} != {want_hp} (+favored 0|{L})")

    check_bonded_creatures(cell, payload)


def check_bonded_creatures(cell, payload):
    """Map #18, slice K (#35). The stat-block arithmetic is gated species-by-species in
    `validate_companion_stats.py`; what is checkable only HERE is the shape of the emitted list and
    the druid flip, both of which need a whole generated character.

    The flip is the regression test for F's rewire, and it is here because of how the original
    measurement failed: "both=0, neither=0 over 400 generations" was reported by a sample that never
    rolled an archetype and so could not reach the broken path. A sample that cannot reach a defect
    reports zero forever, so this counts BRANCHES REACHED and fails if the sweep never saw one.
    """
    entries = payload.get('bonded_creatures')
    check(isinstance(entries, list),
          f"{cell}: bonded_creatures is {type(entries).__name__}, not a list")
    if not isinstance(entries, list):
        return

    for entry in entries:
        tag = f"{cell}: {entry.get('grantor')}/{entry.get('type')}"
        check(entry.get('type') in ('companion', 'mount', 'familiar', 'eidolon'),
              f"{tag}: type {entry.get('type')!r} is not a bonded-creature type")

        if not entry.get('species'):
            BOND['absent'] += 1
            # D9: an absence entry is the record of WHY there is no creature, so it must carry one.
            check(entry.get('outcome') and entry['outcome'] != 'granted',
                  f"{tag}: no species but outcome is {entry.get('outcome')!r}")
            check(entry.get('stats') is None,
                  f"{tag}: absence entry carries a stats block")
            continue

        BOND['granted'] += 1
        check(entry.get('effective_level', 0) >= 1,
              f"{tag}: granted at effective level {entry.get('effective_level')!r}")
        stats = entry.get('stats')
        check(isinstance(stats, dict), f"{tag}: species {entry['species']!r} has no stats block")
        if not isinstance(stats, dict):
            continue

        # #31/D2: the backend is the SOLE source of these numbers, so a missing one is not something
        # a renderer can fill in -- the standalone web sheet has no game system to fall back on.
        for field in ('hp', 'ac', 'touch_ac', 'flat_footed_ac', 'bab', 'cmb', 'cmd', 'hd', 'size'):
            check(stats.get(field) is not None, f"{tag}: stats.{field} is None")
        check(stats.get('hp', 0) >= 1, f"{tag}: hp {stats.get('hp')}")
        check(stats.get('touch_ac', 0) <= stats.get('ac', 0),
              f"{tag}: touch AC {stats.get('touch_ac')} exceeds full AC {stats.get('ac')}")
        check(stats.get('hd') == (entry.get('chassis') or {}).get('hd'),
              f"{tag}: stats.hd {stats.get('hd')} != chassis hd "
              f"{(entry.get('chassis') or {}).get('hd')} -- the chassis is re-read after stacking, "
              f"so these cannot disagree")
        check(all(v is not None for k, v in (stats.get('abilities') or {}).items() if k != 'int'),
              f"{tag}: a non-Int ability score is None ({stats.get('abilities')})")

        # Ticket 04: `size_change` exists exactly when the advancement grew the creature, and its
        # values are provenance for numbers already totalled in. Present-when-it-should-not-be is
        # the failure that would make a renderer apply the geometry twice.
        start = next((v for k, v in (entry.get('species_stats') or {}).items()
                      if str(k) == 'starting statistics' and isinstance(v, dict)), {})
        grew = str(start.get('size') or '').strip().lower() != str(stats.get('size') or '').lower()
        check(bool(stats.get('size_change')) == grew,
              f"{tag}: size {start.get('size')!r} -> {stats.get('size')!r} but size_change is "
              f"{stats.get('size_change')!r}")

    # ---- the druid flip (F's rewire) ----
    # Only meaningful on a character whose ONLY domain source is the druid bond; clerics and
    # inquisitors get domains from their own subsystem and would read as a false "both".
    names = {c['name'] for c in payload['classes']}
    if 'druid' not in names or names & {'cleric', 'inquisitor'}:
        return
    druid = [e for e in entries if e.get('grantor') == 'druid']
    if not druid:
        return
    got_creature = any(e.get('species') for e in druid)
    got_domain = bool(payload.get('full_domain'))
    removed = any(e.get('outcome') == 'archetype_removed' for e in druid)

    if got_creature and got_domain:
        BOND['both'] += 1
        check(False, f"{cell}: druid has BOTH a companion and a domain -- the flip is not "
                     f"exclusive (the defect a fresh per-row draw reintroduces without F's rewire)")
    elif not got_creature and not got_domain and not removed:
        BOND['neither'] += 1
        check(False, f"{cell}: druid has NEITHER a companion nor a domain, and no archetype "
                     f"removed the feature")
    BOND['druid_flip'] += 1


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

    # The companion checks above are all conditional on a creature existing, so a sweep that rolled
    # none would print PASS having asserted nothing. Say so instead.
    if total >= 100:
        check(BOND['granted'] > 0,
              f"no bonded creature was granted in {total} generations -- every companion check "
              f"above was skipped, so this run proves nothing about them")
        check(BOND['druid_flip'] > 0,
              f"the druid flip was never reached in {total} generations")
    print(f"  bonded creatures: {BOND['granted']} granted, {BOND['absent']} absence entries, "
          f"{BOND['druid_flip']} druid flips (both={BOND['both']}, neither={BOND['neither']})")

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
