"""Special materials for the equipped weapon, armor and shield, and the durability breakdown.

Two separate things live here, and they are gated differently on purpose:

* **Special materials are printed PF1e**, so every character can roll one (`buy_material`, called
  per slot from `armor_and_enhancements.plan_enhancements`). The material is paid for out of that
  slot's own share of the enhancement reserve, BEFORE the +N tier is priced, so an adamantine blade
  costs its wielder enchantment rather than appearing for free.
* **The durability breakdown is a Sieg's Guide house rule** (hardness and hit points built up
  additively from the weapon type, the substance, the enhancement and the size), so
  `durability_block` returns nothing unless `homebrew_enabled` says the house rules are on.

Every number -- the hardness table, the substance chart, the prices, which weapon is made of what --
is in `Backend/json/item_materials.json`. The only constants here are the three that tune how often
a material is bought. `scripts/gates/validate_item_materials.py` gates both halves.

Optimized builds (`character.role` set) never reach `buy_material`: the role's gold ladder is tuned
against the power metric, which does not score materials, and random mode's draw order must not
leak into theirs.
"""
import copy
import json
import os
import random
import re

from utils.class_func.skill_ranks import misc_homebrew_enabled

_MATERIALS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'json', 'item_materials.json')
_TABLE = None

# --- Tuning: how often a special material is bought ----------------------------------------------
# The chance is the slot's gold share over MATERIAL_CHANCE_GOLD_SCALE, capped: a slot with a
# 4,000 gp share rolls 10%, one with 20,000 gp or more rolls the cap. Poor characters rarely carry
# mithral; rich ones often do, and never always.
MATERIAL_CHANCE_GOLD_SCALE = 40_000
MATERIAL_CHANCE_CAP = 0.5
# A material may cost at most this fraction of its slot's share (its enchanting surcharge counted),
# so it can thin the enhancement the slot buys but never replace it.
MATERIAL_MAX_SHARE_FRACTION = 0.5

SLOTS = ('weapon', 'armor', 'shield')
ARMOR_SECTIONS = ('Light', 'Medium', 'Heavy')
SHIELD_SECTIONS = ('Shields', 'Tower')
# The size ladder is owned by the gear chooser; the multiplier only needs the distance from Medium.
SIZE_BASIS = 'Medium'

# Row keys in armor.json, as the payload reads them.
_MAX_DEX = 'max dex bonus'
_ACP = 'armor check penalty'
_ASF = 'arcane spell failure chance'
_WEIGHT = 'weight'


def table():
    """Backend/json/item_materials.json, read once."""
    global _TABLE
    if _TABLE is None:
        with open(_MATERIALS_PATH, encoding='utf-8') as handle:
            _TABLE = json.load(handle)
    return _TABLE


def homebrew_enabled(character):
    """Is the Sieg's Guide durability breakdown on for this character?

    The ONE place that answers it, so that when the master default-off `homebrew` key lands the
    breakdown moves under it by changing this line and nothing else.
    """
    return misc_homebrew_enabled(character)


# --- Lookups over the curated table --------------------------------------------------------------

def _number(text):
    """First number in a data cell like '30 lbs.', '1,500 gp', '25%' or '-4'. None when blank."""
    match = re.search(r'-?\d+(?:\.\d+)?', str(text if text is not None else '').replace(',', ''))
    if not match:
        return None
    value = float(match.group(0))
    return int(value) if value == int(value) else value


def weapon_profile(name):
    """{'row', 'material', 'metal_parts'} for a weapons_data.json name, or None if uncurated."""
    for group in table()['weapons']:
        if name in group['names']:
            return {'row': group['row'], 'material': group['material'],
                    'metal_parts': bool(group.get('metal_parts'))}
    return None


def armor_material(name):
    for material, names in table()['armor'].items():
        if name in names:
            return material
    return None


def shield_profile(name):
    for group in table()['shields']:
        if name in group['names']:
            return {'row': group['row'], 'material': group['material']}
    return None


def _section_of(character, name, sections):
    """Which armor.json section holds `name` -- the armor's category, or the shield's."""
    dataset = getattr(character, 'armor', None) or {}
    for section in sections:
        if name in (dataset.get(section) or {}):
            return section
    return None


