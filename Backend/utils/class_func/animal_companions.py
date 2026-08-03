"""Bonded creatures: who grants one, at what effective level, and which creature it is.

Map #18, ticket #30 (D6, amended by the D8 grill #38). `resolve_bonded_creatures` is the SINGLE
path to a bonded creature; the hard-coded druid check this module used to be
(`class_entry_for(character, 'druid') and character.domain_chance <= 90`) is gone.

The grantor set is data -- `Backend/json/companion_grantors.json`. Read its `_readme` before
changing behaviour here; the columns and the three RAW amendments (#23: shifter is not a grantor,
antipaladin is a different subsystem, sorcerer is bloodline-conditional) live there.

FOUR THINGS THE GRILL SETTLED, EACH OF WHICH THIS FILE GETS WRONG IF EDITED CARELESSLY
--------------------------------------------------------------------------------------
1. A FRESH DRAW PER ROW. `random.randint(1, 100)` once per grantor row, never reusing
   `character.domain_chance`.
2. THE RESOLVER OWNS THE DRUID FLIP. `domain_inquisition.py` reads this module's outcome instead of
   comparing `domain_chance` itself. That rewire is mandatory, not tidying: the two outcomes used to
   be mutually exclusive *by construction* (one roll, one number). A fresh draw without the rewire
   gives ~9% of druids both a companion and a domain, and ~9% neither.
3. THE SPECIES TIER GETS ITS OWN DRAW. `domain_chance` used to gate both the domain-vs-companion
   choice (<= 90) and the species ladder (normal <= 80, plant <= 90, else vermin). The ladder only
   ran when the roll was already <= 90, so **no druid ever generated a vermin companion.**
4. ABSENCE IS DATA. When the threshold WAS met but the creature was removed -- a lost flip, or an
   archetype `removes` -- emit an entry with `species: None` and the reason in `outcome`. Below the
   threshold, emit nothing at all (D6: no clamp to level 1).

WHAT THIS SLICE DOES NOT DO
---------------------------
The advancement merge and the stat-block math are #31. Entries carry the raw species block and the
chassis row, exactly as the old payload did. Familiars and eidolons resolve to no entry at all,
because `familiar_choices.json` and `eidolon_base_forms.json` do not exist yet -- their rows are in
the table and marked `species_data`, so the grantor set stays complete and declarative while the
resolver stays honest about what it can actually name.
"""
import random

from utils.class_func.generic_func import class_entry_for

# Prerequisite phrases a bonded character satisfies, registered so feats gated on owning a
# companion (Boon Companion) become reachable. Kept as a tuple so the feat parser's disjunction
# split and a verbatim match both work.
BONDED_CREATURE_PREREQS = (
    'animal companion or familiar class feature',
    'animal companion class feature',
    'animal companion',
)

# The companion species ladder, on its own draw (see 3 above).
SPECIES_TIERS = ((80, 'normal'), (90, 'plant'), (100, 'vermin'))


def register_bonded_creature_prereqs(character):
    """Teach the feat/talent prerequisite pool that this character has a bonded creature."""
    if getattr(character, 'chooseable', None) is not None:
        character.chooseable.update(BONDED_CREATURE_PREREQS)


def _rows(character):
    table = getattr(character, 'companion_grantors', None) or {}
    return table.get('grantors', [])


def _archetype_effects(character, class_name):
    """(archetype name, the set of effects it has on the bond) for the rolled archetype."""
    rolled = getattr(character, 'archetypes_per_class', None) or []
    classes = getattr(character, 'classes', [])
    name = None
    for entry, archetype in zip(classes, rolled):
        if entry['name'] != class_name or not archetype:
            continue
        name = next(iter(archetype), None)
        break
    if not name:
        return None, set(), {}

    table = getattr(character, 'companion_archetypes', None) or {}
    record = table.get(f"{class_name.replace(' (unchained)', '').capitalize()}/{name}")
    if not record:
        return name, set(), {}
    effects = {item.get('effect') for item in (record.get('effects') or [])}
    effects.discard(None)
    if not effects and record.get('effect'):
        effects = {record['effect']}
    return name, effects, record


