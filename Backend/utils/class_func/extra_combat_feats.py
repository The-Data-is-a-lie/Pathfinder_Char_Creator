from math import floor
def extra_combat_feats(character):
    # cavalier_feats = [6,12,18,24,30,36,42]
    monk_feats = [1,2,6,10,14,18,22,26,30,34,38,42]
    brawler_feats = [2,5,8,11,14,17,20,23,26,29,32,35,38,41] 
    warlord_feats = [1,6,10,14,18,22,26,30,34,38,42]     
    magus_feats = [5,11,17,23,29,35,41]
    #setting up extra feats + extra feats_2 as 0 so we don't get errors
    extra_feats = 0
    character.combat_feats_list=0
    i = 0
    #fighter section
    if character.c_class == 'fighter':
        extra_feats +=  1 + floor((character.c_class_level)/2)

    #warpriest section
    if character.c_class == 'warpriest':
        extra_feats += floor((character.c_class_level)/3)        
    #gunslinger/swashbuckler section
    if character.c_class in ['gunslinger', 'swashbuckler']:
        extra_feats += floor((character.c_class_level)/4)    
    #cavalier/samurai section
    if character.c_class in ['cavalier', 'samurai']:
        extra_feats += floor((character.c_class_level)/6)
    #monk section
    # Monk bonus feats are granted by monk_feats_chooser (the real monk bonus-feat list), and any
    # slots it can't fill are reallocated to normal feats in main_test. They must NOT also be
    # counted here, which previously double-granted monks their bonus-feat allotment.
    #magus section
    if character.c_class == 'magus':
        while i < len(magus_feats) and magus_feats[i] <= character.c_class_level:
            i += 1
        extra_feats += i
    # brawler section
    if character.c_class == 'brawler':
        while i < len(brawler_feats) and brawler_feats[i] <= character.c_class_level:
            i += 1
        extra_feats += i
    # wizard section
    if character.c_class == 'wizard':
        i = floor(character.c_class_level / 5)
        extra_feats += i


    # path of war section
    #Warder section
    if character.c_class == 'warder':
        if character.c_class_level < 3:
            extra_feats = 0
            return extra_feats
        else:
            extra_feats = floor((character.c_class_level - 3) / 5) + 1
            return 
    #mystic section
    if character.c_class == 'mystic':
        if character.c_class_level < 2:
            extra_feats = 0
            return extra_feats
        else:
            extra_feats = floor((character.c_class_level - 2) / 5) + 1
            return         
    #warlord section
    if character.c_class == 'warlord' or character.c_class == 'warlord':
        while i < len(warlord_feats) and warlord_feats[i] <= character.c_class_level:
            i += 1
        extra_feats += i


    #currently we're just adding combat feats to total feats, 
    # but we may want to have them be their own separate entity
    character.class_feats_amount = extra_feats 
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


def teamwork_feat_levels(c_class, level):
    """Ordered list of class levels at which a class grants a teamwork feat
    (mirrors extra_teamwork_feats()); used to label teamwork feats."""
    if c_class in ('hunter', 'inquisitor'):
        return list(range(3, level + 1, 3))      # floor(level / 3)
    if c_class in ('cavalier', 'samurai'):
        return [1]
    return []


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
    character.teamwork_feats = 0
    if character.c_class in ['hunter', 'inquisitor']:
        character.teamwork_feats = floor(character.c_class_level / 3)
    
    if character.c_class in ['cavalier', 'samurai']:
        character.teamwork_feats = 1

# Just have wizards get extra feats -> gives them metamagic
# def extra_spell_feats(character):
#     character.spell_feats = 0
#     if character.c_class in ['wizard']:
#         character.spell_feats = floor(character.c_class_level / 5)