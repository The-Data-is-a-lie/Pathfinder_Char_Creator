"""Generate a coherent 1-2 paragraph character backstory from the generated character's data.

Uses an Ollama-compatible chat endpoint when one is reachable, and falls back to a deterministic
template otherwise (e.g. the deployed backend where no local Ollama exists, while a local model is
still downloading, or when the cloud free-tier rate limit is hit). The same code path serves both:

  - LOCAL Ollama:  leave OLLAMA_API_KEY unset -> host defaults to http://localhost:11434,
                   model defaults to "gpt-oss:20b".
  - Ollama CLOUD:  set OLLAMA_API_KEY (free key from https://ollama.com/settings/keys) -> host
                   defaults to https://ollama.com; set OLLAMA_MODEL="gpt-oss:20b-cloud".

Three things are tunable WITHOUT editing this file:
  - Backend/json/backstory_config.json   -- the system prompt, temperature, length, focus phrases.
  - Backend/json/backstory_examples/      -- drop .txt/.json example backstories here and the model
                                             is shown 1-3 of them as few-shot examples (see the
                                             folder's README). Empty folder == old behavior.
  - the ``focus`` argument                -- emphasize chosen facets (combat / profession / family /
                                             faith / personality / appearance / region) for one NPC.

Env:
  OLLAMA_API_KEY  optional bearer token; presence flips the default host to Ollama Cloud.
  OLLAMA_HOST     explicit host override.
  OLLAMA_MODEL    model name (default "gpt-oss:20b").
  OLLAMA_THINK    reasoning depth for gpt-oss models (default "low"); set "" for plain models.
"""
import json
import os
import random
import re
import urllib.error
import urllib.request
from pathlib import Path

from utils.usage_counter import record_backstory

_DEFAULT_LOCAL_HOST = "http://localhost:11434"
_DEFAULT_CLOUD_HOST = "https://ollama.com"
_DEFAULT_MODEL = "gpt-oss:20b"
_TIMEOUT = 120

# Backend/json/ lives two levels up from this file (utils/class_func/ -> utils/ -> Backend/).
_JSON_DIR = Path(__file__).resolve().parents[2] / "json"
_CONFIG_PATH = _JSON_DIR / "backstory_config.json"
_EXAMPLES_DIR = _JSON_DIR / "backstory_examples"
_LORE_PATH = _JSON_DIR / "campaign_lore.json"  # optional campaign canon (homeland/faith/factions)

# Baked-in defaults: the app must work even if the config file is missing or partial. These mirror
# backstory_config.json so deleting that file is a no-op rather than a regression.
_DEFAULT_INSTRUCTIONS = (
    "You are a Pathfinder 1st Edition loremaster. Write a cohesive 2-3 paragraph third-person "
    "backstory (about {min_words}-{max_words} words) for the NPC described by the facts below. Weave "
    "the facts into natural narrative prose: ground the character in their homeland, faith and "
    "alignment, and reflect what their build/class lets them do. {focus_line} Also work in the flavor "
    "of their traits, personality and history. Use ONLY the given facts — you may add light connective "
    "color, but do not invent contradictory details, new proper nouns, or specific events. If a "
    "SETTING / CAMPAIGN CANON block is provided, treat it as the true state of the world: never "
    "contradict its governments, faiths, social structures, factions, or tone, and avoid modern or "
    "real-world references — weave its flavor in naturally rather than quoting or listing it. Do NOT "
    "list stats, labels or bullet points; write flowing prose only. Output only the backstory."
)
_DEFAULT_FOCUS_PHRASES = {
    "profession": "their profession(s), notable craft or trade, and the mentors and trainers who shaped them",
    "combat": "their martial training, fighting style, and the deeds their feats and maneuvers enable",
    "faith": "their faith, their deity, and how their alignment guides them",
    "family": "their family, bloodline, and upbringing",
    "personality": "their personality, mannerisms, and flaws",
    "appearance": "their physical appearance, bearing, and presence",
    "region": "their homeland and how it shaped them",
}
_DEFAULT_CONFIG = {
    "instructions": _DEFAULT_INSTRUCTIONS,
    "temperature": 0.8,
    "max_tokens": 800,
    "word_range": [160, 260],
    "num_examples": 3,
    "smart_match": True,
    "default_focus": ["profession"],
    "focus_phrases": _DEFAULT_FOCUS_PHRASES,
}

