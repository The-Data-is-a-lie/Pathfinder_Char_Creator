# 01 — Where does the psionics data actually come from, and what is in it?

Type: task
Status: resolved
Blocked by: —
Map: [Psionics](../map.md)

## Question

Everything else on this map waits on knowing the real shape of the data we agreed to mirror.

**Re-aimed 2026-07-31.** This ticket originally asked for an inventory of `pf1-psionics`'
`packs-source/` YAML. [Ticket 02](02-data-quality-ogl.md) then found the module's class stat blocks
are unusable placeholders and that powers-known per level exists nowhere in it, and the user
redirected the source to the **Library of Metzofitz wiki** — the campaign's own authority, already
this repo's source for `data/Metzofitz_Feats.csv`. The module remains the Foundry render target.

Do the work:

1. Establish how the wiki can actually be read programmatically.
2. Inventory what it publishes for the twelve in-scope classes: the structural fields
   (`bab`, hit die, skill points, saves) the module got wrong, and the progressions it has none of.
3. Scrape it into a master data resource under `Backend/json/`, in shapes the generator's existing
   conventions can consume.
4. Cross-check the result against an independent source so the numbers are not taken on trust.
5. Also capture the ten *Psionics Unleashed* races from d20pfsrd (scrape now, wire later).
6. Record what is genuinely missing at source, as distinct from what the scrape failed to parse.

The deliverable is facts and landed data, not a design: schemas, counts, and a plain statement of
what is and is not derivable.

## Answer

**Resolved 2026-07-31.** Two scripts and five data files landed; the validator passes with 0 errors.

### Access — the load-bearing practical fact

`libraryofmetzofitz.fandom.com/wiki/<Page>` is behind a **Cloudflare JS challenge**: `WebFetch`
returns HTTP 402 and `curl` returns the challenge page. **`api.php` is not challenged.** Everything
here goes through it with a browser `User-Agent`:

| Call | Used for |
|---|---|
| `action=parse&page=X&prop=wikitext` | prose fields, power-list link pages |
| `action=parse&page=X&prop=text` | the class tables (rendered HTML, parsed with bs4's `html.parser`) |
| `action=query&prop=revisions&rvslots=main&rvprop=content&titles=A\|B\|…&redirects=1` | powers, **50 pages per request** |

d20pfsrd needs no special handling beyond parsing `response.content` rather than `response.text` —
its declared charset is wrong and requests' fallback mangles every en dash.

No new dependencies: `requests`, `beautifulsoup4` and `pandas` are already in `requirements.txt`.
`lxml`/`html5lib` are **not** installed, so `pandas.read_html` is unavailable — tables are walked
with bs4 directly. Run with the repo venv; `C:\Python310` has none of these.

### What landed

`Backend/scripts/scrape_psionics.py` (idempotent, `--only classes|lists|powers|races`) writes into
`Backend/json/class_data/psionics/`, mirroring `class_data/path_of_war/`:

| File | Contents |
|---|---|
| `psionic_classes.json` | 12 classes: role, alignment, hit die, starting wealth, class skills, skill ranks, the raw 20-row table, a `derived` block, and 12–30 class-feature sections each |
| `psionic_powers_known.json` | 11 manifesting classes × `pp_per_day` / `powers_known` / `max_power_level`, **20-int arrays, index = level − 1** (the Path of War convention, not the 21-int spell one) |
| `psionic_power_lists.json` | 12 class power lists + the 7 psion disciplines, `{level: [names]}` with `"0"` = talents; each list flagged `in_scope` |
| `psionic_powers.json` | 615 powers: discipline, level-by-class, display, manifesting time, range, target/effect/area, duration, save, power resistance, PP cost, rules text, augment text, redirect aliases |
| `psionic_races.json` | the 10 d20pfsrd races, full page text plus indexed ability/size/speed/languages lines |

`Backend/scripts/validate_psionics_data.py` is the standing gate (docs doctrine: a hard convention
belongs in a validator, not a sentence).

### The class fields the module got wrong — now sourced

Every field is derived from the class table rather than a declared value; `bab` comes from the
level-20 BAB, which is precisely what upstream got wrong.

| Class | hit die | bab | skills | good saves | manifests |
|---|---|---|---|---|---|
| aegis | d10 | H | 4 | fort, will | PP only |
| cryptic | d8 | M | 4 | ref, will | yes |
| dread | d8 | M | 6 | ref, will | yes |
| highlord | d8 | M | 4 | fort, will | yes |
| marksman | d10 | H | 4 | ref, will | yes |
| psion | d6 | L | 2 | will | yes |
| psychic warrior | d8 | M | 4 | fort | yes |
| **soulknife** | **d10** | **H** | **4** | ref, will | **no** |
| tactician | d8 | M | 4 | will | yes |
| vitalist | d6 | L | 2 | fort, will | yes |
| voyager | d6 | M | 6 | ref, will | yes |
| wilder | d8 | M | 4 | will | yes |

The soulknife row is the case ticket 02 flagged: the module says `bab: low` / `hd: 6` /
`skillsPerLevel: 2` for it. Note the soulknife does **not** manifest — no power points, no powers
known — which makes it a mind-blade subsystem class, not a manifester
([ticket 08](08-bespoke-subsystems.md)). The aegis has power points but no powers-known column.

### Cross-check: two independent sources agree on 220 numbers

**All eleven manifesting classes' power-points-per-day columns match one of the three progressions
`pf1-psionics` hardcodes in `scripts/data/powerpoints.mjs` exactly** — low (aegis, marksman), med
(cryptic, dread, highlord, psychic warrior, voyager), high (psion, tactician, vitalist, wilder).
The module's PP table and the wiki's class tables were authored independently, so this is real
evidence the scrape is correct — and confirms the module's *class* fields, not its *tables*, were
the broken part. The validator hardcodes those three progressions and asserts the match, so a
future scrape regression fails loudly.

### Gaps at source (facts about the wiki, not scrape defects)

- **3 red links**: `Detect Compulsion`, `Manifest Veil`, `Mind Trap` are listed on class power lists
  but have no page.
- **Restore Essence** is missing manifesting time, range, duration, display and PP; five other
  powers are each missing one field. All 615 have discipline, level-by-class and rules text.
- **Noral** has no speed line on its d20pfsrd page.
- **29 pages are power chains** holding several variants under separate headings
  (`Metamorphosis, Minor` / `... Major`). Only the first variant's header is parsed; the headings
  are recorded under `chain_sections` so nothing is silently lost. Modelling them is fog.
- ~10 pages carry **malformed wiki markup** — split bold ticks (`'''Leve'''l'''`), missing colons,
  a `Power` / `Resistance` label broken across a paragraph. The parser reads header fields by
  structure rather than by markup, so these all resolve; they are noted only because they are
  upstream defects.

### Also established

The wiki lists **18** psionic base classes plus the Gifted NPC class, not 12. The twelve in scope
are the intersection with `pf1-psionics`' class items. **`zealot` already exists in
`class_data.json`** as a Path of War class, so the psionic Zealot cannot reuse that key in v2.

**Not done here, deliberately:** nothing is wired into `class_data.json`, `data.good_saves`,
`data.caster_mod` or the payload. That waits on tickets 03/06/07/08.
