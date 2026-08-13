"""House-rule invariant sweep: every generatable class x level ladder x seeds (run directly; this
repo has no pytest harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    C:\\Python310\\python.exe Backend/scripts/tests/test_house_invariants.py
    C:\\Python310\\python.exe Backend/scripts/tests/test_house_invariants.py --classes fighter,wizard
    C:\\Python310\\python.exe Backend/scripts/tests/test_house_invariants.py --levels 1,20 --seeds 1

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import (BACKEND, Report, choice_schedule, schedule_due, schedule_levels,  # noqa: E402
                      schedule_row)
import power_metric  # noqa: E402

# --score (map: optimal-builder, ticket 03). OFF by default, so CI pays nothing: the flag only adds
# a scoring call to the per-character hook every generation already passes through, which is the
# class-choices ticket 05 pattern -- a whole coverage layer for ZERO new generations. Generation is
# the expensive part of this sweep; a check hanging off it is nearly free.
SCORING = False
SCORE_ROWS = []
# Axes no character can legitimately have none of. A zero here is the fold silently failing.
NONZERO_AXES = ('ac', 'hp', 'to_hit')

# The pick schedule, read from disk rather than through the generator's resolver.
SCHEDULE = choice_schedule()

from utils import data  # noqa: E402
from utils.class_func import backstory as _bs  # noqa: E402

# Sever Ollama like test_golden_payload.py: build_archetype reaches for it to break scoring ties.
_bs._try_ollama = lambda *a, **k: ''

import main_test  # noqa: E402

LEVELS = [1, 5, 10, 15, 20]
SEEDS = [1101, 2202, 3303]

with open(BACKEND / 'json' / 'class_data.json', encoding='utf-8') as f:
    CLASS_DATA = json.load(f)

REPORT = Report('test_house_invariants')
METZ_PICKS = [0]
# Bonded-creature branch coverage (#35). Counted rather than assumed, because the #30 stack review's
# "both=0, neither=0 over 400 generations" was measured by a sample that could not reach the path it
# claimed to clear.
BOND = {'granted': 0, 'absent': 0, 'both': 0, 'neither': 0, 'druid_flip': 0,
        'feats': 0, 'tax': 0, 'flaws': 0, 'applied': 0}

# The feat economy's own data, imported rather than restated -- the pool and the tax allowlist are
# curated files and this test must fail when a creature strays outside them, not when a copy here
# falls behind them. `TYPE_NOUNS` is the label vocabulary; only the chassis-driven types have feats.
from utils.class_func.companion_feats import CHASSIS_TYPES as _CHASSIS_TYPES, TYPE_NOUNS as _NOUNS
# The ceiling itself, imported rather than restated -- a copy here could agree with a
# drifted generator, which is the failure this whole file exists to prevent.
from utils.class_func.level_and_bab import MAX_CHARACTER_LEVEL
COMPANION_FEAT_TYPES = {kind: _NOUNS[kind] for kind in _CHASSIS_TYPES}
with open(BACKEND / 'json' / 'animal_companion.json', encoding='utf-8') as _fh:
    _CHASSIS = json.load(_fh)
COMPANION_POOL = _CHASSIS.get('feats') or []
COMPANION_TAX_CHILDREN = _CHASSIS.get('tax_children') or []

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

# Free talents, named talents and the subsystem bucket map are IMPORTED rather than restated: the
# module owns them, and a second copy here would let the gate agree with a drifted generator.
from utils.class_func.psionics import FREE_TALENTS, MANDATED_TALENTS, SUBSYSTEM_BUCKET

# The published class tables, read straight from the data file rather than through psionics.py: the
# point of the check below is to catch the generator disagreeing with the source of truth, which it
# cannot do if both read through the same accessor.
with open(BACKEND / 'json' / 'class_data' / 'psionics' / 'psionic_powers_known.json',
          encoding='utf-8') as f:
    PSIONIC_TABLES = json.load(f)

# Occult Adventures. class -> dataset -> the payload bucket its picks land in; must match the
# generic_class_option_chooser calls in main_test.py and the datasets in
# Backend/scripts/build_occult_class_data.py. validate_occult_data.py owns the DATA (are the pools
# well-formed, do the schedules reach the counts the prose promises); this owns the OUTPUT (did a
# generated character actually receive them).
_OCCULT_BUCKETS = {
    'occultist': {'implements': 'implements', 'focus powers': 'focus_powers'},
    'kineticist': {'elemental focus': 'elemental_focus', 'wild talents': 'wild_talents',
                   'infusions': 'infusions'},
    'medium': {'spirits': 'medium_spirit'},
    'mesmerist': {'mesmerist tricks': 'mesmerist_tricks', 'bold stare': 'bold_stare'},
    'psychic': {'disciplines': 'psychic_discipline',
                'phrenic amplifications': 'phrenic_amplifications'},
    'spiritualist': {'emotional focus': 'emotional_focus'},
}
# The option pools themselves, so a pick can be checked against the list it was supposed to come
# from. Read from the files rather than through the chooser, for the same reason the psionics
# tables above are: a gate that reads through the code it is gating cannot catch that code drifting.
_OCCULT_OPTIONS = {}
for _name in _OCCULT_BUCKETS:
    with open(BACKEND / 'json' / 'class_data' / f'{_name}.json', encoding='utf-8') as f:
        _OCCULT_OPTIONS[_name] = json.load(f)
# Occult branch coverage, same rule as BOND below: every occult check is conditional on an occult
# class being rolled, so a sweep that rolled none would print PASS having asserted nothing.
OCCULT = {'chars': 0, 'picks': 0, 'multi_pick_buckets': 0, 'kineticists': 0, 'casters': 0}


def check(condition, message):
    return REPORT.check(condition, message)


# ---------------------------------------------------------------- class choices (ticket 05)
# Buckets this check cannot attribute, and why. Each is a KNOWN defect owned by class-choices
# ticket 04, not an excuse: asserting on them would fail on characters that are behaving exactly
# as the (wrong) code intends, which trains people to ignore the gate.
CHOICE_SKIP = {
    ('oracle', 'mysteries'):
        "the mystery and the revelations share one bucket -- both call sites pass "
        "dict_name='mysteries' -- so neither count can be read alone (ticket 02 -> 04)",
    ('sorcerer', 'Talents'): "default bucket name; see below",
    ('bloodrager', 'Talents'): "default bucket name; see below",
    ('cavalier', 'Talents'): "default bucket name; see below",
    ('samurai', 'Talents'): "default bucket name; see below",
    ('warpriest', 'Talents'): "default bucket name; see below",
    ('inquisitor', 'Talents'): "default bucket name; see below",
}
# The 'Talents' entries above share one cause: six call sites omit dict_name=, so bloodlines,
# orders, blessings and inquisitions all land in generic_class_option_chooser's DEFAULT bucket.
# On a single-class sweep character the count would in fact be readable -- but the moment two of
# those classes are rolled together the bucket merges and the count is meaningless, so this check
# refuses to assert on a bucket whose name is known not to identify its contents. Deleting these
# entries is part of ticket 04's fix, and the gate below fails if the list stops matching the table.
CHOICE_COVERAGE = {'chars': 0, 'buckets': 0, 'picks': 0, 'stamps': 0, 'skipped': 0, 'capped': 0}

# ---- Inherent luck (map: inherent-luck, ticket 06) -------------------------------------------- #
# The BEHAVIOUR layer. Its partner is scripts/gates/validate_luck.py, which asserts the DATA without
# generating anything. The two share no code ON PURPOSE: the class-choices map proved that
# perturbing a table and re-running a behaviour check PASSES, because the generator reads the same
# table. A table can never be its own witness.
#
# So the Doc's numbers are restated HERE as literals rather than imported from
# utils.class_func.luck. That looks like duplication and is the opposite: it is what makes
# sabotaging luck.py fail this file. Importing LUCK_CAP_POSITIVE would make the assertion
# "25 == 25" no matter what the constant became.
LUCK_CAP_POS = 25            # "The positive cap for luck is +25 ..."
LUCK_CAP_NEG = -50           # "... and the negative cap is -50."
LUCK_CAP_DIMORPHIC = 40      # "each value is equal and has a natural cap of 40"
LUCK_DIVISOR = 5             # "Luck Mod = Luck Score / 5", floored (table ruling)
E_KAT_CAP = 99
LUCK_BUY = {'skill_ranks': 5, 'hp': 5, 'level_up_points': 1}
LUCK_COVERAGE = {'chars': 0, 'stakes': 0, 'buy': 0, 'sell': 0, 'with_feats': 0, 'chains': 0,
                 'with_traits': 0, 'negative_traits': 0, 'deep_sale': 0,
                 'Default': 0, 'Proximity': 0, 'Dimorphic': 0, 'negative': 0, 'nonzero_mod': 0}
# The ten NEGATIVE Luck Traits, by name. They were unreachable by any generated character until
# sellers were let back into the E-Kat economy, so the census below asserts that at least one is
# actually bought across the sweep -- a count of zero means the unlock has silently regressed, and
# that is invisible from the trait total alone.
NEGATIVE_TRAIT_NAMES = set()
# The luck block's field roster, re-declared here rather than imported from validate_luck.py -- the
# same deliberate duplication as LUCK_CAP_POS above, so sabotaging one layer cannot satisfy the other.
LUCK_BLOCK_KEYS = {'type', 'score', 'values', 'mod', 'cap', 'floor', 'e_kat_earned', 'e_kat_reserve',
                   'e_kat_store_cap', 'traits', 'trait_benefits', 'trait_changes', 'vault',
                   'vault_cap', 'dr_pool', 'twist_fate_per_day', 'feats', 'luck_feats',
                   'derivation', 'negative_feats', 'audit', 'payout_changes', 'attribute_bumps', 'stake'}
# The pools the audit accounts for. `skill_ranks` is the BUDGET that moved; the stake's payout calls
# the same thing `skill_points` (what the Doc sells). Both spellings are real and neither is a typo.
LUCK_AUDIT_POOLS = {'hp', 'skill_ranks', 'attribute_points', 'feats'}
# The pf1 targets the payout is allowed to arrive on. `mhp` and `bonusSkillRanks` are pf1's own
# names for max hit points and the sheet's bonus-skill-rank pool; the six abilities carry the
# attribute points. A target outside this set would not crash Foundry -- the change would simply
# never apply, which is invisible until someone re-adds the numbers by hand.
PF1_ABILITIES = ('str', 'dex', 'con', 'int', 'wis', 'cha')
PF1_PAYOUT_TARGETS = {'mhp', 'bonusSkillRanks', *PF1_ABILITIES}
# pf1 change targets this project is allowed to emit for Luck Traits. A whitelist rather than a
# comment, on the MOD_CRITICAL precedent: a stale `critical: "onCrit"` in a doc silently broke six
# weapons, and only a validator caught it. An unknown target is not a crash in Foundry -- the change
# simply never applies, which is invisible until someone audits a save by hand.
PF1_CHANGE_TARGETS = {'will', 'fort', 'ref', 'nac', 'ac', 'allSavingThrows', 'allChecks',
                      'attack', 'skills', 'cmd', 'cmb', 'init', 'mhp', 'cl'}
PF1_BONUS_TYPES = {'untyped', 'untypedPerm', 'base', 'enh', 'dodge', 'haste', 'inherent',
                   'deflection', 'morale', 'luck', 'sacred', 'insight', 'resist', 'profane',
                   'trait', 'racial', 'size', 'competence', 'circumstance', 'alchemical'}
# Distinct seeds for check_luck_branches. The main sweep's three seeds cannot reach selling or
# Dimorphic -- luck is rolled early enough to be seed-locked, so 1,020 generations sample three luck
# draws. These are fixed, so the coverage is deterministic, not flaky.
LUCK_BRANCH_SEED_BASE = 40000
LUCK_BRANCH_SEEDS = 200

with open(BACKEND / 'json' / 'feats' / 'e_kat_feats.json', encoding='utf-8') as f:
    E_KAT_TABLE = {k: v for k, v in json.load(f).items() if not k.startswith('_')}
with open(BACKEND / 'json' / 'feats' / 'luck_traits.json', encoding='utf-8') as f:
    LUCK_TRAIT_TABLE = {k: v for k, v in json.load(f).items() if not k.startswith('_')}
NEGATIVE_TRAIT_NAMES.update(k for k, v in LUCK_TRAIT_TABLE.items() if v.get('category') == 'negative')
# Positive luck feats that are NOT E-Kat feats -- hero point feats and the luck-subject feats. They
# ride the ordinary pool, so any character can hold one, including a seller and a character with no
# luck stake at all. Each grants a flat +1.
with open(BACKEND / 'json' / 'feats' / 'luck_feats.json', encoding='utf-8') as f:
    LUCK_FEAT_TABLE = {k: v for k, v in json.load(f).items() if not k.startswith('_')}


def _feat_luck(names):
    """Luck owed for a set of held E-Kat feats, recomputed from the curated effects.

    The generic +1 applies only to feats with NO explicit bonus -- Ass Pull, It Just Works and Luck
    God state +4 each and do not also collect it. Getting this wrong in the pipeline is a silent +5,
    which is exactly what this recomputation exists to catch.
    """
    total = 0
    for name in names:
        effects = E_KAT_TABLE[name]['effects']
        total += effects['luck_bonus'] or (1 if effects['grants_generic_luck'] else 0)
    return total


def check_luck(cell, payload):
    """The luck subsystem on a generated character (map: inherent-luck).

    Hung on the existing sweep rather than given its own generations: class-choices ticket 05 added
    its whole coverage for ZERO new characters that way, and this needs the same population.
    """
    lk = payload.get('luck')
    # misc_homebrew_rules defaults on for the sweep, so every character must carry a block. A None
    # here means the flag silently flipped, not that this character happens to be unlucky.
    if lk is None:
        check(False, f"{cell}: no luck block -- misc_homebrew_rules is on for this sweep")
        return
    LUCK_COVERAGE['chars'] += 1

    # ---- the block's SHAPE, against an independently declared roster ----
    # validate_luck.py declares the same names as its DATA-layer contract. Both renderers index this
    # block by name, so a field silently renamed or dropped is a blank panel on the sheet rather than
    # a crash -- which is exactly the failure this file exists to catch early.
    check(set(lk) == LUCK_BLOCK_KEYS,
          f"{cell}: luck block keys drifted -- missing {sorted(LUCK_BLOCK_KEYS - set(lk))}, "
          f"unexpected {sorted(set(lk) - LUCK_BLOCK_KEYS)}")

    score, cap = lk['score'], lk['cap']
    LUCK_COVERAGE[lk['type']] = LUCK_COVERAGE.get(lk['type'], 0) + 1

    # ---- the caps hold, at EVERY level in the supported band ----
    base_cap = LUCK_CAP_DIMORPHIC if lk['type'] == 'Dimorphic' else LUCK_CAP_POS
    check(cap >= base_cap and (cap - base_cap) % 5 == 0,
          f"{cell}: luck cap {cap} is not {base_cap} plus a whole number of Expanded Luck steps")
    check(LUCK_CAP_NEG <= score <= cap,
          f"{cell}: luck score {score} outside [{LUCK_CAP_NEG}, {cap}]")

    # ---- the derived field cannot drift from its source ----
    # Floor toward -infinity, which is the ruling: -12 // 5 == -3, not -2.
    check(lk['mod'] == score // LUCK_DIVISOR,
          f"{cell}: luck mod {lk['mod']} != floor({score}/{LUCK_DIVISOR}) = {score // LUCK_DIVISOR}")
    check(lk['dr_pool'] == max(0, score),
          f"{cell}: DR pool {lk['dr_pool']} != the positive part of the score ({max(0, score)})")

    # ---- the audit must ACCOUNT, on every character ----
    # It exists to prove the payout reached the budgets, so an audit that does not reconcile is
    # worse than none at all -- it would be evidence for a number that never moved. Checked for
    # buyers and stake-less characters too: their rows are no-ops, and a no-op that fails to
    # balance means a pool is being adjusted somewhere this record does not see.
    _audit = lk['audit']
    check(set(_audit) == LUCK_AUDIT_POOLS,
          f"{cell}: audit covers {sorted(_audit)}, expected {sorted(LUCK_AUDIT_POOLS)}")
    for _pool, _row in _audit.items():
        check(set(_row) == {'before', 'spent', 'received', 'after', 'final', 'luck_cost'},
              f"{cell}: audit row {_pool} has keys {sorted(_row)}")
        # `received` is NOT part of this sum. The payout is no longer applied to these budgets --
        # it is delivered as pf1 changes on the Negative Luck Payout item, because the module builds
        # actor HP from `total_rolled_hp` and everything the backend added to `Total_HP` was
        # invisible on the sheet. So the budget arithmetic is purely the BUY side.
        check(_row['before'] - _row['spent'] == _row['after'],
              f"{cell}: audit row {_pool} does not balance: "
              f"{_row['before']} - {_row['spent']} != {_row['after']}")
        check(_row['spent'] >= 0 and _row['received'] >= 0,
              f"{cell}: audit row {_pool} has a negative movement: {_row}")
        # A pool can only move in ONE direction: a character either bought luck with it or was paid
        # from it. Both non-zero would mean the two halves of the economy ran on the same budget.
        check(not (_row['spent'] and _row['received']),
              f"{cell}: audit row {_pool} both spent {_row['spent']} and received "
              f"{_row['received']} -- a pool cannot be on both sides of the trade")
    # The two rows whose `final` is a number printed elsewhere on the sheet must equal it, or the
    # audit is quietly describing a different quantity than the one the player reads.
    check(_audit['hp']['final'] == payload['Total_HP'],
          f"{cell}: audit HP final {_audit['hp']['final']} != sheet Total_HP {payload['Total_HP']}")
    check(_audit['skill_ranks']['final'] == payload['skill_rank_budget'],
          f"{cell}: audit skill final {_audit['skill_ranks']['final']} != sheet skill_rank_budget "
          f"{payload['skill_rank_budget']}")

    # THE TABLE MUST CLOSE. Each row's luck_cost inverts the Doc's rate for that route, so the four
    # sum to the magnitude sold. Checked against the STAKE's target rather than the final score: a
    # Luck Trait (Increase Luck) can move the score afterwards, and only the sale bought these rows.
    # Without this the column is decoration -- four numbers nobody can check against anything.
    if lk['stake'] and lk['stake']['direction'] == 'sell':
        _cost = sum(_r['luck_cost'] for _r in _audit.values())
        check(_cost == -lk['stake']['target'],
              f"{cell}: audit luck costs sum to {_cost} but {-lk['stake']['target']} luck was sold "
              f"({ {k: v['luck_cost'] for k, v in _audit.items()} })")
    else:
        check(all(_r['luck_cost'] == 0 for _r in _audit.values()),
              f"{cell}: a non-seller carries a luck cost: "
              f"{ {k: v['luck_cost'] for k, v in _audit.items()} }")

    # ---- the payout is DELIVERED, as pf1 changes ----
    # Every route the sale bought must arrive as a change carrying the same number the stake
    # promised. Without this the payout could silently stop being delivered and nothing would
    # notice: the budgets no longer move, so there is no other evidence it happened.
    # Read off the block, not the `stake` local -- this check runs before that name is bound, and
    # the block is the thing both renderers actually see anyway.
    _changes = lk['payout_changes']
    _stk = lk['stake']
    _pay = (_stk or {}).get('payout', {})
    _selling = bool(_stk) and _stk['direction'] == 'sell'
    check(bool(_changes) == bool(_selling and (_pay.get('hp') or _pay.get('skill_points')
                                               or _pay.get('attribute_points'))),
          f"{cell}: payout_changes {'present' if _changes else 'absent'} does not match the sale")
    _by_target = {}
    for _c in _changes:
        check(set(_c) == {'formula', 'target', 'type', 'operator', 'priority', 'flavor'},
              f"{cell}: payout change has keys {sorted(_c)}")
        check(_c['target'] in PF1_PAYOUT_TARGETS,
              f"{cell}: payout change targets {_c['target']!r}, not a pf1 target that can carry it")
        check(_c['type'] in PF1_BONUS_TYPES, f"{cell}: payout change type {_c['type']!r}")
        _by_target[_c['target']] = _by_target.get(_c['target'], 0) + int(_c['formula'])
    if _selling:
        check(_by_target.get('mhp', 0) == _pay.get('hp', 0),
              f"{cell}: mhp change carries {_by_target.get('mhp', 0)}, sale bought {_pay.get('hp', 0)} HP")
        check(_by_target.get('bonusSkillRanks', 0) == _pay.get('skill_points', 0),
              f"{cell}: bonusSkillRanks carries {_by_target.get('bonusSkillRanks', 0)}, sale bought "
              f"{_pay.get('skill_points', 0)}")
        _bumps = lk['attribute_bumps']
        check(sum(_bumps.values()) == _pay.get('attribute_points', 0),
              f"{cell}: attribute bumps {_bumps} total {sum(_bumps.values())}, sale bought "
              f"{_pay.get('attribute_points', 0)}")
        check(set(_bumps) <= set(PF1_ABILITIES),
              f"{cell}: attribute bumps name {sorted(set(_bumps) - set(PF1_ABILITIES))}")
        for _ab, _n in _bumps.items():
            check(_by_target.get(_ab, 0) == _n,
                  f"{cell}: {_ab} change carries {_by_target.get(_ab, 0)}, bumps say {_n}")
    if lk['mod'] != 0:
        LUCK_COVERAGE['nonzero_mod'] += 1
    # The derivation is what the sheet shows to justify the score; empty means a blank panel.
    check(bool(lk['derivation']), f"{cell}: luck block carries no derivation lines")
    check(str(lk['derivation'][-1]).startswith('='),
          f"{cell}: the derivation should end with the total; got {lk['derivation'][-1]!r}")

    # ---- one shape for every character; Dimorphic holds all three EQUAL ----
    values = lk['values']
    check(set(values) == {'negative', 'default', 'proximity'},
          f"{cell}: typed luck values have keys {sorted(values)}")
    if lk['type'] == 'Dimorphic':
        check(values['negative'] == values['default'] == values['proximity'] == score,
              f"{cell}: Dimorphic must hold all three types at equal values; got {values}")

    # ---- the feats ----
    feats = lk['feats']
    check(len(set(feats)) == len(feats),
          f"{cell}: the same E-Kat feat is counted twice: {feats}")
    unknown = [f for f in feats if f not in E_KAT_TABLE]
    check(not unknown, f"{cell}: luck block names E-Kat feats that do not exist: {unknown}")
    if unknown:
        return
    # Every E-Kat feat the character holds must ALSO be on its actual feat list -- "generated but
    # invisible" is the failure this repo keeps rediscovering. Across EVERY bucket:
    # separate_feats_func splits the merged list five ways, so an E-Kat feat can render as a class
    # or story feat, and checking only `feats` reports a phantom orphan.
    on_sheet = {str(x).lower()
                for key in ('feats', 'story_feats', 'flaw_feats', 'flavor_feats', 'class_feats',
                            'trainer_feats')
                for x in (payload.get(key) or [])}
    for name in feats:
        check(name.lower() in on_sheet,
              f"{cell}: luck credits {name!r} but it is not on the character's feat list")
    # The non-E-Kat luck feats, recomputed from what the character actually holds.
    want_luck_feats = sorted(n for n in LUCK_FEAT_TABLE if n.lower() in on_sheet)
    check(sorted(lk['luck_feats']) == want_luck_feats,
          f"{cell}: luck_feats {sorted(lk['luck_feats'])} != {want_luck_feats} -- every hero point "
          f"and luck feat on the sheet grants +1 Luck")
    luck_feat_luck = len(want_luck_feats)
    # Prerequisite chains must be satisfied by what the character actually kept.
    for name in feats:
        for prereq in E_KAT_TABLE[name]['prerequisites']:
            check(prereq in feats,
                  f"{cell}: holds {name!r} without its prerequisite {prereq!r}")
    if feats:
        LUCK_COVERAGE['with_feats'] += 1
        if any(E_KAT_TABLE[f]['prerequisites'] for f in feats):
            LUCK_COVERAGE['chains'] += 1

    # ---- an E-Kat feat is an ORDINARY feat and must render as one ----
    # The four specialised buckets are separate budgets, so a feat sitting in one occupies a
    # story/flaw/flavour/class slot and renders under that heading. Six of one character's ten used
    # to land in class_feats, because assign_feats_to_levels reorders normal + class as ONE pool.
    for _bucket in ('story_feats', 'flaw_feats', 'flavor_feats', 'class_feats'):
        _stray = [f for f in (payload.get(_bucket) or []) if f in feats]
        check(not _stray,
              f"{cell}: E-Kat feat(s) {_stray} rendered under {_bucket} -- they are ordinary feats "
              f"and must stay in the general feat list")
    _general = {str(f).lower() for f in (payload.get('feats') or [])}
    _absent = [f for f in feats if f.lower() not in _general]
    check(not _absent, f"{cell}: E-Kat feat(s) {_absent} are not in the general feat list")

    # Rules text: without it the module synthesizes a row with a bare name and no benefit -- a
    # failure that is invisible rather than loud.
    _descs = payload.get('homebrew_feat_desc_dict') or {}
    _blank = [f for f in feats if not str(_descs.get(f, '')).strip()]
    check(not _blank, f"{cell}: E-Kat feat(s) {_blank} carry no description")

    # The sheet's "Feats Taken" group must name exactly the feats the character holds -- no more.
    _exchange = (payload.get('class features') or {}).get('E-Kat Exchange') or {}
    if _exchange:
        _listed = {k[len('Feat: '):] for k in (_exchange.get('Feats Taken') or {})
                   if k.startswith('Feat: ')}
        check(_listed == set(feats),
              f"{cell}: 'Feats Taken' lists {sorted(_listed)} but the character holds "
              f"{sorted(feats)}")

    # ---- what the character EARNED: each per-level term gated on its own feat ----
    # "(1, 2 if Double Down)" is verbatim Sweet Dreams and Stream of Luck, so a character holding
    # neither accrues neither term -- and one with no E-Kat feats at all earns nothing.
    # Each per-level term is gated on the feat that produces that kind of E-Kat; Double Down doubles
    # the RATE of both and never the feats x 5 term.
    rate = 2 if 'Double Down' in feats else 1
    long_rest = rate if 'Sweet Dreams' in feats else 0
    discovery = rate if 'Stream of Luck' in feats else 0
    want_earned = payload['total_level'] * (long_rest + discovery) + len(feats) * 5
    if lk['type'] == 'Dimorphic':
        want_earned *= 2
    check(lk['e_kat_earned'] == want_earned,
          f"{cell}: earned {lk['e_kat_earned']} != {want_earned} (level {payload['total_level']}, "
          f"long_rest={long_rest}, discovery={discovery}, {len(feats)} feat(s) x5)")
    check(bool(feats) or lk['e_kat_earned'] == 0,
          f"{cell}: no E-Kat feats but earned {lk['e_kat_earned']} E-Kats -- every term carries the "
          f"feat count as a factor, so this must be zero")

    # ---- the traits it bought with them ----
    # "25 Permanent E-Kats can be used to purchase a Luck Trait" and "These points must be spent".
    traits_held = lk['traits']
    check(len(traits_held) == lk['e_kat_earned'] // 25,
          f"{cell}: bought {len(traits_held)} Luck Trait(s) from {lk['e_kat_earned']} E-Kats, "
          f"expected {lk['e_kat_earned'] // 25}")
    check(lk['e_kat_reserve'] == lk['e_kat_earned'] - len(traits_held) * 25,
          f"{cell}: carried {lk['e_kat_reserve']} != earned {lk['e_kat_earned']} - "
          f"{len(traits_held)}x25")
    check(lk['e_kat_reserve'] <= lk['e_kat_store_cap'],
          f"{cell}: carried {lk['e_kat_reserve']} exceeds the store cap {lk['e_kat_store_cap']}")
    unknown_traits = [t for t in traits_held if t not in LUCK_TRAIT_TABLE]
    check(not unknown_traits, f"{cell}: unknown Luck Trait(s): {unknown_traits}")
    if unknown_traits:
        return
    for t in traits_held:
        info = LUCK_TRAIT_TABLE[t]
        # Category is an eligibility gate, not a label.
        if info['category'] == 'dimorphic':
            check(lk['type'] == 'Dimorphic',
                  f"{cell}: holds the Dimorphic trait {t!r} but its luck type is {lk['type']}")
        # THE UNREACHABILITY IS ASSERTED, NOT ASSUMED. Negative luck comes only from selling;
        # sellers take no E-Kat feats; no feats means no reserve; no reserve means no purchase. If
        # a negative trait ever appears here, one of those three rulings has quietly changed.
        check(info['category'] != 'negative',
              f"{cell}: holds the negative-luck trait {t!r}, which no generated character should "
              f"be able to reach -- one of the three rulings behind that has changed")
        for _pre in info.get('prerequisites', []):
            check(_pre in traits_held,
                  f"{cell}: holds the Luck Trait {t!r} without its prerequisite {_pre!r}")
        _floor = info.get('requires_luck_at_most')
        check(_floor is None or score <= _floor,
              f"{cell}: holds {t!r}, which needs a luck score of {_floor} or worse; score is {score}")
        if not info['repeatable']:
            check(traits_held.count(t) == 1,
                  f"{cell}: {t!r} is not repeatable but was bought {traits_held.count(t)} times")
    # Variety first: a repeat may only appear once every eligible trait is already held.
    if len(traits_held) != len(set(traits_held)):
        eligible = sum(1 for i in LUCK_TRAIT_TABLE.values()
                       if i['category'] == 'standard'
                       or (i['category'] == 'dimorphic' and lk['type'] == 'Dimorphic'))
        check(len(set(traits_held)) == eligible,
              f"{cell}: repeated a Luck Trait with only {len(set(traits_held))} of {eligible} eligible "
              f"traits held -- variety comes first")

    # ---- trait effects reach the numbers they are supposed to move ----
    stacks = lambda field: sum(1 for t in traits_held if LUCK_TRAIT_TABLE[t]['effects'].get(field))
    base_cap = LUCK_CAP_DIMORPHIC if lk['type'] == 'Dimorphic' else LUCK_CAP_POS
    check(cap == base_cap + 5 * stacks('luck_cap_step'),
          f"{cell}: cap {cap} != {base_cap} + 5x{stacks('luck_cap_step')} Expanded Luck")
    check(lk['vault_cap'] == 77 + 77 * stacks('vault_cap_step'),
          f"{cell}: vault cap {lk['vault_cap']} != 77 + 77x{stacks('vault_cap_step')} Big Savings")
    check(lk['e_kat_store_cap'] == E_KAT_CAP + 100 * stacks('e_kat_store_step'),
          f"{cell}: store cap {lk['e_kat_store_cap']} != {E_KAT_CAP} + "
          f"100x{stacks('e_kat_store_step')} Enhanced Luck Storage")
    want_twist = (max(0, lk['mod']) + stacks('twist_fate_bonus')) if lk['type'] == 'Dimorphic' else 0
    check(lk['twist_fate_per_day'] == want_twist,
          f"{cell}: Twist Fate uses {lk['twist_fate_per_day']} != {want_twist} "
          f"(mod {lk['mod']} + {stacks('twist_fate_bonus')} Extra Spin)")
    trait_luck = stacks('luck_score_bonus')
    if traits_held:
        LUCK_COVERAGE['with_traits'] += 1

    # ---- the purchase balances, and the source budget actually shrank ----
    stake = lk['stake']
    feat_luck = _feat_luck(feats)
    if stake is None:
        check(not feats, f"{cell}: holds E-Kat feats with no luck stake: {feats}")
        # No stake means no E-Kat feats and nothing bought -- but an ordinary luck feat still
        # grants its +1, so the score is exactly the luck-feat count.
        check(score == luck_feat_luck,
              f"{cell}: no stake and {luck_feat_luck} luck feat(s), so the score should be "
              f"{luck_feat_luck}, not {score}")
        check(lk['e_kat_earned'] == 0 and not traits_held,
              f"{cell}: no stake means no E-Kat feats, so it must earn nothing and buy nothing; "
              f"earned {lk['e_kat_earned']}, traits {traits_held}")
        return
    LUCK_COVERAGE['stakes'] += 1
    LUCK_COVERAGE[stake['direction']] += 1
    if score < 0:
        LUCK_COVERAGE['negative'] += 1

    if stake['direction'] == 'buy':
        check(not lk['negative_feats'],
              f"{cell}: a buyer carries a negative-luck feat ledger {lk['negative_feats']}")
        paid = stake['paid']
        bought = sum(paid.get(k, 0) // rate for k, rate in LUCK_BUY.items())
        check(score == max(LUCK_CAP_NEG, min(cap, bought + feat_luck + luck_feat_luck + trait_luck)),
              f"{cell}: luck score {score} != clamp(bought {bought} + E-Kat feats {feat_luck} "
              f"+ luck feats {luck_feat_luck} + traits {trait_luck})")
        # It must have paid for what it bought -- never asked for more than it spent.
        for currency, rate in LUCK_BUY.items():
            spent = paid.get(currency, 0)
            check(spent >= 0, f"{cell}: negative spend recorded for {currency}: {spent}")
            check(spent <= stake['requested'].get(currency, 0),
                  f"{cell}: paid {spent} {currency} but only requested "
                  f"{stake['requested'].get(currency, 0)}")
        # The skill-rank budget on the payload is POST-deduction, so the pre-luck budget is the sum.
        # A quarter-of-the-pool ceiling means the spend can never be most of the budget.
        ranks_paid = paid.get('skill_ranks', 0)
        if ranks_paid:
            before = payload['skill_rank_budget'] + ranks_paid
            check(payload['skill_rank_budget'] < before,
                  f"{cell}: {ranks_paid} rank(s) bought luck but the budget did not shrink")
            check(ranks_paid * 4 <= before + 3,
                  f"{cell}: luck took {ranks_paid} of {before} skill ranks -- past the "
                  f"quarter-of-the-pool ceiling")
    else:
        # A SELLER CANNOT CLIMB BACK. Sellers used to be kept out of the E-Kat feat economy
        # entirely, which closed the free-money loop but also denied them the E-Kat reserve --
        # the only currency Luck Traits can be bought with -- making all ten NEGATIVE Luck Traits
        # unreachable by any generated character. Sellers now take E-Kat feats like anyone else,
        # and the loop is closed at the score instead: their feats grant ZERO luck.
        #
        # So the assertion is no longer "holds no E-Kat feats" but the stronger, more direct
        # property: however many luck feats a seller holds, the score is exactly what it sold.
        check(score == max(LUCK_CAP_NEG, stake['target']),
              f"{cell}: sold {stake['target']} luck while holding {len(feats)} E-Kat feat(s) "
              f"(worth {feat_luck}) and {luck_feat_luck} from ordinary luck feat(s), but the score "
              f"is {score} -- a seller must gain no luck from feats")
        check(score <= 0,
              f"{cell}: a seller finished at {score} -- selling must never yield positive luck")
        # A trait outside the negative category must still respect its own eligibility; what is new
        # is that the negative ones are now buyable at all. Count them so the census can prove it.
        if set(traits_held) & NEGATIVE_TRAIT_NAMES:
            LUCK_COVERAGE['negative_traits'] += 1
        # The deep end of the scale -- the reason the sell magnitude was decoupled from the buy
        # side. Traits floored at -25 and below are unreachable without it.
        if stake['target'] <= -25:
            LUCK_COVERAGE['deep_sale'] += 1
        for _t in traits_held:
            _floor = LUCK_TRAIT_TABLE.get(_t, {}).get('requires_luck_at_most')
            check(_floor is None or score <= _floor,
                  f"{cell}: bought {_t!r} (needs luck <= {_floor}) at a score of {score}")
        # ---- the MECHANICS reach the payload, and are shaped for pf1 ----
        # A trait whose data carries a change/note/formula must be exported, or the sheet renders it
        # as prose the player applies by hand -- which is the whole failure this pass exists to fix.
        _tc = lk['trait_changes']
        for _t in set(traits_held):
            _row = LUCK_TRAIT_TABLE.get(_t, {})
            _has = bool(_row.get('changes') or _row.get('context_notes')
                        or _row.get('death_hp_pool_bonus'))
            check(_has == (_t in _tc),
                  f"{cell}: {_t!r} carries mechanics in luck_traits.json but is absent from "
                  f"trait_changes (or vice versa)")
        for _t, _entry in _tc.items():
            check(_t in traits_held,
                  f"{cell}: trait_changes names {_t!r}, which the character does not hold")
            for _c in _entry['changes']:
                check(_c['target'] in PF1_CHANGE_TARGETS,
                      f"{cell}: {_t!r} emits change target {_c['target']!r}, not a pf1 target this "
                      f"project may use -- it would silently never apply")
                check(_c['type'] in PF1_BONUS_TYPES,
                      f"{cell}: {_t!r} emits bonus type {_c['type']!r}, not a pf1 bonus type")
                # These traits are COMPENSATION for being cursed, so every one resolves positive.
                # The formula negates the floor rather than flooring an absolute value, because
                # floor(abs(-44)/5) is 8 where the true magnitude is 9 -- asserted numerically
                # below rather than trusted from the string.
                check('@resources.personalLuck' in _c['formula'],
                      f"{cell}: {_t!r} bakes a literal into {_c['formula']!r}; the formulas are "
                      f"live so a GM editing the score moves them")
            for _n in _entry['contextNotes']:
                check(_n['target'] in PF1_CHANGE_TARGETS,
                      f"{cell}: {_t!r} note targets {_n['target']!r}, not a pf1 target")
                check(bool(str(_n['text']).strip()), f"{cell}: {_t!r} carries an empty context note")
        # The negative-luck ledger: which ordinary feats the sale paid for, at 5 luck each.
        _ledger = lk['negative_feats']
        _sold = stake['payout'].get('feats', 0)
        # EXACTLY the slots sold, not "no more than". This was `<=` while the ledger inferred its
        # rows from the tail of the feat list, so it tolerated the silent under-reporting that
        # tolerance was hiding -- 15% of sellers showed fewer "(-5 Luck)" rows than they had bought.
        # The rows are now named from the reservation itself, so the count is knowable and pinned.
        check(len(_ledger) == _sold,
              f"{cell}: ledger lists {len(_ledger)} feat(s) but {_sold} slot(s) were sold")
        check(len({e['name'] for e in _ledger}) == len(_ledger),
              f"{cell}: ledger repeats a feat: {[e['name'] for e in _ledger]}")
        for _i, _e in enumerate(_ledger):
            check(_e['cumulative'] == -5 * (_i + 1),
                  f"{cell}: ledger row {_i} reads {_e['cumulative']}, expected {-5 * (_i + 1)}")
        _prof = {str(x).lower() for x in (payload.get('profession_feats') or [])}
        _billed = [_e['name'] for _e in _ledger
                   if _e['name'] in feats or str(_e['name']).lower() in _prof]
        check(not _billed,
              f"{cell}: ledger bills {_billed} to negative luck, but those slots were paid for by "
              f"something else (an E-Kat reservation or a profession slot)")

        payout = stake['payout']
        owed = (payout['hp'] // 2 + payout['skill_points'] // 2
                + payout['attribute_points'] * 5 + payout['feats'] * 5)
        # Against the STAKE, not the final score. These now agree for every seller (feats grant a
        # seller no luck), but the stake is still the right thing to check: it is what the payout
        # was computed FROM, so a future rule that moves the score must not silently move this too.
        check(owed == -stake['target'],
              f"{cell}: payout {payout} accounts for {owed} luck, but {-stake['target']} was sold")


def check_class_choices(cell, payload):
    """Every rolled class holds exactly the picks its schedule promises, in every bucket.

    THE GENERALISATION of the psionics-only check further down (class-choices ticket 05). That one
    covered 12 classes through SUBSYSTEM_BUCKET; this covers all 68 through the schedule table, and
    it rides the sweep the file already runs, so it costs no extra generations -- the coverage
    question ticket 05 raised turned out to be answerable for free.

    The expectation is ticket 03's ruling: min(scheduled, |pool|, max_num). All three terms matter
    and each is load-bearing on a real row -- the tactician runs out of strategies at 40th, the
    brawler is held to 8 by its call site's max_num, and everyone else is bounded by the schedule.
    An unresolvable pool means NO cap rather than a free pass, so a real shortfall still fails.
    """
    classes = payload['classes']
    features = payload.get('class_features') or {}
    stamps = payload.get('class_feature_levels') or {}
    CHOICE_COVERAGE['chars'] += 1

    # A bucket two rolled classes both declare cannot be attributed to either (barbarian + skald
    # share rage_powers by design). Skip it rather than guess -- and count the skip, so a sweep
    # that quietly stopped asserting anything is visible in the summary.
    declared = {}
    for entry in classes:
        for bucket in (schedule_row_names(entry['name'])):
            declared.setdefault(bucket, []).append(entry)

    for entry in classes:
        name = entry['name']
        for bucket in schedule_row_names(name):
            if len(declared.get(bucket, [])) > 1:
                CHOICE_COVERAGE['skipped'] += 1
                continue
            if (name, bucket) in CHOICE_SKIP:
                CHOICE_COVERAGE['skipped'] += 1
                continue
            levels = schedule_levels(SCHEDULE, name, bucket, entry['level'])
            if levels is None:
                continue
            row = schedule_row(SCHEDULE, name, bucket) or {}
            want = len(levels)
            pool = _subsystem_pool_size(name, bucket)
            if pool is not None and pool < want:
                want, capped = pool, True
            else:
                capped = False
            if row.get('max_num') is not None and row['max_num'] < want:
                want, capped = row['max_num'], True
            if capped:
                CHOICE_COVERAGE['capped'] += 1

            got = len(features.get(bucket) or ())
            CHOICE_COVERAGE['buckets'] += 1
            CHOICE_COVERAGE['picks'] += got
            check(got == want,
                  f"{cell}: {name} bucket {bucket!r} holds {got} picks, expected {want} at class "
                  f"level {entry['level']} -- picks that never land appear nowhere on a sheet"
                  + (f" (capped: pool={pool}, max_num={row.get('max_num')})" if capped else ""))

            # The level stamp comes off the same list as the count (ticket 01 ruling 3), so a wrong
            # count and a wrong stamp are one bug. Asserting the stamps are a SUBSET of the
            # scheduled levels catches the investigator's old even-level stamping without assuming
            # which k a given pick was.
            if row.get('stamps') is False:
                continue
            got_stamps = set((stamps.get(bucket) or {}).values())
            if not got_stamps:
                continue
            CHOICE_COVERAGE['stamps'] += len(got_stamps)
            stray = sorted(got_stamps - set(levels))
            check(not stray,
                  f"{cell}: {name} bucket {bucket!r} stamps picks at class level(s) {stray}, which "
                  f"the schedule does not grant ({levels}) -- the stamp reaches both sheets")


def schedule_row_names(class_name):
    return list(((SCHEDULE.get(class_name) or {}).get('buckets') or {}))


_POOL_CACHE = {}


def _subsystem_pool_size(class_name, bucket):
    """How many distinct options exist for a bucket, or None if the pool cannot be resolved.

    Read from the class's own data file rather than through the chooser, for the same reason the
    psionics tables above are: a check that reads through the code it is checking cannot catch that
    code drifting. Only used to CAP the expectation -- an unresolvable pool means no cap, which
    keeps this from silently excusing a real shortfall.
    """
    if (class_name, bucket) in _POOL_CACHE:
        return _POOL_CACHE[(class_name, bucket)]
    row = schedule_row(SCHEDULE, class_name, bucket) or {}
    dataset = row.get('dataset', bucket)
    size = None
    path = BACKEND / 'json' / 'class_data' / f'{class_name}.json'
    if path.exists():
        options = json.load(open(path, encoding='utf-8')).get(dataset)
        # Only a flat {name: description} pool is countable; the level-banded and nested shapes
        # (paladin mercies, shaman hexes) are not, and get no cap.
        if isinstance(options, dict) and options and all(
                isinstance(v, str) for v in options.values()):
            size = len(options)
    _POOL_CACHE[(class_name, bucket)] = size
    return size


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


def final_score(payload, stat):
    return (payload[stat] + (payload.get('inherents') or {}).get(stat, 0)
            + (payload.get('level_up_stats') or {}).get(stat, 0))


def final_mod(payload, stat):
    return floor((final_score(payload, stat) - 10) / 2)


def score_character(cell, payload):
    """Collect a power profile for this character, when --score is on.

    Deliberately non-asserting: this is a MEASUREMENT phase, and the point of the baseline is to
    find out what today's random output scores. The assertions live in check_power_metric, which
    runs once at the end over everything collected -- so a single odd character is a data point
    rather than a red build.
    """
    if not SCORING:
        return
    try:
        profile = power_metric.profile_for(payload)
    except Exception:
        tail = traceback.format_exc().strip().splitlines()
        REPORT.error(f"{cell}: power_metric.profile_for raised -- {tail[-1]}")
        return
    profile['cell'] = cell
    profile['class'] = str(payload.get('c_class') or '')
    profile['multiclass'] = bool(payload.get('c_class_2'))
    SCORE_ROWS.append(profile)


def check_power_metric():
    """The BEHAVIOUR layer over the metric: it must actually see the characters it scores.

    Its partner is the CONFIG layer, gates/validate_power_metric.py, which checks the tables resolve
    without generating anything. Neither imports the other's conclusions.

    The failure this exists to catch is the one ticket 03 names: a metric that silently rates a
    warder at zero is worse than one that says it cannot see maneuvers yet. So a whole class scoring
    zero on an axis every character must have is an error, not a finding -- and a run that scored
    nothing at all fails rather than reporting success having asserted nothing.
    """
    if not SCORING:
        return
    if not check(SCORE_ROWS, "--score was passed but no character was scored"):
        return

    by_class = {}
    for row in SCORE_ROWS:
        by_class.setdefault(row['class'], []).append(row)

    for axis in NONZERO_AXES:
        for name, rows in sorted(by_class.items()):
            if all((row['axes'].get(axis) or {}).get('raw') in (None, 0) for row in rows):
                check(False,
                      f"every one of the {len(rows)} scored {name} characters has {axis}=0 -- an "
                      f"axis the fold has stopped reading, not a weak class")

    # The nova round is the sustained round plus adders (or the better blast), so per character
    # burst_raw >= dpr_raw is structural -- a violation is scorer arithmetic, never a weak build.
    # ac_combat >= ac is structural the same way (sheet AC plus defensive folds).
    for row in SCORE_ROWS:
        burst = (row['axes'].get('burst_raw') or {}).get('raw') or 0
        sustained = (row['axes'].get('dpr_raw') or {}).get('raw') or 0
        if burst < sustained:
            check(False,
                  f"a scored {row['class']} L{row['level']} has burst_raw {burst} < dpr_raw "
                  f"{sustained} -- the nova round can never be lower than the sustained round")
            break
        combat_ac = (row['axes'].get('ac_combat') or {}).get('raw') or 0
        sheet_ac = (row['axes'].get('ac') or {}).get('raw') or 0
        if combat_ac < sheet_ac:
            check(False,
                  f"a scored {row['class']} L{row['level']} has ac_combat {combat_ac} < ac "
                  f"{sheet_ac} -- the fight-state AC can never be lower than the sheet AC")
            break

    unknown = sorted({row['diagnostics']['weapon_name'] for row in SCORE_ROWS
                      if not row['diagnostics']['weapon_known']})
    if unknown:
        REPORT.warn(f"{len(unknown)} weapon name(s) do not resolve in weapons_data.json, so their "
                    f"damage dice scored zero: {unknown[:12]}")

    shortfall = [row for row in SCORE_ROWS if row['diagnostics']['web_sheet_ac_shortfall']]
    print(f"  power metric: {len(SCORE_ROWS)} characters scored across {len(by_class)} classes; "
          f"{len(unknown)} unresolved weapon(s); "
          f"{len(shortfall)} would render AC-low on the web sheet")


def check_character(cell, payload):
    L = payload['total_level']
    classes = payload['classes']
    score_character(cell, payload)

    # ---- the level ceiling ----
    # randomize_level CLAMPS a requested level to MAX_CHARACTER_LEVEL rather than rejecting it, and
    # a silent clamp is exactly the kind of rule that can stop firing without anyone noticing -- the
    # symptom would be a level-60 character, not an error. This runs on every swept character, but
    # the sweep's own levels are all under the ceiling, so `check_level_ceiling` below is what
    # actually drives the clamp; without it this pair would pass vacuously forever.
    #
    # The second half is the one that would really rot: the total is capped in one place, but the
    # per-class split happens in another (_split_levels), so a character whose class levels do not
    # add up to its total would satisfy the cap and still be wrong.
    check(L <= MAX_CHARACTER_LEVEL,
          f"{cell}: total level {L} exceeds the ceiling of {MAX_CHARACTER_LEVEL}")
    check(sum(c['level'] for c in classes) == L,
          f"{cell}: class levels {[c['level'] for c in classes]} sum to "
          f"{sum(c['level'] for c in classes)}, not the total level {L}")
    check_class_choices(cell, payload)
    for c in classes:
        check(1 <= c['level'] <= MAX_CHARACTER_LEVEL,
              f"{cell}: {c['name']} is level {c['level']}, outside 1..{MAX_CHARACTER_LEVEL}")
    # `capped_level` -- the min(level, 20) that stops spell and maneuver progressions -- is NOT
    # asserted here: it lives on character.classes and is deliberately not exported, so the payload
    # cannot see it. What a payload CAN show is its effect, and the spell-slot check further down
    # already covers that.

    # ---- spell slots are numbers ----
    # `spells_per_day_attr` loops `range(0, highest_spell_known + 1)` and indexes the scraped table,
    # so a `highest_spell_known` that runs one spell level past what the class actually gets reads a
    # cell the scrape correctly left blank -- and the tables spell blank as the STRING 'null', not
    # JSON null. That string reached the payload and from there the Foundry sheet and the web sheet.
    # It shipped for every sorcerer, oracle, psychic and arcanist at roughly half of all levels
    # (spontaneous casters gain each spell level one class level later than prepared ones), plus
    # every adept, until caster_formula learned both progressions.
    #
    # Checked HERE rather than by a golden fixture on purpose: the seven goldens contain no
    # spontaneous full caster at a divergent level, so fixing the bug moved none of them. A property
    # asserted over the whole swept roster catches the next class to acquire a bespoke progression;
    # one more fixture would only have covered the one class somebody thought to add.
    for book in (payload.get('spellbooks') or []):
        rows = book.get('spells_per_day_list') or []
        bad = [(i, cell_value) for i, cell_value in enumerate(rows)
               if not isinstance(cell_value, (int, float)) or isinstance(cell_value, bool)]
        check(not bad,
              f"{cell}: {book.get('name')} spells_per_day_list has non-numeric slot(s) {bad[:4]} "
              f"-- a blank table cell leaked in as a value; caster_formula is claiming a spell "
              f"level this class does not reach (row: {rows})")

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
    # Luck's workhorse currency: 5 ranks buy +1 luck, and a seller gets 2 skill points back per -1.
    # It is applied to the BUDGET, deliberately, so `sum(ranks) == recorded` below stays true and
    # the deduction is visible here rather than looking like a formula bug. Add back what luck took
    # (or subtract what it granted) before comparing against the house formula.
    _stake = (payload.get('luck') or {}).get('stake') or {}
    luck_ranks = ((_stake.get('paid') or {}).get('skill_ranks', 0)
                  - (_stake.get('payout') or {}).get('skill_points', 0))
    favored = recorded + luck_ranks - base - 2 * L
    check(favored in (0, L),
          f"{cell}: skill budget {recorded} != base {base} + background {2 * L} + favored 0|{L} "
          f"(luck took {luck_ranks:+d})")
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

            # ---- subsystem picks: generated, and findable ----
            # The failure this guards is "generated but invisible": the picks land in the class
            # features dict under a bucket name only main_test.py knew, so a renderer showing a
            # class's psionics had no way to reach them. The aegis and soulknife are the proof
            # cases -- their tab has nothing else on it, so a missing pointer reads as an empty tab.
            want_bucket = SUBSYSTEM_BUCKET.get(name, '')
            check(m['subsystem_bucket'] == want_bucket,
                  f"{tag}: subsystem_bucket {m['subsystem_bucket']!r} != {want_bucket!r}")
            if want_bucket:
                picks = (payload.get('class_features') or {}).get(want_bucket) or {}
                # How many picks are DUE at this level. generic_class_option_chooser walks the
                # schedule (`i = len(chosen_set)`), so the count is exactly the entries at or below
                # the class level; the three single-pick classes have no schedule and take one at
                # 1st. Read from class_choice_schedule.json via the harness's own expansion, NOT
                # through generic_func.levels_for -- see _harness.choice_schedule.
                # ...capped by how many options EXIST: above 20th the schedules keep granting, but
                # the published lists are finite (a tactician 40 is owed 13 strategies and 12
                # exist), and the chooser breaks out rather than inventing one.
                want_picks = schedule_due(SCHEDULE, name, want_bucket, entry['level'],
                                          _subsystem_pool_size(name, want_bucket))
                if want_picks is None:
                    want_picks = 1
                check(len(picks) == want_picks,
                      f"{tag}: subsystem bucket {want_bucket!r} holds {len(picks)} picks, expected "
                      f"{want_picks} at class level {entry['level']} -- picks that never land "
                      f"appear nowhere on a sheet")

            if name in _NO_MANIFESTING:
                check(not m['manifesting_stat'] and not m['pp_per_day'] and not m['powers_chosen']
                      and not m['caster_type'],
                      f"{tag}: manifests nothing, but carries "
                      f"stat={m['manifesting_stat']!r} pp={m['pp_per_day']} "
                      f"caster_type={m['caster_type']!r} powers={len(m['powers_chosen'])}")
                # The mind blade is the soulknife's ONLY psionic thing, so an absent one leaves the
                # class with nothing to render. It must also be the weapon actually equipped.
                blade = m['mind_blade']
                check(isinstance(blade, dict) and blade.get('name'),
                      f"{tag}: no mind blade on the manifester entry")
                if isinstance(blade, dict):
                    check(blade['name'] == payload.get('weapon_name'),
                          f"{tag}: mind blade {blade['name']!r} != equipped weapon "
                          f"{payload.get('weapon_name')!r}")
                continue

            check(m['manifesting_stat'] in ('str', 'dex', 'con', 'int', 'wis', 'cha'),
                  f"{tag}: manifesting stat {m['manifesting_stat']!r} is not an ability")
            # A key ability of 9 or lower cannot manifest AT ALL -- not badly, at all -- so the
            # whole record legitimately reads zero. Everything below assumes the gate is passed.
            if final_mod(payload, m['manifesting_stat']) < 0:
                # caster_type moves with the points: handing Foundry a progression on a book worth
                # zero points would have the module compute points the rules deny this character.
                check(not m['caster_type'],
                      f"{tag}: cannot manifest, but carries caster_type {m['caster_type']!r}")
                continue

            # Power points = the class table at manifester level, PLUS floor(mod x ML / 2). The
            # formula is restated rather than imported so a change to psionics.py has to be a
            # deliberate change here too -- that is the point of an invariant test.
            base_pp = table.get('pp_per_day', [0] * 20)[row]
            bonus = max(0, floor(final_mod(payload, m['manifesting_stat']) * m['manifester_level'] / 2))
            check(m['pp_per_day'] == base_pp + bonus,
                  f"{tag}: pp {m['pp_per_day']} != table {base_pp} + bonus {bonus}")
            # caster_type is the pf1-psionics progression name the Foundry manifester book needs.
            # Recomputed from the class's own table rather than trusted: a wrong one is invisible
            # in the payload and shows up in Foundry as a plausible but wrong power-point total.
            want_type = next((k for k, v in data.psionic_pp_tables.items()
                              if v == table.get('pp_per_day')), '')
            check(m['caster_type'] == want_type,
                  f"{tag}: caster_type {m['caster_type']!r} != {want_type!r} for its pp table")

            if name in _PP_ONLY:
                check(not m['powers_chosen'],
                      f"{tag}: spends power points on class options, but knows "
                      f"{len(m['powers_chosen'])} power(s)")
                continue

            # The class table is a CEILING. Every power-knowing class also demands a key ability of
            # "at least 10 + the power's level" to learn one, so a middling score caps the class
            # table -- most visibly on the psychic warrior, which manifests off Wis but plays off
            # Str. Without this the gate would pass a psion handed 9th-level powers on Int 14.
            want_max = min(table.get('max_power_level', [0] * 20)[row],
                           final_score(payload, m['manifesting_stat']) - 10)
            check(m['max_power_level'] == want_max,
                  f"{tag}: max power level {m['max_power_level']} != min(table, score-10) = {want_max}")
            # Talents are granted free by class feature and explicitly do NOT count against powers
            # known, so the total on the sheet is the table plus the grant.
            want_talents = FREE_TALENTS.get(name, 0)
            check(m['talents_known'] == want_talents,
                  f"{tag}: {m['talents_known']} talents != class grant {want_talents}")
            want_known = table.get('powers_known', [0] * 20)[row]
            check(len(m['powers_chosen']) == want_known + want_talents,
                  f"{tag}: knows {len(m['powers_chosen'])} powers != table {want_known} "
                  f"+ {want_talents} free talents")
            # Talents live in bucket 0 and nowhere else -- a talent that landed in a leveled bucket
            # would mean it had been bought with a powers-known slot after all.
            check(len(m['powers_by_level'][0]) == want_talents if m['powers_by_level'] else True,
                  f"{tag}: bucket 0 holds {len(m['powers_by_level'][0]) if m['powers_by_level'] else 0} "
                  f"names, expected exactly the {want_talents} free talents")
            for named in MANDATED_TALENTS.get(name, []):
                check(named in m['powers_chosen'],
                      f"{tag}: class grants {named!r} by name, but it is not among its powers")
            # powers_known_list is how the sheet groups the same powers by level, so the two views
            # of one fact must agree.
            check(sum(m['powers_known_list']) == len(m['powers_chosen']),
                  f"{tag}: powers_known_list sums to {sum(m['powers_known_list'])} "
                  f"but {len(m['powers_chosen'])} powers were chosen")
            check(len(set(m['powers_chosen'])) == len(m['powers_chosen']),
                  f"{tag}: duplicate powers in powers_chosen")
            # powers_by_level is the only record of WHICH power sits at which level -- the
            # description entry keys its levels by power list ("psion/wilder"), not by class, so a
            # renderer cannot recover it. Both renderers group by these buckets.
            buckets = m['powers_by_level']
            check(len(buckets) == want_max + 1,
                  f"{tag}: powers_by_level has {len(buckets)} buckets, expected {want_max + 1} "
                  f"(levels 0..{want_max})")
            check(sorted(p for b in buckets for p in b) == sorted(m['powers_chosen']),
                  f"{tag}: powers_by_level does not reconcile with powers_chosen")
            check([len(b) for b in buckets] == m['powers_known_list'],
                  f"{tag}: powers_known_list {m['powers_known_list']} != bucket sizes "
                  f"{[len(b) for b in buckets]}")
            # Same failure the Metzofitz-feat check guards: a name with no rules text renders as an
            # empty row in Foundry and as nothing at all on the web sheet.
            missing = [p for p in m['powers_chosen'] if not descs.get(p)]
            check(not missing, f"{tag}: powers with no rules text: {missing[:5]}")
            if name == 'psion':
                # The discipline decides the psion's whole power list, so it cannot be blank.
                check(m['discipline'], f"{tag}: no discipline chosen")

    # ---- Occult Adventures ----
    features = payload.get('class features') or {}
    for entry in classes:
        name = entry['name']
        if name not in _OCCULT_BUCKETS:
            continue
        OCCULT['chars'] += 1
        level = entry['level']
        for dataset, bucket in _OCCULT_BUCKETS[name].items():
            tag = f"{cell}: {name}/{dataset}"
            pool = _OCCULT_OPTIONS[name][dataset]
            chosen = features.get(bucket) or {}
            # How many picks the schedule grants by this class level. A subsystem with no schedule
            # is a single pick taken at 1st -- the marksman/vitalist shape psionics already uses.
            want = schedule_due(SCHEDULE, name, bucket, level, len(pool))
            schedule = schedule_levels(SCHEDULE, name, bucket, level)
            if want is None:
                want = 1
            check(len(chosen) == want,
                  f"{tag}: {len(chosen)} pick(s) at class level {level}, expected {want}")
            OCCULT['picks'] += len(chosen)
            if schedule is not None and want > 1:
                OCCULT['multi_pick_buckets'] += 1
            # A pick that is not in the pool means the bucket was written by something else --
            # exactly the collision that would silently merge two classes' choices into one bucket.
            strays = [p for p in chosen if p not in pool]
            check(not strays, f"{tag}: picks that are not options: {strays[:5]}")
            # Same failure the psionics and Metzofitz checks guard: a name with no rules text is an
            # empty row in Foundry and nothing at all on the web sheet.
            blank = [p for p, text in chosen.items() if not str(text).strip()]
            check(not blank, f"{tag}: picks with no rules text: {blank[:5]}")

        if name == 'kineticist':
            # Burn is Constitution-priced and deliberately unmodelled (section 10), but the class
            # must never acquire a spellbook on the way past -- that is what a stray base_classes
            # or caster_mod entry would look like from out here.
            OCCULT['kineticists'] += 1
            books = [b for b in (payload.get('spellbooks') or []) if b.get('name') == 'kineticist']
            check(not books,
                  f"{cell}: kineticist has a spellbook; it is a non-caster in every table")
        else:
            OCCULT['casters'] += 1
            books = [b for b in (payload.get('spellbooks') or []) if b.get('name') == name]
            check(len(books) == 1,
                  f"{cell}: {name} casts psychic magic but has {len(books)} spellbook(s)")

    # ---- OGL section 10 ----
    # Serving extracted mechanics is Distribution, so every payload must point at the licence.
    check(payload.get('license_url'), f"{cell}: payload carries no license_url")

    # ---- HP ----
    max_hd = sum(hit_die(c['name']) * c['level'] for c in classes)
    check(payload['sheet_health'] == max_hd,
          f"{cell}: sheet_health {payload['sheet_health']} != full-HP hit dice {max_hd}")
    want_hp = max_hd + final_mod(payload, 'con') * L
    # Luck trades against HP (5 HP buys +1 luck; a seller gets 2 HP back per -1). It lands on
    # Total_HP and NOT on sheet_health, so the full-HP house rule above is unaffected -- but this
    # line has to know about it, or a lucky character reads as an HP bug.
    _lk = payload.get('luck') or {}
    _stake = _lk.get('stake') or {}
    luck_hp = (_stake.get('payout') or {}).get('hp', 0) - (_stake.get('paid') or {}).get('hp', 0)
    check(payload['Total_HP'] - want_hp - luck_hp in (0, L),
          f"{cell}: Total_HP {payload['Total_HP']} != {want_hp} (+favored 0|{L}, luck {luck_hp:+d})")

    check_luck(cell, payload)
    check_bonded_creatures(cell, payload)


def check_companion_feats(tag, entry, stats):
    """Spec section 8, D14/D15/D16 -- the feat economy and the modifier fold.

    `validate_companion_feats.py` gates the DATA (every pool name real, every declared effect
    landing on a probe block). What needs a whole generated creature is the wiring: that the labels
    line up with the feats they name, that no feat arrives that this body could not take, and that
    the fold left an audit trail instead of quietly moving a number.
    """
    if entry.get('type') not in COMPANION_FEAT_TYPES:
        return                       # familiars use the master's feats; eidolons are evolutions
    feats = entry.get('feats')
    labels = entry.get('feat_labels')
    check(isinstance(feats, list) and isinstance(labels, list),
          f"{tag}: feats/feat_labels are {type(feats).__name__}/{type(labels).__name__}, not lists")
    if not (isinstance(feats, list) and isinstance(labels, list)):
        return
    BOND['feats'] += len(feats)

    # A label list out of step with its feat list is the defect that renames every feat on the
    # sheet by one position -- silently, and only visibly wrong to someone who knows the chassis.
    check(len(labels) == len(feats),
          f"{tag}: {len(feats)} feats but {len(labels)} labels")
    noun = COMPANION_FEAT_TYPES[entry['type']]
    for label in labels:
        check(str(label).startswith(f'{noun} '),
              f"{tag}: label {label!r} does not read '{noun} <grant level>'")

    pool = set(COMPANION_POOL)
    strays = [f for f in feats + list(entry.get('flaw_feats') or []) if f not in pool]
    check(not strays, f"{tag}: feats that are not in the bonded-creature pool: {strays[:5]}")

    allowed = set(COMPANION_TAX_CHILDREN)
    for primary, children in (entry.get('feat_tax_dict') or {}).items():
        BOND['tax'] += len(children or [])
        outside = [c for c in children or [] if c not in allowed]
        check(not outside,
              f"{tag}: feat tax granted {outside[:5]} via {primary!r}, which is not on the "
              "tax_children allowlist -- that is how a wolf ends up with Drunken Brawler")

    # D16: flaws buy feats on the diminishing house ladder, exactly as they do for a PC.
    flaws = entry.get('flaws')
    check(isinstance(flaws, list), f"{tag}: flaws is {type(flaws).__name__}, not a list")
    if isinstance(flaws, list):
        BOND['flaws'] += len(flaws)
        check(len(flaws) <= 4, f"{tag}: {len(flaws)} flaws; the d100 ladder tops out at 4")
        check(sorted(entry.get('flaw_effects') or {}) == sorted(flaws),
              f"{tag}: flaw_effects does not reconcile with flaws")
        want = min(len(flaws) // 2 + 1, 3) if flaws else 0
        got = entry.get('flaw_feat_amount')
        check(got in (0, want),
              f"{tag}: {len(flaws)} flaws grant {got} feats, expected {want} (or 0 without the "
              "misc_homebrew flag)")
        check(len(entry.get('flaw_feats') or []) <= (got or 0),
              f"{tag}: {len(entry.get('flaw_feats') or [])} flaw feats but only {got} were bought")

    # D14: the fold leaves provenance. `stats` is FINAL for the web sheet, so an unexplained number
    # is unauditable -- and a source naming a feat the creature does not own is a fold gone wrong.
    applied = stats.get('applied_changes')
    check(isinstance(applied, list), f"{tag}: stats.applied_changes is missing")
    owned = set(feats) | set(entry.get('flaw_feats') or []) | set(entry.get('flaws') or [])
    owned |= {c for children in (entry.get('feat_tax_dict') or {}).values() for c in children or []}
    for record in applied or []:
        BOND['applied'] += 1
        source = str(record.get('source') or '')
        stem = source.split(' (via ')[0].split(') ', 1)[-1]
        check(stem in owned,
              f"{tag}: stats.applied_changes credits {source!r}, which the creature does not own")
    check(isinstance(stats.get('context_notes'), list),
          f"{tag}: stats.context_notes is missing")


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

        check_companion_feats(tag, entry, stats)

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


def check_choice_caps():
    """Generate the two classes whose pick counts are CAPPED, at a level where the cap bites.

    Separate from the sweep, and cheap on purpose -- the same shape as `check_level_ceiling` below.
    The standing sweep tops out at 20th, and no cap fires at or below 20: the schedules are smaller
    than the pools there, so `check_class_choices` reported `0 capped` across all 1,020 generations.
    Two of ticket 03's three terms were therefore never exercised, which is how the class-choices
    map's own note ("nothing yet KEEPS high levels running") would have come true again.

    The two cases, both real and both different:
      brawler   `max_num=8` at the call site holds it to 8 where the schedule grants 10 at 40th.
      tactician the POOL runs out -- 12 strategies exist and the schedule grants 13.

    Adding levels 25 and 40 to the whole 68-class matrix would have tripled the sweep's runtime to
    cover two rows. This costs two generations.
    """
    for name in ('brawler', 'tactician'):
        cell = f"cap {name} L40"
        try:
            with redirect_stdout(io.StringIO()):
                payload = main_test.generate_random_char(
                    class_choice=name, chosen_BAB='high', multi_class='N',
                    userInput_race='random', userInput_region='Tal-Falko',
                    alignment_input='random', userInput_gender='random',
                    high_level=40, low_level=40, gold_num=10000,
                    num_dice='4', num_sides='6', use_backstory_api='N',
                    spheres_flag='N', seed=9090)
        except Exception:
            tail = traceback.format_exc().strip().splitlines()
            REPORT.error(f"{cell}: generation raised -- {tail[-1]}")
            continue
        check_character(cell, payload)
    check(CHOICE_COVERAGE['capped'] > 0,
          "no class-choice bucket was capped by its pool or max_num anywhere in this run -- the "
          "min(scheduled, |pool|, max_num) branch is untested, so a regression in it would pass")
    print(f"  class-choice caps: exercised at 40th (brawler max_num, tactician pool)")


def check_level_ceiling():
    """Ask for characters ABOVE the ceiling and confirm they come back at it.

    Separate from the sweep, and cheap on purpose: the clamp is one branch, so it needs a handful
    of generations rather than a level added to the 68-class matrix. Multiclass is on, because the
    interesting half is `_split_levels` -- the total is capped in randomize_level and then divided
    somewhere else, so an off-by-one there produces a character that is over the ceiling without
    any single class being.

    `low_level` is raised with `high_level` so the roll cannot land under the ceiling by luck and
    report a pass it did not earn.
    """
    for requested in (MAX_CHARACTER_LEVEL + 1, 60, 999):
        cell = f"ceiling L{requested}"
        try:
            with redirect_stdout(io.StringIO()):
                payload = main_test.generate_random_char(
                    class_choice='random', chosen_BAB='high', multi_class='Y',
                    userInput_race='random', userInput_region='Tal-Falko',
                    alignment_input='random', userInput_gender='random',
                    high_level=requested, low_level=requested, gold_num=10000,
                    num_dice='4', num_sides='6', use_backstory_api='N',
                    spheres_flag='N', seed=7777)
        except Exception:
            tail = traceback.format_exc().strip().splitlines()
            REPORT.error(f"{cell}: generation raised -- {tail[-1]}")
            continue
        got = payload['total_level']
        check(got == MAX_CHARACTER_LEVEL,
              f"{cell}: asked for level {requested}, got {got} -- the clamp in randomize_level "
              f"should pin it to exactly {MAX_CHARACTER_LEVEL}")
        check_character(f"{cell} (gen seed {payload.get('generation_seed')})", payload)
    print(f"  level ceiling: clamped to {MAX_CHARACTER_LEVEL} from 41/60/999")


def check_luck_coverage(total):
    """Every luck branch must FIRE, or the checks above passed without asserting anything.

    Same guard as the bonded-creature and occult sections, and for the same reason: every assertion
    in check_luck is conditional on the character having rolled the branch. A sweep where nobody
    bought luck would print PASS having proved nothing about the purchase.

    TWO BRANCHES ARE NOT ASSERTED HERE, and the reason is a measured property of this sweep rather
    than an excuse. **Luck is seed-locked.** phase_luck_stake runs so early -- immediately after the
    level -- that the RNG state at that point is nearly identical across classes, so a given seed
    produces the SAME luck outcome for every class and level. Measured: seed 1101 rolls
    Proximity/buy for fighter, wizard, rogue and cleric at both L1 and L20; 2202 and 3303 roll no
    stake at all. This sweep runs 1,020 generations over THREE seeds, so it samples exactly three
    luck rolls -- it found 0 sellers and 0 Dimorphic characters not because they cannot happen, but
    because three draws did not contain them. check_luck_branches below is the answer: 200 distinct
    seeds, where the same code yields 15 sellers and 4 Dimorphic.

    ONE PATH IS NOT CENSUSED AT ALL: the Expanded Luck / Big Savings cap arithmetic. Those are two
    rows in a 1,129-trait pool drawn 8 at a time, offered only to the quarter of characters with a
    stake -- roughly 1 in 300. Requiring it would make the suite flaky rather than thorough, so
    validate_luck.py asserts the cap composition directly instead. Recorded rather than silently
    skipped, per the no-silent-caps rule.
    """
    if total >= 100:
        check(LUCK_COVERAGE['stakes'] > 0,
              f"no character took a luck stake in {total} generations -- every purchase, payout "
              f"and cap assertion in check_luck was skipped, so this run proves nothing")
        check(LUCK_COVERAGE['buy'] > 0,
              f"no character BOUGHT luck in {total} generations; the purchase path is unasserted")
        check(LUCK_COVERAGE['with_feats'] > 0,
              f"no character reached an E-Kat feat in {total} generations -- the reserved-slot "
              f"wiring is the only route to them, so this means it is broken")
        check(LUCK_COVERAGE['chains'] > 0,
              f"no E-Kat prerequisite chain ever completed in {total} generations -- the corrected "
              f"prereq data is untested")
        check(LUCK_COVERAGE['with_traits'] > 0,
              f"no character bought a Luck Trait in {total} generations -- the whole 25-E-Kat "
              f"purchase, the effect folding and the category gating are unasserted")
        check(LUCK_COVERAGE['deep_sale'] > 0,
              f"no character sold 25 luck or more in {total} generations -- the sell scale is "
              f"supposed to reach {LUCK_CAP_NEG}, and without the deep end most of the negative "
              f"trait catalogue is unreachable")
    print(f"  luck: {LUCK_COVERAGE['stakes']} stake(s) in {LUCK_COVERAGE['chars']} characters "
          f"({LUCK_COVERAGE['buy']} buy / {LUCK_COVERAGE['sell']} sell, "
          f"{LUCK_COVERAGE['negative']} negative, {LUCK_COVERAGE['nonzero_mod']} with a live mod)")
    print(f"  luck types: Default {LUCK_COVERAGE['Default']}, "
          f"Proximity {LUCK_COVERAGE['Proximity']}, Dimorphic {LUCK_COVERAGE['Dimorphic']} | "
          f"E-Kat feats on {LUCK_COVERAGE['with_feats']} character(s), "
          f"{LUCK_COVERAGE['chains']} with a completed chain, "
          f"{LUCK_COVERAGE['with_traits']} bought a Luck Trait")
    print(f"  negative luck: {LUCK_COVERAGE['deep_sale']} sale(s) of 25+ luck, "
          f"{LUCK_COVERAGE['negative_traits']} seller(s) bought a NEGATIVE Luck Trait "
          f"(of {len(NEGATIVE_TRAIT_NAMES)} in the catalogue)")


def check_luck_branches():
    """The luck branches this sweep's three seeds structurally cannot reach (see check_luck_coverage).

    Its own generations, and it earns them: selling luck and Dimorphic luck are the two branches
    with no other witness -- the -50 floor, the payout accounting and the 40 cap all hang off them,
    and the main sweep proved it can run 1,020 characters without touching either.

    The seeds are FIXED, so this is deterministic rather than flaky: it either always passes or
    always fails. If an upstream change shifts RNG consumption and a branch drops to zero, WIDEN the
    seed range -- do not delete the check, which is the only thing asserting these paths end to end.
    ~13s for 200 first-level fighters, on the same order as the class-choices sweep's addition.
    """
    seen = {'sell': 0, 'Dimorphic': 0, 'Proximity': 0, 'buy': 0}
    for offset in range(LUCK_BRANCH_SEEDS):
        try:
            with redirect_stdout(io.StringIO()):
                payload = main_test.generate_random_char(
                    class_choice='fighter', chosen_BAB='high', multi_class='N',
                    userInput_race='random', userInput_region='Tal-Falko',
                    alignment_input='random', userInput_gender='random',
                    high_level=1, low_level=1, gold_num=10000,
                    num_dice='4', num_sides='6', use_backstory_api='N',
                    spheres_flag='N', seed=LUCK_BRANCH_SEED_BASE + offset)
        except Exception:
            tail = traceback.format_exc().strip().splitlines()
            REPORT.error(f"luck branch seed {LUCK_BRANCH_SEED_BASE + offset}: "
                         f"generation raised -- {tail[-1]}")
            continue
        # Free extra coverage: every one of these gets the full per-character check too.
        check_luck(f"luck branch seed {LUCK_BRANCH_SEED_BASE + offset}", payload)
        lk = payload.get('luck') or {}
        seen[lk.get('type')] = seen.get(lk.get('type'), 0) + 1
        if lk.get('stake'):
            seen[lk['stake']['direction']] += 1

    check(seen['sell'] > 0,
          f"no character SOLD luck across {LUCK_BRANCH_SEEDS} distinct seeds -- the negative-luck "
          f"payout path is unasserted, and with it the -50 floor. Widen LUCK_BRANCH_SEEDS before "
          f"suspecting the generator")
    check(seen['Dimorphic'] > 0,
          f"no Dimorphic character across {LUCK_BRANCH_SEEDS} distinct seeds -- the three-equal-"
          f"values branch and the 40 cap are unasserted. Widen LUCK_BRANCH_SEEDS first")
    check(seen['Proximity'] > 0,
          f"no Proximity character across {LUCK_BRANCH_SEEDS} distinct seeds")
    print(f"  luck branches ({LUCK_BRANCH_SEEDS} distinct seeds): {seen['buy']} buy, "
          f"{seen['sell']} sell, Proximity {seen['Proximity']}, Dimorphic {seen['Dimorphic']}")


def run(classes, levels, seeds):
    total = len(classes) * len(levels) * len(seeds)
    done = 0
    for name in classes:
        for level in levels:
            # Paizo wealth-by-level, not a constant. This used to be gold_num=10000 at EVERY
            # level -- ~7x wealth at L1 and ~1% at L40 -- and the first power baseline read that
            # fixed purse against a rising benchmark as "characters fall progressively behind the
            # CR curve". The level bands are only comparable when each is funded the way
            # production funds it (data.wealth_by_level is also assign_gold's table).
            purse = data.wealth_by_level(level)
            for seed in seeds:
                cell = f"{name} L{level} seed {seed}"
                done += 1
                try:
                    with redirect_stdout(io.StringIO()):
                        payload = main_test.generate_random_char(
                            class_choice=name, chosen_BAB='high', multi_class='N',
                            userInput_race='random', userInput_region='Tal-Falko',
                            alignment_input='random', userInput_gender='random',
                            high_level=level, low_level=level, gold_num=purse,
                            num_dice='4', num_sides='6', use_backstory_api='N',
                            spheres_flag='N', seed=seed)
                except Exception:
                    tail = traceback.format_exc().strip().splitlines()
                    REPORT.error(f"{cell}: generation raised -- {tail[-1]} "
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
    parser.add_argument('--score', nargs='?', const='-', default=None, metavar='PATH',
                        help='also score every generated character with power_metric and write '
                             'the profiles as JSON (default: the scratchpad). Off unless passed, '
                             'so CI is unaffected.')
    args = parser.parse_args()

    global SCORING
    SCORING = args.score is not None

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

    # Runs on every invocation, including `--classes fighter`: it is three generations, and it is
    # the only thing that exercises the clamp at all.
    check_level_ceiling()
    check_choice_caps()

    # Existence check only on a sweep big enough that zero picks means the wiring broke, not luck.
    if total >= 100:
        check(METZ_PICKS[0] > 0,
              f"no Metzofitz homebrew feat appeared in {total} generations -- pool wiring broken?")
    print(f"  Metzofitz picks across the sweep: {METZ_PICKS[0]}")

    check_luck_branches()
    check_luck_coverage(total)

    # The companion checks above are all conditional on a creature existing, so a sweep that rolled
    # none would print PASS having asserted nothing. Say so instead.
    if total >= 100:
        check(BOND['granted'] > 0,
              f"no bonded creature was granted in {total} generations -- every companion check "
              f"above was skipped, so this run proves nothing about them")
        check(BOND['druid_flip'] > 0,
              f"the druid flip was never reached in {total} generations")
        # Same guard one level down: the whole feat economy is gated behind a granted creature, so
        # a run that granted creatures but rolled no feats or no flaws asserted nothing about D15.
        check(BOND['feats'] > 0,
              f"{BOND['granted']} bonded creatures were granted in {total} generations but not one "
              f"feat was rolled -- every D15 check above was skipped")
        check(BOND['flaws'] > 0,
              f"{BOND['granted']} bonded creatures were granted but not one flaw was rolled -- "
              f"every D16 flaw check above was skipped")
    print(f"  bonded creatures: {BOND['granted']} granted, {BOND['absent']} absence entries, "
          f"{BOND['druid_flip']} druid flips (both={BOND['both']}, neither={BOND['neither']})")
    print(f"  companion feats: {BOND['feats']} rolled, {BOND['tax']} taxed in, "
          f"{BOND['flaws']} flaws, {BOND['applied']} folded changes")

    # Same guard, same reason: every occult check is conditional on rolling one of the six.
    if total >= 100:
        check(OCCULT['chars'] > 0,
              f"no occult class was rolled in {total} generations -- every occult check above was "
              f"skipped, so this run proves nothing about them")
        check(OCCULT['multi_pick_buckets'] > 0,
              "no occult multi-pick bucket was ever exercised; only single picks were checked")
        check(OCCULT['kineticists'] > 0 and OCCULT['casters'] > 0,
              f"the occult sweep reached {OCCULT['kineticists']} kineticist(s) and "
              f"{OCCULT['casters']} caster(s) -- both sides of the spellbook split must be hit")
    print(f"  occult classes: {OCCULT['chars']} rolled, {OCCULT['picks']} picks, "
          f"{OCCULT['multi_pick_buckets']} multi-pick buckets "
          f"({OCCULT['kineticists']} kineticist, {OCCULT['casters']} caster)")

    # Branch coverage for the class-choice check, same rule as BOND and OCCULT: every assertion in
    # it is conditional on a rolled class declaring a bucket, so a sweep that reached none would
    # print PASS having asserted nothing about the map's whole subject.
    check(CHOICE_COVERAGE['buckets'] > 0,
          "the class-choice check asserted on zero buckets -- it is passing vacuously")
    print(f"  class choices: {CHOICE_COVERAGE['buckets']} bucket(s) asserted across "
          f"{CHOICE_COVERAGE['chars']} character(s), {CHOICE_COVERAGE['picks']} picks, "
          f"{CHOICE_COVERAGE['stamps']} level stamps, {CHOICE_COVERAGE['capped']} capped by "
          f"pool/max_num, {CHOICE_COVERAGE['skipped']} skipped (see CHOICE_SKIP)")

    check_power_metric()
    if SCORING:
        target = (BACKEND / 'scripts' / '_power_baseline.json') if args.score == '-' \
            else Path(args.score)
        target.write_text(json.dumps(SCORE_ROWS, indent=1), encoding='utf-8')
        print(f"  power metric: {len(SCORE_ROWS)} profile(s) -> {target}")

    return REPORT.finish(f'{REPORT.checks} checks')


if __name__ == '__main__':
    sys.exit(main())
