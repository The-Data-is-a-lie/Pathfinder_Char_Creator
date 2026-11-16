"""Selection mode: a build concept the client pins, with everything unpinned left to the dice.

The request arrives as one named key, ``selection`` (``app.py::update_character_data`` pops it the
way it pops ``optimize``), and ``phase_selection`` resolves it ONCE, before the classes are picked,
onto two attributes:

* ``character.selection`` -- the resolved plan, or ``None`` when the request carried no usable pin.
  ``None`` is the whole random-mode contract: every chooser below asks this module for its pin
  through an accessor that returns "nothing pinned" for ``None``, and then takes the path it has
  always taken, drawing what it has always drawn. That is what keeps an unpinned request
  byte-identical to a request made before this module existed.
* ``character.selection_report`` -- ``[{'pin': ..., 'reason': ...}]``, one row per pin that could
  not be honoured. Always a list. It is exported as the payload key ``selection_report``.

THE RULINGS (grilled 2026-11-14/15; the changelog carries the rejected alternatives):

* Pins are GUARANTEES. A pin switches on whatever the generator controls to make itself true --
  Spheres is turned on by a sphere pin, a pinned class skips the random pool's pruning rules, a
  pinned path count ignores the house roll's bounds.
* What is still impossible is DROPPED AND REPORTED, never fatal: the character generates, and the
  report says which pin fell and why. A typo in a class name must not cost the caller a character.
* With ``optimize`` on, pins win and the optimizer fills what is unpinned.

WHO OWNS WHAT. This module owns the request vocabulary (``REQUEST_KEYS``), the resolution of names
onto the data files' own keys, the level arithmetic (``resolve_levels``) and the report. It does
NOT own any game list: classes come from ``character.class_data``, schools from
``character.wizard_schools`` and ``spells.csv``, spheres from ``spheres._available_spheres``,
disciplines from ``data.disciplines``. ``options()`` republishes those same sources for the
client's pickers (``GET /selection_options``), which is why a client never needs a list of its own
-- and ``scripts/gates/validate_selection.py`` is what holds the two ends together.

The choosers that honour a pin, each at its own site (grep the accessor):
``util.select_classes`` (``pinned_classes``), ``level_and_bab.randomize_level``
(``pinned_class_levels``), ``power_role.stat_order`` (``pinned_stat_priority``),
``spells.spell_theme_func`` / ``limit_school_func`` and ``wizard_school`` (``school_pins``),
``path_of_war`` (``pinned_disciplines`` / ``pinned_paths``), ``spheres`` (``pinned_spheres``),
``feats.pinned_feat_chooser`` (``pinned_feats``), and ``build_steer`` (``pinned_build``) -- the
one pin that is a STEER rather than a guarantee; its module docstring says why.
"""
import re

from utils import data

from .pipeline import phase

# The keys a `selection` object may carry. Anything else is reported rather than ignored: an
# unrecognised key is almost always a misspelled one, and silence would read as "honoured".
REQUEST_KEYS = ('classes', 'stat_priority', 'schools', 'spheres', 'path_of_war', 'feats', 'build')

# A3: an ordered list of one to four classes, the first being the primary.
MAX_PINNED_CLASSES = 4

# pf1 has three spellbook slots (primary / secondary / tertiary); a fourth casting class would lose
# its spellbook on the Foundry sheet. util.select_classes enforces the same cap on the random pool.
MAX_CASTER_CLASSES = 3

# How many best-fitting classes `options()` names beside each build.
BUILD_CLASS_HINTS = 6

ABILITIES = ('str', 'dex', 'con', 'int', 'wis', 'cha')
_ABILITY_ALIASES = {
    'strength': 'str', 'dexterity': 'dex', 'constitution': 'con',
    'intelligence': 'int', 'wisdom': 'wis', 'charisma': 'cha',
}

# The four tables of wizard_schools.json, with the branch number wizard_school_chooser gives each.
_WIZARD_TABLES = (
    (1, 'elemental_schools'),
    (2, 'elemental_subschools'),
    (3, 'schools'),
    (4, 'subschools'),
)


