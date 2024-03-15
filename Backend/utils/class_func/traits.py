import pandas as pd
def trait_selector(character, count):
    trait_list = []
    trait_data = pd.read_csv('data/traits.csv', sep='|')
    extraction_list = ['name']#, 'description']
    conditions = trait_selector_limits(character, trait_data)
    query_i = trait_data.loc[conditions,extraction_list]
    query_i = query_i.sample(frac=1.0)
    traits = query_i[:count]
    trait_list = traits['name'].to_list()

    return trait_list

def trait_selector_limits(character, trait_data):
    conditions = ( (trait_data['requirement_race'] == character.chosen_race) &
                    (trait_data['requirement_class'] == character.c_class)
                |
                (trait_data['requirement_race'].isnull()) &
                (trait_data['requirement_class'].isnull())                    
                )
                #   trait_data['requirement_faith'] == ,
                #   trait_data['requirement_alignment'] == character.alignment
                    
    return conditions