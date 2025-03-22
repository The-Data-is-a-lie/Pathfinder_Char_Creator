import random
#Want to make this a generic function that works for any class ability selection with complex prerequisites
def chooseable_list(character):
    character.chooseable = set()
    #figure out how to add feats + anything else that could function as a pre-req

    return character.chooseable

def chooseable_list_stats(character,attr,stat_name,base,th = None):
    while base <= int(attr):
        suffix = "th" if base >= 4 else {1: "st", 2: "nd", 3: "rd"}.get(base, "th")
        stat = str(stat_name) + str(base) + (suffix if th else "")
        character.chooseable.add(stat)
        base += 1
        if base == 25:
            break


def chooseable_list_class(character,i,class_1,attr,base,th = None):

    while base <= int(attr):
        even = f"{class_1} {2 * (i + 1)}"
        odd = f"{class_1} {2 * i + 1}"

        suffix = "th" if base >= 4 else {1: "st", 2: "nd", 3: "rd"}.get(base, "th")
        class_level_name = str(base) + (suffix if th else "") + " " + str(class_1) + " level" 
        class_level_name_2 = str(class_1) + " level " + str(base) + (suffix if th else "") 
        char_level_name = str(base) + (suffix if th else "") + " " + "character level" 
        char_level_name_2 = "character level " + str(base) + (suffix if th else "")  
        base += 1

        character.chooseable.update([even, odd, class_level_name, class_level_name_2, char_level_name, char_level_name_2])
        if base == 25:
            break            

def chooseable_list_race(character):
    character.chooseable.add(character.chosen_race)

def chooseable_list_class_features(character):
    remove_list = ["aphorite", "aquatic elf", "boggard", "dhampir", "drow", "duergar", "duskwalker", "dwarf", "elf", "fetchling", "gillman", "gnome", "half-elf", "halfling", "half-orc", "human", "kitsune", "nagaji", "oread", "ratfolk", "strix", "tengu", "wayang", "aasimar", "aquatic elf", "catfolk", "dwarf", "elf", "gathlain", "gnome", "goblin", "half-elf", "halfling", "half-orc", "hobgoblin", "human", "kitsune", "kobold", "locathah", "nagaji", "orc", "vanara", "source", "role", "alignment", "hit die", "parent class(es)", "starting wealth", "skill points at each level" ]
    class_keys_list = list(character.class_data.get(character.c_class, "").keys())
    class_keys_list = [key.strip() for key in class_keys_list if key not in remove_list]
    class_keys_list_class_feature = [key + " class feature" for key in class_keys_list]

    
    character.chooseable.update(class_keys_list)
    character.chooseable.update(class_keys_list_class_feature)