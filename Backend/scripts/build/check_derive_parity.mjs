// Does power_metric.py agree with the web sheet's derive.js? (map: optimal-builder, ticket 03)
//
//   node Backend/scripts/build/check_derive_parity.mjs \
//        --sheet-root "C:/Users/Daniel/AppData/Local/FoundryVTT/Data/Pathfinder-Character-Sheet"
//
// WHY THIS EXISTS
// ---------------
// The payload holds COMPONENTS, not totals -- no AC, save or attack total exists anywhere in it --
// so the metric has to compute PF1e math, which makes power_metric.py the THIRD implementation of
// that math in this stack (pf1 itself, the web sheet's derive.js, and now this). Ticket 10 predicts
// the consequence in so many words: "If 03 says AC 28 and the sheet says 24, one of them is wrong."
// This turns that from a Foundry-session surprise into a command.
//
// LOCAL ONLY, NOT CI. The web sheet is a separate repo and .github/workflows/validate.yml has no
// setup-node step, so wiring this into CI would mean a cross-repo checkout. Run it before a release
// and after any change to either implementation.
//
// WHAT IT COMPARES, AND WHAT IT DELIBERATELY DOES NOT
// ---------------------------------------------------
// Both sides are fed the SAME change ledger (the payload's always-on dicts), so what is under test
// is the FOLD ARITHMETIC -- the AC formula, the Dex cap, save stacking -- not ledger collection.
// The sheet additionally re-looks-up change data from its own bundled data/*_details.json, which is
// a separate concern and out of scope here.
//
// TWO DIVERGENCES ARE EXPECTED AND ASSERTED RATHER THAN TOLERATED. Both are web-sheet bugs this
// harness found:
//   1. AC: derive.js reads only `data.armor_ac` and never adds `armor_enhancement_bonus` /
//      `shield_enhancement_bonus`, so the sheet renders every enhanced character 1-5 AC low. The
//      metric counts them, and the AC delta must equal exactly that sum.
//   2. Size: derive.js's sizeInfo reads `data.race` / `data.c_race`, but the payload key is
//      `chosen_race`. Neither exists, so the sheet treats EVERY character as Medium and Small races
//      never receive their +1 to AC and attack. The metric matches, so this cancels out here --
//      recorded so nobody "fixes" the metric and breaks parity without fixing the sheet too.
// Any OTHER difference is a real disagreement and fails the run.

