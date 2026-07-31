import random

from utils.class_func.generic_func import class_entry_for


def animal_chooser(character):
    """
    if class = druid
    chooses between a plant, vermin, or normal animal companion for a druid
    prints out animal companion info after decidibg which companion to pick
    """
    druid_entry = class_entry_for(character, 'druid')
    if druid_entry is not None and character.domain_chance <= 90:
        random_animal = random.randint(1,100)
        # give all druids carry companion
        # or make it a subset of companions and make them based on region
        normal = list(character.animal_choices["normal"].keys())
        vermin = list(character.animal_choices["vermin"].keys())
        plant =list(character.animal_choices["plant"].keys())
        level = str(druid_entry['level'])


        if random_animal <= 80:
            character.chosen_animal = random.choice(normal)
            character.chosen_animal_kind = "normal"
            character.chosen_animal_description = character.animal_choices["normal"][character.chosen_animal]
        elif random_animal <= 90:
            character.chosen_animal = random.choice(plant)
            character.chosen_animal_kind = "plant"
            character.chosen_animal_description = character.animal_choices["plant"][character.chosen_animal]
        else:
            character.chosen_animal = random.choice(vermin)
            character.chosen_animal_kind = "vermin"
            character.chosen_animal_description = character.animal_choices["vermin"][character.chosen_animal]


        character.companion_info = character.animal_companion["companion"][level]

        return character.chosen_animal         


def animal_feats(character):
    """
    randomly decides animal companion feats
    """
    #may want to expand animal companion feat selection later
    druid_entry = class_entry_for(character, 'druid')
    if druid_entry is not None:
        i = 0
        animal_chosen_feat_list = set()
        feats_choose = [1,3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,48,51]
        while feats_choose[i] < druid_entry['level']:
            animal_feats = list(character.animal_companion["feats"])
            chosen_feat = random.choice(animal_feats)
            animal_chosen_feat_list.add(chosen_feat)
            i = len(animal_chosen_feat_list)

            if i == 26:
                break

        return animal_chosen_feat_list