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
# TEMP (testing 2026-06-16): 0-weight zeroed so an opted-in character ALWAYS rolls >=1 sphere
# (subject to feat budget). REVERT to [1, 4, 3, 2] before shipping.
SPHERE_COUNT_WEIGHTS = [0, 4, 3, 2]      # weights for 0,1,2,3 spheres when the flag is on
# TEMP (testing): force all of a dabbler's flat-8 talents into ONE sphere so the 7 normals satisfy the
# same-sphere prerequisites that gate advanced/legendary talents. Set False to restore 1-3 spheres.
SINGLE_SPHERE_TESTING = True
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


def _talent_match_norm(s):
    """Like ``_norm`` but ALSO drops a trailing ``(variant)`` so a scraped name like
    ``"ragdoll swing (impale)"`` matches the compendium base name ``"Ragdoll Swing"`` (mirrors the
    FoundryVTT module's ``sphereNorm``). Used to test talents against the compendium allowlist."""
    s = str(s).split(" (")[0]
    s = re.sub(r"\s*\[[^\]]*\]\s*", " ", s.lower())
    s = s.replace("'", "").replace("’", "").replace("`", "")   # apostrophe-insensitive (like the front-end)
    return re.sub(r"\s+", " ", s).strip()


def _compendium_allow(system):
    """Set of compendium talent names (match-normalized) for ``system`` from
    ``compendium_talent_names.json``. Returns ``None`` when the file is absent so the caller treats it
    as 'no filter' (keeps generation runnable if the allowlist hasn't been built yet)."""
    key = f"_allow::{system}"
    if key not in _CACHE:
        names = _load("compendium_talent_names.json")
        if not names:
            _CACHE[key] = None
        else:
            lst = names.get("power" if system == "power" else "might", []) or []
            _CACHE[key] = {_talent_match_norm(n) for n in lst}
    return _CACHE[key]


def _sphere_dataset(system):
    """Talents for ``system``, filtered to entries that actually exist on the pf1spheres compendium --
    this drops scraped non-talents (e.g. "Optional Rule: ...", variant-rule sidebars, empty stubs) so
    only real talents are ever picked. No-op (returns the raw data) if the allowlist file is missing."""
    cache_key = f"_ds::{system}"
    if cache_key not in _CACHE:
        raw = _load("spheres_of_power.json" if system == "power" else "spheres_of_might_enriched.json") or {}
        allow = _compendium_allow(system)
        if allow is None:
            _CACHE[cache_key] = raw
        else:
            _CACHE[cache_key] = {
                sphere: {name: rec for name, rec in talents.items() if _talent_match_norm(name) in allow}
                for sphere, talents in raw.items()
            }
    return _CACHE[cache_key]


def _available_spheres(system):
    """Spheres present in the data AND vetted in data.py (keeps homebrew-only spheres from leaking)."""
    ds = _sphere_dataset(system)
    vetted = {_norm(s) for s in (data.magic_spheres if system == "power" else data.combat_spheres)}
    return [s for s in ds if _norm(s) in vetted]


def _advanced_set(system, sphere):
    """Normalized names that are advanced/legendary in this sphere (registry overlay on the data flag).

    Uses ``_talent_match_norm`` (not ``_norm``) so a registry name that carries the wiki variant suffix
    -- e.g. ``"bomb jump (leap)"`` -- normalizes to the clean compendium dataset key ``"bomb jump"`` and
    actually matches.  ``_norm`` left the ``(leap)`` on and silently failed to flag such talents."""
    reg = _load("advanced_talents.json") or {}
    names = (reg.get("power" if system == "power" else "might", {}) or {}).get(sphere, [])
    return {_talent_match_norm(n) for n in names}


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
    # The count is now UNCAPPED by the feat budget: the generator guarantees that a selected dabbler
    # actually receives spheres by funding them with PRIORITY over normal feats (see main_test's
    # PoW/Spheres guarantee block). We no longer zero the roll when the leftover budget is tight.
    n = random.choices([0, 1, 2, 3], weights=SPHERE_COUNT_WEIGHTS, k=1)[0]
    if SINGLE_SPHERE_TESTING and n > 0:
        n = 1                            # TEMP: concentrate the flat-8 talents into one sphere for testing
    character.sphere_count = n
    return n


