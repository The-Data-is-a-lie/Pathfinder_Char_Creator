"""Standalone regression checks for skill-rank and profession-rank allocation (run directly; this
repo has no pytest harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    C:\\Python310\\python.exe Backend/scripts/tests/test_skill_ranks.py

Guards the invariants behind "characters must fill their skill slots exactly":
  * every rank in the budget is spent -- sum(skill_ranks) == character.skill_rank_budget
  * every rank lands on a skill the Foundry module and web sheet can actually render
  * no skill exceeds the per-skill cap (character level; 3x level under the house rules)
  * the min-1-rank-per-CLASS-level floor, so a negative mental mod can never blank a skill block
  * a narrow skill sample is widened until it can physically hold the budget
  * profession ranks sum to exactly the pool, within per-profession caps
  * ordinary ranks reach a Profession only via the Always Improving feat
  * homebrew mode (oks/pathfinder/house-rules/skills-and-hp.md): the 3-ranks-per-level cap and
    +2/level background-only ranks (homebrew flag), and the 2->4 rank floor (the separate
    misc_homebrew_rules catch-all flag -- the split itself is pinned)
"""
import random
import sys
from math import floor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report  # noqa: E402

from utils import data  # noqa: E402
from utils.class_func import profession_chooser as pc  # noqa: E402
from utils.class_func import skill_ranks as sr  # noqa: E402

REPORT = Report('test_skill_ranks')


def check(condition, message):
    return REPORT.check(condition, message)


class FakeCharacter:
    """The slice of createACharacter.Character that skill/profession allocation actually reads."""

    def __init__(self, classes, stats=None, inherents=None, level_ups=None,
                 profession_feats=None, primary_class_index=0, homebrew='N',
                 misc_homebrew_rules='N'):
        self.homebrew_feat_amount = homebrew
        self.misc_homebrew_rules = misc_homebrew_rules
        self.classes = [{'name': n, 'level': l} for n, l in classes]
        self.level = sum(entry['level'] for entry in self.classes)
        self.primary_class_index = primary_class_index
        self.c_class = self.classes[primary_class_index]['name']
        self.c_class_level = self.classes[primary_class_index]['level']
        stats = stats or {}
        self.str = stats.get('str', 10)
        self.dex = stats.get('dex', 10)
        self.con = stats.get('con', 10)
        self.int = stats.get('int', 10)
        self.wis = stats.get('wis', 10)
        self.cha = stats.get('cha', 10)
        self.inherents = inherents or {}
        self.level_up_stats = level_ups or {}
        self.profession_feats = profession_feats or []
        self.Total_HP = 0
        # points-per-level rates keyed the way class_data.json keys them
        self.class_data = {n: {"skill points at each level": str(p)} for n, p in CLASS_POINTS.items()}


CLASS_POINTS = {
    'fighter': 2, 'wizard': 2, 'sorcerer': 2, 'cleric': 2, 'paladin': 2, 'summoner': 2,
    'monk': 4, 'barbarian': 4, 'druid': 4, 'alchemist': 4, 'inquisitor': 6,
    'bard': 6, 'ranger': 6, 'rogue': 8,
}
CLASS_NAMES = list(CLASS_POINTS)


def random_character(rng):
    """A random 1-3 class build spanning the interesting mental-mod range (dump stat -> genius)."""
    n_classes = rng.choice([1, 1, 1, 2, 3])
    total = rng.randint(1, 20)
    levels = []
    for i in range(n_classes):
        remaining_slots = n_classes - i - 1
        take = 1 if remaining_slots else total
        if remaining_slots:
            take = rng.randint(1, max(1, total - remaining_slots))
        levels.append(take)
        total -= take
    classes = [(rng.choice(CLASS_NAMES), lvl) for lvl in levels if lvl > 0]
    stats = {s: rng.randint(3, 24) for s in ('str', 'dex', 'con', 'int', 'wis', 'cha')}
    inherents = {s: rng.randint(0, 5) for s in ('int', 'wis', 'cha')} if rng.random() < 0.5 else {}
    return FakeCharacter(classes, stats=stats, inherents=inherents)


def expected_budget(character, favored):
    """The budget, computed independently of skill_ranks.py so the test is a real second opinion."""
    mental = max(floor((getattr(character, s) + character.inherents.get(s, 0)
                        + character.level_up_stats.get(s, 0) - 10) / 2)
                 for s in ('int', 'wis', 'cha'))
    total = 0
    for entry in character.classes:
        points = int(character.class_data[entry['name']]["skill points at each level"])
        total += max(1, points + mental) * entry['level']
    return total + favored


