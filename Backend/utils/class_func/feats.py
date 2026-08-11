import json, re, random
import pandas as pd
from math import ceil, floor


# Importing custom functions
from utils.class_func.generic_func import *
from utils.class_func.chooseable import *
from utils.class_func.skill_ranks import homebrew_enabled
from utils.class_func import luck
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
    # A chosen option is usually a dict of sub-keys ('bonus feats', 'bonus spells', ...), but it can
    # equally be a plain description string -- every psionics subsystem is shaped that way, and so
    # is every multiple-pick bucket. A string simply has no bonuses to search.
    entry = chosen_desc.get(choice, {})
    if not isinstance(entry, dict):
        return bonus_list
    bonus = entry.get(f"bonus {types}", {})
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


# E-Kat feats (oks/pathfinder/house-rules/luck.md), behind the SAME homebrew flag as the Metzofitz
# library. They are deliberately NOT concatenated into the generic pool, for two reasons:
#   * they are not General/Combat feats -- data/feats_new.csv types them 'E-Kat', and nothing in the
#     runtime reads that file at all, which is why they have never been reachable;
#   * no_prereq_loop appends every eligible name to character.chooseable_talents, a SHARED
#     accumulator later choosers draw from. Feeding E-Kats through it would leak them into every
#     subsequent generic draw, which is exactly what the reserved-slot design exists to avoid.
# So they get their own pool, their own chooser, and slots carved out of the feat budget.
_E_KAT_LOCATION = 'Backend/json/feats/e_kat_feats.json'
_E_KAT_CACHE = None


def e_kat_feat_table():
    """The curated 10, keyed by canonical name. Cached like the feat CSVs -- static during a run."""
    global _E_KAT_CACHE
    if _E_KAT_CACHE is None:
        raw = json.loads(repo_path(_E_KAT_LOCATION).read_text(encoding='utf-8'))
        _E_KAT_CACHE = {k: v for k, v in raw.items() if not k.startswith('_')}
    return _E_KAT_CACHE


def e_kat_description(name):
    """Rules text for an E-Kat feat (case-insensitive); '' when unknown. Same role as
    metzofitz_description -- these feats are absent from data/feats.csv, and a nameless description
    would make the Foundry module synthesize an empty row."""
    for feat_name, info in e_kat_feat_table().items():
        if feat_name.lower() == str(name).lower():
            return info.get('benefit', '')
    return ''


def e_kat_feat_chooser(character, amount):
    """Pick up to `amount` E-Kat feats, honouring the chains.

    Prerequisites here are a structured LIST of exact feat names, not the comma-joined string the
    generic engine parses -- which is what lets 'Luck God' name the nine feats it requires instead of
    the literal 'All of the above' in the CSV, a phrase no string engine can ever resolve.

    Picks register in character.chooseable (lowercased, as the generic chooser does) so no later pass
    re-picks one, but never touch chooseable_talents, so nothing leaks back into the generic pool.
    """
    if not amount or amount <= 0:
        return []
    pool = e_kat_feat_table()
    picked = []
    for _ in range(amount):
        eligible = [
            name for name, info in pool.items()
            if name.lower() not in character.chooseable
            and all(p.lower() in character.chooseable for p in info['prerequisites'])
        ]
        if not eligible:
            break
        # A chain continuation is any feat with prerequisites -- by construction its prereqs are
        # already owned, so it finishes something the character started.
        continuations = [n for n in eligible if pool[n]['prerequisites']]
        if continuations and random.random() < luck.E_KAT_CHAIN_BIAS:
            eligible = continuations
        chosen = random.choice(sorted(eligible))
        picked.append(chosen)
        character.chooseable.add(chosen.lower())
    return picked


# The E-Kat spend table, rendered onto the sheet rather than applied. Everything in it except the
# 25-E-Kat Luck Trait purchase is an in-play action the GM adjudicates; the generator's job is to
# put it in front of the player next to the reserve it bought them.
_E_KAT_EXCHANGE_LOCATION = 'Backend/json/feats/e_kat_exchange.json'
_E_KAT_EXCHANGE_CACHE = None

# TESTING AID (2026-08-08): list the whole 10-feat E-Kat roster in the E-Kat Exchange section,
# marking which ones this character actually holds, so all ten can be checked on a single sheet.
# Set to False to show a character only what it has. This is a display switch -- it changes nothing
# about what the character IS, and no gate depends on it.
LIST_ALL_E_KAT_FEATS = True


