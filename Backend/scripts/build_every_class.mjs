/**
 * Merge 3pp classes (psionics, Path of War) from their Foundry compendium packs into the generator
 * module's every_class.json bundles.
 *
 * WHY THIS EXISTS
 * The generator module does not build class items from scratch. modify-abilities.js copies them out
 * of templates/character_sheet_folder/every_class.json -- a snapshot of the "everyClassPerson"
 * actor, produced by dragging every class onto one actor and exporting it (tools/
 * export_every_class.macro.js). A class that was never dragged onto that actor simply is not in the
 * bundle, and a character rolled with it lands on the sheet with no class item at all:
 *
 *     createCharacter.js:130  Class item Aegis not found in actor's items.
 *
 * The twelve psionic classes were never harvested. Neither were Path of War's Stalker and Zealot.
 * This script harvests them from the modules' own compendium packs instead of by hand, so the fix
 * is repeatable and reviewable rather than a GUI ritual.
 *
 * It deliberately does NOT replace the export macro. Reproducing all 49 already-working classes
 * would risk regressing them; this only splices in the classes that are missing.
 *
 * THE TWO LINK STRUCTURES (the easy thing to get wrong)
 * A class carries its features in two different shapes, and they are not interchangeable:
 *   - compendium side: system.links.classAssociations = [{uuid, level}, ...]  (points at pack docs)
 *   - actor side:      flags.pf1.links.classAssociations = {embeddedItemId: level, ...}
 * The bundle is an ACTOR export, so the second is the one that makes features attach. Copying a
 * compendium class in without rewriting that map yields a class whose features are inert.
 *
 * FOUNDRY MAY STAY OPEN. LevelDB is single-writer and a running Foundry holds the lock, so each
 * pack is copied to a temp directory and the copy is opened. Compendium packs are read-only during
 * play, so the copy is consistent.
 *
 * Usage:
 *   node build_every_class.mjs --classic-level <dir> [--dry-run]
 *   node build_every_class.mjs --classic-level <dir> --modules <FoundryData/modules>
 *
 * Verify after running with --dry-run first: it prints the block sizes it would write and touches
 * nothing.
 */
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';
import crypto from 'node:crypto';

const argv = process.argv.slice(2);
const flag = (name, fallback = null) => {
  const i = argv.indexOf(name);
  return i === -1 || !argv[i + 1] ? fallback : argv[i + 1];
};
const classicLevelDir = flag('--classic-level');
const dryRun = argv.includes('--dry-run');
const modulesDir = flag('--modules',
  path.join(os.homedir(), 'AppData', 'Local', 'FoundryVTT', 'Data', 'modules'));

if (!classicLevelDir) {
  console.error('usage: node build_every_class.mjs --classic-level <dir> [--modules <dir>] [--dry-run]');
  process.exit(2);
}

// Which classes come from which module pack. Names must match the compendium's own spelling, which
// is also what the backend sends after capitalizeWords() ("psychic warrior" -> "Psychic Warrior").
const SOURCES = [
  {
    pack: path.join(modulesDir, 'pf1-psionics', 'packs', 'classes'),
    packId: 'pf1-psionics.classes',
    classes: ['Aegis', 'Cryptic', 'Dread', 'Highlord', 'Marksman', 'Psion',
              'Psychic Warrior', 'Soulknife', 'Tactician', 'Vitalist', 'Voyager', 'Wilder'],
  },
  {
    // Stalker and Zealot are a DIFFERENT problem from psionics, despite looking the same from the
    // sheet. Psionics was never harvested; these two are not in upstream pf1-pow at all -- as of
    // this writing that pack ships only Mystic, Warder, Medic, Warlord and Harbinger. Nothing here
    // can conjure them, so they stay in data.pow_classes_pending_foundry and stay out of the
    // dropdown. They are listed anyway so that the day upstream ships them, re-running this script
    // is the entire fix; until then the SKIP line below is the status report.
    pack: path.join(modulesDir, 'pf1-pow', 'packs', 'classes'),
    packId: 'pf1-pow.classes',
    classes: ['Stalker', 'Zealot'],
  },
];

const BUNDLES = [
  'every_class.json',
  // The modded bundle is selected by the `modded` flag in modify-abilities.js (lines 99-113).
  // Updating only one of the two leaves modded characters broken in a path nothing tests by default.
  'every_class_MODS.json',
];
const BUNDLE_DIR = path.join(modulesDir, 'pf1e_random_char_generator', 'templates',
                             'character_sheet_folder');

// ---------------------------------------------------------------------------------------------
// Foundry ids are exactly 16 chars of [A-Za-z0-9]. Deriving them from the source uuid rather than
// randomising keeps re-runs byte-identical, so a rebuild produces an empty diff instead of churning
// 700 ids and hiding the real change.
const ID_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
function stableId(seed) {
  const hash = crypto.createHash('sha256').update(seed).digest();
  let id = '';
  for (let i = 0; i < 16; i++) id += ID_ALPHABET[hash[i] % ID_ALPHABET.length];
  return id;
}

