import random
from math import ceil, floor

from utils.class_func.skill_ranks import final_ability_mod, homebrew_enabled


def hit_dice_calc(character):
    for entry in character.classes:
        entry['hit_die'] = extract_num(character.class_data[entry['name']]["hit die"])
    # Legacy alias: the primary class's die is the auto-maxed level-1 die in total_hp_calc.
    character.Hit_dice1 = character.classes[character.primary_class_index]['hit_die']


def extract_num(hit_die):
    hit_die = hit_die.replace(".", "").replace("d", "")
    return int(hit_die)


def roll_hp(character):
    """House HP rule (oks/pathfinder/house-rules/skills-and-hp.md): full (max) hit die at EVERY
    level when homebrew is on -- matching the pf1 world's maximized health config, so the injected
    Foundry actor and the generator agree. With homebrew off, the classic per-level roll.
    Either way the primary class's first level is excluded here: total_hp_calc adds it maxed."""
    total = 0
    for i, entry in enumerate(character.classes):
        dice = entry['level'] - 1 if i == character.primary_class_index else entry['level']
        if homebrew_enabled(character):
            total += dice * entry['hit_die']
        else:
            total += sum(random.randint(1, entry['hit_die']) for _ in range(dice))
    character.total_hp_rolls = total
    return character.total_hp_rolls


def total_hp_calc(character):
    """Hit dice + Con mod x level. The Con mod halves BEFORE flooring (the old
    floor(con-10)/2 inflated odd-Con HP by level/2) and uses the FINAL Con score, so
    inherent bonuses and level-up bumps that landed on Con count."""
    con_mod = final_ability_mod(character, 'con')
    character.sheet_health = character.total_hp_rolls + character.Hit_dice1
    character.Total_HP = character.sheet_health + con_mod * character.level
    return character.Total_HP
