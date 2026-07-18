import re

# Bloodlines
def add_bonus_spells(character, bomus_spells, spell_groups=None):
    # spell_groups targets a specific class's spellbook list (multiclass); defaults to the
    # legacy scalar (the primary spellbook — same object, so in-place appends stay in sync).
    if spell_groups is None:
        spell_groups = character.spell_list_choose_from
    for i,spell in enumerate(bomus_spells):
        if i + 1 < len(spell_groups):
            if spell in spell_groups[i + 1]:
                continue
            spell = clean_bonus_spells(spell)
            spell_groups[i + 1].append(spell)

def clean_bonus_spells(spell):
    spell = spell.replace("UM", "")
    # remoth (#th) using regex
    spell = re.sub(r'\s*\(\d+(?:st|nd|rd|th)\)', '', spell)
    spell = spell.title()
    return spell

def add_bonus_spells_from_dict(character, bonus_spells_dict, spell_groups=None):
    if spell_groups is None:
        spell_groups = character.spell_list_choose_from
    i = 0
    for level, spells in bonus_spells_dict.items():
        i += 1
        # Convert level to an integer index if possible (e.g., '1st' -> 1)
        try:
            level_index = int(level[0])  # Extract the numeric part of the level
        except ValueError:
            level_index = i  # Default to i for invalid keys

        # Ensure the level index is within the bounds of spell_list_choose_from
        if level_index < len(spell_groups):
            for spell in spells:
                if spell in spell_groups[level_index]:
                    continue
                spell = clean_bonus_spells(spell)
                spell_groups[level_index].append(spell)