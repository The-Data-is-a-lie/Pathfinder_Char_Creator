"""Dump the `pf-content` Actor names the Foundry module can clone -> pf_content_companions.json.

    C:\\Python310\\python.exe Backend/scripts/dump_pf_content_actors.py
    C:\\Python310\\python.exe Backend/scripts/dump_pf_content_actors.py --module-root <dir>

Map #18, ticket #29. The module renders a bonded creature by cloning the `pf-content` Actor whose
name matches the species (D1-D3), and it attaches BY NAME -- a miss degrades to a bare `npc`. That
degrade is legitimate, but a silent one is not: the same silence already bit spell conditionals and
psionics. This dump is what `validate_companion_names.py` diffs the generator's species names
against.

Reuses `dump_foundry_pack.mjs` and `reconcile_psionics_names.py`'s classic-level hunt rather than
adding a second LevelDB reader -- the ticket asked for a new `.mjs`, but the existing one is already
generic over pack directories, so this is the Python caller only.

FOUNDRY MUST NOT BE RUNNING. LevelDB is single-writer and an open Foundry holds the lock on every
pack it has loaded.

`pf-eidolon-forms` is dumped alongside the creature packs because D4's degraded eidolon takes its
named base form from there, so the same read serves both.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BUILD, REPO as ROOT, SCRIPTS as HERE   # noqa: E402

from reconcile_psionics_names import find_classic_level   # noqa: E402  -- one owner for the hunt

DUMPER = BUILD / "dump_foundry_pack.mjs"
OUT = ROOT / "Backend/json/pf_content_companions.json"

DEFAULT_MODULE_ROOT = (Path(os.environ.get("LOCALAPPDATA", "")) /
                       "FoundryVTT/Data/modules/pf-content")

# pf-companions   -- animal companions and mounts
# pf-familiars    -- core familiars plus the named improved familiars
# pf-eidolon-forms-- all seven base forms in both sizes (D4)
# pf-companion-features -- read in the same pass; #31/#33 want it and a second Foundry-closed
#                          session is a real cost.
PACKS = ("pf-companions", "pf-familiars", "pf-eidolon-forms", "pf-companion-features")


def dump(module_root: Path, classic_level: Path) -> dict:
    import subprocess
    packs = [module_root / "packs" / name for name in PACKS]
    missing = [p for p in packs if not p.exists()]
    if missing:
        sys.exit(f"missing packs under {module_root}: {[p.name for p in missing]}")
    command = ["node", str(DUMPER), "--classic-level", str(classic_level),
               *[str(p) for p in packs]]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        hint = ""
        if "LOCK" in result.stderr or "lock" in result.stderr:
            hint = "\n\nFoundry is probably still running -- it holds the pack lock."
        sys.exit(f"pack dump failed:\n{result.stderr.strip()}{hint}")
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--module-root", default=str(DEFAULT_MODULE_ROOT),
                        help="the pf-content module directory")
    parser.add_argument("--classic-level", default=None,
                        help="directory of an installed classic-level package")
    args = parser.parse_args()

    classic_level = find_classic_level(args.classic_level)
    print(f"classic-level: {classic_level}")
    raw = dump(Path(args.module_root), classic_level)

    out = {}
    for pack, entries in raw.items():
        # Folders share the keyspace (!folders!<id>); only actor documents are clone targets.
        names = sorted({e["name"] for e in entries
                        if e.get("key", "").startswith("!actors!") and e.get("name")})
        out[pack] = names
        print(f"  {pack:<22} {len(names):>5} actors")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
