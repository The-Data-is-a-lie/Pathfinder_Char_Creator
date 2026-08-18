"""Golden-payload regression for the whole generator (run directly; this repo has no pytest
harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    .venv/Scripts/python.exe Backend/scripts/tests/test_golden_payload.py
    .venv/Scripts/python.exe Backend/scripts/tests/test_golden_payload.py --update
    .venv/Scripts/python.exe Backend/scripts/tests/test_golden_payload.py --config spheres

Generates a fixed set of seeded characters and diffs each payload against a committed snapshot in
Backend/scripts/golden/. A refactor that changes generated output shows up here as a concrete list
of differing keys instead of being discovered weeks later on a Foundry sheet.

WHEN A DIFF IS INTENTIONAL: re-run with --update and commit the regenerated golden IN THE SAME
COMMIT as the code change, so the JSON diff in review shows exactly what the change did to
generated characters.

This only works because generation is reproducible. Three things make it so, and breaking any of
them breaks this test (see changelog):
  * generate_random_char(seed=...) seeds `random` AND numpy (pandas .sample() uses numpy's RNG).
  * feats.py::choosing_feats sorts its candidate pool and accumulates into an insertion-ordered
    dict -- a set of strings iterates in hash order, which Python randomizes per process.
  * Ollama is severed below, so the backstory/archetype paths can't vary with a live model.

The configs deliberately span code paths that would otherwise go uncovered: a martial with no
spellcasting, a prepared caster with domains/school buckets, a multiclass Spheres build, a
Path of War initiator, a stacked bonded creature, and a psionic manifester paired with a
points-only one.
"""
import argparse
import json
import sys
from pathlib import Path

# This file computed BACKEND and GOLDEN_DIR from its own nesting depth, which is exactly the
# arrangement `_harness._find_repo_root` exists to replace: moving this script one level down (into
# `tests/`) silently repointed both at the wrong directory rather than raising. Take them from the
# harness, which finds the root by marker, so this file's depth stops being a fact anything depends
# on. The one remaining depth reference is the line below that locates `_harness` itself.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND, GOLDEN_DIR   # noqa: E402

from utils.class_func import backstory as _bs

# Sever Ollama outright: generate_backstory only calls it when use_backstory_api is on (we pass "N"),
# but build_archetype.py reaches for the same helper to break scoring ties. Without this the payload
# would depend on whether a model happens to be running locally.
_bs._try_ollama = lambda *a, **k: ''

import main_test


# Shared inputs; each config overrides what it needs. Backstory API off -- it is a network call and
# the prose is disabled in the generator anyway.
_BASE = dict(
    create_new_char='Y', userInput_region='Tal-Falko', chosen_caster_level='random',
    deity_flag='asdfasd', truly_random_feats='Y', inherents='Y', modded_char_sheet='n',
    homebrew_feat_amount='Y', num_dice='4', num_sides='6', gold_num=10000,
    use_backstory_api='N', spheres_flag='N',
)

