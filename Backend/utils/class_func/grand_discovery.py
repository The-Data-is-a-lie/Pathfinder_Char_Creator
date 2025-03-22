import random

def grand_discovery_chooser(character):
    """
    At level 20 Alchemists get a grand discovery + 2 extra basic discoveries
    This function assigns a random grand discovery, unless there are the 2 basic discoveries needed for greater change alignment
    if it sees these discoveries it will auto assign greater change alignment

    outputs: chosen discovery list (appends to it)
    """
    if character.c_class == 'alchemist' and character.c_class_level >= 20:   
        discovery_list_chosen  = set()
        grand = character.alchemist['grand']
        grand_discoveries = list(grand.keys())  

        alignment_set = {"change alignment", "infusion"}

        if alignment_set.issubset(character.chooseable):
            grand_discovery_chosen = "greater change alignment"
        else:
            grand_discoveries.remove("greater change alignment")
            grand_discovery_chosen = random.choice(grand_discoveries)
                    
        discovery_list_chosen.add(grand_discovery_chosen)
        return discovery_list_chosen
