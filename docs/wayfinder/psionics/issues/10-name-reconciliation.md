# 10 — What happens to a Metzofitz name the Foundry module has never heard of?

Type: research
Status: resolved
Blocked by: 01
Map: [Psionics](../map.md)

## Question

The map locks a split that only works if the two halves agree on names: the **Metzofitz wiki** is
the source of truth for mechanics, and **`pf1-psionics` is the render target**. The module attaches
items by name match, and a name it does not recognise is *silently dropped* — no error, just a
sheet missing the thing the payload asked for. This repo has already been bitten by exactly this
failure mode with conditionals.

The two catalogues are not the same size. The scrape landed **615 powers**; the module ships
**597**, and the wiki is a homebrew republication that adds its own material — powers carrying the
`[Essence]`, `[Network]`, `[Shared]` and `[Trigger]` descriptors, and Akashic / Cerulean Seas
crossover content that Dreamscarred Press never published.

Settle:

- **How big is the gap, in both directions?** Diff the 615 scraped power names against the module's
  powers pack, and the twelve class names against its classes pack. Casing, punctuation and
  disambiguation suffixes (`Astral Construct (power)`, `Mindlink (power)`) all count as mismatches
  until normalised — report the raw diff and the diff after normalisation separately.
- **What is the fallback for a Metzofitz-only power?** Path of War already answers this shape of
  question: it emits `maneuvers_desc_dict` so the module can synthesize an item when the compendium
  has none. Does psionics take the same route, or are unmatched powers excluded from selection
  entirely?
- **Which name wins in the payload** when the two differ — the wiki's or the module's? Emitting the
  module's name makes the sheet work; emitting the wiki's keeps the payload faithful to its source.
  Both cannot be true, and the standalone web sheet has no module to reconcile against.
- **Do the 29 power-chain pages need splitting** before this diff is meaningful? The module almost
  certainly ships `Metamorphosis, Minor` and `Metamorphosis, Major` as separate items, while the
  scrape holds them as one record with a `chain_sections` list.
- **The three red links** (`Detect Compulsion`, `Manifest Veil`, `Mind Trap`) are on class power
  lists with no wiki page. Does the module have them, and can it supply what the wiki lacks?

`pf1-psionics` is **not installed locally** — this ticket needs it installed, or its
`packs-source/` cloned, purely as a name list. That is the one thing the module is still read for.

## Answer

Measured 2026-07-31 against the installed module — which **is** installed at
`FoundryVTT/Data/modules/pf1-psionics`; the ticket's "not installed locally" premise was stale. Its
LevelDB packs read fine without launching Foundry, via `classic-level` (already in
`pf1-conditional-applier/node_modules`). No clone of `packs-source/` was needed.

**Pack structure.** Each pack mixes Folder docs (category headers) with Item docs. Powers pack = 7
discipline folders + **593 power items**. Classes pack = 22 folders + 397 items, of which **12 are
`type: "class"` and 385 are `type: "feat"`** — the module has no class-feature type; class features
*are* feats. That matters for attach code.

### The gap, both directions

| Diff | Ours | Theirs | Raw ours-not-in-theirs | After normalisation |
|---|---|---|---|---|
| Powers | 615 | 593 | 111 | **67** |
| Classes | 12 | 12 | 12 | **0** |
| Class features | 151 | 370 | 151 | **16** |

Normalisation = casefold, collapse whitespace, `’`→`'`, strip trailing `(power)` / `(Su)` / `(Ex)` /
`(Ps)`. Classes close completely on casefold alone (ours are lowercase keys, theirs capitalised).

The 67 unmatched powers are **genuine content gaps, not naming mismatches** — no normalisation
recovers them. They are the Metzofitz-only material the map predicted: `[Essence]` / veil content
(`Essence Theft`, `Suppress Veil`, `Veil Restoration`), mindscape powers, and Akashic/crossover
material DSP never published. This is exactly the population `powers_desc_dict` exists to synthesize,
which validates the fallback decision rather than changing it.

