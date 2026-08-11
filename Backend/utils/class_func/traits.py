import pandas as pd
from utils.paths import repo_path

_TRAIT_DATA = None


def _trait_data():
    """data/traits.csv, parsed once per process. This was re-read on EVERY trait_selector call --
    the only loader in the package without a cache (cf. _FLAWS_CACHE in flaws.py, _SPELL_DATA in
    spells.py). Returns a copy so a caller filtering the frame can't poison the cache."""
    global _TRAIT_DATA
    if _TRAIT_DATA is None:
        _TRAIT_DATA = pd.read_csv(repo_path('data/traits.csv'), sep='|')
    return _TRAIT_DATA.copy()


def trait_selector(character, count):
    trait_data = _trait_data()
    extraction_list = ['name', 'description']
    conditions = trait_selector_limits(character, trait_data)
    query_i = trait_data.loc[conditions, extraction_list]
    query_i = query_i.sample(frac=1.0)
    traits = query_i[:count]
    trait_list = traits['name'].to_list()
    # Stash name -> description for the backstory generator (the exported `selected_traits`
    # name list is unchanged). Descriptions may be blank/NaN in the CSV.
    character.selected_traits_desc = [
        {'name': str(r['name']),
         'description': '' if pd.isna(r['description']) else str(r['description']).strip()}
        for _, r in traits.iterrows()
    ]
    return trait_list

def trait_selector_limits(character, trait_data):
    # class-gated traits match ANY of the character's classes (multiclass-aware)
    class_names = [c['name'] for c in character.classes]
    conditions = ( (trait_data['requirement_race'] == character.chosen_race) &
                    (trait_data['requirement_class'].isin(class_names))
                |
                (trait_data['requirement_race'].isnull()) &
                (trait_data['requirement_class'].isnull())
                )
                #   trait_data['requirement_faith'] == ,
                #   trait_data['requirement_alignment'] == character.alignment

    # NOTE for anyone tempted to add Luck Traits here: they do not belong in this pool. The Luck doc
    # is explicit -- "Luck Traits may only be purchased with E-Kats" -- so they are not character
    # traits at all. An earlier pass did add two of them (Expanded Luck, Big Savings) to
    # data/traits.csv and gate them here; both are removed. The real system is the 25-E-Kat purchase
    # in phase_luck_resolution, reading Backend/json/feats/luck_traits.json.
    return conditions