import random
character_data = {}

# Generate and add character data to the dictionary
character_data["name"] = "Character Name"
character_data["race"] = "Human"
character_data["class"] = "Wizard"
character_data["level"] = 5
character_data["alignment"] = "Lawful Good"

# Generate additional data and add it to the dictionary
character_data["strength"] = random.randint(1, 20)
character_data["dexterity"] = random.randint(1, 20)
character_data["constitution"] = random.randint(1, 20)
character_data["intelligence"] = random.randint(1, 20)
character_data["wisdom"] = random.randint(1, 20)
character_data["charisma"] = random.randint(1, 20)

# Generate and add more data
character_data["luck_score"] = random.randint(1, 40)
character_data["age"] = 25
character_data["weight"] = 160
character_data["height"] = 70

# Add data from printed statements
character_data["professions"] = ["Dog trainer", "Illusionist", "Metalworker"]
character_data["ability_traits"] = [
    "Dump Salvager",
    "Defensive Strategist",
    "Clan Artisan",
    "Adventurous Explorer",
    "Reviving Rest",
    "Tracker of the Society",
    "Gregarious",
    "Iron Mind",
]

# Add data from other sections of the character sheet
character_data["skills"] = ["Acrobatics", "Climb", "Craft", "Diplomacy"]
character_data["specialized_skills"] = ["Knowledge (Arcana)", "Knowledge (Nature)", "Diplomacy", "Knowledge (Religion)"]

# Add data for mythic abilities, path of war, etc.

# Print the complete character data dictionary
print(character_data)