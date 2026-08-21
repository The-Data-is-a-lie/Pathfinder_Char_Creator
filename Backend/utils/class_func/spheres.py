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
  * **Casting tradition (Spheres of Power).** EVERY character rolls one (latent flavor for
    non-casters): a CAM (highest mental stat), general drawbacks (HR3: no cap), 2 drawbacks -> 1 boon,
    and leftover drawbacks -> bonus spell points on the triangular chart (1->1, 2->3, 3->6, 4->10...).
  * **HR4 mana pool.** Any magic content -> pool = highest mental mod (min 1) + tradition bonus SP.

Data (built by ``Backend/scripts/extract_spheres_talents.py`` from the pf1spheres compendium):
  spheres_of_power.json, spheres_of_might_enriched.json, sphere_feats.json, advanced_talents.json,
  and (harvested) spheres_traditions.json.

V4 wall pass (ruling 2026-08-13): a full-house wall (optimize + house_rules, ac_combat primary)
always dabbles ONE defensive might sphere -- any of DEFENSIVE_SPHERES, shield-weighted -- and its
talent picks inside that sphere claim the curated fight-state talents first. Everything is gated
on _house_wall(), so the flag-off and random paths are untouched.

Public API:
    randomize_spheres_num(character)  -> int, also stored on character.sphere_count
    choose_spheres_attr(character)    -> export bundle dict (empty defaults when count 0)
