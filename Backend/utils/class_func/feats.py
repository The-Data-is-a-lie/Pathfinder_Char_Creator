import re, random
import pandas as pd
from math import ceil, floor


# Importing custom functions
from utils.class_func.generic_func import *
from utils.class_func.chooseable import *
from utils.class_func.skill_ranks import homebrew_enabled
from utils.paths import repo_path

def _divine_arcane_flags(character):
    """(is_divine, is_arcane_caster) across ALL classes — a multiclass cleric/wizard is both, and
    then neither the divine- nor arcane-feat filter should strip its feats."""
    divine_casters = getattr(data, "divine_casters")
    is_divine = any(c['name'] in divine_casters for c in character.classes)
    is_arcane = any(c['casting_level_string'] in ('low', 'mid', 'high')
                    and c['name'] not in divine_casters for c in character.classes)
    return is_divine, is_arcane


def feat_spell_searcher(character, class_1, chosen_set, types, info_column, info_column_2 = None):
    if chosen_set == None:
        return
    if class_entry_for(character, class_1) is not None:
        data = pd.read_csv(repo_path(f'data/{types}.csv'), sep='|', on_bad_lines='skip')
    
        if info_column_2 is None:
            extraction_list = ['name', info_column]
        else:
            extraction_list = ['name', info_column, info_column_2]



        query_result = remove_mythic(character, types,data, chosen_set, extraction_list)

        result_dict = {}
        result_dict = remove_dots_dashes(character, result_dict, query_result, info_column)
        character.result_dict.update(result_dict)
        
        return character.result_dict         

def remove_mythic(character, types, data, chosen_set, extraction_list):
    
    if chosen_set == None:
        return None

    chosen_set_upper = {i.upper() for i in chosen_set}

    if types == 'feats':
        query_result = data[(data['name'].str.upper().isin(chosen_set_upper)) & (data['type'] != 'Mythic')][extraction_list]
    else:
        query_result = data[(data['name'].str.upper().isin(chosen_set_upper)) & (data['mythic'] == 0)][extraction_list]  

    return query_result

def remove_dots_dashes(character, result_dict, query_result, info_column, info_column_2=None):
    replace_dash = lambda x: re.sub(r'[-]', ' ', str(x))            
    replace_dot = lambda x: re.sub(r'[.]', '', str(x))            

    if query_result is None:
        return

    for index, row in query_result.iterrows():
        feat_name = row['name']
        if pd.isna(row[info_column]):
            row[info_column] = ''
        feat_info = {f'{info_column}': replace_dash(row[f'{info_column}'])}
        feat_info = {f'{info_column}': replace_dot(row[f'{info_column}'])}
        
        if info_column_2 is not None:
            if pd.isna(row[info_column_2]):
                row[info_column_2] = ''
        feat_info = {f'{info_column}': replace_dash(row[f'{info_column}'])}
        feat_info = {f'{info_column}': replace_dot(row[f'{info_column}'])}

        result_dict[feat_name] = feat_info
    
    return result_dict



def bonus_searcher(character, choice, chosen_desc, types):
    bonus_list = []
    bonus = chosen_desc.get(choice,{}).get(f"bonus {types}", {})
    character.json_list_grabber( bonus_list, ",", bonus)
    remove_parentheses(character, bonus_list)

    return bonus_list


def remove_parentheses(character, text_list):
    result_list = []
    for text in text_list:
        pattern = r'\([^)]*\)'
        result = re.sub(pattern, '', text)
        result_list.extend(result)
    
    return result_list       
        

def remove_duplicates_list(character,lst):
    seen = set()
    result = []
    for item in lst:
        # Convert lists to tuples for hashability
        item_tuple = tuple(item) if isinstance(item, list) else item
        if item_tuple not in seen:
            seen.add(item_tuple)
            result.append(item)
    return result

def build_selector(character):
    casting_level_str = character.class_data[character.c_class]['casting level'].lower()
    specialty_set = {'cleric', 'druid'}
    type_chance = random.choices(range(1, 101))[0]
    feat_list = []

    if character.bab == 'H' or (character.bab == 'M' and casting_level_str not in ('low', 'mid', 'high')):
        add_martial_feats(character, feat_list)
    if character.bab == 'L' and casting_level_str != 'none':
        add_magical_feats(character, feat_list)
    if character.bab == 'M' and casting_level_str != 'none':
        if 50 >= type_chance >= 75:
            add_martial_feats(character, feat_list)
        if 76 >= type_chance:
            add_magical_feats(character, feat_list)
        else:
            add_martial_feats(character, feat_list)
            add_magical_feats(character, feat_list)
    for _entry in character.classes:
        if _entry['name'] in specialty_set:
            add_specialty_feats(character, feat_list, _entry['name'])

    result_dict_pre = feat_spell_searcher(character, character.c_class, feat_list, "feats", "prerequisites", "description")
    result_dict = transform_result_dict(character, result_dict_pre)
    chosen_feats = get_feats_without_prerequisites(character, character.c_class, result_dict, feat_amount=character.feat_amounts)
    cleaned_chosen_feats = capitalize_feats(character, chosen_feats)
    return cleaned_chosen_feats


