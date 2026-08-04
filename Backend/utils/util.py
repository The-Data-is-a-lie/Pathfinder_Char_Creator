from random import randrange
from math import floor
#importing stats in case we want to work on them
import random
from utils import data
from utils.data import traits, mannerisms, regions, REGION_ALIASES, weapon_groups, weapon_groups_region, disciplines, skills,  languages, hair_colors, hair_types, appearance, eye_colors, path_of_war_class#evil_deities, good_deities, neutral_deities,
import json
import sys
from utils.class_func.race_func import *


character_data = {}

def roll_dice(num_dice, num_sides):
    if not (isinstance(num_dice, int)):
        num_dice = 4
    if not isinstance(num_sides, int):
        num_sides = 6
    rolls = []
    for _ in range(num_dice):
        rolls.append(random.randint(1, num_sides))
    total = sum(rolls)   
    return total

def roll_inherent(sides,size):
    return random.randint(sides,size)

def slug(value):
    """Alphanumerics only, lowercased -- the match key for client-supplied names.

    Clients spell things their own way ('monkey-goblin', 'Dust Cairn', 'TAL-FALKO') while the data
    files carry one exact key each. Comparing slugs resolves every spelling that differs only in
    casing, spacing or punctuation, which is the whole of the drift for races and all but one region.
    """
    return ''.join(ch for ch in str(value).lower() if ch.isalnum())


# Sentinels every client sends for "surprise me". None of them is a failed lookup, so none of them
# warns: `sheet.js` and the Foundry dialog both offer a literal 'Random' option, and a blank form
# field arrives as ''.
_RANDOM_SENTINELS = {'', 'random', '0', 'none'}


def region_chooser(character, userInput_region):
    """Resolve a requested region to its CANONICAL key, or roll one.

    The key in `first_names_regions.json` is canonical (`data.regions`) and is what gets stored and
    emitted -- never a `.title()`d form. That is not cosmetic: `.title()` turns 'Tal-falko' into
    'Tal-Falko' and 'Kaeru no Tochi' into 'Kaeru No Tochi', neither of which is a key in either name
    file, so `name_chooser` fell through to its "should never occur" branch and drew BOTH names from
    a randomly chosen other region -- about a fifth of all NPCs.

    Two more things this function used to get wrong, both verified by `validate_name_data.py` now:

    * IT DELETED A REGION. `regions.remove(region)` ran after the `for region in ...` loop, so it
      removed whatever the last key was (Ieso). Zero of 2,000 random draws produced it and asking for
      it explicitly returned something else -- while `campaign_lore.json` carried Ieso lore no
      character could reach. The line it replaced (`randint(1, len(regions)-1)`, see git log -L) had
      the mirror-image bug at index 0, so this is the second off-by-one in the same spot: prefer the
      dict over an index.
    * UNKNOWN INPUT WAS SILENT. A region the resolver could not match looked exactly like one it
      could, which is how 'Grundykin Damplands' and 'Dust Cairn' -- what the Foundry dialog and
      sheet.js actually send -- went years without working.
    """
    regions = list(character.first_names_regions.keys())
    canonical = {slug(name): name for name in regions}

    chosen = None
    if isinstance(userInput_region, str) and slug(userInput_region) not in _RANDOM_SENTINELS:
        key = slug(userInput_region)
        chosen = canonical.get(key) or canonical.get(slug(REGION_ALIASES.get(key, '')))
        if chosen is None:
            print(f"region_chooser: unknown region {userInput_region!r}; rolling randomly "
                  f"(known: {', '.join(regions)})")

    character.region = chosen or random.choice(regions)
    return character.region

def race_chooser(character, userInput_race):
    """
    Characters either choose a race, or randomly select one
    Return
    - userInput_race
    """
    race_data = full_race_data(character)
    # Match on an alphanumeric-only key so any client spelling resolves to the data files'
    # exact key: the web sheet / Foundry module send slugs ('monkey-goblin', 'half-elf'),
    # and the data keys mix casing ('Monkey goblin', 'Half-Elf'). Unknown input (incl.
    # 'Random') falls through to a random race. `slug` is shared with region_chooser.
    canonical = {slug(r): r for r in race_data}
    chosen = canonical.get(slug(userInput_race)) if isinstance(userInput_race, str) else None
    character.chosen_race = chosen or random.choice(list(race_data.keys()))
    return character.chosen_race
        
def gender_chooser(character, userInput_gender):
    """
    Characters either choose a gender, or randomly select one
    Return
    - userInput_gender
    """
    genders = ("Male", "Female")
    if isinstance(userInput_gender, str):
        userInput_gender = userInput_gender.capitalize()
    if userInput_gender not in genders:
        userInput_gender = random.choice(genders).capitalize()
    character.chosen_gender = userInput_gender
    return character.chosen_gender

