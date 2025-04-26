def get_class_abilities(character):
    chosen_class_data = character.class_data.get(character.c_class, "").keys()
    actual_class_abilities = []
    start = 0
    for ability in chosen_class_data:
        if ability.lower() in ['aasimar', 'alicorn', 'any goblinoid race', 'blue', 'decataur', 'dreige', 'dromite', 'dwarves', 'elan', 'elves', 'entoli', 'ethumion', 'gnome', 'grendle', 'Half-Elf', 'half-giant', 'half-gnoll', 'half-hobgoblin', 'halfling', 'Half-Orc', 'human', 'kijin', 'maenad', 'merg', 'murk', 'xeph', 'aphorite', 'catfolk', 'dhampir', 'drow', 'dwarf', 'elf', 'fetchling', 'gathlain', 'gnome', 'goblin', 'grippli', 'Half-Elf', 'halfling', 'Half-Orc', 'hobgoblin', 'human', 'ifrit', 'kitsune', 'kobold', 'nagaji', 'orc', 'ratfolk', 'svirfneblin', 'tiefling', 'vanara', 'vine leshy', 'wyrwood', 'aellar', 'aasimar', 'alicorn', 'aphorite', 'drow', 'aquatic elf', 'boggard', 'kitsune', 'catfolk', 'dwarf', 'duergar', 'kitsune', 'drow', 'duskwalker', 'blue', 'aellar', "blinkling", "atstreidi", "aellar (hawkguard)", "alicorn", "blue"]: 
            start = 0
            break

        if start == 1:
            actual_class_abilities.append(ability)

        if ability == "weapon and armor proficiency":
            start = 1

    return actual_class_abilities

def get_class_abilties_desc(character, actual_class_abilities):
    chosen_class_data = character.class_data.get(character.c_class, "")
    class_ability_desc = {}
    class_ability = []
    for ability in actual_class_abilities:
        desc = chosen_class_data.get(ability, {})
        class_ability_desc.update({ability: desc})
        class_ability.append(f"{ability}_{character.c_class}")

    return class_ability_desc, class_ability
