"""Scrape the chained summoner's eidolon rules from d20pfsrd into three JSON files.

Spec section 8, "Eidolon (v1.1)"; ticket 07 locked the model, ticket 04 locked this source.
The Foundry packs (`pf-eidolon-forms`, `pf-eidolon-evolutions`) are a completeness cross-check,
never the source -- `pf-eidolon-evolutions` carries only about half the entries.

Outputs (all under Backend/json/):

    eidolon_table.json            the 20-row Eidolon Base Statistics table
    eidolon_base_forms.json       the 6 base forms + the Small package
    eidolon_evolutions.draft.json ~79 evolutions, prose plus auto-extracted hints

The draft is the input to hand curation, not a live data file: the spend loop reads the
curated `eidolon_evolutions.json`. Everything under an evolution's `auto` key is a *hint* the
curator confirms or overrules -- a regex over rules prose cannot be trusted to gate legality,
and an unnoticed misparse silently produces illegal eidolons.

Two findings this scrape settled, both recorded because they contradict what was assumed:

  * **There are six base forms, not seven.** The pack ships an "Aberrant Baseform" that the
    chained eidolon rules do not contain; ticket 04 read the count off the pack. Aberrant is
    left unmapped rather than invented.
  * **Small is a modifier package, not a separate form.** Any base form can be built Small
    (Str -4, Dex +2, Con -2, +1 size AC/attack, -1 CMB/CMD, +2 Fly, +4 Stealth, damage one
    step down), which is what the pack's 7x2 actor list is really showing. Avian and tauric
    are the exception: they arrive Small and pay 2 EP to be Medium.

The base forms' `starting statistics` deliberately mirror `animal_choices.json` (spaced keys,
prose `speed`/`ac`/`attack`, bare-int ability scores) so companion_stats' existing parsing
reads them unchanged.

Idempotent: no timestamps are written, so re-running an unchanged page rewrites byte-identical
files.

Usage (needs the repo .venv -- C:/Python310 has no requests/bs4):
    .venv/Scripts/python.exe Backend/scripts/build/scrape_eidolon.py [--dry-run] [--html PATH]
"""
import argparse
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

SOURCE_URL = 'https://www.d20pfsrd.com/classes/base-classes/summoner/eidolons/'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) PathfinderCharCreator/1.0'}

JSON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'json')

BASE_FORMS = ('aquatic', 'avian', 'biped', 'quadruped', 'serpentine', 'tauric')

# The pack actor each form clones (D2/D3: species is the sole match key, a miss degrades).
PF_CONTENT = {form: f'{form.title()} Baseform' for form in BASE_FORMS}

# Forms that arrive Small and buy Medium, rather than the other way round.
MEDIUM_UPGRADE_COST = {'avian': 2, 'tauric': 2}

FIELD_LABELS = ('Size', 'Speed', 'AC', 'Saves', 'Attacks', 'Attack', 'Ability Scores')
STATS = ('str', 'dex', 'con', 'int', 'wis', 'cha')

TABLE_COLUMNS = ('hd', 'bab', 'good_save', 'poor_save', 'skills', 'feats',
                 'armor_bonus', 'str_dex_bonus', 'evolution_pool', 'max_attacks')

STAT_RE = re.compile(r'\b(Str|Dex|Con|Int|Wis|Cha)\s*([+\-]?\d+)', re.I)
SAVE_RE = re.compile(r'\b(Fort|Ref|Will)\s*\((good|bad|poor)\)', re.I)
TYPE_RE = re.compile(r'\s*\((Ex|Su|Sp|Ex or Su|Su or Ex)\)\s*$', re.I)
SOURCE_RE = re.compile(r'^Source\s*:?\s*([A-Z0-9]+)\s*', re.I)
LEVEL_WORDS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}

# Auto-extraction patterns. Each returns a hint the curator confirms; none is authoritative.
RE_FORM_ONLY = re.compile(
    r'only available to eidolons (?:of|with) the ([a-z]+) base form', re.I)
RE_SUMMONER_LEVEL = re.compile(
    r'summoner must be at least (\d+)(?:st|nd|rd|th) level', re.I)
RE_REPEATABLE = re.compile(r'can be (?:selected|taken) more than once', re.I)
RE_PER_LEVELS = re.compile(
    r'can be taken once for every (\w+) levels the summoner possesses', re.I)