def _slot_item(character, slot):
    """(name, row) for the item in `slot`, or None when the character carries none."""
    entry = {'weapon': getattr(character, 'weapon_dict', None),
             'armor': getattr(character, 'armor_dict', None),
             'shield': getattr(character, 'shield_dict', None)}[slot]
    if slot == 'shield' and not getattr(character, 'shield_flag', False):
        return None
    if not isinstance(entry, dict) or not entry:
        return None
    name = next(iter(entry))
    return name, entry[name] or {}


def default_material(slot, name):
    """The ordinary substance the item is made of, and whether metal can replace part of it."""
    if slot == 'weapon':
        profile = weapon_profile(name)
        return (profile['material'], profile['metal_parts']) if profile else (None, False)
    if slot == 'armor':
        return armor_material(name), False
    profile = shield_profile(name)
    return (profile['material'] if profile else None), False


def material_price(material, slot, row, category):
    """(price, enchant_surcharge) in gp for making this item out of `material`, or None if the
    table gives no price for it (which is what makes the material illegal on that item)."""
    rule = ((table()['special_materials'].get(material) or {}).get('price') or {}).get(slot)
    if not rule:
        return None
    price = 0
    if 'flat' in rule:
        price += rule['flat']
    if 'per_pound' in rule:
        # A weightless entry still takes a pound of the stuff; nothing is forged from none of it.
        price += rule['per_pound'] * max(1, _number(row.get(_WEIGHT)) or 0)
    if 'by_category' in rule:
        if category not in rule['by_category']:
            return None
        price += rule['by_category'][category]
    if 'cost_multiplier' in rule:
        price += rule['cost_multiplier'] * (_number(row.get('cost')) or 0)
    return int(round(price)), int(rule.get('enchant_surcharge') or 0)


def _category(character, slot, name, row):
    if slot == 'weapon':
        return str(row.get('category') or '')
    return _section_of(character, name, ARMOR_SECTIONS if slot == 'armor' else SHIELD_SECTIONS)


def legal_materials(character, slot, name, row):
    """{material: (price, surcharge)} for every special material this item can be made of."""
    base, metal_parts = default_material(slot, name)
    category = _category(character, slot, name, row)
    out = {}
    for material, spec in table()['special_materials'].items():
        if slot not in spec['slots']:
            continue
        if spec['base'] != base and not (metal_parts and spec['base'] == 'steel'):
            continue
        priced = material_price(material, slot, row, category)
        if priced is not None:
            out[material] = priced
    return out


# --- Buying --------------------------------------------------------------------------------------

def _is_mind_blade(character):
    """A soulknife's weapon is manifested, not forged -- it has no material to buy."""
    return any(entry.get('name') == 'soulknife' for entry in getattr(character, 'classes', None) or [])


def buy_material(character, slot, share):
    """Maybe buy a special material for `slot` out of its `share` of the enhancement reserve.

    Returns (price_paid, enchant_surcharge). The price is already deducted from `character.gold`
    and the choice recorded on `character.item_materials[slot]`; the surcharge is NOT deducted --
    it is owed only if the caller goes on to enchant the item, so the caller charges it.

    RNG: one `random.random()` per slot that holds an item, then one `random.choice` only when the
    roll hits and something is affordable. Never called for an optimized build.
    """
    materials = getattr(character, 'item_materials', None)
    if materials is None:
        materials = character.item_materials = {}
    item = _slot_item(character, slot)
    if item is None or (slot == 'weapon' and _is_mind_blade(character)):
        return 0, 0
    name, row = item

    hit = random.random() < min(MATERIAL_CHANCE_CAP, share / MATERIAL_CHANCE_GOLD_SCALE)
    if not hit:
        return 0, 0
    ceiling = share * MATERIAL_MAX_SHARE_FRACTION
    gold = character.gold if isinstance(character.gold, int) else 0
    affordable = sorted(material for material, (price, surcharge)
                        in legal_materials(character, slot, name, row).items()
                        if price + surcharge <= ceiling and price <= gold)
    if not affordable:
        return 0, 0
    material = random.choice(affordable)
    price, surcharge = legal_materials(character, slot, name, row)[material]
    character.gold -= price
    materials[slot] = material
    _apply_effects(character, slot, name, row, material)
    return price, surcharge


