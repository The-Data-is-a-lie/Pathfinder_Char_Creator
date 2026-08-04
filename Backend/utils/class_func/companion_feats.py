"""A bonded creature's feat economy: which feats it takes, when it took them, and its flaws.

Spec section 8, D15/D16. Replaces the pick-loop that used to live in `animal_companions.animal_feats`
-- `random.choice` over a bag of 27 lowercase strings, with no prerequisite check, no record of when
a feat was gained, no feat tax and no flaws.

FOUR THINGS THIS MODULE IS CAREFUL ABOUT
----------------------------------------
1. IT DRAWS FROM THE CREATURE'S OWN GENERATOR. `companion_stats._rng`, salted, never the global
   `random`. A companion's feats must not churn its master's gear, feats and backstory -- the same
   ruling `companion_stats` records for skill ranks, now applied to the larger draw this module
   makes. Salted so the feat roll and the later skill roll are independent streams.

2. THE CHASSIS DATES EVERY SLOT. `animal_companion.json`'s `feats` column ticks up at effective
   levels 1, 2, 5, 8, 10, 13, ... and that IS the grant level -- the companion's answer to
   `class_bonus_feat_slots`. It gives the label its number (`Animal Companion 5: Weapon Focus`,
   parallel to `Fighter 1: Weapon Focus`) and the feat-tax cadence its anchor.

3. PICKS ARE GATED, ONE AT A TIME. The legal set is recomputed after every pick, so a chain can
   build itself -- Dodge then Mobility then Spring Attack -- which a single up-front filter could
   never do. Most animals fail Dex 13 or Str 13 outright, and that is the point: an Int-2 body with
   Str 6 has no business with Power Attack.

4. TAX CHILDREN LEAVE THE POOL, BUT NOT THE BODY. `feat_tax_func` runs unchanged, on an adapter
   (see `_TaxAdapter`); its children are then filtered by `legal_for_companion`, which fails CLOSED.
   A prerequisite this module cannot read is a prerequisite it refuses -- that is what drops
   `greater weapon focus` (fighter 8) and `martial focus` (a weapon group a wolf does not have)
   without needing a hand-written blocklist of either.
"""
import re

import pandas as pd

from utils.paths import repo_path
from utils.class_func.companion_stats import _abilities, _rng, merge_advancement
from utils.class_func.feat_tax import feat_tax_func
from utils.class_func.flaws import ANIMAL_FLAWS, pick_flaws
from utils.class_func.level_and_bab import misc_homebrew_enabled
from utils.class_func.randomize_flaw import randomize_flaw_amount

# The creature types that ride the animal chassis and therefore have this feat economy. Familiars
# use their master's feats (RAW) and eidolons are evolution-driven; neither resolves to an entry
# today anyway -- see `animal_companions`' "WHAT THIS SLICE DOES NOT DO".
CHASSIS_TYPES = ('companion', 'mount')

# How each creature type reads in a feat label. `Animal Companion 5: Weapon Focus`.
TYPE_NOUNS = {'companion': 'Animal Companion', 'mount': 'Mount',
              'familiar': 'Familiar', 'eidolon': 'Eidolon'}

_ABILITY_RE = re.compile(r'^(str|dex|con|int|wis|cha)\s+(\d+)$', re.IGNORECASE)
_BAB_RE = re.compile(r'^base attack bonus\s*\+?(\d+)$', re.IGNORECASE)
# "Character level 4th", "Fighter level 8th", "3 ranks in Acrobatics" -- everything a creature with
# no class and no rank record can never satisfy. Named so the refusal is legible in a diff.
_CLASS_LEVEL_RE = re.compile(r'\blevel\b', re.IGNORECASE)
# Prerequisites that are simply true for a body with natural attacks.
_ALWAYS_TRUE = {'natural weapon', 'natural attack'}

_CSV_CACHE = None


def _prereq_table():
    """{normalised feat name: (canonical name, prerequisite string)} from data/feats.csv."""
    global _CSV_CACHE
    if _CSV_CACHE is None:
        frame = pd.read_csv(repo_path('data/feats.csv'), sep='|', on_bad_lines='skip')
        table = {}
        for name, prereq in zip(frame['name'], frame.get('prerequisites')):
            if not isinstance(name, str):
                continue
            key = _norm(name)
            # First row wins; a Mythic duplicate must not overwrite the normal feat's prerequisites.
            table.setdefault(key, (name, prereq if isinstance(prereq, str) else ''))
        _CSV_CACHE = table
    return _CSV_CACHE


