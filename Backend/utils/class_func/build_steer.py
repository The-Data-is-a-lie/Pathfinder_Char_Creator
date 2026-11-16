"""Selection mode's build pin: steer the choosers toward a pinned build archetype.

A build concept may pin ``build`` -- one of the generic archetypes in ``json/build_archetypes.json``
("Bruiser", "AC Tank", "Archer", ...). This module is what makes that pin DO something.

WHY A BUILD IS STEERED, NOT ASSIGNED
------------------------------------
``build_archetype`` on the payload is a measurement: ``build_archetype.choose_build_archetype``
reads the finished character -- weapon, armor, feats, stats, class -- and names what it is. There
is nothing to assign; writing the pinned name onto the sheet would describe a character that does
not play that way. So the pin acts where the label comes from: it moves the choices the scorer
reads, and the scorer still has the last word. ``selection.audit_build`` reports a miss ("aimed for
Bruiser, came out as Dual Wielder") exactly like any other unmet pin.

THE SCORER IS THE ONLY SOURCE
-----------------------------
Nothing here says what a Bruiser is. Every decision shows the scorer an option
(``build_archetype._signals``) and asks how the pinned entry stands against every other entry with
that option taken (``_standing``: its own score, less the best rival's). Tune an entry in the JSON
and the label and the steer move together; there is no second description to keep in step.

What is steered, each at its own chooser (grep the function):

* the class, when none is pinned and the class input is a random one -- ``fitting_classes``,
  called by ``util.chooseClass``;
* which of a class's alternative main stats is used, the order the rolled scores are placed in,
  and a rolled score for an ability a gate feat needs -- ``preferred_main_stat`` /
  ``stat_priority`` / ``gate_feats``, called by ``stats.roll_stats``, ``power_role.stat_order``
  and ``feats.pinned_feat_ability_floors`` (an explicit ``stat_priority`` pin still wins);
* the weapon, the armor band and whether a shield is carried -- ``weapon_pick``, ``armor_band``,
  ``wants_shield``, called by ``armor_and_weapon_chooser``;
* which spells are favoured -- ``weight_spells``, called by ``spells``;
* feats -- ``next_feat_wish``, taken by ``feats.pinned_feat_chooser`` after the explicit feat pins,
  through the same slot reservation and the same prerequisite test.

WHAT IS NOT STEERED (and is therefore the usual reason for a miss): spheres, Path of War
disciplines, companions and mounts. A build defined by one of those is steered as far as class,
scores, gear, spells and feats go, and the rest is the dice. Explicit pins close that gap -- a
concept can pin a build AND the spheres or disciplines that make it.

Every function answers "no opinion" (None / [] / the value it was handed) when no build is pinned,
and none of them draws from the RNG in that case, so an unpinned character is untouched.
"""
import random
import re
from types import SimpleNamespace

import pandas as pd

from utils import data

from . import build_archetype as scorer
from . import selection

# Signals the CLASS decides, and nothing later can change: read off a class by asking the scorer
# about a bare build of that class (see _class_signals). Used to tell which classes can be a build.
_CLASS_SIGNALS = (
    'bab_high', 'bab_mid', 'bab_low', 'caster_tier', 'caster_primary',
    'main_str', 'main_dex', 'main_con', 'main_int', 'main_wis', 'main_cha',
    'precision', 'stealthy', 'summoner_pet', 'kinetic_blast', 'bomb_thrower', 'performer',
    'initiator',
)
# Signals a class can supply outright (the monk is mobile, the cavalier is mounted) but that feats
# can supply too -- so a class without them is not ruled out.
_CLASS_OR_FEAT_SIGNALS = ('mobile', 'mounted')
# The class signals that are an IDENTITY rather than a chassis: one class (or a handful) has it and
# an entry gated on it is that class's own build. See _identity_claim.
_IDENTITY_SIGNALS = ('precision', 'stealthy', 'summoner_pet', 'kinetic_blast', 'bomb_thrower')
# armor.json's bands, as the scorer names them. None is no armor.
_ARMOR_SIGNAL = {None: 'armor_none', 'L': 'armor_light', 'M': 'armor_medium', 'H': 'armor_heavy'}
_ARMOR_ORDER = (None, 'L', 'M', 'H')

