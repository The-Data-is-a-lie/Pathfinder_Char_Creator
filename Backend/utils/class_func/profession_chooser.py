"""Professions (homebrew expanded sub-system).

Beyond a class and level, every character has one or more *professions* — vocations like "shoemaker"
or "blacksmith" — modelled as Profession (X) skills with ranks and a tier of unlocks. For NPC
generation we use the campaign's heuristic for the rank pool:

    profession rank pool = 5 + character level + 10 per profession feat taken

Each individual profession caps at **10 ranks**, EXCEPT one (the primary/backstory vocation) that can
reach **15 when True Calling is taken**. The pool is spread across as many professions as needed to
absorb it (primary first). Profession feats (homebrew; not in any feat CSV):
    - True Calling    : one profession's cap rises from 10 to 15.
    - Multi Talented  : you can invest more total ranks (feeds the +10/feat pool term).
    - Always Improving: you may spend ordinary skill ranks in your chosen profession.
When the character's feats are NOT randomized (curated build), we take at least two profession feats.

Ranks unlock benefits (homebrew doc): associate skills at ranks 1/4/7/10, a set of tiered abilities at
rank 5, and a stronger set at rank 15 (only the True Calling profession reaches it). The abilities are
assigned by ``profession_abilities.assign_profession_abilities`` — tier is fixed by the profession's
name-prestige, theme by the same name (or the character's class for high/top tiers).

The function records everything on ``character`` (``profession_chosen``, ``profession_data``,
``profession_feats``, ``profession_feat_desc``, ``profession_pool``) and returns the list of profession
display names for the legacy ``professions`` export field.
"""
import random

from utils import data
from utils.class_func.profession_abilities import (
    assign_profession_abilities, _theme_for, _tier_for, catalog_professions)

# Homebrew profession feats, taken top-to-bottom. Multi Talented comes FIRST because it is the only
# one that buys ranks (it feeds the +10/feat term of the pool); True Calling and Always Improving are
# one-shot riders on a pool that already exists. Multi Talented is repeatable up to
# 1 + level//10 times -- every surplus pick beyond the three below is another Multi Talented.
PROFESSION_FEATS = [
    ("Multi Talented",
     "Your profession rank cap increases by 10."),
    ("True Calling",
     "Your natural Profession rank cap rises to 15 in one qualifying profession."),
    ("Always Improving",
     "You can spend ordinary skill ranks in your chosen profession. (Requires True Calling and 15 ranks.)"),
]
_MULTI_TALENTED = PROFESSION_FEATS[0][0]

# Generic associate skills a profession can unlock at ranks 1/4/7/10 (themed loosely; the GM refines).
_ASSOCIATE_SKILLS = [
    "Appraise", "Craft", "Diplomacy", "Knowledge (local)", "Perception",
    "Profession", "Sense Motive", "Sleight of Hand", "Use Magic Device", "Handle Animal",
]

_BASE_CAP = 10          # every profession caps here ...
_TRUE_CALLING_CAP = 15  # ... except the one True Calling profession

# Target distribution of GENERATED professions (weighted selection in _themed_profession_names).
# The TIER marginal is honored exactly; the GENRE marginal is approximated within each rolled tier
# (tier and genre are correlated -- there is no top-tier gongfarmer). Tune GENRE_WEIGHTS empirically.
_TIER_WEIGHTS = {"garbage": 5, "bad": 35, "average": 35, "good": 20, "high": 3, "top": 2}
_GENRE_WEIGHTS = {   # relative weights (auto-normalised), by how common the archetype is in fantasy
    "craft": 15, "martial": 13, "nature": 8, "divine": 7, "arcane": 7, "noble": 6,
    "scholar": 5, "skill": 5, "wayfarer": 5, "trade": 4.5, "performance": 4, "service": 4,
    "occult": 3.5, "medical": 3, "alchemy": 3, "villain": 3, "menial": 2.5,
    "elementalist": 2, "ki": 2,
}
_PROFESSION_INDEX = None   # {tier: {genre: [display names]}} -- built once from the whole pool


