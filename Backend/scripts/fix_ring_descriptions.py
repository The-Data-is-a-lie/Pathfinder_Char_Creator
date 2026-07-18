"""Repair the rings slot in Backend/json/items_best.json.

The ring scrape glued each item's description onto the end of its weight
field as '<weight> Description <text> Construction' and named the last key
'requirements' instead of 'construction requirements'. This splits the
weight field back apart, inserts a real 'description' key after 'weight',
and renames the key — editing only the affected lines so the rest of the
file's formatting is untouched.

Run:  python Backend/scripts/fix_ring_descriptions.py
"""
import json
import os
import re

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'json', 'items_best.json')

WEIGHT_RE = re.compile(r'^(\s*)"weight": (".*")(,?)(\s*)$')
REQ_RE = re.compile(r'^(\s*)"requirements":')


def split_weight(value):
    """'1 lb. Description <text> Construction' -> ('1 lb.', '<text>') or None."""
    idx = value.find('Description')
    if idx == -1:
        return None
    weight = value[:idx].strip()
    desc = value[idx + len('Description'):]
    cidx = desc.rfind('Construction')
    if cidx != -1:
        desc = desc[:cidx]
    return weight, desc.strip()


def main():
    with open(PATH, encoding='utf-8') as f:
        original = f.read()
    lines = original.splitlines(keepends=True)

    out, fixed, renamed, skipped = [], 0, 0, []
    in_rings = False
    for line in lines:
        if re.match(r'^\s*"rings": \{\s*$', line):
            in_rings = True
        if not in_rings:
            out.append(line)
            continue
        m = WEIGHT_RE.match(line)
        if m and 'Description' in m.group(2):
            indent, raw, comma, eol = m.groups()
            parts = split_weight(json.loads(raw))
            if parts is None:
                skipped.append(line.strip())
                out.append(line)
                continue
            weight, desc = parts
            out.append(f'{indent}"weight": {json.dumps(weight)},{eol}')
            out.append(f'{indent}"description": {json.dumps(desc)}{comma}{eol}')
            fixed += 1
            continue
        m = REQ_RE.match(line)
        if m:
            out.append(REQ_RE.sub(rf'{m.group(1)}"construction requirements":', line, count=1))
            renamed += 1
            continue
        out.append(line)

    new_text = ''.join(out)
    data = json.loads(new_text)  # must still be valid JSON
    rings = data['rings']
    with_desc = sum(1 for v in rings.values() if v.get('description', '').strip())
    print(f'{fixed} weight fields split, {renamed} requirements keys renamed, '
          f'{with_desc}/{len(rings)} rings now have descriptions')
    if skipped:
        print('needs manual handling (no Description marker):')
        for s in skipped:
            print(' ?', s[:160])

    with open(PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(new_text)
    print(f'wrote {PATH}')


if __name__ == '__main__':
    main()
