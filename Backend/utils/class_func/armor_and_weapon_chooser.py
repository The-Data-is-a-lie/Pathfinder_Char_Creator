import random
import re
from utils import data
# start of Armor + Weapon choosing

# --- Optimized picks (spec 15, rulings 2026-08-11) -----------------------------------------------
# Deterministic best-in-pool selection for the role's weapon policy and for armor AC. Consumes NO
# random draws, and only runs when character.role is set, so random mode's draw pattern is
# untouched. Ties break alphabetically -- stable per seed without touching the stream.

_W_DICE = re.compile(r'(\d+)d(\d+)')
_W_CRIT = re.compile(r'(?:(\d+)\s*-\s*20\s*/\s*)?x\s*(\d+)', re.I)
# Deliberately EMPTY for v1: the rapier is finesse-able but not Light, so picking it turns the
# alpha spine's Piranha Strike (light weapons only) into a dead feat -- the gate's first run
# showed the light+Piranha package outscoring the rapier's wider threat range. Re-add entries
# here only together with a policy that scores the whole package, not the bare weapon.
_FINESSE_EXTRAS = set()


def _weapon_score(entry):
    """Per-swing all-hits damage with crits averaged in -- the metric's own semantics."""
    text = str((entry or {}).get('damage') or '')
    medium = None
    for match in _W_DICE.finditer(text):
        if 'medium' in text[match.end():match.end() + 12].lower():
            medium = match
            break
    medium = medium or _W_DICE.search(text)
    if medium is None:
        return 0.0
    average = int(medium.group(1)) * (int(medium.group(2)) + 1) / 2.0
    crit = _W_CRIT.search(str(entry.get('critical') or 'x2'))
    threat, mult = (1, 2)
    if crit:
        threat = (21 - int(crit.group(1))) if crit.group(1) else 1
        mult = int(crit.group(2))
    return average + (threat / 20.0) * (mult - 1) * average


def _policy_allows(policy, name, entry):
    category = str((entry or {}).get('category') or '').lower()
    ranged = bool(str((entry or {}).get('range') or '').strip()) or 'ranged' in category
    if policy == 'two_handed':
        return 'two-handed' in category and not ranged
    if policy == 'finesse':
        return (('light' in category and not ranged)
                or str(name).strip().lower() in _FINESSE_EXTRAS)
    if policy == 'one_handed_shield':
        return 'one-handed' in category and not ranged
    if policy == 'ranged':
        return ranged
    return True


def optimized_weapon_pick(character, section, useable_weapons):
    """The best usable weapon the role's policy allows, or None to fall back to the random draw."""
    role = getattr(character, 'role', None)
    if not role:
        return None
    policy = role.get('weapon_policy') or 'any'
    if policy == 'any':
        return None
    usable = {str(n) for n in useable_weapons}
    candidates = [n for n, e in section.items()
                  if n in usable and _policy_allows(policy, n, e)]
    if not candidates:
        candidates = [n for n in section if n in usable]
    if not candidates:
        return None
    return max(sorted(candidates), key=lambda n: _weapon_score(section[n]))


def optimized_armor_pick(character, section):
    """The armor (or shield) whose bonus plus usable Dex is highest -- role-agnostic AC math."""
    role = getattr(character, 'role', None)
    if not role or not section:
        return None
    dex_mod = int(getattr(character, 'dex_mod', 0) or 0)

    def total_ac(entry):
        try:
            bonus = int(str((entry or {}).get('armor bonus') or 0).strip() or 0)
        except ValueError:
            bonus = 0
        raw_dex = str((entry or {}).get('max dex bonus') or '').strip()
        try:
            usable_dex = min(dex_mod, int(raw_dex)) if raw_dex and raw_dex != '—' else dex_mod
        except ValueError:
            usable_dex = dex_mod
        return bonus + usable_dex

    return max(sorted(section), key=lambda n: total_ac(section[n]))
    
