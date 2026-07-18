from math import ceil, floor
import random

from utils import data

_BAB_MULT = {'H': 1.0, 'M': 0.75, 'L': 0.5}

# Presentation order for multiclass characters: strongest casters win level ties.
_CASTER_TIER_RANK = {'high': 0, 'mid': 1, 'low': 2}


def randomize_level(character, min_num, max_num, flaw_amount=0):
    if not isinstance(min_num, int) or min_num <= 0:
        min_num = 1
    if not isinstance(max_num, int) or max_num <= 0:
        max_num = 20
    pre_level = random.randint(min_num, max(min_num, max_num))
    level = min(pre_level, 40)

    # select_classes stored the class names; every class needs at least 1 level, so a total level
    # below the rolled class count truncates the picks (a level-2 character caps at 2 classes).
    picks = getattr(character, '_class_picks', None) or [character.c_class]
    picks = picks[:max(1, min(len(picks), level))]
    class_levels = _split_levels(level, len(picks))
    _build_classes(character, picks, class_levels)

    update_level(character, level, flaw_amount)


def _split_levels(total, count):
    """Split total levels across count classes: everyone starts at 1, each remaining level lands
    on a uniformly random class."""
    levels = [1] * count
    for _ in range(total - count):
        levels[random.randrange(count)] += 1
    return levels


def _build_classes(character, picks, class_levels):
    character.classes = []
    for i, (name, lvl) in enumerate(zip(picks, class_levels)):
        character.classes.append({
            'name': name,
            # Display name for the FoundryVTT class item; .title() matches every_class.json,
            # e.g. "barbarian (unchained)" -> "Barbarian (Unchained)".
            'display': name.title(),
            'level': lvl,
            'bab_type': character.class_data[name]['bab'],
            'casting_level_string': str(character.class_data[name]['casting level']).lower(),
            'roll_order': i,
            # capped levels exist for things like spells (progressions stop at 20)
            'capped_level': min(lvl, 20),
        })

    # Presentation order everywhere (payload classes/spellbooks, sheet summary, spellbook
    # slots): level desc, level ties broken by caster tier (high > mid > low), then roll order.
    character.classes.sort(key=lambda c: (
        -c['level'],
        _CASTER_TIER_RANK.get(c['casting_level_string'], 3),
        c['roll_order']))

    # primary class = most levels; ties keep the first-ROLLED class (legacy scalar semantics,
    # independent of the tier-ranked list order above)
    character.primary_class_index = min(
        range(len(character.classes)),
        key=lambda i: (-character.classes[i]['level'], character.classes[i]['roll_order']))

    _sync_legacy_class_aliases(character)


def _sync_legacy_class_aliases(character):
    """Point the legacy scalar fields at the class list: c_class* at the primary entry, c_class_2*
    at the highest-leveled secondary (Foundry-compat plumbing only — backend subsystems should
    loop character.classes, which also covers classes 3 and 4)."""
    primary = character.classes[character.primary_class_index]
    character.c_class = primary['name']
    character.c_class_display = primary['display']
    character.c_class_level = primary['level']
    character.capped_level_1 = primary['capped_level']

    secondaries = sorted(
        (c for c in character.classes if c is not primary),
        key=lambda c: (-c['level'], c['roll_order']))
    if secondaries:
        character.c_class_2 = secondaries[0]['name']
        character.c_class_2_level = secondaries[0]['level']
        character.capped_level_2 = secondaries[0]['capped_level']
    else:
        character.c_class_2 = ''
        character.c_class_2_level = 0
        character.capped_level_2 = 0


#should this be update feats, since we're updating feat amount [it 100% depends on level]
def update_level(character, level, flaw_amount=None):
    character.level = level

    character.flaw_feat_amount = 0
    character.story_feat_amount = 0
    character.flavor_feat_amount = 0
    character.normal_feat_amount = ( ceil(character.level/2) )
    if flaw_amount != 0:
        character.normal_feat_amount = ceil(character.level/2)
        character.flaw_feat_amount = min(max(floor(flaw_amount/2 + 1),1), 3) #So it's always 1<feats<3
    if character.homebrew_feat_amount not in ('N', 'n'):
        character.normal_feat_amount = ceil(character.level/2)
        character.story_feat_amount = 1 + floor(character.level/5)
        character.flaw_feat_amount = min(max(floor(flaw_amount/2 + 1),1), 3) #So it's always 1<feats<3
        character.flavor_feat_amount = 1

    character.feat_amounts = character.normal_feat_amount + character.flaw_feat_amount + character.story_feat_amount + character.flavor_feat_amount


    _update_bab_total(character)
    _update_saves(character)


def update_level_ability_score(character, level):
    character.level=level
    character.extra_ability_score_levels=floor(level/4)



def _update_bab_total(character):
    """PF1 multiclass BAB: each class's progression applies to its own levels, floored per class,
    then summed (H x1, M x0.75, L x0.5). character.bab stays the primary class's tier letter."""
    if getattr(character, 'classes', None):
        character.bab = character.classes[character.primary_class_index]['bab_type']
        character.bab_total = sum(
            floor(c['level'] * _BAB_MULT.get(c['bab_type'], 1.0)) for c in character.classes)
    else:
        # legacy fallback for callers that set a level before select_classes/randomize_level ran
        character.bab = character.class_data[character.c_class]['bab']
        character.bab_total = floor(character.level * _BAB_MULT.get(character.bab, 1.0))


def _update_saves(character):
    """PF1 multiclass base saves: per class, a good save contributes 2 + level//2 and a poor save
    level//3, summed across classes (no ability mods — the sheet adds those)."""
    entries = (getattr(character, 'classes', None)
               or [{'name': character.c_class, 'level': character.level}])
    save_bases = {'fort': 0, 'ref': 0, 'will': 0}
    for entry in entries:
        goods = data.good_saves.get(entry['name'], [])
        for save in save_bases:
            save_bases[save] += (2 + entry['level'] // 2) if save in goods else entry['level'] // 3
    character.save_bases = save_bases
