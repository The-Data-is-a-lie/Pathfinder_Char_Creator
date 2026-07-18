"""Classify a generated NPC into a build archetype (Keep Away Fighter, Team Buffer, Trickster, ...).

An archetype is not just the gear -- it is HOW the character fights: role (Tank/Striker/
Controller/Support/...) crossed with a tactical pattern (zone-denial, hit-and-run, nova, ...).
The roster is deliberately GENERALIZED (v3): no Path-of-War/Spheres-branded entries -- initiators
and sphere practitioners classify into the same generalized archetypes via their disc_*/sph_*
signals (an Iron Tortoise warder is an AC Tank, a Primal Fury charger is a Charger).
The roster lives in Backend/json/build_archetypes.json (research + rationale in
docs/build_archetype_research.md); every entry declares a weighted profile over the FROZEN signal
vocabulary computed by _signals() below, plus hard gates (requires_any / requires_all / vetoes).

Decision path is fully deterministic: gates -> weighted sum -> L1-normalize by the entry's own
weight mass (so many-signal entries can't dominate) -> confidence gap -> tie_break_rank. Ollama
(same endpoint as the backstory module) is only an OPTIONAL refinement that picks among near-tied
finalists; with no model reachable the tie_break_rank winner stands, so results are identical in
production (no Ollama on Render) and locally.
"""
import json
import os
import re
from typing import NamedTuple

from utils.class_func import backstory as _bs

ROSTER_PATH = 'Backend/json/build_archetypes.json'
# Near-tie window on L1-normalized scores (roughly [-1, 1]): candidates within this much of the
# top score are "contenders" -- tie_break_rank (or Ollama, when available) settles between them.
# Kept tight: rank/Ollama arbitrate photo-finishes only, never a real raw-score lead (categorical
# separation is the gates' job, not the tie-break's).
CONFIDENCE_MARGIN = 0.02
MAX_CONTENDERS = 4


class ArchetypeResult(NamedTuple):
    """str(result) is the label, so every existing string consumer keeps working unchanged."""
    label: str
    tactics: str
    family: str
    pattern: str
    confidence: str          # 'high' when the winner cleared CONFIDENCE_MARGIN, else 'low'
    gap: float               # top1 - top2 normalized-score gap
    contenders: tuple        # ((label, score), ...) near-tie set, winner first

    def __str__(self):
        return self.label


_FALLBACK = ArchetypeResult('Generalist', 'Adapts to the situation; no single specialization.',
                            'Hybrid', 'adaptable', 'low', 0.0, (('Generalist', 0.0),))


def choose_build_archetype(build, use_api=True):
    """Return an ArchetypeResult for `build` (the dict assembled in main_test). Deterministic;
    `use_api` only lets Ollama arbitrate genuine near-ties. Always returns a result; never raises."""
    try:
        roster = _load_roster()
        sig = _signals(build)
        scored = []
        for label, entry in roster['archetypes'].items():
            score = _score(entry, sig)
            if score is not None:
                scored.append((score, entry.get('tie_break_rank', 10 ** 6), label, entry))
        if not scored:
            return _FALLBACK
        scored.sort(key=lambda t: (-t[0], t[1], t[2]))
        top = scored[0][0]
        gap = top - scored[1][0] if len(scored) > 1 else 1.0
        ties = [t for t in scored if top - t[0] < CONFIDENCE_MARGIN][:MAX_CONTENDERS]
        # Deterministic default: most specific (lowest tie_break_rank) among the near-tied.
        winner = min(ties, key=lambda t: t[1])
        if use_api and len(ties) > 1:
            picked = _refine_with_ollama(build, ties)
            if picked:
                winner = picked
        _, _, label, entry = winner
        contenders = tuple((lbl, round(s, 3)) for s, _, lbl, _ in
                           sorted(ties, key=lambda t: (t[2] != label, -t[0])))
        return ArchetypeResult(
            label, entry.get('tactics', ''), entry.get('family', ''),
            entry.get('tactical_pattern', ''),
            'high' if gap >= CONFIDENCE_MARGIN else 'low', round(gap, 3), contenders)
    except Exception:
        return _FALLBACK


