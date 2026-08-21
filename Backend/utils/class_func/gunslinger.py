from math import floor, ceil
import random
from utils import data
from utils.class_func.generic_func import class_entry_for, levels_for, record_bucket_owner

def choose_gun_func(character, c_class):
    gunslinger_entry = class_entry_for(character, 'gunslinger')
    if gunslinger_entry is None:
        return []

    # Was an inline floor((level - 1) / 4) -- the FIFTH pick-count convention, found by ticket 02's
    # sweep rather than by reading call sites, because nothing linked it to the other four.
    # start=5/every=4 in the schedule reproduces it exactly at every level.
    x = len(levels_for(character, 'gunslinger', 'gun training', gunslinger_entry['level']))
    firearms = {**character.firearms.get('Siege', {}), **character.firearms.get('Firearm', {}) }
    sections = list(firearms.keys())
    chosen_weapons = set()
    useable_weapons = getattr(data, 'useable_weapons')

    # The pool can run dry before the count does -- `sections` is filtered down to useable_weapons
    # inside the loop, so a firearms list with fewer useable categories than `x` spun forever.
    # Same shape as the exhaustion break generic_class_option_chooser gained in ticket 01, and
    # reachable for the same reason: nothing capped the class level, so a gunslinger 40 asks for
    # nine categories from a list that has fewer.
    pickable = [s for s in sections if s in useable_weapons]
    x = min(x, len(pickable))

    while len(chosen_weapons) < x:
        chosen_weapons.add(random.choice(pickable))

    result = {"gun training": list(chosen_weapons)}

    # Gun training starts at 5th, so `x` is 0 for a gunslinger 1-4 and there is nothing to file.
    # Writing the key anyway put an empty bucket on the sheet, and now that this chooser records an
    # owner that empty bucket would draw its own empty Class Features divider.
    if not chosen_weapons:
        return result

    # MERGE, never assign. This used to be `data_dict.update({'class features': result})`, which
    # replaced the whole bucket dict -- so every character with a gunslinger level silently lost
    # the rage powers, terrors and discoveries its other classes had already chosen, because this
    # chooser runs last in phase_class_options. The `class feature owners` side-table kept naming
    # those buckets, so the payload shipped owners pointing at buckets that no longer existed:
    # "generated but invisible" with the picks not merely unreachable but gone. Every other chooser
    # carries a comment saying merge rather than assign; this one did the opposite.
    if character.data_dict['class features'] in ([], {}):
        character.data_dict['class features'] = result
    else:
        character.data_dict['class features']["gun training"] = result["gun training"]
    record_bucket_owner(character, "gun training", gunslinger_entry['name'])
    return result
        
