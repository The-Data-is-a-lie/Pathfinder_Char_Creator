"""Build mythic_traditions.json + mythic_sphere_masteries.json from the Mythic Spheres wikidot
page (mythic map; Daniel's rulings 2026-08-14).

House scope: of the whole Mythic Spheres system, exactly TWO pieces are in --
  * Mythic traditions (drawbacks / qualities / boons), for EVERY mythic character;
  * Mythic sphere masteries, for sphere users only -- they are RAW 1st-tier universal path
    abilities, so the chooser merges them into the path-ability pool of a mythic character whose
    spheres_flag is on, filtered to the spheres actually held.
Everything else on the page (spheremaster path abilities, mythic talents, the new universal path
abilities, mythic class features) stays out of scope, per the standing house rule that Mythic
Spheres proper is out -- these two carve-outs are the recorded exceptions.

Curation is FLAGGED, never silent (same doctrine as build_mythic_path_abilities.py): overrides
below add machine-readable fields -- `flag` (chooser skips), `requires_spheres` (eligible only
when spheres are on), `counts_as`/`cost` (drawback/boon budget arithmetic), `house_rule`
(the text stays RAW, the chooser implements the house version), `auto` (the chooser resolves the
grant into a concrete pick).

Usage:
    python Backend/scripts/build/build_mythic_traditions.py [--cache-dir DIR]
"""
import argparse
import html as html_mod
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.paths import repo_path  # noqa: E402

URL = 'http://spheresofpower.wikidot.com/mythic-spheres'
OUT_TRADITIONS = repo_path('Backend/json/mythic_traditions.json')
OUT_MASTERIES = repo_path('Backend/json/mythic_sphere_masteries.json')

DRAWBACK_OVERRIDES = {
    'sealed': {'counts_as': 2},
    'traditional': {
        'requires_spheres': True,
        'flag': 'needs three general casting drawbacks; the generator does not model casting-drawback counts',
    },
}
QUALITY_OVERRIDES = {
    'spherebound': {'requires_spheres': True},
}
BOON_OVERRIDES = {
    'expertise': {
        'house_rule': ("Sieg's Guide inversion: draws a MISSED feature from a class the character "
                       "HAS, at the class level they have (Fighter 11/Wizard 3 -> fighter features "
                       "<=11 or wizard <=3) -- not a feature from a class they lack. The chooser "
                       "implements the house version; this text stays RAW for the sheet."),
        'auto': 'missed_class_feature',
    },
    'legendary gear': {
        'flag': 'grants artifact machinery the generator cannot construct',
        'cost': 2,
    },
    'mythic exemplar': {'auto': 'bonus_first_tier_path_ability'},
    'recharging magic': {'requires_spheres': True},
}

_H2_RE = re.compile(r'<h2[^>]*><span>(?P<title>.*?)</span></h2>')
_H3_RE = re.compile(r'<h3[^>]*><span>(?P<title>.*?)</span></h3>')
_TAG_RE = re.compile(r'<[^>]+>')
_CHAR_FIXES = {'‘': "'", '’': "'", '“': '"', '”': '"', '–': '-', '—': '-', '…': '...', '\xa0': ' ', '�': "'"}


def _fetch(cache_dir=None):
    if cache_dir:
        cached = Path(cache_dir) / 'mythic-spheres.html'
        if cached.exists():
            return cached.read_text(encoding='utf-8', errors='replace')
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 (char-generator build script)'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode('utf-8', errors='replace')
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        (Path(cache_dir) / 'mythic-spheres.html').write_text(raw, encoding='utf-8')
    return raw


def _clean(text):
    text = _TAG_RE.sub(' ', text)
    text = html_mod.unescape(text)
    for bad, good in _CHAR_FIXES.items():
        text = text.replace(bad, good)
    return re.sub(r'\s+', ' ', text).strip()


def _section(raw, title):
    heads = [(m.start(), m.end(), _clean(m.group('title'))) for m in _H2_RE.finditer(raw)]
    for idx, (_, end, name) in enumerate(heads):
        if name == title:
            nxt = heads[idx + 1][0] if idx + 1 < len(heads) else len(raw)
            return raw[end:nxt]
    raise SystemExit(f'section {title!r} not found -- the page layout moved, update the parser')


_H4_RE = re.compile(r'<h4[^>]*><span>(?P<title>.*?)</span></h4>')


