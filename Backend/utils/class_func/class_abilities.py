def get_class_abilities(character):
    chosen_class_data = character.class_data.get(character.c_class, "").keys()
    actual_class_abilities = []
    start = 0
    for ability in chosen_class_data:
        if ability.lower() in ['aasimar', 'alicorn', 'any goblinoid race', 'blue', 'decataur', 'dreige', 'dromite', 'dwarves', 'elan', 'elves', 'entoli', 'ethumion', 'gnome', 'grendle', 'half-elf', 'half-giant', 'half-gnoll', 'half-hobgoblin', 'halfling', 'half-orc', 'human', 'kijin', 'maenad', 'merg', 'murk', 'xeph', 'aphorite', 'catfolk', 'dhampir', 'drow', 'dwarf', 'elf', 'fetchling', 'gathlain', 'gnome', 'goblin', 'grippli', 'half-elf', 'halfling', 'half-orc', 'hobgoblin', 'human', 'ifrit', 'kitsune', 'kobold', 'nagaji', 'orc', 'ratfolk', 'svirfneblin', 'tiefling', 'vanara', 'vine leshy', 'wyrwood', 'aellar', 'aasimar', 'alicorn', 'aphorite', 'drow', 'aquatic elf', 'boggard', 'kitsune', 'catfolk', 'dwarf', 'duergar', 'kitsune', 'drow', 'duskwalker', 'blue', 'aellar', "blinkling", "atstreidi", "aellar (hawkguard)", "alicorn", "blue"]: 
            start = 0
            break

        if ability == "weapon and armor proficiency":
            start = 1

        if start == 1:
            actual_class_abilities.append(ability)

    return actual_class_abilities

def get_class_abilties_desc(character, actual_class_abilities):
    chosen_class_data = character.class_data.get(character.c_class, "")
    class_ability_desc = {}
    for ability in actual_class_abilities:
        desc = chosen_class_data.get(ability, {})
        class_ability_desc.update({ability: desc})

    return class_ability_desc
