import pandas as pd
import re
# from utils.class_func.feats import feat_spell_searcher

def feat_tax_func(character, feats):
    ''' search for all feats, then add them into the total feats chosen list, then select feats again at the very end
    while accounting for the taxed feats.
    '''
    feat_taxed_dict = {}
    eligible_feat_taxed_list = []
    pre_eligible_feat_taxed_list = []
    eliblibility_req_dict = {}
    feat_desc_dict = {}

    total_feat_tax_dict = character.feat_tax
    feat_tax_data = total_feat_tax_dict.get("feat_tax", {})

    for feat in feats:
        if feat in feat_tax_data:
            feat_taxed_dict[feat] = list(feat_tax_data[feat].values())
            pre_eligible_feat_taxed_list = list(feat_tax_data[feat].values())

    for feat in pre_eligible_feat_taxed_list:
        eliblibility_req_dict = feat_spell_searcher(character, character.c_class, pre_eligible_feat_taxed_list, "feats", "prerequisites", "description", feat_desc_dict)

    # confirm eligible feats 
    eligible_feat_taxed_list = confirm_eligible(character, eliblibility_req_dict, eligible_feat_taxed_list)
    print("Eligible feats after confirmation:", eligible_feat_taxed_list)

    print("PRE", feat_taxed_dict)
    remove_untaxed_feats(feat_taxed_dict, eligible_feat_taxed_list)
    print("POST", feat_taxed_dict)

    return feat_taxed_dict


def remove_untaxed_feats(feat_taxed_dict, eligible_feat_taxed_list):
    ''' remove feats that are not in the eligible_feat_taxed_list from feat_taxed_dict '''
    for feat, taxed_feats in feat_taxed_dict.items():
        filtered_feats = []
        for taxed_feat in taxed_feats:
            if taxed_feat not in eligible_feat_taxed_list:
                print("not eligible:", taxed_feat)
                continue
            filtered_feats.append(taxed_feat)
        feat_taxed_dict[feat] = filtered_feats

    # remove empty lists
    keys_to_delete = []

    for feat, taxed_feats in feat_taxed_dict.items():
        if not taxed_feats:
            keys_to_delete.append(feat)

    for key in keys_to_delete:
        print("Removing key with no taxed feats:", key)
        del feat_taxed_dict[key]

    return feat_taxed_dict

def confirm_eligible(character, feat_taxed_dict, eligible_feat_taxed_list):
    '''a quick and dirty no_prereq_loop method'''
    for name, info in feat_taxed_dict.items():
        print("name, info:", name, info)
        name_lower = name.lower()
        if name_lower in character.chooseable:
            continue

        prerequisites_clean = determine_prerequisite_name(info)

        # Split by comma and strip each part
        prereq_parts = [
            part.strip() for part in prerequisites_clean.split(",")
            if part.strip() and not character.filter_pattern.search(part.strip())
        ]


        # Check if all prereqs are met
        if not prereq_parts or set(prereq_parts).issubset(character.chooseable):
            eligible_feat_taxed_list.append(name_lower)
            
    return eligible_feat_taxed_list

def determine_prerequisite_name(info):
    prerequisites_raw = info.get("prerequisites", "").lower().strip()
    if not prerequisites_raw:
        prerequisites_raw = info.get("prerequisite", "").lower().strip()

    return re.sub(r'\.', '', prerequisites_raw)


def print_taxable_feats(character, feat_taxed_dict):
    taxable_names = []
    feat_data = pd.read_csv(f'{"data/feats.csv"}', sep='|', on_bad_lines='skip')
    feat_names_data = feat_data['name'].tolist()

    for n in feat_names_data:
        if any(keyword in n.lower() for keyword in ("greater", "improved", "extra")):
            taxable_names.append(n)
    print("taxable_names:", taxable_names)






# reused custom functions
def feat_spell_searcher(character, class_1, chosen_set, types, info_column, info_column_2 = None, feat_desc_dict=None):
    if chosen_set == None:
        return
    if character.c_class == class_1:
        data = pd.read_csv(f'data/{types}.csv', sep='|', on_bad_lines='skip')
    
        if info_column_2 is None:
            extraction_list = ['name', info_column]
        else:
            extraction_list = ['name', info_column, info_column_2]


        query_result = remove_mythic(character, types,data, chosen_set, extraction_list)

        result_dict = {}
        result_dict = remove_dots_dashes(character, result_dict, query_result, info_column)
        feat_desc_dict.update(result_dict)

        return feat_desc_dict

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