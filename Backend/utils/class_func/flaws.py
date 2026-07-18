import json
import os
import random

# Mechanical character flaws (replaces the old personality-flaw strings).
# Data: Backend/json/flaws/flaw_effects.json, tiers "minor"/"major", entries in the
# feat_changes.json house shape plus a rules-text "description".

_FLAWS_CACHE = None


def _load_flaws():
    global _FLAWS_CACHE
    if _FLAWS_CACHE is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', '..', 'json', 'flaws', 'flaw_effects.json')
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        _FLAWS_CACHE = {'minor': data.get('minor') or {}, 'major': data.get('major') or {}}
    return _FLAWS_CACHE


def flaw_chooser(character, flaw_amount):
    """Pick flaw_amount mechanical flaws: the 1st is minor, the 2nd major, any further
    flaw rolls 80% minor / 20% major. A flaw name is never assigned twice (some names
    exist in both tiers). Returns (names, effects) where effects[name] =
    {tier, description, changes, contextNotes}; also stored on the character."""
    flaws = _load_flaws()
    names, effects = [], {}
    for i in range(flaw_amount or 0):
        if i == 0:
            tier = 'minor'
        elif i == 1:
            tier = 'major'
        else:
            tier = 'minor' if random.random() < 0.8 else 'major'
        pool = [n for n in flaws[tier] if n not in effects]
        if not pool:
            tier = 'major' if tier == 'minor' else 'minor'
            pool = [n for n in flaws[tier] if n not in effects]
            if not pool:
                break
        name = random.choice(pool)
        entry = flaws[tier][name] or {}
        names.append(name)
        effects[name] = {
            'tier': tier,
            'description': entry.get('description', ''),
            'changes': entry.get('changes') or [],
            'contextNotes': entry.get('contextNotes') or [],
        }
    character.flaw = names
    character.flaw_effects = effects
    return names, effects