def _norm(value):
    """Client string -> comparison key: lower-cased, hyphens and underscores read as spaces
    (the dropdown slugs "barbarian-(unchained)"), apostrophes dropped ("Fool's Errand"), runs of
    whitespace collapsed."""
    text = str(value if value is not None else '').lower()
    text = text.replace("'", '').replace('’', '').replace('-', ' ').replace('_', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def _as_list(value):
    if value is None or value == '':
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _as_level(value):
    """An optional class level: a positive whole number, or None for "unpinned"."""
    if value is None or value == '' or isinstance(value, bool):
        return None
    try:
        level = int(value)
    except (TypeError, ValueError):
        return None
    return level if level >= 1 else None


def unmet(character, pin, reason):
    """Record one pin that could not be honoured. The only writer of ``selection_report``."""
    report = getattr(character, 'selection_report', None)
    if report is None:
        report = character.selection_report = []
    row = {'pin': str(pin), 'reason': str(reason)}
    if row not in report:
        report.append(row)


# --------------------------------------------------------------------------- #
# Spell schools (the eight a spell can belong to) -- read from the data, cached
# --------------------------------------------------------------------------- #
_SPELL_SCHOOLS = None


def spell_schools():
    """The spell schools a theme can favour or ban: every `school` in spells.csv with enough
    spells to carry a theme. The same threshold spells.spell_theme_func rolls from, so a pin can
    never name a school the random roll could not have produced."""
    global _SPELL_SCHOOLS
    if _SPELL_SCHOOLS is None:
        from .spells import _load_spell_data, THEME_SCHOOL_MIN_SPELLS
        counts = _load_spell_data()['school'].value_counts()
        _SPELL_SCHOOLS = tuple(sorted(counts[counts > THEME_SCHOOL_MIN_SPELLS].index.tolist()))
    return _SPELL_SCHOOLS


# --------------------------------------------------------------------------- #
# Resolution: one function per request key, each returning its slice of the plan
# --------------------------------------------------------------------------- #
def _resolve_classes(character, raw):
    known = {_norm(name): name for name in character.class_data}
    out, seen, casters = [], set(), 0
    for index, item in enumerate(_as_list(raw)):
        label = f'classes[{index}]'
        if isinstance(item, dict):
            name, level_raw = item.get('name'), item.get('level')
        else:
            name, level_raw = item, None
        key = known.get(_norm(name))
        if key is None:
            unmet(character, f'{label}: {name}', 'no class by that name')
            continue
        if key in seen:
            unmet(character, f'{label}: {name}', 'pinned twice; a class is listed once, with its level')
            continue
        if len(out) >= MAX_PINNED_CLASSES:
            unmet(character, f'{label}: {name}',
                  f'a character is built from at most {MAX_PINNED_CLASSES} classes')
            continue
        is_caster = str(character.class_data[key].get('casting level', 'none')).lower() != 'none'
        if is_caster and casters >= MAX_CASTER_CLASSES:
            unmet(character, f'{label}: {name}',
                  f'a character can carry {MAX_CASTER_CLASSES} spellbooks, and '
                  f'{MAX_CASTER_CLASSES} casting classes are already pinned')
            continue
        level = _as_level(level_raw)
        if level_raw not in (None, '') and level is None:
            unmet(character, f'{label}.level: {level_raw}',
                  'a class level is a whole number of 1 or more; the level was left to the roll')
        casters += 1 if is_caster else 0
        seen.add(key)
        out.append({'name': key, 'level': level})
    return out


def _resolve_stat_priority(character, raw):
    tokens = _as_list(raw)
    if not tokens:
        return None
    order = []
    for token in tokens:
        key = _norm(token)
        key = _ABILITY_ALIASES.get(key, key)
        if key not in ABILITIES:
            unmet(character, f'stat_priority: {token}', 'not one of the six abilities')
            continue
        if key not in order:
            order.append(key)
    if not order:
        return None
    # Whatever the list never mentions follows in the standard order, and is thereby the dump --
    # the same rule power_role.stat_order applies to a role's priority.
    order.extend(ability for ability in ABILITIES if ability not in order)
    return order


def _resolve_schools(character, raw):
    empty = {'specialty': None, 'specialty_table': None, 'specialty_school': None,
             'preferred': [], 'opposition': []}
    if not raw:
        return empty
    if not isinstance(raw, dict):
        unmet(character, 'schools', 'expected an object with specialty / preferred / opposition')
        return empty
    for key in raw:
        if key not in ('specialty', 'preferred', 'opposition'):
            unmet(character, f'schools.{key}', 'not a school pin (specialty, preferred, opposition)')
    plan = dict(empty)
    theme = {_norm(name): name for name in spell_schools()}
    tables = character.wizard_schools

    specialty = raw.get('specialty')
    if specialty not in (None, ''):
        wanted = _norm(specialty)
        for branch, table in _WIZARD_TABLES:
            match = next((key for key in tables[table] if _norm(key) == wanted), None)
            if match is None:
                continue
            plan['specialty'], plan['specialty_table'] = match, branch
            # The spell school the specialty favours: itself for one of the eight, its parent for
            # a subschool, and none for universalist or an elemental school (those cut across
            # the eight, so there is no single school to weight).
            if table == 'schools':
                plan['specialty_school'] = theme.get(_norm(match))
            elif table == 'subschools':
                plan['specialty_school'] = theme.get(_norm(tables[table][match].get('associated school')))
            break
        else:
            unmet(character, f'schools.specialty: {specialty}', 'no arcane school by that name')

    def spell_school_list(field):
        out = []
        for name in _as_list(raw.get(field)):
            key = theme.get(_norm(name))
            if key is None:
                unmet(character, f'schools.{field}: {name}', 'not one of the spell schools')
            elif key not in out:
                out.append(key)
        return out

    plan['preferred'] = [s for s in spell_school_list('preferred') if s != plan['specialty_school']]
    favoured = set(plan['preferred']) | ({plan['specialty_school']} if plan['specialty_school'] else set())
    for school in spell_school_list('opposition'):
        if school in favoured:
            unmet(character, f'schools.opposition: {school}',
                  'also pinned as the specialty or a preferred school; favoured wins')
        else:
            plan['opposition'].append(school)
    return plan


def _resolve_spheres(character, raw):
    from . import spheres as spheres_module
    pools = {system: {_norm(key): key for key in spheres_module._available_spheres(system)}
             for system in ('power', 'might')}
    out = []
    for item in _as_list(raw):
        if isinstance(item, dict):
            name, system = item.get('name'), _norm(item.get('system')) or None
        else:
            name, system = item, None
        wanted = _norm(name)
        # Either system, Power first: no sphere name is shared between the two, so the order only
        # decides which book is searched first.
        hit = next(((pools[sy][wanted], sy) for sy in ('power', 'might')
                    if (system in (None, sy)) and wanted in pools[sy]), None)
        if hit is None:
            unmet(character, f'spheres: {name}', 'no sphere by that name')
        elif hit not in out:
            out.append(hit)
    return out


def _resolve_path_of_war(character, raw):
    plan = {'disciplines': [], 'paths': None}
    if not raw:
        return plan
    if not isinstance(raw, dict):
        unmet(character, 'path_of_war', 'expected an object with disciplines / paths')
        return plan
    for key in raw:
        if key not in ('disciplines', 'paths'):
            unmet(character, f'path_of_war.{key}', 'not a Path of War pin (disciplines, paths)')
    from . import path_of_war as pow_module
    resolvable = pow_module._discipline_key_map(character)
    known = {pow_module._dnorm(name): name for name in data.disciplines
             if pow_module._dnorm(name) in resolvable}
    for name in _as_list(raw.get('disciplines')):
        key = known.get(pow_module._dnorm(str(name).replace('-', ' ').replace('_', ' ')))
        if key is None:
            unmet(character, f'path_of_war.disciplines: {name}', 'no discipline by that name')
        elif key not in plan['disciplines']:
            plan['disciplines'].append(key)
    paths = raw.get('paths')
    if paths not in (None, ''):
        try:
            plan['paths'] = max(0, int(paths))
        except (TypeError, ValueError):
            unmet(character, f'path_of_war.paths: {paths}', 'a path count is a whole number')
    return plan


def _resolve_feats(character, raw):
    """Pinned feats, spelled as the feat data spells them.

    Resolution is by name only, against EVERY feat a pin may name (``feats.pinnable_feat_index``:
    the printed feats and the homebrew library). Whether the character can take one is not known
    yet -- its class, level and scores are not rolled -- so prerequisites, the homebrew flag and
    the feat budget are judged where the feat is taken, in ``feats.pinned_feat_chooser``.

    The generator holds a feat by its base name ("Weapon Focus", never "Weapon Focus (longsword)"),
    so a parenthetical the data does not carry is read as the base feat.
    """
    names = _as_list(raw)
    if not names:
        return []
    from .feats import pinnable_feat_index
    index = pinnable_feat_index()
    known = {_norm(key): key for key in index}
    out = []
    for name in names:
        key = known.get(_norm(name)) or known.get(_norm(str(name).split(' (')[0]))
        if key is None:
            unmet(character, f'feats: {name}', 'no feat by that name')
        elif index[key]['name'] not in out:
            out.append(index[key]['name'])
    return out


def _resolve_build(character, raw):
    """The pinned build archetype, spelled as build_archetypes.json spells it, or None.

    One name. The scorer's fallback label is not offered: it is what a character is called when it
    is nothing in particular, which is not something to steer toward.
    """
    if raw in (None, '', [], {}):
        return None
    if not isinstance(raw, str):
        unmet(character, 'build', 'expected the name of one build')
        return None
    from . import build_steer
    known = {_norm(name): name for name in build_steer.roster()}
    name = known.get(_norm(raw))
    if name is None:
        unmet(character, f'build: {raw}', 'no build by that name')
    return name


@phase(requires=[], provides=['selection', 'selection_report'])
def phase_selection(character, request):
    """Resolve the `selection` request onto the character, before any class is picked.

    Runs ahead of ``phase_bootstrap_identity`` because ``select_classes`` is the first reader.
    It draws nothing from the RNG, pinned or not: resolution is lookup, and every random choice a
    pin replaces is skipped at the chooser, not here.
    """
    character.selection_report = []
    character.selection = None
    if request in (None, '', {}, []):
        return
    if not isinstance(request, dict):
        unmet(character, 'selection', 'expected an object of pins')
        return
    for key in request:
        if key not in REQUEST_KEYS:
            unmet(character, key, f'not a selection key (known: {", ".join(REQUEST_KEYS)})')

    plan = {
        'classes': _resolve_classes(character, request.get('classes')),
        'stat_priority': _resolve_stat_priority(character, request.get('stat_priority')),
        'schools': _resolve_schools(character, request.get('schools')),
        'spheres': _resolve_spheres(character, request.get('spheres')),
        'path_of_war': _resolve_path_of_war(character, request.get('path_of_war')),
        'feats': _resolve_feats(character, request.get('feats')),
        'build': _resolve_build(character, request.get('build')),
    }
    schools, martial = plan['schools'], plan['path_of_war']
    pinned_anything = (plan['classes'] or plan['stat_priority'] or plan['spheres'] or plan['feats']
                       or plan['build']
                       or schools['specialty'] or schools['preferred'] or schools['opposition']
                       or martial['disciplines'] or martial['paths'] is not None)
    if pinned_anything:
        character.selection = plan


# --------------------------------------------------------------------------- #
# Accessors: what each chooser asks. Every one answers "nothing pinned" for None.
# --------------------------------------------------------------------------- #
def _plan(character):
    return getattr(character, 'selection', None) or None


def pinned_classes(character):
    """Pinned class names in order (first = primary); [] when classes are unpinned."""
    plan = _plan(character)
    return [row['name'] for row in plan['classes']] if plan else []


def pinned_class_levels(character):
    """{class name: level or None} for the pinned classes; None when classes are unpinned."""
    plan = _plan(character)
    if not plan or not plan['classes']:
        return None
    return {row['name']: row['level'] for row in plan['classes']}


def pinned_stat_priority(character):
    """All six abilities in placement order, or None."""
    plan = _plan(character)
    return list(plan['stat_priority']) if plan and plan['stat_priority'] else None


def school_pins(character):
    """The schools slice of the plan, or None when no school is pinned."""
    plan = _plan(character)
    if not plan:
        return None
    schools = plan['schools']
    if not (schools['specialty'] or schools['preferred'] or schools['opposition']):
        return None
    return schools


def pinned_spheres(character):
    """[(sphere data key, 'power' | 'might'), ...] in pin order."""
    plan = _plan(character)
    return list(plan['spheres']) if plan else []


def pinned_disciplines(character):
    """Pinned discipline names, spelled as data.disciplines spells them."""
    plan = _plan(character)
    return list(plan['path_of_war']['disciplines']) if plan else []


def pinned_feats(character):
    """Pinned feat names in pin order, spelled as the feat data spells them."""
    plan = _plan(character)
    return list(plan['feats']) if plan else []


def pinned_build(character):
    """The pinned build archetype's name, or None."""
    plan = _plan(character)
    return plan['build'] if plan else None


def pinned_paths(character):
    """How many martial paths the pins demand of a non-initiator, or None when unpinned.

    A pinned count is a forced count; pinned disciplines raise it to at least their number, since
    each one is a path of its own.
    """
    plan = _plan(character)
    if not plan:
        return None
    martial = plan['path_of_war']
    if martial['paths'] is None and not martial['disciplines']:
        return None
    return max(martial['paths'] or 0, len(martial['disciplines']))


# --------------------------------------------------------------------------- #
# A4: the level arithmetic. Pure, so the gate can pin its three cases.
# --------------------------------------------------------------------------- #
def resolve_levels(pinned_levels, rolled_total, split):
    """Class levels for a pick list where some picks carry a pinned level.

    ``pinned_levels`` -- one entry per pick, an int or None (unpinned).
    ``rolled_total``  -- the total the level range rolled; IGNORED when every pick is levelled.
    ``split(total, count)`` -- shares ``total`` levels among ``count`` unlevelled picks, each
    getting at least 1 (``level_and_bab._split_levels``, or the optimizer's dip shape).

    * every pick levelled  -> exactly those levels; the total is their sum.
    * some levelled        -> the levelled take theirs first and the unlevelled split what is left
                              of the rolled total, with at least 1 each -- so the total RISES above
                              the roll when the pinned levels leave less than that.
    * none levelled        -> the rolled total, raised to one level per pick. A pinned class is a
                              guarantee, so the pick list is never truncated to fit a low roll.
    """
    levels = list(pinned_levels)
    open_slots = [i for i, level in enumerate(levels) if level is None]
    if not open_slots:
        return levels
    remaining = max(int(rolled_total) - sum(level for level in levels if level is not None),
                    len(open_slots))
    for slot, share in zip(open_slots, split(remaining, len(open_slots))):
        levels[slot] = share
    return levels


def cap_total(levels, ceiling):
    """Trim ``levels`` to sum to at most ``ceiling``, taking from the LAST class first and leaving
    every class at least 1 -- the order a pin list ranks its classes in. Returns the new list."""
    levels = list(levels)
    excess = sum(levels) - ceiling
    for index in range(len(levels) - 1, -1, -1):
        if excess <= 0:
            break
        take = min(excess, levels[index] - 1)
        levels[index] -= take
        excess -= take
    return levels


# --------------------------------------------------------------------------- #
# Post-build audits: pins whose fate is only known after a chooser has run
# --------------------------------------------------------------------------- #
def audit_spheres(character, sphere_data):
    """Report every pinned sphere that ended with no talent in it.

    A sphere is its talents, and talents are paid for (HR1: no freebies), so a pinned sphere the
    feat budget and the mentor together could not fund is not a sphere the character has.
    """
    counts = (sphere_data or {}).get('sphere_counts') or {}
    for sphere, _system in pinned_spheres(character):
        tally = counts.get(sphere.title()) or {}
        if not (tally.get('normal') or tally.get('advanced')):
            unmet(character, f'spheres: {sphere.title()}',
                  'no feat or mentor was left to pay for a talent in it')


def audit_disciplines(character, disciplines):
    """Report every pinned discipline that did not reach the character."""
    have = {_norm(name) for name in (disciplines or [])}
    for name in pinned_disciplines(character):
        if _norm(name) not in have:
            unmet(character, f'path_of_war.disciplines: {name}',
                  'the character has no way into Martial Training (base attack bonus +3)'
                  if not have else 'its Martial Training chain could not be realized')


def audit_build(character, build, label):
    """Report a pinned build the finished character was not named as.

    ``build`` is the dict main_test hands the scorer and ``label`` what the scorer called it. The
    label is a measurement, so this is the one audit that can fail with every chooser having done
    its part: the reason names the gate the character missed, or says another build simply fit
    better.
    """
    target = pinned_build(character)
    if target and str(label) != target:
        from . import build_steer
        unmet(character, f'build: {target}', build_steer.miss_reason(build, target, str(label)))


def audit_feats(character, held, tax_dicts=()):
    """Report every pinned feat the finished character does not hold.

    ``held`` is every feat list the sheet shows; ``tax_dicts`` are the feat-tax bundles, whose
    children are held too (a pinned Great Cleave bundled free onto Cleave is on the sheet, just
    not in a slot). A feat the character already held by rule or by class when the pin was read
    (``character.pinned_feats_held``) is honoured without a slot. What remains was taken and then
    lost to the feat track's count guarantee -- the budget was oversubscribed.
    """
    def base(name):
        return _norm(str(name).split(' (')[0])

    have = {base(name) for name in (held or [])}
    for bundle in tax_dicts or ():
        for children in (bundle or {}).values():
            have.update(base(child) for child in (children or []))
    have.update(base(name) for name in (getattr(character, 'pinned_feats_held', None) or []))
    reported = {row['pin'] for row in getattr(character, 'selection_report', None) or []}
    for name in pinned_feats(character):
        pin = f'feats: {name}'
        if base(name) not in have and pin not in reported:
            unmet(character, pin, 'no feat slot left')


# --------------------------------------------------------------------------- #
# GET /selection_options: the pickers' lists, straight from the data
# --------------------------------------------------------------------------- #
def options(character):
    """Everything a client needs to build a selection picker, read from the same sources the
    resolvers above read. ``character`` is any freshly constructed character (its JSON loaded):
    the lists are static data, so the caller may cache the result for the life of the process.
    """
    from . import spheres as spheres_module
    from . import path_of_war as pow_module
    from .level_and_bab import MAX_CHARACTER_LEVEL
    from .feats import pinnable_feat_index
    from . import build_steer
    from utils.util import _available_class_pool

    groups = {}
    for token, label, roster in data.CLASS_GROUPS:
        for name in roster or []:
            groups[str(name).lower()] = (token, label)
    base_token, base_label = data.CLASS_GROUPS[0][0], data.CLASS_GROUPS[0][1]
    classes = []
    for name in sorted(character.class_data):
        token, label = groups.get(name, (base_token, base_label))
        entry = character.class_data[name]
        classes.append({
            'name': name, 'label': name.title(), 'group': token, 'group_label': label,
            'bab': entry.get('bab'),
            'casting': str(entry.get('casting level', 'none')).lower(),
        })

    tables = character.wizard_schools
    resolvable = pow_module._discipline_key_map(character)
    return {
        'keys': list(REQUEST_KEYS),
        'limits': {'max_classes': MAX_PINNED_CLASSES, 'max_caster_classes': MAX_CASTER_CLASSES,
                   'max_level': MAX_CHARACTER_LEVEL},
        'classes': classes,
        'abilities': list(ABILITIES),
        'schools': {
            'specialty': {table: sorted(tables[table]) for _branch, table in _WIZARD_TABLES},
            'spell_schools': list(spell_schools()),
        },
        'spheres': {system: sorted(key.title() for key in spheres_module._available_spheres(system))
                    for system in ('power', 'might')},
        'disciplines': [name for name in data.disciplines
                        if pow_module._dnorm(name) in resolvable],
        'feats': [{'name': info['name'], 'type': info['type'], 'homebrew': info['homebrew']}
                  for _key, info in sorted(pinnable_feat_index().items())],
        # `classes` is a hint for the picker, best fit first: the classes a build with no class
        # pinned is drawn from come from this same ranking (build_steer.fitting_classes).
        'builds': [{'name': name, 'family': build_steer.roster()[name].get('family', ''),
                    'definition': build_steer.roster()[name].get('definition', ''),
                    'classes': fitting[:BUILD_CLASS_HINTS]}
                   for name, fitting in build_steer.offered(
                       character, sorted(_available_class_pool(character))).items()],
    }
