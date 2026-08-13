"""Assemble the repo's LICENSE-OGL.txt: canonical OGL 1.0a text + a section 15 curated from OUR sources.

Ticket 09 (docs/wayfinder/psionics/issues/09-ogl-attribution.md). Distributing extracted psionics
mechanics is Distribution under the Open Game License, so the licence has to ship with them, and
section 15 has to name every work the content actually derives from.

Why the section 15 is curated here rather than inherited: pf1-psionics' own section 15 is
**incomplete and mis-sourced**. Measured against its LICENSE file, it lists Psionics Unleashed but
omits *Ultimate Psionics*, *Psionics Expanded: Advanced Psionics Guide* (which the aegis traces to)
and *Psionics Augmented: Compilation II*. Inheriting it verbatim would understate what we use, so
the section is curated: unrecognised upstream entries are kept but reported, and ADDITIONS carries
every work OUR data cites that upstream does not declare (psionics, Mythic Adventures and the other
Paizo hardcovers the feat/spell CSVs cite, Spheres of Power/Might). The Path of War lines upstream
copy-pasted from pf1-pow are kept deliberately -- the generator ships PoW mechanics itself.

Why the OGL text itself is COPIED rather than written here: the licence is a legal document whose
operative text must be reproduced exactly. It is read at build time from an existing verbatim copy
on disk -- by default the one pf1-psionics ships -- so a transcription slip is impossible.

    .venv/Scripts/python.exe Backend/scripts/build_ogl_license.py
    .venv/Scripts/python.exe Backend/scripts/build_ogl_license.py --source <path to an OGL 1.0a file>
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import REPO as ROOT   # noqa: E402
TARGET = ROOT / "LICENSE-OGL.txt"
NOTICE = ROOT / "Backend/json/class_data/psionics/NOTICE.md"

DEFAULT_SOURCE = (Path(os.environ.get("LOCALAPPDATA", "")) /
                  "FoundryVTT/Data/modules/pf1-psionics/LICENSE")

# Where the copyright notice starts in the source file; everything before it is the operative
# licence text, which is identical in every OGL 1.0a copy.
#
# Anchored to the start of a line, and the LAST such match is taken. The bare substring appears
# three more times inside the operative text -- section 6 is *about* the copyright notice ("You must
# update the COPYRIGHT NOTICE portion of this License...") -- so a plain `find` cut the licence off
# mid-section-6 and shipped a file that was missing sections 6 through 14 while claiming verbatim
# reproduction. Only the section 15 header sits at a line start.
NOTICE_MARKER = re.compile(r"^COPYRIGHT NOTICE", re.MULTILINE)

# Phrases from the tail of the operative text. The licence is a legal document that is worthless
# truncated, so the build refuses to write one that is missing its closing sections rather than
# leaving the defect to be noticed by a reader.
OPERATIVE_MUST_CONTAIN = (
    "Updating the License",     # section 9
    "Use of Product Identity",  # section 7
    "Inability to Comply",      # section 12
    "Termination",              # section 13
    "Reformation",              # section 14
)

# Entries of the source's own section 15 that we expect to recognise -- the WotC/Paizo/SRD chain,
# which is accurate there and underpins any Pathfinder-derived content. This is a *reporting* list,
# not a filter: everything that is not explicitly dropped is kept (see DROP_PATTERNS). Anything kept
# that matches nothing here is printed as unrecognised, so a source whose formatting has drifted is
# visible rather than silently thinned out.
KEEP_PATTERNS = (
    "Open Game License v 1.0a", "System Reference Document", "Pathfinder RPG Core Rulebook",
    "Pathfinder RPG Bestiary", "Advanced Player", "Modern System Reference Document",
    "Unearthed Arcana", "Hyperconscious", "If Thoughts Could Kill", "Mindscapes",
    "Psionics Unleashed", "Path of War", "Divergent Paths",
)
# Lines to DROP from the source's section 15. Path of War and Divergent Paths were dropped here
# while this file served only the psionics data (upstream had copy-pasted them from pf1-pow's
# licence); the generator now ships Path of War mechanics itself (six initiator classes plus the
# Martial Training chain, maneuvers harvested via the pf1-pow compendium), so those lines are kept
# on their own merit and nothing is dropped.
DROP_PATTERNS = ()

# Works OUR scraped data actually cites that the source's section 15 does not declare. `verified`
# marks whether the copyright line has been checked against the published work itself; unverified
# entries are still emitted (omitting a source is the worse failure) but the build warns, and the
# line records only what the wiki states.
ADDITIONS = [
    ("Ultimate Psionics. Copyright 2013, Dreamscarred Press; "
     "Authors: Jeremy Smith, Andreas Ronnqvist, Philip Leco II.", True),
    ("Psionics Expanded: Advanced Psionics Guide. Copyright 2012, Dreamscarred Press; "
     "Authors: Jeremy Smith, Andreas Ronnqvist, Philip Leco II.", True),
    ("Psionics Augmented: Compilation II. Copyright 2017, Dreamscarred Press.", False),
    ("Arcforge: Technology Expanded. Copyright 2018, Dreamscarred Press.", False),
    ("Arcforge: Psibertech. Copyright 2019, Dreamscarred Press.", False),
    # The 2026-08 sweep (mythic ticket 08): the corpus ships feats/spells from many Paizo works and
    # the whole Spheres system with no section 15 line. Verified lines are quoted from Paizo's own
    # PRD section 15 (legacy.aonprd.com/openGameLicense.html) or the publisher's legal page; the
    # two unverified lines carry no author list rather than a composed one.
    ("Pathfinder Roleplaying Game Mythic Adventures © 2013, Paizo Publishing, LLC; Authors: "
     "Jason Bulmahn, Stephen Radney-MacFarland, Sean K Reynolds, Dennis Baker, Jesse Benner, "
     "Ben Bruck, Jim Groves, Tim Hitchcock, Tracy Hurley, Jonathan Keith, Jason Nelson, "
     "Tom Phillips, Ryan Macklin, F. Wesley Schneider, Amber Scott, Tork Shaw, Russ Taylor, "
     "and Ray Vallese.", True),
    ("Pathfinder Roleplaying Game Advanced Race Guide. © 2012, Paizo Publishing, LLC; Authors: "
     "Dennis Baker, Jesse Benner, Benjamin Bruck, Jason Bulmahn, Adam Daigle, Jim Groves, "
     "Tim Hitchcock, Hal MacLean, Jason Nelson, Stephen Radney-MacFarland, Owen K.C. Stephens, "
     "Todd Stewart, and Russ Taylor.", True),
    ("Pathfinder Roleplaying Game Ultimate Campaign. © 2013, Paizo Publishing, LLC; Authors: "
     "Jesse Benner, Benjamin Bruck, Jason Bulmahn, Ryan Costello, Adam Daigle, Matt Goetz, "
     "Tim Hitchcock, James Jacobs, Ryan Macklin, Colin McComb, Jason Nelson, Richard Pett, "
     "Stephen Radney-MacFarland, Patrick Renie, Sean K Reynolds, F. Wesley Schneider, "
     "James L. Sutter, Russ Taylor, and Stephen Townshend.", True),
    ("Pathfinder Roleplaying Game Advanced Class Guide © 2014, Paizo Inc.; Authors: "
     "Dennis Baker, Ross Byers, Jesse Benner, Savannah Broadway, Jason Bulmahn, Jim Groves, "
     "Tim Hitchcock, Tracy Hurley, Jonathan H. Keith, Will McCardell, Dale C. McCoy, Jr., "
     "Tom Phillips, Stephen Radney-MacFarland, Thomas M. Reid, Sean K Reynolds, Tork Shaw, "
     "Owen K.C. Stephens, and Russ Taylor.", True),
    ("Pathfinder Roleplaying Game Occult Adventures. © 2015, Paizo Inc.; Authors: "
     "John Bennett, Logan Bonner, Robert Brookes, Jason Bulmahn, Ross Byers, John Compton, "
     "Adam Daigle, Jim Groves, Thurston Hillman, Eric Hindley, Brandon Hodge, Ben McFarland, "
     "Erik Mona, Jason Nelson, Tom Phillips, Stephen Radney-MacFarland, Thomas M. Reid, "
     "Alex Riggs, Robert Schwalb, Mark Seifter, Russ Taylor, and Steve Townshend.", True),
    ("Pathfinder Roleplaying Game Ultimate Intrigue. © 2016, Paizo Inc.", False),
    ("Pathfinder Roleplaying Game Horror Adventures. © 2016, Paizo Inc.", False),
    ("Spheres of Power. © 2014, Drop Dead Studios LLC; Author: Adam Meyers.", True),
    ("Spheres of Might. © 2017, Drop Dead Studios LLC; Authors: Adam Meyers, Michael Sayre, "
     "Andrew Stoeckle, N. Jolly.", True),
]

HEADER = """\
OPEN GAME LICENSE
=================