def explain_build_archetype(build, top_n=5):
    """Tuning/debug aid: top-N (label, normalized score, {signal: contribution}) plus the computed
    signal vector. Not used by the pipeline."""
    roster = _load_roster()
    sig = _signals(build)
    rows = []
    for label, entry in roster['archetypes'].items():
        score = _score(entry, sig)
        if score is None:
            continue
        denom = sum(abs(w) for w in entry.get('signals', {}).values()) or 1.0
        parts = {n: round(w * sig.get(n, 0.0) / denom, 3)
                 for n, w in entry.get('signals', {}).items() if sig.get(n, 0.0)}
        rows.append((label, round(score, 3), parts))
    rows.sort(key=lambda r: -r[1])
    return rows[:top_n], {k: round(v, 3) for k, v in sig.items() if v}


# --------------------------------------------------------------------------- #
# roster
# --------------------------------------------------------------------------- #

_roster_cache = None


def _load_roster():
    global _roster_cache
    if _roster_cache is None:
        path = ROSTER_PATH
        if not os.path.exists(path):   # callers normally run from the repo root; be robust anyway
            path = os.path.join(os.path.dirname(__file__), '..', '..', 'json', 'build_archetypes.json')
        with open(path, encoding='utf-8') as f:
            _roster_cache = json.load(f)
    return _roster_cache


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #

def _score(entry, sig):
    """L1-normalized weighted score, or None when a hard gate excludes the entry outright."""
    for gate in entry.get('requires_all') or []:
        if sig.get(gate['signal'], 0.0) < gate.get('min', 1.0):
            return None
    req = entry.get('requires_any') or []
    if req and not any(sig.get(g['signal'], 0.0) >= g.get('min', 1.0) for g in req):
        return None
    for veto in entry.get('vetoes') or []:
        if sig.get(veto['signal'], 0.0) >= veto.get('min', 1.0):
            return None
    weights = entry.get('signals') or {}
    denom = sum(abs(w) for w in weights.values()) or 1.0
    return sum(w * sig.get(name, 0.0) for name, w in weights.items()) / denom


# --------------------------------------------------------------------------- #
# signal extraction (FROZEN vocabulary -- roster entries reference these names)
# --------------------------------------------------------------------------- #

_SPELL_FAMILIES = {
    'spell_blast': ('fireball', 'lightning', 'scorching', 'burning', 'cone of cold', 'disintegrate',
                    'magic missile', 'acid', 'flame strike', 'fire storm', 'meteor', 'shocking',
                    'inflict', 'harm', 'destruction', 'blade barrier', 'chain lightning', 'fire snake'),
    'spell_control': ('wall of', 'hold ', 'black tentacles', 'confusion', 'slow', 'entangle',
                      'grease', 'web', 'pit', 'dominate', 'charm', 'sleep', 'stinking cloud',
                      'cloudkill', 'maze', 'banish', 'fear', 'blindness', 'glitterdust', 'suggestion',
                      'daze', 'dazing', 'bestow curse', 'feeblemind', 'dispel', 'antimagic'),
    'spell_heal': ('cure ', 'heal', 'restoration', 'breath of life', 'remove ', 'regenerate',
                   'raise dead', 'resurrection', 'delay poison', 'lesser restoration'),
    'spell_buff': ('haste', 'bless', 'enlarge', 'heroism', 'prayer', 'magic vestment',
                   'magic weapon', 'shield of faith', 'barkskin', 'divine favor', 'righteous might',
                   'transformation', 'displacement', 'mirror image', 'stoneskin', 'divine power',
                   'blur', 'protection from', 'resist energy', 'freedom of movement'),
    'spell_summon': ('summon ', 'planar ally', 'planar binding', 'gate', 'animate dead',
                     'create undead', 'call ', 'mount'),
}

