"""Mythic Adventures (mythic map). The tier resolver lives here; the path/ability/tradition
choosers join it as the map's tickets land.

THE INPUT IS THE GATE (ticket 02, ruled 2026-08-12): mythic exists on a character only because the
request named it. There is no rarity roll -- the deleted randomize_mythic stub rolled 0.5% and was
untestable by construction -- and no level gate. Absent -> never mythic, and the non-mythic branch
draws NOTHING from the RNG stream, which is what keeps every golden byte-identical and every
replayed seed reproducing.
"""
import random
import re

import pandas as pd

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
