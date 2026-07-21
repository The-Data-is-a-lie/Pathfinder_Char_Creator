"""Validate the CURATED spell-conditional files (exits 1 with a report on any error):

- Backend/json/spells/spell_riders.json   (Buckets B + C -- save + [[ ]] rider text)
- Backend/json/spells/spell_changes.json  (Bucket A -- weapon-buff conditionals)

Checks:
- No draft bookkeeping (`review`, `_*` keys) survives curation.
- spell_riders entries: `attack` in {null, melee, ranged}; `save` null or a well-formed block
  (type fortitude/reflex/will, harmless bool); `riders` a non-empty list of non-empty strings,
  every [[ ]] balanced and every bare number bracketed (house foundry-conditionals rule);
  no uncomputed caster-level scaling (a bare "[[N]] ... per caster level" must be
  "[[N*@spells.primary.cl.total]]"); an entry must carry a save and/or riders.
- spell_changes entries: {name, default, modifiers[]} or {changes[], contextNotes[]} (+ optional
  `rider` string), modifier/change shapes complete.
- No Path-of-War tokens (@INITMOD / @SKILLCHECK / @ATTACKCHECK) -- spells use @spells.primary.*.
- WARN (not fail) when a spell name has no entry in the module's every_spell.json (the module
  synthesizes / skips those, but a typo would silently orphan the entry).

Usage: python Backend/scripts/validate_spell_conditionals.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPELLS_DIR = os.path.join(HERE, '..', 'json', 'spells')
RIDERS_PATH = os.path.join(SPELLS_DIR, 'spell_riders.json')
CHANGES_PATH = os.path.join(SPELLS_DIR, 'spell_changes.json')
EVERY_SPELL = os.path.expandvars(
    r'%LOCALAPPDATA%\FoundryVTT\Data\modules\pf1e_random_char_generator'
    r'\templates\character_sheet_folder\every_spell.json')

SAVE_TYPES = {'fortitude', 'reflex', 'will'}
SAVE_KEYS = {'type', 'dc', 'description', 'harmless'}
MOD_KEYS = {'formula', 'target', 'subTarget', 'type', 'damageType', 'critical'}
CHANGE_KEYS = {'formula', 'target', 'type', 'operator', 'priority'}
POW_TOKENS = re.compile(r'@INITMOD|@SKILLCHECK|@ATTACKCHECK')

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def check_brackets(owner, text):
    if text.count('[[') != text.count(']]'):
        err(f'{owner}: unbalanced [[ ]] in {text!r}')


def check_numbers_bracketed(owner, text):
    """Every bare mechanical number outside a [[ ]] span must be bracketed (dice AND integers).
    Ordinals ("1st level", "11th", "7th") are English, not roll values -- match the FULL number token
    (so we don't backtrack to a leading digit) and skip it when an ordinal suffix follows."""
    stripped = re.sub(r'\[\[.*?\]\]', '', text)
    for m in re.finditer(r'(?<![\w])\d[\d.]*(?:d\d+)?', stripped):
        if re.match(r'(?:st|nd|rd|th)\b', stripped[m.end():]):
            continue
        err(f'{owner}: unbracketed number {m.group(0)!r} in {text!r}')
        return


# A bracketed *plain integer* ([[5]]) scaled by "per (caster) level" with no computed CL total is the
# "5 hit points per caster level" bug -- it must be [[5*@spells.primary.cl.total]]. A computed formula
# ([[5*@spells.primary.cl.total]]) is NOT a plain integer so it never matches. The {0,40} window stops
# at a bracket span, so an intervening [[..cl.total..]] can't hide the miss.
_CL_SCALE_RE = re.compile(r'\[\[\s*\d+\s*\]\][^\[\]]{0,40}?per\s+(?:caster\s+)?levels?', re.IGNORECASE)


def check_uncomputed_cl_scaling(owner, text):
    """Flag a bracketed constant scaled by 'per (caster) level' with no computed CL total. Whitelist an
    EXTERNAL actor's CL ('per caster level of the ...'); 'per inch of thickness' never matches this."""
    for m in _CL_SCALE_RE.finditer(text):
        if text[m.end():m.end() + 8].lower().startswith(' of the'):
            continue                                   # e.g. "per caster level of the dispel evil"
        frag = text[m.start():m.end()]
        err(f'{owner}: uncomputed caster-level scaling {frag!r} (use [[N*@spells.primary.cl.total]]) in {text!r}')


def check_no_draft_keys(owner, entry):
    bad = [k for k in entry if str(k).startswith('_') or k == 'review']
    if bad:
        err(f'{owner}: draft keys survived curation: {bad}')


def check_save(owner, save):
    if save is None:
        return
    if not isinstance(save, dict):
        err(f'{owner}: save is not an object')
        return
    unknown = set(save) - SAVE_KEYS
    if unknown:
        err(f'{owner}: unknown save keys {sorted(unknown)}')
    if str(save.get('type', '')).lower() not in SAVE_TYPES:
        err(f'{owner}: save type {save.get("type")!r} not in {sorted(SAVE_TYPES)}')
    if not isinstance(save.get('harmless', False), bool):
        err(f'{owner}: save harmless must be a bool')


def check_riders_file(riders):
    for name, entry in riders.items():
        owner = f'spell_riders[{name}]'
        if not isinstance(entry, dict):
            err(f'{owner}: not an object')
            continue
        check_no_draft_keys(owner, entry)
        unknown = set(entry) - {'attack', 'save', 'riders'}
        if unknown:
            err(f'{owner}: unknown keys {sorted(unknown)}')
        if entry.get('attack') not in (None, 'melee', 'ranged'):
            err(f'{owner}: attack must be null/melee/ranged, got {entry.get("attack")!r}')
        check_save(owner, entry.get('save'))
        rl = entry.get('riders')
        if rl is not None and not isinstance(rl, list):
            err(f'{owner}: riders must be a list')
            rl = []
        for r in (rl or []):
            if not r or not isinstance(r, str):
                err(f'{owner}: empty/non-string rider')
                continue
            check_brackets(owner, r)
            check_numbers_bracketed(owner, r)
            check_uncomputed_cl_scaling(owner, r)
            if POW_TOKENS.search(r):
                err(f'{owner}: PoW token in rider {r!r}')
        if not entry.get('save') and not (rl or []):
            err(f'{owner}: entry has neither save nor riders')


def check_modifier(owner, m):
    if not isinstance(m, dict):
        err(f'{owner}: modifier is not an object')
        return
    missing = MOD_KEYS - set(m)
    if missing:
        err(f'{owner}: modifier missing keys {sorted(missing)}')
    if m.get('target') not in ('attack', 'damage'):
        err(f'{owner}: modifier target {m.get("target")!r} must be attack/damage')
    if POW_TOKENS.search(str(m.get('formula', ''))):
        err(f'{owner}: PoW token in formula {m.get("formula")!r}')


def check_changes_file(changes):
    for name, entry in changes.items():
        owner = f'spell_changes[{name}]'
        if not isinstance(entry, dict):
            err(f'{owner}: not an object')
            continue
        check_no_draft_keys(owner, entry)
        if isinstance(entry.get('modifiers'), list):
            if not isinstance(entry.get('name'), str) or not entry['name']:
                err(f'{owner}: toggle shape needs a non-empty name')
            check_brackets(owner, entry.get('name', ''))
            for m in entry['modifiers']:
                check_modifier(owner, m)
        elif isinstance(entry.get('changes'), list):
            for ch in entry['changes']:
                missing = CHANGE_KEYS - set(ch)
                if missing:
                    err(f'{owner}: change missing keys {sorted(missing)}')
        else:
            err(f'{owner}: neither modifiers[] nor changes[] present')
        rider = entry.get('rider')
        if rider is not None:
            if not isinstance(rider, str) or not rider:
                err(f'{owner}: rider must be a non-empty string')
            else:
                check_brackets(owner, rider)
                if POW_TOKENS.search(rider):
                    err(f'{owner}: PoW token in rider {rider!r}')


def warn_missing_compendium(riders, changes):
    if not os.path.exists(EVERY_SPELL):
        warnings.append(f'every_spell.json not found at {EVERY_SPELL} -- compendium check skipped')
        return
    with open(EVERY_SPELL, encoding='utf-8') as fh:
        names = {str(i.get('name', '')).lower() for i in json.load(fh)}
    for name in list(riders) + list(changes):
        if name.lower() not in names:
            warnings.append(f'{name!r} not in every_spell.json (module will synthesize/skip)')


def main():
    with open(RIDERS_PATH, encoding='utf-8') as fh:
        riders = json.load(fh)
    with open(CHANGES_PATH, encoding='utf-8') as fh:
        changes = json.load(fh)
    check_riders_file(riders)
    check_changes_file(changes)
    warn_missing_compendium(riders, changes)
    for w in warnings:
        print(f'WARN: {w}')
    if errors:
        print(f'\n{len(errors)} error(s):')
        for e in errors:
            print(f'  {e}')
        sys.exit(1)
    print(f'OK: {len(riders)} rider spells + {len(changes)} buff spells validated '
          f'({len(warnings)} warning(s)).')


if __name__ == '__main__':
    main()