def add_martial_feats(character, feat_list):
    martial = character.feat_buckets['martial']
    universal = character.feat_buckets['universal']

    martial_choice = random.choice(list(martial.keys()))
    universal_choice = random.choice(list(universal.keys()))
    martial_choice_2 = random.choice(list((martial[martial_choice].keys())))
    list_2 = list(universal[universal_choice])
    list_1 = list(martial[martial_choice][martial_choice_2])
    feat_list.extend(list_1 + list_2)        

    if character.dex_mod >= character.str_mod +2:
        feat_list.append('weapon finesse')        

    character.feat_list = feat_list
    return character.feat_list

def add_magical_feats(character, feat_list):
    magical = character.feat_buckets['magical']
    universal = character.feat_buckets['universal']

    magical_choice = random.choice(list(magical.keys()))
    universal_choice = random.choice(list(universal.keys()))
    list_2 = list(universal[universal_choice])
    list_1 = list(magical[magical_choice])
    feat_list.extend(list_1 + list_2)    

def add_specialty_feats(character, feat_list, class_name=None):
    classes_choices = list(character.feat_buckets['classes'][class_name or character.c_class])
    feat_list.extend(classes_choices)

def transform_result_dict(character, result_dict):
    for feat in list(result_dict.keys()):
        feat_info = result_dict[feat]
        prereq_set = set()
        prerequisites = str(feat_info.get('prerequisites', None))

        if prerequisites is not None:
            prereq_set.add(prerequisites.lower())
            result_dict[feat]['prerequisites'] = prerequisites.lower()
            new_feat = feat.lower()

            if prerequisites.lower() == 'nan':
                result_dict[feat]['prerequisites'] = ''
                new_feat = ''

            if new_feat != feat:
                result_dict[new_feat] = result_dict.pop(feat)     
    return result_dict


def get_feats_without_prerequisites(character, class_1, dataset_name, level= None, level_2 = None, dataset_name_2 = None, feat_amount=None):

    if class_entry_for(character, class_1) is None:
        return None

    base_no_prereq = []
    amount = feat_amount
    # print("dataset_name", dataset_name)
    # amount = ceil(character.c_class_level/2)
    base_no_prereq = no_prereq_loop(character, dataset_name)
    total_choices = base_no_prereq


    if amount == None:
        amount = 0

    chosen_feats = choosing_feats(character, amount, dataset_name, total_choices)

    return chosen_feats

def choosing_feats(character, amount, base, total_choices):
    if amount is None or amount <= 0:
        return []

    # An insertion-ordered dict used as a set: `list(chosen_feats)` is the return value, and a real
    # set would hand it back in string-hash order, which Python randomizes per process. That made the
    # SAME seed deal feats into different buckets on every run (separate_feats_func front-pops this
    # list into story/flaw/flavor/class). Keys are the lowercased names, so dedup is unchanged.
    chosen_feats = {}
    # character.chooseable_talents (which feeds total_choices) accumulates across selection
    # passes -- the talent/feat cross-pollination relies on that -- so feats already picked by
    # an EARLIER pass (main pool vs teamwork, class-granted bonus feats, ...) are still in the
    # pool. Drop owned feats so no pass can re-pick another pass's selection (duplicate feats).
    total_choices_set = {c for c in total_choices if c not in character.chooseable}
    stale = 0

    while len(chosen_feats) < amount:
        if not total_choices_set:
            break
        before = len(chosen_feats)
        # sorted(), not tuple(): a set of strings iterates in hash order, and Python randomizes string
        # hashing per process -- so tuple(set) gave a DIFFERENT feat on every run even under a fixed
        # random.seed(). Sorting makes the draw reproducible (see the seed param on
        # main_test.generate_random_char); the set is mutated below, so this re-sorts each pass.
        chosen = random.choice(sorted(total_choices_set))
        chosen_feats[chosen.lower()] = None

        # Update character's chooseable feats
        character.chooseable.add(chosen)

        # Recompute the prereq_list after adding the chosen feat
        prereq_list = no_prereq_loop(character, base)

        # Update total_choices_set with new prerequisites
        total_choices_set.add(chosen.lower())
        total_choices_set.update(c for c in prereq_list if c not in character.chooseable)

        # Termination guard: if we keep drawing feats we already have and the candidate pool
        # isn't growing, stop instead of looping forever. This can happen at high level when
        # more feats are requested (incl. reallocated bonus-feat slots) than the filtered pool
        # can supply. Returns fewer feats rather than hanging; never inflates.
        if len(chosen_feats) == before:
            stale += 1
            if stale > len(total_choices_set):
                break
        else:
            stale = 0

    return list(chosen_feats)

