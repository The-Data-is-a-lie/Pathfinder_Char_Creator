# 10 — What happens to a Metzofitz name the Foundry module has never heard of?

Type: research
Status: open
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

_Unresolved._
