from Backend.utils import data
import random, re
from math import floor, ceil

# Start of Generic class options chooser
def generic_class_option_chooser(character, class_1,  dataset_name, dataset_name_2 = None, dataset_name_3 = None, multiple = None, level=None, level_2 = None, alternate_dataset = False, dict_name="Talents") :
    if character.c_class == class_1: 
        dataset = getattr(character, class_1, {}).get(dataset_name, {}).keys()
        from Backend.utils.class_func.feats import bonus_searcher

        if not multiple:
            choice = random.choice(list(dataset))
            description = getattr(character, class_1, {None}).get(dataset_name, {None}).get(choice,{None})


            character.data_dict['class features'].append({dict_name: {choice: description}})
            
            print("character.data_dict", character.data_dict)

            chosen_desc = {choice: description}
            character.bonus_feats = bonus_searcher(character, choice, chosen_desc, 'feats')
            character.bonus_spells = bonus_searcher(character, choice, chosen_desc, 'spells')
            return chosen_desc
        
        else:
            # Get amount
            amount = getattr(data, 'amount', {}).get(character.c_class, {}).get(dataset_name, {})

            # Start with base dataset
            dataset = getattr(character, class_1, {}).get(dataset_name, {})

            # Debugging print
            print(f"dataset_name_2: {dataset_name_2}, dataset_name_3: {dataset_name_3}, alternate_dataset: {alternate_dataset}")

            # If alternate_dataset is True, determine depth
            if alternate_dataset:
                if dataset_name_2 is None and dataset_name_3 is None:
                    print("1")
                elif dataset_name_2 and not dataset_name_3:
                    dataset = dataset.get(dataset_name_2, {})
                    print("2")
                elif dataset_name_3:
                    dataset = dataset.get(dataset_name_2, {}).get(dataset_name_3, {})
                    print("3")
                

            dataset_list = list(dataset.keys())
            # print("dataset_list", dataset_list)
            chosen_set = set()
            i = 0

            dataset_2 = getattr(character, class_1, {}).get(dataset_name_2, {})
            dataset_2_list = list(dataset_2.keys())

            print(len(amount))
            print(amount[i])
            while i < len(amount) and amount[i] <= character.c_class_level:
                if dataset_name_2 != None and character.c_class_level >= level and alternate_dataset == False:
                    dataset_list.extend(dataset_2_list)
                    dataset.update(dataset_2)

                chosen = random.choice(dataset_list)
                print(chosen)
                chosen_set.add(chosen)
                print(chosen_set)
                i = len(chosen_set)

            if len(chosen_set) <= 0:
                return []

            chosen_dict = chosen_set_append(character, dataset, chosen_set, chosen, dict_name)
            print("chosen_dict", chosen_dict)
            # character.data_dict['class features'] = chosen_dict 
            character.data_dict['class features'].append(chosen_dict)           
            return chosen_dict






        

def chosen_set_append(character, dataset, chosen_set, chosen, dict_name):
    chosen_dict = {dict_name: {}}
    for chosen in chosen_set:
        chosen_desc = dataset.get(chosen, {})
        chosen_dict[dict_name][chosen] = chosen_desc

    return chosen_dict            

# End of Generic Class Option Chooser


def get_data_without_prerequisites(character, class_1, dataset_name, level= None, level_2 = None, dataset_name_2 = None, odd=None, divisor = 2, dict_name="Talents"):

    if character.c_class != class_1:
        return None

    dataset_no_prereq = []
    base_no_prereq = []

    amount = floor(character.c_class_level/divisor)
    # fail safe to not break if any character with amount = 0 tries to use this
    if amount == 0:
        return None
    
    if odd == True:
        amount = ceil(character.c_class_level/divisor)

    if character.c_class == class_1:
        dataset = getattr(character, class_1, {}).get(dataset_name, {})
        base = dataset.copy()
        base_no_prereq = no_prereq_loop(character, base)
        total_choices = base_no_prereq

        if level != None and character.c_class_level >= level:
            print("this is occuring, the advanced talents portion")
            dataset.update( getattr(character, class_1, {}).get(dataset_name_2,{}) )
            dataset_no_prereq = no_prereq_loop(character, dataset)            

        print("dataset", dataset)
        
        chosen_set, chosen_desc, chosen_dict = choosing_talents(character, amount, class_1, dataset, dataset_no_prereq, base, level, total_choices, dict_name)
 
    # print("chosen_set", chosen_set)
    print("chosen_desc", chosen_desc)
    # print("chosen_dict", chosen_dict)

    if character.data_dict['class features'] == [] or character.data_dict['class features']== {}:
        character.data_dict['class features'] = chosen_dict
    else:
        character.data_dict['class features'].update(chosen_dict)
    return base_no_prereq, dataset_no_prereq, chosen_set

