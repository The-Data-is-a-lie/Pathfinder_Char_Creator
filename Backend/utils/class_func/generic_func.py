from utils import data
import random, re
from math import floor, ceil
# Start of Generic class options chooser
def generic_class_option_chooser(character, class_1,  dataset_name, dataset_name_2 = None, dataset_name_3 = None, multiple = None, level=None, level_2 = None):
    if character.c_class == class_1: 
        data_dict = {}
        if multiple != None:
            amount = getattr(data, 'amount', {}).get(character.c_class, {}).get(dataset_name, {})
            dataset = getattr(character, class_1, {}).get(dataset_name, {})
            dataset_list = list(dataset.keys())
            chosen_set = set()
            chosen_set_desc = []
            i = 0

            dataset_2 = getattr(character, class_1, {}).get(dataset_name_2, {})
            dataset_2_list = list(dataset_2.keys())
            # print(f'This is dataset {dataset}')    


            while amount[i] < character.c_class_level:
                if dataset_name_2 != None and character.c_class_level >= level:
                    dataset_list.extend(dataset_2_list)
                    dataset.update(dataset_2)

                if dataset_name_3 != None and character.c_class_level >= level_2:
                    dataset_list.extend(dataset_2_list)
                    dataset.update(dataset_2)                        

                chosen = random.choice(dataset_list)
                chosen_set.add(chosen)
                i = len(chosen_set)

            chosen_set_desc = {desc: dataset[desc] for desc in chosen_set}
            # character.full_data_dictionary(data_dict, chosen_set, chosen_set_desc)
            character.data_dict['class features'].append(chosen_set_desc)
                

            print(chosen_set_desc)
            return chosen_set, chosen_set_desc





        else:
            dataset = getattr(character, class_1, {}).get(dataset_name, {}).keys()
            choice = random.choice(list(dataset))
            description = getattr(character, class_1, {None}).get(dataset_name, {None}).get(choice,{None})

            chosen_desc = {choice: description}

            character.data_dict.update({'class features': chosen_desc})

            character.bonus_feats = character.bonus_searcher(choice, chosen_desc, 'feats')
            character.bonus_spells = character.bonus_searcher(choice, chosen_desc, 'spells')
            return chosen_desc
        

def chosen_set_append(character, dataset, chosen_set, chosen):
    chosen_dict = {}
    for chosen in chosen_set:
        chosen_desc = dataset.get(chosen, {})
        chosen_dict.update({chosen: chosen_desc})

    return chosen_dict            

# End of Generic Class Option Chooser


def get_data_without_prerequisites(self, class_1, dataset_name, level= None, level_2 = None, dataset_name_2 = None, odd=None):

    if self.c_class != class_1:
        return None

    dataset_no_prereq = []
    base_no_prereq = []
    add_advanced_talents = False
    amount = floor(self.c_class_level/2)
    chosen_set = set()

    if odd == True:
        amount = ceil(self.c_class_level/2)

    
    if self.c_class == class_1:
        dataset = getattr(self, class_1, {}).get(dataset_name, {})
        base = dataset.copy()
        base_no_prereq = self.no_prereq_loop(base)
        # print(base_no_prereq)
        total_choices = base_no_prereq

        if level != None and self.c_class_level >= level:
            dataset.update( getattr(self, class_1, {}).get(dataset_name_2,{}) )
            dataset_no_prereq = self.no_prereq_loop(dataset)            

    for i in range(amount):
        chosen = random.choice(total_choices)
        even = f"{class_1} {2 * (i + 1)}"
        odd = f"{class_1} {2 * i + 1}"
        self.chooseable.update([even, odd, chosen])

        prereq_list = self.no_prereq_loop(base, "prereq_list")

        chosen_set.add(chosen.lower())
        i = len(chosen_set)

        print(f'This is your chosen set {chosen_set}')
        
        total_choices.append(chosen.lower()) 
        total_choices.extend(prereq_list)
        total_choices = self.remove_duplicates_list(total_choices)
        total_choices=list(set(total_choices))
        print(f"These are all your options to choose from: {total_choices}")

        chosen_desc = {chosen: dataset.get(chosen, {})}

        if i>= 5 and self.c_class_level >= 10 and level == 10:
            add_advanced_talents = True
            total_choices.extend(dataset_no_prereq)                
            break
        

    chosen_dict = self.chosen_set_append(dataset, chosen_set, chosen)

    

    self.data_dict.update({'class features': chosen_dict})
    return base_no_prereq, dataset_no_prereq, chosen_set


