"""Psionics (Dreamscarred Press, as republished by the Library of Metzofitz) generation.

The Path of War module next door is the governing precedent -- a 3pp system whose mechanics are
scraped into Backend/json/, computed here, and rendered in Foundry by a third-party module. This is
that shape MINUS the prerequisite machinery: psionic powers have no prerequisites, so path_of_war's
_constrained_pick and its prereq graph have no analogue. Selection is just level-weighted picking
from a legal pool.

"Manifester" is three categories, not one, and the payload models all three:
  - full manifesters    power points AND powers known (ten of the twelve)
  - the aegis           power points, NO powers known -- it spends them on astral suit
                        customizations, which are class options, not powers
  - the soulknife       neither; its mind blade is a weapon, not a manifesting subsystem

The backend computes and emits finished numbers even though pf1-psionics can calculate manifester
level, concentration and power points itself (ticket 03). The payload is the API contract, the
standalone web sheet has no game system to compute anything, and test_house_invariants.py needs
something to assert on. The two agree rather than fight because the power-point tables are
identical -- validate_psionics_data.py checks exactly that, every run.

Power points are a table PLUS a formula, not a bigger table: pp_per_day from the class table at
manifester level, plus floor(key ability modifier x manifester level / 2), with a hard gate that a
key ability of 9 or lower cannot manifest at all. There is no spells_from_ability_mod.json analogue
and none is needed.
"""
import random
import re
from math import floor

from utils import data
from utils.class_func.skill_ranks import final_ability_score

# The power list each class draws from, keyed as psionic_power_lists.json spells them. The aegis
# and soulknife are absent on purpose -- see the module docstring. Out-of-scope lists (Gambler,
# Gifted Blade, Sighted Seeker) stay in the data because in-scope powers' Level: lines cite them,
# but no in-scope class selects from them.
POWER_LIST_FOR = {
    "cryptic": "Cryptic Powers",
    "dread": "Dread Powers",
    "highlord": "Highlord Powers",
    "marksman": "Marksman Powers",
    "psion": "Psion/Wilder Powers",
    "psychic warrior": "Psychic Warrior Powers",
    "tactician": "Tactician Powers",
    "vitalist": "Vitalist Powers",
    "voyager": "Voyager Powers",
    "wilder": "Psion/Wilder Powers",
}

DISCIPLINE_LIST = "Psion Discipline Powers"
# A key ability this low cannot manifest at all -- not "manifests badly", cannot.
MIN_MANIFESTING_SCORE = 10
# How many disciplines a non-psion build leans on. A soft bias, not a restriction: it exists so a
# generated manifester reads as a concept rather than a grab bag of unrelated powers.
DISCIPLINE_BIAS = (2, 3)
# Chance a pick ignores the bias and takes anything legal, so builds are flavoured, not fenced in.
OFF_THEME_CHANCE = 0.2


def manifester_entries(character):
    """Every psionic class entry on the character, in class order. Unlike Path of War (max one
    initiator) nothing forbids two psionic classes, so this is a list."""
    return [entry for entry in getattr(character, 'classes', [])
            if entry['name'] in data.psionic_class]


def manifesting_stat(character, class_name):
    """The class's key ability, read from its class_data.json entry.

    Deliberately NOT data.caster_mod -- power points are not spells per day -- and deliberately not
    a separate map in data.py either: the entry already exists and already carries `main_stat`, so
    a sibling key is one owner where a map would be two that can drift. It has to be its own key
    because the two questions differ: a psychic warrior manifests off Wisdom but plays off Strength,
    and a soulknife manifests off nothing.
    """
    entry = getattr(character, 'class_data', {}).get(class_name, {})
    return entry.get('manifesting_stat', '') or ''


def _progression(character, class_name, column, level):
    """One value from a class's 20-row progression table. Index = level - 1 (the Path of War
    convention), and epic levels read the level-20 row."""
    table = getattr(character, 'psionic_powers_known', {}).get(class_name, {})
    values = table.get(column) or []
    if not values:
        return 0
    return values[max(0, min(level, 20) - 1)]


def bonus_power_points(modifier, manifester_level):
    """floor(key ability modifier x manifester level / 2), never negative.

    A formula rather than a table: the published bonus-power-point tables are just this expression
    tabulated, so tabulating it again would be a second copy to keep in sync.
    """
    return max(0, floor(modifier * manifester_level / 2))


