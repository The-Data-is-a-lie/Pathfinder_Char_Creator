# Map: Psionics

Wayfinder map. Tickets are the files in `issues/`; the **frontier** is every ticket that is
`Status: open`, unclaimed, and whose `Blocked by:` list is entirely `resolved`.

> ## CLOSED — 2026-07-31
>
> **All eleven tickets are `resolved` and the frontier is empty.** Gates 1 and 2 below are met:
> `validate_psionics_data.py` and `test_house_invariants.py` pass with all twelve classes present
> (275 generations, 4561 checks), and each of the twelve rolls a populated `manifesters` entry with
> legal powers. **Gate 3 (Foundry import) is deliberately not closed here** — it spans the
> `pf1e_random_char_generator` module repo and is a later branch.
>
> ### Gate 3 — built 2026-08-03, awaiting a live Foundry run
>
> The rendering half now exists in both front ends. `pf1e_random_char_generator`'s
> `modify-abilities.js` writes the `pf1-psionics` manifester book flags (`inUse` is the *entire*
> condition that module's `actor-sheet.mjs` gates its tab on — no class item, tag or power is
> consulted) and attaches `pf1-psionics.power` items, pack-cloned or synthesized, with a feat-item
> fallback when the module is absent. The standalone web sheet gained a Psionics tab. Both were
> exercised headlessly against the new `manifester` golden; **the live import in Foundry is the one
> step still outstanding.**
>
> **Defect found while building it, since fixed:** `build_every_class.mjs` harvested the twelve
> psionic class items from `pf1-psionics` but never patched `bab` / `hd` / `skillsPerLevel`, so all
> twelve sat in `every_class.json` at the module's placeholder `low` / `6` / `2` — the exact
> breakage ticket 02 measured, carried into our own bundle. It is correct for the psion alone. The
> "class items are harvested **with those fields patched** from our scrape" clause of
> [ticket 03](issues/03-division-of-labour.md) was decided and never implemented, and the module
> supplies no BAB of its own, so pf1 derived an aegis 20's attack bonus at +10 instead of +20.
> `patchProgression()` in that script now reads the three fields from `class_data.json` (`bab`
> H/M/L, `hit die`, `skill points at each level`), refuses to write if a harvested class is missing
> from it, and verifies what it wrote; both bundles were rebuilt.
>
> This map is now history, not a work queue. Live psionics work continues in **§9 of
> `docs/feature_spec_todo.md`** (which owns the spec, the amendments, and the deferred list) and in
> **`docs/plan_1.0_finish.md`** (which owns the roadmap). Two decisions taken during the build
> *amend* what the tickets below settled, and the tickets carry the amendments inline:
>
> - The **manifesting ability** lives in `class_data.json` as `manifesting_stat`, not in a `data.py`
>   map — [ticket 04](issues/04-class-pool-entry-trigger.md).
> - The **voyager has no option list**; "path skills" was a psychic warrior feature, so there are
>   nine subsystems, not ten — [ticket 08](issues/08-bespoke-subsystems.md).
>
> Two entries in the defect list further down were also **withdrawn as not-defects** on measurement.

## Destination

**Widened 2026-07-31 (user decision).** Originally "spec only, no generator wiring". The spec landed
as **§9 Psionics** in [`docs/feature_spec_todo.md`](../../feature_spec_todo.md), and the effort now
carries through to **playable**, absorbing Phase 4.5 of `docs/plan_1.0_finish.md`. Work is on branch
`feat/psionics-v1` (plus a matching branch in the FoundryVTT module repo).

Finish line — three gates:

1. `Backend/scripts/test_house_invariants.py` and `validate_psionics_data.py` pass with all twelve
   classes present.
2. `Backend/main_test.py` rolls each of the twelve; the payload carries a populated `manifesters`
   entry with legal powers.
3. A generated psion, soulknife and psychic warrior import into Foundry with `pf1-psionics` active
   and show their powers, power points and correct BAB, with nothing silently dropped.

Web-sheet rendering is explicitly **not** a gate.

## Notes

- **Domain:** Pathfinder 1e psionics (Dreamscarred Press *Ultimate Psionics*, as republished by the
  Library of Metzofitz), this repo's generator backend, the `pf1e_random_char_generator` FoundryVTT
  module, and the standalone web sheet.
- **Skills every session should consult:** the OKF `pathfinder` bundle via the user-level
  `oks-bundles` skill; `/grilling` and `/domain-modeling` for the conversation tickets;
  `/research` for the research tickets.
