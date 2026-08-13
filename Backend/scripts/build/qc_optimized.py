"""QC cards for optimized characters: one glanceable block each, machine-verdicted.

    C:/Python310/python.exe Backend/scripts/build/qc_optimized.py                 # 1 card/role, L10
    C:/Python310/python.exe Backend/scripts/build/qc_optimized.py --levels 5,15
    C:/Python310/python.exe Backend/scripts/build/qc_optimized.py --role wall --cls fighter --level 20 --seed 42
    C:/Python310/python.exe Backend/scripts/build/qc_optimized.py --flags-only    # print only FLAG cards

WHY THIS EXISTS
---------------
Daniel's QC time is the scarcest resource in the loop (map: optimal-builder, ticket 04: "I need
to check a lot of NPCs"). The gates already assert floors/margins on a fixed sample; this renders
ANY character the same way a reviewer would read a sheet -- stats, weapon, big six, spine, ratios
-- and pre-answers every mechanical question with a checkmark, so the human eyeball only has to
linger on cards stamped FLAG. Exit code 1 when any card flags, so it can sit in a script.

The checks are deliberately the reviewer's own checklist, not the gate's: does the weapon match
the role's policy, are the big six present at level-plausible tiers, did the spine fire, is the
primary stat placed on top, did the purse get spent, does every floored/margined axis clear.
"""
import argparse
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND, JSON_DIR, REPO, read_json                            # noqa: E402

# main_test loads its JSON config by REPO-RELATIVE path ('Backend/json/...'), so running this from
# anywhere but the repo root crashes on the first data file. This is a user-facing convenience
# tool; anchor the process to the repo instead of asking the user to cd first.
import os                                                                          # noqa: E402
os.chdir(REPO)

sys.path.insert(0, str(BACKEND))
import power_metric                                                                # noqa: E402
from utils.class_func import backstory as _bs                                      # noqa: E402
_bs._try_ollama = lambda *a, **k: ''
import main_test                                                                   # noqa: E402

BIG_SIX_HINTS = ('cloak of resistance', 'ring of protection', 'amulet of natural armor',
                 'belt of', 'headband of')


def generate(cls, level, seed, role):
    with redirect_stdout(io.StringIO()):
        return main_test.generate_random_char(
            class_choice=cls, chosen_BAB='random', multi_class='N', userInput_race='random',
            userInput_region='Tal-Falko', alignment_input='random', userInput_gender='random',
            high_level=level, low_level=level, gold_num="", num_dice='4', num_sides='6',
            use_backstory_api='N', spheres_flag='N', seed=seed, optimize=role)


def feat_names(payload):
    names = set()
    for key in ('feats', 'class_feats', 'flavor_feats', 'story_feats', 'trainer_feats'):
        value = payload.get(key)
        entries = value if isinstance(value, (list, tuple)) else (value or {})
        for f in entries:
            names.add(str(f[0] if isinstance(f, (list, tuple)) and f else f).lower())
    return names


