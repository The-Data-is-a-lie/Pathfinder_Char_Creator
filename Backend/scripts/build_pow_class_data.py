"""One-off builder: merge the Path of War classes into Backend/json/class_data.json.

Covers the six base PoW classes ('base' tree) plus the Metzofitz homebrew Medic ('metzofitz'
tree). Maps the scraped Backend/json/class_data/path_of_war/path_of_war_classes.json onto the
canonical class_data.json entry shape consumed by the generator:
    main_stat / bab / casting level / role / alignment / hit die /
    skill points at each level / weapon and armor proficiency / <class features...>
Feature keys must come AFTER 'weapon and armor proficiency' (get_class_abilities slices there).
Hand-supplied constants (main_stat, skill points) verified against the d20pfsrd class pages.

Idempotent: re-running replaces the six entries in place. Run from repo root:
    C:\\Python310\\python.exe Backend/scripts/build_pow_class_data.py
"""
import json
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "Backend/json/class_data/path_of_war/path_of_war_classes.json"
TARGET = ROOT / "Backend/json/class_data.json"

# Verified: stalker 6 + Int; warlord/warder/harbinger/mystic/zealot 4 + Int (d20pfsrd class pages).
# Medic (Metzofitz homebrew): Wis-based healer, 4 + Int, M BAB, d8 -- confirmed from the imported
# Foundry class item (savingThrows fort/will high, ref low; Heal/Sense Motive/Perception skill set).
CONSTANTS = {
    "stalker":   {"main_stat": "wis", "skill points at each level": "6"},
    "warlord":   {"main_stat": "cha", "skill points at each level": "4"},
    "warder":    {"main_stat": "int", "skill points at each level": "4"},
    "harbinger": {"main_stat": "int", "skill points at each level": "4"},
    "mystic":    {"main_stat": "wis", "skill points at each level": "4"},
    "zealot":    {"main_stat": "cha", "skill points at each level": "4"},
    "medic":     {"main_stat": "wis", "skill points at each level": "4"},
}

# Source keys that are NOT class features: structural fields, plus the maneuver/stance rules
# text (the generator exports maneuvers/stances separately via the path_of_war module).
SKIP_PREFIXES = (
    "roles", "hd", "bab", "class features", "weapon and armor prof",
    "maneuvers", "stances known",
)

SUFFIX_RE = re.compile(r"\s*\((su|ex|sp)\)\s*$", re.IGNORECASE)


def build_entry(name, src):
    out = OrderedDict()
    out["main_stat"] = CONSTANTS[name]["main_stat"]
    out["bab"] = src["bab"]
    out["casting level"] = "none"
    out["role"] = src.get("Roles", "")
    out["alignment"] = "Any."
    out["hit die"] = src["HD"].strip() + "."
    out["starting wealth"] = "3d6 x 10 gp (average 105 gp)."
    out["skill points at each level"] = CONSTANTS[name]["skill points at each level"]
    prof_key = next(k for k in src if k.lower().startswith("weapon and armor prof"))
    out["weapon and armor proficiency"] = src[prof_key]
    for key, value in src.items():
        if any(key.lower().startswith(p) for p in SKIP_PREFIXES):
            continue
        feature = SUFFIX_RE.sub("", key).lower().strip()
        out[feature] = value
    return out


def main():
    # Merge the 'base' and 'metzofitz' trees under lower-cased keys (source casing is mixed,
    # e.g. metzofitz "medic" lower-case vs "Epilektoi" capitalized).
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    source = {}
    for tree in ("base", "metzofitz"):
        for k, v in raw.get(tree, {}).items():
            source[k.lower().strip()] = v
    target = json.loads(TARGET.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
    for name in CONSTANTS:
        if name not in source:
            raise SystemExit(f"class {name!r} missing from {SOURCE}")
        target[name] = build_entry(name, source[name])
        features = [k for k in target[name]][10:]
        print(f"{name}: bab={target[name]['bab']} hd={target[name]['hit die']} "
              f"features={len(features)} ({', '.join(features[:4])}, ...)")
    TARGET.write_text(json.dumps(target, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {TARGET}")


if __name__ == "__main__":
    main()