# The highest spell level each casting progression reaches, for "could this class ever pass a
# caster_tier gate". PF1's three progressions; the scorer divides by the same nine.
_TOP_SPELL_LEVEL = {'high': 9, 'mid': 6, 'low': 4}

# How close to the best-fitting class another class must score to stay in the draw. Wide enough
# that a build is not always the same class, narrow enough that the class is a real fit.
CLASS_FIT_SHARE = 0.75
# A class "has" a spell family when its list carries at least this share of what the best-stocked
# list carries (the cleric's healing against the paladin's, say). Below it, a gate on that family
# is not something the class can be relied on to meet.
SPELL_FAMILY_SHARE = 0.5
# A `caster_tier` veto trips with LEVEL, not with class, so it ranks classes instead of barring
# them: a class is charged this many times the amount its full progression overshoots the veto.
# Two, so that a class which trips the veto for most of its career ranks below one that barely
# reaches it (the 4-level casters for a build that vetoes real casting).
VETO_OVERSHOOT_COST = 2.0
# The bonded creatures that count as a companion for the scorer (main_test reads `chosen_animal`,
# which a familiar or an eidolon does not set).
_COMPANION_KINDS = ('companion', 'mount')
# How hard a wanted spell family is favoured, and an unwanted one disfavoured, when spells are
# picked. Above the x100 a specialty school gets, so the build outranks the rolled theme.
SPELL_FAVOUR, SPELL_DISFAVOUR = 1000.0, 0.01

# The feat names the scorer tests for by literal string, outside its curated buckets and its named
# tuples. They have to be offered to the scorer as candidates for it to say what they do; a name
# that stops moving any signal is flagged by gates/validate_selection.py.
_SCORER_FEAT_WORDS = ('two-weapon fighting', 'double slice', 'improved critical', 'critical focus',
                      'weapon finesse', 'lunge')
# The feat buckets the scorer reads (build_archetype._BUCKET_SIGNALS paths start with these).
_SCORED_BUCKET_ROOTS = ('martial', 'magical')

_ABILITIES = ('str', 'dex', 'con', 'int', 'wis', 'cha')
# Where an ability falls when nothing asks for it: the order a character misses each least.
_DEFAULT_TAIL = ('con', 'dex', 'wis', 'str', 'int', 'cha')


# --------------------------------------------------------------------------- #
# The pinned entry, and how it stands
# --------------------------------------------------------------------------- #
def roster():
    """{name: entry} for every build that can be pinned -- the scorer's roster minus its fallback
    label, which is what a character is called when it is nothing in particular."""
    entries = scorer._load_roster()['archetypes']
    return {name: entry for name, entry in entries.items() if name != scorer._FALLBACK.label}


def entry_for(character):
    """The pinned build's roster entry, or None."""
    name = selection.pinned_build(character)
    return roster().get(name) if name else None


def _weights(entry):
    return entry.get('signals') or {}


def _gates(entry):
    """(requires_all, requires_any, vetoes) as lists of (signal, min)."""
    def rows(key):
        return [(g['signal'], g.get('min', 1.0)) for g in entry.get(key) or []]
    return rows('requires_all'), rows('requires_any'), rows('vetoes')


def _shortfall(entry, sig):
    """How far ``sig`` is from passing the entry's gates: 0 when it passes, otherwise the summed
    distance to each unmet requirement plus one per veto tripped. Lets a choice be credited for
    moving TOWARD a gate that takes two steps to close."""
    need_all, need_any, vetoes = _gates(entry)
    short = sum(max(0.0, low - sig.get(s, 0.0)) for s, low in need_all)
    if need_any:
        short += min(max(0.0, low - sig.get(s, 0.0)) for s, low in need_any)
    short += sum(1.0 for s, low in vetoes if sig.get(s, 0.0) >= low)
    return short