- **Format to match:** §1 (Path of War) and §2 (Spheres) in `docs/feature_spec_todo.md`. §1 is now
  the closer precedent — a 3pp system whose mechanics are *scraped* into `Backend/json/` while a
  third-party Foundry module renders the result.
- **1.0 scope:** pulled into 1.0, so `docs/plan_1.0_finish.md` gains a phase once the spec lands.

### Locked (user decisions, 2026-07-31)

1. **Adopt [`pf1-psionics`](https://github.com/SoxMax/pf1-psionics); do not build our own module.**
   The original plan was a new public module; research found this one already exists and is active.
2. **The [Library of Metzofitz wiki](https://libraryofmetzofitz.fandom.com/wiki/Psionic_Classes) is
   the source of truth for psionic *mechanics*.** *(Supersedes the original "extract the module's
   `packs-source/` YAML" decision, which [ticket 02](issues/02-data-quality-ogl.md) disproved: all
   twelve of the module's classes carry identical placeholder `bab: low` / `hd: 6` /
   `skillsPerLevel: 2`, and powers-known per level exists nowhere in the module at all.)* The wiki
   is already this repo's source for `data/Metzofitz_Feats.csv`, and it is the campaign's own
   authority.
3. **`pf1-psionics` is the render target, not a data source.** It still decides what appears on a
   Foundry sheet, so **every name the generator emits must reconcile against its pack names** — an
   unmatched name is silently dropped by the module. That reconciliation is
   [ticket 10](issues/10-name-reconciliation.md).
4. **Scope is twelve classes**: Aegis, Cryptic, Dread, Highlord, Marksman, Psion, Psychic Warrior,
   Soulknife, Tactician, Vitalist, Voyager, Wilder — the set that has both a full Metzofitz wiki
   page and a `pf1-psionics` class item. The wiki's other six base classes (Genesis, Skipper, Thug,
   Warpmind, psionic Zealot, Soulknife (High Psionics)) and the Gifted NPC class are held for v2.
5. **Psionic races: scrape now, wire later.** The ten *Psionics Unleashed* races are captured into
   the master data resource; whether they enter the generator's race pool is
   [ticket 11](issues/11-psionic-races.md).

### Starting state (established during charting, 2026-07-31)

- **Zero psionics content existed in this repo** before ticket 01. Grep for psion / power point /
  manifest / psychic / soulknife / wilder / cryptic / vitalist returned only coincidental prose and
  the unrelated core PF1 *psychic* occult class.
- **No *pre-existing* compendium supplied psionics** — `pf-content`, `pf1-pow`, `pf1spheres` and
  `statblock-library` were all checked at the LevelDB level.
- `pf1-psionics` v0.9.1: Foundry v13 min/verified, requires system `pf1` ≥ 11 (verified 11.8) and
  `lib-wrapper`. Seven packs: buffs, classes, feats, macros, powers, races, rules. Licensed OGL 1.0a.
  It **auto-calculates manifester level, concentration and power points** and tracks psionic focus.
  **It is installed locally** at `FoundryVTT/Data/modules/pf1-psionics` (the earlier "not installed"
  note was stale), and its packs are readable without launching Foundry via `classic-level`, already
  present in `pf1-conditional-applier/node_modules` — no clone of `packs-source/` is needed.
- **Measured pack contents (2026-07-31), correcting the earlier item counts:** powers pack **600**
  entries, of which the first several are the **7 disciplines**, not powers; races pack **161**;
  classes pack **419** — because that pack ships **every class *feature* as its own named item**
  alongside the 12 class items. The name-reconciliation surface is ~35× what
  [ticket 10](issues/10-name-reconciliation.md) assumed. The packs also **mix apostrophe
  characters** internally: `Artificer’s Surge` (U+2019) sits beside `Reaper's Blade` (U+0027).
- **Psionic feats already exist in this repo.** `data/Metzofitz_Feats.csv` carries 311
  psionic-flagged rows (264 typed exactly `Psionic`, 52 `Metapsionic`, 3 `Gather_Power`), kept out
  of the random pool on purpose by `_METZ_TYPES` in `Backend/utils/class_func/feats.py`, which
  admits only `General` and `Combat`. No feat scrape is needed; turning them on is a selection
  decision, not a data one.
- **Adding a class to this generator** needs: a `Backend/json/class_data.json` entry (`bab` H/M/L,
  `hit die`, `skill points at each level`, features after the `weapon and armor proficiency` key)
  and a `data.good_saves` entry — BAB and saves derive generically in `class_func/level_and_bab.py`.
  Casters additionally need entries in `data.base_classes` and one of `data.caster_mod`'s three
  lists. The class pool is every `class_data.json` key minus `occult_classes` and
  `pow_classes_pending_foundry` (`Backend/utils/util.py::_available_class_pool`).
  `Backend/scripts/build_pow_class_data.py` is the batch-merge template;
  `Backend/scripts/test_house_invariants.py` is the gate.
- **`zealot` is already taken** in `class_data.json` by the Path of War class. Out of scope for v1,
  but the psionic Zealot cannot use that key.
- **No generic resource-pool mechanism exists** in the backend — spells and maneuvers are each a
  bespoke table + module. The Foundry module *does* have one: `addResourcePools()` +
  `CLASS_RESOURCE_POOLS` in `scripts/modify-abilities.js`.
- **Payload contract:** the response is read by key name everywhere, so new keys are safe. The
  **request is unpacked positionally** (`Backend/app.py::process_input_values`, `input_values[0..18]`);
  any new input flag must be popped by name in `app.py` before the positional list is built (the
  `spheres_of_power` pattern) and read by name in the web sheet's `generate.js::buildPayload` and
  the module's `button.js`.

## Decisions so far

<!-- one line per resolved ticket: gist + link. Detail lives in the ticket, never here. -->

- [02 — Is the module's data trustworthy, and what must we carry to redistribute it?](issues/02-data-quality-ogl.md) —
  **extract-and-validate**: powers are clean (0 errors in 8 samples, two verbatim-identical to
  source) and saving throws are right, but **all 12 classes carry identical placeholder
  `bab: low` / `hd: 6` / `skillsPerLevel: 2`** that contradicts their own prose and is correct only
  for the psion by coincidence; the PP table lives in JS not YAML, powers-known exists nowhere, and
  upstream's §15 is incomplete so ours must be hand-curated. This is what redirected the source to
  the Metzofitz wiki.
- [05 — Reconcile the scraped class tables against RAW and the house rules](issues/05-powers-known-pp-tables.md) —
  **eleven of twelve match RAW exactly; the parser is not at fault anywhere.** All three flagged rows
  (voyager, vitalist, dread) are genuinely written that way. The one real deviation was *not* on the
  watch list: the **psychic warrior has good Fort only** where RAW gives Fort+Will, with a
  wholly-rewritten Path feature track — a **deliberate house divergence**, recorded in §9, not to be
  reverted. Manifesting ability sourced for all twelve (Int: aegis/cryptic/psion/tactician/voyager ·
  Wis: marksman/psychic warrior/vitalist · Cha: dread/highlord/wilder · soulknife: none). **Bonus PP
  is a formula, not a table** — `floor(mod × ML / 2)`, plus a score-≤9-cannot-manifest gate. No
  psionics-specific house rule; the universal 2→4 skill floor applies automatically.
- [10 — What happens to a Metzofitz name the Foundry module has never heard of?](issues/10-name-reconciliation.md) —
  **measured.** After normalisation (casefold, `’`→`'`, strip `(power)`/`(Su)`): classes match
  **12/12**, class features leave **3** real gaps, and **67 of 615 powers** are genuine
  Metzofitz-only content no normalisation recovers — exactly the population `powers_desc_dict`
  synthesizes. Bigger finding: **`psionic_power_lists.json` cites 45 names that have no record in
  `psionic_powers.json`** — our own data is internally inconsistent, independent of Foundry.
  Splitting the 30 `chain_sections` records fixes 30 of them; the other 15 are cited-but-pageless
  powers. `Detect Compulsion` and `Mind Trap` turn out to exist in the module; **`Manifest Veil`
  exists nowhere.** The module has no class-feature type — its 385 class features are `type: "feat"`.
- [03 — What does the backend compute, and what does the module?](issues/03-division-of-labour.md) —
  **the backend computes and emits**; the module renders (the §1 `initiator_level` precedent). Class
  items are harvested from `pf1-psionics` into `every_class.json` with `bab`/`hd`/`skillsPerLevel`
  **patched** from our scrape — `bab: low` was the only one that mattered, since actor HP is already
  backend-supplied. `pf1-psionics` owns PP and focus when active; a payload-driven resource pool is
  the fallback when it is absent.
- [04 — How do psionic classes enter the random pool?](issues/04-class-pool-entry-trigger.md) —
  **no API flag** (the §1 precedent, not the Spheres one). All twelve in the pool by default;
  holdbacks by name in a new `data.psionic_classes_pending`. Accepted: psionics becomes ~12 of 55
  pool entries, ~22% of default rolls. Manifesting ability gets its own `data.py` map, **not**
  `caster_mod`.
- [06 — What is the `manifesters` payload shape?](issues/06-manifesters-payload-shape.md) —
  a list mirroring `spellbooks`, with `powers_desc_dict` as a **sibling** top-level key the way
  `maneuvers_desc_dict` is. **Augmentation is not a generation-time field** (use-time; the module
  ships an augment editor); focus is not a payload field; no `CLASS_RESOURCE_POOLS` entry while
  `pf1-psionics` is active.
- [07 — How are powers actually picked?](issues/07-power-selection-algorithm.md) —
  the `path_of_war.py` shape **minus the prerequisite machinery**: psionic powers have **no
  prerequisites**, so `_constrained_pick`'s prereq graph has no analogue. Level-weighted picks from
  the class list, psion's discipline mandated, soft 2–3 discipline bias for everyone else.
- [08 — Which bespoke class subsystems are v1?](issues/08-bespoke-subsystems.md) —
  **all twelve**. Nine subsystems plus blade skills are the same shape and all ride the *existing*
  `generic_class_option_chooser`; no new chooser module. The real cost is a **scraper extension** to
  capture per-class option lists, which the ticket's framing hid. The soulknife's **mind blade** is
  the one special case — a synthesized weapon scaling off the class table.
- [09 — What OGL attribution do we ship?](issues/09-ogl-attribution.md) —
  root `LICENSE-OGL.txt` (OGL 1.0a + a §15 curated from **our own** `sources:`, since upstream's is
  incomplete), a subtree `NOTICE.md` for §8 marking, and a `/license` endpoint plus payload pointer
  for the §10 API question. `pf1-psionics` credited as intermediate compiled source. Full REUSE/SPDX
  rejected as more ongoing obligation than value.
- [11 — Do the psionic races enter the race pool?](issues/11-psionic-races.md) —
  **no, and re-scoped**: this becomes the **custom-race route** ticket for all homebrew races
  (Loxo / Kalyptran / Dolistani too), because `race_traits_chooser` walks `PlayableRaces.json`
  *positionally* and that route must be designed once, not twice. Data stays where it is.
- [01 — Where does the psionics data actually come from, and what is in it?](issues/01-inventory-packs-source.md) —
  **landed**: `Backend/scripts/scrape_psionics.py` + `validate_psionics_data.py` produce five files
  under `Backend/json/class_data/psionics/` — 12 classes with real bab/hit-die/skill-points/saves,
  20-row progressions, 13 power lists + 7 psion disciplines, 615 powers, 10 races. Access is via
  `api.php` (plain `/wiki/` fetches hit a Cloudflare challenge). **All 11 manifesting classes' PP
  columns match the Foundry module's own low/med/high tables exactly** — independent confirmation
  the scrape is right, and confirmation the module's *class* fields were the broken part.

## Not yet specified

- **Where the manifesting ability lives.** §9 and [ticket 04](issues/04-class-pool-entry-trigger.md)
  lock a new `data.py` map, but that was decided against `caster_mod`, not against
  `class_data.json`. Every psionic class gets a `class_data.json` entry anyway, already carrying
  `main_stat` (read by `class_func/stats.py`), and the scraper supplies the ability either way — a
  `manifesting_stat` key beside `main_stat` is one owner where the `data.py` map is two that can
  drift. It is a separate key regardless: psychic warrior manifests off Wis but plays off Str, and
  soulknife manifests off nothing. **Decide at the `class_data.json` merge**; amend §9 and ticket 04
  if the answer changes. *(The only surface carrying this — §9 still reads as settled.)*
- Multiclass manifester-level stacking across two psionic classes.
- Metapsionic / augment feats at generation time — likely a use-time concern, not confirmed.
- **Turning on the 311 psionic feats already in `data/Metzofitz_Feats.csv`** — the data is there and
  the gate is a one-line `_METZ_TYPES` change, but *which* psionic feats a manifester should be
  eligible for (and whether metapsionic feats need a manifester-level check) is undecided. Sharpens
  once the payload shape lands.
- Power **conditionals** on the main weapon, mirroring the PoW maneuver / Spheres talent pipelines.
  Only sharpens once the payload shape lands.
- The **psicrystal**, which is a psion/wilder bonded item but structurally a companion — cross-refs
  [Map: Bonded creatures](../companions/map.md).
- Whether psionic **items** (cognizance crystals, dorjes, power stones) enter the gear chooser.
- The **v2 classes** — Genesis, Skipper, Thug, Warpmind, psionic Zealot, Soulknife (High Psionics),
  and the Gifted NPC class. All have wiki pages; none has a Foundry class item, and the psionic
  Zealot needs a non-colliding key.
- **Power chains** — 29 scraped pages hold more than one power variant under separate headings
  (`Metamorphosis, Minor` / `... Major`). Only the first variant's header block is parsed; the
  headings are recorded under `chain_sections` so nothing is lost. *Being settled by
  [ticket 10](issues/10-name-reconciliation.md), which checks whether the module ships the variants
  as separate items — if it does, the pages must be split before the name diff means anything.*

### Data-quality defects found while grilling (fix in the scraper, 2026-07-31)

- These files are UTF-8 and **must be opened with `encoding='utf-8'`** — Windows Python defaults to
  cp1252 and raises `UnicodeDecodeError` on them. Applies to the validator and every consumer.
- **`chain_sections` entries keep internal wiki bold ticks.** `scrape_powers` builds them with
  `.strip("= '")`, which only trims the *ends*, so `Far Hand` carries a `C'''lairtangent Hand`
  variant. Use `strip_markup()` (which already handles `'''`) instead of `strip`.
- **`parse_features` keeps every heading section**, so table and section headings land in `features`
  as though they were class features — 13 of the 151 are not features at all.
- The scrape captured a `features` list per class but **not the option lists those features draw
  from** (blade skills, insights, decrees, …). [Ticket 08](issues/08-bespoke-subsystems.md) needs
  them as `{name: description}`; this is the single largest piece of remaining scraper work.
- Confirmed from the data, as [ticket 05](issues/05-powers-known-pp-tables.md) suspected:
  **soulknife has no `powers_known` entry at all** and **aegis has `pp_per_day` but no powers**.
  "Manifester" is three categories, and the payload models all three.
- **Not a defect, withdrawn:** an earlier entry here claimed 45 cited power names had no record. Of
  665 cited names, 53 resolve through `aliases` (wiki redirects) and 3 more are case variants;
  **only the 3 known red links are genuinely missing**. `validate_psionics_data.py` already
  casefolds and follows aliases, and has been reporting exactly 3 all along. The bad number came
  from an ad-hoc probe that did neither.
- **Structural trap:** `psionic_power_lists.json`'s 13th entry, `Psion Discipline Powers`, is keyed by
  **`disciplines`**, not `levels`. Any consumer that assumes `levels` raises `KeyError`.
- **Not a defect, withdrawn:** an earlier entry here called for normalising `derived['hit die']`
  (`"d6."`, trailing period) and `derived['skill points at each level']` (a `str`, not an `int`)
  before the `class_data.json` merge. Those are exactly the shapes `class_data.json` already uses —
  all 51 pre-psionics entries spell the hit die with the period (28× `'d8.'`, 15× `'d10.'`, 5×
  `'d6.'`, 3× `'d12.'`) and hold skill points as a string. Normalising would have **broken** the
  merge; `scrape_psionics.py` says so in a comment at `entry["derived"]`.
- **`manifesting_ability` is not a field yet** — it exists only inside each class's power-points prose
  and must be lifted into `derived` (values sourced by [ticket 05](issues/05-powers-known-pp-tables.md)).
- Checked and **dismissed**: the `` glyph seen in `class skills` prose is a Git-Bash console
  rendering artifact. All five files contain **zero** U+FFFD; the byte is a real U+2019. No data loss.

Settled since: the **out-of-scope power lists** (Gambler, Gifted Blade, Sighted Seeker) stay in the
data because in-scope powers' `Level:` lines cite them, but no in-scope class selects from them —
see [ticket 07](issues/07-power-selection-algorithm.md).

Still unaddressed, as courtesy rather than work: reporting the incomplete §15, the placeholder class
fields, and the ~10 malformed wiki pages **upstream** to SoxMax and to the wiki's editors.

## Out of scope

- Building our own psionics Foundry module — superseded by the adopt decision.
- Extracting class or power mechanics from `pf1-psionics`' `packs-source/` YAML — superseded by
  locked decision 2; the module is read only for name reconciliation and as the render target.
- Balance or playtesting of psionic power lists.
- Psionics Augmented content beyond what the Metzofitz wiki publishes.
- Contributing fixes upstream to SoxMax or to the wiki.
