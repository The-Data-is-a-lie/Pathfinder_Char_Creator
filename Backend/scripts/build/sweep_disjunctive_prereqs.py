"""Reach report for the disjunctive-prerequisite fix -- run directly, like the rest of the
Backend/scripts family (this repo has no pytest harness).

    C:\\Python310\\python.exe Backend/scripts/build/sweep_disjunctive_prereqs.py
    C:\\Python310\\python.exe Backend/scripts/build/sweep_disjunctive_prereqs.py --static-only
    C:\\Python310\\python.exe Backend/scripts/build/sweep_disjunctive_prereqs.py --classes monk --levels 20

Exits 0 always: it is a measurement, not a gate. The gate that holds the wiring in place is
`gates/validate_bond_prereqs.py`.

`generic_func.prereq_part_satisfied` splits a prerequisite fragment on " or " and passes on any
branch. Before it ran outside optimized mode, "A or B" survived comma-splitting as one opaque token
that nothing ever puts into character.chooseable, so one disjunctive fragment made a feat
permanently unselectable for every randomly generated character. This script measures what that
changed, in four passes:

  static      -- over data/feats.csv, applying the same FILTER_WORDS the runtime does: how many
                 feats carry a disjunctive part at all, and what those branches are asking for.

  eligibility -- the real measure of "how many became selectable". Generates characters and captures
                 the actual character.chooseable each one built up, then re-runs both the old and
                 the new satisfaction test against that captured set. Independent of what the
                 random draws happened to pick.

  picks       -- generates the same characters twice, once with the parser monkeypatched back to the
                 old behaviour and once as shipped, and diffs the feats that appear. Same seeds both
                 passes. A wider pool reshuffles draws, so feats drop out as well as appear; that
                 churn is expected and is not a regression.

  bond        -- the acceptance evidence for Boon Companion: its take-rate split by which bonded
                 creature the character actually holds. It must be non-zero for characters with a
                 companion, mount or familiar, and zero for characters with none.

Widening is not free: a branch like "size large or larger" becomes satisfiable the moment "size
large" enters chooseable. Read the eligibility list rather than assuming it is all upside.
"""
import argparse
import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND, SCRIPTS          # noqa: E402  -- one owner for the path constants

sys.path.insert(0, str(BACKEND))               # so `from utils...` resolves
sys.path.insert(0, str(SCRIPTS / 'tests'))     # the invariant sweep's class list and seeds

from utils.class_func import generic_func
from utils.class_func.animal_companions import BOND_PREREQS
from utils.class_func.feats import grab_and_clean_feats
from utils.class_func.generic_func import FILTER_WORDS

# generatable_classes() and the seed list both live in the invariant sweep -- import rather than
# copy, so the two scripts cannot disagree about which classes are rollable.
import test_house_invariants as invariants

FEAT_BUCKETS = ('feats', 'story_feats', 'flaw_feats', 'flavor_feats', 'class_feats')
FILTER_PATTERN = re.compile(r'|'.join(map(re.escape, FILTER_WORDS)))
BOON_COMPANION = 'boon companion'

# What a disjunctive branch is asking for. Which shapes can ever match is decided by what
# main_test.py's phase_class_options actually loads into character.chooseable:
#   * ability scores       chooseable_list_stats(..., 'str ', base=10)     -> "str 13"
#   * BAB and caster level ..., 'base attack bonus +' / 'caster level '    -> "base attack bonus +2"
#   * class feature keys   chooseable_list_class_features                  -> "flurry of blows"
#   * the race             chooseable_list_race                            -> character.chosen_race
#   * bonded creatures     animal_companions.BOND_PREREQS                  -> "animal companion"
#   * feat names           added as each feat is chosen
# CLASS LEVELS ARE NOT LOADED. chooseable_list_class() builds "monk level 1st" / "monk 4" but is
# never called from anywhere -- only its def exists -- so every "X level Nth" branch is dead
# whatever the parser does. That is a separate defect and wants its own ticket.
_CLASS_LEVEL = re.compile(r'^(?:\d+(?:st|nd|rd|th)?\s+\w+\s+level'
                          r'|\w+\s+level\s+\d+(?:st|nd|rd|th)?'
                          r'|\w+\s+\d+(?:st|nd|rd|th)?)$')
_SCALAR = re.compile(r'^base attack bonus \+|^caster level '
                     r'|^(?:str|dex|con|int|wis|cha) \d+')
_SIZE = re.compile(r'\bsize\b|\b(?:tiny|small|medium|large|huge)\b')
_PROFICIENCY = re.compile(r'proficien')
_BOND = re.compile(r'animal companion|familiar')


