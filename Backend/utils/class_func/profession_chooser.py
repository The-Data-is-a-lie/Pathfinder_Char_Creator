import random
from utils import data
def profession_chooser(character,professions):
    """
    *** Will need to enhance the list, maybe redo it from scratch ***
    randomly selects a profession from the list in the data tab
    """
    n = random.randint(1,3)
    profession_data = getattr(data,professions)
    character.profession_chosen = random.sample(profession_data,k=n)

    return character.profession_chosen