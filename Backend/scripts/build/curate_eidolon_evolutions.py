"""Turn `eidolon_evolutions.draft.json` into the curated `eidolon_evolutions.json`.

Spec section 8, "Eidolon (v1.1)". The draft is a scrape: names, costs, prose, and regex
*hints*. The spend loop cannot run on hints -- a misread prerequisite silently produces an
illegal eidolon -- so every legality field the loop reads is settled here, in a table a
reviewer can diff, and the gate (`validate_eidolon_data.py`) then checks the result.

Re-runnable: rescrape, re-run this, and the curated file is rebuilt. What the scraper got
right is inherited automatically; `CURATION` holds only corrections and additions.

WHAT IS AUTHORED HERE, AND WHY IT COULD NOT BE SCRAPED

  * **Attack counts.** Only `rake` says "counts as one natural attack toward the eidolon's
    maximum". Every other attack evolution just calls its attack primary or secondary, and
    the count is in the sentence ("giving it TWO claw attacks"). Max Attacks is a hard cap,
    so each number is set by hand.
  * **Multi-form restrictions.** The prose regex reads one form; `mount` (quadruped and
    serpentine) and `trample` (biped or quadruped) name two. Aquatic's own base-form text
    adds itself to `mount`, which no evolution-side reader could see.
  * **The fold.** `changes` speaks companion_stats' pf1 target vocabulary so
    `apply_modifiers` folds evolutions exactly as it folds companion feats (D14). Ability
    scores and size are NOT changes: they are inputs the stat block is computed FROM, so
    they ride `ability_scores` / `grants_size` and are applied before the block is built.
    That split is what keeps `large` from being counted twice (D11's lesson).
  * **Holdbacks.** A numeric effect this stat block cannot express (energy resistance, DR,
    SR, fast healing, a damage-die step, a fly speed) carries `numeric_holdback` text and is
    REPORTED on `stats.unapplied` -- never silently dropped, never half-applied.

EXCLUSIONS are recorded with a reason rather than deleted, so the census stays honest:
the two `[3PP]` entries are not Paizo content and this generator treats third-party
systems as opt-in.

Usage:
    .venv/Scripts/python.exe Backend/scripts/build/curate_eidolon_evolutions.py [--dry-run]
"""
import argparse
import json
import os
import re
import sys

# The damage and primary/secondary lines, PARSED rather than hand-authored. Every one of the eleven
# attack-granting evolutions states both in the same shape -- "The claws deal 1d4 points of damage
# (1d6 if Large, 1d8 if Huge)" and "This attack is a primary attack" -- so hand-typing 33 dice would
# be transcribing what the source already says uniformly, and would go stale on a re-scrape. The
# gate checks the result, which is where a wording change surfaces.
DAMAGE_RE = re.compile(r'deals?\s+(\d+d\d+)\s+points? of damage\s*'
                       r'\(\s*(\d+d\d+)\s+if Large\s*,\s*(\d+d\d+)\s+if Huge\s*\)', re.IGNORECASE)
ATTACK_KIND_RE = re.compile(r'(?:is|are)\s+(?:an?\s+)?(primary|secondary)\s+(?:natural\s+)?attacks?',
                            re.IGNORECASE)


def parse_attack(entry, count):
    """`{count, kind, damage}` for an attack-granting evolution, read out of its own prose.

    Small is deliberately NOT computed. The published table gives Medium, Large and Huge; stepping
    a die down for a Small eidolon is the same die-ladder question spec section 16 (D11) just ruled
    on for oversized weapons -- the backend emits a marker and lets the ladder's owner scale it. The
    Small package carries `damage_steps_down: 1` for exactly that.
    """
    benefit = entry.get('benefit') or ''
    damage = DAMAGE_RE.search(benefit)
    kind = ATTACK_KIND_RE.search(benefit)
    if not damage or not kind:
        return None
    return {
        'count': count,
        'kind': kind.group(1).lower(),
        'damage': {'medium': damage.group(1).lower(), 'large': damage.group(2).lower(),
                   'huge': damage.group(3).lower()},
    }

JSON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'json')
DRAFT = os.path.join(JSON_DIR, 'eidolon_evolutions.draft.json')
OUT = os.path.join(JSON_DIR, 'eidolon_evolutions.json')

ENERGY = ['acid', 'cold', 'electricity', 'fire', 'sonic']
ABILITIES = ['str', 'dex', 'con', 'int', 'wis', 'cha']


def nac(amount, note=None):
    """A natural-armour change in companion_stats' change shape."""
    return [{'formula': amount, 'target': 'nac', 'type': 'natural',
             'operator': 'add', 'priority': 0}]