def first_name_for(character, region, sex, exclude=None):
    """One first name for (region, sex), or None if that pool does not exist.

    The pure half of `name_chooser`: same `first_names_regions` lookup, same "Tal-Falko" / "Nameless"
    fallbacks, but it does NOT touch the character. Bonded creatures name themselves through here
    (`class_func/animal_companions.py`, #37) so the region -> gender -> names lookup keeps one owner.

    `exclude` drops a name from the pool -- a companion draws from the same list its master drew
    from, and "Tal-Falko and his wolf Tal-Falko" is otherwise a live outcome. It is a preference,
    not a guarantee: a one-name pool still returns that name rather than nothing.
    """
    pools = getattr(character, 'first_names_regions', None) or {}
    if region not in pools:
        # Defence in depth. `region_chooser` now stores the canonical key, so every in-generator
        # caller passes one; this fold only matters for a caller that builds a character itself
        # (`validate_companion_identity.py`) or for data that gains a region the resolver has not
        # seen. It was load-bearing when `character.region` was title-cased.
        folded = {str(key).casefold(): key for key in pools}
        region = folded.get(str(region).casefold(), region)
    by_sex = pools.get(region, "Tal-Falko")
    # The historical default is a STRING, not a dict, so a missing region cannot be `.get`-chained.
    # `name_chooser` never reaches it (both of its branches pick a region that exists); a new caller
    # can, and gets None instead of an AttributeError.
    if not isinstance(by_sex, dict):
        return None
    names = by_sex.get(sex, "Nameless")
    if not isinstance(names, (list, tuple)) or not names:
        return None
    if exclude is not None:
        names = [name for name in names if name != exclude] or names
    return random.choice(names)


def name_chooser(character):
    """
    Randomly generates names by region
    Return
    - f_name, l_name, full_name
    """
    f_name_list = list(character.first_names_regions)
    l_name_list = list(character.last_names_regions)


    if character.region in f_name_list:
        l_names = character.last_names_regions[character.region]
        character.f_name = first_name_for(character, character.region, character.chosen_gender)
        character.l_name = random.choice(l_names)
        character.full_name = character.f_name + character.l_name

    else:
        # wehave this section in case of an emergency and region isn't selected. But this should never occur
        region_list = (list(f_name_list))
        region = random.choice(region_list)
        l_names = character.last_names_regions[region]
        character.f_name = first_name_for(character, region, character.chosen_gender)
        character.l_name = random.choice(l_names)
        character.full_name = character.f_name + character.l_name

    return character.f_name, character.l_name

    
def _available_class_pool(character):
    """The base random-class pool: every class_data key minus the occult classes (not ready yet)
    and the Path of War classes missing from the pf1-pow Foundry compendium (they'd generate fine
    here, but the Foundry sheet can't resolve a class item the module doesn't ship — re-enable by
    emptying pow_classes_pending_foundry in data.py once the module includes them).

    psionic_classes_pending is the same lever for the twelve psionic classes and starts empty —
    they are in the pool by default (ticket 04: psionics is additive like Path of War, not a
    casting replacement like Spheres, so there is no API flag). Anything parked there must be
    recorded in docs/feature_spec_todo.md section 9 with the subsystem it waits on."""
    occult_classes = [x.lower() for x in getattr(data, 'occult_classes')]
    pending = [x.lower() for x in getattr(data, 'pow_classes_pending_foundry', [])]
    pending += [x.lower() for x in getattr(data, 'psionic_classes_pending', [])]
    return [x for x in character.class_data.keys()
            if x not in occult_classes and x not in pending]


