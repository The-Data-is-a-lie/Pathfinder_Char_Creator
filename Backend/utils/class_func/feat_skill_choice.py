"""Feat-selection house-rule helpers (campaign-specific), from docs/homebrew_rules.md §4 / §1.

1. **Free combat feats.** Combat Expertise, Power Attack, Deadly Aim, and Piranha Strike are FREE for
   anyone with BAB >= 1, so the generator never spends a feat slot on them. `main_test.py` seeds them
   into ``character.chooseable`` before feat selection (so no chooser picks them, and feats that list
   them as a prerequisite still qualify — ``no_prereq_loop`` treats chooseable as owned).
   ``filter_free_feats`` is a safety net for bonus-feat sources that bypass the chooseable pool.

2. **Skill-choosing feats target professions.** Skill Focus / Prodigy (feats that pick a skill) are
   pointed at the character's professions, highest-rank first (spreading across professions), and
   their numeric bonus is recorded on the chosen profession so
   ``profession_abilities.build_profession_ability_items`` can fold it into that profession's Rank-5
   item. Surplus picks (more than there are professions) fall back to the best regular skill.
"""
from utils import data

# 1) Free-at-BAB>=1 feats. Seeded into chooseable + filtered as a safety net.
FREE_AT_BAB1 = ["Power Attack", "Deadly Aim", "Combat Expertise", "Piranha Strike"]
_FREE_AT_BAB1_NORM = {f.lower() for f in FREE_AT_BAB1}


def _feat_base_name(name):
    """A feat's base name (before any ' (choice)'), lower-cased, for matching."""
    return str(name).split(" (")[0].strip().lower()


def filter_free_feats(feat_list):
    """Drop the free-at-BAB>=1 feats from an already-selected list (catches bonus-feat sources that
    bypass the chooseable pool). Matches on base name so any '(choice)' variant is caught too."""
    return [f for f in feat_list if _feat_base_name(f) not in _FREE_AT_BAB1_NORM]


# 2) Feats that require choosing a skill -> pointed at professions. `display` is the exact
# every_feat.json casing (the FoundryVTT lookup is case-sensitive on the base name). `count` = how many
# skills it picks; `base`/`improved` = the bonus (improved applies at >= 10 ranks in the chosen skill);
# `restrict` limits the FALLBACK skill (professions always qualify).
_SKILL_CHOICE_FEATS = {
    "skill focus": {"display": "Skill Focus", "count": 1, "base": 3, "improved": 6, "restrict": None},
    "prodigy":     {"display": "Prodigy",     "count": 2, "base": 2, "improved": 4,
                    "restrict": ("craft", "perform", "profession")},
}


def _skill_pf1_id(skill_key):
    """A skill_ranks key -> pf1 change target ('knowledge local' -> 'skill.klo'); None if unmappable.

    Uses the canonical data.SKILL_IDS map so the Skill Focus / Prodigy change targets can never drift
    from the skill pool itself. Craft/Perform/Profession subtypes collapse to their base id.
    """
    k = " ".join(str(skill_key).strip().lower().split())
    if k in data.SKILL_IDS:
        return "skill." + data.SKILL_IDS[k]
    for base in ("profession", "craft", "perform"):
        if k.startswith(base):
            return "skill." + data.SKILL_IDS[base]
    return None


def _skill_change(target, bonus):
    """A pf1 always-on change: +bonus to a skill target (value resolved at gen time -> flat number)."""
    return {"formula": str(int(bonus)), "target": target, "type": "untyped", "operator": "add", "priority": 0}


def _norm_skill_name(name):
    """Normalize a display skill name ('Knowledge (local)') to a skill_ranks key ('knowledge local')."""
    return " ".join(str(name).lower().replace("(", " ").replace(")", " ").split())


