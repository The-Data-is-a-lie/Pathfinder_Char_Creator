from utils import data
import random, re
# Start enhnacement to Armor + Weapons

def enhancement_calculator(character, gold_divisor):
    mapping = getattr(data,'enhancement_bonus_mapping')
    closest_key = min(mapping.keys(), key=lambda x: abs(x - (character.gold // gold_divisor)))
    character.gold = character.gold - closest_key 
    enhancement_bonus = mapping[closest_key]
    return enhancement_bonus

def enhancement_chooser(character, data, enhancement_bonus, weapon_type, shield_type = True):
    if weapon_type == 'Shield' and shield_type != True:
        return []
    else:
        total_bonus = 0
        enhancement_list = list(data.get(weapon_type).keys())
        chosen_enhancement_list = []
        while (enhancement_bonus - total_bonus) > 5: 
            chosen_enhancement = random.choice(enhancement_list)
            item_list = get_enhancement_info(character, weapon_type)
            enhancement_limits(character, item_list, weapon_type, chosen_enhancement)
            chosen_enhancement_bonus = data[weapon_type].get(chosen_enhancement,0).get('enhancement', 0)
            total_bonus += int(chosen_enhancement_bonus)

            try:
                enhancement_list.remove(chosen_enhancement)
                chosen_enhancement_list.append(chosen_enhancement)
            except:
                pass
            
        
        return chosen_enhancement_list
    
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

    




def bonus_gold_calculator(character, chosen_enhancement, weapon_type, data):
    price = data[weapon_type][chosen_enhancement].get('price', 0)
    if price == "":
        bonus_cost = 0
    else:
        price = price.replace(",", "")
        bonus_cost = int(price)
    bonus_cost = character.bonus_gold_calculator(chosen_enhancement, weapon_type, data)
    character.gold -= bonus_cost            






    
# End of enhancement to Armor + Weapons