# The four configs below were chosen so that their UNION populates every buff side-map the export
# builds -- feat/item/quality/class-feature/spell/talent changes AND conditionals. Several of those
# are rare enough that a arbitrary seed misses them (only 17 of 1,586 class_feature_effects entries
# carry conditionals), so the seeds here were selected by sweeping for coverage rather than picked at
# random. Check coverage with scripts/report_buff_coverage.py before changing a seed or config.
CONFIGS = {
    # Martial, no spellcasting: feats, gear, and the weapon/armor QUALITY path. Gold is 400,000
    # against a level-16 wealth-by-level of ~315,000 -- above the table, but only modestly. Named
    # qualities (flaming, keen, ...) are what populate enhancement_effects_dict, and
    # enhancement_chooser only spends on them once the budget exceeds +5, so a poorer character gets
    # a flat bonus and no qualities. This was 5,000,000 while enhancements ran AFTER item_chooser had
    # drained the purse; now that they take a reserved share first, the crutch is no longer needed.
    'martial': dict(_BASE, seed=3002, userInput_race='Human', class_choice='fighter',
                    chosen_BAB='high', multi_class='N', alignment_input='LG',
                    userInput_gender='male', high_level=16, low_level=16, gold_num=400000),
    # Multiclass divine caster + Spheres of Power: spellbooks, bonus spells, domains, spell changes
    # and riders, magic talents, mana pool, casting tradition.
    #
    # RESEEDED 2026-08-04 (was 5004). Seven new classes in the pool (spec section 12) realigned the
    # multiclass roll and 5004's witch became a brawler, leaving ONE spellbook -- in the only golden
    # that pins two, and the only one anywhere that covers an ARCANE spellbook at all. 5002 rolls
    # summoner (unchained) 9 / cleric 6, which keeps the pairing that matters: an arcane spontaneous
    # book beside a divine prepared one. Re-swept 5000-5399 on "two real casters"; do not edit this
    # prose to match a future roll, re-sweep.
    'caster': dict(_BASE, seed=5002, userInput_race='Human', class_choice='cleric',
                   chosen_BAB='medium', multi_class='Y', alignment_input='NG',
                   userInput_gender='female', high_level=15, low_level=15,
                   gold_num=40000, spheres_flag='Y'),
    # High-level rogue + Spheres of Might: the only config that reaches class-feature CONDITIONALS
    # (rogue talents are 4 of the 17 curated entries) and Spheres-of-Might combat talents.
    'rogue': dict(_BASE, seed=4003, userInput_race='Halfling', class_choice='rogue',
                  chosen_BAB='medium', multi_class='N', alignment_input='CN',
                  userInput_gender='female', high_level=18, low_level=18,
                  gold_num=3000000, spheres_flag='Y'),
    # Path of War initiator: disciplines, maneuvers, stances, initiator level, stance auras.
    'initiator': dict(_BASE, seed=1004, userInput_race='Half-Orc', class_choice='warlord',
                      chosen_BAB='high', multi_class='N', alignment_input='LN',
                      userInput_gender='male', high_level=10, low_level=10),
    # The 25% "trainer-backed" branch with BOTH mentors -- the only config that reaches it (the four
    # above all roll lean, so mentor funding was previously untested). This seed funds a whole
    # 3-feat Martial Training chain off-budget, so it pins the invariant that matters: mentor-funded
    # PoW feats appear in trainer_feats under "(Trainer N - Path of War)" and NOT in `feats`, while
    # the general track still lands at exactly normal_feat_amount.
    'mentor': dict(_BASE, seed=6009, userInput_race='Human', class_choice='fighter',
                   chosen_BAB='high', multi_class='N', alignment_input='LG',
                   userInput_gender='male', high_level=15, low_level=15,
                   gold_num=200000, spheres_flag='Y'),
    # A BONDED CREATURE, AND A STACKED ONE. The five configs above all carry
    # `animal_companion: null` -- the entire companion stack (map #18: the grantor table, the species
    # ladder, the archetype effects, the chassis) had NO golden coverage at all, which is how the
    # stacking defect below survived review.
    #
    # This seed rolls druid 4 (Elemental Ally) / magus 4 / ranger 4 / samurai 2 (Warrior Poet), and
    # it covers three things no other golden does:
    #   * a STACK. The druid's own `level` and the ranger's `level - 3` merge into one companion at
    #     effective level 5, so the chassis MUST be re-read there (hd 5) rather than left at either
    #     class's own level, which is exactly what `_stack` used to do.
    #   * an ARCHETYPE-REMOVED BOND. Warrior Poet trades the samurai's MOUNT away, so that grantor
    #     emits an ABSENCE entry (effective_level 0, species null) beside the real one -- the one
    #     payload where both shapes appear together, and here they are different creature TYPES.
    #   * two different `effective_level` expressions in the same stack.
    #
    # RESEEDED 2026-08-03 (was 7323, itself a reseed of 7275). Opening the random pool to the six
    # Occult Adventures classes realigned the multiclass roll: 7323's ranger became a ninja, so its
    # three-grantor stack collapsed to two and the golden that exists FOR the stacking defect had
    # quietly stopped covering it. Same failure mode as the 7275 reseed, same rule -- if this
    # comment ever disagrees with the golden, the seed moved: re-scan, do not edit the prose.
    #
    # REBASELINED 2026-08-04, seed UNCHANGED (spec section 8, D16). This golden moved on 49 keys --
    # the master's own gold, gear, appearance, feats and family among them -- and none of that is a
    # behaviour change to the master. The companion's feat roll used to draw from the GLOBAL random
    # stream; it now draws from the creature's own salted generator, so the global stream is no
    # longer consumed there and every later draw shifts. That is the entire point of the move: a
    # wolf's feats must never churn its master's equipment again, and this is the last time they do.
    # THIS golden is the only one the change moved -- the other six roll no bonded creature, so they
    # never paid the old cost. (Unrelated uncommitted occult work had already re-baselined `caster`
    # and `manifester` in the working tree; do not read those diffs as belonging to D16.)
    #
    # RESEEDED 2026-08-04 (was 7971, itself a reseed of 7323 and 7275). Seven new classes in the
    # pool (spec section 12) realigned the roll for the third time: 7971's ranger and hunter both
    # became psionic classes, so the stack this golden EXISTS for collapsed to a single grantor.
    #
    # The re-sweep changed the predicate, and that is the durable part. The old one was "rolls druid
    # + ranger + hunter", which is not what the fixture is for -- it is only how the coverage
    # happened to arrive at three different seeds, and it is why three seeds in a row silently
    # stopped covering it. 7000-9500 was swept on the COVERAGE instead: an entry with 2+
    # `contributors`, an `effective_level: 0` absence entry, and a real one. Sweep that, not a
    # class list.
    'companion': dict(_BASE, seed=7899, userInput_race='Human', class_choice='druid',
                      chosen_BAB='medium', multi_class='Y', alignment_input='NG',
                      userInput_gender='female', high_level=14, low_level=14),
    # A MANIFESTER, AND A POINTS-ONLY ONE. The six configs above all carry `manifesters: []`, so
    # power selection -- the pool filter, the level-weighted pick, the discipline bias, the
    # powers_by_level buckets both renderers group on -- had no pinned output anywhere.
    #
    # This seed rolls psion 5 / aegis 5 / barbarian 4, and psion+aegis is the pair worth pinning:
    # "manifester" is three shapes (utils/class_func/psionics.py) and one character covers two of
    # them. The psion carries powers, a mandated discipline and the 'high' power-point progression;
    # the aegis carries power points and NO powers, the shape a naive renderer drops on the floor.
    # Two entries also means the Foundry module has to fill two manifester books rather than
    # assuming one. If this comment stops matching the golden, the RNG stream moved: re-sweep, do
    # not edit the prose.
    #
    # RESEEDED 2026-08-04 (was 8041, itself a reseed of 8018). Seven new classes in the pool (spec
    # section 12) realigned the multiclass roll and 8041's aegis became a dread -- the same failure
    # as the 8018 reseed, one pool change later. Re-swept 8000-8399: 8045 rolls FOUR manifesters
    # (voyager/highlord/aegis/psion, all thin at levels 5/4/3/2) and 8133 mixes in a warpriest
    # spellbook that duplicates `caster`'s coverage. 8194 is the clean psion+aegis pair -- 4 power
    # levels on the psion, none on the aegis, and a barbarian that contributes nothing psionic.
    'manifester': dict(_BASE, seed=8194, userInput_race='Human', class_choice='psion',
                       chosen_BAB='low', multi_class='Y', alignment_input='NG',
                       userInput_gender='female', high_level=14, low_level=14),
    # OPTIMIZED MODE (spec 15). The seven fixtures above all run with `optimize` absent and are
    # the proof that random mode never moves; this pair pins the optimizer's whole spine -- the
    # forced-role input path, the gear ladder, six-slot stat placement, the policy weapon pick,
    # the feat spine and the role enhancement split. Roles are FORCED, not drawn, so the fixture
    # does not depend on which candidate the seed happens to sample.
    'optimized_striker': dict(_BASE, seed=3002, userInput_race='Human', class_choice='fighter',
                              chosen_BAB='high', multi_class='N', alignment_input='LG',
                              userInput_gender='male', high_level=16, low_level=16,
                              gold_num="", optimize='striker'),
    'optimized_controller': dict(_BASE, seed=5002, userInput_race='Human', class_choice='wizard',
                                 chosen_BAB='low', multi_class='N', alignment_input='NG',
                                 userInput_gender='female', high_level=15, low_level=15,
                                 gold_num="", optimize='controller'),
    # A FAMILIAR, AND AN UNCONDITIONAL ONE (spec section 8's v1 debt, paid 2026-08-13). The eight
    # fixtures above either roll no familiar grantor or gate it behind an odds roll (the wizard's
    # 70/30), so the master-derived stat block -- half HP, master BAB, best-of saves, the master
    # skill-rank overlay, master_abilities -- had no pinned output anywhere. The witch grant has NO
    # odds roll and this config is single-class, so the coverage cannot be realigned away by a
    # pool change the way `companion`'s was four times. Level 12 is deliberate: it crosses the
    # master table's spell-resistance row (11), pinning the one table ability computed in code.
    'witch': dict(_BASE, seed=9101, userInput_race='Human', class_choice='witch',
                  chosen_BAB='low', multi_class='N', alignment_input='NG',
                  userInput_gender='female', high_level=12, low_level=12, gold_num=30000),
    # THE FULL HOUSE-RULES WALL (V4 pass, rulings 2026-08-13). The seed is picked because this
    # single draw exercises every house lever at once: both Strength of a Warrior variants (str 22
    # / con 21 clear the 20+ prereq), the forced shield (the one_handed_shield promise), the
    # Shield sphere with Active Defense (the one curated sphere_defense row), TWF+TWD, and the
    # Cautious Warrior trait. house_rules off remains pinned by optimized_striker /
    # optimized_controller, so this golden moving while those stay byte-identical is exactly the
    # isolation the named key promises.
    #
    # RESEEDED 2026-08-17 (was 5150). The gear-legality plan's step 5 gave shield_chooser a real
    # ~20% roll, which consumes a draw the old dead code never took, and 5150's Active Defense
    # talent fell out of the realigned stream. Swept 5150-5400 on the PREDICATE below -- not on the
    # talent list, which is only how the coverage happened to arrive -- and 5159 is the first seed
    # that satisfies all five levers again. It still draws the same Heavy steel shield.
    'optimized_wall': dict(_BASE, seed=5159, userInput_race='Orc', class_choice='fighter',
                           chosen_BAB='low', multi_class='N', alignment_input='LG',
                           userInput_gender='female', high_level=11, low_level=11,
                           gold_num=100000, optimize='wall', house_rules=True),
}


