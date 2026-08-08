"""Harvest the omdura's invocations and the vampire hunter's vampiric foci from `pf-content`.

    C:\\Python310\\python.exe Backend/scripts/build/build_collab_class_options.py

Class-choices ticket 02 found both classes generating NOTHING: their defining choice existed only
as prose in `class_data.json` naming options the repo did not have. `build_collab_class_data.py` is
the sibling that harvested their chassis (main stat, BAB, hit die, features); this harvests the
option pools those features choose from, into the `{dataset: {name: description}}` shape the generic
chooser already consumes.

THE TWO CLASSES NEED DIFFERENT EXTRACTIONS, and that is the interesting part:

  vampire hunter  Each vampiric focus is its OWN Item in `pf-collab-content` -- Vampiric Agility,
                  Momentum, Might, and so on. Ordinary harvest, the same shape as the occult six.
                  `Vampiric Focus` itself is excluded: it is the feature that does the choosing.

  omdura          The nine invocations are NOT items. They live as bolded headings inside the
                  single `Invocation` item's own description, which is why a name search for them
                  finds nothing and why ticket 02 filed this as having no source at all. They are
                  parsed out of that one description.

The omdura path is prose parsing, which is the field-glue territory that damaged the hunter's aspect
pool -- but from a clean source: these are real `<b>` headings in authored HTML, not a scraped table
whose cells slid sideways. The parse asserts it found nine, so a pack edit that changes the markup
fails here instead of silently shipping an omdura with three invocations.

Foundry may be running. LevelDB is single-writer, so each pack is copied to a scratch directory and
the copy's LOCK dropped before it is read; the installed packs are never opened or written.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BUILD, REPO as ROOT   # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconcile_psionics_names import find_classic_level   # noqa: E402  -- one owner for the hunt

DUMPER = BUILD / "dump_foundry_pack.mjs"
CLASS_DIR = ROOT / "Backend/json/class_data"
FOUNDRY_DATA = Path(os.environ.get("LOCALAPPDATA", "")) / "FoundryVTT/Data"
DEFAULT_MODULE_ROOT = FOUNDRY_DATA / "modules/pf-content"

# Both classes are collab content, so one pack carries both.
MODULE_PACKS = ("pf-collab-content",)

# The feature that CHOOSES is not one of the choices. Without this the vampire hunter would offer
# "Vampiric Focus" as a vampiric focus.
FOCUS_FEATURE = "vampiric focus"

# Counted from the pack on 2026-08-07. These are assertions, not documentation: the first run of
# this script expected 7 foci (a miscount from a truncated grep) and the guard caught it rather than
# letting a thin pool ship. Update deliberately when the pack changes, never to make a run pass.
EXPECTED = {"vampire hunter": 10, "omdura": 9}


def plain(value: str) -> str:
    """Pack HTML -> readable prose, matching what the other class pools hold."""
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def dump(module_root: Path, classic_level: Path) -> dict:
    packs = [module_root / "packs" / name for name in MODULE_PACKS]
    missing = [p for p in packs if not p.exists()]
    if missing:
        sys.exit(f"missing packs: {[str(p) for p in missing]}")

    scratch = Path(tempfile.mkdtemp(prefix="collab-packs-"))
    try:
        copies = []
        for pack in packs:
            target = scratch / pack.name
            # An open Foundry holds LOCK itself, so it cannot be copied -- ignoring it is the point.
            shutil.copytree(pack, target, ignore=shutil.ignore_patterns("LOCK"))
            (target / "LOCK").unlink(missing_ok=True)
            copies.append(target)
        command = ["node", str(DUMPER), "--classic-level", str(classic_level), "--full",
                   *[str(p) for p in copies]]
        # encoding= is load-bearing: the pack prose is UTF-8 and Windows would otherwise decode
        # node's stdout as cp1252 and die on the first typographic dash.
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            sys.exit(f"pack dump failed:\n{result.stderr.strip()}")
        return json.loads(result.stdout)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def vampiric_foci(docs: list) -> dict:
    """Every `Vampiric X` item the pack associates with the Vampire Hunter, minus the feature.

    Gated on `system.associations.classes` rather than the name alone -- that field is an EXACT
    list, which is what makes the pack a source rather than a renderer (the reasoning
    build_occult_class_data.py already relies on). The name prefix stays as the discriminator,
    because the class is associated with more than its foci: `Technique Feat`, `Detect Undead` and
    the rest of the chassis carry the same association and are granted, not chosen.
    """
    picked = {}
    for doc in docs:
        name = (doc.get("name") or "").strip()
        assoc = ((doc.get("system") or {}).get("associations") or {}).get("classes") or []
        if "Vampire Hunter" not in assoc:
            continue
        if not name.lower().startswith("vampiric ") or name.lower() == FOCUS_FEATURE:
            continue
        body = ((doc.get("system") or {}).get("description") or {}).get("value") or ""
        picked[name] = plain(body)
    return dict(sorted(picked.items()))


def invocations(docs: list) -> dict:
    """The omdura's invocation types, parsed out of the `Invocation` item's own description.

    Each type is a bolded heading followed by its rules text, so the split is on the headings and
    each one's description is everything up to the next. The regex takes <b> or <strong> and
    tolerates the colon being inside or outside the tag, because the pack does both.
    """
    source = next((d for d in docs if (d.get("name") or "").strip().lower() == "invocation"), None)
    if source is None:
        sys.exit("no `Invocation` item in pf-collab-content -- the omdura's pool has no source")
    body = ((source.get("system") or {}).get("description") or {}).get("value") or ""

    marks = list(re.finditer(r"<(?:b|strong)>\s*([^<:]{3,40}?)\s*:?\s*</(?:b|strong)>\s*:?", body))
    picked = {}
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        text = plain(body[mark.end():end])
        if text:
            picked[mark.group(1).strip()] = text
    return dict(sorted(picked.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--module-root", default=str(DEFAULT_MODULE_ROOT))
    parser.add_argument("--classic-level", default=None)
    args = parser.parse_args()

    packs = dump(Path(args.module_root), find_classic_level(args.classic_level))
    docs = [entry["doc"] for entry in packs.get("pf-collab-content", [])]

    sections = {
        "vampire hunter": {"vampiric foci": vampiric_foci(docs)},
        "omdura": {"invocations": invocations(docs)},
    }

    for name, buckets in sections.items():
        for dataset, options in buckets.items():
            want = EXPECTED[name]
            if len(options) != want:
                # Loud rather than partial: a pool that quietly shrinks produces a class that picks
                # from three options and looks like it is working. Same rule as the occult builder.
                sys.exit(f"{name}/{dataset} harvested {len(options)} options, expected {want} -- "
                         f"the pack changed shape; fix the rule rather than shipping a thin pool. "
                         f"Got: {sorted(options)}")
        path = CLASS_DIR / f"{name}.json"
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        existing.update(buckets)
        path.write_text(json.dumps(existing, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        counts = ", ".join(f"{k} {len(v)}" for k, v in buckets.items())
        print(f"  wrote {path.relative_to(ROOT)} -> {counts}")

    print("\nnow run Backend/scripts/gates/validate_class_choices.py, then test_house_invariants.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