def no_prereq_loop(self, dataset_type, return_choice=None):
    dataset_without_prerequisites = []
    prereq_list = set()
    # print(dataset_type.items())

    for name, info in dataset_type.items():
            prerequisites = str(info.get("prerequisites", "")).lower()
            # print(prerequisites)
            prerequisites = re.sub(r'\.', '', prerequisites)
            prerequisites_components = set(p.strip().lower() for p in prerequisites.split(","))
            # print(f'these are the components {prerequisites_components}')
            # removes both . and proficency

            if prerequisites_components.issubset(self.chooseable) == True:
                prereq_list.add(name.lower())
                # print(f'total prereq_list: {prereq_list}')

            if not prerequisites:
                dataset_without_prerequisites.append(name.lower())

    if return_choice == 'prereq_list':
        return prereq_list
    else:
        return dataset_without_prerequisites                

def generic_class_talent_chooser(self, class_1, dataset_name, dataset_name_2 = None):
    # Probably incorrect (the 2nd .get(dataset_name))
    if self.c_class == class_1: 
        dataset = getattr(self, class_1, {}).get(dataset_name, {}).keys()
        choice = random.choice(list(dataset)).get(dataset_name,{})
        description = getattr(self, class_1, {None}).get(dataset_name, {None}).get(choice,{None})

        print(choice)
        print(description)   

        return choice, description     


def remove_duplicates_list(self, input_list):
    seen = set()
    result = []
    for item in input_list:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def generic_multi_chooser(self, class_1, dataset_name, n, n2=None):
    if self.c_class == class_1:
        dataset = getattr(self, class_1, {}).get(dataset_name, {})
        dataset_list = []
        chosen_set = set()
        chosen_list = []
        chosen_set_desc = []
        i = 0

        level = self.c_class_level   
        ii = level // 3         

        while i < ii:
            # print(dataset)
            # print(dataset.keys())
            if n2 != None:
                level = (n // n2 * (i + 1))
                string_level = str(max(level,4))
            else:
                string_level = str((n * (i + 1)))

            dataset_list += dataset.get(string_level, [])
            print(f'This is your chooseable dataset {dataset_list}')
            chosen = random.choice(dataset_list)
            chosen_set.add(chosen)

            for condition, item in [('fatigued', 'exhausted'), ('shaken', 'frightened'),
                                    ('sickened', 'nauseated'), ('enfeebled', 'restorative'),
                                    ('injured', 'amputated')]:
                if condition not in chosen_set:
                    chosen_set.discard(item)

            print(chosen_set)
            i = min(len(chosen_set),ii)

        chosen_dict = {}
        pre_chosen_dict = self.chosen_set_muilt_append(dataset, chosen_set, chosen, dataset_name)
        chosen_dict.update({dataset_name: pre_chosen_dict})
        self.data_dict.update({'class features': chosen_dict})
        return chosen_dict  

def chosen_set_muilt_append(self, dataset, chosen_set, chosen, dataset_name):
    chosen_dict = {}
    for chosen in chosen_set:
        chosen_desc = self.get_description(chosen, dataset)
        chosen_dict.update({chosen: chosen_desc})
    return chosen_dict  

def get_description(self, key, dataset):
    for level_data in dataset.values():
        if key in level_data:
            return level_data[key]
    return None 