"""Draft-generate pf1 buffs for SPHERES talents -- combat (Spheres of Might) or magic (Spheres of
Power) -- as a manual tool, never part of the generation pipeline.

Reads Backend/json/class_data/spheres/spheres_of_might_enriched.json (``--system might``, default) or
spheres_of_power.json (``--system power``) -- both shaped {sphere: {talent: {benefit, description,
type, ...}}} -- and applies CONSERVATIVE regexes to each talent's benefit text to extract:
  - SELF-BUFF flat bonuses ("you gain a +N <type> bonus to/on <target>")  -> changes / contextNotes,
  - PER-HIT weapon riders ("deal an additional NdM damage", "+N to attack") -> modifiers (might only;
    these belong on the main weapon's attack action as default-off conditionals, like maneuvers).

The hard part for Spheres of Might is that most talents affect the TARGET, not the practitioner
("the target gains +2", "the creature takes a -2 penalty"), and most are situational/active. So the
self-buff pass requires a first-person subject ("YOU gain ...") near the bonus and skips everything
else -- expect FEW high-confidence entries. That is the correct outcome: most talents stay
description-only.

Output is a DRAFT nested {sphere: {Talent Name: {changes, contextNotes, modifiers, review, ...}}};
every entry carries "review": true + matched snippets. Hand-curate the SELF-BUFF parts into
Backend/json/class_data/spheres/combat_talent_changes.json (consumed by _talent_item in
utils/class_func/spheres.py) and the WEAPON-RIDER parts into the FoundryVTT module's
combat_talent_changes.json (parallel to maneuver_changes.json). Strip review/_* keys; keep only what
you trust.

Usage:
    C:\\Python310\\python.exe Backend/scripts/build_talent_changes.py [--system might|power] [--out PATH]
"""
import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPHERES_DIR = REPO / "Backend" / "json" / "class_data" / "spheres"
SOURCES = {
    "might": SPHERES_DIR / "spheres_of_might_enriched.json",
    "power": SPHERES_DIR / "spheres_of_power.json",
}
OUTPUTS = {
    "might": SPHERES_DIR / "combat_talent_changes.draft.json",
    "power": SPHERES_DIR / "magic_talent_changes.draft.json",
}

_BONUS_TYPES = ('dodge|morale|insight|luck|competence|circumstance|profane|sacred|'
                'deflection|resistance|shield|enhancement|alchemical|racial|size|trait')
_DMG_TYPES = ('fire|cold|acid|electricity|sonic|force|negative|positive|'
              'bludgeoning|piercing|slashing|untyped')

_TARGETS = [
    (r'armor class|\bac\b', 'ac'),
    (r'attack rolls', 'attack'),
    (r'(?:weapon )?damage rolls', 'wdamage'),
    # Specific saves BEFORE the generic "saving throws" so "all Will saving throws" -> will.
    (r'fortitude sav(?:es|ing throws)', 'fort'),
    (r'ref\s*lex sav(?:es|ing throws)', 'ref'),  # scrape sometimes writes "Reflex" as "Ref lex"
    (r'will sav(?:es|ing throws)', 'will'),
    (r'all saving throws|saving throws|all saves', 'allSavingThrows'),
    (r'\bcmd\b|combat maneuver defense', 'cmd'),
    (r'\bcmb\b|combat maneuver (?:bonus|checks)', 'cmb'),
    (r'initiative(?: checks)?', 'init'),
    (r'(?:base land|movement|land) speed', 'landSpeed'),
]

# Self-buff flat bonus, but ONLY when the feat-holder is the subject ("you gain/have/receive ...").
_SELF_FLAT_RE = re.compile(
    r'\byou (?:gain|have|receive|possess|enjoy|add)\b[^.]{0,40}?'
    r'\+(\d+)\s*(' + _BONUS_TYPES + r')?\s*bonus\s+(?:to|on)\s+([^.,;]{1,60})',
    re.IGNORECASE)
_COND_RE = re.compile(
    r'\b(against|vs\.?|versus|when|while|whenever|if|during|as long as|made to)\b', re.IGNORECASE)

