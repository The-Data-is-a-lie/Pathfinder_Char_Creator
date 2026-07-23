"""Name-matching for the curated Foundry buff data, in one place.

Six independent code paths used to load a curated JSON map, normalize names their own way, and look
up the character's selections -- feats and items and weapon/armor qualities in main_test.py, spells
in spells.py, Spheres talents in spheres.py, Path of War stances in path_of_war.py. Every one of
those lookups was a plain ``.get()``: a curated entry whose key didn't match the selected name was
dropped with no error, no log, and no sign on the sheet. The normalizations had quietly diverged --
Path of War stripped apostrophes, class features stripped ``(Su)/(Ex)/(Sp)``, Spheres didn't
lowercase at all -- so which spellings survived depended on which path you were in.

This module owns that lookup. Each KIND declares where its data lives, whether it is flat or
sectioned, and how keys and queries are normalized. The per-kind rules here are deliberately
IDENTICAL to what each call site did before, so adopting this module changes no output.

What it adds is the gap report. On a strict miss, the lookup retries with a conservative "loose" key
(case, whitespace, apostrophes, hyphens and a trailing ``(Su)/(Ex)/(Sp)`` all folded). A loose hit
after a strict miss means the curated data IS there and only the kind's normalization failed to
reach it -- which is precisely the silent bug this module exists to surface. Those are returned as
gaps and exported as ``buff_gaps``; the strict result is still what gets attached, so the report
measures the problem without changing behaviour. Widen a kind's rule once its gaps say it's worth it.

    from utils.class_func.buff_match import match

    changes, gaps = match('feat', placed_feat_names)
    changes, gaps = match('class_feature', power_names, section='rage_powers')
"""
import json
import re

from utils.paths import repo_path

# --------------------------------------------------------------------------------------------- #
# Normalizers -- one per rule that a call site actually used.
# --------------------------------------------------------------------------------------------- #

def _identity(name):
    return str(name)


def _lower(name):
    return str(name).lower()


def _cfe_key(name):
    """Class-feature pool key: drop a trailing (Su)/(Ex)/(Sp), collapse whitespace, lowercase.
    Mirrors build_class_feature_changes.py, which generates these keys."""
    return re.sub(r"\s+", " ",
                  re.sub(r"\s*\((su|ex|sp)\)\s*$", "", str(name), flags=re.I)).strip().lower()


def _dnorm(name):
    """Path of War discipline/maneuver key: apostrophe- and case-insensitive, so "Fools Errand"
    matches the JSON's "Fool%27s_Errand"."""
    return re.sub(r"\s+", " ", str(name).lower().replace("'", "").replace("’", "").strip())


_SUFFIX_RE = re.compile(r"\s*\((su|ex|sp)\)\s*$", re.I)


def loose_key(name):
    """The conservative superset used only to DETECT gaps, never to attach.

    Folds the differences that are unambiguously cosmetic: case, runs of whitespace, straight vs
    curly apostrophes, hyphens vs spaces, and a trailing (Su)/(Ex)/(Sp). It deliberately does NOT
    drop a trailing parenthetical -- "Weapon Focus (Longsword)" and "Weapon Focus" are different
    feats to the generator, and folding them would report gaps that shouldn't be closed.
    """
    text = _SUFFIX_RE.sub("", str(name))
    text = text.lower().replace("'", "").replace("’", "").replace("`", "")
    text = text.replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------------------------- #
# path       -- repo-root-relative location of the curated JSON
# nested     -- True when the file is {section: {name: entry}} rather than {name: entry}
# key_norm   -- applied to the file's keys when the lookup index is built
# query_norm -- applied to the selected name being looked up
#
# key_norm and query_norm differ on purpose for 'item': build_item_changes.py already writes
# lowercased keys, and the runtime lowercased only the query. Keeping them separate reproduces that
# exactly (a non-lowercase key in that file has never matched, and still won't).