def _legal_pool(character, class_name, max_level, discipline=None):
    """{power name: power level} for everything the class may learn at this manifester level.

    Level "0" is the talents tier and is included: talents are at-will minor powers a manifester
    genuinely knows, and several classes' tables count them.
    """
    lists = getattr(character, 'psionic_power_lists', {})
    pool = {}

    def absorb(levels):
        for level_key, names in (levels or {}).items():
            if not level_key.isdigit() or int(level_key) > max_level:
                continue
            for name in names:
                pool.setdefault(name, int(level_key))

    entry = lists.get(POWER_LIST_FOR.get(class_name, ""), {})
    absorb(entry.get("levels"))

    # The psion's chosen discipline grants its own list on top of the shared psion/wilder one.
    # Structural trap: this entry is keyed by `disciplines`, not `levels` -- a consumer that
    # assumes `levels` raises KeyError here.
    if discipline:
        block = lists.get(DISCIPLINE_LIST, {}).get("disciplines", {}).get(discipline)
        if block:
            absorb(block.get("levels"))
    return pool


def _disciplines_of(character, names):
    """The disciplines the given powers belong to, for the soft thematic bias."""
    powers = getattr(character, 'psionic_powers', {})
    found = []
    for name in names:
        discipline = (powers.get(name) or {}).get('discipline', '')
        discipline = discipline.split('(')[0].strip().lower()
        if discipline and discipline not in found:
            found.append(discipline)
    return found


def _pick_powers(character, pool, count, max_level):
    """Level-weighted picks from the legal pool, with a soft 2-3 discipline bias.

    Weighted toward the highest available level, as Path of War does: a level-appropriate NPC
    should read as one, and uniform sampling over a pool that is mostly low-level talents produces
    a manifester who never learned anything impressive.
    """
    if count <= 0 or not pool:
        return []
    names = list(pool)
    theme = _disciplines_of(character, random.sample(names, min(len(names), 12)))
    theme = theme[:random.randint(*DISCIPLINE_BIAS)]
    powers = getattr(character, 'psionic_powers', {})

    def weight(name):
        level = pool[name]
        # +1 so level-0 talents stay reachable rather than being weighted out entirely.
        base = (level + 1) ** 2
        if theme and random.random() > OFF_THEME_CHANCE:
            discipline = (powers.get(name) or {}).get('discipline', '')
            discipline = discipline.split('(')[0].strip().lower()
            if discipline and discipline not in theme:
                base *= 0.25
        return base

    chosen = []
    remaining = dict(pool)
    while remaining and len(chosen) < count:
        candidates = list(remaining)
        weights = [weight(name) for name in candidates]
        pick = random.choices(candidates, weights=weights, k=1)[0]
        remaining.pop(pick)
        chosen.append(pick)
    return sorted(chosen, key=lambda n: (pool[n], n))


def _emit_name(character, name):
    """The name to put in the payload: the pf1-psionics spelling where the module has the power,
    the wiki's own where it does not.

    The module attaches by name match and silently drops what it does not recognise, so emitting
    our spelling of a power the module knows under a different one loses it with no error. Names
    with no module item are Metzofitz-only content and are carried by powers_desc_dict instead.
    """
    name_map = getattr(character, 'psionic_name_map', {}) or {}
    return name_map.get('matched', {}).get('powers', {}).get(name, name)


def _desc_entry(character, name):
    record = getattr(character, 'psionic_powers', {}).get(name) or {}
    return {
        'name': name,
        'display': record.get('display', ''),
        'discipline': record.get('discipline', ''),
        'level': record.get('level', ''),
        'manifesting time': record.get('manifesting time', ''),
        'range': record.get('range', ''),
        'duration': record.get('duration', ''),
        'saving throw': record.get('saving throw', ''),
        'power resistance': record.get('power resistance', ''),
        'power points': record.get('power points', ''),
        'text': record.get('text', ''),
        'augment': record.get('augment', ''),
    }