Of our 151 scraped feature names, only **3 are genuine gaps** — `lesser insights` (cryptic),
`highlord tenets (Su)`, `vitalist's expertise (Su)`. The other 13 are **scrape artifacts**: generic
table and section headers captured as if they were features (`powers known`, `power points/day`,
`maximum power level known`, `weapon and armor proficiency`, `favored class bonuses`, `archetypes`,
`point-blank shot`, …). They go on the P2 fix list. The reverse direction (370 theirs-not-in-ours) is
**not** apples-to-apples and must not be read as 235 missing features — the module's feat items are
far more granular, with one entry per level for things like "Bonus Feat".

### Apostrophes — normalise on both sides

| Name set | `’` U+2019 | `'` U+0027 |
|---|---|---|
| Our power names (615) | 33 | 1 |
| Module powers (593) | 0 | 35 |
| Module class features (385) | 6 | 5 |

Our source is wiki typography (curly); the module is mostly straight **with curly outliers mixed in**.
No name contains both. Mapping both sides to `'` is required and sufficient.

### Power chains — split, and it is our own bug first

**Yes, split before the diff means anything** — but the decisive reason is not the module. It is that
**`psionic_power_lists.json` cites 45 power names that have no top-level record in
`psionic_powers.json`.** Of 591 cited names, 45 are unresolvable *within our own data*, so a
name-match lookup fails today regardless of Foundry. Splitting the **30** `chain_sections` records
into individual power records fixes **30 of the 45**, because the missing names are chain variants —
`Barred Mind, Personal`, `Concealing Amorpha, Greater`, `Ectoplasmic Creation, Major`,
`Ethereal Form, Greater`, `Energy Adaptation, Specified` and so on. The module already ships these as
standalone items, so the split moves us toward its shape as well as toward internal consistency.

The 32 `Mythic …` variants inside those chains are **out of scope, not gaps** — the module ships no
Mythic Adventures content at all.

There is also **wiki bold markup (`'''`) bleeding into scraped text** — visible in `Far Hand`'s
`chain_sections`, which is where the malformed `Clairtangent Hand` comes from. (Correcting the
research pass on two points: no top-level *key* contains `'''`, and the 13th entry in
`psionic_power_lists.json` is `Psion Discipline Powers`, which is keyed by `disciplines` rather than
`levels` — any consumer that assumes `levels` will `KeyError`.) P2 should strip wiki markup and audit
for other instances.

### The red links — there are 15, not 3

The ticket named three. Measuring cited-vs-present found **15 power names cited by class lists with no
record of their own**, once chain variants are excluded:

`Blinding Shot`, `Call To Mind, Lansis's`, `Detect Compulsion`, `Everyman`, `Expansion`,
`Know Direction And Location`, `Manifest Veil`, `Mind Trap`, `Shift The Tide`, `Slip The Bonds`,
`Soul Feast`, `Spray`, `Thought Shield`, `Touchsight`, `Wall Walker`

Of the original three: **`Detect Compulsion` and `Mind Trap` both exist in the module's powers pack**,
so the module supplies what the wiki lacks. **`Manifest Veil` exists nowhere** — not in any pack, under
any normalisation — and needs sourcing independently or dropping from the lists it appears on.

### Decisions this settles

- **Which name wins:** the **module's**, wherever one matches — a faithful-but-invisible power helps
  nobody. Unmatched names are emitted as the wiki spells them, plus a `powers_desc_dict` entry so the
  module synthesizes an item. No power is excluded from selection merely for being Metzofitz-only.
- **Two independent defences**, as locked: `Backend/scripts/reconcile_psionics_names.py` regenerates
  `psionic_name_map.json` from the packs, `validate_psionics_data.py` fails on any unmapped name, and
  the module normalises case and apostrophes at attach time as a runtime net.
- **The validator also gains an internal-consistency gate** — every name cited by
  `psionic_power_lists.json` must resolve to a record in `psionic_powers.json`. That check is
  independent of Foundry and would have caught all 45 of these on the day the scrape landed.

Draft map and full diff data: the research pass wrote `psionic_name_map_draft.json` and
`diff_report_full.json` to the session scratchpad; `reconcile_psionics_names.py` regenerates both as
committed artifacts in P2.