# Corrections and additions to the scrape, keyed by the draft's own key.
#
#   grants_attack     natural attacks added, counted against the table's Max Attacks column
#   forms             base forms this is legal for (replaces the scraper's single-form read)
#   alignment         required alignment component
#   repeat            {'max_formula': expr|None}; None means "unlimited" (EP is the real cap)
#   choice            a pick the spender makes with the creature's own RNG
#   ability_scores    pre-block ability deltas
#   grants_size       pre-block size change
#   changes           post-block fold, apply_modifiers vocabulary
#   numeric_holdback  a real number this block cannot express -> stats.unapplied
#   exclude           kept in the file, kept out of the pool, with the reason
CURATION = {
    # -- attack-granting evolutions. The count is the number of natural attacks gained.
    'bite': {'grants_attack': 1},
    'claws': {'grants_attack': 2, 'requires': ['limbs']},
    'gore': {'grants_attack': 1},
    'hooves': {'grants_attack': 2, 'requires': ['limbs']},
    'pincers': {'grants_attack': 2, 'requires': ['limbs (arms)']},
    'slam': {'grants_attack': 1, 'requires': ['limbs (arms)']},
    'sting': {'grants_attack': 1, 'requires': ['tail']},
    'tail slap': {'grants_attack': 1, 'requires': ['tail']},
    'tentacle': {'grants_attack': 1},
    'wing buffet': {'grants_attack': 2, 'requires': ['flight']},
    # Rake grants two rake attacks but its own text counts them as ONE against the maximum.
    'rake': {'grants_attack': 1},
    # Head adds no attack itself; it is the prerequisite body part other attacks hang off.
    'head': {'grants_attack': 0},

    # -- restrictions the single-form regex could not read
    'mount': {'forms': ['quadruped', 'serpentine', 'aquatic'],
              'note': ('The aquatic base form grants itself this evolution in its own text, '
                       'which no evolution-side reader could see.')},
    'trample': {'forms': ['biped', 'quadruped']},
    'celestial appearance': {'alignment': 'good'},

    # -- the fold: numbers this stat block can express
    'improved natural armor': {'changes': nac(2)},
    'large': {'grants_size': 'large',
              'ability_scores': {'str': 8, 'con': 4, 'dex': -2},
              'changes': nac(2),
              'note': ('The AC/attack/CMB/CMD/Stealth geometry is NOT here: '
                       'companion_stats.SIZE_GEOMETRY owns it, keyed off the final size, so '
                       'the two can never both apply (D11).')},
    'ability increase': {'choice': {'kind': 'ability', 'options': ABILITIES, 'amount': 2},
                         'note': 'Applied to the pre-block ability scores, not as a change.'},
    'skilled': {'choice': {'kind': 'skill', 'amount': 8, 'bonus_type': 'racial'}},
    'tail': {'changes': [{'formula': 2, 'target': 'skill.acr', 'type': 'racial',
                          'operator': 'add', 'priority': 0}]},

    # -- choices with no foldable number
    'resistance': {'choice': {'kind': 'energy', 'options': ENERGY},
                   'numeric_holdback': ('resist 5 against the chosen energy type, rising by 5 '
                                        'at higher levels: the stat block has no resistance '
                                        'field')},
    'immunity': {'choice': {'kind': 'energy', 'options': ENERGY},
                 'numeric_holdback': 'immunity to the chosen energy type'},
    'limbs': {'choice': {'kind': 'limbs', 'options': ['arms', 'legs']},
              'numeric_holdback': 'a pair of legs adds 10 ft. to base speed'},
    'grab': {'requires_any_attack': True},

    # -- prerequisites the scrape's regex never saw, because they are stated in the TAIL of the
    # prose rather than in a heading. Found 2026-08-17 by sweeping every "must possess the X
    # evolution" sentence against the curated prereqs: the whole spell-like-ability chain and both
    # undead gates were unenforced, so a greedy spender could buy Ultimate Magic (4 EP) on an
    # eidolon that had never bought a cantrip. `min_ability` is the other half of the same
    # sentences -- these five are the only evolutions with an ability-score gate.
    'minor magic': {'requires': ['basic magic'], 'min_ability': {'cha': 11}},
    'major magic': {'requires': ['minor magic'], 'min_ability': {'cha': 12}},
    'ultimate magic': {'requires': ['major magic'], 'min_ability': {'cha': 13}},
    'lifesense': {'requires': ['undead appearance']},
    'channel resistance': {'requires': ['undead appearance'],
                           'numeric_holdback': '+2 against channelled energy'},

    # -- real numbers this block cannot express (D12 holdback discipline)
    'damage reduction': {'numeric_holdback': 'DR 5/opposite alignment, rising with level'},
    'spell resistance': {'numeric_holdback': 'SR equal to 11 + the summoner\'s level'},
    'fast healing': {'numeric_holdback': 'fast healing 1, +1 per 2 further evolution points'},
    'improved damage': {'numeric_holdback': ('one natural attack\'s damage die increases by '
                                             'one step -- a die step is not a modifier')},
    'reach': {'numeric_holdback': ('+5 ft. reach on one attack; reach is deliberately absent '
                                   'from this stat block (D12)')},
    'flight': {'numeric_holdback': 'a fly speed equal to base speed'},
    'climb': {'numeric_holdback': 'a climb speed equal to base speed'},
    'swim': {'numeric_holdback': 'a swim speed equal to base speed'},
    'burrow': {'numeric_holdback': 'a burrow speed of half base speed'},

    # -- kept, but out of the random pool
    'spirit-touched': {'exclude': 'third-party (3PP); this generator opts in to 3pp by flag'},
    'absorb occult energy': {'exclude': 'third-party (3PP); this generator opts in to 3pp by flag'},
}


