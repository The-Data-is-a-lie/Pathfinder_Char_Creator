"""Draft-generate pf1 CHANGES + conditional context notes for FEATS (manual tool, never part of the
generation pipeline).

Reads data/feats.csv (pipe-delimited; the `benefit` column holds the mechanical text) and applies
CONSERVATIVE regexes to extract flat typed bonuses ("+N <type> bonus to/on <target>"). Each match is
classed as either:
  - an always-on CHANGE   (no trigger; the feat-holder simply has the bonus), or
  - a situational NOTE    (a "when / while / against / vs / if ..." trigger, or a bonus granted to a
                           target / ally / companion rather than the feat-holder) -> contextNotes.
Everything the regex can't confidently read is left out on purpose -- those feats stay
description-only (the FoundryVTT module already renders the feat's text).

Double-apply guard: optionally reads the FoundryVTT module's every_feat.json compendium and stamps
`_compendium_automated` (+ the count of changes / contextNotes it already carries) on each drafted
feat, so curation can SKIP feats Foundry already automates and avoid stacking a bonus twice.

Output is a DRAFT keyed by feat name; every entry carries "review": true plus matched snippets and
the bucket guess, and is meant to be hand-curated into Backend/json/feats/feat_changes.json (strip
the review/_* keys; keep only entries you trust, and only for feats the compendium does NOT already
automate).

Usage:
    C:\\Python310\\python.exe Backend/scripts/build_feat_changes.py [--out PATH] [--compendium PATH]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import REPO   # noqa: E402
SOURCE = REPO / "data" / "feats.csv"
DEFAULT_OUT = REPO / "Backend" / "json" / "feats" / "feat_changes.draft.json"
# Best-effort default location of the FoundryVTT module's feat compendium (double-apply guard only;
# the build still works if it's absent -- the guard is just stamped "unknown").
DEFAULT_COMPENDIUM = (Path.home() / "AppData" / "Local" / "FoundryVTT" / "Data" / "modules"
                      / "pf1e_random_char_generator" / "templates" / "character_sheet_folder"
                      / "every_feat.json")

# pf1 bonus types the change "type" field accepts (untyped when absent).
_BONUS_TYPES = ('dodge|morale|insight|luck|competence|circumstance|profane|sacred|'
                'deflection|resistance|shield|enhancement|alchemical|racial|size|trait')

# Target phrase -> pf1 change target. Deliberately small; anything unmapped is skipped.
_TARGETS = [
    (r'armor class|\bac\b', 'ac'),
    (r'melee attack rolls', 'mattack'),
    (r'ranged attack rolls', 'rattack'),
    (r'attack rolls', 'attack'),
    (r'(?:weapon )?damage rolls', 'wdamage'),
    # Specific saves BEFORE the generic "saving throws" so "all Will saving throws" -> will (not allSavingThrows).
    (r'fortitude sav(?:es|ing throws)', 'fort'),
    (r'ref\s*lex sav(?:es|ing throws)', 'ref'),  # scrape sometimes writes "Reflex" as "Ref lex"
    (r'will sav(?:es|ing throws)', 'will'),
    (r'all saving throws|saving throws|all saves', 'allSavingThrows'),
    (r'\bcmd\b|combat maneuver defense', 'cmd'),
    (r'\bcmb\b|combat maneuver (?:bonus|checks)', 'cmb'),
    (r'initiative(?: checks)?', 'init'),
    (r'(?:base land|movement|land) speed', 'landSpeed'),
]

# Skill-check bonuses: "on <Skill> checks". pf1 skill ids.
_SKILLS = {
    'acrobatics': 'skill.acr', 'appraise': 'skill.apr', 'bluff': 'skill.blf', 'climb': 'skill.clm',
    'diplomacy': 'skill.dip', 'disable device': 'skill.dev', 'disguise': 'skill.dis',
    'escape artist': 'skill.esc', 'fly': 'skill.fly', 'heal': 'skill.hea',
    'intimidate': 'skill.int', 'perception': 'skill.per', 'ride': 'skill.rid',
    'sense motive': 'skill.sen', 'sleight of hand': 'skill.slt', 'stealth': 'skill.ste',
    'survival': 'skill.sur', 'swim': 'skill.swm', 'spellcraft': 'skill.spl',
}

# "+2 dodge bonus to <phrase>" -- 'against' is intentionally NOT a connector so that
# "+2 bonus on saving throws against fear" is captured (then flagged conditional by _COND_RE).
_FLAT_RE = re.compile(
    r'\+(\d+)\s*(' + _BONUS_TYPES + r')?\s*bonus\s+(?:to|on)\s+([^.,;]{1,70})',
    re.IGNORECASE)

# Triggers that make a bonus situational -> a context note rather than an always-on change.
_COND_RE = re.compile(
    r'\b(against|vs\.?|versus|when|while|whenever|if|during|as long as|made to|'
    r'to confirm|to resist|to penetrate|to avoid|on a |on the )\b', re.IGNORECASE)

# Subjects that are NOT the feat-holder -> not a clean self change (surfaced as a note for review).
_OTHER_SUBJECT_RE = re.compile(
    r'\b(the target|that creature|the creature|your all(?:y|ies)|each ally|the subject|'
    r'they gain|chosen (?:creature|ally)|your (?:companion|mount|familiar|eidolon|animal))\b',
    re.IGNORECASE)


def _match_target(phrase):
    p = phrase.strip().lower()
    for pat, target in _TARGETS:
        if re.search(pat, p):
            return target
    m = re.search(r'([a-z ]+?) checks', p)
    if m and m.group(1).strip() in _SKILLS:
        return _SKILLS[m.group(1).strip()]
    return None


def _match_targets(phrase):
    """Distinct pf1 targets named in one bonus clause, in order (compound phrases like
    'CMD and to initiative' grant the same bonus to several targets). Deduped, order preserved."""
    targets = []
    for part in re.split(r',|\band\b|\bto\b', phrase):
        t = _match_target(part)
        if t and t not in targets:
            targets.append(t)
    return targets


def _parse_feat(text):
    """Conservatively pull (changes, contextNotes, snippets, bucket) out of one feat's benefit text.
    bucket: 1 = has an always-on change; 2 = situational only; None = nothing parsed."""
    changes, notes, snippets = [], [], []
    for m in _FLAT_RE.finditer(text):
        base, btype, phrase = int(m.group(1)), m.group(2), m.group(3)
        targets = _match_targets(phrase)
        if not targets:
            continue
        window = text[max(0, m.start() - 40): m.end() + 30]
        conditional = bool(_COND_RE.search(m.group(0))) or bool(_OTHER_SUBJECT_RE.search(window))
        snippets.append(m.group(0).strip())
        if conditional:
            notes.append({"text": m.group(0).strip(), "_target": targets[0]})
        else:
            for t in targets:
                changes.append({"formula": str(base), "target": t,
                                "type": (btype or "untyped").lower(),
                                "operator": "add", "priority": 0})
    if not changes and not notes:
        return None
    return changes, notes, snippets, (1 if changes else 2)


def _load_compendium(path):
    """name(lower) -> (n_changes, n_contextNotes) from every_feat.json; None if unreadable."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    out = {}
    for it in (data if isinstance(data, list) else data.values()):
        if not isinstance(it, dict):
            continue
        name = str(it.get("name", "")).strip().lower()
        if not name:
            continue
        sysd = it.get("system") or {}
        nc, nn = len(sysd.get("changes") or []), len(sysd.get("contextNotes") or [])
        prev = out.get(name, (0, 0))
        out[name] = (max(prev[0], nc), max(prev[1], nn))
    return out


