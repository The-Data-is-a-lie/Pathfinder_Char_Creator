"""The optimizer's plan object: pick a power role right after the classes are picked.

Spec 15, rulings 2026-08-11 (map: optimal-builder). The role is one row of
``Backend/json/power_roles.json`` -- 2-3 primary axes to push, floors for the rest, and the spine
policies (stat priority, weapon policy, enhancement split, gear ladder, feat spine, dips) that the
optimized-path choosers read. Random mode never enters this module's branch: ``optimize`` off means
``character.role`` is None and every chooser takes its existing path untouched, which is what keeps
the seven golden fixtures byte-identical.

WHO OWNS WHAT. This module owns the vocabularies the role table is allowed to use --
``GEAR_LADDER_TOKENS``, ``STAT_TOKENS``, ``WEAPON_POLICIES`` -- and
``scripts/gates/validate_power_roles.py`` imports them so the data is checked against the code
(the power_adders.json precedent: a misspelled token contributes nothing forever, and only a gate
that reads both artifacts can say so).

THE ROLE FOLLOWS THE CLASS. Explicit inputs are always honoured, so class selection runs first and
the role is drawn from the FIRST pick's candidates (``class_roles``). ``optimize`` may also name a
role outright -- ``optimize: "wall"`` -- which is forced; an unknown role name is an error by
ruling, never a silent fallback (the unmatched-string trap ticket 06 documents).
"""
import json
import os
import random

from .pipeline import phase

# Tokens a gear ladder may use. The Phase C gear chooser resolves them onto concrete purchases
# (big-six name templates, the enhancement budgets); the validator holds the data to this list.
GEAR_LADDER_TOKENS = (
    'weapon_enhancement', 'armor_enhancement', 'shield_enhancement',
    'cloak_of_resistance', 'ring_of_protection', 'amulet_of_natural_armor',
    'primary_stat_item', 'secondary_stat_item', 'con_item', 'boots_of_speed', 'jingasa',
)

# stat_priority entries: 'primary'/'secondary' resolve through the class's own main_stat /
# main_stat_2; literals are placed in order; any ability the list never mentions is appended in
# _STAT_FILL order, so the DUMP stats are simply whatever the role never asked for.
STAT_TOKENS = ('primary', 'secondary', 'str', 'dex', 'con', 'int', 'wis', 'cha')
_STAT_FILL = ('str', 'dex', 'con', 'int', 'wis', 'cha')

WEAPON_POLICIES = ('two_handed', 'finesse', 'one_handed_shield', 'ranged', 'any')

_ROLES_CACHE = None
_BUFF_NAMES_CACHE = None
_STANCE_AC_CACHE = None
_SPHERE_DEFENSE_CACHE = None


def sphere_defense_names():
    """Lowercased talent names of power_adders.json::sphere_defense -- the curated fight-state
    sphere talents the wall's talent picker claims first (the stance_ac_bases pattern: the
    generator WEIGHTS what the metric will SCORE; the two share the data file, never code)."""
    global _SPHERE_DEFENSE_CACHE
    if _SPHERE_DEFENSE_CACHE is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', '..', 'json', 'power_adders.json')
        with open(path, encoding='utf-8') as handle:
            raw = json.load(handle)
        _SPHERE_DEFENSE_CACHE = frozenset(
            str(k).lower() for k in (raw.get('sphere_defense') or {}) if not str(k).startswith('_'))
    return _SPHERE_DEFENSE_CACHE


def stance_ac_bases():
    """{lowercased stance name: base AC} from power_adders.json::stance_ac -- what the wall's
    stance chooser scores when the prose does not parse flat. Base only: the chooser has no HD
    context, and the scaled part only grows the same pick."""
    global _STANCE_AC_CACHE
    if _STANCE_AC_CACHE is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', '..', 'json', 'power_adders.json')
        with open(path, encoding='utf-8') as handle:
            raw = json.load(handle)
        _STANCE_AC_CACHE = {str(k).lower(): int((v or {}).get('base') or 0)
                            for k, v in (raw.get('stance_ac') or {}).items()
                            if not str(k).startswith('_')}
    return _STANCE_AC_CACHE


