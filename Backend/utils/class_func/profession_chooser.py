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
from utils.class_func.profession_abilities import assign_profession_abilities

# Homebrew profession feats. Order matters: prerequisites flow down the list (True Calling gates
# Always Improving), so we take them top-to-bottom.
PROFESSION_FEATS = [
    ("True Calling",
     "Your natural Profession rank cap rises to 15 in one qualifying profession."),
    ("Multi Talented",
     "Your profession rank cap increases by 10."),
    ("Always Improving",
     "You can spend ordinary skill ranks in your chosen profession. (Requires True Calling and 15 ranks.)"),
]

# Generic associate skills a profession can unlock at ranks 1/4/7/10 (themed loosely; the GM refines).
_ASSOCIATE_SKILLS = [
    "Appraise", "Craft", "Diplomacy", "Knowledge (local)", "Perception",
    "Profession", "Sense Motive", "Sleight of Hand", "Use Magic Device", "Handle Animal",
]

_BASE_CAP = 10          # every profession caps here ...
_TRUE_CALLING_CAP = 15  # ... except the one True Calling profession
_MAX_PROFESSIONS = 6    # safety bound when a big pool needs many vocations to absorb it


def _roll_profession_feat_count(truly_random_feats):
    """How many profession feats to take. Curated builds take at least 2 (per the campaign rule);
    randomized builds usually take 0-1, occasionally 2."""
    base = random.choice([0, 0, 1, 1, 2])
    if str(truly_random_feats).upper() == "N":
        return max(2, base)
    return base


def _pick_profession_feats(n):
    """Take ``n`` profession feats top-to-bottom so prerequisites resolve (cap at the 3 that exist)."""
    n = max(0, min(n, len(PROFESSION_FEATS)))
    return PROFESSION_FEATS[:n]


def _cap_for(idx, has_true_calling):
    """Per-profession rank cap: 10 for all, 15 for the primary (idx 0) only with True Calling."""
    return _TRUE_CALLING_CAP if (has_true_calling and idx == 0) else _BASE_CAP


def _professions_needed(pool, has_true_calling):
    """How many professions are needed to absorb the pool, primary first (bounded)."""
    needed, remaining = 0, pool
    while remaining > 0 and needed < _MAX_PROFESSIONS:
        remaining -= min(remaining, _cap_for(needed, has_true_calling))
        needed += 1
    return max(1, needed)


def _themed_profession_names(character, count):
    """Pick ``count`` distinct profession names, lightly biased toward the character's craft/class so
    a smith tends to get a smithing-flavoured vocation as the primary."""
    pool = list(getattr(data, "professions", []) or [])
    if not pool:
        return ["laborer"] * count
    theme_words = set()
    for src in (getattr(character, "craft_chosen", None), getattr(character, "c_class", None)):
        if src:
            theme_words.update(str(src).lower().split())
    themed = [p for p in pool if theme_words & set(str(p).lower().split())]
    chosen = []
    if themed and random.random() < 0.6:
        chosen.append(random.choice(themed))
    while len(chosen) < count:
        pick = random.choice(pool)
        if pick not in chosen:
            chosen.append(pick)
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
    # 1. Profession feats -> they feed the +10/feat term of the pool and grant the 15-cap (True Calling).
    feats = _pick_profession_feats(_roll_profession_feat_count(truly_random_feats))
    feat_names = [name for name, _desc in feats]
    has_true_calling = "True Calling" in feat_names

    # 2. Rank pool, then enough professions to absorb it (primary first).
    level = getattr(character, "level", 0) or 0
    pool = 5 + level + 10 * len(feats)
    names = _themed_profession_names(character, _professions_needed(pool, has_true_calling))

    # 3. Distribute the pool, each profession capped (one 15 with True Calling, rest 10).
    profession_data = []
    remaining = pool
    for idx, name in enumerate(names):
        cap = _cap_for(idx, has_true_calling)
        ranks = max(0, min(remaining, cap))
        remaining -= ranks
        if ranks <= 0:
            break
        profession_data.append({
            "name": name,
            "skill_label": f"Profession ({name})",
            "ranks": ranks,
            "cap": cap,
            "associate_skills": _pick_associate_skills(ranks),
        })

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
