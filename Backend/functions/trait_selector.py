def trait_selector(count):
    trait_data = pd.read_csv('data/traits.csv', sep='|')
    extraction_list = ['name', 'description']
    query_i = trait_data[extraction_list]
    query_i = query_i.sample(frac=1.0)
    traits = query_i[:count]
    return traits