def e_kat_exchange_rows():
    global _E_KAT_EXCHANGE_CACHE
    if _E_KAT_EXCHANGE_CACHE is None:
        raw = json.loads(repo_path(_E_KAT_EXCHANGE_LOCATION).read_text(encoding='utf-8'))
        _E_KAT_EXCHANGE_CACHE = raw['rows']
    return _E_KAT_EXCHANGE_CACHE


def luck_sheet_sections(luck_block):
    """Class-feature sections for the sheet: what the reserve buys, and what it already bought.

    Returned as ``{section_name: {sub_label: text}}`` -- the shape ``data_dict['class features']``
    already uses -- so the caller can splice them in without the sheet needing to learn anything new.

    Shown only to characters actually in the E-Kat economy (a luck stake, an E-Kat feat, a carried
    E-Kat, or a purchased trait). A nine-row reference table on every NPC in the game would be
    clutter, and three quarters of them have no luck at all.
    """
    if not luck_block:
        return {}
    in_economy = (luck_block.get('stake') or luck_block.get('feats')
                  or luck_block.get('e_kat_reserve') or luck_block.get('traits'))
    if not in_economy:
        return {}

    sections = {}
    # Grouped, not one flat list: the section carries three different KINDS of thing -- what you
    # have, what you took, and what you can do with it -- and running them together made a
    # twenty-row wall. The module renders a nested dict as a sub-heading plus its own list.
    reserve = {
        'Your reserve': (
            f"{luck_block['e_kat_reserve']} E-Kat(s) carried into play, of "
            f"{luck_block['e_kat_earned']} earned at creation "
            f"({len(luck_block['traits'])} spent on Luck Traits at "
            f"{luck.LUCK_TRAIT_COST} each). Storage cap {luck_block['e_kat_store_cap']}."),
    }

    # The E-Kat feat roster, split by what the character ACTUALLY holds.
    #
    # "Feats Taken" once listed all ten with a "[HELD]" / "[not taken]" marker buried in the value.
    # The marker was accurate and the heading was a lie -- a sheet showing "Feats Taken: Luck God"
    # for a character without Luck God is worse than showing nothing, because it reads as true at a
    # glance. The two are separate groups now, and only the held one carries that name.
    #
    # LIST_ALL_E_KAT_FEATS is a TESTING switch: it adds the untaken remainder as a clearly-labelled
    # reference group. Off, a sheet shows only what the character has.
    held = {n.lower() for n in luck_block.get('feats', [])}

    def _row(info):
        effects = info['effects']
        gain = effects['luck_bonus'] or (luck.GENERIC_LUCK_FEAT_BONUS
                                         if effects['grants_generic_luck'] else 0)
        return f"[+{gain} Luck] {info['benefit']}"

    taken, untaken = {}, {}
    for name, info in e_kat_feat_table().items():
        target = taken if name.lower() in held else untaken
        target[f"Feat: {name}"] = _row(info)

    # The base spend table, plus a note when a held feat CHANGES it. The nine rows are static text:
    # they say "2 E-Kats" and "+1 on any roll" regardless of Luck God halving every cost or Very
    # Lucky Boy tripling the bonus, so a sheet that shows only the table is quietly wrong for
    # exactly the characters who invested most.
    actions = {}
    table = e_kat_feat_table()
    modifiers = []
    if any(table[n]['effects']['halves_e_kat_costs'] for n in luck_block.get('feats', [])):
        modifiers.append('every E-Kat cost below is HALVED (Luck God), except the 99 tier and Luck Traits')
    _mult = max([table[n]['effects']['roll_bonus_multiplier']
                 for n in luck_block.get('feats', [])] or [1])
    if _mult > 1:
        modifiers.append(f"roll-based E-Kat bonuses are multiplied by {_mult} "
                         f"({'Very Lucky Boy' if _mult >= 3 else 'Lucky Boy'})")
    if any(table[n]['effects']['doubles_acquisition'] for n in luck_block.get('feats', [])):
        modifiers.append('permanent E-Kat acquisition is doubled (Double Down)')
    if modifiers:
        # Upper-case the first letter only -- str.capitalize() lower-cases everything after it, which
        # turned "Very Lucky Boy" and "E-Kat" into "very lucky boy" and "e-kat".
        _mods = '; '.join(modifiers)
        actions['Active modifiers'] = _mods[0].upper() + _mods[1:] + '.'
    actions.update({row['label']: row['text'] for row in e_kat_exchange_rows()})

    # Actions unlocked by PURCHASED Luck Traits. The "E-Kat Exchange: ..." traits are exactly that --
    # each buys the right to a new action with its own per-use cost -- so they belong beside the
    # base table rather than buried among the passive traits.
    trait_table = luck_trait_table()
    purchased_actions = {}
    for name in dict.fromkeys(luck_block.get('traits', [])):
        if not name.startswith('E-Kat Exchange:'):
            continue
        count = luck_block['traits'].count(name)
        label = name.split('E-Kat Exchange:', 1)[1].strip()
        info = trait_table[name]
        # Name the prerequisite on the row: these chain (Loot Box -> Premium -> Deluxe), and a
        # sheet listing the action without its gate reads as if anyone could buy it.
        prereq = info.get('prerequisites') or []
        gate = ''
        if prereq:
            _names = ', '.join(x.split('E-Kat Exchange:', 1)[-1].strip() for x in prereq)
            gate = f' [requires {_names}]'
        _key = f"{label} (x{count})" if count > 1 else label
        purchased_actions[_key] = f"{info['benefit']}{gate}"

    exchange = {'Reserve': reserve}
    if taken:
        exchange['Feats Taken'] = taken
    if untaken and LIST_ALL_E_KAT_FEATS:
        exchange['Feats Not Taken (reference)'] = untaken
    exchange['Actions'] = actions
    if purchased_actions:
        exchange['Actions (Purchased)'] = purchased_actions
    sections['E-Kat Exchange'] = exchange

    # Purchased Luck Traits are NOT listed here. They render as "(E-kat Trait) X" items on the
    # Traits tab (module: build/feats.js), matching the hand-built reference sheet -- and a real
    # item can carry pf1 changes later, which a text block never could. The block exports
    # `trait_benefits` so the module has the rules text without duplicating the 34-trait table.
    return sections


