"""Draft-generate + WORKLIST-slice the per-roll conditional data for Spheres talents (manual tool,
never part of the generation pipeline).

Two jobs, mirroring build_maneuver_changes.py for Path of War:

  1. DRAFT (default) -- conservative regexes over each talent's benefit text extract the primary
     damage/attack numbers (-> `modifiers`) and a save/condition/contingency skeleton (-> `rider`,
     every number in [[ ]]) into a nested draft:
         { "<Sphere>": { "<Talent>": { "modifiers": [...], "rider": "...", "review": true, ... } } }
     Output: Backend/json/class_data/spheres/combat_talent_conditionals.draft.json (--system might)
          or magic_talent_conditionals.draft.json (--system power). This is a SEED / palette fallback;
     the authoritative curation is done by hand (see _spheres_generator/).

  2. WORKLIST (--dump-worklist DIR) -- slices the huge dataset into one small, attack-relevant file
     per sphere: <DIR>/<system>/<Sphere>.json = {sphere, system, dc_formula, talents:[{name, type,
     prerequisites, benefit, _seed}]}. Each file is the input for ONE curation agent, so an agent
     reads ~30-100 talents instead of the 1.4 MB dataset. Only talents whose text looks attack-relevant
     (damage dice / save / bleed / precision / martial-focus attack / an attack bonus, or ANY
     Destruction talent) are included; pure-utility talents are intentionally left out (they stay
     description-only). Over-inclusion is fine -- a curator marks a false positive `{"skip": "..."}`.

Conventions the seeds/curation follow (docs/spheres_conditional_decision_rules.md):
  * Power save DC   = [[ 10 + floor(@spheres.cl.total / 2) + @spheres.cam ]]
  * Might sphere DC = [[ 10 + floor(@attributes.bab.total / 2) + @spheres.pam ]]
  * BAB scaling  "NdM (+ NdM) for every K ... base attack bonus" -> NdM + (floor(@attributes.bab.total / K))dM
  * CL scaling   "1d6 ... per odd caster level"                  -> (ceil(@spheres.cl.total / 2))d6
  *              "... per caster level"                          -> (@spheres.cl.total)dM
  * Clean this-hit damage/attack -> modifiers[] (plain formula; the module appends a [Source] label);
    saves / conditions / durations / bleed / martial-focus contingencies -> rider text, numbers in [[ ]].

Usage:
    C:\\Python310\\python.exe Backend/scripts/build_talent_conditionals.py [--system might|power] [--out PATH]
    C:\\Python310\\python.exe Backend/scripts/build_talent_conditionals.py --dump-worklist DIR
"""
import argparse
import json
import re
import sys as _sys
from pathlib import Path

_sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_talent_conditionals import is_cost_only   # two-prong gate: never seed a payload-less cost
import conditional_clauses as cc                          # shared six-detail clause builders

REPO = Path(__file__).resolve().parents[2]
SPHERES_DIR = REPO / "Backend" / "json" / "class_data" / "spheres"
SOURCES = {
    "might": SPHERES_DIR / "spheres_of_might_enriched.json",
    "power": SPHERES_DIR / "spheres_of_power.json",
}
OUTPUTS = {
    "might": SPHERES_DIR / "combat_talent_conditionals.draft.json",
    "power": SPHERES_DIR / "magic_talent_conditionals.draft.json",
}

DC_POWER = "[[ 10 + floor(@spheres.cl.total / 2) + max(@abilities.int.mod, @abilities.wis.mod, @abilities.cha.mod) ]]"
DC_MIGHT = "[[ 10 + floor(@attributes.bab.total / 2) + max(@abilities.int.mod, @abilities.wis.mod, @abilities.cha.mod) ]]"

_DMG_TYPES = ('fire|cold|acid|electricity|electric|sonic|force|negative|positive|'
              'bludgeoning|piercing|slashing|untyped')
_WORD_NUMS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
_SAVES = {"reflex": "Reflex", "fortitude": "Fortitude", "will": "Will"}

_DICE_RE = re.compile(r"\d+d\d+")
# "an additional 1d4 bleed/precision/fire damage ..."  (primary this-hit dice)
_DMG_DICE_RE = re.compile(
    r'(?:additional|extra|deals?|inflicts?|takes? an additional|suffers?)[^.]{0,50}?'
    r'\+?(\d+d\d+)\s*(?:points?\s+of\s+)?(' + _DMG_TYPES + r'|precision|bleed)?\s*damage',
    re.IGNORECASE)
# "+1d6 ... for every 5 points of base attack bonus"  (BAB dice scaling of the SAME die)
_BAB_DICE_RE = re.compile(
    r'(\d+d\d+)[^.]{0,80}?for every (\w+)\s*(?:points?\s*of\s*)?base attack bonus', re.IGNORECASE)
