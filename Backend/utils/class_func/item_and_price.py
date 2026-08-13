import re, random, json
from utils.paths import repo_path
# Start of major task: Items and Prices
#
# PRICING CONTRACT: convert_price returns the item's gp cost as an int, or **None for "cannot be
# priced"** -- and None means UNBUYABLE (can_afford treats it as unaffordable), never free. It used
# to return 0 there, which mattered less than it sounds while the casing bug made every "+N" item
# unrollable -- but the moment those items became reachable, the windfall surfaced: a golden bought
# Ring of Protection +5 (50,000 gp) for 0, and another acquired ~97,700 gp of gear for 110 gp,
# because BOTH variant-extraction paths were broken (find_number was handed a list, so its regex
# never matched; the word regex carried an empty alternative that matched everywhere and then
# find_word's `(\d+)\D*` captured the "000" out of "12,000"). Two bugs masking each other is this
# file's history; gates/validate_item_names.py now prices the whole pool and fails on a windfall.

# One priced variant inside a blob: "18,000 gp (+3)" / "450(akoben)" -> (number, paren content).
_PRICED_VARIANT = re.compile(r'(\d{1,3}(?:,\d{3})*|\d+)\s*(?:gp)?\s*\(\s*([^)]+?)\s*\)', re.I)
# A blob that IS one plain price, give or take the scrape's own suffixes: "12,000 gp;" / "400".
_PLAIN_PRICE = re.compile(r'^\s*(\d{1,3}(?:,\d{3})*|\d+)\s*(?:gp)?\s*[.;]?\s*$', re.I)


def convert_price(character, price_input, name):
    blob = str(price_input)
    plain = _PLAIN_PRICE.match(blob)
    if plain:
        price = int(plain.group(1).replace(',', ''))
    else:
        # A multi-variant blob. The item's own name carries the variant tag -- "+5", "greater",
        # "akoben", "3 tricks" (sometimes fused straight onto the base name at scrape time) -- so
        # the matching PARENTHETICAL, not string position, is what selects the price. Longest
        # matching tag wins, so "(+1)" can never shadow "(+10)". A blob whose matching variant got
        # mangled at scrape time ("98,00, greater" -- no parenthesis left) finds nothing and the
        # item is refused rather than guessed at.
        price = None
        lowered = str(name).lower()
        best_len = 0
        for number, tag in _PRICED_VARIANT.findall(blob):
            tag = tag.strip().lower()
            if tag and tag in lowered and len(tag) > best_len:
                best_len = len(tag)
                price = int(number.replace(',', ''))
        if price is None:
            words = extract_dynamic_variable_word(character, name)
            if words:
                price = find_word(character, blob, words[-1])

    price = adjust_price(character, price)
    return price

def extract_dynamic_variable(character, name):
    number_pull = r'\d+'
    dynamic_variable = re.findall(number_pull, name)
    return dynamic_variable

def find_number(character, price_input, bonus):
    """The comma-grouped price whose parenthetical names this +bonus: '18,000 gp (+3)' -> 18000."""
    price_input = str(price_input)
    pattern = rf'(\d{{1,3}}(?:,\d{{3}})*|\d+)\s*(?:gp)?\s*\(\s*\+{re.escape(str(bonus))}\s*\)'
    match = re.search(pattern, price_input, re.I)
    return int(match.group(1).replace(',', '')) if match else None


def find_word(character, text, target_word):
    """The comma-grouped price whose parenthetical mentions the variant word:
    '12,000 gp (lesser), 24,000 gp (greater)' with 'lesser' -> 12000.

    The old pattern was `(\\d+)\\D*word`, which cannot cross the thousands separator and so
    captured the trailing '000' of '12,000' -- or, with a comma-less blob, whatever partial digit
    run sat closest. The price must be read as a full comma-grouped number anchored to the
    parenthetical that actually names the variant.
    """
    pattern = rf'(\d{{1,3}}(?:,\d{{3}})*|\d+)\s*(?:gp)?\s*\(\s*[^)]*{re.escape(target_word)}'
    match = re.search(pattern, str(text), re.I)
    return int(match.group(1).replace(',', '')) if match else None