def special_feats_func(feat_data, extraction_type, special_type):
    query_i = feat_data.loc[
        feat_data[special_type] == 1,
        extraction_type
    ]
    return query_i

_FEAT_DATA_CACHE = {}

def grab_and_clean_feats(location):
    # The feat CSV is static during a run, but this used to be re-parsed on every
    # generic_feat_chooser call. Cache the cleaned DataFrame by path and hand back a copy
    # so callers can filter/drop_duplicates without mutating the cached frame.
    cached = _FEAT_DATA_CACHE.get(location)
    if cached is not None:
        return cached.copy()
    feat_data = pd.read_csv(repo_path(location), sep='|', on_bad_lines='skip')
    # makes prereq NaNs -> empty strings. Without this we can't grab feats with blank prereqs
    feat_data.fillna({'prerequisites': ''}, inplace=True)
    feat_data.fillna({'description': ''}, inplace=True)
    feat_data.fillna({'benefits': ''}, inplace=True)
    _FEAT_DATA_CACHE[location] = feat_data
    return feat_data.copy()

# Metzofitz homebrew library (oks/pathfinder/house-rules/homebrew-content.md), joined into the
# generic pools behind the homebrew flag. Only rows typed EXACTLY 'General' or 'Combat' are taken:
# the chooser filters on type equality, and the CSV's comma-joined subsystem types ('Akashic,
# General', 'Combat, Style', ...) can never match it -- which is what keeps veilweaving / psionic /
# kineticist feats a generic class can't use out, and style chains out of the random pool (those
# are granted through path_of_war.py's Martial Training machinery instead).
_METZ_LOCATION = 'data/Metzofitz_Feats.csv'
_METZ_TYPES = ('General', 'Combat')
_METZ_DESCS = None


def metzofitz_feat_frame():
    """General/Combat Metzofitz rows shaped like data/feats.csv for the pool concat. The CSV keeps
    flavor in 'description' and the rules text in 'benefits'; the sheet wants both, so they are
    merged into 'description' here."""
    metz = grab_and_clean_feats(_METZ_LOCATION)
    metz = metz[metz['type'].isin(_METZ_TYPES)].copy()
    metz['description'] = (metz['description'].astype(str).str.strip() + ' '
                           + metz['benefits'].astype(str).str.strip()).str.strip()
    return metz[['name', 'type', 'prerequisites', 'description']]


def metzofitz_description(name):
    """Rules text for a poolable Metzofitz feat (case-insensitive); '' when unknown. Lets the
    main_test render fallback describe Metzofitz picks -- they are absent from data/feats.csv, and
    a nameless description would make the Foundry module synthesize an empty row."""
    global _METZ_DESCS
    if _METZ_DESCS is None:
        frame = metzofitz_feat_frame()
        _METZ_DESCS = {str(n).lower(): d for n, d in zip(frame['name'], frame['description'])}
    return _METZ_DESCS.get(str(name).lower(), '')


def teamwork_pool_size(character, casting_level_str):
    """Number of teamwork feats this character could actually take, after the same
    caster / arcane / divine filters generic_feat_chooser applies. Lets us detect when a
    class is granted more teamwork slots than there are eligible teamwork feats, so the
    surplus can be reallocated to normal feats. (No prereq filtering -> upper bound, so we
    only ever under-count the surplus, never over-reallocate.)"""
    feat_data = grab_and_clean_feats('data/feats.csv')
    extraction_list = ['name', 'prerequisites', 'description']
    query_i = special_feats_func(feat_data, extraction_list, 'teamwork')
    query_i = query_i.drop_duplicates(subset='name', keep='first')
    feat_result_dict = query_i.set_index('name')[['prerequisites', 'description']].to_dict(orient='index')
    feat_result_dict = transform_result_dict(character, feat_result_dict)

    is_divine, is_arcane = _divine_arcane_flags(character)
    if casting_level_str not in ("low", "mid", "high"):
        feat_result_dict = remove_spell_caster_feats(feat_result_dict)
    if is_divine and not is_arcane:
        feat_result_dict = remove_arcane_feats(feat_result_dict)
    if not is_divine:
        feat_result_dict = remove_divine_feats(feat_result_dict)

    return len(feat_result_dict)

