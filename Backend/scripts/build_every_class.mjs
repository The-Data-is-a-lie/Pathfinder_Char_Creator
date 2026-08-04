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
 * THE HARVEST IS NOT A VERBATIM COPY. pf1-psionics ships all twelve of its classes with the same
 * placeholder progression -- bab "low", hd 6, skillsPerLevel 2 -- which is correct for the psion
 * alone, by coincidence (docs/wayfinder/psionics/issues/02-data-quality-ogl.md). pf1 derives BAB
 * from the class item and the generator module supplies none of its own, so harvesting those values
 * as-is makes an aegis 20 attack at +10 instead of +20. Every class item therefore gets those three
 * fields patched from class_data.json on the way through -- the decision taken in
 * docs/wayfinder/psionics/issues/03-division-of-labour.md. system.hp is deliberately NOT patched:
 * it is a leftover rolled value, not the hit die, and modify-abilities.js zeroes it on extra class
 * items anyway.
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
import { pathToFileURL, fileURLToPath } from 'node:url';
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
// The NPC classes come out of the pf1 SYSTEM's own pack, not a module's, so that root is separate.
const systemDir = flag('--system',
  path.join(os.homedir(), 'AppData', 'Local', 'FoundryVTT', 'Data', 'systems', 'pf1'));

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
  {
    // The five Paizo NPC classes, 2026-08-04. First-party, so unlike everything above they come
    // from the SYSTEM pack -- the everyClassPerson actor was built from the class list as it stood
    // and these were simply never dragged onto it. They harvest to a single item each: pf1 gives
    // them no classAssociations, which is correct (only the adept has features, and its spells and
    // familiar are progression rather than granted items).
    pack: path.join(systemDir, 'packs', 'classes'),
    packId: 'pf1.classes',
    classes: ['Adept', 'Aristocrat', 'Commoner', 'Expert', 'Warrior'],
  },
  {
    // The omdura and the vampire hunter, 2026-08-04 -- the last two first-party Paizo base classes
    // the generator lacked. They are NOT in pf1.classes (49 class Items, neither among them); a
    // sweep of every installed pack found them in pf-content's pf-collab-content.
    //
    // `also` is load-bearing here and nowhere else: four of their granted features are @UUIDs into
    // pf1.class-abilities, the generic shared items (Orisons, Detect Alignment, Track, Swift
    // Tracker). Resolving associations against pf-collab-content alone silently drops all four.
    pack: path.join(modulesDir, 'pf-content', 'packs', 'pf-collab-content'),
    also: [path.join(systemDir, 'packs', 'class-abilities')],
    packId: 'pf-content.pf-collab-content',
    classes: ['Omdura', 'Vampire Hunter'],
  },
];

// ---------------------------------------------------------------------------------------------
// The progression patch (see header). class_data.json is this repo's own file, so it is resolved
// from the script's location rather than the cwd -- the script is run from wherever Foundry's
// modules dir happens to be convenient.
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const CLASS_DATA = path.join(REPO_ROOT, 'Backend', 'json', 'class_data.json');

// class_data.json's vocabulary -> pf1's. pf1's middle value is 'med', not 'medium' (checked against
// the 49 already-working classes in the bundle); writing 'medium' silently yields no BAB at all.
const BAB_WORD = { H: 'high', M: 'med', L: 'low' };

const classData = JSON.parse(fs.readFileSync(CLASS_DATA, 'utf8'));

/**
 * The three fields pf1 needs, read out of class_data.json. Throws rather than falling back: an
 * unpatched class is exactly the defect this exists to fix, and it would be invisible in a 3 MB
 * bundle. The hit die is spelled "d10." and the skill points "4" -- string shapes shared with all
 * 51 pre-psionics entries, so they are parsed here rather than normalised at the source.
 */
