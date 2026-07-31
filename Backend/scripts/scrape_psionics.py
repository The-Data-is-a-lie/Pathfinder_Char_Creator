"""Scrape the psionics master data resource from the Library of Metzofitz wiki (+ d20pfsrd races).

Source of truth for psionic *mechanics* is the Metzofitz wiki, not the `pf1-psionics` Foundry
module: the module ships identical placeholder `bab: low` / `hd: 6` / `skillsPerLevel: 2` on all
twelve classes and has no powers-known table anywhere (see
docs/wayfinder/psionics/issues/02-data-quality-ogl.md). The module stays the Foundry *render
target*, so names must reconcile against its packs -- that reconciliation is ticket 10, not here.

ACCESS GOTCHA: Cloudflare serves a JS challenge for plain `/wiki/<Page>` fetches, so requests and
WebFetch both fail. `api.php` is NOT challenged. Always go through the API with a browser UA.

Outputs (all under Backend/json/class_data/psionics/, mirroring class_data/path_of_war/):
    psionic_classes.json       raw per-class prose + the 20-row class table + feature sections
    psionic_powers_known.json  {class: {pp_per_day/powers_known/max_power_level: [20 ints]}}
    psionic_power_lists.json   {list: {"0".."9": [power names]}} -- "0" is the talents tier
    psionic_powers.json        per-power header fields + rules text
    psionic_races.json         the ten Psionics Unleashed races from d20pfsrd

Level arrays are 20 long, index = class level - 1 -- the Path of War convention
(class_data/path_of_war/path_of_war_maneuvers_known.json), not the 21-long spell convention.

Idempotent: re-running rewrites each file in place. Run from the repo root with the venv python
(C:/Python310 has no requests/pandas):
    .venv/Scripts/python.exe Backend/scripts/scrape_psionics.py
    .venv/Scripts/python.exe Backend/scripts/scrape_psionics.py --only classes powers
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "Backend/json/class_data/psionics"

WIKI_API = "https://libraryofmetzofitz.fandom.com/api.php"
D20_RACES = ("https://www.d20pfsrd.com/alternative-rule-systems/"
             "3rd-party-rules-systems/psionics-unleashed/races/")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
DELAY = 0.35          # polite pause between requests
BATCH = 50            # api.php caps multi-title queries at 50 for anonymous clients

# The twelve classes in scope: present on the wiki AND shipped as class items by pf1-psionics, so
# they render natively in Foundry. The wiki's other six (Genesis, Skipper, Thug, Warpmind, psionic
# Zealot, Soulknife (High Psionics)) are held for v2 -- and psionic Zealot collides with the Path
# of War 'zealot' key already in class_data.json.
CLASSES = {
    "Aegis": "aegis",
    "Cryptic": "cryptic",
    "Dread": "dread",
    "Highlord": "highlord",
    "Marksman": "marksman",
    "Psion": "psion",
    "Psychic Warrior": "psychic warrior",
    "Soulknife": "soulknife",
    "Tactician": "tactician",
    "Vitalist": "vitalist",
    "Voyager": "voyager",
    "Wilder": "wilder",
}

# Linked from the wiki's Powers page. Gambler / Gifted Blade / Sighted Seeker belong to classes and
# archetypes outside the twelve -- scraped anyway (cheap, and power pages cite them in their Level
# lines), flagged as out-of-scope by IN_SCOPE_LISTS below.
POWER_LIST_PAGES = [
    "Cryptic Powers", "Dread Powers", "Gambler Powers", "Gifted Blade Powers", "Highlord Powers",
    "Marksman Powers", "Psion/Wilder Powers", "Psychic Warrior Powers", "Sighted Seeker Powers",
    "Tactician Powers", "Vitalist Powers", "Voyager Powers",
]
DISCIPLINE_PAGE = "Psion Discipline Powers"   # two-level: discipline heading -> level headings
IN_SCOPE_LISTS = {
    "Cryptic Powers", "Dread Powers", "Highlord Powers", "Marksman Powers", "Psion/Wilder Powers",
    "Psychic Warrior Powers", "Tactician Powers", "Vitalist Powers", "Voyager Powers",
}

# Label spellings differ page to page (Psion says "Skill Ranks at Each Level", Soulknife says
# "Skill Ranks per Level"; the colon sometimes sits inside the bold markup and sometimes outside).
PROSE_FIELDS = {
    "role": ["Role"],
    "alignment": ["Alignment"],
    "hit die": ["Hit Die", "Hit Dice"],
    "starting wealth": ["Starting Wealth"],
    "class skills": ["Class Skills"],
    "skill ranks": ["Skill Ranks at Each Level", "Skill Ranks per Level",
                    "Skill Ranks Per Level", "Skill Ranks", "Skill Points at Each Level"],
}

# Power header fields, same variant problem.
POWER_FIELDS = {
    "discipline": ["Discipline"],
    "level": ["Level"],
    "display": ["Display"],
    "manifesting time": ["Manifesting Time", "Manifestation Time"],
    "range": ["Range"],
    "target": ["Target", "Targets"],
    "effect": ["Effect"],
    "area": ["Area"],
    "duration": ["Duration"],
    "saving throw": ["Saving Throw"],
    "power resistance": ["Power Resistance"],
    "power points": ["Power Points"],
}

# Header spellings drift per page -- Soulknife abbreviates to "bab", Marksman numbers its levels
# "1" not "1st", Highlord ships a typo ("kown") and Cryptic renames the column to "design level".
# Any header not listed here is preserved verbatim under the row's "extra" key rather than dropped
# (that is where Aegis' customization points and Soulknife's mind blade enhancement land).
TABLE_COLUMNS = {
    "level": ["level"],
    "bab": ["base attack bonus", "base attack", "bab"],
    "fort": ["fort save", "fortitude save", "fort"],
    "ref": ["ref save", "reflex save", "ref"],
    "will": ["will save", "will"],
    "special": ["special"],
    "pp_per_day": ["power points/day", "power points per day", "power points/ day",
                   "power point/day"],
    "powers_known": ["powers known"],
    "max_power_level": ["maximum power level known", "maximum power level", "max power level",
                        "maximum power level kown", "maximum design level known"],
}

_POWER_LABELS = sorted({label for aliases in POWER_FIELDS.values() for label in aliases}
                       | {"Augment"}, key=len, reverse=True)
_LABEL_ALT = "|".join(re.escape(label) for label in _POWER_LABELS)
# Fields separate on a newline, or on a ';' / ':' that is immediately followed by another label.
# A ';' or ':' NOT followed by a label stays inside its value ("Duration: One hour; see text").
POWER_SPLIT_RE = re.compile(r"\n+|[;:]\s*(?=(?:%s)\b)" % _LABEL_ALT, re.I)
POWER_FIELD_RE = re.compile(r"^\s*(%s)\b\s*:?\s*(.*)$" % _LABEL_ALT, re.I | re.S)

ORDINAL_RE = re.compile(r"^(\d+)(st|nd|rd|th)?\.?$", re.I)
DASHES = {"\u2014", "\u2013", "-", "\u2212", ""}

SESSION = requests.Session()
SESSION.headers["User-Agent"] = UA


# --------------------------------------------------------------------------------------- helpers

def clean(text: str) -> str:
    """Normalise the wiki's non-breaking spaces and stray whitespace."""
    text = (text or "").replace("\u00a0", " ").replace("\ufeff", "").replace("\u200b", "")
    return re.sub(r"[ \t]+", " ", text).strip()


