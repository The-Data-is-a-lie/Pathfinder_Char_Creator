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


def choose_path_abilities(character, path_key, tier, extra_pool=None):
    """One ability per tier from the path's merged pool, gated per slot (1st/3rd/6th-tier lists),
    flagged entries skipped -- the flag is load-bearing, not decoration.

    `extra_pool` extends the candidates without touching the data file: the sphere masteries of a
    sphere-using mythic character join here (they are RAW universal path abilities, in house scope
    for sphere users only).

    Returns [{'name', 'tier', 'type', 'source', 'description', 'universal'}, ...] in slot order."""
    pool = dict(path_ability_data()[path_key]['abilities'])
    extra_pool = extra_pool or {}
    pool.update(extra_pool)
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
        candidates = sorted(candidates)
        # A sphere user's few masteries would drown in a ~100-ability pool (one sphere = one
        # mastery = ~1% per pick); the lean keeps the carve-out real without guaranteeing it.
        weights = [EXTRA_POOL_DRAW_WEIGHT if name in extra_pool else 1 for name in candidates]
        name = random.choices(candidates, weights=weights, k=1)[0]
        chosen_lower.add(name.lower())
        chosen.append({'name': name, 'tier': slot_tier, **{
            k: pool[name][k] for k in ('type', 'source', 'description', 'universal')}})
    return chosen


# One sphere held = one mastery among ~100 candidates; a flat draw makes the sphere-user
# carve-out invisible in practice (~1% per pick). This is a lean, not a guarantee.
EXTRA_POOL_DRAW_WEIGHT = 8


# ------------------------------------------------------------------------------------------------
# The tier chassis (ticket 05's five-way classification). Numbers computed here; the power pool is
# a RESOURCE (tracked, never enforced -- the hero_points pattern), surge and the base abilities
# are number+prose, Amazing Initiative's bonus is a pf1 change the module attaches (ticket 06),
# and the ability-score increases ride as an attributable {stat: bonus} dict EXACTLY like
# level_up_stats and the luck payout -- the backend deliberately does not fold bump dicts into the
# exported scores; the sheets apply them where they are visible and attributable.
# ------------------------------------------------------------------------------------------------

_SURGE_STEPS = ((10, '1d12'), (7, '1d10'), (4, '1d8'), (1, '1d6'))

# RAW Mythic Adventures base abilities by the tier that grants them (hand-authored, ticket 05;
# verified against AoN's Mythic Heroes rules page 2026-08-14 -- the ability TEXTS carry the tier,
# the summary table's columns interleave). Tier 6 grants no base ability; evens grant +2 to an
# ability score; surge steps at 1/4/7/10.
BASE_MYTHIC_ABILITIES = (
    (1, 'Hard to Kill', 'Whenever you are below 0 hit points, you automatically stabilize; you '
                        'die at negative Constitution x 2 instead of negative Constitution.'),
    (1, 'Mythic Power', 'A pool of mythic power fueling surge and many mythic abilities: '
                        '3 + 2 per tier uses per day (plus any tradition bonus).'),
    (1, 'Surge', 'Expend one use of mythic power to add the surge die to a d20 roll you just '
                 'made, possibly turning failure into success. The die grows with tier '
                 '(1d6 / 1d8 at 4th / 1d10 at 7th / 1d12 at 10th).'),
    (2, 'Amazing Initiative', 'A bonus on initiative checks equal to your mythic tier. Also, as a '
                              'free action on your turn, expend one use of mythic power to take '
                              'an additional standard action this turn (not usable to cast a '
                              'second spell in a round).'),
    (3, 'Recuperation', 'Restored to full hit points after 8 hours of rest. Also, expend one use '
                        'of mythic power and rest 1 hour to regain half your maximum hit points '
                        'and all class abilities normally regained by resting 8 hours.'),
    (5, 'Mythic Saving Throws', 'Whenever you succeed at a saving throw against a spell or '
                                'special ability from a non-mythic source, you suffer no effect.'),
    (7, 'Force of Will', 'As an immediate action, expend one use of mythic power to reroll a d20 '
                         'roll you just made, or force any non-mythic creature to reroll one it '
                         'just made; the affected creature takes the second result.'),
    (8, 'Unstoppable', 'As a free action, expend one use of mythic power to immediately end one '
                       'of a list of harmful conditions affecting you (bleed, dazed, shaken, '
                       'staggered, and others); usable even when a condition would prevent it.'),
    (9, 'Immortal', 'If you are killed, you return to life 24 hours later regardless of your '
                    'body\'s condition, unless killed by a mythic creature of your tier or '
                    'higher, an artifact, or a deity.'),
    (10, 'Legendary Hero', 'You regain one use of mythic power every hour, in addition to '
                           'completely refreshing your pool each day.'),
)


