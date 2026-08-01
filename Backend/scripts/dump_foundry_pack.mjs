/**
 * Dump the item names out of Foundry LevelDB compendium packs, as JSON on stdout.
 *
 * Used by reconcile_psionics_names.py: the pf1-psionics module attaches items to a generated actor
 * by NAME MATCH and silently drops anything it does not recognise, so every name the generator
 * emits has to be diffed against the module's own packs before it ships.
 *
 * Usage (paths are pack directories, not the module root):
 *   node dump_foundry_pack.mjs --classic-level <dir> [--full] <pack> [<pack> ...]
 *
 * --full emits each entry's WHOLE document instead of the {key, name, type} summary. Name
 * reconciliation only ever needed the summary, but build_every_class.mjs has to carry real Item
 * documents across into every_class.json, and re-reading the pack a second way would be a second
 * place for the key/sublevel handling to drift. Default stays the summary so the existing caller
 * (reconcile_psionics_names.py) is untouched.
 *
 * --classic-level takes the directory of an installed `classic-level` package. It is a parameter
 * rather than a bare import because this repo is Python and has no node_modules of its own; the
 * caller finds a copy (npx cache, or any node project that has one) and passes it in.
 *
 * Read-only: opens each pack, iterates, closes. Foundry must not be running -- LevelDB is
 * single-writer and an open Foundry holds the lock.
 */
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const argv = process.argv.slice(2);
const flagAt = argv.indexOf('--classic-level');
if (flagAt === -1 || !argv[flagAt + 1]) {
  console.error('usage: node dump_foundry_pack.mjs --classic-level <dir> <pack> [<pack> ...]');
  process.exit(2);
}
const classicLevelDir = argv[flagAt + 1];
const full = argv.includes('--full');
const packs = argv.filter((arg, i) =>
  i !== flagAt && i !== flagAt + 1 && arg !== '--full');
if (packs.length === 0) {
  console.error('no packs given');
  process.exit(2);
}

const entry = pathToFileURL(path.join(classicLevelDir, 'index.js')).href;
const { ClassicLevel } = await import(entry);

const out = {};
for (const pack of packs) {
  const db = new ClassicLevel(pack, { valueEncoding: 'json' });
  await db.open();
  const items = [];
  for await (const [key, value] of db.iterator()) {
    // Keys are sublevel-prefixed: !items!<id> for documents, !folders!<id> for folders. Folders
    // are carried through with their prefix intact so the caller can exclude them -- the powers
    // pack opens with the seven disciplines as folders, which are not powers.
    items.push(full ? { key, doc: value }
                    : { key, name: value?.name ?? '', type: value?.type ?? '' });
  }
  await db.close();
  out[path.basename(pack)] = items;
}
process.stdout.write(JSON.stringify(out));