def _skill_display(character, skill_key):
    """Pretty display for a skill_ranks key ('knowledge local' -> 'Knowledge (Local)')."""
    s = str(skill_key).strip().lower()
    if s.startswith("knowledge "):
        return "Knowledge (" + s[len("knowledge "):].strip().title() + ")"
    if s == "craft":
        spec = getattr(character, "craft_chosen", None)
        return f"Craft ({spec})" if spec else "Craft"
    if s == "profession":
        chosen = getattr(character, "profession_chosen", None) or []
        return f"Profession ({chosen[0]})" if chosen else "Profession"
    return s.title()


def _next_profession(profs):
    """Highest-rank profession assigned the FEWEST skill-focus bonuses so far, so repeated picks spread
    across professions (highest rank first) before doubling up. None if there are no professions."""
    if not profs:
        return None
    return min(profs, key=lambda p: (len(p.get("skill_focus_bonuses", [])), -int(p.get("ranks", 0) or 0)))


def _fallback_skill(skill_ranks, assoc, restrict, used):
    """Surplus pick when professions are exhausted: highest-ranked skill (profession-associate
    preferred), honoring any restriction. Returns a skill_ranks key or None."""
    ranked = sorted(((n, r) for n, r in (skill_ranks or {}).items() if r and r > 0),
                    key=lambda kv: (kv[0] in assoc, kv[1]), reverse=True)
    for n, _r in ranked:
        if n in used:
            continue
        if restrict and not any(n.startswith(x) for x in restrict):
            continue
        return n
    return None


def specialize_skill_choice_feats(character, feat_list, skill_ranks=None):
    """For each feat in ``feat_list`` that requires choosing a skill (Skill Focus / Prodigy / ...),
    point it at the character's professions (highest rank first), inject the choice into the feat NAME,
    and record the feat's numeric bonus on the chosen profession (consumed later by
    ``build_profession_ability_items``). Surplus picks fall back to the best regular skill. The base
    name is rebuilt from the canonical ``display`` so the case-sensitive Foundry lookup still matches.
    Mutates ``feat_list`` in place and returns it."""
    if not isinstance(feat_list, list) or not feat_list:
        return feat_list
    profs = list(getattr(character, "profession_data", []) or [])
    skill_ranks = skill_ranks if skill_ranks is not None else (getattr(character, "skill_ranks", {}) or {})
    assoc = set()
    for p in profs:
        for s in p.get("associate_skills", []) or []:
            assoc.add(_norm_skill_name(s))
    used_skills = set()
    changes_by_feat = {}   # specialized feat name -> {"changes": [...], "contextNotes": []}

    for i, feat in enumerate(feat_list):
        spec = _SKILL_CHOICE_FEATS.get(_feat_base_name(feat))
        if not spec:
            continue
        picks, changes = [], []
        for _ in range(spec["count"]):
            prof = _next_profession(profs)
            if prof is not None:
                bonus = spec["improved"] if int(prof.get("ranks", 0) or 0) >= 10 else spec["base"]
                prof.setdefault("skill_focus_bonuses", []).append({"feat": spec["display"], "bonus": bonus})
                picks.append(f"Profession ({prof['name']})")
                # Each profession is a Foundry subskill under "skill.pro"; bonus resolved flat at gen time.
                changes.append(_skill_change("skill.pro", bonus))
            else:
                fb = _fallback_skill(skill_ranks, assoc, spec["restrict"], used_skills)
                if fb:
                    used_skills.add(fb)
                    picks.append(_skill_display(character, fb))
                    sid = _skill_pf1_id(fb)
                    if sid:
                        bonus = spec["improved"] if int(skill_ranks.get(fb, 0) or 0) >= 10 else spec["base"]
                        changes.append(_skill_change(sid, bonus))
        if picks:
            feat_list[i] = f"{spec['display']} ({', '.join(picks)})"
            if changes:
                changes_by_feat[feat_list[i]] = {"changes": changes, "contextNotes": []}

    # Stash the resolved changes; main_test folds them into feat_changes_dict so the bonus actually
    # lands on the Foundry sheet (previously skill_focus_bonuses was recorded but never consumed).
    if changes_by_feat:
        existing = getattr(character, "skill_focus_changes", None) or {}
        existing.update(changes_by_feat)
        character.skill_focus_changes = existing
    return feat_list
