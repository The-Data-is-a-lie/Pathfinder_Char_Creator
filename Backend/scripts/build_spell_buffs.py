"""Scan the FoundryVTT spell compendium and emit a distributable BUFF for every spell that works as a
buff, for the Multi-Buff Distributor pipeline (see .claude/skills/multi-buff-distributor).

Reads every_spell.json (the module compendium; 3029 spells, names authoritative) and writes
<module>/templates/character_sheet_folder/spell_buffs.json:
    { "<Spell>": { "changes":[...], "contextNotes":[], "aura_range":int|null,
                   "only_others": false, "description": "<full rules text>" } }
consumed by the palette builder (as (UNAMED) buffs) and the module's addSpellBuffs() (as (TAG) buffs).

Spells carry NO structured mechanics, so `changes` are parsed CONSERVATIVELY from the description --
only a clean "+N <bonustype> bonus to/on <target>" -- and everything else is a description-only buff.
CL scaling is left in the description (the flat base is emitted; a distributed buff reads CL 0 on a
non-caster ally anyway). Curated attack/damage changes from spell_changes.json are layered in.

Usage:
    C:\\Python310\\python.exe Backend/scripts/build_spell_buffs.py [--out PATH]
"""
import argparse
import html
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODULE_DIR = Path(
    r"C:\Users\Daniel\AppData\Local\FoundryVTT\Data\modules\pf1e_random_char_generator"
    r"\templates\character_sheet_folder"
)
EVERY_SPELL = MODULE_DIR / "every_spell.json"
CURATED_CHANGES = REPO / "Backend" / "json" / "spells" / "spell_changes.json"
DEFAULT_OUT = MODULE_DIR / "spell_buffs.json"

_BONUS_TYPES = ("enhancement|deflection|morale|luck|resistance|competence|insight|sacred|profane|"
                "dodge|circumstance|alchemical|size|racial|untyped")
# "+N [foot] [type] bonus to|on <targets>"
_BONUS_RE = re.compile(
    r"\+(\d+)\s*(?:-?\s*foot|ft\.?)?\s*(" + _BONUS_TYPES + r")?\s*bonus\s+(?:to|on)\s+([^.;]{1,140})",
    re.IGNORECASE)
_ABILITIES = {"strength": "str", "dexterity": "dex", "constitution": "con",
              "intelligence": "int", "wisdom": "wis", "charisma": "cha"}
# Description-only buff signals (no clean +N bonus, but clearly a beneficial ongoing effect).
_BENEFIT_RE = re.compile(
    r"energy resistance|resist(?:ance to)? (?:acid|cold|fire|electricity|sonic) \d|damage reduction|"
    r"\bDR \d|fast healing|regeneration|fly speed|gain(?:s)? (?:a )?fly|blindsight|blindsense|"
    r"darkvision|true seeing|see invisibility|freedom of movement|invisibl|\bhaste|\bblur\b|"
    r"displacement|mirror image|protection from|temporary hit points|temporary hp|immunity to|"
    r"immune to|concealment|conceal|\bblink\b|spider climb|water breathing|\bfly\b", re.IGNORECASE)


def _strip(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(html or ""))).strip()


def _map_targets(phrase):
    """A comma/'and'-separated bonus target phrase -> list of (pf1 change target, ability?) tuples.
    If any ability score is present, emit ONLY the ability score(s) (pf1 derives AC/saves from it)."""
    p = phrase.lower()
    abilities = [pf for word, pf in _ABILITIES.items() if re.search(r"\b" + word + r"\b", p)]
    if abilities:
        return abilities
    out = []
    def add(t):
        if t not in out:
            out.append(t)
    if re.search(r"natural armor", p): add("nac")
    if re.search(r"armor class|\bac\b", p) and "natural armor" not in p: add("ac")
    if re.search(r"attack roll", p): add("attack")
    if re.search(r"weapon damage|damage roll", p): add("wdamage")
    if re.search(r"fortitude", p): add("fort")
    if re.search(r"reflex", p): add("ref")
    if re.search(r"will save", p): add("will")
    if re.search(r"saving throw|\bsaves\b", p) and not re.search(r"fortitude|reflex|will save", p): add("allSavingThrows")
    if re.search(r"skill check|\bskills\b", p): add("skills")
    if re.search(r"initiative", p): add("init")
    if re.search(r"\bcmd\b|combat maneuver defense", p): add("cmd")
    if re.search(r"\bcmb\b|combat maneuver (?:bonus|check)", p): add("cmb")
    if re.search(r"\bspeed\b", p): add("landSpeed")
    if re.search(r"spell resistance", p): add("sr")
    return out


