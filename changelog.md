# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Categories (use only the ones you need, in this order):
  Added       — new features
  Changed     — changes to existing functionality
  Deprecated  — soon-to-be-removed features
  Removed     — now-removed features
  Fixed       — bug fixes
  Security    — vulnerability fixes
On release: rename "[Unreleased]" to "[x.y.z] - YYYY-MM-DD" and start a fresh Unreleased block.
-->

## [Unreleased]

### Added
- **Feat taxes** now resolve end-to-end. `feat_tax_func()` (`Backend/utils/class_func/feat_tax.py`)
  grants a primary feat's progression chain (from `Backend/json/feat_tax.json`) for free once its
  prerequisites are met, releasing **one chain feat per two levels** since the primary was gained;
  the FoundryVTT module bundles them onto the primary's sheet entry as
  `"<Label> Primary > Tax1 > Tax2"` (e.g. "Fighter 14: Net Adept > Net Maneuvering > Net and
  Trident"). Exceptions handled: "Extra …" feats grant one free self-duplicate, and Mythic feats
  never tax. (Path-of-War Martial Training and Sphere-of-Power talent taxes are deferred until those
  systems are integrated — see `docs/feature_spec_todo.md`.)
- `data/feats_new.csv` — a unified feat pool compiling every feat the project knows about into the
  canonical pipe-delimited schema plus a new trailing `source_dataset` provenance column: the official
  set (`AoN`, from `data/feats.csv`), the homebrew library (`Metzofitz`, from
  `data/Metzofitz_Feats.csv`), 91 net-new feats parsed from the campaign "Sieg's Guide" Feats Google
  Doc (`Sieg's Feats Doc`), and 8 net-new 3.5-only feats scraped from the d20 SRD (`d20srd`: Agile,
  Diligent, Extra/Improved Turning, Investigator, Negotiator, Nimble Fingers, Track). 3,306 feats
  total; AoN/Metzofitz rows are preserved exactly, so same-name entries like a base feat and its
  Mythic version are both kept.
- `Backend/scripts/compile_feats_new.py` — reusable, stdlib-only (+ pandas) compiler that builds
  `feats_new.csv`: maps the Metzofitz schema onto the canonical columns, best-effort-parses the
  freeform Google Doc, scrapes the d20 SRD feats page, dedupes the additive sources against existing
  names (the SRD via an order-insensitive token key, so "Armor Proficiency (Heavy)" matches "Heavy
  Armor Proficiency"), and verifies the output round-trips through the backend's
  `pd.read_csv(sep='|', on_bad_lines='skip')` loader.
- `docs/feature_spec_todo.md` — a TODO doc capturing six partially-scaffolded features awaiting design
  input (Path of War, Spheres of Power/Might, weapon attacks, weapon conditionals, free feats, feat
  taxes), each with its verified current state and a `Your spec:` prompt.
- `class_feat_labels` in the `/update_character_data` response: each class bonus feat is tagged with
  its granting class and level (e.g. "Fighter 1") via a new `class_bonus_feat_levels()` schedule
  helper, so the sheet can show class feats as "Fighter 1: Weapon Focus".
- `teamwork_feat_labels` does the same for teamwork feats (Hunter/Inquisitor every 3 levels;
  Cavalier/Samurai), via a `teamwork_feat_levels()` helper — e.g. "Inquisitor 3".
- `land_speed` (base race land speed) is now exported, consumed by the FoundryVTT custom-buffs feature.
- `bloodline_feats` and `bloodline_feat_labels` exports for Sorcerer & Bloodrager: bonus feats drawn
  from the character's own bloodline list, labeled by granting class and level (e.g. "Sorcerer 7",
  "Bloodrager 6"). New `bloodline_bonus_feat_levels()` schedule (Sorcerer 7/13/19/…; Bloodrager
  6/9/12/…, extending past level 20) and `bloodline_feat_chooser()` helper, which strips parenthetical
  specializations so names resolve in the pf1e compendium ("Skill Focus (Knowledge […])" → "Skill Focus").
- `craft_type` export — one Craft specialization rolled per character (new `crafts` list in `data.py`),
  so the sheet can show "Craft: <type>".
- `c_class_display` export — the class name in `every_class.json` format including the Unchained suffix
  (e.g. "Barbarian (Unchained)"), captured before the internal " (unchained)" strip. The FoundryVTT
  module uses it to create the correct class item.

### Changed
- Feat taxes gained **manual override knobs** in `feat_tax.json` (no code per caveat):
  `tax_chain_override` pins a primary's exact chain (e.g. Weapon Focus now taxes only to Greater
  Weapon Focus, Martial Focus, Weapon Specialization and Greater Weapon Specialization instead of its
  full ~31-feat derived tree), and `tax_exclude_grants` lists feats never granted as a tax child.
  **Critical feats no longer tax** — the `critical`-flagged feats (Blinding Critical, Staggering
  Critical, …) plus the Critical Focus gateway — matching the Mythic exclusion.
- Feat-tax chains are now **derived from the feats.csv prerequisite graph** rather than only the
  hand-listed `feat_tax.json` entries. Any selected "base" feat (has dependents but no feat-prereq of
  its own) or base Style feat auto-grants every feat that transitively requires it — Mounted Combat →
  Mounted Archery / Ride-By Attack / Trample / Spirited Charge / …, Dragon Style → Dragon Ferocity /
  Dragon Roar, Weapon Focus → Greater Weapon Focus / … — gated by the 2-level timing. A tunable
  `tax_primary_blocklist` in `feat_tax.json` tames mega-hubs (Power Attack, Combat Expertise, Dodge,
  Weapon Finesse, Improved Unarmed Strike); the existing `feat_tax` chains remain an optional homebrew
  override layer. (`feat_spell_searcher` now caches the feats.csv read, keeping generation ~fast.)