def _norm(text):
    return re.sub(r'[^a-z0-9]+', '', str(text).lower())


def canonical_name(name):
    """`data/feats.csv` spelling for a name in any casing, or the name unchanged."""
    found = _prereq_table().get(_norm(name))
    return found[0] if found else name


def legal_for_companion(name, owned, abilities, bab):
    """Can this creature take `name`? Fails CLOSED on anything it cannot read.

    Returns `(True, None)` or `(False, reason)`; the reason is kept because a silently missing feat
    is indistinguishable from one that was never rolled.
    """
    found = _prereq_table().get(_norm(name))
    if found is None:
        return False, 'not in data/feats.csv'
    prereq = (found[1] or '').strip().rstrip('.')
    if not prereq:
        return True, None

    owned_n = {_norm(item) for item in owned}
    for part in (piece.strip() for piece in prereq.split(',')):
        if not part:
            continue
        low = part.lower().rstrip('.')
        if low in _ALWAYS_TRUE:
            continue
        match = _ABILITY_RE.match(low)
        if match:
            score = abilities.get(match.group(1).lower())
            if score is None or int(score) < int(match.group(2)):
                return False, f'{part} (has {score})'
            continue
        match = _BAB_RE.match(low)
        if match:
            if bab < int(match.group(1)):
                return False, f'{part} (has +{bab})'
            continue
        if _CLASS_LEVEL_RE.search(low):
            # A class level or a rank count. A bonded creature has neither, and D12 already
            # established that none of the PC's class-shaped machinery applies to it.
            return False, f'{part} (a bonded creature has no class levels or rank record)'
        if _norm(part) in owned_n:
            continue
        # A feat it does not own, or a prerequisite this reader does not understand -- a weapon
        # group, a proficiency, spellcasting, a body part. Refuse either way.
        return False, part
    return True, None


def _slot_levels(chassis_table, effective_level):
    """The effective level at which each feat slot opened, in order.

    The chassis row's `feats` count is the authority for HOW MANY; this walks the same table to
    recover WHEN, which is what a label needs and what the tax cadence is measured from.
    """
    levels, previous = [], 0
    for level in sorted((int(key) for key in chassis_table), key=int):
        count = int((chassis_table.get(str(level)) or {}).get('feats') or 0)
        if level > (effective_level or 0):
            break
        for _ in range(max(0, count - previous)):
            levels.append(level)
        previous = max(previous, count)
    return levels


class _TaxAdapter:
    """The four attributes `feat_tax_func` actually reads, wrapped around a bonded creature.

    D12 found none of the PC's machinery reusable because it all iterates `character.classes`. The
    feat-tax resolver is the exception: it reads `feat_tax`, `level`, `chooseable`, `filter_pattern`
    and one `class_entry_for` gate, so a four-line stand-in buys the whole chain resolver. The
    pattern (and its precedent) is `Backend/scripts/_smoke_spheres.py`'s `Mock`.
    """

    C_CLASS = 'animal companion'

    def __init__(self, character, entry, owned):
        self.feat_tax = getattr(character, 'feat_tax', None) or {}
        self.level = int(entry.get('effective_level') or 0)
        self.chooseable = set(owned)
        self.filter_pattern = getattr(character, 'filter_pattern', None) or re.compile(r'(?!x)x')
        self.c_class = self.C_CLASS
        self.classes = [{'name': self.C_CLASS, 'level': self.level}]


def _pick(pool, owned, abilities, bab, rng, wanted, refusals):
    """Pick `wanted` legal feats, recomputing the legal set after each one so chains can build."""
    picked = []
    while len(picked) < wanted:
        legal = []
        for name in pool:
            if name in owned:
                continue
            ok, reason = legal_for_companion(name, owned, abilities, bab)
            if ok:
                legal.append(name)
            elif reason:
                refusals.setdefault(name, reason)
        if not legal:
            break
        choice = rng.choice(legal)
        picked.append(choice)
        owned.add(choice)
        refusals.pop(choice, None)
    return picked