def extract_dynamic_variable_word(character, name):
    # No trailing empty alternative: the old `...|type iv|)` matched the empty string at every
    # word boundary, so EVERY name "had" a variant word and find_word ran with target '' -- which
    # matched the first digits it saw. Only real variant words count, and only non-empty matches.
    word_pull = r'\b(lesser|greater|superior|major|minor|normal|djinni|efreeti|marid|shaitan|destined|fey|abyssal|accursed|celestial|draconic|elemental|infernal|undead|aberrant|adamantine|silver|cold iron|type i|type ii|type iii|type iv)\b(?![()])'
    return [word for word in re.findall(word_pull, str(name).lower()) if word]

def adjust_price(character, price):
    """1-10 reads as a bare +N bonus and prices at N^2 x 1000; None passes through as None.

    None used to collapse to 0 here, which is the free-item policy the module comment above is
    about. An unpriceable item now stays unpriceable and the caller skips it.
    """
    if isinstance(price, int) and not isinstance(price, bool):
        if price < 11:
            price = (price ** 2) * 1000
        return price
    return None

def capitalize_first_letter_each_word(s):
    return ' '.join([word.capitalize() for word in s.split()])


class ItemNameResolver:
    """Resolves a rolled item name to the FoundryVTT name list's OWN spelling.

    WHY THIS EXISTS -- the single largest defect this generator has shipped.
    ``choose_equipment`` used to Title-Case every rolled name before the membership test in
    ``item_chooser``, so "Belt of Mighty Constitution +4" went in as "Belt **Of** Mighty
    Constitution +4". ``foundry_item_names.json`` stores ``of`` lowercase, so the test failed and
    the retry loop silently re-rolled it. **1,888 of the 6,035 names contain " of " and NOT ONE
    survived the round-trip** -- the entire wondrous-item catalogue: Ring of Protection, Amulet of
    Natural Armor, Cloak of Resistance, every stat belt and headband. The big six were unbuyable.
    Measured consequence at level 20: 88x the gold bought +4 AC and nothing else, and HP, saves and
    damage were byte-identical across 300x wealth. Title-Case was only ever an approximation of
    "needs to be exact for FoundryVTT", and it was wrong for a third of the catalogue.
    `gates/validate_item_names.py` is the guard that stops this happening again silently.

    Resolution, in order:

    1. **Exact** case-insensitive hit -> the stored spelling.
    2. **Forward variant**: the pool says "belt of physical might +2", the list stores
       "Belt of Physical Might +2 (Str & Dex)" / "... (Str & Con)" -- the same item with the choice
       spelled out. First variant in sorted order, so this stays a pure function the gate can call;
       WHICH stat pair a character would rather have is a build decision and therefore the
       optimizer's, not random mode's.
    3. **Reverse variant**: the pool says "belt of impossible action (vudrani)", the list stores
       the bare "Belt of Impossible Action" -- a race/culture-restricted printing of a listed item.
       One trailing parenthetical is stripped and only an EXACT base hit accepted (26 real cases).
    4. Title-Case fallback. This matters: a genuinely unknown name must still FAIL the membership
       test so it lands on ``character.unresolved_items`` as the data-quality signal it is.

    Only the ``(`` form is ever variant-matched, never a comma -- "Kit, Psychic's" is a DIFFERENT
    item from "Kit", and a comma rule would happily conflate them.

    The input is SORTED before first-wins dedup, deliberately: 8 of the 6,035 names exist twice
    differing only in casing ("Signal Horn" / "Signal horn"), and ``Character._load_jsons``
    shuffles every list-shaped JSON per character -- unsorted, which spelling won FoundryVTT's
    exact-match test was a per-run coin flip. Sorting also keeps production and the gate (which
    reads the file unshuffled) resolving identically.
    """

    def __init__(self, data):
        names = list(data.keys()) if isinstance(data, dict) else list(data or [])
        self.exact = {}
        for name in sorted(str(n) for n in names):
            self.exact.setdefault(name.strip().lower(), name)
        # base -> first variant's canonical spelling, precomputed once so a miss in the retry loop
        # is O(1) instead of a linear scan of all ~6,000 entries per failed roll.
        self.variant_of = {}
        for stored in sorted(self.exact):
            if ' (' in stored:
                self.variant_of.setdefault(stored.split(' (', 1)[0], self.exact[stored])

    def resolve(self, name):
        key = str(name).strip().lower()
        hit = self.exact.get(key)
        if hit:
            return hit
        hit = self.variant_of.get(key)
        if hit:
            return hit
        if key.endswith(')') and ' (' in key:
            hit = self.exact.get(key[:key.rindex(' (')])
            if hit:
                return hit
        return capitalize_first_letter_each_word(name)


