import re, random
import pandas as pd
from math import ceil, floor


# Importing custom functions
from Backend.utils.class_func.generic_func import *
from Backend.utils.class_func.chooseable import *



def print_metamagic(character):
    data = pd.read_csv(f'data/feats.csv', sep='|', on_bad_lines='skip')
    Metamagic_feats = data[data['type']=='Metamagic']
    extraction_list = ['name']        
    print(Metamagic_feats[extraction_list])

def feat_spell_searcher(character, class_1, chosen_set, types, info_column, info_column_2 = None):
    if character.c_class == class_1:
        data = pd.read_csv(f'data/{types}.csv', sep='|', on_bad_lines='skip')
    
        if info_column_2 is None:
            extraction_list = ['name', info_column]
        else:
            extraction_list = ['name', info_column, info_column_2]



        query_result = remove_mythic(character, types,data, chosen_set, extraction_list)

        result_dict = {}
        result_dict = remove_dots_dashes(character, result_dict, query_result, info_column)
        # print("this is your result dict", result_dict) 
        character.result_dict.update(result_dict)
        # print("this is your char result dict", character.result_dict)
        
        return character.result_dict         

def remove_mythic(character, types, data, chosen_set, extraction_list):
    

    chosen_set_upper = {i.upper() for i in chosen_set}
    print(f'This is your chosen set {chosen_set_upper}')

    if types == 'feats':
        query_result = data[(data['name'].str.upper().isin(chosen_set_upper)) & (data['type'] != 'Mythic')][extraction_list]
    else:
        query_result = data[(data['name'].str.upper().isin(chosen_set_upper)) & (data['mythic'] == 0)][extraction_list]  

    return query_result

def remove_dots_dashes(character, result_dict, query_result, info_column, info_column_2=None):
    replace_dash = lambda x: re.sub(r'[-]', ' ', str(x))            
    replace_dot = lambda x: re.sub(r'[.]', '', str(x))            

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
    print('bonus', bonus)
    print('bonus list', bonus_list)
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
    casting_level_str = character.classes[character.c_class]['casting level'].lower()
    specialty_set = {'cleric', 'druid'}
    type_chance = random.choices(range(1, 101))[0]
    feat_list = []
    if character.bab == 'H' or (character.bab == 'M' and casting_level_str not in ('low', 'mid', 'high')):
        add_martial_feats(character, feat_list)
    if character.bab == 'L' and casting_level_str != 'none':
        add_magical_feats(character, feat_list)
    if character.bab == 'M' and casting_level_str != 'none':
        if type_chance >= 50:
            add_martial_feats(character, feat_list)
        else:
            add_magical_feats(character, feat_list)
    if character.c_class in specialty_set:
        add_specialty_feats(character, feat_list)
    result_dict_pre = feat_spell_searcher(character, character.c_class, feat_list, "feats", "prerequisites", "description")
    result_dict = transform_result_dict(character, result_dict_pre)
    all_feats, _, build_selector_feats = get_feats_without_prerequisites(character, character.c_class, result_dict, character.feat_amounts)
    cleaned_chosen_feats = capitalize_feats(character, all_feats)
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

def add_specialty_feats(character, feat_list):
    classes_choices = list(character.feat_buckets['classes'][character.c_class])
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


