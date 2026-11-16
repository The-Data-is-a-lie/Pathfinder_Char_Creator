"""Blank mode: the sheet behind the Blank Character Generator.

A blank character is a class (or several) at a level, a race, and NOTHING CHOSEN: every ability at
10, no feats, no spells, no gear -- and in their place a list of ``slots``, one row per thing the
character is owed (a feat, a fighter bonus feat at 4th level, a rogue talent at 2nd, a trait, a
minor flaw). The client draws one placeholder per row and the player drags the real thing onto the
sheet.

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

``scripts/tests/test_blank.py`` holds this to its promise: the same request under two seeds must
produce the same sheet, so anything random that leaks through ``KEEP`` or a rebuild fails there
rather than on a player's screen.

THE COUNTS ARE NOT RESTATED. Each slot count is read from its owner: the feat economy from
``level_and_bab.update_level``, class bonus and teamwork feats from ``extra_combat_feats``, class
choices from ``class_choice_schedule.json`` through ``generic_func.levels_for``, traits from
``traits.TRAIT_COUNT``, trainers from ``trainers.max_trainer_slots``. House-rule slots (story,
flavor and flaw feats, the two creation feats, the flaws themselves, trainers) appear exactly when
those owners grant them.

WHAT IS DELIBERATELY NOT A SLOT (ruled 2026-11-16, after the first sheets were looked at): ability
score increases, spells known and skill ranks. The sheet already carries the item a generated
character records its ability increases on (the ``level_up_stats`` buff, here with every value 0),
and the other two are the sheet's own Spells and Skills tabs -- a placeholder for them was clutter.

THE NAMES ARE THE CLIENT'S. A row's ``label`` is the bare tag text ("Fighter 4", "Trainer 1",
"Flaw, Minor"); the FoundryVTT module wraps it as "(Fighter 4)" and numbers the general, story,
flavor and flaw feats itself, with the same numbering it gives a generated character's feats, so
a blank sheet and a generated one read alike.
"""
import re
from math import ceil

from .extra_combat_feats import (bloodline_bonus_feat_levels, class_bonus_feat_levels,
                                 class_bonus_feat_slots, teamwork_feat_slots)
from .feat_level_assignment import normal_feat_slot_levels
from .flag_assign import human_flag_assigner
from .generic_func import levels_for
from .level_and_bab import update_level
from .skill_ranks import misc_homebrew_enabled
from .spells import caster_formula, spells_known_attr
from .trainers import max_trainer_slots
from .traits import TRAIT_COUNT

ABILITIES = ('str', 'dex', 'con', 'int', 'wis', 'cha')
# Every ability on a blank sheet. PF1's average score: no modifier either way.
BLANK_ABILITY = 10
# The flaws a blank sheet leaves room for, in the order the house rule deals them (the first flaw
# is minor, the second major -- flaws.pick_flaws).
BLANK_FLAWS = ('Minor', 'Major')
# As many trait slots as the generator gives a character traits (ruled 2026-11-16; it was PF1's
# two until the first blank sheets were compared with generated ones).
BLANK_TRAITS = TRAIT_COUNT
# The share of a character's possible trainers a blank sheet leaves room for (ruled 2026-11-16).
# A generated character rolls anywhere from none to the maximum, each teaching one to four feats;
# half the maximum, one slot each, is a sheet with room for trainers that is not mostly rows to
# delete.
BLANK_TRAINER_SHARE = 0.5

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


def trainer_slots(character):
    """How many trainers a blank sheet leaves room for: ``BLANK_TRAINER_SHARE`` of the most this
    character could have studied under, rounded up so a 1st-level character still has one."""
    return ceil(max_trainer_slots(character) * BLANK_TRAINER_SHARE)


def slots(character, trainers_enabled=False):
    """One row per thing the character is owed and has not chosen.

    ``{'section', 'kind', 'label', 'class', 'level', 'bucket'}``: ``section`` is where the client
    files the placeholder (its dividers), ``kind`` what would fill it, ``label`` the bare tag text
    the client wraps in parentheses, ``class`` / ``level`` what grants it (``''`` / ``None`` when
    nothing in particular does), and ``bucket`` the class-choice bucket for a ``class_features``
    row.

    The general, story, flavor and flaw feat rows carry only their tag word as a label: the
    client numbers those rows itself, the way it numbers a generated character's. Their ``level``
    is still the level each general feat is really gained at, for a client that wants it.
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
        add('feats', 'feat', 'Feat', level=level)
    for _index in range(character.story_feat_amount):
        add('story_feats', 'feat', 'Story Feat')
    for _index in range(character.flavor_feat_amount):
        add('flavor_feats', 'feat', 'Flavor')
    for _index in range(character.flaw_feat_amount):
        add('flaw_feats', 'feat', 'Flaw')

    # "<Class> <level>": the shape the payload's own class_feat_labels have.
    for display, level in class_bonus_feat_slots(character):
        add('class_feats', 'feat', f'{display} {level}', cls=display, level=level)
    for entry in character.classes:
        name, display = entry['name'], entry['display']
        # The monk's bonus feats are outside class_bonus_feat_slots (the generator picks them from
        # the monk's own list and deals them into the general feat rows), so they are not
        # `class_feats` in the payload's sense -- but they are owed, and on a blank sheet they
        # belong with the bonus feats. Hence their own section.
        if _base_name(name) == 'monk':
            for level in class_bonus_feat_levels('monk', entry['level']):
                add('monk_feats', 'feat', f'{display} {level}', cls=display, level=level)
        for level in bloodline_bonus_feat_levels(name, entry['level']):
            add('bloodline_feats', 'feat', f'{display} {level}', cls=display, level=level)
    for display, level in teamwork_feat_slots(character):
        add('teamwork_feats', 'feat', f'{display} {level}', cls=display, level=level)

    if trainers_enabled:
        for number in range(1, trainer_slots(character) + 1):
            add('trainer_feats', 'feat', f'Trainer {number}', level=number)

    schedule = (getattr(character, 'class_choice_schedule', None) or {}).get('classes', {})
    for entry in character.classes:
        name, display = entry['name'], entry['display']
        row = schedule.get(name) or schedule.get(_base_name(name)) or {}
        for bucket in row.get('buckets') or {}:
            for level in levels_for(character, name, bucket, entry['level']):
                add('class_features', 'class_feature',
                    f'{str(bucket).replace("_", " ").title()} {level}',
                    cls=display, level=level, bucket=bucket)

    if house_flaws:
        for severity in BLANK_FLAWS:
            add('flaws', 'flaw', f'Flaw, {severity}')
    for index in range(BLANK_TRAITS):
        add('traits', 'trait', f'Trait {index + 1}')
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


def apply(character, trainers_enabled=False):
    """Rewrite ``character.data_dict`` -- the finished payload -- as a blank sheet, in place and in
    the same key order. Call it last, after everything else has been written to the payload.

    ``trainers_enabled`` is the request's own trainers switch (generate_random_char resolves it):
    a blank sheet leaves room for trainers exactly when a generated one could have them.
    """
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
    blanked['slots'] = slots(character, trainers_enabled)

    sheet.clear()
    sheet.update(blanked)
    return sheet