def surge_die(tier):
    for step, die in _SURGE_STEPS:
        if tier >= step:
            return die
    return '1d6'


def mythic_chassis(character, tier, path_key, extra_power=0):
    """The tier-derived numbers. `extra_power` is the tradition's +MP/day purchases."""
    meta = path_ability_data()[path_key]
    per_tier = meta.get('bonus_hp_per_tier') or 0
    return {
        'power_pool': 3 + 2 * tier + extra_power,
        'surge_die': surge_die(tier),
        'amazing_initiative_bonus': tier if tier >= 2 else 0,
        'bonus_hp': per_tier * tier,
        'base_abilities': [{'name': name, 'tier': gained, 'description': text}
                           for gained, name, text in BASE_MYTHIC_ABILITIES if gained <= tier],
    }


def mythic_ability_bumps(character, tier):
    """+2 to a DIFFERENT ability score at every even tier ('another ability score of your
    choice'), delivered as an attributable {stat: bonus} dict like level_up_stats. Priority is
    the role's stat order when the optimizer set one, else main stat first and a random spread."""
    count = tier // 2
    if not count:
        return {}
    from utils.class_func.power_role import stat_order
    priority = list(stat_order(character) or [])
    if not priority:
        stats = ['str', 'dex', 'con', 'int', 'wis', 'cha']
        main = str(getattr(character, 'main_stat', '') or '').split('/')[0].strip().lower()
        if main in stats:
            stats.remove(main)
            priority = [main] + random.sample(stats, k=len(stats))
        else:
            priority = random.sample(stats, k=len(stats))
    bumps = {}
    for stat in priority[:count]:
        bumps[stat] = bumps.get(stat, 0) + 2
    return bumps


def record_base_abilities(character, chassis):
    """The base tier abilities join class features (bucket 'Mythic Abilities', owner mythic,
    tier stamps) -- automatic grants, not picks, so the bucket has no schedule row."""
    features = character.data_dict['class features']
    bucket = features.setdefault('Mythic Abilities', {})
    for ability in chassis['base_abilities']:
        text = ability['description']
        if ability['name'] == 'Surge':
            text = f"Current surge die: {chassis['surge_die']}. " + text
        if ability['name'] == 'Mythic Power':
            text = f"Current pool: {chassis['power_pool']}/day. " + text
        bucket[ability['name']] = {'benefit': text}
        _record_choice_level(character, 'Mythic Abilities', ability['name'], ability['tier'])
    record_bucket_owner(character, 'Mythic Abilities', 'mythic')


def spell_annotations(character):
    """Mythic spell modes for spells the character already knows -- annotation, never a pick
    (ticket 05): the data/spells.csv columns `mythic`/`mythic_text`/`augmented` render onto known
    spells; the sampler and its weighting are untouched, and no name-keyed mythic lookup ever
    happens because nothing is chosen."""
    def _flatten(value):
        if isinstance(value, (list, tuple)):
            for item in value:
                yield from _flatten(item)
        elif value is not None:
            yield str(value).strip().lower()

    names = set()
    for book in getattr(character, 'spellbooks', None) or []:
        names.update(_flatten(book.get('spell_list_choose_from')))
        names.update(_flatten(book.get('spells_known_list')))
    names.discard('')
    if not names:
        return {}
    data = pd.read_csv(repo_path('data/spells.csv'), sep='|', on_bad_lines='skip')
    rows = data[(data['mythic'] == 1) & (data['name'].str.strip().str.lower().isin(names))]
    out = {}
    for _, row in rows.iterrows():
        entry = {}
        for column in ('mythic_text', 'augmented'):
            value = row.get(column)
            if value is not None and not pd.isna(value) and str(value).strip():
                entry[column] = str(value).strip()
        if entry:
            out[str(row['name']).strip()] = entry
    return out


