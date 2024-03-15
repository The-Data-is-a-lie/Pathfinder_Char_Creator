from utils import data
import random, re
# Start of major task: skills assignment

def skills_selector(character, skills, skill_rank_level):
    """
    randomly grabs a subset of skills then assigns skill ranks to them (up to character level for each)
    to prevent any high stats characters from breaking the function, we max them out at character level for all in game skills

    param (skills list from the data section)
    return
    - skill ranks (Dictionary)
    """        

    all_skills = getattr(data, skills)
    max_skill_ranks = character.c_class_level
    skill_ranks = {}

    selectable_skills, dummy_skill_ranks = get_selectable_skills(character, all_skills, skill_rank_level)
    assign_skill_ranks(character, selectable_skills, dummy_skill_ranks, max_skill_ranks, skill_ranks)

    print(skill_ranks)
    print(f'This is your int mod {character.int_mod}')
    total_ranks = sum(skill_ranks.values())
    print("The total sum of ranks is:", total_ranks)

    return skill_ranks


def get_selectable_skills(character,all_skills, skill_ranks_level):
    skill_points = character.class_data[character.c_class]["skill points at each level"]
    scaling = int(skill_points) + character.int_mod
    dummy_skill_ranks = (scaling * character.c_class_level) + skill_ranks_level

    print(scaling)

    if character.c_class not in character.class_data.keys():
        scaling = 2 + character.int_mod

    skill_number = scaling + random.randint(1, 8)
    skill_number = min(skill_number, len(all_skills))
    selectable_skills = random.sample(all_skills, k=skill_number)

    return selectable_skills, dummy_skill_ranks


def assign_skill_ranks(character,selectable_skills, dummy_skill_ranks, max_skill_ranks, skill_ranks):
    i = 0

    while i < dummy_skill_ranks:
        skill = random.choice(selectable_skills)
        ranks_to_assign = min(random.randint(1, 3), dummy_skill_ranks - i, max_skill_ranks)
        ranks_to_assign = min(ranks_to_assign, max_skill_ranks - skill_ranks.get(skill, 0))
        skill_ranks[skill] = skill_ranks.get(skill, 0) + ranks_to_assign
        i += ranks_to_assign

        if i >= dummy_skill_ranks or all(skill_ranks.get(skill, 0) >= max_skill_ranks for skill in selectable_skills):
            break

# Start of major task: skills assignment