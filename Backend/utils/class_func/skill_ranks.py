from utils import data
import random, re
from math import floor
# Start of major task: skills assignment


def final_ability_score(character, stat):
    """FINAL ability score for ``stat``: base roll + inherent bonuses + level-up
    bumps. ``inherents`` / ``level_up_stats`` are ``{stat: bonus}`` dicts and may
    be absent (e.g. inherents disabled), so we read them defensively."""
    inherents = getattr(character, 'inherents', {}) or {}
    level_ups = getattr(character, 'level_up_stats', {}) or {}
    inh = inherents.get(stat, 0) if isinstance(inherents, dict) else 0
    lvl = level_ups.get(stat, 0) if isinstance(level_ups, dict) else 0
    return getattr(character, stat) + inh + lvl


def final_ability_mod(character, stat):
    """Ability modifier derived from the FINAL score (see final_ability_score)."""
    return floor((final_ability_score(character, stat) - 10) / 2)


def highest_mental_mod(character):
    """Highest mental ability modifier using each stat's FINAL score
    (base roll + inherent bonuses + level-up bumps), not just the base roll.

    Bonus skill ranks scale off the best mental ability, so an Int/Wis/Cha that
    was boosted by inherents or level-up bumps now grants the extra ranks it
    should.
    """
    return max(final_ability_mod(character, s) for s in ('int', 'wis', 'cha'))

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

    selectable_skills, dummy_skill_ranks, not_selectable_skills = get_selectable_skills(character, all_skills, skill_rank_level)
    assign_skill_ranks(character, selectable_skills, not_selectable_skills, dummy_skill_ranks, max_skill_ranks, skill_ranks)
    assign_dummy_zeroes(not_selectable_skills, skill_ranks)


    # print(f'This is your int mod {character.int_mod}')
    # total_ranks = sum(skill_ranks.values())
    # print("The total sum of ranks is:", total_ranks)

    return skill_ranks


def get_selectable_skills(character,all_skills, skill_ranks_level):
    skill_points = character.class_data[character.c_class]["skill points at each level"]
    # Use the FINAL highest mental mod (base + inherents + level-ups), not the base roll.
    mental_mod = highest_mental_mod(character)
    scaling = int(skill_points) + mental_mod

    dummy_skill_ranks = (scaling * character.c_class_level) + skill_ranks_level
    print("Dummy skill ranks:", dummy_skill_ranks)


    # For if we don't find a character, just assign them minimum skills
    if character.c_class not in character.class_data.keys():
        scaling = 2 + abs(mental_mod)
        print("couldn't find this character's skills using default scaling", scaling)

    skill_number = scaling + random.randint(abs(mental_mod), abs(mental_mod)+8)
    skill_number = min(skill_number, len(all_skills))
    selectable_skills = random.sample(all_skills, k=skill_number)
    not_selectable_skills = []

    for skill in all_skills:
        if skill not in selectable_skills:
            not_selectable_skills.append(skill)

    return selectable_skills, dummy_skill_ranks, not_selectable_skills


def assign_skill_ranks(character, selectable_skills, not_selectable_skills, dummy_skill_ranks, max_skill_ranks, skill_ranks):
    i = 0
    while i < dummy_skill_ranks:
        skill = random.choice(selectable_skills)
        ranks_to_assign = min(random.randint(1, 3), dummy_skill_ranks - i, max_skill_ranks)
        ranks_to_assign = min(ranks_to_assign, max_skill_ranks - skill_ranks.get(skill, 0))
        skill_ranks[skill] = skill_ranks.get(skill, 0) + ranks_to_assign
        i += ranks_to_assign

        if i >= dummy_skill_ranks or all(skill_ranks.get(skill, 0) >= max_skill_ranks for skill in selectable_skills):
            break

def assign_dummy_zeroes(not_selectable_skills, skill_ranks):
    for unassigned_skill in not_selectable_skills:
        skill_ranks[unassigned_skill] = 0       
        # print("breaking at unassigned") 

    return skill_ranks

