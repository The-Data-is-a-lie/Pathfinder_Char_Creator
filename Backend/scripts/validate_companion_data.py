"""Gate on Backend/json/animal_choices.json -- the companion data the advancement merge reads.

    C:\\Python310\\python.exe Backend/scripts/validate_companion_data.py

Map #18, ticket #27. `repair_animal_choices.py` fixed six scrape defects; this is what stops them
coming back the next time the file is touched. It shares that script's vocabulary -- SIZES, the
block regexes, the drifted key spellings -- by importing them, so the repairer and the gate cannot
disagree about what a well-formed block looks like.

WHAT IS AN ERROR, AND WHY IT IS NOT THE WHOLE SIZE PACKAGE
----------------------------------------------------------
The spec (feature_spec_todo.md §8) describes the PF1e size-up package as Str +8 / Dex -2 / Con +4 /
natural armor +2. That is the Medium -> Large row of the size-change table, not a universal rule:
Small -> Medium is Str +4 / Con +2, and Large -> Huge carries natural armor +3. Measured against
the *correct*, size-scaled table, 97 of the 153 one-step size increases in this file still deviate
-- `bear, grizzly` grows to Large on Str +4, for one. Those are the published per-species entries,
and the published entry is the authority for a companion, not a table derived from it.

So the deviations are reported as WARN and do not fail. What fails is the class of damage a scrape
actually does, and that no legitimate entry can exhibit:

  * a bare int where an advancement delta belongs   (the sign was lost -- the #26 defect)
  * a positive Dex on a size increase               (PF1e never raises Dex when a creature grows)
  * an absolute score written as a delta, or vice versa
  * prose in an ability slot                        (field bleed)
  * an underscored key spelling shadowing a spaced one
  * an `ac` that is not a natural-armor delta
  * a size outside the nine categories

Done when: exit 0 on the repaired data, non-zero on a deliberately reverted row.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from repair_animal_choices import (          # noqa: E402  -- one owner for the shared vocabulary
    ADV_RE, KEY_DRIFT, SIGNED_RE, SIZES, START_RE, STATS, size_step,
)

PATH = os.path.join(HERE, '..', 'json', 'animal_choices.json')

AC_STRICT_RE = re.compile(r'^[+\-]\d+ natural armor$')

# PF1e Table: Size Changes, keyed by the size a creature grows INTO. Advisory here -- the WARN
# block measures against it; nothing fails for disagreeing with it.
SIZE_CHANGE_TABLE = {
    'diminutive': {'str': 2, 'dex': -2, 'con': 0, 'na': 0},
    'tiny':       {'str': 4, 'dex': -2, 'con': 0, 'na': 0},
    'small':      {'str': 4, 'dex': -2, 'con': 2, 'na': 0},
    'medium':     {'str': 4, 'dex': -2, 'con': 2, 'na': 2},
    'large':      {'str': 8, 'dex': -2, 'con': 4, 'na': 2},
    'huge':       {'str': 8, 'dex': -2, 'con': 4, 'na': 3},
    'gargantuan': {'str': 8, 'dex': 0,  'con': 4, 'na': 4},
    'colossal':   {'str': 8, 'dex': 0,  'con': 4, 'na': 5},
}

# Species-body keys that are neither a stat block nor an advancement block, and are fine.
BODY_METADATA = ('source', 'description')
# A one-off special ability parked at body level, e.g. "sudden charge (ex)", "blood rage*".
ABILITY_KEY_RE = re.compile(r'\((?:ex|su|sp)\)\s*$|\*$')

# ---------------------------------------------------------------------------------------------
# The closed vocabulary from the D8 grill (#38). It lives here because this is the gate the
# grantor resolver (#30) and the archetype triad (#40) both import it from -- one owner, the way
# validate_maneuver_changes.py takes MOD_TARGETS from validate_quality_effects.py rather than
# restating it. Both files are validated below once they exist.
# ---------------------------------------------------------------------------------------------
OUTCOMES = ('granted', 'domain', 'bonded_object', 'bond_with_allies', 'archetype_removed')
EFFECTS = ('removes', 'forces', 'species_pool', 'progression', 'none')
FLAGS = ('species_pool_unavailable',)

errors = []
warnings = []
deviations = {}     # WARN grouping: reason -> [where]


def note_deviation(reason, where):
    deviations.setdefault(reason, []).append(where)


def natural_armor(value):
    """The +N from a natural-armor delta, or None if absent, or 'BAD' if malformed."""
    if value is None:
        return None
    if not isinstance(value, str) or not AC_STRICT_RE.match(value.strip()):
        return 'BAD'
    return int(value.strip().split()[0])


def check_key_drift(node, path):
    """No underscored spelling may shadow the spaced one, at any depth."""
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        if key in KEY_DRIFT:
            errors.append(f'{"/".join(path)}: drifted key {key!r} '
                          f'(use {KEY_DRIFT[key]!r})')
        check_key_drift(value, path + [str(key)])


def check_ability_block(where, ability, absolute):
    """`absolute` -> bare ints (starting statistics); otherwise signed strings (deltas)."""
    if not isinstance(ability, dict):
        errors.append(f'{where}: "ability scores" is {type(ability).__name__}, not an object')
        return
    for stat, value in ability.items():
        if stat not in STATS:
            errors.append(f'{where}: {stat!r} is not an ability score -- field bleed?')
            continue
        if value is None:                      # mindless: PF1e "no Int score"
            continue
        if absolute:
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f'{where}: {stat} = {value!r} -- starting statistics hold '
                              f'absolute scores as bare ints')
        else:
            if isinstance(value, int):
                errors.append(f'{where}: {stat} = {value!r} -- bare int in an advancement '
                              f'block means the sign was lost')
            elif not (isinstance(value, str) and SIGNED_RE.match(value.strip())):
                errors.append(f'{where}: {stat} = {value!r} -- advancement deltas are signed '
                              f'strings ("+8", "-2")')


def check_size_package(where, start, block):
    """Errors on the impossible; WARNs on disagreement with the size-change table."""
    step = size_step(start, block)
    if step is None or step <= 0:
        return
    ability = block.get('ability scores') or {}
    dex = ability.get('dex')
    if isinstance(dex, str) and SIGNED_RE.match(dex.strip()) and int(dex) > 0:
        errors.append(f'{where}: dex {dex} on a size increase -- PF1e never raises Dex when a '
                      f'creature grows')
    if step > 1:
        note_deviation(f'size grows {step} categories in one block', where)
        return

    want = SIZE_CHANGE_TABLE.get(str(block.get('size', '')).strip().lower())
    if want is None:
        return
    off = []
    for stat in ('str', 'dex', 'con'):
        if not want[stat]:
            continue
        got = ability.get(stat)
        if got != f'{want[stat]:+d}':
            off.append(f'{stat} {got!r} (table {want[stat]:+d})')
    got_na = natural_armor(block.get('ac'))
    if got_na == 'BAD':
        pass                                   # already an error; do not double-report
    elif got_na is None and want['na']:
        off.append(f'no ac (table +{want["na"]} natural armor)')
    elif isinstance(got_na, int) and got_na != want['na']:
        off.append(f'ac +{got_na} (table +{want["na"]})')
    if off:
        note_deviation('; '.join(off), where)


def check_species(tier, name, body):
    where_species = f'{tier}/{name}'
    if not isinstance(body, dict):
        errors.append(f'{where_species}: species body is {type(body).__name__}, not an object')
        return

    starts = [k for k in body if START_RE.match(k)]
    advancements = [k for k in body if ADV_RE.match(k)]
    if len(starts) != 1:
        errors.append(f'{where_species}: {len(starts)} "starting statistics" blocks, expected 1')
    if len(advancements) > 1:
        note_deviation(f'{len(advancements)} advancement blocks', where_species)

    for key, value in body.items():
        if key in starts or key in advancements or key in BODY_METADATA:
            continue
        if ABILITY_KEY_RE.search(key):
            note_deviation('one-off ability parked at species level', f'{where_species}: {key!r}')
        elif isinstance(value, dict) and any(START_RE.match(k) for k in value):
            errors.append(f'{where_species}: {key!r} looks like a species nested inside another '
                          f'-- the scrape lost a level')
        else:
            note_deviation('unrecognised species-body key', f'{where_species}: {key!r}')

    start = body.get(starts[0]) if starts else None
    for key in starts + advancements:
        block = body[key]
        where = f'{where_species} {key}'
        if not isinstance(block, dict):
            errors.append(f'{where}: block is {type(block).__name__}, not an object')
            continue
        if 'ability scores' in block:
            check_ability_block(where, block['ability scores'], absolute=bool(START_RE.match(key)))
        size = block.get('size')
        if size is not None and str(size).strip().lower() not in SIZES:
            errors.append(f'{where}: size {size!r} is not one of the nine categories')
        if 'ac' in block and natural_armor(block['ac']) == 'BAD':
            errors.append(f'{where}: ac {block["ac"]!r} is not a "+N natural armor" delta')
        if ADV_RE.match(key):
            check_size_package(where, start, block)


def check_closed_vocabulary():
    """#30 and #40 write these files; validate them the moment they appear, not later."""
    grantors = os.path.join(HERE, '..', 'json', 'companion_grantors.json')
    archetypes = os.path.join(HERE, '..', 'json', 'companion_archetypes.json')

    if os.path.exists(grantors):
        with open(grantors, encoding='utf-8') as fh:
            table = json.load(fh)
        rows = table.get('grantors') if isinstance(table, dict) else table
        if not isinstance(rows, list):
            errors.append('companion_grantors.json: expected a "grantors" list')
            rows = []
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                errors.append(f'companion_grantors.json: row is {type(row).__name__}, not an '
                              f'object')
                continue
            key = (row.get('grantor'), row.get('creature_type'))
            if key in seen:
                errors.append(f'companion_grantors.json: duplicate row for {key}')
            seen.add(key)
            if row.get('creature_type') not in ('companion', 'mount', 'familiar', 'eidolon'):
                errors.append(f'companion_grantors.json: {row.get("grantor")!r} creature_type = '
                              f'{row.get("creature_type")!r} is not a bonded-creature type')
            choice = row.get('choice') or {}
            for side in ('on_win', 'on_loss'):
                value = choice.get(side)
                if value is not None and value not in OUTCOMES:
                    errors.append(f'companion_grantors.json: {row.get("grantor")!r} {side} = '
                                  f'{value!r} is not in {OUTCOMES}')
            odds = choice.get('odds')
            if choice and not (isinstance(odds, int) and 1 <= odds <= 100):
                errors.append(f'companion_grantors.json: {row.get("grantor")!r} odds = {odds!r} '
                              f'is not a 1-100 roll target')
    else:
        warnings.append('companion_grantors.json does not exist yet (#30) -- outcome vocabulary '
                        'unchecked')

    if os.path.exists(archetypes):
        with open(archetypes, encoding='utf-8') as fh:
            entries = json.load(fh)
        for key, entry in entries.items():
            effect = (entry or {}).get('effect')
            if effect not in EFFECTS:
                errors.append(f'companion_archetypes.json: {key!r} effect = {effect!r} is not '
                              f'in {EFFECTS}')
    else:
        warnings.append('companion_archetypes.json does not exist yet (#40) -- effect vocabulary '
                        'unchecked')


