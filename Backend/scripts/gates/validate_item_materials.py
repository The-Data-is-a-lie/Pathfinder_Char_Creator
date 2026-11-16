"""Gate special materials and the durability breakdown: the table, and the code that reads it.

    .venv/Scripts/python.exe Backend/scripts/gates/validate_item_materials.py
    .venv/Scripts/python.exe Backend/scripts/gates/validate_item_materials.py --print

WHY THIS EXISTS
---------------
`Backend/json/item_materials.json` is hand-curated: which of 305 weapons is a "two-handed blade"
and which a "two-handed hafted weapon", what each is made of, which special materials it can take
and what they cost. `weapons_data.json` cannot answer any of that -- it has a handedness and a
damage type, and a quarter of its rows have no weapon group at all -- so the map is a judgement,
and a judgement with nothing checking it is how `armor_type_mapping` stayed wrong for the life of
the repo. This gate is what a new weapon runs into.

  1. COVERAGE   -- every weapon, armor and shield the generator can roll is in exactly one group,
                   and no group names an item that no longer exists.
  2. COHERENCE  -- every row a group points at exists; every special material is priced for every
                   slot it claims, replaces a substance it can actually replace, and has a row of
                   its own on the substance chart.
  3. LEGALITY   -- over every item x material the code calls legal: a metal never lands on an item
                   with no metal in it, darkwood never on one with no wood.
  4. EFFECTS    -- a material never changes an armor bonus, never loosens a number the wrong way,
                   and never writes to the row it was handed (that row is the dataset's own dict).
  5. QUALITIES  -- which special abilities count toward the total effective bonus. The quality
                   files give EVERY ability an `enhancement` int, including the gold-priced ones,
                   so this is the check that keeps Impervious from counting itself.
  6. THE EXAMPLE -- the Spombagorn greatsword, which is where the house formula was read from:
                   a Large iron greatsword, effective +5, Impervious = hardness 40, 280 hit points.
  7. THE GATES  -- the breakdown is absent with the house rules off, and an optimized build makes
                   no RNG draw and buys nothing. Both are proved against a build that DOES, so
                   neither can pass by the code simply never running.

The hardness table and the substance chart themselves are external rules (the Sieg's Guide
"Combat References" doc) and are not re-derived here; the worked example is the tie to them.
"""
import argparse
import copy
import random
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import JSON_DIR, Report, read_json                                # noqa: E402

from utils.class_func import armor_and_enhancements, item_materials              # noqa: E402
from utils.class_func.armor_and_weapon_chooser import SIZES                      # noqa: E402

REPORT = Report('validate_item_materials')

MATERIALS = JSON_DIR / 'item_materials.json'
WEAPONS = JSON_DIR / 'weapons_data.json'
ARMOR = JSON_DIR / 'armor.json'
WEAPON_QUALITIES = JSON_DIR / 'weapon_qualities.json'
ARMOR_QUALITIES = JSON_DIR / 'armor_qualities.json'

PRICE_KEYS = {'flat', 'per_pound', 'by_category', 'cost_multiplier', 'enchant_surcharge'}
EFFECT_KEYS = {'max_dex', 'acp', 'asf'}


def _stub(armor, **overrides):
    """The least of a character the materials code reads."""
    fields = dict(armor=armor, weapon_dict=None, armor_dict=None, shield_dict=None,
                  shield_flag=False, classes=[], gold=0, role=None, item_materials={},
                  misc_homebrew_rules='Y', weapon_qualities={}, armor_qualities={})
    fields.update(overrides)
    return SimpleNamespace(**fields)


def check_coverage(doc, weapons, armor):
    def census(label, rollable, groups):
        placed = [name for names in groups for name in names]
        seen = set()
        twice = sorted({name for name in placed if name in seen or seen.add(name)})
        REPORT.check(not twice, f'{label}: listed in more than one group: {twice}')
        missing = sorted(set(rollable) - set(placed))
        REPORT.check(not missing,
                     f'{label}: {len(missing)} rollable item(s) with no group in item_materials.json '
                     f'-- add each to the group for what it is made of: {missing[:12]}')
        stale = sorted(set(placed) - set(rollable))
        REPORT.check(not stale, f'{label}: group(s) name item(s) that do not exist: {stale[:12]}')
        return len(set(placed))

    weapon_names = {name for rows in weapons.values() for name in rows}
    armor_names = {name for section in item_materials.ARMOR_SECTIONS for name in armor[section]}
    shield_names = {name for section in item_materials.SHIELD_SECTIONS for name in armor[section]}
    return (census('weapons', weapon_names, [g['names'] for g in doc['weapons']]),
            census('armor', armor_names, list(doc['armor'].values())),
            census('shields', shield_names, [g['names'] for g in doc['shields']]))


