"""Mythic Adventures (mythic map). The tier resolver lives here; the path/ability/tradition
choosers join it as the map's tickets land.

THE INPUT IS THE GATE (ticket 02, ruled 2026-08-12): mythic exists on a character only because the
request named it. There is no rarity roll -- the deleted randomize_mythic stub rolled 0.5% and was
untestable by construction -- and no level gate. Absent -> never mythic, and the non-mythic branch
draws NOTHING from the RNG stream, which is what keeps every golden byte-identical and every
replayed seed reproducing.
"""
import json
import random
import re

import pandas as pd

from utils import data as static_data
from utils.class_func.generic_func import levels_for, record_bucket_owner, _record_choice_level
from utils.paths import repo_path

# The rolled form decays toward low tiers (ticket 02 amendment, 2026-08-13): tier 1 is common,
# tier 10 is rare, weight = 11 - tier. Level-banding was rejected -- a level-4 tier-3 character
# is legal by construction. The ticket fixes the shape; this constant owns the numbers.
TIER_ROLL_WEIGHTS = [11 - tier for tier in range(1, 11)]

_TRUEISH = ("TRUE", "Y", "YES", "1")


def resolve_mythic_tier(character):
    """Turn character.mythic_request into a tier on character.mythic_rank.

    None/absent -> 0 (never mythic; no RNG draw). An int (or numeric string) 1-10 -> exactly that
    tier, clamped to the RAW cap of 10. True/'true'/'y' -> one weighted draw off
    TIER_ROLL_WEIGHTS. Anything unrecognized -> 0, deliberately quiet: the request is an API
    input, and a misspelled opt-in must degrade to today's behaviour, not crash a generation.
    """
    request = getattr(character, 'mythic_request', None)
    if request is None or request is False:
        character.mythic_rank = 0
        return 0

    if request is True or str(request).strip().upper() in _TRUEISH:
        tier = random.choices(range(1, 11), weights=TIER_ROLL_WEIGHTS, k=1)[0]
        character.mythic_rank = tier
        return tier

    try:
        tier = int(request)
    except (TypeError, ValueError):
        character.mythic_rank = 0
        return 0
    character.mythic_rank = max(0, min(tier, 10))
    return character.mythic_rank


# ------------------------------------------------------------------------------------------------
# Mythic feats (ticket 04). The corpus already holds all 158 rows (`type == 'Mythic'` in
# data/feats.csv); the normal pipeline's ONLY relationship with them stays exactly what it was --
# remove_mythic() keeps them out of every name-keyed description/prereq extraction, and that filter
# is NOT relaxed for mythic characters: 139 of the 158 share a name with a non-mythic feat (mythic
# Acrobatic IS "Acrobatic", by design), so dropping the filter would let the Mythic row clobber the
# normal row inside dicts keyed by name -- the exact collision companion_feats.py:71 documents.
#
# Instead mythic feats come ONLY through this chooser, which reads the CSV filtered to
# type=='Mythic' at every step and never by bare name, and every granted feat wears a
# "<Name> (Mythic)" display name -- the "(unchained)" precedent -- so no name-keyed lookup anywhere
# downstream can ever collide with the namesake. RAW budget: a separate allowance at tiers
# 1,3,5,7,9, never an ordinary feat slot; the grants are appended AFTER the feat-count guarantee
# the way profession feats are, so the cap neither counts nor trims them.
# ------------------------------------------------------------------------------------------------

# "Nth mythic tier" prereqs (6 rows) are gated HERE, outside the string prereq engine -- that
# engine has a measured 6.1% permanently-unsatisfiable tail and "tier 3+" is exactly the shape
# that lands in it.
_TIER_PREREQ_RE = re.compile(r'(\d+)(?:st|nd|rd|th)\s+mythic\s+tier', re.IGNORECASE)

MYTHIC_FEAT_SUFFIX = ' (Mythic)'