# --------------------------------------------------------------------------------------------
# 1. The canonical list and its id map agree, and match what the consumers render.
# --------------------------------------------------------------------------------------------
def test_canonical_list():
    check(len(data.skills) == len(set(data.skills)),
          f"data.skills contains duplicates: {[s for s in data.skills if data.skills.count(s) > 1]}")
    check(len(data.skills) == 35, f"expected 35 canonical PF1 skills, got {len(data.skills)}")
    missing = [s for s in data.skills if s not in data.SKILL_IDS]
    check(not missing, f"skills with no SKILL_IDS entry: {missing}")
    extra = [s for s in data.SKILL_IDS if s not in data.skills]
    check(not extra, f"SKILL_IDS entries not in the skill pool: {extra}")
    # the skills that used to eat ranks and never reach a sheet
    for gone in ('gather information', 'knowledge martial', 'lore', 'artistry'):
        check(gone not in data.skills, f"unrenderable skill still in the pool: {gone}")


# --------------------------------------------------------------------------------------------
# 2. The budget is spent exactly, on renderable skills, within the per-skill cap.
# --------------------------------------------------------------------------------------------
def test_exact_spend(iterations=300):
    rng = random.Random(20260722)
    valid = set(data.skills)
    for _ in range(iterations):
        character = random_character(rng)
        favored = rng.choice([0, character.level])
        want = expected_budget(character, favored)
        ranks = sr.skills_selector(character, 'skills', favored)

        check(character.skill_rank_budget == want,
              f"budget {character.skill_rank_budget} != independently computed {want} "
              f"for {character.classes}")
        check(sum(ranks.values()) == want,
              f"assigned {sum(ranks.values())} of {want} ranks for {character.classes}")
        bad = [s for s in ranks if s not in valid]
        check(not bad, f"ranks assigned to unrenderable skills: {bad}")
        over = {s: r for s, r in ranks.items() if r > character.level}
        check(not over, f"skills above the character-level cap ({character.level}): {over}")
        check(all(r >= 0 for r in ranks.values()), "negative skill ranks assigned")


# --------------------------------------------------------------------------------------------
# 3. The min-1-per-class-level floor: a dump-stat build still gets a usable skill block.
# --------------------------------------------------------------------------------------------
def test_min_rank_floor():
    # every mental stat at 4 -> mod -3; a 2/level class used to budget 20 - 60 = -40 ranks
    character = FakeCharacter([('fighter', 20)], stats={'int': 4, 'wis': 4, 'cha': 4})
    ranks = sr.skills_selector(character, 'skills', 0)
    check(character.skill_rank_budget == 20,
          f"floored budget should be 1/level = 20, got {character.skill_rank_budget}")
    check(sum(ranks.values()) == 20, f"floor budget not spent: {sum(ranks.values())} of 20")

    # per CLASS level, not on the total: rogue 10 (8/lvl) + fighter 10 (2/lvl) at mod -3
    multi = FakeCharacter([('rogue', 10), ('fighter', 10)], stats={'int': 4, 'wis': 4, 'cha': 4})
    ranks = sr.skills_selector(multi, 'skills', 0)
    want = (8 - 3) * 10 + max(1, 2 - 3) * 10   # 50 + 10
    check(multi.skill_rank_budget == want,
          f"per-class floor expected {want}, got {multi.skill_rank_budget}")
    check(sum(ranks.values()) == want, f"multiclass floor budget not spent: {sum(ranks.values())}")


# --------------------------------------------------------------------------------------------
# 4. Capacity: a big budget on a narrow sample must widen the sample, not drop ranks.
# --------------------------------------------------------------------------------------------
def test_capacity_topup():
    # mod 0 -> skill_number rolls as low as 2, against a (2/lvl * 20) + 20 favored-class budget of 60,
    # i.e. up to 30 skills' worth of capacity demanded from a sample that can be as narrow as 2
    want = 2 * 20 + 20
    for seed in range(60):
        random.seed(seed)
        character = FakeCharacter([('fighter', 20)], stats={'int': 10, 'wis': 10, 'cha': 10})
        ranks = sr.skills_selector(character, 'skills', character.level)
        check(sum(ranks.values()) == want,
              f"seed {seed}: assigned {sum(ranks.values())} of {want} (capacity top-up failed)")
        check(len([s for s, r in ranks.items() if r]) >= 3,
              f"seed {seed}: {want} ranks packed into too few skills")
    random.seed()


