"""Find the class features + feats that could become per-roll weapon CONDITIONALS, and slice them
into curation worklists (manual tool, never part of the generation pipeline).

Only 54 of 1,484 feats and 16 of 1,756 class-choice powers carry a curated `conditionals` block
today, so most characters get no toggle for powers that plainly deserve one. This is the same sweep
Spheres and Path of War already went through (build_talent_conditionals.py --dump-worklist /
build_spell_rider_worklist.py): find the attack-relevant entries, hand each curation agent a small
file instead of the whole dataset, and keep a report of what is still uncovered.

Three families:
  class-features -- the scraped CHOICE pools (rage powers, arcana, hexes, talents, ...).
  feats          -- data/feats.csv.
  core           -- the BASELINE chassis features (Smite Evil, Sneak Attack, Challenge, ...), swept
                    from the module export every_class_feature.json because no scraped pool holds
                    them; choice-pool members are excluded so the two families never overlap.
                    Curated entries land in the `core_features` overrides section.

Two outputs:

  1. WORKLISTS  <out>/<tier>/<pool>-NN.json -- {section, class, tier, dc_formula, dc_confidence,
     powers:[{name, sections, signals, prerequisites, benefit, ...}]}. One file per pool per tier,
     split at --batch-size. This is the authoring input; the six-detail rider format the author
     writes is documented in docs/class_feature_conditional_decision_rules.md.
  2. REPORT     docs/conditional_candidates.md -- one scannable line per candidate with its pool,
     tier, matched signals and a text snippet, plus per-pool coverage.

Tiers (a record carries its raw `signals`, so the cut line can be re-derived if you disagree):
  A -- worth authoring now. Class feature: damage dice, a save, or attack/damage/crit/sneak/CMB
       wording. Feat: the same AND toggle-ish phrasing (a tradeoff penalty, a swift/immediate
       action, once per day) -- an always-on feat bonus belongs in feat_changes.json, not here.
  B -- the later sweep. Class feature: no dice or save, but activated or inflicting a condition.
       Feat: attack-relevant but with no toggle wording.

Usage:
    C:\\Python310\\python.exe Backend/scripts/build_conditional_candidates.py
    C:\\Python310\\python.exe Backend/scripts/build_conditional_candidates.py --family feats --tier A
    C:\\Python310\\python.exe Backend/scripts/build_conditional_candidates.py --no-report --out DIR
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conditional_clauses as cc                                   # noqa: E402  DC formula per pool
from build_class_feature_changes import (                          # noqa: E402  pool walk, verbatim
    CLASS_DATA, SECTIONS, SECTION_CLASS, dig, entry_text, norm_name)

REPO = Path(__file__).resolve().parents[2]
FEATS_CSV = REPO / "data" / "feats.csv"
FEAT_CONDITIONALS = REPO / "Backend" / "json" / "feats" / "feat_conditionals.json"
CLASS_FEATURE_EFFECTS = (REPO / "Backend" / "json" / "class_data" / "effects"
                         / "class_feature_effects.json")
DEFAULT_OUT = REPO / "Backend" / "scripts" / "_conditional_candidates"
DEFAULT_REPORT = REPO / "docs" / "conditional_candidates.md"
# Double-apply guard, best-effort: a feat the compendium already automates would stack its bonus with
# a toggle. Absent install -> every record is stamped "unknown" and the build still runs.
DEFAULT_COMPENDIUM = (Path.home() / "AppData" / "Local" / "FoundryVTT" / "Data" / "modules"
                      / "pf1e_random_char_generator" / "templates" / "character_sheet_folder"
                      / "every_feat.json")
# The core sweep's source + its own double-apply guard (the *_MODS twin is what reaches sheets).
EVERY_CLASS_FEATURE = DEFAULT_COMPENDIUM.with_name("every_class_feature.json")
EVERY_CLASS_FEATURE_MODS = DEFAULT_COMPENDIUM.with_name("every_class_feature_MODS.json")
CLASS_FEATURES_JSON = REPO / "Backend" / "json" / "class_features.json"   # 12 core-class chassis

# --- signals -------------------------------------------------------------------------------------
# Deliberately over-inclusive: a false positive costs a curator one line ("skip: utility"), a false
# negative hides a power nobody will look at again.
SIGNALS = OrderedDict((
    ("dice", re.compile(r'\b\d+d\d+\b', re.I)),
    ("save", re.compile(r'\b(?:fortitude|reflex|will)\s+save', re.I)),
    ("attack", re.compile(
        r'(?:bonus\s+on\s+(?:the\s+)?attack\s+roll|attack\s+rolls?\b|\bdamage\s+rolls?\b|'
        r'\bsneak attack\b|\bbleed\b|critical\s+(?:hit|threat)|precision damage|'
        r'combat maneuver|\bCMB\b)', re.I)),
    ("activated", re.compile(
        r'\b(?:swift action|immediate action|free action|full-round action|'
        r'once per (?:day|round|encounter)|when you hit|on a successful)\b', re.I)),
    ("condition", re.compile(
        r'\b(?:staggered|sickened|dazed|stunned|entangled|shaken|frightened|blinded|fatigued|'
        r'exhausted|nauseated|prone|paralyzed|confused|dazzled|deafened)\b', re.I)),
    # Feat-only: the tradeoff / on-demand phrasing that makes a bonus a TOGGLE rather than a change.
    ("toggle", re.compile(
        r'\b(?:you (?:take|suffer) a|penalty (?:on|to)|as a swift action|immediate action|'
        r'once per (?:day|round)|you (?:can|may) choose to|before (?:you )?make|'
        r'while (?:raging|using))\b', re.I)),
    # A power that just hands out a feat has no conditional of its own -- the FEAT is the candidate.
    # Tagged rather than dropped: some grant a feat *and* carry mechanics of their own.
    ("bonus_feat", re.compile(r'\bbonus feat\b', re.I)),
))
STRONG = ("dice", "save", "attack")
SOFT = ("activated", "condition")
# A DC the power's own text states -- always beats the pool default, so surface it on the record.
DC_SENTENCE_RE = re.compile(r'[^.;]*\bDC\b[^.;]*[.;]?', re.I)


def signals_of(text):
    return [name for name, rx in SIGNALS.items() if rx.search(text or '')]


def stated_dc(text):
    """The power's own DC sentence, trimmed, or None."""
    m = DC_SENTENCE_RE.search(text or '')
    if not m:
        return None
    return re.sub(r'\s+', ' ', m.group(0)).strip()[:300]