# LOAD-BEARING exclusions, not decoration: the chooser reads this, so an entry here is a feat no
# generated character can draw. Both grant machinery v1 deliberately does not model -- granting
# the feat while not granting what it promises is the "generated but wrong" failure.
V1_EXCLUDED_MYTHIC_FEATS = {
    'dual path':          "v1 walks exactly one path (ticket 03's ruling); the feat grants a second",
    'extra path ability': "the extra pick it grants isn't wired into the ability chooser yet",
}


def mythic_feat_rows():
    """The 158 Mythic rows, and nothing else. Every mythic read filters on type FIRST."""
    data = pd.read_csv(repo_path('data/feats.csv'), sep='|', on_bad_lines='skip')
    return data[data['type'] == 'Mythic']


def _collision_names():
    """Names that ALSO exist as a non-mythic row (139 of the 158). Only those need the display
    suffix -- 'Mythic Paragon' has no namesake to collide with and reads worse as
    'Mythic Paragon (Mythic)'."""
    data = pd.read_csv(repo_path('data/feats.csv'), sep='|', on_bad_lines='skip')
    return {str(n).strip().lower() for n in data[data['type'] != 'Mythic']['name']}


def _namesakes_held(row, chooseable, held_lower):
    """True when every feat in the row's prerequisite_feats column is already held.

    The curated column carries clean names ("Accursed Hex"), unlike the prose `prerequisites`
    field, and membership is tested against character.chooseable -- the same lowercased universe
    every other prereq check in this stack consults."""
    raw = row.get('prerequisite_feats')
    if raw is None or pd.isna(raw) or not str(raw).strip():
        return True
    parts = [p.strip(' .').lower() for p in str(raw).split(',') if p.strip(' .')]
    return all(p in chooseable or p in held_lower for p in parts)


def choose_mythic_feats(character, tier, slot_tiers):
    """Draw one mythic feat per slot tier (RAW: 1,3,5,7,9 -- the schedule owns the list).

    Slots are filled in ascending tier order and each slot judges tier prereqs against ITS OWN
    tier, so a "3rd mythic tier" feat is reachable by the tier-3 slot and not the tier-1 slot.
    Returns [{'name', 'base_name', 'tier', 'description'}, ...]; the caller appends the display
    names to the feat track and registers the descriptions."""
    rows = mythic_feat_rows()
    collisions = _collision_names()
    chooseable = getattr(character, 'chooseable', set()) or set()
    held_lower = set()
    grants = []

    for slot_tier in sorted(slot_tiers):
        pool = []
        for _, row in rows.iterrows():
            base_name = str(row['name']).strip()
            if base_name.lower() in held_lower or base_name.lower() in V1_EXCLUDED_MYTHIC_FEATS:
                continue
            required = _TIER_PREREQ_RE.search(str(row.get('prerequisites') or ''))
            if required and int(required.group(1)) > slot_tier:
                continue
            if not _namesakes_held(row, chooseable, held_lower):
                continue
            pool.append((base_name, row))
        if not pool:
            # The pool can run dry (a tier-1 character who holds few namesakes); under-delivering
            # is the correct behaviour, exactly like a talent pool running dry.
            continue

        base_name, row = random.choice(sorted(pool, key=lambda item: item[0]))
        held_lower.add(base_name.lower())
        display = base_name + MYTHIC_FEAT_SUFFIX if base_name.lower() in collisions else base_name
        benefit = row.get('benefit')
        description = row.get('description')
        text = str(benefit) if benefit is not None and not pd.isna(benefit) else ''
        if not text:
            text = str(description) if description is not None and not pd.isna(description) else ''
        grants.append({'name': display, 'base_name': base_name,
                       'tier': slot_tier, 'description': text})
        # The display name joins the prereq universe (a later mythic feat may chain off it); the
        # namesake is already there or the row would not have been eligible.
        if isinstance(chooseable, set):
            chooseable.add(display.lower())

    return grants


# ------------------------------------------------------------------------------------------------
# The path and its abilities (ticket 03). Data: mythic_path_abilities.json (built by
# scripts/build/build_mythic_path_abilities.py -- six RAW paths, universal merged in, curation
# flags load-bearing); schedule: mythic_schedule.json through the same levels_for() resolver as
# every class bucket, with the TIER passed where a class level would be.
# ------------------------------------------------------------------------------------------------