# --------------------------------------------------------------------------------------------
# 5. Professions: the pool is distributed exactly, within caps, over a sane number of vocations.
# --------------------------------------------------------------------------------------------
def test_profession_pool(iterations=200):
    rng = random.Random(99)
    for _ in range(iterations):
        level = rng.randint(1, 30)
        character = FakeCharacter([('fighter', level)])
        pc.profession_chooser(character, "professions", rng.choice(["Y", "N"]))
        pool = character.profession_pool
        prof = character.profession_data
        check(sum(p['ranks'] for p in prof) == pool,
              f"level {level}: professions hold {sum(p['ranks'] for p in prof)} of pool {pool}")
        check(all(p['ranks'] >= 1 for p in prof), f"level {level}: profession with 0 ranks")
        over = [p for p in prof if p['ranks'] > p['cap']]
        check(not over, f"level {level}: profession over its cap: {[(p['name'], p['ranks'], p['cap']) for p in over]}")

        # every Multi Talented pick must be its OWN feat entry (each one costs a feat slot; see
        # _prof_feat_n in main_test.py) and every entry must be uniquely named
        mt = [f for f in character.profession_feats if f.startswith("Multi Talented")]
        mt_count = len(mt)
        check(len(set(character.profession_feats)) == len(character.profession_feats),
              f"duplicate profession feat names: {character.profession_feats}")
        check(len(character.profession_feat_desc) == len(character.profession_feats),
              f"a profession feat lost its description to a name collision: {character.profession_feats}")
        check(mt_count <= pc._max_multi_talented(level),
              f"level {level}: {mt_count} Multi Talented picks exceeds cap {pc._max_multi_talented(level)}")
        check(pool == 5 + level + 10 * mt_count,
              f"level {level}: pool {pool} != 5 + {level} + 10*{mt_count}")
        # order: Multi Talented is always taken first, so any feat implies Multi Talented
        if character.profession_feats:
            check(character.profession_feats[0].startswith("Multi Talented"),
                  f"first profession feat should be Multi Talented, got {character.profession_feats[0]}")


# --------------------------------------------------------------------------------------------
# 6. The Always Improving gate, and the fold-back of ordinary Profession ranks.
# --------------------------------------------------------------------------------------------
def test_always_improving_gate():
    without = FakeCharacter([('rogue', 20)], stats={'int': 20, 'wis': 10, 'cha': 10})
    without.profession_feats = ["Multi Talented", "True Calling"]
    ranks = sr.skills_selector(without, 'skills', 0)
    check(ranks.get('profession', 0) == 0,
          f"Profession got {ranks.get('profession')} ordinary ranks without Always Improving")

    withfeat = FakeCharacter([('rogue', 20)], stats={'int': 20, 'wis': 10, 'cha': 10})
    withfeat.profession_feats = ["Multi Talented", "True Calling", "Always Improving"]
    check(sr.has_always_improving(withfeat), "has_always_improving failed to detect the feat")
    # the gate lets Profession into the pool; whether it wins the random draw is chance, so just
    # confirm the spend stays exact with Profession selectable
    ranks = sr.skills_selector(withfeat, 'skills', 0)
    check(sum(ranks.values()) == withfeat.skill_rank_budget,
          "exact spend broken when Profession is selectable")

    # fold-back: ordinary ranks land on the True Calling profession, capped at character level
    folded = FakeCharacter([('rogue', 20)])
    folded.profession_data = [
        {"name": "Smith", "skill_label": "Profession (Smith)", "ranks": 15, "cap": 15, "associate_skills": []},
        {"name": "Cook", "skill_label": "Profession (Cook)", "ranks": 8, "cap": 10, "associate_skills": []},
    ]
    placed = pc.apply_always_improving_ranks(folded, {'profession': 9})
    check(placed == 9, f"expected 9 ranks folded, got {placed}")
    check(folded.profession_data[0]['ranks'] == 20,
          f"True Calling profession should cap at character level 20, got {folded.profession_data[0]['ranks']}")
    check(folded.profession_data[1]['ranks'] == 12,
          f"spillover expected 8+4=12, got {folded.profession_data[1]['ranks']}")

    check(pc.apply_always_improving_ranks(FakeCharacter([('rogue', 5)]), {'profession': 4}) == 0,
          "fold-back should be a no-op with no professions")


