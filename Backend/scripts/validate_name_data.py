"""Validate Backend/json/first_names_regions.json and last_names_regions.json.

These two files are hand-authored -- no scraper, no builder -- so nothing but this script stands
between a bad edit and every generated NPC being called "Stefan rling".

That is not hypothetical. Every non-ASCII Latin character in last_names_regions.json was at some
point deleted, mid-word included: `Lindström` -> `Lindstrm`, `Åkesson` -> `kesson`,
`Örlingsson` -> `rlingsson`, `Longpré` -> `Longpr`. Twelve surnames, all in the two regions that
use them, silently shipping for two years.

It also gates REGION REACHABILITY, because the names and the region are one question: a region a
player cannot select is a name pool nobody can draw from. Five of the ten were unreachable for over
a year, in three different ways, and nothing noticed:

- `region_chooser` deleted the last region outright (`regions.remove(region)` running after the loop
  variable), so **Ieso** appeared in 0 of 2,000 random draws and asking for it returned something
  else -- while `campaign_lore.json` carried Ieso lore no character could ever reach.
- It stored a `.title()`d form, which is not a key for **Tal-falko** or **Kaeru no Tochi**, so
  `name_chooser` fell through and drew BOTH names from a random OTHER region (~a fifth of NPCs).
- The Foundry dialog and `sheet.js` send **Grundykin Damplands** and **Dust Cairn**, which match no
  key, and unmatched input silently randomised.

Every one of those is invisible from the data files alone -- a wrong region looks exactly like a
right one -- so this script drives the resolver itself and reads the clients' own option lists.

Checks (all must pass; exits 1 with a report otherwise):
- Both files parse as UTF-8 JSON and cover the SAME set of regions (name_chooser indexes both by
  character.region, so a region in one file and not the other is a KeyError waiting to happen).
- Every region is reachable through `region_chooser`: asked for by key, and by its `.title()`,
  `.upper()` and `.lower()` forms, it comes back as the canonical key; and a sample of no-input
  calls produces all of them (which is what catches a region being dropped from the pool).
- Every option the in-repo clients offer -- `sheet.js`, `index.html`, `data.py::regions` -- resolves
  to a region, and between them they cover all of them. Resolving is enough: `Dust Cairn` is fine
  via slug matching and `Grundykin Damplands` via `data.py::REGION_ALIASES`.
- first_names: every region has both `Male` and `Female`, each a non-empty list.
- last_names: every region maps to a non-empty list.
- Every name is a non-empty string, starts with an uppercase letter, and has no leading/trailing
  whitespace.

Duplicates are REPORTED BUT NOT FATAL. Sojoria's surname list deliberately concatenates a
male-patronymic section, a female-patronymic section and a root-stem section into one flat array, so
shared non-patronymic surnames (Viklund, Fridlund, Lindström) legitimately appear two or three times.
A duplicate only skews selection weighting; treating it as an error would mean 90 false failures and
a validator nobody runs.

WHAT THIS CANNOT CATCH, deliberately stated rather than implied:
the uppercase-initial rule catches a stripped diacritic only when it ate a LEADING capital
(`rling`, `kesson`, `berg` -- 5 of the 12 real cases). It cannot catch `Lindstrm` or `Trnqvist`:
those are still well-formed capitalised words, and no rule short of a dictionary distinguishes them
from a deliberately odd fantasy surname. A guard trusted further than it earns is worse than a
guard with a documented ceiling.

Usage: python Backend/scripts/validate_name_data.py
"""
import json
import os
import random
import re
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(HERE, '..', 'json')
FIRST_PATH = os.path.join(JSON_DIR, 'first_names_regions.json')
LAST_PATH = os.path.join(JSON_DIR, 'last_names_regions.json')

sys.path.insert(0, os.path.join(HERE, '..'))          # Backend/
# One owner each: the resolver decides what a region is, data.py owns the canonical list and the
# client aliases. Restating either here is how the two copies drift apart in the first place.
from utils.util import region_chooser, slug                      # noqa: E402
from utils.data import regions as DATA_REGIONS, REGION_ALIASES   # noqa: E402

GENDERS = ('Male', 'Female')

# Where an in-repo client declares what a user may pick. Each is (label, path, extractor).
SHEET_JS = os.path.join(HERE, '..', 'static', 'scripts', 'sheet.js')
INDEX_HTML = os.path.join(HERE, '..', 'templates', 'index.html')

# Sentinels a client legitimately offers for "surprise me"; they are not region names.
SENTINELS = {'', 'random'}

# How many no-input draws to take. Every region has a ~10% share, so 500 makes a missing one a
# 1-in-10^22 fluke rather than a flaky test.
DRAW_SAMPLE = 500

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def check_name_list(owner, names):
    if not isinstance(names, list) or not names:
        err(f'{owner}: missing or empty name list')
        return
    seen = set()
    for i, name in enumerate(names):
        where = f'{owner}[{i}]'
        if not isinstance(name, str) or not name:
            err(f'{where}: not a non-empty string ({name!r})')
            continue
        if name != name.strip():
            err(f'{where}: leading/trailing whitespace ({name!r})')
        if not name[0].isupper():
            # The detectable half of the diacritic-stripping bug: "Örling" -> "rling".
            err(f'{where}: does not start with an uppercase letter ({name!r})')
        key = name.casefold()
        if key in seen:
            warnings.append(f'{where}: duplicate name ({name!r})')
        seen.add(key)


