import random, re
from utils.class_func.race_func import *
def language_chooser(character):
    full_race_data_grab = full_race_data(character)
    language_text = full_race_data_grab.get(character.chosen_race, {}).get('Languages', [])        
    regex = ':(.*)'
    captured_content = regex_search(character,language_text, regex)
    language_list = language_splitter(character,captured_content)
    languages = random_language_chooser(character,language_list, character.int_mod)
    
    return languages

def regex_search(character, string, regex):
    pattern = rf"{regex}"
    match = re.search(pattern, string)
    if match:
        captured_content = match.group(1)
        print(captured_content)
    else:
        captured_content = []

    print(f'this is your captured_content {captured_content}')
    return captured_content

def language_splitter(character, language_text):
    pre_language_list = language_text.split(",")
    language_list = []
    for lang in pre_language_list:
        lang = lang.strip().lower()
        lang = remove_word(character,lang, 'and')
        language_list.append(lang)
    return language_list

def random_language_chooser(character, language_list, number):
    k=min(number, len(language_list))
    if k < 0:
        k =0
    languages = random.sample(language_list, k)
    return languages

def remove_word(character, string, word_to_remove):
    new_string = string.replace(word_to_remove, '')
    new_string = new_string.replace('.', '').replace(' ', '')
    return new_string