def _standing(target, sig):
    """How the build named ``target`` stands on ``sig``: its own score less the best rival's.

    A gated-out target stands below every scored one, by its shortfall. The rivals are the whole
    roster, the fallback label included -- they are who the scorer would name instead.
    """
    entries = scorer._load_roster()['archetypes']
    own = scorer._score(entries[target], sig)
    if own is None:
        own = -1.0 - _shortfall(entries[target], sig)
    rivals = [scorer._score(entry, sig) for name, entry in entries.items() if name != target]
    return own - max((score for score in rivals if score is not None), default=0.0)


# --------------------------------------------------------------------------- #
# Class
# --------------------------------------------------------------------------- #
_SPELL_STOCK = None
_STEERABLE = None


def _spell_column(name):
    """The spells.csv column class ``name`` casts from (the skald reads the bard's, and so on)."""
    from .spells import class_for_spells_attr
    return class_for_spells_attr(SimpleNamespace(classes=[{'name': name}]))[0]


def _spell_stock(character):
    """{spell-list column: {family: share}} -- how well stocked each class spell list is in each
    of the scorer's spell families, as a share of the best-stocked list's COUNT for that family
    (a count, not a proportion: a twelve-spell list that happens to be half cures cannot carry a
    healer). Read from spells.csv with the scorer's own keyword lists, over the columns a class
    actually casts from."""
    global _SPELL_STOCK
    if _SPELL_STOCK is None:
        from .spells import _load_spell_data
        frame = _load_spell_data()
        names = frame['name'].astype(str).str.lower()
        in_family = {family: names.apply(lambda n, w=words: any(k in n for k in w))
                     for family, words in scorer._SPELL_FAMILIES.items()}
        raw = {}
        for column in sorted({_spell_column(name) for name in character.class_data}):
            if column not in frame.columns:
                continue
            on_list = pd.to_numeric(frame[column], errors='coerce').notna()
            if on_list.any():
                raw[column] = {family: float(hit[on_list].sum()) for family, hit in in_family.items()}
        best = {family: max((row[family] for row in raw.values()), default=0.0) or 1.0
                for family in scorer._SPELL_FAMILIES}
        _SPELL_STOCK = {column: {family: count / best[family] for family, count in row.items()}
                        for column, row in raw.items()}
    return _SPELL_STOCK


def steerable_signals(character):
    """The signals a chooser here can switch on for any class, asked of the data rather than
    listed: every weapon signal some rollable weapon actually produces (a signal no weapon in
    weapons_data.json carries cannot be steered to, whatever an entry asks), every signal some
    candidate feat raises, and the three the score placement decides."""
    global _STEERABLE
    if _STEERABLE is None:
        found = {'con_focus', 'str_over_dex', 'dex_over_str'}
        usable = set(getattr(data, 'useable_weapons', []) or [])
        for section in (getattr(character, 'weapons_data', None) or {}).values():
            for name, row in section.items():
                if name in usable:
                    sig = scorer._signals(_weapon_facts(name, row))
                    found.update(s for s, v in sig.items() if v and s.startswith('wpn_'))
        found.discard('wpn_none')            # "no weapon" is what the scorer reads off an empty build
        for moved in feat_effects(character).values():
            found.update(moved)
        _STEERABLE = frozenset(found)
    return _STEERABLE


