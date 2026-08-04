import json
import os
import random

# Mechanical character flaws (replaces the old personality-flaw strings).
# Data: Backend/json/flaws/flaw_effects.json, tiers "minor"/"major", entries in the
# feat_changes.json house shape plus a rules-text "description".

# One cache per file, because a bonded creature draws from its own catalogue -- see `pick_flaws`.
_FLAWS_CACHE = {}

PC_FLAWS = 'flaw_effects.json'
# Bonded creatures get their own catalogue: the PC's 44 are written for people (Alcoholic,
# Bespectacled, Racial Distrust, Accustomed to Society), and filtering them down left a pool of
# roughly eight, which every companion would then repeat. Spec section 8, D16.
ANIMAL_FLAWS = 'animal_flaw_effects.json'


def load_flaws(filename=PC_FLAWS):
    cached = _FLAWS_CACHE.get(filename)
    if cached is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', '..', 'json', 'flaws', filename)
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        cached = {'minor': data.get('minor') or {}, 'major': data.get('major') or {}}
        _FLAWS_CACHE[filename] = cached
    return cached


def pick_flaws(flaw_amount, filename=PC_FLAWS, rng=None):
    """Pick flaw_amount mechanical flaws: the 1st is minor, the 2nd major, any further
    flaw rolls 80% minor / 20% major. A flaw name is never assigned twice (some names
    exist in both tiers). Returns (names, effects) where effects[name] =
    {tier, description, changes, contextNotes}.

    `rng` defaults to the module-level `random`, which is what the PC path uses. A bonded creature
    passes its OWN generator so its flaws cannot churn the rolls its master makes later.
    """
    rng = rng or random
    flaws = load_flaws(filename)
    names, effects = [], {}
    for i in range(flaw_amount or 0):
        if i == 0:
            tier = 'minor'
        elif i == 1:
            tier = 'major'
        else:
            tier = 'minor' if rng.random() < 0.8 else 'major'
        pool = [n for n in flaws[tier] if n not in effects]
        if not pool:
            tier = 'major' if tier == 'minor' else 'minor'
            pool = [n for n in flaws[tier] if n not in effects]
            if not pool:
                break
        name = rng.choice(pool)
        entry = flaws[tier][name] or {}
        names.append(name)
        effects[name] = {
            'tier': tier,
            'description': entry.get('description', ''),
            'changes': entry.get('changes') or [],
            'contextNotes': entry.get('contextNotes') or [],
        }
    return names, effects


def flaw_chooser(character, flaw_amount):
    """The PC's flaws, stored on the character. See `pick_flaws` for the ladder."""
    names, effects = pick_flaws(flaw_amount, PC_FLAWS)
    character.flaw = names
    character.flaw_effects = effects
    return names, effects