def api(**params):
    params.setdefault("format", "json")
    params.setdefault("formatversion", 2)
    for attempt in range(4):
        try:
            resp = SESSION.get(WIKI_API, params=params, timeout=60)
            resp.raise_for_status()
            payload = resp.json()
            if "error" in payload:
                raise RuntimeError(payload["error"].get("info", "api error"))
            time.sleep(DELAY)
            return payload
        except Exception as exc:                                    # noqa: BLE001
            if attempt == 3:
                raise
            print(f"    retry {attempt + 1} ({exc})")
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def page_wikitext(title: str) -> str:
    return api(action="parse", page=title, prop="wikitext")["parse"]["wikitext"]


def page_html(title: str) -> str:
    return api(action="parse", page=title, prop="text")["parse"]["text"]


def bold_field(text: str, labels, tight: bool = False) -> str:
    """Pull a '''Label:'''value field, tolerating the colon inside or outside the bold markup.

    Two terminator modes, because the two page families are shaped differently:

    - loose (class pages): capture through blank lines, stop only at a bold label that starts a
      line. Class Skills runs to several paragraphs plus a bullet list before Skill Ranks.
    - tight (power pages): stop at ANY bold run or blank line. Power headers pack two fields onto
      one line ("Discipline: X; '''Level: '''Y"), and the last header is followed by the rules
      text with only a blank line between.
    """
    stop = r"(?='''|\n\n|\n\s*==|\Z)" if tight else r"(?=\n'''|\n\s*==|\Z)"
    for label in labels:
        pattern = (r"'''\s*" + re.escape(label) + r"\s*:?\s*'''\s*:?\s*(.*?)" + stop)
        match = re.search(pattern, text, re.S | re.I)
        if match:
            value = clean(match.group(1))
            if value:
                return value
    # Fallback: some pages forget the bold markup entirely (Tactician's skill ranks line).
    for label in labels:
        pattern = (r"^\s*" + re.escape(label) + r"\s*:\s*(.*?)(?=\n'''|\n\s*==|\n\n|\Z)")
        match = re.search(pattern, text, re.S | re.I | re.M)
        if match:
            value = clean(match.group(1))
            if value:
                return value
    return ""