RE_ADDITIONAL_PER = re.compile(
    r'1 additional time for every (\w+) levels the summoner possesses', re.I)
RE_COUNTS_ATTACK = re.compile(
    r'counts as (\w+) natural attacks? toward the eidolon', re.I)
RE_MUST_BE_SIZE = re.compile(r'eidolon must be (Medium|Large|Small) to take', re.I)
RE_MUST_HAVE = re.compile(
    r'eidolon must (?:have|possess) the ([a-z]+(?: \([a-z]+\))?) evolution', re.I)
RE_ATTACK_PROSE = re.compile(
    r'\b(?:this|these) attacks? (?:is|are) (?:a )?(?:primary|secondary) attacks?', re.I)


# UTF-8 bytes decoded as latin-1. A whole-string re-decode is not usable: the page also
# carries genuine non-latin-1 characters, so the round trip raises and silently hands back
# the corruption unrepaired. These are the sequences this page actually produces.
MOJIBAKE = {
    '\u00e2\u0080\u0093': '-',    # en dash -- the minus on every ability penalty
    '\u00e2\u0080\u0094': '--',   # em dash -- the table's empty Special cell
    '\u00e2\u0080\u0099': "'",
    '\u00e2\u0080\u0098': "'",
    '\u00e2\u0080\u009c': '"',
    '\u00e2\u0080\u009d': '"',
    '\u00c2\u00a0': ' ',
}


def fix_mojibake(text):
    """d20pfsrd serves UTF-8 without declaring it, so a naive decode turns every dash into
    latin-1 noise. A dropped minus sign is exactly the class of silent corruption that
    inflated every advanced companion in `animal_choices.json` (spec section 8, "the data
    defect"), so repair it rather than stripping non-ASCII and hoping."""
    if '\u00e2' not in text and '\u00c2' not in text:
        return text
    for bad, good in MOJIBAKE.items():
        text = text.replace(bad, good)
    return text


def flatten(node):
    """d20pfsrd wraps every keyword in a link, so get_text() shatters a stat block into
    fragments. Rejoin into one flat string and normalise the typography."""
    text = node.get_text(' ') if hasattr(node, 'get_text') else str(node)
    text = fix_mojibake(text)
    text = (text.replace('\u00a0', ' ').replace('\u2019', "'")
                .replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
                .replace('\u2212', '-').replace('\u2013', '-').replace('\u2014', '--'))
    return re.sub(r'\s+', ' ', text).strip()


def section_body(heading):
    """Flat text from one heading up to the next heading of any level."""
    parts = []
    for sib in heading.next_siblings:
        if getattr(sib, 'name', None) in ('h1', 'h2', 'h3', 'h4'):
            break
        parts.append(flatten(sib) if getattr(sib, 'name', None) else str(sib).strip())
    return re.sub(r'\s+', ' ', ' '.join(p for p in parts if p)).strip()


