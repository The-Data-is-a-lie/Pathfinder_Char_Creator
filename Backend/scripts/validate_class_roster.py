"""Gate the FoundryVTT module's class roster against the backend's own class list.

    C:\\Python310\\python.exe Backend/scripts/validate_class_roster.py
    C:\\Python310\\python.exe Backend/scripts/validate_class_roster.py --module-root <dir>
    C:\\Python310\\python.exe Backend/scripts/validate_class_roster.py --print

WHY. The class roster used to exist three times by hand -- the dropdown in button.js, a dead
byte-identical copy in html_dialog.js, and the collectItems() boundary list in modify-abilities.js
-- with nothing checking they agreed. On 2026-08-03 the six Occult Adventures classes entered the
random pool and reached two of the three; the dropdown was missed, so for a day the only way to
roll an occultist was to ask for a random class. Per CLAUDE.md a hard convention belongs in a
validator, not a comment: this is that validator.

The module now keeps ONE roster, scripts/class-roster.js, and this checks five things about it:

  1. it lists exactly the classes the backend can roll  (the check that would have caught the bug)
  2. every class belongs to exactly one group
  3. CLASS_ITEM_ORDER matches every_class.json's real class order  (collectItems' contract)
  4. every rostered class has a class Item the sheet can resolve
  5. its group tokens are the ones the backend's data.CLASS_GROUPS understands

The module lives outside this repo, under a machine-specific Foundry path, so an absent module is
a SKIP rather than a failure -- validate_all.py runs this with no arguments on any machine.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "Backend"))

from utils import data as _data                              # noqa: E402

CLASS_DATA = ROOT / "Backend/json/class_data.json"
DEFAULT_MODULE_ROOT = (Path(os.environ.get("LOCALAPPDATA", "")) /
                       "FoundryVTT/Data/modules/pf1e_random_char_generator")
ROSTER_JS = "scripts/class-roster.js"
BUNDLE = "templates/character_sheet_folder/every_class.json"

# The lists in data.py that hold a class OUT of the pool. Each is a deliberate lever with its own
# blocker recorded in docs/feature_spec_todo.md; a class in one of them must NOT be in the roster.
HOLDBACK_LISTS = ("occult_classes", "pow_classes_pending_foundry", "psionic_classes_pending",
                  "classes_pending_foundry")


# --------------------------------------------------------------------------------------------- #
# Reading the JS. class-roster.js is deliberately kept to literal string arrays so this stays a
# regex job rather than a parser -- see the note in its header. Comments are stripped first,
# because they contain apostrophes ("the next one's items") that would otherwise read as quotes.
# --------------------------------------------------------------------------------------------- #
def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    out = []
    for line in text.splitlines():
        quote, cut = None, len(line)
        i = 0
        while i < len(line):
            char = line[i]
            if quote:
                if char == "\\":
                    i += 2
                    continue
                if char == quote:
                    quote = None
            elif char in "'\"`":
                quote = char
            elif char == "/" and line[i + 1:i + 2] == "/":
                cut = i
                break
            i += 1
        out.append(line[:cut])
    return "\n".join(out)


def _balanced(text: str, start: int, open_ch: str, close_ch: str) -> str:
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("unbalanced")


def _strings(literal: str) -> list:
    return re.findall(r"'([^']*)'", literal)


def read_roster(module_root: Path) -> tuple:
    """(groups, class_item_order) from class-roster.js. groups = [(token, label, [names])]."""
    text = _strip_comments((module_root / ROSTER_JS).read_text(encoding="utf-8"))

    order_at = text.index("CLASS_ITEM_ORDER")
    order = _strings(_balanced(text, text.index("[", order_at), "[", "]"))

    groups_at = text.index("CLASS_GROUPS")
    body = _balanced(text, text.index("[", groups_at), "[", "]")
    groups = []
    for match in re.finditer(r"token:\s*'([^']+)'", body):
        token = match.group(1)
        label = re.search(r"label:\s*'([^']+)'", body[match.end():]).group(1)
        classes_at = body.index("[", body.index("classes:", match.end()))
        groups.append((token, label, _strings(_balanced(body, classes_at, "[", "]"))))
    return groups, order


def bundle_class_order(module_root: Path) -> list:
    bundle = json.loads((module_root / BUNDLE).read_text(encoding="utf-8"))
    return [item["name"] for item in bundle["items"] if item.get("type") == "class"]


# --------------------------------------------------------------------------------------------- #
def expected_roster() -> tuple:
    """(rollable class names, {name: group token}) straight from the backend."""
    pool = set(json.loads(CLASS_DATA.read_text(encoding="utf-8")))
    for name in HOLDBACK_LISTS:
        pool -= {x.lower() for x in getattr(_data, name, [])}

    rosters = {token: {x.lower() for x in (roster or [])}
               for token, _label, roster in _data.CLASS_GROUPS}
    claimed = {name for names in rosters.values() for name in names}

    group_of = {}
    for token, _label, roster in _data.CLASS_GROUPS:
        names = (pool - claimed) if roster is None else (pool & rosters[token])
        for name in names:
            group_of[name] = token
    return pool, group_of


def check(module_root: Path) -> list:
    pool, group_of = expected_roster()
    groups, order = read_roster(module_root)
    problems = []

    # 5. tokens -- checked first, because a token mismatch makes every group look empty.
    want_tokens = [token for token, _label, _roster in _data.CLASS_GROUPS]
    got_tokens = [token for token, _label, _names in groups]
    if got_tokens != want_tokens:
        problems.append(f"group tokens {got_tokens} != data.CLASS_GROUPS {want_tokens} -- the "
                        f"dropdown's 'random-<token>' entries would fall back to the whole pool")

    # 1. the roster is exactly the rollable pool.
    listed = [name.lower() for _token, _label, names in groups for name in names]
    missing = sorted(pool - set(listed))
    extra = sorted(set(listed) - pool)
    if missing:
        problems.append(f"rollable but NOT in the dropdown (reachable only via Random): {missing}")
    if extra:
        problems.append(f"in the dropdown but not rollable (picking one silently rolls a random "
                        f"class instead): {extra}")

    duplicated = sorted({name for name in listed if listed.count(name) > 1})
    if duplicated:
        problems.append(f"listed in more than one group: {duplicated}")

    # 2. every class in its backend group.
    for token, _label, names in groups:
        for name in names:
            want = group_of.get(name.lower())
            if want is not None and want != token:
                problems.append(f"{name!r} is under {token!r} but the backend puts it in {want!r}")

    # 3 + 4. the bundle. collectItems() slices class boundary -> next boundary, so ORDER is the
    # contract: a name out of place makes the preceding class swallow the next one's items.
    if not (module_root / BUNDLE).exists():
        problems.append(f"{BUNDLE} is missing -- cannot check the collectItems boundaries")
        return problems

    bundle_order = bundle_class_order(module_root)
    if order != bundle_order:
        first = next((i for i, (a, b) in enumerate(zip(order, bundle_order)) if a != b),
                     min(len(order), len(bundle_order)))
        problems.append(f"CLASS_ITEM_ORDER does not match every_class.json (first difference at "
                        f"index {first}: roster has {order[first:first + 1]}, bundle has "
                        f"{bundle_order[first:first + 1]}) -- rebuild with build_every_class.mjs "
                        f"or fix the roster")

    unrenderable = sorted({name for _t, _l, names in groups for name in names}
                          - set(bundle_order))
    if unrenderable:
        problems.append(f"in the dropdown but has no class Item in every_class.json -- the sheet "
                        f"cannot resolve these: {unrenderable}")
    return problems


def print_expected() -> None:
    pool, group_of = expected_roster()
    print(f"{len(pool)} rollable classes, per Backend/json/class_data.json minus the holdbacks\n")
    for token, label, _roster in _data.CLASS_GROUPS:
        names = sorted(name for name, tok in group_of.items() if tok == token)
        print(f"  {{ token: '{token}', label: '{label}',  // {len(names)}")
        print("    classes: [" + ", ".join(f"'{n.title()}'" for n in names) + "] },")
    held = {name: [x.lower() for x in getattr(_data, name, [])] for name in HOLDBACK_LISTS}
    print("\nheld out (must NOT appear in the roster):")
    for name, names in held.items():
        print(f"  {name:<28} {names or '--'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--module-root", default=str(DEFAULT_MODULE_ROOT),
                        help="the installed pf1e_random_char_generator module directory")
    parser.add_argument("--print", action="store_true", dest="show",
                        help="print the roster the backend expects, then exit")
    args = parser.parse_args()

    if args.show:
        print_expected()
        return 0

    module_root = Path(args.module_root)
    if not (module_root / ROSTER_JS).exists():
        print(f"SKIP: no {ROSTER_JS} under {module_root} -- the FoundryVTT module is not installed "
              f"here. Pass --module-root to check it.")
        return 0

    problems = check(module_root)
    if problems:
        print(f"FAIL: {len(problems)} problem(s) between the backend and {ROSTER_JS}")
        for problem in problems:
            print(f"  - {problem}")
        print("\nRun with --print to see the roster the backend expects.")
        return 1

    pool, _group_of = expected_roster()
    groups, order = read_roster(module_root)
    shape = ", ".join(f"{label} {len(names)}" for _token, label, names in groups)
    print(f"OK: {len(pool)} rollable classes -- {shape}; {len(order)} class Items in "
          f"every_class.json, in the order collectItems expects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
