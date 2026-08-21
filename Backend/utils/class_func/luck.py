"""The inherent-luck subsystem: luck score, luck types, the E-Kat economy, and the Vault.

Authority is Sieg's Guide's Luck sub-doc, extracted to ``oks/pathfinder/house-rules/luck.md``.
Per the docs doctrine, **this module owns every number in the system** -- the spec paragraph in
``docs/feature_spec_todo.md`` names these symbols rather than restating them, because a prose
sentence saying "luck caps at +25" decays the moment someone edits a constant.

WHAT LUCK IS
------------
Luck is **bought**, not rolled. The Doc's primary currency is point-buy attribute points, which this
generator does not have -- it rolls stats (``stats.roll_stats``). The two currencies that do exist
here are level-up attribute bumps (1:1) and skill ranks / HP (5:1), and the ruling (ticket 03) is to
use all three that exist, weighted, with skill ranks as the workhorse.

Luck also runs **negative**, and the Doc pays you for it: *"an additional attribute point for -5
luck"*, *"2 hit points or skill points for -1 luck"*, *"a feat for -5 luck"*. Note the spread against
the buy side -- buying costs 5 HP per +1, selling returns 2 HP per -1. The exchange is deliberately
lossy, which is what stops it being a free-money loop, and the gate asserts the asymmetry holds.

THE THREE TYPES
---------------
*"Three Types of luck may be selected: Default, Proximity, and Dimorphic."* Negative Luck is a
**sign on the score**, not a fourth selectable type -- the bundle leaf originally said otherwise and
was corrected against the Doc.

    Default     works by the standard rules; applies to percentile rolls about yourself, and
                doubles as the daily DR pool.
    Proximity   applies luck to those AROUND you, excluding yourself. Same costs and caps.
    Dimorphic   "chaos" -- inherently holds Negative, Default and Proximity at EQUAL values, each
                capped at 40. Doubles E-Kat acquisition and unlocks Twist Fate.

All three values are stored on every character so the shape is uniform for both gate layers and both
renderers; a Default character simply has the other two at zero. A sometimes-scalar/sometimes-triple
field would make every consumer branch.

WHY THE PURCHASE IS SPLIT ACROSS TWO PHASES
-------------------------------------------
``phase_luck_stake`` runs early and decides *intent* -- type, direction, magnitude, and how many feat
slots a seller is owed. It cannot do the spending, because the pools it spends from have not been
allocated yet. So each pool deducts at its own site, where it knows its real size, clamps against
its own house-rule floor, and records what it ACTUALLY paid via ``settle``.

That is deliberate rather than convenient. ``test_house_invariants`` already asserts the 2->4 rank
floor, the 3-ranks-per-level cap and the full-HP house rule; a luck spend that quietly violated any
of them would put the two gate layers in conflict. A *declared* deduction that each pool clamps for
itself keeps every existing invariant true, and lets ticket 06 assert the stronger property: the
luck gained equals the budget that actually left.

``phase_luck_resolution`` then runs late -- after the feat tax and swap pass, because a swap can
remove an E-Kat feat after the fact -- and turns the settled stake plus the feats actually held into
the final score.
"""
import random

# --- Caps -------------------------------------------------------------------------------------
# "The positive cap for luck is +25 and the negative cap is -50."
LUCK_CAP_POSITIVE = 25
LUCK_CAP_NEGATIVE = -50
# "Dimorphic luck is chaos... each value is equal and has a natural cap of 40." Read as replacing
# the positive cap only; the Doc states no separate Dimorphic floor, so -50 still applies.
LUCK_CAP_DIMORPHIC = 40
# Expanded Luck trait: "Your luck cap is increased by +5. You may take this trait additional times."
EXPANDED_LUCK_CAP_STEP = 5