# --- Effects on the worn item --------------------------------------------------------------------

def _toward_zero(text, amount):
    """An armor check penalty eased by `amount`: '-4' and 3 give '-1'; never past 0."""
    value = _number(text)
    if value is None:
        return text
    return str(min(0, int(value) + amount))


def material_effects(row, material, slot):
    """A COPY of an armor.json row with the material's stat changes applied.

    Never the row itself: `list_selection` hands back the dataset's own dict, and writing to it
    would turn every later breastplate in this process into a mithral one. Armor bonus is never
    touched -- no material here changes what the armor is worth to AC.
    """
    spec = table()['special_materials'].get(material) or {}
    out = copy.deepcopy(row)
    change = spec.get(slot) or {}
    if change.get('max_dex') and _number(out.get(_MAX_DEX)) is not None:
        out[_MAX_DEX] = str(int(_number(out[_MAX_DEX])) + change['max_dex'])
    if change.get('acp'):
        out[_ACP] = _toward_zero(out.get(_ACP), change['acp'])
    if change.get('asf') and _number(out.get(_ASF)) is not None:
        out[_ASF] = f"{max(0, int(_number(out[_ASF])) + change['asf'])}%"
    multiplier = spec.get('weight_multiplier')
    if multiplier and _number(out.get(_WEIGHT)) is not None:
        out[_WEIGHT] = f"{_number(out[_WEIGHT]) * multiplier:g} lbs."
    return out


def _apply_effects(character, slot, name, row, material):
    if slot == 'armor':
        character.armor_dict = {name: material_effects(row, material, slot)}
    elif slot == 'shield':
        character.shield_dict = {name: material_effects(row, material, slot)}


def armor_material_dr(character):
    """DR/- granted by the armor's material (adamantine: 1 / 2 / 3 by category), else 0."""
    material = (getattr(character, 'item_materials', None) or {}).get('armor')
    item = _slot_item(character, 'armor')
    table_dr = (table()['special_materials'].get(material) or {}).get('armor_dr')
    if not (material and item and table_dr):
        return 0
    return int(table_dr.get(_section_of(character, item[0], ARMOR_SECTIONS)) or 0)


def weapon_material_damage(character):
    """Flat damage change from the weapon's material (alchemical silver: -1), else 0."""
    material = (getattr(character, 'item_materials', None) or {}).get('weapon')
    return int((table()['special_materials'].get(material) or {}).get('weapon_damage') or 0)


def material_label(material):
    return (table()['substances'].get(material) or {}).get('label', '')


# --- Durability breakdown (house rule) -----------------------------------------------------------

def bonus_equivalent(quality_row):
    """How many +1s a special ability counts as toward the item's total effective bonus.

    The quality files carry an `enhancement` int for EVERY ability, because the generator's budget
    needs a cost for all of them -- including the ones PF1e prices in gold. Those are not bonus
    equivalents, and the `price` cell is what tells the two apart:

    * weapons: blank price = a true +N ability; any price ('+1,500', '7,500') = gold-priced.
    * armor:   a price of 1-5 IS the +N; anything larger is a gold price.
    """
    row = quality_row or {}
    price = str(row.get('price') or '').strip()
    if not price:
        return int(row.get('enhancement') or 0)
    amount = _number(price)
    if amount is not None and '+' not in price and ',' not in price and amount <= 5:
        return int(amount)
    return 0


def effective_bonus(flat_bonus, quality_names, quality_pool):
    """Flat +N plus every chosen ability's bonus-equivalent."""
    pool = quality_pool or {}
    return int(flat_bonus or 0) + sum(bonus_equivalent(pool.get(name)) for name in quality_names or [])


def size_factor(size, sizes):
    """(multiplier, label) for hit points: x2 per category above Medium, half per category below."""
    if size not in sizes or SIZE_BASIS not in sizes:
        return 1, None
    steps = sizes.index(size) - sizes.index(SIZE_BASIS)
    if steps == 0:
        return 1, None
    if steps > 0:
        return 2 ** steps, f'x{2 ** steps}'
    return 1 / (2 ** -steps), f'/{2 ** -steps}'