_PATH_DATA = None
_SCHEDULE = None

PATHS = ('archmage', 'champion', 'guardian', 'hierophant', 'marshal', 'trickster')

# Role-weighted path draw (Daniel, 2026-08-13): every path stays possible, nonsense stays rare.
# Two signal sources, both additive onto a baseline of 1 per path: what the CLASSES are (weighted
# by their level share -- a fighter 11 / wizard 3 leans champion), and, when the optimizer set a
# role, what the ROLE wants. The numbers are draw weights, not rules; tune here.
_CLASS_PATH_WEIGHTS = {
    'arcane':  {'archmage': 4, 'trickster': 1},
    'divine':  {'hierophant': 4, 'champion': 1},
    'bab_H':   {'champion': 3, 'guardian': 2, 'marshal': 1},
    'bab_M':   {'champion': 1, 'guardian': 1, 'marshal': 2, 'trickster': 1},
    'skill':   {'trickster': 3, 'marshal': 1},          # no casting, not full-BAB
}
_ROLE_PATH_BONUS = {
    'striker': 'champion', 'alpha': 'champion', 'sniper': 'trickster',
    'wall': 'guardian', 'juggernaut': 'guardian',
    'controller': 'archmage', 'specialist': 'marshal',
}

# Path-ability prereqs stay OUTSIDE the string prereq engine, like feat tier gates: most are
# prose, but the recurring machine-readable shapes are cheap to honor. Fail-open by design --
# an unparsed clause admits the ability rather than silently shrinking the pool.
_CLASS_FEATURE_PREREQ_RE = re.compile(r'must have the ([a-z\' ]+?) (?:class feature|path ability)')
_CAST_PREREQ_RE = re.compile(r'must be able to cast (arcane|divine|psychic) spells')


def path_ability_data():
    global _PATH_DATA
    if _PATH_DATA is None:
        with open(repo_path('Backend/json/mythic_path_abilities.json'), encoding='utf-8') as fh:
            _PATH_DATA = json.load(fh)
    return _PATH_DATA['paths']


def mythic_schedule():
    global _SCHEDULE
    if _SCHEDULE is None:
        with open(repo_path('Backend/json/mythic_schedule.json'), encoding='utf-8') as fh:
            _SCHEDULE = json.load(fh)
    return _SCHEDULE


def _caster_flags(character):
    divine_casters = getattr(static_data, 'divine_casters')
    is_divine = any(c['name'] in divine_casters for c in character.classes)
    is_arcane = any(c['casting_level_string'] in ('low', 'mid', 'high')
                    and c['name'] not in divine_casters for c in character.classes)
    return is_divine, is_arcane


def path_weights(character):
    """Draw weights over the six paths for THIS character. Deterministic; the draw is not."""
    weights = {p: 1.0 for p in PATHS}
    divine_casters = getattr(static_data, 'divine_casters')
    total_levels = sum(c['level'] for c in character.classes) or 1

    for entry in character.classes:
        share = entry['level'] / total_levels
        bab = str(character.class_data.get(entry['name'], {}).get('bab', 'M'))
        casting = entry.get('casting_level_string', 'none')
        signals = []
        if casting in ('low', 'mid', 'high'):
            signals.append('divine' if entry['name'] in divine_casters else 'arcane')
        if bab == 'H':
            signals.append('bab_H')
        elif bab == 'M':
            signals.append('bab_M')
        if casting == 'none' and bab != 'H':
            signals.append('skill')
        for sig in signals:
            for path, bonus in _CLASS_PATH_WEIGHTS[sig].items():
                weights[path] += bonus * share

    role = getattr(character, 'role', None)
    if role:
        favored = _ROLE_PATH_BONUS.get(str(role.get('name', '')).lower())
        if favored:
            weights[favored] += 2.0
    return weights


