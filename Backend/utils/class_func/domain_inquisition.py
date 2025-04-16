import random
def domain_chooser(character):
    chosen_dict = {}
    character.chosen_domain = []
    if character.c_class == 'cleric' or character.c_class_2 == 'cleric':  
        deity_choice_list = list(character.deity_choice['Domains'])
        character.deity_choice_list = deity_choice_list
        character.chosen_domain = random.sample(deity_choice_list,k=2)
        chosen_first = character.chosen_domain[0].capitalize()
        chosen_second = character.chosen_domain[1].capitalize()
    if (character.c_class == 'druid' or character.c_class_2 == 'druid' and character.domain_chance > 90):

        druid_domains_list = list(character.druid_domains.keys())
        chosen_domain = random.choice(druid_domains_list)
        character.chosen_domain.append(chosen_domain)

    if (character.c_class == 'inquisitor' or character.c_class_2 == 'inquisitor' and character.domain_chance > 90):

        deity_choice_list = list(character.deity_choice['Domains'])
        character.chosen_domain = random.sample(deity_choice_list,k=2)
        chosen_first = character.chosen_domain[0].capitalize()
        chosen_second = character.chosen_domain[1].capitalize()

    if len(character.chosen_domain) <= 0:
        return
    
    # Grabbing full domain info from their respetive domain lists
    if character.c_class == 'cleric':
        for d in character.chosen_domain:
            domain_info = character.cleric_domains.get("domains", {}).get(d, None)
            chosen_dict[d] = domain_info

    if character.c_class == 'druid':
        for d in character.chosen_domain:
            domain_info = character.druid_domains.get(d, None)
            chosen_dict[d] = domain_info

    # Adding to the base class features
    if character.data_dict['class features'] == [] or character.data_dict['class features']== {}:
        character.data_dict['class features'] = chosen_dict
    else:
        character.data_dict['class features'].update(chosen_dict)
    
    return character.chosen_domain    

def domain_chance(character):
    """
    Some druids choose a domain, some choose an animal companion. This decides which they do
    Some inquisitors go domains instead of inquisitions
    """
    #chance to get a domain vs an animal companion
    character.domain_chance = random.randint(1,100)
    return character.domain_chance