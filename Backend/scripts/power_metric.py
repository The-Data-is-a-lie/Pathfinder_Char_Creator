"""Score a generated character against PF1e's own CR benchmarks.

    from power_metric import profile_for
    prof = profile_for(payload)          # {'axes': {...}, 'blind': [...], 'notes': [...]}

WHY THIS EXISTS
---------------
The optimal-builder map (`tickets: feature/optimal-builder`) has three witnesses and two of them
consume a number nobody had built: a margin gate and an A/B delta report. Its ticket 05 then came
back and found that five of the eight candidate "dead choice" kinds do not exist in this codebase,
which left the metric carrying most of the map's evidential weight. So the metric gets built and
run against TODAY's random output before any optimizer exists -- the first real answer to "how good
are the characters we already make".

WHAT THIS IS NOT
----------------
It is not a scalar. Collapsing the axes needs weights, weights are ticket 01's to set, and a scalar
would hard-wire the tautology trap ticket 09 names: an optimizer that maximises score X, gated by a
check that X went up, tests only that a maximiser maximises. So this emits a PROFILE -- one ratio
per axis against the benchmark row -- and leaves the collapse undone.

THE PAYLOAD DOES NOT HOLD THESE NUMBERS
---------------------------------------
Ticket 03 assumed "the character object already knows nearly all of it". It does not. The payload
carries `bab_total`, `save_bases`, `armor_ac`, `shield_ac`, `Total_HP` and raw ability scores --
COMPONENTS, not totals. No AC, save, attack or damage total exists anywhere in it, and deflection
and natural armour sit unfolded inside `item_changes_dict`. This module therefore COMPUTES PF1e
math, which makes it the third implementation of that math in the stack (pf1 itself, the web
sheet's `derive.js`, and this). `build/check_derive_parity.mjs` is the insurance: it diffs this
module against `derive.js` over the seven goldens, locally, so a divergence is caught here rather
than in a Foundry session.

DELIBERATE FIDELITY CHOICE
--------------------------
`derive.js`'s `sumParts` is a PLAIN SUM -- the web sheet applies no pf1 typed-bonus non-stacking, so
two `enhancement` bonuses to AC both count. This module matches that, on purpose: the parity harness
only produces signal if both sides compute the same thing, and "the web sheet does not apply typed
stacking" is a finding to file rather than a difference to bury. See TYPED_STACKING_NOTE.

TWO TRAPS THAT WOULD SILENTLY CORRUPT EVERY AXIS
------------------------------------------------
1. `payload['str']` is the rolled score PLUS racial only. `inherents` and `level_up_stats` are
   SEPARATE dicts (`stats.py:99,131`) delivered to Foundry as their own buff and changes, worth up
   to +10 each. Reading `payload['str']` alone understates every character.
2. A creature with PC class levels is **CR = level - 1** (a 1st-level PC-classed NPC is CR 1/2).
   Scoring a level-12 NPC against the CR 12 row would call every character underpowered.
"""
import json
import math
import re
from functools import lru_cache

from _harness import JSON_DIR

TYPED_STACKING_NOTE = (
    'AC and save ledger bonuses are summed untyped, matching derive.js sumParts. pf1 itself would '
    'take the best of each bonus type instead, so a character carrying two same-typed bonuses to '
    'one target reads slightly high here AND on the web sheet.')

# Change buckets folded into the ledger. Only ALWAYS-ON sources: an equipped item and a feat are on
# in every round, a spell buff and a togglable class feature are not, and the metric's declared
# round is "no pre-cast buffs" (power_adders.json::_assumptions).
ALWAYS_ON_CHANGE_KEYS = ('item_changes_dict', 'feat_changes_dict')
# enhancement_effects_dict is sectioned weapon/armor/shield; the weapon section is on-hit
# conditionals, so only the worn sections are always-on.
WORN_ENHANCEMENT_SECTIONS = ('armor', 'shield')

# The vocabularies power_adders.json is allowed to use. Exported so validate_power_metric.py can
# check the DATA against the CODE -- an entry whose `model` is misspelled contributes zero forever
# and nothing would otherwise say so, which is the same silent-nothing failure as a curated name
# that matches no feat.
IMPLEMENTED_MODELS = frozenset({
    'flat_attack', 'flat_damage', 'power_attack', 'caster_level_scaled_damage',
    'double_threat_range', 'extra_attack', 'flat_ac', 'toughness_hp', 'vital_strike',
    'negate_power_attack_penalty_first_attack',
})
IMPLEMENTED_CONDITIONS = frozenset({
    'always', 'melee', 'ranged', 'light_melee', 'melee_two_handed', 'light_offhand',
    'within_30_ft', 'standard_action_only',
})
IMPLEMENTED_RULE_MODELS = frozenset({'blast_dice', 'strike_damage'})
# The nova round's limited-use class offense (power_adders.json::nova) and the curated class-DR
# table (::dr). Same contract as IMPLEMENTED_MODELS: the gate checks the data against these, so a
# misspelled model fails loudly instead of contributing zero forever.
IMPLEMENTED_NOVA_MODELS = frozenset({'rage', 'smite', 'challenge', 'sneak_attack',
                                     'inspire_courage', 'ki_extra_attack'})
IMPLEMENTED_DR_MODELS = frozenset({'scaling_dr', 'flat_dr_at'})
# Spell-buff effect models (power_adders.json::spell_buffs). Effects are MODELED here rather than
# read from spell_changes.json: that file's formulas are sheet-variable-bound
# (@spells.primary.cl.total resolves only on a live sheet) and it covers barely half the buffs
# that matter (no righteous might, no bull's strength, no GMW). The validator still cross-checks
# every curated name against the spell corpus, so the silent-nothing rule holds.
IMPLEMENTED_BUFF_MODELS = frozenset({'flat', 'scaled_flat', 'stat_bonus', 'size_step',
                                     'extra_attack', 'dr'})

# Flat '+N ... bonus ... to AC' in stance/ability prose (the wall pass). Scaled wordings go in
# power_adders.json::stance_ac instead -- curate, never guess.
_AC_BONUS_TEXT = re.compile(r'\+(\d+)[^.]{0,40}?bonus[^.]{0,30}?to (?:AC|Armor Class)', re.I)

# "deals an additional 2d8 damage" -- the near-universal PoW bonus-dice phrasing (the
# power_adders note: only 12 of 1,033 maneuvers fail this parse).
_BONUS_DICE = re.compile(r'additional\s+(\d+)d(\d+)', re.I)

# One size step up (enlarge person, righteous might): the PF1e weapon-dice progression for the
# common medium dice. Anything unlisted steps by adding one die of the same face -- close enough
# for a metric, stated here rather than guessed silently.
_SIZE_STEP = {
    (1, 2): (1, 3), (1, 3): (1, 4), (1, 4): (1, 6), (1, 6): (1, 8), (1, 8): (2, 6),
    (1, 10): (2, 8), (1, 12): (3, 6), (2, 4): (2, 6), (2, 6): (3, 6), (2, 8): (3, 8),
    (2, 10): (4, 8), (3, 6): (4, 6),
}

# DR stated in text the character actually HOLDS (see damage_reduction for which buckets qualify --
# class_ability_desc does NOT: it lists every ability the class ever gets, level-gated by nothing).
_DR_TEXT = re.compile(r'(?:damage reduction|\bDR)\s*(\d+)\s*/', re.I)
_ERES_TEXT = re.compile(
    r'(?:resist(?:ance)?\s+(?:to\s+)?(acid|cold|electricity|fire|sonic)\s+(\d+)'
    r'|(acid|cold|electricity|fire|sonic)\s+resistance\s+(\d+))', re.I)

