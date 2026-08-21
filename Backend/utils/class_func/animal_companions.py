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

IDENTITY AND GEAR (the #37 grill, 2026-08-03)
---------------------------------------------
A creature that EXISTS gets a `name` drawn from the MASTER'S region pool (never the master's own
name) and a rolled `sex`, because `animal_choices.json` carries no sex and the pool is keyed by one.
`species` remains the SOLE `pf-content` match key -- the module clones by species and attaches by
name match, so a named companion must never be able to miss its own compendium Actor. Nothing is
composed here: the backend emits atoms and each renderer builds its own label (D2).

It owns nothing in v1: `gear` is `[]` and `GEAR_SOURCE_V1` says both that the absence is deliberate
and whose money will buy the gear when #37's v1.1 ticket lands (the master's -- PF1e gives companions
no wealth-by-level). An ABSENCE entry records why there is no creature, so it carries `name: None`,
`sex: None` and NO gear key at all: a null-named, empty-geared ghost still renders.

WHAT THIS SLICE DOES NOT DO
---------------------------
The advancement merge and the stat-block math are #31. Entries carry the raw species block and the
chassis row, exactly as the old payload did. FAMILIARS resolve here too (2026-08-12, the v1 debt):
their species come from `familiar_choices.json` via the same bucket lookup, they carry NO chassis
(their numbers key off the master, computed by `familiars.stat_familiars` in a LATE pass because
the master's HP/skills/luck are not final when the companion stat pass runs). EIDOLONS resolve here
as of v1.1 -- see the delimited eidolon section at the foot of this file for the EP spender, and
note that its chassis is `eidolon_table.json`, not the companion table.
"""
import random
import re

from utils.class_func.generic_func import class_entry_for
from utils.util import first_name_for

# The v1 gear posture, in ONE place. Restating this sentence anywhere else is the "restate a symbol
# instead of naming its owner" pattern CLAUDE.md calls a bug magnet; import it instead.
GEAR_SOURCE_V1 = ('not modelled in v1; when added, funded from character.gold '
                  '(PF1e: companions have no wealth-by-level)')

# Rolled per creature, in the PC's own casing (`util.py::gender_chooser`). NOT the master's sex:
# reusing it would make every companion match its master 100% of the time.
SEXES = ('Male', 'Female')

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


def _species_buckets(character):
    """Every bucket a `species_pool` may draw from: the animal_choices tiers plus the familiar
    pool. One lookup, so `_find_species` and `_kind_of` can never disagree about who exists."""
    buckets = dict(getattr(character, 'animal_choices', None) or {})
    familiar = (getattr(character, 'familiar_choices', None) or {}).get('familiar')
    if familiar:
        buckets['familiar'] = familiar
    return buckets


def _standard_pool(character, tiers):
    """Species names from the named animal_choices tiers, or the literal names given."""
    choices = _species_buckets(character)
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
    choices = _species_buckets(character)
    for bucket in choices.values():
        if name in bucket:
            return bucket[name]
    return None


def _kind_of(character, name):
    choices = _species_buckets(character)
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
        grantor_class = grantor
        conditional = row.get('conditional') or {}

        if row.get('source') == 'spheres_of_might_talent':
            talents = getattr(character, 'chooseable_talents', []) or []
            if conditional.get('talent') and conditional['talent'] not in talents:
                continue
            level = character_level
        else:
            class_entry = class_entry_for(character, grantor)
            if class_entry is None:
                continue
            level = class_entry['level']
            # The class name AS ROLLED, kept out of `entry` because that name is rebound to the
            # creature further down this loop. The eidolon branch is the one reader that needs it:
            # `class_entry_for` resolves `summoner (unchained)` off the single `summoner` row.
            grantor_class = class_entry['name']

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
            entries.append(_entry(character, row, grantor, None, None, None, None,
                                  outcome=outcome, archetype=archetype_name,
                                  effective_level=0))
            continue

        outcome = 'granted'
        if choice and 'forces' not in effects:
            if random.randint(1, 100) > choice['odds']:
                outcome = choice['on_loss']
        character.bond_outcomes[grantor] = outcome
        if outcome != 'granted':
            entries.append(_entry(character, row, grantor, None, None, None, None,
                                  outcome=outcome, archetype=archetype_name,
                                  effective_level=0))
            continue

        effective = _effective_level(row['effective_level'], level, character,
                                     row.get('minimum'))
        if effective <= 0:
            continue

        if row['creature_type'] == 'eidolon':
            # Built here, BOUGHT after `_stack` -- see the eidolon section's ordering note. The
            # chained/unchained split reads the matched class entry rather than the row, because
            # `class_entry_for` resolves both names off the single `summoner` row (D4, 07 #1).
            unchained = '(unchained)' in grantor_class
            eidolon = _eidolon_entry(character, row, grantor, unchained, effective)
            if eidolon is None:
                continue                   # the data is not on the character; emit nothing
            entries.append(eidolon)
            continue

        curated = record.get('species_pool') if 'species_pool' in effects else None
        species, kind, fell_back = _pick_species(character, row, curated)
        if species is None:
            continue

        # A familiar has no chassis row: its numbers key off the MASTER (familiars.py's late
        # pass), and handing it the companion table here would put wrong data on the entry.
        chassis = (None if row['creature_type'] == 'familiar'
                   else _chassis(character, min(effective, character_level or effective)))
        entry = _entry(character, row, grantor, species, kind, _find_species(character, species),
                       chassis,
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
    # AFTER the stack: the evolution pool is read at the creature's final effective level.
    spend_eidolon_evolutions(character)

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


def _entry(character, row, grantor, species, kind, stats, chassis, outcome, archetype,
           effective_level):
    """One bonded-creature entry. IDENTITY AND GEAR in the module docstring owns the shape.

    The identity fields are conditional ON PURPOSE. An entry with no species is not a creature, it
    is the record of why there isn't one, so it gets `name: None` / `sex: None` and no gear key --
    the alternative (a uniform key set with nulls) ships a null-named, empty-geared ghost that a
    renderer will happily draw.
    """
    entry = {
        'type': row['creature_type'],
        'grantor': grantor,
        'effective_level': effective_level,
        'species': species,
        'name': None,
        'sex': None,
        'kind': kind,
        'species_stats': stats,
        'chassis': chassis,
        'feats': [],
        'outcome': outcome,
        'archetype': archetype,
        'flags': [],
        'contributors': [grantor] if species else [],
    }
    if species:
        entry['sex'] = random.choice(SEXES)
        entry['name'] = first_name_for(character, getattr(character, 'region', None), entry['sex'],
                                       exclude=getattr(character, 'f_name', None))
        entry['gear'] = []
        entry['gear_source'] = GEAR_SOURCE_V1
    return entry


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
        # A familiar's chassis stays None through the re-read too -- its numbers key off the
        # master, and handing it the companion table here is exactly the stomp the resolver
        # already refused once (caught by the invariant sweep, 2026-08-13). An EIDOLON's chassis
        # is its own table (`eidolon_table.json`, a different set of columns entirely) and is
        # written by `spend_eidolon_evolutions` at this same resolved level -- so it is excluded
        # here for the same reason, not a new one.
        if entry['type'] not in ('familiar', 'eidolon'):
            entry['chassis'] = _chassis(character, entry['effective_level'])
        out.append(entry)
    return out


# ==============================================================================================
# Start of Eidolon section -- spec section 8 "Eidolon (v1.1)", companions ticket 07
# ==============================================================================================
#
# WHY THIS LIVES HERE. Ticket 07 ruled the eidolon needs a new MECHANISM but not a new home: it is
# bought from a point budget rather than picked N-of-a-list, so `generic_class_option_chooser` does
# not fit, but it is still a bonded creature and every other bonded creature resolves in this file.
# Spheres-style funding was rejected too -- that machinery converts FEATS into talents, and the
# evolution pool is a class-table resource with no feat in sight.
#
# THE ONE ORDERING FACT THAT MATTERS. The spend runs AFTER `_stack`, not inside the row loop. The
# pool is read off `eidolon_table.json` at the creature's FINAL effective level, and stacking is what
# decides that level; spending in the loop would give a summoner 5 / summoner 5 two three-point
# eidolons' worth of picks instead of one eight-point eidolon's. Ticket 07 ruling 7 (snapshot
# semantics: the pool is spent whole at the resolved level) is only meaningful once that level is
# resolved, so the row loop builds the creature and this pass buys its evolutions.
#
# EVERY DRAW IS THE CREATURE'S OWN. `companion_stats._rng`, salted per consumer, exactly as the feat
# and skill passes do (D16). Rolling evolutions off the global stream would churn the master's items
# and backstory for every future diff.

# Summoner level -> the most EP the Aspect class feature may divert to the summoner (07 #5).
# Ordered high-to-low because the first match wins.
ASPECT_TIERS = ((18, 6), (10, 2))

# What the unchained summoner is owed and does not get. Ticket 07 ruling 1 holds the line at the
# chained summoner: the unchained eidolon's outsider subtype brings its own granted-evolution list,
# alignment locks and EP table, none of which is sourced. Naming the debt on the entry is D12's
# holdback discipline -- an unmodelled feature is described, never silently absent.
UNCHAINED_HOLDBACK = ('unchained summoner: subtype-granted evolutions, alignment locks and the '
                      'unchained evolution-point table are not sourced, so this eidolon carries its '
                      'base form and no evolutions (companions ticket 07, ruling 1)')

# A qualified evolution token: `limbs (arms)`, `reach (bite)`. Same vocabulary the data gate reads.
_QUALIFIED = re.compile(r'^(.*?)\s*\((.*)\)$')


def _split_token(token):
    """`limbs (arms)` -> ('limbs', 'arms'); `bite` -> ('bite', None)."""
    match = _QUALIFIED.match(token)
    if not match:
        return token, None
    return match.group(1).strip(), match.group(2).strip()


def _repeat_cap(formula, level):
    """`repeat.max_formula` at `level`, or None for unlimited (EP is the real cap).

    The grammar is `N` or `N + level // M` and is gated by `validate_eidolon_data.py`; an
    unreadable cap resolves to 1 here rather than to unlimited, because the failure that costs
    something is a cap that silently stops capping.
    """
    if formula is None:
        return None
    try:
        base, _, per = str(formula).partition('+')
        cap = int(base.strip())
        if per.strip():
            cap += level // int(per.split('//')[1].strip())
        return cap
    except (ValueError, IndexError):
        return 1


def _eidolon_data(character):
    """The three data files, or None when any is missing -- in which case the creature degrades."""
    forms = getattr(character, 'eidolon_base_forms', None) or {}
    table = getattr(character, 'eidolon_table', None) or {}
    evolutions = getattr(character, 'eidolon_evolutions', None) or {}
    if not (forms.get('forms') and table.get('levels') and evolutions.get('evolutions')):
        return None
    return {'forms': forms, 'table': table, 'evolutions': evolutions}


def _pick_base_form(rng, forms, small_odds=25):
    """A base form and a size. Ticket 07 ruling 2: the full scraped pool, both sizes.

    The scrape found SIX forms, not the seven ticket 07 assumed: `pf-eidolon-forms` ships an
    Aberrant Baseform that the d20pfsrd chained rules do not contain, and the base-form file says
    so. `validate_eidolon_data.py` asserts that pair is the only unmapped one, so a form that
    silently stops being offered fails there rather than here.
    """
    name = rng.choice(sorted(forms['forms']))
    form = forms['forms'][name]
    small = rng.randint(1, 100) <= small_odds
    size = 'small' if small else form.get('default_size', 'medium')
    actor = form.get('pf_content_small') if small else form.get('pf_content')
    return name, form, size, actor


def _free_evolutions(form):
    """The form's free evolutions as held counts: {'limbs': ['legs', 'legs'], 'bite': [None]}.

    The value in the data is HOW MANY TIMES the form grants it, not what it costs -- the quadruped's
    `limbs (legs): 2` is two pairs of legs, and the avian's `flight: 1` is one flight evolution that
    would have cost 2 EP. Free evolutions cost nothing but DO count against repeat caps and the Max
    Attacks column, which is why they are seeded into the same held state the spender reads.
    """
    held = {}
    for token, count in (form.get('free evolutions') or {}).items():
        name, qualifier = _split_token(token)
        held.setdefault(name, []).extend([qualifier] * max(1, int(count)))
    return held


def _attacks_held(held, pool):
    return sum((pool[name]['grants_attack'] or 0) * len(picks)
               for name, picks in held.items() if name in pool)


def _is_legal(name, evolution, held, pool, level, form, size, budget, max_attacks, abilities):
    """Ticket 07 ruling 4: prereqs, form restriction, size, RAW caps and Max Attacks, every one of
    them a data field. Returns True when this evolution may be bought right now.

    `abilities` is the eidolon's running scores -- the form's own, the Small package, and every
    increase bought so far. Only the spell-like-ability chain reads it (Cha 11/12/13), so the
    table's Str/Dex bonus is deliberately absent: it lands in the stat block, and adding it here
    would let a Str bonus satisfy a Cha gate by accident.
    """
    if (evolution.get('cost') or 0) > budget:
        return False

    prereqs = evolution.get('prereqs') or {}
    minimum = prereqs.get('min_summoner_level')
    if minimum and level < minimum:
        return False
    if prereqs.get('forms') and form not in prereqs['forms']:
        return False
    if prereqs.get('size') and prereqs['size'] != size:
        return False
    if prereqs.get('any_attack') and not _attacks_held(held, pool):
        return False
    for stat, floor in (prereqs.get('min_ability') or {}).items():
        if (abilities.get(stat) or 0) < floor:
            return False
    # PARITY, not mere presence. Slam's printed text is "can be selected more than once, but the
    # eidolon must possess an equal number of the limbs evolution", and claws / hooves / pincers /
    # sting / tail slap all hang off a body part the same way. Checking only that the prereq is
    # HELD bought a tauric eidolon two slams off one pair of arms in the first smoke run -- legal
    # to the filter, illegal at the table, and invisible on the sheet.
    already = len(held.get(name, []))
    for token in prereqs.get('evolutions') or []:
        required, qualifier = _split_token(token)
        picks = held.get(required)
        if not picks:
            return False
        if qualifier and qualifier not in picks:
            # The qualifier may name another evolution the prereq hangs off (`reach (bite)`)
            # rather than one of its own choices.
            if qualifier not in held:
                return False
            supply = len(picks)
        else:
            supply = picks.count(qualifier) if qualifier else len(picks)
        if supply <= already:
            return False

    cap = _repeat_cap((evolution.get('repeat') or {}).get('max_formula'), level)
    if cap is not None and already >= cap:
        return False

    gained = evolution.get('grants_attack') or 0
    if gained and _attacks_held(held, pool) + gained > max_attacks:
        return False
    return True


def _roll_choice(rng, name, evolution, held, level):
    """The pick an evolution carries with it (an ability, an energy type, arms-or-legs, a skill).

    Returns None when the evolution has no choice, and None when every option is already at its own
    per-choice cap -- the caller reads that as "not legal right now", which is how `ability
    increase` stops at RAW's once per score plus one per six levels.
    """
    choice = evolution.get('choice')
    if not choice:
        return None, True
    options = list(choice.get('options') or [])
    if not options and choice.get('kind') == 'skill':
        from utils import data as _data
        options = sorted(_data.SKILL_IDS)
    per_choice = _repeat_cap((evolution.get('repeat') or {}).get('per_choice_max_formula'), level)
    taken = held.get(name, [])
    if per_choice is not None:
        options = [option for option in options if taken.count(option) < per_choice]
    if not options:
        return None, False
    return rng.choice(sorted(options)), True


def _spend(rng, budget, held, pool, level, form, size, max_attacks, abilities):
    """Ticket 07 ruling 3: pure random greedy. Buy a random affordable, legal evolution until none
    remains -- no weighting and no curated first stage, which is what every other chooser here does.

    Mutates `held` and `abilities`; returns (bought, spent, size). `bought` is ordered by purchase,
    so the entry shows what the creature grew and in what order -- and so the spell-like chain
    reads in the order it was actually bought.
    """
    bought, spent = [], 0
    names = sorted(pool)
    while True:
        legal = [name for name in names
                 if _is_legal(name, pool[name], held, pool, level, form, size, budget - spent,
                              max_attacks, abilities)]
        if not legal:
            break
        rng.shuffle(legal)
        for name in legal:
            evolution = pool[name]
            qualifier, ok = _roll_choice(rng, name, evolution, held, level)
            if not ok:
                continue                     # every option of this one is capped; try the next
            held.setdefault(name, []).append(qualifier)
            spent += evolution['cost']
            size = evolution.get('grants_size') or size
            for stat, delta in (evolution.get('ability_scores') or {}).items():
                abilities[stat] = (abilities.get(stat) or 0) + delta
            choice = evolution.get('choice') or {}
            if choice.get('kind') == 'ability' and qualifier:
                abilities[qualifier] = (abilities.get(qualifier) or 0) + (choice.get('amount') or 0)
            bought.append({'name': evolution.get('name') or name, 'key': name,
                           'cost': evolution['cost'], 'choice': qualifier,
                           'benefit': evolution.get('benefit')})
            break
        else:
            break                            # nothing in the legal set could resolve its choice
    return bought, spent, size


def _starting_abilities(forms, form, size):
    """The eidolon's scores before any evolution: the form's own, plus the Small package (D11's
    discipline again -- the geometry is `SIZE_GEOMETRY`'s, only the ability deltas are here)."""
    scores = dict(((form.get('starting statistics') or {}).get('ability scores')) or {})
    if size == 'small':
        for stat, delta in ((forms.get('small_package') or {}).get('ability_scores') or {}).items():
            scores[stat] = (scores.get(stat) or 0) + delta
    return scores


def _aspect(character, rng, entry, pool, level, held, form, size, max_attacks, abilities):
    """Aspect / Greater Aspect (07 ruling 5): the summoner may divert EP to itself.

    Daniel overrode the recommended deferral, so this is in scope: up to 2 EP at 10th and up to 6 at
    18th, the amount ROLLED inside the cap (the generator's chance-based idiom, not always-maximum),
    spent through the same legality filter and recorded on the PC's own sheet through the ordinary
    class-feature machinery -- so it needs no new export key and renders where every other class
    choice does.
    """
    cap = next((amount for tier, amount in ASPECT_TIERS if level >= tier), 0)
    if not cap:
        return 0
    diverted = rng.randint(0, cap)
    if not diverted:
        return 0

    # The summoner takes evolutions its own eidolon could take, so the filter reads COPIES of the
    # eidolon's held state and scores -- the picks are the summoner's and must not leave a mark on
    # the creature's own caps, attacks or abilities.
    # The copy has to go one level deep: `_spend` appends to the LISTS inside `held`, so a shallow
    # dict() would let the summoner's own picks count against the creature's repeat caps.
    mirror = {name: list(picks) for name, picks in held.items()}
    taken, spent, _ = _spend(rng, diverted, mirror, pool, level, form, size, max_attacks,
                             dict(abilities))
    if not taken:
        return 0
    from utils.class_func.generic_func import _record_choice_level, update_class_features
    bucket = {}
    for pick in taken:
        label = f"{pick['name']} ({pick['choice']})" if pick['choice'] else pick['name']
        bucket[label] = pick['benefit']
        _record_choice_level(character, 'Aspect', label, level)
    update_class_features(character, {'Aspect': bucket}, class_name=entry['grantor'])
    return spent


def _eidolon_entry(character, row, grantor, unchained, effective_level):
    """The creature itself: base form, size, identity, compendium actor. No evolutions yet -- the
    pool is not knowable until `_stack` has resolved the effective level."""
    data = _eidolon_data(character)
    if data is None:
        return None
    # THE GLOBAL STREAM, deliberately -- the same one `_pick_species` and the sex roll use. The
    # per-creature RNG cannot be used here: it is seeded off the entry's identity, which does not
    # exist yet, and seeding it off (grantor, level) instead made the form a pure function of the
    # level -- every level-10 summoner in the world got the same tauric eidolon. Caught by the
    # legality sweep's form histogram, which showed five forms in exact multiples of the seed count.
    name, form, size, actor = _pick_base_form(random, data['forms'])

    entry = _entry(character, row, grantor, name, None, form.get('starting statistics'), None,
                   outcome='granted', archetype=None, effective_level=effective_level)
    entry['base_form'] = name
    entry['base_form_notes'] = list(form.get('notes') or [])
    # Two size fields, and both are needed: `size` is FINAL (the Large evolution moves it) while
    # `base_size` is what the creature was born as. `stats.size_change` is the difference, and D11's
    # ruling is that the geometry for it is applied exactly once -- so the block has to be able to
    # tell "Small by base form" from "Medium that grew".
    entry['base_size'] = size
    entry['size'] = size
    entry['pf_content'] = actor
    entry['evolutions'] = []
    entry['ep'] = {'pool': 0, 'spent': 0, 'diverted': 0}
    if unchained:
        entry['flags'].append('unchained_degraded')
        entry['holdback'] = UNCHAINED_HOLDBACK
    return entry


def spend_eidolon_evolutions(character):
    """Buy every granted eidolon's evolutions, after `_stack` has fixed its effective level.

    Degraded (unchained) entries are skipped by their own flag rather than by re-deriving which
    class granted them: `_stack` may have merged two grantors into one creature, and the flag is the
    record of what was decided when both were still visible.
    """
    data = _eidolon_data(character)
    if data is None:
        return
    pool = {name: evolution for name, evolution in data['evolutions']['evolutions'].items()
            if not evolution.get('exclude')}
    levels = data['table']['levels']

    for entry in getattr(character, 'bonded_creatures', None) or []:
        if entry['type'] != 'eidolon' or not entry.get('species'):
            continue
        if 'unchained_degraded' in entry['flags']:
            continue
        level = entry['effective_level']
        chassis = levels.get(str(level)) or levels.get(str(min(20, max(1, level))))
        entry['chassis'] = chassis
        if not chassis:
            continue

        form = data['forms']['forms'][entry['base_form']]
        free = _free_evolutions(form)
        held = {name: list(picks) for name, picks in free.items()}
        abilities = _starting_abilities(data['forms'], form, entry['size'])
        rng = _creature_rng(entry, 'eidolon-evolutions')

        budget = chassis['evolution_pool']
        diverted = _aspect(character, rng, entry, pool, level, held, entry['base_form'],
                           entry['size'], chassis['max_attacks'], abilities)
        bought, spent, size = _spend(rng, budget - diverted, held, pool, level,
                                     entry['base_form'], entry['size'],
                                     chassis['max_attacks'], abilities)

        entry['evolutions'] = bought
        entry['free_evolutions'] = free
        entry['size'] = size
        entry['ep'] = {'pool': budget, 'spent': spent, 'diverted': diverted}


def _creature_rng(entry, salt):
    """`companion_stats._rng`, imported late. The two modules are peers -- companion_stats reads the
    entries this file builds -- so the import stays inside the call, exactly as `animal_feats` does
    with `companion_feats`."""
    from utils.class_func.companion_stats import _rng
    return _rng(entry, salt)


# ==============================================================================================
# End of Eidolon section
# ==============================================================================================


def animal_chooser(character):
    """Back-compat shim: the resolver is the single path now."""
    resolve_bonded_creatures(character)
    return getattr(character, 'chosen_animal', None)


def animal_feats(character):
    """Back-compat shim: the feat economy moved to `companion_feats` (spec section 8, D15/D16).

    It outgrew this module. What used to be "pick N names out of a bag" is now a prerequisite gate,
    a grant-level record, feat tax and a flaw roll -- a concern of its own, and one that has to read
    the merged ability scores this module deliberately knows nothing about.
    """
    from utils.class_func.companion_feats import companion_feats
    return companion_feats(character)