def main():
    with open(PATH, encoding='utf-8') as fh:
        data = json.load(fh)

    check_key_drift(data, ['animal_choices.json'])
    species_count = 0
    for tier, species in data.items():
        if not isinstance(species, dict):
            errors.append(f'{tier}: tier is {type(species).__name__}, not an object')
            continue
        for name, body in species.items():
            species_count += 1
            check_species(tier, name, body)
    check_closed_vocabulary()

    for message in warnings:
        print(f'WARN: {message}')
    if deviations:
        total = sum(len(v) for v in deviations.values())
        print(f'WARN: {total} advancement block(s) disagree with the PF1e size-change table or '
              f'carry an unusual key. The published per-species entry is the authority, so this '
              f'is an audit surface, not a failure:')
        for reason, where in sorted(deviations.items(), key=lambda kv: -len(kv[1])):
            print(f'  {len(where):>4}  {reason}')
            for one in where[:2]:
                print(f'          e.g. {one}')

    if errors:
        print()
        for message in errors:
            print(message)
        print(f'FAILED: {len(errors)} problem(s)')
        return 1

    print(f'OK: {species_count} species across {len(data)} tiers -- advancement deltas signed, '
          f'no Dex raised on a size increase, no key drift, no prose in an ability slot')
    return 0


if __name__ == '__main__':
    sys.exit(main())