def strip_markup(text: str) -> str:
    """Wikitext -> plain prose: unwrap links, drop bold/italic ticks and templates."""
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\{\{[^}]*\}\}", "", text)
    text = text.replace("'''", "").replace("''", "")
    return clean(text)


def split_sections(text: str):
    """Yield (heading, body) for every heading, at any '='-depth.

    Depth and inner spacing are inconsistent across pages -- Voyager writes
    ===='''Class Features'''==== with no inner spaces while Tactician writes === '''X''' === --
    so match any run of '=' and strip the decoration off the title.
    """
    def title_of(raw: str) -> str:
        # Clean BEFORE stripping: a non-breaking space between the bold ticks and the closing '='
        # run would otherwise halt strip() and leave the decoration attached.
        return clean(raw).strip("= ' ").strip("= '").strip()

    marks = [(m.start(), m.end(), title_of(m.group(0)))
             for m in re.finditer(r"^=+ *.+? *=+\s*$", text, re.M)]
    for idx, (_, end, heading) in enumerate(marks):
        stop = marks[idx + 1][0] if idx + 1 < len(marks) else len(text)
        yield heading, text[end:stop]


def write_json(name: str, payload) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


# --------------------------------------------------------------------------------------- classes

def parse_class_table(title: str):
    """Return (rows, columns_present) from the class's wikitable.

    Read from rendered HTML rather than raw wikitext: every cell carries inline styling that makes
    the wikitext form painful, and bs4's html.parser handles the rendered form with no lxml
    dependency (which this repo does not have).
    """
    soup = BeautifulSoup(page_html(title), "html.parser")
    for table in soup.find_all("table", class_="wikitable"):
        raw_rows = table.find_all("tr")
        if not raw_rows:
            continue
        headers = [clean(c.get_text(" ", strip=True)).lower()
                   for c in raw_rows[0].find_all(["th", "td"])]
        if "level" not in headers:
            continue                                    # editor's-note boxes are wikitables too
        mapping = {}
        for key, aliases in TABLE_COLUMNS.items():
            for idx, header in enumerate(headers):
                if header in aliases:
                    mapping[key] = idx
                    break
        unmapped = {idx: header for idx, header in enumerate(headers)
                    if idx not in mapping.values()}
        rows = []
        for raw in raw_rows[1:]:
            cells = [clean(c.get_text(" ", strip=True)) for c in raw.find_all(["th", "td"])]
            if not cells or not ORDINAL_RE.match(cells[0]):
                continue
            row = {}
            for key, idx in mapping.items():
                row[key] = cells[idx] if idx < len(cells) else ""
            extra = {header: cells[idx] for idx, header in unmapped.items() if idx < len(cells)}
            if extra:
                row["extra"] = extra
            rows.append(row)
        if rows:
            return rows, sorted(mapping), headers
    raise RuntimeError(f"no class table found on {title}")


