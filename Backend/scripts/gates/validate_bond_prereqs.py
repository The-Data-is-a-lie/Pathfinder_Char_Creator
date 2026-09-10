"""Gate the wiring that makes a bonded creature satisfy a feat prerequisite.

    C:\\Python310\\python.exe Backend/scripts/gates/validate_bond_prereqs.py

Boon Companion sat in `data/feats.csv`, complete and correct, and was taken by nobody: it was
offered 329 times across twelve druids and passed the prerequisite gate zero times. Two independent
causes, and BOTH have to hold for the feat to be reachable --

  1. `animal_companions.register_bonded_creature_prereqs` puts a phrase into `character.chooseable`
     at the moment a creature is actually granted. No class-feature key can stand in for it: a
     druid's key is `nature bond`, which is present whether the druid took the companion or the
     domain. Only the grant knows.
  2. `generic_func.prereq_part_satisfied` splits a fragment on " or " and passes on any branch.
     Boon Companion's prerequisite is "Animal companion or familiar class feature." -- a
     disjunction, and before the split it survived comma-splitting as one opaque token.

Neither half is visible in a payload: `chooseable` is generator-internal and the feat only shows up
when the random draw happens to land on it, which over a whole sweep of one character per class it
did not once. A take-rate assertion would therefore be a coin flip. This runs the REAL parser over
the REAL prerequisite text from `data/feats.csv` against a stub character, which is deterministic
and fails the moment either half regresses -- including if the CSV text is re-scraped and drifts
away from the phrases `BOND_PREREQS` registers.

What it asserts:

- A character holding a companion, a mount or a familiar has Boon Companion in its eligible pool.
- A character holding only an eidolon, or nothing, does not. An eidolon is neither an animal
  companion nor a familiar, and an absence entry (`species: None`) grants no prerequisite at all.
- Every phrase the tables register is load-bearing: it appears in at least one real prerequisite in
  `data/feats.csv`. A phrase that matches nothing is dead weight that reads as coverage.

Done when: exit 0 on the shipped wiring, non-zero if the registration is narrowed back to
companions, the disjunction split is reverted, or Boon Companion's prerequisite text drifts.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))            # Backend/scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))   # Backend

from _harness import Report                                    # noqa: E402
from utils.class_func.animal_companions import (               # noqa: E402
    BOND_PREREQS, BOND_PREREQS_EITHER, register_bonded_creature_prereqs,
)
from utils.class_func.feats import grab_and_clean_feats        # noqa: E402
from utils.class_func.generic_func import no_prereq_loop, no_prereq_prep  # noqa: E402

REPORT = Report('bond prereqs')

FEAT = 'boon companion'


class _Stub:
    """The four attributes `no_prereq_loop` reads. Nothing else about a character matters here."""

    def __init__(self):
        self.chooseable = set()
        self.chooseable_talents = []
        no_prereq_prep(self)          # compiles filter_pattern from the runtime's own FILTER_WORDS
        self.role = None              # random mode: the path that was broken


def eligible(types, dataset):
    stub = _Stub()
    register_bonded_creature_prereqs(stub, types)
    return FEAT in no_prereq_loop(stub, dataset)


def main():
    feats = grab_and_clean_feats('data/feats.csv')
    column = 'prerequisites' if 'prerequisites' in feats.columns else 'prerequisite'
    rows = feats[feats['name'].astype(str).str.strip().str.lower() == FEAT]
    if rows.empty:
        REPORT.error(f"{FEAT!r} is not in data/feats.csv at all -- the feat this gate exists for "
                     f"has been removed or renamed")
        return REPORT.finish()

    prereq = str(rows.iloc[0].get(column, '')).strip()
    REPORT.check(bool(prereq),
                 f"{FEAT!r} carries no prerequisite text, so this gate cannot tell a working "
                 f"registration from a broken one")
    dataset = {'Boon Companion': {'prerequisites': prereq}}

    for kind in sorted(BOND_PREREQS):
        REPORT.check(eligible({kind}, dataset),
                     f"a character holding a {kind} cannot take Boon Companion "
                     f"(prerequisite {prereq!r}) -- registration or the disjunction split broke")

    REPORT.check(eligible({'companion', 'familiar'}, dataset),
                 "a character holding both a companion and a familiar cannot take Boon Companion")

    # The disjunction split on its own, against the same real text. Every registration above also
    # writes BOND_PREREQS_EITHER -- the whole phrase, pre-composed -- so those checks would keep
    # passing on a verbatim match alone if the split were reverted. This one registers only the
    # atomic phrases, so it passes ONLY if "animal companion or familiar class feature" is actually
    # being split and matched on its second branch.
    atomic = _Stub()
    atomic.chooseable.update(BOND_PREREQS['familiar'])
    REPORT.check(FEAT in no_prereq_loop(atomic, dataset),
                 f"{BOND_PREREQS['familiar']} does not satisfy {prereq!r} -- the disjunction is not "
                 f"being split, and the 153 other feats that need it are unreachable again")
    REPORT.check(not eligible({'eidolon'}, dataset),
                 "an eidolon satisfied Boon Companion -- it is neither an animal companion nor a "
                 "familiar, and RAW does not let it be boosted this way")
    REPORT.check(not eligible(set(), dataset),
                 "a character with NO bonded creature can take Boon Companion -- the prerequisite "
                 "is being satisfied by something other than the grant")

    # Every registered phrase must be load-bearing somewhere in the real data.
    all_prereqs = ' | '.join(str(v).lower() for v in feats[column].dropna())
    for phrase in sorted(set(BOND_PREREQS_EITHER).union(*BOND_PREREQS.values())):
        REPORT.check(re.search(re.escape(phrase), all_prereqs) is not None,
                     f"the registered phrase {phrase!r} appears in no prerequisite in "
                     f"data/feats.csv -- it reads as coverage and provides none")

    return REPORT.finish(
        f"{FEAT!r} ({prereq!r}) is reachable for {', '.join(sorted(BOND_PREREQS))} and unreachable "
        f"without a bond; all {len(set(BOND_PREREQS_EITHER).union(*BOND_PREREQS.values()))} "
        f"registered phrases are load-bearing")


if __name__ == '__main__':
    sys.exit(main())
