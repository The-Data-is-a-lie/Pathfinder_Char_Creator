"""Build Backend/json/class_data/effects/class_feature_effects.json from the class-choice pools.

Walks every choice-based class-feature pool (rage powers, ki powers, discoveries, hexes,
rogue/ninja/slayer/investigator/vigilante talents, magus arcana, mercies, cruelties, arcanist
exploits, oracle revelations/curses, fighter trainings) in Backend/json/class_data/<class>.json
and drafts a mechanical-effects entry per power, reusing build_item_changes' sentence parser:
clean unconditional numeric bonuses -> pf1 `changes`; situational/scaling bonus text and
activated abilities -> `contextNotes` with [[ ]] inline rolls per the house style.

Every auto-drafted entry is flagged "review": true — the generator ships review-flagged
contextNotes but NEVER unvetted changes/conditionals. Hand-curated entries in
class_feature_effects_overrides.json are merged on top (full replacement per power, review
dropped). Curated entries may also carry:
  - "conditionals": default-off weapon toggles [{name, default, modifiers[]}] (feat pattern)
  - "tagBuff": a Multi-Buff-Distributor payload {onlyOthers, auraRange, changes, contextNotes}
    for powers that affect OTHER creatures (hexes on allies/enemies); caster-scaling formulas
    may reference @classes.<class>.level / @abilities.<ab>.mod — the generator bakes these to
    the NPC's numbers at export time since a recipient's sheet can't resolve them.

Monk ki powers are ki-cost stubs backed by spells ("barkskin": "(self only, 1 ki point)"), so
they are additionally joined case-insensitively against spells/spell_changes.json, with
@spells.primary.cl.total remapped to @classes.monk.level (qinggong CL = monk level).

Output keys are normalized power names: lowercased, "(su)/(ex)/(sp)" suffix stripped,
whitespace collapsed — main_test.py normalizes chosen names the same way at lookup.

Run:  python Backend/scripts/build_class_feature_changes.py [--report]
      --report prints per-section draft stats and unparsed bonus sentences instead of writing.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_item_changes as bic  # noqa: E402  (sentence parser + house [[ ]] style)

BACKEND = os.path.dirname(HERE)
CLASS_DATA = os.path.join(BACKEND, 'json', 'class_data')
SPELL_CHANGES = os.path.join(BACKEND, 'json', 'spells', 'spell_changes.json')
OUT_DIR = os.path.join(CLASS_DATA, 'effects')
OUT_PATH = os.path.join(OUT_DIR, 'class_feature_effects.json')
OVERRIDES_PATH = os.path.join(OUT_DIR, 'class_feature_effects_overrides.json')

# section (matches the dict_name the choosers store under character.data_dict['class features'])
#   -> list of (class json filename, path to the pool dict; '*' fans out over all values)
SECTIONS = {
    'rage_powers': [('barbarian.json', ['basic'])],          # skald shares the same pool
    'ki_powers': [('monk.json', ['ki_powers'])],             # level-keyed spell stubs
    'discoveries': [('alchemist.json', ['basic']),
                    ('alchemist.json', ['grand'])],
    'hexes': [('witch.json', ['basic']), ('witch.json', ['greater']),
              ('witch.json', ['grand']), ('shaman.json', ['hexes', 'basic'])],
    'rogue_talents': [('rogue.json', ['basic']), ('rogue.json', ['advanced'])],
    'ninja_talents': [('ninja.json', ['basic']), ('ninja.json', ['advanced'])],
    'slayer_talents': [('slayer.json', ['basic']), ('slayer.json', ['advanced'])],
    'investigator_talents': [('investigator.json', ['basic'])],
    'vigilante_talents': [('vigilante.json', ['basic'])],
    'social_talents': [('vigilante.json', ['social'])],
    'arcana': [('magus.json', ['basic'])],
    'mercy': [('paladin.json', ['mercy'])],                  # level-keyed
    'cruelty': [('antipaladin.json', ['cruelty'])],          # level-keyed
    'exploits': [('arcanist.json', ['basic']), ('arcanist.json', ['greater'])],
    'mysteries': [('oracle.json', ['mysteries', '*', 'revelations'])],
    'curses': [('oracle.json', ['curses'])],
    'armor_training': [('fighter.json', ['armor_train'])],
    'weapon_training': [('fighter.json', ['weapon_train'])],
}

# the class whose level scaling formulas in this section should reference
SECTION_CLASS = {
    'rage_powers': 'barbarian', 'ki_powers': 'monk', 'discoveries': 'alchemist',
    'hexes': 'witch', 'rogue_talents': 'rogue', 'ninja_talents': 'ninja',
    'slayer_talents': 'slayer', 'investigator_talents': 'investigator',
    'vigilante_talents': 'vigilante', 'social_talents': 'vigilante', 'arcana': 'magus',
    'mercy': 'paladin', 'cruelty': 'antipaladin', 'exploits': 'arcanist',
    'mysteries': 'oracle', 'curses': 'oracle',
    'armor_training': 'fighter', 'weapon_training': 'fighter',
}

# non-mechanics keys in dict-shaped pool entries
META_KEYS = {'benefit', 'benefits', 'description', 'prerequisites', 'prerequisite', 'source'}

SUFFIX_RE = re.compile(r'\s*\((su|ex|sp)\)\s*$', re.I)


def norm_name(name):
    """Canonical lookup key: lowercase, no (Su)/(Ex)/(Sp) suffix, collapsed whitespace."""
    return re.sub(r'\s+', ' ', SUFFIX_RE.sub('', str(name))).strip().lower()


def entry_text(value):
    """Flatten a pool entry (bare string / list / dict) into one benefit-prose string."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ' '.join(str(v) for v in value if isinstance(v, str))
    if isinstance(value, dict):
        # Case-insensitive: a few scraped pool entries capitalise the key ("Benefits" on four
        # investigator talents). Matching only lowercase dropped their text entirely — the first
        # branch missed the key, and the second excluded it because META_KEYS is checked lowercased.
        lower = {k.lower(): v for k, v in value.items()}
        parts = [lower[k] for k in ('benefit', 'benefits', 'description')
                 if isinstance(lower.get(k), str)]
        # leveled riders like "At 5th level": "..." carry mechanics too
        parts += [f'{k}: {v}' for k, v in value.items()
                  if k.lower() not in META_KEYS and isinstance(v, str)]
        return ' '.join(parts)
    return ''


