"""Mythic Adventures (mythic map). The tier resolver lives here; the path/ability/tradition
choosers join it as the map's tickets land.

THE INPUT IS THE GATE (ticket 02, ruled 2026-08-12): mythic exists on a character only because the
request named it. There is no rarity roll -- the deleted randomize_mythic stub rolled 0.5% and was
untestable by construction -- and no level gate. Absent -> never mythic, and the non-mythic branch
draws NOTHING from the RNG stream, which is what keeps every golden byte-identical and every
replayed seed reproducing.
"""
import random

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