# --------------------------------------------------------------------------------------------- #
# COVERAGE. Three of these fixtures exist for a SHAPE, not for a seed, and the shape arrives by
# multiclass roll -- so any change to the class pool can silently take it away. It has, repeatedly:
# `companion` has been re-seeded four times (7275 -> 7323 -> 7971 -> 7899) and `manifester` three
# (8018 -> 8041 -> 8194), each time noticed by a human reading a 2,000-line golden diff after the
# fact. The comments above already said what each fixture covers; nothing checked it.
#
# These predicates ARE that check, and they are also the sweep predicate. When a pool change costs
# a fixture its coverage, sweep for one of these coming back true -- not for a class list, which is
# only ever how the coverage happened to arrive.
#
# A predicate returns None when satisfied, or a one-line reason it is not.
# --------------------------------------------------------------------------------------------- #
def _covers_companion(payload):
    """A stacked bond AND an archetype-removed one, so both bonded_creatures shapes are pinned."""
    entries = payload.get('bonded_creatures') or []
    stacked = [e for e in entries if len(e.get('contributors') or []) >= 2]
    absent = [e for e in entries if e.get('effective_level') == 0 and e.get('species') is None]
    real = [e for e in entries if e.get('effective_level') and e.get('species')]
    missing = []
    if not stacked:
        missing.append('no STACK (no entry with 2+ contributors)')
    if not absent:
        missing.append('no ABSENCE entry (effective_level 0, species null)')
    if not real:
        missing.append('no real bonded creature')
    if missing:
        return (f"{'; '.join(missing)} -- grantors "
                f"{[e.get('grantor') for e in entries] or 'none'}")
    return None