# --------------------------------------------------------------------------- #
# Talent selection (with the §8 hard gate)
# --------------------------------------------------------------------------- #
def _is_advanced(name_lower, dataset, advanced_norm):
    entry = dataset.get(name_lower, {})
    # ``advanced_norm`` is keyed by ``_talent_match_norm`` (suffix-stripped); normalize the dataset
    # name the same way so e.g. dataset key "bomb jump" matches registry "bomb jump (leap)".
    return str(entry.get("type", "")).lower() == "advanced" or _talent_match_norm(name_lower) in advanced_norm


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
        # Plain names on drawbacks/boons keep these fields .join()-safe for any older/stale front-end
        # render (avoids "[object Object]" during backend<->module version skew). The rich
        # {name, description, counts_as} dicts live in the parallel *_detail keys, which the current
        # sheet reads to spell out what each one DOES (and its 1-/2-point weight).
        "drawbacks": [d.get("name", "") for d in drawbacks],
        "boons": [b.get("name", "") for b in boons],
        "drawbacks_detail": [{"name": d.get("name", ""), "description": d.get("description", ""),
                              "counts_as": int(d.get("counts_as", 1) or 1)} for d in drawbacks],
        "boons_detail": [{"name": b.get("name", ""), "description": b.get("description", "")} for b in boons],
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


_COMBAT_BUFFS = None


def _combat_talent_buffs():
    """Curated numeric buffs for Spheres-of-MIGHT (combat) talents, keyed {Sphere: {Talent: {...}}}
    (display-cased to match _display_name). Loaded once; {} if the file is absent. Authored via
    Backend/scripts/build_talent_changes.py + manual curation. Magic (Power) talents stay
    description-only -- they cast effects, not passive self-buffs."""
    global _COMBAT_BUFFS
    if _COMBAT_BUFFS is None:
        from pathlib import Path as _Path
        _p = _Path(__file__).resolve().parents[2] / "json" / "class_data" / "spheres" / "combat_talent_changes.json"
        try:
            _COMBAT_BUFFS = json.loads(_p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _COMBAT_BUFFS = {}
    return _COMBAT_BUFFS


def _talent_item(sphere, system, name, rec):
    desc = rec.get("description") or rec.get("benefit") or ""
    # Reliable advanced/legendary flag for the sheet (mirrors _is_advanced): the compendium clone the
    # front-end builds carries no advanced marker, so the front-end relies on this to label "(Advanced)"
    # and sort advanced talents to the bottom of each sphere.
    advanced = (str(rec.get("type", "")).lower() == "advanced"
                or _talent_match_norm(name) in _advanced_set(system, sphere))
    disp_sphere, disp_name = _display_name(sphere), _display_name(name)
    # Numeric buffs land on the Foundry "Changes" tab for combat talents only (Power = text-only).
    buff = _combat_talent_buffs().get(disp_sphere, {}).get(disp_name, {}) if system == "might" else {}
    return {
        "name": disp_name,
        "sphere": disp_sphere,
        "system": "Spheres of Power" if system == "power" else "Spheres of Might",
        "type": rec.get("type", "base"),
        "advanced": advanced,
        "description": desc,
        "changes": buff.get("changes", []),
        "contextNotes": buff.get("contextNotes", []),
        "uses": None,
    }


def _extra_talent_desc(feat_name, granted):
    """HR7 record-keeping: an Extra-Talent feat's bundled contents = the talents it granted."""
    lines = [f"{feat_name} > {feat_name} (house rule: one slot, two talents).", "Talents gained:"]
    for sphere, _system, name, rec in granted:
        body = (rec.get("description") or rec.get("benefit") or "").strip().replace("\n", " ")
        lines.append(f"- {_display_name(name)} ({_display_name(sphere)}): {body[:300]}")
    return "\n".join(lines)


def mentor_sphere_summary(spheres_chosen, talents):
    """HTML description for the dedicated "Spheres Mentor" trainer (25% trainer-backed branch): the
    spheres it funded + the OFF-BUDGET talents it taught beyond the character's own budget, presented as
    HR1 Extra-Talent feats (one "Extra X Talent > Extra X Talent" per 2 talents) followed by the talent
    names. ``talents`` is a list of {name, sphere, system} dicts (non-budget-paid flat-8 + overflow);
    ``system`` may be raw ("power"/"might") or the display string ("Spheres of Power") -- both handled."""
    if not talents:
        return "A dedicated mentor who funded this character's sphere talents beyond their own study."

    def _is_power(t):
        return "power" in str(t.get("system", "")).lower()

    sphere_str = ", ".join(
        f"{s.get('sphere', '')} ({'Power' if str(s.get('system', '')).lower().startswith('p') else 'Might'})"
        for s in (spheres_chosen or []) if s.get('sphere'))
    feat_lines = []
    for want_power, label in ((True, "Extra Magic Talent"), (False, "Extra Combat Talent")):
        grp = [t for t in talents if _is_power(t) == want_power]
        for i in range(0, len(grp), 2):
            feat_lines.append(f"{label} > {label}" if len(grp[i:i + 2]) == 2 else label)
    talent_lines = [f"{t.get('name', '')} ({t.get('sphere', '')})" for t in talents]
    parts = []
    if sphere_str:
        parts.append(f"<strong>Spheres funded:</strong> {sphere_str}")
    parts.append("<br>".join(feat_lines))
    parts.append("<br>".join(talent_lines))
    return "<br><br>".join(p for p in parts if p)


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
        "sphere_feat_budget_count": 0,
        # Working state surfaced for the generator's overflow step (not exported to the sheet).
        "_chosen": [], "_counts": {},
    }


