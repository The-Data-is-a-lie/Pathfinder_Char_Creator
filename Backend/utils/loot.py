"""Encounter treasure -- the ONE owner of the CR -> gp curve, and the parcel builder over it.

NOT to be confused with ``utils.data.wealth_by_level``. That is Paizo's PC **wealth by level**: how
much gear one character of level N should be carrying, cumulative, and it is what
``Character.assign_gold`` spends. This module owns Paizo's **treasure values per encounter**: how
much a single CR-N fight is worth as loot, per campaign speed. Same units, different curves, and
mixing them up hands a level-5 party a level-5 character's entire kit for one goblin ambush.

Shape of the answer (sheet ticket #81): a parcel = coins + gems + items, whose combined gp value
lands at or just under the budget. Deliberately NOT an Ultimate Equipment percentile-table
emulation -- the decision (2026-08-13) was a hand-coded value table filled from the item compendia
this repo already prices, because that is the part a GM actually re-rolls.

Two rules the fill obeys, both learned from ``item_and_price``'s history:

* **Wondrous items must resolve in ``foundry_item_names.json``.** The web sheet hydrates a loot item
  by name against its own compendium extract of the same Foundry packs, so an unlisted name arrives
  as a bare row with no description and no changes. Resolution goes through ``ItemNameResolver``,
  the same class the generator uses, so the spelling matches. Weapons and armor are exempt: that
  file is the wondrous pack only and does not contain "Longsword", so they ship with the spelling
  their own dataset carries.
* **An unpriceable item is skipped, never freed.** ``convert_price`` returns ``None`` for a blob it
  cannot read; treating that as 0 is how this repo once handed out a 50,000 gp ring for nothing.
"""
import json
import random
import re

from utils.paths import repo_path
from utils.class_func.item_and_price import ItemNameResolver, convert_price

# --- the curve -----------------------------------------------------------------------------------

# Paizo, "Treasure Values per Encounter" (Core Rulebook / GameMastery Guide): gp of treasure a
# single encounter of this CR is worth, by campaign speed. Hand-coded per the #81 decision; there is
# no machine-readable copy of this table in either repo.
TREASURE_PER_ENCOUNTER = {
    1: (170, 260, 400),
    2: (350, 550, 800),
    3: (550, 800, 1_200),
    4: (750, 1_150, 1_700),
    5: (1_000, 1_550, 2_300),
    6: (1_350, 2_000, 3_000),
    7: (1_750, 2_600, 3_900),
    8: (2_200, 3_350, 5_000),
    9: (2_850, 4_250, 6_400),
    10: (3_650, 5_450, 8_200),
    11: (4_650, 7_000, 10_500),
    12: (6_000, 9_000, 13_500),
    13: (7_750, 11_600, 17_500),
    14: (10_000, 15_000, 22_000),
    15: (13_000, 19_500, 29_000),
    16: (16_500, 25_000, 38_000),
    17: (22_000, 33_000, 49_000),
    18: (28_000, 42_000, 63_000),
    19: (35_000, 53_000, 79_000),
    20: (44_000, 67_000, 100_000),
}

SPEEDS = ('slow', 'medium', 'fast')
MIN_CR = 1
MAX_CR = 20
# CR 21+ is never published. Continue the last delta linearly, the same ruling
# ``wealth_by_level`` already applies to levels 21-40 -- the tail accelerates in the real table,
# and a flat continuation keeps a CR 30 parcel readable instead of absurd.
_TAIL_DELTA = tuple(TREASURE_PER_ENCOUNTER[20][i] - TREASURE_PER_ENCOUNTER[19][i] for i in range(3))


def treasure_value(cr, speed='medium'):
    """Budget in gp for one encounter of this CR at this campaign speed."""
    cr = max(MIN_CR, int(cr))
    idx = SPEEDS.index(speed if speed in SPEEDS else 'medium')
    if cr <= MAX_CR:
        return TREASURE_PER_ENCOUNTER[cr][idx]
    return TREASURE_PER_ENCOUNTER[MAX_CR][idx] + _TAIL_DELTA[idx] * (cr - MAX_CR)


# --- gems ----------------------------------------------------------------------------------------

# The standard PF1 gem value bands. Small and curated on purpose: gems exist here so a parcel can
# absorb an awkward remainder as something a GM can hand over, not as a second item catalogue.
GEMS = {
    10: ['banded agate', 'eye agate', 'moss agate', 'azurite', 'blue quartz', 'hematite',
         'lapis lazuli', 'malachite', 'obsidian', 'rhodochrosite', 'tiger eye turquoise',
         'freshwater pearl'],
    50: ['bloodstone', 'carnelian', 'chalcedony', 'chrysoprase', 'citrine', 'iolite', 'jasper',
         'moonstone', 'onyx', 'peridot', 'rock crystal', 'sard', 'sardonyx', 'smoky quartz',
         'star rose quartz', 'zircon'],
    100: ['amber', 'amethyst', 'chrysoberyl', 'coral', 'red garnet', 'jade', 'jet', 'white pearl',
          'red spinel', 'tourmaline'],
    500: ['alexandrite', 'aquamarine', 'violet garnet', 'black pearl', 'golden yellow topaz'],
    1_000: ['emerald', 'white opal', 'fire opal', 'blue sapphire', 'star ruby'],
    5_000: ['clearest bright green emerald', 'blue-white diamond', 'jacinth', 'ruby'],
}


