"""The inherent-luck subsystem's DATA and CONSTANTS must be coherent (map: inherent-luck, ticket 06).

    C:/Python310/python.exe Backend/scripts/gates/validate_luck.py

WHY THIS GATE EXISTS
--------------------
Per CLAUDE.md, a hard convention belongs in a validator, not only in a sentence: a stale
`critical: "onCrit"` in a doc silently broke six weapons, and a `MOD_CRITICAL` whitelist fixed it.
A spec paragraph saying "luck caps at +25" decays the moment someone edits a constant.

This is the CONFIG layer. It asserts the data is coherent WITHOUT generating a character -- the
roster of E-Kat feats, their prerequisite chains, the no-double-count rule, the arithmetic
relationships between the constants, and the shape of the payload block. Its partner is the
BEHAVIOUR layer, `check_luck` in scripts/tests/test_house_invariants.py, which generates and
asserts the result.

THE TWO LAYERS DELIBERATELY SHARE NO CODE. The class-choices map proved why: perturbing a schedule
table and re-running the behaviour check PASSED, because the generator reads the same file. A table
can never be its own witness. So this file re-derives what it can from first principles and the Doc,
rather than importing the pipeline's own helpers to check the pipeline.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report  # noqa: E402

from utils.class_func import luck  # noqa: E402
from utils.class_func.feats import (e_kat_feat_table, luck_trait_table, luck_feat_table,  # noqa: E402
                                    e_kat_exchange_rows)
from utils.paths import repo_path  # noqa: E402
from utils.payload import PAYLOAD_KEYS  # noqa: E402

REPORT = Report('validate_luck')

# The roster, transcribed from oks/pathfinder/house-rules/luck.md -- NOT read from the JSON this
# gate is checking. That is the whole point: a roster that reads its own file proves nothing.
# There are TEN. Charting said eleven; ticket 01 corrected it against the Doc, and a search for an
# eleventh will not find one.
DOC_FEATS = {
    'Double Down': [],
    'Stream of Luck': [],
    'Sweet Dreams': ['Stream of Luck'],
    'Lucky Boy': [],
    'Very Lucky Boy': ['Lucky Boy'],
    'Ass Pull': [],
    'It Just Works': ['Ass Pull'],
    'Middle Finger': [],
    'Right of Deferment': [],
    'Luck God': ['Double Down', 'Stream of Luck', 'Sweet Dreams', 'Lucky Boy', 'Very Lucky Boy',
                 'Ass Pull', 'It Just Works', 'Middle Finger', 'Right of Deferment'],
}
# The three feats that state their own Luck bonus and therefore do NOT also collect the generic +1.
DOC_EXPLICIT_LUCK = {'Ass Pull': 4, 'It Just Works': 4, 'Luck God': 4}

# The block phase_luck_resolution emits. Both renderers read these names. Asserted for real by the
# behaviour layer (test_house_invariants.check_luck), which has a generated block to compare against;
# this copy is the DATA layer's declaration of the same contract, and the two are deliberately
# independent so sabotaging one cannot quietly satisfy the other.
BLOCK_KEYS = {'type', 'score', 'values', 'mod', 'cap', 'floor', 'e_kat_earned', 'e_kat_reserve',
              'e_kat_store_cap', 'traits', 'trait_benefits', 'trait_changes', 'vault', 'vault_cap',
              'dr_pool', 'twist_fate_per_day', 'feats', 'luck_feats', 'derivation',
              'negative_feats', 'audit', 'payout_changes', 'attribute_bumps', 'stake'}

# Positive luck feats that are NOT E-Kat feats. "Every positive luck based feat grants a +1 Luck",
# and "every e-kat and hero point feat grant an extra luck point" -- so hero point feats count, as
# do feats whose subject is luck. Transcribed here, not read from the file being checked.
DOC_LUCK_FEATS = {'Blood Of Heroes', "Hero's Fortune", 'Luck Of Heroes',
                  'Defiant Luck', 'Fortunate One', 'Adaptive Fortune'}


def check_roster(table):
    REPORT.check(len(table) == len(DOC_FEATS),
                 f'e_kat_feats.json has {len(table)} feats, the Doc has {len(DOC_FEATS)} -- '
                 f'the count was already wrong once (charting said 11)')
    missing = [n for n in DOC_FEATS if n not in table]
    extra = [n for n in table if n not in DOC_FEATS]
    REPORT.check(not missing, f'E-Kat feats named in the Doc but absent from the table: {missing}')
    REPORT.check(not extra, f'E-Kat feats in the table but not in the Doc: {extra}')


def check_prereqs(table):
    """Every chain must be SATISFIABLE -- the defect that made two of them unreachable."""
    for name, want in DOC_FEATS.items():
        info = table.get(name)
        if info is None:
            continue
        got = info['prerequisites']
        REPORT.check(sorted(got) == sorted(want),
                     f'{name}: prerequisites {got} != the Doc\'s {want}')
        for prereq in got:
            REPORT.check(prereq in table,
                         f'{name} requires {prereq!r}, which is not a feat in the table -- this is '
                         f'the unsatisfiable-tail defect ("Asspull", "All of the above") returning')
    # No cycles: every chain must terminate, or the chooser can never satisfy it.
    for name in table:
        seen, frontier = set(), list(table[name]['prerequisites'])
        while frontier:
            nxt = frontier.pop()
            if nxt in seen:
                break
            seen.add(nxt)
            frontier.extend(table.get(nxt, {}).get('prerequisites', []))
        REPORT.check(name not in seen, f'{name}: prerequisite chain is cyclic ({sorted(seen)})')


def check_effects(table):
    for name, info in table.items():
        effects = info.get('effects')
        if not isinstance(effects, dict):
            REPORT.error(f'{name}: no structured effects block -- the feedback loop cannot be '
                         f'computed from prose, which is why this table exists')
            continue
        # THE NO-DOUBLE-COUNT RULE. A feat granting +4 must not also collect the generic +1.
        REPORT.check(not (effects['luck_bonus'] and effects['grants_generic_luck']),
                     f'{name}: states an explicit +{effects["luck_bonus"]} Luck AND collects the '
                     f'generic +1 -- the Doc says these do not stack')
        want = DOC_EXPLICIT_LUCK.get(name, 0)
        REPORT.check(effects['luck_bonus'] == want,
                     f'{name}: luck_bonus {effects["luck_bonus"]}, the Doc says {want}')
        if not want:
            REPORT.check(effects['grants_generic_luck'],
                         f'{name}: a positive luck feat with no explicit bonus must take the '
                         f'generic +1')
    dd = [n for n, i in table.items() if i['effects']['doubles_acquisition']]
    REPORT.check(dd == ['Double Down'],
                 f'exactly one feat doubles E-Kat acquisition; found {dd}')
    hp = [n for n, i in table.items() if i['effects']['hero_points_per_session']]
    REPORT.check(hp == ['It Just Works'],
                 f'exactly one feat grants a hero point per session; found {hp}')


def check_constants():
    """The numbers, against the Doc -- re-stated here so a constant edit has a witness."""
    REPORT.check(luck.LUCK_CAP_POSITIVE == 25, 'the positive luck cap is +25')
    REPORT.check(luck.LUCK_CAP_NEGATIVE == -50, 'the negative luck cap is -50')
    REPORT.check(luck.LUCK_CAP_DIMORPHIC == 40, 'Dimorphic luck has a natural cap of 40')
    REPORT.check(luck.LUCK_MOD_DIVISOR == 5, 'Luck Mod = Luck Score / 5')
    REPORT.check(luck.E_KAT_STORE_CAP == 99, 'the E-Kat store cap is 99')
    REPORT.check(luck.VAULT_CAP_BASE == 77 and luck.BIG_SAVINGS_VAULT_STEP == 77,
                 'Twist Fate draws up to 77 from the Vault; Big Savings raises the cap by 77')
    REPORT.check(luck.EXPANDED_LUCK_CAP_STEP == 5, 'Expanded Luck raises the cap by +5')

    # The ruling: floor toward -infinity, not truncation toward zero. -12/5 is -3, not -2.
    REPORT.check(luck.luck_mod(12) == 2 and luck.luck_mod(-12) == -3,
                 f'luck_mod rounds toward -infinity; got {luck.luck_mod(12)} and {luck.luck_mod(-12)}')

    # THE SPREAD. Buying costs 5 HP per +1; selling returns 2 HP per -1. If those ever equalise,
    # sell-then-buy becomes a free-money loop and the whole economy is broken.
    REPORT.check(luck.BUY_HP_PER_LUCK > luck.SELL_HP_PER_LUCK,
                 f'buying luck ({luck.BUY_HP_PER_LUCK} HP) must cost more than selling returns '
                 f'({luck.SELL_HP_PER_LUCK} HP), or the exchange is a free-money loop')
    REPORT.check(luck.BUY_SKILL_RANKS_PER_LUCK > luck.SELL_SKILL_POINTS_PER_LUCK,
                 'the skill-rank exchange must be lossy in the same direction')

    # Caps compose the way the traits say they do. Asserted directly because a generated character
    # almost never draws these traits (2 rows in a 1,129-row pool), so the behaviour sweep cannot
    # be relied on to exercise this path -- see the note in check_luck.
    REPORT.check(luck.luck_cap('Default') == 25 and luck.luck_cap('Dimorphic') == 40,
                 'base caps by type')
    REPORT.check(luck.luck_cap('Default', 3) == 40,
                 f'three Expanded Luck stacks give 25+15=40; got {luck.luck_cap("Default", 3)}')
    REPORT.check(luck.vault_cap(2) == 77 + 154,
                 f'two Big Savings stacks give 77+154; got {luck.vault_cap(2)}')
    REPORT.check(luck.clamp_luck(999, 'Default') == 25 and luck.clamp_luck(-999, 'Default') == -50,
                 'clamp_luck holds both ceilings')

    # The weights are probabilities over the pools that exist, and must stay so.
    for label, weights in (('currency', luck.LUCK_CURRENCY_WEIGHTS),
                           ('payout', luck.LUCK_PAYOUT_WEIGHTS),
                           ('luck type', luck.LUCK_TYPE_WEIGHTS)):
        total = round(sum(weights.values()), 6)
        REPORT.check(total == 1.0, f'{label} weights sum to {total}, not 1.0')
    REPORT.check(set(luck.LUCK_TYPE_WEIGHTS) == set(luck.LUCK_TYPES),
                 'every selectable luck type is weighted, and no others -- the Doc\'s three are '
                 'Default, Proximity and Dimorphic (Negative is a SIGN, not a type)')

    # THE SELL SCALE REACHES THE FLOOR, AT EVERY LEVEL. The sell side used to share the buy side's
    # magnitude formula, which capped a 20th-level seller at -12 -- and the negative Luck Traits are
    # floored from -10 to -50, so nine of the ten could never be bought by anyone. Asserted here
    # rather than in the behaviour sweep because the deep end is a tail draw: the sweep records how
    # often it landed, this proves it CAN.
    _depth = abs(luck.LUCK_CAP_NEGATIVE)
    for _lvl in (1, 5, 10, 20, 40):
        _draws = {luck.sell_magnitude(_lvl) for _ in range(20000)}
        REPORT.check(min(_draws) >= 1 and max(_draws) <= _depth,
                     f'level {_lvl}: sell magnitude {min(_draws)}..{max(_draws)} escapes '
                     f'1..{_depth}')
        REPORT.check(max(_draws) >= _depth - 1,
                     f'level {_lvl}: sell magnitude tops out at {max(_draws)}, so a character of '
                     f'this level can never reach the {luck.LUCK_CAP_NEGATIVE} floor the traits '
                     f'are written against')
    # Weighted, not uniform: deeper sales must get MORE likely as level rises, or "weighted by
    # level" is just a comment. Compared at the ends of the range where the gap is unambiguous.
    _mean = lambda lvl: sum(luck.sell_magnitude(lvl) for _ in range(20000)) / 20000
    _low, _high = _mean(1), _mean(20)
    REPORT.check(_high > _low,
                 f'sell depth must scale with level; level 1 averages {_low:.1f} and level 20 '
                 f'averages {_high:.1f}')


def check_reserve(table):
    """The reserve formula, recomputed from the Doc's words rather than from luck.e_kat_reserve.

    The gated cases are the point. Each per-level term rides its own feat -- "(1, 2 if Double Down)"
    is verbatim Sweet Dreams and Stream of Luck -- so a character with no E-Kat feats earns NOTHING.
    An earlier version gave every character level x 2 regardless, which handed a 20th-level
    character uninvolved with luck enough E-Kats to buy a Luck Trait for free.
    """
    SD, SL, DD, LB = 'Sweet Dreams', 'Stream of Luck', 'Double Down', 'Lucky Boy'
    ALL_TEN = list(DOC_FEATS)
    # These are the TABLE'S OWN worked examples, transcribed. "Long Rest E-Kats" and "Discovery
    # E-Kats" are never defined in the Doc, so the formula is a ruling rather than a reading, and
    # worked examples are the only thing that can witness a ruling. Two earlier readings both
    # produced plausible arithmetic and both were wrong; these numbers are what settled it.
    #
    #   long_rest = 2 if Double Down else 1, but only with Sweet Dreams   (else 0)
    #   discovery = 2 if Double Down else 1, but only with Stream of Luck (else 0)
    #   earned    = level*long_rest + level*discovery + feats*5     ... x2 if Dimorphic
    #
    # Note Double Down doubles ONLY the two level terms: the third example is 55, not 59.
    for level, feats, dim, want in (
            (20, [], False, 0),                     # no E-Kat feats earns nothing
            (10, [LB], False, 5),                   # neither gate: only the feats x 5
            (10, [SD, LB], False, 20),              # 10x1 + 10x0 + 5x2
            (10, [SD, SL], False, 30),              # 10x1 + 10x1 + 5x2
            (10, [SD, SL, DD], False, 55),          # 2x(10+10) + 5x3  -- NOT 59
            (10, [SD, SL, DD], True, 110),          # Dimorphic doubles the lot
            (20, ALL_TEN, False, 130),              # 2x(20+20) + 10x5
            (20, ALL_TEN, True, 260),
    ):
        got = luck.e_kat_reserve(level, feats, dim)
        REPORT.check(got == want,
                     f'e_kat_reserve(level={level}, feats={feats}, dimorphic={dim}) == {got}, '
                     f'expected {want}')

    # The 99 governs STORAGE, not the computation -- these points "must be spent", so they pass
    # through. A high-level Dimorphic build legitimately computes far above the cap.
    big = luck.e_kat_reserve(40, [SD, SL, DD, LB], True)   # deep investment, high level
    REPORT.check(big > luck.E_KAT_STORE_CAP,
                 f'a 40th-level Dimorphic build computes {big}; the store cap must NOT clamp the '
                 f'earned total, only what is carried')
    REPORT.check(luck.carried_e_kats(big, luck.luck_traits_afforded(big)) < luck.LUCK_TRAIT_COST,
                 'whatever is carried after buying traits is under one trait\'s price by definition')
    REPORT.check(luck.carried_e_kats(10_000, 0) == luck.E_KAT_STORE_CAP,
                 'an unspent reserve IS clamped by the store cap')
    REPORT.check(luck.e_kat_store_cap(2) == luck.E_KAT_STORE_CAP + 2 * luck.ENHANCED_STORAGE_STEP,
                 'Enhanced Luck Storage raises the store cap by +100 per stack')


# The 34 Luck Traits, transcribed from the Doc -- name -> category, and which are repeatable.
# Not read from the JSON this gate is checking: a roster that reads its own file proves nothing.
DOC_TRAITS = {
    'Expanded Luck': ('standard', True), 'Lucky Survivor': ('standard', True),
    'Increase Luck': ('standard', True),
    'E-Kat Exchange: Enhanced Luck Storage': ('standard', True),
    'E-Kat Exchange: Momentum': ('standard', False), 'Lucky Survival': ('standard', True),
    'God Has Failed Us': ('standard', False), 'E-Kat Exchange: Loaded Dice': ('standard', False),
    'E-Kat Exchange: Pull': ('standard', False), 'E-Kat Exchange: Aim-Bot': ('standard', False),
    'E-Kat Exchange: Auto-Dodge': ('standard', False),
    'E-Kat Exchange: Loot Box': ('standard', False),
    'E-Kat Exchange: Premium Loot Box': ('standard', False),
    'E-Kat Exchange: Deluxe Loot Box': ('standard', False),
    'E-Kat Exchange: Optimal Allocation': ('standard', False),
    'E-Kat Exchange: Convenient Failure': ('standard', False),
    'E-Kat Exchange: Lucky Navigator': ('standard', False),
    'E-Kat Exchange: Blind Luck': ('standard', False),
    'E-Kat Exchange: Rotten Luck': ('standard', False),
    'When It Counts': ('negative', False), 'Trauma Survivor': ('negative', False),
    'Never-Ending Suffering': ('negative', False), 'Tough Luck': ('negative', False),
    'Tough Skin': ('negative', False), 'Seen it all': ('negative', False),
    'Hardened Mind': ('negative', False), 'Hardened Body': ('negative', False),
    'Hardened Reflexes': ('negative', False), 'Been there done that': ('negative', False),
    'Fated Survival': ('dimorphic', True), 'Extra Spin': ('dimorphic', True),
    'Interest Growth': ('dimorphic', True), 'Big Savings': ('dimorphic', True),
    'Inevitable': ('dimorphic', True),
}
# The only five that move a number the generator computes: field -> (trait, matching constant).
DOC_TRAIT_EFFECTS = {
    'luck_cap_step': ('Expanded Luck', luck.EXPANDED_LUCK_CAP_STEP),
    'luck_score_bonus': ('Increase Luck', 1),
    'e_kat_store_step': ('E-Kat Exchange: Enhanced Luck Storage', luck.ENHANCED_STORAGE_STEP),
    'twist_fate_bonus': ('Extra Spin', 1),
    'vault_cap_step': ('Big Savings', luck.BIG_SAVINGS_VAULT_STEP),
}


# Trait prerequisites, transcribed from the Doc. Three forms, and all three must be enforced or a
# character buys Deluxe Loot Box having never bought Loot Box.
DOC_TRAIT_PREREQ = {
    'E-Kat Exchange: Premium Loot Box': ['E-Kat Exchange: Loot Box'],
    'E-Kat Exchange: Deluxe Loot Box': ['E-Kat Exchange: Premium Loot Box'],
    'Never-Ending Suffering': ['Trauma Survivor'],
}
DOC_TRAIT_LUCK_FLOOR = {
    'Tough Luck': -10, 'Been there done that': -15, 'Hardened Mind': -25, 'Hardened Body': -25,
    'Hardened Reflexes': -25, 'Trauma Survivor': -25, 'Tough Skin': -30, 'Seen it all': -40,
    'When It Counts': -50,
}


def check_trait_prereqs(traits):
    for name, info in traits.items():
        want = DOC_TRAIT_PREREQ.get(name, [])
        REPORT.check(info.get('prerequisites', []) == want,
                     f'{name}: prerequisites {info.get("prerequisites")} != the roster {want}')
        for pre in info.get('prerequisites', []):
            REPORT.check(pre in traits,
                         f'{name} requires {pre!r}, which is not a trait -- the unsatisfiable-tail '
                         f'defect returning in the trait table')
        floor = info.get('requires_luck_at_most')
        REPORT.check(floor == DOC_TRAIT_LUCK_FLOOR.get(name),
                     f'{name}: luck floor {floor} != the roster value '
                     f'{DOC_TRAIT_LUCK_FLOOR.get(name)}')

    REPORT.check(traits['Inevitable'].get('requires_luck_assets_per_stack') == 10,
                 'Inevitable requires 10 luck feats/traits PER STACK')

    # The score floor must actually gate. A character at -5 cannot take a trait wanting -25.
    from utils.class_func.feats import eligible_luck_traits
    _shallow = eligible_luck_traits('Default', -5)
    _deep = eligible_luck_traits('Default', -50)
    REPORT.check('Trauma Survivor' not in _shallow,
                 'Trauma Survivor wants -25 luck; a character at -5 must not be offered it')
    REPORT.check('Trauma Survivor' in _deep and 'When It Counts' in _deep,
                 'a character at -50 should be offered every negative trait')
    # No cycles: a chain must terminate or nothing in it is ever buyable.
    for name in traits:
        seen, frontier = set(), list(traits[name].get('prerequisites', []))
        while frontier:
            nxt = frontier.pop()
            if nxt in seen:
                break
            seen.add(nxt)
            frontier.extend(traits.get(nxt, {}).get('prerequisites', []))
        REPORT.check(name not in seen, f'{name}: trait prerequisite chain is cyclic')


def check_luck_traits(traits):
    REPORT.check(len(traits) == len(DOC_TRAITS),
                 f'luck_traits.json has {len(traits)} traits, the Doc has {len(DOC_TRAITS)}')
    missing = [n for n in DOC_TRAITS if n not in traits]
    extra = [n for n in traits if n not in DOC_TRAITS]
    REPORT.check(not missing, f'Luck Traits in the Doc but absent from the table: {missing}')
    REPORT.check(not extra, f'Luck Traits in the table but not in the Doc: {extra}')

    for name, (category, repeatable) in DOC_TRAITS.items():
        info = traits.get(name)
        if info is None:
            continue
        REPORT.check(info['category'] == category,
                     f'{name}: category {info["category"]!r}, the Doc puts it under {category!r}')
        REPORT.check(info['repeatable'] == repeatable,
                     f'{name}: repeatable={info["repeatable"]}, the Doc says {repeatable}')

    counts = {c: sum(1 for i in traits.values() if i['category'] == c)
              for c in (luck.TRAIT_CATEGORY_STANDARD, luck.TRAIT_CATEGORY_NEGATIVE,
                        luck.TRAIT_CATEGORY_DIMORPHIC)}
    REPORT.check(counts == {'standard': 19, 'negative': 10, 'dimorphic': 5},
                 f'category split is {counts}, the Doc has 19 standard / 10 negative / 5 dimorphic')

    # Exactly five traits carry a structured effect, and each one's step must agree with the
    # constant the pipeline actually applies -- data declaring +5 while the code adds +10 is the
    # classic silent drift this pair of gates exists to catch.
    for field, (owner, step) in DOC_TRAIT_EFFECTS.items():
        carriers = [n for n, i in traits.items() if field in i.get('effects', {})]
        REPORT.check(carriers == [owner],
                     f'{field} should be carried by exactly {owner!r}; found {carriers}')
        if carriers == [owner]:
            REPORT.check(traits[owner]['effects'][field] == step,
                         f'{owner}: {field} is {traits[owner]["effects"][field]}, but the code '
                         f'applies {step}')
    with_effects = [n for n, i in traits.items() if i.get('effects')]
    REPORT.check(len(with_effects) == len(DOC_TRAIT_EFFECTS),
                 f'{len(with_effects)} traits carry structured effects, expected '
                 f'{len(DOC_TRAIT_EFFECTS)}: {sorted(with_effects)}')

    # "These Traits do not grant 1 extra luck" -- the mirror of the feats' no-double-count rule.
    # Only Increase Luck may touch the score, and only by its own stated amount.
    score_movers = [n for n, i in traits.items() if i.get('effects', {}).get('luck_score_bonus')]
    REPORT.check(score_movers == ['Increase Luck'],
                 f'only Increase Luck may move the luck score; found {score_movers} -- "These '
                 f'Traits do not grant 1 extra luck"')

    REPORT.check(luck.LUCK_TRAIT_COST == 25,
                 f'"25 Permanent E-Kats can be used to purchase a Luck Trait"; the constant is '
                 f'{luck.LUCK_TRAIT_COST}')

    # ---- THE TRAIT MECHANICS ----------------------------------------------------------------
    # NO INERT PROSE. `pf1_change_candidate` is the curator's own marker that a trait's benefit
    # names a mechanical effect; if one is marked and carries nothing, it renders as text the
    # player applies by hand. Driven off the flag rather than off a list of names here, so adding
    # a trait and marking it is enough to make this gate demand the mechanics.
    import math
    MOD_FORMULA = '-floor(@resources.personalLuck.value / 5)'
    SCORE_FORMULA = '-@resources.personalLuck.value'
    for name, info in traits.items():
        if not info.get('pf1_change_candidate'):
            continue
        carries = (info.get('changes') or info.get('context_notes')
                   or info.get('death_hp_pool_bonus'))
        REPORT.check(bool(carries),
                     f'{name} is marked pf1_change_candidate but carries no change, context note '
                     f'or formula -- its benefit is prose the player must apply by hand')
        for c in info.get('changes') or []:
            REPORT.check(c['formula'] == MOD_FORMULA,
                         f'{name}: change formula is {c["formula"]!r}, not the canonical '
                         f'{MOD_FORMULA!r}')
            REPORT.check(set(c) == {'formula', 'target', 'type', 'operator', 'priority'},
                         f'{name}: change has keys {sorted(c)}, not pf1\'s five')
        if info.get('death_hp_pool_bonus'):
            REPORT.check(info['death_hp_pool_bonus'] == SCORE_FORMULA,
                         f'{name}: death-pool formula is {info["death_hp_pool_bonus"]!r}, not the '
                         f'canonical {SCORE_FORMULA!r} (it uses the SCORE, not the mod)')

    # THE FORMULA'S ARITHMETIC, against luck_mod itself. `-floor(score/5)` is the magnitude of the
    # mod ONLY because the negation sits outside the floor: at -44 the mod is -9 (magnitude 9) but
    # floor(abs(-44)/5) is 8. Foundry's floor() is Math.floor, which rounds toward -infinity exactly
    # as Python's // does -- so this also pins luck_mod's rounding. If anyone ever "fixes" luck_mod
    # to truncate toward zero, the sheet and the score would silently disagree by one, and this is
    # the only thing that would say so.
    for s in range(luck.LUCK_CAP_NEGATIVE, 0):
        REPORT.check(-math.floor(s / 5) == -luck.luck_mod(s),
                     f'score {s}: the sheet formula yields {-math.floor(s / 5)} but luck_mod gives '
                     f'a magnitude of {-luck.luck_mod(s)}')
        REPORT.check(-luck.luck_mod(s) >= 0,
                     f'score {s}: trait bonus resolves to {-luck.luck_mod(s)}; these traits are '
                     f'compensation and must never be a penalty')

    # THE NEGATIVE CATALOGUE IS REACHABLE. All ten negative traits were dead content until sellers
    # were let back into the E-Kat economy: eligible_luck_traits opens the category at score < 0,
    # but sellers earned no reserve, so nothing could ever afford one. The behaviour sweep only
    # RECORDS how many landed (a seller needs a deep score and 25 E-Kats at once, which is a tail
    # event); this asserts every one of them is buyable at the score its own floor demands.
    from utils.class_func.feats import eligible_luck_traits
    for name, info in traits.items():
        if info['category'] != luck.TRAIT_CATEGORY_NEGATIVE:
            continue
        floor = info.get('requires_luck_at_most')
        score = floor if floor is not None else -1
        REPORT.check(score >= luck.LUCK_CAP_NEGATIVE,
                     f'{name} needs luck <= {floor}, past the {luck.LUCK_CAP_NEGATIVE} floor -- no '
                     f'character can ever qualify')
        REPORT.check(name in eligible_luck_traits('Default', score),
                     f'{name} is not offered at a score of {score}, so the negative category is '
                     f'unreachable for it')


def check_traits_are_not_character_traits(traits):
    """Luck Traits may ONLY be purchased with E-Kats, so they must not be in the trait pool.

    An earlier pass put Expanded Luck and Big Savings into data/traits.csv, where trait_selector
    would hand them out as ordinary character traits. This is the gate that keeps them out.
    """
    csv_path = repo_path('data/traits.csv')
    rows = [line for line in csv_path.read_text(encoding='utf-8', errors='replace').splitlines()[1:]
            if line.strip()]

    # The type marker is the primary signal -- both traits the earlier pass added carried type=Luck.
    typed = [line.split('|')[0] for line in rows
             if len(line.split('|')) > 1 and line.split('|')[1].strip() == 'Luck']
    REPORT.check(not typed, f'data/traits.csv carries type="Luck" row(s): {typed}. "Luck Traits may '
                            f'only be purchased with E-Kats" -- they are not character traits and '
                            f'trait_selector must never be able to draw them')

    # A name match alone is NOT a leak. "Tough Skin" is both a Luck Trait (natural AC equal to your
    # luck mod) and a long-standing Tiefling race trait (+1 AC against crit confirmations); the two
    # are unrelated and the Tiefling one predates all of this. So a collision only counts when the
    # row also talks like the luck system.
    vocabulary = ('e-kat', 'luck cap', 'vaulted interest', 'twist of fate', 'luck mod', 'luck score')
    leaked = []
    for line in rows:
        parts = line.split('|')
        if parts[0].strip() not in traits:
            continue
        if any(word in line.lower() for word in vocabulary):
            leaked.append(parts[0].strip())
    REPORT.check(not leaked,
                 f'data/traits.csv row(s) {sorted(leaked)} share a Luck Trait name AND use luck-'
                 f'system vocabulary -- that is a real leak, not a coincidental collision')


def check_payload_contract():
    REPORT.check('luck' in PAYLOAD_KEYS,
                 "PAYLOAD_KEYS does not declare 'luck' -- both consumers read this order")
    idx = list(PAYLOAD_KEYS).index('luck')
    tail = set(PAYLOAD_KEYS[idx + 1:])
    # 'mythic' is the other tail-appended nested block (mythic map, ticket 05) -- added under
    # exactly the luck precedent, so it legitimately sits after 'luck'. The four weapon_size_*
    # fields (gear-legality plan, D11) are appended for the same reason: they are a new marker at
    # the very end, so nothing above them moves, which is the property this check exists to
    # protect. This list is meant to be short and to be extended DELIBERATELY -- a key turning up
    # here that nobody added on purpose is a key that shifted somebody's sheet.
    REPORT.check(tail <= {'mythic', 'buff_gaps', 'generator_version', 'license_url',
                          'weapon_size', 'weapon_size_steps', 'weapon_size_source',
                          'weapon_size_attack_penalty'},
                 f"'luck' must sit at the tail of the content keys so no existing key shifts "
                 f"position; keys after it: {sorted(tail)}")


def check_typed_values():
    """One shape for every character: three typed values, Dimorphic holding all three equal."""
    dim = luck.typed_values(10, 'Dimorphic')
    REPORT.check(dim == {'negative': 10, 'default': 10, 'proximity': 10},
                 f'Dimorphic holds all three types at EQUAL values; got {dim}')
    REPORT.check(luck.typed_values(7, 'Default') == {'negative': 0, 'default': 7, 'proximity': 0},
                 'Default luck populates only the default value')
    REPORT.check(luck.typed_values(7, 'Proximity')['proximity'] == 7,
                 'Proximity luck populates the proximity value')
    for luck_type in luck.LUCK_TYPES:
        REPORT.check(set(luck.typed_values(0, luck_type)) == {'negative', 'default', 'proximity'},
                     f'{luck_type}: typed_values must always emit the same three keys')


def check_luck_feats(luck_feats, e_kat_table):
    """The non-E-Kat luck feats: the roster, and that every name still resolves in the live pool.

    These are ordinary Paizo feats already reachable through generic_feat_chooser, so unlike the
    E-Kat feats they need no ingestion -- only recognition. Which makes the failure mode a silent
    one: rename a row upstream and the feat simply stops granting luck, with nothing to notice. This
    check is that notice.
    """
    REPORT.check(set(luck_feats) == DOC_LUCK_FEATS,
                 f'luck_feats.json roster {sorted(set(luck_feats) ^ DOC_LUCK_FEATS)} differs from '
                 f'the ruling')

    overlap = sorted(set(luck_feats) & set(e_kat_table))
    REPORT.check(not overlap,
                 f'{overlap} appear in BOTH luck_feats.json and e_kat_feats.json -- they would be '
                 f'counted twice, and the E-Kat table already grants their luck')

    # Every name must exist in the pool a character actually draws from, or it grants luck to nobody.
    import csv
    with repo_path('data/feats.csv').open(encoding='utf-8', errors='replace', newline='') as fh:
        pool = {row['name'].strip().lower() for row in csv.DictReader(fh, delimiter='|')
                if row.get('name')}
    missing = sorted(n for n in luck_feats if n.lower() not in pool)
    REPORT.check(not missing,
                 f'luck feat(s) {missing} are not in data/feats.csv, so no character can ever hold '
                 f'them and they grant luck to nobody -- renamed upstream, or mistyped here?')


def check_exchange_table(rows):
    """The spend table the sheet renders. Its costs are rule text, but one of them is load-bearing."""
    REPORT.check(len(rows) == 9, f'the E-Kat spend table has {len(rows)} rows, the Doc has 9')

    labels = [r['label'] for r in rows]
    REPORT.check(len(set(labels)) == len(labels),
                 f'duplicate labels in the spend table: {labels} -- these become class-feature KEYS')
    # ASCII on purpose: the labels become keys, and keys travel through the FoundryVTT module's name
    # matching, where a stray em-dash is the same class of defect as a casing mismatch.
    non_ascii = [l for l in labels if not l.isascii()]
    REPORT.check(not non_ascii,
                 f'non-ASCII spend-table label(s) {non_ascii} -- they become class-feature keys and '
                 f'the module matches those by name')
    REPORT.check(all(r.get('text') for r in rows), 'every spend-table row needs its rule text')

    # THE ONE ROW THE GENERATOR ACTS ON. If the table says a Luck Trait costs 25 and the code
    # charges something else, a sheet tells the player a price the generator did not use.
    trait_rows = [r for r in rows if 'Luck Trait' in r['label']]
    REPORT.check(len(trait_rows) == 1 and trait_rows[0]['cost'] == luck.LUCK_TRAIT_COST,
                 f'the spend table prices a Luck Trait at '
                 f'{trait_rows[0]["cost"] if trait_rows else "?"}, but luck.LUCK_TRAIT_COST is '
                 f'{luck.LUCK_TRAIT_COST}')
    REPORT.check(max(r['cost'] for r in rows) == luck.E_KAT_STORE_CAP,
                 f'the most expensive row should cost exactly the store cap ({luck.E_KAT_STORE_CAP})')


def check_sheet_section():
    """The E-Kat Exchange renders as three GROUPS, not one flat wall of rows.

    The module turns a nested dict into a sub-heading plus its own list; a flat dict becomes one
    twenty-row bullet list, which is what this replaced. Asserted here because the grouping is a
    contract between the backend's shape and the module's renderer, and neither half fails loudly
    if the other changes.
    """
    from utils.class_func.feats import luck_sheet_sections
    probe = {'stake': {'direction': 'buy'}, 'feats': ['Double Down'], 'traits': [],
             'e_kat_reserve': 7, 'e_kat_earned': 32, 'e_kat_store_cap': 99}
    sections = luck_sheet_sections(probe)
    REPORT.check('E-Kat Exchange' in sections, 'a character in the E-Kat economy gets the section')
    block = sections.get('E-Kat Exchange', {})
    groups = list(block)
    REPORT.check(groups and groups[0] == 'Reserve' and 'Actions' in groups,
                 f'E-Kat Exchange groups are {groups}; Reserve must lead and Actions must be present')
    # Every "E-Kat Exchange: ..." trait buys an ACTION, so a character holding one must see it listed
    # beside the base table rather than only among its passive traits.
    probe2 = dict(probe, traits=['E-Kat Exchange: Loaded Dice', 'Expanded Luck'])
    block2 = luck_sheet_sections(probe2).get('E-Kat Exchange', {})
    REPORT.check(list(block2.get('Actions (Purchased)', {})) == ['Loaded Dice'],
                 f"purchased actions are {list(block2.get('Actions (Purchased)', {}))}, expected the "
                 f"Loaded Dice action (and NOT the passive Expanded Luck)")
    # A feat that changes the base table must say so on the sheet -- the nine rows are static text.
    probe3 = dict(probe, feats=['Luck God', 'Very Lucky Boy'])
    acts3 = luck_sheet_sections(probe3).get('E-Kat Exchange', {}).get('Actions', {})
    REPORT.check('Active modifiers' in acts3 and 'halved' in acts3['Active modifiers'].lower(),
                 'Luck God halves every E-Kat cost; the Actions group must say so')
    # The probe holds exactly one feat, so the heading must list exactly that one. A "Feats Taken"
    # group naming a feat the character does not have reads as true at a glance, which is worse
    # than omitting it -- that is the defect this asserts against.
    REPORT.check(list(block.get('Feats Taken', {})) == ['Feat: Double Down'],
                 f"'Feats Taken' lists {list(block.get('Feats Taken', {}))}, but the character holds "
                 f"only Double Down")
    REPORT.check('Feat: Luck God' not in block.get('Feats Taken', {}),
                 "an untaken feat must never appear under 'Feats Taken'")
    for name, group in block.items():
        REPORT.check(isinstance(group, dict) and group,
                     f'group {name!r} must be a non-empty dict for the module to render a sub-list')
    _labels = {r['label'] for r in e_kat_exchange_rows()}
    _missing = sorted(_labels - set(block.get('Actions', {})))
    REPORT.check(not _missing,
                 f'spend-table row(s) {_missing} never reached the Actions group')
    REPORT.check(not luck_sheet_sections(None) and not luck_sheet_sections(
        {'stake': None, 'feats': [], 'traits': [], 'e_kat_reserve': 0}),
        'a character with no luck involvement gets no section at all')


def main():
    table = e_kat_feat_table()
    traits = luck_trait_table()
    luck_feats = luck_feat_table()
    check_roster(table)
    check_prereqs(table)
    check_effects(table)
    check_constants()
    check_reserve(table)
    check_luck_traits(traits)
    check_trait_prereqs(traits)
    check_traits_are_not_character_traits(traits)
    check_luck_feats(luck_feats, table)
    check_exchange_table(e_kat_exchange_rows())
    check_sheet_section()
    check_typed_values()
    check_payload_contract()
    return REPORT.finish(f'{len(table)} E-Kat feats, {len(luck_feats)} other luck feats, '
                         f'{len(traits)} Luck Traits, {len(e_kat_exchange_rows())} spend-table rows, '
                         f'{len(BLOCK_KEYS)} luck payload fields')


if __name__ == '__main__':
    sys.exit(main())