def branch_kind(branch, known_feats):
    branch = branch.strip()
    if branch in known_feats:
        return 'feat name'
    if _SCALAR.match(branch):
        return 'bab / caster level / ability score'
    if _CLASS_LEVEL.match(branch):
        return 'class level (never loaded -- dead)'
    if _BOND.search(branch):
        return 'bonded creature'
    if _SIZE.search(branch):
        return 'size'
    if _PROFICIENCY.search(branch):
        return 'proficiency'
    return 'other (race, prose, class feature)'


def surviving_parts(raw_prereq):
    """The comma-separated fragments the runtime actually gates on, filter words removed."""
    clean = re.sub(r'\.', '', str(raw_prereq).lower().strip())
    return [part.strip() for part in clean.split(",")
            if part.strip() and not FILTER_PATTERN.search(part.strip())]


def legacy_satisfied(parts, chooseable):
    """The pre-fix test: every fragment had to be present verbatim."""
    return all(part in chooseable for part in parts)


def shipped_satisfied(parts, chooseable):
    return all(generic_func.prereq_part_satisfied(part, chooseable) for part in parts)


def patch_everywhere(name, replacement, original):
    """Rebind `name` in every module that imported it, not just the module that defines it."""
    touched = [mod for mod in list(sys.modules.values())
               if getattr(mod, name, None) is original]
    for mod in touched:
        setattr(mod, name, replacement)
    return touched


def static_report():
    # The runtime's own loader (on_bad_lines='skip', prereq NaNs -> ''), so this measures exactly
    # the population the generator sees rather than a slightly different parse of the same file.
    feats = grab_and_clean_feats('data/feats.csv')
    column = 'prerequisites' if 'prerequisites' in feats.columns else 'prerequisite'
    known = {str(n).lower().strip() for n in feats['name'].dropna()}

    rows = len(feats)
    with_parts = 0
    disjunctive_rows = 0      # feats.csv carries same-name variants, so rows > distinct names
    disjunctive = {}          # feat name -> every surviving part (not only the disjunctive ones)
    kinds = {}                # branch shape -> count, across every disjunctive part

    for _, row in feats.iterrows():
        parts = surviving_parts(row.get(column, ''))
        if not parts:
            continue
        with_parts += 1
        alternates = [p for p in parts if ' or ' in p]
        if not alternates:
            continue
        disjunctive_rows += 1
        disjunctive[str(row['name']).lower().strip()] = parts
        for part in alternates:
            for branch in part.split(' or '):
                kind = branch_kind(branch, known)
                kinds[kind] = kinds.get(kind, 0) + 1

    print("static -- data/feats.csv")
    print(f"  rows                                      {rows}")
    print(f"  with >=1 surviving prerequisite part      {with_parts}")
    print(f"  with >=1 disjunctive part                 {disjunctive_rows} rows,"
          f" {len(disjunctive)} distinct names   <- unreachable before the fix")
    print("  disjunctive branches by shape:")
    for kind, count in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"    {count:>5}  {kind}")
    return disjunctive


def run_generations(classes, levels, seeds, capture=False):
    """(feats seen across the sweep, chooseable snapshots, per-character records, error count)."""
    seen, snapshots, records, errors = set(), [], [], 0
    biggest = {'set': set()}

    original_loop = generic_func.no_prereq_loop

    def spy(character, dataset):
        result = original_loop(character, dataset)
        current = set(character.chooseable)
        if len(current) > len(biggest['set']):
            biggest['set'] = current
        return result

    touched = patch_everywhere('no_prereq_loop', spy, original_loop) if capture else []
    try:
        for name in classes:
            for level in levels:
                for seed in seeds:
                    biggest['set'] = set()
                    try:
                        with redirect_stdout(io.StringIO()):
                            payload = invariants.main_test.generate_random_char(
                                class_choice=name, chosen_BAB='high', multi_class='N',
                                userInput_race='random', userInput_region='Tal-Falko',
                                alignment_input='random', userInput_gender='random',
                                high_level=level, low_level=level, gold_num=10000,
                                num_dice='4', num_sides='6', use_backstory_api='N',
                                spheres_flag='N', seed=seed)
                    except Exception:
                        errors += 1
                        continue
                    feats = set()
                    for bucket in FEAT_BUCKETS:
                        feats.update(str(f).lower().strip() for f in (payload.get(bucket) or []))
                    seen.update(feats)
                    held = {e.get('type') for e in (payload.get('bonded_creatures') or [])
                            if e.get('species')}
                    records.append((f"{name} L{level}", held, feats))
                    if capture and biggest['set']:
                        snapshots.append((f"{name} L{level}", biggest['set']))
    finally:
        for mod in touched:
            setattr(mod, 'no_prereq_loop', original_loop)
    return seen, snapshots, records, errors


