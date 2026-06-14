import pandas as pd
import re
from collections import deque
# from utils.class_func.feats import feat_spell_searcher


def feat_tax_func(character, feats, feat_levels=None, already_granted=None):
    '''Feat-tax resolver.

    For each selected feat that is a tax *primary*, return the progression-chain feats granted free
    and bundled onto that primary. A primary is a "base" feat (has dependents in the feats.csv
    prerequisite graph but no feat-prerequisite of its own) or an explicit feat_tax.json override key,
    excluding any feat in `tax_primary_blocklist`. Each primary's chain is DERIVED from the
    prerequisite graph (every feat that transitively requires it). Honors:
      - dependency order (direct dependents first) so a later link can rely on an earlier one;
      - the 2-levels-per-slot cadence: a primary gained at level L_p releases
        floor((char_level - L_p) / 2) *free* (un-owned) chain feats;
      - a chain feat the character already OWNS (independently selected) always bundles, ignoring
        timing; ineligible / missing / Mythic-only links are skipped (they don't block later links);
      - exceptions: a Mythic-only primary does not tax; an "Extra ..." feat grants one free duplicate
        of itself (still 2-level gated).

    Returns {primary_feat: [granted feat names]} (raw lower-case names; the front-end resolves display
    casing). Granted feats do NOT consume feat slots -- they are logged on the primary entry.

    `already_granted` (optional, mutated): a set of lower-case feat names already bundled onto some
    primary. Pass ONE shared set across multiple feat_tax_func calls so overlapping chains (e.g.
    riptide attack under both Improved Drag and Improved Trip) bundle a child exactly once; grants
    made here are added to it, and count as owned for later links' prerequisites.
    '''
    cfg = getattr(character, "feat_tax", None) or {}
    # Keys/list entries are matched through _norm(), so feat_tax.json spellings ("point blank
    # shot") fire for the CSV-spelled selected feat ("Point-Blank Shot") and vice versa.
    explicit = {_norm(k): v for k, v in cfg.get("feat_tax", {}).items()}
    blocklist = {_norm(x) for x in cfg.get("tax_primary_blocklist", [])}
    overrides = {_norm(k): [str(v).lower().strip() for v in vals]
                 for k, vals in cfg.get("tax_chain_override", {}).items()}
    exclude_grants = {_norm(x) for x in cfg.get("tax_exclude_grants", [])}
    if not feats:
        return {}

    char_level = getattr(character, "level", 0) or 0
    if already_granted is None:
        already_granted = set()
    result = {}

    for idx, primary in enumerate(feats):
        primary_l = _norm(primary)

        # Mythic-only feats do not tax (a feat that also has a normal row is the one the generator
        # selected, so it still taxes).
        if _is_mythic_only(primary_l):
            continue

        if primary_l.startswith("extra "):
            chain = [_canon(primary)]                 # "Extra ..." -> one free duplicate of itself
        elif primary_l in overrides:
            chain = _topo_sort([_canon(v) for v in overrides[primary_l]])  # taxes to EXACTLY these
        elif _is_primary(primary_l, explicit, blocklist):
            chain = _derive_chain(primary_l, explicit)
        else:
            continue
        if not chain:
            continue

        # The 2-levels cadence gates only how many *free* (un-owned) chain feats release; feats the
        # character already owns always bundle.
        if feat_levels is not None and idx < len(feat_levels):
            acquired_at = feat_levels[idx] or 0
            free_budget = max(0, (char_level - acquired_at) // 2)
        else:
            free_budget = len(chain)                  # no level info -> all free

        granted = _resolve_chain(character, chain, free_budget, exclude_grants, already_granted)
        if granted:
            result[primary] = granted

    return result


def _ordered_chain(chain_dict):
    '''An explicit feat_tax.json chain {"1": "great cleave", "2": "whirlwind attack"} -> ordered list
    of its values.'''
    try:
        keys = sorted(chain_dict.keys(), key=lambda k: int(k))
    except (ValueError, TypeError):
        keys = list(chain_dict.keys())
    return [str(chain_dict[k]).lower().strip() for k in keys]


# --------------------------------------------------------------------------- #
# Prerequisite graph: primary detection + chain derivation (built once, cached)
# --------------------------------------------------------------------------- #
_PREREQ_GRAPH = None       # (requires, dependents, style_feats, critical_feats, canon)
_DERIVE_CACHE = {}

# Prereq parts the feat-tax resolver treats as auto-satisfied, on TOP of character.filter_pattern:
# level / BAB / tier / ability-score gates. The 2-levels-per-slot cadence already controls *when* a
# chain feat is granted, so a level gate shouldn't separately block a free grant; ability scores
# ("Dex 13") aren't tracked per level and selection already guaranteed final-level legality --
# without this, stat gates permanently blocked whole chains (Rapid Shot, the Two-Weapon line, ...).
_TAX_EXTRA_FILTER = re.compile(
    r'base attack bonus|caster level|character level|hit dice|\blevel\b|\btier\b'
    r'|\b(?:str|dex|con|int|wis|cha|strength|dexterity|constitution|intelligence|wisdom|charisma)\s+\d+'
)

_PUNCT_TRANS = str.maketrans({'-': ' ', '_': ' ', '’': "'"})


def _norm(s):
    '''Canonical feat-name comparison key: lower-cased, stripped, hyphens/underscores read as
    spaces, curly apostrophe as straight, whitespace collapsed. Every name comparison in this
    module goes through it, so punctuation variants ("Point-Blank Shot" as selected from
    data/feats.csv vs the "point blank shot" key in feat_tax.json) resolve to the same feat.'''
    return re.sub(r'\s+', ' ', str(s).lower().strip().translate(_PUNCT_TRANS))


def _canon(s):
    '''Map a name to its lower-cased data/feats.csv spelling when one exists (matched via _norm).
    Names absent from the CSV pass through lowered, so they are skipped at lookup like before.
    Emitting CSV spellings keeps granted chain names consistent with the selected feat lists
    (the tax-child strip compares .lower() forms) and with the FoundryVTT compendium lookup.'''
    _, _, _, _, canon = _prereq_graph()
    return canon.get(_norm(s), str(s).lower().strip())


def _prereq_graph():
    '''Build and cache the feat prerequisite graph from data/feats.csv. `requires[f]` is the set of
    feats f directly requires; `dependents[f]` is the set of feats that require f. Values hold the
    lower-cased CSV names; each key is registered under BOTH the lower-cased CSV name and its
    _norm() form (aliases of the same set), so punctuation variants hit the same entry. `canon`
    maps _norm(name) -> lower-cased CSV name. Only parts of a prerequisite string that match a
    known feat name are kept; self-loops are dropped.'''
    global _PREREQ_GRAPH
    if _PREREQ_GRAPH is None:
        requires, dependents, style_feats, critical_feats, canon = {}, {}, set(), set(), {}
        try:
            df = pd.read_csv('data/feats.csv', sep='|', dtype=str,
                             keep_default_na=False, on_bad_lines='skip')
            for n in df['name']:
                canon.setdefault(_norm(n), str(n).lower().strip())
            if 'style' in df.columns:
                style_feats = {_norm(n)
                               for n, s in zip(df['name'], df['style']) if str(s).strip() == '1'}
            if 'critical' in df.columns:
                critical_feats = {_norm(n)
                                  for n, s in zip(df['name'], df['critical']) if str(s).strip() == '1'}
            for n, pre in zip(df['name'], df['prerequisites']):
                feat = str(n).lower().strip()
                parts = [p.strip() for p in re.sub(r'\.', '', str(pre)).lower().split(',')]
                feat_prereqs = {canon[_norm(p)] for p in parts
                                if _norm(p) in canon and _norm(p) != _norm(feat)}
                if feat_prereqs:
                    req = requires.setdefault(feat, set())
                    req.update(feat_prereqs)
                    requires[_norm(feat)] = req               # alias under the normalized key
                for p in feat_prereqs:
                    dep = dependents.setdefault(p, set())
                    dep.add(feat)
                    dependents[_norm(p)] = dep                # alias under the normalized key
        except Exception:
            pass
        _PREREQ_GRAPH = (requires, dependents, style_feats, critical_feats, canon)
    return _PREREQ_GRAPH


def _is_primary(feat_l, explicit, blocklist):
    '''A selected feat triggers a tax chain when it is NOT blocklisted, NOT a Critical feat, AND it is
    one of: an explicit feat_tax.json override key; a "base" feat (has dependents but no
    feat-prerequisite of its own -- blocklisted prereqs don't count, since those are the
    house-rule-waived free feats like Power Attack / Combat Expertise, making e.g. Improved Drag
    the effective base of its maneuver chain); or a base STYLE feat (style-flagged, has dependents,
    and requires no other style feat -- the start of its style line, e.g. Dragon Style but not
    Dragon Ferocity).'''
    if feat_l in blocklist:
        return False
    if feat_l in explicit:
        return True
    requires, dependents, style_feats, critical_feats, _ = _prereq_graph()
    if feat_l in critical_feats:
        return False                                  # Critical feats do not tax
    if not dependents.get(feat_l):
        return False
    req_n = {_norm(r) for r in requires.get(feat_l, set())}
    if not (req_n - blocklist):
        return True                                   # base feat (no non-waived feat prerequisites)
    if feat_l in style_feats and not (req_n & style_feats):
        return True                                   # base style feat (start of its style line)
    return False


def _derive_chain(feat_l, explicit):
    '''Feats that transitively depend on `feat_l`, ordered by dependency depth (direct dependents
    first, alphabetical tie-break), then any explicit feat_tax.json children not already present (so
    homebrew links not present in feats.csv are preserved).'''
    cached = _DERIVE_CACHE.get(feat_l)
    if cached is None:
        _, dependents, _, _, _ = _prereq_graph()
        seen = set()                                  # lower-cased CSV names
        dq = deque([feat_l])
        while dq:
            cur = dq.popleft()
            for dep in dependents.get(cur, ()):
                if _norm(dep) != feat_l and dep not in seen:
                    seen.add(dep)
                    dq.append(dep)
        seed = sorted(seen)
        # The house rule's named target -- "Improved X grants Greater X" -- must win the first
        # free slot; alphabetical order would otherwise spend a small budget on earlier-named
        # siblings (e.g. "drag down" before "greater drag"). Topo-safe: greater X's only
        # in-chain prerequisite is the root, which is never part of the chain.
        if feat_l.startswith("improved "):
            greater_n = "greater " + feat_l[len("improved "):]
            greater = next((s for s in seed if _norm(s) == greater_n), None)
            if greater is not None:
                seed.remove(greater)
                seed.insert(0, greater)
        cached = _topo_sort(seed)                     # dependency order (improved before greater, ...)
        _DERIVE_CACHE[feat_l] = cached
    chain = list(cached)
    chain_n = {_norm(c) for c in chain}
    for c in _ordered_chain(explicit.get(feat_l, {})):
        c = _canon(c)
        if _norm(c) not in chain_n:
            chain.append(c)
            chain_n.add(_norm(c))
    return chain


def _topo_sort(feats):
    '''Stable topological sort of `feats` (lower-case names): each feat is placed after all of its
    prerequisites that are also in `feats`; ties keep the input order. Guarantees e.g. "improved X"
    before "greater X" even when "greater X" also lists the root feat as a prerequisite (which made a
    BFS shortest-path order tie them and mis-sort alphabetically).'''
    requires, _, _, _, _ = _prereq_graph()
    chain_set = set(feats)
    in_chain_req = {f: (requires.get(f, set()) & chain_set) - {f} for f in feats}
    out, placed, remaining, progressed = [], set(), list(feats), True
    while remaining and progressed:
        progressed = False
        still = []
        for f in remaining:
            if in_chain_req[f] <= placed:
                out.append(f)
                placed.add(f)
                progressed = True
            else:
                still.append(f)
        remaining = still
    out.extend(remaining)                              # cycle leftovers (shouldn't happen) keep order
    return out


def _resolve_chain(character, chain, free_budget, exclude_grants=frozenset(), already_granted=None):
    '''Return the chain feats to bundle on the primary. A feat the character already OWNS (in
    character.chooseable) always bundles, ignoring timing. An un-owned feat is a free grant: bundled
    while the free budget remains and its prerequisites are met, adding each grant to the working set
    so later links can depend on it. Ineligible / missing / over-budget links are SKIPPED -- they do
    not block later links (chains can branch; an early side-link being unavailable shouldn't drop the
    rest). A feat already bundled under an EARLIER primary (`already_granted`, shared + mutated) is
    skipped here but still counts as owned for later links' prerequisites.'''
    feat_desc_dict = {}
    info = feat_spell_searcher(
        character, character.c_class, chain, "feats", "prerequisites", "description", feat_desc_dict
    ) or {}
    info_l = {_norm(k): v for k, v in info.items()}

    if already_granted is None:
        already_granted = set()
    _, _, _, critical_feats, _ = _prereq_graph()
    # All membership checks run on _norm() keys so punctuation variants ("point-blank shot" in a
    # prereq string vs "point blank shot" in chooseable) match; emitted names keep CSV spelling.
    granted_n = {_norm(g) for g in already_granted}
    obtained_n = {_norm(x) for x in character.chooseable} | granted_n
    out = []
    free_used = 0
    for feat_l in chain:
        feat_n = _norm(feat_l)
        if feat_n in critical_feats or feat_n in exclude_grants:
            continue                                  # Critical feats / manual excludes never tax
        if feat_n in granted_n:
            continue                                  # bundled under an earlier primary -> once only
        if feat_n in obtained_n:
            out.append(feat_l)                        # already owned -> always bundle
            already_granted.add(feat_l)
            granted_n.add(feat_n)
            continue
        if free_used >= free_budget:
            continue                                  # free budget spent -> skip (keep scanning owned)
        meta = info_l.get(feat_n)
        if meta is None:
            continue                                  # not in feats.csv (e.g. Mythic-dropped) -> skip
        prereqs_clean = determine_prerequisite_name(meta)
        prereq_parts = [
            part.strip() for part in prereqs_clean.split(",")
            if part.strip()
            and not character.filter_pattern.search(part.strip())
            and not _TAX_EXTRA_FILTER.search(part.strip())
        ]
        if not prereq_parts or {_norm(p) for p in prereq_parts} <= obtained_n:
            out.append(feat_l)
            obtained_n.add(feat_n)
            already_granted.add(feat_l)
            granted_n.add(feat_n)
            free_used += 1
    return out


_MYTHIC_ONLY_NAMES = None


def _is_mythic_only(feat_name_lower):
    '''True only if EVERY data/feats.csv row with this name is type 'Mythic' (no normal version
    exists). A feat that merely has a Mythic same-name variant alongside a normal one (e.g. "Iron
    Will" is listed as both General and Mythic) is NOT treated as Mythic, because the generator only
    selects the normal version. Names absent from feats.csv (e.g. homebrew) are treated as not Mythic.
    The map is read once and cached.'''
    global _MYTHIC_ONLY_NAMES
    if _MYTHIC_ONLY_NAMES is None:
        try:
            df = pd.read_csv('data/feats.csv', sep='|', on_bad_lines='skip')
            types_by_name = {}
            for n, t in zip(df['name'], df['type']):
                types_by_name.setdefault(_norm(n), set()).add(str(t))
            _MYTHIC_ONLY_NAMES = {n for n, types in types_by_name.items() if types == {'Mythic'}}
        except Exception:
            _MYTHIC_ONLY_NAMES = set()
    return _norm(feat_name_lower) in _MYTHIC_ONLY_NAMES


def determine_prerequisite_name(info):
    prerequisites_raw = info.get("prerequisites", "").lower().strip()
    if not prerequisites_raw:
        prerequisites_raw = info.get("prerequisite", "").lower().strip()

    return re.sub(r'\.', '', prerequisites_raw)


# reused custom functions
_CSV_CACHE = {}


def _read_data_csv(types):
    '''Cached read of data/<types>.csv (the feat-tax resolver now queries it once per primary, so
    avoid re-parsing it each call).'''
    cached = _CSV_CACHE.get(types)
    if cached is None:
        cached = pd.read_csv(f'data/{types}.csv', sep='|', on_bad_lines='skip')
        _CSV_CACHE[types] = cached
    return cached


def feat_spell_searcher(character, class_1, chosen_set, types, info_column, info_column_2 = None, feat_desc_dict=None):
    if chosen_set == None:
        return
    if character.c_class == class_1:
        data = _read_data_csv(types)

        if info_column_2 is None:
            extraction_list = ['name', info_column]
        else:
            extraction_list = ['name', info_column, info_column_2]


        query_result = remove_mythic(character, types,data, chosen_set, extraction_list)

        result_dict = {}
        result_dict = remove_dots_dashes(character, result_dict, query_result, info_column)
        feat_desc_dict.update(result_dict)

        return feat_desc_dict

def remove_mythic(character, types, data, chosen_set, extraction_list):

    if chosen_set == None:
        return None

    chosen_set_upper = {i.upper() for i in chosen_set}

    if types == 'feats':
        query_result = data[(data['name'].str.upper().isin(chosen_set_upper)) & (data['type'] != 'Mythic')][extraction_list]
    else:
        query_result = data[(data['name'].str.upper().isin(chosen_set_upper)) & (data['mythic'] == 0)][extraction_list]

    return query_result

def remove_dots_dashes(character, result_dict, query_result, info_column, info_column_2=None):
    replace_dash = lambda x: re.sub(r'[-]', ' ', str(x))
    replace_dot = lambda x: re.sub(r'[.]', '', str(x))

    if query_result is None:
        return

    for index, row in query_result.iterrows():
        feat_name = row['name']
        if pd.isna(row[info_column]):
            row[info_column] = ''
        feat_info = {f'{info_column}': replace_dash(row[f'{info_column}'])}
        feat_info = {f'{info_column}': replace_dot(row[f'{info_column}'])}

        if info_column_2 is not None:
            if pd.isna(row[info_column_2]):
                row[info_column_2] = ''
        feat_info = {f'{info_column}': replace_dash(row[f'{info_column}'])}
        feat_info = {f'{info_column}': replace_dot(row[f'{info_column}'])}

        result_dict[feat_name] = feat_info

    return result_dict
