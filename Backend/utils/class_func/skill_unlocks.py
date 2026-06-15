"""Skill unlocks (Pathfinder Unchained) — every generated character gets exactly ONE.

The campaign grants each character a free skill unlock (homebrew_rules.md §1). We pick one skill
the character actually has ranks in, look up its unlock benefits (5/10/15/20 ranks) from
Backend/json/skill_unlocks.json, and hand back a display name + rendered HTML so the sheet can show a
"Skill Unlock: <skill>" class feature and the Foundry module can build a "(Skill Unlocks) <skill>"
item under its "____Skill Unlocks____" divider.

The data file is keyed by base skill; this module maps the generator's skill names
(data.skills, e.g. "knowledge arcana", "craft", "profession") onto those base keys.
"""
import json
import os
import random

# Backend/json/skill_unlocks.json, resolved relative to THIS file so it works regardless of CWD
# (mirrors the 'Backend/json/...' load paths used in main_test.py, but CWD-independent).
_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "json", "skill_unlocks.json")
_UNLOCKS = None


def _load_unlocks():
    global _UNLOCKS
    if _UNLOCKS is None:
        try:
            with open(_JSON_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            _UNLOCKS = {k: v for k, v in data.items() if not k.startswith("_")}
        except (OSError, ValueError) as exc:
            print(f"skill_unlocks: could not load {_JSON_PATH} ({exc}); skill unlock disabled.")
            _UNLOCKS = {}
    return _UNLOCKS


def _base_key(skill_name):
    """Map a generator skill name to a skill_unlocks.json key, or None if there's no unlock for it.
    All Knowledge specializations share the single 'knowledge' unlock; everything else maps by name."""
    s = str(skill_name).strip().lower()
    unlocks = _load_unlocks()
    if s.startswith("knowledge"):
        return "knowledge" if "knowledge" in unlocks else None
    return s if s in unlocks else None


def _display_name(character, skill_name):
    """Human-facing label, adding the parenthetical specialization for craft/profession/knowledge."""
    s = str(skill_name).strip().lower()
    if s == "craft":
        spec = getattr(character, "craft_chosen", None)
        return f"Craft ({spec})" if spec else "Craft"
    if s == "profession":
        chosen = getattr(character, "profession_chosen", None) or []
        spec = chosen[0] if chosen else None
        return f"Profession ({spec})" if spec else "Profession"
    if s.startswith("knowledge "):
        field = s[len("knowledge "):].strip()
        return f"Knowledge ({field})"
    return s.title()


def _render_html(display_name, entry):
    """Build the unlock body in the same shape as the example sheets: an <h2> title then one
    <p><strong>N Ranks</strong>: ...</p> per threshold."""
    parts = [f"<h2>{display_name}</h2>"]
    for rank in ("5", "10", "15", "20"):
        text = entry.get(rank)
        if text:
            parts.append(f"<p><strong>{rank} Ranks</strong>: {text}</p>")
    return "".join(parts)


def choose_skill_unlock(character, skill_ranks):
    """Pick one skill the character has ranks in and return its unlock.

    Returns a dict ``{"skill", "base_skill", "ranks", "unlock", "unlock_html"}`` or ``None`` when no
    ranked skill has a defined unlock (e.g. a character with ranks only in homebrew skills).
    ``skill_ranks`` is the ``{skill: ranks}`` dict from ``skills_selector`` (main_test.py).
    """
    unlocks = _load_unlocks()
    if not unlocks or not isinstance(skill_ranks, dict):
        return None

    # Candidates: skills with at least one rank that also have a defined unlock.
    ranked = [(name, ranks) for name, ranks in skill_ranks.items()
              if ranks and ranks > 0 and _base_key(name)]
    if not ranked:
        return None

    skill_name, ranks = random.choice(ranked)
    key = _base_key(skill_name)
    entry = unlocks.get(key, {})
    display = _display_name(character, skill_name)
    result = {
        "skill": display,
        "base_skill": key,
        "ranks": ranks,
        "unlock": entry,
        "unlock_html": _render_html(display, entry),
    }
    character.skill_unlock = result
    return result
