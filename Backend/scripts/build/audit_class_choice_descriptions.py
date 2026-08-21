"""Audit every class-choice pool for entries with missing/trivial description text.

Walks the multi-pick pools shared with build_class_feature_changes (SECTIONS: rage powers,
talents, hexes, discoveries, arcana, revelations, ...) plus the single-pick pools the effects
builder doesn't cover (bloodlines, orders, blessings, inquisitions, spirits), and flags any
entry whose flattened prose (prerequisites/source excluded) is empty or trivial ("see text",
under MIN_LEN chars). These render as name-only class-feature items on the Foundry sheet.

Level-keyed pools (ki powers, mercies, cruelties) are checked at bucket granularity — their
sub-entries are intentionally terse spell/condition stubs.

Also catches the scraper field-glue bug where an entry's benefit prose was appended into its
"prerequisites" string (long prereq, no benefit key) — fix by splitting the fields.

Usage: python Backend/scripts/audit_class_choice_descriptions.py
Exits 1 with a per-class report if anything is flagged; 0 (clean) otherwise.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import SCRIPTS   # noqa: E402
HERE = str(SCRIPTS)
import build_class_feature_changes as bcfc  # noqa: E402  (SECTIONS, dig, CLASS_DATA)

POOLS = dict(bcfc.SECTIONS)
POOLS.update({
    'sorcerer_bloodlines': [('sorcerer.json', ['bloodline'])],
    'bloodrager_bloodlines': [('bloodrager.json', ['bloodline'])],
    'cavalier_orders': [('cavalier.json', ['orders'])],
    'samurai_orders': [('samurai.json', ['orders'])],
    'blessings': [('warpriest.json', ['blessing'])],
    'inquisitions': [('inquisitor.json', ['inquisitions'])],
    'spirits': [('shaman.json', ['spirits'])],
})

META_KEYS = {'prerequisites', 'prerequisite', 'source'}
TRIVIAL = re.compile(r'^\s*(see (text|description)\.?)?\s*$', re.I)
MIN_LEN = 15
# a prereq string this long almost certainly swallowed the benefit prose (field-glue bug)
GLUED_PREREQ_LEN = 120


def deep_text(value):
    """Every descriptive string in an entry, recursively, excluding prereq/source fields."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ' '.join(deep_text(v) for v in value)
    if isinstance(value, dict):
        return ' '.join(deep_text(v) for k, v in value.items()
                        if str(k).lower() not in META_KEYS)
    return ''


def main():
    problems = {}  # (section, filename) -> [(entry, reason)]

    def flag(section, fname, entry, reason):
        problems.setdefault((section, fname), []).append((entry, reason))

    for section, sources in sorted(POOLS.items()):
        for fname, path in sources:
            fpath = os.path.join(bcfc.CLASS_DATA, fname)
            if not os.path.exists(fpath):
                flag(section, fname, '<file>', 'file not found')
                continue
            with open(fpath, encoding='utf-8') as fh:
                data = json.load(fh)
            pools = list(bcfc.dig(data, path))
            if not pools:
                flag(section, fname, '<pool>', 'pool path not found: %s' % '/'.join(path))
                continue
            for pool in pools:
                for name, value in pool.items():
                    text = re.sub(r'\s+', ' ', deep_text(value)).strip()
                    if TRIVIAL.match(text) or len(text) < MIN_LEN:
                        prereq = value.get('prerequisites', value.get('prerequisite', '')) \
                            if isinstance(value, dict) else ''
                        if isinstance(prereq, str) and len(prereq) > GLUED_PREREQ_LEN:
                            flag(section, fname, name,
                                 'benefit prose glued into "prerequisites" — split the fields')
                        else:
                            flag(section, fname, name, 'empty/trivial text: %r' % text[:40])

    total = sum(len(v) for v in problems.values())
    for (section, fname), entries in sorted(problems.items()):
        print('%s (%s):' % (section, fname))
        for entry, reason in entries:
            print('  - %r: %s' % (entry, reason))
    checked = sum(len(srcs) for srcs in POOLS.values())
    print('\n%d pool source(s) checked across %d sections: %s'
          % (checked, len(POOLS), ('%d problem entr%s' % (total, 'y' if total == 1 else 'ies'))
             if total else 'all clean'))
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
