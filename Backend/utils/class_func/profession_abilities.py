"""Profession abilities (homebrew tiered powers).

Each profession a character carries is worth more than a skill rank: it unlocks *abilities*. Per the
campaign's design, a profession's power **tier** is fixed by the prestige of its name (Pope/Royal →
top, Bishop/Cardinal/Inquisitor → high, Knight/Guard/Soldier & skilled smiths → good, most artisans
and performers → average, Acolyte/Nun → bad, Custodian/Pool-cleaner → garbage), and its **theme**
(martial / ki / divine / arcane / alchemy / skill / craft / scholar / nature / medical / menial) is
read from the same name. The strongest professions are meant to *supercharge the character's actual
build*, so for **high/top tier** professions we swap in the character's class theme when one is known.

Within a profession, the **rank-5** entry grants a *weaker* band of abilities and the **rank-15**
entry (only the single True-Calling profession reaches it) grants the *full* tier band — the strongest
items on the sheet. Abilities are drawn from ``Backend/json/profession_abilities.json`` (a curated,
power-tagged ladder per theme) and resolved against the real character (level/class placeholders),
i.e. a mix of curated content and procedural fill. Each resolved ability carries optional pf1
``changes`` / ``contextNotes`` / ``uses`` so passive bonuses are mechanically wired on the sheet.

Public API:
    assign_profession_abilities(character)      -> mutates character.profession_data in place,
                                                   adding "rank5_abilities"/"rank15_abilities".
    build_profession_ability_items(character)   -> list of {name, description, changes,
                                                   contextNotes, uses} item payloads for export.
"""
import json
import os
import random

# Backend/json/profession_abilities.json, resolved relative to THIS file (CWD-independent), mirroring
# skill_unlocks.py.
_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "json", "profession_abilities.json")
_LIBRARY = None

_TIER_INDEX = {"garbage": 0, "bad": 1, "average": 2, "good": 3, "high": 4, "top": 5}

# Theme classification. Each rule is (theme, keywords); the FIRST rule that matches the name wins, so
# specific themes (divine/ki/arcane) precede the catch-all "craft". Keywords are matched as
# substrings, so suffixes like "smith"/"wright"/"maker" catch the many artisan names.
_THEME_RULES = [
    ("menial", ["custodian", "pool clean", "gongfarm", "gong farm", "gravedig", "grave dig",
                "chimney", "rat catch", "ratcatch", "water carrier", "launder", "scavenger",
                "grave robber", "sewer", "latrine", "dung", "muck", "scullery", "well-dig",
                "well dig", "lamplighter", "lamp lighter"]),
    ("ki", ["monk", "ascetic", "martial artist", "hermit"]),
    ("divine", ["priest", "cleric", "bishop", "cardinal", "pope", "nun", "friar", "abbot", "abbess",
                "abess", "abbott", "prior", "chaplain", "acolyte", "pilgrim", "missionary", "deacon",
                "templar", "crusader", "evangelist", "inquisitor", "exorcist", "oracle", "paladin",
                "monastic", "mother superior", "theolog", "witch hunter", "cult leader", "heretic",
                "blasphem", "zealot"]),
    ("arcane", ["wizard", "witch", "sorcer", "mage", "magician", "illusion", "conjur", "enchanter",
                "necromanc", "summoner", "warlock", "occultist", "medium", "spiritualist", "psychic",
                "astrolog", "soothsay", "fortune", "demonolog", "diviner", "arcanist", "hedge witch",
                "seer"]),
    ("alchemy", ["alchemist", "apothecar", "herbalist", "chirurgeon", "perfumer", "poison"]),
    ("medical", ["physician", "surgeon", "dentist", "barber", "healer", "midwife", "doctor", "nurse",
                 "leech", "bonesetter"]),
    ("martial", ["soldier", "guard", "knight", "mercenar", "warrior", "warlord", "fighter", "captain",
                 "constable", "watchman", "sentinel", "gladiator", "duelist", "fencer", "marine",
                 "pirate", "corsair", "privateer", "bandit", "outlaw", "highwayman", "executioner",
                 "master of arms", "master-at-arms", "man-at-arms", "quartermaster", "siege",
                 "cavalier", "squire", "champion", "raider", "reaver", "legion", "swordsman",
                 "spearman", "pikeman", "halberd", "gunslinger", "arquebus", "crossbowman",
                 "longbowman", "archer", "slinger", "javelin", "watchman", "jailer", "jailor",
                 "torturer", "interrogator", "assassin"]),
    ("nature", ["ranger", "hunter", "huntsman", "trapper", "tracker", "forester", "gamekeeper",
                "woodsman", "falconer", "falconry", "beekeeper", "fisher", "fisherman", "sailor",
                "seaman", "navigator", "explorer", "guide", "poacher", "herdsman", "shepherd",
                "farmer", "gardener", "orchardist", "horse trainer", "dog trainer", "hawker",
                "whaler", "scout", "groom", "stable", "jockey", "master of hounds", "woodsman",
                "landscaper", "lighthouse"]),
    ("scholar", ["scholar", "scribe", "historian", "archivist", "librarian", "sage", "philosoph",
                 "professor", "teacher", "astronom", "mathematic", "cartograph", "geograph",
                 "chronicler", "curator", "writer", "playwright", "clerk", "accountant", "bookkeep",
                 "barrister", "map maker", "bookseller", "book seller", "diplomat", "courtier",
                 "herald", "burgomaster", "mayor", "bailiff"]),
    ("skill", ["bard", "minstrel", "troubadour", "jester", "actor", "dancer", "acrobat", "tumbler",
               "fire-eater", "juggler", "clown", "performer", "contortionist", "tightrope",
               "knife thrower", "noble", "merchant", "trader", "banker", "moneylender", "spy",
               "thief", "burglar", "smuggler", "fool", "piper", "circus", "street performer",
               "prostitute", "urchin", "wanderer", "innkeeper", "barkeep", "alewife", "grocer"]),
]