# --------------------------------------------------------------------------------------------
# 7. House rules (homebrew flag on): 2->4 rank floor, 3x-level cap, +2/level background ranks.
# --------------------------------------------------------------------------------------------
def test_house_rank_floor():
    # fighter is a 2/level class; under the misc-homebrew floor it budgets like a 4/level class,
    # plus the +2/level background grant (main homebrew flag) recorded into skill_rank_budget
    character = FakeCharacter([('fighter', 10)], stats={'int': 10, 'wis': 10, 'cha': 10},
                              homebrew='Y', misc_homebrew_rules='Y')
    ranks = sr.skills_selector(character, 'skills', 0)
    want = 4 * 10 + 2 * 10
    check(character.skill_rank_budget == want,
          f"house budget should be (2->4)*10 + background 2*10 = {want}, got {character.skill_rank_budget}")
    check(sum(ranks.values()) == want,
          f"house budget not spent exactly: {sum(ranks.values())} of {want}")

    # a 4/level class is NOT floored upward -- only the 2s become 4s
    monk = FakeCharacter([('monk', 10)], stats={'int': 10, 'wis': 10, 'cha': 10},
                         homebrew='Y', misc_homebrew_rules='Y')
    sr.skills_selector(monk, 'skills', 0)
    check(monk.skill_rank_budget == want,
          f"monk (4/level) should budget {want} like the floored fighter, got {monk.skill_rank_budget}")

    # the flag split: main homebrew WITHOUT misc keeps the raw 2/level rate (background still on)
    split = FakeCharacter([('fighter', 10)], stats={'int': 10, 'wis': 10, 'cha': 10},
                          homebrew='Y')
    sr.skills_selector(split, 'skills', 0)
    check(split.skill_rank_budget == 2 * 10 + 2 * 10,
          f"homebrew-only fighter should budget unfloored 2*10 + background 2*10 = 40, "
          f"got {split.skill_rank_budget}")


def test_house_cap_and_exact_spend(iterations=150):
    rng = random.Random(20260730)
    valid = set(data.skills)
    for _ in range(iterations):
        character = random_character(rng)
        character.homebrew_feat_amount = 'Y'
        character.misc_homebrew_rules = 'Y'
        favored = rng.choice([0, character.level])
        ranks = sr.skills_selector(character, 'skills', favored)
        check(sum(ranks.values()) == character.skill_rank_budget,
              f"house spend {sum(ranks.values())} != budget {character.skill_rank_budget} "
              f"for {character.classes}")
        cap = 3 * character.level
        over = {s: r for s, r in ranks.items() if r > cap}
        check(not over, f"skills above the house 3x-level cap ({cap}): {over}")
        bad = [s for s in ranks if s not in valid]
        check(not bad, f"house ranks on unrenderable skills: {bad}")


def test_background_ranks_pool():
    # the background walk alone: exactly 2/level ranks, only on background skills
    character = FakeCharacter([('fighter', 15)], homebrew='Y')
    placed = {}
    spent = sr.assign_background_ranks(character, placed, sr.per_skill_cap(character))
    check(spent == 30, f"background grant should be 2*15 = 30, got {spent}")
    outside = [s for s in placed if s not in sr.BACKGROUND_SKILLS]
    check(not outside, f"background ranks landed outside the background pool: {outside}")
    check(all(r <= 3 * 15 for r in placed.values()), "background rank over the house cap")

    # background skills must all be renderable and profession-free
    check('profession' not in sr.BACKGROUND_SKILLS, "profession must stay in its own subsystem")
    unrenderable = [s for s in sr.BACKGROUND_SKILLS if s not in data.skills]
    check(not unrenderable, f"BACKGROUND_SKILLS not in the canonical pool: {unrenderable}")

    # homebrew off -> no background grant
    plain = FakeCharacter([('fighter', 15)])
    check(sr.assign_background_ranks(plain, {}, plain.level) == 0,
          "background ranks granted with homebrew off")


# --------------------------------------------------------------------------------------------
# 8. Favored class scales off TOTAL level, and empty racial slots are gone.
# --------------------------------------------------------------------------------------------
def test_favored_class():
    from utils.class_func.favored_class import favored_class_calculator
    character = FakeCharacter([('monk', 8), ('summoner', 7), ('wizard', 5)])
    ranks, chosen = favored_class_calculator(character, ['health', 'skill ranks'])
    check(ranks == 20, f"favored-class skill ranks should be total level 20, got {ranks}")
    check(character.Total_HP == 20, f"favored-class HP should be total level 20, got {character.Total_HP}")
    check(chosen == ['health', 'skill ranks'], f"favored class list mangled: {chosen}")


def main():
    for test in (test_canonical_list, test_exact_spend, test_min_rank_floor, test_capacity_topup,
                 test_profession_pool, test_always_improving_gate, test_house_rank_floor,
                 test_house_cap_and_exact_spend, test_background_ranks_pool, test_favored_class):
        test()

    return REPORT.finish(f'{REPORT.checks} checks')


if __name__ == "__main__":
    sys.exit(main())