def dig(node, path):
    """Yield the dict(s) at path inside node; '*' fans out over all values."""
    if not path:
        if isinstance(node, dict):
            yield node
        return
    head, rest = path[0], path[1:]
    if head == '*':
        for value in (node or {}).values():
            yield from dig(value, rest)
    elif isinstance(node, dict) and node.get(head) is not None:
        yield from dig(node[head], rest)


def iter_pool(pool):
    """Yield (name, prose) from a pool dict, descending level-keyed layers ("3": {...})."""
    if not isinstance(pool, dict):
        return
    keys = list(pool)
    if keys and all(re.fullmatch(r'\d+', k) for k in keys):
        for k in keys:
            yield from iter_pool(pool[k])
        return
    for name, value in pool.items():
        yield name, entry_text(value)


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def draft_entry(name, prose):
    """Auto-draft {changes, contextNotes[, unplaced], review} from benefit prose via the
    item parser. Class powers are overwhelmingly situational ("while raging", scaling by
    level), which the parser already routes to contextNotes."""
    parsed, unparsed, _flags = bic.parse_item(name, prose)
    entry = {'changes': parsed['changes'], 'contextNotes': parsed['contextNotes'],
             'review': True}
    if parsed.get('unplaced'):
        entry['unplaced'] = parsed['unplaced']
    return entry, unparsed