# Discipline -> tactical tags (identity per docs/build_archetype_research.md).
_DISCIPLINE_TAGS = {
    'primal fury': ('rage',), 'broken blade': ('dual', 'mobile'), 'veiled moon': ('stealth', 'mobile'),
    'solar wind': ('ranged',), 'thrashing dragon': ('dual', 'mobile'), 'iron tortoise': ('tank', 'counter'),
    'golden lion': ('support',), 'scarlet throne': ('counter',), 'silver crane': ('support',),
    'steel serpent': ('control', 'stealth'), 'riven hourglass': ('control', 'counter'),
    'elemental flux': ('control',), 'sleeping goddess': ('control', 'support'),
    'mithral current': ('counter', 'mobile'), 'eternal guardian': ('tank', 'control'),
    'shattered mirror': ('control',), 'tempest gale': ('ranged', 'control'),
    'piercing thunder': ('mobile', 'control'), 'black seraph': ('control', 'rage'),
    'cursed razor': ('control',), "fool's errand": ('counter', 'mobile'),
}

_SPHERES_OF_POWER = {
    'alteration', 'bear', 'blood', 'conjuration', 'creation', 'dark', 'death', 'destruction',
    'divination', 'enhancement', 'fallen fey', 'fate', 'illusion', 'life', 'light', 'mana', 'mind',
    'nature', 'protection', 'telekinesis', 'time', 'war', 'warp', 'weather',
}
_SPHERES_OF_MIGHT = {
    'alchemy', 'athletics', 'barrage', 'barroom', 'beastmastery', 'berserker', 'boxing', 'brute',
    'dual wielding', 'duelist', 'equipment', 'fencing', 'gladiator', 'guardian', 'lancer',
    'leadership', 'open hand', 'scoundrel', 'scout', 'shield', 'sniper', 'tech', 'tinker', 'trap',
    'warleader', 'wrestling',
}
_SPHERE_TAGS = {
    'sph_blast': ('destruction', 'war'),
    'sph_control': ('illusion', 'mind', 'dark', 'time', 'fate', 'weather', 'telekinesis', 'death'),
    'sph_heal': ('life',),
    'sph_tank': ('guardian', 'protection', 'shield'),
    'sph_beast': ('beastmastery',),
    'sph_skirmish': ('scout', 'athletics', 'warp'),
    'sph_buff': ('enhancement', 'warleader', 'leadership'),
    'sph_summon': ('conjuration',),
    'sph_grapple': ('wrestling', 'boxing', 'brute', 'open hand'),
    'sph_rage': ('berserker',),
}

# feat_buckets.json leaf path -> signal name (counts capped at 3 -> 0..1).
_BUCKET_SIGNALS = {
    ('martial', 'melee', 'attack action'): 'feat_melee_attack',
    ('martial', 'melee', 'full attack'): 'feat_melee_full',
    ('martial', 'melee', 'cmb'): 'feat_cmb',
    ('martial', 'melee', 'tank'): 'feat_tank',
    ('martial', 'ranged', 'attack action'): 'feat_ranged_attack',
    ('martial', 'ranged', 'full attack'): 'feat_ranged_full',
    ('magical', 'control'): 'feat_magic_control',
    ('magical', 'blaster'): 'feat_magic_blast',
    ('magical', 'enhancer'): 'feat_magic_buff',
}

_FINESSE_WEAPONS = ('rapier', 'whip', 'elven curve blade', 'estoc', 'kukri', 'starknife',
                    'scimitar', 'dagger', 'shortsword', 'short sword', 'kama', 'sai', 'wakizashi')
_MOBILITY_FEATS = ('spring attack', 'shot on the run', 'wind stance', 'lightning stance',
                   'mobility', 'dodge', 'nimble moves', 'flyby attack')
_AOO_FEATS = ('combat reflexes', 'stand still', 'improved trip', 'greater trip',
              'vicious stomp', 'paired opportunists', 'bodyguard')
_MOUNTED_FEATS = ('mounted combat', 'ride-by attack', 'spirited charge', 'trick riding',
                  'mounted archery', 'unseat')
