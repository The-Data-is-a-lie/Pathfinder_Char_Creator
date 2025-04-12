import re 

# Bloodlines
def add_bonus_spells(character, bomus_spells):
    for i,spell in enumerate(bomus_spells):
        if i + 1 < len(character.spell_list_choose_from):
            spell = clean_bonus_spells(spell)
            character.spell_list_choose_from[i + 1].append(spell)

def clean_bonus_spells(spell):
    spell = spell.replace("UM", "")
    # remoth (#th) using regex
    spell = re.sub(r'\s*\(\d+(?:st|nd|rd|th)\)', '', spell)
    spell = spell.title()
    return spell