# Per-hit weapon riders (might only); the practitioner's own attack adds damage / to-hit.
_DMG_DICE_RE = re.compile(
    r'(?:additional|extra|deals?|inflicts?)[^.]{0,40}?\+?(\d+d\d+)\s*'
    r'(?:points?\s+of\s+)?(' + _DMG_TYPES + r')?\s*damage', re.IGNORECASE)
_ATK_RE = re.compile(
    r'\+(\d+)\s*(' + _BONUS_TYPES + r')?\s*bonus\s+(?:to|on)\s+'
    r'(?:his|her|its|their|your|the)?\s*attack rolls?', re.IGNORECASE)


def _display_name(name):
    name = re.sub(r"\s*\[[^\]]*\]\s*", " ", str(name)).strip()
    return " ".join(w[:1].upper() + w[1:] for w in name.split())


def _match_target(phrase):
    p = phrase.strip().lower()
    for pat, target in _TARGETS:
        if re.search(pat, p):
            return target
    return None


def _match_targets(phrase):
    out = []
    for part in re.split(r',|\band\b|\bto\b', phrase):
        t = _match_target(part)
        if t and t not in out:
            out.append(t)
    return out


def _parse_talent(text, system):
    changes, notes, modifiers, snippets = [], [], [], []
    for m in _SELF_FLAT_RE.finditer(text):
        base, btype, phrase = int(m.group(1)), m.group(2), m.group(3)
        targets = _match_targets(phrase)
        if not targets:
            continue
        snippets.append(m.group(0).strip())
        if _COND_RE.search(m.group(0)):
            notes.append({"text": m.group(0).strip(), "_target": targets[0]})
        else:
            for t in targets:
                changes.append({"formula": str(base), "target": t,
                                "type": (btype or "untyped").lower(),
                                "operator": "add", "priority": 0})
    if system == "might":
        dm = _DMG_DICE_RE.search(text)
        if dm:
            dtype = dm.group(2)
            modifiers.append({"formula": dm.group(1), "target": "damage", "subTarget": "allDamage",
                              "type": "untyped",
                              "damageType": [dtype] if dtype and dtype != "untyped" else [],
                              "critical": "normal"})
            snippets.append(dm.group(0).strip())
        am = _ATK_RE.search(text)
        if am:
            modifiers.append({"formula": am.group(1), "target": "attack", "subTarget": "allAttack",
                              "type": (am.group(2) or "untyped").lower(),
                              "damageType": [], "critical": "normal"})
            snippets.append(am.group(0).strip())
    if not (changes or notes or modifiers):
        return None
    return changes, notes, modifiers, snippets


def build_draft(system):
    data = json.loads(SOURCES[system].read_text(encoding="utf-8"))
    draft = {}
    total = self_buff = weapon_rider = situational = text_only = 0
    for sphere, talents in data.items():
        if not isinstance(talents, dict):
            continue
        for tname, rec in talents.items():
            if not isinstance(rec, dict):
                continue
            total += 1
            text = (str(rec.get("benefit", "")).strip() or str(rec.get("description", "")).strip())
            parsed = _parse_talent(text, system) if text else None
            if not parsed:
                text_only += 1
                continue
            changes, notes, modifiers, snippets = parsed
            self_buff += bool(changes)
            situational += bool(notes) and not changes
            weapon_rider += bool(modifiers)
            entry = {"changes": changes, "contextNotes": notes, "review": True,
                     "_sphere": _display_name(sphere), "_type": rec.get("type", "base"),
                     "_snippets": snippets}
            if system == "might":
                entry["modifiers"] = modifiers
            draft.setdefault(_display_name(sphere), {})[_display_name(tname)] = entry
    print(f"[{system}] talents scanned: {total}")
    print(f"  self-buff change:   {self_buff}")
    print(f"  situational only:   {situational}")
    if system == "might":
        print(f"  weapon rider:       {weapon_rider}")
    print(f"  text-only:          {text_only}")
    return draft


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--system", choices=("might", "power"), default="might")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    out = args.out or OUTPUTS[args.system]
    draft = build_draft(args.system)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    entries = sum(len(v) for v in draft.values())
    print(f"wrote {entries} draft entries across {len(draft)} spheres -> {out}")


if __name__ == "__main__":
    main()
