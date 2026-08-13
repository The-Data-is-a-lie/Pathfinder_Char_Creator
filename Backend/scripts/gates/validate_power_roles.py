"""The role table must resolve against the code, the roster and the corpus (spec 15, ruling 2026-08-11).

    C:/Python310/python.exe Backend/scripts/gates/validate_power_roles.py

WHY THIS GATE EXISTS
--------------------
power_roles.json is the optimizer's whole tuning surface, and every one of its vocabularies is a
name that must match something else exactly: a primary axis must be one the metric measures, a
gear-ladder token one the chooser resolves, a feat one data/feats.csv spells that way, a class one
class_data.json knows. A miss in any of them is the stack's signature silent-nothing bug -- the
role would simply not do that part of its job, forever, and nothing would say so.

It also asserts two RULINGS as invariants, not conventions: casting roles carry no dips (CL
fragmentation is the one measured multiclass cost), and the class_roles map covers the rollable
roster exactly -- a class added to the pool without a role row must fail here, the same shape as
class_choice_schedule.json's one-row-per-class rule.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import JSON_DIR, Report, read_json                                    # noqa: E402
from validate_power_metric import BENCHMARKED_AXES, REQUIRED_AXES, feat_names       # noqa: E402

from utils.class_func import power_role                                             # noqa: E402
from utils import data as gen_data                                                  # noqa: E402

REPORT = Report('validate_power_roles')

# Axes a role may name as primary = everything the metric emits. The expected/diagnostic pair
# rides along in profiles but a role must not target them -- they share their benchmarked twin's
# meaning and would double-count it.
TARGETABLE_AXES = tuple(a for a in REQUIRED_AXES if not a.endswith('_expected'))


def rollable_roster():
    """class_data.json keys minus the holdback lists in data.py -- the derivation
    _available_class_pool uses, recomputed here from the same sources."""
    table = read_json(JSON_DIR / 'class_data.json')
    held = set()
    for attr in ('pow_classes_pending_foundry', 'psionic_classes_pending',
                 'occult_classes', 'classes_pending_foundry'):
        held.update(str(x).lower() for x in getattr(gen_data, attr, []) or [])
    return {c.lower() for c in table} - held


def check_roles(table):
    corpus = feat_names()
    roles = {k: v for k, v in (table.get('roles') or {}).items() if not k.startswith('_')}
    if not REPORT.check(roles, 'power_roles.json defines no roles'):
        return roles
    for name, row in roles.items():
        primaries = row.get('primaries') or []
        REPORT.check(1 <= len(primaries) <= 3,
                     f'role {name!r}: {len(primaries)} primaries -- the ruling says 2-3 axes '
                     f'(1 tolerated), a longer list is a weighted objective in disguise')
        for axis in primaries:
            REPORT.check(axis in TARGETABLE_AXES,
                         f'role {name!r} primary {axis!r} is not an axis the metric measures '
                         f'(known: {sorted(TARGETABLE_AXES)}) -- a role may only name a measured '
                         f'primary, by ruling')
        for axis, floor in (row.get('floors') or {}).items():
            REPORT.check(axis in BENCHMARKED_AXES,
                         f'role {name!r} floors {axis!r}, which has no benchmark ratio to floor')
            REPORT.check(isinstance(floor, (int, float)) and 0 < floor <= 1.5,
                         f'role {name!r} floor {axis}={floor!r} is not a sane ratio bound')
        for token in row.get('stat_priority') or []:
            REPORT.check(token in power_role.STAT_TOKENS,
                         f'role {name!r} stat_priority token {token!r} is not one '
                         f'power_role.STAT_TOKENS knows -- it would be skipped silently')
        REPORT.check(row.get('weapon_policy') in power_role.WEAPON_POLICIES,
                     f'role {name!r} weapon_policy {row.get("weapon_policy")!r} is not one the '
                     f'chooser implements (known: {power_role.WEAPON_POLICIES})')
        split = row.get('enhancement_split') or {}
        REPORT.check(set(split) == {'weapon', 'armor', 'shield'},
                     f'role {name!r} enhancement_split keys {sorted(split)} != weapon/armor/shield')
        total = sum(v for v in split.values() if isinstance(v, (int, float)))
        REPORT.check(abs(total - 1.0) < 0.001,
                     f'role {name!r} enhancement_split sums to {total}, not 1.0 -- part of the '
                     f'budget would evaporate (or be spent twice)')
        ladders = {k: v for k, v in (row.get('gear_ladders') or {}).items()
                   if not k.startswith('_')}
        REPORT.check(2 <= len(ladders) <= 3,
                     f'role {name!r} has {len(ladders)} gear ladders -- the ruling is 2-3 '
                     f'(variety through build divergence, not suboptimal purchases)')
        for ladder, steps in ladders.items():
            for step in steps or []:
                REPORT.check(step in power_role.GEAR_LADDER_TOKENS,
                             f'role {name!r} ladder {ladder!r} step {step!r} is not a '
                             f'power_role.GEAR_LADDER_TOKENS entry -- the chooser would skip it')
        for feat in row.get('feat_spine') or []:
            REPORT.check(feat in corpus,
                         f'role {name!r} feat_spine names {feat!r}, which is in no data/feats.csv '
                         f'row -- it would never be granted')
        dips = row.get('dips')
        REPORT.check(isinstance(dips, list),
                     f'role {name!r} has no dips list (empty is fine; absent is a hole)')
        if row.get('casting'):
            REPORT.check(not dips,
                         f'role {name!r} is a casting role but carries dips -- the ruling protects '
                         f'CL/DC: casting roles stay single-class')
    return roles


def check_dips(table, roster):
    for name, row in (table.get('roles') or {}).items():
        if name.startswith('_'):
            continue
        for dip in row.get('dips') or []:
            cls = str(dip.get('class') or '').lower()
            REPORT.check(cls in roster,
                         f'role {name!r} dip class {cls!r} is not in the rollable roster')
            REPORT.check(isinstance(dip.get('levels'), int) and 1 <= dip['levels'] <= 2,
                         f'role {name!r} dip {cls!r} levels {dip.get("levels")!r} -- a dip is '
                         f'1-2 levels, anything deeper is a multiclass the role table must argue '
                         f'for differently')
            REPORT.check(bool(str(dip.get('buys') or '').strip()),
                         f'role {name!r} dip {cls!r} does not say what it buys -- the ruling '
                         f'requires the dip to name its purchase')


def check_class_map(table, roles, roster):
    mapping = {str(k).lower(): v for k, v in (table.get('class_roles') or {}).items()}
    missing = sorted(roster - set(mapping))
    extra = sorted(set(mapping) - roster)
    REPORT.check(not missing,
                 f'class_roles is missing {len(missing)} rollable class(es): {missing[:8]} -- a '
                 f'class without a role row would fall back to every role, silently')
    REPORT.check(not extra,
                 f'class_roles names {extra[:8]}, which are not rollable -- stale rows that would '
                 f'hide a rename')
    used = set()
    for cls, candidates in mapping.items():
        REPORT.check(isinstance(candidates, list) and candidates,
                     f'class_roles[{cls!r}] is empty -- the class would fall back to every role')
        for role in candidates or []:
            REPORT.check(role in roles,
                         f'class_roles[{cls!r}] names role {role!r}, which is not defined')
            used.add(role)
    unreachable = sorted(set(roles) - used)
    REPORT.check(not unreachable,
                 f'role(s) {unreachable} are defined but no class maps to them -- dead rows')


def main():
    table = read_json(JSON_DIR / 'power_roles.json')
    roster = rollable_roster()
    roles = check_roles(table)
    check_dips(table, roster)
    check_class_map(table, roles, roster)
    return REPORT.finish(f'{len(roles)} roles, {len(table.get("class_roles") or {})} class rows, '
                         f'{len(roster)} rollable classes')


if __name__ == '__main__':
    sys.exit(main())
