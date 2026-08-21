import random
from math import ceil, floor

from utils.class_func import luck
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
    # Luck trades against HP in both directions -- 5 HP buys +1 luck, and "2 hit points ... for -1
    # luck" pays a seller back. It lands on Total_HP and deliberately NOT on sheet_health:
    # sheet_health means "full hit dice", which is the house rule itself (skills-and-hp.md), and a
    # luck purchase does not repeal the house rule -- it spends the result of it. Keeping the two
    # apart is what lets test_house_invariants keep asserting the full-HP rule unchanged.
    stake = luck.stake_of(character)
    _before = character.Total_HP
    _spent = luck.settle(stake, luck.CURRENCY_HP, character.Total_HP)
    character.Total_HP -= _spent
    # THE PAYOUT IS NO LONGER ADDED HERE. It is delivered as a pf1 `mhp` change on the Negative Luck
    # Payout item instead, for a reason this line could not fix: the FoundryVTT module builds actor
    # HP from `total_rolled_hp` (the raw dice), never from `Total_HP`, so every point added here was
    # invisible on the sheet the character is actually played from. A change lands.
    #
    # The BUY side still settles here, because that is a deduction from a pool this function owns
    # and a negative `mhp` change would misrepresent it as a penalty rather than a smaller pool.
    _received = luck.payout(stake, luck.PAYOUT_HP)
    luck.record_audit(character, 'hp', _before, _spent, _received, character.Total_HP)
    return character.Total_HP
