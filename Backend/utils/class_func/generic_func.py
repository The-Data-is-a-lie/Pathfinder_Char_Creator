from Backend.utils import data
import random, re
from math import floor, ceil

# Start of Generic class options chooser
def generic_class_option_chooser(character, class_1,  dataset_name, dataset_name_2 = None, dataset_name_3 = None, multiple = None, level=None, level_2 = None, alternate_dataset = False):
    if character.c_class == class_1: 
        dataset = getattr(character, class_1, {}).get(dataset_name, {}).keys()
        from Backend.utils.class_func.feats import bonus_searcher

        if not multiple:
            choice = random.choice(list(dataset))
            description = getattr(character, class_1, {None}).get(dataset_name, {None}).get(choice,{None})

            chosen_desc = {choice: description}
            if character.data_dict['class features'] == [] or character.data_dict['class features']== {}:
                character.data_dict['class features'] = chosen_desc
            else:
                character.data_dict['class features'].update(chosen_desc)

            character.bonus_feats = bonus_searcher(character, choice, chosen_desc, 'feats')
            character.bonus_spells = bonus_searcher(character, choice, chosen_desc, 'spells')
            return chosen_desc
        
        else:            
            amount = getattr(data, 'amount', {}).get(character.c_class, {}).get(dataset_name, {})
            dataset = getattr(character, class_1, {}).get(dataset_name, {})
            # Options for if we have a dataset 3 deep or 2 deep with alternate dataset
            if alternate_dataset == True and not (dataset_name_2 or dataset_name_3):
                dataset = getattr(character, class_1, {}).get(dataset_name, {})
                print("1")
            elif alternate_dataset == True and not dataset_name_3:
                dataset = getattr(character, class_1, {}).get(dataset_name, {}).get(dataset_name_2, {})
                print("2")
            elif alternate_dataset == True and not dataset_name_3:  
                dataset = getattr(character, class_1, {}).get(dataset_name, {}).get(dataset_name_2, {}).get(dataset_name_3, {})
                print("3")
            
            dataset_list = list(dataset.keys())
            print("dataset_list", dataset_list)
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

            
            chosen_set_desc = {desc: dataset[desc] for desc in chosen_set}
            if character.data_dict['class features'] == [] or character.data_dict['class features']== {}:
                character.data_dict['class features'] = chosen_set_desc
            else:
                character.data_dict['class features'].update(chosen_set_desc)

            return chosen_set, chosen_set_desc






        

def chosen_set_append(character, dataset, chosen_set, chosen):
    chosen_dict = {}
    for chosen in chosen_set:
        chosen_desc = dataset.get(chosen, {})
        chosen_dict.update({chosen: chosen_desc})

    return chosen_dict            

# End of Generic Class Option Chooser


def get_data_without_prerequisites(character, class_1, dataset_name, level= None, level_2 = None, dataset_name_2 = None, odd=None, divisor = 2):

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
        
        chosen_set, chosen_desc, chosen_dict = choosing_talents(character, amount, class_1, dataset, dataset_no_prereq, base, level, total_choices)
 
    # print("chosen_set", chosen_set)
    print("chosen_desc", chosen_desc)
    # print("chosen_dict", chosen_dict)

    if character.data_dict['class features'] == [] or character.data_dict['class features']== {}:
        character.data_dict['class features'] = chosen_dict
    else:
        character.data_dict['class features'].update(chosen_dict)
    return base_no_prereq, dataset_no_prereq, chosen_set

def choosing_talents(character, amount, class_1, dataset, dataset_no_prereq, base, level, total_choices):
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
        chosen_dict = chosen_set_append(character, dataset, chosen_set, chosen)

    return chosen_set, chosen_desc, chosen_dict

def no_prereq_loop(character, dataset_type, return_choice=None):
    dataset_without_prerequisites = []
    prereq_list = set()
    # print(dataset_type.items())

    for name, info in dataset_type.items():
            prerequisites = str(info.get("prerequisites", "")).lower()
            try:
                prerequisites = re.sub(r'\.', '', prerequisites)
                # print("prerequisites loop:", prerequisites)

                prerequisites_components = set(p.strip().lower() for p in prerequisites.split(","))
            except Exception as e:
                print("Error:", e)
                print("prerequisites:", prerequisites)

            if prerequisites_components.issubset(character.chooseable) == True:
                prereq_list.add(name.lower())

            if not prerequisites:
                dataset_without_prerequisites.append(name.lower())

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

    chosen_dict = {dataset_name: chosen_set}
    if character.data_dict['class features'] == [] or character.data_dict['class features']== {}:
        character.data_dict['class features'] = chosen_dict
    else:
        character.data_dict['class features'].update(chosen_dict)
    return chosen_dict


def chosen_set_muilt_append(character, dataset, chosen_set, chosen, dataset_name):
    chosen_dict = {}
    for chosen in chosen_set:
        chosen_desc = get_description(character, chosen, dataset)
        chosen_dict.update({chosen: chosen_desc})
    return chosen_dict  

def get_description(character, key, dataset):
    for level_data in dataset.values():
        if key in level_data:
            return level_data[key]
    return None 