# "1d6 ... per odd caster level" / "... per caster level"
_CL_ODD_RE = re.compile(r'(\d+d\d+)[^.]{0,40}?per odd caster level', re.IGNORECASE)
_CL_EACH_RE = re.compile(r'(\d+d\d+)[^.]{0,40}?per caster level', re.IGNORECASE)
_ATK_RE = re.compile(
    r'\+(\d+)\s*(dodge|morale|insight|luck|competence|circumstance|profane|sacred|deflection|'
    r'resistance|enhancement|alchemical|racial|size)?\s*bonus\s+(?:to|on)\s+'
    r'(?:his|her|its|their|your|the)?\s*attack rolls?', re.IGNORECASE)
_SAVE_RE = re.compile(r'\b(reflex|fortitude|will)\b\s+sav', re.IGNORECASE)
_MARTIAL_FOCUS_RE = re.compile(r'expend(?:s|ing)?\s+(?:your|their|his|her)?\s*martial focus', re.IGNORECASE)
_SPECIAL_ATTACK_RE = re.compile(r'special attack action', re.IGNORECASE)
_ATTACK_OR_AOO_RE = re.compile(r'attack action or an? attack of opportunity', re.IGNORECASE)
_SPELL_POINT_RE = re.compile(r'spend(?:s|ing)?\s+(?:a|\d+)\s+spell point', re.IGNORECASE)

# Attack-relevance heuristic for the worklist (over-include; curators prune).
_RELEVANT_RE = re.compile(
    r'\d+d\d+|\bbleed\b|precision damage|saving throw|\bsave\b|attack roll|'
    r'martial focus|special attack action|attack of opportunity|\bblast\b|\bdamage\b', re.IGNORECASE)
# A "strike" / on-attack rider: strikes apply on ANY attack roll, so they are always conditional-worthy
# (Destruction "Energy Strike", Death "Vampiric Strike", Enhancement "Crippling Strike", ...). Detect by
# the talent name or the tell-tale "in conjunction with an attack" / "deliver … through a touch attack"
# phrasing. See docs/spheres_conditional_decision_rules.md.
_STRIKE_RE = re.compile(
    r'\bstrike\b|make a (?:single )?(?:weapon |melee |ranged )?attack in conjunction|'
    r'deliver[^.]{0,60}?through a (?:melee |ranged )?(?:touch )?attack|'
    r'as part of (?:an|your|a) (?:melee |ranged )?(?:weapon |touch )?attack|'
    r'when you (?:hit|strike|damage) (?:a|an|the|your)|'
    r'make a (?:melee|ranged|touch) attack', re.IGNORECASE)
# A single-target debuff / condition / ability damage -> likely conditional (soft rule).
_DEBUFF_RE = re.compile(
    r'\bpenalty\b|sickened|staggered|shaken|dazed|dazzled|blinded|deafened|entangled|'
    r'fatigued|exhausted|nauseated|frightened|panicked|paralyzed|stunned|\bprone\b|cowering|confused|'
    r'\bcursed\b|\bbleed\b|negative level|ability damage|ability drain', re.IGNORECASE)


def _hint(name, benefit):
    """Routing suggestion for the curator: strike (always a conditional) / damage / debuff / maybe-skip."""
    if re.search(r'\bstrike\b', name, re.IGNORECASE) or _STRIKE_RE.search(benefit):
        return "strike"
    if re.search(r'\d+d\d+', benefit):
        return "damage"
    if _DEBUFF_RE.search(benefit):
        return "debuff"
    return "maybe-skip"


def _display_name(name):
    """Match spheres.py _display_name: strip [source] tags, upper-case each word's first letter while
    preserving the rest (so 'knight's blast' -> "Knight's Blast", 'dual wielding' -> 'Dual Wielding')."""
    name = re.sub(r"\s*\[[^\]]*\]\s*", " ", str(name)).strip()
    return " ".join(w[:1].upper() + w[1:] for w in name.split())


def _num(word):
    word = str(word).strip().lower()
    if word.isdigit():
        return int(word)
    return _WORD_NUMS.get(word)


def _damage_seed(text, system):
    """Best-effort primary damage modifier(s) from the benefit text. Returns a list of modifier dicts."""
    mods = []
    # CL-scaled blast-ish dice first (power), then BAB-scaled (might), then a flat additional die.
    m = _CL_ODD_RE.search(text)
    if m and system == "power":
        die = m.group(1).split("d")[1]
        mods.append(_dmg_mod(f"(ceil(@spheres.cl.total / 2))d{die}", None))
        return mods
    m = _BAB_DICE_RE.search(text)
    if m:
        base = m.group(1)
        div = _num(m.group(2))
        die = base.split("d")[1]
        formula = f"{base} + (floor(@attributes.bab.total / {div}))d{die}" if div else base
        dtype = _dice_dtype(text, base)
        mods.append(_dmg_mod(formula, dtype))
        return mods
    m = _DMG_DICE_RE.search(text)
    if m:
        dtype = m.group(2)
        # bleed/precision are NOT clean damage modifiers -> leave for the rider (return none here).
        if dtype and dtype.lower() in ("bleed",):
            return mods
        mods.append(_dmg_mod(m.group(1), None if (not dtype or dtype.lower() in ("precision", "untyped")) else dtype.lower()))
    return mods


