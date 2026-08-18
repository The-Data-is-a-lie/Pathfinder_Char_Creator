import json
import os
import random
import re
from utils import data
# start of Armor + Weapon choosing

# --- Gear legality (plan docs/plan_gear_legality.md, rulings D3/D4/D5) ---------------------------
# The band a character may wear comes from Backend/json/armor_proficiency.json, which is DERIVED
# from class_data.json's own proficiency prose and gated by
# Backend/scripts/gates/validate_gear_legality.py.
#
# What it replaces: `data.armor_type_mapping`, whose keys were tuples while the lookup passed a
# string. It never matched once, so every character in this repo's history took the 'H' default --
# a wizard in Full plate, a druid in Half-plate -- and when the band was None, `list_selection`
# drew a RANDOM SECTION out of all five, Shields and Tower included.

_PROFICIENCY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'json', 'armor_proficiency.json')
_PROFICIENCY = None

# Weakest to strongest; index() is the comparison D5's union and cap both need.
ARMOR_BANDS = (None, 'L', 'M', 'H')
# armor.json's section per band.
BAND_SECTION = {'L': 'Light', 'M': 'Medium', 'H': 'Heavy'}

# THE SHIFTER RULING, made in the open. The shifter's prose prohibits metal armour and never says
# what is left, and armor.json carries no material column, so there is nothing to resolve it
# against (validate_gear_legality.py reports this as a standing gap on every run). The druid's
# taboo is the same taboo one sentence longer, so the druid's own allowlist is what a
# metal-prohibited class without a list of its own gets. Named here rather than inlined so the
# ruling is greppable from the gate that reports the gap.
_METAL_FREE_FALLBACK = ('Padded', 'Leather', 'Hide')


def armor_proficiency():
    """Backend/json/armor_proficiency.json's class table, read once."""
    global _PROFICIENCY
    if _PROFICIENCY is None:
        with open(_PROFICIENCY_PATH, encoding='utf-8') as handle:
            _PROFICIENCY = json.load(handle).get('classes', {})
    return _PROFICIENCY


def _rolled_class_names(character):
    """Every class on the character, or its single class when the roll produced no list."""
    names = [entry['name'] for entry in getattr(character, 'classes', []) or [] if entry.get('name')]
    return names or [getattr(character, 'c_class', None)]


def _row_for(table, name):
    """The table row for a class, tolerating the ' (unchained)' stripping done mid-pipeline."""
    if not name:
        return None
    return table.get(name) or table.get(str(name).replace(' (unchained)', ''))

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
        # `limits is None` means NOTHING IS LEGAL -- no armour band, no shield -- and the answer is
        # to wear nothing. It used to fall through to a random draw over ALL FIVE armor.json
        # sections, which is how an unarmoured class ended up in a Tower shield, and it is the
        # single line that made `armor_type = None` unsafe to set honestly.
        if limits is None:
            return None
        choice = list_selection_limits(character, name, limits)

        section = getattr(character, name).get(choice, {})
        result = list(section.keys())

        # The druid/shifter taboo (D4). Applied to the item list rather than to the band, so the
        # band stays the rules answer and the taboo stays a filter over it. `_legal_band` has
        # already walked down to a band this cannot empty.
        allowed = getattr(character, 'armor_allow', None)
        if name == 'armor' and allowed:
            legal = [item for item in result if item in allowed]
            if legal:
                result = legal
                section = {item: section[item] for item in legal}

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

def armor_allowlist(character):
    """The exact armour names a character is limited to, or None when nothing limits them.

    D5's "intersection of restrictions": a taboo one class carries binds the whole character. A
    druid/fighter is still a druid, and the fighter's freedom does not launder the druid's metal
    prohibition -- so the allowed SETS intersect even though the bands union.
    """
    table = armor_proficiency()
    allowed = None
    for name in _rolled_class_names(character):
        row = _row_for(table, name)
        if not row:
            continue
        names = row.get('armor_allow')
        if not names and row.get('metal_prohibited'):
            names = list(_METAL_FREE_FALLBACK)
        if not names:
            continue
        allowed = set(names) if allowed is None else (allowed & set(names))
    return allowed


def _legal_band(character):
    """D3 + D5: the heaviest band every rolled class agrees to, capped for arcane casters."""
    table = armor_proficiency()
    band, capped_by = None, None

    for name in _rolled_class_names(character):
        row = _row_for(table, name)
        if row is None:
            # An unknown class is NOT silently promoted to heavy the way the old default did.
            # Nothing legal is known about it, so it wears nothing and the gate says which class.
            continue
        if ARMOR_BANDS.index(row['armor']) > ARMOR_BANDS.index(band):
            band = row['armor']

    # ...then the cap. An arcane caster's spells fail in anything its own class does not exempt, so
    # the band drops to that exemption -- to nothing at all for a wizard or sorcerer, which have no
    # exemption to give. This is why a wizard/fighter goes unarmoured rather than into plate, and
    # it is deliberate: ruling D5 says a rolled caster must not be broken by the armour roll.
    for name in _rolled_class_names(character):
        row = _row_for(table, name)
        if not row or not row.get('asf_sensitive'):
            continue
        cap = (row.get('asf_exempt') or {}).get('armor')
        if ARMOR_BANDS.index(cap) < ARMOR_BANDS.index(band):
            band, capped_by = cap, name

    # A taboo can make a band unreachable: the heaviest section with nothing legal in it is not the
    # heaviest LEGAL band. Walk down until something in the section survives the allowlist.
    allowed = armor_allowlist(character)
    if allowed is not None:
        sections = getattr(character, 'armor', {}) or {}
        while band is not None and not (allowed & set(sections.get(BAND_SECTION[band], {}))):
            band = ARMOR_BANDS[ARMOR_BANDS.index(band) - 1]

    character.armor_capped_by = capped_by
    return band


# here to help create AC calculation
def armor_chooser(character):
    """Set `character.armor_type` to the heaviest band the character may legally wear.

    None means NO ARMOUR and is honoured as such by `list_selection`. It used to mean "no limit",
    which is how the random-section draw reached Shields and Tower.
    """
    character.armor_allow = armor_allowlist(character)
    character.armor_type = _legal_band(character)
    return character.armor_type


def weapon_chooser(character):
    useable_weapons = getattr(data, 'useable_weapons')

    weapon_type_data = character.class_data.get(character.c_class, {}).get('weapon and armor proficiency')
    character.weapon_type = 'M' if 'martial' in weapon_type_data else 'S'
    return character.weapon_type


# `magus_armor_chooser` lived here and is gone. It promoted a magus to medium armour at 7th and
# (via an `elif` that could never be reached after the `if` above it) heavy at 13th. Both are real
# magus class features, and both are now MOOT: the magus's arcane spell failure exemption covers
# light armour only, so D5's caster cap holds it at Light no matter what it is proficient with.
# Keeping the function would have left a level ladder that computes a band nothing uses -- the
# precise shape of dead code this plan exists to remove. The class features themselves are
# unaffected; what changed is which armour the generator hands the character.