def slot_options(character, equipment_key, data, resolver):
    """Every item in one slot that both resolves and the character can afford right now.

    Returns ``[(canonical_name, price, description)]``. Used only by ``item_chooser``'s second
    pass -- the first pass keeps its single uniform draw so that a well-funded character's gear
    stays as chaotic as random mode intends.
    """
    options = []
    item_dict = character.items[str(equipment_key)]
    for raw in item_dict:
        name = resolver.resolve(raw)
        if name not in data:
            continue
        price = convert_price(character, str(item_dict[raw]['price']), raw)
        if not can_afford(character, price):
            continue
        options.append((name, price, item_dictionary(character, raw, equipment_key)))
    return options


# How many draws the first pass spends on a slot before giving up on it. No slot is anywhere near
# 100% unresolvable today (worst is neck at 34%), so in practice this never triggers -- it exists
# because the retry loop used to be UNBOUNDED, and a slot drifting to fully-unresolvable via a data
# edit would have hung the request forever with no error. A capped-out slot is not lost: the second
# pass draws it from resolvable stock directly.
FIRST_PASS_DRAW_CAP = 100


# --- The optimized gear ladder (spec 15, rulings 2026-08-11) --------------------------------------
# power_roles.json ladder tokens -> concrete items_best.json purchases. The *_enhancement tokens
# are NOT bought here -- plan_enhancements already spends the reserved share under the role's own
# split -- so in this module they are documentation of the ladder's intent, not purchases.
# Spellings are items_best.json's own (the slot dicts are matched case-insensitively and the
# resolver canonicalises for FoundryVTT). One purchase per body slot: when the primary stat item
# and the con item both want the belt slot, the first token in ladder order wins and the second is
# skipped -- combined items (Belt of Physical Might) are a later refinement, recorded in the spec.
STAT_ITEM_TEMPLATES = {
    'str': ('belts', 'belt of giant strength +{n}'),
    'dex': ('belts', 'belt of incredible dexterity +{n}'),
    'con': ('belts', 'belt of mighty constitution +{n}'),
    'int': ('headband', 'headband of vast intelligence +{n}'),
    'wis': ('headband', 'headband of inspired wisdom +{n}'),
    'cha': ('headband', 'headband of alluring charisma +{n}'),
}
LADDER_FIXED = {
    'cloak_of_resistance': ('shoulders', 'cloak of resistance +{n}', (5, 4, 3, 2, 1)),
    'ring_of_protection': ('rings', 'ring of protection +{n}', (5, 4, 3, 2, 1)),
    'amulet_of_natural_armor': ('neck', 'amulet of natural armor +{n}', (5, 4, 3, 2, 1)),
    # The activated-haste item (the sweaty pass): one extra full-BAB attack in the metric's nova
    # round. Single tier -- the {n}-less template formats to itself.
    'boots_of_speed': ('feet', 'boots of speed', (0,)),
    # The wall pass: +1 luck AC; its ledger change reaches base ac on BOTH parity sides.
    'jingasa': ('head', 'jingasa of the fortunate soldier', (0,)),
}
STAT_ITEM_TIERS = (6, 4, 2)


def _slot_lookup(character, slot, wanted):
    """The slot dict's own key for `wanted` (case-insensitive), or None."""
    for raw in character.items.get(slot) or {}:
        if str(raw).strip().lower() == wanted:
            return raw
    return None