def build_draft(compendium_path):
    df = pd.read_csv(SOURCE, sep="|", on_bad_lines="skip", dtype=str, keep_default_na=False)
    comp = _load_compendium(compendium_path)
    draft = {}
    total = with_change = with_note = text_only = redundant = 0
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        ftype = str(row.get("type", "")).strip()
        if not name or ftype == "Mythic":
            continue
        total += 1
        text = (str(row.get("benefit", "")).strip() or str(row.get("description", "")).strip())
        parsed = _parse_feat(text) if text else None
        if not parsed:
            text_only += 1
            continue
        changes, notes, snippets, bucket = parsed
        with_change += bucket == 1
        with_note += bucket == 2
        entry = {"changes": changes, "contextNotes": notes, "review": True,
                 "_type": ftype, "_bucket": bucket, "_snippets": snippets}
        if comp is not None:
            nc, nn = comp.get(name.lower(), (0, 0))
            entry["_compendium_automated"] = bool(nc or nn)
            entry["_compendium_changes"] = nc
            entry["_compendium_contextnotes"] = nn
            redundant += bool(nc or nn)
        else:
            entry["_compendium_automated"] = None
        draft[name] = entry
    print(f"feats scanned: {total}")
    print(f"  with always-on change (bucket 1): {with_change}")
    print(f"  situational only      (bucket 2): {with_note}")
    print(f"  text-only (nothing parsed):       {text_only}")
    if comp is not None:
        print(f"  of drafted, already automated by compendium (likely skip): {redundant}")
    else:
        print("  compendium not found -> _compendium_automated stamped null (no double-apply guard)")
    return draft


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--compendium", type=Path, default=DEFAULT_COMPENDIUM,
                    help="every_feat.json for the double-apply guard (optional)")
    args = ap.parse_args()
    draft = build_draft(args.compendium)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(draft)} draft entries -> {args.out}")


if __name__ == "__main__":
    main()
