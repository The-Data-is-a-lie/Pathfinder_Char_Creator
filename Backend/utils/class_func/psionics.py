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

Powers known is likewise a table plus two rules the table does not carry, both of them in the
scraped prose rather than in any column -- see FREE_TALENTS and the max_power_level cap in
choose_psionics_attr. Talents (0-level powers) are granted free and land in bucket 0 of
powers_by_level; the key ability caps the highest level learnable regardless of class level.
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

# Free 0-level talents, granted by class feature IN ADDITION to powers known. The scraped rules text
# says so in as many words -- psionic_classes.json -> psion -> features -> talents:
#   "Each psion gains three 0 level talents of their choice, as well as detect psionics. These
#    talents do not count against the psion's powers known."
# A class absent here grants none: the marksman has no talent feature at all, and the aegis and
# soulknife manifest no powers to begin with.
FREE_TALENTS = {
    'psion': 3,
    'tactician': 3,
    # The vitalist's third talent should come from its chosen METHOD's power list, and the
    # highlord's second from its chosen TENET's. Neither of those lists is in the scrape, so both
    # draw from the class list instead -- recorded in docs/wayfinder/psionics/map.md under
    # "Not yet specified". The COUNT is right either way; only the source list is approximated.
    'vitalist': 3,
    'psychic warrior': 2,
    'cryptic': 2,
    'dread': 2,
    'highlord': 2,
    'voyager': 2,
    'wilder': 1,
}

# Talents a class is given BY NAME rather than choosing. The psion's detect psionics is the only one.
MANDATED_TALENTS = {'psion': ['Detect Psionics']}

# The class-features bucket each class's subsystem picks land in -- the `dict_name` its
# generic_class_option_chooser call in main_test.py writes into data_dict['class features'].
#
# Emitted on the payload so a renderer can find a class's own subsystem without hard-coding this map
# on its side. The aegis and the soulknife NEED it: they are the two classes whose psionics tab has
# nothing else on it, and without this their picks are generated but invisible anywhere a player
# would look for them.
SUBSYSTEM_BUCKET = {
    'aegis': 'customizations',
    'cryptic': 'insights',
    'dread': 'terrors',
    'highlord': 'decrees',
    'marksman': 'combat_style',
    'psychic warrior': 'warrior_path',
    'soulknife': 'blade_skills',
    'tactician': 'strategies',
    'vitalist': 'vitalist_method',
}
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


def caster_type(character, class_name):
    """The class's power-point progression as pf1-psionics names it: 'low', 'med', 'high' or ''.

    DERIVED, not stored: it is whichever of the three published tables the class's own pp_per_day
    column equals. A hand-maintained map would be a second thing to keep in sync with the scrape,
    and validate_psionics_data.py already fails the run when a class matches none of the three --
    so an unrecognised progression is a build error there, never a silent '' here.

    The Foundry module needs this on the manifester book (`casterType`): it selects the module's
    own power-point table, and a book without it computes zero points.
    """
    table = getattr(character, 'psionic_powers_known', {}).get(class_name, {})
    column = table.get('pp_per_day') or []
    if not column:
        return ''
    return next((name for name, values in data.psionic_pp_tables.items() if values == column), '')


def bonus_power_points(modifier, manifester_level):
    """floor(key ability modifier x manifester level / 2), never negative.

    A formula rather than a table: the published bonus-power-point tables are just this expression
    tabulated, so tabulating it again would be a second copy to keep in sync.
    """
    return max(0, floor(modifier * manifester_level / 2))


def _power_index(character):
    """{casefolded name or alias: the psionic_powers.json key it names}.

    The power LISTS cite names the power PAGES spell differently: wiki redirects are recorded as
    `aliases` ("Thought Shield" -> "Thought Shield (power)"), and a few differ only in case
    ("Know Direction And Location"). validate_psionics_data.py has always resolved both; doing less
    here let a cited name reach the payload with no rules text and no entry in the Foundry name map
    -- an empty row on a Foundry sheet, nothing at all on the web sheet.

    Built once per character: the index is ~700 entries and every pick consults it.
    """
    cached = getattr(character, '_psionic_power_index', None)
    if cached is not None:
        return cached
    index = {}
    for key, record in (getattr(character, 'psionic_powers', {}) or {}).items():
        index.setdefault(key.casefold(), key)
        for alias in (record.get('aliases') or []):
            index.setdefault(str(alias).casefold(), key)
    character._psionic_power_index = index
    return index


def _power_record(character, name):
    """The record a cited name resolves to, or {} when the name has no page of its own."""
    key = _power_index(character).get(str(name).casefold())
    return (getattr(character, 'psionic_powers', {}) or {}).get(key) or {}


