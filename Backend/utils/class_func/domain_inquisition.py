import random
def domain_chooser(character):
    character.chosen_domain = []
    if character.c_class == 'cleric' or character.c_class_2 == 'cleric':  
        deity_choice_list = list(character.deity_choice['Domains'])
        character.chosen_domain = random.sample(deity_choice_list,k=2)
        chosen_first = character.chosen_domain[0].capitalize()
        chosen_second = character.chosen_domain[1].capitalize()
#            this is randomly selecting from all without regard to Deity
#            character.chosen_domain =  random.choice(list(character.cleric_domains["domains"].keys()))
        print(f'This is your first selected domain {character.chosen_domain[0]} + its info: \n{character.cleric_domains["domains"][chosen_first]}')
        print(f'This is your second selected domain {character.chosen_domain[1]} + its info: \n{character.cleric_domains["domains"][chosen_second]}')  

    if (character.c_class == 'druid' or character.c_class_2 == 'druid' and character.domain_chance > 90):

        druid_domains_list = list(character.druid_domains.keys())
        chosen_domain = random.choice(druid_domains_list)
        print(chosen_domain)
        print(character.druid_domains[chosen_domain])
        character.chosen_domain.append(chosen_domain)

    if (character.c_class == 'inquisitor' or character.c_class_2 == 'inquisitor' and character.domain_chance > 90):

        deity_choice_list = list(character.deity_choice['Domains'])
        character.chosen_domain = random.sample(deity_choice_list,k=2)
        chosen_first = character.chosen_domain[0].capitalize()
        chosen_second = character.chosen_domain[1].capitalize()
        print(f'This is your first selected domain {character.chosen_domain[0]} + its info: \n{character.cleric_domains["domains"][chosen_first]}')
        print(f'This is your second selected domain {character.chosen_domain[1]} + its info: \n{character.cleric_domains["domains"][chosen_second]}')  

        return character.chosen_domain    


def inquisition_chooser(character):
    if character.c_class == 'inquisitor' or character.c_class_2 == 'inquisitor' and character.domain_chance <= 90:
        inquisitions = character.inquisitions.get("inquisitions", {})
        chosen_deity = character.deity_choice['Name'][0].lower()

        print(f'this is your chosen deity!!!!! {chosen_deity}')

        valid_inquisitions = {
            inq: data for inq, data in inquisitions.items() if chosen_deity in data.get("deities", "")
        }

        if not valid_inquisitions:
            character.domain_chance = 100
            character.domain_chooser()

        else:
            character.inquisition_choice = random.sample(list(valid_inquisitions), k=2)
            print(character.inquisition_choice)

            return character.inquisition_choice
        


def domain_chance(character):
    """
    Some druids choose a domain, some choose an animal companion. This decides which they do
    Some inquisitors go domains instead of inquisitions
    """
    #chance to get a domain vs an animal companion
    character.domain_chance = random.randint(1,100)
    return character.domain_chance