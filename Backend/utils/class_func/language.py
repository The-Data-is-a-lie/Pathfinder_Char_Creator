import random, re
from utils.class_func.race_func import *
from utils.data import languages as ALL_LANGUAGES

# words that mark a token as descriptive prose rather than a language name
# (e.g. Human's "their ethnic language", "any regional human tongue")
_NON_LANGUAGE_WORDS = {'their', 'ethnic', 'language', 'languages', 'regional',
                       'tongue', 'tongues', 'any', 'want', 'except', 'secret', 'such'}


def language_chooser(character, skill_ranks=None):
    """Return the character's known languages.

    Always includes the race's automatic starting languages ("begin play
    speaking ..."), then adds bonus languages funded by a positive Int
    modifier and any Linguistics ranks, drawn from the race's bonus list
    (or the master list for "choose any" races).
    """
    full_race_data_grab = full_race_data(character)
    language_text = full_race_data_grab.get(character.chosen_race, {}).get('Languages', '')
    if not isinstance(language_text, str):
        language_text = ''

    known = automatic_languages(language_text)
    if getattr(character, 'druidic_flag', False) and 'Druidic' not in known:
        known.append('Druidic')

    bonus_count = max(character.int_mod, 0)
    if skill_ranks:
        bonus_count += skill_ranks.get('linguistics', 0)

    if bonus_count > 0:
        pool = bonus_language_pool(language_text, known)
        known += random.sample(pool, min(bonus_count, len(pool)))

    return known


def automatic_languages(language_text):
    """Parse the race's guaranteed starting languages from its Languages blurb."""
    match = re.search(r'begin play speaking (.*?)(?:\.|$)', language_text)
    if not match:
        return ['Common']
    tokens = split_language_list(match.group(1))
    automatic = []
    for token in tokens:
        token = resolve_either(token)
        if token and not is_prose(token) and token not in automatic:
            automatic.append(token)
    return automatic or ['Common']


def resolve_either(token):
    """Pick one option from 'either Abyssal or Infernal' style tokens."""
    match = re.match(r'(?i)either\s+(.+)', token)
    if match and re.search(r'\bor\b', match.group(1)):
        options = [o.strip(' .') for o in re.split(r'\bor\b', match.group(1))]
        return random.choice([o for o in options if o])
    return token


def bonus_language_pool(language_text, known):
    """Languages the character may pick bonus languages from (excluding known)."""
    if re.search(r'choose any languages', language_text):
        pool = list(ALL_LANGUAGES)
    else:
        match = re.search(r':(.*)', language_text)
        if match:
            pool = [t for t in split_language_list(match.group(1)) if t and not is_prose(t)]
        else:
            pool = list(ALL_LANGUAGES)
    known_lower = {lang.lower() for lang in known}
    return [lang for lang in pool if lang.lower() not in known_lower]


def split_language_list(text):
    """Split 'Common, Dwarven, and Giant' style prose into clean name tokens."""
    text = re.sub(r'\([^)]*\)', '', text)  # drop parentheticals like "(understanding only)"
    tokens = re.split(r',|\band\b', text)
    return [re.sub(r'\s+', ' ', token).strip(' .') for token in tokens]


def is_prose(token):
    return any(word in _NON_LANGUAGE_WORDS for word in token.lower().split())
