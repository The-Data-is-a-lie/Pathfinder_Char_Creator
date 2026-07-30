from utils import data
import random, re
from math import floor
# Start of major task: skills assignment

# House skill rules (oks/pathfinder/house-rules/skills-and-hp.md), all gated on the homebrew flag:
#   * rank floor -- any 2-ranks/level class grants 4 instead
#   * per-skill cap -- up to 3 ranks per character level in one skill (vs the usual 1/level)
#   * background ranks -- +2/level spendable only on the background skills below
# BACKGROUND_SKILLS is PF Unchained's background list intersected with data.skills (artistry/lore
# are unrenderable, see data.py) minus "profession", whose ranks live in the profession subsystem.
BACKGROUND_SKILLS = [
    "appraise", "craft", "handle animal", "knowledge engineering", "knowledge geography",
    "knowledge history", "knowledge nobility", "linguistics", "perform", "sleight of hand",
]


def homebrew_enabled(character):
    """The house-rule gate; same flag convention as level_and_bab.update_level."""
    return str(getattr(character, 'homebrew_feat_amount', 'N')) not in ('N', 'n')


def class_skill_points(character, name):
    """Points-per-level for a class, with the house rank floor (2 -> 4) when homebrew is on.
    Unknown classes fall back to the 2/level minimum (floored to 4 like any other 2)."""
    if name in character.class_data:
        points = int(character.class_data[name]["skill points at each level"])
    else:
        points = 2
        print("couldn't find this class's skills, using default scaling", points)
    if homebrew_enabled(character) and points == 2:
        points = 4
    return points


def per_skill_cap(character):
    """Max ranks in one skill: 3/character level under the house rules, else the PF1 level cap."""
    return 3 * character.level if homebrew_enabled(character) else character.level


def final_ability_score(character, stat):
    """FINAL ability score for ``stat``: base roll + inherent bonuses + level-up
    bumps. ``inherents`` / ``level_up_stats`` are ``{stat: bonus}`` dicts and may
    be absent (e.g. inherents disabled), so we read them defensively."""
    inherents = getattr(character, 'inherents', {}) or {}
    level_ups = getattr(character, 'level_up_stats', {}) or {}
    inh = inherents.get(stat, 0) if isinstance(inherents, dict) else 0
    lvl = level_ups.get(stat, 0) if isinstance(level_ups, dict) else 0
    return getattr(character, stat) + inh + lvl


def final_ability_mod(character, stat):
    """Ability modifier derived from the FINAL score (see final_ability_score)."""
    return floor((final_ability_score(character, stat) - 10) / 2)


def highest_mental_mod(character):
    """Highest mental ability modifier using each stat's FINAL score
    (base roll + inherent bonuses + level-up bumps), not just the base roll.

    Bonus skill ranks scale off the best mental ability, so an Int/Wis/Cha that
    was boosted by inherents or level-up bumps now grants the extra ranks it
    should.
    """
    return max(final_ability_mod(character, s) for s in ('int', 'wis', 'cha'))

def has_always_improving(character):
    """True when the character took the homebrew 'Always Improving' profession feat, which is the ONLY
    way ordinary skill ranks may be spent in a Profession (profession_chooser.PROFESSION_FEATS).
    Requires profession_chooser to have run first -- see the ordering note in main_test.py."""
    feats = getattr(character, 'profession_feats', None) or []
    return any(str(f).startswith("Always Improving") for f in feats)


def skill_rank_budget(character, skill_ranks_level):
    """TOTAL skill ranks the character is owed.

    PF1 multiclass: every class grants its own points-per-level rate for its own levels, and the
    mental mod applies per character level. The ``max(1, ...)`` is PF1's "at least 1 rank per level
    regardless of an Int penalty" floor, applied PER CLASS LEVEL -- without it a 2/level class with a
    negative mental mod budgeted ZERO ranks (and went negative at -3, leaving every skill blank).
    ``skill_ranks_level`` is the favored-class contribution.
    """
    mental_mod = highest_mental_mod(character)
    budget = 0
    for entry in character.classes:
        points = class_skill_points(character, entry['name'])
        budget += max(1, points + mental_mod) * entry['level']
    return budget + skill_ranks_level


