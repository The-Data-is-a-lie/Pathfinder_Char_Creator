import random, json, sys, math
from math import ceil, floor
from utils import data
import pandas as pd

def class_for_spells_attr(character):
    #currently we only know that skald spells aren't proper, but 
    # skalds use bard spell list -> just have an if statement for them 
    # CON 10
    # INT 12
    # investigators use alchemists spells
    # + check others
            
    #This is a quick and easy function to make it so we search
    #for different spell lists than our current class
    if character.c_class in ['skald']:
        character.c_class_for_spells = 'bard'
    elif character.c_class in ['investigator']:
        character.c_class_for_spells = 'alchemist'
    elif character.c_class in ['witch', 'arcanist']:
        character.c_class_for_spells='wizard' 
    elif character.c_class in ['warpriest', 'oracle']:
        character.c_class_for_spells='cleric'    
    elif character.c_class in ['summoner (unchained)']:
        character.c_class_for_spells='summoner'               
    else:
        character.c_class_for_spells = character.c_class     
    return character.c_class_for_spells



def caster_formula(character,n, class_2 = 'missing'):
    character.casting_level_string = str(character.class_data.get(character.c_class, "").get("casting level", "").lower())
    character.casting_level_num = character.c_class_level

    if character.casting_level_string == 'high':
        if n % 2 == 0:
            highest_spell_known=n // 2
        else:
            highest_spell_known=(n + 1) // 2
        highest_spell_known = min(highest_spell_known,9)

    elif character.casting_level_string == 'mid':
        if n % 3 != 0:
            highest_spell_known= ceil(n // 3) + 1
        else:
            highest_spell_known= ceil(n // 3)
        highest_spell_known = min(highest_spell_known,6)           
    
    elif character.casting_level_string == 'low':
        highest_spell_known= ceil(n / 3)-1
        highest_spell_known = min(highest_spell_known,4)           
        character.casting_level_num -= 3


    else:
        highest_spell_known = 0 
        character.casting_level_num = 0

    if class_2 == 'missing':
        character.highest_spell_known_1 = highest_spell_known
        return character.highest_spell_known_1    
    else:
        character.highest_spell_known_2 = highest_spell_known
        return character.highest_spell_known_2


#need to create this for casting_level_2 as well
def spells_known_attr(character,base_classes, divine_casters):     
    base_classes = getattr(data,base_classes)
    divine_casters=getattr(data, divine_casters)    
    character.casting_level_string = str(character.class_data[character.c_class]["casting level"].lower())         
    character.spells_known_list = []
    list = []    

    if character.c_class not in base_classes:
        print('Not a base class')
        return []

    elif character.c_class in divine_casters:
        print('Divine Casters know all spells')
        return []
    
    elif character.c_class == 'alchemist':
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)                
            list=character.spells_known[character.c_class][key][character.capped_level_1-1]
            character.spells_known_list.append(list)

    elif character.casting_level_string in ('low', 'mid', 'high'):
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)
            list=character.spells_known[character.c_class][key][character.capped_level_1-1]
            character.spells_known_list.append(list)
    else:
        print('Not an arcane caster')

    return character.spells_known_list

def spells_known_extra_roll(character):
    extra_spell_list = []        
    if character.c_class_for_spells in ['alchemist','wizard'] :
        for i in range(0,character.highest_spell_known_1 + 1):
            extra_spells = random.randint(1,10)
            extra_spell_list.append(extra_spells)

            # Remove 'null' values and ensure both lists have the same number of non-null elements
            filtered_spells_known = [0 if x == 'null' else x for x in character.spells_known_list]
            filtered_extra_spells = extra_spell_list[:len(filtered_spells_known)]

            if filtered_spells_known[i] == 0:
                filtered_extra_spells[i] = 0
            # Add corresponding elements of both lists
            result = [x + y for x, y in zip(filtered_spells_known, filtered_extra_spells)]

        character.spells_known_list=result
    return character.spells_known_list

