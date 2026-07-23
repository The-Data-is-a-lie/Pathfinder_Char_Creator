import re, random, json
from utils.paths import repo_path
# Start of major task: Items and Prices
def convert_price(character, price_input, name):
    try:
        price = int(price_input.replace(',', ''))
    except ValueError:
        dynamic_variable = extract_dynamic_variable(character, name)
        dynamic_variable_word = extract_dynamic_variable_word(character, name)
        if dynamic_variable:
            price = find_number(character, price_input, dynamic_variable)
        elif dynamic_variable_word:
            price = find_word(character, price_input, dynamic_variable_word[-1])
            price = int(price) if price is not None else 0
        else:
            price = handle_invalid_price_input(character, price_input, name)
    
    price = adjust_price(character, price)
    return price

def extract_dynamic_variable(character, name):
    number_pull = r'\d+'
    dynamic_variable = re.findall(number_pull, name)
    return dynamic_variable

def find_number(character, price_input, dynamic_variable):
    price_input = str(price_input)  # Ensure price_input is a string
    pattern = rf'(\d{{1,3}}(?:,\d{{3}})*)\s*\(\s*\+{dynamic_variable}\)'
    price_list = re.findall(pattern, price_input)
    
    if price_list:
        price = int(price_list[0].replace(',', ''))
        return price
    else:
        return None
    

def find_word(character, text, target_word):
    pattern = r'(\d+)\D*' + re.escape(target_word)
    match = re.search(pattern, text)
    
    if match:
        return match.group(1)
    else:
        return None        

def extract_dynamic_variable_word(character, name):
    word_pull = r'\b(lesser|greater|superior|major|minor|normal|djinni|efreeti|marid|shaitan|destined|fey|abyssal|accursed|celestial|draconic|elemental|infernal|undead|aberrant|adamantine|silver|cold iron|type i|type ii|type iii|type iv|)\b(?![()])'
    dynamic_variable_word = re.findall(word_pull, name)
    return dynamic_variable_word

def handle_invalid_price_input(character, price_input, name):
    if price_input is None or '(' in str(price_input):
        price_input = 0
    else:
        price_input = 0
    return price_input

def adjust_price(character, price):
    if isinstance(price, int):
        if price < 11:
            price = (price ** 2) * 1000

    else:
        price = 0

    return price

def capitalize_first_letter_each_word(s):
    return ' '.join([word.capitalize() for word in s.split()])

def item_chooser(character, data):
    i = 0
    k = 0
    # i = character.determine_start_index()
    select_from_list = list(character.items.keys())
    price_total = []
    equipment_list = []
    equip_dict = {}
    # Items rolled that the FoundryVTT name list can't resolve. Collected per character and folded
    # into the payload's buff_gaps by main_test -- see log_error() on why this is no longer a file.
    unresolved = {}
    character.unresolved_items = unresolved

    while i < len(select_from_list):
        equipment_name, random_equip, price, equip_descrip = choose_equipment(character, select_from_list[i])
        while random_equip not in data:
            unresolved[str(random_equip)] = None
            equipment_name, random_equip, price, equip_descrip = choose_equipment(character, select_from_list[i])

        # Check BEFORE buying. This used to subtract first and then `break` on gold <= 0, which meant
        # the character paid for an item that was never added to the list, ended up with negative gold,
        # AND abandoned every remaining slot even when something cheap would have fit. Now an
        # unaffordable slot is simply skipped and the batch continues, so gold never goes below 0.
        if not can_afford(character, price):
            i += 1
            continue

        subtract_price_from_gold(character, price)
        # Ring bookkeeping only runs on a real purchase, so a skipped ring doesn't burn the
        # character's second-ring slot.
        i,k = grab_two_rings(character, select_from_list[i], k, i)

        equipment_list.append(random_equip)
        equip_details = {'item_name': random_equip, 'description': equip_descrip}

        equip_dict[equipment_name] = equip_details
        price_total.append(price)

        i += 1

    return equipment_list, equip_dict

def item_dictionary(character, random_equip, equipment_key):
    items = character.items
    equip_descrip = items.get(equipment_key, {}).get(random_equip, {}).get('description', {})
    return equip_descrip


def determine_start_index(character):
    if character.armor_type is None:
        return 2
    elif character.armor_type == 'L' or character.weapons[1] in ('Axes', 'Blades, Heavy', 'Bows', 'Crossbows', 'Double', 'Firearms', 'Polearms', 'Siege Engines'):
        return 1
    else:
        return 0
    
def choose_equipment(character, equipment_key):
    equipment_name = equipment_key
    item_dict = character.items[str(equipment_key)]
    random_equip = random.choice(list(item_dict.keys()))
    price = str(item_dict[random_equip]['price'])
    price = convert_price(character, price, random_equip)
    equip_descrip = item_dictionary(character, random_equip, equipment_key)

    # capitalize the first letter of each random_equip (B/c it gets exported to foundryVTT and needs to be exact)
    random_equip = capitalize_first_letter_each_word(random_equip)
    return equipment_name, random_equip, price, equip_descrip

def can_afford(character, price):
    """True when the character can pay ``price`` without going below 0 gold. Unusable prices (None, or
    a non-int purse) are treated as unaffordable so the caller skips the slot rather than guessing."""
    if price is None or not isinstance(character.gold, int):
        return False
    try:
        return character.gold - int(price) >= 0
    except (TypeError, ValueError):
        return False


def subtract_price_from_gold(character, price):
    if price != None and isinstance(character.gold, int):
        character.gold -= int(price)
    else:
        # Previously this zeroed the character's entire purse whenever a price was unusable -- a
        # silent, total loss of gold. Callers now gate on can_afford(), so this branch only fires on
        # malformed data: leave the gold alone and say so.
        print(f"item_and_price: skipping unusable price {price!r}; gold left at {character.gold!r}")

def grab_two_rings(character, equipment_key, k, i):
    if equipment_key == "rings" and k < 1:
        i -= 1
        k += 10
    return i,k
    
# log_error() was removed. It read Backend/json/items_broken.json, appended the unresolved item and
# wrote the file back, in the middle of generating a character -- an unlocked read-modify-write that
# four gunicorn workers raced on, mutating a repo file as a side effect of an HTTP request. It also
# accumulated forever, so the file recorded every item ever missed rather than what this character
# hit. item_chooser now collects unresolved names on character.unresolved_items and main_test folds
# them into the payload's buff_gaps, which is the same channel the curated-buff mismatches use.



# End of major task: Items and Prices