def _covers_caster(payload):
    """Two spellbooks, one arcane and one divine -- the only arcane spellbook coverage anywhere."""
    books = [b for b in (payload.get('spellbooks') or []) if b.get('spell_list_choose_from')]
    if len(books) < 2:
        return f'{len(books)} spellbook(s) with spells, needs 2 -- {[b["name"] for b in books]}'
    if not any(b.get('divine') for b in books):
        return f'no DIVINE spellbook -- {[b["name"] for b in books]}'
    if not any(not b.get('divine') for b in books):
        return f'no ARCANE spellbook -- {[b["name"] for b in books]}'
    return None


def _covers_manifester(payload):
    """One manifester with powers and one with power points and NO powers -- the shape a naive
    renderer drops on the floor."""
    entries = payload.get('manifesters') or []
    with_powers = [m for m in entries if m.get('powers_by_level')]
    points_only = [m for m in entries if not m.get('powers_by_level') and m.get('pp_per_day')]
    missing = []
    if not with_powers:
        missing.append('no manifester carrying powers')
    if not points_only:
        missing.append('no POINTS-ONLY manifester (power points, no powers)')
    if missing:
        return f"{'; '.join(missing)} -- manifesters {[m.get('name') for m in entries] or 'none'}"
    return None


def _covers_optimized_striker(payload):
    """The striker spine actually fired: Furious Focus granted, a big-six purchase made.

    Furious Focus, not Power Attack: PA is on feat_tax.json's tax_primary_blocklist -- house-waived
    AMBIENT, held by rule, never in any payload bucket. This predicate hunting for it is how that
    was discovered (and how the metric's never-firing Power Attack model was caught). Furious
    Focus is real spine evidence AND proof the waived-prerequisite machinery grants through it.
    Feats are read across the same buckets the power metric folds -- separate_feats_func deals a
    fighter's combat feats into `class_feats`, not `feats`.
    """
    feats = set()
    for key in ('feats', 'class_feats', 'flavor_feats', 'story_feats', 'trainer_feats'):
        value = payload.get(key)
        entries = value if isinstance(value, (list, tuple)) else (value or {})
        for f in entries:
            feats.add(str(f[0] if isinstance(f, (list, tuple)) and f else f).lower())
    if 'furious focus' not in feats:
        return 'no Furious Focus in any feat bucket -- the striker spine did not fire'
    gear = ' | '.join(str(x) for x in (payload.get('equipment_list') or [])).lower()
    if 'cloak of resistance' not in gear:
        return 'no Cloak of Resistance purchase -- the gear ladder did not run'
    return None