def choosing_talents(character, amount, class_1, dataset, dataset_no_prereq, base, level, total_choices, dict_name="Talents"):
    # added this logic so low level characters don't break
    if amount == None or amount <= 0:
        return [], [], []

    chosen_set = set()
    i = 0
    # ensure that all dict keys are lower:
    dataset = {k.lower(): v for k, v in dataset.items()}
    
    while i < amount:
    # for i in range(amount):
        chosen = random.choice(total_choices)
        even = f"{class_1} {2 * (i + 1)}"
        odd = f"{class_1} {2 * i + 1}"
        character.chooseable.update([even, odd, chosen])

        prereq_list = no_prereq_loop(character, base, "prereq_list")

        chosen_set.add(chosen.lower())
        i = len(chosen_set)

        total_choices.append(chosen.lower()) 
        total_choices.extend(prereq_list)
        total_choices = remove_duplicates_list(character, total_choices)
        total_choices=list(set(total_choices))

        print("post dataset", dataset)
        chosen_desc = {chosen: dataset.get(chosen, {})}
        print("ultimate chosen", chosen_desc)
        chosen_dict = chosen_set_append(character, dataset, chosen_set, chosen, dict_name)

    return chosen_set, chosen_desc, chosen_dict

def no_prereq_loop(character, dataset_type, return_choice=None):
    import pandas as pd

    dataset_without_prerequisites = []
    prereq_list = set()
    skipped_feats = []

    for name, info in dataset_type.items():
        # Retrieve prerequisites and sanitize input
        prerequisites = info.get("prerequisites", None)

        # Handle NaN or missing prerequisites
        if pd.isna(prerequisites) or not prerequisites or str(prerequisites).strip() == "":
            dataset_without_prerequisites.append(name.lower())
            print(f"[NO PREREQ] Added: {name}")
            continue

        try:
            # Clean up prerequisites
            prerequisites = str(prerequisites).lower()
            prerequisites = re.sub(r'\.', '', prerequisites)
            prerequisites_components = set(p.strip().lower() for p in prerequisites.split(","))

            # Special case: if the only component is "" (blank), treat as no prerequisite
            if prerequisites_components == {""}:
                dataset_without_prerequisites.append(name.lower())
                print(f"[NO PREREQ] (Blank) Added: {name}")
                continue

        except Exception as e:
            print("Error processing prerequisites:", e)
            print("Problematic prerequisites:", prerequisites)
            continue

        # Check if prerequisites are satisfied
        if prerequisites_components.issubset(character.chooseable):
            prereq_list.add(name.lower())
            print(f"[VALID PREREQ] Added: {name}")
        else:
            skipped_feats.append(name)

    print("\n[SKIPPED FEATS - Unmet Prerequisites]")
    for feat in skipped_feats:
        print(f"- {feat}")

    if return_choice == 'prereq_list':
        return prereq_list
    else:
        return dataset_without_prerequisites

def generic_class_talent_chooser(character, class_1, dataset_name, dataset_name_2 = None):
    if character.c_class == class_1: 
        dataset = getattr(character, class_1, {}).get(dataset_name, {}).keys()
        choice = random.choice(list(dataset)).get(dataset_name,{})
        description = getattr(character, class_1, {None}).get(dataset_name, {None}).get(choice,{None})

        print(choice)
        print(description)   

        return choice, description     


def remove_duplicates_list(character, input_list):
    seen = set()
    result = []
    for item in input_list:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def generic_multi_chooser(character, class_1, dataset_name,  n2=None, start_level = 1):
    if character.c_class != class_1:
        return None
    
    dataset = getattr(character, class_1, {}).get(dataset_name, {})
    dataset_list = []
    level = character.c_class_level

    divisor = n2 if isinstance(n2, int) else 3
    selection_count = max(floor((level - start_level) / divisor) + 1, 0) 
    chosen_set = set()

    i = 0
    while (i-1) < selection_count:
        effective_level = start_level + (i*divisor)
        if effective_level > level:
            break

        print(f"Effective level: {effective_level}")
        dataset_list += dataset.get(str(effective_level), [])

        print(dataset_list)

        # create weights to pick higher level abilities more:
        list_size = len(dataset_list)
        # exponentially increase weights [1,4,9,16,25 ...]
        weights = [(i + 1) ** 2 for i in range(list_size)]
        chosen = random.choices(dataset_list, weights=weights, k=1)[0]
        chosen_set.add(chosen)

        for condition, item in [('fatigued', 'exhausted'), ('shaken', 'frightened'),
                                ('sickened', 'nauseated'), ('enfeebled', 'restorative'),
                                ('injured', 'amputated')]:
            if condition not in chosen_set:
                chosen_set.discard(item)

        i = len(chosen_set)
        print("chosen set", chosen_set)

    # changing to a list, allows for it to be json serializable -> can export to foundryVTT
    # But, we want descriptions as well -> not just a list/set
    chosen_list = list(chosen_set)
    for item in chosen_list:
        description = dataset.get(item, {}).get('description', '')
        print(f"Item: {item}, Description: {description}")
    chosen_dict = chosen_set_muilt_append(character, dataset, chosen_set, chosen_list, dataset_name)

    # chosen_dict = {dataset_name: list(chosen_set)}
    if character.data_dict['class features'] == [] or character.data_dict['class features']== {}:
        character.data_dict['class features'] = chosen_dict
    else:
        character.data_dict['class features'].update(chosen_dict)
    return chosen_dict


def chosen_set_muilt_append(character, dataset, chosen_set, chosen, dataset_name):
    chosen_dict = {dataset_name: {}}
    for chosen in chosen_set:
        chosen_desc = get_description(character, chosen, dataset)
        # Store with benefit -> allows to act as an object in foundryVTT
        chosen_dict[dataset_name][chosen] = {"benefit": chosen_desc}

    return chosen_dict  

def get_description(character, key, dataset):
    for level_data in dataset.values():
        if key in level_data:
            return level_data[key]
    return None 