_REGISTRY = {
    'feat': dict(path='Backend/json/feats/feat_changes.json',
                 nested=False, key_norm=_lower, query_norm=_lower),
    'feat_conditional': dict(path='Backend/json/feats/feat_conditionals.json',
                             nested=False, key_norm=_lower, query_norm=_lower),
    'item': dict(path='Backend/json/items/item_changes.json',
                 nested=False, key_norm=_identity, query_norm=_lower),
    'quality': dict(path='Backend/json/items/quality_effects.json',
                    nested=True, key_norm=_lower, query_norm=_lower),
    'class_feature': dict(path='Backend/json/class_data/effects/class_feature_effects.json',
                          nested=True, key_norm=_cfe_key, query_norm=_cfe_key),
    'spell_change': dict(path='Backend/json/spells/spell_changes.json',
                         nested=False, key_norm=_lower, query_norm=_lower),
    'spell_rider': dict(path='Backend/json/spells/spell_riders.json',
                        nested=False, key_norm=_lower, query_norm=_lower),
    'talent': dict(path='Backend/json/class_data/spheres/combat_talent_changes.json',
                   nested=True, key_norm=_identity, query_norm=_identity),
    'stance': dict(path='Backend/json/class_data/path_of_war/stance_auras.json',
                   nested=False, key_norm=_dnorm, query_norm=_dnorm),
}

KINDS = tuple(sorted(_REGISTRY))

# {kind: raw json}. Loaded once per process -- the feat/item/quality/class-feature maps used to be
# re-read and re-parsed on EVERY generation (~1.6 MB), because their loader was defined inside
# generate_random_char. Under gunicorn --preload this now loads pre-fork and is shared copy-on-write.
_RAW = {}
# {(kind, section): ({strict_key: (display, entry)}, {loose_key: display})}
_INDEX = {}


def _raw(kind):
    if kind not in _RAW:
        try:
            _RAW[kind] = json.loads(repo_path(_REGISTRY[kind]['path']).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            # A missing or malformed curated file means the feature is simply off, exactly as the
            # hand-rolled loaders behaved. Never fatal to character generation.
            _RAW[kind] = {}
    return _RAW[kind]


def _index(kind, section):
    """(strict, loose) lookup tables for a kind (and section, when nested)."""
    cache_key = (kind, section)
    if cache_key in _INDEX:
        return _INDEX[cache_key]

    spec = _REGISTRY[kind]
    data = _raw(kind)
    if spec['nested']:
        data = (data or {}).get(section) or {}
    if not isinstance(data, dict):
        data = {}

    strict, loose = {}, {}
    for display, entry in data.items():
        if str(display).startswith('_'):        # '_comment'-style metadata in the curated files
            continue
        strict.setdefault(spec['key_norm'](display), (display, entry))
        loose.setdefault(loose_key(display), display)

    _INDEX[cache_key] = (strict, loose)
    return _INDEX[cache_key]


def raw(kind):
    """The curated file for ``kind`` exactly as authored, cached. For validators and test scripts
    that check the DATA rather than the matching; generation code should use match()."""
    return _raw(kind)


def sections(kind):
    """Section names available for a nested kind ([] for a flat one)."""
    if not _REGISTRY[kind]['nested']:
        return []
    return [k for k in (_raw(kind) or {}) if not str(k).startswith('_')]


def match(kind, names, section=None):
    """Look up ``names`` in ``kind``'s curated data.

    Returns ``(matched, gaps)``:
      matched -- {selected name as given: curated entry}, so callers keep their display casing
      gaps    -- [{kind, section, name, curated_as}] for selections the strict rule missed but a
                 loose key would have found. A gap means curated data exists and only the
                 normalization stood in the way; an ordinary "nothing curated for this name" is
                 not a gap and is not reported.

    Order follows ``names``, deduped, so results are stable for the golden payloads.
    """
    if kind not in _REGISTRY:
        raise KeyError(f'unknown buff kind {kind!r}; known: {", ".join(KINDS)}')
    if _REGISTRY[kind]['nested'] and section is None:
        raise ValueError(f'kind {kind!r} is sectioned -- pass section=')

    strict, loose = _index(kind, section)
    matched, gaps = {}, []

    for name in dict.fromkeys(names or []):
        entry = strict.get(_REGISTRY[kind]['query_norm'](name))
        if entry is not None:
            matched[name] = entry[1]
            continue
        curated_as = loose.get(loose_key(name))
        if curated_as is not None:
            gaps.append({'kind': kind, 'section': section,
                         'name': str(name), 'curated_as': str(curated_as)})

    return matched, gaps


def format_gaps(gaps):
    """One line per gap, for the end-of-run summary."""
    out = []
    for gap in gaps:
        where = f"{gap['kind']}/{gap['section']}" if gap.get('section') else gap['kind']
        out.append(f"{where}: {gap['name']!r} did not match curated {gap['curated_as']!r}")
    return out