def alignment_spell_limits(character, spell_data, i, alignment_exclusion):
    """
    Creates flags to limit spell choices to only be within the character's alignment for all classes 
    (not just cleric to make characters more thematic)

    return: query_i 
    params: spell_data (pandas file), i (number)
    """
    alignment = character.alignment.lower()
    extraction_list = ['name', 'school', 'descriptor']#, character.c_class_for_spells 'lawful', 'chaotic', 'evil', 'good']
    alignment_exclusion = getattr(data, alignment_exclusion)


    excluded_columns = set()

    for alignment_part in alignment.split(' '):
        excluded_column = alignment_exclusion.get(alignment_part)
        if excluded_column:
            excluded_columns.add(excluded_column)

    condition = spell_data[character.c_class_for_spells] == i

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



def spells_known_selection(character):
    spell_data=pd.read_csv('data/spells.csv', sep='|')
    spell_theme_func(character, spell_data)
    spell_theme_descriptor_func(character, spell_data)

    #extraction_list = ['name', character.c_class]                
    character.spell_list = []
    # the character has no cantrips, so they need to start at level 1 spells (slot 1)

    base_classes=getattr(data,'base_classes')
    divine_casters=getattr(data, 'divine_casters')
    # instantiate the spell list counter
    i=0
    if character.casting_level_string.lower() == 'low' or character.c_class in ('alchemist', 'investigator'):
        i = 1

    character.spell_list_choose_from=[]
    # Per-level count of spells a PREPARED caster prepares (= spells/day), aligned 1:1 to
    # spell_list_choose_from so the FoundryVTT module can mark exactly that many prepared per level.
    # Divine casters select day_list spells (so this equals the group size); spellbook casters
    # (wizard/witch/...) select the larger known_list, so this is the prepared subset.
    character.spells_prepared_per_level=[]

    #separating the lists
    known_list = character.spells_known_list
    day_list = character.spells_per_day_list

    if character.c_class not in base_classes or character.casting_level_string == 'none':
        return [], [], []
    
    if character.c_class not in divine_casters:
        select_spell_list = known_list
    else:
        select_spell_list = day_list

#we need to make sure we aren't grabbing null or our program will break
    while i <= character.highest_spell_known_1:
        if select_spell_list[i] == 'null':
            break

        select_spell = select_spell_list[i]

        query_i = alignment_spell_limits(character, spell_data, i, "alignment_exclusion")
        # Don't want more spells selected than there are in the list
        select_spell=min(select_spell_list[i], len(query_i), select_spell)             
        # only sample required number of spells
        spells = query_i.sample(n=select_spell, weights=query_i['weight'])

        spell_list = spells['name'].tolist()
        character.spell_list_choose_from.append(spell_list)
        # how many of this level a prepared caster prepares = spells/day, capped to what we picked.
        try:
            prepared_n = int(day_list[i])
        except (TypeError, ValueError, IndexError):
            prepared_n = 0
        character.spells_prepared_per_level.append(min(prepared_n, len(spell_list)))

        i += 1

    else:
        print('cannot select spells_known_selection')

    # for df in character.spell_list_choose_from:
    #     spell_names = df['name'].tolist()
    #     all_spell_names.extend(spell_names)

    # character.spell_list_choose_from = all_spell_names

    return character.spell_list_choose_from, day_list, known_list


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
_SPELL_CHANGES = None
_SPELL_RIDERS = None


