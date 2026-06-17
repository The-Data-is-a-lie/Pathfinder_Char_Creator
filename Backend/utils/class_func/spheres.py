"""Spheres of Power / Spheres of Might dabbling for normal (non-spherecasting) NPCs.

Real spherecasting *base classes* are out of scope (the user adds those via the FoundryVTT compendium
/ everyClass). This module lets a NORMAL character opt into the Spheres ecosystem -- spending feat
slots to pick up sphere feats and talents, with a casting tradition + "mana" pool for the magic side.
It mirrors ``path_of_war.py``: a ``randomize_spheres_num`` count roll + a ``choose_spheres_attr``
selector that returns an export bundle the generator splices into its feat/talent/export machinery.

Design (locked with the user):
  * **Trigger** -- opt-in ``character.spheres_flag`` (default off). When off, every entry point no-ops.
  * **0-3 spheres.** Each sphere independently rolls **might vs power** off caster level (none->might;
    low->50/50; mid/3-4->power 75%; high/full->power 90%).
  * **Feat-funded talents.** Magic entry = the ``Basic Magic Training`` feat (sphere base + tradition +
    pool, 1 talent); further magic spheres + talents come from ``Extra Magic Talent`` feats (HR1: each
    grants **2** talents). Combat entry/extra = ``Extra Combat Talent`` (2 talents each, first grants
    martial focus). Sphere feats are reserved out of the normal feat budget like Path of War's MT feats.
  * **§8 advanced-talent HARD GATE** -- per sphere, advanced/legendary talents allowed =
    ``(normal_talents + 2*sphere_feats) // 7``. Enforced as a precondition during selection AND a
    post-condition drop. The pf1 prereq engine alone is NOT trusted here: ``no_prereq_prep``'s
    ``filter_pattern`` matches the substring "cast", so a magic talent's "caster level Nth" gate is
    auto-satisfied and would leak advanced talents -- ``type`` is the authoritative guard.
  * **Casting tradition (Spheres of Power).** Taking any magic sphere picks a CAM (highest mental
    stat), rolls general drawbacks (HR3: no cap), converts 2 drawbacks -> 1 boon, and routes leftover
    drawbacks to bonus spell points on the triangular chart (1->1, 2->3, 3->6, 4->10, 5->15, 6->21...).
  * **HR4 mana pool.** Any magic content -> pool = highest mental mod (min 1) + tradition bonus SP.

Data (built by ``Backend/scripts/extract_spheres_talents.py`` from the pf1spheres compendium):
  spheres_of_power.json, spheres_of_might_enriched.json, sphere_feats.json, advanced_talents.json,
  and (harvested) spheres_traditions.json.

Public API:
    randomize_spheres_num(character)  -> int, also stored on character.sphere_count
    choose_spheres_attr(character)    -> export bundle dict (empty defaults when count 0)
"""
import json
import os
import random
import re

from utils.class_func.generic_func import no_prereq_loop
from utils.class_func.skill_ranks import highest_mental_mod, final_ability_mod
import utils.data as data

# --------------------------------------------------------------------------- #
# Tunables (named so the curve is easy to retune)
# --------------------------------------------------------------------------- #
SPHERE_COUNT_WEIGHTS = [1, 4, 3, 2]      # weights for 0,1,2,3 spheres when the flag is on
MAX_EXTRA_TALENT_FEATS = 2               # cap on Extra-Talent feats beyond one entry feat per sphere
KEEP_FREE_FEATS = 1                      # try to leave the character at least this many normal feats
DRAWBACK_MIN, DRAWBACK_MAX = 2, 6        # general drawbacks rolled for a casting tradition (HR3: no cap)
ADVANCED_RATIO = 7                       # §8: this many normal-talent-equivalents per advanced talent

_JSON_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "json", "class_data", "spheres")
_CACHE = {}