# --- The mod ----------------------------------------------------------------------------------
# "Luck Mod = Luck Score / 5". The Doc gives no rounding direction; the table ruling is FLOOR, to
# match PF1's own ability-modifier math (Str 7 -> -2, not -1) and every other rounding decision in
# this codebase. It matters more than it looks: Twist Fate is usable luck_mod times per day.
LUCK_MOD_DIVISOR = 5

# --- Buying luck ------------------------------------------------------------------------------
# Doc rates. Point buy does not exist in this generator; the other two do.
BUY_LEVEL_UP_POINTS_PER_LUCK = 1
BUY_SKILL_RANKS_PER_LUCK = 5
BUY_HP_PER_LUCK = 5

# --- Selling luck (negative) ------------------------------------------------------------------
SELL_HP_PER_LUCK = 2
SELL_SKILL_POINTS_PER_LUCK = 2
SELL_LUCK_PER_ATTRIBUTE_POINT = 5
SELL_LUCK_PER_FEAT = 5

# --- Who has a stake, and how big ---------------------------------------------------------------
# Ticket 03's ruling: a minority buys, but buys meaningfully. Luck reads as a character trait some
# people have rather than background noise, and when present the mod is actually non-zero -- a score
# under 5 floors to a mod of 0 and is mechanically silent.
LUCK_PROPENSITY = 0.25
LUCK_SELL_SHARE = 0.25
LUCK_MAGNITUDE_BASE = 2
LUCK_MAGNITUDE_LEVEL_DIVISOR = 2

# --- How deep a seller sells --------------------------------------------------------------------
# THE TWO SIDES ARE NOT SYMMETRIC, and they used to be. Buying is bounded by what the character can
# afford: every point costs 5 skill ranks or 5 HP out of pools that a low-level character barely
# has, so `LUCK_MAGNITUDE_BASE + level // 2` is a fair ceiling on *intent*. Selling is bounded by
# nothing -- it PAYS you -- so the same formula capped a level-20 seller at -12 and made most of the
# system unreachable: the ten negative Luck Traits are written against floors from -10 to -50
# (`requires_luck_at_most` in luck_traits.json), so nine of them could never be bought by anyone.
#
# The ruling is that ANY character can sell all the way to LUCK_CAP_NEGATIVE, with depth weighted by
# level: a 20th-level character hits the deep end often, a 1st-level one rarely but really can. A
# triangular draw expresses exactly that -- full range at every level, mode sliding with level --
# and `random.triangular` uses the same seeded global `random` as everything else here, so a
# replayed seed still reproduces the draw.
#
# Deliberately NOT clamped by what the pools can pay. A 1st-level character that sells -50 is
# entitled to the whole payout -- ten feats, or a hundred HP, or a hundred skill points, or a mix --
# because `_plan_payout` spends the magnitude DOWN across routes, so it is ten feats *or* a hundred
# HP, never both. That is the sacrifice being crippled is supposed to buy.
SELL_MAGNITUDE_MIN = 1
SELL_MAGNITUDE_LEVEL_SPAN = 20   # level at which the mode reaches the floor


def sell_magnitude(level):
    """How much luck this seller gives up: 1..50 at every level, biased deep by level.

    The mode rises linearly from ``SELL_MAGNITUDE_MIN`` at level 0 to the full negative cap at
    ``SELL_MAGNITUDE_LEVEL_SPAN``, and is held inside the range for levels beyond it. Returns a
    POSITIVE magnitude; the caller applies the sign.
    """
    depth = abs(LUCK_CAP_NEGATIVE)
    ratio = min(1.0, max(0.0, level / SELL_MAGNITUDE_LEVEL_SPAN))
    mode = SELL_MAGNITUDE_MIN + (depth - SELL_MAGNITUDE_MIN) * ratio
    return max(SELL_MAGNITUDE_MIN,
               min(depth, int(round(random.triangular(SELL_MAGNITUDE_MIN, depth, mode)))))

