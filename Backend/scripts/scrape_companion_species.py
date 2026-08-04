"""Scrape missing companion species from d20pfsrd into Backend/json/animal_choices.json.

Map #18, ticket #41. The ticket listed nine species as missing; five of them were already
present under the file's own "noun, modifier" spelling (`bat, dire`, `weasel, giant`) or
without the "giant" qualifier the archetype pools use (`seahorse`, `tortoise`, `axe beak`).
Those five are handled by companion_species_aliases.json, not by this script.

What this script adds:

    deer, reindeer      -> normal          plain animal
    griffon             -> magical_beast   archetype-only (Beast Rider, Sable Company Marine)
    hippogriff          -> magical_beast   archetype-only

`magical_beast` is a fourth top-level tier. `animal_companions.py::animal_chooser` reads only
`normal` / `plant` / `vermin`, so a magical beast can never come up on the random druid roll --
which is its RAW availability: reachable only through a curated archetype species pool.

NOT added: **giant eagle**. Ticket #41 lists it, but PF1e has no animal-companion stat block for
one -- it is a Bestiary magical beast, and the Beast Rider archetype that would grant it forbids
mounts with a fly speed. Authoring a stat block would be inventing rules. See the ticket comment.

Output conventions match the repaired file (see repair_animal_choices.py):
  - keys and values lowercased, spaced key spellings
  - `starting statistics` ability scores are bare ints (absolute)
  - `<N>th-level advancement` ability scores are signed strings (deltas)

Idempotent: re-running rewrites the same entries in place.

Usage (needs the repo .venv -- C:/Python310 has no requests/bs4):
    .venv/Scripts/python.exe Backend/scripts/scrape_companion_species.py [--dry-run]
"""
import argparse
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

SOURCE_URL = 'https://www.d20pfsrd.com/classes/core-classes/druid/animal-companions/'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) PathfinderCharCreator/1.0'}

JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '..', 'json', 'animal_choices.json')

# (enclosing section heading, species heading) -> (key in animal_choices.json, tier)
#
# The section is part of the key because d20pfsrd carries TWO griffon and TWO hippogriff
# companion entries with different stat blocks:
#   "Magical Beast Companions"        -- Source LG:LH, third-party, gated behind a
#                                        Beast-Speaker feat this generator does not model.
#   "Other Magical Beast Companions"  -- no third-party marker; Large, with the
#                                        "unable to carry a rider while flying" / mastery rules.
# We take the second. Selecting by section rather than by name keeps that a stated decision
# instead of whichever copy the parser happened to reach last.
WANTED = {
    ('Animal Companion Descriptions', 'Deer, Reindeer'): ('deer, reindeer', 'normal'),
    ('Other Magical Beast Companions', 'Griffon'): ('griffon', 'magical_beast'),
    ('Other Magical Beast Companions', 'Hippogriff'): ('hippogriff', 'magical_beast'),
}

FIELD_LABELS = ('Size', 'Speed', 'AC', 'Attack', 'Ability Scores',
                'Special Qualities', 'Special Attacks', 'Special Ability', 'Bonus Feat')

STATS = ('str', 'dex', 'con', 'int', 'wis', 'cha')

ADV_HEADING = re.compile(r'(\d+)(?:st|nd|rd|th)[-\s]Level Advancement', re.I)
STAT_RE = re.compile(r'\b(Str|Dex|Con|Int|Wis|Cha)\s*([+\-\u2212]?\d+)', re.I)


def flatten(node_or_html):
    """d20pfsrd wraps every keyword in a link, so get_text() shatters a stat block across
    dozens of fragments. Rejoin into one flat string and normalise whitespace."""
    if isinstance(node_or_html, str):
        node_or_html = BeautifulSoup(node_or_html, 'html.parser')
    text = node_or_html.get_text(' ')
    text = text.replace('\u00a0', ' ').replace('\u2019', "'").replace('\u2212', '-')
    return re.sub(r'\s+', ' ', text).strip()


def species_sections(html):
    """{(enclosing section, species name): flat text of that species' entry}.

    Every species on the page is an <h4>, and that is the only reliable boundary: bounding by a
    fixed character window silently swallows the *next* species' advancement blocks, which is
    how reindeer first acquired a deinotherium's trample attack. Each heading appears twice
    (contents list, then body); the body copy is the one followed by "Starting Statistics".
    """
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()

    sections = {}
    for h in soup.find_all('h4'):
        name = flatten(h)
        parts = []
        for sib in h.next_siblings:
            if getattr(sib, 'name', None) in ('h1', 'h2', 'h3', 'h4'):
                break
            parts.append(flatten(sib) if getattr(sib, 'name', None) else str(sib).strip())
        body = re.sub(r'\s+', ' ', ' '.join(p for p in parts if p)).strip()
        if 'Starting Statistics' not in body:
            continue
        parent = h.find_previous(['h2', 'h3'])
        # Section headings on this page carry trailing mojibake, so match on ASCII only.
        section = re.sub(r'[^\x20-\x7e]+', '', flatten(parent)).strip() if parent else ''
        sections[(section, name)] = body
    return sections