def _max_multi_talented(level):
    """Multi Talented is repeatable 1 + one-per-10-levels times."""
    return 1 + (level // 10)


def _roll_profession_feat_count(truly_random_feats, level):
    """How many profession feats to take: a roll, plus one guaranteed feat per 10 character levels.
    Curated builds floor the roll at 2 (per the campaign rule); randomized builds may roll 0."""
    base = random.choice([0, 0, 1, 1, 2, 3])
    if str(truly_random_feats).upper() == "N":
        base = max(2, base)
    return base + (level // 10)


_ORDINALS = ["", "", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"]


def _pick_profession_feats(n, level):
    """Take ``n`` profession feats in order -- Multi Talented, True Calling, Always Improving -- then
    spend every surplus pick on another Multi Talented (repeatable ``1 + level//10`` times).

    Returns ``([(name, desc)], mt_count)``. Each repeat is its OWN entry ("Multi Talented (2nd)",
    "Multi Talented (3rd)", mirroring the "Extra Magic Talent (<suffix>)" convention in spheres.py) --
    NOT collapsed into one line. main_test.py reserves feat slots with
    ``len(character.profession_feats)``, so a collapsed entry would buy +10 profession ranks per repeat
    while paying the feat tax only once.
    """
    n = max(0, n)
    if n <= 0:
        return [], 0

    unique = list(PROFESSION_FEATS[:n])
    mt_cap = _max_multi_talented(level)
    # picks beyond the three unique feats are extra Multi Talented, bounded by its repeat cap
    mt_count = min(mt_cap, 1 + max(0, n - len(PROFESSION_FEATS)))

    out = list(unique)
    mt_desc = dict(PROFESSION_FEATS)[_MULTI_TALENTED]
    for i in range(2, mt_count + 1):
        ordinal = _ORDINALS[i] if i < len(_ORDINALS) else f"{i}th"
        out.append((f"{_MULTI_TALENTED} ({ordinal})",
                    f"{mt_desc} This is the {ordinal} time you have taken this feat."))
    return out, mt_count


def _cap_for(idx, has_true_calling):
    """Per-profession rank cap: 10 for all, 15 for the primary (idx 0) only with True Calling."""
    return _TRUE_CALLING_CAP if (has_true_calling and idx == 0) else _BASE_CAP


def _split_pool(remaining, cap=_BASE_CAP):
    """Split ``remaining`` ranks into a random number of professions, each getting 1..cap ranks.

    The COUNT is chosen first (``ceil(remaining/cap)`` plus a small random spread) and the split is
    then built to sum to exactly ``remaining`` -- so no ranks can be truncated by a profession bound,
    which is how the old fill-to-cap-then-clamp version lost ranks off the end of a big pool.
    Produces the "one strong vocation plus a few dabbles" texture rather than 10/10/10.
    """
    if remaining <= 0:
        return []
    min_needed = -(-remaining // cap)                 # ceil
    max_allowed = remaining                           # every profession at 1 rank
    count = min(min_needed + random.randint(0, 2), max_allowed)

    parts = [1] * count                               # every profession gets at least 1
    left = remaining - count
    while left > 0:
        open_idx = [i for i, p in enumerate(parts) if p < cap]
        if not open_idx:                              # can't happen (count >= ceil), belt and braces
            parts[-1] += left
            break
        i = random.choice(open_idx)
        take = min(left, cap - parts[i], random.randint(1, cap))
        parts[i] += take
        left -= take
    random.shuffle(parts)
    return parts


def _profession_index():
    """Classify the whole profession pool (legacy ``data.professions`` + the curated catalog) into a
    ``{tier: {genre: [names]}}`` index, built once, for target-weighted selection."""
    global _PROFESSION_INDEX
    if _PROFESSION_INDEX is None:
        pool = list(getattr(data, "professions", []) or []) + catalog_professions()
        idx, seen = {}, set()
        for name in pool:
            key = str(name).strip()
            if not key or key.lower() in seen:
                continue
            seen.add(key.lower())
            idx.setdefault(_tier_for(key), {}).setdefault(_theme_for(key), []).append(key)
        _PROFESSION_INDEX = idx
    return _PROFESSION_INDEX


def _themed_profession_names(character, count):
    """Pick ``count`` distinct profession names following the target distributions: roll a tier from
    ``_TIER_WEIGHTS`` (exact marginal), then a genre present at that tier from ``_GENRE_WEIGHTS``
    (approximate marginal), then a random unused name from that cell. Falls back within the tier, then
    anywhere, if a cell is exhausted."""
    idx = _profession_index()
    if not idx:
        return ["Laborer"] * count
    tiers = [t for t in _TIER_WEIGHTS if t in idx]
    tier_w = [_TIER_WEIGHTS[t] for t in tiers]
    chosen, chosen_l = [], set()
    attempts = 0
    while len(chosen) < count and attempts < count * 40:
        attempts += 1
        tier = random.choices(tiers, weights=tier_w, k=1)[0]
        genres = list(idx[tier].keys())
        genre = random.choices(genres, weights=[_GENRE_WEIGHTS.get(g, 1) for g in genres], k=1)[0]
        candidates = [nm for nm in idx[tier][genre] if nm.lower() not in chosen_l]
        if not candidates:   # relax: any unused at this tier, then any unused anywhere
            candidates = [nm for g in idx[tier].values() for nm in g if nm.lower() not in chosen_l]
        if not candidates:
            candidates = [nm for t in idx.values() for g in t.values() for nm in g
                          if nm.lower() not in chosen_l]
        if not candidates:
            break
        pick = random.choice(candidates)
        chosen.append(pick)
        chosen_l.add(pick.lower())
    while len(chosen) < count:
        chosen.append("Laborer")
    return chosen[:count]


def _pick_associate_skills(ranks):
    """Associate skills unlocked so far: one per rank threshold (1/4/7/10) reached."""
    count = sum(1 for threshold in (1, 4, 7, 10) if ranks >= threshold)
    if not count:
        return []
    return random.sample(_ASSOCIATE_SKILLS, k=min(count, len(_ASSOCIATE_SKILLS)))


def profession_chooser(character, professions, truly_random_feats="Y"):
    """Build the character's profession sub-system. ``professions`` is the data attribute name to
    sample from ("professions"). Returns the list of profession display names (legacy field)."""
    # 1. Profession feats. ONLY Multi Talented buys ranks (+10 each); True Calling grants the 15-cap
    #    and Always Improving opens the profession to ordinary skill ranks.
    level = getattr(character, "level", 0) or 0
    feats, mt_count = _pick_profession_feats(_roll_profession_feat_count(truly_random_feats, level), level)
    feat_names = [name for name, _desc in feats]
    has_true_calling = "True Calling" in feat_names

    # 2. Rank pool: base 5, +1 per level, +10 per Multi Talented pick.
    pool = 5 + level + 10 * mt_count

    # 3. Distribute. The True Calling profession takes its 15-rank cap first (that is what the feat is
    #    for); the remainder spreads as random 1-10 chunks across a count picked up front, so the split
    #    always sums to exactly `pool` -- no profession bound can truncate it.
    ranks_list = []
    remaining = pool
    if has_true_calling:
        primary_ranks = min(remaining, _TRUE_CALLING_CAP)
        ranks_list.append(primary_ranks)
        remaining -= primary_ranks
    ranks_list.extend(_split_pool(remaining))

    names = _themed_profession_names(character, len(ranks_list))
    profession_data = []
    for idx, (name, ranks) in enumerate(zip(names, ranks_list)):
        profession_data.append({
            "name": name,
            "skill_label": f"Profession ({name})",
            "ranks": ranks,
            "cap": _cap_for(idx, has_true_calling),
            "associate_skills": _pick_associate_skills(ranks),
        })

    assigned = sum(p["ranks"] for p in profession_data)
    if assigned != pool:
        print(f"professions: WARNING distributed {assigned} of {pool} pool ranks")

    # 4. Record on the character for the exporter / skill-unlock picker / backstory.
    character.profession_chosen = [p["name"] for p in profession_data]
    character.profession_data = profession_data
    character.profession_feats = feat_names
    character.profession_feat_desc = {name: desc for name, desc in feats}
    character.profession_pool = pool

    # 5. Grant tiered abilities (rank-5 / rank-15 entries) keyed off each profession's name-prestige.
    assign_profession_abilities(character)

    print(f"professions -> {[p['skill_label'] + ' r' + str(p['ranks']) + '/' + str(p['cap']) for p in profession_data]}, "
          f"pool {pool}, feats {feat_names}")
    return character.profession_chosen


def apply_always_improving_ranks(character, skill_ranks):
    """Fold ordinary Profession skill ranks into ``character.profession_data`` (Always Improving only).

    ``skills_selector`` only puts ranks in "profession" when the character has the Always Improving
    feat, so this is a no-op otherwise. Ranks land on the True Calling profession first (index 0 --
    the feat says "your chosen profession"), capped at character level per the PF1 max-ranks rule,
    spilling to the next profession. Returns the number of ranks placed.
    """
    prof_data = getattr(character, "profession_data", None) or []
    extra = int((skill_ranks or {}).get("profession", 0) or 0)
    if extra <= 0 or not prof_data:
        return 0

    level = getattr(character, "level", 0) or 0
    placed = 0
    for prof in prof_data:
        if placed >= extra:
            break
        room = max(0, level - int(prof.get("ranks", 0) or 0))
        take = min(extra - placed, room)
        if take <= 0:
            continue
        prof["ranks"] = int(prof.get("ranks", 0) or 0) + take
        prof["associate_skills"] = _pick_associate_skills(prof["ranks"])
        placed += take

    if placed:
        # Ranks may have crossed the rank-5 / rank-15 ability thresholds; the assigner overwrites the
        # ability lists in place, so re-running it is safe and keeps the tiers consistent.
        assign_profession_abilities(character)
        print(f"professions -> Always Improving folded {placed} ordinary rank(s) into "
              f"{[p['skill_label'] + ' r' + str(p['ranks']) for p in prof_data]}")
    if placed < extra:
        print(f"professions: WARNING {extra - placed} ordinary Profession rank(s) had nowhere to go")
    return placed