LUCK_TYPES = ('Default', 'Proximity', 'Dimorphic')
LUCK_TYPE_WEIGHTS = {'Default': 0.80, 'Proximity': 0.15, 'Dimorphic': 0.05}

# --- Which pool pays --------------------------------------------------------------------------
CURRENCY_SKILL_RANKS = 'skill_ranks'
CURRENCY_HP = 'hp'
CURRENCY_LEVEL_UP_POINTS = 'level_up_points'
# Skill ranks as the workhorse keeps level-up bumps almost always intact -- a permanent -1 to an
# ability score for +0.2 luck mod is the worst trade on the board, so it is the rarest draw.
LUCK_CURRENCY_WEIGHTS = {
    CURRENCY_SKILL_RANKS: 0.60,
    CURRENCY_HP: 0.30,
    CURRENCY_LEVEL_UP_POINTS: 0.10,
}
# The sell side reuses the same shape, splitting the 10% attribute branch evenly between the two
# things -5 luck buys, so the weighting traces back to one ruling instead of inventing a second.
PAYOUT_HP = 'hp'
PAYOUT_SKILL_POINTS = 'skill_points'
PAYOUT_ATTRIBUTE_POINTS = 'attribute_points'
PAYOUT_FEATS = 'feats'
LUCK_PAYOUT_WEIGHTS = {
    PAYOUT_SKILL_POINTS: 0.60,
    PAYOUT_HP: 0.30,
    PAYOUT_ATTRIBUTE_POINTS: 0.05,
    PAYOUT_FEATS: 0.05,
}

# Per-pool ceilings, applied where the pool is spent (see ``settle``). No single budget gets gutted:
# a character can lose a quarter of its skill ranks or HP to luck, and at most one level-up bump.
MAX_LEVEL_UP_POINTS_SPENT = 1
MAX_POOL_SHARE_SPENT = 0.25

# --- The Vault --------------------------------------------------------------------------------
# Twist Fate: "Roll 1d100 and add any amount from your Luck Vault up to 77." Big Savings trait:
# "Increase Vaulted Interest Limit Cap by 77." The Doc states no separate base, so the 77 the twist
# can draw is the base cap. Generated characters start with an empty vault -- it banks in play,
# one point per luck check landing below 0.
VAULT_CAP_BASE = 77
BIG_SAVINGS_VAULT_STEP = 77
VAULT_STARTING_BALANCE = 0

# --- The E-Kat economy ------------------------------------------------------------------------
# "You cannot store more than 99 E-Kats." A STORAGE cap: it bounds what a character carries into
# play, not what the creation formula may compute (those points "must be spent").
E_KAT_STORE_CAP = 99
E_KAT_PER_FEAT = 5
# The two per-level acquisition terms are each gated on the feat that produces that kind of E-Kat,
# and Double Down doubles the RATE of both. Named here rather than spelled inline so a rename in
# e_kat_feats.json breaks loudly.
FEAT_LONG_REST = 'Sweet Dreams'      # gates the Long Rest term
FEAT_DISCOVERY = 'Stream of Luck'    # gates the Discovery term
FEAT_DOUBLE_DOWN = 'Double Down'     # doubles both rates; never the feats x 5 term
# "You can opt to start with 50 if you do not wish to spend and would have that much total or more
# otherwise." Never taken by the generator -- it always computes, and the opt-out is only offered
# when the computed total already exceeds it, so it is never the better deal. Recorded so nobody
# re-derives it from the Doc.
E_KAT_FLAT_ALTERNATIVE = 50

