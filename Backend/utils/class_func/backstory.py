"""Generate a coherent 1-2 paragraph character backstory from the generated character's data.

Uses an Ollama-compatible chat endpoint when one is reachable, and falls back to a deterministic
template otherwise (e.g. the deployed backend where no local Ollama exists, while a local model is
still downloading, or when the cloud free-tier rate limit is hit). The same code path serves both:

  - LOCAL Ollama:  leave OLLAMA_API_KEY unset -> host defaults to http://localhost:11434,
                   model defaults to "gpt-oss:20b".
  - Ollama CLOUD:  set OLLAMA_API_KEY (free key from https://ollama.com/settings/keys) -> host
                   defaults to https://ollama.com; set OLLAMA_MODEL="gpt-oss:20b-cloud".

Env:
  OLLAMA_API_KEY  optional bearer token; presence flips the default host to Ollama Cloud.
  OLLAMA_HOST     explicit host override.
  OLLAMA_MODEL    model name (default "gpt-oss:20b").
"""
import json
import os
import urllib.error
import urllib.request

_DEFAULT_LOCAL_HOST = "http://localhost:11434"
_DEFAULT_CLOUD_HOST = "https://ollama.com"
_DEFAULT_MODEL = "gpt-oss:20b"
_TIMEOUT = 120


def generate_backstory(brief, use_api=True):
    """Return a 1-2 paragraph backstory string for the character described by `brief` (a dict).

    When `use_api` is true, tries Ollama (local or cloud) first; when false (the "use API" button is
    off), the network call is skipped entirely and the deterministic template is used. Always returns
    a non-empty string."""
    text = _try_ollama(_build_prompt(brief)) if use_api else ""
    if not text:
        text = _template_backstory(brief)
    return (text or "").strip()


# --------------------------------------------------------------------------- #
# helpers
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
    feats = brief.get("notable_feats") or []
    if isinstance(feats, (list, tuple)):
        feats = [str(f) for f in feats if str(f).strip()]
        if feats:
            parts.append("notable for " + ", ".join(feats[:3]))
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


def _build_prompt(brief):
    facts = [f"Name: {_flat(brief.get('name')) or 'Unknown'}"]
    for label, key in (("Race", "race"), ("Gender", "gender"), ("Age", "age"),
                       ("Homeland", "region"), ("Alignment", "alignment"), ("Deity", "deity")):
        v = _flat(brief.get(key))
        if v:
            facts.append(f"{label}: {v}")
    bs = _build_summary(brief)
    if bs:
        facts.append(f"Build / what they do: {bs}")
    tlines = _trait_lines(brief)
    if tlines:
        facts.append("Character traits (mechanical flavor to weave in narratively):\n" + "\n".join(tlines))
    for label, key in (("Personality", "personality_traits"), ("Mannerisms", "mannerisms"),
                       ("Flaws", "flaw"), ("Background", "background_traits"),
                       ("Professions / vocations (central to their daily life)", "professions"),
                       ("Notable craft / trade", "craft"),
                       ("Trainers they studied under (who shaped their skills)", "trainers"),
                       ("Appearance", "appearance")):
        v = _flat(brief.get(key))
        if v:
            facts.append(f"{label}: {v}")
    fam = _family_text(brief)
    if fam:
        facts.append(f"Family: {fam}")

    return (
        "You are a Pathfinder 1st Edition loremaster. Write a cohesive 2-3 paragraph third-person "
        "backstory (about 160-260 words) for the NPC described by the facts below. Weave the facts "
        "into natural narrative prose: ground the character in their homeland, faith and alignment, "
        "and reflect what their build/class lets them do. IMPORTANT: devote a substantial part of "
        "the story to their profession(s), their notable craft or trade, and the trainers who taught "
        "them — these vocations and mentors define their everyday life and how they came to be who "
        "they are, so give each real narrative weight rather than a passing mention. Also work in the "
        "flavor of their traits, personality and history. Use ONLY the given facts — you may add light "
        "connective color, but do not invent contradictory details, new proper nouns, or specific "
        "events. Do NOT list stats, labels or bullet points; write flowing prose only. Output only "
        "the backstory.\n\n"
        "FACTS:\n" + "\n".join(facts)
    )


def _try_ollama(prompt):
    api_key = os.environ.get("OLLAMA_API_KEY", "").strip()
    host = (os.environ.get("OLLAMA_HOST", "").strip()
            or (_DEFAULT_CLOUD_HOST if api_key else _DEFAULT_LOCAL_HOST))
    model = os.environ.get("OLLAMA_MODEL", "").strip() or _DEFAULT_MODEL
    url = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.8, "num_predict": 800},
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
            print(f"backstory: generated via Ollama ({model} @ {host}).")
            return text
        print("backstory: Ollama returned no content; using template fallback.")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as e:
        print(f"backstory: Ollama unavailable ({type(e).__name__}: {e}); using template fallback.")
    return ""


def _template_backstory(brief):
    """Deterministic offline composer (the safety net when no model is reachable)."""
    name = _flat(brief.get("name")) or "This character"
    race, region = _flat(brief.get("race")), _flat(brief.get("region"))
    align, deity = _flat(brief.get("alignment")), _flat(brief.get("deity"))
    summary = _build_summary(brief)
    pers, mann = _flat(brief.get("personality_traits")), _flat(brief.get("mannerisms"))
    flaw, prof = _flat(brief.get("flaw")), _flat(brief.get("professions"))
    craft, trainers = _flat(brief.get("craft")), _flat(brief.get("trainers"))
    fam = _family_text(brief)
    trait_names = _flat([t.get("name") if isinstance(t, dict) else t
                         for t in (brief.get("traits") or [])])

    p1 = [f"{name} is a {race}".rstrip() + (f" hailing from {region}" if region else "") + "."]
    if summary:
        p1.append(f"They are {summary}.")
    if align:
        p1.append(f"Their alignment is {align}"
                  + (f", and they keep faith with {deity}." if deity else "."))
    if fam:
        p1.append(fam[0].upper() + fam[1:] + ".")

    # Vocation chunk — professions, craft and trainers carry real weight in this character's history.
    p_work = []
    if prof:
        p_work.append(f"Much of their life has been shaped by their work as {prof}.")
    if craft:
        p_work.append(f"They are known in particular for their skill at {craft}.")
    if trainers:
        p_work.append(f"They honed their abilities under the guidance of {trainers}.")

    p2 = []
    if trait_names:
        p2.append(f"Their defining traits include {trait_names}.")
    if pers:
        p2.append(f"In temperament they are {pers}.")
    if mann:
        p2.append(f"Among their mannerisms: {mann}.")
    if flaw:
        p2.append(f"For all that, they are marked by {flaw}.")

    paras = [" ".join(p) for p in (p1, p_work, p2) if p]
    return "\n\n".join(paras).strip()