def _effective_level(expression, level, character, minimum=None):
    """Evaluate a row's expression over the grantor's OWN class level.

    The expressions are repo-owned data, not user input, so a restricted eval is the honest way to
    keep `max(bab, handle_animal, ride) - 3` in the table rather than as a code branch.
    """
    ranks = getattr(character, 'skill_ranks', None) or {}
    scope = {
        'level': level,
        'bab': getattr(character, 'bab_total', 0) or 0,
        'handle_animal': ranks.get('Handle Animal', ranks.get('handle animal', 0)) or 0,
        'ride': ranks.get('Ride', ranks.get('ride', 0)) or 0,
        'max': max,
        'min': min,
    }
    try:
        value = int(eval(expression, {'__builtins__': {}}, scope))   # noqa: S307 -- repo-owned data
    except Exception:
        value = level
    if minimum is not None:
        value = max(value, minimum)
    return value


def _standard_pool(character, tiers):
    """Species names from the named animal_choices tiers, or the literal names given."""
    choices = getattr(character, 'animal_choices', None) or {}
    names = []
    for tier in tiers:
        if tier in choices:
            names.extend(choices[tier].keys())
        elif any(tier in bucket for bucket in choices.values()):
            names.append(tier)          # the row named a species directly (the mount rows do)
    return names


def _pick_species(character, row, curated):
    """Curated pool if the archetype supplied one, else the tier ladder on its own draw."""
    if curated:
        available = [name for name in curated if _find_species(character, name)]
        if available:
            return random.choice(available), _kind_of(character, available[0]), False
        # #38: fall back to the standard pool, but say so.
        pass

    tiers = row.get('species_pool') or []
    if tiers == ['normal', 'plant', 'vermin']:
        draw = random.randint(1, 100)
        tier = next(name for threshold, name in SPECIES_TIERS if draw <= threshold)
        pool = _standard_pool(character, [tier])
        if pool:
            return random.choice(pool), tier, bool(curated)
    pool = _standard_pool(character, tiers)
    if not pool:
        return None, None, bool(curated)
    chosen = random.choice(pool)
    return chosen, _kind_of(character, chosen), bool(curated)


def _find_species(character, name):
    choices = getattr(character, 'animal_choices', None) or {}
    for bucket in choices.values():
        if name in bucket:
            return bucket[name]
    return None


def _kind_of(character, name):
    choices = getattr(character, 'animal_choices', None) or {}
    for tier, bucket in choices.items():
        if name in bucket:
            return tier
    return None


def _chassis(character, effective_level):
    table = getattr(character, 'animal_companion', None) or {}
    rows = table.get('companion', {})
    return rows.get(str(effective_level)) or rows.get(str(max(1, effective_level)))


def resolve_bonded_creatures(character):
    """Every bonded creature this character has, as a list of entries. Also the absences."""
    entries = []
    character.bond_outcomes = {}          # grantor -> outcome, read by domain_inquisition.py
    character_level = sum(c['level'] for c in getattr(character, 'classes', [])) or 0

    for row in _rows(character):
        grantor = row['grantor']
        conditional = row.get('conditional') or {}

        if row.get('source') == 'spheres_of_might_talent':
            talents = getattr(character, 'chooseable_talents', []) or []
            if conditional.get('talent') and conditional['talent'] not in talents:
                continue
            level = character_level
        else:
            entry = class_entry_for(character, grantor)
            if entry is None:
                continue
            level = entry['level']

        if level < row['level_gained']:
            continue                       # D6: nothing at all, no clamp to level 1

        if 'bloodline' in conditional:
            rolled = str(getattr(character, 'chosen_bloodline', '') or '').lower()
            if conditional['bloodline'] not in rolled:
                continue

        archetype_name, effects, record = _archetype_effects(character, grantor)

        choice = row.get('choice')

        if 'removes' in effects:
            # WHAT was removed decides whether anything survives. A bond that IS a choice has two
            # sides, and an archetype can forbid the creature while leaving the other side intact --
            # a blight druid "may not bond with an animal companion, but may ... select from the
            # Darkness, Death, and Destruction domains". Collapsing every `removes` to
            # `archetype_removed` gave those druids NEITHER a companion nor a domain, silently
            # deleting the whole class feature. `removes_scope` is authored per archetype in
            # companion_archetypes_overrides.json; see the builder for why `feature` is the default.
            scope = record.get('removes_scope') or 'feature'
            outcome = choice['on_loss'] if (choice and scope == 'creature') else 'archetype_removed'
            character.bond_outcomes[grantor] = outcome
            entries.append(_entry(row, grantor, None, None, None, None,
                                  outcome=outcome, archetype=archetype_name,
                                  effective_level=0))
            continue

        outcome = 'granted'
        if choice and 'forces' not in effects:
            if random.randint(1, 100) > choice['odds']:
                outcome = choice['on_loss']
        character.bond_outcomes[grantor] = outcome
        if outcome != 'granted':
            entries.append(_entry(row, grantor, None, None, None, None,
                                  outcome=outcome, archetype=archetype_name,
                                  effective_level=0))
            continue

        if row.get('species_data'):
            # The row is real; the species list it needs has not been authored yet.
            continue

        effective = _effective_level(row['effective_level'], level, character,
                                     row.get('minimum'))
        if effective <= 0:
            continue

        curated = record.get('species_pool') if 'species_pool' in effects else None
        species, kind, fell_back = _pick_species(character, row, curated)
        if species is None:
            continue

        entry = _entry(row, grantor, species, kind, _find_species(character, species),
                       _chassis(character, min(effective, character_level or effective)),
                       outcome='granted', archetype=archetype_name,
                       effective_level=effective)
        if fell_back:
            entry['flags'].append('species_pool_unavailable')
        if 'progression' in effects:
            # Handed to #31's merge, which can veto individual fields of the advancement block.
            entry['progression_override'] = record.get('progression') or {'source': archetype_name}
        entries.append(entry)

    entries = _stack(character, entries, character_level)
    character.bonded_creatures = entries

    companions = [e for e in entries if e['type'] == 'companion' and e['species']]
    if companions:
        register_bonded_creature_prereqs(character)
        first = companions[0]
        # Back-compat: the existing payload and the `companion` flag read these.
        character.chosen_animal = first['species']
        character.chosen_animal_kind = first['kind']
        character.chosen_animal_description = first['species_stats']
        character.companion_info = first['chassis']
    return entries


