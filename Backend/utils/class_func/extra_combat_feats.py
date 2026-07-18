from math import floor
def extra_combat_feats(character):
    #currently we're just adding combat feats to total feats,
    # but we may want to have them be their own separate entity
    character.combat_feats_list=0
    # Count = one slot per (class, granting level) across every rolled class, so the count and
    # the "(Class level)" labels can never drift apart (they share class_bonus_feat_slots).
    character.class_feats_amount = len(class_bonus_feat_slots(character))
    return character.class_feats_amount


def class_bonus_feat_levels(c_class, level):
    """Ordered list of class levels at which a class grants a bonus (class) feat.
    Its length matches the count from extra_combat_feats(); used to label class
    feats as "(Class) (level)", e.g. Fighter -> [1, 2, 4, 6, ...]."""
    arrays = {
        'monk':           [1, 2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42],
        'unchained_monk': [1, 2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42],
        'magus':          [5, 11, 17, 23, 29, 35, 41],
        'brawler':        [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41],
        'warlord':        [1, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42],
    }
    if c_class == 'fighter':
        return [1] + list(range(2, level + 1, 2))            # 1, 2, 4, 6, ...
    if c_class == 'wizard':
        return list(range(5, level + 1, 5))                  # 5, 10, 15, 20
    if c_class == 'warpriest':
        return list(range(3, level + 1, 3))
    if c_class in ('gunslinger', 'swashbuckler'):
        return list(range(4, level + 1, 4))
    if c_class in ('cavalier', 'samurai'):
        return list(range(6, level + 1, 6))
    if c_class == 'warder':
        return list(range(3, level + 1, 5)) if level >= 3 else []
    if c_class == 'mystic':
        return list(range(2, level + 1, 5)) if level >= 2 else []
    if c_class in arrays:
        return [lvl for lvl in arrays[c_class] if lvl <= level]
    return []


def class_bonus_feat_slots(character):
    """Ordered (display, granting level) pair per class bonus feat, across EVERY rolled class in
    character.classes order — the single source for both the class-feat count
    (extra_combat_feats) and the "(Fighter 1)" / "(Gunslinger 4)" labels, so a multiclass roll
    labels each slot with the class that actually grants it. Monk is skipped: monk bonus feats
    are granted by monk_feats_chooser (unfilled slots reallocate to normal feats in main_test),
    so they never occupy a class-feat slot."""
    slots = []
    for entry in getattr(character, 'classes', []):
        name = entry['name'].replace(' (unchained)', '')
        if name == 'monk':
            continue
        for lvl in class_bonus_feat_levels(name, entry['level']):
            slots.append((entry['display'], lvl))
    return slots


def teamwork_feat_levels(c_class, level):
    """Ordered list of class levels at which a class grants a teamwork feat
    (mirrors extra_teamwork_feats()); used to label teamwork feats."""
    if c_class in ('hunter', 'inquisitor'):
        return list(range(3, level + 1, 3))      # floor(level / 3)
    if c_class in ('cavalier', 'samurai'):
        return [1]
    return []


def teamwork_feat_slots(character):
    """Ordered (display, granting level) pair per teamwork feat across EVERY rolled class —
    single source for both the count (extra_teamwork_feats) and the "(Inquisitor 3)" labels,
    same pattern as class_bonus_feat_slots."""
    slots = []
    for entry in getattr(character, 'classes', []):
        name = entry['name'].replace(' (unchained)', '')
        for lvl in teamwork_feat_levels(name, entry['level']):
            slots.append((entry['display'], lvl))
    return slots


def bloodline_bonus_feat_levels(c_class, level):
    """Ordered list of class levels at which a bloodline grants a bonus feat.
    Sorcerer: 7, 13, 19, 25, ...  ·  Bloodrager: 6, 9, 12, ...  Both are range-based
    so they extend past 20 for high-level NPCs; used to size + label bloodline feats."""
    if c_class == 'sorcerer':
        return list(range(7, level + 1, 6))      # 7, 13, 19, 25, 31, 37, ...
    if c_class == 'bloodrager':
        return list(range(6, level + 1, 3))      # 6, 9, 12, 15, ..., (>20)
    return []


def extra_teamwork_feats(character):
    # Count = one slot per (class, granting level), shared with the labels (teamwork_feat_slots).
    character.teamwork_feats = len(teamwork_feat_slots(character))

# Just have wizards get extra feats -> gives them metamagic
# def extra_spell_feats(character):
#     character.spell_feats = 0
#     if character.c_class in ['wizard']:
#         character.spell_feats = floor(character.c_class_level / 5)