def _covers_optimized_controller(payload):
    """The controller ladder bought the casting-stat headband and the spellbook survived."""
    gear = ' | '.join(str(x) for x in (payload.get('equipment_list') or [])).lower()
    if 'headband of vast intelligence' not in gear:
        return 'no Headband of Vast Intelligence -- the primary_stat_item ladder token did not fire'
    if not any(b.get('spell_list_choose_from') for b in (payload.get('spellbooks') or [])):
        return 'no populated spellbook -- optimization broke the caster chassis'
    return None


def _covers_witch(payload):
    """A granted familiar at a full master-derived stat block, master_abilities included."""
    fams = [e for e in (payload.get('bonded_creatures') or [])
            if e.get('type') == 'familiar' and e.get('species')]
    if not fams:
        return ('no granted familiar -- the witch grant is unconditional, so the resolver or the '
                'late pass broke')
    entry = fams[0]
    stats = entry.get('stats') or {}
    if stats.get('bab') != payload.get('bab_total'):
        return (f"familiar bab {stats.get('bab')} != master bab_total {payload.get('bab_total')} "
                f"-- the master-derived numbers did not apply")
    if not (entry.get('master_abilities') or {}).get('abilities'):
        return 'familiar carries no master_abilities -- level 1 already grants four'
    if stats.get('spell_resistance') is None:
        return 'no spell_resistance at master level 12 -- the table rows past 11 did not apply'
    return None


def _covers_optimized_wall(payload):
    """Every V4 house lever on one sheet -- if any is missing, the config stopped covering it."""
    fc = {str(k).lower() for k in (payload.get('feat_changes_dict') or {})}
    soaw = [k for k in fc if 'strength of a warrior' in k]
    if len(soaw) < 2:
        return (f'only {len(soaw)} Strength of a Warrior change(s) -- the seed was picked to '
                f'clear both variants\' 20+ prereq')
    try:
        shield_ac = int(float(payload.get('shield_ac') or 0))
    except (TypeError, ValueError):
        shield_ac = 0
    if shield_ac <= 0:
        return 'no shield -- the one_handed_shield promise regressed'
    talents = {str((t or {}).get('name') or '').lower()
               for t in payload.get('combat_talent_items') or []}
    if 'active defense' not in talents:
        return 'no Active Defense talent -- the defensive-sphere package or its bias broke'
    feats_all = ' '.join(str(x).lower() for b in payload.values() if isinstance(b, list)
                         for x in b if isinstance(x, str))
    if 'two-weapon defense' not in feats_all:
        return 'Two-Weapon Defense missing from every feat bucket'
    traits = {str(t).strip().lower() for t in payload.get('selected_traits') or []}
    if 'cautious warrior' not in traits:
        return 'Cautious Warrior missing from selected_traits -- the house trait pick broke'
    return None


