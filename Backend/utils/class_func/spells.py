import random, json, sys, math
from math import ceil, floor
from Backend.utils import data
import pandas as pd

def class_for_spells_attr(character):
    #currently we only know that skald spells aren't proper, but 
    # skalds use bard spell list -> just have an if statement for them 
    # CON 10
    # INT 12
    # investigators use alchemists spells
    # + check others
            
    #This is a quick and easy function to make it so we search
    #for different spell lists than our current class
    if character.c_class in ['skald']:
        character.c_class_for_spells = 'bard'
    elif character.c_class in ['investigator']:
        character.c_class_for_spells = 'alchemist'
    elif character.c_class in ['witch', 'arcanist']:
        character.c_class_for_spells='wizard' 
    elif character.c_class in ['warpriest', 'oracle']:
        character.c_class_for_spells='cleric'    
    elif character.c_class in ['summoner (unchained)']:
        character.c_class_for_spells='summoner'               
    else:
        character.c_class_for_spells = character.c_class     
    return character.c_class_for_spells



def caster_formula(character,n, class_2 = 'missing'):
    print(f'this is your damn class 2: {class_2}')
    character.casting_level_string = str(character.classes.get(character.c_class, "").get("casting level", "").lower())
    character.casting_level_num = character.c_class_level

    if character.casting_level_string == 'high':
        if n % 2 == 0:
            highest_spell_known=n // 2
        else:
            highest_spell_known=(n + 1) // 2
        highest_spell_known = min(highest_spell_known,9)

    elif character.casting_level_string == 'mid':
        if n % 3 == 1:
            highest_spell_known= ceil(n // 3)+1
        else:
            highest_spell_known= ceil(n / 3)
        highest_spell_known = min(n,6)           
    
    elif character.casting_level_string == 'low':
        highest_spell_known= ceil(n / 3)-1
        highest_spell_known = min(highest_spell_known,4)           
        character.casting_level_num -= 3


    else:
        highest_spell_known = 0 
        character.casting_level_num = 0

    if class_2 == 'missing':
        character.highest_spell_known_1 = highest_spell_known
        return character.highest_spell_known_1    
    else:
        character.highest_spell_known_2 = highest_spell_known
        return character.highest_spell_known_2


#need to create this for casting_level_2 as well
def spells_known_attr(character,base_classes, divine_casters):     
    base_classes = getattr(data,base_classes)
    divine_casters=getattr(data, divine_casters)    
    character.casting_level_string = str(character.classes[character.c_class]["casting level"].lower())         
    character.spells_known_list = []
    list = []    


    if character.c_class in base_classes and character.casting_level_string == 'high' and character.c_class not in divine_casters:
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)
            list=character.spells_known[character.c_class][key][character.capped_level_1-1]
            character.spells_known_list.append(list)
    elif character.c_class in base_classes and character.casting_level_string == 'mid' and character.c_class not in divine_casters and character.c_class != 'alchemist':
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)                
            list=character.spells_known[character.c_class][key][character.capped_level_1-1]
            character.spells_known_list.append(list)

    #Low casters + some mid casters don't have orisons/cantrips [but we just have 0 for spells known + spells per day so it doesn't select any]
    elif character.c_class == 'alchemist':
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)                
            list=character.spells_known[character.c_class][key][character.capped_level_1-1]
            character.spells_known_list.append(list)

    elif character.c_class in base_classes and character.casting_level_string == 'low' and character.c_class not in divine_casters:
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)                
            list=character.spells_known[character.c_class][key][character.capped_level_1-1]
            character.spells_known_list.append(list)
    elif character.c_class in divine_casters:
        print('Divine Casters know all spells')
    else:
        print('Not an Arcane caster')

    return character.spells_known_list