# Positive luck-based feats that are NOT E-Kat feats -- hero point feats and the luck-subject feats
# -- which still grant the generic +1 Luck. Unlike the E-Kat feats these are ordinary Paizo rows in
# data/feats.csv, already in the generic pool, so nothing needs to reach them; they only need to be
# RECOGNISED. No column marks them (every one is typed General), so the roster is curated.
_LUCK_FEAT_LOCATION = 'Backend/json/feats/luck_feats.json'
_LUCK_FEAT_CACHE = None


def luck_feat_table():
    global _LUCK_FEAT_CACHE
    if _LUCK_FEAT_CACHE is None:
        raw = json.loads(repo_path(_LUCK_FEAT_LOCATION).read_text(encoding='utf-8'))
        _LUCK_FEAT_CACHE = {k: v for k, v in raw.items() if not k.startswith('_')}
    return _LUCK_FEAT_CACHE


def held_luck_feats(feat_names):
    """The non-E-Kat luck feats a character holds, matched case-insensitively and deduped.

    Case-insensitive because these names travel through capitalize_feats and the feat-tax passes;
    'Blood Of Heroes' and 'Blood of Heroes' are the same feat and must not count twice.
    """
    table = luck_feat_table()
    canonical = {name.lower(): name for name in table}
    return list(dict.fromkeys(
        canonical[str(f).lower()] for f in (feat_names or []) if str(f).lower() in canonical))


# Luck Traits are NOT feats and NOT character traits -- "Luck Traits may only be purchased with
# E-Kats" -- but they load like the E-Kat feat table and are chosen by the same kind of curated
# picker, so they live next to it rather than in traits.py (whose pool they must never enter).
_LUCK_TRAIT_LOCATION = 'Backend/json/feats/luck_traits.json'
_LUCK_TRAIT_CACHE = None


def luck_trait_table():
    """The curated 34, keyed by canonical name. Cached like the feat tables."""
    global _LUCK_TRAIT_CACHE
    if _LUCK_TRAIT_CACHE is None:
        raw = json.loads(repo_path(_LUCK_TRAIT_LOCATION).read_text(encoding='utf-8'))
        _LUCK_TRAIT_CACHE = {k: v for k, v in raw.items() if not k.startswith('_')}
    return _LUCK_TRAIT_CACHE


def luck_trait_description(name):
    """Benefit text for a purchased Luck Trait (case-insensitive); '' when unknown."""
    for trait_name, info in luck_trait_table().items():
        if trait_name.lower() == str(name).lower():
            return info.get('benefit', '')
    return ''