COVERAGE = {
    'companion': _covers_companion,
    'caster': _covers_caster,
    'manifester': _covers_manifester,
    'optimized_striker': _covers_optimized_striker,
    'optimized_controller': _covers_optimized_controller,
    'witch': _covers_witch,
    'optimized_wall': _covers_optimized_wall,
}


def generate(name):
    """Run the generator for a named config and return its payload."""
    kwargs = dict(CONFIGS[name])
    return main_test.generate_random_char(**kwargs)


def canonical(payload):
    """Stable text form for comparison. sort_keys so payload key ORDER never fails the test (the
    Foundry module and web sheet both read by name); default=str so a stray non-JSON value is
    rendered rather than raising."""
    return json.dumps(payload, indent=1, sort_keys=True, default=str, ensure_ascii=False)


def golden_path(name):
    return GOLDEN_DIR / f'{name}.json'


def diff_keys(old, new):
    """[(key, kind)] for every key that differs, so a failure names what moved."""
    out = []
    for key in sorted(set(old) | set(new)):
        if key not in old:
            out.append((key, 'added'))
        elif key not in new:
            out.append((key, 'removed'))
        elif json.dumps(old[key], sort_keys=True, default=str) != \
                json.dumps(new[key], sort_keys=True, default=str):
            out.append((key, 'changed'))
    return out


def run(names, update):
    failures = []
    GOLDEN_DIR.mkdir(exist_ok=True)

    for name in names:
        payload = generate(name)
        path = golden_path(name)

        # Checked on --update too, and deliberately: the moment a fixture loses its coverage is a
        # re-seed, and a re-seed is exactly when --update gets run. Reporting it only on a plain
        # run would mean writing the coverage away and finding out on the next pass.
        if name in COVERAGE:
            lost = COVERAGE[name](payload)
            if lost:
                failures.append(f'{name}: COVERAGE LOST -- {lost}')
                print(f'    {name}: coverage -- {lost}')
            else:
                print(f'  {name}: coverage OK')

        if update:
            path.write_text(canonical(payload), encoding='utf-8')
            print(f'  {name}: wrote {path.relative_to(BACKEND.parent)} ({len(payload)} keys)')
            continue

        if not path.exists():
            failures.append(f'{name}: no golden at {path} -- run with --update to create it')
            continue

        old = json.loads(path.read_text(encoding='utf-8'))
        changed = diff_keys(old, payload)
        if changed:
            failures.append(f'{name}: {len(changed)} key(s) differ from the golden')
            for key, kind in changed:
                print(f'    {name}: {key} ({kind})')
        else:
            print(f'  {name}: OK ({len(payload)} keys)')

    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update', action='store_true',
                        help='overwrite the goldens with current output (commit the result)')
    parser.add_argument('--config', action='append', choices=sorted(CONFIGS),
                        help='only run this config (repeatable); default is all')
    args = parser.parse_args()

    names = args.config or sorted(CONFIGS)
    failures = run(names, args.update)

    if args.update:
        print(f'\nUPDATED -- {len(names)} golden(s). Commit them with the change that caused the diff.')
        if failures:
            # The goldens were written; the point is that this one is no longer worth pinning.
            print('\nBut a fixture no longer covers what it exists for:')
            for line in failures:
                print(f'  {line}')
            print('\nRe-sweep for a seed that satisfies the predicate in COVERAGE -- not for the '
                  'class list that happened to produce it last time.')
            return 1
        return 0

    if failures:
        print('\nFAIL')
        for line in failures:
            print(f'  {line}')
        print('\nIf the change is intentional, re-run with --update and commit the new golden.')
        return 1

    print(f'\nPASS -- {len(names)} golden payload(s) match')
    return 0


if __name__ == '__main__':
    sys.exit(main())