# ------------------------------------------------------------------------------------------------
# Mythic traditions (Mythic Spheres wikidot, traditions tab -- Daniel's house scope, 2026-08-14:
# traditions apply to EVERY mythic character, not just spherecasters). Up to three drawbacks, each
# buying one boon or one extra use of mythic power per day; at most one quality. The counts are
# rolled here with decay toward fewer -- a tradition-free mythic character is the common case.
# ------------------------------------------------------------------------------------------------

_TRADITIONS = None
_MASTERIES = None

DRAWBACK_COUNT_WEIGHTS = [4, 3, 2, 1]     # 0..3 drawback-units, decaying
BOON_VS_POWER_WEIGHTS = (2, 1)            # each earned benefit: a boon, or +1 mythic power/day
QUALITY_ONE_IN = 3                        # ~1 character in 3 carries a quality

def tradition_data():
    global _TRADITIONS
    if _TRADITIONS is None:
        with open(repo_path('Backend/json/mythic_traditions.json'), encoding='utf-8') as fh:
            _TRADITIONS = json.load(fh)
    return _TRADITIONS


def sphere_mastery_pool(spheres_chosen):
    """Sphere masteries for the spheres actually held, shaped like path-ability pool entries so
    choose_path_abilities can merge them as extra candidates. Empty when no spheres."""
    global _MASTERIES
    if _MASTERIES is None:
        with open(repo_path('Backend/json/mythic_sphere_masteries.json'), encoding='utf-8') as fh:
            _MASTERIES = json.load(fh)
    held = {str(s).strip().lower() for s in (spheres_chosen or [])}
    pool = {}
    for sphere, entry in _MASTERIES['masteries'].items():
        if sphere.strip().lower() in held:
            pool[f'Mythic Sphere Mastery: {sphere}'] = {
                'tier': entry['tier'], 'type': 'Su', 'source': 'Mythic Spheres (wikidot)',
                'description': entry['description'], 'universal': True,
            }
    return pool


def _talent_description(character, name_lower):
    """Best-effort description for an unpicked bucket option, from the owning class's datasets."""
    for entry in character.classes:
        datasets = getattr(character, entry['name'], None)
        if not isinstance(datasets, dict):
            continue
        for dataset in datasets.values():
            if not isinstance(dataset, dict):
                continue
            for key, value in dataset.items():
                if str(key).lower() == name_lower:
                    if isinstance(value, dict):
                        return str(value.get('description') or value.get('benefit') or '')
                    return str(value or '')
    return ''


def missed_class_features(character):
    """The Expertise pool under the house inversion: options from classes the character HAS that
    they qualified for at their level and did not select.

    v1 sources the prereq-qualified leftovers the choosers accumulated (chooseable_talents keeps
    every unpicked qualifying option across all of the character's classes). Features an archetype
    traded away are NOT enumerable -- archetype swaps are deliberately unmodelled past the
    companion bond -- and stay a recorded simplification."""
    leftovers = list(dict.fromkeys(getattr(character, 'chooseable_talents', None) or []))
    out = []
    for name in leftovers:
        out.append({'name': str(name).title(),
                    'description': _talent_description(character, str(name).lower())})
    return out