def _entries(section_html, overrides, stop_at=None):
    """h4-titled entries -> {name: {description, type, ...overrides}}.

    `stop_at` cuts the section before a trailing sub-section (the boons list runs into 'Sample
    Mythic Traditions'). Variant paragraphs ('<strong>Phobia (Variant):' -- the session-based
    alternates the page itself says not to use in traditional games) are dropped per entry."""
    if stop_at:
        cut = section_html.find(stop_at)
        if cut != -1:
            section_html = section_html[:cut]
    heads = list(_H4_RE.finditer(section_html))
    out = {}
    for idx, m in enumerate(heads):
        title = _clean(m.group('title'))
        kind = re.search(r'\((Ex|Su|Sp)\)$', title)
        name = re.sub(r'\s*\((Ex|Su|Sp)\)$', '', title)
        end = heads[idx + 1].start() if idx + 1 < len(heads) else len(section_html)
        body = section_html[m.end():end]
        body = re.split(r'<p>\s*<strong>[^<]*\(Variant\)\s*:', body)[0]
        entry = {'description': _clean(body), 'type': kind.group(1) if kind else ''}
        entry.update(overrides.get(name.lower(), {}))
        out[name] = entry
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache-dir', default=None)
    args = ap.parse_args()
    raw = _fetch(args.cache_dir)

    drawbacks = _entries(_section(raw, 'Mythic Drawbacks'), DRAWBACK_OVERRIDES)
    qualities = _entries(_section(raw, 'Mythic Qualities'), QUALITY_OVERRIDES)
    boons = _entries(_section(raw, 'Mythic Boons'), BOON_OVERRIDES,
                     stop_at='Sample Mythic Traditions')

    traditions = {
        '_readme': [
            'Generated by Backend/scripts/build/build_mythic_traditions.py -- do not hand-edit;',
            'rerun after changing its overrides or parser. Source: the Mythic Spheres wikidot page,',
            'mythic traditions tab. House scope (Daniel, 2026-08-14): traditions apply to EVERY',
            'mythic character; up to 3 drawbacks, each buying one boon OR +1 mythic power/day; at',
            'most one quality. Variant (session-based) drawback texts are deliberately omitted.',
            'Machine-readable fields: flag (chooser skips), requires_spheres, counts_as, cost,',
            'house_rule (text stays RAW, chooser implements the house version), auto.',
        ],
        'drawbacks': drawbacks,
        'qualities': qualities,
        'boons': boons,
    }
    Path(OUT_TRADITIONS).write_text(json.dumps(traditions, indent=1, ensure_ascii=False) + '\n',
                                    encoding='utf-8')
    print(f'traditions: {len(drawbacks)} drawbacks, {len(qualities)} qualities, {len(boons)} boons')

    masteries = {}
    heads = [(m.start(), m.end(), _clean(m.group('title'))) for m in _H2_RE.finditer(raw)]
    for m in _H3_RE.finditer(raw):
        title = _clean(m.group('title'))
        got = re.match(r'Mythic Sphere Mastery:\s*(.+)', title)
        if not got:
            continue
        sphere = got.group(1).strip()
        nxt_h3 = _H3_RE.search(raw, m.end())
        body = raw[m.end():nxt_h3.start() if nxt_h3 else len(raw)]
        tier_head = [t for s, _, t in heads if s < m.start() and 'Tier' in t]
        tier = {'1st': 1, '3rd': 3, '6th': 6}.get((tier_head[-1].split('-')[0] if tier_head else '1st'), 1)
        masteries[sphere] = {'tier': tier, 'description': _clean(body)}

    out = {
        '_readme': [
            'Generated by Backend/scripts/build/build_mythic_traditions.py. Mythic sphere',
            'masteries are RAW 1st-tier UNIVERSAL PATH ABILITIES from the Mythic Spheres wikidot',
            "page -- in house scope for SPHERE USERS ONLY (Daniel, 2026-08-14): the ability",
            'chooser merges the masteries of spheres the character actually has into the',
            'path-ability pool when spheres_flag is on. Keyed by sphere name.',
        ],
        'masteries': masteries,
    }
    Path(OUT_MASTERIES).write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n',
                                   encoding='utf-8')
    print(f'masteries: {len(masteries)} spheres')


if __name__ == '__main__':
    main()