def parse_features(text: str) -> dict:
    """The heading sections that follow the class table, minus the 'Class Features' wrapper."""
    features = {}
    for heading, body in split_sections(text):
        name = clean(heading).lower()
        prose = strip_markup(body)
        if name and prose and name not in {"class features", "class feature"}:
            features[name] = prose
    return features


def as_int(value: str) -> int:
    value = clean(value)
    if value in DASHES:
        return 0
    match = re.search(r"\d+", value.replace(",", ""))
    return int(match.group()) if match else 0


def bab_number(value: str) -> int:
    """'+15/+10/+5' -> 15."""
    match = re.search(r"\+?(\d+)", clean(value))
    return int(match.group(1)) if match else 0


def bab_category(level20: int) -> str:
    """H/M/L, the class_data.json vocabulary. Derived from the level-20 BAB, never trusted from a
    single declared field -- getting exactly this wrong is what makes the module's data unusable."""
    if level20 >= 20:
        return "H"
    if level20 >= 15:
        return "M"
    return "L"


def save_categories(rows) -> dict:
    """A good save opens at +2 and a poor save at +0 -- the standard PF1 progressions."""
    out = {}
    for key in ("fort", "ref", "will"):
        if key not in rows[0]:
            continue
        out[key] = "good" if bab_number(rows[0][key]) >= 2 else "poor"
    return out


def scrape_classes() -> None:
    print("classes:")
    classes, progressions = {}, {}
    for title, key in CLASSES.items():
        print(f"  {title}")
        text = page_wikitext(title)
        rows, columns, headers = parse_class_table(title)
        if len(rows) != 20:
            print(f"    WARNING: {len(rows)} table rows (expected 20)")

        entry = {"wiki_page": title, "columns": columns, "columns_raw": headers}
        for field, labels in PROSE_FIELDS.items():
            entry[field] = strip_markup(bold_field(text, labels))

        hit_die = re.search(r"d\d+", entry.get("hit die", ""))
        skill_ranks = re.search(r"\d+", entry.get("skill ranks", ""))
        level20 = bab_number(rows[-1].get("bab", ""))
        entry["derived"] = {
            "hit die": f"{hit_die.group()}." if hit_die else "",
            "skill points at each level": skill_ranks.group() if skill_ranks else "",
            "bab": bab_category(level20),
            "bab at 20": level20,
            "good saves": [k for k, v in save_categories(rows).items() if v == "good"],
            "manifests": "pp_per_day" in columns,
        }
        entry["table"] = rows
        entry["features"] = parse_features(text)
        classes[key] = entry

        progression = {}
        for column in ("pp_per_day", "powers_known", "max_power_level"):
            if column in columns:
                progression[column] = [as_int(r.get(column, "")) for r in rows]
        if progression:
            progressions[key] = progression

    write_json("psionic_classes.json", classes)
    write_json("psionic_powers_known.json", progressions)
    manifesting = sorted(k for k, v in classes.items() if v["derived"]["manifests"])
    print(f"  {len(classes)} classes, {len(manifesting)} manifest: {', '.join(manifesting)}")


