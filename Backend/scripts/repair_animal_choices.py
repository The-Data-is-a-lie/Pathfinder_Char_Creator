"""Scripted, idempotent repair of Backend/json/animal_choices.json.

The file was webscraped and carries five defects, all of which corrupt a companion's
stat block once the advancement blocks are merged (map #18, ticket #26):

1. NESTING     - the scrape lost a nesting level at `seahorse` and swallowed the next
                 eleven alphabetical species into its body, where nothing can reach
                 them; `seahorse` and `walrus` also hold their own advancement block
                 one level too deep, inside `starting statistics`.
2. KEY DRIFT   - six underscored spellings shadow the spaced ones, at both block and
                 field level, so a lookup on the spaced form silently misses them.
3. SIGN LOSS   - advancement `dex` deltas lost their minus sign. A PF1e size increase
                 never raises Dex, so a positive value on a size-up row is a scrape
                 artefact, not data.
4. FIELD BLEED - `faerie mount`'s advancement `ability scores` block swallowed the
                 sibling `size` / `speed` / `attack` fields.
5. MINDLESS INT- vermin render PF1e's "no Int score" as both `""` and `null`.

Advancement ability values are normalised to **signed strings** (`"+8"`, `"-2"`); the
absolute scores in `starting statistics` stay bare ints. That type split is what lets
validate_companion_data.py assert "no bare int survives in an advancement block".

Usage:
    python Backend/scripts/repair_animal_choices.py [--dry-run]

Idempotent: a second run reports zero repairs and rewrites nothing.
"""
import argparse
import json
import os
import re
import sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    '..', 'json', 'animal_choices.json')

SIZES = ['fine', 'diminutive', 'tiny', 'small', 'medium',
         'large', 'huge', 'gargantuan', 'colossal']

ADV_RE = re.compile(r'^\d+(?:st|nd|rd|th)-level[ _]advancement$')
START_RE = re.compile(r'^starting[ _]statistics$')
SIGNED_RE = re.compile(r'^[+\-]\d+$')

STATS = ('str', 'dex', 'con', 'int', 'wis', 'cha')

# Underscored spellings -> the spaced form that every lookup uses.
KEY_DRIFT = {
    'starting_statistics': 'starting statistics',
    'ability_scores': 'ability scores',
    'special_attacks': 'special attacks',
    'special_qualities': 'special qualities',
}

# The eleven species swallowed by `seahorse`, in the order they appear in its body.
SWALLOWED_HOST = 'seahorse'

# Fields that bled into an `ability scores` block and belong to its parent.
BLED_FIELDS = ('size', 'speed', 'ac', 'attack', 'special qualities', 'special attacks')


class Report:
    def __init__(self):
        self.repairs = []      # (defect, detail)
        self.untouched = []    # things deliberately left alone

    def fix(self, defect, detail):
        self.repairs.append((defect, detail))

    def leave(self, detail):
        self.untouched.append(detail)

    def count(self, defect):
        return sum(1 for d, _ in self.repairs if d == defect)


def normalise_adv_key(key):
    """`4th-level_advancement` -> `4th-level advancement`."""
    return key.replace('-level_advancement', '-level advancement')


def repair_key_drift(node, path, rep):
    """Recursively rename drifted keys, preserving insertion order."""
    if not isinstance(node, dict):
        return node
    out = {}
    for key, value in node.items():
        new = KEY_DRIFT.get(key, key)
        if ADV_RE.match(key):
            new = normalise_adv_key(key)
        if new != key:
            if new in node:
                rep.leave(f'{"/".join(path)}: {key!r} would collide with existing '
                          f'{new!r} - left alone')
                new = key
            else:
                rep.fix('key drift', f'{"/".join(path)}: {key!r} -> {new!r}')
        out[new] = repair_key_drift(value, path + [new], rep)
    return out


def repair_nesting(tier_name, species, rep):
    """Hoist swallowed species to the tier, and over-deep advancement blocks to the body."""
    host = species.get(SWALLOWED_HOST)
    if isinstance(host, dict):
        swallowed = [k for k, v in host.items()
                     if isinstance(v, dict)
                     and any(START_RE.match(ik) or ADV_RE.match(ik) for ik in v)
                     and not START_RE.match(k) and not ADV_RE.match(k)]
        if swallowed:
            rebuilt = {}
            for name, body in species.items():
                if name != SWALLOWED_HOST:
                    rebuilt[name] = body
                    continue
                rebuilt[name] = {k: v for k, v in body.items() if k not in swallowed}
                for victim in swallowed:
                    if victim in species:
                        rep.leave(f'{tier_name}/{victim!r} already exists at tier level '
                                  f'- nested copy dropped')
                        continue
                    rebuilt[victim] = host[victim]
                    rep.fix('nesting', f'{tier_name}: hoisted {victim!r} out of '
                                       f'{SWALLOWED_HOST!r}')
            species = rebuilt

    # An advancement block sitting inside `starting statistics` belongs beside it.
    for name, body in species.items():
        if not isinstance(body, dict):
            continue
        for bkey, bval in list(body.items()):
            if not (START_RE.match(bkey) and isinstance(bval, dict)):
                continue
            deep = [k for k in bval if ADV_RE.match(k)]
            for adv in deep:
                if adv in body:
                    rep.leave(f'{tier_name}/{name!r}: {adv!r} nested inside {bkey!r} '
                              f'duplicates the top-level block - left alone')
                    continue
                body[adv] = bval.pop(adv)
                rep.fix('nesting', f'{tier_name}/{name!r}: lifted {adv!r} out of {bkey!r}')
    return species