def _class_facts(character, name):
    """Everything about class ``name`` that bears on whether it can be a build:

    * ``sig`` -- what the scorer says of a bare build of the class at full progression, merged over
      its alternative main stats (a class that may lead with Str or Dex can be either);
    * ``armor`` / ``shield`` -- the heaviest band it may wear and whether it may carry a shield at
      all, from armor_proficiency.json (the table the gear choosers obey);
    * ``companion`` -- whether companion_grantors.json gives it a bonded creature;
    * ``spells`` -- how well its spell list is stocked per spell family, {} for a non-caster.
    """
    from .armor_and_weapon_chooser import armor_proficiency, _row_for
    row = character.class_data[name]
    casting = str(row.get('casting level', 'none')).lower()
    top = _TOP_SPELL_LEVEL.get(casting, 0)
    initiators = {str(c).lower() for token, _label, names in data.CLASS_GROUPS
                  if token == 'pow' for c in names or []}
    sig = {}
    for main in str(row.get('main_stat') or '').lower().split('/'):
        bare = scorer._signals({
            'class_names': [name], 'primary_class': name,
            'class_entries': [{'name': name, 'level': 20}], 'total_level': 20,
            'bab_tier': str(row.get('bab', 'M')), 'spell_levels': [top] if top else [],
            'main_stat': main, 'initiator_level': 20 if name in initiators else 0,
        })
        for key in _CLASS_SIGNALS + _CLASS_OR_FEAT_SIGNALS:
            sig[key] = max(sig.get(key, 0.0), bare.get(key, 0.0))
    proficiency = _row_for(armor_proficiency(), name) or {}
    grantors = {str(r.get('grantor')).lower()
                for r in (getattr(character, 'companion_grantors', None) or {}).get('grantors', [])
                if r.get('creature_type') in _COMPANION_KINDS}
    return {'sig': sig, 'armor': proficiency.get('armor'), 'shield': bool(proficiency.get('shield')),
            'companion': name in grantors or name.replace(' (unchained)', '') in grantors,
            'spells': _spell_stock(character).get(_spell_column(name), {}) if top else {}}


def _identity_claim(target, sig):
    """How strongly ANOTHER build already owns a class with signals ``sig``.

    Some entries are a class's identity: an alchemist is a Mad Bomber, a summoner an Eidolon
    Master, a rogue a Trickster -- their gate is met by the class alone, through one of the
    identity signals. Steering such a class toward a different build mostly loses to its own, so
    the rival's class-only score is taken off the fit. Entries gated on something every class of a
    kind has (base attack, casting) are not identities and claim nothing.
    """
    claim = 0.0
    for name, entry in roster().items():
        if name == target:
            continue
        need_all, need_any, _vetoes = _gates(entry)
        owned = any(s in _IDENTITY_SIGNALS and sig.get(s, 0.0) >= low for s, low in need_all + need_any)
        score = scorer._score(entry, sig) if owned else None
        if score is not None:
            claim = max(claim, score)
    return claim


def class_fit(character, name, target):
    """How well class ``name`` can be the build named ``target``, or None when it cannot.

    Ruled out means a gate no later choice can fix: a veto the class itself trips (a caster for a
    build that vetoes ``caster_primary``), or a requirement neither the class nor a chooser can
    meet -- a shield for a class with no shield proficiency, a companion for a class that is
    granted none, a spell family its list barely holds, a weapon kind the weapon data does not
    carry. Requirements on spheres and disciplines are not something a class or this module can
    promise, so they never satisfy a gate here: a build that asks ONLY for those fits no class and
    is left to the dice.

    The fit is the entry's weights over what the class settles -- its own signals, the best armor
    band it may wear, the shield and the companion if it has them, its stock of each spell family
    -- less two things: how far a full progression overshoots a ``caster_tier`` veto (which trips
    with level, so it ranks classes rather than barring them), and any rival's identity claim.
    """
    entry = roster()[target]
    facts = _class_facts(character, name)
    sig = facts['sig']
    bands = _ARMOR_ORDER[:_ARMOR_ORDER.index(facts['armor']) + 1] if facts['armor'] in _ARMOR_ORDER else (None,)
    wearable = {_ARMOR_SIGNAL[band] for band in bands}
    steerable = steerable_signals(character)

    def reach(signal):
        if signal in _CLASS_SIGNALS:
            return sig.get(signal, 0.0)
        if signal in _CLASS_OR_FEAT_SIGNALS or signal in steerable:
            return 1.0
        if signal.startswith('armor_'):
            return 1.0 if signal in wearable else 0.0
        if signal == 'shield':
            return 1.0 if facts['shield'] else 0.0
        if signal == 'companion':
            return 1.0 if facts['companion'] else 0.0
        if signal.startswith('spell_'):
            return 1.0 if facts['spells'].get(signal, 0.0) >= SPELL_FAMILY_SHARE else 0.0
        return 0.0

    need_all, need_any, vetoes = _gates(entry)
    overshoot = 0.0
    for signal, low in vetoes:
        if signal == 'caster_tier':
            overshoot += max(0.0, sig.get(signal, 0.0) - low)
        elif signal in _CLASS_SIGNALS and sig.get(signal, 0.0) >= low:
            return None
    if any(reach(s) < low for s, low in need_all):
        return None
    if need_any and not any(reach(s) >= low for s, low in need_any):
        return None
    weights = _weights(entry)
    mass = sum(abs(w) for w in weights.values()) or 1.0
    fit = sum(w * sig.get(s, 0.0) for s, w in weights.items()
              if s in _CLASS_SIGNALS or s in _CLASS_OR_FEAT_SIGNALS)
    fit += max(weights.get(signal, 0.0) for signal in wearable)
    fit += max(weights.get('shield', 0.0), 0.0) if facts['shield'] else 0.0
    fit += weights.get('companion', 0.0) if facts['companion'] else 0.0
    fit += sum(weights.get(family, 0.0) * share for family, share in facts['spells'].items())
    return fit / mass - VETO_OVERSHOOT_COST * overshoot - _identity_claim(target, sig)


