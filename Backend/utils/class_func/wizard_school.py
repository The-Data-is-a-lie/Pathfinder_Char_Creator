import random

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
        opposing_school = random.sample(school_list, k=2)

    return opposing_school


def wizard_school_chooser(character):
    if character.c_class == 'wizard':        
        chosen_dict = {}
    
        elemental_data = character.wizard_schools["elemental_schools"]
        schools_data = character.wizard_schools["schools"]
        elemental_subschools_data = character.wizard_schools["elemental_subschools"]
        subschools_data = character.wizard_schools["subschools"]

        associated_school = []
        associated = None

        random_choice = random.randint(1,4)


        if random_choice == 1:
            random_school = random.choice(list(elemental_data.keys()))
            description = elemental_data[random_school]

        elif random_choice == 2:            
            random_school = random.choice(list(elemental_subschools_data.keys()))
            description = elemental_subschools_data[random_school]
            associated = elemental_subschools_data[random_school]["associated school"][1]
            associated_school = elemental_data[associated]

        elif random_choice == 3:
            random_school = random.choice(list(schools_data.keys()))
            description = schools_data[random_school]

        else:
            random_school = random.choice(list(subschools_data.keys()))
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
        
        return random_school