# Loaded-once caches (config + examples are read from disk only on first use, like a long-lived
# server would want). Restart the process to pick up edits / newly-added example files.
_CONFIG_CACHE = None
_EXAMPLES_CACHE = None
_LORE_CACHE = None


def generate_backstory(brief, use_api=True, focus=None):
    """Return a 1-2 paragraph backstory string for the character described by `brief` (a dict).

    When `use_api` is true, tries Ollama (local or cloud) first; when false (the "use API" button is
    off), the network call is skipped entirely and the deterministic template is used. `focus` is an
    optional aspect or list of aspects to emphasize (see _normalize_focus). Always returns a
    non-empty string."""
    cfg = _config()
    text = _try_ollama(_build_messages(brief, focus, cfg), cfg) if use_api else ""
    # Tally only requests where the visitor actually asked for the API (that's "usage"); record
    # whether the model answered or we fell back to the template so the split is visible.
    if use_api:
        record_backstory("ollama" if text else "template")
    if not text:
        text = _template_backstory(brief, focus)
    # The sheet's structured fact block already shows Personality/Mannerisms/Appearance/Flaws, so a
    # closing labeled list in the prose (the old house style, still present in some few-shot
    # examples the model may imitate) is duplicate noise -- always strip it.
    return _strip_trailing_label_list(text)


_LABEL_LIST_RE = re.compile(r"^(personality|mannerisms|appearance|flaws|traits)\s*:", re.IGNORECASE)


def _strip_trailing_label_list(text):
    """Drop trailing paragraph(s) that start with a Personality:/Mannerisms:/Appearance:/Flaws:/
    Traits: label -- the legacy closing list the prose used to end with."""
    paragraphs = re.split(r"\n\s*\n", (text or "").strip())
    while paragraphs and _LABEL_LIST_RE.match(paragraphs[-1].strip()):
        paragraphs.pop()
    return "\n\n".join(paragraphs).strip()


_PROF_RANK_RE = re.compile(r"\(\s*Profession rank\b", re.IGNORECASE)