def ladder_purchases(character, resolver):
    """Buy the role's chosen gear ladder: best affordable tier of each named piece, in order.

    Returns [(slot, canonical_name, price, description)] and deducts gold. Empty (and draws
    NOTHING from the RNG) when the character has no role, which is what keeps random mode
    byte-identical. Greedy top-down per token -- the +5 cloak before the +4 -- because the ladder
    IS the priority statement; a token whose best tier is unaffordable degrades tier by tier
    rather than being skipped.
    """
    role = getattr(character, 'role', None)
    if not role:
        return []
    from utils.class_func.power_role import stat_order
    order = stat_order(character) or []
    steps = (role.get('gear_ladders') or {}).get(role.get('_chosen_ladder')) or []
    filled, purchases = set(), []
    for token in steps:
        if token.endswith('_enhancement'):
            continue
        if token in LADDER_FIXED:
            slot, template, tiers = LADDER_FIXED[token]
        else:
            if token == 'con_item':
                ability = 'con'
            elif token == 'primary_stat_item' and order:
                ability = order[0]
            elif token == 'secondary_stat_item' and len(order) > 1:
                ability = order[1]
            else:
                continue
            entry = STAT_ITEM_TEMPLATES.get(ability)
            if not entry:
                continue
            slot, template = entry
            tiers = STAT_ITEM_TIERS
        if slot in filled:
            continue
        for index, tier in enumerate(tiers):
            raw = _slot_lookup(character, slot, template.format(n=tier))
            if raw is None:
                continue
            price = convert_price(character, str(character.items[slot][raw]['price']), raw)
            if not can_afford(character, price):
                continue
            # Spread before upgrading: one purchase never eats more than half the remaining
            # purse unless it is the token's cheapest tier -- a greedy +5 ring at mid levels
            # starved the cloak, amulet and jingasa out of existence (the wall QC card's own
            # finding), and four +2s beat one +5 on every axis the roles measure.
            last_tier = index == len(tiers) - 1
            if not last_tier and isinstance(character.gold, int) and price > character.gold // 2:
                continue
            subtract_price_from_gold(character, price)
            purchases.append((slot, resolver.resolve(raw), price,
                              item_dictionary(character, raw, slot)))
            filled.add(slot)
            break
    return purchases


def item_chooser(character, data):
    i = 0
    k = 0
    # i = character.determine_start_index()
    select_from_list = list(character.items.keys())
    price_total = []
    equipment_list = []
    equip_dict = {}
    # Items rolled that the FoundryVTT name list can't resolve. Collected per character and folded
    # into the payload's buff_gaps by main_test -- see log_error() on why this is no longer a file.
    unresolved = {}
    character.unresolved_items = unresolved
    resolver = ItemNameResolver(data)
    # Purchases per slot, so the second pass knows what pass one already filled -- including the
    # two-ring convention, which equip_dict alone cannot express (it is keyed by slot name).
    bought = {}

    # OPTIMIZED MODE ONLY: the role's gear ladder shops first -- big six by the role's priority,
    # best affordable tier of each. Slots it fills are withheld from the first pass entirely (a
    # second draw there would evict the ladder's purchase via the slot-keyed equip_dict); the
    # second pass still tops up anything due more (the second ring). Random mode gets an empty
    # list and an untouched RNG stream.
    ladder_slots = set()
    for slot, name, price, equip_descrip in ladder_purchases(character, resolver):
        bought[slot] = bought.get(slot, 0) + 1
        equipment_list.append(name)
        equip_dict[slot] = {'item_name': name, 'description': equip_descrip}
        price_total.append(price)
        ladder_slots.add(slot)

    while i < len(select_from_list):
        if select_from_list[i] in ladder_slots:
            i += 1
            continue
        equipment_name, random_equip, price, equip_descrip = choose_equipment(character, select_from_list[i], resolver)
        draws = 1
        while random_equip not in data and draws < FIRST_PASS_DRAW_CAP:
            unresolved[str(random_equip)] = None
            equipment_name, random_equip, price, equip_descrip = choose_equipment(character, select_from_list[i], resolver)
            draws += 1
        if random_equip not in data:
            i += 1
            continue          # capped out -- leave the slot to the second pass

        # Check BEFORE buying. This used to subtract first and then `break` on gold <= 0, which meant
        # the character paid for an item that was never added to the list, ended up with negative gold,
        # AND abandoned every remaining slot even when something cheap would have fit. Now an
        # unaffordable slot is simply skipped and the batch continues, so gold never goes below 0.
        if not can_afford(character, price):
            i += 1
            continue

        subtract_price_from_gold(character, price)
        # Ring bookkeeping only runs on a real purchase, so a skipped ring doesn't burn the
        # character's second-ring slot.
        i,k = grab_two_rings(character, select_from_list[i], k, i)

        bought[equipment_name] = bought.get(equipment_name, 0) + 1
        equipment_list.append(random_equip)
        equip_details = {'item_name': random_equip, 'description': equip_descrip}

        equip_dict[equipment_name] = equip_details
        price_total.append(price)

        i += 1

    # SECOND PASS -- the slots that bought less than their due get one more look, restricted to
    # what the purse can actually reach. The first pass draws ONE item per slot and skips the slot
    # outright when that draw is unaffordable, so a character could walk away from a slot it could
    # easily have filled from the cheaper end. That is the code failing its own stated intent ("an
    # unaffordable slot is simply skipped and the batch continues"), not random mode being chaotic
    # on purpose -- WHICH item gets drawn stays uniform, deliberately, because preferring the
    # powerful one is the optimizer's job and not random mode's.
    #
    # Rings are due TWO purchases (the grab_two_rings convention); every other slot one. The
    # options are re-filtered between buys because each purchase shrinks the purse. One pass
    # suffices and terminates: gold only ever decreases, so a slot with no affordable option now
    # cannot acquire one later.
    for equipment_key in select_from_list:
        due = 2 if equipment_key == 'rings' else 1
        while bought.get(equipment_key, 0) < due:
            options = slot_options(character, equipment_key, data, resolver)
            if not options:
                break
            name, price, equip_descrip = random.choice(options)
            subtract_price_from_gold(character, price)
            bought[equipment_key] = bought.get(equipment_key, 0) + 1
            equipment_list.append(name)
            equip_dict[equipment_key] = {'item_name': name, 'description': equip_descrip}
            price_total.append(price)

    return equipment_list, equip_dict