def _spell_change_buffs():
    """Curated Bucket-A weapon buffs keyed by spell display name. Loaded once; {} if absent."""
    global _SPELL_CHANGES
    if _SPELL_CHANGES is None:
        from pathlib import Path as _Path
        _p = _Path(__file__).resolve().parents[2] / "json" / "spells" / "spell_changes.json"
        try:
            _SPELL_CHANGES = json.loads(_p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _SPELL_CHANGES = {}
    return _SPELL_CHANGES


def _spell_rider_buffs():
    """Curated Bucket-B save/rider data keyed by spell display name. Loaded once; {} if absent."""
    global _SPELL_RIDERS
    if _SPELL_RIDERS is None:
        from pathlib import Path as _Path
        _p = _Path(__file__).resolve().parents[2] / "json" / "spells" / "spell_riders.json"
        try:
            _SPELL_RIDERS = json.loads(_p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _SPELL_RIDERS = {}
    return _SPELL_RIDERS


def spell_conditionals_selection(character):
    """Filter the curated spell-conditional maps down to the spells this NPC actually has.

    Returns (spell_changes_dict, spell_riders_dict), each keyed by the spell's display name, for the
    spells present in character.spell_list_choose_from (a list of per-level lists of names). Matching
    is case-insensitive (mirrors the feat-map lookup in main_test.py). Both are {} for non-casters."""
    chosen = set()
    for level_list in (getattr(character, "spell_list_choose_from", None) or []):
        if isinstance(level_list, list):
            chosen.update(str(s) for s in level_list)
    chg_ci = {str(k).lower(): (k, v) for k, v in _spell_change_buffs().items()}
    rid_ci = {str(k).lower(): (k, v) for k, v in _spell_rider_buffs().items()}
    spell_changes_dict, spell_riders_dict = {}, {}
    for name in chosen:
        lc = name.lower()
        if lc in chg_ci:
            spell_changes_dict[name] = chg_ci[lc][1]
        if lc in rid_ci:
            spell_riders_dict[name] = rid_ci[lc][1]
    return spell_changes_dict, spell_riders_dict


# remove if need to give an accurate spells per day (only for foundryVTT (to have more spells populate in list))
def extra_spells_divine(character):
    divine_casters = getattr(data, 'divine_casters')

    if character.c_class not in divine_casters:
        return character.spells_per_day_list
    if character.casting_level_string == 'none':
        return []


    i = 0
    subtract_num = 0


    # We need to make sure we aren't grabbing null or our program will break
    while i in range(len(character.spells_per_day_list) - subtract_num):
        random_num = random.randint(1,10)
        if character.spells_per_day_list[i] == 'null':
            break
        character.spells_per_day_list[i] = character.spells_per_day_list[i] + random_num
        i+=1

    return character.spells_per_day_list


    

def spells_per_day_attr(character, base_classes):
    # We have to use normal spell class, since certain classes like Arcanist or Witch have the same spells but diff progressions as wizard/sorc 
    base_classes = getattr(data,base_classes)  
    character.spells_per_day_list = []
    list = []            

    if character.c_class not in base_classes:
        print('Not a base class')
        return []

    elif character.c_class == 'alchemist':
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)                
            list=character.spells_per_day[character.c_class][key][character.capped_level_1-1]
            character.spells_per_day_list.append(list)                

    elif character.casting_level_string in ('low', 'mid', 'high'):
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)
            list=character.spells_per_day[character.c_class][key][character.capped_level_1-1]
            character.spells_per_day_list.append(list)

    else:
        print('Not an spell list caster')

    return character.spells_per_day_list            


def spells_per_day_from_ability_mod(character, caster_mod):
    caster_mod = getattr(data,caster_mod)
    dataset = character.spells_from_ability_mod
    #for now we make sure it can't be above 17 -> otherwise breaks
    int_str = str(min(character.int_mod,17))
    wis_str = str(min(character.wis_mod,17))
    cha_str = str(min(character.cha_mod,17))
    i=0
    bonus_spells = []
    if character.c_class in caster_mod["int_casters"]:
        list=dataset[int_str]          
        for i in range (character.highest_spell_known_1 + 1):
            spells= list[i]
            bonus_spells.append(spells)
            i+=1
    elif character.c_class in caster_mod["wis_casters"]:
        list=dataset[wis_str]         
        print("list", list)
        for i in range (character.highest_spell_known_1 + 1):
            spells= list[i]
            bonus_spells.append(spells)
            i+=1
    elif character.c_class in caster_mod["cha_casters"]:
        list=dataset[cha_str]          
        for i in range (character.highest_spell_known_1 + 1):
            spells= list[i]
            bonus_spells.append(spells)                                
            i+=1
    else:
        print('Not a caster sorry bucko')

    #  adding a section for low casterse since they don't have cantrips
    for i,bonus in enumerate(bonus_spells):
        if bonus == 'null':
            break
        if not isinstance(character.spells_per_day_list[i], str):
            character.spells_per_day_list[i] = character.spells_per_day_list[i] + bonus

    return bonus_spells