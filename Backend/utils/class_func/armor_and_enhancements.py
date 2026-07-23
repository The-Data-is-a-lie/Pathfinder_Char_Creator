from utils import data
import random, re
# Start enhnacement to Armor + Weapons

def enhancement_calculator(character, gold_divisor):
    """Buy the best enhancement tier this item's slice of the purse can actually afford.

    ``gold_divisor`` splits the remaining gold between the item slots (armor 3, weapon 2, shield 1).
    This used to take the mapping key CLOSEST to that budget, which for a poor character is the key
    just ABOVE it -- the table starts at 2000, so 500 gold budgeted 166 and then spent 2000, leaving
    -1500, three times over. Now we take the largest key at or below the budget and spend nothing when
    even the cheapest tier is out of reach (enhancement_chooser already returns ([], 0) for a bonus
    below 1), so gold can never go negative here.
    """
    mapping = getattr(data,'enhancement_bonus_mapping')
    if not isinstance(character.gold, int) or character.gold <= 0:
        return 0
    budget = character.gold // gold_divisor
    affordable = [key for key in mapping if key <= budget]
    if not affordable:
        return 0
    best_key = max(affordable)
    character.gold = character.gold - best_key
    enhancement_bonus = mapping[best_key]
    return enhancement_bonus

def enhancement_chooser(character, data, enhancement_bonus, weapon_type, shield_type = True):
    """Returns (chosen quality names, flat +N enhancement bonus).

    enhancement_bonus is the total effective bonus budget (PF pricing, up to +10); qualities
    spend from it until at most 5 remains, and that leftover is the item's flat +N (1..5).
    """
    if weapon_type == 'Shield' and shield_type != True:
        return [], 0
    else:
        total_bonus = 0
        enhancement_list = list(data.get(weapon_type).keys())
        chosen_enhancement_list = []
        while (enhancement_bonus - total_bonus) > 5:
            chosen_enhancement = random.choice(enhancement_list)
            item_list = get_enhancement_info(character, weapon_type)
            enhancement_limits(character, item_list, weapon_type, chosen_enhancement)
            chosen_enhancement_bonus = data[weapon_type].get(chosen_enhancement,0).get('enhancement', 0)
            total_bonus += int(chosen_enhancement_bonus or 0)

            try:
                enhancement_list.remove(chosen_enhancement)
                chosen_enhancement_list.append(chosen_enhancement)
            except:
                pass

        flat_bonus = max(1, min(5, enhancement_bonus - total_bonus)) if enhancement_bonus >= 1 else 0
        return chosen_enhancement_list, flat_bonus
    
def get_enhancement_info(character, weapon_type):
    if weapon_type in ('Melee', 'Ranged'):
        item_list = set()
        for item in character.weapon_dict.values():
            item_list.add(item.get('type', 0))
            item_list.add(item.get('special', 1))
            item_list.add(item.get('only', 2))

        key = list(character.weapon_dict.keys())[0] 
        if re.search(r'(bow)|(firearm)', key.lower()):
            key_add = ('bow' if re.search(r'bow', key) else 'firearm')
            item_list.add(key_add)

        item_list = split_item_list(character, item_list)
        return item_list
    
def split_item_list(character, item_list):
    normalized_items = []
    for item in item_list:
        if isinstance(item, str):
            stripped_item = item.lower()
            split_items = re.split(r"[,|+|/]", stripped_item)
            normalized_items.extend(split_items)
        else:
            normalized_items.append(item)
    unique_items = set(normalized_items)
    return unique_items

def clean_up_only(character, only):
    only_list = []
    only_list = only.split(",") if only else []
    only_list = [item.lower() for item in only_list]
    only_list = set(only_list)
    return only_list

def enhancement_limits(character, item_list, weapon_type, chosen_enhancement):
    if weapon_type in ('Melee', 'Ranged'):
        only = character.weapon_qualities[weapon_type].get(chosen_enhancement,0).get('only',"N/A").lower()
        not_only = character.weapon_qualities[weapon_type].get(chosen_enhancement,0).get('not',"N/A").lower()
        only_list = clean_up_only(character, only)
        not_only_list = clean_up_only(character, not_only)
        if len(only_list) > 0 and len(not_only_list) > 0:
            if only_list.issubset(item_list):
                pass
            else:
                chosen_enhancement = ''
                return chosen_enhancement

    




# bonus_gold_calculator was removed: nothing called it (its only reference was the unrelated
# character.bonus_gold_calculator method inside its own body), and it subtracted from gold with no
# affordability check -- a trap for anyone who wired it up later.



    
# End of enhancement to Armor + Weapons