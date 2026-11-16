"""Blank mode: the sheet behind the Blank Character Generator.

A blank character is a class (or several) at a level, a race, and NOTHING CHOSEN: every ability at
10, no feats, no spells, no gear -- and in their place a list of ``slots``, one row per thing the
character is owed (a feat at 3rd level, a fighter bonus feat at 4th, a rogue talent at 2nd, a minor
flaw, an ability score increase at 8th). The client draws one placeholder per row and the player
drags the real thing onto the sheet.

HOW IT IS MADE: GENERATE, THEN BLANK
------------------------------------
The request runs the ordinary pipeline with the classes and levels pinned (selection mode's
``classes`` pin), and ``apply`` rewrites the finished payload:

* every key is emptied BY TYPE -- a list becomes ``[]``, a dict ``{}``, a string ``''``, a number
  ``0`` -- so the payload keeps the exact keys, order and shapes two other repositories parse, and
  nothing rolled can survive by being overlooked;
* the few keys in ``KEEP`` pass through, because the classes, the level and the race decide them
  and nothing else does;
* a handful are rebuilt here from the data (the class rows without their rolled archetype, the
  spellbooks without their spells, hit points at a fixed rule, a name);
* and ``slots`` is computed from the functions that own each count.

*Rejected:* building the payload from scratch, which means restating the neutral value and shape
of some 190 keys by hand and keeping that list in step with ``payload.PAYLOAD_KEYS`` forever. And
running the pipeline with every chooser switched off, which is a guard in each of fifty modules.

``scripts/gates/validate_blank.py`` holds this to its promise: the same request under two seeds
must produce the same sheet, so anything random that leaks through ``KEEP`` or a rebuild fails
there rather than on a player's screen.

THE COUNTS ARE NOT RESTATED. Each slot count is read from its owner: the feat economy from
``level_and_bab.update_level`` and ``feat_level_assignment.normal_feat_slot_levels``, class bonus
and teamwork feats from ``extra_combat_feats``, class choices from ``class_choice_schedule.json``
through ``generic_func.levels_for``, ability increases from
``level_and_bab.update_level_ability_score``, spells known from the spellbooks the pipeline built,
skill ranks from ``skill_ranks.class_skill_points``. House-rule slots (story, flavor and flaw
feats, the two creation feats, the flaws themselves) appear exactly when those owners grant them.
"""
import re
from types import SimpleNamespace

from utils import data

from .extra_combat_feats import (bloodline_bonus_feat_levels, class_bonus_feat_levels,
                                 class_bonus_feat_slots, teamwork_feat_slots)
from .feat_level_assignment import normal_feat_slot_levels
from .flag_assign import human_flag_assigner
from .generic_func import levels_for
from .level_and_bab import update_level, update_level_ability_score
from .skill_ranks import class_skill_points, misc_homebrew_enabled
from .spells import caster_formula, spells_known_attr

ABILITIES = ('str', 'dex', 'con', 'int', 'wis', 'cha')
# Every ability on a blank sheet. PF1's average score: no modifier either way.
BLANK_ABILITY = 10
# The flaws a blank sheet leaves room for, in the order the house rule deals them (the first flaw
# is minor, the second major -- flaws.pick_flaws).
BLANK_FLAWS = ('Minor', 'Major')
# Traits are dragged on rather than rolled; PF1's standard allotment is two.
BLANK_TRAITS = 2

# Keys that pass through untouched: decided by the request (region), the race, or the pinned
# classes and levels, and by nothing the dice touch. Anything not here is emptied by type.
KEEP = (
    'region', 'chosen_race', 'land_speed', 'c_class', 'c_class_display', 'c_class_2',
    'level', 'total_level', 'bab_total', 'save_bases', 'casting_level_str_foundry',
    'selection_report', 'generator_version', 'license_url',
)
# The spellbook fields a class and level decide; a book's other fields are emptied by type, and
# the three the caster formula owns are recomputed (see _blank_spellbook).
_SPELLBOOK_KEEP = ('name', 'display', 'level', 'capped_level', 'casting_level_string',
                   'casting_stat', 'divine')
# Keys whose TYPE depends on what was rolled: a character in armor carries numbers where an
# unarmored one carries '', and one with a companion a name where another carries None. Emptying
# by type would let that difference through, so their blank value is stated -- and it is the value
# a character WITHOUT the thing carries, which is what a blank sheet is.
NEUTRAL = {
    'armor_ac': 0, 'shield_ac': 0,
    'armor_name': '', 'armor_spell_failure': '', 'armor_weight': '',
    'armor_armor_check_penalty': '', 'armor_max_dex_bonus': '',
    'shield_name': '', 'shield_spell_failure': '', 'shield_weight': '',
    'shield_armor_check_penalty': '', 'shield_max_dex_bonus': '',
    'animal_companion': None,
}