This file accompanies the Open Game Content distributed by the Pathfinder 1E Randomized Character
Generator. See NOTICE.md files in the source tree for which portions are Open Game Content.

The operative text below is the Open Game License Version 1.0a, reproduced verbatim. The COPYRIGHT
NOTICE (section 15) that follows it is curated for THIS project by
Backend/scripts/build_ogl_license.py -- do not hand-edit it there; edit the script.

"""

NOTICE_TEXT = """\
# Open Game Content notice

**Everything in this directory is Open Game Content**, declared under section 8 of the Open Game
License Version 1.0a. The full licence, including the section 15 copyright notice naming every work
this content derives from, is in [`LICENSE-OGL.txt`](../../../../LICENSE-OGL.txt) at the repository
root.

## What is Open Game Content

The five generated data files here — `psionic_classes.json`, `psionic_class_options.json`,
`psionic_power_lists.json`, `psionic_powers.json`, `psionic_powers_known.json` — carry game
mechanics (class tables, power descriptions, power point progressions, class option lists) derived
from the Dreamscarred Press psionics line as republished by the Library of Metzofitz wiki. Those
mechanics are Open Game Content and are redistributed as such.

`psionic_races.json` likewise carries Open Game Content, sourced from d20pfsrd.

## What is not

The **Python source of this repository is not Open Game Content** — the scrapers, validators,
builders and generation modules are the project's own work and are not released under the OGL.
`psionic_name_map.json` is a reconciliation artifact of this project, not game content.