# --- the priced item pool ------------------------------------------------------------------------

_POOL = None


def _weight_lbs(raw):
    """'10 lbs.' / '1 lb. ' / '--' -> float or None. Weight is decoration here, never a filter."""
    text = str(raw or '').replace(',', '')
    digits = ''
    for ch in text:
        if ch.isdigit() or (ch == '.' and digits):
            digits += ch
        elif digits:
            break
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def _load(name):
    with open(repo_path('Backend', 'json', name), encoding='utf-8') as handle:
        return json.load(handle)


# '5 gp' / '1,500 gp' / '2 sp' / '5 cp' -> gp as a float. Mundane gear ONLY.
_COIN_COST = re.compile(r'^\s*(\d{1,3}(?:,\d{3})*|\d+)(?:\.(\d+))?\s*(pp|gp|sp|cp)\b', re.I)
_COIN_IN_GP = {'pp': 10.0, 'gp': 1.0, 'sp': 0.1, 'cp': 0.01}


def _mundane_price(blob):
    """Weapon/armor ``cost`` -> gp, or None.

    Mundane costs must NOT go through ``convert_price``: its ``adjust_price`` reads any integer
    under 11 as a **+N enhancement bonus** and returns N^2 x 1000, which is correct for the magic
    blobs it was written for and turns a 2 gp dagger into a 4,000 gp one here. Sub-gp prices matter
    too -- half the adventuring kit is priced in silver.
    """
    match = _COIN_COST.match(str(blob or ''))
    if not match:
        return None
    whole = int(match.group(1).replace(',', ''))
    frac = float('0.' + match.group(2)) if match.group(2) else 0.0
    gp = (whole + frac) * _COIN_IN_GP[match.group(3).lower()]
    return round(gp, 2) if gp > 0 else None


def _pool():
    """Every priced, Foundry-resolvable item, as ``{name, price, weight, slot, kind}``.

    Built once per process. The four sources are the same ones ``choose_equipment`` buys from, so a
    parcel can only contain gear the generator could itself have handed a character.
    """
    global _POOL
    if _POOL is not None:
        return _POOL

    resolver = ItemNameResolver(_load('foundry_item_names.json'))
    known = set(resolver.exact.values())
    broken = {str(n).strip().lower() for n in _load('items_broken.json')}
    items = []

    def add(raw_name, price_blob, weight_raw, slot, kind):
        if str(raw_name).strip().lower() in broken:
            return
        if kind == 'magic':
            # Wondrous items: resolve to the Foundry list's own spelling and drop anything not in
            # it, exactly as `choose_equipment` does.
            name = resolver.resolve(raw_name)
            if name not in known:
                return
            price = convert_price(None, price_blob, raw_name)
        else:
            # Weapons and armor are NOT in `foundry_item_names.json` -- that file is the wondrous /
            # magic-item pack only (it has "Ring of Protection +2" but not "Longsword"). Their
            # source spelling here came from the weapon and armor packs of the same scrape, and the
            # sheet's own extract keys those case-insensitively, so pass them through unfiltered
            # rather than measuring them against a list that was never about them.
            name = str(raw_name).strip()
            price = _mundane_price(price_blob)
        if not isinstance(price, (int, float)) or price <= 0:
            return                     # unpriceable is unbuyable, never free
        items.append({'name': name, 'price': price, 'weight': _weight_lbs(weight_raw),
                      'slot': slot, 'kind': kind})

    for slot, bucket in _load('items_best.json').items():
        for raw_name, rec in bucket.items():
            add(raw_name, rec.get('price'), rec.get('weight'), rec.get('slot') or slot, 'magic')
    for raw_name, rec in _load('Magic_Rings.json').get('MagicRings', {}).items():
        add(raw_name, rec.get('price'), rec.get('weight'), 'ring', 'magic')
    for group, bucket in _load('weapons_data.json').items():
        for raw_name, rec in bucket.items():
            add(raw_name, rec.get('cost'), rec.get('weight'), '', 'weapon')
    for group, bucket in _load('armor.json').items():
        for raw_name, rec in bucket.items():
            add(raw_name, rec.get('cost'), rec.get('weight'), '', 'armor')

    # Dedup by canonical name, cheapest reading wins (a name printed in two sources is one item).
    best = {}
    for item in items:
        prior = best.get(item['name'])
        if prior is None or item['price'] < prior['price']:
            best[item['name']] = item
    _POOL = sorted(best.values(), key=lambda i: i['price'])
    return _POOL


# --- the parcel ----------------------------------------------------------------------------------