def mind_blade(character, melee=True):
    """The soulknife's mind blade, or None.

    Ticket 08's one genuine exception: every other psionic subsystem is a list to pick from, but the
    mind blade is a *weapon*, and armor_and_weapon_chooser.py assumes a weapon is something you buy.

    Resolution, and the reason it stays small: the mind blade is not a weapon of its own, it is a
    weapon *shape*. "Shape mind blade" lets the soulknife form it as any light, one-handed or
    two-handed melee weapon, so the chosen weapon's own damage dice, crit range and groups are
    already right -- what changes is that it costs nothing, is named for what it is, and takes its
    enhancement bonus from the class table instead of from the purse. The existing
    enhancement_effects_dict machinery then applies unchanged.

    Returns {'name', 'shape', 'enhancement_bonus', 'max_enhancement_bonus'}. `enhancement_bonus` is
    the total the class grants; `max_enhancement_bonus` is how much of it may be a pure plus, with
    the remainder spent on special abilities (the class table tracks the two separately).
    """
    entry = next((e for e in getattr(character, 'classes', []) if e['name'] == 'soulknife'), None)
    if entry is None:
        return None
    table = (getattr(character, 'psionic_classes', {}).get('soulknife', {}).get('table') or [])
    if not table:
        return None
    row = table[max(0, min(entry['capped_level'], 20) - 1)]

    # Total enhancement is written into the Special column as "Enhanced mind blade +N"; the pure
    # cap has its own column, which the scraper keeps under 'extra' because no other class has it.
    total = 0
    match = re.search(r"enhanced mind blade \+(\d+)", row.get('special', ''), re.IGNORECASE)
    if match:
        total = int(match.group(1))
    pure = 0
    for value in (row.get('extra') or {}).values():
        found = re.search(r"\+(\d+)", str(value))
        if found:
            pure = int(found.group(1))
            break

    # Only name the shape when the rolled weapon is actually melee -- "shape mind blade" covers
    # light, one-handed and two-handed MELEE weapons, so a ranged roll gets the bare name rather
    # than a mind blade shaped like a crossbow.
    shape = next(iter(getattr(character, 'weapon_dict', {}) or {}), '') if melee else ''
    return {
        'name': f"Mind Blade ({shape})" if shape else "Mind Blade",
        'shape': shape,
        'enhancement_bonus': total,
        'max_enhancement_bonus': pure,
    }


def choose_psionics_attr(character):
    """Build the `manifesters` payload block plus its sibling `powers_desc_dict`.

    Returns the empty bundle for a character with no psionic class, so the caller can splice it in
    unconditionally the way the Path of War bundle is.
    """
    bundle = {'manifesters': [], 'powers_desc_dict': {}}
    entries = manifester_entries(character)
    if not entries:
        return bundle

    for entry in entries:
        name = entry['name']
        level = entry['capped_level']
        stat = manifesting_stat(character, name)

        record = {
            'name': name,
            'display': entry.get('display', name.title()),
            'level': entry['level'],
            'manifester_level': level,
            'manifesting_stat': stat,
            'pp_per_day': 0,
            'max_power_level': 0,
            'powers_known_list': [],
            'powers_chosen': [],
            'discipline': '',
        }

        # The soulknife: no manifesting stat, no power points, no powers. It still gets an entry --
        # a class silently absent from the payload is indistinguishable from a bug.
        if not stat:
            bundle['manifesters'].append(record)
            continue

        score = final_ability_score(character, stat)
        if score < MIN_MANIFESTING_SCORE:
            # Cannot manifest at all. The entry stays, with zeroes, for the same reason.
            bundle['manifesters'].append(record)
            continue

        modifier = (score - 10) // 2
        base_pp = _progression(character, name, 'pp_per_day', level)
        record['pp_per_day'] = base_pp + bonus_power_points(modifier, level)
        record['max_power_level'] = _progression(character, name, 'max_power_level', level)

        # The aegis manifests but knows no powers -- it has power points and nothing to spend them
        # on but its astral suit. POWER_LIST_FOR has no entry for it, so the pool stays empty.
        if name not in POWER_LIST_FOR:
            bundle['manifesters'].append(record)
            continue

        # The psion's discipline is rules-mandated and picked first: it decides the class's whole
        # power list, so it cannot be an afterthought the way another class's theme can.
        discipline = ''
        if name == 'psion':
            available = sorted(getattr(character, 'psionic_power_lists', {})
                               .get(DISCIPLINE_LIST, {}).get('disciplines', {}))
            if available:
                discipline = random.choice(available)
        record['discipline'] = discipline

        max_level = record['max_power_level']
        known = _progression(character, name, 'powers_known', level)
        pool = _legal_pool(character, name, max_level, discipline)
        chosen = _pick_powers(character, pool, known, max_level)

        record['powers_chosen'] = [_emit_name(character, n) for n in chosen]
        # One count per power level 0..max, the shape the sheet groups by.
        record['powers_known_list'] = [sum(1 for n in chosen if pool[n] == lvl)
                                       for lvl in range(0, max(max_level, 0) + 1)]
        for power in chosen:
            bundle['powers_desc_dict'][_emit_name(character, power)] = _desc_entry(character, power)

        bundle['manifesters'].append(record)

    return bundle