def _legal_pool(character, class_name, max_level, discipline=None, min_level=1):
    """{power name: power level} for everything the class may learn at this manifester level.

    Level "0" is the talents tier and is EXCLUDED by default -- hence min_level=1. Talents are
    granted free by class feature and explicitly "do not count against powers known" (FREE_TALENTS),
    so letting one into the counted pool would spend a powers-known slot on something the rules give
    away, inverting the rule instead of implementing it. Pass min_level=0, max_level=0 to get the
    talent tier on its own.
    """
    lists = getattr(character, 'psionic_power_lists', {})
    index = _power_index(character)
    pool = {}

    def absorb(levels):
        for level_key, names in (levels or {}).items():
            if not level_key.isdigit() or not (min_level <= int(level_key) <= max_level):
                continue
            for name in names:
                # Keyed by the PAGE's own name, so rules text, discipline and the Foundry name map
                # all resolve downstream. A name that resolves to nothing is a cited-but-pageless
                # red link (Manifest Veil, Detect Compulsion, Mind Trap) -- picking one would put a
                # power with no rules text and no Foundry item on the sheet, so it is not legal.
                key = index.get(str(name).casefold())
                if key:
                    pool.setdefault(key, int(level_key))

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
    found = []
    for name in names:
        discipline = _power_record(character, name).get('discipline', '')
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

    def weight(name):
        level = pool[name]
        # +1 so level-0 talents stay reachable rather than being weighted out entirely.
        base = (level + 1) ** 2
        if theme and random.random() > OFF_THEME_CHANCE:
            discipline = _power_record(character, name).get('discipline', '')
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
    record = _power_record(character, name)
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
            # Stays '' for anything that cannot manifest -- the soulknife, and a manifester whose
            # key ability failed the score gate below. It moves with pp_per_day on purpose: a
            # caster type on a zero-point book would have the Foundry module compute points for a
            # character the rules say has none.
            'caster_type': '',
            'pp_per_day': 0,
            'max_power_level': 0,
            'powers_known_list': [],
            'powers_by_level': [],
            'powers_chosen': [],
            'talents_known': 0,
            'discipline': '',
            # Where this class's subsystem picks live in the class-features dict. Carried so a
            # renderer can show a class's own options on its psionics tab rather than only under
            # generic class features -- the aegis and soulknife have nothing else to show.
            'subsystem_bucket': SUBSYSTEM_BUCKET.get(name, ''),
            'mind_blade': None,
        }

        # The soulknife: no manifesting stat, no power points, no powers. It still gets an entry --
        # a class silently absent from the payload is indistinguishable from a bug -- and that entry
        # carries its mind blade, which is the only psionic thing it has. main_test.py stashes the
        # blade it actually equipped; recomputing here would let the weapon and the tab disagree.
        if not stat:
            record['mind_blade'] = getattr(character, 'mind_blade', None)
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
        # The class table is a ceiling, not the answer: every one of the ten power-knowing classes
        # also requires a key ability of "at least 10 + the power's level" to LEARN a power
        # (psionic_classes.json -> manifesting_prose -> 'maximum power level known'). A 17th-level
        # psion with Int 14 caps at 4th-level powers, not 9th. Hits the psychic warrior hardest --
        # it manifests off Wisdom but plays off Strength -- and that is the rule working, not a bug.
        record['max_power_level'] = max(0, min(
            _progression(character, name, 'max_power_level', level), score - 10))
        record['caster_type'] = caster_type(character, name)

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

        # Free 0-level talents, on TOP of powers known. Named grants (the psion's detect psionics)
        # come first because they are not a choice; the rest are picked from the talent tier alone.
        # Anything already taken as a leveled power is excluded so a name cannot land twice -- a few
        # powers appear on both tiers, and `pool` is authoritative for what level this class learns
        # each one at.
        talent_pool = {n: 0 for n in _legal_pool(character, name, 0, discipline, min_level=0)
                       if n not in pool}
        mandated = [t for t in MANDATED_TALENTS.get(name, []) if talent_pool.pop(t, None) is not None]
        talents = mandated + _pick_powers(
            character, talent_pool, FREE_TALENTS.get(name, 0) - len(mandated), 0)
        record['talents_known'] = len(talents)

        # Merged into the same maps the leveled picks use, so talents ride every code path below --
        # bucketing, counts, description entries -- instead of needing a parallel one.
        pool.update({name_: 0 for name_ in talents})
        chosen = talents + chosen

        record['powers_chosen'] = [_emit_name(character, n) for n in chosen]
        # One bucket per power level 0..max -- path_of_war's maneuvers_choose_from shape. This is
        # the ONLY place a power's level survives: psionic_powers.json keys its levels by power
        # LIST ("psion/wilder"), not by class, so no renderer can recover the level of a psion's
        # power from the description entry. `pool` is the class's own list, so pool[n] is exactly
        # the level this class learns it at.
        record['powers_by_level'] = [[_emit_name(character, n) for n in chosen if pool[n] == lvl]
                                     for lvl in range(0, max(max_level, 0) + 1)]
        # Derived from the buckets rather than recounted, so the two can never disagree.
        record['powers_known_list'] = [len(bucket) for bucket in record['powers_by_level']]
        for power in chosen:
            bundle['powers_desc_dict'][_emit_name(character, power)] = _desc_entry(character, power)

        bundle['manifesters'].append(record)

    return bundle