def ambient_feat_names():
    """feat_tax.json's tax_primary_blocklist, lowercased -- the house-ambient feats every
    qualifying character has. The optimized feat path seeds these into the prereq vocabulary so
    a spine can legally chain through Dodge / Improved Unarmed Strike / Combat Expertise."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', '..', 'json', 'feat_tax.json')
    with open(path, encoding='utf-8') as handle:
        raw = json.load(handle)
    return tuple(str(n).lower() for n in raw.get('tax_primary_blocklist') or [])


def buff_spell_names():
    """Lowercased names of power_adders.json::spell_buffs -- the sweaty buff list.

    Read here (the generator side) so the spell chooser can WEIGHT what the metric will SCORE;
    the two sides share the data file, never each other's code.
    """
    global _BUFF_NAMES_CACHE
    if _BUFF_NAMES_CACHE is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', '..', 'json', 'power_adders.json')
        with open(path, encoding='utf-8') as handle:
            raw = json.load(handle)
        _BUFF_NAMES_CACHE = frozenset(
            str(k).lower() for k in (raw.get('spell_buffs') or {}) if not str(k).startswith('_'))
    return _BUFF_NAMES_CACHE


def load_roles():
    """The parsed power_roles.json, cached for the process (it is static data)."""
    global _ROLES_CACHE
    if _ROLES_CACHE is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', '..', 'json', 'power_roles.json')
        with open(path, encoding='utf-8') as handle:
            _ROLES_CACHE = json.load(handle)
    return _ROLES_CACHE


def optimize_requested(value):
    """The named `optimize` input, folded to (enabled, forced_role_name_or_None).

    Off is anything falsy or an explicit no; True/'y'/'true'/'1' enables with the role drawn from
    the class map; any other string names a role outright. The caller validates the name.
    """
    if value is None or value is False:
        return False, None
    text = str(value).strip()
    if text.lower() in ('', 'n', 'no', 'false', '0', 'none'):
        return False, None
    if value is True or text.lower() in ('y', 'yes', 'true', '1'):
        return True, None
    return True, text.lower()


@phase(requires=['_class_picks'], provides=['optimize_enabled', 'role_name', 'role'])
def phase_power_role(character, optimize, house_rules=None):
    """Choose the plan: the role every optimized-path chooser downstream serves.

    Runs immediately after phase_bootstrap_identity (the ruling: right after select_classes), off
    the FIRST class pick -- explicit inputs were already honoured there. Also samples which of the
    role's gear ladders this character follows (`_chosen_ladder`), because ladder variation is
    per-character by ruling (role-variation only, no flavour reserve).

    `house_rules` (V4 wall pass, ruling 2026-08-13) lands as ``role['_house']`` and nowhere else:
    the house AC kickers (Strength of a Warrior, the defensive-sphere package, sword-and-board
    TWD, Cautious Warrior) are curated content a chooser may only reach through the role object,
    so with optimize off -- role None -- the flag is inert by construction and random mode cannot
    see it.

    Draws from the seeded stream, so a replayed seed reproduces the same role and ladder.
    """
    enabled, forced = optimize_requested(optimize)
    house_enabled, _ = optimize_requested(house_rules)
    character.optimize_enabled = enabled
    if not enabled:
        character.role_name = None
        character.role = None
        return

    table = load_roles()
    roles = {k: v for k, v in table['roles'].items() if not k.startswith('_')}
    if forced is not None:
        if forced not in roles:
            raise ValueError(
                f"optimize names role {forced!r}, which power_roles.json does not define "
                f"(known: {sorted(roles)}) -- an unknown role is an error by ruling, "
                f"never a silent fallback")
        name = forced
    else:
        primary = str(character._class_picks[0]).lower()
        candidates = table['class_roles'].get(primary) or []
        # A class the map somehow misses falls back to every role rather than crashing a random
        # request; the validator is what keeps this branch dead.
        name = random.choice(candidates or sorted(roles))

    row = roles[name]
    ladders = sorted(k for k in (row.get('gear_ladders') or {}) if not k.startswith('_'))
    character.role_name = name
    character.role = dict(row)
    character.role['_chosen_ladder'] = random.choice(ladders) if ladders else None
    # Runtime-injected like _chosen_ladder (underscored so the data-file validator never has to
    # know it): the single switch every house-kicker chooser branches on.
    character.role['_house'] = house_enabled


def role_feat_spine(role):
    """The role's effective feat spine: the house kickers splice in ABOVE the standard spine,
    but only when the request set house_rules (role['_house']) -- with house off the list is
    feat_spine exactly, which is what keeps the standard optimized goldens byte-identical.
    House first because the spine is claimed top-down and the kickers (Strength of a Warrior)
    are the levers the V4 band was ruled around."""
    if not role:
        return []
    spine = list(role.get('feat_spine_house') or []) if role.get('_house') else []
    spine.extend(role.get('feat_spine') or [])
    return spine


def stat_order(character):
    """The six abilities in placement order for this character's role.

    'primary'/'secondary' resolve through the class's own casting/main stats, so one role row
    serves a wizard (int first) and a cleric (wis first) alike; unmentioned abilities append in
    _STAT_FILL order and are thereby the dumps. Returns None when not optimizing.
    """
    role = getattr(character, 'role', None)
    if not role:
        return None
    entry = character.class_data.get(str(character._class_picks[0]).lower(), {})
    resolved = []
    for token in role.get('stat_priority') or []:
        if token == 'primary':
            token = str(entry.get('main_stat') or '').lower()[:3]
        elif token == 'secondary':
            token = str(entry.get('main_stat_2') or '').lower()[:3]
        if token in _STAT_FILL and token not in resolved:
            resolved.append(token)
    resolved.extend(ab for ab in _STAT_FILL if ab not in resolved)
    return resolved