def generic_feat_chooser(character, class_1, casting_level_str,feat_type, info_column, override = None, special_type = None, feat_amount = None, extra_feats_flag = False):
    if class_entry_for(character, class_1) is not None:
        feat_data = grab_and_clean_feats('data/feats.csv')

        # Metzofitz homebrew joins the pool behind the homebrew flag (backlog #1). Concat order
        # matters: feats.csv first, so the drop_duplicates(keep='first') below lets AoN win any
        # name collision with the homebrew library.
        if homebrew_enabled(character):
            feat_data = pd.concat([feat_data, metzofitz_feat_frame()], ignore_index=True)

        #----- grab divine casters list
        divine_casters=getattr(data, "divine_casters")        

        extraction_list = ['name', 'prerequisites', 'description']
        if casting_level_str in ("mid", "high"):
            query_i = feat_data.loc[
                (feat_data['type'] == feat_type.capitalize()) 
                | (feat_data['type'] == 'General') 
                | (feat_data['type'] == 'Item Creation')
                | (feat_data['type'] == 'Story') 
                | (feat_data['type'] == 'Achievement'), 
                extraction_list
            ]
        else:
            query_i = feat_data.loc[
                (feat_data['type'] == feat_type.capitalize()) 
                | (feat_data['type'] == 'General') 
                | (feat_data['type'] == 'Story') 
                | (feat_data['type'] == 'Achievement'), 
                extraction_list
            ]


        if override is not None:
            query_i = special_feats_func(feat_data, extraction_list, special_type)
        
        query_i = query_i.drop_duplicates(subset='name', keep='first')
        feat_result_dict = query_i.set_index('name')[['prerequisites', 'description']].to_dict(orient='index')
        feat_result_dict = transform_result_dict(character, feat_result_dict)
        feat_result_dict.update(feat_result_dict)

        is_divine, is_arcane = _divine_arcane_flags(character)
        # remove feats if not spellcaster
        if casting_level_str not in ("low", "mid", "high"):
            feat_result_dict = remove_spell_caster_feats(feat_result_dict)
        # remove feats with 'arcane' words if a (purely) divine caster
        if is_divine and not is_arcane:
            feat_result_dict = remove_arcane_feats(feat_result_dict)
        # remove feats with 'divine' words if an arcane/non-divine character
        if not is_divine:
            feat_result_dict = remove_divine_feats(feat_result_dict)

        chosen_feats = get_feats_without_prerequisites(character, character.c_class, feat_result_dict, feat_amount=feat_amount)
        # chosen_feats.remove("")
        cleaned_chosen_feats = capitalize_feats(character, chosen_feats)
        # character.chosen_feats = cleaned_chosen_feats

        return cleaned_chosen_feats

def topup_feat_chooser(character, casting_level_str, amount):
    """Draw `amount` additional feats from progressively wider pools. Used to top up a
    shortfall after the main selection (the type/caster-filtered pools can exhaust at high
    level) and to backfill slots freed by the feat-tax child strip. choosing_feats registers
    every pick in character.chooseable, so repeated calls never duplicate earlier picks."""
    if not amount or amount <= 0:
        return []
    primary = 'metamagic' if (casting_level_str in ('mid', 'high') and character.bab in ('L', 'M')) else 'combat'
    # widen: preferred type -> combat -> 'Null' (matches no type -> General/Story-heavy pool)
    attempts = [primary] + (['combat'] if primary == 'metamagic' else []) + ['Null']
    picked = []
    for feat_type in attempts:
        remaining = amount - len(picked)
        if remaining <= 0:
            break
        extra = generic_feat_chooser(character, character.c_class, casting_level_str, feat_type,
                                     info_column='description', feat_amount=remaining)
        if isinstance(extra, list):
            picked.extend(extra)
    if len(picked) < amount:
        print(f"feat top-up: pools exhausted, {amount - len(picked)} slot(s) unfilled")
    return picked

def remove_spell_caster_feats(feats):
    spell_word_list = ['spell', 'cast', 'dispel', 'aracane', 'summon', 'teleport']
    feats = {name: info for name, info in feats.items()
            if not  any(word in name.lower() or
                        word in info.get('description', '').lower() or
                        word in info.get('prerequisites', '').lower() or
                        word in info.get('prerequisite', '').lower() or
                        word in info.get('benefits', '').lower()
                        for word in spell_word_list)}
    return feats

