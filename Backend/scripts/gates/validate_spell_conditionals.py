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

Usage: python Backend/scripts/gates/validate_spell_conditionals.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _harness import Report, JSON_DIR, read_json  # noqa: E402
from damage_types import classify_damage_type  # noqa: E402  the one owner of the type vocabulary

SPELLS_DIR = os.path.join(JSON_DIR, 'spells')
RIDERS_PATH = os.path.join(SPELLS_DIR, 'spell_riders.json')
CHANGES_PATH = os.path.join(SPELLS_DIR, 'spell_changes.json')
EVERY_SPELL = os.path.expandvars(
    r'%LOCALAPPDATA%\FoundryVTT\Data\modules\pf1e_random_char_generator'
    r'\templates\character_sheet_folder\every_spell.json')

SAVE_TYPES = {'fortitude', 'reflex', 'will'}
SAVE_KEYS = {'type', 'dc', 'description', 'harmless'}
MOD_KEYS = {'formula', 'target', 'subTarget', 'type', 'damageType', 'critical'}
# Mirrors validate_quality_effects.MOD_CRITICAL -- pf1's action-model enum is
# {NORMAL:"normal", CRITICAL:"crit", NON_CRITICAL:"nonCrit"}. Kept as a literal rather than an
# import so each validator runs standalone; if pf1 ever adds a value, update both.
MOD_CRITICAL = {'normal', 'crit', 'nonCrit'}
CHANGE_KEYS = {'formula', 'target', 'type', 'operator', 'priority'}
POW_TOKENS = re.compile(r'@INITMOD|@SKILLCHECK|@ATTACKCHECK')

errors = []
warnings = []
REPORT = Report('validate_spell_conditionals', errors=errors, warnings=warnings)


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
    # pf1's action-model enum is exactly {normal, crit, nonCrit}. An unknown value (the historical
    # "onCrit") is DELETED by pf1 on the next sheet edit, silently dropping the modifier -- that bug
    # shipped once on six burst qualities. validate_quality_effects.py guards the weapon-quality
    # data the same way; this is the spell-side copy of that guard.
    if 'critical' in m and m.get('critical') not in MOD_CRITICAL:
        err(f'{owner}: modifier critical {m.get("critical")!r} must be one of {sorted(MOD_CRITICAL)}')
    if POW_TOKENS.search(str(m.get('formula', ''))):
        err(f'{owner}: PoW token in formula {m.get("formula")!r}')
    # WARN (not fail): a dice DAMAGE modifier with an empty damageType renders "undefined" on the
    # sheet. The consumers coerce it to ["untyped"] at attach time, but a real element is preferable.
    dt = m.get('damageType')
    # Members must be real pf1 ids: a prose alias ("electricity") is an error with a fix, an
    # unrecognised value only a warning -- see damage_types.py for why that asymmetry.
    if isinstance(dt, list):
        for t in dt:
            state, suggestion = classify_damage_type(t)
            if state == 'alias':
                err(f'{owner}: damageType {t!r} is rules prose, not a pf1 id -- use {suggestion!r}')
            elif state == 'unknown':
                warnings.append(f'{owner}: damageType {t!r} is not a known pf1 id '
                                f'(add it to damage_types.py if it is legitimate)')
    if (m.get('target') == 'damage' and re.search(r'[\d)]d\d', str(m.get('formula', '')))
            and not (isinstance(dt, list) and dt)):
        warnings.append(f'{owner}: dice damage modifier has empty damageType '
                        f'(coerced to untyped; prefer a real element) -- formula {m.get("formula")!r}')


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
    names = {str(i.get('name', '')).lower() for i in read_json(EVERY_SPELL)}
    for name in list(riders) + list(changes):
        if name.lower() not in names:
            warnings.append(f'{name!r} not in every_spell.json (module will synthesize/skip)')


def main():
    riders = read_json(RIDERS_PATH)
    changes = read_json(CHANGES_PATH)
    check_riders_file(riders)
    check_changes_file(changes)
    warn_missing_compendium(riders, changes)
    return REPORT.finish(f'{len(riders)} rider spells + {len(changes)} buff spells validated')


if __name__ == '__main__':
    sys.exit(main())