ABILITIES = ('str', 'dex', 'con', 'int', 'wis', 'cha')
SAVES = ('fort', 'ref', 'will')

# pf1 change targets, by what they modify.
AC_TARGETS = {'ac', 'aac', 'sac', 'nac'}
AC_TOUCH_TARGETS = {'ac', 'tac', 'nac'}
AC_FLAT_TARGETS = {'ac', 'ffac', 'aac', 'sac', 'nac'}
ATTACK_TARGETS = {'attack', 'mattack', 'rattack'}


# --------------------------------------------------------------------------- data

@lru_cache(maxsize=1)
def benchmarks():
    """{cr: row} from cr_benchmarks.json."""
    raw = json.loads((JSON_DIR / 'cr_benchmarks.json').read_text(encoding='utf-8'))
    return {row['cr']: row for row in raw['rows']}


@lru_cache(maxsize=1)
def target_multipliers():
    """{axis: multiplier} applied to every benchmark denominator -- the bar-raising lever.

    All 1.0 today, so ratios read pure table. When Daniel wants the NPCs held above the published
    row (the house feat surplus should put them well past a stock monster), the bar moves by
    editing cr_benchmarks.json::_target_multipliers -- the build_archetypes.json precedent: tune
    the JSON, not the engine. validate_power_metric.py asserts the block covers exactly the
    benchmarked axes, so a misspelled axis fails loudly instead of silently keeping the old bar.
    """
    raw = json.loads((JSON_DIR / 'cr_benchmarks.json').read_text(encoding='utf-8'))
    block = raw.get('_target_multipliers') or {}
    return {axis: float(value) for axis, value in block.items() if not axis.startswith('_')}