# --- Luck Traits ------------------------------------------------------------------------------
# "25 Permanent E-Kats can be used to purchase a Luck Trait." And, decisively:
# "Luck Traits may only be purchased with E-Kats. These Traits do not grant 1 extra luck."
#
# That second sentence is why Luck Traits are NOT in data/traits.csv and are never drawn by
# trait_selector -- an earlier pass put Expanded Luck and Big Savings there, which made them
# ordinary character traits the rules do not allow them to be. It is also an explicit no-double-count
# rule, the mirror of the feats': a Luck Trait never collects the generic +1 Luck. Only
# *Increase Luck* moves the score at all, by its own stated +1 per stack.
LUCK_TRAIT_COST = 25
# "E-Kat Exchange: Enhanced Luck Storage -- +100 max E-Kats", repeatable.
ENHANCED_STORAGE_STEP = 100
TRAIT_CATEGORY_STANDARD = 'standard'
TRAIT_CATEGORY_NEGATIVE = 'negative'
TRAIT_CATEGORY_DIMORPHIC = 'dimorphic'

# Every positive luck-based feat grants +1 Luck, EXCEPT those that state a larger explicit bonus.
# The no-double-count rule is the one ticket 06 asserts by name.
GENERIC_LUCK_FEAT_BONUS = 1

# --- Reserved E-Kat feat slots ------------------------------------------------------------------
# E-Kat feats do NOT join the general pool -- they would crowd out ordinary feats on every character
# and, worse, leak into the shared ``chooseable_talents`` accumulator that later choosers draw from.
# Instead a character with a luck stake gets slots CARVED OUT of its existing feat budget, the same
# way path_of_war / spheres / professions reserve theirs before phase_feat_selection spends the rest.
#
# The scale is what makes Luck God reachable at all: it requires the other nine, so a character needs
# ten E-Kat slots before it can ever be drawn. At one slot per four levels it arrives around level 36
# -- legendary rather than impossible, which is the intent. Below that the chains still complete
# (Lucky Boy -> Very Lucky Boy, Ass Pull -> It Just Works) and the gate's census sees every path.
E_KAT_SLOTS_BASE = 1
E_KAT_SLOTS_LEVEL_DIVISOR = 4
# Once a chain is started, prefer continuing it -- a character with Lucky Boy and no Very Lucky Boy
# reads as unfinished. Applied only when a chain continuation is actually eligible.
E_KAT_CHAIN_BIAS = 0.7


