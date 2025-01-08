import re, random, json
# Start of major task: Items and Prices
def convert_price(character, price_input, name):
    try:
        price = int(price_input.replace(',', ''))
    except ValueError:
        dynamic_variable = extract_dynamic_variable(character, name)
        dynamic_variable_word = extract_dynamic_variable_word(character, name)
        if dynamic_variable:
            price = find_number(character, price_input, dynamic_variable)
            print(f'1st case price {price}')
        elif dynamic_variable_word:
            print(f"Target word: {dynamic_variable_word[-1]}")
            price = find_word(character, price_input, dynamic_variable_word[-1])
            print(f"Matched price: {price}")
            price = int(price) if price is not None else 0
        else:
            price = handle_invalid_price_input(character, price_input, name)
    
    price = adjust_price(character, price)
    return price

def extract_dynamic_variable(character, name):
    number_pull = r'\d+'
    dynamic_variable = re.findall(number_pull, name)
    print(f'This is the dynamic variable {dynamic_variable}')
    return dynamic_variable

def find_number(character, price_input, dynamic_variable):
    price_input = str(price_input)  # Ensure price_input is a string
    pattern = rf'(\d{{1,3}}(?:,\d{{3}})*)\s*\(\s*\+{dynamic_variable}\)'
    price_list = re.findall(pattern, price_input)
    print(f'this is the price_list {price_list}')
    
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
    print(f'This is the dynamic variable word {dynamic_variable_word}')
    return dynamic_variable_word

def handle_invalid_price_input(character, price_input, name):
    if price_input is None or '(' in str(price_input):
        print(f'no price detected for {name} + {price_input}')
        price_input = 0
    else:
        print(f'invalid price format for {name} + {price_input}')
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

    # print("these are your foundry item names: " + str(character.foundry_item_names))

    while i < len(select_from_list):
        equipment_name, random_equip, price, equip_descrip = choose_equipment(character, select_from_list[i])
        # print("equipment_name, random_equip, price, equip_descrip ", random_equip)
        # print('this is the anti-loop data: ', data)
        
        while random_equip not in data:
            # print("equipment_name, random_equip, price, equip_descrip ", random_equip)
            log_error(random_equip)
            equipment_name, random_equip, price, equip_descrip = choose_equipment(character, select_from_list[i])


        subtract_price_from_gold(character, price)
        i,k = grab_two_rings(character, select_from_list[i], k, i)
        
        if character.gold <= 0:
            break

        equipment_list.append(random_equip)
        equip_details = {'item_name': random_equip, 'description': equip_descrip}
        
        equip_dict[equipment_name] = equip_details
        price_total.append(price)

        i += 1

    print(equipment_list)
    print(price_total)
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

def subtract_price_from_gold(character, price):
    if price != None and isinstance(character.gold, int):
        character.gold -= int(price)
    else:
        character.gold = 0

def grab_two_rings(character, equipment_key, k, i):
    if equipment_key == "rings" and k < 1:
        i -= 1
        k += 10
    return i,k
    
def log_error(item_name):
    try:
        with open(r'Backend\json\items_broken.json', 'r', encoding='utf-8') as f:
            broken_items = json.load(f)
    except FileNotFoundError:
        broken_items = []

    if item_name not in broken_items:
        broken_items.append(item_name)

        with open(r'Backend\json\items_broken.json', 'w', encoding='utf-8') as f:
            json.dump(broken_items, f, ensure_ascii=False, indent=4)
    
    return None



# End of major task: Items and Prices