def ranked_classes(character, target, pool):
    """[(fit, class name)] for the classes in ``pool`` that can be the build ``target``, best first."""
    fits = [(class_fit(character, name, target), name) for name in pool]
    return sorted(((fit, name) for fit, name in fits if fit is not None), key=lambda t: (-t[0], t[1]))


def fitting_classes(character, pool):
    """The classes in ``pool`` a pinned build should be drawn from: [] when no build is pinned, or
    when no class in the pool can be the build (the usual draw then stands)."""
    target = selection.pinned_build(character)
    if not target or target not in roster():
        return []
    ranked = ranked_classes(character, target, pool)
    if not ranked:
        return []
    best = ranked[0][0]
    floor = best * CLASS_FIT_SHARE if best > 0 else best
    return [name for fit, name in ranked if fit >= floor]


def offered(character, pool):
    """{build name: [fitting classes, best first]} for the builds worth offering in a picker:
    those at least one class in ``pool`` can be. A build no class can be -- one whose gate the
    data cannot meet -- is still accepted by name and steered as far as it goes, but offering it
    would be offering a pin that is reported every time."""
    out = {}
    for name in roster():
        ranked = ranked_classes(character, name, pool)
        if ranked:
            out[name] = [cls for _fit, cls in ranked]
    return out


# --------------------------------------------------------------------------- #
# Ability scores
# --------------------------------------------------------------------------- #
def preferred_main_stat(character, parts, rolled):
    """Which of a class's alternative main stats ("str/dex") a pinned build wants; ``rolled`` (the
    random pick already made) when no build is pinned or the entry has no preference."""
    entry = entry_for(character)
    if entry is None:
        return rolled
    weights = _weights(entry)
    best = max(parts, key=lambda part: weights.get('main_' + part[:3], 0.0))
    return best if weights.get('main_' + best[:3], 0.0) > weights.get('main_' + rolled[:3], 0.0) else rolled