_ORDINALS = ('0-level', '1st-level', '2nd-level', '3rd-level', '4th-level', '5th-level',
             '6th-level', '7th-level', '8th-level', '9th-level')
_HIT_DIE = re.compile(r'd(\d+)')


def requested(value):
    """Whether a request asked for a blank sheet. The named ``blank`` input: true / 'y' / 'yes'."""
    if isinstance(value, bool):
        return value
    return str(value or '').strip().lower() in ('y', 'yes', 'true', '1')


def selection_for(selection_request):
    """The selection a blank request runs with: its ``classes`` pin and nothing else. A blank sheet
    has no feats, spheres or schools to pin, and a build concept left active in the client must
    not turn Spheres on or spend feat slots behind a sheet that will show none of it."""
    classes = (selection_request or {}).get('classes') if isinstance(selection_request, dict) else None
    return {'classes': classes} if classes else None


def _empty(value):
    """The same shape with nothing in it."""
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return 0
    if isinstance(value, str):
        return ''
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    return None


def _base_name(name):
    return str(name).replace(' (unchained)', '')


def hit_points(character):
    """Hit points for a blank sheet: the full hit die at the first character level and the PF1
    average (half the die, plus one) at each level after -- the fixed rule a table uses when it
    does not roll. Read from each class's own ``hit die``; Constitution is 10, so nothing is added."""
    total, first = 0, True
    for entry in character.classes:
        match = _HIT_DIE.search(str(character.class_data.get(entry['name'], {}).get('hit die', '')))
        die = int(match.group(1)) if match else 8
        levels = int(entry['level'])
        if first and levels:
            total += die
            levels -= 1
            first = False
        total += levels * (die // 2 + 1)
    return total


def _ability_increase_levels(level):
    """The character levels at which an ability score increase arrives, up to ``level`` -- read off
    the owner (level_and_bab.update_level_ability_score) by asking it level by level, so its
    cadence is not written down a second time."""
    probe, levels, held = SimpleNamespace(), [], 0
    for at in range(1, int(level) + 1):
        update_level_ability_score(probe, at)
        if probe.extra_ability_score_levels > held:
            levels.extend([at] * (probe.extra_ability_score_levels - held))
            held = probe.extra_ability_score_levels
    return levels


def slots(character):
    """One row per thing the character is owed and has not chosen.

    ``{'section', 'kind', 'label', 'class', 'level', 'bucket'}``: ``section`` is where the client
    files the placeholder (its dividers), ``kind`` what would fill it, ``label`` what to call it,
    ``class`` / ``level`` what grants it (``''`` / ``None`` when nothing in particular does), and
    ``bucket`` the class-choice bucket for a ``class_features`` row.
    """
    rows = []

    def add(section, kind, label, cls='', level=None, bucket=''):
        rows.append({'section': section, 'kind': kind, 'label': label,
                     'class': cls, 'level': level, 'bucket': bucket})

    house_flaws = misc_homebrew_enabled(character)
    # The feat economy, asked of its owner for THIS sheet: the pinned level, and the flaws a blank
    # sheet leaves room for (which is what sizes the flaw-feat grant).
    update_level(character, character.level, len(BLANK_FLAWS) if house_flaws else 0)
    general = character.normal_feat_amount
    human_flag_assigner(character)
    general += 1 if getattr(character, 'human_flag', False) else 0

    for level in normal_feat_slot_levels(character, general):
        add('feats', 'feat', f'Feat (Level {level})', level=level)
    for index in range(character.story_feat_amount):
        add('story_feats', 'feat', f'Story Feat {index + 1}')
    for index in range(character.flavor_feat_amount):
        add('flavor_feats', 'feat', 'Flavor Feat' if character.flavor_feat_amount == 1 else f'Flavor Feat {index + 1}')
    for index in range(character.flaw_feat_amount):
        add('flaw_feats', 'feat', f'Flaw Feat {index + 1}')

    for display, level in class_bonus_feat_slots(character):
        add('class_feats', 'feat', f'{display} Bonus Feat (Level {level})', cls=display, level=level)
    for entry in character.classes:
        name, display = entry['name'], entry['display']
        # The monk's bonus feats are outside class_bonus_feat_slots (the generator picks them from
        # the monk's own list), but they are owed all the same.
        # Their own section: the generator deals them into the general feat rows, so they are not
        # `class_feats` in the payload's sense, but on a blank sheet they belong with the bonus feats.
        if _base_name(name) == 'monk':
            for level in class_bonus_feat_levels('monk', entry['level']):
                add('monk_feats', 'feat', f'{display} Bonus Feat (Level {level})', cls=display, level=level)
        for level in bloodline_bonus_feat_levels(name, entry['level']):
            add('bloodline_feats', 'feat', f'{display} Bloodline Feat (Level {level})', cls=display, level=level)
    for display, level in teamwork_feat_slots(character):
        add('teamwork_feats', 'feat', f'{display} Teamwork Feat (Level {level})', cls=display, level=level)

    schedule = (getattr(character, 'class_choice_schedule', None) or {}).get('classes', {})
    for entry in character.classes:
        name, display = entry['name'], entry['display']
        row = schedule.get(name) or schedule.get(_base_name(name)) or {}
        for bucket in row.get('buckets') or {}:
            for level in levels_for(character, name, bucket, entry['level']):
                add('class_features', 'class_feature',
                    f'{str(bucket).replace("_", " ").title()} ({display} {level})',
                    cls=display, level=level, bucket=bucket)

    if house_flaws:
        for severity in BLANK_FLAWS:
            add('flaws', 'flaw', f'Flaw, {severity}')
    for index in range(BLANK_TRAITS):
        add('traits', 'trait', f'Trait {index + 1}')

    for level in _ability_increase_levels(character.level):
        add('abilities', 'ability_increase', f'Ability Score Increase (Level {level})', level=level)

    for book in getattr(character, 'spellbooks', None) or []:
        if book.get('name') in data.divine_casters:
            continue                    # a divine caster knows its whole list; nothing to choose
        for spell_level, count in enumerate(_blank_spellbook(character, book)['spells_known_list']):
            if isinstance(count, int) and not isinstance(count, bool) and count > 0 and spell_level < len(_ORDINALS):
                add('spells', 'spells_known',
                    f'{book.get("display", book.get("name", ""))} Spells Known, {_ORDINALS[spell_level]}: {count}',
                    cls=book.get('display', ''), level=spell_level)

    for entry in character.classes:
        per_level = class_skill_points(character, entry['name'])
        add('skills', 'skill_ranks',
            f'Skill Ranks: {entry["display"]} {per_level} per level x {entry["level"]} = '
            f'{per_level * entry["level"]} (plus Int modifier per level)',
            cls=entry['display'], level=entry['level'])
    return rows


def _blank_spellbook(character, book):
    """A spellbook with its class facts and none of its spells.

    The spells-known table is read again from the class's own progression, because the pipeline's
    copy has had rolled extras added to it for the classes that keep a spellbook
    (spells.spells_known_extra_roll); the highest spell level and the caster level come from
    ``spells.caster_formula``, which reads the class level and nothing else.
    """
    out = {key: (value if key in _SPELLBOOK_KEEP else _empty(value)) for key, value in book.items()}
    scratch = {key: book.get(key) for key in ('name', 'level', 'capped_level', 'casting_level_string')}
    caster_formula(character, scratch['level'], scratch)
    out['highest_spell_known'] = scratch.get('highest_spell_known', 0)
    out['casting_level_num'] = scratch.get('casting_level_num', book.get('level', 0))
    out['spells_known_list'] = list(spells_known_attr(character, 'base_classes', 'divine_casters', scratch) or [])
    return out


def apply(character):
    """Rewrite ``character.data_dict`` -- the finished payload -- as a blank sheet, in place and in
    the same key order. Call it last, after everything else has been written to the payload."""
    sheet = character.data_dict
    blanked = {key: (value if key in KEEP else _empty(value)) for key, value in sheet.items()}

    for ability in ABILITIES:
        blanked[ability] = BLANK_ABILITY
    for key in ('inherents', 'level_up_stats', 'racial_stats'):
        blanked[key] = {ability: 0 for ability in ABILITIES}
    blanked['classes'] = [{'name': entry['name'], 'display': entry['display'],
                           'level': entry['level'], 'archetype': {}} for entry in character.classes]
    blanked.update((key, value) for key, value in NEUTRAL.items() if key in blanked)
    blanked['spellbooks'] = [_blank_spellbook(character, book) for book in sheet.get('spellbooks') or []]
    # The first of a class's alternative main stats ("str/dex"): the pipeline picks one at random.
    row = character.class_data.get(character.c_class, {})
    blanked['main_stat'] = str(row.get('main_stat') or '').lower().split('/')[0]
    blanked['character_full_name'] = 'Blank ' + ' / '.join(
        f'{entry["display"]} {entry["level"]}' for entry in character.classes)
    for key in ('total_rolled_hp', 'Total_HP', 'sheet_health'):
        blanked[key] = hit_points(character)
    # The feat budget keeps its keys (the client reads them by name) with nothing owed through it:
    # what the character is owed is in `slots`.
    blanked['feat_budget'] = {key: 0 for key in (sheet.get('feat_budget') or {})}
    blanked['slots'] = slots(character)

    sheet.clear()
    sheet.update(blanked)
    return sheet
