"""Build Backend/json/mythic_path_abilities.json from Archives of Nethys (mythic map, ticket 03).

The six RAW paths' ability pools -- 1st/3rd/6th-tier gated -- plus each path's chassis (bonus HP
per tier, the tier-1 feature and its sub-choice options, the 10th-tier capstone), with the
UNIVERSAL ability list merged into every path's pool at build time. One pool per path is the
ruling: the chooser sees a single dataset, the sheet renders a single bucket, and the universal/
path distinction survives only as a per-ability `universal` marker no chooser branches on.

THE POOL MOVES, IT IS NOT COPIED: this file is consumed only by the mythic chooser
(utils/class_func/mythic.py) and is never seeded into class_data.json's `chooseable` path --
the 27-silently-unpickable-shifter-aspects lesson.

Curation is FLAGGED, never silent: an ability the generator cannot honestly grant carries a
`flag` field with the reason, and the chooser skips flagged entries. Deleting a row instead of
flagging it is how a pool quietly lies about its own size.

Usage:
    python Backend/scripts/build/build_mythic_path_abilities.py [--cache-dir DIR]

Re-fetches AoN on every run (six path pages + six ability pages + universal); --cache-dir reuses
previously downloaded HTML for offline re-parses.
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.paths import repo_path  # noqa: E402

BASE = 'https://www.aonprd.com/'
PATHS = ['Archmage', 'Champion', 'Guardian', 'Hierophant', 'Marshal', 'Trickster']
OUT = repo_path('Backend/json/mythic_path_abilities.json')

# Load-bearing curation: the chooser skips these. Flag, never delete.
FLAGS = {
    'legendary item': 'grants an artifact the generator cannot construct; a GM-built item, not a pick',
}

# cp1252 artifacts AoN ships (the CSVs carry the same); normalized so downstream regexes and the
# sheet never meet a stray \x92.
_CHAR_FIXES = {
    '‘': "'", '’': "'", '“': '"', '”': '"',
    '–': '-', '—': '-', '…': '...', '\xa0': ' ', '�': "'",
}

_ABILITY_RE = re.compile(
    r'<b>(?P<name>[^<]+?)\s*(?:\((?P<kind>Ex|Su|Sp)\))?\s*</b>\s*'
    r'\((?P<sourcelink>.*?)\)\s*:\s*(?P<desc>.*?)<hr\s*/?>',
    re.S)
_TIER_HEAD_RE = re.compile(r'(?P<tier>1st|3rd|6th)-Tier [A-Za-z]+ Path Abilities')
_TAG_RE = re.compile(r'<[^>]+>')


def _fetch(url, cache_dir=None):
    name = re.sub(r'\W+', '_', url.split('/')[-1]) + '.html'
    if cache_dir:
        cached = Path(cache_dir) / name
        if cached.exists():
            return cached.read_text(encoding='utf-8', errors='replace')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (char-generator build script)'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode('utf-8', errors='replace')
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        (Path(cache_dir) / name).write_text(raw, encoding='utf-8')
    return raw


def _clean(text):
    import html as _html
    text = _TAG_RE.sub('', text)
    text = _html.unescape(text)
    for bad, good in _CHAR_FIXES.items():
        text = text.replace(bad, good)
    return re.sub(r'\s+', ' ', text).strip()


def parse_abilities(html):
    """{name: {tier, type, source, description}} for one PathAbilities.aspx page."""
    sections = list(_TIER_HEAD_RE.finditer(html))
    out = {}
    for idx, head in enumerate(sections):
        tier = {'1st': 1, '3rd': 3, '6th': 6}[head.group('tier')]
        end = sections[idx + 1].start() if idx + 1 < len(sections) else len(html)
        for m in _ABILITY_RE.finditer(html, head.end(), end):
            name = _clean(m.group('name'))
            entry = {
                'tier': tier,
                'type': m.group('kind') or '',
                'source': _clean(m.group('sourcelink')),
                'description': _clean(m.group('desc')),
            }
            if name.lower() in FLAGS:
                entry['flag'] = FLAGS[name.lower()]
            out[name] = entry
    return out


def parse_path_page(html, path_name):
    """The path chassis: bonus HP, the tier-1 feature with its options, the capstone."""
    text = _clean(html[html.find('Bonus Hit Points'):][:400])
    hp = re.search(r'you gain (\d+) bonus hit points', text)

    # The tier-1 feature ("Archmage Arcana : Select one of the following...") runs from its bold
    # heading to the generic "Path Ability :" paragraph; options are the bold (Su)/(Ex) entries.
    feature = None
    feat_m = re.search(r'<b>\s*(?P<fname>[A-Z][^<:]*?)\s*</b>\s*:\s*Select one of the following', html)
    if feat_m:
        seg_end = html.find('<b>Path Ability</b>', feat_m.end())
        seg = html[feat_m.end():seg_end if seg_end != -1 else feat_m.end() + 12000]
        options = {}
        # Options are ITALIC headings ("<i>Arcane Surge (Su)</i>:"); inline spell names are italic
        # too but never end in an (Ex|Su|Sp) tag, which is what keeps them out of this match.
        for om in re.finditer(r'<i>\s*(?P<name>[^<]+?)\s*\((?P<kind>Ex|Su|Sp)\)\s*</i>\s*:\s*(?P<desc>.*?)'
                              r'(?=<i>[^<]+\((?:Ex|Su|Sp)\)\s*</i>\s*:|\Z)', seg, re.S):
            options[_clean(om.group('name'))] = {
                'type': om.group('kind'),
                'description': _clean(om.group('desc')),
            }
        feature = {'name': _clean(feat_m.group('fname')), 'options': options}

    capstone = None
    cap_m = re.search(r'<b>\s*(?P<name>[A-Z][^<]*?)\s*\((?P<kind>Ex|Su|Sp)\)\s*:?\s*</b>\s*:?\s*(?P<desc>At 10th tier.*?)(?=<b>|</span>|\Z)', html, re.S)
    if cap_m:
        capstone = {'name': _clean(cap_m.group('name')), 'type': cap_m.group('kind'),
                    'description': _clean(cap_m.group('desc'))}

    return {
        'display': path_name,
        'bonus_hp_per_tier': int(hp.group(1)) if hp else None,
        'tier1_feature': feature,
        'capstone': capstone,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache-dir', default=None)
    args = ap.parse_args()

    universal = parse_abilities(_fetch(BASE + 'PathAbilities.aspx?Path=Universal', args.cache_dir))
    print(f'universal: {len(universal)} abilities')

    paths = {}
    for path_name in PATHS:
        meta = parse_path_page(_fetch(BASE + f'MythicPaths.aspx?Path={path_name}', args.cache_dir), path_name)
        own = parse_abilities(_fetch(BASE + f'PathAbilities.aspx?Path={path_name}', args.cache_dir))
        merged = {}
        for name, entry in own.items():
            merged[name] = dict(entry, universal=False)
        for name, entry in universal.items():
            # A path-specific ability keeps its row on a name clash; none exists today, and a
            # future one should be visible rather than silently overwritten.
            if name in merged:
                print(f'  NOTE {path_name}: universal {name!r} shadowed by path ability, path row kept')
                continue
            merged[name] = dict(entry, universal=True)
        meta['abilities'] = merged
        paths[path_name.lower()] = meta
        flagged = sum(1 for a in merged.values() if a.get('flag'))
        print(f'{path_name.lower()}: {len(own)} own + universal -> {len(merged)} '
              f'(hp {meta["bonus_hp_per_tier"]}, tier1 {len((meta["tier1_feature"] or {}).get("options", {}))} options, '
              f'capstone {bool(meta["capstone"])}, flagged {flagged})')

    out = {
        '_readme': [
            'Generated by Backend/scripts/build/build_mythic_path_abilities.py -- do not hand-edit;',
            'rerun the script after changing its FLAGS or parsers. Source: Archives of Nethys',
            '(PathAbilities.aspx / MythicPaths.aspx), Mythic Adventures et al. per-ability source field.',
            'Universal abilities are MERGED into every path (universal: true) -- one pool per path,',
            "ticket 03's ruling. `flag` entries are load-bearing: the chooser skips them.",
            "`tier` is the minimum mythic tier (1/3/6) gating the pick, judged per slot.",
        ],
        'paths': paths,
    }
    Path(OUT).write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    total = sum(len(p['abilities']) for p in paths.values())
    print(f'wrote {OUT} ({total} merged ability rows across {len(paths)} paths)')


if __name__ == '__main__':
    main()
