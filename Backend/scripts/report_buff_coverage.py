"""Report which Foundry buff side-maps the golden payloads actually populate (run directly; this
repo has no pytest harness).

    .venv/Scripts/python.exe Backend/scripts/report_buff_coverage.py

Reads the committed goldens in Backend/scripts/golden/ and prints a per-config × per-side-map matrix.
This is the tool that justifies the seeds in test_golden_payload.py: several side-maps are rare
enough that an arbitrary seed misses them entirely (only 17 of 1,586 class_feature_effects entries
carry conditionals), so the configs were swept for coverage rather than chosen at random.

Run it after changing a golden config or seed. A side-map that drops to zero across ALL configs is
no longer regression-covered -- the buff-attach code for it could break silently.

Exits 1 if any side-map has zero coverage across every config.
"""
import json
import sys
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parent / 'golden'

# The export keys built by the buff-attach code (main_test.py, spells.py, spheres.py, path_of_war.py).
SIDE_MAPS = [
    'feat_changes_dict',
    'feat_conditionals_dict',
    'item_changes_dict',
    'enhancement_effects_dict',
    'class_feature_changes_dict',
    'class_feature_conditionals_dict',
    'spell_changes_dict',
    'spell_riders_dict',
    'flaw_effects_dict',
    'combat_talent_items',
    'magic_talent_items',
]


def size(value):
    """Entry count for a side-map, which may be a dict, a list, or absent."""
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, list):
        return len(value)
    return 0


def main():
    goldens = sorted(GOLDEN_DIR.glob('*.json'))
    if not goldens:
        print(f'No goldens in {GOLDEN_DIR}. Run test_golden_payload.py --update first.')
        return 1

    loaded = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in goldens}
    names = sorted(loaded)

    width = max(len(k) for k in SIDE_MAPS) + 2
    print(f'{"side-map":<{width}}' + ''.join(f'{n:>12}' for n in names) + f'{"TOTAL":>9}')
    print('-' * (width + 12 * len(names) + 9))

    uncovered = []
    for key in SIDE_MAPS:
        counts = [size(loaded[n].get(key)) for n in names]
        total = sum(counts)
        cells = ''.join(f'{c:>12}' for c in counts)
        print(f'{key:<{width}}{cells}{total:>9}' + ('   <-- UNCOVERED' if total == 0 else ''))
        if total == 0:
            uncovered.append(key)

    print()
    for name in names:
        p = loaded[name]
        classes = ', '.join(f"{c['name']} {c['level']}" for c in (p.get('classes') or []))
        print(f'  {name:<11} seed={p.get("generation_seed")}  {classes or p.get("c_class")}')

    if uncovered:
        print(f'\nFAIL -- {len(uncovered)} side-map(s) with no coverage in any golden:')
        for key in uncovered:
            print(f'  {key}')
        print('\nAdjust a config/seed in test_golden_payload.py until it is populated, or record why '
              'it is unreachable.')
        return 1

    print(f'\nPASS -- all {len(SIDE_MAPS)} side-maps covered by at least one golden')
    return 0


if __name__ == '__main__':
    sys.exit(main())