def get_feats_without_prerequisites(character, class_1, dataset_name, level= None, level_2 = None, dataset_name_2 = None, odd=None, feat_amount=None):

    if character.c_class != class_1:
        return None

    dataset_no_prereq = []
    base_no_prereq = []
    add_advanced_talents = False
    amount = floor(character.c_class_level/2)
    chosen_set = set()

    if odd == True and amount == None:
        amount = ceil(character.c_class_level/2)
    else:
        amount = feat_amount
    

    
    dataset = dataset_name
    base = dataset.copy()
    base_no_prereq = no_prereq_loop(character, base)
    print(base_no_prereq)
    total_choices = base_no_prereq
    i = 0

    if amount == None:
        amount = 0

    while i < amount + 1:
        print(f'This is your total choices {total_choices}')
        chosen = random.choice(total_choices)

        chooseable_list_class(character,i,character.c_class,character.c_class_level, base=0, th='th')

        prereq_list = no_prereq_loop(character, base, "prereq_list")

        chosen_set.add(chosen.lower())
        i = len(chosen_set)
        
        total_choices.append(chosen.lower()) 
        total_choices.extend(prereq_list)
        total_choices = remove_duplicates_list(character, total_choices)
        total_choices=list(set(total_choices))
        # print(f"this is total choices {total_choices}")
        # print(f'this is your chosen {chosen}')
        # print(f'This is your chosen set {chosen_set}')
        # print(f"These are all your options to choose from: {total_choices}")
        # print(f"this is your len {len(chosen_set)}")
        # print(f"this is your i {i}")
        # print(f"this is your amount {amount}")

        character.chooseable.add(chosen)

    return base_no_prereq, dataset_no_prereq, chosen_set


def generic_feat_chooser(character, class_1,feat_type, info_column):
    if class_1 == character.c_class:
        feat_data = pd.read_csv(f'data/feats.csv', sep='|', on_bad_lines='skip')
        extraction_list = ['name', 'prerequisites', 'description']
        query_i = feat_data.loc[(feat_data['type'] == feat_type.capitalize()) | (feat_data['type'] == 'General'), extraction_list]
        query_i = query_i.drop_duplicates(subset='name', keep='first')
        feat_result_dict = query_i.set_index('name')[['prerequisites', 'description']].to_dict(orient='index')
        # feat_result_dict = character.remove_mythic('feats',feat_data,query_i, info_column)   
        # feat_result_dict = character.remove_dots_dashes(feat_result_dict, query_i, info_column)
        feat_result_dict = transform_result_dict(character, feat_result_dict)

        feat_result_dict.update(feat_result_dict)

        # print(f' post transform result_dict {feat_result_dict}')
        _, _, chosen_feats = get_feats_without_prerequisites(character, character.c_class, feat_result_dict, feat_amount= character.feat_amounts)
        chosen_feats = list(chosen_feats)
        chosen_feats.remove("")
        cleaned_chosen_feats = capitalize_feats(character, chosen_feats)
        character.chosen_feats = cleaned_chosen_feats
        print(f'These are your chosen feats {cleaned_chosen_feats}')

        return cleaned_chosen_feats
    
def capitalize_feats(character, chosen_feats):
    fillers = ["the", "of", "and", "a", "an", "in", "on", "at", "to", "for"]  # Add more as needed
    cleaned_chosen_feats = []
    for feats in chosen_feats:
        words = feats.split()
        capitalized_words = []
        for word in words:
            if '-' in word:
                parts = word.split('-')
                print("these are the parts " + str(parts))
                capitalized_parts = [part.capitalize() for part in parts]
                capitalized_words.append('-'.join(capitalized_parts))
            else:
                capitalized_words.append(word.capitalize() if word.lower() not in fillers else word)
        feat = ' '.join(capitalized_words)
        cleaned_chosen_feats.append(feat)
    return cleaned_chosen_feats




def simple_list_chooser(character, class_1, *dataset_names, max_num=float('inf'), **kwargs):
    if character.c_class.lower() == class_1.lower():
        chosen = []
        chosen_dict = {}
        for dataset_name in dataset_names:
            dataset_input = getattr(data, dataset_name)
            dataset = character.json_list_grabber(dataset_input, ',', **kwargs)
            print(f"This is your dataset for {dataset_name}: {dataset}")
            formula_calc = formula_grabber(character, dataset_name, **kwargs)
            if isinstance(dataset, dict):
                dataset = list(dataset.keys())
            # chosen.append(random.sample(dataset, k=min(formula_calc, max_num)))
            chosen_dict[dataset_name] = random.sample(dataset, k=min(formula_calc, max_num))
            character.data_dict.update({'class features': chosen_dict})
        print(chosen)
        return chosen

def formula_grabber(character, dataset_name):
    formula = getattr(data, 'formulas').get(dataset_name,1)
    print(f'this is your formula {formula}')
    amount = eval(formula)
    return amount  