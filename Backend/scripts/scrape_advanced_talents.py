r"""Scrape the Spheres of Power / Might wiki for the authoritative list of advanced/legendary talents.

The pf1spheres compendium packs carry NO structured "advanced/legendary" flag, so the generator relies
on ``advanced_talents.json`` (the human-auditable registry that ``Backend/utils/class_func/spheres.py``
overlays on the talent data -- see ``_advanced_set`` / ``_is_advanced``).  That registry was previously
built from cross-references and was both incomplete (whole combat spheres like ``equipment`` /
``warleader`` were missing) and inconsistent.  This script rebuilds it comprehensively from the wiki,
which IS the source of truth: every sphere page lists its advanced talents under an
``Advanced <Sphere> Talents`` heading (magic) or a ``Legendary Talents`` heading (combat).

How it works:
  * Fetches each sphere page over **http** (the site 301-loops https->http, so we must request http
    directly with a browser User-Agent -- wikidot rejects the stdlib default UA).
  * Parses ``<hN>`` headers; for every section header matching ``Advanced ... Talents`` /
    ``Legendary Talents`` (excluding the deprecated ``Old ...`` sections) it collects the talent
    headers nested under it (the deepest header level inside that section -- ``<h4>`` in practice),
    keeping the wiki name verbatim incl. its ``(variant)`` / ``[source]`` suffix.
  * Maps the wiki slug to the generator's dataset sphere key and **merges** (union, dedup by the same
    match-normalization spheres.py uses) into the existing ``advanced_talents.json`` -- so curated /
    homebrew-only keys with no wiki page (e.g. power -> ``bear``) are preserved and nothing regresses.

This touches ONLY ``advanced_talents.json`` -- never the talent datasets -- so it cannot reintroduce
the magic ``type`` regression.  The matching of these suffixed names against the clean dataset keys is
handled at runtime by ``spheres._talent_match_norm`` (which strips the trailing ``(variant)``).

Run:  C:\Python310\python.exe Backend/scripts/scrape_advanced_talents.py [--dry-run]
"""

import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(REPO, "Backend", "json", "class_data", "spheres")
ADV_FILE = os.path.join(OUT_DIR, "advanced_talents.json")
DATASET_FILE = {
    "power": os.path.join(OUT_DIR, "spheres_of_power.json"),
    "might": os.path.join(OUT_DIR, "spheres_of_might_enriched.json"),
}

BASE_URL = "http://spheresofpower.wikidot.com/"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Sphere page slugs harvested from the wiki nav.  "power" == Magic Spheres, "might" == Combat Spheres.
# (Skill spheres are intentionally excluded -- they are not in the power/might compendium the generator
# draws from.)
SLUGS = {
    "power": [
        "alteration", "blood", "conjuration", "creation", "dark", "polished-dark", "death",
        "destruction", "divination", "enhancement", "fallen-fey", "fate", "illusion", "life",
        "light", "mana", "mind", "nature", "protection", "telekinesis", "time", "war", "warp",
        "weather",
    ],
    "might": [
        "alchemy", "athletics", "barrage", "barroom", "beastmastery", "berserker", "boxing", "brute",
        "dual-wielding", "duelist", "equipment-sphere", "fencing", "gladiator", "guardian", "lancer",
        "open-hand", "scoundrel", "scout", "shield", "sniper", "trap", "warleader-sphere", "wrestling",
        "leadership", "tech", "tinker", "pilot",
    ],
}

# Section headings that introduce advanced/legendary talents (lowercased, anchored). "Old ..." sections
# are deprecated reprints and are excluded by the leading-anchor.
SECTION_RE = re.compile(r"^(advanced\b.*\btalents?|legendary\b.*\btalents?)\s*$", re.I)
HEADER_RE = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.S)
_TAG = re.compile(r"<[^>]+>")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def match_norm(s):
    """Mirror ``spheres._talent_match_norm``: drop a trailing ``(variant)`` and ``[source]`` tags,
    strip apostrophes, lowercase, collapse whitespace.  This is the runtime match key, so deduping the
    registry by it yields exactly one entry per runtime-distinct talent."""
    s = str(s).split(" (")[0]
    s = re.sub(r"\s*\[[^\]]*\]\s*", " ", s.lower())
    for ch in ("'", "’", "`"):
        s = s.replace(ch, "")
    return re.sub(r"\s+", " ", s).strip()


