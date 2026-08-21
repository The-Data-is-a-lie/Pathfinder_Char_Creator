from utils import data
import random, re
# Start enhnacement to Armor + Weapons

# --- Enhancement budget -------------------------------------------------------------------------
# Tuning levers. ENHANCEMENT_SHARE is the fraction of the purse reserved for magic enhancements
# before ordinary gear is bought; the rest (and anything the tiers can't use) goes to item_chooser.
# Raising it buys bigger pluses at the cost of gear, lowering it does the reverse.
ENHANCEMENT_SHARE = 0.5
# How the reserve splits across the three slots. Explicit proportions, NOT the old 3/2/1 divisor
# cascade: under that cascade each call took a fraction of what was LEFT, so whichever slot ran last
# swallowed the remainder -- and that was the shield. It produced armor +8 / weapon +8 / shield +9 at
# high wealth, and at 5,000 gp a character enchanted its shield and nothing else. Weapon first is the
# priority that actually matters for an NPC.
ENHANCEMENT_SPLIT = {'weapon': 0.50, 'armor': 0.35, 'shield': 0.15}


def plan_enhancements(character, share=ENHANCEMENT_SHARE, has_shield=None):
    """Buy an enhancement tier per slot out of a reserved share of the purse.

    Returns ``{'weapon': n, 'armor': n, 'shield': n}`` of effective +N budgets (0 where nothing was
    affordable) and deducts the cost from ``character.gold``.

    Why a reserve: this used to run AFTER item_chooser, which drains the purse, so a realistically
    funded NPC never bought a weapon or armor quality at all -- enhancement_effects_dict was empty
    for every normal character. It now runs first against ``share`` of the gold, and gear spends what
    is left plus whatever the tier table couldn't use.

    A shieldless character is charged nothing for a shield (``enhancement_chooser`` returns ([], 0)
    for one, so the old code paid for an enchantment that was never received -- and with divisor 1 it
    was the largest of the three deductions). Its share is redistributed to weapon and armor rather
    than banked.

    Tiers come from ``data.enhancement_bonus_mapping`` (cost -> +N). Each slot takes the largest tier
    at or below its slice, and every purchase is also checked against ACTUAL gold, so the reserve can
    never overdraw the purse.
    """
    mapping = getattr(data, 'enhancement_bonus_mapping')
    out = {'weapon': 0, 'armor': 0, 'shield': 0}
    if not isinstance(character.gold, int) or character.gold <= 0:
        return out

    if has_shield is None:
        has_shield = bool(getattr(character, 'shield_flag', False))

    # Optimized mode (spec 15): the role's own split replaces the hardcoded one -- a controller
    # puts the reserve into armor, a wall into armor+shield. Random mode never has a role, so the
    # constant keeps owning that path and the goldens do not move.
    role = getattr(character, 'role', None)
    split = dict((role or {}).get('enhancement_split') or ENHANCEMENT_SPLIT)
    if not has_shield:
        # Give the shield's share to the other two in proportion, so a shieldless character spends
        # its full reserve on the gear it actually carries.
        freed = split.pop('shield')
        total = sum(split.values())
        split = {slot: frac + freed * (frac / total) for slot, frac in split.items()}

    reserve = int(character.gold * share)
    for slot in ('weapon', 'armor', 'shield'):
        if slot not in split:
            continue
        budget = int(reserve * split[slot])
        affordable = [key for key in mapping if key <= budget and key <= character.gold]
        if not affordable:
            continue
        best_key = max(affordable)
        character.gold -= best_key
        out[slot] = mapping[best_key]
    return out