def _pick_flat_talents(character, chosen, counts, n_normal=7, n_advanced=1):
    """Testing model: pick a FLAT set of talents across the chosen spheres -- ``n_normal`` normal +
    ``n_advanced`` advanced, all prerequisite-legal -- decoupled from the feat count. Round-robins the
    normals across spheres, then takes the advanced from any qualifying sphere; if no advanced is
    available it backfills an extra normal so the total stays ``n_normal + n_advanced``.

    Reuses the same prereq machinery as ``_pick_talents_in_sphere`` (``no_prereq_loop`` + ``_is_advanced``).
    Mutates ``counts[sphere]`` and returns ``(magic_items, combat_items, picks_by_sphere)`` where
    ``picks_by_sphere[sphere]`` is the list of raw (sphere, system, name, rec) picks for that sphere."""
    spheres = list(chosen)
    for sphere, system in spheres:                       # seed sphere access (base + "<sphere> sphere")
        character.chooseable.update({_norm(sphere), f"{_norm(sphere)} sphere", f"{system} sphere"})
    datasets = {s: _sphere_dataset(sy).get(s, {}) for s, sy in spheres}
    adv_sets = {s: _advanced_set(sy, s) for s, sy in spheres}
    taken = {s: set() for s, _ in spheres}
    picks_by_sphere = {s: [] for s, _ in spheres}
    magic_items, combat_items = [], []

    def _take(sphere, system, want_advanced):
        ds = datasets[sphere]
        if not ds:
            return False
        character.chooseable_talents = []
        pool = [c for c in no_prereq_loop(character, ds) if c not in taken[sphere]]
        cands = [c for c in pool if _is_advanced(c, ds, adv_sets[sphere]) == want_advanced]
        if not cands:
            return False
        name = random.choice(cands)
        rec = ds[name]
        taken[sphere].add(name)
        character.chooseable.add(name)                   # let dependent talents chain off this one
        counts[sphere]["advanced" if want_advanced else "normal"] += 1
        pick = (sphere, system, name, rec)
        picks_by_sphere[sphere].append(pick)
        (magic_items if system == "power" else combat_items).append(_talent_item(*pick))
        return True

    def _round_robin_normals(target):
        got, active = 0, list(spheres)
        while got < target and active:
            progressed = False
            for sphere, system in list(active):
                if got >= target:
                    break
                if _take(sphere, system, False):
                    got, progressed = got + 1, True
                else:
                    active.remove((sphere, system))      # this sphere has no more legal normals
            if not progressed:
                break
        return got

    _round_robin_normals(n_normal)
    adv_got = 0
    for sphere, system in spheres:
        if adv_got >= n_advanced:
            break
        if _take(sphere, system, True):
            adv_got += 1
    if adv_got < n_advanced:                              # no advanced available -> backfill normals
        _round_robin_normals(n_advanced - adv_got)
    return magic_items, combat_items, picks_by_sphere


def _roll_magic_sphere_feats(character, chosen, counts):
    """Magic-side bonus (user rule): a Spheres-of-Power dabbler rolls 50/50 to take sphere-specific
    feat(s) from their MOST-TAKEN power sphere, heavily favoring exactly 1. Returns ``(feat_names,
    feat_descs)`` drawn from ``sphere_feats.json`` (system power/either, prerequisites naming that
    sphere). Prereq filtering is lightweight -- it prefers feats whose only listed prerequisite is the
    sphere itself (most sphere feats), which the character meets by having taken that sphere."""
    power = [s for s, sy in chosen if sy == "power"]
    if not power or random.random() < 0.5:
        return [], {}
    most = max(power, key=lambda s: counts[s]["normal"] + counts[s]["advanced"])
    n = random.choices([1, 2, 3], weights=[80, 15, 5], k=1)[0]
    lib = _load("sphere_feats.json") or {}
    needle = f"{_norm(most)} sphere"
    cands = []                                            # (extra_prereq_weight, name, rec)
    for name, rec in lib.items():
        if str(rec.get("system", "")).lower() not in ("power", "either"):
            continue
        prereq = _norm(rec.get("prerequisites", ""))
        if needle not in prereq:
            continue
        weight = prereq.replace(needle, "").count(",")    # rough proxy for # of extra prerequisites
        cands.append((weight, name, rec))
    if not cands:
        return [], {}
    cands.sort(key=lambda t: t[0])
    pool = cands[:max(n * 3, 6)]                           # sample from the lowest-prereq tier
    random.shuffle(pool)
    names, descs = [], {}
    for _w, name, rec in pool[:n]:
        disp = _display_name(name)
        names.append(disp)
        descs[disp] = str(rec.get("benefit", "")).strip()
    return names, descs