# Tier classification. Ordered top -> garbage; the FIRST matching rule wins. Single-word keywords are
# matched against the name's WORDS (so "chandler" never matches the word "hand"); phrases (with a
# space) are matched as substrings.
_TIER_RULES = [
    ("top", ["pope", "king", "queen", "emperor", "empress", "archmage", "royal", "high priest",
             "grandmaster", "grand master", "archbishop", "sovereign", "monarch", "prince",
             "princess"]),
    ("high", ["cardinal", "bishop", "master", "warlord", "general", "admiral", "duke", "duchess",
              "marquis", "count", "earl", "viscount", "lord", "lady", "noble", "nobleman",
              "noblewoman", "inquisitor", "necromancer", "abbot", "abbess", "magus", "chancellor",
              "seneschal", "commander", "mayor", "burgomaster", "high", "grand", "archbishop"]),
    ("good", ["knight", "guard captain", "captain", "constable", "soldier", "mercenary", "sergeant",
              "wizard", "witch", "sorcerer", "magician", "physician", "surgeon", "blacksmith",
              "armorer", "weaponsmith", "goldsmith", "silversmith", "jeweler", "merchant", "banker",
              "moneylender", "diplomat", "barrister", "ranger", "assassin", "spy", "professor",
              "sage", "astronomer", "alchemist", "architect", "shipwright", "engineer",
              "cartographer", "gunsmith", "artisan", "scholar", "priest", "cleric", "druid", "monk",
              "guard", "watchman"]),
    ("bad", ["acolyte", "novice", "apprentice", "initiate", "nun", "friar", "scribe", "clerk",
             "servant", "peasant", "laborer", "labourer", "serf", "page", "pilgrim", "cottager",
             "drudge", "hermit"]),
    ("garbage", ["custodian", "pool cleaner", "gongfarmer", "gong farmer", "gravedigger",
                 "grave digger", "chimneysweep", "chimney sweep", "rat catcher", "ratcatcher",
                 "water carrier", "launderer", "laundress", "slave", "scavenger", "grave robber",
                 "beggar", "urchin", "gutter", "ferryman"]),
]