def snippet(text, width=120):
    s = re.sub(r'\s+', ' ', str(text or '')).strip()
    return s if len(s) <= width else s[:width - 1].rstrip() + '…'


# --- class features ------------------------------------------------------------------------------
def load_curated_sections():
    """{section: {power_key: True_if_it_has_conditionals}} from the generated effects file."""
    try:
        eff = json.loads(CLASS_FEATURE_EFFECTS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {sec: {k: bool(isinstance(v, dict) and v.get('conditionals'))
                  for k, v in pool.items() if isinstance(v, dict)}
            for sec, pool in eff.items() if isinstance(pool, dict)}


def collect_class_features():
    """[record] deduped across pools + {section: (total, curated)} coverage.

    A power shared by several pools (41 of them across rogue/ninja/slayer) is emitted ONCE, carrying
    every section it belongs to and filed under the first -- which is also the canonical class whose
    level token the curated copies use, with the sibling retarget fixing it at attach time. Authoring
    it once is what keeps the three copies identical.
    """
    curated = load_curated_sections()
    records, by_name, coverage = [], {}, {}
    for section, sources in SECTIONS.items():
        pool = {}
        for filename, path in sources:
            try:
                data = json.loads(Path(CLASS_DATA, filename).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            for node in dig(data, path):
                for name, value in node.items():
                    pool[norm_name(name)] = entry_text(value)
        sec_curated = curated.get(section, {})
        coverage[section] = (len(pool), sum(1 for v in sec_curated.values() if v))
        for key, text in pool.items():
            if sec_curated.get(key):                       # already has a conditional
                continue
            found = signals_of(text)
            tier = 'A' if any(s in found for s in STRONG) else (
                   'B' if any(s in found for s in SOFT) else None)
            if not tier:
                continue
            if key in by_name:                             # same power, another pool
                rec = by_name[key]
                if section not in rec['sections']:
                    rec['sections'].append(section)
                continue
            rec = {
                "name": key,
                "sections": [section],
                "class": SECTION_CLASS.get(section),
                "tier": tier,
                "signals": found,
                "benefit": re.sub(r'\s+', ' ', text).strip(),
            }
            dc = stated_dc(text)
            if dc:
                rec["dc_stated"] = dc
            by_name[key] = rec
            records.append(rec)
    return records, coverage


# --- core (baseline chassis) features ------------------------------------------------------------
# The pf1 compendium disambiguates same-named features with a class-abbreviation suffix; there is no
# machine-readable class on the exported item, so attribution is best-effort, in this order:
# suffix -> chassis list (class_features.json) -> first class named in the prose -> None.
LABEL_CLASS = {
    'ROG': 'rogue', 'NIN': 'ninja', 'SLA': 'slayer', 'CAV': 'cavalier', 'SAM': 'samurai',
    'ORA': 'oracle', 'VIG': 'vigilante', 'ARC': 'arcanist', 'SOR': 'sorcerer', 'WIZ': 'wizard',
    'INV': 'investigator', 'MAG': 'magus', 'SHA': 'shaman', 'BLO': 'bloodrager', 'CLE': 'cleric',
    'SPI': 'spiritualist', 'PSY': 'psychic', 'SWA': 'swashbuckler', 'BAR': 'barbarian',
    'PAL': 'paladin', 'RAN': 'ranger', 'FTR': 'fighter', 'MNK': 'monk', 'DRU': 'druid',
    'BRD': 'bard', 'ALC': 'alchemist', 'WAR': 'warpriest', 'HUN': 'hunter', 'SKA': 'skald',
    'INQ': 'inquisitor', 'GUN': 'gunslinger', 'BRA': 'brawler', 'MES': 'mesmerist',
    'OCC': 'occultist', 'KIN': 'kineticist', 'MED': 'medium', 'SHI': 'shifter', 'WIT': 'witch',
}
CLASS_WORDS = sorted({*LABEL_CLASS.values(), 'monk', 'druid', 'bard'}, key=len, reverse=True)
CLASS_WORD_RE = re.compile(r'\b(' + '|'.join(CLASS_WORDS) + r')\b', re.I)
LABEL_RE = re.compile(r'\(([^)]+)\)\s*$')
TAG_RE = re.compile(r'<[^>]+>')


def strip_html(html):
    return re.sub(r'\s+', ' ', TAG_RE.sub(' ', str(html or ''))).strip()


def pool_power_keys():
    """Every choice-pool power name (curated or not), fully normalized -- the overlap filter."""
    keys = set()
    for sources in SECTIONS.values():
        for filename, path in sources:
            try:
                data = json.loads(Path(CLASS_DATA, filename).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            for node in dig(data, path):
                keys.update(norm_name(n) for n in node)
    return keys


def core_key(name):
    """norm_name minus any trailing '(...)' label -- '(UC)'/'(SLA)' variants match their base pool
    power; the RAW name still keys the record, so labeled variants stay separate candidates."""
    return norm_name(LABEL_RE.sub('', str(name)).strip())


def attribute_class(raw_name, text, chassis_index):
    m = LABEL_RE.search(str(raw_name))
    if m:
        cls = LABEL_CLASS.get(m.group(1).strip().upper())
        if cls:
            return cls, 'label'
    cls = chassis_index.get(core_key(raw_name))
    if cls:
        return cls, 'chassis'
    m = CLASS_WORD_RE.search(text[:300])
    if m:
        return m.group(1).lower(), 'prose'
    return None, None


def load_chassis_index():
    """{feature_key: class} from class_features.json (12 core classes)."""
    try:
        data = json.loads(CLASS_FEATURES_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    index = {}
    for cls, feats in data.items():
        for name in feats:
            index.setdefault(norm_name(name), cls.replace('unchained_', ''))
    return index


def collect_core_features():
    """[record] + (total items, pool members excluded, already curated).

    Sweeps the module export because the baseline features exist nowhere in the scraped class_data
    pools -- they are exactly what SECTIONS does not cover. A curated core feature lives in the
    `core_features` section of class_feature_effects.json, so presence there = already covered.
    """
    try:
        items = json.loads(EVERY_CLASS_FEATURE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"  ! core sweep skipped — export not readable ({EVERY_CLASS_FEATURE})")
        return [], (0, 0, 0)
    mods = load_compendium(EVERY_CLASS_FEATURE_MODS)
    pool_keys = pool_power_keys()
    chassis = load_chassis_index()
    curated = {norm_name(k)
               for k, v in (load_curated_sections().get('core_features') or {}).items() if v}
    records, seen = [], set()
    total = excluded = 0
    for it in items:
        if it.get("type") != "feat" or (it.get("system") or {}).get("subType") != "classFeat":
            continue
        name = str(it.get("name", "")).strip()
        text = strip_html(((it.get("system") or {}).get("description") or {}).get("value"))
        if not name or not text:
            continue
        total += 1
        key = norm_name(name)                              # raw name keys the record
        if key in seen or key in curated:
            continue
        if core_key(name) in pool_keys:                    # a choice power (or its (UC) twin)
            excluded += 1
            continue
        seen.add(key)
        found = signals_of(text)
        tier = 'A' if any(s in found for s in STRONG) else (
               'B' if any(s in found for s in SOFT) else None)
        if not tier:
            continue
        cls, how = attribute_class(name, text, chassis)
        rec = {
            "name": name,
            "tier": tier,
            "signals": found,
            "class": cls,
            "class_source": how,
            "benefit": text,
            "_sheet_automated": ("unknown" if mods is None else mods.get(name.lower())),
        }
        dc = stated_dc(text)
        if dc:
            rec["dc_stated"] = dc
        records.append(rec)
    return records, (total, excluded, len(curated))


# --- feats ---------------------------------------------------------------------------------------
def load_compendium(path):
    """{feat_name_lower: {changes, contextNotes, actions}} or None when the module isn't installed."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    items = raw if isinstance(raw, list) else raw.get("items", [])
    out = {}
    for it in items:
        sysd = it.get("system") or {}
        counts = {k: len(sysd.get(k) or []) for k in ("changes", "contextNotes", "actions")}
        if any(counts.values()):                           # only automated feats are worth flagging
            out[str(it.get("name", "")).strip().lower()] = counts
    return out


def collect_feats(compendium):
    """[record] + (total, curated). Tier A needs toggle wording on top of the attack relevance --
    an always-on feat bonus is feat_changes.json's job and would double-apply as a toggle."""
    try:
        curated = {k.lower() for k in json.loads(FEAT_CONDITIONALS.read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        curated = set()
    with FEATS_CSV.open(encoding="utf-8", errors="replace") as fh:
        rows = list(csv.DictReader(fh, delimiter="|"))
    records, seen = [], set()
    for row in rows:
        name = (row.get("name") or "").strip()
        text = row.get("benefit") or ""
        if not name or name.lower() in curated:
            continue
        # 155 names in the CSV appear twice: the real feat and its MYTHIC variant. The generator
        # never places mythic feats (randomize_mythic is commented out in main_test.py, and
        # feat_buckets.json has no mythic entry), and a mythic row would collide by name with the
        # base feat when the applier matches an actor's feat items -- so drop them outright.
        if (row.get("type") or "").strip().lower() == "mythic":
            continue
        if name.lower() in seen:                           # any remaining same-name row
            continue
        seen.add(name.lower())
        found = signals_of(text)
        if not any(s in found for s in STRONG):
            continue
        tier = 'A' if 'toggle' in found else 'B'
        rec = {
            "name": name,
            "tier": tier,
            "signals": found,
            "type": (row.get("type") or "").strip(),
            "prerequisites": (row.get("prerequisites") or "").strip(),
            "benefit": re.sub(r'\s+', ' ', text).strip(),
            "_compendium_automated": ("unknown" if compendium is None
                                      else compendium.get(name.lower())),
        }
        records.append(rec)
    return records, (len(rows), len(curated))


# --- output --------------------------------------------------------------------------------------
def write_batches(out_dir, tier, pool_name, records, batch_size, extra=None):
    """<out>/<tier>/<pool>-NN.json. Returns the paths written."""
    target = Path(out_dir, tier)
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for i in range(0, len(records), batch_size):
        chunk = records[i:i + batch_size]
        path = target / f"{pool_name}-{i // batch_size + 1:02d}.json"
        payload = {"section": pool_name, "tier": tier, "count": len(chunk)}
        payload.update(extra or {})
        payload["powers"] = chunk
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
                        encoding="utf-8")
        written.append(path)
    return written


def write_report(path, cf_records, cf_coverage, feat_records, feat_totals, out_dir,
                 core_records=(), core_totals=(0, 0, 0)):
    def rows_for(records):
        return "\n".join(
            f"| {r['name']} | {r['tier']} | {', '.join(r['signals'])} | {snippet(r['benefit'])} |"
            for r in sorted(records, key=lambda r: (r['tier'], r['name'])))

    lines = [
        "# Conditional candidates — class features + feats",
        "",
        "GENERATED by `Backend/scripts/build_conditional_candidates.py` — re-run it, don't hand-edit.",
        "",
        "Every row is a power/feat that could plausibly become a per-roll weapon conditional and does",
        "not have one yet. **Tier A** is the sweep to author now; **tier B** is the later pass. The",
        "full benefit text of each row lives in the worklist batches under",
        f"`{Path(out_dir).relative_to(REPO).as_posix()}/<tier>/<pool>-NN.json`; authoring conventions",
        "are in [class_feature_conditional_decision_rules.md](class_feature_conditional_decision_rules.md).",
        "",
        "## Summary",
        "",
        "| family | tier A | tier B | already curated | pool |",
        "|---|---|---|---|---|",
    ]
    cfa = sum(1 for r in cf_records if r['tier'] == 'A')
    cfb = sum(1 for r in cf_records if r['tier'] == 'B')
    cf_total = sum(t for t, _ in cf_coverage.values())
    cf_cur = sum(c for _, c in cf_coverage.values())
    fa = sum(1 for r in feat_records if r['tier'] == 'A')
    fb = sum(1 for r in feat_records if r['tier'] == 'B')
    ca = sum(1 for r in core_records if r['tier'] == 'A')
    cb = sum(1 for r in core_records if r['tier'] == 'B')
    lines += [
        f"| class features | {cfa} | {cfb} | {cf_cur} | {cf_total} in {len(cf_coverage)} pools |",
        f"| core (chassis) | {ca} | {cb} | {core_totals[2]} | {core_totals[0]} classFeat items, "
        f"{core_totals[1]} choice-pool members excluded |",
        f"| feats | {fa} | {fb} | {feat_totals[1]} | {feat_totals[0]} |",
        "",
        "## Class features",
        "",
    ]
    by_section = {}
    for r in cf_records:
        by_section.setdefault(r['sections'][0], []).append(r)
    for section in SECTIONS:
        recs = by_section.get(section, [])
        total, cur = cf_coverage.get(section, (0, 0))
        a = sum(1 for r in recs if r['tier'] == 'A')
        b = sum(1 for r in recs if r['tier'] == 'B')
        dc_formula, dc_conf = cc.class_feature_save_dc(section)
        lines.append(f"### {section}  (candidates {a} A / {b} B · curated {cur} of {total})")
        lines.append("")
        if dc_formula:
            lines.append(f"Save DC (`{dc_conf}`): `{dc_formula}`")
            lines.append("")
        if not recs:
            lines += ["_no candidates_", ""]
            continue
        shared = [r for r in recs if len(r['sections']) > 1]
        if shared:
            lines.append(f"_{len(shared)} of these are shared with "
                         f"{', '.join(sorted({s for r in shared for s in r['sections'][1:]}))} — "
                         "author once, fan out on promote._")
            lines.append("")
        lines += ["| power | tier | signals | text |", "|---|---|---|---|", rows_for(recs), ""]

    lines += ["## Core (chassis) class features", "",
              "Baseline features no choice pool holds — swept from `every_class_feature.json`. The",
              "curated landing zone is the `core_features` overrides section. `class` is best-effort",
              "(name label → chassis list → prose); labeled variants like `Sneak Attack (SLA)` stay",
              "separate rows because their progressions differ — author them separately, the applier",
              "matches the raw name before the label-stripped one.", ""]
    by_class = {}
    for r in core_records:
        by_class.setdefault(r['class'] or '(unattributed)', []).append(r)
    for cls in sorted(by_class):
        recs = by_class[cls]
        a = sum(1 for r in recs if r['tier'] == 'A')
        b = sum(1 for r in recs if r['tier'] == 'B')
        lines += [f"### {cls}  ({a} A / {b} B)", "",
                  "| feature | tier | signals | text |", "|---|---|---|---|", rows_for(recs), ""]
    automated = [r for r in core_records if isinstance(r["_sheet_automated"], dict)]
    if automated:
        lines += ["### Sheet already automates these core features", "",
                  "The `_MODS` twin carries changes/notes/actions for these — a toggle on top of an "
                  "always-on change double-applies. Read both before authoring.", "",
                  "| feature | tier | MODS carries |", "|---|---|---|"]
        lines += [f"| {r['name']} | {r['tier']} | "
                  f"{', '.join(f'{k} {v}' for k, v in r['_sheet_automated'].items() if v)} |"
                  for r in sorted(automated, key=lambda r: r['name'])]
        lines.append("")

    lines += ["## Feats", "", "| feat | tier | signals | text |", "|---|---|---|---|",
              rows_for(feat_records), ""]
    flagged = [r for r in feat_records if isinstance(r["_compendium_automated"], dict)]
    lines += ["### Foundry already automates these", ""]
    if flagged:
        lines.append("A compendium `change` is always-on, so adding a toggle on top double-applies "
                     "the bonus — read both texts before authoring.")
        lines.append("")
        lines += ["| feat | tier | compendium carries |", "|---|---|---|"]
        lines += [f"| {r['name']} | {r['tier']} | "
                  f"{', '.join(f'{k} {v}' for k, v in r['_compendium_automated'].items() if v)} |"
                  for r in sorted(flagged, key=lambda r: r['name'])]
    else:
        lines.append("_none — or the compendium wasn't readable on this machine._")
    lines.append("")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", choices=("class-features", "core", "feats", "all"), default="all")
    ap.add_argument("--tier", choices=("A", "B", "all"), default="all")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="worklist batch directory")
    ap.add_argument("--batch-size", type=int, default=40)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--no-report", action="store_true")
    ap.add_argument("--compendium", type=Path, default=DEFAULT_COMPENDIUM)
    args = ap.parse_args()
    tiers = ("A", "B") if args.tier == "all" else (args.tier,)

    cf_records, cf_coverage = ([], {})
    if args.family in ("class-features", "all"):
        cf_records, cf_coverage = collect_class_features()
    core_records, core_totals = ([], (0, 0, 0))
    if args.family in ("core", "all"):
        core_records, core_totals = collect_core_features()
    feat_records, feat_totals = ([], (0, 0))
    compendium = None
    if args.family in ("feats", "all"):
        compendium = load_compendium(args.compendium)
        if compendium is None:
            print(f"  ! compendium not readable ({args.compendium}) — double-apply guard unknown")
        feat_records, feat_totals = collect_feats(compendium)

    files = 0
    for tier in tiers:
        by_section = {}
        for r in cf_records:
            if r['tier'] == tier:
                by_section.setdefault(r['sections'][0], []).append(r)
        for section, recs in by_section.items():
            dc_formula, dc_conf = cc.class_feature_save_dc(section)
            files += len(write_batches(
                args.out, tier, section, sorted(recs, key=lambda r: r['name']), args.batch_size,
                extra={"class": SECTION_CLASS.get(section),
                       "dc_formula": dc_formula, "dc_confidence": dc_conf}))
        core = sorted((r for r in core_records if r['tier'] == tier),
                      key=lambda r: (r['class'] or '~', r['name']))
        if core:
            files += len(write_batches(args.out, tier, "core", core, args.batch_size,
                                       extra={"overrides_section": "core_features"}))
        feats = sorted((r for r in feat_records if r['tier'] == tier), key=lambda r: r['name'])
        if feats:
            files += len(write_batches(args.out, tier, "feats", feats, args.batch_size))

    for tier in tiers:
        cf_n = sum(1 for r in cf_records if r['tier'] == tier)
        co_n = sum(1 for r in core_records if r['tier'] == tier)
        ft_n = sum(1 for r in feat_records if r['tier'] == tier)
        print(f"  tier {tier}: {cf_n:>4} class features, {co_n:>4} core, {ft_n:>4} feats")
    print(f"  wrote {files} worklist file(s) -> {args.out}")

    if not args.no_report:
        write_report(args.report, cf_records, cf_coverage, feat_records, feat_totals, args.out,
                     core_records, core_totals)
        print(f"  wrote report -> {args.report}")


if __name__ == "__main__":
    main()
