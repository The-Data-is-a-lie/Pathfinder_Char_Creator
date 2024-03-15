import random

def versatile_perfomance(character):

    choose_list = [2,6,10,14,18,22,26,30,34,38,42,46,50,54]
    character.performance_chosen_list = set()
    character.performance_chosen_description_list=[]
    character.martial_performance_choice=set()
    expanded_choice_check = set()         
    character.martial_performance_choice_description=[]  
    martial_set = set()      
    versatile_data = character.bard_choices["versatile_perfomances"]
    expanded_data = list(character.bard_choices["expanded_versatility"])
    martial_data = list(character.bard_choices["martial_performance"])

    random_chance = random.randint(1,100)
    performance_list = list(versatile_data.keys())  
    random_chance_martial=0      
    i=0


    if character.c_class == 'bard':
        performance_chosen=random.choice(performance_list)
        performance_chosen_description=versatile_data[performance_chosen]
        character.performance_chosen_description_list.append(performance_chosen_description)
        character.performance_chosen_list.add(performance_chosen)
        i=len(character.performance_chosen_list) 

        #sometimes a bard will just choose all instruments
        while choose_list[i] <= character.c_class_level and random_chance<=50:

            if len(martial_set)>=8:
                break
            
            if len(character.performance_chosen_list)>=8:
                break

            if random_chance_martial<=50:
                performance_chosen=random.choice(performance_list)
                performance_chosen_description=versatile_data[performance_chosen]
                character.performance_chosen_list.add(performance_chosen)
                character.performance_chosen_description_list.append(performance_chosen_description)                    
                i=len(character.performance_chosen_list)
                random_chance_martial = random.randint(1,100)

            if random_chance_martial>50:
                
                martial_choice = random.choice(martial_data)
                martial_set.add(martial_choice)
                print(f'This is your martial choice: {martial_choice}')
                print(f'This is your martial choice: {martial_set}')                    
                i=len(character.performance_chosen_list) + len(martial_set)
                print(f'character.performance_chosen_list {character.performance_chosen_list}')
                print(martial_set.issubset(character.performance_chosen_list))

                if martial_set.issubset(character.performance_chosen_list) == True:
                    character.martial_performance_choice.add(martial_choice)
                    character.martial_performance_choice_description.append(character.bard_choices["martial_performance"][martial_choice])
                    random_chance_martial = random.randint(1,100)



                #reroll random_chance martial
                else:
                    random_chance_martial = random.randint(51,100)
                    martial_set.discard(martial_choice)
                    print(f'martial_set has bee removed {martial_set}')
                #reroll performance
            else:
                random_chance_martial=random.randint(1,50)


    #sometimes a bard will focus on one performance
        while choose_list[i] <= character.c_class_level and random_chance > 50:
            expanded_choice = random.choice(expanded_data)
            print(f'This is your expanded choice {expanded_choice}')                
            expanded_choice_check.add(expanded_choice)
            character.performance_chosen_description_list.append(expanded_choice)
            i=len(expanded_choice_check) + len(character.performance_chosen_list)
            print(f'the number of elements in expanded choices {i}')

            if len(expanded_choice_check)>7:
                break


    print('!!!!!!!!!!!!versatile performance choices !!!!!!!!!!!!!!')
    print(character.performance_chosen_list) 
    print(character.performance_chosen_description_list)  
    print(character.martial_performance_choice)
    print(character.martial_performance_choice_description)     

    return character.performance_chosen_list, character.performance_chosen_description_list, character.martial_performance_choice, character.martial_performance_choice_description   