def structured_bio(brief):
    """Deterministic, scannable fact block for the sheet's Biography tab: a noun section header,
    then one "- Label: Value" bullet per fact, blank line between sections. Reads as a prompt a
    GM (or an AI) can build a story from. Pure formatting -- no network, no randomness. Empty
    fields (and whole empty sections) are skipped."""
    def cap(v):
        # Word-capitalize without str.title()'s apostrophe mangling ("jester's" -> "Jester's").
        s = _flat(v)
        return " ".join(w[:1].upper() + w[1:] for w in s.split()) if s else ""

    def as_list(v):
        return [x for x in (v if isinstance(v, (list, tuple)) else [v]) if _flat(x)]

    def section(header, facts):
        bullets = [f"- {f}" for f in facts if f]
        return [header] + bullets if bullets else None

    sections = []

    # Identity: headed by the character's name.
    name = _flat(brief.get("name")) or "This Character"
    ident = []
    if _flat(brief.get("alignment")):
        ident.append(f"Alignment: {_flat(brief.get('alignment'))}")
    if _flat(brief.get("deity")):
        ident.append(f"Deity: {_flat(brief.get('deity'))}")
    if _flat(brief.get("race")):
        ident.append(f"Race: {cap(brief.get('race'))}")
    cls = _flat(brief.get("char_class"))
    if cls:
        lvl = _flat(brief.get("level"))
        line = f"Level {lvl} {cls}" if lvl else cls
        if _flat(brief.get("class_2")):
            line += f" / {cap(brief.get('class_2'))}"
        ident.append(f"Class: {line}")
    if _flat(brief.get("build_archetype")):
        ident.append(f"Archetype: {_flat(brief.get('build_archetype'))}")
    if _flat(brief.get("build_tactics")):
        ident.append(f"Tactics: {_flat(brief.get('build_tactics'))}")
    if _flat(brief.get("main_stat")):
        ident.append(f"Stat Focus: {cap(brief.get('main_stat'))}")
    if _flat(brief.get("martial_disciplines")):
        ident.append(f"Disciplines: {_flat(brief.get('martial_disciplines'))}")
    if _flat(brief.get("region")):
        ident.append(f"Homeland: {cap(brief.get('region'))}")
    sections.append(section(name, ident))

    # Vocation: professions ("Name (Profession rank N)" -> "Name (rank N)"), craft, trainers.
    voc = [f"Profession: {_PROF_RANK_RE.sub('(rank', _flat(p))}"
           for p in as_list(brief.get("professions"))]
    if _flat(brief.get("craft")):
        voc.append(f"Known for: {cap(brief.get('craft'))}")
    for t in as_list(brief.get("trainers")):
        # Each entry reads "an average trainer who taught them X, Y" (built in main_test).
        s = _flat(t)
        voc.append(f"Training: {s[:1].upper() + s[1:]}")
    sections.append(section("Vocation", voc))

    # Family: the parents phrase split into bullets ("loving mother, absent father, raised in a
    # poor household" -> three), then sibling counts ("1 Older Brother", "2 Younger Sisters") --
    # or an explicit "No Siblings" so the section always covers both parents and siblings.
    fam = [cap(part) for part in _flat(brief.get("parents")).split(",") if part.strip()]
    sib_labels = ("Older Brother", "Younger Brother", "Older Sister", "Younger Sister")
    sibs = brief.get("siblings") or []
    sib_bullets = []
    for label, raw in zip(sib_labels, sibs):
        m = re.search(r"\d+", str(raw))          # sibling fields are " you have N older brothers"
        n = int(m.group()) if m else 0
        if n > 0:
            sib_bullets.append(f"{n} {label}{'' if n == 1 else 's'}")
    if sibs and not sib_bullets:
        sib_bullets.append("No Siblings")
    sections.append(section("Family", fam + sib_bullets))

    # Personality: the labeled trio (same trio the prose backstory used to close with).
    traits = [f"{label}: {_flat(brief.get(key))}"
              for label, key in (("Personality", "personality_traits"),
                                 ("Mannerisms", "mannerisms"), ("Flaws", "flaw"))
              if _flat(brief.get(key))]
    sections.append(section("Personality", traits))

    # Appearance: hair / eyes / build.
    looks = []
    hair = cap(" ".join(x for x in (_flat(brief.get("hair_type")), _flat(brief.get("hair_color"))) if x))
    if hair:
        looks.append(f"Hair: {hair}")
    if _flat(brief.get("eye_color")):
        looks.append(f"Eyes: {cap(brief.get('eye_color'))}")
    if _flat(brief.get("appearance")):
        looks.append(f"Build: {cap(brief.get('appearance'))}")
    sections.append(section("Appearance", looks))

    return "\n\n".join("\n".join(s) for s in sections if s)


# --------------------------------------------------------------------------- #
# config + few-shot examples
# --------------------------------------------------------------------------- #

