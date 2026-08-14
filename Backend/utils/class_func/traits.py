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


# The house wall's trait pick (V4 wall pass, ruling 2026-08-13). NOT in data/traits.csv on
# purpose: trait_selector samples that whole pool, so a CSV row would leak into random mode and
# move the goldens. The +1 the metric scores lives in power_adders.json::posture
# (cautious_warrior_trait), keyed to this name appearing in selected_traits.
HOUSE_WALL_TRAIT = {
    'name': 'Cautious Warrior',
    'description': ('You know when to fight carefully. Benefit: You gain an additional +1 dodge '
                    'bonus to your Armor Class when fighting defensively or using total defense. '
                    "(Sieg's table combat trait, ruling 2026-08-13.)"),
}


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
    # Full house-rules wall: the last sampled slot yields to Cautious Warrior, so the count is
    # unchanged and no RNG draw is added or skipped (the sample above already consumed the same
    # stream either way -- random mode and house-off optimized mode are untouched by construction).
    role = getattr(character, 'role', None)
    if (role and role.get('_house') and 'ac_combat' in (role.get('primaries') or [])
            and HOUSE_WALL_TRAIT['name'] not in trait_list):
        trait_list = trait_list[:max(0, count - 1)] + [HOUSE_WALL_TRAIT['name']]
        character.selected_traits_desc = (character.selected_traits_desc[:max(0, count - 1)]
                                          + [dict(HOUSE_WALL_TRAIT)])
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