_PRECISION_CLASSES = {'rogue', 'ninja', 'slayer', 'vigilante', 'investigator', 'assassin', 'stalker'}
_STEALTH_CLASSES = {'rogue', 'ninja', 'stalker', 'vigilante', 'slayer'}


def _signals(build):
    """One generic pass: build dict -> {signal name: 0..1}. Archetype entries only ever reference
    these names, so new roster entries never require code changes here unless they need a
    genuinely new feature."""
    sig = {}
    # Unchained variants roll as "summoner (unchained)" etc. -- strip parenthetical qualifiers so
    # every class-identity check (summoner_pet, precision, stealthy, mobile, ...) sees the base name.
    classes = [re.sub(r'\s*\([^)]*\)', '', str(c)).strip().lower()
               for c in (build.get('class_names') or [])]
    primary = re.sub(r'\s*\([^)]*\)', '', str(build.get('primary_class') or '')).strip().lower()
    if primary and primary not in classes:
        classes.append(primary)
    class_entries = build.get('class_entries') or []
    total_level = int(build.get('total_level') or sum(int(c.get('level') or 0) for c in class_entries) or 1)
    feats_lower = [str(f).lower() for f in (build.get('feats') or [])]
    feats_blob = ' | '.join(feats_lower)

    # -- casting --
    spell_levels = [int(x or 0) for x in (build.get('spell_levels') or [])]
    if not spell_levels:   # fallback: parse the "name (spells up to level N)" strings
        spell_levels = [int(m) for s in (build.get('casting') or [])
                        for m in re.findall(r'level (\d+)', str(s))]
    highest = max(spell_levels or [0])
    sig['caster_tier'] = min(1.0, highest / 9.0)

    bab = str(build.get('bab_tier') or 'M').upper()[:1]
    sig['bab_high'] = 1.0 if bab == 'H' else 0.0
    sig['bab_mid'] = 1.0 if bab == 'M' else 0.0
    sig['bab_low'] = 1.0 if bab == 'L' else 0.0

    # Full-BAB chassis (paladin, ranger, bloodrager) never counts as caster-primary -- their
    # spells support a martial game plan. The old `highest >= 4` arm vetoed high-level paladins
    # out of every martial archetype, stranding them on Generalist.
    sig['caster_primary'] = 1.0 if (highest >= 2 and not sig['bab_high']) else 0.0

    spells_lower = [str(s).lower() for s in (build.get('spells') or [])]
    for name, keywords in _SPELL_FAMILIES.items():
        hits = sum(1 for s in spells_lower if any(k in s for k in keywords))
        sig[name] = hits / len(spells_lower) if spells_lower else 0.0

    # -- Path of War --
    il = int(build.get('initiator_level') or 0)
    sig['initiator'] = min(1.0, il / total_level) if il else 0.0
    disc_tags = set()
    for d in (build.get('disciplines') or []):
        disc_tags.update(_DISCIPLINE_TAGS.get(str(d).strip().lower(), ()))
    for tag in ('tank', 'control', 'support', 'rage', 'mobile', 'stealth', 'ranged', 'dual', 'counter'):
        sig['disc_' + tag] = 1.0 if tag in disc_tags else 0.0

    # -- Spheres --
    spheres = [str(s).strip().lower() for s in (build.get('spheres') or [])]
    n_spheres = len(spheres) or 1
    sig['sphere_power'] = sum(1 for s in spheres if s in _SPHERES_OF_POWER) / n_spheres
    sig['sphere_might'] = sum(1 for s in spheres if s in _SPHERES_OF_MIGHT) / n_spheres
    for name, members in _SPHERE_TAGS.items():
        sig[name] = 1.0 if any(s in members for s in spheres) else 0.0
    sig['sphere_invest'] = min(1.0, int(build.get('sphere_mana_pool') or 0) / 10.0)

    # -- weapon --
    weapon = str(build.get('weapon') or '').strip().lower()
    category = str(build.get('weapon_category') or '').lower()
    groups = str(build.get('weapon_groups') or '').lower()
    special = str(build.get('weapon_special') or '').lower()
    critical = str(build.get('weapon_critical') or '')
    # 'Close' group covers cestus/punching dagger/gauntlet -- ordinary light weapons, not a
    # martial-artist identity. Only the Monk group and true unarmed/handwrap attacks qualify.
    unarmed = 'monk' in groups or 'unarmed' in weapon or 'handwrap' in weapon
    ranged = 'ranged' in category or 'firearm' in groups or 'thrown' in groups
    sig['wpn_none'] = 0.0 if weapon else 1.0
    sig['wpn_unarmed'] = 1.0 if (weapon and unarmed) else 0.0
    sig['wpn_ranged'] = 1.0 if ranged else 0.0
    sig['wpn_firearm'] = 1.0 if ('firearm' in groups or 'firearm' in category) else 0.0
    sig['wpn_thrown'] = 1.0 if 'thrown' in (groups + category) else 0.0
    melee = weapon and not ranged and not unarmed
    sig['wpn_light'] = 1.0 if (melee and 'light' in category) else 0.0
    sig['wpn_one_handed'] = 1.0 if (melee and 'one-hand' in category) else 0.0
    sig['wpn_two_handed'] = 1.0 if (melee and 'two-hand' in category) else 0.0
    sig['wpn_finesse'] = 1.0 if (sig['wpn_light'] or 'weapon finesse' in feats_blob
                                 or any(w in weapon for w in _FINESSE_WEAPONS)) else 0.0
    sig['wpn_reach'] = 1.0 if ('reach' in special or 'lunge' in feats_blob) else 0.0
    # A plain 19-20 longsword is not a crit-fishing BUILD -- only a wide 18-20 threat range or
    # deliberate crit-feat investment signals the playstyle.
    sig['crit_fisher'] = 1.0 if ('18-20' in critical
                                 or 'improved critical' in feats_blob
                                 or 'critical focus' in feats_blob) else 0.0
    sig['two_weapon'] = 1.0 if ('two-weapon' in feats_blob or 'double slice' in feats_blob) else 0.0

    # -- defense --
    armor_type = build.get('armor_type')
    sig['armor_none'] = 1.0 if not armor_type else 0.0
    sig['armor_light'] = 1.0 if armor_type == 'L' else 0.0
    sig['armor_medium'] = 1.0 if armor_type == 'M' else 0.0
    sig['armor_heavy'] = 1.0 if armor_type == 'H' else 0.0
    sig['shield'] = 1.0 if build.get('shield_flag') else 0.0

    # -- curated feat buckets --
    buckets = build.get('feat_buckets') or {}
    pools = {}
    for path, name in _BUCKET_SIGNALS.items():
        node = buckets
        for key in path:
            node = node.get(key, {}) if isinstance(node, dict) else {}
        pools[path] = {str(f).lower() for f in node} if isinstance(node, list) else set()
    # Generic feats curated into BOTH the melee and ranged buckets (Weapon Focus, ...) carry no
    # melee-vs-ranged information -- counting them lets a longsword fighter satisfy a ranged gate.
    melee_all = set().union(*(p for path, p in pools.items() if path[:2] == ('martial', 'melee')))
    ranged_all = set().union(*(p for path, p in pools.items() if path[:2] == ('martial', 'ranged')))
    ambiguous = melee_all & ranged_all
    for path, name in _BUCKET_SIGNALS.items():
        pool = pools[path] - (ambiguous if path[0] == 'martial' else set())
        hits = sum(1 for f in feats_lower if any(f.startswith(p) or p in f for p in pool))
        sig[name] = min(1.0, hits / 3.0)

    # -- stats --
    stats = build.get('stat_dict') or {}
    s_str, s_dex, s_con = (int(stats.get(k) or 0) for k in ('str', 'dex', 'con'))
    main = str(build.get('main_stat') or '').lower()[:3]
    for stat in ('str', 'dex', 'con', 'int', 'wis', 'cha'):
        sig['main_' + stat] = 1.0 if main == stat else 0.0
    sig['con_focus'] = 1.0 if (s_con >= max(s_str, s_dex) and s_con >= 14) else 0.0
    sig['str_over_dex'] = 1.0 if s_str > s_dex else 0.0
    sig['dex_over_str'] = 1.0 if s_dex > s_str else 0.0

    # -- tactics & pets --
    features_blob = ' | '.join(str(f).lower() for f in (build.get('class_feature_names') or []))
    sig['precision'] = 1.0 if (set(classes) & _PRECISION_CLASSES
                               or 'sneak attack' in features_blob or 'death attack' in features_blob
                               or 'sneak attack' in feats_blob) else 0.0
    sig['stealthy'] = 1.0 if (set(classes) & _STEALTH_CLASSES or sig['disc_stealth']
                              or 'stealthy' in feats_blob or 'hellcat stealth' in feats_blob) else 0.0
    sig['mobile'] = 1.0 if ('monk' in classes
                            or any(f in feats_blob for f in _MOBILITY_FEATS)) else 0.0
    sig['aoo_control'] = min(1.0, sum(1 for f in _AOO_FEATS if f in feats_blob) / 2.0)
    sig['companion'] = 1.0 if build.get('companion') else 0.0
    sig['summoner_pet'] = 1.0 if 'summoner' in classes else 0.0
    sig['mounted'] = 1.0 if ('cavalier' in classes
                             or any(f in feats_blob for f in _MOUNTED_FEATS)) else 0.0
    sig['multiclass'] = 1.0 if len(classes) > 1 else 0.0
    primary_level = max([int(c.get('level') or 0) for c in class_entries] or [total_level])
    sig['class_split'] = 1.0 - (primary_level / total_level) if total_level else 0.0

    # -- class-identity accents (offense/support engines invisible to spell & weapon signals) --
    sig['kinetic_blast'] = 1.0 if 'kineticist' in classes else 0.0
    sig['bomb_thrower'] = 1.0 if 'alchemist' in classes else 0.0
    sig['performer'] = 1.0 if ('bard' in classes or 'skald' in classes) else 0.0
    return sig


