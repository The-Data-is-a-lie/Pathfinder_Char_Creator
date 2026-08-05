import random, json, sys, math
from math import ceil, floor
from utils import data
from utils.paths import repo_path
from utils.class_func.buff_match import match as match_buffs
import pandas as pd

def class_for_spells_attr(character):
    #currently we only know that skald spells aren't proper, but
    # skalds use bard spell list -> just have an if statement for them
    # CON 10
    # INT 12
    # investigators use alchemists spells
    # + check others

    #This is a quick and easy function to make it so we search
    #for different spell lists than our current class. Each class entry gets its own mapping.
    for entry in character.classes:
        name = entry['name']
        if name in ['skald']:
            entry['class_for_spells'] = 'bard'
        elif name in ['investigator']:
            entry['class_for_spells'] = 'alchemist'
        elif name in ['witch', 'arcanist']:
            entry['class_for_spells'] = 'wizard'
        # The omdura's RAW list is the union of the cleric's and the inquisitor's, which nobody has
        # written down as a list. It reads the CLERIC column: the superset at every level a 'mid'
        # caster can reach, and the omdura is a cleric alternate class. The column's 7th-9th entries
        # are unreachable -- caster_formula caps 'mid' at 6 and the selector filters by level.
        elif name in ['warpriest', 'oracle', 'omdura']:
            entry['class_for_spells'] = 'cleric'
        # The vampire hunter casts off the inquisitor list RAW; that column already exists.
        elif name in ['vampire hunter']:
            entry['class_for_spells'] = 'inquisitor'
        elif name in ['summoner (unchained)']:
            entry['class_for_spells'] = 'summoner'
        else:
            entry['class_for_spells'] = name
    return [entry['class_for_spells'] for entry in character.classes]



def casting_stat_for(class_name):
    """The class's casting ability ('int'/'wis'/'cha') per data.caster_mod, or None for
    non-casters. Classes in two lists (shaman) resolve to the first match: int > wis > cha."""
    for stat, key in (('int', 'int_casters'), ('wis', 'wis_casters'), ('cha', 'cha_casters')):
        if class_name in data.caster_mod[key]:
            return stat
    return None


# PF1e: a SPONTANEOUS full caster gains each new spell level one class level LATER than a prepared
# caster of the same tier -- a sorcerer reaches 2nd-level spells at 4, a wizard at 3. Spell level 1
# is the exception; both get it at class level 1.
#
# Keyed by class NAME rather than by widening `casting_level_string`, because that tier string is a
# cross-repo contract: it ships in the payload and both the FoundryVTT module and the web sheet read
# it. A new tier value would be a breaking change to two other repositories to express a rule that
# is purely internal to this function.
#
# This is a RULE, not a restatement of the tables. Keeping it here is what lets
# gates/validate_progression_tables.py go on cross-checking the scraped data against independently
# computed levels -- deriving the answer from the table instead would have made the gate compare the
# data with itself, and a scraper error would become the character's behaviour with no second
# opinion. Verified against all 30 tables: these four lag by exactly 1 at every spell level, and no
# other class does.
SPONTANEOUS_FULL_CASTERS = frozenset({'sorcerer', 'oracle', 'psychic', 'arcanist'})

# `adept` is not a lag -- it is an NPC class with its own published ladder, unlocking a spell level
# every 4 class levels (1/4/8/12/16) and stopping at 5th. It was mapped onto 'mid' because that was
# the closest tier that existed, which made it wrong by up to 3 levels and gave it a 6th-level row
# it never reaches. Same reasoning as above for keying on the name: its declared tier stays 'mid'
# for the payload's sake.
_ADEPT_CAP = 5


