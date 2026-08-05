"""Fixture gate for the companion-archetype classifier -- the 15 human-signed verdicts.

    C:\\Python310\\python.exe Backend/scripts/validate_companion_archetype_classifier.py
    C:\\Python310\\python.exe Backend/scripts/validate_companion_archetype_classifier.py -v

NAMED `validate_` DELIBERATELY. It was `test_companion_archetype_classifier.py`, which meant
`validate_all.py` -- whose whole design is discovery by glob over `validate_*.py` -- never picked it
up, and neither did CI. It passed only when somebody ran it by hand, while looking exactly like a
wired gate (argparse, -v, PASS/FAIL, this docstring). A regex tweak in the builder could silently
re-break every trap below with the build still green. It IS a data gate by this repo's own
definition: it asserts the classifier still reproduces the signed verdicts.

Map #18, ticket #40. The first pass of `build_companion_archetypes.py` classified by running generic
regexes over a whole-archetype prose blob, and scored **6 of 15** against the first batch of human
sign-offs. Each miss was a distinct rule the classifier did not have, so these fifteen are pinned
here: they are the only evidence that a rewrite is better rather than differently wrong.

Two verdicts differ from the raw worksheet, revised by the rules settled on 2026-08-02:

  * Sunrider        species_pool -> forces + species_pool. Its text forbids the domain alternative
                    ("cannot choose a different animal or choose a domain instead"), and `forces`
                    means exactly that the flip is suppressed.
  * Aerie Protector none -> species_pool. "an animal with a fly speed" is derivable from
                    animal_choices.json (21 species qualify), so it is a real pool, not flavour.

Two verdicts are pinned AGAINST the signed worksheet, both flagged for confirmation. If the human
verdict is upheld, change it HERE deliberately -- do not loosen the classifier to pass.

  * Devolutionist  pinned with `progression` on top of the signed forces+species_pool. The text says
                   "the devolved humanoid doesn't increase to size Large at 4th level", which is the
                   per-field veto #38 named as its canonical example.
  * Dragon Shaman  pinned `species_pool`, NOT the signed forces+species_pool. Its text is
                   grammatically identical to the five other totem shamans -- "A dragon shaman WHO
                   CHOOSES an animal companion must select a crocodile or monitor lizard. If
                   choosing a domain, ... domains." -- and every one of those was signed
                   `species_pool`. No rule can separate them, and inventing one would be encoding
                   noise. The conditional "who chooses" is precisely what makes it not `forces`.

MOUNTAIN DRUID, and two others, are expected to be ABSENT. `BOND_TARGETS` contained a bare "mount",
which matches inside "mountain" and "mountaineer"; Mountain Druid, Summit Sentinel and Mountain Witch
were classified although none of them touches a bond feature at all. Word-boundaried, the real count
is 203, not 206. A `None` expectation below means "must not be classified".
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _harness import Report                   # noqa: E402

import build_companion_archetypes as bca      # noqa: E402

# key -> (expected effects, expected creature_type or None)
EXPECTED = {
    # Signed `none`; the honest expression of "no effect on the bond" is not being a bond archetype.
    "Druid/Mountain Druid":    (None, None),
    "Ranger/Summit Sentinel":  (None, None),
    "Witch/Mountain Witch":    (None, None),
    "Druid/Nithveil Adept":    ({"removes"}, None),
    "Druid/Sunrider":          ({"forces", "species_pool"}, None),
    "Druid/Aerie Protector":   ({"species_pool"}, None),
    "Druid/Ancient Guardian":  ({"removes"}, None),
    "Druid/Ape Shaman":        ({"species_pool"}, None),
    "Druid/Bat Shaman":        ({"species_pool"}, None),
    "Druid/Bear Shaman":       ({"species_pool"}, None),
    "Druid/Boar Shaman":       ({"species_pool"}, None),
    "Druid/Eagle Shaman":      ({"species_pool"}, None),
    "Druid/Cave Druid":        ({"none"}, None),
    "Druid/Devolutionist":     ({"forces", "species_pool", "progression"}, None),
    "Druid/Draconic Druid":    ({"forces", "creature_type"}, "drake"),
    "Druid/Dragon Shaman":     ({"species_pool"}, None),          # signed forces+; see docstring
    "Druid/Elemental Ally":    ({"forces", "creature_type"}, "eidolon"),
}

# Why each one is here, printed on failure so the fix is aimed at the rule and not the symptom.
RULE = {
    "Druid/Nithveil Adept": "R1 removal by prohibition -- 'cannot select an animal companion'",
    "Druid/Cave Druid": "R2 domain-side only -- its bond text names no creature at all",
    "Druid/Sunrider": "R3 forcing by prohibition -- 'cannot ... choose a domain instead'",
    "Druid/Dragon Shaman": "R3 forcing by prohibition",
    "Druid/Devolutionist": "R3 + R5 + progression veto",
    "Druid/Draconic Druid": "R4 creature type -- a drake, not an animal",
    "Druid/Elemental Ally": "R4 creature type -- elemental eidolons",
    "Druid/Aerie Protector": "R5 derivable property pool -- fly speed",
    "Druid/Ancient Guardian": "R1 -- forced onto the domain side, so no creature",
}

REPORT = Report('validate_companion_archetype_classifier')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show every case, not only the failures")
    args = parser.parse_args()

    entries = bca.build()

    failures, passes = [], 0
    for key, (want_effects, want_type) in sorted(EXPECTED.items()):
        entry = entries.get(key)
        if want_effects is None:                 # must NOT be classified -- see the docstring
            if entry is None:
                passes += 1
                if args.verbose:
                    print(f"  ok    {key:<26} absent, as expected")
            else:
                got = "+".join(sorted(e["effect"] for e in entry.get("effects", [])))
                failures.append((key, "absent (touches no bond feature)", got))
            continue
        if entry is None:
            failures.append((key, "+".join(sorted(want_effects)), "not classified at all"))
            continue
        got_effects = {item["effect"] for item in entry.get("effects", [])}
        got_type = entry.get("creature_type")
        ok = got_effects == want_effects and (got_type or None) == want_type

        want_text = "+".join(sorted(want_effects)) + (f" ({want_type})" if want_type else "")
        got_text = "+".join(sorted(got_effects)) + (f" ({got_type})" if got_type else "")
        if ok:
            passes += 1
            if args.verbose:
                print(f"  ok    {key:<26} {got_text}")
        else:
            failures.append((key, want_text, got_text))

    for key, want, got in failures:
        lines = [key, f"want: {want}", f"got:  {got}"]
        if key in RULE:
            lines.append(f"rule: {RULE[key]}")
        REPORT.error("\n      ".join(lines))

    return REPORT.finish(f"{passes}/{len(EXPECTED)} signed verdicts reproduced")


if __name__ == "__main__":
    sys.exit(main())