def skills_selector(character, skills, skill_rank_level):
    """
    randomly grabs a subset of skills then assigns skill ranks to them (up to character level for each)
    to prevent any high stats characters from breaking the function, we max them out at character level for all in game skills

    Every rank in the budget IS spent: the selectable set is topped up until it can physically hold the
    budget, and the walk only draws from skills with room left. Any shortfall is reported, never silent.

    param (skills list from the data section)
    return
    - skill ranks (Dictionary)
    """

    all_skills = getattr(data, skills)
    # max ranks in one skill: house 3/level cap under homebrew, else the PF1 character-level cap
    max_skill_ranks = per_skill_cap(character)
    skill_ranks = {}

    selectable_skills, budget, not_selectable_skills = get_selectable_skills(character, all_skills, skill_rank_level)
    assign_skill_ranks(character, selectable_skills, not_selectable_skills, budget, max_skill_ranks, skill_ranks)
    # Zero-fill BEFORE the background pass: assign_dummy_zeroes overwrites its skills with 0, and
    # background ranks may land on skills outside the main sample.
    assign_dummy_zeroes(not_selectable_skills, skill_ranks)
    background_spent = assign_background_ranks(character, skill_ranks, max_skill_ranks)

    # Record the budget so downstream code (and test_skill_ranks.py) can check the invariant without
    # recomputing it, then verify the spend was exact.
    character.skill_rank_budget = budget + background_spent
    total = sum(skill_ranks.values())
    if total != character.skill_rank_budget:
        print(f"skill_ranks: WARNING assigned {total} of {character.skill_rank_budget} ranks "
              f"({character.skill_rank_budget - total} unplaced)")

    return skill_ranks


def assign_background_ranks(character, skill_ranks, max_skill_ranks):
    """House rule: +2 background-only skill ranks per level. Runs AFTER the ordinary walk so each
    skill's remaining room already accounts for adventurer ranks (which may themselves have landed
    on background skills -- the rule allows that). Returns the ranks actually spent; a shortfall is
    only possible when every background skill is capped, and is reported, never silent."""
    if not homebrew_enabled(character):
        return 0
    budget = 2 * character.level
    before = sum(skill_ranks.values())
    assign_skill_ranks(character, list(BACKGROUND_SKILLS), [], budget, max_skill_ranks, skill_ranks)
    spent = sum(skill_ranks.values()) - before
    if spent < budget:
        print(f"skill_ranks: background skills all capped -- placed {spent} of {budget} background ranks")
    return spent


def get_selectable_skills(character,all_skills, skill_ranks_level):
    # Use the FINAL highest mental mod (base + inherents + level-ups), not the base roll.
    mental_mod = highest_mental_mod(character)
    budget = skill_rank_budget(character, skill_ranks_level)
    print("Skill rank budget:", budget)

    # Professions run on their own homebrew rank pool (profession_chooser), so ordinary ranks may only
    # be spent there with the 'Always Improving' feat.
    pool = [s for s in all_skills if s != 'profession' or has_always_improving(character)]

    # breadth of distinct skills keys off the primary class's per-level rate (house floor included)
    primary = character.classes[character.primary_class_index]
    primary_points = class_skill_points(character, primary['name'])
    scaling = primary_points + mental_mod

    skill_number = scaling + random.randint(abs(mental_mod), abs(mental_mod)+8)
    skill_number = max(1, min(skill_number, len(pool)))
    selectable_skills = random.sample(pool, k=skill_number)

    # Capacity guarantee: a narrow sample can't hold a big budget (each skill caps at per_skill_cap),
    # and the leftover used to be dropped on the floor. Widen the sample ONLY when it's actually short,
    # so focused characters stay focused.
    max_skill_ranks = per_skill_cap(character)
    capacity = len(selectable_skills) * max_skill_ranks
    if capacity < budget:
        spare = [s for s in pool if s not in selectable_skills]
        random.shuffle(spare)
        while spare and capacity < budget:
            selectable_skills.append(spare.pop())
            capacity += max_skill_ranks
        if capacity < budget:
            # Every skill in the game maxed and still short -- clamp loudly rather than silently.
            print(f"skill_ranks: budget {budget} exceeds max capacity {capacity} "
                  f"({len(selectable_skills)} skills x {max_skill_ranks} ranks); clamping to capacity")
            budget = capacity

    not_selectable_skills = []
    for skill in all_skills:
        if skill not in selectable_skills:
            not_selectable_skills.append(skill)

    return selectable_skills, budget, not_selectable_skills


def assign_skill_ranks(character, selectable_skills, not_selectable_skills, budget, max_skill_ranks, skill_ranks):
    """Spend the budget down to exactly zero, 1-3 ranks at a time (the chunking is what gives NPCs their
    uneven, lived-in skill profile). Skills are retired from the draw once full, so the walk can't spin
    on a maxed skill and can't exit with ranks still in hand."""
    remaining = budget
    open_skills = list(dict.fromkeys(selectable_skills))   # dedupe, preserve order

    while remaining > 0 and open_skills:
        skill = random.choice(open_skills)
        room = max_skill_ranks - skill_ranks.get(skill, 0)
        ranks_to_assign = min(random.randint(1, 3), remaining, room)
        if ranks_to_assign <= 0:
            open_skills.remove(skill)
            continue
        skill_ranks[skill] = skill_ranks.get(skill, 0) + ranks_to_assign
        remaining -= ranks_to_assign
        if skill_ranks[skill] >= max_skill_ranks:
            open_skills.remove(skill)

def assign_dummy_zeroes(not_selectable_skills, skill_ranks):
    for unassigned_skill in not_selectable_skills:
        skill_ranks[unassigned_skill] = 0       
        # print("breaking at unassigned") 

    return skill_ranks