def _parse_changes(desc):
    changes = []
    seen = set()
    for m in _BONUS_RE.finditer(desc):
        val, btype, phrase = m.group(1), (m.group(2) or "untyped").lower(), m.group(3)
        for tgt in _map_targets(phrase):
            key = (tgt, btype)
            if key in seen:
                continue
            seen.add(key)
            changes.append({"formula": str(int(val)), "target": tgt, "type": btype,
                            "operator": "add", "priority": 0})
    return changes


def _duration_bucket(action):
    """rounds | minutes | hours | other, from the spell's duration value string ('1 min./level' etc.).
    The `units` field is often 'spec', so parse the human-readable value."""
    val = str((action.get("duration") or {}).get("value") or "").lower()
    if re.search(r"\bround", val):
        return "rounds"
    if re.search(r"\bmin", val):
        return "minutes"
    if re.search(r"\bhour", val):
        return "hours"
    return "other"


def _range_value(rng):
    """Numeric value on the range object (ft/mi), else None."""
    v = str((rng or {}).get("value") or "").strip()
    m = re.match(r"\d+", v)
    return int(m.group()) if m else None


def _aura_from_range(units, value, cl):
    """The spell's range as a concrete number of feet at caster level `cl` (close/medium/long
    conventions). The distributor's Aura Range = how far the caster can place this buff."""
    if units == "personal":
        return 0
    if units == "touch":
        return 5
    if units == "close":
        return 25 + 5 * (cl // 2)
    if units == "medium":
        return 100 + 10 * cl
    if units == "long":
        return 400 + 40 * cl
    if units == "ft":
        return value or 0
    if units == "mi":
        return (value or 1) * 5280
    return 0   # seeText / spec / unlimited / unknown -> hand-distributed


# --------------------------------------------------------------------------- #
# spell stat-block formatting (School / Casting Time / Components / ... + Benefits)
# --------------------------------------------------------------------------- #
_SCHOOLS = {"abj": "Abjuration", "con": "Conjuration", "div": "Divination", "enc": "Enchantment",
            "evo": "Evocation", "ill": "Illusion", "nec": "Necromancy", "trs": "Transmutation",
            "uni": "Universal"}
_RANGE = {"touch": "touch", "personal": "personal", "close": "close (25 ft. + 5 ft./2 levels)",
          "medium": "medium (100 ft. + 10 ft./level)", "long": "long (400 ft. + 40 ft./level)",
          "unlimited": "unlimited", "seeText": "see text", "spec": "see text"}
_TARGET_READABLE = {"ac": "AC", "nac": "natural armor", "attack": "attack rolls",
    "wdamage": "weapon damage rolls", "damage": "damage rolls", "allSavingThrows": "all saving throws",
    "fort": "Fortitude saves", "ref": "Reflex saves", "will": "Will saves", "skills": "skill checks",
    "cmd": "CMD", "cmb": "CMB", "init": "initiative", "landSpeed": "speed", "sr": "spell resistance",
    "str": "Strength", "dex": "Dexterity", "con": "Constitution", "int": "Intelligence",
    "wis": "Wisdom", "cha": "Charisma"}
_ACT = {"standard": "1 standard action", "move": "1 move action", "swift": "1 swift action",
        "immediate": "1 immediate action", "full": "1 full-round action", "free": "1 free action",
        "round": "1 round"}


def _esc(s):
    return html.escape(str(s if s is not None else ""))


def _component_str(sy):
    c = sy.get("components") or {}
    parts = [x for x, on in (("V", c.get("verbal")), ("S", c.get("somatic")),
                             ("M", c.get("material")), ("F", c.get("focus")), ("DF", c.get("divineFocus")))
             if on]
    s = ", ".join(parts)
    mat = (sy.get("materials") or {}).get("value")
    if c.get("material") and mat:
        s += f" ({_esc(mat)})"
    return s or "&mdash;"


def _range_str(action):
    r = action.get("range") or {}
    u = r.get("units") or ""
    if u == "ft" and r.get("value"):
        return f"{_esc(r['value'])} ft."
    return _RANGE.get(u, _esc(u) if u else "&mdash;")


def _save_str(action):
    s = action.get("save") or {}
    d = s.get("description") or s.get("type") or ""
    if not d:
        return "none"
    return _esc(d) + (" (harmless)" if s.get("harmless") else "")


def _level_str(sy):
    cls = ((sy.get("learnedAt") or {}).get("class")) or {}
    if cls:
        return ", ".join(f"{_esc(k)} {v}" for k, v in sorted(cls.items()))
    lvl = sy.get("level")
    return f"any {lvl}" if lvl is not None else ""


def _benefits_str(changes):
    if not changes:
        return "<em>see description (no numeric bonus auto-parsed)</em>"
    groups, order = {}, []
    for c in changes:
        key = (str(c.get("formula")), c.get("type", "untyped"))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(_TARGET_READABLE.get(c.get("target"), c.get("target")))
    outs = []
    for val, typ in order:
        sign = "" if str(val).startswith("-") else "+"
        typ_s = "" if typ == "untyped" else f" {_esc(typ)}"
        outs.append(f"{sign}{_esc(val)}{typ_s} bonus to {_esc(', '.join(groups[(val, typ)]))}")
    return "; ".join(outs)


def _statblock_html(sy, action, level, changes):
    school = _SCHOOLS.get(str(sy.get("school") or "").lower(), _esc(sy.get("school") or "&mdash;"))
    sub = sy.get("subschool") or ""
    head = f"<strong>School</strong> {school}" + (f" ({_esc(sub)})" if sub else "")
    if level is not None:
        head += f" &bull; <strong>(level {level})</strong>"
    rows = [f"<p>{head}</p>"]
    lvls = _level_str(sy)
    if lvls:
        rows.append(f"<p><strong>Level</strong> {lvls}</p>")
    act = action.get("activation") or {}
    rows.append(f"<p><strong>Casting Time</strong> {_ACT.get(act.get('type'), _esc(act.get('type') or '&mdash;'))}</p>")
    rows.append(f"<p><strong>Components</strong> {_component_str(sy)}</p>")
    tgt = (action.get("target") or {}).get("value")
    rline = f"<strong>Range</strong> {_range_str(action)}"
    if tgt:
        rline += f"; <strong>Target</strong> {_esc(tgt)}"
    rows.append(f"<p>{rline}</p>")
    dur = (action.get("duration") or {}).get("value") or "&mdash;"
    rows.append(f"<p><strong>Duration</strong> {_esc(dur)}; <strong>Saving Throw</strong> {_save_str(action)}; "
                f"<strong>Spell Resistance</strong> {'yes' if sy.get('sr') else 'no'}</p>")
    return "".join(rows)


def build(out_path):
    spells = json.loads(EVERY_SPELL.read_text(encoding="utf-8"))
    try:
        curated = json.loads(CURATED_CHANGES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        curated = {}
    cur_norm = {re.sub(r"\s+", " ", k).strip().lower(): v for k, v in curated.items()}
    out = {}
    n_changes = n_desc = n_area = 0
    for s in spells:
        if not isinstance(s, dict):
            continue
        name = s.get("name")
        sy = s.get("system", {}) or {}
        action = (sy.get("actions") or [{}])[0]
        dur_units = (action.get("duration") or {}).get("units", "")
        if dur_units == "inst":                      # instantaneous -> not a lasting buff
            continue
        raw_html = sy.get("description", {}).get("value", "") if isinstance(sy.get("description"), dict) else ""
        text = _strip(raw_html)      # stripped plain text for parsing / detection
        if not text:
            continue
        changes = _parse_changes(text)
        is_buff = bool(changes) or bool(_BENEFIT_RE.search(text))
        if not is_buff:
            continue
        # Layer curated attack/damage changes (accurate) for targets we didn't already emit.
        cur = cur_norm.get(re.sub(r"\s+", " ", str(name)).strip().lower())
        if cur and isinstance(cur.get("changes"), list):
            have = {(c["target"], c.get("type", "untyped")) for c in changes}
            for c in cur["changes"]:
                if (c.get("target"), c.get("type", "untyped")) not in have:
                    changes.append({"formula": str(c.get("formula", "0")), "target": c.get("target", ""),
                                    "type": c.get("type", "untyped"), "operator": "add", "priority": 0})
        rng = action.get("range") or {}
        r_units = rng.get("units") or ""
        r_value = _range_value(rng)
        lvl = sy.get("level")
        lvl_int = int(lvl) if isinstance(lvl, (int, float)) else None
        # Full formatted description: spell stat block + the ORIGINAL description HTML + Benefits.
        formatted = (_statblock_html(sy, action, lvl_int, changes) + "<hr>" + (raw_html or "")
                     + f"<p><strong>Benefits:</strong> {_benefits_str(changes)}</p>")
        out[name] = {"changes": changes, "contextNotes": [], "only_others": False,
                     "level": lvl_int, "duration_bucket": _duration_bucket(action),
                     "range_units": r_units, "range_value": r_value,
                     # aura_range = the spell's range at a reference CL 10 (palette default; NPCs recompute).
                     "aura_range": _aura_from_range(r_units, r_value, 10),
                     "description": formatted}
        n_changes += bool(changes)
        n_desc += not bool(changes)
        n_area += rng is not None
    out = dict(sorted(out.items()))
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"spell buffs: {len(out)} ({n_changes} with changes, {n_desc} description-only, {n_area} area/aura)")
    print(f"wrote -> {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    build(ap.parse_args().out)


if __name__ == "__main__":
    main()
