"""Validate Backend/json/first_names_regions.json and last_names_regions.json.

These two files are hand-authored -- no scraper, no builder -- so nothing but this script stands
between a bad edit and every generated NPC being called "Stefan rling".

That is not hypothetical. Every non-ASCII Latin character in last_names_regions.json was at some
point deleted, mid-word included: `Lindström` -> `Lindstrm`, `Åkesson` -> `kesson`,
`Örlingsson` -> `rlingsson`, `Longpré` -> `Longpr`. Twelve surnames, all in the two regions that
use them, silently shipping for two years.

Checks (all must pass; exits 1 with a report otherwise):
- Both files parse as UTF-8 JSON and cover the SAME set of regions (name_chooser indexes both by
  character.region, so a region in one file and not the other is a KeyError waiting to happen).
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
import sys

JSON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'json')
FIRST_PATH = os.path.join(JSON_DIR, 'first_names_regions.json')
LAST_PATH = os.path.join(JSON_DIR, 'last_names_regions.json')

GENDERS = ('Male', 'Female')

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

    if errors:
        for e in errors:
            print(e)
        print(f'\nFAILED: {len(errors)} problem(s)')
        sys.exit(1)
    note = f' ({len(warnings)} duplicate warnings)' if warnings else ''
    print(f'OK: {len(first)} regions, {total} names.{note}')


if __name__ == '__main__':
    main()