def spells_known_extra_roll(character):
    extra_spell_list = []        
    if character.c_class_for_spells in ['alchemist','wizard'] :
        for i in range(0,character.highest_spell_known_1 + 1):
            extra_spells = random.randint(1,10)
            extra_spell_list.append(extra_spells)

            # Remove 'null' values and ensure both lists have the same number of non-null elements
            filtered_spells_known = [0 if x == 'null' else x for x in character.spells_known_list]
            filtered_extra_spells = extra_spell_list[:len(filtered_spells_known)]

            if filtered_spells_known[i] == 0:
                filtered_extra_spells[i] = 0

            print(filtered_extra_spells)
            print(f'This is the spells known {filtered_spells_known}')

            # Add corresponding elements of both lists
            result = [x + y for x, y in zip(filtered_spells_known, filtered_extra_spells)]

        character.spells_known_list=result
        print(f'This is the spells known list {character.spells_known_list}')

    return character.spells_known_list

def alignment_spell_limits(character, spell_data, i, alignment_exclusion):
    """
    Creates flags to limit spell choices to only be within the character's alignment for all classes 
    (not just cleric to make characters more thematic)

    return: query_i 
    params: spell_data (pandas file), i (number)
    """
    alignment = character.alignment.lower()
    extraction_list = ['name', 'school']#, character.c_class_for_spells 'lawful', 'chaotic', 'evil', 'good']
    alignment_exclusion = getattr(data, alignment_exclusion)


    excluded_columns = set()

    for alignment_part in alignment.split(' '):
        excluded_column = alignment_exclusion.get(alignment_part)
        if excluded_column:
            excluded_columns.add(excluded_column)

    condition = spell_data[character.c_class_for_spells] == i

    for col in excluded_columns:
        condition &= (spell_data[col] == 0)

    query_i = spell_data.loc[condition, extraction_list]
    # selecting spells by randomly selected thematic schools
    query_i = limit_school_func(character, query_i)

    return query_i

def spell_theme_func(character, spell_data):
    character.available_schools = spell_data['school'].value_counts()
    character.available_schools = character.available_schools[character.available_schools > 30].index.tolist()    
    # grab a list of chooseable spell schools
    num_of_schools = random.randint(1,2)
    specialty_schools = random.sample(character.available_schools, num_of_schools)
    for school in specialty_schools:
        print(school)
        character.available_schools.remove(school)
    remaining_schools = character.available_schools
    counter_schools = random.sample(remaining_schools, num_of_schools)

    character.specialty_schools = specialty_schools
    character.counter_schools = counter_schools

def limit_school_func(character, query_i):
    #apply weights
    query_i['weight'] = 1
    query_i.loc[query_i['school'].isin(character.specialty_schools), 'weight'] = 100
    query_i.loc[query_i['school'].isin(character.counter_schools), 'weight'] = .1

    return query_i.sort_values(by='weight', ascending=False)
    



def spells_known_selection(character,base_classes,divine_casters):
    spell_data=pd.read_csv('data/spells.csv', sep='|')
    spell_theme_func(character, spell_data)

    #extraction_list = ['name', character.c_class]                
    character.spell_list = []
    character.casting_level_string = str(character.classes[character.c_class]["casting level"].lower())         
    base_classes=getattr(data,base_classes)
    divine_casters=getattr(data, divine_casters)
    i=0
    character.spell_list_choose_from=[]
    all_spell_names = []
    
    #separating the lists
    known_list = character.spells_known_list
    day_list = character.spells_per_day_list

    #we need to make sure we aren't grabbing null or our program will break
    if character.casting_level_string != 'none' and character.c_class in base_classes and character.c_class not in divine_casters:
        while i <= character.highest_spell_known_1:
            print(known_list)
            print(i)
            if known_list[i] != 'null':
                select_spell=known_list[i]             

                query_i = alignment_spell_limits(character, spell_data, i, "alignment_exclusion")
                query_i = query_i.sample(weights=query_i['weight'], frac=1.0)
                spells = query_i[:select_spell]
                spell_list = spells['name'].tolist()

                character.spell_list_choose_from.append(spell_list)

                i += 1 




            else:
                break     

    elif character.casting_level_string != 'none' and character.c_class in divine_casters:   
        day_list = extra_spells_divine(day_list)
        while i <= character.highest_spell_known_1:
            print(f'this is i {i}')
            print('day_list: ', day_list[i])
            print(f"i: {i}, len(day_list): {len(day_list)}")
            print(day_list)


            if day_list[i] != 'null':
                
                select_spell=day_list[i]         

                query_i = alignment_spell_limits(character, spell_data, i, "alignment_exclusion")                        
                query_i = query_i.sample(weights=query_i['weight'], frac=1.0)
                spells = query_i[:select_spell]
                spell_list = spells['name'].tolist()
                character.spell_list_choose_from.append(spell_list)

                i += 1 
            else:
                break                 

    else:
        print('cannot select spells_known_selection')

    # for df in character.spell_list_choose_from:
    #     spell_names = df['name'].tolist()
    #     all_spell_names.extend(spell_names)

    # character.spell_list_choose_from = all_spell_names

    return character.spell_list_choose_from, day_list, known_list