def load_soup(html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
    # FAQ boxes are commentary spliced between an evolution's heading and its rules text.
    # `reach` puts one FIRST, so anything that reads text positionally loses the whole entry.
    for tag in soup.select('div.faq'):
        tag.decompose()
    return soup


# ---------------------------------------------------------------- the class table

def parse_table(soup):
    """The one <table> on the page -> {level: {column: value}}.

    The Special column is the class-feature schedule (darkvision, link, share spells,
    evasion, ability score increase, devotion, multiattack, improved evasion); it is kept as
    a list of lowercase names because the eidolon section promotes them into real items the
    way D16 promotes a companion's species abilities.
    """
    tables = soup.find_all('table')
    if len(tables) != 1:
        raise SystemExit(f'expected exactly 1 table on the page, found {len(tables)}')
    rows = tables[0].find_all('tr')
    header = [flatten(c) for c in rows[0].find_all(['td', 'th'])]
    if 'Evolution Pool' not in header or 'Max Attacks' not in header:
        raise SystemExit(f'table header changed: {header}')

    levels = {}
    for row in rows[1:]:
        cells = [flatten(c) for c in row.find_all(['td', 'th'])]
        if len(cells) != len(header):
            raise SystemExit(f'ragged table row: {cells}')
        level = int(re.match(r'(\d+)', cells[0]).group(1))
        entry = {}
        for key, raw in zip(TABLE_COLUMNS, cells[1:11]):
            entry[key] = int(raw.replace('+', '').strip())
        special = cells[11].strip()
        entry['special'] = ([] if special in ('--', '-', '\u2014', '')
                            else [s.strip().lower() for s in special.split(',') if s.strip()])
        levels[str(level)] = entry

    if sorted(int(k) for k in levels) != list(range(1, 21)):
        raise SystemExit(f'expected levels 1-20, got {sorted(int(k) for k in levels)}')
    return levels


# ---------------------------------------------------------------- base forms

def parse_fields(chunk):
    """`Size Medium; Speed 30 ft.; AC +2 natural armor; ...` -> {'size': 'medium', ...}."""
    hits = []
    for label in FIELD_LABELS:
        for m in re.finditer(rf'\b{re.escape(label)}\b\s*:?', chunk):
            hits.append((m.start(), m.end(), label))
    hits.sort()
    # "Attacks" also matches "Attack"; keep the longer label at a shared position.
    deduped = []
    for hit in hits:
        if deduped and hit[0] == deduped[-1][0]:
            if hit[1] > deduped[-1][1]:
                deduped[-1] = hit
            continue
        deduped.append(hit)

    out = {}
    for i, (_, end, label) in enumerate(deduped):
        stop = deduped[i + 1][0] if i + 1 < len(deduped) else len(chunk)
        # Keep a trailing period: `speed` is prose that companion_stats reads for
        # movement-gated skills, and `animal_choices.json` spells it "40 ft.".
        value = re.sub(r'\s+([,;.])', r'\1', chunk[end:stop]).strip(' ;,\t')
        key = 'attack' if label == 'Attacks' else label.lower()
        if value and key not in out:
            out[key] = value
    return out


def parse_free_evolutions(raw):
    """`Claws , limbs (arms), limbs (legs) (2).` -> ({'claws': 1, ...}, [notes])."""
    free, notes = {}, []
    for part in re.split(r',| and (?=can )', raw):
        part = part.strip(' .')
        if not part:
            continue
        if ' can select ' in part or part.startswith('can select'):
            notes.append(part.rstrip('.').strip())
            continue
        count = 1
        m = re.search(r'\s*\((\d+)\)\s*$', part)
        if m:
            count = int(m.group(1))
            part = part[:m.start()]
        name = re.sub(r'\s+', ' ', part).strip().lower()
        if name:
            free[name] = free.get(name, 0) + count
    return free, notes


def parse_base_form(name, body):
    head, _, rest = body.partition('Starting Statistics')
    if not rest:
        raise SystemExit(f'{name}: no Starting Statistics block')
    stats_text, _, free_text = rest.partition('Free Evolutions')

    fields = parse_fields(stats_text)
    entry = {}
    m = SOURCE_RE.search(head.strip())
    if m:
        entry['source'] = m.group(1).upper()

    size_raw = fields.get('size', '')
    # Avian and tauric state their size as a rule, not a value.
    if re.search(r'is Small unless it spends', size_raw, re.I):
        default_size = 'small'
        entry['size_note'] = size_raw.rstrip('.')
    else:
        default_size = size_raw.split(';')[0].strip().lower() or 'medium'

    starting = {'size': default_size}
    for key in ('speed', 'ac', 'attack'):
        if key in fields:
            starting[key] = fields[key].lower()
    scores = {}
    for stat, value in STAT_RE.findall(fields.get('ability scores', '')):
        scores.setdefault(stat.lower(), int(value.lstrip('+')))
    if sorted(scores) != sorted(STATS):
        raise SystemExit(f'{name}: parsed ability scores {scores}')
    starting['ability scores'] = {s: scores[s] for s in STATS}
    entry['starting statistics'] = starting

    saves = {}
    for save, quality in SAVE_RE.findall(fields.get('saves', '')):
        saves[save.lower()] = 'good' if quality.lower() == 'good' else 'poor'
    if sorted(saves) != ['fort', 'ref', 'will']:
        raise SystemExit(f'{name}: parsed saves {saves}')
    entry['saves'] = saves

    free, notes = parse_free_evolutions(free_text)
    if not free:
        raise SystemExit(f'{name}: no free evolutions parsed from {free_text!r}')
    entry['free evolutions'] = free
    if notes:
        entry['notes'] = notes

    entry['default_size'] = default_size
    if name in MEDIUM_UPGRADE_COST:
        entry['medium_upgrade_cost'] = MEDIUM_UPGRADE_COST[name]
    entry['pf_content'] = PF_CONTENT[name]
    entry['pf_content_small'] = f'{PF_CONTENT[name]} (Small)'
    return entry


def parse_small_package(soup):
    """The `Alternatively, any one of these base forms can be used to make a Small eidolon`
    paragraph, as data. These are the ability deltas only -- the AC/attack/CMB/CMD/Stealth
    geometry is companion_stats.SIZE_GEOMETRY's job, keyed off the final size, so that the
    two never both apply (D11's double-count lesson)."""
    text = flatten(soup)
    i = text.find('any one of these base forms can be used to make a Small eidolon')
    if i < 0:
        raise SystemExit('the Small eidolon paragraph is gone -- page structure changed')
    para = text[i:i + 800]
    package = {
        'ability_scores': {'str': -4, 'dex': 2, 'con': -2},
        'damage_steps_down': 1,
        'geometry': 'companion_stats.SIZE_GEOMETRY (do not re-apply here)',
        'rules_text': para[:para.find('If this choice is made')].strip(),
    }
    checks = (('+2 bonus to its Dexterity', 'dex'), ('-4 penalty to its Strength', 'str'),
              ('-2 penalty to its Constitution', 'con'))
    for phrase, stat in checks:
        if phrase not in para:
            raise SystemExit(f'Small package changed: {phrase!r} missing (stat {stat})')
    return package


def parse_base_forms(soup):
    forms = {}
    for h in soup.find_all('h4'):
        name = flatten(h).lower()
        if name not in BASE_FORMS or name in forms:
            continue
        body = section_body(h)
        if 'Starting Statistics' not in body:
            continue
        forms[name] = parse_base_form(name, body)
    missing = [f for f in BASE_FORMS if f not in forms]
    if missing:
        raise SystemExit(f'base forms not found: {missing}')
    return dict(sorted(forms.items()))


# ---------------------------------------------------------------- evolutions

def word_to_int(word):
    word = word.strip().lower()
    if word.isdigit():
        return int(word)
    return LEVEL_WORDS.get(word)


def auto_hints(body):
    """Best-effort structure from rules prose. Every value here is a hint for the curator."""
    hints = {}
    m = RE_FORM_ONLY.search(body)
    if m:
        hints['form_restriction'] = m.group(1).lower()
    m = RE_SUMMONER_LEVEL.search(body)
    if m:
        hints['min_summoner_level'] = int(m.group(1))
    m = RE_MUST_BE_SIZE.search(body)
    if m:
        hints['requires_size'] = m.group(1).lower()
    have = [h.lower() for h in RE_MUST_HAVE.findall(body)]
    if have:
        hints['requires_evolutions'] = sorted(set(have))
    m = RE_COUNTS_ATTACK.search(body)
    if m:
        hints['grants_attack'] = word_to_int(m.group(1)) or 1
    elif RE_ATTACK_PROSE.search(body):
        # Only `rake` spells out "counts as one natural attack toward the maximum"; every
        # other attack-granting evolution just calls the attack primary or secondary. The
        # Max Attacks cap depends on getting this right, so the curator sets the number.
        hints['attack_prose'] = True
    m = RE_PER_LEVELS.search(body)
    if m:
        hints['repeat_cap'] = {'per_summoner_levels': word_to_int(m.group(1))}
    elif RE_REPEATABLE.search(body):
        cap = {'repeatable': True}
        m = RE_ADDITIONAL_PER.search(body)
        if m:
            cap['plus_one_per_summoner_levels'] = word_to_int(m.group(1))
        hints['repeat_cap'] = cap
    if re.search(r'additional evolution points?', body, re.I):
        hints['has_paid_upgrade'] = True
    return hints


def parse_evolutions(soup):
    """The four `N-Point Evolutions` sections -> {key: entry}. Cost comes from the section
    heading; the h4 heading carries the ability type, never the cost."""
    evolutions = {}
    cost = None
    # The tier headings are not DOM parents or siblings of the entries they head, so walk the
    # headings in document order and carry the current tier instead of traversing structure.
    for tag in soup.find_all(['h2', 'h3', 'h4']):
        label = flatten(tag)
        if tag.name == 'h2':
            # "Eidolon Models" follows the evolutions and reuses h4 for pre-built packages,
            # so any new section closes the current tier.
            cost = None
            continue
        if tag.name == 'h3':
            m = re.match(r'(\d+)-Point Evolutions', label, re.I)
            cost = int(m.group(1)) if m else None
            continue
        if cost is not None:
            heading = label
            third_party = heading.startswith('[3PP]')
            heading = heading.replace('[3PP]', '').strip().rstrip('*').strip()
            kind = None
            tm = TYPE_RE.search(heading)
            if tm:
                kind = tm.group(1).lower()
                heading = TYPE_RE.sub('', heading).strip()
            body = section_body(tag)
            source = None
            sm = SOURCE_RE.search(body)
            if sm:
                source = sm.group(1).upper()
                body = SOURCE_RE.sub('', body).strip()

            key = heading.lower()
            if key in evolutions:
                raise SystemExit(f'duplicate evolution heading: {heading}')
            if len(body) < 40:
                # Fail rather than emit a benefit-less evolution: the curator would have no
                # prose to read the legality fields off, and the spender would happily buy it.
                raise SystemExit(f'{heading}: benefit text too short ({len(body)} chars)')
            entry = {'name': heading, 'cost': cost, 'benefit': body}
            if kind:
                entry['type'] = kind
            if source:
                entry['source'] = source
            if third_party:
                entry['third_party'] = True
            entry['auto'] = auto_hints(body)
            evolutions[key] = entry
    if not evolutions:
        raise SystemExit('no evolutions parsed -- page structure changed')
    return dict(sorted(evolutions.items()))


# ---------------------------------------------------------------- output

def write_json(path, payload, dry_run):
    if dry_run:
        print(f'--- {os.path.basename(path)} (dry run) ---')
        print(json.dumps(payload, indent=2, ensure_ascii=False)[:1500])
        return
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
    print(f'  wrote {os.path.relpath(path)}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dry-run', action='store_true', help='print instead of writing')
    ap.add_argument('--html', help='parse a saved copy instead of fetching')
    args = ap.parse_args()

    if args.html:
        print(f'reading {args.html}')
        with open(args.html, encoding='utf-8') as fh:
            html = fh.read()
    else:
        print(f'fetching {SOURCE_URL}')
        resp = requests.get(SOURCE_URL, headers=UA, timeout=60)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'
        html = resp.text

    soup = load_soup(html)

    levels = parse_table(soup)
    forms = parse_base_forms(soup)
    small = parse_small_package(soup)
    evolutions = parse_evolutions(soup)

    histogram = {}
    for entry in evolutions.values():
        histogram[entry['cost']] = histogram.get(entry['cost'], 0) + 1
    third_party = sorted(k for k, v in evolutions.items() if v.get('third_party'))

    print(f'  table: {len(levels)} levels, '
          f"pool {levels['1']['evolution_pool']}..{levels['20']['evolution_pool']}, "
          f"max attacks {levels['1']['max_attacks']}..{levels['20']['max_attacks']}")
    print(f'  base forms: {", ".join(forms)}')
    print(f'  evolutions: {len(evolutions)} '
          f'({", ".join(f"{c} EP x{histogram[c]}" for c in sorted(histogram))})')
    print(f'  third-party (flagged, not filtered here): {", ".join(third_party) or "none"}')

    write_json(os.path.join(JSON_DIR, 'eidolon_table.json'),
               {'meta': {'source': SOURCE_URL,
                         'note': 'Eidolon Base Statistics; columns verified against ticket 07.'},
                'levels': levels}, args.dry_run)
    write_json(os.path.join(JSON_DIR, 'eidolon_base_forms.json'),
               {'meta': {'source': SOURCE_URL,
                         'note': ('Six chained base forms. The pack ships an Aberrant Baseform '
                                  'that these rules do not contain; it is intentionally '
                                  'unmapped. Small is a package applied to any form.')},
                'small_package': small,
                'forms': forms}, args.dry_run)
    write_json(os.path.join(JSON_DIR, 'eidolon_evolutions.draft.json'),
               {'meta': {'source': SOURCE_URL,
                         'note': ('Draft. Curate into eidolon_evolutions.json: confirm every '
                                  '`auto` hint, add costs of paid upgrades, author `changes` '
                                  'for the numeric evolutions. Nothing here is authoritative.')},
                'evolutions': evolutions}, args.dry_run)
    return 0


if __name__ == '__main__':
    sys.exit(main())
