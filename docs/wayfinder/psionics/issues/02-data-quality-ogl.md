# 02 — Is the module's data trustworthy, and what must we carry to redistribute it?

Type: research
Status: resolved
Blocked by: —
Map: [Psionics](../map.md)

## Question

Two risks attach to adopting someone else's data set.

**Quality.** The Foundry package listing for `pf1-psionics` discloses that generative AI was used
during coding and data entry; the repo README does not repeat this. Spot-check a sample against
d20pfsrd's Psionics Unleashed pages — a dozen powers across levels and disciplines, plus every class
table we intend to use — and report the error rate and the *kind* of errors (wrong numbers, missing
fields, paraphrased rules text). This decides whether we extract straight, extract-and-validate, or
walk away from the data while keeping the module as the render target.

**Licensing.** The module is OGL 1.0a and the underlying content is *Psionics Unleashed*, © 2010
Dreamscarred Press. Establish what we must actually do when copying extracted mechanics into
`Backend/json/` in this repo and shipping them in a payload: the required §15 copyright-notice
entries, what counts as Product Identity that must be excluded, and how `pf1-pow` and `pf1spheres`
handle the same obligation (both ship the OGL text as their LICENSE). Report where the repo's own
attribution should live.

Report findings with URLs. A wrong "this is fine" is worse than "unclear — here is the text".

## Answer

**Resolved 2026-07-31.** Verdict: **extract-and-validate**, and the validation is not optional — the
data splits sharply into a trustworthy half and a broken half.

### The AI disclosure is real, and it is absent from GitHub

[The Foundry package page](https://foundryvtt.com/packages/pf1-psionics/) carries:

> "This package contains art, text, or software code produced using generative AI." /
> "AI tools were used during coding & data entry."

The repo README and homepage contain **no AI mention at all** — confirmed by direct fetch of both.
Anyone evaluating this module from GitHub alone would not know.

### Powers are clean — 0 errors in 8 samples

Sampled across levels 1/2/7/8 and six disciplines, checked field-by-field against d20pfsrd: Crystal
Shard, Astral Construct, Bend Reality, Catfall, Biofeedback, Brain Lock, Bond of Death, Astral Seed.
Name, level, discipline, range, manifesting time, display, augment text and the PP-cost formula
(`max(0, @sl*2-1)`) all check out; Catfall and Biofeedback are **word-for-word identical** to source.

This is the bulk of the value — 597 entries — and it is safe to extract close to straight.

### Class stat blocks are broken defaults — do not trust them

**Every one of the 12 classes** reports identically `bab: low`, `hd: 6`, `hp: 6`,
`skillsPerLevel: 2`. That is wrong for nearly all of them, and the module **contradicts itself in the
same file** — its own embedded description HTML carries the right numbers:

| Class | Module structured fields | Its own prose / d20pfsrd |
|---|---|---|
| Soulknife | `bab: low`, `hd: 6`, `skills: 2` | d10 Hit Die, **full/good BAB**, 4 + Int |
| Psychic Warrior | `bab: low`, `hd: 6`, `skills: 2` | d8 Hit Die, **medium BAB** (+15 at L20), 4 + Int |
| Wilder | `bab: low`, `hd: 6`, `skills: 2` | d8 Hit Die, 4 + Int |
| Psion | `bab: low`, `hd: 6`, `skills: 2` | d6, 2 + Int — **correct by coincidence** |

The bug is not "always wrong", it is "unfilled default that happens to match the psion". That is the
dangerous kind: a straight extract would silently produce soulknives with d6 HD and low BAB, and
nothing in `test_house_invariants.py` would catch it, because that test asserts the house *formulas*
against whatever `class_data.json` says — garbage in, consistent garbage out.

By contrast the categorical `savingThrows` fields (fort/ref/will = low/high) were checked against all
four core classes and **matched real data every time** — so `data.good_saves` entries can come from
the module.

### The progression tables are not in `packs-source/` at all

- **Power points per day** is a hardcoded JS table at
  [`scripts/data/powerpoints.mjs`](https://raw.githubusercontent.com/SoxMax/pf1-psionics/main/scripts/data/powerpoints.mjs).
  Its "high" progression (2, 6, 11, 17, 25 … 343) was verified against the known psion PP table and
  is correct. Extractable, but from JS, not YAML.
- **Powers known per level does not exist anywhere in the repo** — not in data, not in code. It must
  be hand-sourced. This substantially answers ticket 05 before it starts.

### OGL — and pf1-psionics' own §15 is incomplete

OGL 1.0a §6 requires carrying forward the **exact** §15 copyright notice of every work you copy from;
§8 requires marking which portions are OGC; §10 requires shipping the licence with every copy you
distribute. An extractor inherits the **whole upstream chain**, not just the DSP line.

Required §15 entries, verified on each d20pfsrd page's own notice block:

- *"Psionics Unleashed. Copyright 2010, Dreamscarred Press."*
- *"Psionics Expanded: Advanced Psionics Guide. Copyright 2011, Dreamscarred Press; Authors: Jeremy
  Smith and Andreas Rönnqvist."* — the **Aegis** traces here, not to a standalone "Ultimate Psionics".

**pf1-psionics' own [LICENSE](https://raw.githubusercontent.com/SoxMax/pf1-psionics/main/LICENSE) is
missing both the Psionics Expanded line and the Psionics Augmented: Seventh Path line** (which its
own Bond of Death power cites). The same text block appears verbatim in `pf1-pow`'s LICENSE —
including a Psionics Unleashed line inside a Path of War module — so it is copy-pasted boilerplate,
not a curated §15. **Copying their notice would inherit the gap.** Ours must be hand-curated from the
`sources:` blocks actually present in what we extract.

Note: the DSP SRD wikidot mirror is a stale 2010 revision that predates Psionics Unleashed's release
and does not list it — **not a usable source for §15.** Use d20pfsrd.

Product Identity vs OGC: mechanics and stat text are OGC and safe to extract; DSP branding, logos and
trade dress are PI and must not imply endorsement.

**How the comparables do it:** `pf1-pow` ships the full OGL text as `LICENSE` plus a README section
with the Paizo Community Use Policy, a DSP non-endorsement disclaimer, and a hand-curated content
sources list. `pf1spheres` is the more rigorous pattern — REUSE.software/SPDX, with
`LICENSES/LicenseRef-OGL-1.0a.txt` and a `REUSE.toml` that machine-declares
`src/packs/** → LicenseRef-OGL-1.0a`, keeping the module's own code separately licensed.

Recommendation carried to [ticket 09](09-ogl-attribution.md) for a decision.
