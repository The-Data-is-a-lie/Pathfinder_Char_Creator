"""The familiar's stat block: master-derived numbers over a species body (spec section 8, v1 debt).

A familiar is the one bonded-creature type whose numbers key off the MASTER, not a chassis table
(RAW, wizard Familiar class feature): HP is half the master's total, BAB is the master's, each base
save is the better of the familiar's own (Fort +2 / Ref +2 / Will +0) and the master's, and skill
ranks are per-skill the better of the animal's own and the master's. That is why this module runs
as a LATE pass (the phase_bloodline_resolution precedent) instead of inside stat_bonded_creatures:
at that point in the pipeline the master has no HP, no skills, and luck has not settled -- every
number here would be wrong. main_test calls stat_familiars() after phase_luck_resolution, when the
inputs are final.

Body geometry (size, attacks, natural armor parsing) reuses companion_stats' machinery on purpose:
the RULES are shared even though the sourcing differs, and a second attack parser would drift.
"""
from utils import data
from utils.class_func.companion_stats import (
    SIZE_GEOMETRY, _abilities, _attack_count, _eligible_skills, _leftovers, _mod, _natural_armor,
    _parse_attacks, _racial_skill_mods, merge_advancement,
)

# RAW: the familiar's own base saves; each slot competes with the master's base save.
FAMILIAR_BASE_SAVES = {'fort': 2, 'ref': 2, 'will': 0}

# RAW: Tiny or smaller creatures use Dex in place of Str for CMB. Every base familiar qualifies;
# companions never do, which is why companion_stats does not model it and this module does.
DEX_CMB_SIZES = ('fine', 'diminutive', 'tiny')


def _master_table(character):
    return getattr(character, 'familiar_master_bonus', None) or {}


def _table_row(character, level):
    rows = _master_table(character).get('levels') or {}
    return rows.get(str(min(20, max(1, int(level or 1))))) or {}


def _accumulated_specials(character, level):
    """Every table ability gained at or below `level`, in table order."""
    rows = _master_table(character).get('levels') or {}
    names = []
    for step in range(1, min(20, max(1, int(level or 1))) + 1):
        names.extend((rows.get(str(step)) or {}).get('special') or [])
    return names


def _familiar_skills(merged, abilities, master_ranks, hd, size_stealth):
    """Per-skill max of the master's ranks and the animal's own -- the animal's own are zero here
    (no chassis budget exists for a familiar), so this is the master-rank overlay with the
    familiar's OWN ability/racial/size modifiers on top, capped at HD like every rank."""
    racial = _racial_skill_mods(merged)
    eligible = set(_eligible_skills(merged, abilities.get('int')))
    ranks = {}
    for skill, rank in (master_ranks or {}).items():
        name = str(skill).strip().lower()
        if name in eligible and int(rank or 0) > 0:
            ranks[name] = min(int(rank), hd)
    out = {}
    for skill in sorted(set(list(ranks) + list(racial))):
        rank = ranks.get(skill, 0)
        ability = data.SKILL_ABILITY.get(skill)
        mod = _mod(abilities.get(ability)) or 0
        total = rank + mod + racial.get(skill, 0)
        if rank:
            total += 3                       # trained, same convention as companion _skills
        if skill == 'stealth':
            total += size_stealth
        out[skill] = {'ranks': rank, 'total': total}
    return out


def familiar_stats(character, entry, master_ranks):
    """The finished `stats` block for one familiar entry, or None when there is nothing to stat."""
    if not entry.get('species'):
        return None
    merged, notes = merge_advancement(entry.get('species_stats'), 0)
    if not merged:
        return None

    level = entry.get('effective_level') or 0
    row = _table_row(character, level)
    hd = max(1, int(getattr(character, 'level', None) or level or 1))  # RAW: HD = master's level

    abilities = _abilities(merged, None)
    if abilities.get('int') is not None and row.get('int_score'):
        abilities['int'] = int(row['int_score'])   # the table's Int always wins (RAW)
    mods = {stat: _mod(score) for stat, score in abilities.items()}
    dex_mod = mods.get('dex') or 0
    str_mod = mods.get('str') or 0

    size = str(merged.get('size') or 'tiny').strip().lower()
    geometry = SIZE_GEOMETRY.get(size, SIZE_GEOMETRY['tiny'])
    natural = _natural_armor(merged.get('ac')) + int(row.get('natural_armor_adj') or 0)
    bab = int(getattr(character, 'bab_total', None) or 0)
    master_bases = getattr(character, 'save_bases', None) or {}

    cmb_mod = dex_mod if size in DEX_CMB_SIZES else str_mod
    specials = _accumulated_specials(character, level)
    routine = merged.get('attack')

    stats = {
        'size': size,
        'space': geometry['space'],
        'hd': hd,
        'hit_die': None,   # HP is derived from the master, never rolled on the body's dice
        'hp': max(1, int(getattr(character, 'Total_HP', None) or 0) // 2),
        'abilities': abilities,
        'ability_modifiers': mods,
        'ac': 10 + geometry['ac'] + dex_mod + natural,
        'touch_ac': 10 + geometry['ac'] + dex_mod,
        'flat_footed_ac': 10 + geometry['ac'] + natural,
        'natural_armor': natural,
        'saves': {
            save: max(FAMILIAR_BASE_SAVES[save], int(master_bases.get(save) or 0)) + own_mod
            for save, own_mod in (('fort', mods.get('con') or 0),
                                  ('ref', dex_mod),
                                  ('will', mods.get('wis') or 0))
        },
        'bab': bab,
        'initiative': dex_mod,
        'cmb': bab + cmb_mod + geometry['special'],
        'cmd': 10 + bab + str_mod + dex_mod + geometry['special'],
        'speed': merged.get('speed'),
        'attacks': _parse_attacks(routine, bab, str_mod, geometry['ac'],
                                  _attack_count(routine) == 1),
        'skills': _familiar_skills(merged, abilities, master_ranks, hd, geometry['stealth']),
        'special_qualities': merged.get('special qualities'),
        'special_attacks': merged.get('special attacks'),
        'special': ', '.join(specials) or None,
        'spell_resistance': (hd + 5) if 'spell resistance' in specials else None,
        'size_change': None,
        'other': _leftovers(merged),
        'merge_notes': notes,
    }
    return stats


def master_abilities(character, entry):
    """The `master_abilities` payload field (spec section 8 export table, familiars only):
    the table abilities the bond has reached, each with its one-line note, plus the perk the
    species grants the MASTER. Recorded, not computed into the master's numbers -- Alertness is
    conditional on arm's reach and the perks are situational, so folding them into master math
    would overstate them the same way D12 refuses to guess at progression_override."""
    table = _master_table(character)
    notes = table.get('ability_notes') or {}
    perks = table.get('species_perks') or {}
    return {
        'abilities': [{'name': name, 'note': notes.get(name)}
                      for name in _accumulated_specials(character, entry.get('effective_level') or 0)],
        'species_perk': perks.get(str(entry.get('species') or '').lower()),
    }


def stat_familiars(character, skill_ranks):
    """Write `stats` and `master_abilities` onto every familiar entry. The late pass -- see the
    module docstring for why this cannot run where stat_bonded_creatures does."""
    for entry in getattr(character, 'bonded_creatures', None) or []:
        if entry.get('type') != 'familiar' or not entry.get('species'):
            continue
        entry['stats'] = familiar_stats(character, entry, skill_ranks)
        entry['master_abilities'] = master_abilities(character, entry)
    return getattr(character, 'bonded_creatures', None) or []