def remove_arcane_feats(feats):
    spell_word_list = ['arcane']
    feats = {name: info for name, info in feats.items()
            if not  any(word in name.lower() or
                        word in info.get('description', '').lower() or
                        word in info.get('prerequisites', '').lower() or
                        word in info.get('prerequisite', '').lower() or
                        word in info.get('benefits', '').lower()
                        for word in spell_word_list)}
    return feats

def remove_divine_feats(feats):
    spell_word_list = ['divine']
    feats = {name: info for name, info in feats.items()
            if not  any(word in name.lower() or
                        word in info.get('description', '').lower() or
                        word in info.get('prerequisites', '').lower() or
                        word in info.get('prerequisite', '').lower() or
                        word in info.get('benefits', '').lower()
                        for word in spell_word_list)}
    return feats


def dedupe_feats_case_insensitive(feats):
    """Order-preserving dedup keyed on lower().strip(). The general pool already avoids
    re-picking feats registered in character.chooseable, so this is a safety net for the
    same feat arriving from two sources with different casing/whitespace (ranger style vs
    main pool, hardcoded appends, ...). Also drops empty-string artifacts."""
    seen = set()
    out = []
    for f in feats:
        key = str(f).lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(f)
    return out


def capitalize_feats(character, chosen_feats):
    fillers = ["the", "of", "and", "a", "an", "in", "on", "at", "to", "for"]  # Add more as needed
    cleaned_chosen_feats = []
    for feats in chosen_feats:
        words = feats.split()
        capitalized_words = []
        for word in words:
            if '-' in word:
                parts = word.split('-')
                capitalized_parts = [part.capitalize() for part in parts]
                capitalized_words.append('-'.join(capitalized_parts))
            else:
                capitalized_words.append(word.capitalize() if word.lower() not in fillers else word)
        feat = ' '.join(capitalized_words)
        cleaned_chosen_feats.append(feat)
    return cleaned_chosen_feats


def bloodline_feat_chooser(character, c_class, bloodline_name, feat_amount):
    """Pick up to ``feat_amount`` bonus feats from this bloodline's own list.

    Each bloodline stores its bonus feats as a list holding one comma-joined
    string, e.g. ``["Combat Casting, Improved Disarm, ..."]``; a few entries omit
    the space after a comma (``"Steam Spell,Toughness"``) and some carry a
    parenthetical specialization (``"Skill Focus (Knowledge [dungeoneering])"``).
    We flatten + split on commas, strip the parenthetical so the base feat
    resolves in the pf1e compendium (Foundry matches the part before ``" ("``),
    dedupe, capitalize, then randomly sample. The sample is capped at the list
    size — you can't take more feats than the bloodline offers.
    """
    raw = getattr(character, c_class, {}).get('bloodline', {}).get(bloodline_name, {}).get('bonus feats', [])
    if not raw:
        return []
    # Flatten the one-element (comma-joined) list into individual feat names.
    joined = ','.join(raw) if isinstance(raw, list) else str(raw)
    feats = [f.strip() for f in joined.split(',') if f.strip()]
    feats = remove_duplicates_list(character, feats)
    # Drop trailing parenthetical specializations: "Skill Focus (Knowledge [...])" -> "Skill Focus".
    feats = [re.sub(r'\s*\(.*\)$', '', f).strip() for f in feats]
    feats = remove_duplicates_list(character, feats)
    feats = capitalize_feats(character, feats)
    return random.sample(feats, k=min(feat_amount, len(feats)))


def simple_list_chooser(character, class_1, *dataset_names, max_num=float('inf'), **kwargs):
    if class_entry_for(character, class_1.lower()) is not None:
        chosen = []
        chosen_dict = {}
        for dataset_name in dataset_names:
            dataset_input = getattr(data, dataset_name)
            dataset = character.json_list_grabber(dataset_input, ',', **kwargs)
            formula_calc = formula_grabber(character, dataset_name, **kwargs)
            if isinstance(dataset, dict):
                dataset = list(dataset.keys())
            # chosen.append(random.sample(dataset, k=min(formula_calc, max_num)))
            chosen_dict[dataset_name] = random.sample(dataset, k=min(formula_calc, max_num))
            # Merge like the other choosers (generic_func.py) — a straight assignment clobbers the
            # buckets earlier classes wrote (bloodline/hexes/...) on a multiclass roll.
            if character.data_dict['class features'] in ([], {}):
                character.data_dict['class features'] = chosen_dict
            else:
                character.data_dict['class features'].update(chosen_dict)
            record_bucket_owner(character, dataset_name, class_1.lower())
        return chosen

def formula_grabber(character, dataset_name):
    formula = getattr(data, 'formulas').get(dataset_name,1)
    amount = eval(formula)
    return amount  