def eligible_luck_traits(luck_type, score):
    """Which traits this character may buy at all, before prerequisites between traits.

    Two gates:
      * CATEGORY -- dimorphic traits are written in terms of Twist of Fate and the Vault, negative
        traits in terms of a negative score. A character that has neither cannot use them.
      * SCORE THRESHOLD -- "(Prerequisites : -25 luck)". A floor on how negative the score must be,
        so a character at -10 cannot take a trait that wants -25.
    """
    allowed = {luck.TRAIT_CATEGORY_STANDARD}
    if luck_type == 'Dimorphic':
        allowed.add(luck.TRAIT_CATEGORY_DIMORPHIC)
    if score < 0:
        allowed.add(luck.TRAIT_CATEGORY_NEGATIVE)
    out = {}
    for name, info in luck_trait_table().items():
        if info['category'] not in allowed:
            continue
        floor = info.get('requires_luck_at_most')
        if floor is not None and score > floor:
            continue
        out[name] = info
    return out


def luck_trait_chooser(amount, luck_type, score, luck_feat_count=0):
    """Buy `amount` Luck Traits, preferring variety.

    Prerequisites are enforced in all three forms the Doc uses -- another trait, a luck-score floor
    (via eligible_luck_traits), and Inevitable's per-stack count of luck feats and traits. Without
    this a character could buy Deluxe Loot Box having never bought Loot Box.

    Distinct traits are drawn first; a Repeatable trait is only taken a second time once every
    eligible one is already held. At realistic reserves (two to four traits) a repeat never happens
    -- the branch exists for the 40th-level Dimorphic outlier that can afford a dozen, where the
    alternative is a character holding Increase Luck sixteen times.

    Returns a list in purchase order, so duplicates sit adjacent and the sheet reads as stacks.
    """
    if not amount or amount <= 0:
        return []
    pool = eligible_luck_traits(luck_type, score)
    if not pool:
        return []

    def _legal(name, held, assets):
        info = pool[name]
        # (a) another TRAIT: the Loot Box chain, and Never-Ending Suffering <- Trauma Survivor.
        if any(p not in held for p in info.get('prerequisites', [])):
            return False
        # (b) a COUNT that scales with the stack: Inevitable wants 10 luck feats/traits per copy,
        # so a second one needs 20. `assets` already includes everything bought so far.
        per_stack = info.get('requires_luck_assets_per_stack')
        if per_stack and assets < per_stack * (held.count(name) + 1):
            return False
        return True

    bought = []
    for _ in range(amount):
        assets = luck_feat_count + len(bought)
        legal = [n for n in pool if _legal(n, bought, assets)]
        unheld = sorted(n for n in legal if n not in bought)
        if unheld:
            bought.append(random.choice(unheld))
            continue
        repeatable = sorted(n for n in legal if pool[n]['repeatable'])
        if not repeatable:
            break                      # nothing legal left that may stack
        bought.append(random.choice(repeatable))
    return bought


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
    """Ranger favoured terrains/enemies and brawler maneuvers: pick N from a flat data.py list.

    THE FOURTH PICK-COUNT CONVENTION, and the one ticket 01 never saw. The count used to come from
    `data.formulas` -- eval'd strings like 'ceil((character.c_class_level - 2) / 5)' -- which is why
    reading the three known chooser call sites did not find it. Ticket 02's sweep found it by
    generating a character for all 68 classes and asking which buckets landed.

    Migrating it to levels_for() fixed a MULTICLASS BUG for free: `c_class_level` is an alias of the
    PRIMARY class's level (createACharacter.py:94), so a rogue 16 / ranger 4 sized its favoured
    enemies off the rogue's 16. The schedule is per-class and reads this class's own entry, which is
    the property ticket 01 ruling 3 exists to protect.

    These buckets hold a LIST, not the {choice: description} dict every other bucket holds, and they
    record no level stamp (hence `stamps: false` on their rows). Both are ticket 04's to rule on.
    """
    class_entry = class_entry_for(character, class_1.lower())
    if class_entry is not None:
        chosen = []
        chosen_dict = {}
        for dataset_name in dataset_names:
            dataset_input = getattr(data, dataset_name)
            dataset = character.json_list_grabber(dataset_input, ',', **kwargs)
            levels = levels_for(character, class_1.lower(), dataset_name, class_entry['level'])
            if isinstance(dataset, dict):
                dataset = list(dataset.keys())
            # min() against the pool too: random.sample raises when k exceeds the population, and
            # nothing caps these counts at 20th any more.
            chosen_dict[dataset_name] = random.sample(
                dataset, k=min(len(levels), max_num, len(dataset)))
            # Merge like the other choosers (generic_func.py) — a straight assignment clobbers the
            # buckets earlier classes wrote (bloodline/hexes/...) on a multiclass roll.
            if character.data_dict['class features'] in ([], {}):
                character.data_dict['class features'] = chosen_dict
            else:
                character.data_dict['class features'].update(chosen_dict)
            record_bucket_owner(character, dataset_name, class_1.lower())
        return chosen