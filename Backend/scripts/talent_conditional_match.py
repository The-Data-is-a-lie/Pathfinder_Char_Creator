"""Python port of the applier macro's sphere-talent match (apply-conditionals.macro.js): given an
actor's known sphere talents, decide which get a conditional attached from the curated dicts. Kept in
sync with the JS `norm` / `stripSource` / lookup order so the tests observe the real attach behavior.
"""
import re


def norm(s):
    return re.sub(r"\s+", " ", str(s).lower().replace("'", "").replace("’", "").replace("`", "")).strip()


def strip_source(name):
    """"Ragdoll Swing (impale)" / "Foo [apoc]" -> base name (a trailing parenthetical/bracket tag)."""
    return re.sub(r"\s*[\(\[][^\)\]]*[\)\]]\s*$", "", str(name)).strip()


def _table(d):
    out = {}
    for sphere, talents in (d or {}).items():
        k = norm(sphere)
        out.setdefault(k, {})
        for talent, entry in (talents or {}).items():
            out[k][norm(talent)] = entry
    return out


def match_actor(talents, magic, combat):
    """[{name, sphere, matched, has_modifier, rider}] for each {name, sphere} the actor knows.
    Lookup order mirrors the macro: combat then magic, exact norm then source-stripped norm."""
    mt, ct = _table(magic), _table(combat)
    out = []
    for t in talents:
        name = t.get("name", "")
        sphere = t.get("sphere", "")
        sk = norm(sphere)
        nk, nk2 = norm(name), norm(strip_source(name))
        entry = ((ct.get(sk) or {}).get(nk) or (mt.get(sk) or {}).get(nk)
                 or (ct.get(sk) or {}).get(nk2) or (mt.get(sk) or {}).get(nk2))
        mods = (entry or {}).get("modifiers") if entry else None
        out.append({
            "name": name,
            "sphere": sphere,
            "matched": entry is not None,
            "has_modifier": bool(isinstance(mods, list) and len(mods) > 0),
            "rider": str((entry or {}).get("rider", "")) if entry else "",
        })
    return out
