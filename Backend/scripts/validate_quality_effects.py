"""Validate Backend/json/items/quality_effects.json against the scraped quality lists.

Checks (all must pass; exits 1 with a report otherwise):
- JSON parses; only known sections/keys.
- Coverage: every quality name in weapon_qualities.json (Melee+Ranged) has a weapon entry,
  every name in armor_qualities.json (Armor+Shield) has an armor entry — and no dead keys.
- Weapon entries: conditionals[] with name/default/modifiers; modifier fields whitelisted
  (plain formulas — the Foundry module appends the [Source] label, so hand-baked [labels]
  are an error).
- Armor entries: changes[]/contextNotes[] with valid pf1 change / context-note targets.
- [[ ]] inline-roll brackets balanced in every name/text.

Usage: python Backend/scripts/validate_quality_effects.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(HERE, '..', 'json')
QE_PATH = os.path.join(JSON_DIR, 'items', 'quality_effects.json')
WEAPON_QUALITIES = os.path.join(JSON_DIR, 'weapon_qualities.json')
ARMOR_QUALITIES = os.path.join(JSON_DIR, 'armor_qualities.json')

SKILL_IDS = {
    'acr', 'apr', 'art', 'blf', 'clm', 'crf', 'dip', 'dev', 'dis', 'esc', 'fly',
    'han', 'hea', 'int', 'lin', 'lor', 'per', 'prf', 'pro', 'rid', 'sen', 'slt',
    'spl', 'ste', 'sur', 'swm', 'umd', 'kar', 'kdu', 'ken', 'kge', 'khi', 'klo',
    'kna', 'kno', 'kpl', 'kre',
}

# mirrors build_item_changes.PF1_NOTE_TARGETS (pf1 contextNoteTargets) + skill.<id>
PF1_NOTE_TARGETS = {
    'attack', 'critical', 'effect', 'melee', 'meleeWeapon', 'meleeSpell',
    'ranged', 'rangedWeapon', 'rangedSpell', 'cmb',
    'allSavingThrows', 'fort', 'ref', 'will',
    'skills', 'strSkills', 'dexSkills', 'conSkills', 'intSkills', 'wisSkills', 'chaSkills',
    'allChecks', 'strChecks', 'dexChecks', 'conChecks', 'intChecks', 'wisChecks', 'chaChecks',
    'spellEffect', 'concentration', 'cl', 'ac', 'cmd', 'sr', 'init',
    'landSpeed', 'climbSpeed', 'swimSpeed', 'burrowSpeed', 'flySpeed', 'allSpeeds',
}

# pf1 buff/change targets this data set is allowed to write (subset of pf1 buffTargets)
PF1_CHANGE_TARGETS = {
    'str', 'dex', 'con', 'int', 'wis', 'cha',
    'ac', 'aac', 'sac', 'nac', 'ffac', 'tac',
    'attack', 'mattack', 'rattack', 'damage', 'wdamage', 'sdamage',
    'allSavingThrows', 'fort', 'ref', 'will',
    'cmb', 'cmd', 'init', 'mhp', 'spellResist',
    'landSpeed', 'climbSpeed', 'swimSpeed', 'burrowSpeed', 'flySpeed', 'allSpeeds',
    'skills',
}

MOD_TARGETS = {'damage', 'attack'}
MOD_SUBTARGETS = {'allDamage', 'allAttack', 'attack_0'}
MOD_CRITICAL = {'normal', 'nonCrit', 'onCrit'}
MOD_KEYS = {'formula', 'target', 'subTarget', 'type', 'damageType', 'critical'}
# `tier`: "A" = apply by default; "B" = authored but filed under the applier's "(NOT RECOMMENDED)"
# section, offered unchecked, and filtered out of the generator's feat toggles. Absent means A, so
# every entry authored before the tier sweep stays valid and recommended.
COND_KEYS = {'name', 'default', 'modifiers', 'tier'}
COND_TIERS = {'A', 'B'}
WEAPON_ENTRY_KEYS = {'conditionals'}
ARMOR_ENTRY_KEYS = {'changes', 'contextNotes'}
CHANGE_KEYS = {'formula', 'target', 'type', 'operator', 'priority'}

errors = []


def err(msg):
    errors.append(msg)


def valid_target(target, valid_set):
    return target in valid_set or (
        isinstance(target, str) and target.startswith('skill.') and target[6:] in SKILL_IDS)


def check_brackets(owner, text):
    if text.count('[[') != text.count(']]'):
        err(f'{owner}: unbalanced [[ ]] in {text!r}')
    if re.search(r'\[\[[^\]]*\[\[', text):
        err(f'{owner}: nested [[ in {text!r}')


def check_conditional(owner, cond):
    unknown = set(cond) - COND_KEYS
    if unknown:
        err(f'{owner}: unknown conditional keys {sorted(unknown)}')
    name = cond.get('name')
    if not name or not isinstance(name, str):
        err(f'{owner}: conditional missing name')
    else:
        check_brackets(owner, name)
    if not isinstance(cond.get('default'), bool):
        err(f'{owner}: conditional "default" must be a bool')
    if 'tier' in cond and cond['tier'] not in COND_TIERS:
        err(f'{owner}: conditional "tier" must be one of {sorted(COND_TIERS)}, got {cond["tier"]!r}')
    mods = cond.get('modifiers')
    if not isinstance(mods, list):
        err(f'{owner}: conditional "modifiers" must be a list')
        return
    for mod in mods:
        unknown = set(mod) - MOD_KEYS
        if unknown:
            err(f'{owner}: unknown modifier keys {sorted(unknown)}')
        formula = mod.get('formula')
        if not formula or not isinstance(formula, str):
            err(f'{owner}: modifier missing formula')
        elif re.search(r'\[', formula):
            err(f'{owner}: modifier formula {formula!r} must be plain '
                '(no [label]/[[ ]] — the module appends the [Source] label)')
        if mod.get('target') not in MOD_TARGETS:
            err(f'{owner}: bad modifier target {mod.get("target")!r}')
        if mod.get('subTarget') not in MOD_SUBTARGETS:
            err(f'{owner}: bad modifier subTarget {mod.get("subTarget")!r}')
        if mod.get('critical') not in MOD_CRITICAL:
            err(f'{owner}: bad modifier critical {mod.get("critical")!r}')
        if not isinstance(mod.get('damageType'), list):
            err(f'{owner}: modifier damageType must be a list')
        if not isinstance(mod.get('type'), str) or not mod.get('type'):
            err(f'{owner}: modifier bonus type must be a non-empty string')


def check_armor_entry(owner, entry):
    unknown = set(entry) - ARMOR_ENTRY_KEYS
    if unknown:
        err(f'{owner}: unknown entry keys {sorted(unknown)}')
    changes = entry.get('changes')
    notes = entry.get('contextNotes')
    if not isinstance(changes, list) or not isinstance(notes, list):
        err(f'{owner}: armor entry needs "changes" and "contextNotes" lists')
        return
    if not changes and not notes:
        err(f'{owner}: armor entry has no changes and no contextNotes')
    for ch in changes:
        unknown = set(ch) - CHANGE_KEYS
        if unknown:
            err(f'{owner}: unknown change keys {sorted(unknown)}')
        if not isinstance(ch.get('formula'), str) or not ch.get('formula'):
            err(f'{owner}: change missing formula')
        if not valid_target(ch.get('target'), PF1_CHANGE_TARGETS):
            err(f'{owner}: invalid change target {ch.get("target")!r}')
        if ch.get('operator') not in ('add', 'set'):
            err(f'{owner}: bad change operator {ch.get("operator")!r}')
        if not isinstance(ch.get('type'), str) or not ch.get('type'):
            err(f'{owner}: change bonus type must be a non-empty string')
    for note in notes:
        unknown = set(note) - {'text', 'target'}
        if unknown:
            err(f'{owner}: unknown contextNote keys {sorted(unknown)}')
        text = note.get('text')
        if not text or not isinstance(text, str):
            err(f'{owner}: contextNote missing text')
        else:
            check_brackets(owner, text)
        if not valid_target(note.get('target'), PF1_NOTE_TARGETS):
            err(f'{owner}: invalid contextNote target {note.get("target")!r}')


def main():
    with open(QE_PATH, encoding='utf-8') as f:
        qe = json.load(f)
    with open(WEAPON_QUALITIES, encoding='utf-8') as f:
        wq = json.load(f)
    with open(ARMOR_QUALITIES, encoding='utf-8') as f:
        aq = json.load(f)

    unknown = set(qe) - {'_readme', 'weapon', 'armor'}
    if unknown:
        err(f'unknown top-level sections {sorted(unknown)}')

    qe_weapon = qe.get('weapon') or {}
    qe_armor = qe.get('armor') or {}

    weapon_names = {n for sec in wq.values() for n in sec}
    armor_names = {n for sec in aq.values() for n in sec}

    def names_ci(names):
        return {n.lower(): n for n in names}

    for label, wanted, have in (('weapon', weapon_names, qe_weapon),
                                ('armor', armor_names, qe_armor)):
        have_ci = names_ci(have)
        for name in sorted(wanted):
            if name.lower() not in have_ci:
                err(f'{label}: MISSING entry for {name!r}')
        wanted_ci = names_ci(wanted)
        for name in sorted(have):
            if name.lower() not in wanted_ci:
                err(f'{label}: dead key {name!r} (not in the qualities list)')

    for name, entry in qe_weapon.items():
        owner = f'weapon.{name}'
        unknown = set(entry) - WEAPON_ENTRY_KEYS
        if unknown:
            err(f'{owner}: unknown entry keys {sorted(unknown)}')
        conds = entry.get('conditionals')
        if not isinstance(conds, list) or not conds:
            err(f'{owner}: needs a non-empty "conditionals" list')
            continue
        for cond in conds:
            check_conditional(owner, cond)

    for name, entry in qe_armor.items():
        check_armor_entry(f'armor.{name}', entry)

    if errors:
        for e in errors:
            print(e)
        print(f'\nFAILED: {len(errors)} problem(s)')
        sys.exit(1)
    print(f'OK: {len(qe_weapon)} weapon + {len(qe_armor)} armor entries; '
          f'full coverage of {len(weapon_names)} weapon and {len(armor_names)} '
          'armor/shield quality names.')


if __name__ == '__main__':
    main()