@lru_cache(maxsize=1)
def adders():
    return json.loads((JSON_DIR / 'power_adders.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def waived_feats():
    """feat_tax.json's tax_primary_blocklist -- the Elephant-in-the-Room feats this table WAIVES.

    A waived feat is ambient: every qualifying character simply has it, it is never picked and
    never exported, so gating its model on the name appearing in a payload bucket means the model
    NEVER fires -- which is exactly what happened: Power Attack contributed zero damage to every
    baseline martial until the optimized_striker golden's coverage predicate went looking for the
    name and could not find it anywhere.
    """
    raw = json.loads((JSON_DIR / 'feat_tax.json').read_text(encoding='utf-8'))
    return tuple(str(n).lower() for n in raw.get('tax_primary_blocklist') or [])


def ambient_feats(mods, bab):
    """The waived feats this character QUALIFIES for, spelled as power_adders spells them.

    Qualification is each feat's own published prerequisite (Str/Dex 13, BAB +1), checked against
    final scores. Waived feats without a damage/AC model here simply have no entry to match.
    """
    out = set()
    waived = waived_feats()
    if 'power attack' in waived and mods['str'] >= 1 and bab >= 1:
        out.add('Power Attack')
    if 'weapon finesse' in waived and mods['dex'] >= 1:
        out.add('Weapon Finesse')
    if 'combat expertise' in waived and mods['int'] >= 1:
        out.add('Combat Expertise')
    # Ambient Dodge is deliberately NOT folded: armor_class must keep matching derive.js exactly
    # (the parity harness asserts the AC delta equals the enhancement shortfall and nothing else),
    # so the house-waived +1 stays a named blind spot rather than a silent parity break.
    return out


@lru_cache(maxsize=1)
def weapons():
    """{lowercased weapon name: entry} flattened across the proficiency sections."""
    raw = json.loads((JSON_DIR / 'weapons_data.json').read_text(encoding='utf-8'))
    out = {}
    for section in raw.values():
        if isinstance(section, dict):
            for name, entry in section.items():
                out.setdefault(name.strip().lower(), entry)
    return out


@lru_cache(maxsize=1)
def stance_texts():
    """{lowercased spaced name: description} for every Path of War maneuver/stance entry.

    Martial_Disciplines.json keys entries Underscored_Like_This under each discipline; the
    payload's `stances_chosen` spells them with spaces. Flattened once for the process.
    """
    raw = json.loads((JSON_DIR / 'class_data' / 'path_of_war' /
                      'Martial_Disciplines.json').read_text(encoding='utf-8'))
    out = {}
    for discipline in raw.values():
        if not isinstance(discipline, dict):
            continue
        for name, entry in discipline.items():
            if isinstance(entry, dict):
                key = str(name).replace('_', ' ').strip().lower()
                out.setdefault(key, str(entry.get('Description') or ''))
    return out


def _best_bonus_dice(named_texts):
    """(average, note) of the largest 'additional NdM' in any of the (name, text) pairs."""
    best, note = 0.0, None
    for name, text in named_texts:
        for match in _BONUS_DICE.finditer(str(text)):
            average = int(match.group(1)) * (int(match.group(2)) + 1) / 2.0
            if average > best:
                best = average
                note = f'{name}: +{match.group(1)}d{match.group(2)}'
    return best, note


def pow_dice(payload):
    """The Path of War bonus dice this character actually has, parsed from prose it HOLDS.

    Returns {'stance': avg, 'stance_note', 'strike': avg, 'strike_note'}. A stance is always-on
    while fighting, so its dice ride EVERY attack in BOTH rounds (Savage Stance: +2d8 per hit);
    a strike is one expended maneuver, so its dice land ONCE, in the nova round. Held-maneuver
    prose is in the payload (`maneuvers_desc_dict`); stance prose is looked up by name.
    """
    stances = [(name, stance_texts().get(str(name).strip().lower(), ''))
               for name in payload.get('stances_chosen') or []]
    stance_avg, stance_note = _best_bonus_dice(stances)
    desc = payload.get('maneuvers_desc_dict') or {}
    readied = set()
    for group in payload.get('maneuvers_readied_names') or []:
        readied.update(str(x) for x in (group or []))
    strike_avg, strike_note = _best_bonus_dice((n, desc.get(n) or '') for n in sorted(readied))
    return {'stance': stance_avg, 'stance_note': stance_note,
            'strike': strike_avg, 'strike_note': strike_note}


def castable_spells(payload):
    """Every spell name (lowercased) this character's spellbooks can reach.

    `spell_list_choose_from` is per-castable-level, so membership means the class can actually
    cast it. For prepared casters that is exact (a cleric can prepare any list spell tomorrow);
    for spontaneous casters it slightly overstates (the pool, not the known picks) -- an upper
    bound, consistent with the metric's declared sweaty-round semantics.
    """
    out = set()
    for book in payload.get('spellbooks') or []:
        for level_list in book.get('spell_list_choose_from') or []:
            if isinstance(level_list, (list, tuple)):
                out.update(str(s).strip().lower() for s in level_list)
    return out


def buff_shifts(payload, mods, level, two_handed, ranged):
    """The curated spell-buff fold (power_adders.json::spell_buffs), split by duration tier.

    Returns {tier: {'attack','damage','extra_attack','size_steps','ac','saves','notes'}} for
    tier in ('persistent', 'combat'). Offensive numbers are folded into the real axes by
    offence(); 'ac'/'saves' accumulate ONLY into the buffed diagnostics -- the base ac/save axes
    are parity-locked to derive.js. Caster level is the capped character level, the same upper
    bound the blast rule uses. Stat bonuses shift attack/damage like rage does (half the bonus,
    1.5x two-handed damage, Dex drives ranged attack).
    """
    table = adders()
    known = castable_spells(payload)
    tiers = {t: {'attack': 0.0, 'damage': 0.0, 'extra_attack': 0, 'size_steps': 0,
                 'ac': 0.0, 'saves': 0.0, 'dr': 0, 'notes': []} for t in ('persistent', 'combat')}
    if not known:
        return tiers
    caster = min(level, 20)
    for name, spec in (table.get('spell_buffs') or {}).items():
        if name.startswith('_') or str(name).lower() not in known:
            continue
        tier = tiers.get(str(spec.get('tier') or ''))
        if tier is None:
            continue
        for effect in spec.get('effects') or []:
            model = effect.get('model')
            targets = set(effect.get('targets') or [])
            if model == 'flat':
                amount = float(effect.get('amount') or 0)
            elif model == 'scaled_flat':
                per = max(1, _int(effect.get('per'), 3))
                amount = float(min(_int(effect.get('cap'), 99),
                                   max(_int(effect.get('min'), 1), caster // per)))
            elif model == 'stat_bonus':
                bonus = _int(effect.get('amount'))
                stat = str(effect.get('stat') or 'str').lower()
                shift = bonus // 2
                if stat == 'str' and not ranged:
                    tier['attack'] += shift
                    tier['damage'] += shift * (1.5 if two_handed else 1.0)
                elif stat == 'dex' and ranged:
                    tier['attack'] += shift
                continue
            elif model == 'size_step':
                tier['size_steps'] += 1
                tier['attack'] -= 1          # size penalty to hit
                continue
            elif model == 'extra_attack':
                tier['extra_attack'] = 1     # haste-family effects never stack with each other
                continue
            elif model == 'dr':
                tier['dr'] = max(tier['dr'], _int(effect.get('amount')))
                continue
            else:
                continue
            for target in targets:
                if target in tier:
                    tier[target] += amount
        tiers[str(spec['tier'])]['notes'].append(name)
    return tiers


def _step_dice(count, faces, steps):
    for _ in range(max(0, steps)):
        stepped = _SIZE_STEP.get((count, faces))
        count, faces = stepped if stepped else (count + 1, faces)
    return count, faces


def cr_for_level(level):
    """PF1e's published offset: a creature with PC class levels is CR = character level - 1.

    Level 1 lands on CR 1/2, which is exactly where the published table starts -- so the whole
    1-40 band resolves without inventing a row.
    """
    level = max(1, int(level or 1))
    return 0.5 if level == 1 else float(level - 1)


def benchmark_row(level):
    return benchmarks().get(cr_for_level(level))


# --------------------------------------------------------------------------- helpers

def _int(value, default=0):
    """Payload numerics arrive as str as often as int ('armor_ac' is "8")."""
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _mod(score):
    return math.floor((score - 10) / 2)


_NUMERIC = re.compile(r'^[+-]?\d+$')


def _eval_formula(formula):
    """A change's numeric value, or None when it is not a plain integer.

    Deliberately narrow. `derive.js` has a small formula evaluator with the sheet's variables in
    scope; this module has no sheet, so anything referencing one is UNRESOLVED and contributes
    zero -- which is also what derive.js does with an unresolved part (`sumParts` skips it). The
    count of skipped formulas rides along on the profile so the blindness is visible.
    """
    text = str(formula).strip()
    return int(text) if _NUMERIC.match(text) else None


def iter_changes(payload):
    """Every always-on pf1 change on the character, as (target, type, value_or_None)."""
    for key in ALWAYS_ON_CHANGE_KEYS:
        for entry in (payload.get(key) or {}).values():
            for change in (entry or {}).get('changes') or []:
                yield (str(change.get('target') or ''), str(change.get('type') or ''),
                       _eval_formula(change.get('formula')))
    enhancements = payload.get('enhancement_effects_dict') or {}
    for section in WORN_ENHANCEMENT_SECTIONS:
        for entry in (enhancements.get(section) or {}).values():
            for change in (entry or {}).get('changes') or []:
                # `set` operators (Spell Resistance 13) are not additive bonuses; skip them.
                if str(change.get('operator') or 'add') != 'add':
                    continue
                yield (str(change.get('target') or ''), str(change.get('type') or ''),
                       _eval_formula(change.get('formula')))


def ledger_sum(payload, targets):
    """Plain sum of resolved always-on changes hitting `targets`, plus an unresolved count.

    Plain, not typed-max -- see TYPED_STACKING_NOTE.
    """
    total = unresolved = 0
    for target, _type, value in iter_changes(payload):
        if target not in targets:
            continue
        if value is None:
            unresolved += 1
        else:
            total += value
    return total, unresolved


def class_levels(payload):
    """{lowercased class name: level} from the payload's `classes` list.

    The nova and dr tables key on these names, listing chained and unchained variants explicitly
    ('rogue' and 'rogue (unchained)' are separate class_data.json keys and separate rows there).
    """
    out = {}
    for entry in payload.get('classes') or []:
        if isinstance(entry, dict) and entry.get('name'):
            name = str(entry['name']).strip().lower()
            out[name] = max(out.get(name, 0), _int(entry.get('level')))
    return out


def _scale_value(scale, level):
    """Highest value whose (numeric-string) key is <= level -- the shape rage and bard song share.

    {"1": 4, "11": 6, "20": 8} at level 13 -> 6. Returns 0 below the first threshold.
    """
    best = 0
    best_key = -1
    for key, value in (scale or {}).items():
        threshold = _int(key, default=-1)
        if 0 <= threshold <= level and threshold > best_key:
            best_key, best = threshold, _int(value)
    return best


# --------------------------------------------------------------------------- abilities

def ability_scores(payload):
    """Final ability scores.

    `payload[ab]` is the rolled score with racial folded in (`race_func.apply_racial_stats` adds
    into the stats dict). `inherents` and `level_up_stats` are separate and must be added -- see
    the module docstring's trap 1. Luck's attribute payout reaches the sheet as ordinary pf1
    ability changes and so arrives through the ledger.
    """
    inherent = payload.get('inherents') or {}
    levelup = payload.get('level_up_stats') or {}
    scores = {}
    for ab in ABILITIES:
        base = _int(payload.get(ab), 10)
        bonus, _ = ledger_sum(payload, {ab})
        scores[ab] = base + _int(inherent.get(ab)) + _int(levelup.get(ab)) + bonus
    return scores


def ability_mods(payload):
    return {ab: _mod(score) for ab, score in ability_scores(payload).items()}


# --------------------------------------------------------------------------- defence

def armor_class(payload, mods=None):
    """AC, touch AC and flat-footed AC, folded the way derive.js folds them.

    Size is assumed Medium: the payload carries no size key and `derive.js`'s `sizeInfo` falls back
    to Medium for a character with no `_sheet`. A Small race therefore reads 1 low on AC and attack;
    recorded on the profile rather than guessed at.
    """
    mods = mods or ability_mods(payload)
    # ARMOUR ENHANCEMENT IS NOT IN armor_ac. `armor_enhancement_bonus` is a separate payload key,
    # it produces no `ac` change in item_changes_dict, and derive.js reads only `data.armor_ac` --
    # so the standalone web sheet renders every enhanced character 1-5 AC low. The metric measures
    # the CHARACTER, not the rendering bug, so it counts them; check_derive_parity.mjs asserts the
    # resulting delta equals exactly these two numbers, which makes it a regression test for the
    # sheet. Foundry is unaffected: the module builds real armour items and pf1 does the maths.
    armor = _int(payload.get('armor_ac')) + _int(payload.get('armor_enhancement_bonus'))
    shield = _int(payload.get('shield_ac')) + _int(payload.get('shield_enhancement_bonus'))
    max_dex = payload.get('armor_max_dex_bonus')
    dex = mods['dex']
    if str(max_dex).strip() not in ('', 'None'):
        dex = min(dex, _int(max_dex))

    normal, unresolved = ledger_sum(payload, AC_TARGETS)
    touch, _ = ledger_sum(payload, AC_TOUCH_TARGETS)
    flat, _ = ledger_sum(payload, AC_FLAT_TARGETS)
    return {
        'ac': 10 + armor + shield + dex + normal,
        'ac_touch': 10 + dex + touch,
        'ac_flat': 10 + armor + shield + flat,
        'unresolved_changes': unresolved,
        # What the web sheet will be low by, until derive.js folds these in.
        'sheet_shortfall': _int(payload.get('armor_enhancement_bonus'))
                           + _int(payload.get('shield_enhancement_bonus')),
    }


def saving_throws(payload, mods=None):
    """save_bases is authoritative -- the backend stacks it per class for multiclass builds."""
    mods = mods or ability_mods(payload)
    bases = payload.get('save_bases') or {}
    ability = {'fort': 'con', 'ref': 'dex', 'will': 'wis'}
    out = {}
    for save in SAVES:
        bonus, _ = ledger_sum(payload, {save, 'allSavingThrows'})
        out[save] = _int(bases.get(save)) + mods[ability[save]] + bonus
    return out


# Payload buckets whose text the character actually HOLDS at its level AND whose prose states the
# current value. class_ability_desc is deliberately NOT here (get_class_abilities has no level
# filter -- an L16 fighter carries the 19th-level armor mastery text), and neither is the chosen
# 'class features' bucket: a chosen option is held, but its prose states scaling maxima and
# conditionals ("to a maximum of DR 15/silver", "DR 10/- against swarm damage") -- the first
# baseline read DR 15 off a level-5 character that way. Choice-granted DR belongs in the curated
# dr table, per source, when a role needs it.
_HELD_TEXT_KEYS = ('profession_ability_items', 'profession_feats', 'feats', 'class_feats',
                   'trainer_feats', 'traits')


def _held_texts(payload):
    """(bucket, text) for every string in the level-gated held buckets, two levels deep."""
    for key in _HELD_TEXT_KEYS:
        value = payload.get(key)
        stack = [value]
        while stack:
            node = stack.pop()
            if isinstance(node, str):
                yield key, node
            elif isinstance(node, dict):
                stack.extend(node.values())
            elif isinstance(node, (list, tuple)):
                stack.extend(node)


def damage_reduction(payload):
    """Always-on DR, from the curated class table plus text the character holds.

    DR does not stack in PF1e, so the axis is the MAX, not a sum. The pf1 change vocabulary in this
    stack has no dr/eres target, so nothing arrives through the ledger -- the sources are the
    power_adders.json::dr class rules (barbarian's scaler, the fighter's armor mastery) and a
    regex over the level-gated held-text buckets (a profession rank granting "DR 2/-", a feat).
    Energy resistance is harvested the same way but stays a diagnostic: no axis, by ruling, until
    a benchmark or a role needs it.
    """
    table = adders()
    levels = class_levels(payload)
    best, sources = 0, []
    for name, spec in (table.get('dr') or {}).items():
        if name.startswith('_'):
            continue
        model = spec.get('model')
        for cls, params in (spec.get('classes') or {}).items():
            level = levels.get(str(cls).lower())
            if not level:
                continue
            value = 0
            if model == 'scaling_dr':
                start, per = _int(params.get('start'), 7), max(1, _int(params.get('per'), 3))
                if level >= start:
                    value = min(_int(params.get('cap'), 99), (level - start) // per + 1)
            elif model == 'flat_dr_at':
                if level >= _int(params.get('level'), 99):
                    value = _int(params.get('amount'))
            if value > best:
                best, sources = value, [f'{name}:{cls}']
    eres = {}
    for bucket, text in _held_texts(payload):
        for match in _DR_TEXT.finditer(text):
            value = int(match.group(1))
            if value > best:
                best, sources = value, [f'text:{bucket}']
        for match in _ERES_TEXT.finditer(text):
            kind = (match.group(1) or match.group(3) or '').lower()
            value = int(match.group(2) or match.group(4) or 0)
            if kind and value > eres.get(kind, 0):
                eres[kind] = value
    return {'dr': best, 'sources': sources, 'eres': eres}


# --------------------------------------------------------------------------- weapon

_CRIT = re.compile(r'(?:(\d+)\s*-\s*20\s*/\s*)?x\s*(\d+)', re.I)
_DICE = re.compile(r'(\d+)d(\d+)')


def weapon_entry(payload):
    return weapons().get(str(payload.get('weapon_name') or '').strip().lower())


def _medium_damage_dice(entry):
    """Average damage of the medium-size dice, from a 'damage' string like
    '1d4 (small), 1d6 (medium)'. Returns (average, count, faces)."""
    text = str((entry or {}).get('damage') or '')
    medium = None
    for match in _DICE.finditer(text):
        tail = text[match.end():match.end() + 12].lower()
        if 'medium' in tail:
            medium = match
            break
    if medium is None:
        medium = _DICE.search(text)
    if medium is None:
        return 0.0, 0, 0
    count, faces = int(medium.group(1)), int(medium.group(2))
    return count * (faces + 1) / 2.0, count, faces


def _crit(entry):
    """(threat_range_size, multiplier) -- '19-20/x2' -> (2, 2), 'x3' -> (1, 3)."""
    match = _CRIT.search(str((entry or {}).get('critical') or 'x2'))
    if not match:
        return 1, 2
    low, mult = match.group(1), int(match.group(2))
    return (21 - int(low)) if low else 1, mult


def _is_ranged(entry):
    return bool(str((entry or {}).get('range') or '').strip())


def _is_two_handed(entry):
    return 'two-handed' in str((entry or {}).get('category') or '').lower()


def _is_light(entry):
    return 'light' in str((entry or {}).get('category') or '').lower()


# --------------------------------------------------------------------------- offence

def _feat_names(payload):
    """Every feat the character actually has, across the buckets that hold them."""
    names = set()
    for key in ('feats', 'class_feats', 'flavor_feats', 'story_feats', 'trainer_feats',
                'profession_feats', 'teamwork_feats', 'bloodline_feats', 'mt_feats',
                'sphere_feats', 'flaw_feats'):
        value = payload.get(key)
        if isinstance(value, dict):
            names.update(str(n) for n in value)
        elif isinstance(value, (list, tuple)):
            for item in value:
                names.add(str(item[0]) if isinstance(item, (list, tuple)) and item else str(item))
    return names


def _power_attack_shift(bab, entry, two_handed):
    """PF1e Power Attack / Deadly Aim / Piranha Strike: -1 attack, +2 damage per 4 BAB."""
    steps = 1 + bab // 4
    return -steps, steps * 2 * (1.5 if two_handed else 1.0)


def _blast(payload, table, mods, level, target_ac):
    """The spheres destructive blast, an at-will standard action -- so it competes with the weapon
    routine rather than adding to it.

    This rule sat in power_adders.json from day one and was never folded -- IMPLEMENTED_RULE_MODELS
    declared `blast_dice` while offence() dispatched nothing, the exact silent-nothing failure the
    gates exist for, one artifact deep. Caster level is the capped character level (the payload
    exports no sphere CL; an upper bound, stated here and in the rule's note). The blast is a
    ranged touch attack but the CR table has no touch column, so the expected figure is scored
    against full benchmark AC and reads deliberately low; the raw (all-hits) figure is unaffected.
    """
    spec = (table.get('rules') or {}).get('spheres_destructive_blast')
    if not spec or spec.get('model') != 'blast_dice':
        return None
    held = {str(entry.get('sphere') or '').strip().lower()
            for entry in payload.get('spheres_chosen') or [] if isinstance(entry, dict)}
    if str(spec.get('requires_sphere') or '').lower() not in held:
        return None
    caster = min(level, 20)
    dice = max(_int(spec.get('minimum_dice'), 1), caster // max(1, _int(spec.get('per_caster_levels'), 2)))
    faces = _int(str(spec.get('dice') or 'd6').lstrip('dD'), 6)
    average = dice * (faces + 1) / 2.0
    attack = _int(payload.get('bab_total')) + mods['dex']
    hit = min(0.95, max(0.05, (21 - (target_ac - attack)) / 20.0))
    return {
        'dpr_raw': round(average + (1 / 20.0) * average, 2),
        'dpr_expected': round(hit * average + min(1 / 20.0, hit) * average, 2),
        'note': f'spheres_destructive_blast: {dice}d{faces} ranged touch (CL=capped level)',
    }


def _talent_shifts(payload):
    """The spheres talents' structured `changes`, folded by target.

    combat_talent_items / magic_talent_items already carry pf1 changes in the payload; plain-int
    formulas fold (the same narrowness as _eval_formula), offensive targets into the real axes,
    defensive into the buffed diagnostics only. Talents are treated as always-available (martial
    focus up) -- an upper bound, declared in the assumptions.
    """
    out = {'attack': 0, 'damage': 0, 'ac': 0, 'saves': 0}
    for key in ('combat_talent_items', 'magic_talent_items'):
        for item in payload.get(key) or []:
            if not isinstance(item, dict):
                continue
            for change in item.get('changes') or []:
                value = _eval_formula(change.get('formula'))
                if value is None:
                    continue
                target = str(change.get('target') or '')
                if target in ATTACK_TARGETS:
                    out['attack'] += value
                elif target in ('damage', 'wdamage'):
                    out['damage'] += value
                elif target in AC_TARGETS:
                    out['ac'] += value
                elif target in ('fort', 'ref', 'will', 'allSavingThrows'):
                    out['saves'] += value
    return out


def _has_boots_of_speed(payload):
    return any('boots of speed' in str(item).lower()
               for item in payload.get('equipment_list') or [])


def _vital_strike_extra(table, feats):
    """Extra weapon-dice multiples from the best held Vital Strike feat (0 when none)."""
    best = 0
    for name, spec in table['feats'].items():
        if name.startswith('_'):
            continue
        if spec.get('model') == 'vital_strike' and name in feats:
            best = max(best, _int(spec.get('extra_weapon_dice')))
    return best


def _nova_shifts(payload, table, mods, two_handed, ranged):
    """(flat_attack, flat_damage, precision_damage, extra_attacks, notes) for the nova round.

    flat_damage multiplies on a crit like every other per-hit bonus in this model; precision
    (sneak attack) deliberately does not -- PF1e precision dice never multiply.
    """
    levels = class_levels(payload)
    assumptions = table.get('_assumptions') or {}
    attack = damage = precision = 0.0
    extra_attacks = 0
    notes = []
    for name, spec in (table.get('nova') or {}).items():
        if name.startswith('_'):
            continue
        model = spec.get('model')
        for cls, params in (spec.get('classes') or {}).items():
            level = levels.get(str(cls).lower())
            if not level:
                continue
            if model == 'rage' and not ranged:
                bonus = _scale_value(params.get('scale'), level)
                shift = bonus // 2                       # Str-style bonus -> attack and damage
                if shift:
                    attack += shift
                    damage += shift * (1.5 if two_handed else 1.0)
                    notes.append(f'{name}:{cls} +{bonus} Str-equivalent')
            elif model == 'smite':
                attack += max(0, mods['cha'])
                damage += level
                notes.append(f'{name}:{cls} +cha to hit, +{level} damage')
            elif model == 'challenge':
                damage += level
                notes.append(f'{name}:{cls} +{level} damage')
            elif model == 'sneak_attack':
                if not assumptions.get('nova_flanking', True):
                    continue
                start, per = _int(params.get('start'), 1), max(1, _int(params.get('per'), 2))
                if level >= start:
                    dice = (level - start) // per + 1
                    precision += dice * 3.5
                    notes.append(f'{name}:{cls} +{dice}d6 precision (flanking)')
            elif model == 'inspire_courage':
                bonus = _scale_value(params.get('scale'), level)
                if bonus:
                    attack += bonus
                    damage += bonus
                    notes.append(f'{name}:{cls} +{bonus} attack and damage')
            elif model == 'ki_extra_attack':
                extra_attacks = max(extra_attacks, 1)
                notes.append(f'{name}:{cls} ki extra attack')
    return attack, damage, precision, extra_attacks, notes


def _combat_defense(payload, table, mods, feats, bab):
    """The wall pass (ruling 2026-08-12): everything defensive the sheet-state ac cannot show.

    Returns {'ac_bonus', 'cmd_bonus', 'dr', 'notes'} -- the ac_bonus lands on the new ac_combat
    axis ONLY (the base ac axis stays parity-locked to derive.js), cmd_bonus on the cmd axis.
    Components, all RAW by ruling: the defensive posture (fighting defensively +2, +3 with 3
    Acrobatics ranks, +1 more and half penalty with Crane Style; ambient Combat Expertise
    1+BAB/4), the active stance's AC (best of parsed-flat and the curated stance_ac table --
    one stance at a time, so MAX not sum), class AC (monk Wis, unarmored only), flat_ac feat
    rows (Snapping Turtle), the ambient house-waived Dodge, wild shape natural armor, and a
    '+N bonus to AC' harvest over held profession text.
    """
    notes = []
    ac_bonus = 0.0
    cmd_bonus = 0.0

    # Posture: fighting defensively (universal) + ambient Combat Expertise.
    posture = table.get('posture') or {}
    fd = posture.get('fighting_defensively') or {}
    ranks = payload.get('skill_ranks') or {}
    acrobatics = _int(ranks.get('acrobatics')) if isinstance(ranks, dict) else 0
    fd_ac = _int(fd.get('ac_with_acrobatics_3'), 3) if acrobatics >= 3 else _int(fd.get('ac'), 2)
    if 'Crane Style' in feats:
        fd_ac += _int(fd.get('crane_style_bonus'), 1)
    # The two house posture rows (V4, ruling 2026-08-13) key off what the sheet carries -- the
    # feat / the trait -- so no request flag reaches the metric and a RAW two-weapon character
    # scores its TWD honestly too.
    if 'Two-Weapon Defense' in feats:
        twd = _int((posture.get('two_weapon_defense') or {}).get('ac_fighting_defensively'), 2)
        fd_ac += twd
        notes.append(f'two-weapon defense +{twd} while fighting defensively')
    traits_held = {str(t).strip().lower() for t in payload.get('selected_traits') or []}
    if 'cautious warrior' in traits_held:
        cw = _int((posture.get('cautious_warrior_trait') or {}).get('ac_fighting_defensively'), 1)
        fd_ac += cw
        notes.append(f'cautious warrior trait +{cw} while fighting defensively')
    ac_bonus += fd_ac
    notes.append(f'fighting defensively +{fd_ac}')
    if 'Combat Expertise' in feats:
        ce = 1 + bab // 4
        ac_bonus += ce
        cmd_bonus += ce
        notes.append(f'combat expertise +{ce} ac/cmd')

    # The active stance: MAX of parsed flat AC and the curated table.
    level = _int(payload.get('total_level') or payload.get('level'), 1)
    stance_best, stance_note = 0, None
    curated = table.get('stance_ac') or {}
    for name in payload.get('stances_chosen') or []:
        text = stance_texts().get(str(name).strip().lower(), '')
        value = max((int(m.group(1)) for m in _AC_BONUS_TEXT.finditer(text)), default=0)
        row = curated.get(str(name)) or {}
        if row and not str(name).startswith('_'):
            value = max(value, _int(row.get('base')) + (
                level // _int(row.get('per_hd'), 99) if row.get('per_hd') else 0))
        if value > stance_best:
            stance_best, stance_note = value, f'stance {name} +{value} ac'
    if stance_best:
        ac_bonus += stance_best
        notes.append(stance_note)

    # Defensive-sphere talents (V4, ruling 2026-08-13): curated fight-state values for prose the
    # ledger never carries. Keyed to what the sheet holds (combat_talent_items), so no request
    # flag reaches the metric; requires_shield rows key off the payload's own gear.
    sphere_rows = {str(k).lower(): v for k, v in (table.get('sphere_defense') or {}).items()
                   if not str(k).startswith('_')}
    if sphere_rows:
        has_shield = _int(payload.get('shield_ac')) > 0
        for item in payload.get('combat_talent_items') or []:
            row = sphere_rows.get(str((item or {}).get('name') or '').strip().lower())
            if not row or (row.get('requires_shield') and not has_shield):
                continue
            value = _int(row.get('ac')) + (bab // _int(row.get('per_bab'), 99)
                                           if row.get('per_bab') else 0)
            if value:
                ac_bonus += value
                notes.append(f"sphere {item.get('name')} +{value} ac")

    # Class AC (monk Wis) -- unarmored only; the payload's own gear decides.
    unarmored = _int(payload.get('armor_ac')) == 0 and _int(payload.get('shield_ac')) == 0
    levels = class_levels(payload)
    for name, spec in (table.get('ac_class') or {}).items():
        if name.startswith('_') or spec.get('model') != 'stat_to_ac' or not unarmored:
            continue
        for cls in spec.get('classes') or {}:
            cls_level = levels.get(str(cls).lower())
            if not cls_level:
                continue
            stat = str(spec.get('stat') or 'wis').lower()
            value = max(0, mods.get(stat, 0)) + cls_level // max(1, _int(spec.get('level_per'), 4))
            if value:
                ac_bonus += value
                notes.append(f'{name}:{cls} +{value} ac')
            break

    # flat_ac feat rows (style feats) + the ambient Dodge, both ac_combat-only by design.
    for name, spec in table['feats'].items():
        if not name.startswith('_') and spec.get('model') == 'flat_ac' and name in feats:
            amount = _int(spec.get('amount'))
            if amount:
                ac_bonus += amount
                notes.append(f'{name} +{amount} ac')
    if 'dodge' in waived_feats() and mods['dex'] >= 1:
        ac_bonus += 1
        notes.append('ambient dodge +1 ac')

    # Wild shape: natural armor by druid band (defense only -- natural-attack routines stay blind).
    ws = (table.get('wild_shape') or {}).get('druid') or {}
    druid_level = levels.get('druid', 0)
    band_na = 0
    for threshold, band in sorted((ws.get('bands') or {}).items(), key=lambda kv: int(kv[0])):
        if druid_level >= int(threshold):
            band_na = _int(band.get('na'))
    if band_na:
        ac_bonus += band_na
        notes.append(f'wild shape +{band_na} natural armor')

    # Held-text AC harvest (profession ranks and the like) -- same buckets as the DR harvest.
    harvest = 0
    for _bucket, text in _held_texts(payload):
        for match in _AC_BONUS_TEXT.finditer(text):
            harvest += int(match.group(1))
    if harvest:
        ac_bonus += harvest
        notes.append(f'held-text ac +{harvest}')

    return {'ac_bonus': ac_bonus, 'cmd_bonus': cmd_bonus, 'notes': notes}


def offence(payload, mods=None):
    """Full-attack routine and expected damage per round against the benchmark AC.

    TWO round shapes (map: optimal-builder, ruling 2026-08-11). The sustained round is unchanged:
    single target, full attack, round two, no pre-cast buffs, nothing situational. The NOVA round
    (`burst_raw`) is the round-1 alpha: the same routine with the limited-use class offense the
    character actually has switched on -- rage, smite, challenge, bard song, flanked sneak attack
    (power_adders.json::nova) -- benchmarked against the same damage_high column, so ratio > 1 is
    a spike above the table. Pre-cast buffs stay out of BOTH rounds. Everything excluded is named
    in `blind`.
    """
    mods = mods or ability_mods(payload)
    table = adders()
    feats = _feat_names(payload)
    entry = weapon_entry(payload)
    level = _int(payload.get('total_level') or payload.get('level'), 1)
    row = benchmark_row(level) or {}
    target_ac = _int(row.get('ac'), 10)

    bab = _int(payload.get('bab_total'))
    # The table's waived (ambient) feats -- held by rule, absent from every payload bucket.
    feats |= ambient_feats(mods, bab)
    enh = _int(payload.get('weapon_enhancement_bonus'))
    ranged = _is_ranged(entry)
    two_handed = _is_two_handed(entry)

    # Attack stat: Dex for ranged, Str for melee unless Weapon Finesse makes Dex better.
    if ranged:
        attack_mod = mods['dex']
    elif 'Weapon Finesse' in feats and mods['dex'] > mods['str'] and not two_handed:
        attack_mod = mods['dex']
    else:
        attack_mod = mods['str']
    # Damage stat: no ability to thrown/projectile damage in this model.
    damage_mod = 0.0 if ranged else mods['str'] * (1.5 if two_handed else 1.0)

    flat_attack = flat_damage = 0.0
    notes = []
    for name, spec in table['feats'].items():
        if name.startswith('_') or name not in feats:
            continue
        model, condition = spec.get('model'), spec.get('condition')
        if condition == 'within_30_ft' and not table['_assumptions']['within_30_ft']:
            continue
        if condition == 'standard_action_only':
            continue          # the declared round is a full attack
        if condition == 'ranged' and not ranged:
            continue
        if condition in ('melee', 'melee_two_handed', 'light_melee') and ranged:
            continue
        if condition == 'light_melee' and not _is_light(entry):
            continue
        if condition == 'melee_two_handed' and not two_handed:
            continue
        if condition == 'light_offhand':
            continue          # no two-weapon routine in this model

        if model == 'flat_attack':
            flat_attack += _int(spec.get('amount'))
        elif model == 'flat_damage':
            flat_damage += _int(spec.get('amount'))
        elif model == 'power_attack':
            if table['_assumptions'].get(f"{name.lower().replace(' ', '_').replace('-', '_')}_active", True):
                shift_attack, shift_damage = _power_attack_shift(bab, entry, two_handed)
                flat_attack += shift_attack
                flat_damage += shift_damage
        elif model == 'caster_level_scaled_damage':
            caster = _int(payload.get('initiator_level')) or level
            flat_damage += max(_int(spec.get('minimum'), 1), caster // _int(spec.get('per'), 5))

    ledger_attack, _ = ledger_sum(payload, ATTACK_TARGETS)
    base_attack = bab + attack_mod + enh + flat_attack + ledger_attack

    # PoW: a readied strike's near-universal text adds the initiation modifier to damage. Only the
    # presence of a readied strike is modelled; scaling dice and riders are blind, by ruling.
    readied = payload.get('maneuvers_readied_names') or []
    has_strike = any(names for names in readied if names)
    if has_strike:
        stat = str(payload.get('initiation_stat') or '').lower()[:3]
        if stat in mods:
            flat_damage += mods[stat]
            notes.append('pow_readied_strike: +initiation modifier to damage')

    dice_avg, dice_count, dice_faces = _medium_damage_dice(entry)
    threat, multiplier = _crit(entry)
    if 'Improved Critical' in feats:
        threat = threat * 2

    # The always-on 3pp layer (metric v2): stance dice ride every attack in BOTH rounds, spheres
    # talent changes fold by target, and PERSISTENT spell buffs (10+ min/level -- up before every
    # fight) join the sustained round. Combat-tier buffs join the nova round below.
    pw = pow_dice(payload)
    talents = _talent_shifts(payload)
    buffs = buff_shifts(payload, mods, level, two_handed, ranged)
    persistent, combat = buffs['persistent'], buffs['combat']
    if pw['stance_note']:
        notes.append(f"stance dice: {pw['stance_note']}")
    if talents['attack'] or talents['damage']:
        notes.append(f"sphere talents: +{talents['attack']} attack, +{talents['damage']} damage")
    if persistent['notes']:
        notes.append(f"persistent buffs: {', '.join(persistent['notes'])}")

    base_attack += talents['attack'] + persistent['attack']
    per_hit = (dice_avg + damage_mod + enh + flat_damage + pw['stance']
               + talents['damage'] + persistent['damage'])

    iteratives = max(1, (bab - 1) // 5 + 1) if bab else 1
    if 'Rapid Shot' in feats and ranged:
        iteratives += 1
        base_attack -= 2

    def routine(bonuses, hit_part, crit_part, precision_part, once):
        """All-hits and hit-weighted damage for a list of attack bonuses.

        `crit_part` is what multiplies on a crit (per-hit flat damage does, precision dice and
        one-shot strike dice never do). `once` lands a single time, weighted by the FIRST
        attack's hit chance on the expected side.
        """
        raw = expected = 0.0
        for attack in bonuses:
            hit = min(0.95, max(0.05, (21 - (target_ac - attack)) / 20.0))
            raw += hit_part + precision_part + (threat / 20.0) * (multiplier - 1) * crit_part
            expected += (hit * (hit_part + precision_part)
                         + min(threat / 20.0, hit) * (multiplier - 1) * crit_part)
        if once and bonuses:
            first_hit = min(0.95, max(0.05, (21 - (target_ac - bonuses[0])) / 20.0))
            raw += once
            expected += first_hit * once
        return raw, expected

    # TWO damage numbers, deliberately (map: optimal-builder, ruling 2026-08-11). The CR table's
    # damage_high is RAW full-attack damage -- every attack lands, crits average in; the expected
    # figure rides along unbenchmarked and the gap between them IS the accuracy story.
    attacks = [base_attack - 5 * index for index in range(iteratives)]
    dpr_raw, dpr_expected = routine(attacks, per_hit, per_hit, 0.0, 0.0)
    dpr_raw, dpr_expected = round(dpr_raw, 2), round(dpr_expected, 2)

    # An at-will blast is a routine of its own; the better routine IS the character's damage.
    blast = _blast(payload, table, mods, level, target_ac)
    if blast and blast['dpr_raw'] > dpr_raw:
        dpr_raw, dpr_expected = blast['dpr_raw'], blast['dpr_expected']
        notes.append(blast['note'])

    # ---- the nova round: the fully-juiced fight (ruling 2026-08-11, the sweaty pass) ----
    # Limited-use class offense (rage, smite, ki, ...), COMBAT-tier buffs (divine power,
    # righteous might, haste), an activated haste item, the best readied strike's dice once, and
    # size steps on the weapon dice. burst = the best of the full-attack routine, the
    # vital-strike standard-action alpha, and the blast.
    nova_attack, nova_damage, precision, ki_extra, nova_notes = _nova_shifts(
        payload, table, mods, two_handed, ranged)
    if _has_boots_of_speed(payload) and not combat['extra_attack']:
        combat['extra_attack'] = 1
        combat['attack'] += 1
        nova_notes.append('boots of speed: haste (extra attack, +1 to hit)')
    if combat['notes']:
        nova_notes.append(f"combat buffs: {', '.join(combat['notes'])}")
    if pw['strike_note']:
        nova_notes.append(f"strike dice (once): {pw['strike_note']}")

    steps = int(combat['size_steps'])
    if steps and dice_count:
        stepped_count, stepped_faces = _step_dice(dice_count, dice_faces, steps)
        nova_dice_avg = stepped_count * (stepped_faces + 1) / 2.0
        nova_notes.append(f'size step: {dice_count}d{dice_faces} -> '
                          f'{stepped_count}d{stepped_faces}')
    else:
        nova_dice_avg = dice_avg

    nova_base = base_attack + nova_attack + combat['attack']
    nova_per_hit = per_hit - dice_avg + nova_dice_avg + nova_damage + combat['damage']
    extras = int(combat['extra_attack']) + ki_extra
    nova_bonuses = [nova_base] * extras + [nova_base - 5 * index for index in range(iteratives)]
    burst_raw, burst_expected = routine(nova_bonuses, nova_per_hit, nova_per_hit,
                                        precision, pw['strike'])

    # The standard-action alpha: one attack, weapon dice multiplied by the best held Vital
    # Strike, everything else riding along. Precision still lands (a flanked vital strike).
    vital_extra = _vital_strike_extra(table, feats)
    if vital_extra:
        alpha_per_hit = nova_per_hit + nova_dice_avg * vital_extra
        alpha_raw, alpha_expected = routine([nova_base], alpha_per_hit, alpha_per_hit,
                                            precision, pw['strike'])
        if alpha_raw > burst_raw:
            burst_raw, burst_expected = alpha_raw, alpha_expected
            nova_notes.append(f'vital strike alpha: +{vital_extra}x weapon dice, one attack')

    if blast and blast['dpr_raw'] > burst_raw:
        burst_raw, burst_expected = blast['dpr_raw'], blast['dpr_expected']
        nova_notes = [blast['note']]

    defense = _combat_defense(payload, table, mods, feats, bab)

    return {
        'to_hit': base_attack,
        'dpr_raw': dpr_raw,
        'dpr_expected': dpr_expected,
        'burst_raw': round(burst_raw, 2),
        'burst_expected': round(burst_expected, 2),
        'attacks': attacks,
        'per_hit': round(per_hit, 2),
        'target_ac': target_ac,
        'weapon_known': entry is not None,
        'notes': notes,
        'nova_notes': nova_notes,
        # Defensive buff/talent value -- kept OUT of the base ac/save axes (parity-locked to
        # derive.js); they land on the ac_combat axis and the buffed diagnostics instead.
        'buffed_ac_bonus': int(talents['ac'] + persistent['ac'] + combat['ac']),
        'buffed_saves_bonus': int(talents['saves'] + persistent['saves'] + combat['saves']),
        'combat_ac_bonus': defense['ac_bonus'],
        'cmd_bonus': defense['cmd_bonus'],
        'defense_notes': defense['notes'],
        'buff_dr': max(int(persistent['dr']), int(combat['dr'])),
    }


_CASTING_STAT = {'strength': 'str', 'dexterity': 'dex', 'constitution': 'con',
                 'intelligence': 'int', 'wisdom': 'wis', 'charisma': 'cha'}


def caster_axes(payload):
    """Reach and DC for spell and power casters.

    `caster_tier` is the highest spell/power level the character can reach; `dc` is the classic
    10 + level + casting-stat modifier, which is what the CR table's `dc_primary` column benchmarks.
    Vancian SPELL damage is still declared blind (a wizard reads as low-DPR by design rather than
    by accident); the spheres destructive blast, being an at-will attack routine, IS scored -- in
    offence(), not here. See _blast.

    Two payload shapes bite here and are handled rather than guessed at: `casting_tradition` is a
    DICT (the Spheres tradition, carrying `casting_ability_modifier` as a word like "Charisma"),
    and `manifesters` is a LIST of per-class dicts carrying `max_power_level` and
    `manifesting_stat` outright.
    """
    mods = ability_mods(payload)

    # Spell levels: count the entries that carry a nonzero known/prepared count.
    highest = 0
    for key in ('known_list', 'spells_prepared_per_level'):
        entries = payload.get(key)
        if isinstance(entries, (list, tuple)) and entries:
            highest = max(highest, sum(1 for value in entries if _int(value)))

    stat = None
    tradition = payload.get('casting_tradition')
    if isinstance(tradition, dict):
        stat = _CASTING_STAT.get(str(tradition.get('casting_ability_modifier') or '').lower())

    # Psionics scores on this axis only -- max_power_level is stated outright.
    for entry in (payload.get('manifesters') or []):
        if not isinstance(entry, dict):
            continue
        highest = max(highest, _int(entry.get('max_power_level')))
        stat = stat or _CASTING_STAT.get(
            str(entry.get('manifesting_stat') or '').lower(),
            str(entry.get('manifesting_stat') or '').lower()[:3] or None)

    if stat not in mods:
        stat = max(('int', 'wis', 'cha'), key=lambda ab: mods[ab])
    return {
        'dc': (10 + highest + mods[stat]) if highest else 0,
        'caster_tier': highest,
    }


def utility(payload):
    """Skill breadth: how many skills carry meaningful ranks. No CR column exists for this."""
    ranks = payload.get('skill_ranks') or {}
    level = _int(payload.get('total_level') or payload.get('level'), 1)
    threshold = max(1, level // 2)
    if isinstance(ranks, dict):
        return sum(1 for value in ranks.values() if _int(value) >= threshold)
    return 0


# --------------------------------------------------------------------------- the profile

def profile_for(payload):
    """The per-axis profile. Each axis carries {raw, benchmark, ratio}.

    `ratio` is raw / benchmark, so 1.0 is exactly on the CR row. Axes with no benchmark column
    carry benchmark None and ratio None rather than a fabricated denominator.
    """
    level = _int(payload.get('total_level') or payload.get('level'), 1)
    row = benchmark_row(level)
    mods = ability_mods(payload)
    ac = armor_class(payload, mods)
    saves = saving_throws(payload, mods)
    off = offence(payload, mods)
    cast = caster_axes(payload)
    dr = damage_reduction(payload)

    raw = {
        'to_hit': off['to_hit'],
        # dpr_raw vs the table (damage_high is all-hits damage, the table's own semantics);
        # dpr_expected unbenchmarked -- the gap between them is what accuracy costs. See offence().
        'dpr_raw': off['dpr_raw'],
        'dpr_expected': off['dpr_expected'],
        # The nova round, against the SAME damage_high column: ratio > 1 is a spike above the
        # table. burst_expected rides along unbenchmarked, like dpr_expected.
        'burst_raw': off['burst_raw'],
        'burst_expected': off['burst_expected'],
        'dc': cast['dc'],
        'caster_tier': cast['caster_tier'],
        'ac': ac['ac'],
        # The fight-state AC (wall pass): sheet AC + buffs/talents + posture + stance + class AC
        # + style feats + ambient dodge + wild shape + held-text AC. Same CR column as `ac`, so
        # a built wall reads 2x+ the way real table walls do; `ac` itself stays sheet-state and
        # derive.js-parity-locked.
        'ac_combat': ac['ac'] + off['buffed_ac_bonus'] + int(off['combat_ac_bonus']),
        'ac_touch': ac['ac_touch'],
        'ac_flat': ac['ac_flat'],
        # CMD, raw-only (no CR column): 10 + BAB + Str + Dex + ledger cmd + posture cmd.
        'cmd': 10 + _int(payload.get('bab_total')) + mods['str'] + mods['dex']
               + ledger_sum(payload, {'cmd'})[0] + int(off['cmd_bonus']),
        'hp': _int(payload.get('Total_HP')),
        'fort': saves['fort'],
        'ref': saves['ref'],
        'will': saves['will'],
        # No CR column for DR exists, so the axis reports raw-only, like caster_tier.
        'dr': max(dr['dr'], off['buff_dr']),
        'skill_breadth': utility(payload),
    }
    bench = {
        'to_hit': row and row['attack_high'],
        'dpr_raw': row and row['damage_high'],
        'dpr_expected': None,
        'burst_raw': row and row['damage_high'],
        'burst_expected': None,
        'dc': row and row['dc_primary'],
        'caster_tier': None,
        'ac': row and row['ac'],
        'ac_combat': row and row['ac'],
        'ac_touch': None,
        'ac_flat': None,
        'cmd': None,
        'hp': row and row['hp'],
        'fort': row and row['save_good'],
        'ref': row and row['save_good'],
        'will': row and row['save_good'],
        'dr': None,
        'skill_breadth': None,
    }

    multipliers = target_multipliers()
    axes = {}
    for name, value in raw.items():
        mark = bench.get(name)
        if mark:
            # The bar-raising lever: 1.0 today, tuned in cr_benchmarks.json, never here.
            mark = mark * multipliers.get(name, 1.0)
        axes[name] = {
            'raw': value,
            'benchmark': mark,
            'ratio': round(value / mark, 3) if mark else None,
        }

    table = adders()
    return {
        'level': level,
        'cr': cr_for_level(level),
        'cr_extrapolated': bool(row and row.get('extrapolated')),
        'classes': payload.get('c_class_display') or payload.get('c_class'),
        'build_archetype': payload.get('build_archetype'),
        'axes': axes,
        'blind': table['_blind'],
        'assumptions': {k: v for k, v in table['_assumptions'].items() if not k.startswith('_')},
        'diagnostics': {
            'weapon_known': off['weapon_known'],
            'weapon_name': payload.get('weapon_name'),
            # Cash the generator failed to convert into power. The gear-blackout bug hid behind
            # exactly this number being enormous and unprinted.
            'gold_unspent': _int(payload.get('gold')),
            'unresolved_ac_changes': ac['unresolved_changes'],
            'web_sheet_ac_shortfall': ac['sheet_shortfall'],
            'size_assumed': 'medium',
            'typed_stacking': TYPED_STACKING_NOTE,
            'notes': off['notes'],
            'nova_notes': off['nova_notes'],
            'dr_sources': dr['sources'],
            'energy_resistance': dr['eres'],
            # Buffed defense, diagnostics ONLY -- the base ac/save axes are parity-locked to
            # derive.js; this is what the fully-buffed character actually defends at.
            'ac_buffed': ac['ac'] + off['buffed_ac_bonus'],
            'saves_buffed_bonus': off['buffed_saves_bonus'],
            'defense_notes': off['defense_notes'],
        },
    }