def parse_fields(chunk):
    """`Size Medium; Speed 50 ft.; AC +2 natural armor; ...` -> {'size': 'medium', ...}."""
    out = {}
    # Locate each known label and take everything up to the next label as its value.
    hits = []
    for label in FIELD_LABELS:
        for m in re.finditer(rf'\b{re.escape(label)}\b', chunk):
            hits.append((m.start(), m.end(), label))
    hits.sort()
    for i, (start, end, label) in enumerate(hits):
        stop = hits[i + 1][0] if i + 1 < len(hits) else len(chunk)
        value = chunk[end:stop].strip(' ;,\t')
        # Keywords are wrapped in links, so get_text leaves a space before punctuation.
        value = re.sub(r'\s+([,;.])', r'\1', value).strip(' ;,')
        if not value:
            continue
        key = label.lower()
        if key in out:            # first spelling wins; the page repeats labels in prose
            continue
        out[key] = value
    return out


def parse_abilities(raw, absolute):
    """`Str 13, Dex 14` -> bare ints; `Str +2, Dex -2` -> signed strings."""
    scores = {}
    for stat, value in STAT_RE.findall(raw):
        stat = stat.lower()
        if stat in scores:
            continue
        if absolute:
            scores[stat] = int(value.lstrip('+'))
        else:
            n = int(value)
            scores[stat] = f'+{n}' if n > 0 else str(n)
    return scores


def build_block(chunk, absolute):
    fields = parse_fields(chunk)
    block = {}
    for key in ('size', 'speed', 'ac', 'attack'):
        if key in fields:
            block[key] = fields[key].lower()
    if 'ability scores' in fields:
        scores = parse_abilities(fields['ability scores'], absolute)
        if scores:
            block['ability scores'] = scores
    for key in ('special attacks', 'special qualities', 'bonus feat'):
        if key in fields:
            block[key] = fields[key].lower()
    return block


def extract(section):
    """Pull one species' Starting Statistics + advancement blocks out of its section text."""
    head, _, body = section.partition('Starting Statistics')
    if not body:
        return None

    entry = {}
    source = re.search(r'Source\s*:?\s*([A-Za-z0-9:\s\-]{2,20}?)(?:Prerequisite|$)', head)
    if source and source.group(1).strip():
        entry['source'] = source.group(1).strip().lower()

    adv = list(ADV_HEADING.finditer(body))
    end_of_start = adv[0].start() if adv else len(body)
    entry['starting statistics'] = build_block(body[:end_of_start], absolute=True)

    for i, a in enumerate(adv):
        stop = adv[i + 1].start() if i + 1 < len(adv) else len(body)
        level = int(a.group(1))
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(level, 'th')
        entry[f'{level}{suffix}-level advancement'] = build_block(
            body[a.end():stop], absolute=False)
    return entry


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dry-run', action='store_true',
                    help='print the parsed entries without writing')
    args = ap.parse_args()

    print(f'fetching {SOURCE_URL}')
    resp = requests.get(SOURCE_URL, headers=UA, timeout=60)
    resp.raise_for_status()
    sections = species_sections(resp.text)
    print(f'  {len(sections)} species sections on the page')

    parsed = {}
    for (section_name, heading), (key, tier) in WANTED.items():
        section = sections.get((section_name, heading))
        entry = extract(section) if section else None
        if entry is None or not entry.get('starting statistics', {}).get('ability scores'):
            print(f'  FAILED to parse {heading!r} under {section_name!r} '
                  f'-- page structure may have changed')
            return 1
        parsed[key] = (tier, entry)
        blocks = [k for k in entry if k.endswith('advancement')]
        print(f'  parsed {heading!r} ({section_name}) -> {tier}/{key!r}, '
              f'{len(blocks)} advancement block(s)')

    if args.dry_run:
        print()
        for key, (tier, entry) in parsed.items():
            print(f'--- {tier}/{key} ---')
            print(json.dumps(entry, indent=2, ensure_ascii=False))
        return 0

    with open(JSON_PATH, encoding='utf-8') as fh:
        data = json.load(fh)

    for key, (tier, entry) in parsed.items():
        data.setdefault(tier, {})
        data[tier][key] = entry
        data[tier] = dict(sorted(data[tier].items()))

    with open(JSON_PATH, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write('\n')

    print(f'\nwrote {JSON_PATH}')
    print('tiers: ' + ', '.join(f'{t}={len(v)}' for t, v in data.items()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