def _config():
    """Load backstory_config.json once, layered over the baked-in defaults (so partial files work)."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        cfg = dict(_DEFAULT_CONFIG)
        try:
            cfg.update(json.loads(_CONFIG_PATH.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass  # missing/broken file -> defaults
        _CONFIG_CACHE = cfg
    return _CONFIG_CACHE


# --------------------------------------------------------------------------- #
# campaign lore (optional): grounds backstories in the homebrew setting
# --------------------------------------------------------------------------- #

def _lore():
    """Load campaign_lore.json once (optional). Returns a dict — {} when the file is missing or
    unparseable, so the SETTING block is simply omitted and behavior matches the no-lore default."""
    global _LORE_CACHE
    if _LORE_CACHE is None:
        loaded = {}
        try:
            parsed = json.loads(_LORE_PATH.read_text(encoding="utf-8-sig"))
            if isinstance(parsed, dict):
                loaded = parsed
        except (OSError, ValueError):
            pass  # missing / broken file -> no lore
        _LORE_CACHE = loaded
    return _LORE_CACHE


def _lore_region(lore, region):
    """Case-insensitively resolve a region (matching keys and any 'aliases') to its lore dict, or {}.
    character.region is title-cased at runtime (e.g. 'Tal-Falko'), so the match must be lowercased."""
    regions = (lore or {}).get("regions") or {}
    key = str(region or "").strip().lower()
    if not key:
        return {}
    for name, info in regions.items():
        if not isinstance(info, dict):
            continue
        if any(str(n).strip().lower() == key for n in [name] + list(info.get("aliases") or [])):
            return info
    return {}


def _lore_deity_notes(lore, brief, limit=2):
    """Up to `limit` one-line notes for the character's deity/deities from the lore 'deities' index."""
    index = {str(k).strip().lower(): v for k, v in ((lore or {}).get("deities") or {}).items()}
    out = []
    for nm in _flat(brief.get("deity")).split(","):
        note = index.get(nm.strip().lower())
        if note and note not in out:
            out.append(_flat(note))
        if len(out) >= limit:
            break
    return out


def _lore_context(brief):
    """The SETTING / CAMPAIGN CANON block for this character, or '' when no lore applies. Only
    documented regions (those with a 'brief') produce a block; everything else degrades to the
    generic, setting-agnostic behavior. Pulls the world blurb + tone, the homeland brief + naming,
    deity note(s), and one local order."""
    lore = _lore()
    region_info = _lore_region(lore, brief.get("region"))
    if not region_info.get("brief"):
        return ""
    lines = []
    world = lore.get("world") or {}
    if world.get("blurb"):
        lines.append(_flat(world["blurb"]))
    if world.get("tone"):
        lines.append("Tone: " + _flat(world["tone"]))
    homeland = _flat(brief.get("region")) or "their homeland"
    line = f"Homeland — {homeland}: {_flat(region_info['brief'])}"
    if region_info.get("naming"):
        line += " " + _flat(region_info["naming"])
    lines.append(line)
    notes = _lore_deity_notes(lore, brief)
    if notes:
        lines.append("Faith: " + " ".join(notes))
    orders = region_info.get("orders") or []
    if orders:
        lines.append("A notable local order: " + _flat(random.choice(orders)) + ".")
    header = "SETTING / CAMPAIGN CANON (treat as true; do not contradict; do not quote verbatim):"
    return header + "\n" + "\n".join(lines)


def _load_examples():
    """Read every .txt/.json example in backstory_examples/ once. Returns a list of
    {"backstory", "facts", "tags"} dicts; unparseable files are skipped silently."""
    global _EXAMPLES_CACHE
    if _EXAMPLES_CACHE is not None:
        return _EXAMPLES_CACHE
    out = []
    try:
        paths = sorted(_EXAMPLES_DIR.glob("*"))
    except OSError:
        paths = []
    for p in paths:
        suffix = p.suffix.lower()
        try:
            raw = p.read_text(encoding="utf-8-sig")  # -sig strips a leading BOM (Notepad-saved files)
        except OSError:
            continue
        if suffix == ".txt":
            if raw.strip():
                out.append({"backstory": raw.strip(), "facts": "", "tags": {}})
        elif suffix == ".json":
            try:
                data = json.loads(raw)
            except ValueError:
                continue
            for obj in (data if isinstance(data, list) else [data]):
                if isinstance(obj, dict) and str(obj.get("backstory", "")).strip():
                    out.append({
                        "backstory": str(obj["backstory"]).strip(),
                        "facts": str(obj.get("facts", "")).strip(),
                        "tags": obj.get("tags") or {},
                    })
    _EXAMPLES_CACHE = out
    return out


