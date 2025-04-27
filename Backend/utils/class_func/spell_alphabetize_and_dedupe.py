def spell_alphabetize_and_dedupe_func(spell_list):
    # Alphabetizes and dedupes each unique spell list
    if spell_list in (None, [], {}):
        return None


    try:
        for i, levels_list in enumerate(spell_list):
            unique_spells = list(set(levels_list))
            unique_spells.sort()
            spell_list[i] = unique_spells

    except: 
        return None   
    return unique_spells