# Share of the budget that stays as coins before anything is bought. A parcel that is all magic
# items reads like a shop inventory; a parcel that is all coins reads like a payroll.
COIN_SHARE = (0.15, 0.40)
MAX_ITEMS = 6
# An item is only worth listing if it is a real slice of what is left. Without a floor, a 100,000 gp
# CR 20 parcel fills up with 8 gp daggers.
ITEM_FLOOR_SHARE = 0.20
# The mundane pool (306 weapons, 65 armors) is nearly as large as the magic one, so an unweighted
# draw makes every parcel a rack of exotic polearms. Treasure is mostly coin and wonder; ordinary
# steel shows up, but it does not fill the chest.
MAX_MUNDANE = 2


def _split_coins(total_gp, rng):
    """gp value -> a pp/gp/sp/cp purse that reads like something found, not a bank balance."""
    coins = {'pp': 0, 'gp': 0, 'sp': 0, 'cp': 0}
    remaining = int(total_gp)
    if remaining <= 0:
        return coins
    # Platinum only once the pile is big enough that counting it in gp is silly.
    if remaining >= 2_000:
        pp_gp = int(remaining * rng.uniform(0.3, 0.6))
        coins['pp'] = pp_gp // 10
        remaining -= coins['pp'] * 10
    coins['gp'] = remaining
    # Small change only at small scale -- 40 cp in a dragon's hoard is noise, in a bandit's purse
    # it is flavour.
    if remaining < 200 and remaining >= 2:
        shave = rng.randint(1, max(1, remaining // 4))
        coins['gp'] -= shave
        coins['sp'] = shave * 10 - rng.randint(0, 9)
        coins['cp'] = rng.randint(0, 99)
    return coins


def _pick_gems(budget, rng):
    """0-3 gems whose bands fit the budget. Returns ``([{name, value}], spent)``."""
    bands = [v for v in sorted(GEMS) if v <= budget]
    if not bands:
        return [], 0
    picked = []
    spent = 0
    for _ in range(rng.randint(0, 3)):
        options = [v for v in bands if v <= budget - spent]
        if not options:
            break
        # Weight toward the larger bands the budget can afford, so a CR 15 parcel is not 3 agates.
        value = rng.choice(options[-3:])
        picked.append({'name': rng.choice(GEMS[value]).title(), 'value': value})
        spent += value
    return picked, spent


def generate_loot(cr, speed='medium', seed=None):
    """A treasure parcel for one encounter.

    ``{cr, speed, budget, value, coins{pp,gp,sp,cp}, gems[{name,value}], items[...], seed}``

    ``value`` is what the parcel is actually worth, which is at or a little under ``budget`` --
    the fill stops when nothing left in the pool is a meaningful slice of the remainder, and the
    difference goes back into coins rather than being padded with junk.
    """
    cr = max(MIN_CR, int(cr))
    speed = speed if speed in SPEEDS else 'medium'
    if seed is None:
        seed = random.randrange(1, 2 ** 31)
    rng = random.Random(seed)

    budget = treasure_value(cr, speed)
    coin_budget = int(budget * rng.uniform(*COIN_SHARE))
    remaining = budget - coin_budget

    gems, gem_spent = _pick_gems(int(remaining * rng.uniform(0.0, 0.35)), rng)
    remaining -= gem_spent

    pool = _pool()
    items = []
    while len(items) < MAX_ITEMS and remaining > 0:
        floor = remaining * ITEM_FLOOR_SHARE
        taken = {i['name'] for i in items}
        mundane_full = sum(1 for i in items if i['kind'] != 'magic') >= MAX_MUNDANE
        options = [i for i in pool
                   if floor <= i['price'] <= remaining
                   and i['name'] not in taken
                   and not (mundane_full and i['kind'] != 'magic')]
        if not options:
            break
        # Weighted by price: given 40,000 gp to spend, the interesting answer is one 30,000 gp
        # item, not the 25 gp handaxe that also "fits".
        item = rng.choices(options, weights=[i['price'] for i in options])[0]
        items.append(dict(item))
        remaining -= item['price']

    # Whatever the fill could not spend joins the coins -- the parcel is worth its budget either way.
    coins = _split_coins(coin_budget + remaining, rng)
    coin_value = coins['pp'] * 10 + coins['gp'] + coins['sp'] / 10 + coins['cp'] / 100
    value = int(round(coin_value + gem_spent + sum(i['price'] for i in items)))

    return {
        'cr': cr,
        'speed': speed,
        'budget': budget,
        'value': value,
        'coins': coins,
        'gems': gems,
        'items': [{'name': i['name'], 'price': i['price'], 'weight': i['weight'],
                   'slot': i['slot'], 'magic': i['kind'] == 'magic'} for i in items],
        'seed': seed,
    }


def capabilities():
    """What the sheet's feature-detect probe reads. Kept tiny and free of generation cost."""
    return {'ok': True, 'speeds': list(SPEEDS), 'cr': [MIN_CR, MAX_CR], 'version': 1}