def e_kat_slots(level, pool_size):
    """Reserved E-Kat feat slots for a character that has a luck stake."""
    return min(pool_size, E_KAT_SLOTS_BASE + level // E_KAT_SLOTS_LEVEL_DIVISOR)


def luck_mod(score):
    """Luck Score / 5, floored toward -infinity.

    Python's ``//`` already floors toward -infinity for negatives (-12 // 5 == -3), which is the
    ruling. Written as one function so the rounding direction lives in exactly one place and the
    behaviour gate can assert ``mod == luck_mod(score)`` against the same symbol the pipeline used.
    """
    return score // LUCK_MOD_DIVISOR


def luck_cap(luck_type, expanded_luck_stacks=0):
    """The positive ceiling for a character: 25, or 40 for Dimorphic, +5 per Expanded Luck stack."""
    base = LUCK_CAP_DIMORPHIC if luck_type == 'Dimorphic' else LUCK_CAP_POSITIVE
    return base + EXPANDED_LUCK_CAP_STEP * expanded_luck_stacks


def luck_floor(luck_type):
    """The negative floor. The Doc states one value and does not vary it by type."""
    return LUCK_CAP_NEGATIVE


def clamp_luck(score, luck_type, expanded_luck_stacks=0):
    """Hold a score inside its caps. Enforced at write time so nothing downstream can drift out."""
    return max(luck_floor(luck_type), min(luck_cap(luck_type, expanded_luck_stacks), score))


def vault_cap(big_savings_stacks=0):
    return VAULT_CAP_BASE + BIG_SAVINGS_VAULT_STEP * big_savings_stacks


def twist_fate_per_day(score):
    """"A number of times per day equal to your Luck Mod: (Luck Score/5), you may twist fate."

    Doc-native to Dimorphic, but the count is a pure function of the mod; the caller decides who
    gets to use it. Negative mods give zero uses rather than negative ones.
    """
    return max(0, luck_mod(score))


def dr_pool(score):
    """Luck doubles as a daily DR pool -- the Doc's worked example spends 11 of Gary's 20 luck to
    reduce 11 damage to 0. Negative luck grants no pool."""
    return max(0, score)


def e_kat_reserve(level, held_feats, dimorphic=False):
    """The E-Kats a character has EARNED by creation, before any of it is spent.

    The Doc's formula, verbatim:

        "Level*Long Rest E-Kats(1, 2 if Double Down)+Level*Discovery E-Kats(1, 2 if Double
         Down)+E-Kat feats*5"        (doubled if Dimorphic)

    **Each per-level term is gated on the feat that produces that kind of E-Kat**, and Double Down
    doubles the rate of both:

        long_rest = 2 if Double Down else 1,  but only with Sweet Dreams   (else 0)
        discovery = 2 if Double Down else 1,  but only with Stream of Luck (else 0)
        earned    = level x long_rest + level x discovery + (n_feats x 5)  ... x2 if Dimorphic

    "Long Rest E-Kats" and "Discovery E-Kats" are never defined anywhere in the Doc, so this is a
    table ruling rather than a reading -- confirmed against worked examples from the table:
    L10 Sweet Dreams + Lucky Boy = 10 + 0 + 10 = 20; L10 Sweet Dreams + Stream of Luck = 30; adding
    Double Down = 2x(10+10) + 15 = 55, and 110 if Dimorphic; L20 with all ten feats = 2x(20+20) + 50
    = 130, and 260 if Dimorphic.

    Note Double Down doubles only the two LEVEL terms. The ``n_feats x 5`` term is never doubled by
    it -- 55 rather than 59 in the third example above is what pins that down.

    **No E-Kat feats earns zero.** The first implementation gave every character ``level x 2``
    regardless, which handed a 20th-level character with no involvement in the luck system 40
    E-Kats -- enough, once the trait economy landed, to buy a Luck Trait free.

    **No 99 cap here.** "You cannot store more than 99 E-Kats" governs STORAGE, and these points
    "must be spent" -- they pass through rather than being held. The cap applies to the remainder
    that is actually carried; see ``carried_e_kats``.
    """
    names = {str(f) for f in (held_feats or [])}
    if not names:
        return 0
    # Double Down doubles the RATE of both per-level terms -- it is not a gate for one of them, and
    # it never touches the feats x 5 term.
    rate = 2 if FEAT_DOUBLE_DOWN in names else 1
    long_rest = rate if FEAT_LONG_REST in names else 0
    discovery = rate if FEAT_DISCOVERY in names else 0
    reserve = level * long_rest + level * discovery + len(names) * E_KAT_PER_FEAT
    if dimorphic:
        reserve *= 2
    return reserve


def luck_traits_afforded(earned):
    """How many Luck Traits a starting reserve buys. "25 Permanent E-Kats can be used to purchase a
    Luck Trait", and "These points must be spent" -- so the reserve is a creation-time budget, not a
    bank. Whatever is left over is under one trait's price by definition."""
    return max(0, earned) // LUCK_TRAIT_COST


def carried_e_kats(earned, traits_bought, enhanced_storage_stacks=0):
    """What the character actually carries into play, after buying traits and under the store cap.

    This is the only place the 99 applies. *E-Kat Exchange: Enhanced Luck Storage* raises it by 100
    per stack, which is the trait's whole purpose and only has one if the cap can bind."""
    remainder = max(0, earned - traits_bought * LUCK_TRAIT_COST)
    return min(e_kat_store_cap(enhanced_storage_stacks), remainder)


def e_kat_store_cap(enhanced_storage_stacks=0):
    return E_KAT_STORE_CAP + ENHANCED_STORAGE_STEP * enhanced_storage_stacks


def _weighted_choice(weights):
    """Pick a key from a {key: weight} mapping. Uses the process-global ``random`` the rest of the
    generator seeds, so a replayed seed reproduces the draw."""
    keys = list(weights)
    return random.choices(keys, weights=[weights[k] for k in keys], k=1)[0]


def roll_luck_type():
    return _weighted_choice(LUCK_TYPE_WEIGHTS)


def plan_stake(level, direction=None):
    """Decide this character's *intent* toward luck, before any pool has been allocated.

    Returns ``None`` for the ~75% with no stake at all, else a dict carrying the type, the direction,
    the target magnitude, the per-currency request, and -- for sellers -- the payout including bonus
    feat slots. Nothing is spent here; ``settle`` records what each pool actually paid.

    ``direction`` ('buy' / 'sell') forces the branch and guarantees a stake, bypassing BOTH rolls.
    It exists because the only way to see the negative side used to be hand-editing LUCK_PROPENSITY
    and LUCK_SELL_SHARE in this file -- two live constants that then had to be remembered before
    shipping. It is an optional debug input, defaulted off; normal generation never passes it.
    """
    forced = str(direction).lower() if direction else None
    if forced not in ('buy', 'sell'):
        forced = None
    if forced is None and random.random() >= LUCK_PROPENSITY:
        return None

    selling = forced == 'sell' if forced else random.random() < LUCK_SELL_SHARE
    # The sell side runs its own scale all the way to the negative cap -- see sell_magnitude.
    magnitude = (sell_magnitude(level) if selling
                 else random.randint(1, LUCK_MAGNITUDE_BASE + level // LUCK_MAGNITUDE_LEVEL_DIVISOR))
    stake = {
        'luck_type': roll_luck_type(),
        'direction': 'sell' if selling else 'buy',
        'target': -magnitude if selling else magnitude,
        'requested': {},
        'paid': {},
        'payout': {},
        'bonus_feat_slots': 0,
    }

    if selling:
        _plan_payout(stake, magnitude)
    else:
        _plan_spend(stake, magnitude)
    return stake


def _plan_spend(stake, magnitude):
    """Split the luck target across the three currencies that exist here, one point at a time."""
    points = {CURRENCY_SKILL_RANKS: 0, CURRENCY_HP: 0, CURRENCY_LEVEL_UP_POINTS: 0}
    for _ in range(magnitude):
        points[_weighted_choice(LUCK_CURRENCY_WEIGHTS)] += 1
    # A level-up bump is 1:1 and the other two are 5:1, so the ceiling bites here rather than at the
    # spend site -- overflow past MAX_LEVEL_UP_POINTS_SPENT falls back to skill ranks.
    overflow = max(0, points[CURRENCY_LEVEL_UP_POINTS] - MAX_LEVEL_UP_POINTS_SPENT)
    points[CURRENCY_LEVEL_UP_POINTS] -= overflow
    points[CURRENCY_SKILL_RANKS] += overflow
    stake['luck_points'] = points
    stake['requested'] = {
        CURRENCY_SKILL_RANKS: points[CURRENCY_SKILL_RANKS] * BUY_SKILL_RANKS_PER_LUCK,
        CURRENCY_HP: points[CURRENCY_HP] * BUY_HP_PER_LUCK,
        CURRENCY_LEVEL_UP_POINTS: points[CURRENCY_LEVEL_UP_POINTS] * BUY_LEVEL_UP_POINTS_PER_LUCK,
    }


def _plan_payout(stake, magnitude):
    """Spend negative luck on the Doc's four payout routes. Attribute points and feats cost 5 luck
    each, so a route drawn with fewer than 5 luck left falls through to the 1-luck routes."""
    payout = {PAYOUT_HP: 0, PAYOUT_SKILL_POINTS: 0, PAYOUT_ATTRIBUTE_POINTS: 0, PAYOUT_FEATS: 0}
    remaining = magnitude
    while remaining > 0:
        route = _weighted_choice(LUCK_PAYOUT_WEIGHTS)
        if route == PAYOUT_ATTRIBUTE_POINTS and remaining >= SELL_LUCK_PER_ATTRIBUTE_POINT:
            payout[PAYOUT_ATTRIBUTE_POINTS] += 1
            remaining -= SELL_LUCK_PER_ATTRIBUTE_POINT
        elif route == PAYOUT_FEATS and remaining >= SELL_LUCK_PER_FEAT:
            payout[PAYOUT_FEATS] += 1
            remaining -= SELL_LUCK_PER_FEAT
        elif route == PAYOUT_HP:
            payout[PAYOUT_HP] += SELL_HP_PER_LUCK
            remaining -= 1
        else:
            payout[PAYOUT_SKILL_POINTS] += SELL_SKILL_POINTS_PER_LUCK
            remaining -= 1
    stake['payout'] = payout
    stake['bonus_feat_slots'] = payout[PAYOUT_FEATS]


def settle(stake, currency, available):
    """How many units of ``currency`` this pool actually hands over, recorded on the stake.

    Called from the pool's own allocation site, which is the only place that knows the real budget.
    Clamps to MAX_POOL_SHARE_SPENT so no single budget is gutted, and records the result so
    ``resolve_purchased_luck`` can credit only the luck that was genuinely paid for -- the property
    ticket 06 asserts as "the purchase balances and the source budget actually shrank".
    """
    if not stake or stake['direction'] != 'buy':
        return 0
    requested = stake['requested'].get(currency, 0)
    if requested <= 0 or available <= 0:
        stake['paid'][currency] = 0
        return 0
    ceiling = available if currency == CURRENCY_LEVEL_UP_POINTS else int(available * MAX_POOL_SHARE_SPENT)
    paid = max(0, min(requested, ceiling))
    stake['paid'][currency] = paid
    return paid


def payout(stake, route):
    """What a seller receives from one payout route. Zero for buyers and for characters with no
    stake, so every pool's call site is an unconditional one-liner rather than a nested branch."""
    if not stake or stake['direction'] != 'sell':
        return 0
    return stake.get('payout', {}).get(route, 0)


# --- Where a seller's attribute points land -----------------------------------------------------
# The payout is delivered as pf1 ability-score CHANGES rather than folded into the level-up bumps,
# so each point has to name an ability. The table ruling: the character's main stat is half the
# draw, the other five split the rest evenly -- 5/10 and 1/10 each, which sums to exactly 1. That
# concentrates the payout where the character actually plays while still letting an odd point land
# anywhere, and it keeps the weighting in one named constant instead of inline in the roller.
ATTRIBUTE_PAYOUT_MAIN_WEIGHT = 5
ATTRIBUTE_PAYOUT_OTHER_WEIGHT = 1
ABILITIES = ('str', 'dex', 'con', 'int', 'wis', 'cha')


def roll_attribute_payout(points, main_stat):
    """Spread `points` attribute bumps across the six abilities, main-stat weighted.

    Returns {ability: bumps} with zero-count abilities omitted, so a caller can emit one pf1 change
    per entry. Rolled one point at a time -- two points can land on the same ability (a +2) or on
    two different ones, which is what a per-point draw means.
    """
    if not points or points <= 0:
        return {}
    main = str(main_stat or '').lower()
    weights = {a: (ATTRIBUTE_PAYOUT_MAIN_WEIGHT if a == main else ATTRIBUTE_PAYOUT_OTHER_WEIGHT)
               for a in ABILITIES}
    out = {}
    for _ in range(points):
        pick = random.choices(ABILITIES, weights=[weights[a] for a in ABILITIES], k=1)[0]
        out[pick] = out.get(pick, 0) + 1
    return out


def sell_cost(route, amount):
    """How much LUCK a payout route cost, inverting the Doc's own rates.

    The stake records what the sale bought; this says what each purchase was paid for in luck, so
    the rows sum back to the magnitude sold and the sheet can be checked against the score by eye.
    Inverted here rather than in the renderer because these four rates are this module's to own --
    a renderer that hard-coded "HP / 2" would silently disagree the day a rate changed.

        2 HP per -1 luck      ->  luck = hp // 2
        2 skill points per -1 ->  luck = points // 2
        an attribute point for -5 luck
        a feat for -5 luck
    """
    amount = int(amount or 0)
    if amount <= 0:
        return 0
    if route == PAYOUT_HP:
        return amount // SELL_HP_PER_LUCK
    if route == PAYOUT_SKILL_POINTS:
        return amount // SELL_SKILL_POINTS_PER_LUCK
    if route == PAYOUT_ATTRIBUTE_POINTS:
        return amount * SELL_LUCK_PER_ATTRIBUTE_POINT
    if route == PAYOUT_FEATS:
        return amount * SELL_LUCK_PER_FEAT
    return 0


# The audit's pool names are the BUDGETS that move; the stake's payout keys are what the Doc sells.
# They differ for one of the four (`skill_ranks` vs `skill_points`), so the mapping is named rather
# than assumed equal.
AUDIT_POOL_TO_PAYOUT = {
    'hp': PAYOUT_HP,
    'skill_ranks': PAYOUT_SKILL_POINTS,
    'attribute_points': PAYOUT_ATTRIBUTE_POINTS,
    'feats': PAYOUT_FEATS,
}


def record_audit(character, pool, before, spent, received, after):
    """Record what a pool's budget ACTUALLY did across its luck adjustment.

    The luck block already says what the character was *promised* -- "Sold -45 luck for 22 HP, 38
    skill points" -- but that is the plan, read back from the same stake that produced it. It proves
    nothing about whether the HP and skill budgets moved. This records the numbers each pool held on
    either side of its own adjustment, at the only place they exist, so the sheet can show the
    arithmetic instead of asserting the outcome.

    Written on the character rather than returned because the pools are called from three different
    modules at three different points in the pipeline, and the renderer needs all of them together.
    """
    audit = getattr(character, 'luck_audit', None)
    if audit is None:
        audit = {}
        character.luck_audit = audit
    audit[pool] = {'before': int(before), 'spent': int(spent),
                   'received': int(received), 'after': int(after)}


def stake_of(character):
    """The character's luck stake, or None. ``getattr`` because bare test fakes never set it."""
    return getattr(character, 'luck_stake', None)


def resolve_purchased_luck(stake):
    """The luck a settled stake actually earned -- from what was paid, never from what was asked.

    A pool that could not afford its share simply yields less luck, which is why the buy rates are
    applied here rather than trusted from ``plan_stake``.
    """
    if not stake:
        return 0
    if stake['direction'] == 'sell':
        return stake['target']
    paid = stake.get('paid', {})
    return (
        paid.get(CURRENCY_SKILL_RANKS, 0) // BUY_SKILL_RANKS_PER_LUCK
        + paid.get(CURRENCY_HP, 0) // BUY_HP_PER_LUCK
        + paid.get(CURRENCY_LEVEL_UP_POINTS, 0) // BUY_LEVEL_UP_POINTS_PER_LUCK
    )


def typed_values(score, luck_type):
    """Split a score into the three typed values, uniformly for every character.

    Dimorphic holds all three at EQUAL values, which is the Doc's own definition of the state, so
    the score is the value each type carries rather than a total to divide. Default and Proximity
    carry their own and leave the others at zero -- one shape, no consumer has to branch.
    """
    values = {'negative': 0, 'default': 0, 'proximity': 0}
    if luck_type == 'Dimorphic':
        values['negative'] = values['default'] = values['proximity'] = score
    elif luck_type == 'Proximity':
        values['proximity'] = score
    else:
        values['default'] = score
    if score < 0 and luck_type != 'Dimorphic':
        values['negative'] = score
    return values