def _match_score(example, brief):
    """How well an example's tags resemble the character being generated (higher = closer)."""
    tags = example.get("tags") or {}
    weights = {"char_class": 3, "region": 2, "race": 2, "alignment": 1, "main_stat": 1, "gender": 1}
    score = 0
    for key, weight in weights.items():
        bv = str(brief.get(key, "")).lower().strip()
        tv = str(tags.get(key, "")).lower().strip()
        if bv and tv and bv == tv:
            score += weight
    return score


def _select_examples(brief, examples, n, smart_match):
    """Pick up to `n` few-shot examples: best-matching when smart_match, else random."""
    if not examples or n <= 0:
        return []
    if smart_match:
        # Stable: examples already in filename order; sort by descending match score only.
        ranked = sorted(examples, key=lambda e: _match_score(e, brief), reverse=True)
        return ranked[:n]
    return random.sample(examples, min(n, len(examples)))


# --------------------------------------------------------------------------- #
# prompt assembly
# --------------------------------------------------------------------------- #

def _clean(text):
    """Trim model output; if it was truncated mid-sentence, cut back to the last finished sentence."""
    text = (text or "").strip()
    if text and text[-1] not in ".!?\"')]" and any(p in text for p in ".!?"):
        cut = max(text.rfind(c) for c in ".!?")
        if cut > 40:
            text = text[:cut + 1].strip()
    return text


def _flat(v):
    """Render a field (str / list / None) as a clean comma-joined string."""
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x).strip() for x in v if str(x).strip())
    return str(v).strip()


def _first_sentence(text):
    """First sentence of a blurb (for the offline template's one-line homeland grounding)."""
    text = _flat(text)
    cut = text.find(". ")
    return (text[:cut + 1] if cut != -1 else text).strip()


def _normalize_focus(focus):
    """Coerce a focus argument (str like 'combat, faith', list, or None) into a clean lowercase list
    of recognized aspect keys. Unknown aspects are dropped."""
    if not focus:
        return []
    if isinstance(focus, str):
        items = [f for chunk in focus.split(",") for f in chunk.split()]
    elif isinstance(focus, (list, tuple, set)):
        items = [str(f) for f in focus]
    else:
        return []
    known = _DEFAULT_FOCUS_PHRASES.keys()
    seen, out = set(), []
    for raw in items:
        a = raw.strip().lower()
        if a in known and a not in seen:
            seen.add(a)
            out.append(a)
    return out


def _join_and(items):
    """Oxford-comma join: ['a'] -> 'a'; ['a','b'] -> 'a and b'; ['a','b','c'] -> 'a, b, and c'."""
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _focus_line(focus, cfg):
    """Build the dynamic emphasis sentence injected into the system prompt. Falls back to the config's
    default_focus (profession, matching the historical default) when no focus is requested."""
    phrases_map = cfg.get("focus_phrases") or _DEFAULT_FOCUS_PHRASES
    aspects = _normalize_focus(focus) or _normalize_focus(cfg.get("default_focus")) or ["profession"]
    phrases = [phrases_map[a] for a in aspects if a in phrases_map]
    if not phrases:
        return ""
    return ("IMPORTANT: give particular narrative weight to " + _join_and(phrases)
            + " — let these sit at the heart of the story rather than receiving a passing mention.")


