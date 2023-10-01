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
    # "character_flaws": None
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
        # character_flaws
    )

    from createACharacter import (
        formatted_charisma, formatted_constitution, formatted_dexterity, formatted_intelligence, formatted_strength, formatted_wisdom
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
 