def durability(base_label, base, material, bonus, impervious, size, sizes, size_sources=()):
    """The additive breakdown for one item, on a Medium basis.

    `base` is the type row ({'hardness', 'hp'}), `material` a substance id, `bonus` the total
    effective enhancement bonus. Returns totals plus the ordered lines that sum to them, so a
    renderer never recomputes anything.
    """
    doc = table()
    substance = doc['substances'][material]
    per = doc['enhancement']
    hardness_lines = [[base_label, base['hardness']], [substance['label'], substance['hardness']]]
    hp_lines = [[base_label, base['hp']], [substance['label'], substance['hp']]]
    if bonus:
        hardness_lines.append(['Enhancement', bonus * per['hardness_per_bonus']])
        hp_lines.append(['Enhancement', bonus * per['hp_per_bonus']])
        if impervious:
            # "Double its enhancement bonus to hardness and hit points": one more enhancement line.
            hardness_lines.append(['Impervious', bonus * per['hardness_per_bonus']])
            hp_lines.append(['Impervious', bonus * per['hp_per_bonus']])
    factor, size_label = size_factor(size, sizes)
    subtotal = sum(value for _, value in hp_lines)
    return {
        'material': material,
        'material_label': substance['label'],
        'hardness': sum(value for _, value in hardness_lines),
        'hp': max(1, int(subtotal * factor)),
        'hardness_lines': hardness_lines,
        'hp_lines': hp_lines,
        'size_lines': [[size, size_label]] if size_label else [],
        'size_sources': [source for source in size_sources if source],
    }


def _label(row_name):
    """'two-handed blade' -> 'Two-Handed Blade'."""
    return ' '.join('-'.join(part.capitalize() for part in word.split('-'))
                    for word in row_name.split(' '))


def durability_block(character, *, weapon_bonus, weapon_qualities, armor_bonus, armor_qualities,
                     shield_bonus, shield_qualities, weapon_size, weapon_size_source, wearer_size,
                     sizes, melee=True):
    """`item_durability` for the payload: {slot: breakdown} for each carried item.

    {} when the house rules are off. Built at payload time rather than in the gear phase because
    the weapon's size is only known once the feats that oversize it have been chosen.
    """
    if not homebrew_enabled(character):
        return {}
    doc = table()
    materials = getattr(character, 'item_materials', None) or {}
    weapon_pool = (getattr(character, 'weapon_qualities', None) or {}).get('Melee' if melee else 'Ranged')
    armor_pools = getattr(character, 'armor_qualities', None) or {}
    out = {}

    item = _slot_item(character, 'weapon')
    profile = weapon_profile(item[0]) if item else None
    if profile and not _is_mind_blade(character):
        out['weapon'] = durability(
            _label(profile['row']), doc['weapon_base'][profile['row']],
            materials.get('weapon') or profile['material'],
            effective_bonus(weapon_bonus, weapon_qualities, weapon_pool),
            'Impervious' in (weapon_qualities or []), weapon_size, sizes, [weapon_size_source])

    item = _slot_item(character, 'armor')
    if item and armor_material(item[0]):
        armor_bonus_value = int(_number(item[1].get('armor bonus')) or 0)
        base = {'hardness': doc['armor_base']['hardness'],
                'hp': armor_bonus_value * doc['armor_base']['hp_per_armor_bonus']}
        out['armor'] = durability(
            'Armor', base, materials.get('armor') or armor_material(item[0]),
            effective_bonus(armor_bonus, armor_qualities, armor_pools.get('Armor')),
            'Impervious' in (armor_qualities or []), wearer_size, sizes)

    item = _slot_item(character, 'shield')
    profile = shield_profile(item[0]) if item else None
    if profile:
        out['shield'] = durability(
            _label(profile['row']), doc['shield_base'][profile['row']],
            materials.get('shield') or profile['material'],
            effective_bonus(shield_bonus, shield_qualities, armor_pools.get('Shield')),
            'Impervious' in (shield_qualities or []), wearer_size, sizes)
    return out
