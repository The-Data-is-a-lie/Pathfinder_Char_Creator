"""The one place that owns pf1's damage-type vocabulary.

WHY THIS EXISTS
---------------
The conditional builders scrape Pathfinder rules **prose** and write the matched word straight into
a modifier's ``damageType``. Prose and pf1 ids are not the same language: the rules read "5d6 points
of **electricity** damage", but pf1's damage-type id is ``electric``. Emitting the prose word gives a
type pf1 does not recognise, so a creature with electricity resistance/immunity is never matched and
takes damage it should have resisted -- silent, and only visible if you audit the data.

That bug shipped across Path of War, Spheres and spells at once, because the same prose alternation
was copy-pasted into three builders. Matching the prose word is correct; emitting it as an id is not.
So the builders keep their prose regex and pass the captured word through ``normalize_damage_type``.

``PF1_DAMAGE_TYPES`` is **observed**, not authoritative: it was read out of pf1's own compendium
exports (``every_item/spell/feat.json``, the ``type.values[]`` shape) plus the conventions this repo
deliberately uses. That is why validators should *warn* on an unrecognised value but *error* on a
known alias -- a value we have simply never seen may still be legitimate, whereas an alias is
provably wrong.
"""

# Read from pf1's own compendium data (type.values[]): the ids pf1 itself writes.
_PF1_OBSERVED = {
    "fire", "cold", "acid", "electric", "sonic", "force",
    "negative", "positive", "precision",
    "bludgeoning", "piercing", "slashing",
    "nonlethal", "untyped",
}

# Deliberate additions this repo uses. `as-weapon` is a placeholder the attach-time pipeline
# resolves to the wielder's own weapon damage; the alignment types are real Pathfinder damage
# concepts that simply do not appear in the sampled compendium exports.
_REPO_CONVENTIONS = {
    "as-weapon",
    "good", "evil", "lawful", "chaotic",
}

PF1_DAMAGE_TYPES = _PF1_OBSERVED | _REPO_CONVENTIONS

# Prose word -> pf1 id. Extend this when a scrape turns up another rules-text spelling; do NOT
# "fix" it by widening PF1_DAMAGE_TYPES, or the wrong id keeps shipping.
DAMAGE_TYPE_ALIASES = {
    "electricity": "electric",
}


def normalize_damage_type(t):
    """Map one scraped word to its pf1 id. Unknown values pass through untouched (a validator
    warns about them; guessing here would hide a real authoring mistake)."""
    if not isinstance(t, str):
        return t
    return DAMAGE_TYPE_ALIASES.get(t.strip().lower(), t)


def normalize_damage_types(types):
    """``normalize_damage_type`` over a list, preserving order and dropping nothing."""
    if not isinstance(types, list):
        return types
    return [normalize_damage_type(t) for t in types]


def classify_damage_type(t):
    """('ok' | 'alias' | 'unknown', suggestion). Shared by every validator so the three states are
    defined once: an alias is an error with a fix, an unknown is a warning."""
    if not isinstance(t, str):
        return "unknown", None
    key = t.strip().lower()
    if key in DAMAGE_TYPE_ALIASES:
        return "alias", DAMAGE_TYPE_ALIASES[key]
    if key in PF1_DAMAGE_TYPES:
        return "ok", None
    return "unknown", None