def enhancement_chooser(character, data, enhancement_bonus, weapon_type, shield_type = True):
    """Returns (chosen quality names, flat +N enhancement bonus).

    enhancement_bonus is the total effective bonus budget (PF pricing, up to +10). The FLAT +N is
    reserved FIRST -- min(5, budget) -- and qualities spend only what is left, never overshooting.

    It used to be the other way around: qualities bought first (`while budget - total > 5`) and the
    flat +N was the leftover, so a +10 budget routinely yielded a +3 weapon wearing +7 of qualities
    -- measured at a 1.5M-gp purse -- and an overshooting quality granted bonus value the budget
    never paid for. Flat-first is also the PF1e shape: the flat enhancement is what every attack
    and AC roll actually feels, and an item legally needs it before any quality. (Which qualities
    load stays a uniform draw -- preferring the strong one is the optimizer's job, not random
    mode's. Map: optimal-builder, ruling 2026-08-11.)
    """
    if weapon_type == 'Shield' and shield_type != True:
        return [], 0
    else:
        enhancement_list = list(data.get(weapon_type).keys())
        chosen_enhancement_list = []
        flat_bonus = max(1, min(5, enhancement_bonus)) if enhancement_bonus >= 1 else 0
        remaining = enhancement_bonus - flat_bonus

        def cost_of(name):
            return int((data[weapon_type].get(name, {}) or {}).get('enhancement', 0) or 0)

        # Stop as soon as nothing left in the pool can still reduce `remaining`: without this, a
        # pool holding only zero-cost flavour qualities would be vacuumed wholesale onto every
        # high-budget item. Zero-cost qualities can still ride along while real shopping happens,
        # which is the old behaviour.
        while (remaining > 0 and enhancement_list
               and any(0 < cost_of(name) <= remaining for name in enhancement_list)):
            chosen_enhancement = random.choice(enhancement_list)
            enhancement_list.remove(chosen_enhancement)
            item_list = get_enhancement_info(character, weapon_type)
            enhancement_limits(character, item_list, weapon_type, chosen_enhancement)
            cost = cost_of(chosen_enhancement)
            if cost > remaining:
                continue          # does not fit -- skip it, never overshoot
            remaining -= cost
            chosen_enhancement_list.append(chosen_enhancement)

        return chosen_enhancement_list, flat_bonus
    
def get_enhancement_info(character, weapon_type):
    if weapon_type in ('Melee', 'Ranged'):
        item_list = set()
        for item in character.weapon_dict.values():
            item_list.add(item.get('type', 0))
            item_list.add(item.get('special', 1))
            item_list.add(item.get('only', 2))

        key = list(character.weapon_dict.keys())[0] 
        if re.search(r'(bow)|(firearm)', key.lower()):
            key_add = ('bow' if re.search(r'bow', key) else 'firearm')
            item_list.add(key_add)

        item_list = split_item_list(character, item_list)
        return item_list
    
def split_item_list(character, item_list):
    normalized_items = []
    for item in item_list:
        if isinstance(item, str):
            stripped_item = item.lower()
            split_items = re.split(r"[,|+|/]", stripped_item)
            normalized_items.extend(split_items)
        else:
            normalized_items.append(item)
    unique_items = set(normalized_items)
    return unique_items

def clean_up_only(character, only):
    only_list = []
    only_list = only.split(",") if only else []
    only_list = [item.lower() for item in only_list]
    only_list = set(only_list)
    return only_list

def enhancement_limits(character, item_list, weapon_type, chosen_enhancement):
    if weapon_type in ('Melee', 'Ranged'):
        only = character.weapon_qualities[weapon_type].get(chosen_enhancement,0).get('only',"N/A").lower()
        not_only = character.weapon_qualities[weapon_type].get(chosen_enhancement,0).get('not',"N/A").lower()
        only_list = clean_up_only(character, only)
        not_only_list = clean_up_only(character, not_only)
        if len(only_list) > 0 and len(not_only_list) > 0:
            if only_list.issubset(item_list):
                pass
            else:
                chosen_enhancement = ''
                return chosen_enhancement

    




# bonus_gold_calculator was removed: nothing called it (its only reference was the unrelated
# character.bonus_gold_calculator method inside its own body), and it subtracted from gold with no
# affordability check -- a trap for anyone who wired it up later.



    
# End of enhancement to Armor + Weapons