def chooseClass(character, class_choice, chosen_BAB, chosen_caster_level=None):
    """
    Select a class or
    Gives the Character a random class based off of BAB selection
    Returns
    - c_class (String)
    """
    occult_classes = [x.lower() for x in getattr(data, 'occult_classes')]
    available_classes = _available_class_pool(character)

    if isinstance(class_choice, str):
        # Lower-case for case-insensitivity, and turn the frontend's slug form (spaces -> hyphens,
        # e.g. "barbarian-(unchained)") back into the space-separated keys used in class_data
        # ("barbarian (unchained)"). No class name contains a hyphen, so this is safe. Without this
        # the four space-named classes (the Unchained variants) never matched and fell back to a
        # random class.
        class_choice = class_choice.lower().replace('-', ' ')

    if not class_choice in available_classes:
        available_classes_manip = ensure_BAB_and_caster_level(character, available_classes, "bab", chosen_BAB)
        available_classes_manip = ensure_BAB_and_caster_level(character, available_classes_manip, "casting level", chosen_caster_level)
        try:
            class_choice = random.choice(available_classes_manip)
        except:
            print("No classes available for the given BAB and caster level. Defaulting to a random class.")
            class_choice = random.choice(available_classes)

    # if no class is specified, allow for people to specify BAB and caster level

    # looping to ensure we don't have a class we don't want included
    while class_choice in occult_classes and class_choice not in available_classes:
        class_choice = random.choice(available_classes)

    # userInput_class = input(f'please type a class name to select a class, or type 0 for a random class: ').lower()
    userInput_class = class_choice.lower()
    character.c_class = userInput_class
    character.c_class_2 = ''

    all_classes = list(character.class_data.keys()) # + list(character.class_data["Path of War"].keys())

    if userInput_class not in all_classes:
        bab = random.choice(('H','M','L'))
        # bab = input('Enter bab (H/M/L): ').capitalize()
        character.bab = bab
        userInput_class = None

        if bab not in ('H','M','L'):
            bab = 'H'
            character.bab = 'H'

        classes = []
        for class_name in all_classes:
                if bab == "H" and character.class_data[class_name]["bab"] == "H":
                    classes.append(class_name)
                elif bab == "M" and character.class_data[class_name]["bab"] == "M":
                    classes.append(class_name)
                elif bab == "L" and character.class_data[class_name]["bab"] == "L":
                    classes.append(class_name)
    
        classes = list(all_classes)
        character.c_class = classes[randrange(0,len(classes))]
    # Display name for the FoundryVTT class item, captured BEFORE archetype_data() later strips
    # " (unchained)" for data lookups. .title() matches every_class.json exactly, e.g.
    # "barbarian (unchained)" -> "Barbarian (Unchained)", "fighter" -> "Fighter".
    character.c_class_display = character.c_class.title()
    return character.c_class


def ensure_BAB_and_caster_level(character, available_classes, BAB_or_caster_level, pre_chosen_bab = ['H', 'M', 'L']):
    chooseable_classes_bab = []
    if not isinstance(pre_chosen_bab, list):
        chosen_bab = [pre_chosen_bab.upper()]

    # print("chosen_bab", chosen_bab)
    if not isinstance(pre_chosen_bab, list) and BAB_or_caster_level not in ('bab'):
        pre_chosen_bab = ['none', 'low', 'mid', 'high']

    # print("pre_chosen_bab", pre_chosen_bab)

    for c in available_classes:
        # print("c.lower()", c.lower())
        if not character.class_data[c.lower()][str(BAB_or_caster_level)].upper() in chosen_bab:
            continue
        chooseable_classes_bab.append(c.lower())

    return chooseable_classes_bab

def _prune_class_pool(pool, picked):
    """Remove a picked class from the pool, plus its whole restricted group when the pick belongs
    to one (max 1 Path of War initiator class and max 1 Spheres class per character)."""
    pool = [c for c in pool if c != picked]
    for group in (data.path_of_war_class, getattr(data, 'spheres_classes', [])):
        if picked in group:
            pool = [c for c in pool if c not in group]
    return pool


def _is_caster(character, c):
    """True when class `c` has a real spellcasting progression (casting level != 'none'). Used to cap
    a multiclass at 3 caster classes: pf1 has only 3 spellbook slots (primary/secondary/tertiary), so a
    4th caster's spellbook would be dropped on the Foundry sheet — losing its spells AND its sphere
    caster-level contribution."""
    return str(character.class_data[c].get('casting level', 'none')).lower() != 'none'


def select_classes(character, class_choice, chosen_BAB, chosen_caster_level=None, multi_class='N'):
    """
    Pick the character's class NAMES. Slot 0 honors class_choice / chosen_BAB /
    chosen_caster_level exactly like the single-class path; when multiclassing, the class count is
    rolled with weights 2->50% / 3->35% / 4->15% and the extra slots draw unconstrained from the
    remaining pool (no duplicates, max 1 PoW initiator, max 1 Spheres class).

    Levels are NOT assigned here — randomize_level splits the rolled total level across
    character._class_picks (truncating the picks if the total is smaller than the count) and
    builds character.classes there.
    Returns
    - _class_picks (list of class-name strings, pick order preserved)
    """
    chooseClass(character, class_choice, chosen_BAB, chosen_caster_level)
    picks = [character.c_class]

    want_multi = isinstance(multi_class, str) and multi_class.lower() in ('y', 'yes')
    if want_multi:
        count = random.choices([2, 3, 4], weights=[50, 35, 15], k=1)[0]
        pool = _prune_class_pool(_available_class_pool(character), picks[0])
        while len(picks) < count and pool:
            # Cap caster classes at 3 (pf1 has only 3 spellbook slots) — once 3 casters are picked,
            # drop the rest of the casters so remaining slots draw from non-casters only.
            if sum(1 for p in picks if _is_caster(character, p)) >= 3:
                pool = [c for c in pool if not _is_caster(character, c)]
                if not pool:
                    break
            picked = random.choice(pool)
            picks.append(picked)
            pool = _prune_class_pool(pool, picked)

    character._class_picks = picks
    return picks