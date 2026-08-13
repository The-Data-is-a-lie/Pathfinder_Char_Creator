"""The baseline: how good are the characters the generator already makes?

    C:/Python310/python.exe Backend/scripts/tests/test_house_invariants.py --score \
        --levels 1,5,10,15,20,25,30,40
    C:/Python310/python.exe Backend/scripts/build/report_power_baseline.py

WHY THIS EXISTS
---------------
The optimal-builder map's charting note says to take the measurements first, and three of the last
four maps were decided by a number rather than by an argument. This is that number. It renders the
profiles `--score` collected into something readable at volume, because ticket 04's exit condition
is Daniel's verdict that the report IS readable at volume -- not that it is correct first time.

It answers three questions:

1. **Where does today's random output sit against PF1e's own CR benchmarks**, per axis, per class,
   per level. The classes at the bottom are a finding.
2. **Does `build_archetype` predict profile shape?** Ticket 01's most promising answer to "how do
   combat-effectiveness and good-at-its-job reconcile" is one fixed set of axes weighted PER
   ARCHETYPE. That rests on an assumption nobody has tested: that characters sharing an archetype
   share a profile shape. Measured here with eta-squared -- the fraction of an axis's variance
   explained by archetype -- while the label is free, because it is already in every payload. If
   the groups do not separate, ticket 01 needs a different answer and we learn it before an
   optimizer is built on top of it.
3. **What could the metric not see?** Printed, never implied.

No scalar. Collapsing the axes needs weights and weights are ticket 01's to set; this reports the
profile and leaves the collapse undone (see power_metric's docstring on the tautology trap).
"""
import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND, JSON_DIR                                             # noqa: E402

DEFAULT_INPUT = BACKEND / 'scripts' / '_power_baseline.json'

# Axes with a CR column, so a ratio means something. The others are reported raw elsewhere.
# dpr_raw is the benchmarked one (all-hits, the table's own semantics); dpr_expected is the
# hit-weighted diagnostic and deliberately has no benchmark -- the gap between them is what
# accuracy costs, and folding it into the ratio would penalise misses twice. burst_raw is the
# nova round against the same damage_high column; dr has no CR column and reports raw.
RATIO_AXES = ('to_hit', 'dpr_raw', 'burst_raw', 'dc', 'ac', 'ac_combat', 'hp', 'fort', 'ref',
              'will')
RAW_AXES = ('dpr_expected', 'burst_expected', 'ac_touch', 'ac_flat', 'cmd', 'caster_tier', 'dr',
            'skill_breadth')

# eta-squared: the share of an axis's variance explained by group membership. Rough reading --
# 0.01 small, 0.06 medium, 0.14 large (Cohen). A grouping that explains under ~0.14 across the
# board is not carrying an objective function.
ETA_STRONG = 0.14
ETA_MEDIUM = 0.06


def families():
    """{archetype name: family} from build_archetypes.json -- the vocabulary already curated."""
    raw = json.loads((JSON_DIR / 'build_archetypes.json').read_text(encoding='utf-8'))
    return {name: spec.get('family') for name, spec in (raw.get('archetypes') or {}).items()}


def ratio(row, axis):
    entry = (row.get('axes') or {}).get(axis) or {}
    return entry.get('ratio')


def raw(row, axis):
    entry = (row.get('axes') or {}).get(axis) or {}
    return entry.get('raw')