def _dice_dtype(text, base):
    m = re.search(re.escape(base) + r'\s*(?:points?\s+of\s+)?(' + _DMG_TYPES + r')', text, re.IGNORECASE)
    return m.group(1).lower() if m else None


def _dmg_mod(formula, dtype):
    dt = [dtype] if dtype and dtype != "untyped" else []
    if dtype == "electric":
        dt = ["electricity"]
    return {"formula": formula, "target": "damage", "subTarget": "allDamage",
            "type": "untyped", "damageType": dt,
            "critical": "nonCrit" if _DICE_RE.search(formula) else "normal"}


def _rider_seed(text, system):
    """Best-effort rider skeleton: contingencies first, then a save with the system DC. Numbers in [[ ]]
    where trivial; the curator finishes it."""
    parts = []
    if _MARTIAL_FOCUS_RE.search(text):
        parts.append("expend martial focus")
    if _SPECIAL_ATTACK_RE.search(text):
        parts.append("special attack action")
    elif _ATTACK_OR_AOO_RE.search(text):
        parts.append("attack action or attack of opportunity only")
    sp = cc.talent_spellpoint_count(text)                # REAL count from the benefit (not always 1)
    if sp is not None:
        parts.append(f"spend [[{sp}]] spell point{'s' if sp != 1 else ''}")
    rng = cc.talent_range_clause(text)                   # a Range clause when clearly derivable
    if rng:
        parts.append(rng)
    sv = _SAVE_RE.search(text)
    if sv:
        dc = DC_POWER if system == "power" else DC_MIGHT
        parts.append(f"{_SAVES[sv.group(1).lower()]} Save {dc} negates")
    # bleed rider
    bm = re.search(r'(\d+d\d+)\s*bleed', text, re.IGNORECASE)
    if bm:
        parts.append(f"on hit the target takes [[{bm.group(1)}]] bleed damage")
    return "; ".join(parts)


def _seed(text, system):
    return {"modifiers": _damage_seed(text, system), "rider": _rider_seed(text, system)}


def build_draft(system):
    data = json.loads(SOURCES[system].read_text(encoding="utf-8"))
    draft, total, kept = {}, 0, 0
    for sphere, talents in data.items():
        if not isinstance(talents, dict):
            continue
        for tname, rec in talents.items():
            if not isinstance(rec, dict):
                continue
            total += 1
            text = str(rec.get("benefit", "") or rec.get("description", "")).strip()
            seed = _seed(text, system)
            # A seed with no real payload -- a bare cost ("expend martial focus" / "spend [[1]] spell
            # point") -- is NOT a conditional (two-prong rule; validate_talent_conditionals).
            if is_cost_only({"modifiers": seed["modifiers"], "rider": seed["rider"]}):
                continue
            kept += 1
            entry = {"modifiers": seed["modifiers"], "review": True,
                     "_type": rec.get("type", "base")}
            if seed["rider"]:
                entry["rider"] = seed["rider"]
            draft.setdefault(_display_name(sphere), {})[_display_name(tname)] = entry
    print(f"[{system}] talents scanned: {total}; seeded draft entries: {kept}")
    return draft


def dump_worklist(out_dir):
    for system, src in SOURCES.items():
        data = json.loads(src.read_text(encoding="utf-8"))
        sysdir = Path(out_dir) / system
        sysdir.mkdir(parents=True, exist_ok=True)
        dc = DC_POWER if system == "power" else DC_MIGHT
        total_rel = 0
        for sphere, talents in data.items():
            if not isinstance(talents, dict):
                continue
            rows = []
            for tname, rec in talents.items():
                if not isinstance(rec, dict):
                    continue
                text = str(rec.get("benefit", "") or rec.get("description", "")).strip()
                is_destruction = _display_name(sphere).lower() == "destruction"
                if not (is_destruction or _RELEVANT_RE.search(text)
                        or _STRIKE_RE.search(text) or _DEBUFF_RE.search(text)):
                    continue
                rows.append({
                    "name": _display_name(tname),
                    "type": rec.get("type", "base"),
                    "prerequisites": rec.get("prerequisites", ""),
                    "benefit": text,
                    "_hint": _hint(_display_name(tname), text),
                    "_seed": _seed(text, system),
                })
            if not rows:
                continue
            total_rel += len(rows)
            payload = {"sphere": _display_name(sphere), "system": system,
                       "dc_formula": dc, "talents": rows}
            (sysdir / f"{_display_name(sphere)}.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        n_files = len(list(sysdir.glob("*.json")))
        print(f"[{system}] wrote {n_files} sphere worklist file(s), {total_rel} attack-relevant talents -> {sysdir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--system", choices=("might", "power"), default="might")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--dump-worklist", type=Path, default=None,
                    help="instead of a draft, slice both systems into per-sphere worklist files under DIR.")
    args = ap.parse_args()
    if args.dump_worklist:
        dump_worklist(args.dump_worklist)
        return
    out = args.out or OUTPUTS[args.system]
    draft = build_draft(args.system)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    entries = sum(len(v) for v in draft.values())
    print(f"wrote {entries} draft entries across {len(draft)} spheres -> {out}")


if __name__ == "__main__":
    main()