def check_coherence(doc):
    substances = doc['substances']
    for name, row in substances.items():
        REPORT.check(isinstance(row.get('hardness'), int) and isinstance(row.get('hp'), int)
                     and row['hardness'] >= 0 and row['hp'] >= 0 and row.get('label'),
                     f'substances.{name}: needs a label and non-negative int hardness / hp')
    for group in doc['weapons']:
        REPORT.check(group['row'] in doc['weapon_base'],
                     f'weapons: row {group["row"]!r} is not in weapon_base')
        REPORT.check(group['material'] in substances,
                     f'weapons: material {group["material"]!r} is not a substance')
    for group in doc['shields']:
        REPORT.check(group['row'] in doc['shield_base'],
                     f'shields: row {group["row"]!r} is not in shield_base')
        REPORT.check(group['material'] in substances,
                     f'shields: material {group["material"]!r} is not a substance')
    for material in doc['armor']:
        REPORT.check(material in substances, f'armor: material {material!r} is not a substance')

    for name, spec in doc['special_materials'].items():
        REPORT.check(name in substances,
                     f'special_materials.{name}: no substance row, so it has no durability line')
        REPORT.check(spec.get('base') in substances,
                     f'special_materials.{name}: base {spec.get("base")!r} is not a substance')
        slots = spec.get('slots') or []
        REPORT.check(slots and set(slots) <= set(item_materials.SLOTS),
                     f'special_materials.{name}: slots must be drawn from {item_materials.SLOTS}')
        for slot in slots:
            rule = (spec.get('price') or {}).get(slot)
            if REPORT.check(isinstance(rule, dict) and rule,
                            f'special_materials.{name}: claims slot {slot!r} but has no price for it'):
                REPORT.check(set(rule) <= PRICE_KEYS,
                             f'special_materials.{name}.price.{slot}: unknown key(s) '
                             f'{sorted(set(rule) - PRICE_KEYS)}')
        for slot in ('armor', 'shield'):
            REPORT.check(set(spec.get(slot) or {}) <= EFFECT_KEYS,
                         f'special_materials.{name}.{slot}: unknown effect key(s)')


def _items(weapons, armor):
    """(slot, name, row) for everything rollable, with a stub that can resolve its category."""
    for rows in weapons.values():
        for name, row in rows.items():
            yield 'weapon', name, row
    for section in item_materials.ARMOR_SECTIONS:
        for name, row in armor[section].items():
            yield 'armor', name, row
    for section in item_materials.SHIELD_SECTIONS:
        for name, row in armor[section].items():
            yield 'shield', name, row


def check_legality_and_effects(doc, weapons, armor):
    stub = _stub(armor)
    pairs = 0
    for slot, name, row in _items(weapons, armor):
        base, metal_parts = item_materials.default_material(slot, name)
        for material, (price, surcharge) in item_materials.legal_materials(stub, slot, name, row).items():
            pairs += 1
            spec = doc['special_materials'][material]
            REPORT.check(spec['base'] == base or (metal_parts and spec['base'] == 'steel'),
                         f'{name}: {material} replaces {spec["base"]}, but this item is {base}')
            REPORT.check(isinstance(price, int) and price > 0 and surcharge >= 0,
                         f'{name} in {material}: price {price!r} / surcharge {surcharge!r}')
            if slot == 'weapon':
                continue
            before = copy.deepcopy(row)
            after = item_materials.material_effects(row, material, slot)
            REPORT.check(row == before, f'{name} in {material}: material_effects wrote to its input row')
            REPORT.check(after.get('armor bonus') == row.get('armor bonus'),
                         f'{name} in {material}: the armor bonus moved')
            number = item_materials._number
            if number(row.get('armor check penalty')) is not None:
                REPORT.check(number(row['armor check penalty']) <= number(after['armor check penalty']) <= 0,
                             f'{name} in {material}: armor check penalty went the wrong way or past 0')
            if number(row.get('arcane spell failure chance')) is not None:
                REPORT.check(0 <= number(after['arcane spell failure chance'])
                             <= number(row['arcane spell failure chance']),
                             f'{name} in {material}: spell failure went up or below 0')
            if number(row.get('max dex bonus')) is not None:
                REPORT.check(number(after['max dex bonus']) >= number(row['max dex bonus']),
                             f'{name} in {material}: max Dex went down')
    REPORT.check(pairs > 0, 'no item accepts any special material -- the legality rule matches nothing')
    return pairs