def choose_spheres_attr(character, max_feats=None, trainer_backed=False, mentor_talents=None):
    """Select sphere talents (flat-8) + a feat slot for each BUDGET-PAID talent; return the bundle.

    Empty defaults when ``character.sphere_count`` is 0 (flag off). Each budget-paid talent is tracked
    by an HR1 "Extra Talent > Extra Talent" feat (2 talents per feat; the first magic talent uses Basic
    Magic Training, 1 talent + access). ``trainer_backed`` (the 25% branch): only ~half the talents are
    budget-paid and get feats; the rest are funded by the 2 dedicated Spheres Mentor trainers (tracked
    there, not here). Lean characters pay for all their talents. ``max_feats`` is accepted for
    backward-compat but no longer used (the feat count now follows the budget-paid talent count). The
    generator reserves the realized feats with priority.
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

    # ---- pick the flat-8 talents first (talent COUNT is decoupled from the feat slots) ---- #
    # Every spheres-selected dabbler takes a flat 8 talents (7 normal + 1 advanced); the 25%
    # "trainer-backed" branch adds overflow talents on top in main_test.
    counts = {s: {"normal": 0, "advanced": 0, "feats": 0} for s, _ in chosen}
    magic_items, combat_items, picks_by_sphere = _pick_flat_talents(character, chosen, counts)
    took_magic = any(sy == "power" for _, sy in chosen)

    # ---- a feat slot for each BUDGET-PAID talent (HR1: one Extra-Talent feat = 2 talents) ---- #
    # Lean dabblers pay for ALL their talents from the feat budget; trainer-backed dabblers pay for
    # ~half (the rest are funded by the 2 dedicated "Spheres Mentor" trainers, tracked there). Both
    # talents on one Extra-Talent feat share a system (HR2). The first paid magic talent is funded by
    # Basic Magic Training (sphere access + 1 talent). Feats are uniquely named by the talents they pay
    # for -- both for tracking and to avoid the duplicate-name collapse in the feat-tax/desc dicts.
    magic_picks = [p for s, _sy in chosen for p in picks_by_sphere.get(s, []) if p[1] == "power"]
    combat_picks = [p for s, _sy in chosen for p in picks_by_sphere.get(s, []) if p[1] == "might"]
    all_picks = magic_picks + combat_picks            # magic first -> Basic Magic Training stays budget-paid
    n_total = len(all_picks)
    if trainer_backed and mentor_talents is not None:
        budget_paid = max(0, n_total - mentor_talents)   # the dedicated mentor funds min(mentor_talents, n_total) off-budget
    elif trainer_backed:
        budget_paid = (n_total + 1) // 2                 # fallback: mentor funds the off-budget half
    else:
        budget_paid = n_total                            # lean: the character pays for all flat-8 talents
    paid_magic = [p for p in all_picks[:budget_paid] if p[1] == "power"]
    paid_combat = [p for p in all_picks[:budget_paid] if p[1] == "might"]

    sphere_feats, sphere_feat_tax, desc = [], {}, {}
    feat_lib = _load("sphere_feats.json") or {}

    def _pair_suffix(pair):
        return " / ".join(_display_name(p[2]) for p in pair)

    mp = list(paid_magic)
    if mp:
        first = mp.pop(0)                              # first paid magic talent -> Basic Magic Training (1 talent)
        sphere_feats.append("Basic Magic Training")
        _base = (feat_lib.get("basic magic training", {}) or {}).get("benefit", "")
        desc["Basic Magic Training"] = (
            _base + f"\nSphere/talent gained: {_display_name(first[2])} ({_display_name(first[0])})").strip()
    for i in range(0, len(mp), 2):                     # remaining magic talents -> Extra Magic Talent (2 each)
        pair = mp[i:i + 2]
        fname = f"Extra Magic Talent ({_pair_suffix(pair)})"
        sphere_feats.append(fname)
        sphere_feat_tax[fname] = ["Extra Magic Talent"]     # HR1 -> renders "... > Extra Magic Talent"
        desc[fname] = _extra_talent_desc("Extra Magic Talent", pair)
    for i in range(0, len(paid_combat), 2):            # combat talents -> Extra Combat Talent (2 each)
        pair = paid_combat[i:i + 2]
        fname = f"Extra Combat Talent ({_pair_suffix(pair)})"
        sphere_feats.append(fname)
        sphere_feat_tax[fname] = ["Extra Combat Talent"]
        desc[fname] = _extra_talent_desc("Extra Combat Talent", pair)

    # Shared base-name descriptions so the front-end's feat-tax child ("... > Extra X Talent") resolves.
    if any(f.startswith("Extra Magic Talent") for f in sphere_feats):
        desc.setdefault("Extra Magic Talent", (feat_lib.get("extra magic talent", {}) or {}).get("benefit", "") or "Extra Magic Talent.")
    if any(f.startswith("Extra Combat Talent") for f in sphere_feats):
        desc.setdefault("Extra Combat Talent", (feat_lib.get("extra combat talent", {}) or {}).get("benefit", "") or "Extra Combat Talent.")

    # ---- magic-side bonus feat(s) from the most-taken power sphere (50/50, favor 1) ---- #
    if took_magic:
        _mf_names, _mf_descs = _roll_magic_sphere_feats(character, chosen, counts)
        sphere_feats.extend(_mf_names)
        desc.update(_mf_descs)

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
        # Flat name-only mirrors (back-compat surface). casting_tradition.drawbacks/boons are already
        # name strings; the rich text lives in casting_tradition.drawbacks_detail/boons_detail.
        "sphere_drawbacks": tradition.get("drawbacks", []),
        "sphere_boons": tradition.get("boons", []),
        "sphere_traits": tradition.get("drawbacks", []) + tradition.get("boons", []),
        "homebrew_feat_desc_dict": desc,
        # Budget-paid sphere feats (incl. the magic-side bonus feats) -> the generator reserves this many
        # feat slots. Working state for the overflow step (_chosen/_counts). Not exported to the sheet.
        "sphere_feat_budget_count": len(sphere_feats),
        "_chosen": chosen, "_counts": counts,
        # Off-budget talents (the non-budget-paid half of the flat-8) -> listed on the dedicated
        # "Spheres Mentor" trainer. Empty for lean characters (budget_paid == n_total).
        "mentor_funded_talents": [{"name": _display_name(p[2]), "sphere": _display_name(p[0]), "system": p[1]}
                                  for p in all_picks[budget_paid:]],
    })
    # Leftover (unpicked) sphere talents must NOT linger in chooseable_talents: that list ACCUMULATES
    # into the feat chooser's pool (feats.py), so an unpicked talent would otherwise get selected as a
    # bare normal/flaw/class/trainer feat (no description, not a real feat). Clear it now that talent
    # selection is done. (Safe: this list was already reset by _pick_talents_in_sphere, so no legitimate
    # class-talent cross-pollination is lost; non-spheres characters hit the early returns above.)
    character.chooseable_talents = []
    return bundle


def add_overflow_talents(character, chosen, counts, n_extra):
    """Trainer-funded surplus (25% "trainer-backed" branch): pick up to ``n_extra`` MORE talents across
    the already-chosen spheres, reusing the live per-sphere ``counts`` so the §8 advanced-talent gate
    (``_advanced_quota``) keeps holding. These ride the 2 dedicated trainers, so they cost no feat
    slots. Returns ``(magic_items, combat_items)`` of extra talent items (may be shorter than
    ``n_extra`` if the chosen spheres run dry)."""
    magic_items, combat_items = [], []
    if n_extra <= 0 or not chosen:
        return magic_items, combat_items
    pool = [(s, sy) for s, sy in chosen if s in counts]
    while n_extra > 0 and pool:
        progressed = False
        for sphere, system in list(pool):
            if n_extra <= 0:
                break
            picks = _pick_talents_in_sphere(character, system, sphere, 1, counts[sphere])
            if picks:
                for p in picks:
                    (magic_items if system == "power" else combat_items).append(_talent_item(*p))
                n_extra -= len(picks)
                progressed = True
            else:
                pool.remove((sphere, system))   # this sphere is exhausted / gated out
        if not progressed:
            break
    character.chooseable_talents = []   # same leak guard as choose_spheres_attr -- this also picks talents
    return magic_items, combat_items