# --------------------------------------------------------------------------- #
# optional Ollama refinement (near-ties only; deterministic winner stands on any failure)
# --------------------------------------------------------------------------- #

def _norm(s):
    return re.sub(r'[^a-z0-9]+', '', str(s or '').lower())


def _refine_with_ollama(build, ties):
    """Ask the model to pick among the near-tied finalists; return that tie tuple or None."""
    try:
        roster_lines = '\n'.join(
            f"- {label}: {entry.get('definition', '')} Tactics: {entry.get('tactics', '')}"
            for _, _, label, entry in ties)
        flat = _bs._flat
        facts = '\n'.join(f'{k}: {flat(build.get(key))}' for k, key in (
            ('Classes', 'classes'), ('Main stat', 'main_stat'), ('Stats', 'stats'),
            ('Casting', 'casting'), ('Notable spells', 'spells'), ('Spheres', 'spheres'),
            ('Disciplines', 'disciplines'), ('Weapon', 'weapon'), ('Armor', 'armor'),
            ('Shield', 'shield'), ('Feats', 'feats')) if flat(build.get(key)))
        messages = [
            {'role': 'system', 'content':
                'You are a Pathfinder 1e build analyst. These archetypes all roughly fit the '
                'character; pick the ONE whose tactics best match how this build actually fights. '
                'Answer with the archetype name only.\n' + roster_lines},
            {'role': 'user', 'content': 'BUILD:\n' + facts},
        ]
        reply = _norm(_bs._try_ollama(messages, {'temperature': 0.2, 'max_tokens': 60},
                                      tag='build archetype tie-break'))
        if not reply:
            return None
        hits = [t for t in ties if _norm(t[2]) == reply] or \
               [t for t in ties if _norm(t[2]) in reply]
        return hits[0] if len(hits) == 1 else None
    except Exception:
        return None