def roll_mythic_tradition(character, tier, spheres_on, path_key, chosen_ability_names):
    """Roll one tradition: 0-3 drawback-units (decaying), each buying a boon or +1 MP/day, plus an
    independent 0-1 quality. Eligibility honors the data's machine-readable fields: `flag` skips,
    `requires_spheres` gates on the spheres flag, `counts_as`/`cost` spend the unit budget.

    Returns None when the roll produces nothing at all -- a mythic character without a tradition
    is a legal, common state, not a half-built one."""
    data = tradition_data()
    spheres_on = bool(spheres_on)

    def eligible(section):
        return {name: entry for name, entry in data[section].items()
                if not entry.get('flag') and (spheres_on or not entry.get('requires_spheres'))}

    units_target = random.choices([0, 1, 2, 3], weights=DRAWBACK_COUNT_WEIGHTS, k=1)[0]
    drawbacks, units = [], 0
    pool = eligible('drawbacks')
    while units < units_target and pool:
        fits = sorted(name for name, e in pool.items() if e.get('counts_as', 1) <= units_target - units)
        if not fits:
            break
        name = random.choice(fits)
        entry = pool.pop(name)
        units += entry.get('counts_as', 1)
        drawbacks.append({'name': name, 'description': entry['description']})

    boons, extra_power = [], 0
    budget = units
    boon_pool = eligible('boons')
    while budget > 0:
        affordable = sorted(name for name, e in boon_pool.items() if e.get('cost', 1) <= budget)
        pick_boon = affordable and random.choices(('boon', 'power'), weights=BOON_VS_POWER_WEIGHTS, k=1)[0] == 'boon'
        if not pick_boon:
            extra_power += 1
            budget -= 1
            continue
        name = random.choice(affordable)
        entry = boon_pool.pop(name)
        budget -= entry.get('cost', 1)
        boon = {'name': name, 'description': entry['description']}
        if entry.get('house_rule'):
            boon['house_rule'] = entry['house_rule']
        if entry.get('auto') == 'missed_class_feature':
            options = missed_class_features(character)
            if options:
                boon['grants'] = dict(random.choice(sorted(options, key=lambda o: o['name'])),
                                      via='Expertise (house): a qualified-but-unselected option from your own classes')
        elif entry.get('auto') == 'bonus_first_tier_path_ability':
            own_pool = path_ability_data()[path_key]['abilities']
            taken = {n.lower() for n in chosen_ability_names}
            candidates = sorted(n for n, e in own_pool.items()
                                if e['tier'] == 1 and not e.get('flag') and n.lower() not in taken)
            if candidates:
                extra = random.choice(candidates)
                boon['grants'] = {'name': extra, 'description': own_pool[extra]['description'],
                                  'via': 'Mythic Exemplar: a bonus 1st-tier path ability'}
        boons.append(boon)

    quality = None
    if random.randint(1, QUALITY_ONE_IN) == 1:
        qual_pool = eligible('qualities')
        if qual_pool:
            name = random.choice(sorted(qual_pool))
            quality = {'name': name, 'description': qual_pool[name]['description']}

    if not drawbacks and not quality:
        return None
    return {'drawbacks': drawbacks, 'boons': boons,
            'extra_mythic_power': extra_power, 'quality': quality}


def record_tradition(character, tradition):
    """The tradition joins class features (bucket 'Mythic Tradition', owner mythic, stamp 1) so
    both sheets render it through machinery they already read."""
    if not tradition:
        return
    features = character.data_dict['class features']
    bucket = features.setdefault('Mythic Tradition', {})

    def _add(prefix, item):
        entry_name = f"{prefix}: {item['name']}" if prefix else item['name']
        bucket[entry_name] = {'benefit': item['description']}
        _record_choice_level(character, 'Mythic Tradition', entry_name, 1)
        grants = item.get('grants')
        if grants:
            grant_name = f"{item['name']} → {grants['name']}"
            bucket[grant_name] = {'benefit': f"({grants['via']}) {grants['description']}"}
            _record_choice_level(character, 'Mythic Tradition', grant_name, 1)

    for drawback in tradition['drawbacks']:
        _add('Drawback', drawback)
    for boon in tradition['boons']:
        _add('Boon', boon)
    if tradition['extra_mythic_power']:
        name = 'Boon: Additional Mythic Power'
        bucket[name] = {'benefit': f"+{tradition['extra_mythic_power']} use(s) of mythic power per "
                                   f"day, bought with this tradition's drawbacks."}
        _record_choice_level(character, 'Mythic Tradition', name, 1)
    if tradition['quality']:
        _add('Quality', tradition['quality'])
    record_bucket_owner(character, 'Mythic Tradition', 'mythic')


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
