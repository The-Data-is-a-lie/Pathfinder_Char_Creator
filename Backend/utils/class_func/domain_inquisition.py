import random

from utils.class_func.generic_func import class_entry_for, record_bucket_owner


def domain_chooser(character):
    chosen_dict = {}
    character.chosen_domain = []
    has_cleric = class_entry_for(character, 'cleric') is not None
    has_druid = class_entry_for(character, 'druid') is not None
    has_inquisitor = class_entry_for(character, 'inquisitor') is not None

    if has_cleric:
        deity_choice_list = list(character.deity_choice['Domains'])
        character.deity_choice_list = deity_choice_list
        character.chosen_domain = random.sample(deity_choice_list,k=2)
        chosen_first = character.chosen_domain[0].capitalize()
        chosen_second = character.chosen_domain[1].capitalize()
    # The druid's domain-vs-companion flip is owned by animal_companions.resolve_bonded_creatures,
    # which runs first and records its outcome. Reading `domain_chance` here as well would roll the
    # question twice: the resolver now draws per grantor row, so the two answers would agree only by
    # luck -- ~9% of druids would get both a companion and a domain, and ~9% neither. `domain_chance`
    # is left untouched for the inquisitor gate below, which is a separate question.
    if has_druid and getattr(character, 'bond_outcomes', {}).get('druid') == 'domain':

        druid_domains_list = list(character.druid_domains.keys())
        chosen_domain = random.choice(druid_domains_list)
        character.chosen_domain.append(chosen_domain)

    if has_inquisitor and not has_cleric and character.domain_chance > 90:

        deity_choice_list = list(character.deity_choice['Domains'])
        character.chosen_domain = random.sample(deity_choice_list,k=2)
        chosen_first = character.chosen_domain[0].capitalize()
        chosen_second = character.chosen_domain[1].capitalize()

    if len(character.chosen_domain) <= 0:
        return

    # Grabbing full domain info from their respetive domain lists (a multiclass cleric/druid can
    # have domains from both lists in chosen_domain, so only keep the hits from each lookup)
    if has_cleric or has_inquisitor:
        for d in character.chosen_domain:
            domain_info = character.cleric_domains.get("domains", {}).get(d.title(), None)
            if domain_info is not None:
                chosen_dict[d.title()] = domain_info
                record_bucket_owner(character, d.title(), 'cleric' if has_cleric else 'inquisitor')

    if has_druid:
        for d in character.chosen_domain:
            domain_info = character.druid_domains.get(d, None)
            if domain_info is not None:
                chosen_dict[d] = domain_info
                record_bucket_owner(character, d, 'druid')

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