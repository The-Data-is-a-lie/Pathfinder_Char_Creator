character_data = {
    "str": None,
    "dex": None,
    "con": None,
    "int": None,
    "wis": None,
    "cha": None,
    "level": None,
    "feats": None,
    "BAB": None,
    # "race": None,
    "weapons_no_region": None,
    "weapons": None,
    "luck": None,
    "mythic": None,
    # "class": None,
    # "class_secondary": None,
    "flaws": None,
    "professions": None,
    "ability_traits": None,
    "personality": None,
    "mannerisms": None,
    "stats": None,
    "age": None,
    "height": None,
    "weight": None,
    "hair_color": None,
    "hair_type": None,
    "eye_color": None,
    "appearance": None,
    "deity": None,
    "alignment": None,
    "languages":None,    
    "racial_traits": None,
    # "racial_language": None,
    "racial_size": None,
    "racial_speed": None,
    "ability_scores":None,
    # "character_flaws": None
    "region":None,
    "class": None,
    "f_name":None,
    "l_name": None,
    "Hit_Dice": None,
    "Total_HP": None,
    "extra_ability_score_levels":None,
    "npc_level": None,
    "BAB_total": None
}

def update_character_data(key_value_pairs):
    global character_data

    """
    Update a dictionary with multiple key-value pairs.
    
    Args:
        key_value_pairs (list of tuples): A list of key-value pairs to update the dictionary.

    Returns:
        None
    """

    for key, value in key_value_pairs:
        character_data[key] = value

# Example usage:
def initialize_character_data():
    from utils.util import (
        feats,
        BAB,
        level,
        # c_race,
        weapons,
        weaponz,
        luck_score,
        mythic_rank,
        # c_class,
        # c_class_2, Sometimes this is a tuple, we'll need to update the code to handle that
        flaw,
        proforce,
        ability,
        personality,
        random_mannerisms,
        stats,
        age_roll, 
        weight_roll, 
        height_roll,
        hair_color_choice, 
        hair_type_choice, 
        eye_color_choice, 
        appearance_choice,
        chosen_deity,
        racial_traits, 
        # racial_language, 
        racial_size, 
        racial_speed, 
        ability_scores,
        region,
        f_name,
        l_name,
        full_name,
        Total_HP,
        Hit_dice,
        extra_ability_score_levels,
        npc_level,
        BAB_total,
        c_class
        # character_flaws
    )

    from createACharacter import (
        formatted_charisma, formatted_constitution, formatted_dexterity, formatted_intelligence, formatted_strength, formatted_wisdom,
        c_alignment, c_langs
    )

    update_list = [
        ("str", formatted_strength),
        ("dex", formatted_dexterity),
        ("con", formatted_constitution),
        ("int", formatted_intelligence),
        ("wis", formatted_wisdom),
        ("cha", formatted_charisma),
        ("level", level),
        ("feats", feats),
        ("BAB", BAB),
        # ("race", c_race),
        ("weapons_no_region", weapons),
        ("weapons", weaponz),
        ("luck", luck_score),
        ("mythic", mythic_rank),
        # ("class", c_class)
        # ("class_secondary", c_class_2),
        ("flaws", flaw),
        ("professions", proforce),
        ("ability_traits", ability),
        ("personality", personality),
        ("mannerisms", random_mannerisms),
        ("inherent_stats", stats),
        ("age", age_roll),
        ("height", height_roll),
        ("Weight", weight_roll),
        ("hair_color", hair_color_choice),
        ("hair_type", hair_type_choice),
        ("eye", eye_color_choice),
        ("appearance", appearance_choice),
        ("deity", chosen_deity),
        ("alignment", c_alignment),
        ("languages", c_langs),
        ("racial_traits", racial_traits),
        # ("racial_language", racial_language),
        ("racial_size", racial_size),
        ("racial_speed", racial_speed),
        ("ability_scores", ability_scores),
        ("region", region),
        ("c_class", c_class),        
        ("full_name", full_name),
        ("Total_HP", Total_HP),
        ("Hit_dice", Hit_dice),
        ("extra_ability_score_levels", extra_ability_score_levels),
        ("npc_level", npc_level),
        ("BAB_total", BAB_total)


        # ("character_flaws", character_flaws),
    ]

    
    update_character_data(update_list)
    print(character_data)

def character_data_to_json():
        global character_json
        import json
        character_json = json.dumps(character_data, indent=4)
        print(character_json)

def convert_character_json_to_html():
  import re
  import ast
  """Converts a JavaScript dictionary to readable HTML.

  Returns:
    A string containing the HTML output.
  """

  html_output = ""

    #reusing the Python dictionary
  for key, value in character_data.items():
    if isinstance(value, str) and re.match(r"<span style=\"font-weight: bold; color: red;\">.*</span>", value):
      # Extract the text from the span element and remove the element.
      value = re.sub(r"<span style=\"font-weight: bold; color: red;\">", "", value)
      value = re.sub(r"</span>", "", value)

    html_output += f"<b>{key}:</b> {value}<br>"
  print(html_output)
  return html_output
 