# Built-in fallback used only if spheres_traditions.json is absent (keeps the feature runnable). These
# names are the verified-canonical subset (the full, richer set lives in spheres_traditions.json).
_FALLBACK_TRADITIONS = {
    "casting_ability_modifiers": ["Intelligence", "Wisdom", "Charisma"],
    "general_drawbacks": [
        {"name": "Addictive Casting", "description": "Your magic is addictive.", "counts_as": 2},
        {"name": "Draining Casting", "description": "Spending spell points deals nonlethal damage.", "counts_as": 1},
        {"name": "Extended Casting", "description": "Sphere abilities take one step longer to activate.", "counts_as": 2},
        {"name": "Focus Casting", "description": "You must wield a focus item to cast.", "counts_as": 1},
        {"name": "Magical Signs", "description": "Your magic produces obvious sensory signs.", "counts_as": 1},
        {"name": "Material Casting", "description": "You expend consumable components to cast.", "counts_as": 1},
        {"name": "Prepared Caster", "description": "You pre-assign spell points to spheres after rest.", "counts_as": 1},
        {"name": "Skilled Casting", "description": "Casting is channeled through a Craft/Perform/Profession check.", "counts_as": 1},
        {"name": "Somatic Casting", "description": "You need a free hand and suffer armor spell failure.", "counts_as": 1},
        {"name": "Verbal Casting", "description": "You must speak clearly to cast.", "counts_as": 1},
        {"name": "Wild Magic", "description": "Spending spell points risks a wild-magic event.", "counts_as": 1},
    ],
    "boons": [
        {"name": "Easy Focus", "description": "You no longer need a check to cast without your focus item."},
        {"name": "Empowered Abilities", "description": "Your sphere abilities gain caster level as your pool drains."},
        {"name": "Fortified Casting", "description": "Use Constitution as your casting ability modifier if higher."},
        {"name": "Overcharge", "description": "Push +2 caster level on an ability, becoming fatigued afterward."},
    ],
    "bonus_spell_point_chart": [{"drawbacks": n, "bonus_spell_points": n * (n + 1) // 2} for n in range(0, 12)],
    "sphere_specific_drawbacks": [],
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _load(name):
    if name not in _CACHE:
        path = os.path.join(_JSON_DIR, name)
        try:
            with open(path, encoding="utf-8") as fh:
                _CACHE[name] = json.load(fh)
        except (OSError, ValueError):
            _CACHE[name] = None
    return _CACHE[name]


def _norm(s):
    """Match key: lower, drop trailing source tags like ``[apoc]``, collapse whitespace."""
    s = re.sub(r"\s*\[[^\]]*\]\s*", " ", str(s).lower())
    return re.sub(r"\s+", " ", s).strip()


def _sphere_dataset(system):
    return _load("spheres_of_power.json" if system == "power" else "spheres_of_might_enriched.json") or {}


def _available_spheres(system):
    """Spheres present in the data AND vetted in data.py (keeps homebrew-only spheres from leaking)."""
    ds = _sphere_dataset(system)
    vetted = {_norm(s) for s in (data.magic_spheres if system == "power" else data.combat_spheres)}
    return [s for s in ds if _norm(s) in vetted]


def _advanced_set(system, sphere):
    """Normalized names that are advanced/legendary in this sphere (registry overlay on the data flag)."""
    reg = _load("advanced_talents.json") or {}
    names = (reg.get("power" if system == "power" else "might", {}) or {}).get(sphere, [])
    return {_norm(n) for n in names}


def _advanced_quota(normal, feats):
    """§8: advanced talents allowed in a sphere = (normal talents + 2*sphere feats) // 7."""
    return (normal + 2 * feats) // ADVANCED_RATIO


def _casting_level(character):
    """'high' | 'mid' | 'low' | 'none' for the character's main class (drives might-vs-power)."""
    try:
        return str(character.class_data[character.c_class]["casting level"]).lower()
    except (AttributeError, KeyError, TypeError):
        return str(getattr(character, "casting_level_string", "none") or "none").lower()


def _system_for_sphere(character, casting_level):
    """Per-sphere might-vs-power roll (user rule): none->might; low->50/50; mid->75% power; high->90%."""
    p = {"high": 0.90, "mid": 0.75, "low": 0.50}.get(casting_level, 0.0)
    return "power" if random.random() < p else "might"


def _mental_stat_name(character):
    best = max(("int", "wis", "cha"), key=lambda s: final_ability_mod(character, s))
    return {"int": "Intelligence", "wis": "Wisdom", "cha": "Charisma"}[best]


# --------------------------------------------------------------------------- #
# Count roll
# --------------------------------------------------------------------------- #
def randomize_spheres_num(character):
    """Roll 0-3 spheres for a dabbler. No-op (0) unless ``character.spheres_flag`` is truthy ('Y')."""
    flag = str(getattr(character, "spheres_flag", "N") or "N").upper()
    if flag not in ("Y", "YES", "TRUE", "1"):
        character.sphere_count = 0
        return 0
    n = random.choices([0, 1, 2, 3], weights=SPHERE_COUNT_WEIGHTS, k=1)[0]
    # Feat-funded: each sphere needs at least one entry feat, so never plan more spheres than the
    # (post-Path-of-War) feat budget can seat.
    budget = max(0, int(getattr(character, "feat_amounts", 0) or 0) - KEEP_FREE_FEATS)
    character.sphere_count = min(n, budget)
    return character.sphere_count


# --------------------------------------------------------------------------- #
# Talent selection (with the §8 hard gate)
# --------------------------------------------------------------------------- #
def _is_advanced(name_lower, dataset, advanced_norm):
    entry = dataset.get(name_lower, {})
    return str(entry.get("type", "")).lower() == "advanced" or _norm(name_lower) in advanced_norm


def _pick_talents_in_sphere(character, system, sphere, n, counts):
    """Pick up to ``n`` prerequisite-legal talents from one sphere, enforcing the §8 advanced gate.

    Reuses ``no_prereq_loop`` for prereq filtering (the existing class-talent machinery); ``counts`` is
    the per-sphere tally {'normal','advanced','feats'} that drives the quota (mutated in place).
    Returns a list of (sphere, system, talent_name, record) for the accepted picks.
    """
    dataset = _sphere_dataset(system).get(sphere, {})
    if not dataset or n <= 0:
        return []
    advanced_norm = _advanced_set(system, sphere)
    # Seed sphere access so base talents (empty prereq, or "<sphere> sphere") surface.
    character.chooseable.update({_norm(sphere), f"{_norm(sphere)} sphere", f"{system} sphere"})

    picks, taken = [], set()
    character.chooseable_talents = []
    pool = [c for c in no_prereq_loop(character, dataset) if c not in taken]
    guard = 0
    while len(picks) < n and guard < 1000:
        guard += 1
        if not pool:
            break
        quota = _advanced_quota(counts["normal"], counts["feats"])
        allow_adv = counts["advanced"] < quota
        base = [c for c in pool if not _is_advanced(c, dataset, advanced_norm)]
        adv = [c for c in pool if _is_advanced(c, dataset, advanced_norm)]
        candidates = base if base else (adv if allow_adv else [])
        if not candidates:
            break  # only advanced talents remain but quota is exhausted -> the rule cannot be broken
        chosen = random.choice(candidates)
        is_adv = _is_advanced(chosen, dataset, advanced_norm)
        if is_adv:
            counts["advanced"] += 1
        else:
            counts["normal"] += 1
        rec = dataset[chosen]
        picks.append((sphere, system, chosen, rec))
        taken.add(chosen)
        character.chooseable.add(chosen)            # let dependent talents chain off this one
        character.chooseable_talents = []
        pool = [c for c in no_prereq_loop(character, dataset) if c not in taken]

    # Defensive post-condition: never exceed the quota even if classification drifted (§8 invariant).
    quota = _advanced_quota(counts["normal"], counts["feats"])
    kept, adv_kept = [], 0
    for p in picks:
        if _is_advanced(p[2], dataset, advanced_norm):
            if adv_kept >= quota:
                counts["advanced"] -= 1
                continue
            adv_kept += 1
        kept.append(p)
    return kept


# --------------------------------------------------------------------------- #
# Casting tradition + mana pool
# --------------------------------------------------------------------------- #
def _choose_casting_tradition(character):
    trad = _load("spheres_traditions.json") or _FALLBACK_TRADITIONS
    cam = _mental_stat_name(character)
    db_pool = list(trad.get("general_drawbacks", []))
    boon_pool = list(trad.get("boons", []))
    drawbacks = random.sample(db_pool, min(random.randint(DRAWBACK_MIN, DRAWBACK_MAX), len(db_pool))) if db_pool else []
    total_db = sum(int(d.get("counts_as", 1) or 1) for d in drawbacks)
    n_boons = total_db // 2                          # HR: 2 general drawbacks = 1 boon
    boons = random.sample(boon_pool, min(n_boons, len(boon_pool))) if boon_pool else []
    leftover = total_db - 2 * len(boons)
    bonus_sp = leftover * (leftover + 1) // 2        # triangular chart (1->1, 2->3, 3->6, ...)
    return {
        "casting_ability_modifier": cam,
        "drawbacks": [d.get("name", "") for d in drawbacks],
        "boons": [b.get("name", "") for b in boons],
        "bonus_spell_points": bonus_sp,
    }


def _mana_pool(character, tradition):
    """HR4: any Spheres-of-Power content -> pool = max(int,wis,cha) mod (min 1) + tradition bonus SP."""
    return max(1, highest_mental_mod(character)) + int(tradition.get("bonus_spell_points", 0))


# --------------------------------------------------------------------------- #
# Item / feat builders
# --------------------------------------------------------------------------- #
def _display_name(name):
    """Clean a talent name for the sheet: drop source tags like ``[apoc]`` and title-case the words
    without breaking apostrophes (``jester's`` -> ``Jester's``, not ``Jester'S``)."""
    name = re.sub(r"\s*\[[^\]]*\]\s*", " ", str(name)).strip()
    return " ".join(w[:1].upper() + w[1:] for w in name.split())


def _talent_item(sphere, system, name, rec):
    desc = rec.get("description") or rec.get("benefit") or ""
    return {
        "name": _display_name(name),
        "sphere": _display_name(sphere),
        "system": "Spheres of Power" if system == "power" else "Spheres of Might",
        "type": rec.get("type", "base"),
        "description": desc,
        "changes": [], "contextNotes": [], "uses": None,
    }


def _extra_talent_desc(feat_name, granted):
    """HR7 record-keeping: an Extra-Talent feat's bundled contents = the talents it granted."""
    lines = [f"{feat_name} > {feat_name} (house rule: one slot, two talents).", "Talents gained:"]
    for sphere, _system, name, rec in granted:
        body = (rec.get("description") or rec.get("benefit") or "").strip().replace("\n", " ")
        lines.append(f"- {_display_name(name)} ({_display_name(sphere)}): {body[:300]}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #
def _empty_bundle():
    return {
        "magic_talent_items": [], "combat_talent_items": [],
        "sphere_feats": [], "sphere_feat_tax": {}, "sphere_mana_pool": 0,
        "spheres_chosen": [], "casting_tradition": {}, "sphere_drawbacks": [],
        "sphere_boons": [], "sphere_traits": [], "sphere_counts": {},
        "homebrew_feat_desc_dict": {},
    }


def choose_spheres_attr(character):
    """Select sphere feats + talents for a dabbler and return the export bundle.

    Empty defaults when ``character.sphere_count`` is 0 (flag off / no budget). Reserves the sphere
    feats out of ``character.feat_amounts`` so the downstream feat chooser asks for fewer normals
    (mirrors the Path of War MT/style reservation); the generator appends ``sphere_feats`` to the
    normal bucket and merges ``sphere_feat_tax`` like the style chains.
    """
    bundle = _empty_bundle()
    n = int(getattr(character, "sphere_count", 0) or 0)
    if n <= 0:
        return bundle

    casting_level = _casting_level(character)
    pool_p, pool_m = _available_spheres("power"), _available_spheres("might")
    if not pool_p and not pool_m:
        return bundle

    # ---- choose distinct spheres + their system ------------------------- #
    chosen = []                                       # [(sphere, system), ...]
    used = set()
    for _ in range(n):
        system = _system_for_sphere(character, casting_level)
        if system == "power" and not pool_p:
            system = "might"
        if system == "might" and not pool_m:
            system = "power"
        avail = [s for s in (pool_p if system == "power" else pool_m) if (system, s) not in used]
        if not avail:
            continue
        sphere = random.choice(avail)
        used.add((system, sphere))
        chosen.append((sphere, system))
    if not chosen:
        return bundle

    # ---- allocate feat slots (feat-funded) ------------------------------ #
    budget = max(len(chosen), min(int(getattr(character, "feat_amounts", 0) or 0) - KEEP_FREE_FEATS,
                                  len(chosen) + random.randint(0, MAX_EXTRA_TALENT_FEATS)))
    budget = min(budget, int(getattr(character, "feat_amounts", 0) or 0))
    # Per sphere: feats taken (names), talent count granted, running §8 tally.
    counts = {s: {"normal": 0, "advanced": 0, "feats": 0} for s, _ in chosen}
    sphere_feat_names = {s: [] for s, _ in chosen}
    sphere_talent_n = {s: 0 for s, _ in chosen}
    took_basic_magic = False
    spent = 0
    # entry feat for each sphere first
    for sphere, system in chosen:
        if spent >= budget:
            break
        if system == "power" and not took_basic_magic:
            feat, gained = "Basic Magic Training", 1
            took_basic_magic = True
        elif system == "power":
            feat, gained = "Extra Magic Talent", 2
        else:
            feat, gained = "Extra Combat Talent", 2
        sphere_feat_names[sphere].append(feat)
        counts[sphere]["feats"] += 1
        sphere_talent_n[sphere] += gained
        spent += 1
    # spread any remaining budget as Extra-Talent feats
    fundable = [s for s, _ in chosen]
    while spent < budget and fundable:
        sphere = random.choice(fundable)
        system = dict((s, sy) for s, sy in chosen)[sphere]
        feat = "Extra Magic Talent" if system == "power" else "Extra Combat Talent"
        sphere_feat_names[sphere].append(feat)
        counts[sphere]["feats"] += 1
        sphere_talent_n[sphere] += 2
        spent += 1

    # ---- pick talents per sphere (gate-enforced) ------------------------ #
    magic_items, combat_items = [], []
    extra_granted = {"Extra Magic Talent": [], "Extra Combat Talent": [], "Basic Magic Training": []}
    took_magic = False
    for sphere, system in chosen:
        picks = _pick_talents_in_sphere(character, system, sphere, sphere_talent_n[sphere], counts[sphere])
        for p in picks:
            (magic_items if system == "power" else combat_items).append(_talent_item(*p))
        # attribute granted talents to the sphere's entry/extra feats for HR7 record-keeping
        if system == "power":
            took_magic = True
            key = "Basic Magic Training" if "Basic Magic Training" in sphere_feat_names[sphere] else "Extra Magic Talent"
        else:
            key = "Extra Combat Talent"
        extra_granted[key].extend(picks)

    # ---- feats, feat-tax (HR1), descriptions ---------------------------- #
    sphere_feats, sphere_feat_tax, desc = [], {}, {}
    feat_lib = _load("sphere_feats.json") or {}
    for sphere, _system in chosen:
        sphere_feats.extend(sphere_feat_names[sphere])
    for feat in set(sphere_feats):
        if feat.lower().startswith("extra "):
            sphere_feat_tax[feat] = [feat]            # HR1: one slot -> a free duplicate -> 2 talents
        granted = extra_granted.get(feat, [])
        if feat.lower().startswith("extra ") and granted:
            desc[feat] = _extra_talent_desc(feat, granted)
        else:
            base = (feat_lib.get(feat.lower(), {}) or {}).get("benefit", "")
            if feat == "Basic Magic Training" and granted:
                base = (base + "\nSphere/talent gained: "
                        + ", ".join(f"{_display_name(name)} ({_display_name(sphere)})" for sphere, _s, name, _r in granted)).strip()
            if base:
                desc[feat] = base

    # ---- tradition + mana pool (magic only) ----------------------------- #
    tradition = _choose_casting_tradition(character) if took_magic else {}
    bundle.update({
        "magic_talent_items": magic_items,
        "combat_talent_items": combat_items,
        "sphere_feats": sphere_feats,
        "sphere_feat_tax": sphere_feat_tax,
        "sphere_mana_pool": _mana_pool(character, tradition) if took_magic else 0,
        "spheres_chosen": [{"sphere": s.title(), "system": "power" if sy == "power" else "might"} for s, sy in chosen],
        "sphere_counts": {s.title(): counts[s] for s, _sy in chosen},
        "casting_tradition": tradition,
        "sphere_drawbacks": tradition.get("drawbacks", []),
        "sphere_boons": tradition.get("boons", []),
        "sphere_traits": tradition.get("drawbacks", []) + tradition.get("boons", []),
        "homebrew_feat_desc_dict": desc,
    })
    return bundle