def repair_field_bleed(tier_name, name, block_key, block, rep):
    """Lift sibling fields that bled into an `ability scores` sub-dict."""
    ability = block.get('ability scores')
    if not isinstance(ability, dict):
        return
    for field in list(ability):
        if field in STATS or field not in BLED_FIELDS:
            continue
        if field in block:
            rep.leave(f'{tier_name}/{name!r} {block_key}: bled {field!r} duplicates an '
                      f'existing field - left alone')
            ability.pop(field)
            continue
        block[field] = ability.pop(field)
        rep.fix('field bleed', f'{tier_name}/{name!r} {block_key}: lifted {field!r} '
                               f'out of "ability scores"')


def repair_mindless_int(tier_name, name, block_key, block, rep):
    """PF1e mindless creatures have no Int score; `""` and `null` both mean that."""
    ability = block.get('ability scores')
    if not isinstance(ability, dict):
        return
    if 'int' in ability and isinstance(ability['int'], str) and not ability['int'].strip():
        ability['int'] = None
        rep.fix('mindless int', f'{tier_name}/{name!r} {block_key}: int "" -> null')


def size_step(start_block, adv_block):
    """How many size categories the advancement grows, or None if undeterminable."""
    if not isinstance(start_block, dict) or not isinstance(adv_block, dict):
        return None
    a, b = start_block.get('size'), adv_block.get('size')
    if not (isinstance(a, str) and isinstance(b, str)):
        return None
    a, b = a.strip().lower(), b.strip().lower()
    if a not in SIZES or b not in SIZES:
        return None
    return SIZES.index(b) - SIZES.index(a)


def repair_signs(tier_name, name, block_key, block, step, rep):
    """Normalise advancement deltas to signed strings, restoring the lost Dex minus."""
    ability = block.get('ability scores')
    if not isinstance(ability, dict):
        return
    for stat in STATS:
        if stat not in ability:
            continue
        value = ability[stat]
        if value is None or (isinstance(value, str) and SIGNED_RE.match(value.strip())):
            continue
        if isinstance(value, str):
            # U+2212 MINUS SIGN and stray whitespace both appear in the scrape.
            cleaned = value.strip().replace('−', '-')
            if SIGNED_RE.match(cleaned):
                ability[stat] = cleaned
                rep.fix('sign', f'{tier_name}/{name!r} {block_key}: {stat} {value!r} '
                                f'-> {cleaned!r}')
                continue
            rep.leave(f'{tier_name}/{name!r} {block_key}: {stat} = {value!r} is not a '
                      f'delta - left alone')
            continue
        if not isinstance(value, int):
            rep.leave(f'{tier_name}/{name!r} {block_key}: {stat} = {value!r} '
                      f'({type(value).__name__}) - left alone')
            continue

        # A bare int in an advancement block lost its sign. Only Dex on a size
        # increase can be recovered by rule; everything else is assumed positive.
        if stat == 'dex' and step is not None and step > 0:
            if value > 0:
                ability[stat] = f'-{value}'
                rep.fix('sign', f'{tier_name}/{name!r} {block_key}: dex {value} -> '
                                f'"-{value}" (size {step:+d})')
            else:
                ability[stat] = f'{value}'
                rep.fix('sign', f'{tier_name}/{name!r} {block_key}: dex {value} -> '
                                f'"{value}" (already negative, typed)')
        elif stat == 'dex':
            rep.leave(f'{tier_name}/{name!r} {block_key}: dex = {value} but the block '
                      f'shows no size increase - sign not recoverable, left alone')
        else:
            ability[stat] = f'+{value}' if value > 0 else f'{value}'
            rep.fix('sign', f'{tier_name}/{name!r} {block_key}: {stat} {value} -> '
                            f'{ability[stat]!r}')


def repair(data, rep):
    out = {}
    for tier_name, species in data.items():
        species = repair_key_drift(species, [tier_name], rep)
        species = repair_nesting(tier_name, species, rep)
        for name, body in species.items():
            if not isinstance(body, dict):
                continue
            start = next((v for k, v in body.items()
                          if START_RE.match(k) and isinstance(v, dict)), None)
            for bkey, bval in body.items():
                if not isinstance(bval, dict):
                    continue
                is_start, is_adv = START_RE.match(bkey), ADV_RE.match(bkey)
                if not (is_start or is_adv):
                    continue
                repair_field_bleed(tier_name, name, bkey, bval, rep)
                if is_start:
                    repair_mindless_int(tier_name, name, bkey, bval, rep)
                else:
                    repair_signs(tier_name, name, bkey, bval,
                                 size_step(start, bval), rep)
        out[tier_name] = species
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dry-run', action='store_true',
                    help='report what would change without writing the file')
    ap.add_argument('--verbose', '-v', action='store_true',
                    help='list every individual repair')
    args = ap.parse_args()

    with open(PATH, encoding='utf-8') as fh:
        data = json.load(fh)

    rep = Report()
    repaired = repair(data, rep)

    for defect in ('nesting', 'key drift', 'sign', 'field bleed', 'mindless int'):
        print(f'{defect:>14}: {rep.count(defect)}')
    print(f'{"TOTAL":>14}: {len(rep.repairs)}')

    if args.verbose:
        for defect, detail in rep.repairs:
            print(f'  [{defect}] {detail}')

    if rep.untouched:
        print(f'\nLeft alone ({len(rep.untouched)}) - reported, not repaired:')
        for detail in rep.untouched:
            print(f'  {detail}')

    species_count = sum(len(v) for v in repaired.values())
    print(f'\nreachable species: {species_count}')

    if not rep.repairs:
        print('\nnothing to repair - already clean.')
        return 0
    if args.dry_run:
        print('\n--dry-run: file not written.')
        return 0

    with open(PATH, 'w', encoding='utf-8') as fh:
        json.dump(repaired, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
    print(f'\nwrote {PATH}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