def item_dictionary(character, random_equip, equipment_key):
    items = character.items
    equip_descrip = items.get(equipment_key, {}).get(random_equip, {}).get('description', {})
    return equip_descrip


def determine_start_index(character):
    if character.armor_type is None:
        return 2
    elif character.armor_type == 'L' or character.weapons[1] in ('Axes', 'Blades, Heavy', 'Bows', 'Crossbows', 'Double', 'Firearms', 'Polearms', 'Siege Engines'):
        return 1
    else:
        return 0
    
def choose_equipment(character, equipment_key, resolver=None):
    equipment_name = equipment_key
    item_dict = character.items[str(equipment_key)]
    random_equip = random.choice(list(item_dict.keys()))
    price = str(item_dict[random_equip]['price'])
    price = convert_price(character, price, random_equip)
    equip_descrip = item_dictionary(character, random_equip, equipment_key)

    # The name has to be EXACT for FoundryVTT, so resolve it to the canonical spelling the name
    # list holds. `resolver` is optional only so a caller without the list still gets the old
    # Title-Case behaviour; see ItemNameResolver for what Title-Casing on its own used to cost.
    if resolver is not None:
        random_equip = resolver.resolve(random_equip)
    else:
        random_equip = capitalize_first_letter_each_word(random_equip)
    return equipment_name, random_equip, price, equip_descrip

def can_afford(character, price):
    """True when the character can pay ``price`` without going below 0 gold. Unusable prices (None, or
    a non-int purse) are treated as unaffordable so the caller skips the slot rather than guessing."""
    if price is None or not isinstance(character.gold, int):
        return False
    try:
        return character.gold - int(price) >= 0
    except (TypeError, ValueError):
        return False


def subtract_price_from_gold(character, price):
    if price != None and isinstance(character.gold, int):
        character.gold -= int(price)
    else:
        # Previously this zeroed the character's entire purse whenever a price was unusable -- a
        # silent, total loss of gold. Callers now gate on can_afford(), so this branch only fires on
        # malformed data: leave the gold alone and say so.
        print(f"item_and_price: skipping unusable price {price!r}; gold left at {character.gold!r}")

def grab_two_rings(character, equipment_key, k, i):
    if equipment_key == "rings" and k < 1:
        i -= 1
        k += 10
    return i,k
    
# log_error() was removed. It read Backend/json/items_broken.json, appended the unresolved item and
# wrote the file back, in the middle of generating a character -- an unlocked read-modify-write that
# four gunicorn workers raced on, mutating a repo file as a side effect of an HTTP request. It also
# accumulated forever, so the file recorded every item ever missed rather than what this character
# hit. item_chooser now collects unresolved names on character.unresolved_items and main_test folds
# them into the payload's buff_gaps, which is the same channel the curated-buff mismatches use.



# End of major task: Items and Prices