def check_qualities(weapon_qualities, armor_qualities):
    equivalent = item_materials.bonus_equivalent
    for section in ('Melee', 'Ranged'):
        pool = weapon_qualities[section]
        REPORT.check(equivalent(pool['Impervious']) == 0,
                     f'weapon_qualities.{section}.Impervious is gold-priced and must count +0 toward '
                     f'the effective bonus, got {equivalent(pool["Impervious"])}')
        REPORT.check(equivalent(pool['Flaming Burst']) == 2,
                     f'weapon_qualities.{section}."Flaming Burst" must count +2')
        for name, row in pool.items():
            if str(row.get('price') or '').strip():
                REPORT.check(equivalent(row) == 0,
                             f'weapon_qualities.{section}.{name}: has a gold price but counts '
                             f'+{equivalent(row)} toward the effective bonus')
    for section in ('Armor', 'Shield'):
        for name, row in armor_qualities[section].items():
            value = equivalent(row)
            REPORT.check(0 <= value <= 5, f'armor_qualities.{section}.{name}: bonus-equivalent {value}')
    REPORT.check(equivalent(armor_qualities['Armor']['Impervious']) == 1,
                 'armor_qualities.Armor.Impervious is a true +1 ability and must count +1')


def check_worked_example(doc, weapon_qualities):
    """The Spombagorn greatsword. `x2 Mythic` on the original is deliberately not modelled."""
    profile = item_materials.weapon_profile('Greatsword')
    if not REPORT.check(profile == {'row': 'two-handed blade', 'material': 'steel', 'metal_parts': False},
                        f'Greatsword must be a steel two-handed blade, got {profile}'):
        return
    bonus = item_materials.effective_bonus(3, ['Flaming Burst', 'Impervious'], weapon_qualities['Melee'])
    REPORT.check(bonus == 5, f'+3 Flaming Burst Impervious must be an effective +5, got +{bonus}')
    got = item_materials.durability('Two-Handed Blade', doc['weapon_base'][profile['row']],
                                    profile['material'], bonus, True, 'Large', SIZES)
    REPORT.check(got['hardness'] == 40 and [v for _, v in got['hardness_lines']] == [10, 10, 10, 10],
                 f'greatsword hardness must be 40 = 10 + 10 + 10 + 10, got {got["hardness"]} '
                 f'from {got["hardness_lines"]}')
    REPORT.check(got['hp'] == 280 and [v for _, v in got['hp_lines']] == [10, 30, 50, 50]
                 and got['size_lines'] == [['Large', 'x2']],
                 f'greatsword hit points must be 280 = (10 + 30 + 50 + 50) x2 for Large, got '
                 f'{got["hp"]} from {got["hp_lines"]} {got["size_lines"]}')
    small = item_materials.durability('Two-Handed Blade', doc['weapon_base'][profile['row']],
                                      profile['material'], 0, False, 'Small', SIZES)
    REPORT.check(small['hp'] == 20 and small['size_lines'] == [['Small', '/2']],
                 f'a Small plain greatsword must have (10 + 30) / 2 = 20 hit points, got {small["hp"]}')
    medium = item_materials.durability('Two-Handed Blade', doc['weapon_base'][profile['row']],
                                       profile['material'], 0, False, 'Medium', SIZES)
    REPORT.check(medium['size_lines'] == [] and medium['hp'] == 40,
                 'a Medium item must carry no size line')


def _greatsword_character(weapons, armor, **overrides):
    fields = dict(weapon_dict={'Greatsword': weapons['Martial']['Greatsword']},
                  armor_dict={'Full plate': armor['Heavy']['Full plate']},
                  gold=400_000)
    fields.update(overrides)
    return _stub(armor, **fields)