async function readPack(packDir, classicLevel) {
  // Copy out from under a possibly-running Foundry (see header).
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'packcopy-'));
  for (const f of fs.readdirSync(packDir)) {
    if (f === 'LOCK') continue;
    try { fs.copyFileSync(path.join(packDir, f), path.join(tmp, f)); } catch { /* held open; skip */ }
  }
  const { ClassicLevel } = classicLevel;
  const db = new ClassicLevel(tmp, { valueEncoding: 'json' });
  await db.open();
  const docs = new Map();
  for await (const [key, value] of db.iterator()) {
    if (key.startsWith('!items!') && value?._id) docs.set(value._id, value);
  }
  await db.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  return docs;
}

const { ClassicLevel } = await import(pathToFileURL(path.join(classicLevelDir, 'index.js')).href);

// ---------------------------------------------------------------------------------------------
// Build the blocks: one class item followed immediately by its feature items. collectItems() in
// modify-abilities.js slices from a class boundary to the next, so contiguity IS the contract.
const blocks = [];
for (const source of SOURCES) {
  if (!fs.existsSync(source.pack)) {
    console.error(`SKIP: pack not found: ${source.pack}`);
    continue;
  }
  const docs = await readPack(source.pack, { ClassicLevel });
  const byName = new Map([...docs.values()].filter(d => d.type === 'class').map(d => [d.name, d]));

  for (const className of source.classes) {
    const cls = byName.get(className);
    if (!cls) {
      console.error(`SKIP: ${className} not found in ${source.packId}`);
      continue;
    }
    const links = cls.system?.links?.classAssociations ?? [];
    const items = [];
    const assoc = {};   // actor-side map: embedded feature id -> level granted

    for (const link of links) {
      const srcId = String(link.uuid ?? '').split('.').pop();
      const feat = docs.get(srcId);
      if (!feat) {
        console.error(`  WARN ${className}: unresolved association ${link.uuid}`);
        continue;
      }
      const id = stableId(`${source.packId}:${className}:${srcId}`);
      assoc[id] = link.level ?? 1;
      items.push({
        ...structuredClone(feat),
        _id: id,
        folder: null,
        sort: 0,   // assigned in a second pass, once the block order is final
        _stats: { ...(feat._stats ?? {}),
                  compendiumSource: `Compendium.${source.packId}.Item.${srcId}` },
      });
    }

    const classItem = {
      ...structuredClone(cls),
      _id: stableId(`${source.packId}:${className}`),
      folder: null,
      sort: 0,
      // Harvested class items sit at level 20; createCharacter.js:adjustLevel rewrites it per
      // character. A non-numeric level would fail updateLevel's typeof guard.
      system: { ...cls.system, level: 20 },
      flags: {
        ...(cls.flags ?? {}),
        pf1: { ...((cls.flags ?? {}).pf1 ?? {}), links: { classAssociations: assoc } },
      },
      _stats: { ...(cls._stats ?? {}),
                compendiumSource: `Compendium.${source.packId}.Item.${cls._id}` },
    };

    blocks.push({ name: className, items: [classItem, ...items] });
  }
}

if (!blocks.length) {
  console.error('nothing harvested; aborting without touching the bundles');
  process.exit(1);
}

console.log('Harvested blocks:');
for (const b of blocks) console.log(`  ${b.name.padEnd(18)} ${b.items.length} items (1 class + ${b.items.length - 1} features)`);

// ---------------------------------------------------------------------------------------------
const names = new Set(blocks.map(b => b.name));

for (const bundleName of BUNDLES) {
  const file = path.join(BUNDLE_DIR, bundleName);
  if (!fs.existsSync(file)) { console.error(`SKIP bundle (missing): ${file}`); continue; }

  const bundle = JSON.parse(fs.readFileSync(file, 'utf8'));
  const before = bundle.items.length;

  // Idempotency: drop any previously-written block for these classes, using the same
  // class-boundary rule the consumer uses, so a re-run replaces rather than duplicates.
  const kept = [];
  let dropping = false;
  for (const item of bundle.items) {
    if (item.type === 'class') dropping = names.has(item.name);
    if (!dropping) kept.push(item);
  }

  // Appending is safe: the previously-last class used to collect to end-of-array and now stops at
  // our first boundary, which is correct as long as every new name is in modify-abilities.js's
  // class_list -- see the note this script prints at the end.
  const maxSort = Math.max(0, ...kept.map(i => (Number.isSafeInteger(i.sort) ? i.sort : 0)));
  let sort = maxSort + 100000;
  const appended = [];
  for (const b of blocks) {
    for (const item of b.items) { appended.push({ ...item, sort }); sort += 100000; }
  }
  bundle.items = [...kept, ...appended];

  const msg = `${bundleName}: ${before} -> ${bundle.items.length} items `
            + `(removed ${before - kept.length}, added ${appended.length})`;
  if (dryRun) {
    console.log(`DRY RUN ${msg}`);
  } else {
    fs.writeFileSync(file, JSON.stringify(bundle, null, 2), 'utf8');
    console.log(`WROTE   ${msg}`);
  }
}

console.log('\nReminder: every name above must also appear in class_list in modify-abilities.js,');
console.log('or the PRECEDING class absorbs its items instead of stopping at the boundary.');