def stat_priority(character):
    """All six abilities in the order a pinned build wants the rolled scores placed, or None.

    The class's main stat leads, as it always does. The entry then moves three things, because
    they are the three things the scorer reads off the scores: Con ahead of Str and Dex when the
    build is defined by ``con_focus`` (it gates the entry by itself or in ``requires_all``),
    otherwise Con straight after the main stats when the entry merely likes it; and Str and Dex in
    the order ``str_over_dex`` / ``dex_over_str`` are weighted (a veto on one counts for the other).
    """
    entry = entry_for(character)
    if entry is None:
        return None
    weights = _weights(entry)
    need_all, need_any, vetoes = _gates(entry)
    row = character.class_data.get(str(character._class_picks[0]).lower(), {})
    main = str(getattr(character, 'main_stat', None) or row.get('main_stat') or '').lower().split('/')[0][:3]
    second = max(str(row.get('main_stat_2') or '').lower().split('/'),
                 key=lambda part: weights.get('main_' + part[:3], 0.0))[:3]
    order = list(dict.fromkeys(a for a in (main, second) if a in _ABILITIES))
    leads = len(order)
    order.extend(a for a in _DEFAULT_TAIL if a not in order)

    def before(first, other):
        """Move ``first`` to sit immediately ahead of ``other`` when it is behind it."""
        if order.index(first) > order.index(other):
            order.remove(first)
            order.insert(order.index(other), first)

    defined_by_con = (tuple(s for s, _low in need_any) == ('con_focus',)
                      or any(s == 'con_focus' for s, _low in need_all))
    if defined_by_con:
        order.remove('con')
        order.insert(0, 'con')
    elif weights.get('con_focus', 0.0) > 0 and 'con' not in order[:leads]:
        order.remove('con')
        order.insert(leads, 'con')
    vetoed = {s for s, _low in vetoes}
    lean = (weights.get('str_over_dex', 0.0) + (1.0 if 'dex_over_str' in vetoed else 0.0)
            - weights.get('dex_over_str', 0.0) - (1.0 if 'str_over_dex' in vetoed else 0.0))
    if lean > 0:
        before('str', 'dex')
    elif lean < 0:
        before('dex', 'str')
    return order


# --------------------------------------------------------------------------- #
# The character so far, as the scorer reads it
# --------------------------------------------------------------------------- #
def _weapon_facts(name, row):
    row = row or {}
    return {
        'weapon': name,
        'weapon_category': row.get('category'),
        # weapons_data.json glues the prose description onto the group names (main_test trims it
        # the same way before the scorer sees it).
        'weapon_groups': str(row.get('weapon groups') or '').split('Description')[0].strip(),
        'weapon_special': row.get('special'),
        'weapon_critical': row.get('critical'),
    }


def snapshot(character, feats=(), **override):
    """The character as far as it is built, in the shape the scorer reads (the keys main_test's
    export assembles, minus what is not chosen yet). Tolerant of anything still unset; ``override``
    replaces keys, which is how an option is tried on."""
    weapons = getattr(character, 'weapon_dict', None)
    name, row = next(iter(weapons.items()), ('', {})) if isinstance(weapons, dict) else ('', {})
    classes = getattr(character, 'classes', None) or []
    primary = getattr(character, 'c_class', '') or ''
    build = _weapon_facts(name, row)
    build.update({
        'class_names': [c['name'] for c in classes],
        'class_entries': [{'name': c['name'], 'level': c['level']} for c in classes],
        'total_level': getattr(character, 'level', 0),
        'primary_class': primary,
        'bab_tier': str(character.class_data.get(primary, {}).get('bab', 'M')),
        'main_stat': getattr(character, 'main_stat', ''),
        'stat_dict': {a: getattr(character, a, 0) for a in _ABILITIES},
        'armor_type': getattr(character, 'armor_type', None),
        'shield_flag': getattr(character, 'shield_flag', None),
        'feats': list(feats),
        'feat_buckets': getattr(character, 'feat_buckets', None) or {},
    })
    build.update(override)
    return build


# --------------------------------------------------------------------------- #
# Gear
# --------------------------------------------------------------------------- #
def weapon_pick(character, section, candidates):
    """A weapon from ``candidates`` (names in ``section``) that suits a pinned build, or None for
    the usual random draw.

    Each candidate is tried on the character as it stands and judged by ``_standing``. The pick is
    random among the best, and weapons the scorer cannot tell apart stand equal -- so a build has a
    weapon STYLE, not a single weapon. None when no build is pinned, or when the entry does not
    tell the candidates apart at all.
    """
    target = selection.pinned_build(character)
    candidates = sorted(candidates)
    if not target or not candidates:
        return None
    stood = {name: round(_standing(target, scorer._signals(
        snapshot(character, **_weapon_facts(name, section.get(name))))), 6) for name in candidates}
    best = max(stood.values())
    if best == min(stood.values()):
        return None
    return random.choice([name for name in candidates if stood[name] == best])