Product Identity of Paizo Inc. and of Dreamscarred Press is not used, and no compatibility with any
trademark is claimed. `pf1-psionics` is credited in section 15's lineage as an intermediate
compiled source. Dreamscarred Press does not endorse this project.

## Section 10

Serving these mechanics in an HTTP response is Distribution under section 10 of the licence, so the
backend exposes the licence at the `/license` route and every generated payload carries a
`license_url` pointer to it rather than embedding the text.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", default=str(DEFAULT_SOURCE),
                        help="a file containing verbatim OGL 1.0a text")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        sys.exit(f"no OGL source text at {source}\n"
                 f"Pass --source pointing at a verbatim OGL 1.0a copy. This script deliberately "
                 f"does not carry the licence text itself -- it must be copied, not retyped.")
    raw = source.read_text(encoding="utf-8")
    matches = list(NOTICE_MARKER.finditer(raw))
    if not matches:
        sys.exit(f"{source} has no section 15 header at a line start -- is it really an OGL 1.0a "
                 f"copy?")
    marker = matches[-1]

    operative = raw[:marker.start()].strip().strip('"').strip()
    upstream_notice = raw[marker.end():].strip().strip('"').strip()

    missing = [s for s in OPERATIVE_MUST_CONTAIN if s not in operative]
    if missing:
        sys.exit(f"the operative licence text extracted from {source} is missing "
                 f"{len(missing)} expected section(s): {', '.join(missing)}.\n"
                 f"Refusing to write a truncated licence. Check the section 15 header in the "
                 f"source -- it must be the last line-initial 'COPYRIGHT NOTICE'.")

    # Upstream keeps section 15 as one run-on paragraph; split it back into entries at a sentence
    # end followed by a new work's title. The second lookbehind spares author initials -- without it
    # "Bruce R. Cordell" and "based on material by E. Gary Gygax" split mid-name, and the orphaned
    # surnames then matched no pattern and were dropped, quietly deleting attribution.
    entries = [e.strip() for e in re.split(r"(?<=\.)(?<!\s[A-Z]\.)\s+(?=[A-Z])", upstream_notice)
               if e.strip()]
    # Keep by default, drop only what is explicitly disowned. Section 15 must name every work the
    # content derives from, so an entry we fail to recognise has to survive: omitting a source is
    # the worse failure. Unrecognised survivors are reported below.
    kept, dropped, unrecognised = [], [], []
    for entry in entries:
        if any(p in entry for p in DROP_PATTERNS):
            dropped.append(entry)
            continue
        kept.append(entry)
        if not any(p in entry for p in KEEP_PATTERNS):
            unrecognised.append(entry)

    added = []
    unverified = []
    for line, verified in ADDITIONS:
        if any(line.split(".")[0] in k for k in kept):
            continue
        added.append(line)
        if not verified:
            unverified.append(line)

    body = [HEADER, operative, "", "", "15. COPYRIGHT NOTICE", ""]
    body += [f"{entry}" for entry in kept]
    body += [f"{entry}" for entry in added]
    body += ["",
             "pf1-psionics (https://github.com/SoxMax/pf1-psionics) is credited as an intermediate",
             "compiled source of the psionics mechanics reconciled against in this project.",
             ""]
    TARGET.write_text("\n".join(body) + "\n", encoding="utf-8")

    NOTICE.parent.mkdir(parents=True, exist_ok=True)
    NOTICE.write_text(NOTICE_TEXT, encoding="utf-8")

    print(f"source:  {source}")
    print(f"kept {len(kept)} upstream entries, dropped {len(dropped)} "
          f"(pf1-pow leftovers), added {len(added)} psionics works")
    for line in dropped:
        print(f"  dropped: {line[:80]}")
    for line in added:
        print(f"  added:   {line[:80]}")
    if unrecognised:
        print(f"\n{len(unrecognised)} kept section 15 entr(ies) matched no known work. They are "
              f"kept deliberately -- section 15 may not lose a source -- but a run of these means "
              f"the source's formatting has drifted and the split needs revisiting:")
        for line in unrecognised:
            print(f"  ? {line[:100]}")
    if unverified:
        print(f"\nWARNING: {len(unverified)} section 15 line(s) carry a copyright year/holder that "
              f"has NOT been checked against the published work. They are emitted because omitting "
              f"a source is the worse failure, but verify them before a public release:")
        for line in unverified:
            print(f"  - {line}")
    print(f"\nwrote {TARGET.relative_to(ROOT)}")
    print(f"wrote {NOTICE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