def _tax(character, entry, owned, levels, feats, abilities, bab, allowed, granted):
    """Feat-tax bundles for one creature, with every child re-checked against the body.

    TWO gates, and both are needed. `allowed` is the curated `tax_children` list: the derived chains
    run to 128 feats and a prerequisite reader cannot refuse Drunken Brawler or Wand Dancer, because
    their prerequisites really are met. `legal_for_companion` is the mechanical half on top of it --
    the allowlist says a feat SUITS an animal, not that this animal qualifies.
    """
    bundles = feat_tax_func(_TaxAdapter(character, entry, owned), feats, levels, granted)
    out, dropped = {}, []
    for primary, children in (bundles or {}).items():
        kept = []
        for child in children or []:
            name = canonical_name(child)
            if _norm(name) not in allowed:
                dropped.append(f'{name} (via {primary}): not on the bonded-creature tax allowlist')
                granted.discard(_norm(child))
                continue
            ok, reason = legal_for_companion(name, owned, abilities, bab)
            if ok:
                kept.append(name)
                owned.add(name)
            else:
                dropped.append(f'{name} (via {primary}): {reason}')
                granted.discard(_norm(child))
        if kept:
            out[primary] = kept
    return out, dropped


def companion_feats(character):
    """Roll feats, feat-tax bundles and flaws onto every chassis-driven bonded creature.

    Writes, per entry: `feats` (plain names -- the frozen `animal_companion` alias reads this object,
    so it must stay a bare list), `feat_labels` parallel to it, `feat_tax_dict`, `flaw_feats`,
    `flaws`, `flaw_effects`, `flaw_feat_amount` and `feat_notes` (what was refused, and why).

    Returns the union of every creature's chassis feats, which is what the deprecated
    `animal_companion` alias exports.
    """
    entries = [entry for entry in getattr(character, 'bonded_creatures', None) or []
               if entry.get('type') in CHASSIS_TYPES and entry.get('species')]
    if not entries:
        return None
    chassis = getattr(character, 'animal_companion', None) or {}
    chassis_table = chassis.get('companion') or {}
    pool = sorted(chassis.get('feats') or [])
    allowed = {_norm(name) for name in chassis.get('tax_children') or []}
    if not pool:
        return None

    union = set()
    for entry in entries:
        rng = _rng(entry, salt='feats')
        chassis = entry.get('chassis') or {}
        bab = int(chassis.get('bab') or 0)
        merged, _ = merge_advancement(entry.get('species_stats'),
                                      entry.get('effective_level') or 0)
        abilities = _abilities(merged, chassis)

        # Flaws first: they buy feats, so the slot count depends on them.
        flaw_amount = randomize_flaw_amount(rng)
        flaw_names, flaw_effects = pick_flaws(flaw_amount, ANIMAL_FLAWS, rng)
        flaw_feat_amount = (min(len(flaw_names) // 2 + 1, 3)
                            if flaw_names and misc_homebrew_enabled(character) else 0)

        owned, refusals = set(), {}
        levels = _slot_levels(chassis_table, entry.get('effective_level'))
        wanted = min(int(chassis.get('feats') or 0), len(levels))
        feats = _pick(pool, owned, abilities, bab, rng, wanted, refusals)
        flaw_feats = _pick(pool, owned, abilities, bab, rng, flaw_feat_amount, refusals)

        noun = TYPE_NOUNS.get(entry.get('type'), 'Companion')
        granted = set()
        tax, dropped = _tax(character, entry, owned, levels[:len(feats)], feats,
                            abilities, bab, allowed, granted)
        flaw_tax, flaw_dropped = _tax(character, entry, owned, [levels[0]] * len(flaw_feats)
                                      if levels else None, flaw_feats, abilities, bab,
                                      allowed, granted)
        tax.update(flaw_tax)

        entry['feats'] = feats
        entry['feat_labels'] = [f'{noun} {level}' for level in levels[:len(feats)]]
        entry['flaw_feats'] = flaw_feats
        entry['feat_tax_dict'] = tax
        entry['flaws'] = flaw_names
        entry['flaw_effects'] = flaw_effects
        entry['flaw_feat_amount'] = flaw_feat_amount
        entry['feat_notes'] = _notes(pool, feats, flaw_feats, refusals, dropped + flaw_dropped)
        union |= set(feats)
    return union


def _notes(pool, feats, flaw_feats, refusals, dropped):
    """Why the creature does not have the rest of the pool. Reported, never implied by absence."""
    notes = []
    unfilled = [name for name in pool if name not in set(feats) | set(flaw_feats)]
    for name in unfilled:
        reason = refusals.get(name)
        if reason:
            notes.append(f'{name}: ineligible -- {reason}')
    for line in dropped:
        notes.append(f'feat tax dropped {line}')
    return notes