def resolve_repeat(key, auto, curated):
    """`repeat.max_formula` is an expression in `level` (the summoner's), or None = unlimited.

    RAW spells its caps two ways: "once for every five levels" (improved natural armor) is a
    total cap, while ability increase caps PER ability score and adds one more per six levels.
    """
    if 'repeat' in curated:
        return curated['repeat']
    cap = auto.get('repeat_cap') or {}
    if 'per_summoner_levels' in cap:
        return {'max_formula': f"1 + level // {cap['per_summoner_levels']}"}
    if cap.get('repeatable'):
        per = cap.get('plus_one_per_summoner_levels')
        if per:
            return {'max_formula': None, 'per_choice_max_formula': f'1 + level // {per}'}
        return {'max_formula': None}
    return {'max_formula': '1'}


def build(draft):
    out = {}
    for key, entry in draft.items():
        auto = entry.get('auto') or {}
        curated = CURATION.get(key, {})

        forms = curated.get('forms')
        if forms is None and auto.get('form_restriction'):
            forms = [auto['form_restriction']]

        requires = curated.get('requires')
        if requires is None:
            requires = auto.get('requires_evolutions') or []

        prereqs = {
            'min_summoner_level': curated.get('min_summoner_level')
                                  or auto.get('min_summoner_level'),
            'evolutions': sorted(requires),
            'forms': sorted(forms) if forms else None,
            'size': curated.get('size') or auto.get('requires_size'),
            'alignment': curated.get('alignment'),
            'any_attack': bool(curated.get('requires_any_attack')),
            # {'cha': 11} -- the eidolon's OWN score, after the ability increases it has bought.
            'min_ability': curated.get('min_ability'),
        }

        record = {
            'name': entry['name'],
            'cost': entry['cost'],
            'benefit': entry['benefit'],
            'prereqs': prereqs,
            'repeat': resolve_repeat(key, auto, curated),
            'grants_attack': curated.get('grants_attack', 0),
        }
        if record['grants_attack']:
            attack = parse_attack(entry, record['grants_attack'])
            if attack:
                record['attack'] = attack
        for field in ('type', 'source'):
            if entry.get(field):
                record[field] = entry[field]
        for field in ('choice', 'ability_scores', 'grants_size', 'changes',
                      'numeric_holdback', 'note', 'exclude'):
            if curated.get(field) is not None:
                record[field] = curated[field]
        if entry.get('third_party'):
            record['third_party'] = True
            record.setdefault('exclude', 'third-party (3PP)')
        out[key] = record
    return dict(sorted(out.items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    with open(DRAFT, encoding='utf-8') as fh:
        draft = json.load(fh)

    unknown = sorted(set(CURATION) - set(draft['evolutions']))
    if unknown:
        raise SystemExit(f'CURATION names no longer in the draft: {unknown}')

    evolutions = build(draft['evolutions'])
    pool = {k: v for k, v in evolutions.items() if not v.get('exclude')}
    attackers = {k: v['grants_attack'] for k, v in pool.items() if v['grants_attack']}
    folded = [k for k, v in pool.items()
              if v.get('changes') or v.get('ability_scores') or v.get('choice')]
    holdbacks = [k for k, v in pool.items() if v.get('numeric_holdback')]

    print(f'  {len(evolutions)} evolutions, {len(pool)} in the pool '
          f'({len(evolutions) - len(pool)} excluded)')
    print(f'  attack-granting: {len(attackers)} '
          f'({sum(attackers.values())} attacks if every one were bought)')
    print(f'  folded: {len(folded)} | numeric holdbacks: {len(holdbacks)}')

    payload = {
        'meta': {
            'source': draft['meta']['source'],
            'built_by': 'Backend/scripts/build/curate_eidolon_evolutions.py',
            'note': ('Curated from eidolon_evolutions.draft.json. `changes` uses '
                     'companion_stats.apply_modifiers vocabulary; `ability_scores` and '
                     '`grants_size` are pre-block inputs, not changes. An entry with '
                     '`exclude` stays in the file and out of the random pool.'),
        },
        'evolutions': evolutions,
    }
    if args.dry_run:
        print(json.dumps(payload['evolutions']['large'], indent=2))
        print(json.dumps(payload['evolutions']['bite'], indent=2))
        return 0
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
    print(f'  wrote {os.path.relpath(OUT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