def _entry(row, grantor, species, kind, stats, chassis, outcome, archetype, effective_level):
    return {
        'type': row['creature_type'],
        'grantor': grantor,
        'effective_level': effective_level,
        'species': species,
        'kind': kind,
        'species_stats': stats,
        'chassis': chassis,
        'feats': [],
        'outcome': outcome,
        'archetype': archetype,
        'flags': [],
        'contributors': [grantor] if species else [],
    }


def _stack(character, entries, character_level):
    """Multiple sources of the SAME creature type stack, capped at character level (D6).

    Absence entries never merge -- each explains one grantor's outcome and they can legitimately
    coexist with a granted creature of the same type (a druid's companion beside a ranger who
    chose bond with allies).

    THE CHASSIS IS RE-READ HERE, AND MUST BE. Each entry's chassis was fetched at that row's OWN
    pre-stack effective level, because stacking has not happened yet when the entry is built. A
    druid 5 / ranger 7 stacks to effective level 9; leaving the level-5 chassis in place gives the
    companion HD 5 instead of 8 and 3 feats instead of 4, and `animal_feats` then draws from the
    stale row too. Caught by the #30 stack review -- it had no test because the goldens never
    rolled a companion at all.
    """
    granted, out, seen = {}, [], []
    for entry in entries:
        if not entry['species']:
            out.append(entry)
            continue
        key = entry['type']
        if key in granted:
            primary = granted[key]
            primary['effective_level'] += entry['effective_level']
            primary['contributors'].append(entry['grantor'])
        else:
            granted[key] = entry
            seen.append(entry)
    for entry in seen:
        if character_level:
            entry['effective_level'] = min(entry['effective_level'], character_level)
        entry['chassis'] = _chassis(character, entry['effective_level'])
        out.append(entry)
    return out


def animal_chooser(character):
    """Back-compat shim: the resolver is the single path now."""
    resolve_bonded_creatures(character)
    return getattr(character, 'chosen_animal', None)


def animal_feats(character):
    """The companion's feats -- the chassis row's own `feats` count, not the PC formula.

    Replaces a loop that advanced its index only on a NEW draw, indexed an 18-entry list without a
    guard, and never reached its own break. It also gated on `druid`, which the resolver has just
    made wrong.
    """
    entries = [e for e in getattr(character, 'bonded_creatures', []) or []
               if e['type'] == 'companion' and e['species']]
    if not entries:
        return None
    pool = list((getattr(character, 'animal_companion', None) or {}).get('feats') or [])
    if not pool:
        return None

    chosen = set()
    for entry in entries:
        want = int((entry.get('chassis') or {}).get('feats') or 0)
        want = min(want, len(pool))
        picks = set()
        while len(picks) < want:
            picks.add(random.choice(pool))
        entry['feats'] = sorted(picks)
        chosen |= picks
    return chosen