"""
import json
import os
import random
import re
from math import ceil

from utils.class_func.generic_func import no_prereq_loop
from utils.class_func.skill_ranks import highest_mental_mod, final_ability_mod
from utils.class_func.buff_match import match as match_buffs
import utils.data as data

# --------------------------------------------------------------------------- #
# Tunables (named so the curve is easy to retune)
# --------------------------------------------------------------------------- #
# TEMP (testing 2026-06-16): 0-weight zeroed so an opted-in character ALWAYS rolls >=1 sphere
# (subject to feat budget). REVERT to [1, 4, 3, 2] before shipping.
SPHERE_COUNT_WEIGHTS = [0, 4, 3, 2]      # weights for 0,1,2,3 spheres when the flag is on
# TEMP (testing): force all of a dabbler's talents into ONE sphere so the normals satisfy the
# same-sphere prerequisites that gate advanced/legendary talents. Set False to restore 1-3 spheres.
SINGLE_SPHERE_TESTING = True

MAX_EXTRA_TALENT_FEATS = 2               # cap on Extra-Talent feats beyond one entry feat per sphere
KEEP_FREE_FEATS = 1                      # try to leave the character at least this many normal feats
DRAWBACK_MIN, DRAWBACK_MAX = 2, 6        # general drawbacks rolled for a casting tradition (HR3: no cap)
ADVANCED_RATIO = 7                       # §8: this many normal-talent-equivalents per advanced talent

# How many talents a dabbler ROLLS for, by character level. The flat 8 this replaces was a testing
# convenience, not a rule -- it gave a 1st-level character the same eight talents as a 20th, which is
# how the feat budget came to be over-committed at level 1 (ticket 08: 16/700 generations, all L1).
#
# Read as "level < L -> roll 0..N"; 20+ scales with level so the curve keeps going past the band
# table rather than flattening. randint is INCLUSIVE, and the low end is a real 0 -- a dabbler who
# rolls nothing is a legitimate outcome, not an error.
TALENT_BANDS = ((5, 8), (10, 12), (20, 16))
TALENT_20_PLUS_OFFSET = 4                # 20+ rolls 0..(level - 4); at 20 that is 0..16, continuous

# V4 wall pass (ruling 2026-08-13): the might-side spheres a full-house wall counts as defensive.
# The wall's FIRST sphere comes from this list, always -- "an optimal character can get various
# different spheres (that are focused on defense), not just shield" -- and the talent picker
# prefers the curated fight-state names (power_role.sphere_defense_names) inside them. Shield is
# the only sphere with curated scoring today; the others contribute build variety and render as
# rules text, a recorded blind spot in power_adders._blind until their values are curated.
DEFENSIVE_SPHERES = ('shield', 'guardian', 'dual wielding', 'open hand')


def _house_wall(character):
    """True when this character is an optimized wall built under house_rules -- the only
    population whose sphere behaviour this module changes."""
    role = getattr(character, 'role', None)
    return bool(role and role.get('_house') and 'ac_combat' in (role.get('primaries') or []))


def roll_talent_budget(level):
    """How many sphere talents this character rolls for, before funding is applied."""
    level = int(level or 0)
    for band_level, high in TALENT_BANDS:
        if level < band_level:
            return random.randint(0, high)
    return random.randint(0, max(0, level - TALENT_20_PLUS_OFFSET))


def feats_for_talents(paid_magic_n, paid_combat_n):
    """Feats needed to pay for a given split of BUDGET-PAID talents (HR1).

    One Extra-Talent feat buys 2 talents of one system (HR2: both share a system), except the first
    paid magic talent, which rides Basic Magic Training and buys only 1 (it also grants the sphere
    access). This is the exact inverse of the feat-building loop below, and the two must agree -- if
    that loop changes, this changes with it, or the budget reservation goes wrong in silence."""
    feats = 0
    if paid_magic_n >= 1:
        feats += 1                                       # Basic Magic Training: 1 talent
        feats += ceil((paid_magic_n - 1) / 2)            # the rest pair up
    feats += ceil(paid_combat_n / 2)
    return feats

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
    """Roll 0-3 spheres for a dabbler. No-op (0) unless ``character.spheres_flag`` is truthy ('Y').

    Exception (V4 wall pass): a full-house wall ALWAYS gets exactly one sphere, by design, even
    with the flag off -- the defensive-sphere package is part of the ruled build. Deterministic 1
    rather than a roll, so the flag-off branch consumes no RNG it did not before.
    """
    flag = str(getattr(character, "spheres_flag", "N") or "N").upper()
    if flag not in ("Y", "YES", "TRUE", "1"):
        if _house_wall(character):
            character.sphere_count = 1
            return 1
        character.sphere_count = 0
        return 0
    # The count is now UNCAPPED by the feat budget: the generator guarantees that a selected dabbler
    # actually receives spheres by funding them with PRIORITY over normal feats (see main_test's
    # PoW/Spheres guarantee block). We no longer zero the roll when the leftover budget is tight.
    n = random.choices([0, 1, 2, 3], weights=SPHERE_COUNT_WEIGHTS, k=1)[0]
    if SINGLE_SPHERE_TESTING and n > 0:
        n = 1                            # TEMP: concentrate the flat-8 talents into one sphere for testing
    if _house_wall(character):
        n = max(1, n)                    # the wall's defensive sphere is by design, never a 0 roll
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
        # V4 wall pass: inside a defensive sphere, a full-house wall claims the curated
        # fight-state talents (power_adders.sphere_defense) first -- the same greedy-then-random
        # shape as the PoW stance picker. Everyone else's draw is untouched.
        if _house_wall(character) and sphere in DEFENSIVE_SPHERES:
            from utils.class_func.power_role import sphere_defense_names
            curated = [c for c in candidates if c in sphere_defense_names()]
            if curated:
                candidates = curated
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


# Curated numeric buffs for Spheres-of-MIGHT (combat) talents live in
# json/class_data/spheres/combat_talent_changes.json, keyed {Sphere: {Talent: {...}}} in
# _display_name casing, and are loaded/matched by utils/class_func/buff_match.py (kind 'talent').
# Magic (Power) talents stay description-only -- they cast effects, not passive self-buffs.
# Gaps are accumulated here and collected into the payload's buff_gaps by main_test.
_TALENT_GAPS = []


def _talent_item(sphere, system, name, rec):
    desc = rec.get("description") or rec.get("benefit") or ""
    # Reliable advanced/legendary flag for the sheet (mirrors _is_advanced): the compendium clone the
    # front-end builds carries no advanced marker, so the front-end relies on this to label "(Advanced)"
    # and sort advanced talents to the bottom of each sphere.
    advanced = (str(rec.get("type", "")).lower() == "advanced"
                or _talent_match_norm(name) in _advanced_set(system, sphere))
    disp_sphere, disp_name = _display_name(sphere), _display_name(name)
    # Numeric buffs land on the Foundry "Changes" tab for combat talents only (Power = text-only).
    buff = {}
    if system == "might":
        _matched, _gaps = match_buffs('talent', [disp_name], section=disp_sphere)
        buff = _matched.get(disp_name) or {}
        _TALENT_GAPS.extend(_gaps)
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


def _mentor_is_power(t):
    """Is this mentor-funded talent a Spheres-of-Power one? ``system`` may be raw ("power"/"might")
    or the display string ("Spheres of Power") -- both handled."""
    return "power" in str(t.get("system", "")).lower()


def mentor_feat_worth(talents):
    """How many FEATS' worth a Spheres Mentor funded -- the rank the trainer is labelled with.

    HR1 bundles 2 talents per Extra-Talent feat and HR2 forbids mixing systems in one pair, so the
    count is per-system ``ceil(n / 2)``. That is exactly the number of "Extra ... Talent" lines
    ``mentor_sphere_summary`` prints, so the printed description and the rank can never disagree.
    """
    talents = talents or []
    n_power = sum(1 for t in talents if _mentor_is_power(t))
    n_might = len(talents) - n_power
    return -(-n_power // 2) + -(-n_might // 2)


def mentor_sphere_summary(spheres_chosen, talents):
    """HTML description for the dedicated "Spheres Mentor" trainer (25% trainer-backed branch): the
    spheres it funded + the OFF-BUDGET talents it taught beyond the character's own budget, presented as
    HR1 Extra-Talent feats (one "Extra X Talent > Extra X Talent" per 2 talents) followed by the talent
    names. ``talents`` is a list of {name, sphere, system} dicts (non-budget-paid flat-8 + overflow)."""
    if not talents:
        return "A dedicated mentor who funded this character's sphere talents beyond their own study."

    _is_power = _mentor_is_power

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
    # Append-order pick lists plus a pick -> item map, so a caller that has to DROP unfunded talents
    # can rebuild the item lists exactly rather than filtering them by name. Name matching was not
    # good enough: the item carries a display-cased name while the pick carries the raw one, so a
    # filter silently kept talents nobody paid for.
    magic_order, combat_order, item_of = [], [], {}

    def _take(sphere, system, want_advanced):
        ds = datasets[sphere]
        if not ds:
            return False
        character.chooseable_talents = []
        pool = [c for c in no_prereq_loop(character, ds) if c not in taken[sphere]]
        cands = [c for c in pool if _is_advanced(c, ds, adv_sets[sphere]) == want_advanced]
        if not cands:
            return False
        # V4 wall pass: inside a defensive sphere, a full-house wall claims the curated
        # fight-state talents (power_adders.sphere_defense) first -- the PoW stance picker's
        # greedy-then-random shape. Everyone else's draw is untouched.
        if _house_wall(character) and sphere in DEFENSIVE_SPHERES:
            from utils.class_func.power_role import sphere_defense_names
            curated = [c for c in cands if c in sphere_defense_names()]
            if curated:
                cands = curated
        name = random.choice(cands)
        rec = ds[name]
        taken[sphere].add(name)
        character.chooseable.add(name)                   # let dependent talents chain off this one
        counts[sphere]["advanced" if want_advanced else "normal"] += 1
        pick = (sphere, system, name, rec)
        picks_by_sphere[sphere].append(pick)
        item = _talent_item(*pick)
        (magic_items if system == "power" else combat_items).append(item)
        (magic_order if system == "power" else combat_order).append(pick)
        item_of[id(pick)] = item
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
    return magic_items, combat_items, picks_by_sphere, magic_order, combat_order, item_of


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


def choose_spheres_attr(character, max_feats=None, trainer_backed=False, mentor_talents=None,
                        talent_budget=None, max_budget_feats=None):
    """Select sphere talents + a feat slot for each BUDGET-PAID talent; return the bundle.

    Empty defaults when ``character.sphere_count`` is 0 (flag off). Each budget-paid talent is tracked
    by an HR1 "Extra Talent > Extra Talent" feat (2 talents per feat; the first magic talent uses Basic
    Magic Training, 1 talent + access). ``trainer_backed`` (the 25% branch): only ~half the talents are
    budget-paid and get feats; the rest are funded by the 2 dedicated Spheres Mentor trainers (tracked
    there, not here). Lean characters pay for all their talents.

    Two callers-supplied numbers decide how many talents survive, and they are NOT the same thing:

    * ``talent_budget`` -- how many talents are ROLLED for, from ``roll_talent_budget(level)``. Level-
      scaled; ``None`` falls back to the historical flat 8 so the attic/ smoke scripts still run.
    * ``max_budget_feats`` -- how many FEATS the character can actually spend here, i.e. what is left
      of the feat budget after Path of War and professions take their share. Talents the feat budget
      and the mentor together cannot fund are DROPPED, not granted (no freebies -- HR1's whole point
      is that talents cost feats). ``None`` means "unbounded", for the same smoke scripts.

    That second parameter is the fix for ticket 08's level-1 over-commit: the affordability was
    already being computed by the caller and then thrown away, so the feat count followed the talent
    count instead of the budget. ``max_feats`` is the vestige of that era -- accepted for
    backward-compat, never read. The generator reserves the realized feats with priority.
    """
    # Per-character gap accumulator; main_test folds character.talent_buff_gaps into buff_gaps.
    del _TALENT_GAPS[:]
    character.talent_buff_gaps = _TALENT_GAPS

    bundle = _empty_bundle()
    # HR: EVERY character carries a casting tradition (drawbacks/boons + casting ability) -- for
    # non-casters it is latent flavor describing how their magic would work if they ever picked any
    # up. Rolled before the early returns below so pure martials get one too; the mana pool and the
    # talent/feat machinery stay gated on actually taking sphere content.
    tradition = _choose_casting_tradition(character)
    bundle.update({
        "casting_tradition": tradition,
        # Flat name-only mirrors (back-compat surface). casting_tradition.drawbacks/boons are already
        # name strings; the rich text lives in casting_tradition.drawbacks_detail/boons_detail.
        "sphere_drawbacks": tradition.get("drawbacks", []),
        "sphere_boons": tradition.get("boons", []),
        "sphere_traits": tradition.get("drawbacks", []) + tradition.get("boons", []),
    })
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
    # V4 wall pass: the full-house wall's FIRST sphere is a defensive might sphere, by design --
    # any of DEFENSIVE_SPHERES, weighted toward shield because it is the one with curated
    # fight-state scoring today (the others are build variety the metric records as blind).
    if _house_wall(character):
        defensive = [s for s in DEFENSIVE_SPHERES if s in pool_m]
        if defensive:
            weights = [3 if s == 'shield' else 1 for s in defensive]
            sphere = random.choices(defensive, weights=weights, k=1)[0]
            used.add(("might", sphere))
            chosen.append((sphere, "might"))
    for _ in range(n - len(chosen)):
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

    # ---- pick the rolled talents first (talent COUNT is decoupled from the feat slots) ---- #
    # A spheres-selected dabbler rolls for `talent_budget` talents (all but one normal, 1 advanced);
    # the 25% "trainer-backed" branch adds overflow talents on top in main_test. How many of these
    # SURVIVE is decided further down by what the feat budget and the mentor can fund.
    counts = {s: {"normal": 0, "advanced": 0, "feats": 0} for s, _ in chosen}
    # How many talents to pick. `talent_budget` is the level-scaled roll; the flat 7+1 remains the
    # default only so the older smoke scripts in attic/ still run.
    _want = 8 if talent_budget is None else max(0, int(talent_budget))
    if _want == 0:
        return bundle                                 # rolled nothing: a legitimate outcome
    _n_advanced = 1 if _want >= 1 else 0
    (magic_items, combat_items, picks_by_sphere,
     _magic_order, _combat_order, _item_of) = _pick_flat_talents(
        character, chosen, counts, n_normal=_want - _n_advanced, n_advanced=_n_advanced)
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

    # The magic-side bonus feats are rolled HERE, before the talents are capped, because they come
    # out of the SAME feat budget. Rolling them after the cap (as this used to) meant the budget was
    # sized for the talents alone and then quietly overspent by one or two -- which is most of what
    # the ticket-08 gate was catching once the talent count itself was fixed.
    _bonus_names, _bonus_descs = ([], {})
    if took_magic:
        _bonus_names, _bonus_descs = _roll_magic_sphere_feats(character, chosen, counts)
    if max_budget_feats is not None and len(_bonus_names) >= max_budget_feats:
        # Talents are the point of taking a sphere; the bonus feat is a flavour extra. When the
        # budget cannot carry both, the extra goes.
        _bonus_names, _bonus_descs = [], {}
    _talent_feat_budget = (None if max_budget_feats is None
                           else max(0, max_budget_feats - len(_bonus_names)))
    if trainer_backed and mentor_talents is not None:
        budget_paid = max(0, n_total - mentor_talents)   # the dedicated mentor funds min(mentor_talents, n_total) off-budget
    elif trainer_backed:
        budget_paid = (n_total + 1) // 2                 # fallback: mentor funds the off-budget half
    else:
        budget_paid = n_total                            # lean: the character pays for all its talents

    # ---- NO FREEBIES: every talent is paid for, by the feat budget or by a mentor ---- #
    # The invariant this enforces is `budget_paid + mentor_funded == kept talents`. It used to hold
    # by construction because the talent count was a flat 8 and lean characters simply paid for all
    # of them -- which is exactly how the budget came to be over-committed at 1st level, where 8
    # talents cost more feats than a 1st-level character has (ticket 08).
    #
    # Now the rolled budget can exceed what the character can fund, so the surplus has to go
    # somewhere. It is DROPPED, not granted: a talent nobody paid for is a freebie, and the whole
    # point of HR1 is that talents cost feats.
    mentor_funded = min(int(mentor_talents or 0), n_total) if trainer_backed else 0
    if _talent_feat_budget is not None:
        budget_paid = min(budget_paid, n_total - mentor_funded)
        # Shrink to fit. Done by measuring the ACTUAL magic/combat split rather than by a formula,
        # because the split changes the answer: 2 magic talents cost 2 feats (Basic Magic Training
        # buys only one) while 2 combat talents cost 1. A closed form would have to assume the worst
        # case and would under-grant everyone to protect the edge.
        while budget_paid > 0:
            _pm = sum(1 for p in all_picks[:budget_paid] if p[1] == "power")
            if feats_for_talents(_pm, budget_paid - _pm) <= _talent_feat_budget:
                break
            budget_paid -= 1

    kept = budget_paid + mentor_funded
    if kept < n_total:
        dropped = {id(p) for p in all_picks[kept:]}
        _dropped_names = {p[2] for p in all_picks[kept:]}
        all_picks = all_picks[:kept]
        magic_picks = [p for p in magic_picks if id(p) not in dropped]
        combat_picks = [p for p in combat_picks if id(p) not in dropped]
        for _sphere in list(picks_by_sphere):
            picks_by_sphere[_sphere] = [p for p in picks_by_sphere[_sphere] if id(p) not in dropped]
        # The sheet items and the per-sphere counters have to follow, or the character displays
        # talents it never paid for and the advanced-talent gate is computed against a talent count
        # that no longer exists. Rebuilt from the append-order pick lists, so the surviving items
        # keep their original order and every drop is exact.
        magic_items = [_item_of[id(p)] for p in _magic_order if id(p) not in dropped]
        combat_items = [_item_of[id(p)] for p in _combat_order if id(p) not in dropped]
        for _sphere, _sy in chosen:
            _norm_n = sum(1 for p in picks_by_sphere.get(_sphere, []))
            counts[_sphere]["normal"] = min(counts[_sphere]["normal"], _norm_n)
            counts[_sphere]["advanced"] = min(counts[_sphere]["advanced"], _norm_n)
        n_total = len(all_picks)

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
    # Rolled further up, where the cap could see their cost; appended here so the exported feat
    # order is unchanged (paid talent feats first, then the bonus).
    sphere_feats.extend(_bonus_names)
    desc.update(_bonus_descs)

    # ---- mana pool (magic only; the tradition itself was rolled up front for every NPC) ---- #
    bundle.update({
        "magic_talent_items": magic_items,
        "combat_talent_items": combat_items,
        "sphere_feats": sphere_feats,
        "sphere_feat_tax": sphere_feat_tax,
        "sphere_mana_pool": _mana_pool(character, tradition) if took_magic else 0,
        "spheres_chosen": [{"sphere": s.title(), "system": "power" if sy == "power" else "might"} for s, sy in chosen],
        "sphere_counts": {s.title(): counts[s] for s, _sy in chosen},
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
