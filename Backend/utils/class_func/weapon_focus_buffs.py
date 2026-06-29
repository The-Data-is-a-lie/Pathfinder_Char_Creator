"""Weapon Focus / Weapon Specialization family -> cumulative pf1 attack/damage changes.

The feat-tax (utils/class_func/feat_tax.py) bundles the whole chain onto the BASE "Weapon Focus"
primary: Greater Weapon Focus, Weapon Specialization, and Greater Weapon Specialization are granted
free and rendered as one merged feat item ("Weapon Focus > Greater Weapon Focus > ...") rather than
as separate items. So their numeric bonuses can't be applied per-child (the children aren't their own
items) -- they must be SUMMED onto the primary's change.

The bonus is emitted GLOBAL (target ``attack`` for the focus line, ``wdamage`` for the specialization
line). The generator equips a single main weapon, so a global attack/weapon-damage bonus matches that
weapon's line on the sheet; an NPC who also wields a secondary weapon would see the bonus there too
(a minor over-application we accept rather than weapon-scoping every feat). main_test.py folds the
result into ``feat_changes_dict``; the FoundryVTT module overlays it onto the Weapon Focus item.
"""
import re

# family member (normalized name) -> (pf1 change target, per-feat bonus)
_FAMILY = {
    "weapon focus": ("attack", 1),
    "greater weapon focus": ("attack", 1),
    "weapon specialization": ("wdamage", 2),
    "greater weapon specialization": ("wdamage", 2),
}


def _norm(s):
    return re.sub(r"\s+", " ", str(s).lower().strip().replace("-", " "))


def _change(target, value):
    return {"formula": str(int(value)), "target": target, "type": "untyped", "operator": "add", "priority": 0}


def weapon_focus_changes(render_feat_names, tax_dicts):
    """Return {placed_primary_name: {"changes":[...], "contextNotes":[]}} for the Weapon Focus family.

    ``render_feat_names``: the placed feat names (only the primary "Weapon Focus" appears; the chain is
    bundled in the tax dicts). ``tax_dicts``: an iterable of {primary_name: [bundled child names]}.
    For each placed family feat, sum its own + its bundled family children's bonuses (attack vs weapon
    damage) and emit one cumulative change set keyed by the placed primary's name."""
    combined = {}
    for d in tax_dicts:
        for k, v in (d or {}).items():
            combined.setdefault(k, []).extend(v or [])

    out = {}
    for name in dict.fromkeys(render_feat_names):
        if _norm(name) not in _FAMILY:
            continue
        atk = dmg = 0
        for member in [name] + list(combined.get(name, [])):
            fam = _FAMILY.get(_norm(member))
            if not fam:
                continue
            target, value = fam
            if target == "attack":
                atk += value
            else:
                dmg += value
        changes = []
        if atk:
            changes.append(_change("attack", atk))
        if dmg:
            changes.append(_change("wdamage", dmg))
        if changes:
            out[name] = {"changes": changes, "contextNotes": []}
    return out