def read(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def _block(body, pattern, where):
    """The inside of a declaration, or None with an error -- a parse miss must never pass quietly."""
    found = re.search(pattern, body, re.S)
    if not found:
        # A silently skipped check is the exact failure being fixed here.
        err(f'{where}: could not find `{pattern}`; the drift check cannot run')
        return None
    return found.group(1)


def sheet_js_regions():
    """What the web sheet POSTs: its REGIONS labels, mapped through REGION_VALUES."""
    body = read(SHEET_JS)
    listed = _block(body, r'const REGIONS\s*=\s*\[(.*?)\]', 'sheet.js')
    mapped = _block(body, r'const REGION_VALUES\s*=\s*\{(.*?)\}', 'sheet.js')
    if listed is None or mapped is None:
        return []
    labels = re.findall(r"'([^']*)'", listed)
    values = dict(re.findall(r"'([^']*)'\s*:\s*'([^']*)'", mapped))
    if not labels:
        err('sheet.js: REGIONS parsed as empty')
    return [values.get(label, label) for label in labels]


def index_html_regions():
    """The option values of the region <select> on the page served at `/`."""
    body = read(INDEX_HTML)
    block = _block(body, r'<select name="input2">(.*?)</select>', 'index.html')
    if block is None:
        return []
    values = re.findall(r'<option value="([^"]*)"', block)
    if not values:
        err('index.html: the region <select> has no options')
    return values


def check_regions(first):
    """Reachability through the resolver, then what the in-repo clients actually offer."""
    character = SimpleNamespace(first_names_regions=first)
    canonical = list(first)

    for region in canonical:
        for form in (region, region.title(), region.upper(), region.lower()):
            got = region_chooser(character, form)
            if got != region:
                err(f'region_chooser({form!r}) -> {got!r}, expected {region!r}')

    random.seed(0)
    drawn = {region_chooser(character, None) for _ in range(DRAW_SAMPLE)}
    missing = sorted(set(canonical) - drawn)
    if missing:
        err(f'unreachable by random draw over {DRAW_SAMPLE} rolls: {missing} '
            '-- something is excluding regions from the pool')

    if sorted(DATA_REGIONS) != sorted(canonical):
        err(f'data.py::regions disagrees with first_names_regions.json: '
            f'only in data.py {sorted(set(DATA_REGIONS) - set(canonical))}, '
            f'only in the JSON {sorted(set(canonical) - set(DATA_REGIONS))}')

    for target in REGION_ALIASES.values():
        if target not in canonical:
            err(f'REGION_ALIASES points at {target!r}, which is not a region')

    # An unresolvable value still RETURNS a region (the resolver rolls one), so asking
    # region_chooser what it returned cannot distinguish a hit from a miss. Apply the resolution
    # rule itself, using the same slug function and the same alias table the resolver uses.
    by_slug = {slug(name): name for name in canonical}
    for label, offered in (('sheet.js', sheet_js_regions()), ('index.html', index_html_regions())):
        covered = set()
        for value in offered:
            if value.strip().lower() in SENTINELS:
                continue
            key = slug(value)
            resolved = by_slug.get(key) or by_slug.get(slug(REGION_ALIASES.get(key, '')))
            if resolved is None:
                err(f'{label}: offers {value!r}, which no user can actually select '
                    '(send the canonical key, or add a row to data.py::REGION_ALIASES)')
                continue
            covered.add(resolved)
        gap = sorted(set(canonical) - covered)
        if offered and gap:
            err(f'{label}: never offers {gap}')


def main():
    with open(FIRST_PATH, encoding='utf-8') as f:
        first = json.load(f)
    with open(LAST_PATH, encoding='utf-8') as f:
        last = json.load(f)

    only_first = sorted(set(first) - set(last))
    only_last = sorted(set(last) - set(first))
    if only_first:
        err(f'regions in first_names but not last_names: {only_first}')
    if only_last:
        err(f'regions in last_names but not first_names: {only_last}')

    total = 0
    for region, entry in first.items():
        if not isinstance(entry, dict):
            err(f'first_names.{region}: expected an object keyed by gender')
            continue
        unknown = set(entry) - set(GENDERS)
        if unknown:
            err(f'first_names.{region}: unknown gender keys {sorted(unknown)}')
        for gender in GENDERS:
            if gender not in entry:
                err(f'first_names.{region}: missing {gender!r}')
                continue
            check_name_list(f'first_names.{region}.{gender}', entry[gender])
            total += len(entry[gender]) if isinstance(entry[gender], list) else 0

    for region, names in last.items():
        check_name_list(f'last_names.{region}', names)
        total += len(names) if isinstance(names, list) else 0

    check_regions(first)

    if errors:
        for e in errors:
            print(e)
        print(f'\nFAILED: {len(errors)} problem(s)')
        sys.exit(1)
    note = f' ({len(warnings)} duplicate warnings)' if warnings else ''
    print(f'OK: {len(first)} regions, {total} names, all regions reachable.{note}')


if __name__ == '__main__':
    main()