def _build_system(focus, cfg):
    """The system-role instruction string, with word range and focus line filled in."""
    rng = cfg.get("word_range") or _DEFAULT_CONFIG["word_range"]
    lo, hi = (rng + [260, 260])[:2]
    instr = cfg.get("instructions") or _DEFAULT_INSTRUCTIONS
    # str.replace (not .format) so a hand-edited config with stray braces can't raise.
    return (instr.replace("{min_words}", str(lo))
                 .replace("{max_words}", str(hi))
                 .replace("{focus_line}", _focus_line(focus, cfg)))


def _build_summary(brief):
    """A short phrase describing what the character DOES (class / level / role / notables)."""
    parts = []
    cls, lvl = _flat(brief.get("char_class")), brief.get("level")
    if cls:
        parts.append(f"a level {lvl} {cls}" if lvl else f"a {cls}")
    second = _flat(brief.get("class_2"))
    if second:
        parts.append(f"multiclassed with {second}")
    stat = _flat(brief.get("main_stat"))
    if stat:
        parts.append(f"{stat}-focused")
    disc = _flat(brief.get("martial_disciplines"))
    if disc:
        parts.append(f"a Path of War initiator versed in {disc}")
    # Feats are intentionally omitted -- the house style keeps backstories off game mechanics.
    return ", ".join(parts)


def _trait_lines(brief):
    out = []
    for t in (brief.get("traits") or []):
        if isinstance(t, dict):
            nm, d = t.get("name", ""), t.get("description", "")
            out.append(f"- {nm}: {d}" if d else f"- {nm}")
        elif str(t).strip():
            out.append(f"- {t}")
    return out


def _family_text(brief):
    parts = []
    parents = _flat(brief.get("parents"))
    if parents:
        parts.append(parents)
    sibs = [_flat(s) for s in (brief.get("siblings") or []) if _flat(s)]
    if sibs:
        parts.append("; ".join(sibs))
    return ". ".join(parts)


def _build_facts(brief):
    """The FACTS block (everything after 'FACTS:\\n') describing this specific character."""
    facts = [f"Name: {_flat(brief.get('name')) or 'Unknown'}"]
    for label, key in (("Race", "race"), ("Gender", "gender"), ("Age", "age"),
                       ("Homeland / where they are from", "region")):
        v = _flat(brief.get(key))
        if v:
            facts.append(f"{label}: {v}")
    # Core of the story (lead with these): vocation, family/upbringing, homeland.
    for label, key in (("Profession(s) / vocation (the work that defines their days)", "professions"),
                       ("Notable craft / trade", "craft"),
                       ("Trainers / mentors who shaped them", "trainers")):
        v = _flat(brief.get(key))
        if v:
            facts.append(f"{label}: {v}")
    fam = _family_text(brief)
    if fam:
        facts.append(f"Family & upbringing (situation growing up): {fam}")
    # Secondary color.
    for label, key in (("Background", "background_traits"),
                       ("Alignment", "alignment"), ("Deity / faith", "deity")):
        v = _flat(brief.get(key))
        if v:
            facts.append(f"{label}: {v}")
    bs = _build_summary(brief)
    if bs:
        facts.append(f"Role / what they do: {bs}")
    tlines = _trait_lines(brief)
    if tlines:
        facts.append("Character traits (light flavor only):\n" + "\n".join(tlines))
    # Flavor color for the prose (the sheet's structured block lists these verbatim; the prose
    # must weave them in, never end with a labeled list of them).
    for label, key in (("Personality", "personality_traits"), ("Mannerisms", "mannerisms"),
                       ("Appearance", "appearance"), ("Flaws", "flaw")):
        v = _flat(brief.get(key))
        if v:
            facts.append(f"{label}: {v}")
    return "\n".join(facts)