def check_gates(weapons, armor, weapon_qualities, armor_qualities):
    def block(character):
        return item_materials.durability_block(
            character, weapon_bonus=1, weapon_qualities=[], armor_bonus=1, armor_qualities=[],
            shield_bonus=0, shield_qualities=[], weapon_size='Medium', weapon_size_source=None,
            wearer_size='Medium', sizes=SIZES)

    pools = dict(weapon_qualities=weapon_qualities, armor_qualities=armor_qualities)
    on = block(_greatsword_character(weapons, armor, **pools))
    off = block(_greatsword_character(weapons, armor, misc_homebrew_rules='N', **pools))
    REPORT.check(set(on) == {'weapon', 'armor'},
                 f'house rules on: expected a weapon and an armor breakdown, got {sorted(on)}')
    REPORT.check(off == {}, f'house rules off: item_durability must be {{}}, got {off}')

    # Optimized builds: no draw, no purchase. Proved against random mode on the SAME seed, which
    # must do both -- otherwise "nothing happened" would also be what a dead call site looks like.
    bought = draws = 0
    for seed in range(40):
        random.seed(seed)
        before = random.getstate()
        optimized = _greatsword_character(weapons, armor, role={})
        armor_and_enhancements.plan_enhancements(optimized, has_shield=False)
        REPORT.check(random.getstate() == before and optimized.item_materials == {},
                     f'seed {seed}: an optimized build drew from the RNG or bought a material')

        random.seed(seed)
        plain = _greatsword_character(weapons, armor)
        gold = plain.gold
        armor_and_enhancements.plan_enhancements(plain, has_shield=False)
        draws += random.getstate() != before
        bought += bool(plain.item_materials)
        REPORT.check(0 <= plain.gold <= gold, f'seed {seed}: the purse went negative or grew')
        REPORT.check(armor['Heavy']['Full plate'] == _PRISTINE['Full plate'],
                     f'seed {seed}: buying a material rewrote the armor dataset itself')
    REPORT.check(draws == 40, f'random mode must roll for a material every time; rolled {draws}/40')
    REPORT.check(bought > 0, 'random mode never bought a material in 40 well-funded tries')

    # The ceiling: a material never takes more than its fraction of the slot's share.
    for seed in range(200):
        random.seed(seed)
        character = _greatsword_character(weapons, armor, gold=50_000)
        price, surcharge = item_materials.buy_material(character, 'weapon', 10_000)
        REPORT.check(price + surcharge <= 10_000 * item_materials.MATERIAL_MAX_SHARE_FRACTION,
                     f'seed {seed}: paid {price} + {surcharge} out of a 10,000 gp share')
        REPORT.check(character.gold == 50_000 - price,
                     f'seed {seed}: buy_material must deduct the price and only the price')
    return bought


_PRISTINE = {}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--print', dest='show', action='store_true',
                        help='list every weapon group and the materials it can take')
    args = parser.parse_args(argv)

    doc = read_json(MATERIALS)
    weapons = read_json(WEAPONS)
    armor = read_json(ARMOR)
    weapon_qualities = read_json(WEAPON_QUALITIES)
    armor_qualities = read_json(ARMOR_QUALITIES)
    _PRISTINE['Full plate'] = copy.deepcopy(armor['Heavy']['Full plate'])

    counts = check_coverage(doc, weapons, armor)
    check_coherence(doc)
    pairs = 0
    if not REPORT.errors:
        pairs = check_legality_and_effects(doc, weapons, armor)
        check_qualities(weapon_qualities, armor_qualities)
        check_worked_example(doc, weapon_qualities)
        check_gates(weapons, armor, weapon_qualities, armor_qualities)

    if args.show:
        stub = _stub(armor)
        for group in doc['weapons']:
            sample = group['names'][0]
            row = next(rows[sample] for rows in weapons.values() if sample in rows)
            takes = sorted(item_materials.legal_materials(stub, 'weapon', sample, row))
            print(f'{group["row"]:<24} {group["material"]:<8} {len(group["names"]):>3} weapons  '
                  f'e.g. {sample}: {", ".join(takes) or "no special material"}')

    return REPORT.finish(f'{counts[0]} weapons, {counts[1]} armors, {counts[2]} shields; '
                         f'{len(doc["special_materials"])} special materials over {pairs} legal '
                         f'item x material pairs; greatsword example 40 / 280')


if __name__ == '__main__':
    sys.exit(main())