# ----------------------------------------------------------------------------------- power lists

LEVEL_HEADING_RE = re.compile(r"^=+ *'*(\d+)(?:st|nd|rd|th)-Level +(.+?) *'* *=+", re.I | re.M)
TALENT_HEADING_RE = re.compile(r"^=+ *'*0-Level +(.+?) *'* *=+", re.I | re.M)
POWER_ENTRY_RE = re.compile(r"'''\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", re.M)


def powers_in(body: str):
    seen, names = set(), []
    for match in POWER_ENTRY_RE.finditer(body):
        name = clean(match.group(1))
        if name and name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)
    return names


def scrape_power_lists() -> None:
    print("power lists:")
    lists = {}
    for title in POWER_LIST_PAGES:
        text = page_wikitext(title)
        by_level = {}
        for heading, body in split_sections(text):
            match = re.match(r"(\d+)(?:st|nd|rd|th)-Level", heading, re.I)
            if match:
                by_level[str(int(match.group(1)))] = powers_in(body)
            elif re.match(r"0-Level", heading, re.I):
                by_level["0"] = powers_in(body)
        total = sum(len(v) for v in by_level.values())
        lists[title] = {"in_scope": title in IN_SCOPE_LISTS, "levels": by_level}
        print(f"  {title}: {total} entries across {len(by_level)} levels")

    # The discipline page nests level headings under a heading per discipline.
    text = page_wikitext(DISCIPLINE_PAGE)
    disciplines, current = {}, None
    for heading, body in split_sections(text):
        level = re.match(r"(\d+)(?:st|nd|rd|th)-Level", heading, re.I)
        if level and current:
            disciplines[current]["levels"][str(int(level.group(1)))] = powers_in(body)
        elif not level:
            current = clean(re.sub(r"Discipline Powers$", "", heading, flags=re.I))
            disciplines[current] = {"levels": {}}
    lists[DISCIPLINE_PAGE] = {"in_scope": True, "disciplines": disciplines}
    print(f"  {DISCIPLINE_PAGE}: {len(disciplines)} disciplines "
          f"({', '.join(sorted(disciplines))})")

    write_json("psionic_power_lists.json", lists)


# ---------------------------------------------------------------------------------------- powers

def collect_power_names(lists: dict):
    names, seen = [], set()

    def add(name):
        if name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)

    for entry in lists.values():
        for level_names in entry.get("levels", {}).values():
            for name in level_names:
                add(name)
        for discipline in entry.get("disciplines", {}).values():
            for level_names in discipline["levels"].values():
                for name in level_names:
                    add(name)
    return names


def parse_level_line(value: str) -> dict:
    """'Cryptic 0, gambler 0, psion/wilder 0' -> {'cryptic': 0, 'gambler': 0, 'psion/wilder': 0}"""
    out = {}
    for chunk in value.split(","):
        match = re.match(r"\s*(.+?)\s+(\d+)\s*$", clean(chunk))
        if match:
            out[match.group(1).strip().lower()] = int(match.group(2))
    return out