def caster_formula(character, n, class_entry):
    """Highest castable spell level + adjusted caster level for ONE class entry (n = its class
    level). Writes class_entry['highest_spell_known'] / ['casting_level_num'].

    `character` is unused -- gates call this with None to exercise the formula in isolation."""
    casting_level_string = class_entry['casting_level_string']
    casting_level_num = class_entry['level']
    # .get: gates construct a bare {'casting_level_string', 'level'} entry to probe the formula.
    name = (class_entry.get('name') or '').lower()

    if name == 'adept':
        # 1st at class level 1, then one more every 4 levels. min() rather than a branch on n<4
        # because 1 + n//4 already yields 1 for n in 1..3.
        highest_spell_known = min(1 + n // 4, _ADEPT_CAP)

    elif casting_level_string == 'high' and name in SPONTANEOUS_FULL_CASTERS:
        # Spell level s unlocks at class level 2s (vs 2s-1 prepared), except 1st at level 1 --
        # which is what max(1, ...) preserves, and why this is not simply the prepared value minus
        # one.
        highest_spell_known = min(max(1, n // 2), 9)

    elif casting_level_string == 'high':
        if n % 2 == 0:
            highest_spell_known=n // 2
        else:
            highest_spell_known=(n + 1) // 2
        highest_spell_known = min(highest_spell_known,9)

    elif casting_level_string == 'mid':
        if n % 3 != 0:
            highest_spell_known= ceil(n // 3) + 1
        else:
            highest_spell_known= ceil(n // 3)
        highest_spell_known = min(highest_spell_known,6)

    elif casting_level_string == 'low':
        highest_spell_known= ceil(n / 3)-1
        highest_spell_known = min(highest_spell_known,4)
        casting_level_num -= 3


    else:
        highest_spell_known = 0
        casting_level_num = 0

    class_entry['highest_spell_known'] = highest_spell_known
    class_entry['casting_level_num'] = casting_level_num
    return highest_spell_known


def spells_known_attr(character, base_classes, divine_casters, class_entry):
    base_classes = getattr(data,base_classes)
    divine_casters=getattr(data, divine_casters)
    class_entry['spells_known_list'] = []
    name = class_entry['name']
    list = []

    if name not in base_classes:
        print('Not a base class')
        return []

    elif name in divine_casters:
        print('Divine Casters know all spells')
        return []

    elif name == 'alchemist' or class_entry['casting_level_string'] in ('low', 'mid', 'high'):
        for i in range(0, class_entry['highest_spell_known']+1):
            key = str(i)
            list=character.spells_known[name][key][class_entry['capped_level']-1]
            class_entry['spells_known_list'].append(list)
    else:
        print('Not an arcane caster')

    return class_entry['spells_known_list']

def spells_known_extra_roll(character, class_entry):
    extra_spell_list = []
    if class_entry.get('class_for_spells') in ['alchemist','wizard'] :
        for i in range(0, class_entry['highest_spell_known'] + 1):
            extra_spells = random.randint(1,10)
            extra_spell_list.append(extra_spells)

            # Remove 'null' values and ensure both lists have the same number of non-null elements
            filtered_spells_known = [0 if x == 'null' else x for x in class_entry['spells_known_list']]
            filtered_extra_spells = extra_spell_list[:len(filtered_spells_known)]

            if filtered_spells_known[i] == 0:
                filtered_extra_spells[i] = 0
            # Add corresponding elements of both lists
            result = [x + y for x, y in zip(filtered_spells_known, filtered_extra_spells)]

        class_entry['spells_known_list']=result
    return class_entry['spells_known_list']

def alignment_spell_limits(character, spell_data, i, alignment_exclusion, spells_class):
    """
    Creates flags to limit spell choices to only be within the character's alignment for all classes
    (not just cleric to make characters more thematic)

    return: query_i
    params: spell_data (pandas file), i (number), spells_class (spell-list column name)
    """
    alignment = character.alignment.lower()
    extraction_list = ['name', 'school', 'descriptor']#, 'lawful', 'chaotic', 'evil', 'good']
    alignment_exclusion = getattr(data, alignment_exclusion)


    excluded_columns = set()

    for alignment_part in alignment.split(' '):
        excluded_column = alignment_exclusion.get(alignment_part)
        if excluded_column:
            excluded_columns.add(excluded_column)

    condition = spell_data[spells_class] == i

    for col in excluded_columns:
        condition &= (spell_data[col] == 0)
    query_i = spell_data.loc[condition, extraction_list]
    query_i = limit_school_func(character, query_i)
    query_i = limit_descriptor_func(character, query_i)

    return query_i

def spell_theme_func(character, spell_data):
    character.available_schools = spell_data['school'].value_counts()
    character.available_schools = character.available_schools[character.available_schools > 30].index.tolist()    
    # grab a list of chooseable spell schools
    num_of_schools = random.randint(1,2)
    specialty_schools = random.sample(character.available_schools, num_of_schools)
    for school in specialty_schools:
        character.available_schools.remove(school)
    remaining_schools = character.available_schools
    counter_schools = random.sample(remaining_schools, num_of_schools)

    character.specialty_schools = specialty_schools
    character.counter_schools = counter_schools
    return []


def limit_school_func(character, query_i):
    #apply weights
    # intialize with a float (1.0) so we don;'t encounter a pandas issue later (since intialize as int64 but uses float later)
    query_i['weight'] = 1.0
    query_i.loc[query_i['school'].isin(character.specialty_schools), 'weight'] = 100
    query_i.loc[query_i['school'].isin(character.counter_schools), 'weight'] = .1
    return query_i.sort_values(by='weight', ascending=False)

def limit_descriptor_func(character, query_i):
    query_i.loc[query_i['descriptor'].isin(character.chosen_descriptors), 'weight'] *= 100
    return query_i

def remove_commas_func(spell_data):
    all_descriptors = spell_data['descriptor'].dropna().str.split(',').explode().str.strip()
    return all_descriptors

def spell_theme_descriptor_func(character, spell_data):
    all_descriptors = remove_commas_func(spell_data)
    descriptor_counts = all_descriptors.value_counts()
    character.available_descriptors = descriptor_counts[descriptor_counts > 30].index.tolist()
    num_of_descriptors = random.randint(1,2)
    chosen_descriptors = random.sample(character.available_descriptors, num_of_descriptors)
    for school in chosen_descriptors:
        character.available_descriptors.remove(school)
    remaining_descriptors = character.available_descriptors
    counter_descriptors = random.sample(remaining_descriptors, num_of_descriptors)

    character.chosen_descriptors = chosen_descriptors
    character.counter_descriptors = counter_descriptors



_SPELL_DATA = None


def _load_spell_data():
    """spells.csv, loaded once per process (it's static data and multiclass reads it per book)."""
    global _SPELL_DATA
    if _SPELL_DATA is None:
        _SPELL_DATA = pd.read_csv(repo_path('data/spells.csv'), sep='|')
    return _SPELL_DATA


def spell_themes(character):
    """Roll the character-wide spell themes (specialty/counter schools + descriptors) once —
    every spellbook of a multiclass caster weights its picks by the same themes, and the fields
    are exported for non-casters too."""
    spell_data = _load_spell_data()
    spell_theme_func(character, spell_data)
    spell_theme_descriptor_func(character, spell_data)


def spells_known_selection(character, class_entry):
    spell_data = _load_spell_data()

    character.spell_list = []
    # the character has no cantrips, so they need to start at level 1 spells (slot 1)

    base_classes=getattr(data,'base_classes')
    divine_casters=getattr(data, 'divine_casters')
    name = class_entry['name']
    casting_level_string = class_entry['casting_level_string']
    # instantiate the spell list counter
    i=0
    if casting_level_string == 'low' or name in ('alchemist', 'investigator'):
        i = 1

    class_entry['spell_list_choose_from']=[]
    # Per-level count of spells a PREPARED caster prepares (= spells/day), aligned 1:1 to
    # spell_list_choose_from so the FoundryVTT module can mark exactly that many prepared per level.
    # Divine casters select day_list spells (so this equals the group size); spellbook casters
    # (wizard/witch/...) select the larger known_list, so this is the prepared subset.
    class_entry['spells_prepared_per_level']=[]

    #separating the lists
    known_list = class_entry.get('spells_known_list', [])
    day_list = class_entry.get('spells_per_day_list', [])

    if name not in base_classes or casting_level_string == 'none':
        return [], [], []

    if name not in divine_casters:
        select_spell_list = known_list
    else:
        select_spell_list = day_list

#we need to make sure we aren't grabbing null or our program will break
    while i <= class_entry['highest_spell_known']:
        if select_spell_list[i] == 'null':
            break

        select_spell = select_spell_list[i]

        query_i = alignment_spell_limits(character, spell_data, i, "alignment_exclusion",
                                         class_entry['class_for_spells'])
        # Don't want more spells selected than there are in the list
        select_spell=min(select_spell_list[i], len(query_i), select_spell)
        # only sample required number of spells
        spells = query_i.sample(n=select_spell, weights=query_i['weight'])

        spell_list = spells['name'].tolist()
        class_entry['spell_list_choose_from'].append(spell_list)
        # how many of this level a prepared caster prepares = spells/day, capped to what we picked.
        try:
            prepared_n = int(day_list[i])
        except (TypeError, ValueError, IndexError):
            prepared_n = 0
        class_entry['spells_prepared_per_level'].append(min(prepared_n, len(spell_list)))

        i += 1

    else:
        print('cannot select spells_known_selection')

    return class_entry['spell_list_choose_from'], day_list, known_list


# --- Spell conditionals / riders -----------------------------------------------------------------
# Curated, name-keyed pf1 data attached to a generated NPC's chosen spells so the FoundryVTT module
# can carry them into the actor (mirrors the feat_changes / feat_conditionals split). Authored via
# Backend/scripts/build_spell_conditionals.py + manual curation; {} if the file is absent.
#   spell_changes.json -- Bucket A buffs (Bless, Divine Favor, True Strike, Magic Weapon, Flame
#                         Arrow): a default-off conditional toggle / always-on change on the wielder's
#                         WEAPON ({name,default,modifiers} or {changes,contextNotes}).
#   spell_riders.json  -- Bucket B damaging-attack spells (Chill Touch, Frigid Touch, Acid Arrow):
#                         the formal save block + non-damage riders ([[ ]] inline text) on the SPELL's
#                         own action (its attack + damage already come from the pf1 compendium).
# The curated spell maps are loaded and cached by utils/class_func/buff_match.py (kinds
# 'spell_change' and 'spell_rider'); the private loaders that used to live here were a second
# copy of that cache. Scripts that need the raw data call buff_match.raw(<kind>).


def spell_conditionals_selection(character):
    """Filter the curated spell-conditional maps down to the spells this NPC actually has.

    Returns (spell_changes_dict, spell_riders_dict), each keyed by the spell's display name, for the
    spells present in character.spell_list_choose_from (a list of per-level lists of names). Matching
    is case-insensitive (mirrors the feat-map lookup in main_test.py). Both are {} for non-casters."""
    # dict.fromkeys, not a set: a set of strings iterates in hash order, which Python randomizes per
    # process, so the two dicts below came out with different key ORDER on every run.
    chosen = {}
    for level_list in (getattr(character, "spell_list_choose_from", None) or []):
        if isinstance(level_list, list):
            for s in level_list:
                chosen[str(s)] = None

    spell_changes_dict, changes_gaps = match_buffs('spell_change', chosen)
    spell_riders_dict, rider_gaps = match_buffs('spell_rider', chosen)
    # main_test collects these into the payload's buff_gaps.
    character.spell_buff_gaps = changes_gaps + rider_gaps
    return spell_changes_dict, spell_riders_dict


# remove if need to give an accurate spells per day (only for foundryVTT (to have more spells populate in list))
def extra_spells_divine(character, class_entry):
    divine_casters = getattr(data, 'divine_casters')

    if class_entry['name'] not in divine_casters:
        return class_entry.get('spells_per_day_list', [])
    if class_entry['casting_level_string'] == 'none':
        return []


    i = 0
    subtract_num = 0
    spells_per_day_list = class_entry['spells_per_day_list']


    # We need to make sure we aren't grabbing null or our program will break
    while i in range(len(spells_per_day_list) - subtract_num):
        random_num = random.randint(1,10)
        if spells_per_day_list[i] == 'null':
            break
        spells_per_day_list[i] = spells_per_day_list[i] + random_num
        i+=1

    return spells_per_day_list




def spells_per_day_attr(character, base_classes, class_entry):
    # We have to use normal spell class, since certain classes like Arcanist or Witch have the same spells but diff progressions as wizard/sorc
    base_classes = getattr(data,base_classes)
    class_entry['spells_per_day_list'] = []
    name = class_entry['name']
    list = []

    if name not in base_classes:
        print('Not a base class')
        return []

    elif name == 'alchemist' or class_entry['casting_level_string'] in ('low', 'mid', 'high'):
        for i in range(0, class_entry['highest_spell_known']+1):
            key = str(i)
            list=character.spells_per_day[name][key][class_entry['capped_level']-1]
            class_entry['spells_per_day_list'].append(list)

    else:
        print('Not an spell list caster')

    return class_entry['spells_per_day_list']


def spells_per_day_from_ability_mod(character, caster_mod, class_entry):
    caster_mod = getattr(data,caster_mod)
    dataset = character.spells_from_ability_mod
    name = class_entry['name']
    #for now we make sure it can't be above 17 -> otherwise breaks
    int_str = str(min(character.int_mod,17))
    wis_str = str(min(character.wis_mod,17))
    cha_str = str(min(character.cha_mod,17))
    i=0
    bonus_spells = []
    if name in caster_mod["int_casters"]:
        list=dataset[int_str]
        for i in range (class_entry['highest_spell_known'] + 1):
            spells= list[i]
            bonus_spells.append(spells)
            i+=1
    elif name in caster_mod["wis_casters"]:
        list=dataset[wis_str]
        print("list", list)
        for i in range (class_entry['highest_spell_known'] + 1):
            spells= list[i]
            bonus_spells.append(spells)
            i+=1
    elif name in caster_mod["cha_casters"]:
        list=dataset[cha_str]
        for i in range (class_entry['highest_spell_known'] + 1):
            spells= list[i]
            bonus_spells.append(spells)
            i+=1
    else:
        print('Not a caster sorry bucko')

    #  adding a section for low casterse since they don't have cantrips
    spells_per_day_list = class_entry.get('spells_per_day_list', [])
    for i,bonus in enumerate(bonus_spells):
        if bonus == 'null':
            break
        if i >= len(spells_per_day_list):
            break
        if not isinstance(spells_per_day_list[i], str):
            spells_per_day_list[i] = spells_per_day_list[i] + bonus

    return bonus_spells


def sync_legacy_spell_fields(character):
    """Point the legacy scalar spell fields at the PRIMARY spellbook — the primary class's if it
    casts, else the first caster's in roll order — or at the empty no-caster shapes. Downstream
    consumers (prereq pools, bonus-spell insertion, export) keep reading the scalars; extra
    multiclass spellbooks live in character.spellbooks."""
    primary = character.classes[character.primary_class_index]
    book = None
    if primary['casting_level_string'] in ('low', 'mid', 'high'):
        book = primary
    else:
        for entry in character.classes:
            if entry['casting_level_string'] in ('low', 'mid', 'high'):
                book = entry
                break

    if book is None:
        character.c_class_for_spells = primary.get('class_for_spells', primary['name'])
        character.casting_level_string = primary['casting_level_string']
        character.casting_level_num = 0
        character.highest_spell_known_1 = 0
        character.spells_known_list = []
        character.spells_per_day_list = []
        character.spell_list_choose_from = []
        character.spells_prepared_per_level = []
    else:
        character.c_class_for_spells = book['class_for_spells']
        character.casting_level_string = book['casting_level_string']
        # feat/talent prereqs ("caster level X") should see the character's best caster level
        character.casting_level_num = max(e.get('casting_level_num', 0) for e in character.classes)
        character.highest_spell_known_1 = book['highest_spell_known']
        character.spells_known_list = book.get('spells_known_list', [])
        character.spells_per_day_list = book.get('spells_per_day_list', [])
        character.spell_list_choose_from = book.get('spell_list_choose_from', [])
        character.spells_prepared_per_level = book.get('spells_prepared_per_level', [])