def armor_band(character, legal, wearable):
    """The armor band a pinned build wants, among ``wearable`` (the bands at or below ``legal``
    the character may actually wear, None for no armor). ``legal`` when no build is pinned or the
    entry has no opinion; ties go to the heaviest, which is what an unpinned character wears."""
    target = selection.pinned_build(character)
    if not target or not wearable:
        return legal
    stood = {band: round(_standing(target, scorer._signals(snapshot(character, armor_type=band))), 6)
             for band in wearable}
    best = max(stood.values())
    if best == min(stood.values()):
        return legal
    return [band for band in wearable if stood[band] == best][-1]


def wants_shield(character):
    """True / False when a pinned build decides the shield, None to leave it to the roll.

    Decided the way the weapon is: the character as it stands is tried with a shield and without,
    and the better standing wins. Not the entry's own weight alone -- a build that mildly likes a
    shield can still be handed to the shield build by carrying one."""
    target = selection.pinned_build(character)
    if not target:
        return None
    carried = _standing(target, scorer._signals(snapshot(character, shield_flag=True)))
    bare = _standing(target, scorer._signals(snapshot(character, shield_flag=False)))
    if abs(carried - bare) < 1e-9:
        return None
    return carried > bare


# --------------------------------------------------------------------------- #
# Spells
# --------------------------------------------------------------------------- #
def weight_spells(character, query):
    """Favour the spell families a pinned build wants in ``query`` (a spell frame with ``name`` and
    ``weight``), and disfavour the ones it weights against. The families and their keywords are
    the scorer's own (``_SPELL_FAMILIES``), so what is favoured is exactly what it will count.
    Returns ``query``; untouched when no build is pinned or the entry names no spell family.
    """
    entry = entry_for(character)
    if entry is None or query is None or not len(query):
        return query
    weights = _weights(entry)
    need_all, need_any, _vetoes = _gates(entry)
    gated = {s for s, _low in need_all + need_any}
    # Only the family the entry weights MOST is favoured (and any it gates on). A build that leans
    # on control and merely likes summoning must not be handed a spell list that reads as a
    # summoner's -- the lesser family would win the label for the build next door.
    top = max((weights.get(family, 0.0) for family in scorer._SPELL_FAMILIES), default=0.0)
    names = query['name'].astype(str).str.lower()
    for family, words in scorer._SPELL_FAMILIES.items():
        weight = weights.get(family, 0.0)
        if family in gated or (weight > 0 and weight >= top):
            factor = SPELL_FAVOUR
        elif weight < 0:
            factor = SPELL_DISFAVOUR
        else:
            continue
        hit = names.apply(lambda n, w=words: any(k in n for k in w))
        query.loc[hit, 'weight'] *= factor
    return query


# --------------------------------------------------------------------------- #
# Feats
# --------------------------------------------------------------------------- #
_FEAT_CANDIDATES = None
_FEAT_EFFECTS = None


def feat_candidates(character):
    """Every feat name the scorer could react to, lower-cased: the leaves of the feat buckets it
    reads, its own named tuples, and the handful it tests for by literal string."""
    global _FEAT_CANDIDATES
    if _FEAT_CANDIDATES is None:
        names = []

        def leaves(node):
            if isinstance(node, dict):
                for child in node.values():
                    leaves(child)
            elif isinstance(node, list):
                names.extend(str(leaf).lower() for leaf in node)

        buckets = getattr(character, 'feat_buckets', None) or {}
        for root in _SCORED_BUCKET_ROOTS:
            leaves(buckets.get(root, {}))
        names.extend(scorer._MOBILITY_FEATS + scorer._AOO_FEATS + scorer._MOUNTED_FEATS)
        names.extend(_SCORER_FEAT_WORDS)
        _FEAT_CANDIDATES = tuple(dict.fromkeys(names))
    return _FEAT_CANDIDATES