def choose_mythic_path(character):
    """One of the six RAW paths, role-weighted (v1 walks exactly one -- Dual/Hard Path are
    recorded not-v1). Also picks the path's tier-1 feature option (Archmage Arcana &c.)."""
    weights = path_weights(character)
    path_key = random.choices(PATHS, weights=[weights[p] for p in PATHS], k=1)[0]
    meta = path_ability_data()[path_key]

    feature_choice = None
    feature = meta.get('tier1_feature') or {}
    options = feature.get('options') or {}
    if options:
        name = random.choice(sorted(options))
        feature_choice = {'feature': feature['name'], 'name': name, **options[name]}
    return path_key, feature_choice


def _ability_prereq_ok(description, character, chosen_lower):
    """The two machine-readable prereq shapes; everything else admits (fail-open, see above)."""
    text = str(description).lower()
    for feature in _CLASS_FEATURE_PREREQ_RE.findall(text):
        token = feature.strip()
        if token in chosen_lower:
            continue
        if token not in (getattr(character, 'chooseable', None) or set()):
            return False
    cast = _CAST_PREREQ_RE.search(text)
    if cast:
        is_divine, is_arcane = _caster_flags(character)
        if cast.group(1) == 'arcane' and not is_arcane:
            return False
        if cast.group(1) == 'divine' and not is_divine:
            return False
        if cast.group(1) == 'psychic':
            return False    # the generator has no psychic-caster flag; conservative here
    return True


def choose_path_abilities(character, path_key, tier):
    """One ability per tier from the path's merged pool, gated per slot (1st/3rd/6th-tier lists),
    flagged entries skipped -- the flag is load-bearing, not decoration.

    Returns [{'name', 'tier', 'type', 'source', 'description', 'universal'}, ...] in slot order."""
    pool = path_ability_data()[path_key]['abilities']
    slot_tiers = levels_for(character, 'mythic', 'Mythic Path Abilities', tier,
                            schedule_attr='mythic_schedule')
    chosen = []
    chosen_lower = set()

    for slot_tier in slot_tiers:
        candidates = [name for name, entry in pool.items()
                      if name.lower() not in chosen_lower
                      and not entry.get('flag')
                      and entry['tier'] <= slot_tier
                      and _ability_prereq_ok(entry['description'], character, chosen_lower)]
        if not candidates:
            break
        name = random.choice(sorted(candidates))
        chosen_lower.add(name.lower())
        chosen.append({'name': name, 'tier': slot_tier, **{
            k: pool[name][k] for k in ('type', 'source', 'description', 'universal')}})
    return chosen


def record_mythic_choices(character, path_key, feature_choice, abilities, tier):
    """Land the path and its picks in data_dict['class features'] + the owner/level side-tables
    both renderers already read -- owner 'mythic', and the stamp is the TIER (rendering a tier
    stamp where every sibling carries a level is ticket 06's line item; this only fixes what the
    stamp IS). A mythic character is on the sheet TODAY through the existing class-features
    path; the namespaced payload block is provenance and chassis, not the only route in."""
    meta = path_ability_data()[path_key]
    features = character.data_dict['class features']

    path_bucket = {}
    display = meta['display']
    blurb = f"Mythic path ({display}); one path ability per tier, mythic feats at tiers 1/3/5/7/9."
    path_bucket[display] = {'benefit': blurb}
    _record_choice_level(character, 'Mythic Path', display, 1)
    if feature_choice:
        entry_name = f"{feature_choice['feature']}: {feature_choice['name']}"
        path_bucket[entry_name] = {'benefit': feature_choice['description']}
        _record_choice_level(character, 'Mythic Path', entry_name, 1)
    capstone = meta.get('capstone')
    if capstone and tier >= 10:
        path_bucket[capstone['name']] = {'benefit': capstone['description']}
        _record_choice_level(character, 'Mythic Path', capstone['name'], 10)
    features.setdefault('Mythic Path', {}).update(path_bucket)
    record_bucket_owner(character, 'Mythic Path', 'mythic')

    if abilities:
        bucket = features.setdefault('Mythic Path Abilities', {})
        for ability in abilities:
            bucket[ability['name']] = {'benefit': ability['description']}
            _record_choice_level(character, 'Mythic Path Abilities', ability['name'],
                                 ability['tier'])
        record_bucket_owner(character, 'Mythic Path Abilities', 'mythic')