- Bonus skill ranks now scale off the FINAL highest mental ability — base score plus inherent bonuses
  and level-up bumps — instead of the base roll, via a new `highest_mental_mod()` helper. An Int/Wis/Cha
  boosted by inherents or level-ups now grants the extra ranks it should.
- Bloodline (Sorcerer/Bloodrager), teamwork (Inquisitor/Hunter/Cavalier/Samurai), monk, and ranger
  bonus-feat slots that exceed the available special-feat pool are now reallocated to extra normal
  feats, so the total feat count is preserved instead of silently dropping the slots. Example: a
  level-40 Bloodrager whose ~7-feat bloodline list can't fill all 12 granted slots now gets the 5
  leftover slots as normal feats.
- `data/feats.csv` is parsed once per run and cached (`grab_and_clean_feats`), instead of being
  re-parsed on every feat-selection call.

### Fixed
- Feat-tax chains are now ordered by a **stable topological sort** (each feat after all its in-chain
  prerequisites) instead of BFS shortest-path depth, fixing chains that rendered "Greater X > Improved
  X" (e.g. Two-Weapon Fighting, whose Greater feat lists the base feat directly and so tied with
  Improved and lost the alphabetical tiebreak). Two-Weapon Fighting, Two-Weapon Defense and Vital
  Strike also got `tax_chain_override` entries so they tax only to their improved/greater line instead
  of their full derived tree.
- Feat-tax resolution no longer stops at the first ineligible chain link. A link whose prerequisites
  aren't met (e.g. the Spheres-of-Might side-feat "Martial Focus" that sat in the Weapon Focus chain)
  is now skipped instead of blocking the rest, so "Weapon Focus > Greater Weapon Focus" bundles.
  Level / BAB prerequisites are treated as satisfied by the 2-level release cadence.
- Feat-tax chains whose feat also has a Mythic same-name variant (Iron Will, Lightning Reflexes, …)
  now bundle. `feat_tax.py` treated any feat with a Mythic row in `feats.csv` as Mythic (and Mythic
  feats don't tax), so those primaries were silently skipped; it now skips only feats that are
  Mythic-*only*.
- Independently-selected chain children no longer render as their own standalone feat — they're
  stripped from the feat lists and bundled onto the primary entry (e.g. "Iron Will > Improved Iron
  Will"). An already-owned child bundles regardless of the 2-level timing, which now gates only
  genuinely-free grants.
- The FoundryVTT module merges each bundled feat's benefit text into the primary feat's description
  (under a labeled separator) and clones template items before editing them, so the shared compendium
  template is no longer mutated across generations.
- Feat-tax eligibility no longer keeps only the LAST primary feat's chain. `feat_tax_func` overwrote
  its candidate list each iteration (`pre_eligible_feat_taxed_list = …` at `feat_tax.py:21`), so
  every primary feat but the last had its granted feats stripped; each primary is now resolved
  independently.
- Unchained classes (Barbarian/Monk/Rogue/Summoner) selected in the FoundryVTT dialog no longer
  produce a random class. The dialog sends a slug (e.g. `barbarian-(unchained)`, spaces→hyphens) but
  `chooseClass` only matched the space-separated `class_data` keys, so the four space-named classes
  fell through to a random pick; `chooseClass` now converts hyphens back to spaces. (As before, they
  resolve to their base class for data/archetype lookup.)
- `skill_ranks` is no longer double-JSON-encoded in the `/update_character_data` response, so the
  FoundryVTT module can read the generated skill ranks (they previously arrived as an un-parseable string).
- Sorcerer & Bloodrager bloodline bonus feats now actually reach the response. They were appended to
  `character.total_feats`, which is never exported, so they were silently dropped; they are now selected
  into the dedicated `bloodline_feats` export.
- High-level (>20) generation is no longer extremely slow. Feat-eligibility (`no_prereq_loop`) was
  O(n²) over ~1478 feats and re-run once per requested feat, so cost exploded as feat counts grew with
  level; it's now a single O(n) pass and `choosing_feats` no longer rebuilds its candidate list each
  pick. A level-40 character of any class now generates in ~0.2s.
- Fixed loops that could hang or crash at high level once a candidate pool was exhausted:
  `choosing_talents` (rogue/slayer/etc. talents) could spin or hit `random.choice([])`, and
  `monk_feats_chooser`/`ranger_feats_chooser` could loop forever (ranger's `== 7` break compared a set
  to an int and never fired). Each now stops when its pool runs out.
- Ranger combat-style feats and monk bonus feats were silently discarded in the default (truly-random)
  feat path: `character.feats` was reassigned by the normal-feat selector right after the choosers
  populated it. They now survive (merged once after selection and name-normalized to match the Foundry
  compendium), so rangers actually receive combat-style feats.
- Monks no longer double-count their bonus feats. The allotment was added both by `extra_combat_feats`
  (as labeled class feats) and `monk_feats_chooser`; monk bonus feats now come solely from
  `monk_feats_chooser`, with unfilled slots reallocated to normal feats, keeping the total the same.
- Fighter/Brawler (and other high-bonus-feat classes) no longer crash with "list index out of range"
  when using non-random (curated) feats. `separate_feats_func` popped `story+flaw+flavor+class_feats`
  from the front with unguarded indexing while the curated `build_selector` pool under-produced; it now
  pops from the front bounded by what's available (also fixing a latent every-other selection bug). The
  curated path additionally tops up from the general feat pool when its buckets come up short, so a
  level-40 curated character gets its full feat count instead of a stub.
- Unchained classes now display as their Unchained variant on the FoundryVTT sheet (via the new
  `c_class_display` export) instead of their base class.