def feat_effects(character):
    """{candidate feat: the signals it raises on an otherwise empty build}, asked of the scorer."""
    global _FEAT_EFFECTS
    if _FEAT_EFFECTS is None:
        buckets = getattr(character, 'feat_buckets', None) or {}
        base = scorer._signals({'feats': [], 'feat_buckets': buckets})
        effects = {}
        for name in feat_candidates(character):
            sig = scorer._signals({'feats': [name], 'feat_buckets': buckets})
            effects[name] = frozenset(s for s in sig if sig[s] > base.get(s, 0.0))
        _FEAT_EFFECTS = effects
    return _FEAT_EFFECTS


def gate_feats(character):
    """The feats a pinned build cannot do without: for each of the entry's requirements that a
    feat can meet, the first candidate that meets it. ``feats.pinned_feat_ability_floors`` reads
    these so the rolled scores can be placed for them (Two-Weapon Fighting needs Dex 15, and a
    Dual Wielder with Dex 12 is not one). [] when no build is pinned."""
    entry = entry_for(character)
    if entry is None:
        return []
    need_all, need_any, _vetoes = _gates(entry)
    effects = feat_effects(character)
    out = []
    for signal, _low in need_all + need_any:
        feat = next((name for name in feat_candidates(character) if signal in effects[name]), None)
        if feat and feat not in out:
            out.append(feat)
    return out


def next_feat_wish(character, held, tried, known):
    """The feat that would do a pinned build the most good right now, or None.

    ``held`` is what the character holds so far (names), ``tried`` what has already been offered
    (taken or refused), ``known`` the names that can be taken at all (the pinnable feat index's
    keys). Each remaining candidate is tried on the character and judged by ``_standing``; the
    wish is the one that improves it most. That one measure does three jobs: it prefers what the
    entry weights, it credits a step toward a gate, and it refuses a feat that helps a rival more
    than the build (Two-Weapon Fighting on a Bruiser makes a Dual Wielder). None when no build is
    pinned or nothing left would help -- the remaining slots are then the dice's.
    """
    target = selection.pinned_build(character)
    if not target:
        return None
    held = [str(name).lower() for name in held]
    base = _standing(target, scorer._signals(snapshot(character, held)))
    best, best_gain = None, 1e-9
    for name in feat_candidates(character):
        if name in tried or name in held or name not in known:
            continue
        gain = _standing(target, scorer._signals(snapshot(character, held + [name]))) - base
        if gain > best_gain:
            best, best_gain = name, gain
    return best


# --------------------------------------------------------------------------- #
# The miss report
# --------------------------------------------------------------------------- #
_SIGNAL_PREFIX_WORDS = {'wpn': 'weapon', 'feat': 'feats', 'sph': 'sphere', 'disc': 'discipline',
                        'spell': 'spells', 'armor': 'armor', 'main': 'main stat', 'bab': 'base attack'}


def signal_words(signal):
    """A signal name in words a player can read: "wpn_two_handed" -> "weapon: two handed"."""
    head, _sep, tail = signal.partition('_')
    if head in _SIGNAL_PREFIX_WORDS and tail:
        return f'{_SIGNAL_PREFIX_WORDS[head]}: {tail.replace("_", " ")}'
    return re.sub(r'_', ' ', signal)


def miss_reason(build, target, label):
    """Why a character steered toward ``target`` was named ``label`` instead."""
    entry = roster().get(target) or {}
    sig = scorer._signals(build)
    need_all, need_any, vetoes = _gates(entry)
    lacking = [signal_words(s) for s, low in need_all if sig.get(s, 0.0) < low]
    if need_any and not any(sig.get(s, 0.0) >= low for s, low in need_any):
        lacking.append(' or '.join(signal_words(s) for s, _low in need_any))
    tripped = [signal_words(s) for s, low in vetoes if sig.get(s, 0.0) >= low]
    if lacking:
        return f'came out as {label}: the character lacks {"; ".join(lacking)}'
    if tripped:
        return f'came out as {label}: the build rules out {"; ".join(tripped)}'
    return f'came out as {label}, which fit the finished character better'