def parse_power(name: str, text: str) -> dict:
    """Split a power page into header fields + rules text + augment block.

    The header block is the run of leading bolded lines; the rules text is what follows. Walk the
    lines rather than searching for labels anywhere on the page, or a power that says "power
    points" mid-prose truncates its own rules text.

    Header fields are read by *structure*, not by bold markup: 32 pages carry mangled ticks
    (`'''Leve'''l''':'''`, `Level''' '''Kineticist 9`, or no colon at all). Fields are actually
    separated by newlines, or by a semicolon when a label follows -- so strip the ticks and split
    on that. A semicolon NOT followed by a label stays inside its value ("One hour; see text").
    """
    # Work in blank-line-separated paragraphs, not lines: a field's value sometimes wraps onto the
    # next line ("'''Level''':\nDread 4"), and the opening tick is sometimes misplaced
    # ("Di'''scipline:"), so "line starts with '''" is not a reliable header test. A paragraph is
    # header if, once the ticks are gone and it is folded to one line, it opens with a known label
    # or is a heading. The first paragraph that is neither begins the rules text.
    # A few pages title themselves with a bold line instead of a heading; normalise so the
    # leading-heading strip below catches both.
    text = re.sub(r"^'''([^']+)'''[ \t]*$", r"== \1 ==", text, flags=re.M)
    # ~20 pages break the "Power Resistance" label across a paragraph boundary, which would
    # otherwise end the header block early and lose every field after it (Power Points included).
    text = re.sub(r"Power'*\s*\n\s*\n\s*'*\s*Resistance", "Power Resistance", text)

    header_parts, body_parts = [], []
    for para in re.split(r"\n\s*\n", text):
        folded = clean(re.sub(r"\s*\n\s*", " ", para.replace("'''", "").replace("''", "")))
        # Some pages glue the '== Power Name ==' heading onto the first field line with a single
        # newline, so drop a leading heading before testing and storing.
        folded = re.sub(r"^=+[^=]*=+\s*", "", folded).strip()
        if not body_parts and (not folded or POWER_FIELD_RE.match(folded)):
            header_parts.append(folded)
        else:
            body_parts.append(para)
    header, body = "\n".join(header_parts), "\n\n".join(body_parts)

    record = {"name": name}
    sections = [clean(h).strip("= '") for h in re.findall(r"^=+ *.+? *=+\s*$", text, re.M)]
    if len(sections) > 1:
        # A chain page: only the first variant's header is parsed here. Flagged so the
        # reconciliation ticket can decide how chains are modelled rather than losing them.
        record["chain_sections"] = sections
    fields = {}
    for part in POWER_SPLIT_RE.split(header):
        match = POWER_FIELD_RE.match(part or "")
        if match:
            fields.setdefault(clean(match.group(1)).lower(), clean(match.group(2)))
    for field, labels in POWER_FIELDS.items():
        record[field] = next((fields[a.lower()] for a in labels if a.lower() in fields), "")
    record["level_by_class"] = parse_level_line(record.get("level", ""))

    augment = re.split(r"(?:'''\s*)?Augment\s*:?\s*(?:''')?", body, maxsplit=1, flags=re.I)
    record["text"] = strip_markup(augment[0])
    record["augment"] = strip_markup(augment[1]) if len(augment) > 1 else fields.get("augment", "")
    return record


def scrape_powers() -> None:
    print("powers:")
    lists_path = OUT_DIR / "psionic_power_lists.json"
    if not lists_path.exists():
        raise SystemExit("run --only lists first: psionic_power_lists.json is missing")
    names = collect_power_names(json.loads(lists_path.read_text(encoding="utf-8")))
    print(f"  {len(names)} distinct power names referenced by the lists")

    powers, missing, redirects = {}, [], {}
    for start in range(0, len(names), BATCH):
        chunk = names[start:start + BATCH]
        payload = api(action="query", prop="revisions", rvslots="main", rvprop="content",
                      titles="|".join(chunk), redirects=1)["query"]
        for hop in payload.get("redirects", []):
            redirects[hop["from"]] = hop["to"]
        for page in payload.get("pages", []):
            title = page["title"]
            if page.get("missing"):
                missing.append(title)
                continue
            content = page["revisions"][0]["slots"]["main"]["content"]
            powers[title] = parse_power(title, content)
        print(f"  fetched {min(start + BATCH, len(names))}/{len(names)}")

    for source, target in redirects.items():
        if target in powers:
            powers[target].setdefault("aliases", []).append(source)

    write_json("psionic_powers.json", powers)
    print(f"  {len(powers)} power pages, {len(redirects)} redirects, {len(missing)} missing")
    if missing:
        print("  MISSING: " + ", ".join(sorted(missing)[:20]))


