"""Validate Backend/json/class_data/effects/class_feature_effects.json (+ its overrides file)
against the class-choice pools.

Checks (all must pass; exits 1 with a report otherwise):
- JSON parses; only known sections; every power key resolves to a name in that section's
  source pool (no dead keys), and every overrides key does too (catches typos).
- Entry keys whitelisted; changes/contextNotes/tagBuff-changes use valid pf1 change and
  context-note targets (reusing validate_quality_effects' whitelists).
- conditionals follow the weapon-toggle rules (plain modifier formulas — no [[ ]]/[label] —
  valid targets/subTargets); unlike weapon qualities, an EMPTY modifiers list is allowed
  (name-only riders, PoW style).
- tagBuff payloads: onlyOthers bool, auraRange int/str/null, nested changes/notes valid.
- [[ ]] inline-roll brackets balanced and unnested in every name/text.

Usage: python Backend/scripts/validate_class_feature_effects.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import validate_quality_effects as vqe  # noqa: E402  (shared whitelists + checkers)
import build_class_feature_changes as bcfc  # noqa: E402  (SECTIONS, pool walker, norm_name)

EFFECTS_PATH = bcfc.OUT_PATH
OVERRIDES_PATH = bcfc.OVERRIDES_PATH

# 'tier' is carried per-conditional (see validate_quality_effects.COND_KEYS); allowed at entry level
# too so a whole power can be marked without repeating it on each of its conditionals.
ENTRY_KEYS = {'changes', 'contextNotes', 'conditionals', 'tagBuff', 'unplaced', 'review', 'tier'}
TAGBUFF_KEYS = {'onlyOthers', 'auraRange', 'changes', 'contextNotes'}

err = vqe.err


def check_changes(owner, changes):
    if not isinstance(changes, list):
        err(f'{owner}: "changes" must be a list')
        return
    for ch in changes:
        unknown = set(ch) - vqe.CHANGE_KEYS
        if unknown:
            err(f'{owner}: unknown change keys {sorted(unknown)}')
        if not isinstance(ch.get('formula'), str) or not ch.get('formula'):
            err(f'{owner}: change missing formula')
        if not vqe.valid_target(ch.get('target'), vqe.PF1_CHANGE_TARGETS):
            err(f'{owner}: invalid change target {ch.get("target")!r}')
        if ch.get('operator') not in ('add', 'set'):
            err(f'{owner}: bad change operator {ch.get("operator")!r}')
        if not isinstance(ch.get('type'), str) or not ch.get('type'):
            err(f'{owner}: change bonus type must be a non-empty string')


def check_notes(owner, notes):
    if not isinstance(notes, list):
        err(f'{owner}: "contextNotes" must be a list')
        return
    for note in notes:
        unknown = set(note) - {'text', 'target'}
        if unknown:
            err(f'{owner}: unknown contextNote keys {sorted(unknown)}')
        text = note.get('text')
        if not text or not isinstance(text, str):
            err(f'{owner}: contextNote missing text')
        else:
            vqe.check_brackets(owner, text)
        if not vqe.valid_target(note.get('target'), vqe.PF1_NOTE_TARGETS):
            err(f'{owner}: invalid contextNote target {note.get("target")!r}')


def check_entry(owner, entry, curated):
    if not isinstance(entry, dict):
        err(f'{owner}: entry must be a dict')
        return
    unknown = set(entry) - ENTRY_KEYS
    if unknown:
        err(f'{owner}: unknown entry keys {sorted(unknown)}')
    check_changes(owner, entry.get('changes', []))
    check_notes(owner, entry.get('contextNotes', []))
    for cond in entry.get('conditionals', []) or []:
        vqe.check_conditional(owner, cond)
    tag = entry.get('tagBuff')
    if tag is not None:
        if not isinstance(tag, dict):
            err(f'{owner}: tagBuff must be a dict')
        else:
            unknown = set(tag) - TAGBUFF_KEYS
            if unknown:
                err(f'{owner}: unknown tagBuff keys {sorted(unknown)}')
            if not isinstance(tag.get('onlyOthers'), bool):
                err(f'{owner}: tagBuff.onlyOthers must be a bool')
            if not isinstance(tag.get('auraRange'), (int, str, type(None))):
                err(f'{owner}: tagBuff.auraRange must be int, formula string, or null')
            check_changes(f'{owner}.tagBuff', tag.get('changes', []))
            check_notes(f'{owner}.tagBuff', tag.get('contextNotes', []))
            if not tag.get('changes') and not tag.get('contextNotes'):
                err(f'{owner}: tagBuff has no changes and no contextNotes')
    if curated and not any(entry.get(k) for k in
                           ('changes', 'contextNotes', 'conditionals', 'tagBuff')):
        err(f'{owner}: curated entry has no effects at all')


def pool_name_sets():
    """{section -> set of normalized power names} rebuilt from the source pools."""
    pools = {}
    for section, sources in bcfc.SECTIONS.items():
        names = set()
        for filename, path in sources:
            filepath = os.path.join(bcfc.CLASS_DATA, filename)
            if not os.path.exists(filepath):
                err(f'{section}: source file {filename} missing')
                continue
            data = bcfc.load_json(filepath)
            for pool in bcfc.dig(data, path):
                for name, _prose in bcfc.iter_pool(pool):
                    key = bcfc.norm_name(name)
                    if key:
                        names.add(key)
        pools[section] = names
    return pools


def main():
    with open(EFFECTS_PATH, encoding='utf-8') as f:
        effects = json.load(f)
    try:
        with open(OVERRIDES_PATH, encoding='utf-8') as f:
            overrides = json.load(f)
    except OSError:
        overrides = {}

    pools = pool_name_sets()
    curated_keys = {section: {bcfc.norm_name(n) for n in powers}
                    for section, powers in overrides.items() if not section.startswith('_')}
    # rogue-pool overrides propagate into the ninja/slayer sections at build time
    for target, source in (('ninja_talents', 'rogue_talents'),
                           ('slayer_talents', 'rogue_talents')):
        curated_keys.setdefault(target, set()).update(curated_keys.get(source, set()))

    unknown_sections = set(effects) - set(bcfc.SECTIONS) - {'_readme'}
    if unknown_sections:
        err(f'unknown top-level sections {sorted(unknown_sections)}')
    for section, powers in overrides.items():
        if section.startswith('_'):
            continue
        if section not in bcfc.SECTIONS:
            err(f'overrides: unknown section {section!r}')
            continue
        for name in powers:
            if bcfc.norm_name(name) not in pools[section]:
                err(f'overrides.{section}: {name!r} not found in the source pool')

    n_entries = n_curated = 0
    for section, powers in effects.items():
        if section.startswith('_'):
            continue
        pool = pools.get(section, set())
        for name, entry in powers.items():
            owner = f'{section}.{name}'
            if name not in pool:
                err(f'{owner}: dead key (not in the source pool)')
            curated = name in curated_keys.get(section, set())
            check_entry(owner, entry, curated)
            n_entries += 1
            n_curated += curated
            if curated and entry.get('review'):
                err(f'{owner}: curated entry still carries a review flag')

    if vqe.errors:
        for e in vqe.errors:
            print(e)
        print(f'\nFAILED: {len(vqe.errors)} problem(s)')
        sys.exit(1)
    print(f'OK: {n_entries} entries across {sum(1 for s in effects if not s.startswith("_"))} '
          f'sections ({n_curated} curated); all keys resolve to pool names, all targets valid.')


if __name__ == '__main__':
    main()