import { readFileSync, readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..', '..');
const GOLDEN = join(REPO, 'Backend', 'scripts', 'golden');
const PYTHON = process.env.PYTHON || 'C:/Python310/python.exe';

const args = process.argv.slice(2);
const sheetRootArg = args.indexOf('--sheet-root');
const SHEET_ROOT = sheetRootArg >= 0 ? args[sheetRootArg + 1]
    : 'C:/Users/Daniel/AppData/Local/FoundryVTT/Data/Pathfinder-Character-Sheet';

// The always-on buckets power_metric folds. Kept in step with ALWAYS_ON_CHANGE_KEYS there.
const ALWAYS_ON = ['item_changes_dict', 'feat_changes_dict'];
const WORN_SECTIONS = ['armor', 'shield'];

function ledgerFor(data) {
    const changes = [];
    for (const key of ALWAYS_ON) {
        for (const [source, entry] of Object.entries(data[key] || {})) {
            for (const c of (entry?.changes || [])) changes.push({ ...c, source });
        }
    }
    const enh = data.enhancement_effects_dict || {};
    for (const section of WORN_SECTIONS) {
        for (const [source, entry] of Object.entries(enh[section] || {})) {
            for (const c of (entry?.changes || [])) {
                if ((c.operator || 'add') !== 'add') continue;
                changes.push({ ...c, source });
            }
        }
    }
    return { changes };
}

// Replicates state.js's seedBackendStatBonuses. WITHOUT this the sheet side reads ability scores
// as `data[ab]` alone and understates every save -- not because the sheet is wrong, but because the
// live sheet runs this seeder at adopt time and a bare stub does not. Getting this wrong would have
// reported five phantom "sheet bugs".
function seedBackendStatBonuses(data, st) {
    if (st.statSeeded) return;
    st.statSeeded = true;
    for (const [dict, field] of [[data.inherents, 'inherent'], [data.level_up_stats, 'levelup']]) {
        if (!dict || typeof dict !== 'object') continue;
        for (const ab of ['str', 'dex', 'con', 'int', 'wis', 'cha']) {
            const v = Number(dict[ab]) || 0;
            if (!v) continue;
            st.abilityAdjust ??= {};
            st.abilityAdjust[ab] ??= {};
            if (st.abilityAdjust[ab][field] == null) st.abilityAdjust[ab][field] = v;
        }
    }
}

function makeSandbox() {
    const window = {};
    // sheetState must return `data._sheet` ITSELF, not a detached object: abilityInfo reads
    // `data._sheet.abilityAdjust` directly, so a stub that hands back a copy silently loses the
    // seeded inherent and level-up columns and understates every save.
    window.SheetState = {
        sheetState: (d) => {
            if (!d._sheet) {
                d._sheet = {};
                seedBackendStatBonuses(d, d._sheet);
            }
            return d._sheet;
        },
        disabledBuffSet: () => new Set(),
        removedBuffSet: () => new Set(),
        buffSourceKey: (s, k) => `${s}:${k}`,
        ensureCastingAbility: () => null,
        ensureClassList: (d) => (d.classes || []).map((c) => c.name || c.display),
    };
    window.SheetDetails = {
        collectChanges: (d) => ledgerFor(d),
        changesForTargets: (ledger, targets) =>
            (ledger.changes || []).filter((c) => targets.includes(c.target)),
        evalSimpleFormula: (f) => {
            const text = String(f).trim();
            return /^[+-]?\d+$/.test(text)
                ? { ok: true, value: parseInt(text, 10) }
                : { ok: false, formula: text };
        },
        typeLabel: (t) => t || '',
        // computeDerived also builds an attack line; this harness compares AC and saves only, so
        // the weapon lookups return nothing rather than pulling in the sheet's weapon dataset.
        lookupWeapon: () => null,
        lookupItem: () => null,
        lookupFeat: () => null,
        lookupSpell: () => null,
        lookupClassFeature: () => null,
        lookupTrait: () => null,
        maneuverConditionalsFor: () => ({}),
        stanceBenefitsFor: () => ({}),
        talentConditionalFor: () => null,
    };
    window.SheetData = { SIZES: [], SMALL_RACES: new Set(), CONDITION_CHANGES: {}, COMBAT_TOGGLES: [] };
    window.SheetInventoryModel = null;
    window.SheetClassInfo = null;
    const sandbox = { window, console, Set, Map, Math, Number, String, Array, Object, JSON, Boolean };
    sandbox.globalThis = sandbox;
    return sandbox;
}

function loadDerive() {
    const sandbox = vm.createContext(makeSandbox());
    for (const file of ['ui.js', 'derive.js']) {
        const src = readFileSync(join(SHEET_ROOT, 'scripts', file), 'utf8');
        vm.runInContext(src, sandbox, { filename: file });
    }
    return sandbox.window.SheetDerive;
}

function pythonProfiles(names) {
    const code = `
import json, sys
sys.path.insert(0, r'${join(REPO, 'Backend', 'scripts').replace(/\\/g, '/')}')
from power_metric import profile_for, armor_class, saving_throws
out = {}
for n in ${JSON.stringify(names)}:
    p = json.load(open(r'${GOLDEN.replace(/\\/g, '/')}/' + n + '.json', encoding='utf-8'))
    ac = armor_class(p); sv = saving_throws(p)
    out[n] = {'ac': ac['ac'], 'ac_touch': ac['ac_touch'], 'ac_flat': ac['ac_flat'],
              'fort': sv['fort'], 'ref': sv['ref'], 'will': sv['will'],
              'shortfall': ac['sheet_shortfall']}
print(json.dumps(out))
`;
    const res = spawnSync(PYTHON, ['-c', code], { encoding: 'utf8' });
    if (res.status !== 0) {
        console.error('python side failed:\n' + (res.stderr || res.stdout));
        process.exit(2);
    }
    return JSON.parse(res.stdout.trim().split('\n').pop());
}

// --------------------------------------------------------------------------------------------

const names = readdirSync(GOLDEN).filter((f) => f.endsWith('.json')).map((f) => f.slice(0, -5));
const SD = loadDerive();
const py = pythonProfiles(names);

let failures = 0;
const rows = [];
for (const name of names) {
    const data = JSON.parse(readFileSync(join(GOLDEN, `${name}.json`), 'utf8'));
    const d = SD.computeDerived(data);
    const mine = py[name];
    // derive.js returns flat AC fields for legacy call sites and puts the saves under `blocks`.
    const sheet = {
        ac: d.ac, ac_touch: d.touch, ac_flat: d.flat,
        fort: d.blocks?.fort?.total, ref: d.blocks?.ref?.total, will: d.blocks?.will?.total,
    };
    for (const axis of ['ac', 'ac_touch', 'ac_flat', 'fort', 'ref', 'will']) {
        const delta = (mine[axis] ?? 0) - (sheet[axis] ?? 0);
        // Only normal and flat-footed AC carry the enhancement shortfall. TOUCH AC excludes armour
        // and shield entirely, so it must match exactly -- as must every save.
        const expected = (axis === 'ac' || axis === 'ac_flat') ? mine.shortfall : 0;
        const ok = delta === expected;
        if (!ok) failures++;
        rows.push([name, axis, sheet[axis] ?? '--', mine[axis] ?? '--', delta, expected,
                   ok ? 'ok' : 'MISMATCH']);
    }
}

const widths = [12, 9, 7, 7, 7, 9, 9];
const head = ['golden', 'axis', 'sheet', 'metric', 'delta', 'expected', ''];
console.log(head.map((h, i) => String(h).padEnd(widths[i])).join(''));
for (const r of rows) console.log(r.map((c, i) => String(c).padEnd(widths[i])).join(''));

if (failures) {
    console.log(`\nFAILED -- ${failures} axis/golden pair(s) disagree beyond the known ` +
                `armour-enhancement shortfall.`);
    process.exit(1);
}
console.log(`\nOK -- ${names.length} goldens x 6 axes agree with derive.js ` +
            `(AC differing by exactly the armour/shield enhancement the sheet does not fold in).`);