def eligibility_report(snapshots, disjunctive):
    """Of the disjunctive feats, which flip from ineligible to eligible against a REAL chooseable."""
    flipped = {}   # feat -> how many characters it became eligible for
    for _, chooseable in snapshots:
        for feat, parts in disjunctive.items():
            if legacy_satisfied(parts, chooseable):
                continue
            if shipped_satisfied(parts, chooseable):
                flipped[feat] = flipped.get(feat, 0) + 1

    print(f"\neligibility -- {len(snapshots)} captured character.chooseable snapshots")
    print(f"  of the {len(disjunctive)} disjunctive feats, newly eligible for at least one "
          f"character: {len(flipped)}")
    for feat, count in sorted(flipped.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"    {count:>3}/{len(snapshots)}  {feat}")
    return set(flipped)


def bond_report(records):
    """Boon Companion's take-rate by bond type -- the acceptance evidence for the feat itself."""
    eligible_types = set(BOND_PREREQS)
    buckets = {}    # label -> [characters, took Boon Companion]
    for _, held, feats in records:
        eligible = held & eligible_types
        label = '+'.join(sorted(eligible)) if eligible else ('eidolon only' if held else 'no bond')
        row = buckets.setdefault(label, [0, 0])
        row[0] += 1
        row[1] += BOON_COMPANION in feats

    print(f"\nbond -- Boon Companion take-rate over {len(records)} generations")
    for label, (total, took) in sorted(buckets.items()):
        print(f"    {took:>3}/{total:<4}  {label}")
    unbonded = sum(took for label, (_, took) in buckets.items()
                   if label in ('no bond', 'eidolon only'))
    bonded = sum(took for label, (_, took) in buckets.items()
                 if label not in ('no bond', 'eidolon only'))
    print(f"  taken by a character with an eligible bond: {bonded}")
    print(f"  taken by a character without one:           {unbonded}   <- must be 0")
    return bonded, unbonded


def picks_report(classes, levels, seeds, disjunctive, newly_eligible):
    total = len(classes) * len(levels) * len(seeds)
    print(f"\npicks -- {len(classes)} classes x {levels} x {len(seeds)} seed(s) = {total} "
          f"generations, run twice")

    shipped = generic_func.prereq_part_satisfied
    legacy = lambda part, satisfied, normalize=None: (
        (normalize(part) if normalize is not None else part) in satisfied)
    touched = patch_everywhere('prereq_part_satisfied', legacy, shipped)
    try:
        before, _, _, before_errors = run_generations(classes, levels, seeds)
    finally:
        for mod in touched:
            setattr(mod, 'prereq_part_satisfied', shipped)
    after, _, _, after_errors = run_generations(classes, levels, seeds)

    gained = sorted(after - before)
    lost = sorted(before - after)
    from_disjunction = [f for f in gained if f in disjunctive]

    print(f"  distinct feats before                     {len(before)}"
          f"{f'  ({before_errors} generations failed)' if before_errors else ''}")
    print(f"  distinct feats after                      {len(after)}"
          f"{f'  ({after_errors} generations failed)' if after_errors else ''}")
    print(f"  newly appearing                           {len(gained)}")
    print(f"  ... of those, previously disjunction-blocked  {len(from_disjunction)}")
    for feat in from_disjunction:
        marker = '' if feat in newly_eligible else '   (not flagged by the eligibility pass)'
        print(f"    + {feat}{marker}")
    other = len(gained) - len(from_disjunction)
    if other:
        print(f"  newly appearing for other reasons (knock-on picks): {other}")
    if lost:
        # Not a regression: a wider eligible pool reshuffles which feats a fixed seed lands on.
        print(f"  no longer appearing (pool reshuffle):               {len(lost)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--classes', help='comma-separated subset (default: every generatable class)')
    parser.add_argument('--levels', default='20', help='comma-separated levels (default 20)')
    parser.add_argument('--seeds', type=int, default=1,
                        help="how many of the invariant sweep's fixed seeds to run (default 1)")
    parser.add_argument('--static-only', action='store_true',
                        help='skip the generation passes (fast; csv analysis only)')
    parser.add_argument('--skip-picks', action='store_true',
                        help='run the eligibility and bond passes but not the two-pass pick diff')
    args = parser.parse_args()

    disjunctive = static_report()
    if args.static_only:
        return 0

    classes = args.classes.split(',') if args.classes else invariants.generatable_classes()
    levels = [int(x) for x in args.levels.split(',')]
    seeds = invariants.SEEDS[:max(1, args.seeds)]

    _, snapshots, records, errors = run_generations(classes, levels, seeds, capture=True)
    if errors:
        print(f"\n  note: {errors} generation(s) raised and were skipped")
    newly_eligible = eligibility_report(snapshots, disjunctive)
    bond_report(records)

    if not args.skip_picks:
        picks_report(classes, levels, seeds, disjunctive, newly_eligible)
    return 0


if __name__ == '__main__':
    sys.exit(main())