function patchProgression(className) {
  const entry = classData[className.toLowerCase()];
  if (!entry) throw new Error(`${className}: no entry in ${CLASS_DATA}`);

  const bab = BAB_WORD[entry.bab];
  if (!bab) throw new Error(`${className}: unknown bab ${JSON.stringify(entry.bab)} (want H/M/L)`);

  const hd = /^d(\d+)\.?$/.exec(entry['hit die'] ?? '');
  if (!hd) throw new Error(`${className}: unparseable hit die ${JSON.stringify(entry['hit die'])}`);

  const skills = /^\d+$/.test(entry['skill points at each level'] ?? '');
  if (!skills) {
    throw new Error(`${className}: unparseable skill points `
                  + JSON.stringify(entry['skill points at each level']));
  }

  return { bab, hd: Number(hd[1]), skillsPerLevel: Number(entry['skill points at each level']) };
}

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
const fatal = [];   // collected so one run reports every broken class, not just the first
for (const source of SOURCES) {
  if (!fs.existsSync(source.pack)) {
    console.error(`SKIP: pack not found: ${source.pack}`);
    continue;
  }
  const docs = await readPack(source.pack, { ClassicLevel });
  const byName = new Map([...docs.values()].filter(d => d.type === 'class').map(d => [d.name, d]));

  // Feature lookup may need to span packs (see `also` on the pf-collab-content source). These are
  // merged for ASSOCIATION RESOLUTION only -- byName above is built from source.pack alone, so an
  // extra pack can never contribute a class item of its own.
  for (const extra of source.also ?? []) {
    if (!fs.existsSync(extra)) { console.error(`SKIP extra pack (missing): ${extra}`); continue; }
    for (const [id, doc] of await readPack(extra, { ClassicLevel })) {
      if (!docs.has(id)) docs.set(id, doc);
    }
  }

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

    let progression;
    try {
      progression = patchProgression(className);
    } catch (err) {
      fatal.push(err.message);
      continue;
    }

    const classItem = {
      ...structuredClone(cls),
      _id: stableId(`${source.packId}:${className}`),
      folder: null,
      sort: 0,
      // Harvested class items sit at level 20; createCharacter.js:adjustLevel rewrites it per
      // character. A non-numeric level would fail updateLevel's typeof guard.
      // ...progression overwrites the pack's placeholder bab/hd/skillsPerLevel -- see header.
      system: { ...cls.system, level: 20, ...progression },
      flags: {
        ...(cls.flags ?? {}),
        pf1: { ...((cls.flags ?? {}).pf1 ?? {}), links: { classAssociations: assoc } },
      },
      _stats: { ...(cls._stats ?? {}),
                compendiumSource: `Compendium.${source.packId}.Item.${cls._id}` },
    };

    blocks.push({ name: className, items: [classItem, ...items], progression });
  }
}

if (fatal.length) {
  console.error('cannot patch class progression; aborting without touching the bundles:');
  for (const message of fatal) console.error(`  ${message}`);
  process.exit(1);
}

if (!blocks.length) {
  console.error('nothing harvested; aborting without touching the bundles');
  process.exit(1);
}

console.log('Harvested blocks (bab/hd/skills patched from class_data.json):');
for (const b of blocks) {
  const p = b.progression;
  console.log(`  ${b.name.padEnd(18)} ${`${p.bab}/${p.hd}/${p.skillsPerLevel}`.padEnd(12)}`
            + `${b.items.length} items (1 class + ${b.items.length - 1} features)`);
}

// ---------------------------------------------------------------------------------------------
const names = new Set(blocks.map(b => b.name));
const expected = new Map(blocks.map(b => [b.name, b.progression]));

/**
 * Read a written bundle back off disk and assert every harvested class carries the patched
 * progression. The convention lives here rather than in a Backend/scripts/validate_*.py because the
 * bundles sit outside this repo, under a machine-specific Foundry path no repo validator can rely
 * on. Returns the number of mismatches.
 */
function verifyBundle(file) {
  const written = JSON.parse(fs.readFileSync(file, 'utf8'));
  let bad = 0;
  for (const item of written.items) {
    if (item.type !== 'class' || !expected.has(item.name)) continue;
    const want = expected.get(item.name);
    const got = { bab: item.system?.bab, hd: item.system?.hd,
                  skillsPerLevel: item.system?.skillsPerLevel };
    if (got.bab !== want.bab || got.hd !== want.hd || got.skillsPerLevel !== want.skillsPerLevel) {
      console.error(`  MISMATCH ${item.name}: want ${want.bab}/${want.hd}/${want.skillsPerLevel}, `
                  + `got ${got.bab}/${got.hd}/${got.skillsPerLevel}`);
      bad++;
    }
  }
  return bad;
}

let mismatches = 0;

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
    mismatches += verifyBundle(file);
  }
}

if (mismatches) {
  console.error(`\n${mismatches} class item(s) did not land with the patched progression.`);
  process.exit(1);
}

console.log('\nReminder: every name above must also appear in class_list in modify-abilities.js,');
console.log('or the PRECEDING class absorbs its items instead of stopping at the boundary.');