# Character class -> theme (for the high/top "supercharge the build" override). Keyword substrings.
_CLASS_THEME_RULES = [
    ("ki", ["monk"]),
    ("alchemy", ["alchemist", "investigator"]),
    ("nature", ["ranger", "druid", "hunter"]),
    ("divine", ["cleric", "paladin", "warpriest", "oracle", "inquisitor", "shaman", "antipaladin",
                "zealot", "crusader"]),
    ("arcane", ["wizard", "sorcerer", "magus", "witch", "arcanist", "summoner", "bard", "skald",
                "occultist", "medium", "psychic", "spiritualist", "bloodrager", "warlock", "mystic"]),
    ("skill", ["rogue", "vigilante", "swashbuckler", "slayer", "ninja", "bard"]),
    ("martial", ["fighter", "barbarian", "cavalier", "brawler", "gunslinger", "samurai", "warder",
                 "warlord", "stalker", "harbinger", "soldier", "antipaladin"]),
]


def _load_library():
    global _LIBRARY
    if _LIBRARY is None:
        try:
            with open(_JSON_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            _LIBRARY = data.get("themes", {})
        except (OSError, ValueError) as exc:
            print(f"profession_abilities: could not load {_JSON_PATH} ({exc}); abilities disabled.")
            _LIBRARY = {}
    return _LIBRARY


def _theme_for(name):
    n = str(name).strip().lower()
    for theme, keywords in _THEME_RULES:
        if any(kw in n for kw in keywords):
            return theme
    return "craft"  # catch-all: the bulk of unmapped names are artisans


def _tier_for(name):
    n = str(name).strip().lower()
    words = set(n.replace("(", " ").replace(")", " ").replace("-", " ").split())
    for tier, keywords in _TIER_RULES:
        for kw in keywords:
            if " " in kw:
                if kw in n:
                    return tier
            elif kw in words:
                return tier
    return "average"


def _class_theme(c_class):
    n = str(c_class or "").strip().lower()
    if not n:
        return None
    for theme, keywords in _CLASS_THEME_RULES:
        if any(kw in n for kw in keywords):
            return theme
    return None


def resolve_profile(name, class_theme=None):
    """Return (theme, tier) for a profession name. For high/top-tier professions, swap to the
    character's class theme when known so the strongest professions supercharge the real build."""
    tier = _tier_for(name)
    theme = _theme_for(name)
    if tier in ("high", "top") and class_theme:
        theme = class_theme
    if theme not in _load_library():
        theme = "craft" if "craft" in _load_library() else (next(iter(_load_library()), None))
    return theme, tier


def _fill(text, character):
    """Fill {class}/{level}/{half_level} placeholders from the actual character."""
    level = int(getattr(character, "level", 0) or 0)
    cls = getattr(character, "c_class_display", None) or getattr(character, "c_class", None) or "your class"
    return (str(text)
            .replace("{class}", str(cls))
            .replace("{level}", str(level))
            .replace("{half_level}", str(level // 2)))


def _resolve_ability(template, character):
    """Copy a library ability and fill placeholders so mutation never touches the cached library."""
    return {
        "name": str(template.get("name", "")),
        "desc": _fill(template.get("desc", ""), character),
        "changes": [dict(c) for c in (template.get("changes") or [])],
        "contextNotes": [dict(c) for c in (template.get("contextNotes") or [])],
        "uses": dict(template["uses"]) if template.get("uses") else None,
    }


def _select(abilities, target_power, count, exclude_names):
    """Pick up to ``count`` abilities at or below ``target_power``, always taking the strongest
    eligible one (the tier payoff) then filling with the next-strongest, randomised on ties."""
    pool = [a for a in abilities if a["name"] not in exclude_names]
    if not pool:
        return []
    eligible = [a for a in pool if a.get("power", 0) <= target_power]
    if not eligible:  # tier lower than the cheapest ability in this theme -> take the cheapest
        eligible = sorted(pool, key=lambda a: a.get("power", 0))[:1]
    eligible.sort(key=lambda a: (a.get("power", 0), random.random()), reverse=True)
    return eligible[:count]


def assign_profession_abilities(character):
    """Populate rank5/rank15 ability lists on each entry of ``character.profession_data``."""
    library = _load_library()
    prof_data = getattr(character, "profession_data", None) or []
    if not library or not prof_data:
        return
    class_theme = _class_theme(getattr(character, "c_class", None))
    used_global = set()  # avoid repeating the same ability across a character's professions

    for prof in prof_data:
        theme, tier = resolve_profile(prof.get("name", ""), class_theme)
        prof["ability_theme"] = theme
        prof["ability_tier"] = tier
        ladder = library.get(theme, [])
        tier_idx = _TIER_INDEX.get(tier, 2)
        ranks = int(prof.get("ranks", 0) or 0)

        # Rank 15 (the True-Calling payoff) is chosen FIRST so it claims the full tier band; rank 5
        # then draws from the weaker band that's left, guaranteeing rank 15 > rank 5 in power.
        rank15_abilities = []
        if ranks >= 15 and ladder:
            count = 3 if tier_idx <= 3 else 4
            picks = _select(ladder, tier_idx, count, used_global)
            rank15_abilities = [_resolve_ability(t, character) for t in picks]
            used_global.update(a["name"] for a in rank15_abilities)
        prof["rank15_abilities"] = rank15_abilities

        rank5_abilities = []
        if ranks >= 5 and ladder:
            target = max(0, tier_idx - 1)
            count = 2 if tier_idx <= 2 else 3
            picks = _select(ladder, target, count, used_global)
            rank5_abilities = [_resolve_ability(t, character) for t in picks]
            used_global.update(a["name"] for a in rank5_abilities)
        prof["rank5_abilities"] = rank5_abilities


def _entry_html(header, abilities):
    """Render an entry: an <em> header line then one bold-titled block per ability, <hr>-separated
    (the same shape real feats render in)."""
    parts = [f"<p><em>{header}</em></p>"] if header else []
    for ab in abilities:
        parts.append(f"<p><strong>{ab['name']}</strong></p>{ab['desc']}")
    return "<hr>".join(parts)


def _bundle(abilities):
    """Merge the mechanical fields of a rank entry's abilities into one feat item. Passive ``changes``
    and ``contextNotes`` stack freely; a ``uses`` pool is attached only when exactly one ability in the
    entry has one (otherwise per-ability uses stay described in prose, since a feat holds one pool)."""
    changes, notes, pools = [], [], []
    for ab in abilities:
        changes.extend(ab.get("changes") or [])
        notes.extend(ab.get("contextNotes") or [])
        if ab.get("uses"):
            pools.append(ab["uses"])
    return changes, notes, (pools[0] if len(pools) == 1 else None)


def build_profession_ability_items(character):
    """Build the export payload: one item per Rank-5 / Rank-15 entry (abilities bundled) plus the
    profession-feat entries. Returned in display order; the FoundryVTT module assigns sort/placement."""
    items = []
    prof_data = getattr(character, "profession_data", None) or []
    for prof in prof_data:
        name = prof.get("name", "")
        ranks = int(prof.get("ranks", 0) or 0)
        cap = prof.get("cap", "")
        assoc = ", ".join(prof.get("associate_skills") or [])

        r5 = prof.get("rank5_abilities") or []
        if r5:
            header = f"Profession ({name}) - rank {ranks}/{cap}."
            if assoc:
                header += f" Associate skills (ranks 1/4/7/10): {assoc}."
            changes, notes, uses = _bundle(r5)
            items.append({
                "name": f"Profession Rank 5: ({name})",
                "description": _entry_html(header, r5),
                "changes": changes, "contextNotes": notes, "uses": uses,
            })

        r15 = prof.get("rank15_abilities") or []
        if r15:
            changes, notes, uses = _bundle(r15)
            items.append({
                "name": f"Profession Rank 15: ({name})",
                "description": _entry_html(f"Profession ({name}) - rank {ranks}/{cap}.", r15),
                "changes": changes, "contextNotes": notes, "uses": uses,
            })

    # NB: the profession feats (True Calling / Multi Talented / Always Improving) are NOT emitted here.
    # main_test.py attributes them to a dedicated trainer slot so they render in the Trainers section.
    return items