def ki_spell_join(name, spell_changes_ci):
    """A ki power whose name matches a buff spell inherits that spell's changes with
    CL remapped to monk level."""
    spell = spell_changes_ci.get(norm_name(name))
    if not spell:
        return None
    remap = lambda s: s.replace('@spells.primary.cl.total', '@classes.monk.level')
    return {
        'changes': [dict(c, formula=remap(str(c.get('formula', '')))) for c in
                    spell.get('changes', [])],
        'contextNotes': [dict(n, text=remap(str(n.get('text', '')))) for n in
                         spell.get('contextNotes', [])],
    }


def main():
    report = '--report' in sys.argv
    try:
        spell_changes_ci = {norm_name(k): v for k, v in load_json(SPELL_CHANGES).items()}
    except (OSError, ValueError):
        spell_changes_ci = {}

    result, stats, all_unparsed = {}, {}, []
    pool_names = {}  # section -> set of normalized power names in its source pool
    for section, sources in SECTIONS.items():
        entries = {}
        pool_names[section] = set()
        for filename, path in sources:
            filepath = os.path.join(CLASS_DATA, filename)
            if not os.path.exists(filepath):
                print(f'WARNING: {filename} missing, section {section} incomplete')
                continue
            data = load_json(filepath)
            for pool in dig(data, path):
                for name, prose in iter_pool(pool):
                    key = norm_name(name)
                    if not key:
                        continue
                    pool_names[section].add(key)
                    if key in entries:
                        continue
                    if section == 'ki_powers':
                        joined = ki_spell_join(name, spell_changes_ci)
                        if joined:
                            note = bic.wrap_rolls(bic.clean_sentence(
                                f'{name} ki power {prose}'.strip()))
                            joined['contextNotes'].append({'text': note, 'target': 'skills'})
                            joined['review'] = True
                            entries[key] = joined
                            continue
                    entry, unparsed = draft_entry(name, prose)
                    if entry['changes'] or entry['contextNotes'] or entry.get('unplaced'):
                        entries[key] = entry
                    all_unparsed += [f'{section}/{name}: {s}' for s in unparsed]
        result[section] = entries
        stats[section] = (len(entries),
                          sum(1 for e in entries.values() if e.get('changes')),
                          sum(len(e.get('contextNotes', [])) for e in entries.values()))

    # ninja/slayer talents reuse the rogue pool — one curated entry covers all three
    SHARED_OVERRIDES = {'ninja_talents': 'rogue_talents', 'slayer_talents': 'rogue_talents'}
    overridden = 0
    if os.path.exists(OVERRIDES_PATH):
        overrides = load_json(OVERRIDES_PATH)
        for section, powers in overrides.items():
            if section.startswith('_'):
                continue
            if section not in result:
                print(f'WARNING: overrides section {section!r} is not a known section')
                result.setdefault(section, {})
            for name, entry in powers.items():
                result[section][norm_name(name)] = entry  # full replacement, no review flag
                overridden += 1
        for target, source in SHARED_OVERRIDES.items():
            for name, entry in (overrides.get(source) or {}).items():
                key = norm_name(name)
                if key in pool_names.get(target, ()) and \
                        key not in {norm_name(n) for n in overrides.get(target, ())}:
                    result[target][key] = entry
                    overridden += 1

    for section, (n, with_changes, notes) in sorted(stats.items()):
        print(f'{section:22s} {n:4d} drafted | {with_changes:3d} with changes | {notes:4d} notes')
    print(f'{overridden} curated overrides merged, {len(all_unparsed)} unparsed bonus sentences')
    if report:
        for line in all_unparsed:
            print(' ?', line[:220])
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    result['_readme'] = (
        'GENERATED by scripts/build_class_feature_changes.py — edit '
        'class_feature_effects_overrides.json and re-run, never this file. Sections match '
        "the dict_name keys in the character's class_features export; power keys are "
        'normalized (lowercase, no (Su)/(Ex)/(Sp)). "review": true = auto-draft, the '
        'generator ships its contextNotes only.')
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
    total = sum(len(v) for k, v in result.items() if not k.startswith('_'))
    print(f'wrote {OUT_PATH} ({total} powers)')


if __name__ == '__main__':
    main()