# remove if need to give an accurate spells per day (only for foundryVTT (to have more spells populate in list))
def extra_spells_divine(day_list):
    # we need i,num > 0 otherwise it breaks here (B/c divine casters + cantrips/irisons breaks)
    for i in range(len(day_list) -1):
        random_num = random.randint(1,10)
        print("day_list[i]: ", day_list[i])
        # me sure we don't break for mid/low casters
        if day_list[i] == 'null':
            return day_list

        day_list[i] = day_list[i] + random_num
    return day_list


    

def spells_per_day_attr(character, base_classes):
    # We have to use normal spell class, since certain classes like Arcanist or Witch have the same spells but diff progressions as wizard/sorc 
    base_classes = getattr(data,base_classes)  
    character.spells_per_day_list = []
    list = []            

    if character.c_class in base_classes and character.casting_level_string == 'high':
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)
            print(character.c_class)
            list=character.spells_per_day[character.c_class][key][character.capped_level_1-1]
            character.spells_per_day_list.append(list)
    elif character.c_class in base_classes and character.casting_level_string == 'mid' and character.c_class != 'alchemist':
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)                
            list=character.spells_per_day[character.c_class][key][character.capped_level_1-1]
            character.spells_per_day_list.append(list)

    #adding an exception for alchemist (+ other classes that don't receive cantrips)
    elif character.c_class == 'alchemist':
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)                
            list=character.spells_per_day[character.c_class][key][character.capped_level_1-1]
            character.spells_per_day_list.append(list)        
    elif character.c_class in base_classes and character.casting_level_string == 'low':
        for i in range(0,character.highest_spell_known_1+1):
            key = str(i)                
            list=character.spells_per_day[character.c_class][key][character.capped_level_1-1]
            character.spells_per_day_list.append(list)                



    else:
        print('Not an spell list caster')

    return character.spells_per_day_list            




def spells_per_day_from_ability_mod(character, caster_mod):
    caster_mod = getattr(data,caster_mod)
    dataset = character.spells_from_ability_mod
    #for now we make sure it can't be above 17 -> otherwise breaks
    int_str = str(min(character.int_mod,17))
    wis_str = str(min(character.wis_mod,17))
    cha_str = str(min(character.cha_mod,17))
    i=0
    i_2=0
    bonus_spells = []
    if character.c_class in caster_mod["int_casters"]:
        list=dataset[int_str]          
        for i in range (character.highest_spell_known_1):
            i+=1
            spells= list[i]
            bonus_spells.append(spells)
    if character.c_class in caster_mod["wis_casters"]:
        list=dataset[wis_str]         
        for i in range (character.highest_spell_known_1):
            i+=1
            spells= list[i]
            bonus_spells.append(spells)
    if character.c_class in caster_mod["cha_casters"]:
        list=dataset[cha_str]          
        for i in range (character.highest_spell_known_1):
            i+=1
            spells= list[i]
            bonus_spells.append(spells)                                
    else:
        print('Not a caster sorry bucko')

    return bonus_spells