def summarise(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    def pct(p):
        return values[min(len(values) - 1, int(p * (len(values) - 1)))]
    return {'n': len(values), 'median': statistics.median(values),
            'p10': pct(0.10), 'p90': pct(0.90)}


def eta_squared(groups):
    """Share of total variance explained by group membership.

    groups: {label: [values]}. Returns None when there is not enough spread to be meaningful --
    an honest None beats a number computed from two data points.
    """
    pooled = [v for values in groups.values() for v in values if v is not None]
    if len(pooled) < 8 or len({tuple(sorted(g)) for g in groups.values()}) < 2:
        return None
    grand = statistics.fmean(pooled)
    total = sum((v - grand) ** 2 for v in pooled)
    if total == 0:
        return None
    between = 0.0
    for values in groups.values():
        clean = [v for v in values if v is not None]
        if len(clean) < 2:
            continue
        between += len(clean) * (statistics.fmean(clean) - grand) ** 2
    return between / total


def table(rows, header, widths=None):
    widths = widths or [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    out = ['| ' + ' | '.join(str(h).ljust(w) for h, w in zip(header, widths)) + ' |',
           '|' + '|'.join('-' * (w + 2) for w in widths) + '|']
    for row in rows:
        out.append('| ' + ' | '.join(str(c).ljust(w) for c, w in zip(row, widths)) + ' |')
    return '\n'.join(out)


def fmt(value, places=2):
    return '--' if value is None else f'{value:.{places}f}'


# --------------------------------------------------------------------------- sections

def section_overview(rows, out):
    out.append('## Where the generator sits against the CR benchmarks\n')
    out.append('`1.00` is exactly on the *Monster Statistics by CR* row for the character\'s CR '
               '(level - 1, PF1e\'s published offset for PC-classed NPCs). Below 1.00 is under '
               'benchmark.\n')
    body = []
    for axis in RATIO_AXES:
        stats = summarise([ratio(r, axis) for r in rows])
        if stats:
            body.append([axis, stats['n'], fmt(stats['median']), fmt(stats['p10']),
                         fmt(stats['p90'])])
    out.append(table(body, ['axis', 'n', 'median', 'p10', 'p90']))
    out.append('')


def section_by_level(rows, out):
    out.append('## By level band\n')
    out.append('A metric that is right at level 5 and wrong at level 40 is worth knowing about '
               'before anything is tuned on it.\n')
    by_level = defaultdict(list)
    for row in rows:
        by_level[row['level']].append(row)
    body = []
    for level in sorted(by_level):
        group = by_level[level]
        cells = [level, len(group)]
        for axis in ('to_hit', 'dpr_raw', 'ac', 'hp', 'fort'):
            stats = summarise([ratio(r, axis) for r in group])
            cells.append(fmt(stats and stats['median']))
        # Cash the generator could not convert into power -- the gear-blackout bug hid behind
        # this column being enormous and unprinted.
        unspent = summarise([(r.get('diagnostics') or {}).get('gold_unspent') for r in group])
        cells.append(f"{int(unspent['median']):,}" if unspent else '--')
        body.append(cells)
    out.append(table(body, ['level', 'n', 'to_hit', 'dpr_raw', 'ac', 'hp', 'fort',
                            'unspent gp (median)']))
    out.append('')


def section_by_class(rows, out):
    out.append('## By class\n')
    out.append('Sorted by median DPR ratio, best first, so **the classes at the bottom are the '
               'finding**. Read them against the blind-spot list: a class whose damage lives in '
               'maneuvers, sphere talents or spells is invisible to the offence axes by design, '
               'not because it is weak.\n')
    out.append('> **Read the DPR column relatively, not absolutely.** The CR table\'s damage row '
               'describes a monster full-attacking with several natural attacks; a PC-classed NPC '
               'swinging one weapon at -5/-10 iteratives cannot reach it, so a low ratio here is '
               'partly the PC-vs-monster offset ticket 03 warned about rather than a weak build. '
               'What is comparable is one class against another on the same column.\n')
    by_class = defaultdict(list)
    for row in rows:
        by_class[row.get('class') or '?'].append(row)
    body = []
    for name, group in by_class.items():
        cells = [name, len(group)]
        # dpr_raw stays at index 2: the sort below rides on this tuple's order.
        for axis in ('dpr_raw', 'to_hit', 'ac', 'hp', 'will'):
            stats = summarise([ratio(r, axis) for r in group])
            cells.append(fmt(stats and stats['median']))
        body.append(cells)
    body.sort(key=lambda r: (r[2] == '--', -float(r[2]) if r[2] != '--' else 0))
    out.append(table(body, ['class', 'n', 'dpr_raw', 'to_hit', 'ac', 'hp', 'will']))
    out.append('')


def section_archetype(rows, out):
    out.append('## Does `build_archetype` predict profile shape?\n')
    out.append('Ticket 01 wants one set of axes weighted per archetype. That only works if '
               'characters sharing an archetype share a profile shape. `eta^2` is the share of '
               'each axis\'s variance explained by the grouping '
               f'(Cohen: 0.01 small, 0.06 medium, {ETA_STRONG} large).\n')
    family_of = families()
    by_arch, by_family = defaultdict(list), defaultdict(list)
    for row in rows:
        name = row.get('build_archetype') or '?'
        by_arch[name].append(row)
        by_family[family_of.get(name) or '?'].append(row)

    body = []
    for axis in RATIO_AXES:
        arch_eta = eta_squared({k: [ratio(r, axis) for r in v] for k, v in by_arch.items()})
        fam_eta = eta_squared({k: [ratio(r, axis) for r in v] for k, v in by_family.items()})
        body.append([axis, fmt(arch_eta, 3), fmt(fam_eta, 3)])
    out.append(table(body, ['axis', 'eta^2 by archetype', 'eta^2 by family']))
    out.append('')

    values = [float(r[1]) for r in body if r[1] != '--']
    strong = [r[0] for r in body if r[1] != '--' and float(r[1]) >= ETA_STRONG]
    median_eta = statistics.median(values) if values else 0.0
    fam_values = [float(r[2]) for r in body if r[2] != '--']
    median_fam = statistics.median(fam_values) if fam_values else 0.0

    if median_eta >= ETA_STRONG:
        verdict = (f'**Verdict: the groups separate.** Median eta^2 by archetype is '
                   f'{median_eta:.3f}, at or above the large-effect threshold, and '
                   f'{len(strong)} of {len(RATIO_AXES)} axes clear it individually. Ticket 01\'s '
                   f'per-archetype weighting has real ground under it and the coefficients could '
                   f'be fitted from this data rather than hand-authored.')
    elif median_eta >= ETA_MEDIUM:
        verdict = (f'**Verdict: partial -- real signal, but not enough to carry the objective '
                   f'function alone.** Median eta^2 by archetype is {median_eta:.3f}: a medium '
                   f'effect, with only {len(strong)} of {len(RATIO_AXES)} axes '
                   f'({", ".join(strong) or "none"}) reaching the large threshold of '
                   f'{ETA_STRONG}. So the archetype label explains roughly '
                   f'{median_eta * 100:.0f}% of the variance in a typical axis and something '
                   f'else explains the rest -- class and level, most likely. Ticket 01 can use '
                   f'per-archetype weights, but it should NOT assume the archetype alone defines '
                   f'what good looks like, and any fitted coefficients need level and class '
                   f'controlled for first.')
    else:
        verdict = (f'**Verdict: the groups do NOT separate.** Median eta^2 by archetype is '
                   f'{median_eta:.3f} -- below even a medium effect, so weighting a fixed axis '
                   f'set per archetype would be weighting noise. Ticket 01 needs a different '
                   f'reconciliation between combat-effectiveness and good-at-its-job.')
    out.append(verdict + '\n')
    out.append(f'Note that the coarser **family** grouping is consistently WEAKER (median eta^2 '
               f'{median_fam:.3f} vs {median_eta:.3f}). Collapsing 33 archetypes into 7 families '
               f'destroys signal rather than concentrating it, so an objective function should '
               f'weight on the archetype, not the family.\n')

    counts = sorted(((len(v), k) for k, v in by_arch.items()), reverse=True)
    out.append('Most common archetypes: '
               + ', '.join(f'{name} ({n})' for n, name in counts[:10]) + '\n')


def section_diagnostics(rows, out):
    out.append('## What the metric could not see\n')
    unknown = sorted({r['diagnostics']['weapon_name'] for r in rows
                      if not r['diagnostics']['weapon_known']})
    shortfall = [r for r in rows if r['diagnostics']['web_sheet_ac_shortfall']]
    extrapolated = [r for r in rows if r.get('cr_extrapolated')]
    out.append(f'- **{len(unknown)}** weapon name(s) did not resolve in `weapons_data.json`, so '
               f'their damage dice scored zero{": " + ", ".join(unknown[:10]) if unknown else ""}')
    out.append(f'- **{len(shortfall)} of {len(rows)}** characters carry an armour or shield '
               f'enhancement bonus that `derive.js` does not fold in, so the standalone web sheet '
               f'renders their AC low. The metric counts it; the sheet does not.')
    out.append(f'- **{len(extrapolated)}** characters scored against an extrapolated CR row '
               f'(past the published CR 30).')
    out.append('')
    blind = rows[0]['blind'] if rows else {}
    for area in ('offense', 'defense', 'utility'):
        items = blind.get(area) or []
        if items:
            out.append(f'**Blind ({area}):** ' + '; '.join(items))
    out.append('')
    out.append('**Assumptions:** '
               + '; '.join(f'{k}={v}' for k, v in (rows[0]['assumptions'] if rows else {}).items()))
    out.append('')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--input', default=str(DEFAULT_INPUT),
                        help=f'profiles written by --score (default {DEFAULT_INPUT})')
    parser.add_argument('--out', default=None, help='write Markdown here instead of stdout')
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"no profiles at {path} -- run the sweep with --score first", file=sys.stderr)
        return 2
    rows = json.loads(path.read_text(encoding='utf-8'))
    if not rows:
        print(f"{path} holds no profiles", file=sys.stderr)
        return 2

    levels = sorted({r['level'] for r in rows})
    classes = sorted({r.get('class') for r in rows})
    out = [f'# Power baseline -- {len(rows)} characters, {len(classes)} classes, levels '
           f'{levels[0]}-{levels[-1]}\n',
           'Today\'s **random** output, scored. No optimizer exists yet; this is the number every '
           'later claim is measured against.\n']
    section_overview(rows, out)
    section_by_level(rows, out)
    section_archetype(rows, out)
    section_by_class(rows, out)
    section_diagnostics(rows, out)

    text = '\n'.join(out)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
        print(f"wrote {args.out} ({len(rows)} profiles)")
    else:
        print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