# Start of AC calculation
def ac_bonus_calculator(character, dictionary):
    if dictionary is None:
        return 0

    for _, value in dictionary.items():
        armor_bonus = value.get('armor bonus', 0)
    return armor_bonus

def shield_chooser(character, dictionary):
    shieldless_weapons = ["Two-Handed", "Ranged"]
    for item in dictionary.values():
        category = item.get('category', 'no shield')
        limits = 'Shield' if all(weapon not in category for weapon in shieldless_weapons) else 'no shield'
    if limits == 'Shield' and (character.armor_type == 'H' and random.randint(1,100)>90):
        limits = 'Tower'
        return limits
def shield_flag_func(character, limits):
    if limits == 'Shield' or limits == 'Tower':
        character.shield_flag = True
    else:
        character.shield_flag = False
    
def weapon_type_flag_func(character, dictionary):
    for item in dictionary.values():
        if item.get('category', 'no shield') == 'Ranged':
            weapon_type = 'Ranged'
        else:
            weapon_type = 'Melee'
    return weapon_type

def list_selection(character, name, limits=None, shield_flag=True):
    if shield_flag == True:
        useable_weapons = getattr(data, 'useable_weapons')
        if limits is not None:
            choice = list_selection_limits(character, name, limits)
        else:
            choice = random.choice(list(getattr(character, name).keys()))

        section = getattr(character, name).get(choice, {})
        result = list(section.keys())

        # OPTIMIZED MODE (spec 15): the role's weapon policy (or straight AC math for armor and
        # shields) picks the best of the same legal pool, deterministically and without touching
        # the RNG. A None fall-through -- no role, or a policy of 'any' -- is the random draw.
        choice_2 = None
        if name == 'weapons_data':
            choice_2 = optimized_weapon_pick(character, section, useable_weapons)
        elif name == 'armor':
            choice_2 = optimized_armor_pick(character, section)
        if choice_2 is None:
            choice_2 = random.choice(result)
        result_2 = section.get(choice_2, {})

        result_dict = {choice_2: result_2}
        reroll_weapon(character, name, list(result_dict.keys())[0], useable_weapons, result)


        return result_dict

def list_selection_limits(character, name, limits=None):
    skip_count = {'L': 0, 'S':0, 'M': 1, 'H': 2, 'Shield': 3, 'Tower': 4}.get(limits, 0)
    attribute_keys = iter(getattr(character, name))
    key = next(attribute_keys, None)            

    for _ in range(skip_count):
        key = next(attribute_keys, None)
        if key is None:
            break
    return key

# Reroll weapon can take a few seconds -> (we may want to just make it output a specific weapon if it doesn't exist in the list rather than a while statement)
def reroll_weapon(character, name, choice, useable_weapons, result):
    if name == 'weapons_data':
        y = 0
        while choice not in useable_weapons:
            choice = random.choice(result)
            y += 1
            if y > 5:
                choice = 'longsword'
                break
    return choice

# here to help create AC calculation
def armor_chooser(character):
    armor_type_data = getattr(data, 'armor_type_mapping')
    default_armor_type = 'H'  # Default armor type

    armor_type = armor_type_data.get(character.c_class, default_armor_type)
    if character.bab == 'L':
        armor_type = None

    magus_armor_chooser(character, character.c_class_level)

    character.armor_type = armor_type
    return character.armor_type   


def weapon_chooser(character):
    useable_weapons = getattr(data, 'useable_weapons')

    weapon_type_data = character.class_data.get(character.c_class, {}).get('weapon and armor proficiency')
    character.weapon_type = 'M' if 'martial' in weapon_type_data else 'S'
    return character.weapon_type


def magus_armor_chooser(character, level):
    from utils.class_func.generic_func import class_entry_for
    magus_entry = class_entry_for(character, 'magus')
    if magus_entry is not None:
        level = magus_entry['level']
        character.armor_type = 'L'
        if level >= 7:
            character.armor_type = 'M'
        elif level >= 13:
            character.armor_type = 'H'

        return character.armor_type
    