def _build_messages(brief, focus, cfg):
    """Assemble the /api/chat messages array: system instruction, optional few-shot example turns,
    then the user turn with this character's facts."""
    messages = [{"role": "system", "content": _build_system(focus, cfg)}]
    lore_block = _lore_context(brief)  # campaign canon for the homeland/faith; '' when none applies
    if lore_block:
        messages.append({"role": "system", "content": lore_block})
    examples = _select_examples(brief, _load_examples(),
                                int(cfg.get("num_examples", 0) or 0), cfg.get("smart_match", True))
    for ex in examples:
        user_turn = ("FACTS:\n" + ex["facts"]) if ex.get("facts") else \
            "Write a Pathfinder NPC backstory in your established style."
        messages.append({"role": "user", "content": user_turn})
        messages.append({"role": "assistant", "content": ex["backstory"]})
    messages.append({"role": "user", "content": "FACTS:\n" + _build_facts(brief)})
    return messages


def _try_ollama(messages, cfg, tag="backstory"):
    api_key = os.environ.get("OLLAMA_API_KEY", "").strip()
    host = (os.environ.get("OLLAMA_HOST", "").strip()
            or (_DEFAULT_CLOUD_HOST if api_key else _DEFAULT_LOCAL_HOST))
    model = os.environ.get("OLLAMA_MODEL", "").strip() or _DEFAULT_MODEL
    url = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": cfg.get("temperature", 0.8),
            "num_predict": cfg.get("max_tokens", 800),
        },
    }
    # Reasoning models (gpt-oss) otherwise spend the whole token budget "thinking" and return empty
    # or mid-sentence content; "low" keeps reasoning minimal so the prose completes. Set
    # OLLAMA_THINK="" for plain models that reject the field.
    think = os.environ.get("OLLAMA_THINK", "low").strip()
    if think:
        payload["think"] = think
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = _clean((data.get("message") or {}).get("content") or "")
        if text:
            print(f"{tag}: generated via Ollama ({model} @ {host}).")
            return text
        print(f"{tag}: Ollama returned no content; using fallback.")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as e:
        print(f"{tag}: Ollama unavailable ({type(e).__name__}: {e}); using fallback.")
    return ""


def _template_backstory(brief, focus=None):
    """Deterministic offline composer (the safety net when no model is reachable): vocation /
    family / homeland-led prose only. No closing Personality/Mannerisms/Appearance/Flaws list --
    the sheet's structured fact block (structured_bio) displays those facts."""
    name = _flat(brief.get("name")) or "This character"
    race, region = _flat(brief.get("race")), _flat(brief.get("region"))
    align, deity = _flat(brief.get("alignment")), _flat(brief.get("deity"))
    summary = _build_summary(brief)
    prof = _flat(brief.get("professions"))
    craft, trainers = _flat(brief.get("craft")), _flat(brief.get("trainers"))
    fam = _family_text(brief)

    # Paragraph 1 — homeland grounding (when documented), then vocation (the work of their days).
    p_work = []
    region_info = _lore_region(_lore(), brief.get("region"))
    if region_info.get("brief"):
        s = _first_sentence(region_info["brief"])
        if s and not s.endswith((".", "!", "?")):
            s += "."
        if s:
            p_work.append(s)
    if prof:
        p_work.append(f"{name} makes their living as {prof}.")
    else:
        p_work.append(f"{name} is a {race}".rstrip() + (f" from {region}" if region else "") + ".")
    if craft:
        p_work.append(f"They are known in particular for their skill at {craft}.")
    if trainers:
        p_work.append(f"They learned their trade under {trainers}.")

    # Paragraph 2 — homeland, family/upbringing, role, faith.
    p_home = []
    if prof and (race or region):
        p_home.append(f"A {race}".rstrip() + (f" from {region}" if region else "")
                      + ", they were shaped by where they came from.")
    if fam:
        p_home.append(fam[0].upper() + fam[1:] + ".")
    if summary:
        p_home.append(f"These days they are {summary}.")
    if align:
        p_home.append(f"They hold to a {align} outlook"
                      + (f", keeping faith with {deity}." if deity else "."))

    paras = [" ".join(p) for p in (p_work, p_home) if p]
    return "\n\n".join(paras).strip()
