import random

from utils.class_func.generic_func import record_bucket_owner
from utils.class_func import selection

def wizard_opposing_school(character, random_school):
    """
    wizards choose a school of magic (elemental/other). If elemental, it always as an opposing school. If not, we grab 2 random opposing schools

    Return
    - opposing_school
    """
    elemental_list = ['metal', 'void', 'earth', 'air', 'water', 'fire']
    i = 0    

    if random_school in elemental_list:
        elemental_opposing_schools = {'metal': 'wood', 'wood': 'metal', 'fire': 'water', 'water': 'fire', 'earth': 'air', 'air': 'earth'}
        opposing_school = elemental_opposing_schools.get(random_school, random.choice(elemental_list))
    else:
        school_list = (list(character.wizard_schools["schools"].keys()))
        school_list.remove('universalist')
        # SELECTION MODE (A7): pinned opposition schools ARE the wizard's opposition schools. A
        # wizard has two, so the first two pins take the slots and a single pin leaves the other
        # to the roll; the specialty itself (or its parent school) can never be one of them.
        pins = selection.school_pins(character)
        pinned = [s for s in ((pins or {}).get('opposition') or []) if s in school_list]
        if pinned:
            own = (pins or {}).get('specialty_school')
            pinned = [s for s in pinned if s != own][:2]
            spare = [s for s in school_list if s not in pinned and s != own]
            opposing_school = pinned + random.sample(spare, k=2 - len(pinned))
        else:
            opposing_school = random.sample(school_list, k=2)

    return opposing_school


def wizard_school_chooser(character):
    from utils.class_func.generic_func import class_entry_for
    if class_entry_for(character, 'wizard') is not None:
        chosen_dict = {}
    
        elemental_data = character.wizard_schools["elemental_schools"]
        schools_data = character.wizard_schools["schools"]
        elemental_subschools_data = character.wizard_schools["elemental_subschools"]
        subschools_data = character.wizard_schools["subschools"]

        associated_school = []
        associated = None

        # SELECTION MODE (A7): a pinned specialty names both the table and the school, so neither
        # is rolled. Unpinned, the two draws below are exactly the ones this has always made.
        pins = selection.school_pins(character)
        random_school = None
        if pins and pins['specialty']:
            random_choice, random_school = pins['specialty_table'], pins['specialty']
        else:
            random_choice = random.randint(1,4)


        if random_choice == 1:
            random_school = random_school or random.choice(list(elemental_data.keys()))
            description = elemental_data[random_school]

        elif random_choice == 2:
            random_school = random_school or random.choice(list(elemental_subschools_data.keys()))
            description = elemental_subschools_data[random_school]
            associated = elemental_subschools_data[random_school]["associated school"][1]
            associated_school = elemental_data[associated]

        elif random_choice == 3:
            random_school = random_school or random.choice(list(schools_data.keys()))
            description = schools_data[random_school]

        else:
            random_school = random_school or random.choice(list(subschools_data.keys()))
            description = subschools_data[random_school]
            associated = subschools_data[random_school]["associated school"]
            associated_school = schools_data[associated]            

        # print(f"random school: {random_school}")
        # print(f"description: {description}")
        # print(f"associated: {associated}")
        # print(f"associated school: {associated_school}")

        chosen_dict[random_school]      = description
        if associated != None and associated_school != []:
            chosen_dict[associated]  = associated_school
        # Adding to the base class features
        if character.data_dict['class features'] == [] or character.data_dict['class features']== {}:
            character.data_dict['class features'] = chosen_dict
        else:
            character.data_dict['class features'].update(chosen_dict)
        for bucket in chosen_dict:
            record_bucket_owner(character, bucket, 'wizard')
        
        return random_school