# ----------------------------------------------------------------------------------------- races

# d20pfsrd carries two race-page layouts: a newer one with explicit labels ("Ability Score
# Modifiers: ...") and an older one where the trait itself is the label ("+2 Dexterity, +2 Wisdom,
# -2 Charisma:", "Medium:", "Normal Speed:") -- the same shape Backend/json/PlayableRaces.json
# already uses. Match both. Anything unmatched still survives in the record's "paragraphs" list.
RACE_LABELS = {
    "ability": re.compile(r"ability (score )?(modifier|racial)|^[+–−-]\d+ +(Str|Dex|Con|Int|Wis|Cha)", re.I),
    "size": re.compile(r"^size|^(fine|diminutive|tiny|small|medium|large|huge)\b", re.I),
    "speed": re.compile(r"^(base )?speed|^(normal|slow|fast) (speed|and steady)", re.I),
    "languages": re.compile(r"^languages", re.I),
}


def scrape_races() -> None:
    print("races:")
    index = SESSION.get(D20_RACES, timeout=60)
    index.raise_for_status()
    soup = BeautifulSoup(index.text, "html.parser")
    links = {}
    for anchor in soup.select("a[href]"):
        href = anchor["href"]
        if D20_RACES in href and href.rstrip("/") != D20_RACES.rstrip("/"):
            name = clean(anchor.get_text(" ", strip=True))
            if name and name.lower() not in {"races"}:
                links.setdefault(name, href)
    print(f"  {len(links)} race subpages: {', '.join(sorted(links))}")

    races = {}
    for name, href in sorted(links.items()):
        time.sleep(DELAY)
        try:
            resp = SESSION.get(href, timeout=60)
            resp.raise_for_status()
        except Exception as exc:                                    # noqa: BLE001
            print(f"    {name}: FAILED ({exc})")
            continue
        # Parse the bytes, not resp.text: d20pfsrd's declared charset is wrong and requests'
        # fallback turns every en dash into mojibake. bs4 sniffs the meta charset correctly.
        page = BeautifulSoup(resp.content, "html.parser")
        article = page.find("div", class_="article-content") or page.find("article") or page
        # Some races (Ophiduan) lay their racial traits out as a table rather than paragraphs.
        paragraphs = [clean(node.get_text(" ", strip=True))
                      for node in article.find_all(["p", "li", "tr"])]
        paragraphs = [re.sub(r"\s+([,.;:])", r"\1", p) for p in paragraphs if p]
        record = {"source_url": href, "traits": []}
        for para in paragraphs:
            # Labels are sometimes 'Size: ...' and sometimes a bare run-in heading 'Size Blues
            # are Small...', so test the opening words rather than requiring a colon.
            head = re.split(r"[:.]", para)[0][:40]
            for key, pattern in RACE_LABELS.items():
                if key not in record and pattern.search(head):
                    record[key] = para
            if re.match(r"^[A-Z][A-Za-z' \-()]{2,40}\s*\(?(Ex|Su|Sp)?\)?\s*:", para):
                record["traits"].append(para)
        record["paragraphs"] = paragraphs
        races[name] = record
        print(f"    {name}: {len(paragraphs)} paragraphs, {len(record['traits'])} traits")

    write_json("psionic_races.json", races)


# ------------------------------------------------------------------------------------------ main

STEPS = {
    "classes": scrape_classes,
    "lists": scrape_power_lists,
    "powers": scrape_powers,
    "races": scrape_races,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", nargs="+", choices=sorted(STEPS),
                        help="run a subset of the steps (default: all, in order)")
    args = parser.parse_args()
    for step in (args.only or ["classes", "lists", "powers", "races"]):
        STEPS[step]()
    print("done -- now run Backend/scripts/validate_psionics_data.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
