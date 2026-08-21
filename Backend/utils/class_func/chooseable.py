import random
#Want to make this a generic function that works for any class ability selection with complex prerequisites
def chooseable_list(character):
    character.chooseable = set()
    #figure out how to add feats + anything else that could function as a pre-req

    return character.chooseable

def chooseable_list_stats(character,attr,stat_name,base,th = None):
    while base <= int(attr):
        suffix = "th" if base >= 4 else {1: "st", 2: "nd", 3: "rd"}.get(base, "th")
        stat = str(stat_name) + str(base) + (suffix if th else "")
        character.chooseable.add(stat)
        base += 1
        if base == 25:
            break


def chooseable_list_class(character,i,class_1,attr,base,th = None):

    while base <= int(attr):
        even = f"{class_1} {2 * (i + 1)}"
        odd = f"{class_1} {2 * i + 1}"

        suffix = "th" if base >= 4 else {1: "st", 2: "nd", 3: "rd"}.get(base, "th")
        class_level_name = str(base) + (suffix if th else "") + " " + str(class_1) + " level" 
        class_level_name_2 = str(class_1) + " level " + str(base) + (suffix if th else "") 
        char_level_name = str(base) + (suffix if th else "") + " " + "character level" 
        char_level_name_2 = "character level " + str(base) + (suffix if th else "")  
        base += 1

        character.chooseable.update([even, odd, class_level_name, class_level_name_2, char_level_name, char_level_name_2])
        if base == 25:
            break            

def chooseable_list_race(character):
    character.chooseable.add(character.chosen_race)


# Archetype names that are ALSO the name of a selectable option somewhere in class_data/. Seeding
# these would satisfy a prerequisite that meant the OPTION -- 'brawler, greater' requires the
# `brawler` RAGE POWER, and 'spell sunder' requires the `witch hunter` rage power, neither of which
# has anything to do with the same-named archetype. There is no way to tell the two apart from a
# prereq string, so a colliding name is never seeded and the archetype-gated options behind it stay
# unreachable -- the safe direction.
#
# This is a checked baseline, not the authority: gates/validate_class_choices.py recomputes the
# intersection from archetypes.json and every pool, and FAILS if it stops matching this set. Kept as
# a constant rather than computed here because computing it means reading ~73 pool files, and this
# runs inside every generation. Measured 2026-08-07: 18 collisions out of 1,267 archetype names.
# None of the seven hunter archetypes collide, which is why the 144 hunter aspects this exists for
# are unaffected.
ARCHETYPE_PREREQ_COLLISIONS = frozenset({
    'brawler', 'chameleon', 'dreadnought', 'drill sergeant', 'exemplar', 'marauder',
    'master of disguise', 'mastermind', 'opportunist', 'saboteur', 'scavenger', 'scout',
    'shadow walker', 'snare setter', 'spellbreaker', 'survivalist', 'trapsmith', 'witch hunter',
})


def chooseable_list_archetypes(character, archetypes_per_class):
    """Seed the rolled archetype names, so archetype-gated options can satisfy their prerequisites.

    144 of the hunter's 155 aspects are gated on an archetype, and the gate is written as a bare
    archetype name in the option's `prerequisites` ("Verminous Hunter"). The prerequisite engine
    already knows how to check that -- it just never had the archetype to check against. So this is
    a seeding change rather than a new filter: `no_prereq_loop` then admits an archetype's options
    to exactly the characters who rolled that archetype, and refuses them to everyone else.

    NOTE this does NOT model archetype feature SWAPS. An archetype that trades a bucket away still
    leaves the bucket in place -- that ruling (bond-only) is unchanged, and is a different thing
    from honouring an archetype prerequisite.

    Takes `archetypes_per_class` as an argument rather than reading it off the character: this must
    run before the choosers, and at that point the attribute has not been assigned yet.
    """
    for info in archetypes_per_class or []:
        for name in (info or {}):
            name = name.lower().strip()
            if name and name not in ARCHETYPE_PREREQ_COLLISIONS:
                character.chooseable.add(name)

def chooseable_list_class_features(character):
    remove_list = ["aphorite", "aquatic elf", "boggard", "dhampir", "drow", "duergar", "duskwalker", "dwarf", "elf", "fetchling", "gillman", "gnome", "Half-Elf", "halfling", "Half-Orc", "human", "kitsune", "nagaji", "oread", "ratfolk", "strix", "tengu", "wayang", "aasimar", "aquatic elf", "catfolk", "dwarf", "elf", "gathlain", "gnome", "goblin", "Half-Elf", "halfling", "Half-Orc", "hobgoblin", "human", "kitsune", "kobold", "locathah", "nagaji", "orc", "vanara", "source", "role", "alignment", "hit die", "parent class(es)", "starting wealth", "skill points at each level" ]
    # every class contributes its feature keys to the prereq pool (multiclass-aware)
    for entry in character.classes:
        class_keys_list = list(character.class_data.get(entry['name'], "").keys())
        class_keys_list = [key.strip() for key in class_keys_list if key not in remove_list]
        class_keys_list_class_feature = [key + " class feature" for key in class_keys_list]

        character.chooseable.update(class_keys_list)
        character.chooseable.update(class_keys_list_class_feature)