def card(role_name, row, cls, level, seed):
    payload = generate(cls, level, seed, role_name)
    prof = power_metric.profile_for(payload)
    axes, diag = prof['axes'], prof['diagnostics']
    flags = []

    stats = {ab: payload.get(ab) for ab in ('str', 'dex', 'con', 'int', 'wis', 'cha')}
    order = sorted(stats, key=lambda ab: -int(stats[ab] or 0))
    stat_line = ' '.join(f"{ab}{stats[ab]}" for ab in ('str', 'dex', 'con', 'int', 'wis', 'cha'))

    weapon = str(payload.get('weapon_name') or '?')
    if not diag['weapon_known']:
        flags.append(f'weapon {weapon!r} unresolved (scores zero dice)')

    gear = [str(x) for x in (payload.get('equipment_list') or [])]
    six = [g for g in gear if any(h in g.lower() for h in BIG_SIX_HINTS)]
    if level >= 8 and len(six) < 3:
        flags.append(f'only {len(six)} big-six item(s) at L{level}')

    held = feat_names(payload)
    spine = [str(f) for f in (row.get('feat_spine') or [])]
    spine_hit = [f for f in spine if f.lower() in held]
    if level >= 7 and not spine_hit:
        flags.append('no spine feat landed by L7+')

    # One line per axis: the strictest bar wins the display (an axis can carry both a floor and
    # a measured margin; printing it twice read as a glitch).
    bars = {}
    for axis, floor in (row.get('floors') or {}).items():
        bars[axis] = (floor, 'floor')
    for axis, margin in (row.get('margins') or {}).items():
        current = bars.get(axis)
        if current is None or margin > current[0]:
            bars[axis] = (margin, 'margin')
    ratio_bits = []
    for axis, (bar, kind) in sorted(bars.items()):
        entry = axes.get(axis) or {}
        value = entry['ratio'] if entry.get('ratio') is not None else entry.get('raw')
        ok = value is not None and value >= bar
        ratio_bits.append(f"{axis} {value}{'.' if ok else '<' + kind.upper() + str(bar)}")
        if not ok:
            flags.append(f'{axis} {value} under {kind} {bar}')

    gold = diag['gold_unspent']
    if level <= 15 and isinstance(gold, int) and gold > 5000:
        flags.append(f'{gold} gp unspent at L{level}')

    verdict = 'FLAG' if flags else 'PASS'
    lines = [
        f"== {verdict} == {role_name}/{cls} L{level} seed {seed} | "
        f"{payload.get('chosen_race')} | {payload.get('build_archetype') or '-'}",
        f"   stats  {stat_line}   (top: {order[0]}, dumps: {order[-2]},{order[-1]})",
        f"   weapon {weapon} +{payload.get('weapon_enhancement_bonus')} | "
        f"armor {payload.get('armor_name')} +{payload.get('armor_enhancement_bonus')} | "
        f"gold left {gold}",
        f"   six    {'; '.join(six) or '--'}",
        f"   spine  {'; '.join(spine_hit) or '--'}  (missing: "
        f"{'; '.join(f for f in spine if f.lower() not in held) or 'none'})",
        f"   axes   {'  '.join(ratio_bits)}",
    ]
    for flag in flags:
        lines.append(f"   !! {flag}")
    return '\n'.join(lines), bool(flags)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--levels', default='10', help='comma-separated levels (default 10)')
    parser.add_argument('--n', type=int, default=1, help='characters per role per level')
    parser.add_argument('--role', default=None, help='one role only')
    parser.add_argument('--cls', default=None, help='one class only (with --role)')
    parser.add_argument('--level', type=int, default=None, help='shorthand for --levels')
    parser.add_argument('--seed', type=int, default=None, help='exact seed (single-card mode)')
    parser.add_argument('--flags-only', action='store_true', help='print only FLAG cards')
    args = parser.parse_args()

    table = read_json(JSON_DIR / 'power_roles.json')
    roles = {k: v for k, v in table['roles'].items() if not k.startswith('_')}
    levels = [args.level] if args.level else [int(x) for x in args.levels.split(',')]

    cells = []
    if args.role:
        row = roles[args.role]
        classes = [args.cls] if args.cls else sorted(
            c for c, r in table['class_roles'].items() if args.role in r)[:1]
        cells = [(args.role, row, c) for c in classes]
    else:
        for name, row in sorted(roles.items()):
            classes = sorted(c for c, r in table['class_roles'].items() if name in r)
            cells.append((name, row, classes[0]))

    flagged = total = 0
    for role_name, row, cls in cells:
        for level in levels:
            for index in range(args.n):
                seed = args.seed if args.seed is not None else 97000 + hash(
                    (role_name, cls)) % 900 + level * 7 + index
                try:
                    text, bad = card(role_name, row, cls, level, seed)
                except Exception as exc:                                # noqa: BLE001
                    text, bad = f"== FLAG == {role_name}/{cls} L{level} seed {seed}: {exc!r}", True
                total += 1
                flagged += bad
                if bad or not args.flags_only:
                    print(text)
                    print()
    print(f"{total} card(s), {flagged} flagged.")
    return 1 if flagged else 0


if __name__ == '__main__':
    sys.exit(main())
