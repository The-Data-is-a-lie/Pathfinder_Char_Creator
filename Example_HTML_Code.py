def html_builder():
    from jinja2 import Environment, FileSystemLoader
    import datetime
    env = Environment(loader=FileSystemLoader('.'))  # Adjust the loader path as needed
    template = env.get_template('character_sheet.html')

    # Generate a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Define the output HTML filename using the timestamp
    output_filename = f"character_sheet_{timestamp}.html"


    # from utils.data_dict import character_data
    # Define your character data dictionary
    character_data = {
        "region": "Esterdragon",
        "weapons": "['Blades, Light', 'Monk']",
        "weapon_name": "Staff",
        "character_name": "Kusumo Armando",
        "character_class": "mageknight",
        "strength": 25,
        "dexterity": 15,
        "constitution": 27,
        "intelligence": 14,
        "wisdom": 113,
        "charisma": 5,
        "npc_levels": 92,
        "non_npc_levels": 11,
        "total_hp": 64,
        "inherent_stat_buff": 9,
        "age": 28,
        "weight": 44,
        "height": 37,
        "race": "Kobold",
        "racial_scores": {'Dexterity': '+2', 'Constitution': '-2', 'Strength': '-4'},
        "racial_traits": ['Crafty', 'Light Sensitivity', 'Armor', 'Darkvision'],
        "racial_languages": ['Kobold', 'Draconic', 'Common'],
        "racial_size": "Small",
        "racial_speed": 30,
        "hair_colors": "Grey",
        "hair_types": "Wavy",
        "eye_colors": "Green",
        "appearance": ['Smooth skin', 'Distinguished', 'Husky'],
        "professions": ["Zoo Cleaner", "Textile Merchant", "Spearman"],
        "ability_traits": ["Ghost Survivor", "Heat Fortitude", "Supportive", "Authoritarian", "Hero Worship", "Sphinx Riddler", "Rice Runner", "Stargazer"],
        "personality_traits": ["Stubborn", "Considerate", "Methodical", "Empathetic", "Respectful"],
        "mannerisms": ["Kicks at the ground", "Raises eyebrows", "Brushes hair out of face"],
        "character_flaws": ["Obese", "Banned"],
        "alignment": "Lawful neutral",
        "deity": "Ghlaunder",
        "extra_languages": ['Elven', 'Abyssal', 'Kelish', 'Wayang'],
        "path_of_war_abilities": 1,
        "path_number_1": "Sagitta Stellaris",
        "bonus_feats_per_level": 9,
        "bonus_ability_scores": 2,
        "archetype": "Dragoon",
        "skills": ['Acrobatics', 'Bluff', 'Climb', 'Craft', 'Disguise', 'Fly', 'Handle Animal', 'Intimidate', 'Knowledge (geography)', 'Knowledge (nature)', 'Perception', 'Profession', 'Sense Motive', 'Spellcraft', 'Stealth', 'Survival', 'Swim'],
        "specialized_skills": ['Craft', 'Climb', 'Handle Animal', 'Profession'],
        "mythic": "Did not get mythic"
    }


    # Render the template with your character data
    html_content = template.render(character_data=character_data)

    # Save the HTML content to a file
    with open(output_filename, 'w') as html_file:
        html_file.write(html_content)

    import webbrowser

    # Open the generated HTML file in the default web browser
    webbrowser.open('character_sheet.html')

html_builder()