def slug_to_key(slug):
    """Wiki slug -> generator dataset sphere key (hyphens->spaces, drop a trailing ' sphere')."""
    key = slug.replace("-", " ").strip()
    if key.endswith(" sphere"):
        key = key[: -len(" sphere")].strip()
    return key


def fetch(slug, retries=3):
    """GET the wiki page for ``slug`` over http; returns HTML text or None on persistent failure."""
    url = BASE_URL + slug
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, OSError) as exc:
            if attempt == retries:
                print(f"  !! fetch failed for {slug}: {exc}")
                return None
            time.sleep(0.8 * attempt)
    return None


def parse_advanced_names(page):
    """Return the verbatim talent names listed under any Advanced/Legendary section of ``page``."""
    headers = []
    for m in HEADER_RE.finditer(page):
        text = html.unescape(_TAG.sub("", m.group(2)).strip())
        if text:
            headers.append((int(m.group(1)), text))
    names = []
    for i, (lvl, txt) in enumerate(headers):
        if not SECTION_RE.match(txt):
            continue
        end = len(headers)
        for k in range(i + 1, len(headers)):
            if headers[k][0] <= lvl:          # next sibling/parent section ends this block
                end = k
                break
        block = headers[i + 1:end]
        if not block:
            continue
        # Talents are the most common header level in the block (h4 in practice).  Using the *mode*
        # rather than the deepest level avoids being fooled by a talent's stray <h5> sub-detail (which
        # broke death/divination/time/warp) and by any <h3> sub-group labels.  Tie -> shallowest.
        counts = {}
        for l, _ in block:
            counts[l] = counts.get(l, 0) + 1
        top = max(counts.values())
        talent_level = min(l for l, c in counts.items() if c == top)
        names.extend(t for l, t in block if l == talent_level)
    return names


def merge(existing, scraped):
    """Union ``existing`` + ``scraped`` (both lists of lowercased names), dedup by ``match_norm``,
    preferring the existing form on a tie (minimizes diff churn).  Returns a sorted list."""
    out, seen = [], set()
    for n in list(existing) + scraped:
        nn = match_norm(n)
        if not nn or nn in seen:
            continue
        seen.add(nn)
        out.append(n)
    return sorted(out)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    dry_run = "--dry-run" in sys.argv

    with open(ADV_FILE, encoding="utf-8") as fh:
        reg = json.load(fh)
    reg.setdefault("might", {})
    reg.setdefault("power", {})

    dataset_keys = {}
    for system, path in DATASET_FILE.items():
        with open(path, encoding="utf-8") as fh:
            dataset_keys[system] = set(json.load(fh).keys())

    skipped, empty, changes = [], [], 0
    for system in ("power", "might"):
        for slug in SLUGS[system]:
            key = slug_to_key(slug)
            if key not in dataset_keys[system]:
                skipped.append(f"{system}/{slug} (-> '{key}' not in dataset)")
                continue
            page = fetch(slug)
            time.sleep(0.3)
            if page is None:
                continue
            scraped = [n.lower() for n in parse_advanced_names(page)]
            if not scraped:
                empty.append(f"{system}/{slug}")
            before = reg[system].get(key, [])
            merged = merge(before, scraped)
            added = [n for n in merged if n not in before]
            changes += len(added)
            note = f"  +{len(added)} new" if added else ""
            print(f"[{system}] {slug} -> {key}: scraped {len(scraped)}, total {len(merged)}{note}")
            for n in added:
                print(f"        + {n}")
            reg[system][key] = merged

    # Sort sphere keys within each system; keep top-level order might, then power (matches the file).
    out = {sysk: {k: reg[sysk][k] for k in sorted(reg[sysk])} for sysk in ("might", "power")}

    print("\n=== summary ===")
    print(f"new names added: {changes}")
    if skipped:
        print("skipped (no dataset key):", ", ".join(skipped))
    if empty:
        print("WARNING - 0 advanced/legendary found (check manually):", ", ".join(empty))

    if dry_run:
        print("\n--dry-run: advanced_talents.json NOT written.")
        return
    with open(ADV_FILE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)   # match existing format (1-space, UTF-8)
    print(f"\nwrote {ADV_FILE}")


if __name__ == "__main__":
    main()
