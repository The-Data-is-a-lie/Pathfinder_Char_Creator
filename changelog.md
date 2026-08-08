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
- **Seven classes now make the choice they are built around.** Every gap class-choices ticket 02
  found is built. Each was generating an **empty class-features dict** — the bard, hunter, shifter,
  psion, vampire hunter, omdura, and the witch's patron.
  - **bard** — three buckets (versatile performances, martial performances, expanded versatility).
    The picker already worked; its results were returned in a tuple the call site discarded. Each
    bucket now has its own schedule instead of the three sharing one budget split by a coin flip,
    so a bard gains **more total picks than before** — intended, not incidental.
  - **hunter** — Animal Focus, two frozen picks at 1st (one for herself, one for her companion).
  - **shifter** — aspects at 1st, 9th, 14th and 20th.
  - **psion** — the discipline that decides which of its powers are legal.
  - **vampire hunter** — vampiric foci at 1st, 8th and 16th (the only gap that is not a single pick).
  - **omdura** — an invocation, the first pick to use ticket 02's roll-once-and-freeze rule.
  - **witch** — a patron, **and its spells**, level-gated: a patron grants nine spells at witch
    levels 2–18, which are spell levels 1–9 in order, so the list is truncated at the witch's own
    level. Closes the *"need to add patron spells to the witch spell list"* TODO that shipped with
    the file. The patron is the gap that **hid inside a non-empty row** — the witch already had a
    `hexes` row, so a sweep that only inspected empty rows would have missed it.
  - **Archetype-gated options now work through the existing prerequisite engine.** 144 of the
    hunter's aspects are gated on an archetype named in the option's own `prerequisites`, and the
    engine could already check that — it just never had the archetype. Rolled archetype names are
    seeded into `character.chooseable`, minus 18 that are also the name of a selectable option
    (`brawler` is both an archetype and a rage power, and a prereq string cannot say which it
    meant). This does **not** model archetype feature *swaps*; that ruling is unchanged.
  - Two pools were harvested from `pf-content` by a new
    `build_collab_class_options.py`. They needed different extractions: the vampire hunter's 10
    foci are each their own Item, while the omdura's 9 invocations are **bolded headings inside one
    item's description** — which is why a name search found nothing and ticket 02 recorded the
    omdura as having no source at all.
  - **Data repairs found on the way.** The hunter's pool was missing Snake: one aspect's name cell
    was empty in the scrape, so the base list read as 11 plus a blank. Filtering blanks — the
    obvious defensive move — would have shipped 11 aspects forever; the key is repaired and the
    gate now pins the base list at RAW's twelve. One witch patron's key/value split mid-citation
    because the scrape broke on a comma *inside* the sourcebook parenthetical.
  - **A pool must MOVE, not be copied.** Extracting the shifter's aspects while leaving them in
    `class_data.json` made all 27 silently unpickable and raised nothing:
    `chooseable_list_class_features` seeds every feature key into `chooseable`, and
    `no_prereq_loop` skips any option already there. The gate now fails on it, and immediately
    found four pre-existing single-option cases, baselined as plausibly benign.
  - Six of the seven leave all 7 goldens byte-identical. Only `manifester.json` moves, because it
    carries a psion. The bard would have moved all seven — its picker draws from the RNG stream
    before checking whether the character is a bard — so that draw is kept deliberately.

### Added
- **Class choices are gated on every push, in two layers that deliberately share no code.**
  Class-choices ticket 05. Every class-specific pick — rogue talents, rage powers, aegis
  customizations, bloodlines, orders and the other 51 buckets — now has something that fails when
  it drifts.
  - **`Backend/scripts/gates/validate_class_choices.py`** (new, 506 checks, generates nothing)
    catches **config** drift: a rollable class with no schedule row, a row with no chooser call
    site, a call site with no row, a bad `reason`/`source` token, an empty verdict note, a dataset
    that resolves to no pool. Call sites are parsed with `ast` rather than a regex, because the
    bucket is `dict_name` when present and the chooser's own default when not — and that default
    differs per chooser. 51 call sites resolve against 51 rows, asserted in both directions.
  - **`check_class_choices` in `test_house_invariants.py`** catches **behaviour** drift: every
    rolled class holds `min(scheduled, |pool|, max_num)` picks per bucket, and every level stamp is
    one the schedule actually grants. It **costs no new generations** — it rides the sweep the file
    already runs, so the "coverage vs runtime" worry turned out to be free (3,637 → 3,724 checks).
  - **Why two layers and not one:** perturbing the schedule table and re-running the behaviour
    check *passes*, because the generator reads the same file — a table can never be its own
    witness. Config drift is the gate's job; behaviour drift is the sweep's. Neither imports
    `levels_for`; the gate re-reads the JSON and the check expands it a second time.
  - **The most valuable assertion is the cheapest:** a class that joins the rollable pool without a
    schedule row fails immediately, naming the class — so onboarding a new class cannot silently
    skip deciding what it picks.
  - The behaviour check skips 7 class/bucket pairs, each a named renderer-side defect, and
    **prints the skip count every run**; the gate fails if a skip outlives its stated cause.
  - **Two generations at 40th cover what 1,020 at 1–20 could not.** The first full sweep reported
    `0 capped by pool/max_num` — no cap bites at or below 20th, so two of the three terms in
    `min(scheduled, |pool|, max_num)` were never exercised. `check_choice_caps` generates a brawler
    (held to 8 by its call site's `max_num`) and a tactician (12 strategies exist, 13 scheduled) at
    40th, and a guard fails the run if nothing anywhere is capped. Adding levels 25 and 40 to the
    whole 68-class matrix would have tripled the sweep's runtime to cover two rows.

### Fixed
- **A gunslinger level no longer erases every other class's class features.**
  `choose_gun_func` ended `phase_class_options` with
  `data_dict.update({'class features': result})` — a straight assignment that replaced the whole
  bucket dict. Because it ran last, any character with a gunslinger level shipped **only**
  `gun training`: a dread/spiritualist/gunslinger lost its terrors and its emotional focus, a
  gunslinger/ninja lost its ninja tricks. The `class feature owners` side-table went on naming
  those buckets, so the payload advertised owners for buckets that no longer existed — the
  "generated but invisible" failure in its worst form, with the picks not merely unreachable but
  gone. Every other chooser carries a comment saying *merge, never assign*; this one did the
  opposite. Found by class-choices ticket 02's sweep.
  - `gun training` now records a bucket owner too, so it has a home on the Foundry sheet's Class
    Features tab instead of landing under no class.
  - A gunslinger 1–4 no longer emits an **empty** `gun training` bucket. Gun training starts at
    5th, and an empty bucket with an owner draws its own empty divider.
  - The category loop gained the pool-exhaustion break its siblings have. It filtered candidates
    *inside* `while len(chosen) < x`, so a firearms list with fewer useable categories than the
    count would spin forever — unreachable only while levels stopped at 20.
- **A multiclass ranger's favoured enemies and terrains were sized off the wrong class.** The
  counts came from `data.formulas`, whose strings read `character.c_class_level` — an alias of the
  **primary** class's level, not the ranger's. A ranger 3 / skald 13 received 3 favoured enemies
  and 3 favoured terrains where RAW grants 1 and 1. Now read per-class from the schedule table.

### Changed
- **The generator now states what it guarantees about a pick's legality — narrowly, and on
  purpose.** Class-choices ticket 03. It enforces prerequisites the string engine can evaluate
  (option names, class levels, ability/BAB/caster thresholds — 93.9% of the 4,883 comma-split
  prerequisite parts), no duplicates within a bucket, and no cross-bucket bleed. It **knowingly
  does not** enforce the other 6.1%: disjunctive prose (`"animal fury rage power or a natural bite
  attack"`), `"any two X"` counting, mutual exclusion and once-only, or buckets an archetype trades
  away. Measuring that tail at 6.1% is what settled the question — the choice looked like
  best-effort-versus-a-rules-engine only while nobody knew whether it was 5% or 50%. *Rejected:*
  structured prerequisites in the data, because the pools are **re-scraped**, so the parse and its
  review would recur forever.
  - **Under-delivery is legal exactly when the pool is provably dry** — the gate asserts
    `min(scheduled, |pool|, max_num)`. Of the three live under-deliveries, only the tactician's is
    real exhaustion; the brawler's is its own `max_num` cap and the oracle's is a bucket-naming
    defect, so a simpler "under-delivered ⇒ pool dry" rule would have been wrong twice out of three.
  - **A rage power cannot be unlocked by a rogue level.** `character.chooseable` stays shared
    across classes, now on measured rather than assumed grounds: the only pools naming a foreign
    class are ninja→rogue, slayer→rogue and skald→barbarian, and the gate fails if a fourth appears.
  - Found on the way: the scraper's field-glue bug also corrupts `prerequisites`, not just
    descriptions — one entry's prereq field has swallowed its benefit text.
- **The pick-schedule table is the whole story: five conventions, not three.** Class-choices
  ticket 01 migrated three count arithmetics into
  `Backend/json/class_choice_schedule.json`; ticket 02's sweep — generating a character for all 68
  rollable classes and asking which buckets actually landed — found **two more that no one had
  counted**, and both are now rows:
  - **The fourth**, `data.formulas` + `eval()` in `feats.formula_grabber`, read by
    `simple_list_chooser` (ranger favoured terrains/enemies, brawler maneuvers). `data.formulas` is
    **deleted**, not deprecated: a second schedule nobody reads is exactly the decay CLAUDE.md's
    stale-`critical` story warns about.
  - **The fifth**, an inline `floor((level - 1) / 4)` in `gunslinger.choose_gun_func`.
  - *Why reading the code missed them:* neither was reachable from `data.amount` or from the three
    known chooser call sites. Only generating characters found them. That is the sweep's real
    lesson, and it is why the gate ticket 05 builds must assert against **behaviour**, not only
    against config.
- **Single-pick class features now read their level from the table instead of a hardcoded `1`.**
  Bloodlines, orders, mysteries, curses, spirits, methods and the rest were stamped by a literal
  `1` inside `generic_class_option_chooser`, which made every single-pick bucket invisible to the
  schedule — so "a call site with no row" was silently correct rather than detectable. All 14 now
  declare `levels: [1]`. Behaviour is unchanged (all 7 goldens byte-identical); what changes is
  that the table is now the **complete inventory** of class choices, which is what lets ticket
  05's gate assert that every chooser call site has a row.
- **Per-use choices are rolled once and frozen.** A feature re-chosen at every use or every day has
  no home in a static snapshot. The medium's daily seance already worked this way as a one-off
  house ruling (§10); it is now the **general rule**, and the hunter's animal focus, the shifter's
  aspect and the omdura's invocation will follow it. *Rejected:* emitting the whole pool as a
  reference bucket — honest about the mechanic, but a new bucket kind both renderers would have to
  learn, and it would mean re-doing the medium to match.

### Removed
- **`gunslinger_deeds_dares.json` and `spirits.json`** — pools with no reader anywhere in
  `Backend/`. Gunslinger deeds are granted by level in RAW rather than chosen, so the file was
  never a missing chooser; `spirits.json` was superseded by `class_data/shaman.json`, which is
  where the shaman actually reads its spirits. `witch_patrons.json` is the third orphan and is
  **kept**: a witch's patron is a genuine 1st-level pick that nothing makes, so it is a logged gap
  rather than dead weight.

### Added
- **The web sheet's Companions tab now pre-fills from the generated character** *(sibling repo:
  `Pathfinder-Character-Sheet`)* — the last gate on the Companion Sheets map. A druid's rolled
  companion arrives with its HP/AC/saves, abilities, skills, attack lines and notes already in place,
  and stays fully hand-editable.
  - **Generated rows are seeded ONCE into the user's own array, then left alone.** `seedCompanions()`
    joins `seedBackendStatBonuses` / `seedRacialColumn` in `renderSheet`, guarded by its own
    `_sheet.companionsSeeded` flag — its own, not theirs, so characters saved before this feature
    still upgrade. It sits *above* the simple-view early return, so both view modes and
    `loadCharacter()` fill, not just a fresh generation. After that first render a generated
    companion is an *ordinary* companion: same model, same editors, same `×`.
  - *Rejected:* live-deriving the rows with a per-field override layer. It keeps generated numbers
    correct if the payload changes — but the payload never changes for a saved character, and the
    price is rewiring every editor plus designing a "reset to generated" affordance nobody asked for.
    *Rejected:* a read-only generated block above the editable list — cleanest provenance, but the
    player could not tick their own companion's HP down without copying it first.
  - **A player who hand-typed their bird may now see two rows.** That is correct and visible — both
    are editable and either has a `×`. Silently reconciling them would mean guessing which fields
    the player meant to keep.
  - **Entries that explain an ABSENCE render as a dim line, not a row** (*"Samurai — no mount: traded
    away by Warrior Poet."*). They are not creatures, so they must not become deletable rows, and
    they render straight from the payload every time. Skipping them was rejected: an empty tab cannot
    distinguish "the generator decided no companion" from "this is broken", which is the confusion
    that opened this work. An unrecognised `outcome` prints the token itself rather than vanishing.
  - **`merge_notes` is dropped and `unapplied` is kept**, deliberately: the first explains how a
    number was built, the second names something the generator *could not do*, which the player needs
    to know. `size_change` renders as a sentence and never as a modifier — its values are already
    inside `ac` / `attacks[].atk` / `cmb` / `cmd` / `skills`, so re-applying it would double-count.
  - Three widget changes came with it: **speed is free text** (the backend ships prose —
    `"10 ft. , fly 80 ft. (average)"` — and the second number is the one a bird's player needs),
    **CMB/CMD join the vitals strip**, and **a skills row** mirrors the abilities row with a 🎲 each.
    All three are backward-compatible with rows already saved.
  - The row takes the **bare** creature name, not Foundry's composed
    `<Master>'s animal companion: <Name>`: the tab heading, the type dropdown and the HD badge
    already say all three things. The two renderers differ here on purpose.
- **The payload shape is a declared manifest.** `Backend/utils/payload.py` owns `build_payload()`
  and `PAYLOAD_KEYS` — the exact 172-key order the FoundryVTT module and the web sheet read
  **positionally** — and `validate_payload_shape.py` fails when the built payload stops matching it.
  Previously that contract was the insertion order of a dict literal in the middle of a 2,700-line
  file, where inserting a key in the wrong place breaks nothing locally and breaks a character sheet
  in another repository.
  - **It found a live contract violation on its first run.** `class feature owners` was inserted
    only when some chooser happened to call `setdefault`, so a character with no class choices at
    all (fighter 1) shipped a payload **one key shorter than everyone else**. It is now seeded
    alongside its two siblings, so the shape never depends on the character.
  - That is a bug the goldens structurally could not catch: a golden says *this character did not
    change*, never *the contract is what we think it is*. The gate compares **two different**
    characters for exactly that reason, and has no `--update`.
  - `build_payload` **derives** rather than receives the ~15 values that are pure unpackings of
    character state (`armor_name` and its five siblings out of `character.armor_dict`, `deity_name`,
    `school`, `archetype_info`). Two pre-existing quirks are preserved deliberately and recorded in
    the module docstring rather than silently fixed: `shield_max_dex_bonus` reads `armor_dict`, and
    `armor_dict` is only bound on one branch. Fixing either is a behaviour change, not a move.
- **The feat budget is no longer allowed to be over-committed in silence** — `test_feat_budget.py`
  reports the arithmetic and names who over-drew. **It currently fails, deliberately**, on a real
  bug it found.
  - The `max(0, ...)` that reserves feat slots for Path of War, Spheres and professions was
    clamping a negative result to zero, so an over-committed character quietly ended up with fewer
    feats than the rules allow. The golden fixtures could never catch it: they record whatever the
    clamp produced, so a clamped character is "correct" forever.
  - **Instrumented before designing anything**, as ticket 08 asked: 70 classes x 5 levels x 2 seeds
    = 700 generations. The clamp fires in **16 of 700 (2.3%)**, **every one of them at level 1**,
    worst overdraft 2 feats. The sibling clamp on `normal_feat_amount` never fires at all.
  - The cause is a sizing mismatch, not a structural over-commit: a 1st-level budget is 7, and the
    homebrew subsystems ask for ~8 (typically 5 sphere feats + 3 profession feats). The subsystems
    are sized as though the budget were a mid-level one.
  - **That measurement is why there is no `FeatBudget` object.** A `reserve()`/`grant()` interface
    that refuses to go negative is real leverage, but inventing an interface for one value to
    prevent a bug confined to one level in 2.3% of runs costs more than it buys, and the map warns
    against exactly that. The arithmetic stays; the silence goes. If over-commits ever appear
    outside level 1, the gate says so in those words — and that is the evidence that promotes it.
- **`validate_alias_invariants.py`** — an alias was dropped because its writer runs once; this keeps
  that true. Two aliases had **identical shape and opposite verdicts**, and the discriminator is
  invisible at the alias site: `full_domain` was safe to drop because `domain_chooser` runs *once*,
  while `day_list`/`known_list` had to be kept because `sync_legacy_spell_fields` runs *twice*. The
  gate pins both call counts and fails either way they move — including the harmless direction,
  because a stale verdict is still a stale verdict.
  - The failure it prevents is silent and remote. Add a second `domain_chooser(character)` call and
    nothing breaks locally: the payload's `full_domain` just starts reporting the second roll
    instead of the first, on a character sheet, in another repository. The key is still present and
    still a list of domains, so no test, diff or exception would have said a word.
- **`validate_phase_contracts.py`** — the phase rules are now a gate, not a paragraph. It catches a
  `phase_*` function that lost its `@phase` decorator (it would keep working and stop checking
  anything), a value declared in both `provides` and `returns`, a `requires` list grown past four,
  and a phase that declares `returns` without building a `PhaseRecord`. The three phases that still
  return bare tuples are listed as named debt and warn rather than fail — a gate that fails the day
  it lands is a gate people disable.

### Removed
- **The dead `try/except NameError` handlers around the wizard school reads.** They were the
  non-wizard path back when `school`/`opposing_school` were conditionally-bound locals; once
  `phase_class_options` began seeding both attributes to `None`, an attribute lookup could only ever
  raise `AttributeError`, so the handlers were unreachable. They were deliberately left standing
  while that extraction was in flight — a pure move must not fold in a cleanup — and are removed now
  in their own commit, with the `if ... else "N/A"` carrying the non-wizard path exactly as before.

### Changed
- **Sphere talents now scale with level instead of being a flat 8, and nothing is free.** The flat 8
  was a testing convenience that handed a 1st-level character the same eight talents as a 20th —
  which is *why* the feat budget was over-committed at level 1. `test_feat_budget.py` is now green:
  **0 over-commits in 840 generations**, where it previously fired 16 times.
  - **The roll** (`spheres.roll_talent_budget`): under 5th rolls 0–8, under 10th 0–12, under 20th
    0–16, and 20th+ rolls 0–(level−4) so the curve keeps going instead of flattening. The low end is
    a real 0 — a dabbler who rolls nothing is a legitimate character.
  - **No freebies.** Every talent is paid for by a feat (HR1: one Extra-Talent feat = 2 talents; the
    first magic talent rides Basic Magic Training for 1) or by a Spheres Mentor. What neither can
    fund is **dropped, not granted**. Verified directly: 0 unpaid talents across 225 bundles.
  - **The three levers, in order.** What is left of the feat budget after Path of War and professions
    have taken their share; then, if that falls short and trainers are on, a **Spheres Mentor is
    forced** to cover the gap; if trainers are off the roll **halves** (no mentor can be conjured),
    and if feat taxing is off it halves **again** — both off quarters it. Measured at 20th level:
    6.9 talents → 3.6 (no trainers) → 3.4 (no taxing) → 1.6 (neither).
  - **The magic-side bonus feats are now rolled before the cap, not after.** They come out of the
    same budget, so rolling them afterwards meant the budget was sized for the talents alone and
    then quietly overspent. When the budget cannot carry both, the bonus feat goes and the talents
    stay — talents are the point of taking a sphere.
  - **Dropping a talent rebuilds the sheet items from the pick list**, not by filtering on name: the
    item carries a display-cased name and the pick the raw one, so a name filter silently kept
    talents nobody had paid for. That was caught by checking the invariant, not by reading.
  - **"Feat taxing" is read from `homebrew_feat_amount`**, the flag that actually governs the
    homebrew feat economy (creation/story/flavour feats). There is no separate feat-tax toggle in the
    code; if a distinct one is wanted, that is the line to change.
  - Golden fixtures re-baselined — a deliberate behaviour change, and the first on this map for which
    `--update` is the correct response rather than a failure signal.
- **A phase's outputs now have three declared homes, not one.** Extraction was heading toward
  `build_payload(character)` — the payload built from the character alone — and a runtime census
  priced it: the payload literal reads **98 function locals**, of which **88** would have to become
  character attributes, on an object that already carries ~200.
  - **Four of those names already exist on the character holding different values**, and three were
    invisible to reading. `character.feats` is the *pre-*`separate_feats_func` list;
  	`character.martial_disciplines` is the discipline data **table**, not the chosen list (the same
    shape as the known `character.deity` trap); `character.class_features` is not the `data_dict`
    slice the local holds; `character.archetype_info` is the dict whose `json.dumps` the local is.
    Repointing any of them by name would have shipped a wrong character.
  - So outputs sort three ways, by *who else needs this*: **character state** (`provides`),
    **derivable at export** (stored nowhere — `armor_name` and its five siblings come straight out
    of `character.armor_dict`), and **everything else** (a `PhaseRecord`, declared in `returns`).
  - **This reopens ticket 06's "positional soup" ruling, and narrows it.** That objection was
    against a 15-element *tuple*, and it was right about tuples. A record is not a tuple:
    `gear.weapon_name` names itself at the call site, cannot be mis-ordered, and is checked on the
    way out exactly as `provides` is. The rule is now positionality, not returning.
- **`generate_random_char` is 934 lines, down from 1,904** — every ordering-sensitive block in it is
  now a declared phase (15 of them), and the goldens stayed **byte-identical through every
  extraction**. The later blocks landed as records: `phase_path_of_war_and_spheres` alone hands back
  **32 values, not one of which is character state**, which is the clearest case the record rule
  makes for itself.
  - The two feat blocks are **not** adjacent (the class-features phase sits between them) and
    `feats`/`teamwork_feats` are re-bound across them, so the records are **unpacked at the call
    site** rather than repointed downstream — 97 references left untouched instead of rewritten.
  - **`validate_phase_contracts.py` caught a modelling error in one of these extractions**:
    `phase_feat_selection` had declared `feats` in *both* `provides` and `returns`. It is character
    state (choosers and `no_prereq_loop` read `character.feats`), and the local is only an alias.
    The gate written earlier in the same session is what found it.
- **Three more blocks are declared pipeline phases**, golden payloads byte-identical throughout:
  `phase_gear_and_equipment` (the kit and the purse — eleven outputs cross out of it and *every one*
  is read only by the export, which is what proved the record), `phase_appearance_and_traits` (seven
  flavour rolls, and the first phase that puts **nothing** on the character), and
  `phase_class_bonus_feats` (the feats a class grants, before any are chosen).
  - The appearance phase's hazard is one no attribute could express: `language_chooser` is *handed*
    the skill ranks, so running it early picks languages against an empty rank sheet without raising.
    Requiring `skill_rank_budget` — which only the professions phase sets — is what forces the order.
  - The class-bonus-feats hazard hides itself: run before `character.bloodline` is resolved, the
    bonus list comes back empty and the phase's own refund converts every unfilled slot into an
    ordinary feat, so the character ends with the right feat **count** and the wrong feats.
- **Every class-specific choice is now a declared pipeline phase.** `phase_class_options` covers
  schools, archetypes, bloodlines, domains, bonded creatures and the thirty-odd option buckets.
  Golden payloads unchanged.
  - It was expected to be the twenty-plus-`requires` case and it needs **four**. The block reads a
    great deal, but nearly all of it is state the block itself produced a few lines earlier; only
    the prerequisite-seeding state (ability scores, BAB, caster level) and one write-after-write
    genuinely cross in.
  - **That write-after-write is the pipeline's only one, and it is now a contract.**
    `favored_class_calculator` does `character.Total_HP += character.level`, so letting the HP phase
    run afterwards would *overwrite* the favoured-class bonus rather than lose it loudly.
  - **A local here was conditionally bound, and the export site knew it** — the wizard school is
    only assigned for wizards, which is why the export reads it inside a `try/except NameError`. An
    attribute cannot raise `NameError`, so it is seeded to `None` to keep the non-wizard path
    landing on "N/A" exactly as before. Those handlers are now provably dead; they are left standing
    because deleting them is a cleanup, not a move.
  - **Three locals turned out to be dead**, including one — the favoured-class list — with no reader
    anywhere in the repo.
- **Hit points and the per-class spellbooks are now a declared pipeline phase.**
  `phase_hp_and_spellbooks` declares that it needs the finished ability scores, because
  `total_hp_calc` reads the *final* Con score — running it before the stats phase never raised, it
  just gave every character the hit points of a Con-10 one. Golden payloads unchanged.
  - Nothing crosses out of this block: all three names that used to leave it were already aliases of
    character attributes. Zero new attributes; the export now names the attribute rather than the
    alias.
  - **Those aliases were only safe to drop because it was measured, not assumed.** The legacy spell
    scalars are re-pointed a *second* time much later, after the spell lists are deduped — so an
    alias captured early and an attribute read at export are two different reads, and a rebinding in
    between would have made the substitution a silent payload change. Asserted equal at the export
    site across 68 classes at three levels, with the probe first confirmed able to fire.
- **The alignment / body / flaw / personality / level block is now a declared pipeline phase.**
  `phase_alignment_and_level` covers everything rolled off a finished identity but before any levels
  are spent, and it declares what it needs (`region`, `chosen_race`, `_class_picks`) and what it
  produces. Nothing in that block would have *crashed* out of order — each mis-ordering produced a
  quietly different NPC, which is exactly why the ordering had to become a contract rather than a
  comment. The generated character is unchanged: all seven golden payloads are byte-identical with
  no fixture edits.
  - The level roll belongs to this phase rather than one of its own, because `flaw_amount` crosses
    from the flaw roll straight into `update_level`'s feat economy and nowhere else. Splitting them
    would have promoted a local into an exported attribute to serve exactly one reader.
  - **Three near-misses, each of which would have been a silent wrong-character bug.** The two
    alignment strings are *not* interchangeable — `choose_alignment` stores the lowercased form
    because the deity table is keyed that way, while the payload exports the title-cased one, so
    both now have their own name. `character.deity` was already taken by the deity *data table*
    keyed by alignment, so the chosen deity keeps its existing home at `character.deity_choice`;
    giving it an attribute named `deity` would have overwritten the table and broken domain
    selection. And the block's `professions` roll was overwritten 240 lines later by
    `phase_professions_and_skills`, which returns *trainer* professions — two unrelated things
    sharing one name.
  - **That third one turned out to be dead code that cannot be deleted.** Nothing had ever read the
    personality-flavour profession list; every downstream reader was reading the trainer list that
    replaced it. The call still has to run, because it draws from the shared RNG and removing it
    would shift every later roll and change the character. Dropping the flavour list is a behaviour
    change and belongs with the class-choices work, not with a pure move.
- **The level-40 ceiling is now a named rule with a test behind it, instead of a bare `40` nobody
  guarded.** The ceiling itself already worked — `randomize_level` has always clamped, and asking
  for level 999 has always produced a level-40 character — but it was an unexplained literal in one
  function, and *nothing anywhere asserted it*. Because the clamp is silent rather than an error, a
  regression would have shipped level-60 characters rather than failing. It is now
  `level_and_bab.MAX_CHARACTER_LEVEL`, imported by the sweep rather than restated in it.
  - Every swept character is checked against it, plus the invariant that would actually rot: the
    total is capped in `randomize_level` but divided across classes in `_split_levels`, so a
    character whose class levels do not sum to its total would satisfy the cap and still be wrong.
  - A dedicated check asks for levels 41, 60 and 999 and requires exactly 40 back, multiclassed so
    the split is exercised. **Verified by breaking it:** with the clamp removed the suite reports
    the over-ceiling total, the failed clamp, and a level-344 dread. The sweep's own levels all sit
    under the ceiling, so without this the assertions would have passed vacuously forever.
  - Requests above the ceiling are still **clamped, not rejected** — the caller is asking for a
    random character, not a specific one.

### Fixed
- **A character above 20th level stopped gaining nine kinds of class option, while still gaining
  the others.** Above 20th the game is homebrew, and the house ruling is that a level-30 character
  goes on picking rogue talents, rage powers and aegis customizations at their class's own cadence —
  only *spells* stop, because there is no 10th-level spell. The code already modelled that: spells
  and maneuvers read `capped_level` (`min(level, 20)`), class choices read the uncapped class level.
  But nine schedules had been scraped as finite lists that happened to stop at 19th or 20th, so an
  aegis 30 quietly received 10 customizations instead of 15 while a rogue 30 correctly received 15
  talents. The truncations were an artifact of how the tables were harvested, never a ruling, and
  they are gone.
  - Schedules whose gaps are **deliberate** keep them past 20th rather than filling them in: the
    shaman's missing 6th and 14th levels are wandering hexes, a separate feature. Bounded features
    do **not** continue, and are now distinguishable from truncated ones — the warpriest's two
    blessings and the occultist's *"maximum of seven implement schools"* are caps the classes state,
    not lists that ran out.
- **Fixed a hang that could freeze character generation outright.** `generic_class_option_chooser`
  advanced its loop only on a *distinct* pick, with no check for the option pool running dry — so a
  class owed more picks than its pool holds would spin forever rather than take what exists. It was
  unreachable only because every schedule stopped at 20th; removing those caps made it reachable
  immediately (an occultist 40 is owed 12 implements and only eight schools of magic exist). The
  loop now stops when the pool is exhausted, which is what its sibling `choosing_talents` has always
  done. **Found by running the generator above 20th for the first time** — no fixture and no sweep
  had ever gone past 18th, so the entire 21–40 band was unexercised.
- **Magi were getting 10 arcana where the rules grant 6, and investigators 10 talents where the
  rules grant 9 — with the wrong "gained at" level on every one of them.** Neither number was ever
  chosen by anyone: both call sites omitted the `divisor` argument and inherited the default of 2,
  so a magus picked one arcanum every 2 levels instead of every 3. A magus 4 shipped **two** arcana
  stamped "gained at 2" and "gained at 4"; it now ships **one**, stamped 3, which is what a 4th-level
  magus has. The investigator's talents now land on odd levels (3rd, 5th, 7th…) as the rules say,
  instead of even.
  - The stamps were wrong *because* the counts were: both were derived from the same divisor in two
    separate places. Fixing the schedule fixes both at once — see the entry below, which made that
    structurally true before this change was attempted.
  - **Only these two.** Every other schedule that disagrees with the rulebook was authored by a
    human on purpose or has not been checked against Sieg's Guide yet — the aegis's customization
    approximation, the warpriest's and inquisitor's doubled 1st-level picks, the witch's missing
    1st-level hex. Those are marked `unverified` in the table and deliberately left alone.
    *Rejected alternative:* fixing everything that disagrees with RAW, which would have quietly
    overwritten house rulings nobody wrote down.
  - **One golden fixture moved, `companion.json`, and it was recording the bug.** 116 of its 172
    keys are unchanged; the 56 that differ are everything drawn *after* the arcana chooser, because
    one fewer random pick shifts the shared RNG stream. The class composition, stats, saves and HP
    are identical.

### Changed
- **Every class's pick schedule — how many rogue talents, rage powers, arcana or hexes a character
  gets, and at which levels — now lives in one place: `Backend/json/class_choice_schedule.json`.**
  It used to live in three, and they disagreed. `data.amount` held explicit level lists for 13
  classes; `get_data_without_prerequisites` computed `floor(level / divisor)`; `generic_multi_chooser`
  computed `floor((level - start) / divisor) + 1`. A single resolver, `generic_func.levels_for()`,
  now answers for all of them, and the arithmetic is deleted from the choosers. **No behaviour
  changed** — this is the first of two steps, and the second one carries the fixes.
  - **The three conventions were nested in generality, not redundant**, which is why this was a bug
    factory rather than untidiness. The divisor form can only say "every N levels starting at N".
    The investigator's schedule is *3rd, then every 2* — unreachable in that form — so it silently
    delivered 10 talents instead of 9 **and** stamped them on even levels instead of odd. One
    missing degree of freedom, two visible symptoms. A table entry now declares either a compact
    `{start, every, until}` rule or an explicit `levels[]` list, so both are sayable.
  - **The level stamp and the pick count now come from one source.** They were derived twice from
    the same formula in two different functions, so a wrong count was always also a wrong "gained
    at" on the sheet. The k-th pick's level is simply `levels[k-1]`, which makes that class of bug
    unrepresentable rather than merely fixed. `_record_choice_level`'s docstring claimed it recorded
    a *character* level; every caller has always passed a *class* level, and class level is correct
    — it is what lets a rogue 4 / magus 6 draw on each class's own progression.
  - **`until` is load-bearing, not tidiness.** Class levels reach 40 (`level_and_bab.py:19`) and
    nine of these schedules stop at 19 or 20, so an unbounded `{start, every}` rule would have handed
    a level-30 aegis 15 customizations instead of 10. Found by checking, not by reading.
  - **`data.amount` is deleted, not left in place**, and its three remaining readers (the psionics
    and occult invariants, the occult gate) now read the new table through `_harness.schedule_levels`
    — a *second* implementation of the expansion, deliberately not `levels_for`, so a check cannot
    confirm the generator against itself. A schedule table that nothing reads is how the original
    one drifted. *Rejected alternative:* keeping `data.amount` and syncing the two.
  - Dead knobs removed rather than ignored: `divisor`/`odd` on `get_data_without_prerequisites` and
    `n2`/`start_level` on `generic_multi_chooser` no longer exist, because a parameter a caller can
    still set while nothing reads it is how a schedule change silently does nothing.
  - Verified by replaying the old arithmetic from git across **1,360 bucket × level pairs at levels
    1–40** (count and stamps identical), 7/7 golden payloads byte-identical, and 30,553 house
    invariants across all 68 classes.
  - Decisions and rejected alternatives:
    [class-choices ticket 01](https://github.com/The-Data-is-a-lie/tickets/blob/main/tks/pathfinder-char-creator/feature/class-choices/01-pick-schedule-authority.md).

### Fixed
- **Sorcerers, oracles, psychics and arcanists were shipping the text `null` where a spell-slot
  count belongs — at roughly half of all class levels.** PF1e spontaneous full casters gain each new
  spell level one class level *later* than a prepared caster of the same tier: a sorcerer reaches
  2nd-level spells at 4, a wizard at 3. `caster_formula` modelled only the prepared progression, so
  `spells_per_day_attr` looped one spell level too far and read a cell the scrape had correctly left
  blank — and these tables spell "blank" as the **string** `'null'`, not JSON null. A level-3
  sorcerer's spells-per-day row was literally `[0, 5, 'null']`, and that string reached the payload,
  the Foundry sheet and the web sheet. `adept` was wrong for a different reason: an NPC class with
  its own 1/4/8/12/16 ladder, mapped onto the closest tier that existed, wrong by up to three levels
  and handed a 6th-level row it can never reach. Both progressions are now modelled.
  - The rule lives in the **code**, as a named constant, not derived from the tables. *Rejected
    alternative:* reading the unlock level straight out of `spells_per_day.json`, which needs no
    hand-maintained list and was the tempting option. It would have made
    `validate_progression_tables.py` compare the data against itself — a scraper error would silently
    become the character's behaviour with no second opinion. The gate's whole value is that the data
    and the code are two independent statements of one published table. Verified across all 30
    tables: those four lag by exactly 1 at every spell level, and no other class does.
  - **No golden fixture moved, and that is the finding.** None of the seven covers a spontaneous
    full caster at a divergent level, so the bug was invisible to them. The invariant is asserted
    over the whole swept roster in `test_house_invariants.py` instead — every `spells_per_day_list`
    entry must be a number — which also catches the next class to acquire a bespoke progression.
    Confirmed by reverting the fix: the sweep then fails for arcanist, oracle and psychic at both
    levels 3 and 17.
- **The magus 5th-level spells-per-day column was one row late at high levels.** It granted 4 slots
  at level 20 while the magus's own 6th-level column granted 5 — which no PF1e caster does. Checked
  against Archive of Nethys: the published row is 1/2/3/3/4/4/**5/5** at class levels 13–20, and the
  scrape had 1/2/3/3/4/4/4/4 with the 5 pushed onto the unreachable 21st row. Two cells corrected.
  - **Left unfixed on purpose:** the same source says the magus *4th-level* column should read 3 at
    level 12 and 5 at 18, where the scrape has 2 and 4 — the same off-by-one, in a column no
    structural rule catches because it never inverts against its neighbours. The evidence is one
    LLM-extracted table, and hand-editing game data on that basis is how you introduce a silent
    wrong-character bug while fixing another. It needs a re-scrape against the source.
  - Both exemption blocks in `validate_progression_tables.py` are **deleted**, which is what the
    gate demanded: it fails if an allowance outlives the bug it excused. It now reports 423 columns,
    **30/30 classes aligned** with `caster_formula` and **30/30 per-day tables free of inversion**,
    with nothing excused.

- **One Path of War maneuver was called "Solar Flare maneuver" and never matched anything.** The
  scrape recorded the Solar Wind strike's key as `Solar_Flare_maneuver`, so that suffix travelled all
  the way into `maneuvers_choose_from` and `maneuvers_desc_dict` — the only name in the repo carrying
  it, while its own siblings Solar Reflection and Dazzling Solar Flare were clean. The cost was not
  cosmetic: the FoundryVTT module matches maneuvers against the `pf1-pow` compendium by that name,
  folding case, apostrophes and whitespace but not a trailing word, so Solar Flare missed its
  document and arrived synthesized — no automation, no discipline, no `(Strike)` prefix. The module's
  curated conditional key had been hand-patched to the artifact to compensate; both sides now use the
  real name. *Rejected:* teaching the module to strip a trailing `" maneuver"`, which would have made
  the consumer absorb a defect in the producer's data and hidden the next one.
- **FoundryVTT module — five defects the new golden harness found before anyone reported them.**
  Recorded here because this changelog is the stack's decision log, not just the backend's. A
  companion's AC was a point low whenever a feat granted one (feat automation is stripped because the
  payload already counted it, and AC is the one folded stat pf1 gives no seed to write the difference
  back into — so AC-targeted changes are now kept, and only those; *rejected:* keeping natural armour
  too, which **does** have a seed and would double). Twelve `pf1-pow` maneuvers carry a
  double-encoded apostrophe in their compendium names and silently arrived with no automation at all.
  Seventeen stances were labelled `(Boost)` by the pack while their own buff said `(Stance)` — our
  stance list now outranks the pack. Synthesized psionic powers were missing
  `uses.autoDeductChargesCost` and so were free to manifest. And every character carried two token
  effects both named "Inherent", because re-identifying a buff item never reached the ActiveEffect
  inside it. *Rejected throughout:* re-recording a golden to accept a diff without reading it — which
  is how the Solar Flare conditional above was nearly lost for a second time.
- **Seven build and curation scripts had been dying with `ModuleNotFoundError`.** Filing the
  validators and tests into `gates/` and `tests/` moved modules that seven other scripts import
  (`build_companion_archetypes`, `build_talent_conditionals`, `enrich_conditional_riders`,
  `promote_conditional_candidates`, `promote_talent_conditionals`, `prune_talent_conditionals`,
  `sweep_buff_gaps`), and none of them imported `_harness` — the thing that puts the buckets on
  `sys.path`. The check that closed that work was `compileall`, which proves a file parses and never
  once imports it. All seven now route through `_harness` and run again.

### Changed
- **A Redis outage can no longer take the API down with it.** `flask-limiter`'s `swallow_errors`
  defaults to **False**, and the Redis URL is resolved once at import by a single ping — so a Redis
  that was reachable at boot and died later (a managed instance restarting, a network blip, free-tier
  maintenance) would raise out of the storage layer on *every* rate-limited request, and
  `/update_character_data` would return 500 until someone redeployed. The generator would have been
  fine; the limiter would have been taking the API down with it. Now `swallow_errors=True` plus
  `in_memory_fallback_enabled=True`, so a storage failure degrades to per-process counting and
  characters keep generating. Verified by pointing the limiter at a dead Redis and confirming the
  route still answers 200. This mattered only once a real Redis instance was configured — with
  `memory://` there was nothing to fail.

- **A third pipeline phase is extracted: `phase_bootstrap_identity`** — gender, region, race, name
  and class selection now declare what they set instead of being 30 loose lines at the top of a
  1,900-line function. Generated characters are byte-identical (7/7 goldens), and
  `test_pipeline_phases.py` gained cases for it.
  - Its `requires` is **empty**, and that is the correct declaration rather than a stub: it is the
    first phase, so nothing can cross in. All its guard value is in `provides`, which is checked on
    the way out — `region` is set *inside* `region_chooser` and `c_class` inside `chooseClass`,
    never returned, and those invisible writes are exactly what goes missing unnoticed.
  - **The seam is one line lower than it looked.** A phase takes the character as its first argument
    and checks `requires` against it, so the phase cannot be the thing that *creates* the character.
    Construction stays at the call site.
  - **The second candidate block was measured and deliberately not extracted.** 15 locals cross out
    of it (`flaw` alone has 14 later references), so returning them would be a 15-value tuple — the
    same silent-miscount failure as the `export_list_dict` helpers already deleted from
    `createACharacter.py`. The remaining phases must write to the character and declare via
    `provides` instead; but only 5 of those 13 names are on the character today, so that work is
    ~8 new attributes plus rewriting ~60 references, not a move. Recorded so the next pass is
    scoped from a measurement rather than from a reading.

- **`Backend/scripts/` has buckets: the 21 gates now live in `gates/`, the 11 tests in `tests/`.**
  81 files sat under one name that told you nothing about what any of them was, and the prefix was
  the only signal. The two runners stay at the top level because they are what you *run*, not what
  gets run, and `golden/` did not move because `_harness.GOLDEN_DIR` owns that path. Both runners'
  globs now point at their bucket; the counts are unchanged (21 gates, 11 tests), which is the check
  that matters — a move that drops a script produces a *smaller passing run*, which reads as success.
  - **Only half the split landed, deliberately.** The plan assumed the earlier harness work had made
    this "a deletion, not a recalculation". That holds for gates and tests, which were migrated. It
    is false for the other 43 files — the builders and one-off fixits never imported `_harness` and
    still compute the repo root from their own nesting depth. One level down, `parents[2]` would
    point at `Backend/` instead of the repo root and read the *wrong file* rather than raising, which
    is precisely the silent failure the marker-based resolver exists to prevent. Moving them is
    blocked on finishing that migration; *rejected alternative:* bumping each `parents[2]` to
    `parents[3]`, which would have been quick and would have re-encoded directory depth in 37 files —
    undoing the thing the resolver was written to achieve, and breaking them all again on the next move.
  - Five gates and one test were still computing their own paths and would have broken silently:
    four companion gates via `HERE.parents[1]`, three more via `os.path.join(HERE, '..', 'json')`,
    and `test_golden_payload.py` — which computed its own `GOLDEN_DIR`, the very constant the harness
    was supposed to own. All now take `REPO` / `JSON_DIR` / `BACKEND` / `GOLDEN_DIR` from `_harness`.
  - `_harness` puts `gates/` and `tests/` on `sys.path` as well, because several gates are also
    libraries imported across buckets (`validate_talent_conditionals.is_cost_only` has five callers,
    one of them a test). Adding a bucket means adding it there and nowhere else.
  - **The other half landed too, and the 43 files were converted first.** `build/` (34) holds
    anything you run to *produce or maintain* generated or curated data — the builders and scrapers,
    the `promote_*`/`prune_*`/`enrich_*` conditional-curation chain, the audits, and both
    sub-toolkits; `attic/` (9) holds only the self-described one-offs. Ticket 03's prefix rule left
    ten scripts in neither, and filing a maintained curation tool under *"kept for the record, not
    maintained"* would have been a lie about it. *Rejected:* a third bucket, which would have reopened
    a settled decision for ten files.
  - **Verified by measurement, not by reading the diff.** Every module-level path constant of all 50
    scripts was captured by importing each in a subprocess before the move and again after: 134
    values identical, and every changed value accounted for by an intended move. That is what caught
    the one real bug — `_pow_generator/` and `_spheres_generator/` went a level deeper too, so
    `build_pow_template_actor`'s own `parents[2]` quietly became `Backend/` instead of the repo root
    and doubled `Backend/Backend/` into fourteen data paths. Nothing in a code review would have
    shown that.
  - Two more of the plan's claims failed on contact. **`.gitignore` did need changing** — five of its
    eight `Backend/scripts/` paths name things that move in this half. And **the buckets are not
    independent**: `build/build_companion_archetypes.py` imports `attic/repair_animal_choices`, which
    is the one edge saying the attic is not yet archaeology.

### Added
- **A gate for the shape of the scripts directory itself.** `gates/validate_scripts_layout.py` fails
  on a `validate_*.py` outside `gates/` or a `test_*.py` outside `tests/`, and checks that both
  runners' globs still match a non-empty set — a glob that silently matches nothing is the exact
  failure `validate_all.py` exists to prevent, and a PASS over zero scripts looks like success. The
  argument for it is this directory's own history: the naming convention was *also* only a
  convention, and `check_racial_stats.py` went years without ever running because nothing checked
  that it held.
  - It reported the 43 unmoved scripts as **one counted line**, not 43 warnings. Forty-three
    near-identical warnings about a known backlog is not information — it is the noise that teaches
    people to stop reading a gate's output, which is the same failure as a gate nobody runs. Now that
    the backlog is empty those two warnings are **errors**: the next runnable file to appear at the
    top level is the pile reforming, not the tail of something already ticketed.
  - It also fails on **anything at the top level that computes a path from its own nesting depth**.
    That is the defect the second half of the split was blocked on, and it fails *silently* —
    `parents[2]` one level down points at `Backend/` and reads the wrong file rather than raising —
    so it earns a check rather than a sentence. Negative-tested against a file carrying both faults.

### Removed
- **The server-side session is gone.** Every request wrote the whole generated character to
  `session['character_data']` and read it back on the very next line — a local variable wearing a
  session's clothes, inherited from `app_Backup_Working.py`. None of the four routes ever read it
  across requests, and both consumers (the FoundryVTT module and the standalone web sheet) keep the
  payload themselves. The cost was a full serialisation of the payload to disk or Redis on every
  request — 40 KB for a level-5 rogue, more at high level — for a 60-second lifetime nobody queried,
  plus a `Secure; SameSite=None` cookie on every response. 87 stale session files had accumulated
  locally. Responses now carry no `Set-Cookie` at all.
  - **Redis stays**, and this is what it is for: rate limiting. `memory://` storage counts per
    *worker*, so under `gunicorn -w 4` the declared 60/minute is really 240/minute. That — not
    session storage — is the argument for provisioning an instance. *Rejected alternative:* keeping
    the session because "sessions are standard for a Flask app". This backend is a stateless JSON
    API; the payload's `generation_seed` already replays any character exactly, which is a cheaper
    handle than storing the result.
- **The production image no longer ships a Jupyter notebook stack.** `requirements-docker.txt` was a
  byte-for-byte copy of `requirements.txt`, so the deployed container installed `ipython`,
  `ipykernel`, `jupyter_client`, `jupyter_core`, `debugpy`, `pyzmq`, `tornado`, `traitlets`, `jedi`,
  `parso`, `prompt-toolkit`, `stack-data`, `matplotlib-inline`, `nest-asyncio`, `comm` and `psutil`,
  plus the scraper stack (`beautifulsoup4`, `requests` and their transitive deps) that only
  `Backend/scripts/scrape_*.py` needs, plus four junk packages that do nothing at all (`ceiling`,
  `floor`, `jsonify`, `flask_abort` — accidental installs, not the standard-library names they look
  like). None of it is imported: after `import app; import main_test` and five full generations, the
  only module that arrives lazily is pandas. **The image went from 714 MB to 602 MB.** On Render's
  free tier the image is pulled on every cold start, which is the one place this actually costs
  something. `requirements.txt` keeps the full set, because CI installs it to run the scrapers and
  the gates.
  - `waitress` is deliberately kept despite nothing importing it — `usage_counter.py`'s docstring
    claims production serves under waitress via a `render.yaml` that does not exist in this repo,
    and a Docker Command override in the Render dashboard isn't visible from the code. Dropping it
    on that assumption would take the service down. The stale docstring is the bug; it is flagged in
    `requirements-docker.txt` rather than guessed at.

### Added
- **A new gate checks what is actually inside the level progression tables, not just that they
  exist.** Around 423 columns across four webscraped files answer "what do you get at class level
  N?" — spells per day, spells known, power points, maneuvers. The existing caster gate only checked
  that a class *had* a row. A single shifted cell inside one was invisible: it doesn't raise, and it
  only reaches a golden fixture if that exact class at that exact level happens to be seeded. On a
  character sheet it looks like someone who simply has one fewer spell slot than they should.
  `validate_progression_tables.py` checks table length, gaps, direction, and that no caster has more
  high-level slots than low-level ones — and cross-checks every column's unlock level against
  `caster_formula` by *running* it, so the data and the code are two independent statements of one
  published table rather than one number nobody recomputes.
  - It found two real bugs on its first run, both recorded and neither fixed here, because fixing
    either changes generated characters and this branch was a refactor: **spontaneous casters
    (sorcerer, oracle, psychic, arcanist) ship the string `'null'` as a spells-per-day count** at
    around half of all levels, because `caster_formula` only models the prepared-caster progression
    and reads one spell level too far; and the **magus's 5th-level column looks shifted one row
    late**. Both are carried as itemised exemptions that name their reason, and the gate fails if an
    exemption is ever left behind after the bug it excuses is fixed — an allowance that can't be
    retired is how "temporary" becomes documentation.
- **Every regression test now runs in CI, including the golden-payload fixtures.** There were eleven
  `test_*.py` scripts in `Backend/scripts/` and CI ran exactly one of them. The expensive omission
  was `test_golden_payload.py` — seven seeded characters with every payload key diffed byte for byte,
  which is the only thing that can prove a refactor didn't quietly change a character. A new
  `test_all.py` discovers the family by glob, exactly as `validate_all.py` already did for the data
  gates, and both now run on every push. The whole suite is about 25 seconds.
  - **A trimmed run says it was trimmed.** The full-roster sweeps are slow (the unabridged invariant
    sweep is 825 generations), so `test_all.py` trims them by default and prints a `NOTE:` naming
    what it shortened. `--full` runs everything; do that before a release. A suite that quietly
    tests less than it appears to is the same failure as a gate nobody runs.
- **`check_racial_stats.py` was renamed to `validate_racial_stats.py` — and started running for the
  first time.** It checks all 25 playable races against their stat entries, and it had never once
  been executed by `validate_all.py`, purely because its name didn't match the `validate_*` glob. It
  passes, and always would have; nobody was looking. The gate count went from 18 to 19. This is the
  cost of glob discovery: it makes the naming convention load-bearing wiring rather than a style
  preference.

- **The class dropdown is grouped, and it finally lists every class you can roll.** The FoundryVTT
  generator dialog now shows five labelled sections with their sizes — Paizo base classes (40),
  Path of War (5), Psionics (12), Occult Adventures (6), NPC classes (5) — and each section opens
  with a **Random \<group\>** entry that rolls only inside that family. Picking "Random Occult
  Adventures" gets you one of the six occult classes and nothing else.
  - **The six Occult Adventures classes were missing from the dropdown entirely.** They entered the
    random pool on 2026-08-03 and the Foundry module could already render them, but nobody added
    them to the list, so the only way to get an occultist was to roll Random and hope. Fixed, and
    gated so it cannot happen again — see the roster note under *Changed*.
- **Seven more classes, all of them first-party Paizo: the generator now rolls 68.** Every class on
  d20pfsrd's index is present except prestige classes.
  - **The five NPC classes — adept, aristocrat, commoner, expert, warrior.** An NPC generator that
    could not produce a commoner was missing the most common person in the world; a town guard had
    to be a fighter and an innkeeper a bard. They are **fully rollable**, not selector-only: about
    7% of random characters are now NPC-class. *Rejected:* listing them but holding them out of the
    random pool. If that proves wrong in play, the lever is one list in `data.py`.
  - **The omdura and the vampire hunter**, the last two first-party base classes, with their full
    feature chains (12 and 15 features).
  - Their chassis is **read out of the pf1 compendium, not typed from the book** — hit die, BAB,
    skill ranks, saves, class skills and proficiencies all come from the class Items, and
    `build_npc_class_data.py` refuses to write if `data.py`'s hand-maintained good-save table
    disagrees with the pack.
  - **Prestige classes are deliberately excluded.** 100+ classes needing an entry-prerequisite
    engine and base-class-level gating that the generator has no model for, for characters nobody
    asked to roll.
  - **The omdura and the vampire hunter cast, and the adept does too.** RAW gives all three divine
    spellcasting. The omdura is a six-level Charisma caster reading the cleric spell list; the
    vampire hunter a four-level Wisdom caster reading the inquisitor list, its first spells at 4th.
    Neither needed a new spell list written: the generator has always been able to point one class
    at another's list, which is how the warpriest and the oracle read the cleric's. Their
    per-day tables are the standard six- and four-level progressions every other class of that
    shape already uses.
    - Their compendium class Items carry no casting information at all, so the tier is asserted in
      `build_collab_class_data.py` — and the build now **fails** if the upstream pack ever ships
      casting information of its own, rather than quietly preferring a hand-written answer to a
      real one.
    - **Remaining gap, and it is small:** the omdura's list is RAW the union of the cleric's and
      the inquisitor's, and no such list has ever been written down. It reads the cleric's, which
      contains everything an omdura can reach. *Rejected:* deriving the union as a new column.
    - **A 16th-level-or-higher adept sees one spell slot on the Foundry sheet it cannot fill, and
      that is allowed to stand.** The adept's spells stop at 5th level; the backend enforces that
      and the web sheet shows it, but the Foundry sheet works its slots out from the caster tier
      rather than from the numbers the generator sends, and offers a 6th. *Rejected:* having the
      generator's own spell table drive the Foundry sheet instead. It would fix this, but it would
      also put the generator in charge of every caster's slots at once — thirty classes' worth of
      arithmetic that pf1 has been doing correctly — to correct one empty row on the rarest kind of
      character in the game. Not worth the blast radius. If it is ever revisited, the trap is
      written down in `build_npc_class_data.py`.

- **Animal companions and mounts build like characters now.** A bonded creature used to arrive as a
  stat block and a list of feat names picked at random out of a bag. It now chooses feats it actually
  qualifies for, records which level each one came from, pays feat taxes, rolls its own mechanical
  flaws, and reaches a Foundry sheet with the same dividers, tracker groups and basic buffs a player
  character gets. Spec: `docs/feature_spec_todo.md` §8 **D14/D15/D16**.
  - **Feats are labelled like class bonus feats** — `Animal Companion 5: Weapon Focus`, beside a
    PC's `Fighter 1: Weapon Focus`. The number is the effective level at which that slot opened,
    read off the chassis table's own `feats` column, which also anchors the feat-tax cadence.
    *Rejected:* labelling by HD, and by species.
  - **The 27-name feat pool was canonicalised and gated.** It held a dozen lowercase spellings and
    one entry, `armor proficiency (light, medium, and heavy)`, that is not a feat in either
    `data/feats.csv` or the pf1 compendium — so it could never resolve, and the module would have
    attached a bare item with no rules text. It is now 29 canonical names, and picks are checked
    against the creature's own ability scores and BAB one at a time, so a chain can build itself
    (Dodge → Mobility → Spring Attack) and a Str 6 body cannot take Power Attack.
  - **Feat tax runs, behind a curated allowlist.** The pool's feats open **128** distinct chain
    children, and a prerequisite reader cannot refuse most of them — *Drunken Brawler*, *Wand
    Dancer*, *Sword and Pistol* and *Arcane Armor Training* all have prerequisites an animal
    genuinely meets. `tax_children` in `animal_companion.json` is the 23 that suit a body, each one
    verified reachable and grantable. *Rejected:* confining tax to the pool, which would have fired
    exactly once (`endurance → diehard`); and trusting the prerequisite reader alone.
  - **A new animal flaw catalogue** (`Backend/json/flaws/animal_flaw_effects.json`, 12 minor / 10
    major: Skittish, Gun-Shy, Old Wound, One-Eyed, Lame, Ill-Tempered …) on the PC's own ladder —
    1st minor, 2nd major, 80/20 thereafter — buying bonus feats on the same diminishing scale.
    *Rejected:* filtering the PC's 44 down to the animal-safe ones; about eight survive, so every
    companion would have repeated the same flaws.
  - **Feat and flaw effects are folded into the payload's numbers, and the sheet is told not to
    re-apply them.** `stats.applied_changes` records every fold with its source, so a companion's HP
    can be explained rather than just trusted, and the Foundry module strips `system.changes` off
    every feat and flaw item. Buffs take the opposite rule: they keep their changes and ship
    **inactive**, because they are situational and nothing counted them. *Rejected:* letting pf1
    derive from intact changes — the standalone web sheet has no game system, so it would have been
    wrong by exactly the feat bonuses.
- **The six Occult Adventures classes generate.** `occultist`, `kineticist`, `medium`, `mesmerist`,
  `psychic` and `spiritualist` are now in the default random pool — they had been filtered out since
  the generator was written. Each one makes its own class choices, and the five casters get a
  psychic-magic spellbook. Spec: `docs/feature_spec_todo.md` §10.
  - **They were held out for a reason that turned out not to apply to them.** A compendium census
    (`docs/wayfinder/class-pool/issues/01`) found all six fully present in the installed `pf1`
    11.11 — class Item, features *and* choice pools. The renderer objection that the list was built
    around is real only for the Path of War stalker and zealot, which `pf1-pow` 1.6.4 genuinely does
    not ship; those two stay pending, now with a named blocker instead of a bare list entry.
  - **The option pools are harvested, not authored.** `Backend/scripts/build_occult_class_data.py`
    reads the Foundry compendia and writes 449 options into `Backend/json/class_data/<class>.json`.
    *Rejected:* scraping d20pfsrd / Archive of Nethys. §8's familiar work had found `pf-content` too
    thin to generate from, so this was checked rather than assumed — and this time the packs are
    complete, because the class Item's `classAssociations` gives an exact granted-vs-selectable split
    instead of a guess. Re-run the script after any pf1 or `pf-content` update.
  - **Spell progressions are derived from pf1's own `casterProgression` tables**, read out of the
    system's sourcemap. *Rejected:* typing the tables from the book. The derived occultist row
    reproduces the repo's existing `bard` row exactly and the psychic row reproduces `sorcerer` in
    both files — two independently-authored sources agreeing, which a hand-typed table could not
    give. It also means the payload and the Foundry sheet cannot disagree about spell counts.
  - **Two of the six degrade rather than being held back**, reusing §8's eidolon ruling. The
    **kineticist's burn** is named and described but not tracked — it is an HP-priced resource with
    no analogue in the generator. The **medium's spirit** is rolled once and frozen; the spirit is a
    *daily* choice and the generator emits a static snapshot, so this is a house ruling and is
    recorded as one. *Rejected:* holding both classes out until their subsystems could be modelled.
  - **Eleven new `class features` buckets reach the Foundry sheet**, all registered in the module's
    `CLASS_FEATURE_BUCKETS`. For the kineticist those buckets are the entire sheet, so an
    unregistered one would have left the class looking empty — the "generated but invisible" failure
    the psionics work already hit once.
  - **The same eleven buckets are named on the standalone web sheet**, which had been falling back to
    a prettified key (`Medium Spirit`, `Bold Stare`) with no "(Chosen)" tag. They now carry the
    module's labels verbatim, so the two sheets name the same pick the same way. *Rejected:* a
    dedicated Occult tab beside Path of War and Psionics — six classes run six different engines with
    little in common, and unlike power points or maneuvers none of them needs a tracker the Class
    Features tab cannot already show.
- **Psionics generates.** All twelve Dreamscarred Press psionic classes — aegis, cryptic, dread,
  highlord, marksman, psion, psychic warrior, soulknife, tactician, vitalist, voyager, wilder — are
  now ordinary entries in `Backend/json/class_data.json` and roll in the default random pool with no
  request flag, so roughly a fifth of random NPCs are manifesters. Each generated manifester carries
  a manifester level, power points, a legal power selection and its class subsystem picks.
  - **The payload gained a `manifesters` list** (one entry per psionic class, beside `spellbooks`)
    and a sibling `powers_desc_dict`, mirroring how the Path of War block and `maneuvers_desc_dict`
    already sit together. Consumers that ignore the new keys are unaffected.
  - **"Manifester" is modelled as three shapes, not one**, because the classes genuinely differ: the
    ten full manifesters get power points *and* powers; the **aegis** gets power points and no
    powers (it spends them on astral-suit customizations); the **soulknife** manifests nothing at
    all. All three still emit an entry — a class silently missing from the payload is
    indistinguishable from a bug.
  - **Nine class subsystems ride the existing chooser** rather than new code — aegis customizations,
    cryptic insights, vitalist methods, psychic warrior paths, marksman styles, tactician strategies,
    dread terrors, highlord decrees, soulknife blade skills. The **soulknife's mind blade** is the
    one exception: it is a weapon, not a list, so it is synthesized with the enhancement bonus from
    the class table.
  - **Power selection has no prerequisite machinery**, unlike Path of War maneuvers, because psionic
    powers have no prerequisites. The psion's discipline is picked first and decides its whole power
    list; every other class takes a soft bias toward 2–3 disciplines so a build reads as a concept
    rather than a grab bag.
  - Power points are a table *plus* a formula — the class table at manifester level plus
    `floor(key ability modifier × manifester level / 2)`, with a hard gate that a key ability of 9
    or lower cannot manifest at all. *Rejected:* tabulating the bonus-power-point table, which is
    only that expression written out.
  - **The manifesting ability lives in `class_data.json`** as a `manifesting_stat` key beside
    `main_stat`. *Rejected:* a separate map in `data.py` (the shape ticket 04 originally settled on)
    — the class entry already exists and already carries the class's other key ability, so one row
    owning both beats two places that can drift. It stays distinct from `main_stat` because the
    questions differ: a psychic warrior manifests off Wisdom but plays off Strength.
- **Psionic characters now show their psionics on both sheets.** Generation already picked the
  powers; nothing downstream rendered them. A manifester imported into Foundry arrived with no
  Psionics tab at all, and the only way to reveal one was to add a psionics class to the manifester
  book by hand. Both front ends now build themselves from the payload.
  - **The FoundryVTT module fills the `pf1-psionics` manifester books** (module repo,
    `scripts/modify-abilities.js`). `pf1-psionics` gates its entire Psionics tab on a single flag —
    whether any manifester book is marked in use — and reads nothing else: not a class item, not a
    class tag, not a power. Writing that flag per manifesting class *is* the fix. Powers become real
    `pf1-psionics.power` items, cloned from the module's own compendium where the name matches and
    synthesized from `powers_desc_dict` where it does not, the same way Path of War maneuvers
    already resolve. Misses are expected, not a defect: a measured 67 of the powers are
    Metzofitz-only content that exists in no compendium.
  - **Power points stay the module's to compute**, because its published tables and ours are the
    same twenty numbers and `validate_psionics_data.py` asserts exactly that on every run. The
    generator seeds the *current* pool instead, so a rolled NPC arrives rested. *Rejected:* pinning
    our number into the book's formula, which would have two owners for one fact.
  - **With `pf1-psionics` absent, powers become feat items** plus a per-class power-point pool,
    mirroring the Path of War fallback. *Rejected:* skipping psionics entirely, which would import a
    manifester with no trace of what it can do.
  - **The standalone web sheet gained a Psionics tab**, beside Path of War: manifester level,
    manifesting ability, max power level, discipline, an editable power-point tracker with a Rest
    button, and powers grouped into collapsible per-level blocks. Non-manifesters see an empty
    state, and the soulknife — which manifests nothing — is correctly not one.
  - **The payload gained two fields the renderers could not derive.** `caster_type` on each
    manifester entry is the low/med/high progression the Foundry book needs, derived by matching the
    class's own power-point column against the published tables rather than hand-maintained in a
    second map. `powers_by_level` names which power sits at which level: `psionic_powers.json` keys
    a power's level by power *list* ("psion/wilder"), not by class, so the level a psion learns a
    power at survives nowhere else. `powers_known_list` is now counted from those buckets, so the
    two views cannot disagree.
  - **A `manifester` golden payload** (seeded psion 8 / aegis 6) pins power selection for the first
    time — the other six goldens all carry `manifesters: []`. One character covers two of the three
    manifester shapes, including the points-but-no-powers aegis that a naive renderer drops.
- **The Open Game License artifacts that psionics obliges.** Serving extracted game mechanics over
  HTTP is Distribution under section 10, so the licence now ships with them: a root
  `LICENSE-OGL.txt`, an Open Game Content notice marking the psionics data subtree (and marking the
  Python as *not* Open Game Content), a `GET /license` endpoint serving the licence as plain text,
  and a `license_url` pointer on every generated payload — absolute when served over HTTP, since the
  Foundry module may surface it long after the request. *Rejected:* embedding the licence in each
  payload, which would add ~10 KB of legal text to every character and dwarf several blocks that are
  actually about the character.
  - Section 15 is **curated from our own sources** by `Backend/scripts/build_ogl_license.py` rather
    than inherited: upstream's omits *Ultimate Psionics* and *Psionics Expanded* while carrying Path
    of War lines copy-pasted from an unrelated module. The build **warns** about copyright lines it
    has not verified against the published work instead of dropping them — omitting a source is the
    worse failure.
- **`Backend/scripts/test_psionics_sweep.py` — a per-class psionics table.** The house-invariant
  sweep answers "did anything break" across every class and prints pass or fail; this answers "is
  *each* psionic class right", one row per class per level, in a table you can read. It exists
  because the defect that prompted it was invisible to a pass/fail gate: the aegis and soulknife
  generated their subsystem picks correctly and put them somewhere no renderer looked, so every
  assertion passed while the sheet stayed empty. Columns cover powers known, free talents, the
  ability-capped max power level, power points and caster type, whether the subsystem bucket
  actually holds the picks due at that level, whether every emitted power carries rules text, and —
  the one that makes "it shows up in Foundry" testable without launching Foundry — whether every
  emitted name is one `pf1-psionics` will keep rather than silently drop.
- **`test_house_invariants.py` now checks psionics** on every generated character, so all twelve
  classes are swept at levels 1/5/10/15/20 alongside the rest. It asserts that the `manifesters`
  block names exactly the character's psionic classes, that power points equal the published table
  plus the ability formula, that powers-known and max power level match the table, that the two
  views of the same powers (`powers_chosen` and `powers_known_list`) agree, that no power is emitted
  without rules text, and that every payload carries its `license_url`. The tables are read straight
  from the data file rather than through `psionics.py`, so the test can catch the generator
  disagreeing with its source instead of agreeing with it by construction.
- **The bonded-creature design is settled and written down** as **§8 Bonded creatures** in
  `docs/feature_spec_todo.md`, closing six of the seven tickets on `docs/wayfinder/companions/` and
  marking that map CLOSED. Nothing generates yet — this is the contract implementation is built
  against. Today the generator gives a companion to druids only, computes none of its numbers, never
  applies the species' advancement block, and emits it on a payload key **nothing reads**; summoners
  roll with no eidolon at all. What was decided:
  - **One payload, several actors.** A generated character stays a single character; the FoundryVTT
    module creates one extra actor per bonded creature in the existing "Random Characters" folder,
    so a druid 5 / wizard 5 imports as three actors — the character, a companion and a familiar.
    *Rejected:* folding the creature into the owner's own sheet as items, and describing it in sheet
    text only; a companion has its own AC, saves, HP and attacks, and both alternatives either fight
    Foundry's derived data or throw those numbers away.
  - **The generator computes every number; Foundry supplies the body.** The payload carries a
    finished stat block, and the module clones the matching creature out of the `pf-content`
    compendium for art, natural attacks and senses, then patches the numbers over it. *Rejected:*
    letting the Foundry system derive the stat block — the standalone web sheet has no game system
    to derive anything with, so that would have left it with an empty companion block and two
    consumers disagreeing about the same creature.
  - **A missing creature degrades loudly instead of vanishing.** An unmatched species still produces
    a plain actor built from the payload numbers, plus a warning, and a validator gates species
    names against a checked-in dump of the compendium. *Rejected:* a curated name map, which would
    have quietly shrunk the species pool to whatever happened to match.
  - **v1 covers animal companions, mounts and familiars with full stat blocks; the eidolon is
    deliberately partial** — a named base form and descriptive text, with its evolutions deferred.
    *Rejected:* removing summoner from the random class pool until evolutions exist. A summoner has
    spells, class features, gear and a named eidolon; a partial summoner beats no summoner in a
    campaign that has to be table-ready.
  - **The single `animal_companion` payload key becomes a `bonded_creatures` list**, because one
    character can legitimately have several. The old key is kept as a deprecated alias to the first
    animal companion so existing readers keep working.
  - **Who grants a companion becomes a data table** rather than the hard-coded druid check, covering
    13 classes plus the Spheres *Beastmastery* talent. Multiple sources stack and the total is capped
    at character level; a class below the level where its feature arrives grants **nothing** rather
    than a level-1 creature.
  - **Three grantors in the design notes turned out not to be grantors**, caught by checking each
    against the published rules: the **shifter** has no animal companion at all, the **antipaladin**'s
    fiendish servant is a permanent *summon monster* rather than a companion (deferred as a separate
    subsystem), and the **sorcerer** only qualifies through the Arcane bloodline. The paladin's mount
    question left over from earlier research is settled too — it uses the paladin's own level, not
    level − 3, from 5th.
  - **The companion species data has to be repaired before any of this can be used.** Of 120
    advancement rows recording a Dexterity change, **109 lost their minus sign** during the original
    scrape; applied as written, every advanced companion would gain +4 Dexterity it should not have
    — a wrong AC, Reflex save and initiative on every one of them. Sixteen rows in the same situation
    kept their `-2`, which is what proves it. The repair is scripted and guarded by a validator
    rather than hand-edited.
- **The psionics design is settled and written down** as **§9 Psionics** in
  `docs/feature_spec_todo.md`, closing seven of the nine open tickets on
  `docs/wayfinder/psionics/`. Nothing generates yet — this is the contract implementation is built
  against. The decisions that shape everything downstream:
  - **The backend computes manifester level, power points and powers-known and emits them as
    finished numbers**, even though the `pf1-psionics` Foundry module can calculate all three
    itself. *Rejected:* emitting bare selections and deferring to the module — that would leave the
    standalone web sheet (which has no game system) unable to render a manifester, make the payload
    non-self-describing, and give `test_house_invariants.py` nothing to assert on. The duplicate-math
    objection does not apply: our scraped power-point columns already match the module's own tables
    exactly, so the two agree by construction.
  - **The twelve classes enter the random pool with no opt-in flag**, following Path of War rather
    than Spheres of Power. *Rejected:* a `psionics` request flag — Spheres needs one because it
    *replaces* casting, whereas psionics is additive, and a flag would cost plumbing in three places
    across two repos to buy a switch nobody asked for. **Visible consequence:** psionic classes
    become about 12 of 55 pool entries, so roughly a fifth of default random NPCs will be psionic.
    Reversible in one line via a new `psionic_classes_pending` holdback list.
  - **All twelve classes ship, subsystems included.** Nine of them carry a bespoke subsystem
    (astral suits, insights, collectives, terrors, decrees, blade skills…), and all nine turn out to
    be the same shape as bloodlines and orders — so they reuse the existing class-option chooser
    rather than gaining new modules. The soulknife's mind blade is the sole exception and becomes a
    synthesized weapon. *Rejected:* holding the soulknife back, and letting the data decide which
    classes ship — a class held back would be recorded with the reason, but it is meant to be an
    exception rather than the plan.
  - **Power selection has no prerequisite logic**, unlike Path of War maneuvers: psionic powers have
    no prerequisites at all, so only class list, power level and discipline gate a pick.
  - **Every name the generator emits is reconciled against the module's compendium before it ships,**
    and the validator fails on any unmapped name. The module silently drops names it does not
    recognise — the same failure that once cost six weapons their conditionals — and its packs turn
    out to mix two different apostrophe characters internally.
  - **Psionic races are deferred**, and that ticket is re-scoped into the route for *all* homebrew
    races (Loxo, Kalyptran, Dolistani included), because the race files are walked positionally and
    that problem should be solved once rather than per-supplement.
  - **The scraped class tables were checked against the published rules and hold up** — eleven of the
    twelve match exactly, including the three that looked wrong at a glance. The one genuine
    difference is the **psychic warrior**, which in this campaign has a good Fortitude save only
    where the published class has both Fortitude and Will, and an entirely rewritten feature track.
    That is a deliberate house rule, now recorded as one, so nobody "corrects" it later.
- **The psionics scrape now separates class features from page furniture.** Headings like
  "Archetypes", "Favored Class Bonuses" and the power-point tables were being captured as though they
  were selectable class features, which would have offered a generated character "Archetypes" as a
  class ability. Weapon and armour proficiency is promoted to its own field, the archetype lists are
  kept as lists, the manifesting rules text is kept separately (it is where each class's manifesting
  ability is stated), and the favored-class sections are dropped since the generator does not model
  them. Each class now also records its **manifesting ability**, declared from the published rules
  and checked against the class's own prose so a future edit that disagrees warns rather than drifts.
  Wiki category links no longer leak into descriptions, and multi-variant power pages no longer carry
  stray bold markup in their variant names.
  - Open Game Content obligations are **decided** too — nothing is built yet: an OGL notice with a
    §15 curated from our own sources rather than copied from upstream's (which is incomplete),
    per-subtree marking of which files are Open Game Content, and a `/license` endpoint so API
    responses can point at the licence instead of embedding it. (The artifacts themselves land
    further up this Unreleased section.)
- **A psionics master data resource, scraped from the Library of Metzofitz wiki.** Two new scripts —
  `Backend/scripts/scrape_psionics.py` and `Backend/scripts/validate_psionics_data.py` — produce and
  gate five files under `Backend/json/class_data/psionics/`: the twelve in-scope classes with real
  BAB / hit die / skill points / good saves and 20-row power-point, powers-known and
  maximum-power-level progressions; twelve class power lists plus the seven psion disciplines; 615
  powers with full header fields and rules text; and the ten *Psionics Unleashed* races from
  d20pfsrd. Nothing is wired into the generator yet — no class enters the random pool, and the
  payload is unchanged — because the payload shape and the power-selection algorithm are still open
  questions on `docs/wayfinder/psionics/`.
  - **Confidence comes from two sources agreeing.** All eleven manifesting classes' power-points
    columns match, exactly, one of the three progressions the `pf1-psionics` Foundry module
    hardcodes in `scripts/data/powerpoints.mjs` — 220 independently-authored numbers in agreement.
    The validator hardcodes those progressions and asserts the match on every run, so a future
    scrape regression fails loudly rather than silently shipping wrong class tables.
  - Recorded as facts about the source, not defects: three power names on class lists are red links
    (`Detect Compulsion`, `Manifest Veil`, `Mind Trap`), `Restore Essence` is missing most of its
    header fields, the Noral race page has no speed line, and 29 pages hold multi-variant power
    chains whose extra variants are noted but not yet modelled.
- **The twelve psionic classes are selectable in the Foundry generator dialog**, instead of only
  being reachable by rolling Random. `Psychic Warrior` sends the slug `psychic-warrior` and the
  backend turns the hyphen back into its space-separated key, the same path the Unchained variants
  already take, so no new normalisation was needed.
  - **Psionic characters now land complete on the Foundry sheet.** Previously a generated
    manifester arrived with no class item at all (`Class item Aegis not found in actor's items.`):
    the module does not build class items, it copies them out of `every_class.json`, a snapshot of
    the `everyClassPerson` actor that no psionic class had ever been dragged onto. All twelve
    classes and their 145 class features are now in both the standard and `_MODS` bundles.
- **`Backend/scripts/build_every_class.mjs` harvests 3pp classes from their compendium packs**,
  replacing a by-hand GUI ritual with a repeatable command. It reads the `pf1-psionics` LevelDB
  packs directly, resolves each class's `classAssociations` to its feature items, and splices
  class-then-features blocks into both `every_class.json` and `every_class_MODS.json`. Re-running is
  byte-identical, so a rebuild produces an empty diff rather than churning 900 ids.
  - **Foundry may stay open.** LevelDB is single-writer and a running Foundry holds the lock, so
    each pack is copied to a temp dir and the copy is read. *Rejected:* requiring the user to close
    Foundry, which is what made the old export macro a chore.
  - It deliberately does **not** replace `tools/export_every_class.macro.js`. Regenerating all 49
    already-working classes to fix 12 missing ones risks regressing the 49.
  - The twelve names were also added to `class_list` in `modify-abilities.js`. This is load-bearing,
    not cosmetic: a class present in the bundle but absent from that list does not act as a
    collection boundary, so the *preceding* class silently absorbs its items.
  - **Stalker and Zealot remain unavailable, and are a different problem than they appear.** They
    are not missing from the harvest — they are absent from upstream `pf1-pow` entirely, which ships
    only Mystic, Warder, Medic, Warlord and Harbinger. They stay in `pow_classes_pending_foundry`
    and out of the dropdown. The build script lists them anyway, so the day upstream ships them,
    re-running it is the whole fix.
- **`Backend/scripts/validate_name_data.py`** guards the two hand-authored name files, which had no
  validator and no generator standing between a bad edit and every NPC being called `Stefan rling`.
  Checks structure, region parity between the two files, and that every name is a non-empty,
  uppercase-initial, untrimmed-whitespace string. Duplicates are reported but **not** fatal:
  Sojoria's surname list deliberately concatenates male-patronymic, female-patronymic and root-stem
  sections, so repeats are intentional and erroring on them would mean 85 false failures.
  - The docstring states plainly what it **cannot** catch: a stripped diacritic is only detectable
    when it ate a leading capital (`rling`), never mid-word (`Lindstrm`). A guard trusted further
    than it earns is worse than one with a documented ceiling.
- **Bonded creatures have names, and a stated position on gear.** A companion, mount or familiar
  that exists now carries a **name** drawn from its master's region pool and a rolled **sex**, so a
  druid's wolf arrives as "Cédric" rather than as a second row labelled *Wolf*. Both sit on the
  entry beside the species; nothing composes them into a label, because the Foundry module and the
  web sheet each want a different one (spec §8 D2).
  - **The name reuses `first_names_regions.json`** — the same ten region pools the PC draws from —
    so it costs no new data and reads as regionally flavoured. *Rejected:* a curated animal-name
    list (new curation, which the road-to-1.0 plan defers) and species-as-label.
  - **The name never collides with the master's**, and **`species` is left strictly alone** because
    it is the only key the Foundry module matches a `pf-content` Actor on. A name that leaked into
    the match key would make every named companion miss its clone and silently degrade to a bare
    stat block — the failure mode that already bit spell conditionals.
  - **The sex is rolled per creature.** *Rejected:* reusing the master's, which would have made
    every companion the same sex as its owner 100% of the time.
  - **A companion owns nothing yet, and now says so**: `gear: []` plus a `gear_source` note that
    records *both* the absence and that the gear will be bought from `character.gold` when it
    arrives (Pathfinder gives companions no wealth-by-level, so the master pays). The point is that
    the emptiness is a stated fact a later ticket fills, not a field nobody noticed was missing.
    *Rejected:* modelling a mount's tack now, which drags barding's AC math into this release; and
    saying nothing at all, which is how the question would have been answered by omission.
    ⚠ When gear does land, characters generated from the same seed will make **different** armour
    and weapon purchases, because the money now has a competing claim on it.
  - **An entry that records an absence stays empty**: a lost coin flip or an archetype that removes
    the bond yields `name: None`, `sex: None` and no gear key at all. *Rejected:* one uniform key
    set with nulls everywhere, which ships a null-named, empty-geared creature for renderers to draw.
  - **The deprecated `animal_companion` payload key is frozen** at its five existing fields and
    gains none of this. *Rejected:* mirroring the new fields onto it — a deprecated key that is
    never worse than its replacement is never migrated away from, and the name is the only reason
    the sheet would ever move to `bonded_creatures`.
  - **`Backend/scripts/validate_companion_identity.py`** holds all of the above, including the rule
    that the sample must actually *reach* both a granted and an absent entry before it may report
    success. The generated payload cannot carry these fields until `bonded_creatures` ships, so
    without this the rules would have existed only as sentences in a spec.
  - Companions of masters from **Tal-falko** and **Kaeru no Tochi** would have come out nameless:
    the region a character carries is title-cased while the name-file keys are not, so two of the
    ten regions never matched. The new name lookup resolves the region case-insensitively.
- **Bonded creatures have numbers.** A druid's wolf now has HP, AC, touch and flat-footed AC, saves,
  BAB, CMB/CMD, ability scores, size, speed, parsed attack lines and spent skill ranks — everything a
  sheet needs to be worth opening. The block is computed by merging the species' published
  advancement into its base stats; nothing reads it yet (the payload key is the next change).
  - **A companion that grows no longer gets its size increase twice.** The published per-species
    advancement numbers already fold the size change in — the proof is that a Dexterity *penalty*
    appears on all 153 size-increasing rows and on none of the other 43, and growing is the only
    thing in Pathfinder that lowers Dexterity. So those numbers are applied **exactly as printed**,
    and the size table supplies only what the data provably lacks: the size modifiers to AC, attack,
    CMB/CMD, Stealth and space. Without this a grizzly bear would have come out four points of
    Strength too strong. *Rejected:* subtracting the size table back out of the published numbers —
    27 species would have been left with a *negative* Strength residue, describing a bear that never
    existed at any point in its life.
  - **Where the size change came from is recorded, and marked as already counted.** The stat block
    says a creature grew Medium → Large and what that contributed, purely so a sheet can explain a
    number. A renderer that applies it a second time is the one way to reintroduce the double-count,
    so the record says so in its own text and again in the payload comment.
  - **A companion that was *born* Small gets its +1 too.** The size modifiers key off the creature's
    final size rather than off the step it took, which is a case the original framing of the problem
    missed entirely.
  - **The house rules that apply to dice carry over; the ones shaped like a class do not.** A
    companion gets maximised hit points, exactly as the character does. It does **not** get the
    2-to-4 skill-rank floor, because that rule floors a *class's* ranks-per-level and an animal has
    no class — its rank total is a single published number. The per-skill cap is likewise the
    standard Pathfinder one. This is the same line already drawn for companion feats.
  - **Attack routines stored as prose become real attack lines** — `"bite (1d8 plus trip)"` becomes a
    line at full attack bonus with the damage, the Strength bonus and the rider separated out,
    including Pathfinder's one-and-a-half Strength for a creature with a single natural attack
    (rounded down, which an obvious `round(x * 1.5)` gets wrong at odd modifiers). **357 of the 358
    routines parse**; the one that does not is an octopus's *tentacles (grab)*, which genuinely has
    no damage die. Getting there meant handling the awkward eighth of the file rather than the tidy
    majority: eight routines put commas *inside* the parentheses, four omit the parentheses entirely,
    several offer an *"X or Y"* alternative that is not a second attack, and the axe beak spells the
    one-and-a-half-Strength rule out in words. A companion whose bite shows no damage is a visibly
    broken sheet, so the count is asserted rather than assumed.
  - **Skill ranks go where an animal would actually put them**: Perception first, then the rest of
    its permitted list, and never into Fly or Swim for a creature with no such speed. **A mindless
    companion gets none at all** — 24 species (the vermin and most of the plants) have no
    Intelligence score, and Pathfinder says such a creature cannot hold skill ranks. The companion
    table still offers it a rank total, because that table was written for animals; spending it would
    have put Perception ranks on a slug.
  - **A companion's dice never disturb the character's.** The one random choice in a stat block draws
    from its own generator seeded off the creature's identity, so adding companion skills does not
    shift every roll made later in generation — otherwise a wolf's Stealth ranks would have quietly
    changed its master's feats, gear and backstory.
  - **Nothing the merge produces is dropped.** One-off species abilities that no stat field
    enumerates — *sudden charge*, *stampede*, *ink cloud*, and 28 others — survive in their own
    bucket. The spec had called for the merged block to replace the raw one on the entry; it cannot,
    because the frozen `animal_companion` alias reads the same object and its consumer would have
    silently changed underneath it.
  - **Two things are carried but explicitly not applied**, rather than implied: the 17 archetypes
    that alter a companion's progression describe it only in prose, so the entry reports them as
    unapplied; and reach is omitted because it depends on whether a body is tall or long, which the
    data never says.
  - **`Backend/scripts/validate_companion_stats.py`** checks all 392 stat blocks and would fail on
    447 counts if the double-count were reintroduced. It also asserts that the published numbers
    still *disagree* with the size table in at least 30 places — otherwise the check could quietly
    become vacuous if the data ever moved.
- **The payload finally carries them.** A new `bonded_creatures` list on every payload carries one
  entry per creature — companion, mount, familiar, eidolon — each with the stat block above,
  including the entries that exist only to explain why there *isn't* one. The five-key
  `animal_companion` alias is unchanged, so nothing reading it has to move.
  - **The stacking golden had stopped testing stacking.** Its seed was chosen to roll two companion
    grantors at once, but the region fix realigned the random stream and it quietly became a single
    ordinary druid. Re-seeded to a case that stacks **three** grantors — hunter, ranger and druid —
    which also exercises three different effective-level formulas at once.
- **The invariant sweep now watches companions too**, covering what only a whole generated character
  can show: the emitted shape, that an absence entry carries no stats, that the hit dice agree with
  the post-stack chassis, that a size change is recorded exactly when the creature grew, and the
  **druid flip** — a druid takes a companion or a domain, never both and never neither.
  - **The sweep fails if it never produced a bonded creature at all.** It counts the branches it
    reached, so a run cannot report success having asserted nothing — the failure mode that let the
    stacking golden go quiet. 15,560 checks across 825 generations: 55 granted, 39 absences,
    15 druid flips.
- **A companion will get its own character sheet, and the route there is charted.** A new design
  effort, `docs/wayfinder/companion-sheets/`, takes bonded creatures from *specified* to *on screen*:
  a druid's wolf becomes a second sheet titled *"Ophir's animal companion: Cédric"*, not a row of
  data on its master's.
  - **Foundry and the web sheet get different shapes, deliberately** (spec §8 **D10**). In Foundry
    each creature is a separate Actor, as already planned. On the standalone web sheet it instead
    **fills in the Companions tab you currently type by hand**. *Rejected:* a second character in the
    web sheet's roster — that sheet exports as one JSON file, and splitting a companion out of it
    would break the portability the tab was built to protect.
  - **Neither renderer is handed a ready-made title.** The backend keeps emitting plain facts — the
    creature's name, its type, the master's name — and each renderer writes its own heading.
    *Rejected:* a single title field on the payload, which would have forced one phrasing onto two
    surfaces that word things differently.
  - **The numbers came first.** The advancement merge and stat-block math landed before any sheet, so
    the first companion sheet anyone opens shows real HP, AC, saves and attacks. *Rejected:* shipping
    a sheet early from the level-chassis row alone — a page of placeholder numbers looks finished and
    teaches nobody anything.
  - **Two questions were genuinely open at charting**, each blocking one renderer: whether Foundry's
    Pathfinder system honours numbers patched onto a compendium creature or quietly recomputes over
    them, and what happens to companion details you have edited by hand when the same character is
    imported again. Both have since been answered — see the two entries below.
  - Two documents were **wrong and are now right**: the spec's "current state" and the codebase map
    both still described the companion code as druid-only, which stopped being true when the grantor
    table landed.
  - **The Foundry half now has a recipe, and it starts by deleting something.** Every one of the 205
    creature Actors the module clones from ships two hidden items that re-apply the companion
    advancement table — so patching a generated companion's ability scores over the clone would have
    made every one of them stronger than the rules allow, the same double-count the size package
    already sprang once. Handing the job to Foundry instead is not the way out: its formula raises
    Strength, Dexterity and natural armour a level early, at 3rd, 6th, 9th and every third level
    after. The module deletes those two items and drives the creature's hit dice instead, which is
    the number Foundry derives HP, attack bonus and saves from — and the table it uses to do that is
    the same table the generator read.
- **The Foundry module builds the companion sheets** (module repo, `scripts/createCompanions.js`).
  One Actor per bonded creature in the Random Characters folder, body cloned from `pf-content`,
  numbers written from `stats`, absences logged rather than dropped, and a species with no
  compendium body built from the payload alone. The module's own changelog carries the
  reader-facing version.
  - **The recipe's numbers were verified before Foundry ever ran them.** A headless harness
    (`tools/test_create_companions.mjs`, re-runnable against any payload) stubs the parts of pf1 the
    file touches and replays the `companion` golden through it: the cloned
    body's class item driven at the creature's **hit dice** reproduces the payload's HP, BAB, saves
    and AC with **zero corrections**. That is ticket 02's central claim tested rather than asserted.
  - **The correction pass stays anyway.** It diffs what pf1 derived against what the backend said
    and writes the remainder into the stored seeds pf1 accumulates on top, so a world with different
    health rules — or a familiar that does not advance like an animal — still lands on the payload's
    numbers. What it cannot correct, it names.
  - **The skill-name map moved to its own file** (`scripts/skills-dict.js`), because the companion
    renderer spends ranks through the same table the character does and the map already carries the
    scar of having drifted once. ⚠ `modify-abilities.js` still holds an identical copy — it was
    being edited by other work at the time — so the deletion there is pending and both the file
    header and the codebase map say so.
- **The web sheet's Companions tab will fill itself in, and your edits are safe.** The tab you
  currently type by hand gets one pre-filled block per bonded creature — HP, AC, saves, abilities,
  attacks, skills, the lot — and the design for it is settled
  (`docs/wayfinder/companion-sheets/` ticket 03). The tab is still yours: a filled-in companion is an
  ordinary row you can rename, edit or delete like any other.
  - **The clobber everyone was worried about cannot happen.** Rolling a character always creates a
    *new* entry in your library rather than overwriting one, so a generated companion can never
    arrive on top of one you have edited. Re-opening a character you exported restores exactly what
    you saved, edits included.
  - **Characters already in your library get filled in too**, not just newly rolled ones — the fill
    runs once per character, the first time its sheet is drawn. If you had already typed your druid's
    bird by hand you will end up with two rows and can delete either. *Rejected:* guessing which of
    the two you meant to keep.
  - **A companion you were never given is explained rather than omitted.** A druid who rolled a
    domain instead of a bird, or a bond an archetype traded away, shows a one-line note — *"Druid —
    no animal companion: chose a domain instead."* — instead of an empty tab that looks broken.
    *Rejected:* skipping those entries silently, which is the confusion that started this effort.
  - **Speed becomes free text, and skills and CMB/CMD get their own line.** A bird companion's speed
    is *"10 ft., fly 80 ft. (average)"* and no single number can hold that; skill totals and CMB/CMD
    are things you roll at the table, so they get real widgets rather than being buried in the notes
    box. Everything else the generator computes — feats, special abilities, size, bonus tricks — is
    written into the notes.
  - **The block is titled with the companion's plain name**, not *"Ophir's animal companion:
    Cédric"*. Foundry keeps the long form because there the companion is a separate sheet that needs
    the context; here the tab heading and the type dropdown already supply it. *Rejected:* one
    phrasing across both surfaces.
- **Two more design efforts are charted, and both wait their turn.** `docs/wayfinder/class-pool/`
  asks which classes should be rollable at all, and `docs/wayfinder/class-choices/` asks whether the
  ones that are rollable pick their class options correctly. Neither is worked until the
  bonded-creature system is finished and we are happy with it — that gate is written into both maps.
  - **Six classes you cannot currently roll are Occult Adventures classes** — occultist, kineticist,
    medium, mesmerist, psychic and spiritualist — held out of the random pool rather than missing,
    along with the Path of War stalker and zealot. The first ticket is a census of what the installed
    Foundry content can actually render, because a class that generates and cannot be imported is not
    ready. The stalker and zealot may simply not exist in their module, in which case the answer is a
    named blocker rather than a plan.
  - **Charting already found characters getting the wrong number of class options.** A 20th-level
    magus is handed **10 arcana where the rules grant 6**, and an investigator **10 talents where the
    rules grant 9** — labelled with the wrong levels besides. The cause is that "how many picks, and
    when" is currently answered three different ways in three different places, and nobody has ever
    swept the whole table.
  - **A bard's versatile performances are chosen and then thrown away.** The generator rolls them and
    discards the result, so they reach neither sheet. The gunslinger's deeds and the hunter's animal
    focus have option lists sitting in the repo that nothing reads, and the shifter has no aspect
    picker at all.
  - **The effort ends in a validator, not just a document.** Whatever the sweep concludes about each
    class gets asserted in code, because a spec that says "the magus gets six arcana" goes stale the
    moment someone edits a divisor — the same lesson a stale doc taught this repo when it silently
    broke six weapons.

### Changed
- **All 30 data gates and regression tests share one harness.** Each of them used to hand-roll an
  error list, a warning list, a pass/fail print and an exit code — roughly a third of every file,
  and already drifted: the same failing run printed `FAILED: N problem(s)`, `FAILED: N problem(s)
  across N modifier(s)` or `FAILED -- N problems` depending on which gate tripped, so "did it fail?"
  could not be answered from the shape of the output. `Backend/scripts/_harness.py` owns that now,
  and a new gate opens with its first real rule instead of forty lines of ceremony.
  - **Path resolution moved into the harness, which is the larger win.** About thirty scripts each
    recomputed the repo root from their own nesting depth (`Path(__file__).resolve().parents[1]`),
    so the directory layout was encoded thirty times over. The harness now finds the root by walking
    up for a directory carrying both `CLAUDE.md` and `.git`, and *raises* rather than guessing when
    there isn't one — a wrong-but-existing path reads the wrong file silently, which is the worse
    failure. Depth is no longer a fact any script knows.
  - **The three bare-`assert` tests now collect instead of stopping at the first failure.** When a
    data change breaks nine things you want all nine, not the first one and a traceback. Verified by
    deliberately breaking two fixtures and confirming both were reported. Converting the loop
    assertions also showed how little was being counted — `test_spell_conditionals` went from 17
    assertions to 762 checks.
  - *Deliberately not done:* no pytest, and no shared argparse. The standalone-script convention here
    is documented and intentional; the flags are genuinely per-gate (`--print`, `--module-root`,
    `--verbose`), and a shared parser would either accept all of them everywhere or grow bigger than
    the parsers it replaced.
- **The wayfinder tracker moved out of this repo** into the standalone
  [`tickets`](https://github.com/The-Data-is-a-lie/tickets) repo, restructured in the okf-bundles
  format as `tks/pathfinder-char-creator/<problem-type>/<effort>/`. Five maps and 32 tickets moved;
  links pointing back into this repo became absolute GitHub URLs so a ticket resolves when read from
  anywhere. `docs/wayfinder.md` now points at it. *Why:* the maps increasingly span this repo, the
  FoundryVTT module and the web sheet, and a tracker living inside one of the three repos it tracks
  had become the wrong home.

- **The module's class roster lives in one file instead of three.** It used to be hard-coded in the
  dropdown, in a dead byte-identical copy of the dialog, and in the item-collection boundary list,
  with nothing checking they agreed — which is exactly how the occult classes reached two of the
  three and not the one you look at. There is now a single `scripts/class-roster.js`, and a new
  `Backend/scripts/validate_class_roster.py` (validator 17) fails if it disagrees with the backend's
  rollable class list, puts a class in the wrong family, or drifts from `every_class.json`'s class
  order — the ordering contract that decides whether one class swallows the next one's features.
- **A class that says it casts is now checked in all four places it has to say so.** Declaring a
  spellcaster means a caster tier, a place on the spellcasting roster, a casting ability and a
  spells-per-day table — four files that never knew about each other. Miss one and the failure is
  invisible in the worst way: the class ships with an empty spellbook, or blows up only on the
  seeds that happen to roll it. `Backend/scripts/validate_caster_data.py` (validator 18) fails on
  any of the four, and on a spell list pointed at a list that doesn't exist. The adept, the omdura
  and the vampire hunter each had to be walked through those four by hand; nothing else will.
  - It also fails a class filed under two casting abilities at once, which the **shaman** was —
    listed as both Wisdom- and Charisma-based. Wisdom was already the one that took effect, and is
    the one the shaman has by the book, so no shaman changes; the Charisma entry was text that
    read like a rule and did nothing.
- **Three golden fixtures were re-seeded, not just regenerated.** Seven new classes in the pool
  realigned every multiclass draw, and all three multiclass goldens quietly stopped covering the
  thing they exist for: `caster` lost its second spellbook, `companion` lost the three-grantor stack
  and its archetype-removed bond, `manifester` lost the aegis and with it the only coverage of the
  power-points-with-no-powers shape. Same failure mode as the 7275, 7323 and 8018 re-seeds. The
  `companion` sweep now selects on the **coverage** — a stacked entry plus an absence entry — rather
  than on "rolls druid + ranger + hunter", which was only ever how that coverage happened to arrive.
  - **And that rule is now enforced instead of merely written down**, which is the durable half.
    Each of the three fixtures carries a predicate describing the shape it exists to pin, checked on
    every run — including when the goldens are being regenerated, because that is precisely when the
    coverage gets written away. A pool change that costs a fixture its purpose now fails immediately
    and says which shape went missing, instead of arriving as a two-thousand-line diff for someone
    to read after the fact. All four historical losses would have been caught by name.

### Removed
- **The module's `html_dialog.js`.** An unreferenced copy of the generator dialog that nothing
  imported and that had already gone stale — and the copy that missed the occult classes.
- **The in-repo character sheet and `GET /sheet` are gone.** The standalone
  *Pathfinder-Character-Sheet* front end superseded this copy some time ago, and the copy had been
  quietly rotting behind it: its generate form posted to `/execute`, a route that does not exist,
  and loaded two scripts (`saveFormData.js`, `populateForm.js`) that were not in `Backend/static/`
  either — so the page had been non-functional apart from its link to `/sheet`. Deleted:
  `templates/sheet.html`, `static/scripts/sheet.js`, `static/styles/sheet.css`, and the route.
  New features land on the standalone sheet only; this one will not be extended again.
  - **`/` still answers**, now as a signpost page naming the API endpoints, so the deployment's root
    does not start 404ing on a health check. `/license`, `/backstory-stats` and
    `/update_character_data` are untouched. *Rejected:* removing `/` too and going pure API.
  - **`validate_name_data.py` follows the clients out of the repo.** Its region-reachability check
    read the two deleted files, so it now reads the standalone sheet's `REGIONS` and the Foundry
    module's dialog instead — both real clients, both outside this repo. A machine without them
    checked out prints a loud `SKIPPED:` line per client rather than folding it into the warning
    count, because a check that quietly stops running is the exact failure this script exists to
    catch. `PF_FOUNDRY_DATA` overrides where it looks.

### Fixed
- **`test_skill_ranks.py` checked a different number of things on every run — now it checks 4331,
  every time.** The count moved between 3688 and 3696 because a conditional assertion fired a
  varying number of times. The test never failed; what varied is how much it *checked*, which is why
  nobody noticed. A regression hiding in the untaken branch would have passed most of the time.
  - The cause was not where it was first recorded. The suspect was a local `random.Random(99)`
    pinning only the test's own inputs — a red herring. The actual carrier was a bare `random.seed()`
    at the end of a *different* test, which re-seeds from OS entropy in the middle of the run and
    handed every test after it an uncontrolled stream. The global seed is now set before each test,
    so the suite no longer depends on its own running order either.
  - **The test now proves this itself** rather than relying on someone comparing consecutive runs:
    two identically-seeded passes must produce identical characters and identical check counts.
    Deliberately not a pinned expected total — a magic number would need editing every time a check
    is added, so it would be updated reflexively and stop meaning anything.
  - Separately, the conditional assertion now **declares its own coverage** and fails if the sample
    never exercised it. Determinism made the coverage stable; that makes it non-zero. Two different
    failures, both live here.
  - The remaining architectural fix — threading a `random.Random` instance into
    `profession_chooser.py` instead of seeding a global — still moves draw order and therefore the
    golden fixtures, so it stays out of a refactor branch.

- **The kineticist would have been handed a spellbook, and the medium two spell levels it never
  gets.** Both carried `"casting level": "mid"` in `class_data.json`, which `spells.py` branches on.
  The pf1 class Items disagree — the kineticist has no `casting` block at all (burn is
  Constitution-priced, exactly as `caster_mod`'s own comment says the caster map cannot express) and
  the medium is a `low` progression. Corrected to `none` and `low`, and
  `build_occult_class_data.py` now reconciles the field from the pack so it cannot drift back.
  Latent until now only because the six were filtered out of the pool.
- **Two goldens had stopped covering what they exist for.** Opening the pool to six more classes
  realigned the multiclass roll: `companion`'s ranger became a ninja, collapsing the three-grantor
  stack the golden was seeded for, and `manifester`'s aegis became a wizard, leaving no coverage at
  all of the points-only manifester shape. Both were **re-scanned for new seeds rather than
  regenerated in place** — 7971 (which also picks up an archetype-removed bond beside a real one,
  so absence and stack now appear in one payload) and 8041. This is the second time this trap has
  been hit; the seed comments say re-scan rather than edit the prose, and that is what they mean.
- **Manifesters were short their free talents, and were spending real powers to buy them.** Every
  one of the ten power-knowing psionic classes grants 0-level talents by class feature, and the
  rules say in as many words that those talents *do not count against powers known* — a psion gets
  three plus Detect Psionics, a tactician and a vitalist three, most classes two, a wilder one, a
  marksman none. The generator granted none of them, and it drew from a pool that mixed the talent
  tier in with real powers, so a level-1 psion who should know three powers *and* four talents could
  roll three talents and nothing else. Talents are now granted on top of the class table and land in
  power level 0; the counted pool starts at level 1 so a free thing can no longer cost a slot.
- **Powers were handed out that the manifester's key ability forbids.** Every power-knowing class
  requires a score of "at least 10 + the power's level" to learn a power, and only the
  can-manifest-at-all floor was enforced — so a 17th-level psion with Int 14 was given 9th-level
  powers instead of stopping at 4th. Max power level is now the class table capped by the ability
  score. Most visible on the **psychic warrior**, which manifests off Wisdom but plays off Strength
  and so is routinely capped below its table; that is the rule working, not a regression.
- **Some powers reached the sheet with no rules text and no Foundry item.** The power *lists* cite
  names the power *pages* spell differently — wiki redirects (`Thought Shield` →
  `Thought Shield (power)`) and a few case-only variants — and selection matched names exactly,
  which the data validator never did. A cited name that resolved to no page was picked anyway, and
  arrived as an empty row in Foundry and as nothing at all on the web sheet. Selection now resolves
  through the same aliases and casefolding the validator uses, and a name that resolves to nothing
  is no longer legal to pick — which excludes the three known red links (`Manifest Veil`,
  `Detect Compulsion`, `Mind Trap`) the validator has been warning about all along.
- **The web sheet's Psionics tab existed but never appeared.** The tab module was written, loaded
  and referenced, but had no entry in the sheet's tab list — the only thing that builds the tab
  buttons and panes — so no manifester ever saw it. Registered beside Spells.
- **The aegis and the soulknife showed nothing psionic.** Both generated their subsystem picks
  correctly and filed them where nothing pointed: the soulknife has no manifesting ability, so a
  manifesting-only filter dropped it and it produced no psionics block at all, and the aegis
  rendered a bare power-point line while its 87 astral-suit customizations sat under generic class
  features. The payload now carries a `subsystem_bucket` pointer on every psionic class (and the
  soulknife's `mind_blade`), and both front ends render a class's own options on its psionics page.
  The nine psionic buckets also gained Foundry display metadata, so blade skills and customizations
  get their own dividers instead of the generic band — and "strategies" stops being labelled
  "Strategie" by the trailing-s fallback.
- **34 class options were named after a citation instead of themselves.** The option-list scraper
  splits an entry on its first colon, which for an unbolded entry carrying a source note lands
  *inside* it — so a soulknife blade skill was recorded as `Animal Senses (Source` with the rest of
  the citation leaking into its description. The parser now hands an unbalanced parenthesis back to
  the description. Beyond reading correctly, this fixed real Foundry matching: **class options
  matched against `pf1-psionics` rose from 195 to 229 of 335**, because all 34 truncated names
  match module items once they are spelled properly.
- **Psionic characters imported into Foundry attacked at half their proper bonus.** All twelve
  psionic classes arrived carrying the same progression — low BAB, a d6 hit die, 2 skill ranks per
  level — because that is the placeholder the `pf1-psionics` module ships for every one of its
  classes, and the harvest that puts those classes into the generator module's bundle copied it
  through untouched. It happens to be right for the psion. It was wrong for the other eleven: an
  **aegis or soulknife at level 20 showed +10 to hit instead of +20**, a psychic warrior +10 instead
  of +15, and nearly every manifester was short half its skill ranks. The harvest
  (`Backend/scripts/build_every_class.mjs`) now patches base attack bonus, hit die and skill ranks
  from `Backend/json/class_data.json` — the scraped values the generator itself has used all along —
  so the sheet and the backend finally agree. Re-run against the module repo's `every_class.json`
  and `every_class_MODS.json`. *Rejected:* editing the two bundles by hand (they are generated, and
  the next rebuild would silently undo it) and fixing it downstream in the module (pf1 reads the
  class item directly, so the wrong number would still be in the file). The script now also refuses
  to write at all if a harvested class is missing from `class_data.json`, and re-reads what it wrote
  to confirm the values landed — an unpatched class is invisible in a 3 MB generated file, which is
  why this one survived a release.
- **Every region can now be chosen — five of the ten never worked.** Region selection had three
  independent defects, all in `region_chooser`, and each looked exactly like success:
  - **Ieso did not exist.** A stray `regions.remove(region)` ran after the loop that built the list,
    so it deleted the last region. It appeared in **0 of 2,000** random draws, and asking for it
    explicitly handed back a different region — while the campaign lore file carried Ieso lore no
    character could ever reach. The line it replaced had the mirror-image bug at the other end of the
    list, so this was the second off-by-one in the same spot; the resolver now works from the region
    names themselves rather than positions in a list.
  - **Tal-falko and Kaeru no Tochi characters were given other regions' names.** The chosen region
    was title-cased before being stored, which turned `Tal-falko` into `Tal-Falko` and
    `Kaeru no Tochi` into `Kaeru No Tochi` (capitalising a Japanese particle). Neither matches the
    name files, so those characters — roughly a fifth of all NPCs — silently drew **both** their
    first and last name from a randomly chosen different region. The old golden characters show it:
    a fighter whose homeland reads *Tal-Falko* was named *Henry Sokolov*, a **Dolestan** name.
  - **"Grundykin Damplands" and "Dust Cairn" were never selectable.** Those are the labels the
    Foundry dialog and the web sheet send; the regions are recorded as `Grundy` and `Dust-Cairn`, and
    an unrecognised region silently became a random one.
  - **The region a character is given is now the one that was asked for**, in whatever spelling or
    casing the client uses, and an unrecognised one says so instead of quietly substituting. Region
    names are matched the same way race names already are (ignoring case, spaces and punctuation),
    with a small alias table for the two labels that are a genuinely different name. *Rejected:*
    correcting only the clients — the Foundry module ships on its own release cycle and a browser's
    saved form data keeps sending old values, so the backend has to keep accepting them.
  - The web sheet and the page at `/` now send the recorded region name while still showing the
    friendlier label. The root page's region field was a **number** input whose value the generator
    could not read at all, so every region choice made there had always been discarded.
  - **`validate_name_data.py` now proves it**: every region must come back as itself when asked for
    by name in any casing, must appear across a sample of random draws, and every option the in-repo
    clients offer must resolve to a real region — with all ten covered between them. None of this is
    visible from the data files alone, which is how it went unnoticed for over a year.
  - ⚠ **Generated characters change for the same seed.** Names and homelands are the point of the
    fix; some seeds also shift further, because the corrected name draw consumes a different amount
    of randomness and everything drawn afterwards moves with it. All six golden payloads were
    regenerated; four changed only their name and region, two changed broadly.

### Changed
- **Psionic mechanics will be sourced from the Library of Metzofitz wiki, not from the
  `pf1-psionics` module's `packs-source/` YAML** — reversing the extraction decision logged further
  down this section. The module's own data disproved it: all twelve of its classes carry the same
  placeholder `bab: low` / `hd: 6` / `skillsPerLevel: 2`, which is correct only for the psion by
  coincidence and would have produced soulknives with d6 hit dice and half BAB; and powers-known per
  level exists nowhere in the module, neither in data nor in code. The wiki publishes the full class
  table — BAB, all three saves, power points per day, powers known and maximum power level for
  twenty levels — and is already this repo's source for `data/Metzofitz_Feats.csv`.
  **`pf1-psionics` remains the Foundry render target**, so generated names still have to reconcile
  against its packs or the module drops them silently. Rejected: extracting the module's YAML (its
  class fields are unusable and its power tables do not exist), and hand-authoring the tables (240
  numbers per class family, with no second source to check them against).
  - Scope is fixed at **twelve classes** — Aegis, Cryptic, Dread, Highlord, Marksman, Psion, Psychic
    Warrior, Soulknife, Tactician, Vitalist, Voyager, Wilder — the intersection of what the wiki
    documents (18 base classes) with what the module can render. The other six are held for a v2,
    where the psionic Zealot will also need a key that does not collide with the Path of War zealot.
  - Psionic **feats need no scraping**: `data/Metzofitz_Feats.csv` already carries 311
    psionic-flagged rows, deliberately excluded from the random pool by `_METZ_TYPES` in
    `Backend/utils/class_func/feats.py`. Turning them on is a selection decision, not a data one.
- **Two new design efforts are charted under `docs/wayfinder/`, and both are 1.0 scope**
  (Road-to-1.0 Phase 4.5): `companions/` (animal companions, familiars, eidolons, mounts) and
  `psionics/`. Each is a map — destination, locked decisions, and one file per open *question* in
  `issues/` — that ends at a spec section in `docs/feature_spec_todo.md` (§8 and §9). Decisions get
  made before code, the way Path of War and Spheres were specced first.
  - **Psionics will adopt the existing [`pf1-psionics`](https://github.com/SoxMax/pf1-psionics)
    module rather than build one.** The original plan was to write a new public FoundryVTT psionics
    module; that module already exists, is active (v0.9.1, Foundry v13 / pf1 v11), and ships 597
    powers, 309 feats, 7 disciplines and 12 classes with a custom `power` item type, a Manifesting
    tab, and auto-calculated manifester level and power points. Adopting it also means the data can
    be extracted from its `packs-source/` YAML — mirroring how
    `Backend/scripts/extract_spheres_talents.py` extracts Spheres data from `pf1spheres` — instead
    of scraping d20pfsrd. Rejected: building our own module (duplicates maintained work, and was by
    far the largest piece of the effort) and scraping (no structured psionics dataset exists, and
    the module's YAML is already pf1-shaped).
  - **Psionics data will be extracted *and validated*, not extracted straight.** Research against
    `pf1-psionics` found its 597 powers accurate (zero errors in an eight-power sample, two of them
    verbatim-identical to d20pfsrd) and its saving-throw fields correct — but **all 12 class entries
    carry the same placeholder `bab: low` / `hd: 6` / `skillsPerLevel: 2`**, contradicting the prose
    in those same files and correct only for the psion by coincidence. A straight extract would have
    silently produced soulknives with a d6 Hit Die and low BAB, and `test_house_invariants.py` would
    not have caught it — the house-formula assertions are only as good as `class_data.json`. Class
    mechanical fields will be re-sourced instead. Also found: power-points-per-day lives in the
    module's JavaScript rather than its YAML, and a powers-known table exists nowhere in the module.
  - **OGL attribution will be hand-curated rather than inherited.** `pf1-psionics`' own §15 omits
    *Psionics Expanded: Advanced Psionics Guide* (which the Aegis traces to) and *Psionics Augmented:
    Seventh Path* (cited by a power it ships); the identical block appears in `pf1-pow`, so it is
    boilerplate rather than a curated notice. Copying it would inherit the gap.
  - **The two halves are separate maps, not one.** Their frontiers do not inform each other:
    companions block on a Foundry rendering question (there is no second-Actor precedent anywhere in
    the module), psionics blocked on the module decision above. Merging them would have parked one
    half behind the other's unrelated ticket. The single crossover — a psicrystal is structurally a
    companion — is a cross-reference between the maps.
- **The API payload now carries the animal-companion stat block** (`animal_companion`; sheet repo
  issue #15). A companion druid's payload gains the species name and kind (normal/plant/vermin),
  the full species statistics from `animal_choices.json` (including the advancement block), the
  druid-level chassis row from `animal_companion.json` (HD, BAB, saves, natural armor, str/dex
  bonus, tricks, special), and the rolled companion feats — all of which the generator already
  computed and then discarded; only a boolean `companion` flag used to survive. Characters
  without a companion get `null`, and the existing flag is unchanged, so current consumers are
  unaffected.
- **The two-step table workflow is now documented where users will find it** (Road-to-1.0
  Phase 5): a walkthrough (generate + inject → run the Apply Conditionals macro, and why there is
  deliberately no creation-time equivalent) in the Foundry module repo's root `README.md`
  *(module repo)*, a developer pointer in `docs/CODEBASE_MAP.md`, and the applier README's stale
  curated-toggle count replaced with a pointer to the `build_data.py` output *(applier repo)*.
- **Eighteen more baseline chassis features get weapon conditionals (Road-to-1.0 Phase 3).** The
  top-20 curation pass ranked the 905 core tier-A candidates by how often they actually appear on
  generated NPCs (129-generation batch across all 43 classes; chassis features counted via the
  `class_ability` list, which the first frequency attempt missed) and curated every ranked feature
  with a genuine on-attack payload: Stunning Fist, Quivering Palm, Quarry, Master Hunter, Master
  Strike, Debilitating Injury, Knockout, Cavalier's Charge, Mighty Charge, Supreme Charge, Gun
  Training, Judgment (separate Justice and Destruction toggles), Greater Bane, True Judgment,
  Studied Combat, Studied Strike, Inspiration (attack-roll use), and Sacred Weapon. Higher-ranked
  candidates that got **no** conditional were rejected deliberately: defensive/passive rows
  (Improved Uncanny Dodge — the most frequent hit of all, Trap Sense, Bravery), self-buffs that
  belong to the changes/buff side (rage and bloodrage chains, Animal Focus), BAB mechanics
  (Flurry of Blows, Spell Combat), own-action attacks (Bomb, Channel Energy, Lay on Hands) and
  affects-others auras (Banner) — a toggle whose rider carries no on-attack payload is the
  cost-only defect all over again. Synced to the applier (`build_data.py`, `bundle_macro.py`,
  `verify_specs.mjs` 97 passed) *(pf1-conditional-applier repo: data + rebuilt bundle)*.
- **Phase-3 correctness pass came back clean**: the same batch reported zero `buff_gaps` rows and
  `report_buff_coverage.py` still covers all 11 side-maps with no curated-name collisions, so
  there were no orphans or casing mismatches to fix this round.
- **Metzofitz homebrew feats join the random pool (Road-to-1.0 Phase 2, backlog #1).** Behind the
  homebrew flag, `generic_feat_chooser` now concatenates the General- and Combat-typed rows of
  `data/Metzofitz_Feats.csv` (~490 of 1,735) into the selection pool — subsystem-typed rows
  (Akashic, Psionic, Kineticist, styles, …) stay out because the chooser's exact type match can
  never hit their comma-joined type strings, and style chains keep arriving via Martial Training.
  Name collisions resolve to the AoN version; picks flow through the existing prerequisite loop.
  Placed Metzofitz feats get their rules text from the library (they're absent from
  `data/feats.csv`), so Foundry rows render with descriptions instead of empty fallbacks. The
  invariant sweep now asserts every Metzofitz pick is described and that picks actually occur
  (1,773 across the 645-generation sweep).
- **House-rule numbers verified and implemented (Road-to-1.0 Phase 1).** The three "suspected
  wrong" areas from the 2026-07-29 grilling were diffed against the OKF house-rules bundle and
  fixed, all gated on the existing homebrew flag so the standard-PF1 path is unchanged:
  - *Skill ranks* (`skill_ranks.py`): any 2-ranks/level class now grants 4 (the house rank
    floor — gated on the new internal `misc_homebrew_rules` catch-all flag, see below); the
    per-skill cap is 3 ranks per character level instead of the PF1 level cap; and every
    character gets +2/level background-only ranks (PF Unchained background list ∩ the canonical
    35 skills, minus Profession which keeps its own subsystem).
  - *Feat counts* (`level_and_bab.py`): +2 creation feats (folded into the normal bucket — they
    carry no label). Flaw feats keep the diminishing house schedule the old clamp already encoded
    (first 2 flaws grant 1 feat each, the 4th grants the 3rd: 0→0, 1→1, 2→2, 3→2, 4→3) and now
    sit behind `misc_homebrew_rules`; the only real defect was the phantom feat granted at zero
    flaws, now fixed.
  - *HP* (`hp_rolls.py`): full (max) hit die at every level per the house rule, matching what pf1's
    `healthConfig` world setting (auto-HP, maximized) already showed on injected sheets — the
    generator and Foundry now agree instead of Foundry silently overriding a rolled value.
- **`misc_homebrew_rules` — a catch-all flag for small homebrew rules.** House rules too minor to
  deserve their own Yes/No input question now gate on one internal flag
  (`skill_ranks.misc_homebrew_enabled`; currently the 2→4 rank floor and the diminishing
  flaw-feat grant). It defaults on in `generate_random_char` and is deliberately not an API
  input — exposing it is a noted backlog item in `docs/homebrew_rules.md`.
- **`scripts/test_house_invariants.py` — the invariant sweep.** Every generatable class (43) ×
  levels 1/5/10/15/20 × 3 seeds = 645 generations asserting the house *formulas* (feat buckets,
  skill budget/cap, full-HP totals) rather than pinned sheets; `--classes/--levels/--seeds` trim
  the matrix. The payload now exports `skill_rank_budget` and `normal_feat_amount` as the sweep's
  assertion handles.

### Changed
- **One definition of the archetype pipeline, and one owner for its vocabulary.**
  `build_companion_archetypes.generate()` is now the single statement of what the generated file is
  (classify → confirm → correct → guarantee a `removes_scope`); `validate_companion_archetypes.py`
  calls it instead of hand-copying the builder's call sequence, which was kept in step by nothing
  but a comment reading "must mirror … exactly". The quiet failure was the dangerous one: a new
  pipeline step added to one and not the other would leave the two agreeing by coincidence until it
  first changed real output. The builder likewise imports `EFFECTS` from `validate_companion_data.py`
  rather than restating it — the "restate a symbol instead of naming its owner" pattern CLAUDE.md
  calls a bug magnet.
- **The archetype classifier reads clause by clause instead of blob by blob, and it now reproduces
  every human verdict.** The first pass concatenated an archetype's whole prose and matched generic
  regexes over it; measured against the first 15 signed sign-offs it scored **6/15**. The blob was
  the bug: a druid's nature bond has **two sides**, and once the text is concatenated a sentence
  about domains is indistinguishable from one about the companion. It now splits the *bond feature's
  own* text into clauses and binds each prohibition to its own object — **17/17**, pinned by the new
  `Backend/scripts/test_companion_archetype_classifier.py`.
  - **Five rules the sign-off exposed**, none of which existed before: removal by prohibition
    ("cannot select an animal companion" — no "replaces" sentence to key on, so Nithveil Adept read
    as harmless); domain-side-only text (Cave Druid's bond text is *only* a domain list, and read as
    a species restriction); forcing by prohibition ("cannot … choose a domain instead"); a change of
    creature **kind**; and property restrictions.
  - **A sixth effect, `creature_type`.** #38's five effects cannot say "the bond yields something
    else" — a Draconic Druid gets a *drake*, an Elemental Ally four *eidolons*. 25 archetypes carry
    it. Without it a druid whose rules say drake would silently generate a wolf.
  - **Property restrictions are derived, not hand-listed.** "An animal with a fly speed" resolves
    against `animal_choices.json` to the 21 species that have one, so it stays correct as species are
    added. Only *resolved* names enter `species_pool`; an unresolved phrase is carried separately,
    because a guessed species is a hard validator failure.
  - **`forces` and `removes` are mutually exclusive** and were co-occurring on 13 entries. Where the
    bond yields a different kind of creature the prohibition is on the *animal companion* and the
    grant is its replacement, so it is not a removal; the 8 genuinely ambiguous ones are marked
    `conflict` and dropped to low confidence rather than silently resolved.
  - **Three archetypes were never bond archetypes at all.** `BOND_TARGETS` held a bare `"mount"`,
    which matches inside "**mount**ain" — Mountain Druid, Summit Sentinel and Mountain Witch were
    classified on a substring. The real population is **202**, not 206.

### Added
- **Who grants a bonded creature is a data table now, and five more classes actually get one**
  ([#30](https://github.com/The-Data-is-a-lie/Pathfinder_Char_Creator/issues/30)). The generator
  gave a companion to druids and nobody else, through a hard-coded check. New
  `Backend/json/companion_grantors.json` declares every grantor — druid, ranger, hunter, wizard,
  sorcerer (Arcane bloodline only), witch, paladin, cavalier, samurai, summoner, and the Spheres of
  Might *Beastmastery* talent, which is not a class at all — and one resolver in
  `animal_companions.py` is the single path to a creature. **Paladins, cavaliers and samurai now
  arrive with mounts; rangers and hunters with companions.**
  - **Effective level is the grantor's own class level**, transformed by that row's expression
    (a ranger's companion is at *level − 3*), stacked across sources and capped at character level.
    Below a grantor's threshold there is **no creature at all** — a paladin 3 has no mount and does
    not get a level-1 one.
  - **`shifter`, `antipaladin` and unconditional `sorcerer` are deliberately not rows**, per the
    rules check in #23.
- **No druid has ever generated a vermin companion. Now they can.** `domain_chance` was read by
  *both* the domain-vs-companion gate (`<= 90`) and the species ladder (normal `<= 80`, plant
  `<= 90`, else vermin). The ladder only ran when the roll was already `<= 90`, so the vermin branch
  was unreachable by construction. The species tier draws its own number: **23 vermin companions in
  400 druids**, where the count was previously zero.
- **The validators are wired to something that runs them.** This repo had eleven
  `Backend/scripts/validate_*.py` gates and **nothing invoked any of them** — no CI, no pre-commit,
  no runner. A gate nobody runs is a sentence, which is the failure the docs doctrine exists to
  prevent. New `Backend/scripts/validate_all.py` discovers every validator by glob (so a new one is
  covered the moment it is added, with nothing to register) and runs each in its own process, so one
  crashing cannot hide the rest. New `.github/workflows/validate.yml` runs it on every push,
  alongside a trimmed invariant sweep and a check that the generated data files still match their
  builders. All eleven pass today, which is the first evidence that the eight pre-existing ones had
  not silently rotted.
- **Bond-touching archetypes are classified: the `companion_archetypes.json` triad**
  ([#40](https://github.com/The-Data-is-a-lie/Pathfinder_Char_Creator/issues/40)).
  `archetypes.json` holds 1,303 archetypes with no structured `replaces` field — the relation
  between an archetype and the class feature it swaps exists only as prose. Since an archetype is
  rolled *unconditionally* for every class, a druid has a ~57% chance of rolling one that touches
  its nature bond, so this cannot be skipped. `build_companion_archetypes.py` classifies the 206
  that do; `companion_archetypes_overrides.json` wins over it; `validate_companion_archetypes.py`
  gates the pair.
  - **The trap is that `forces` cannot be read off the closing sentence.** Cinderwalker (deletes the
    companion) and Beast Master (grants one) carry the *identical* "This ability replaces hunter's
    bond." Classification therefore reads what the **replacing feature is**, from its own text.
    Both come out right.
  - **The vocabulary needed widening: 33 archetypes have two effects.** Devolutionist both forces a
    species ("must choose a devolved humanoid … use the stats for an ape animal companion") *and*
    suppresses a field of the advancement merge ("doesn't increase to size Large at 4th level").
    #38 gives an archetype one `effect`; collapsing the pair silently drops whichever was tested
    second, so entries now carry an `effects` **list** beside the single-valued primary.
  - **Every verdict is a proposal until signed off.** `docs/companion_archetype_signoff.md` is the
    worksheet — least-confident first, each proposed effect quoted with the phrase that triggered
    it, so a reviewer can judge without opening the book. 23 entries are flagged where a "select
    from the following" restriction names **domains** rather than creatures: the druid's nature bond
    has two sides, and a domain-side restriction is indistinguishable from a species pool until you
    read what is being listed.
  - **All 202 verdicts are now signed off**, every one read against the archetype's own rules text
    rather than the classifier's proposal. 110 came back corrected and live in
    `companion_archetypes_overrides.json`; the other 92 agreed with the generated verdict. The
    classifier scored **20/81** against the deliberately-hard residue and **92/121** against the
    rest — good enough to propose, not to be believed, which is why the signed data is what ships.
  - **A confirmation is deliberately not an override.** New
    `Backend/json/companion_archetypes_verified.json` records "a full read agreed with the generated
    verdict" as its own thing, because an override wins permanently: recording the 92 agreements as
    overrides would freeze today's proposal and stop any later classifier fix from ever taking
    effect. If the classifier later disagrees with a verified entry the builder prints `STALE:`
    instead of quietly changing the answer under a "signed off" label.
  - **`forces` now applies only to classes whose bond is a choice** — druid, ranger, wizard,
    sorcerer. A hunter, witch, cavalier, samurai or summoner always has its creature, so there is no
    flip to suppress; tagging those `forces` described nothing and hid the real effect. Kept in step
    with which rows of `companion_grantors.json` carry a `choice`.
- **The `pf-content` Actor names the module clones are captured and gated**
  ([#29](https://github.com/The-Data-is-a-lie/Pathfinder_Char_Creator/issues/29)).
  `dump_pf_content_actors.py` writes `pf_content_companions.json` — 205 companions, 175 familiars
  and 14 eidolon base forms (seven forms in both sizes, as the spec predicted).
  `validate_companion_names.py` diffs every species the generator can emit against it: **144 of 196
  match**, and the 52 that do not are listed by name. A miss stays a warning, because degrading to a
  bare `npc` is the intended behaviour (D3) — but a *silent* miss is what already bit spell
  conditionals and psionics, so the count is printed every run and `--strict` promotes it.
  - The ticket asked for a new `.mjs` LevelDB reader; the existing `dump_foundry_pack.mjs` is
    already generic over pack directories, and `reconcile_psionics_names.py` already solves finding
    an installed `classic-level`. Reused both — the new file is the Python caller only.
- **The companion data has a gate: `Backend/scripts/validate_companion_data.py`**
  ([#27](https://github.com/The-Data-is-a-lie/Pathfinder_Char_Creator/issues/27)). The scrape repair
  above is worth nothing if the next edit quietly undoes it, so the conventions it established are
  now asserted rather than described. It shares `repair_animal_choices.py`'s vocabulary — the size
  list, the block regexes, the drifted spellings — by importing them, so the repairer and the gate
  cannot disagree about what a well-formed block is.
  - **What fails is what no legitimate entry can be:** a bare integer where an advancement delta
    belongs, a positive Dex on a size increase, an absolute score written as a delta or the reverse,
    prose in an ability slot, an underscored key shadowing a spaced one, an `ac` that is not a
    natural-armor delta, a size outside the nine categories.
  - **What does *not* fail is the size package**, and this is a correction to the spec. §8 describes
    it as Str +8 / Dex −2 / Con +4 / natural armor +2, but that is one row of PF1e's size-change
    table, not a universal rule — Small → Medium is Str +4 / Con +2, and Large → Huge carries
    natural armor +3. Measured against the *correct* scaled table, **97 of 153 size increases still
    disagree** — `bear, grizzly` reaches Large on Str +4. Those are the published per-species
    entries, and for a companion the published entry is the authority, not a table derived from it.
    So the deviations print as a WARN census every run: visible, counted, and never a build failure
    over faithfully transcribed rules text. *Rejected: hard-failing the table* (turns 97 faithful
    rows red and invites "fixing" the data to match a formula) *and a curated 97-row allowlist*
    (the same audit, paid up front, for a signal the WARN block already gives).
  - It also **owns the closed vocabulary** from the D8 grill — the `outcome`, `effect` and `flags`
    sets — as module constants, and validates `companion_grantors.json` and
    `companion_archetypes.json` against them the moment those files exist. One owner, importable by
    the grantor resolver and the archetype triad, the way `validate_maneuver_changes.py` takes its
    target vocabulary from `validate_quality_effects.py` instead of restating it.
- **Reindeer, griffon and hippogriff join the companion roster, and a `magical_beast` tier keeps
  the last two out of the random roll.** Added by the new `Backend/scripts/scrape_companion_species.py`
  ([#41](https://github.com/The-Data-is-a-lie/Pathfinder_Char_Creator/issues/41)).
  - Griffon and hippogriff are magical beasts no druid can simply have — they arrive only through an
    archetype's curated species pool. `animal_chooser` reads only `normal` / `plant` / `vermin`, so a
    fourth `magical_beast` tier makes that restriction structural rather than something every future
    consumer has to remember.
  - d20pfsrd carries **two** griffon and two hippogriff entries; the script selects by enclosing
    section, taking the non-third-party one over the `LG:LH` version gated behind a *Beast-Speaker*
    feat this generator doesn't model. Choosing by name alone would silently take whichever the
    parser reached last.
  - **Five of the nine species the ticket called missing already existed** under this file's
    `"noun, modifier"` spelling — `bat, dire`, `weasel, giant` — or without a *giant* qualifier that
    the stat block already implies (the companion seahorse is Large; `seahorse` *is* the giant one).
    Verified field-by-field against Archives of Nethys. New
    `Backend/json/companion_species_aliases.json` maps the pool spellings onto the file's keys, so
    the hard-failure rule for absent species doesn't fire on five creatures that are present.
  - **Giant eagle was not added.** PF1e publishes no animal-companion stat block for one, and the
    archetype that would grant it forbids mounts with a fly speed. It is recorded in the alias file
    as unavailable, with guidance, rather than invented.

### Fixed
- **A druid whose archetype removes the animal companion keeps its domain.** Six archetypes —
  Blight Druid, Nithveil Adept, Storm Druid, Urban Druid, Life Channeler and Ancient Guardian —
  forbid the *creature* while leaving the other half of the nature bond reachable ("a blight druid
  may not bond with an animal companion, but may … select from the Darkness, Death, and Destruction
  domains"). The resolver collapsed every `removes` to `archetype_removed`, and the domain gate
  fires only on `domain`, so those druids generated with **no companion and no domain** — the entire
  class feature silently gone.
  - **`removes` now says WHAT it removed.** A new `removes_scope` on each entry is either `creature`
    (the other side of a choice-bond survives) or `feature` (the whole thing is replaced, so nothing
    does). `feature` is the default because it is both conservative and overwhelmingly common: all
    25 Ranger and all 18 Wizard `removes` entries read "this ability replaces hunter's bond / arcane
    bond". Druid is the only class with a genuine split, 6 and 6 — Death Druid, Feral Shifter,
    Halcyon Druid, Progenitor, Tempest Druid and Urushiol trade the bond away for a phantom, a
    bonded mask, an aura or a poison, and correctly still get nothing.
  - *Rejected:* falling through unconditionally for every choice-bearing class. It would have fixed
    six archetypes and broken five, handing a domain to archetypes whose rules text gives it up. The
    scoped version needed six entries marked and no re-reading of the other 93 signed `removes`.
  - The value is closed by `validate_companion_archetypes.py` in both directions on the *merged*
    file — a `removes` without a scope fails, and a scope without a `removes` fails — because an
    override is a partial patch and neither file is complete alone.
  - **This also retires a measurement that could not have caught it.** The "both = 0, neither = 0
    over 400 generations" figure recorded for the druid flip never rolled an archetype, so it could
    not reach the broken path at all. A sample that cannot reach a defect reports zero forever.
- **A companion fed by two classes is built from the right row of the advancement table.** Sources
  of the same creature type stack their effective levels, but the chassis was read at each row's own
  *pre-stack* level and never re-read, so a hunter 8 / druid 6 stacked to effective level 14 while
  keeping the druid's level-6 row — HD 6 instead of 12, three feats instead of six — and
  `animal_feats` drew from the stale row too.
- **The companion stack has a golden payload at last.** All five existing goldens carry
  `animal_companion: null`, so map #18 — the grantor table, the species ladder, the archetype
  effects, the chassis — had no end-to-end coverage whatsoever, which is precisely how the stacking
  defect above survived a review. The new `companion` config rolls hunter 8 / druid 6 and pins the
  stacked chassis. The seed pair was chosen deliberately: most adjacent companion-table levels
  differ, but 6→7 does not, so a closer pair would have pinned nothing.
- **The classifier's fixture gate actually runs now.** It was
  `test_companion_archetype_classifier.py`, while `validate_all.py` discovers gates by globbing
  `validate_*.py` — so neither the runner nor CI ever invoked it, and its 17/17 was only ever true
  when somebody ran it by hand, from a file that looks exactly like a wired test. Renamed to
  `validate_companion_archetype_classifier.py`; the existing glob now finds it, with nothing to
  register. **Twelve validators run, not eleven.**
- **`validate_companion_names.py` can fail at the thing it exists for.** Its `--strict` flag was
  passed by nobody, so the name-match rate it polices could regress from 52 misses to 150 and the
  build would stay green. A miss is still legitimate — the module degrades to a bare `npc` by D3 —
  so the gate is now a ratchet on `UNMATCHED_BASELINE`, which fails only on *regression*.
  *Rejected:* wiring `--strict`, which would fail the build today over 52 known and accepted misses.
- **Eleven animal companions the generator could never roll are reachable, and advanced companions
  stopped gaining +2 AC they were never owed.** `Backend/json/animal_choices.json` carried five
  distinct scrape defects, repaired by the new idempotent
  `Backend/scripts/repair_animal_choices.py` ([#26](https://github.com/The-Data-is-a-lie/Pathfinder_Char_Creator/issues/26)).
  - **The scrape lost a nesting level and swallowed a species run whole.** `shark`,
    `shark, hammerhead`, `shrike, impaler`, `skittergoat`, `skunk, giant`, four snakes,
    `snapping turtle` and `spinosaurus` were sitting *inside* `seahorse`'s body, so the chooser —
    which rolls over the top-level keys — could not reach any of them. `seahorse` and `walrus` also
    had their own advancement block buried one level too deep. Normal companions: **145 → 156**.
  - **Advancement `dex` deltas had lost their minus sign** on 128 rows. A PF1e size increase never
    *raises* Dexterity, and 16 rows in the identical position had kept their `-2`, which is what
    identified the rest as damage rather than data. Merging the file as written inflated every
    advanced companion by +4 Dex — **+2 AC, +2 Reflex, +2 initiative**.
  - Advancement deltas are now **signed strings** (`"+8"`, `"-2"`) while the absolute scores in
    `starting statistics` stay bare integers, so the delta-vs-absolute distinction is visible in the
    type rather than inferred from context.
  - **Six underscored key spellings** (`ability_scores`, `starting_statistics`,
    `4th-level_advancement`, …) shadowed the spaced forms across 88 keys, so lookups silently missed
    those species. Normalised to the spaced spelling.
  - `faerie mount`'s advancement `ability scores` block had swallowed its sibling `size` / `speed` /
    `attack` fields, and 24 mindless vermin split PF1e's "no Int score" between `""` and `null` —
    now uniformly `null`, which is distinct from an Int of 0.
  - **Three further defects, found by pointing the new validator at the repaired file** — the
    argument for writing the gate in the same pass as the repair rather than after it.
    - **Three Dex deltas had the minus flipped to a plus rather than dropped** — `giant raven`
      `+2`, `troodon` `+4`, `sniper cactus` `+2`, each on a size increase. They survived the first
      pass because they *were* signed strings, and the repair only distrusted bare integers. Same
      rule, same repair: the entry owns the magnitude, PF1e owns the sign.
    - **Nine `ac` values were missing the word "armor"** (`"+1 natural"`, `"+2"`, `"+8 natural"`),
      eight of them in `starting statistics`, which the first pass never examined. Only the wording
      is normalised — the magnitude is left exactly as published.
    - `giant salamander`'s 4th-level `dex: 2` — previously reported and left alone, because with no
      size increase there is no rule to recover the sign from — is now resolved by hand to `"+2"`,
      in a named `HAND_SIGNS` table. Dex rising without a size change is legal PF1e, so positive is
      the reading; recording it as a one-entry exception keeps the single survivor from quietly
      becoming the precedent for a second.
- **Characters from Sojoria, Tal-falko and Feyador have their names back.** Every non-ASCII Latin
  character had been deleted from the two hand-authored name files — mid-word, not just at the
  start — so the generator produced `Stefan rling` for `Stefan Örling`, plus `Lindstrm`, `Trnqvist`,
  `Åkesson` → `kesson`, `Hélène` → `Hlne`, `Zoé` → `Zo`, `Longpré` → `Longpr`. 104 names across
  both files are restored.
  - The damage was **wider than the first report of it**: `first_names_regions.json` was affected
    too, not only surnames, and the mid-word cases are invisible to any lowercase-initial heuristic.
    They were found by reading all three regions' lists in full.
  - Names left deliberately unrepaired: `Clement`, `Gagne`, `Lefevre`, `Leger`, `Levesque`,
    `Riviere`, `Chretien`, `Desire`. These are plausible accent-free spellings in their own right,
    so restoring an accent would be inventing authorial intent rather than repairing damage.
  - No pipeline change was needed — the loader already reads UTF-8 explicitly. This was a one-off
    authoring accident, not something the stack does to the data.
- **Class options described by a plain string no longer crash feat selection.** `bonus_searcher`
  assumed every chosen class option was a dict of sub-keys (`bonus feats`, `bonus spells`, …) and
  called `.get` on it. Every psionics subsystem — and every multiple-pick bucket — is a plain
  description string instead, which raised `AttributeError` mid-generation. A string simply has no
  bonuses to search.
- **Game data no longer fails to load on Windows.** The shared JSON loader opened files with the
  platform default encoding, which is cp1252 on Windows, so any file carrying a curly apostrophe or
  an en dash raised `UnicodeDecodeError` — and the psionics classes brought both into
  `class_data.json`, taking every class in the game down with them. The Linux deploy was unaffected,
  which is what made it easy to miss. Files are now read as UTF-8, as JSON specifies.

- **HP Con-modifier math.** `total_hp_calc` floored before halving (`floor(con-10)/2`), inflating
  every odd-Con character by level/2 HP, and it read the *base* Con score — inherent bonuses and
  level-up bumps that landed on Con never reached HP. It now uses the final-score ability modifier.
- **Background/skill interaction:** `assign_dummy_zeroes` ran after rank assignment and would have
  zeroed background ranks landing outside the main skill sample; it now zero-fills first.
- **Baseline chassis class features now get weapon conditionals in the applier.** Smite Evil, Sneak
  Attack and their kin were missing at every layer — the conditional pipeline only ever swept the
  scraped *choice* pools (rage powers, arcana, hexes, talents), so the always-there features no class
  "picks" were never candidates, and the applier silently skipped their items on every actor. Ten
  are now curated in a new `core_features` overrides section (generic Sneak Attack plus the `(SLA)`
  and `(CAV)` labeled variants — separate entries because their progressions differ and the applier
  matches the raw item name before the label-stripped one — Smite Evil/Good, Challenge (CAV/SAM),
  Bane, Studied Target, Favored Enemy; Weapon Training already belongs to the `weapon_training`
  choice pool, and Flurry of Blows is a BAB mechanic, not a toggle). They reach sheets only through
  the applier macro — generation-time payloads never carried a consumer for class-feature
  conditionals, and still don't.
- **`--family core`: the candidate slicer now audits baseline features too.** Rather than curating a
  hand-picked list (rejected: coverage claims would rest on recall), a third
  `build_conditional_candidates.py` family sweeps all 4,506 `every_class_feature.json` classFeat
  items — minus choice-pool members, so families never overlap — through the same signal tiers, and
  reports per-class with best-effort attribution (name label → chassis list → prose). First run:
  905 tier-A / 497 tier-B candidates still uncurated, batched under `_conditional_candidates/`.
- **Applier: gear attack-notes become weapon toggles** *(pf1-conditional-applier repo, committed
  this session from a week-old working tree)*. Items with attack-target contextNotes in
  `item_changes.json` now yield default-off `"(Display): text"` conditionals via a new
  `item_conditionals.json`, with a byte-faithful `capitalizeWords` port so applier re-runs adopt
  the generator's own rows instead of duplicating them (rejected alternative: fuzzy name matching —
  exact-string adoption is what makes idempotency provable). Tier-B demotion machinery is
  scaffolded but deliberately disabled until unplaced spells route through it.
- **Curated-only sections are validator-backed.** `core_features` has no scraped source pool to
  check keys against, so `validate_class_feature_effects.py` instead requires every key to match a
  classFeat item name in the module export — the same lookup the applier performs, making a typo'd
  key a test failure instead of a silently orphaned conditional (soft-skipped when the module isn't
  installed). The applier's spec harness gained five chassis specs (paladin resolve, Unchained
  retarget, labeled-variant precedence).
- **Professions and trainers can now be switched off.** Both subsystems ran unconditionally on every
  character, so a request for a plain NPC still came back carrying profession ranks and a mentor.
  `/update_character_data` now accepts `professions` and `trainers` (`y`/`n`), read **by name** like
  `spheres_of_power` and `seed` — they never enter the fixed 19-field positional unpack, so a client
  that omits them is unaffected. Both **default to on**, which is exactly today's behaviour, so the
  FoundryVTT module and the bundled web sheet need no change. Turning professions off skips
  `profession_chooser` only: `skills_selector` still runs and still allocates the full rank budget
  (the two share `has_always_improving`, so the profession attributes are zeroed rather than left
  unset). Turning trainers off suppresses both trainer sources — ordinary `select_trainer_feats`
  picks *and* the 25% "trainer-backed" Path of War / Spheres mentors, which render as
  `(Trainer N - …)` rows of their own; the mentor branch's dice roll still happens, so a replayed
  seed reproduces the same character minus its mentors.

### Fixed
- **Mentors are no longer always ranked "terrible".** The backstory ranked each trainer by counting
  the rows in its `(Trainer N)` group, which is right for an ordinary trainer (one feat per row) but
  wrong for the Spheres Mentor — a **single** row funding up to four feats' worth of talents, so it
  read `1 → terrible` every time, even at six talents. Every trainer is now ranked by the **feats'
  worth it actually delivered** (`mentor_feat_worth` for the Spheres Mentor = the `Extra … Talent`
  feats its talents bundle into; funded feat count for the Path of War mentor), clamped to the top of
  the ladder — and by what it *delivered*, never its caliber roll, so a caliber-4 mentor that could
  only fund two feats' worth honestly reads "average". Mentor lines also name the **content** they
  funded rather than the mentor's own row name (was: "taught them Spheres Mentor"), and carry the
  system: `An excellent (Path of War) trainer who taught them Martial Training I (Broken Blade)`.
  Trainer labels carry it on the Feats tab too (`(Trainer 3 - Path of War)`); both the module and the
  web sheet print labels verbatim, so no JS change was needed.
- **Per-roll bonuses now land on the right d20 (crit-confirm encoding).** pf1 splits a weapon
  conditional's `attack` modifier by its `critical` field: `normal` parts roll on the initial attack
  **only**, `crit` parts on the critical-confirmation roll **only**. Three problems followed from
  this being missed during curation, all resolved (see `docs/conditional_open_questions.md` #2):
  - **Confirm-only feats were text, not a modifier.** Seven feats whose bonus fires only on the
    confirmation roll (`Object Of Legend` +10, `Improved Low Blow`, `Planar Wild Shape`,
    `Net and Trident`, `Demonic Nemesis`, `Greater Snap Shot`, `Desperate Swing`) now carry a
    structured `{target:"attack", critical:"crit"}` modifier, with the redundant "+N to confirm"
    prose trimmed from each name.
  - **Standing to-hit bonuses under-applied on the confirm roll.** A curated audit of all 127
    hand-curated `attack`/`normal` modifiers added a `critical:"crit"` **twin** to every bonus
    scoped to a state/duration/creature-type (RAW it applies to the confirmation roll too): 34
    feats, 8 class-feature powers, and the 9 bane-family weapon qualities. One-shot, penalty,
    stat-swap-per-attack, and combat-maneuver modifiers were deliberately left `normal`-only.
    `Earth Child Topple` was reclassified `normal`→`crit` (it grants Wis to confirmation and trips,
    not to normal attacks, so `normal` was over-applying).
  - **Six burst weapons were silently broken.** `Flaming/Icy/Shocking/Corrosive Burst`, `Thundering`
    and `Shattering` used `critical:"onCrit"` — never a pf1 value; pf1 deletes an unknown `critical`
    on the next sheet edit, dropping the burst dice. Corrected to `crit` (rolls in `critParts`,
    repeated `critMult-1` times — exactly burst RAW). The validator whitelist, which carried the
    bogus `onCrit` and lacked `crit`, is now `{normal, crit, nonCrit}`.

  Shipping this requires an applier `build_data.py` rebuild (done) and a backend deploy so the
  FoundryVTT module picks up the edited `feat_conditionals`/`quality_effects`.
- **Class-feature save-DC confidence metadata corrected.** `conditional_clauses.CLASS_FEATURE_DC`
  (offline curation metadata; not read at generation time) relabeled all nine `assumed` pools from a
  scan of their own DC sentences — the ability was kept in every case; only the confidence changed.
  A new `rules` confidence marks pools whose DC ability is fixed by the governing subsystem
  (`ki_powers`, `discoveries`, `mercy`, `cruelty`, `social_talents`); the rest moved to `varies`
  (incl. `slayer_talents`/`curses`, which mix abilities) or `stated` (`investigator_talents`).
  `assumed` is retained but now unused. See `docs/conditional_open_questions.md` #4.

### Added
- **Path of War mentors, and one uniform funding rule for both homebrew systems.** A mentor now funds
  *the portion of a character's training that lies beyond their own half-share*, and **whatever it
  funds leaves the normal feat track and renders under its `(Trainer N)` slot instead** — the rule
  Spheres already followed, now applied to Path of War as well. Concretely: the 25% "trainer-backed"
  branch rolls **one mentor per system the character has content in** (each with its own caliber),
  and a Path of War mentor's caliber buys whole Martial Training chains first
  (`caliber // (depth // 2)`), with the remainder refunding feats the character had already
  realized — capped at the Path of War that exists. Those feats move to the mentor's
  `(Trainer N - Path of War)` group, so the freed slots refill with ordinary feats: the character
  keeps the same maneuvers **and** gets that many feats back.
  - This replaces a silent inconsistency: the single caliber roll already raised `realize_total` for
    Path of War, but the reservation billed the character for the result and then suppressed the
    mentor row (`mentor_funded_talents` was empty), so **a pure-martial NPC could never have a mentor
    at all** — the roll was spent and thrown away.
  - **Rejected — pure refund** (content drops to the lean half): mentored martial NPCs would end up
    with *less* Path of War than before, which reads backwards for a character who had a teacher.
    **Rejected — pure expansion** (keep today's realization, character still pays): the mentor row is
    then a label on feats the character bought themselves, which is the duplicate listing that
    blocked a Path of War mentor in the first place.
  - The Path of War mentor gets **no header row of its own** — the funded feats *are* its content, so
    a "Path of War Mentor" row would be the content-free mentor this code has always refused to emit.
    The Spheres Mentor keeps its row because its talents render elsewhere, leaving that row as the
    only record of who paid for them.
  - New `mentor` golden config (`test_golden_payload.py`, seed 6009) — the four existing configs all
    roll lean, so mentor funding had no regression gate.
- **Conditional tiers: `A` applies, `B` is authored but not shipped.** Roughly half the authored
  conditionals describe real effects that don't earn a permanent checkbox in the pf1 attack dialog.
  Every conditional already ships `default: false`, so **nothing was ever auto-applied** — the
  problem is purely that shipping them all buries the dialog in opt-in text (**89 of 184** feat
  conditionals fall in this class). A `tier` field now marks them: **A** applies by default; **B** is
  filed under the applier macro's "(NOT RECOMMENDED)" section, offered unchecked. The generator's
  payload has no such section — the FoundryVTT module attaches whatever it is given — so **tier B is
  omitted from the payload entirely**. An absent tier means A, keeping every pre-sweep entry valid.

  The field sits at **two levels**, matching the two data shapes: a feat entry *is* a single
  conditional so it carries `tier` directly, while a class-feature entry has a `conditionals` list
  whose members each carry their own. Both validators accept it and reject anything outside `{A, B}`.
  Curated pools gained three new feat conditionals (Patient Strike, Butterfly's Sting, Hammer the
  Gap), and the rogue's *positioning attack* was recurated from an always-on change into a toggle.
- **Scraped pool keys that merged two powers are repaired.** The webscrape ran a power's trailing
  body text into the **next** power's key — e.g. `"Should the bridge be attacked, treat it as a wall
  of force Spray of Shooting Stars (Su)"` — which both hid the real power (unreachable by name) and
  left a junk entry an NPC could roll. Split across oracle (×2 mysteries), vigilante, witch, ninja,
  alchemist, barbarian and fighter. Also fixes ninja's *deadly shuriken*, where a lost minus sign
  made "her highest base attack bonus −5" read as "5". Catalogued in
  `docs/conditional_open_questions.md` §3.
- **A character can be replayed through the API.** `/update_character_data` accepts an optional
  `seed`, read **by name** (like `spheres_of_power`) so the fixed 19-field positional unpack is
  untouched and older clients are unaffected. Pass back the `generation_seed` from a previous
  response to reproduce that character exactly. Until now the seed was output-only — the replay
  handle existed but was unreachable from the API the Foundry module and web sheet actually use.

  **The pop must happen before `items = list(data.items())`**: `last_5_keys` is derived from
  `items[-5:]`, so a trailing `seed` key left in the dict would displace one of the five numeric
  fields and break the int conversion.

  Generation is also now **serialized behind a lock**. `generate_random_char` seeds the
  process-global `random` (and numpy), so two generations at once in one process interleave draws —
  the second request perturbs the first and a replayed seed doesn't reproduce. `gunicorn -w 4` uses
  **sync** workers so production already serialized (the 4 worker *processes* still run in
  parallel), but Flask's dev server is threaded, which is exactly where you'd be replaying a seed to
  debug a character. At ~80 ms per generation against a 31 s cold start, the lock costs nothing that
  matters. **Rejected:** threading a `random.Random` instance through the pipeline — it would isolate
  phases properly but touches the 41 modules using the global `random`, and a process-wide seed is
  sufficient for replay. Verified byte-identical against a direct `generate_random_char(seed=…)`
  call across all 165 payload keys.
- **Character generation is reproducible: `generate_random_char(seed=…)`.** The generator took 22
  knobs and no seed, so no run could be replayed — an NPC that came out wrong was simply gone, and
  the only way to test the pipeline was to construct fake character objects and call individual
  functions (which is exactly what `test_gold_and_stats.py` and `test_skill_ranks.py` do). It now
  accepts `seed=None`, resolves it to a random value when omitted, and ships it back as the
  `generation_seed` payload key; pass that value in to reproduce the character exactly.

  **Seeding `random` alone was not enough** — three separate holes had to be closed first:
  1. **numpy.** Trait selection (`traits.py`) and spell selection (`spells.py`) go through pandas
     `.sample()`, which draws from **numpy's** global RNG, not Python's. Both RNGs are now seeded.
  2. **`random.choice(tuple(total_choices_set))`** (`feats.py::choosing_feats`) drew from a set of
     strings. Python randomizes string hashing per process, so the tuple came out in a different
     order every run and the same seed picked different feats. Now `sorted()`.
  3. **`return list(chosen_feats)`** from the same function returned a **set**, so even an identical
     selection came back in a different order — and `separate_feats_func` front-pops that list into
     the story/flaw/flavor/class buckets, so the order decided which bucket each feat landed in. Two
     runs of one seed put the same two feats in swapped buckets. The accumulator is now an
     insertion-ordered dict keyed by lowercased name; dedup semantics are unchanged.

  **Rejected alternative:** threading an injected `random.Random` instance through the pipeline. It
  would isolate phases from each other, but it touches the 41 modules that use the global `random`
  module, and a process-wide seed is sufficient for replay. **Also rejected:** pinning
  `PYTHONHASHSEED`, which makes runs reproducible without fixing anything — it would have hidden
  holes 2 and 3 rather than closing them, and can only be set before the interpreter starts.
- **Golden-payload regression test** (`Backend/scripts/test_golden_payload.py`). Generates four
  seeded characters and diffs each full payload against a committed snapshot in
  `Backend/scripts/golden/`, naming the keys that differ. `--update` rewrites the goldens; the
  convention is to commit a regenerated golden **in the same commit** as the change that caused it,
  so the JSON diff in review shows exactly what the change did to generated characters. Ollama is
  severed at import — `generate_backstory` only calls it when the backstory API is on (off here),
  but `build_archetype` reaches for the same helper to break scoring ties, which would otherwise
  make the payload depend on whether a model happens to be running locally.

  The four configs were **swept for coverage, not picked at random**: their union populates all 11
  buff side-maps, several of which are rare enough that an arbitrary seed misses them entirely (only
  **17 of 1,586** `class_feature_effects` entries carry conditionals — 4 of them rogue talents, which
  is why one config is a level-18 rogue). `Backend/scripts/report_buff_coverage.py` prints the
  per-config side-map matrix and fails if any side-map drops to zero coverage, so a config change
  that silently stops exercising a buff path gets caught.

  **Known gap, deliberately not worked around:** the `martial` config carries an absurd 5,000,000 gp
  because `enhancement_calculator` (`main_test.py:518`) runs *after* `item_chooser` (`:480`) has
  drained the purse — a realistically-funded NPC never buys a weapon or armor quality at all, so
  `enhancement_effects_dict` is empty for every normal character. That ordering is a real generator
  issue; the config exists to keep the quality path under regression until it is triaged.
- **Buff name-matching lives in one module, and mismatches are now reported.** Six code paths each
  loaded a curated buff map, normalized names their own way, and looked up the character's
  selections — feats/items/qualities in `main_test.py`, spells in `spells.py`, Spheres talents in
  `spheres.py`, PoW stances in `path_of_war.py`. Every lookup was a plain `.get()`, so a curated
  entry whose key didn't match was dropped with **no error, no log, and no sign on the sheet**. The
  rules had quietly diverged: PoW stripped apostrophes, class features stripped `(Su)/(Ex)/(Sp)`,
  items lowercased only the query, Spheres didn't lowercase at all — which spellings survived
  depended on which path you were in.

  `utils/class_func/buff_match.py` now owns the lookup behind a per-kind registry (data location,
  flat vs sectioned, key and query normalizers). **Each kind's rule is identical to what its call
  site did before**, so no buff changed — the golden payloads differ by exactly one added key.

  That key is the point: on a strict miss the lookup retries with a conservative loose key (case,
  whitespace, apostrophes, hyphens, trailing `(Su)/(Ex)/(Sp)`). A loose hit after a strict miss
  means the curated data **is** there and only the normalization failed to reach it. Those ship as
  `buff_gaps` and print at the end of a run. An ordinary "nothing curated for this name" is not a
  gap. It found a real one on the first run: the generator's spell list carries **`Orders Wrath`**
  while `spell_riders.json` curates **`Order's Wrath`**, so that rider has been silently dropped.
  **Deliberately left unfixed** — the decision was to measure first and widen each kind's rule one
  golden diff at a time, rather than change generated output blind.

  Also folds in four caches: the feat/item/quality/class-feature maps were re-read and re-parsed on
  **every generation (~1.6 MB)** because their loader was defined *inside* `generate_random_char`.
  **Excluded:** flaws (`flaws.py` draws the name *from* `flaw_effects.json`, so selection and lookup
  cannot diverge — there is no gap to find).
- **Phase ordering is enforced, not documented.** Every rule about what must run before what was a
  comment (`main_test.py:305`, `:490`, `:632`), and violating one didn't raise — it produced a
  quietly worse character. `utils/class_func/pipeline.py` adds `@phase(requires=…, provides=…)`;
  `requires` must already be set on the character, `provides` is checked on the way out so a phase
  that stops producing something fails at its own boundary. Presence uses `hasattr`, not truthiness
  — a level of `0` or an empty class list *is* set. Two phases are extracted so far
  (`phase_roll_and_assign_stats`, `phase_professions_and_skills`), chosen because they carry the
  known hazards; **the feat/PoW/Spheres block stays inline on purpose** (~600 lines of interdependent
  backfill loops).

  The fourth hazard needed a different mechanism: `data_dict['class features']` always *exists*, so
  a presence check can't tell "no chooser ran" from "this class has no choices".
  `seal()`/`require_sealed()` express that instead. `test_pipeline_phases.py` deliberately violates
  each contract and asserts the error — a guard that never fires is worth nothing.

### Fixed
- **Every scraped "electricity" effect carried a damage type pf1 does not recognise.** pf1's id is
  **`electric`** (verified against its own compendium exports: `electric` 28×, `electricity` 0×), but
  41 modifiers across the generator, the FoundryVTT module and the applier were typed `electricity`.
  The consequence is silent and in the `onCrit` family — an unrecognised type never matches, so a
  creature with **electricity resistance or immunity took the damage anyway**.
  - **Root cause was not a typo but a missing translation step.** The same `_DMG_TYPES` prose
    alternation was copy-pasted into three builders (`build_maneuver_changes.py`,
    `build_spell_conditionals.py`, `build_talent_changes.py`), and every entry in it is a real pf1 id
    *except* `electricity`. The builders scrape Pathfinder rules prose — which correctly reads "points
    of electricity damage" — and wrote the matched word **verbatim** as the id. Matching the prose
    word is right; emitting it as an id is the bug, which is why it appeared in Path of War, Spheres
    and spells simultaneously.
  - New `Backend/scripts/damage_types.py` is the single owner of the vocabulary
    (`PF1_DAMAGE_TYPES`, `DAMAGE_TYPE_ALIASES`, `normalize_damage_type`, `classify_damage_type`); the
    three builders now normalize at the emit site while keeping their prose regex intact.
  - **Rejected:** patching the 41 values alone. The builders would have re-emitted the wrong id on the
    next scrape, so the data would silently rot again.
  - Repair was structural, not textual: only members of a `damageType` array changed. "electricity" is
    correct English in rider and description prose and is untouched (verified: prose counts identical
    before and after, in all three repos).

### Added
- **`damageType` members are now validated, and Path of War has a structural validator at last.**
  The gap audit had flagged both. `validate_quality_effects.py` (which `validate_class_feature_effects`
  reuses), `validate_spell_conditionals.py` and `validate_talent_conditionals.py` now check every
  `damageType` member, and a new `validate_maneuver_changes.py` covers the PoW maneuver/stance change
  files — whose flat `{name: {modifiers, rider}}` shape no existing validator understood, and which
  `fix_maneuver_crit.py` deliberately leaves alone whenever `critical` is not `"normal"`.
  - **Errors** on a known prose alias (with the correct id in the message); **warns** on a merely
    unrecognised value, because the vocabulary is observed from compendium exports rather than
    authoritative and hard-failing an unseen-but-valid type would block real work.
  - Verified against the real data (197 qualities, 739 spells, 788 talent conditionals, 726 PoW
    modifiers) and against deliberately broken fixtures.
- **The `onCrit` bug class can no longer ship in Spheres talents or spell conditionals.** An audit of
  every hard rule in the conditional decision-rules docs against the validators found the
  `critical`-whitelist guard was only **partial**: `validate_quality_effects.py` protected weapon
  qualities (and, at promotion time, feats/class features), but `validate_talent_conditionals.py`
  never inspected `critical` **at all**, and `validate_spell_conditionals.check_modifier` didn't
  either. The exact typo that silently broke six burst weapons could still ride a Spheres talent or a
  spell rider forever.
  - Both validators now enforce `{normal, crit, nonCrit}` (`find_bad_critical`; the spell side gained
    a `MOD_CRITICAL` mirroring the quality one).
  - The Spheres decision-rules doc claimed the Path-of-War tokens `@INITMOD`/`@SKILLCHECK`/
    `@ATTACKCHECK` were rejected by "the promote check". **Nothing rejected them** — the rule existed
    only in prose. `find_pow_tokens` now actually enforces it, and the doc names the check.
  - Both new guards were verified to pass the real data (788 talent conditionals, 619 rider + 120
    buff spells) **and** to fail on deliberately broken fixtures — a guard that never fires is worth
    nothing.
  - **Known gaps, recorded not fixed:** Path of War's `maneuver_changes.json` still has no structural
    validator (`fix_maneuver_crit.py` preserves any non-`normal` value as "deliberate"), and no
    validator checks `damageType` members against pf1's built-in list.

### Changed
- **`docs/` split by purpose, and a docs doctrine recorded in `CLAUDE.md`.** Reviewing the folder
  surfaced a sharper problem than "which files move": a doc branded a *source of truth* drifts, and
  drift here had already shipped a bug. `critical: "onCrit"` — never a valid pf1 value — sat in a doc
  for months and silently broke six burst weapons; what fixed it was an executable whitelist
  (`MOD_CRITICAL`), not better prose. The skills had likewise documented caliber weights that
  disagreed with the code. **Relocating a doc does not protect it** — the OKF bundle had inherited
  both errors.
  - The doctrine now in `CLAUDE.md`: **code owns behaviour**, and a doc earns its place only when it
    holds what code cannot — *where* things are (`CODEBASE_MAP.md`), *why* a choice was made
    (`changelog.md`), *external rules* (PF1e / Sieg's Guide / 3pp → the bundle), or *not-yet-code*
    (TODOs, open questions). Never restate a tuning constant, formula or enum in prose; name the
    symbol that owns it. Hard conventions belong in a `validate_*.py`, not only in a sentence.
  - **Moved out** (authority lives outside this repo): the pf1spheres caster-level resolution write-up
    and the build-archetype taxonomy/research, plus the house **rules** themselves and the spell
    caster-level token standard. **Stayed** (things code can't hold): the codebase map, the generated
    conditional-candidates worklist, the spec/open-question trackers, and the three conditional
    decision-rules docs — those govern *hand-authored data*, not code behaviour, and 8 curation
    scripts cite them.
  - `docs/homebrew_rules.md` is no longer the "source of truth" — the Sieg's Guide docs are. It now
    keeps only the **rule → code map**, the implementation **backlog**, and the source-coverage tracker.
  - Applying the doctrine immediately caught another rotted claim: the bundle still described Path of
    War chain count as "capped by available normal feat slots", a clamp removed when the generator
    started guaranteeing Path of War with feat priority.

### Removed
- **`.claude/skills/` is gone — the domain knowledge moved to the OKF `pathfinder` bundle.** All ten
  project skills (`path-of-war`, `spheres-of-power`, `trainers-and-professions`, `foundry-conditionals`,
  `foundry-sheet-references`, `multi-buff-distributor`, `fantasy-expert`, `changelog`,
  `pull-requests`, `commit-conventions`) were folded into `oks/pathfinder/` as a **faithful superset**
  — implementation specifics (function names, file paths, verification steps) kept, not just
  summaries — and then deleted, so there is one home for this knowledge instead of two that drift.
  Reach it through the user-level `oks-bundles` skill. `CLAUDE.md` and `docs/CODEBASE_MAP.md` now
  point there, and the decision-rule docs / script docstrings were repointed off the dead paths.
  - The move **fixed drift the bundle had inherited**: trainer caliber weights `15/40/30/15` →
    `8/45/45/2`; profession feats documented as riding a `(Trainer N)` slot when they actually render
    in the general feat track; and `critical: "onCrit"` documented as valid when the real whitelist is
    `{normal, crit, nonCrit}` (the very value that silently broke the burst weapons above).
  - New bundle material: the mentor system, `contributing/` (changelog + PR conventions), and
    `generator-backend/profession-genre-and-tiers.md`.
  - **Trade-off accepted:** skills auto-surface by description, bundles do not — that guidance now
    arrives via the `oks-bundles` router plus `CLAUDE.md` instead of a skill loading itself.
  - `commit-conventions` was byte-identical to the surviving **user-level** skill, so commit
    conventions still auto-trigger.

### Fixed
- **180 bonus-spell names shipped wrong.** `clean_bonus_spells` finished with `str.title()`, which
  broke domain / bloodline / wizard-school bonus spells four ways at once:

  | stored | shipped | should be |
  |---|---|---|
  | `breath of life` | `Breath Of Life` | `Breath of Life` — Paizo lowercases connecting words |
  | `beast shape III` | `Beast Shape Iii` | `Beast Shape III` — Roman numerals destroyed |
  | `bull's strength` | `Bull'S Strength` | `Bull's Strength` — uppercase after the apostrophe |
  | `bulls strength` | `Bulls Strength` | `Bull's Strength` — source data lost the apostrophe |

  Names now resolve against `data/spells.csv` through a fold that ignores case and apostrophes,
  taking the CSV's exact spelling — which fixes all four at once, the stripped-apostrophe source
  data included, because the fold makes the stored spelling irrelevant. Further candidates are tried
  in order and **accepted only if they resolve against the CSV**, so a wrong guess costs nothing:
  source tags and modified-spell asterisks are stripped (`frightful aspectUC`), and the
  greater/lesser/mass qualifier is rewritten to the comma form the CSV uses, from either the
  parenthesized spelling (`command (greater)`) or the prefix spelling (`greater command`) →
  `Command, Greater`.

  **A qualifier that doesn't resolve deliberately does not fall back to the stem**: *Cure Critical
  Wounds, Mass* is 8th level against the base spell's 4th, so degrading would hand the character a
  different, weaker spell. A *descriptive* parenthetical is stripped, since `animal shapes (birds
  only)` is a domain restriction rather than part of the name.

  **180 unresolved → 9**, and those 9 are genuine source typos (`Slipsream`, `Vermin Shap II`,
  `Giant Vermin,`) that now fall back to word-wise capitalization instead of substituting a wrong
  spell. This matters beyond the buff maps: the FoundryVTT module resolves a spell **by name**
  against `every_spell.json`, so a mis-spelled bonus spell renders as a synthesized stand-in rather
  than the real compendium spell.
- **Tier-B class-feature conditionals are filtered too.** The tier sweep filtered feats but not class
  features, so 26 tier-B conditionals still appeared as toggles in the attack dialog. The rule now
  lives in one place — `buff_match.keep_tier_a()` — called from both sites, handling both curated
  shapes (entry-level tier for feats, per-conditional for class features) and returning falsy when
  nothing survives, so an all-tier-B power stays out of the payload rather than shipping as an empty
  toggle. `quality_effects.json` gets the same behaviour free when it is swept.

### Changed
- **The planned widening of buff name-matching was dropped, on evidence.** New
  `Backend/scripts/sweep_buff_gaps.py` generates many characters and ranks `buff_gaps` by kind.
  **210 characters produced exactly two gaps, both caused by the bonus-spell naming bug above** —
  zero in feat, item, class_feature, quality, talent or stance. That has a structural reason worth
  recording: those kinds' curated data is **generated from the same source the generator selects
  from**, so it cannot drift; only the spell maps are hand-curated against Paizo canon while names
  come from `data/spells.csv`. Widening the matcher would have masked the upstream defect instead of
  fixing it. `report_buff_coverage.py` now also **fails on curated-name collisions** (two names in
  one kind folding together, where the index silently keeps the first) — none today; it exists to
  catch the edit that introduces one.
- **Magic enhancements are bought before ordinary gear, out of a reserved share of the purse.**
  `item_chooser` ran first and drained the gold, so `enhancement_calculator` could never afford a
  tier — **every realistically-funded NPC had `enhancement_effects_dict` empty** and no magic weapon
  or armor at all. (The golden `martial` config carried 5,000,000 gp purely to keep that code path
  under regression; it is now 400,000, just above the level-16 wealth-by-level of ~315,000.)

  New `plan_enhancements()` takes `ENHANCEMENT_SHARE` (0.5) of the purse first; gear spends the rest
  plus whatever the tier table couldn't use. Both are module constants in
  `armor_and_enhancements.py`, not generator knobs — nothing in the Foundry module or web sheet UI
  would drive them.

  **The 3/2/1 divisor cascade is gone**, replaced by explicit proportions
  (`weapon 50 / armor 35 / shield 15`). Under the cascade each call took a fraction of what was
  *left*, so whichever slot ran last swallowed the remainder — and that was the **shield**. Modelled,
  it produced armor +8 / weapon +8 / **shield +9** at high wealth, and at 5,000 gp a character
  enchanted **only its shield**. Weapon-first is the priority that matters for an NPC, and no slot
  now wins by being last.

  **Fixes a gold leak**: `enhancement_calculator(character, 1)` deducted for a shield enhancement
  even when `enhancement_chooser` returns `([], 0)` for a shieldless character — with divisor 1 that
  was the *largest* of the three deductions. A shieldless character is now charged nothing and its
  15% is redistributed to weapon and armor.

  **Why `item_chooser` moved later rather than the enhancement calls moving earlier:**
  `character.shield_flag` isn't set until after the weapon and shield choosers run, so computing the
  shield reserve earlier would be blind. Verified `equipment_list`/`equip_descrip` are unused in
  between.

  **Note on the golden diff:** reordering the calls changes the *order of RNG draws*, so every
  downstream decision shifts — the goldens are entirely different characters, not a reviewable
  delta. Step verified instead against invariants across six wealth levels × two seeds: gold never
  negative, gear always bought, no shieldless shield charge, and weapon ≥ armor ≥ shield at every
  level. `test_gold_and_stats.py` rewritten against `plan_enhancements` (424 checks, up from 139).
- **Static data paths are anchored to `__file__`; the `os.chdir` at import is gone.** Both entry
  points called `os.chdir(repo_root)` at import time — a process-wide side effect just to make
  imports work, inherited by anything else in the process — purely because the data paths were
  written relative to the CWD. New `utils/paths.py::repo_path()` resolves them against `__file__`.
  Anchoring inside `Load_when_needed.__init__` covers all ~60 `Backend/json/*.json` entries in one
  place; the seven CSV reads in `feats.py`/`feat_tax.py`/`spells.py`/`traits.py`/`path_of_war.py`
  and `item_and_price.py`'s hardcoded `Backend\json\items_broken.json` (also not portable) follow.
  `traits.py` gains a cache — it was the only loader re-parsing its CSV on **every call**. Verified
  the CLI runs from the repo root, from inside `Backend/`, and from an unrelated directory, and that
  importing no longer changes `os.getcwd()`. Production was never affected: `Dockerfile` sets
  `WORKDIR /app`, so the chdir was already a no-op there.
- **The exported payload is one ordered dict literal.** It was assembled from four parallel
  positional lists — 146 values and 146 key strings **80 lines apart**, plus a second pair of 14 —
  held in alignment by nothing but position. The 146-pair had a length assert; **the 14-pair did
  not**, so a miscount there would zip-truncate and drop a payload key in silence. Now built in the
  same place in the same order, so the payload is byte-identical. The pairing was derived by
  extracting both lists with `ast` and zipping the exact source segments, **not** by reading lines:
  the value list isn't one-value-per-line (multi-line comprehensions) and several pairs don't share
  a name — `character.c_class_level` exports as `"level"`, and `character.spell_list_choose_from`
  exports **twice**. Removed `Character.export_list_non_dict`, `export_list_dict` (each a one-line
  `dict(zip(...))` whose interface dwarfed its implementation) and the uncalled
  `full_data_dictionary`. The assert is now structurally unnecessary.
- **`items_broken.json` is no longer written during generation.** `log_error()` did an unlocked
  read-modify-write of a repo file in the middle of a character — four gunicorn workers raced on it
  — and accumulated forever, so it described every item ever missed rather than this character.
  `item_chooser` now collects names on `character.unresolved_items` and prints a summary. They are
  **not** added to `buff_gaps`: the surrounding loop re-rolls until it finds a name that *is* in
  `foundry_item_names.json`, so an unresolved name is the retry loop working as intended — a typical
  character rejects a couple of dozen, which would bury the genuine mismatches.
- **Bundled sample character on the public web sheet.** The standalone
  `Pathfinder-Character-Sheet` repo now ships `data/demo-character.json` — a generated level-20
  Cleric who also walks the Path of War Martial Training chain (initiator level 10, disciplines
  Eternal Guardian + Piercing Thunder, 6 maneuvers / 8 stances, 161 prepared spells across levels
  0–9) — and `loadDemoCharacter()` in `scripts/sheet.js` renders it when a visitor's library is
  empty, in place of the "No character yet" placeholder. **Why:** the live sheet was a first-class
  portfolio link but opened empty, and the only way to see anything was **Generate**, which
  cold-starts the free Render backend — measured at **31 s**. Cleric was chosen over Wizard because
  BAB-Medium guarantees 1–3 martial-path disciplines at level 20 (the `+1 to both bounds at 20+`
  house rule lifts the floor off zero) and BAB +15 reaches Martial Training V vs the Wizard's III,
  so the Path of War tab is populated without relying on a lucky roll. **Rejected alternatives:**
  (a) leaving it as-is and relying on the existing "the backend can take up to a minute" status
  text — honest, but the first impression stays an empty form; (b) saving the sample into
  IndexedDB — it would pollute a real roster and become a record the user has to delete, so the
  sample is **render-only** and never written to the library; (c) a `?demo=1` deep link — helps
  only readers who arrive via the résumé, not ordinary first-time visitors.
- **"On Other Attacks" section in the conditional applier dialog.** The `pf1-conditional-applier`
  review dialog now shows a bottom **On Other Attacks** section listing the conditionals that live on
  the actor's OTHER, differently-named weapons/attacks — as opt-in rows (default **off**, with the
  section's all-on/off toggle and per-row include/edit, just like Spells / Path of War) that **copy the
  real conditional (its modifiers)** onto the selected weapon when applied. Deduped by name prefix
  (text before the first `:`); excludes the same-named attack twin, `──────` dividers / inert
  name-only entries, and prefixes already offered by the built-in sections or already on this weapon;
  recomputed per selected weapon. Lets you copy feat/enhancement/item conditionals (which the applier
  can't generate itself) from one weapon onto another. In
  `pf1-conditional-applier/src/apply-conditionals.macro.js` (`openDialog` `otherAttackSpecs` + the
  `On Other Attacks` rank/label in `applyToWeapon`), re-bundled.
- **Combined homebrew caster level for spell riders, resolved at attach time.** Spell-rider caster
  level now follows the campaign rule: a multiclass character's effective CL is the **sum** of each
  casting class's contribution — high/mid casters count their **full** class level, **low casters
  count level − 3** (`max(level − 3, 0)`), floored to a minimum of 1. Riders keep authoring the
  existing `@spells.primary.cl.total` token; a new `spellCLExpr()` expands it into the combined
  expression (using `@classes.<tag>.level`) at attach time — added to the generator module
  (`modify-abilities.js`, `subSpellTokens`) and the applier (`pf1-conditional-applier`,
  `subSpell`), mirroring the existing `sphereCLExpr()` path. **Decision:** compute-and-substitute
  rather than (a) authoring a raw three-book sum — pf1 leaves `@spells.<book>.cl.total` at *full*
  class level even for low casters (`casterType` only drives slots), so summing raw tokens would
  over-count every low caster by 3; or (b) fixing each spellbook's `cl.formula` at the source —
  broader/riskier and still needs the summing on top. Keeping the token means all ~619 existing
  riders upgrade with zero JSON churn.
- **Validator guard against uncomputed caster-level scaling.**
  `validate_spell_conditionals.py` now errors when a rider has a bare `[[N]] … per (caster) level`
  with no computed CL total (the "5 hit points per caster level" bug), whitelisting an external
  actor's CL ("per caster level of the …"); "per inch of thickness" never matches.
  `validate_talent_conditionals.py` now errors on malformed `@spheres.cam.total` / `@spheres.pam.total`
  (cam/pam are bare ability mods — only `@spheres.cl` takes `.total`; a stray `.total` survives
  substitution as `@abilities.x.mod.total` and silently resolves to 0).
- **Grouped section dividers in the weapon attack-roll conditionals list.** The `pf1-conditional-applier`
  now inserts inert "separator" conditionals (empty-modifier no-op checkboxes) that head each family
  block in the fixed order **General (Feats & Items) → Path of War → Spheres → Spells**, styled
  `──────  LABEL  ──────`. Rows are section-sorted so the order holds regardless of build order; the
  General header is suppressed when a weapon carries no feat/item conditionals, and per-section headers
  are suppressed for empty sections. Divider ids fold into the existing `condIds` cleanup, so re-running
  the applier stays idempotent (no duplicate separators). Changed in
  `pf1-conditional-applier/src/apply-conditionals.macro.js` (`applyToWeapon`) and re-bundled; **decision:**
  the applier owns all four separators including "General", even though the feat/item conditionals it
  labels are authored earlier by the generator module's `modify-abilities.js`.
- **Detailed spell-effect sweep — all 619 rider spells re-authored verbose + grounded.** Every
  offensive spell's `Effect` was rewritten from its full `data/spells.csv` description into a
  maximally-complete rider: per-target-type splits (living / undead / incorporeal / object),
  immunities and "no effect if already X", per-round/repeat saves, secondary targets/damage with
  their DC deltas, ability damage, durations, spell resistance, and stacking/counters. Every
  sheet-scaled quantity is now a **computed inline roll** (`[[@spells.primary.cl.total]] rounds`,
  `[[ min(20, @spells.primary.cl.total) ]] targets`) instead of "per caster level" prose, so the card
  shows the real number. The primary save shows once as the `Save:` clause; the body carries only
  secondary/nuanced saves. Pipeline: `build_spell_rider_worklist.py` → a Sonnet author→verify/repair
  workflow (42 agents, 0 held) → `merge_spell_riders.py` → `enrich_conditional_riders.py` →
  `validate_spell_conditionals.py`. `spell_riders.json` grew 213 KB → 545 KB; sample output in
  `docs/spell_rider_pilot_samples.md`. The `pf1-conditional-applier` bundle was refreshed. (The
  number-bracketing validator now correctly ignores ordinals like "1st level".)
- **Six-detail conditional riders + a per-weapon editable apply pop-up.** Every curated conditional
  now spells out all six details a player needs at a glance — damage, save DC/type, range, aux
  effects, activation, and cost — as `; `-separated **labeled clauses** (`Cost:` → `Activation:` →
  `Range:` → `Save:` → `Effect:`). A new idempotent `Backend/scripts/enrich_conditional_riders.py`
  (with shared builders in `Backend/scripts/conditional_clauses.py`) appends only the *missing*
  clauses to the already-curated finals — `Range:` (CL-scaled feet + delivery from the CSV `range`
  column), `Cost:` (gp material components; real sphere spell-point counts, fixing the seed's
  hardcoded `[[1]]`), and injects the computed spell save DC `[[ 10 + @slvl + @castMod ]]` into
  existing save clauses — leaving hand-written text untouched (re-running is a no-op). `build_*`
  seeders reuse the same helpers so new drafts start enriched. The generator module's
  `addSpellRiders`/`addSpellConditionals` now substitute `@slvl`/`@castMod` (spell level + casting
  ability) so NPC sheets render the DC. On the applier side, `pf1-conditional-applier`'s macro grew a
  **per-weapon dialog**: pick a weapon, review the full list of conditionals about to be added, toggle
  each on/off, expand a row to edit its clauses / per-roll default, then "Apply to this weapon"
  (`actions[0]`, with an action picker when a weapon has several). The dialog stays open to walk every
  weapon, and edits **persist per weapon** in a `flags["pf1-conditional-applier"].overrides` actor
  flag so they survive the idempotent re-apply.
- **Bulk-promoted the spell-conditional draft into the curated riders.** `spell_riders.json` grew
  from **239 → 619** curated rider spells (Bucket B damaging-touch + Bucket C offensive
  save/area/debuff) via the new `Backend/scripts/promote_spell_conditionals.py`, which merges the
  reviewed `spell_conditionals.draft.json` under the same gates the palette uses: curation wins on a
  name clash; harmless-save misreads (48), `(see spell description)` save-only C stubs (559), and
  empty-shell B entries (37, their damage already on the compendium spell) are dropped. Bucket A was
  already fully curated (120 buff spells, unchanged). `validate_spell_conditionals.py` passes.

### Fixed
- **`inherents="N"` crashed the generator.** `character.inherents` was assigned in exactly one place —
  `create_inherents_func` (`stats.py:121`), reachable only from the `if inherent_flag != 'n'` branch —
  and `Character.__init__` never initialized it, so turning inherents off raised
  `AttributeError: 'Character' object has no attribute 'inherents'` at payload assembly
  (`main_test.py:1407`). `level_up_stats` was unaffected: it is called unconditionally and always
  assigns. Now `__init__` publishes both `inherents` and `level_up_stats` as `{}`, and the disabled
  branch of `roll_stats` writes a **zeroed `{stat: 0}` dict of the same shape**
  `create_inherents_func` produces. **Why the zeroed dict and not just the `__init__` default:** the
  Foundry module builds an "Inherents" buff straight from this dict, so the right shape matters —
  `{}` would only have stopped the crash. **Rejected alternative:** making the export site defensive
  with `getattr`; it is one of ~5 readers, and the real defect was a field that wasn't always set.
- **Characters bought their way into negative gold.** Two spenders both subtracted *before* checking
  affordability:
  - `item_chooser` (`item_and_price.py`) deducted the price, then `break`-ed on `gold <= 0` — so the
    character paid for an item that was never added to `equipment_list`, finished with a negative
    purse, and abandoned **every remaining slot** even when something cheap would have fit. It now
    checks first and, when a slot's roll is unaffordable, skips that slot and continues the batch. Ring
    bookkeeping (`grab_two_rings`) only runs on a real purchase, so a skipped ring doesn't burn the
    second-ring slot.
  - `enhancement_calculator` (`armor_and_enhancements.py`), called three times (armor ÷3, weapon ÷2,
    shield ÷1), took the `enhancement_bonus_mapping` key **closest** to its budget. The table starts at
    2000, so for a poor character the closest key is the one *above* what they have: 500 gold budgeted
    166 and spent 2000, leaving −1500 — three times over. It now takes the largest tier at or below the
    budget and spends nothing when even +1 is out of reach (`enhancement_chooser` already returns
    `([], 0)` for a bonus below 1).

  `subtract_price_from_gold`'s fallback branch used to zero the character's **entire purse** whenever a
  price was unusable; it now leaves gold alone and logs. Removed `bonus_gold_calculator`
  (`armor_and_enhancements.py`) — dead code (its only reference was the unrelated
  `character.bonus_gold_calculator` method inside its own body) that also deducted unchecked. A guard
  before `character.platnium = character.gold / 10` clamps and warns, so a future spender cannot
  silently reintroduce a negative purse (and negative platinum with it).

  **Accepted consequences of "skip the slot, keep the remainder"** (both chosen deliberately over the
  alternatives): an NPC too poor for a slot's roll simply leaves it empty rather than re-rolling for
  cheaper gear, and unspent gold now stays on the sheet instead of being driven to ~0 — a level-20
  character can finish holding a six-figure purse. A 300-gold level-20 test character buys nothing at
  all and keeps all 300, which is the rules-correct outcome.
  Guarded by `Backend/scripts/test_gold_and_stats.py` (139 checks; `--slow` adds an end-to-end
  generation with `inherents="N"` and a 300-gold purse): gold never goes negative, the batch continues
  past an unaffordable slot, every listed item was actually paid for, the enhancement tier is the
  correct affordable one across a gold sweep at all three divisors, and the inherents dict is present
  and zeroed when disabled.
- **Four sheet/module readings of the `level` payload key that wanted a different level.** The payload
  ships `level` (= `c_class_level`, the **primary class's** level — documented as legacy at
  `main_test.py:1461`) and `total_level` (the true total). Nothing consumed `total_level`; everything
  read `level`, so an Alchemist 10 / Barbarian 6 / Wizard 4 was treated as level 10 throughout.
  Fixed the four sites that wanted something else, leaving the key's meaning alone:
  - *Web sheet feats footer* (`sheet.js` `renderFeatCounts`) — the "By level" box is `ceil(level / 2)`
    and drives a red **Missing/Excess** badge; the test character reported a 5-feat entitlement against
    10 owned and flagged "Excess 5". Now `ceil(totalLevel(data) / 2)` → 10, badge clears.
  - *Web sheet caster level* (`casterLevelValue`) — `caster_level` is **user-entered only** (the
    generator never ships it), so a fresh import always fell through to the primary-class level. Now:
    explicit override → the campaign's homebrew **combined** CL → total level.
  - *Web sheet class labels* (class-sheet card title + class picker) — every class card printed the
    primary's level ("Wizard — level 10"). Now each shows its own (10 / 6 / 4).
  - *Foundry module aura ranges* (`modify-abilities.js` `addSpellBuffs`) — the caster-level proxy that
    turns close/medium/long into concrete feet for the Multi-Buff Distributor. New numeric
    `spellCasterLevelNum()` sits beside `spellCLExpr()` and mirrors it exactly.

  **The combined-CL rule:** `spellCLExpr()` already encodes it — each casting class contributes its full
  class level, or level−3 for a `low` caster, summed and floored to 1. `caster_formula` (`spells.py:42`)
  already bakes the −3 into each book's `casting_level_num` (only the `low` branch subtracts), so
  `Σ casting_level_num` is its numeric twin. The test character is CL **14** (Alchemist 10 + Wizard 4),
  not 10. **Rejected alternative:** the *highest* book's CL, or `total_level` — both are wrong in a new
  direction rather than right.
  **Why `totalLevel()` derives instead of reading `total_level`:** `level` is editable in the sheet
  header (`editNum(data, 'level', …)`) while `classes[]` and `total_level` are not, so the stored total
  goes stale the moment a level is edited — reading it would freeze the feat count for the single-class
  majority. It computes `level + Σ secondary class levels` instead, which is safe because `classes[]`
  arrives level-descending (`level_and_bab.py:57`). Likewise `classLevelFor()` falls back to `level`
  rather than the total, so a user-added class never inherits a fabricated "level 20".
  Backend unchanged. Verified in-browser against a generated Alchemist 10 / Barbarian 6 / Wizard 4:
  By level 10, Caster level 14, per-class labels 10/6/4 — and with `classes`/`spellbooks`/`total_level`
  stripped (a pre-multiclass payload) every value falls back to the old rendering exactly.
  **Left alone deliberately:** `modify-abilities.js:660`, `createCharacter.js:107` and `sheet.js:1287`
  legitimately want the primary-class level (they are the `classes`-absent fallbacks).
- **Characters now spend their skill ranks exactly.** Generated NPCs were silently losing a chunk of
  their skill budget between the generator and the sheet — the reference case (Monk 8 / Summoner 7 /
  Wizard 5, level 20) was owed 264 ranks and reached Foundry with 241 flat ranks plus a Profession
  block reading 1/0/0/0 against a bio claiming 15/10/10/10. Five independent leaks, all silent:
  1. **Unrenderable skills ate ranks.** `data.skills` carried `gather information` (not a PF1 skill),
     `knowledge martial` (pf1-pow's `kmt`, absent from the module's `base_skill.json`), `lore` and
     `artistry` (pf1 *container* skills — `containerSkills: ["art","crf","lor","prf","pro"]` — whose
     ranks must live in `subSkills`, so ranks on the container are unusable), plus a **duplicate**
     `profession`. Any ranks spent there were dropped by the Foundry module and by the web sheet.
     The pool is now the 35 core PF1 skills that all three consumers actually render.
  2. **No min-1-rank-per-level floor.** The budget was `class_points + mental_mod × level` with no
     floor, so a level-20 Fighter (2/level) whose best mental mod was −2 budgeted **zero** ranks and
     −3 went negative — a completely blank skill block. Now floored **per class level**
     (`max(1, points + mental_mod) × class_level`, summed), which is where PF1 puts the floor and
     which composes correctly across a multiclass build.
  3. **A narrow skill sample silently discarded the remainder.** `skill_number` could sample fewer
     distinct skills than the budget needed (each skill caps at character level), and the assignment
     walk then hit its `all(... >= max)` break and threw the leftover away. The selectable set is now
     topped up on demand until it can physically hold the budget, and the walk draws only from skills
     with room left, so it terminates at exactly zero remaining.
  4. **The favored-class bonus paid for the wrong number of levels.** `favored_class_calculator` used
     `c_class_level` — an alias for the *primary* class's level — so the reference character was paid
     for 8 of his 20 levels, in both the HP and skill-rank branches. Now `character.level`, matching
     the total-level treatment of inherents and level-up bumps below.
  5. **An empty favored-class slot.** `favored_class_option` appended the racial favored-class option
     even when `CoreRaces.json` had no entry for that race/class pair, so ~1 in 3 non-humans rolled a
     bonus that was the empty string and did nothing. Falsy entries are now filtered out.

  **Why per-class rather than a single floor on the total:** PF1 states the floor per level, and a
  lump-sum floor of `character.level` would under-pay a high-skill class that happens to have a bad
  mental mod (a Rogue 10 / Fighter 10 at mod −3 is owed 50 + 10, not a flat 20). **Why top up capacity
  on demand rather than widening the breadth formula:** raising `skill_number` generally would spread
  every low-Int NPC across many more skills, changing the "focused specialist" texture; topping up only
  when the sample is genuinely too narrow leaves typical characters untouched. The 1–3 rank chunking of
  the assignment walk is deliberately unchanged — it is what gives NPCs their uneven, lived-in profile.
  Guarded by `Backend/scripts/test_skill_ranks.py` (3,000+ assertions over randomized builds: exact
  spend, renderable keys only, per-skill cap, the floor, capacity top-up, and the profession
  invariants). Touches `Backend/utils/data.py`, `Backend/utils/class_func/skill_ranks.py`,
  `favored_class.py`, `Backend/main_test.py`.
- **Profession ranks reach the Foundry sheet.** The module was splitting the *ordinary* Profession
  skill rank evenly across the character's professions and ignoring the `profession_ranks` payload
  field the backend already ships — which is how a 45-rank homebrew pool rendered as 1/0/0/0. The
  `pro` subskills now read `profession_ranks[i].ranks` directly; the backend owns the pool, the caps,
  True Calling and Always Improving, and the module does no arithmetic of its own
  (`modify-abilities.js`). It also now `console.warn`s instead of silently dropping any rank key it
  cannot place, so backend/module drift is visible rather than invisible.
- **Ordinary skill ranks no longer leak into Profession.** Professions run on their own homebrew rank
  pool, so ordinary ranks may only be spent there with the **Always Improving** feat (the house rule).
  That gate is now real: `profession_chooser` runs *before* `skills_selector` (verified safe — neither
  it nor `profession_abilities` reads `skill_ranks` or `craft_chosen`), Profession is excluded from the
  ordinary pool unless the feat is present, and `apply_always_improving_ranks` folds any ranks that did
  go there onto the True Calling profession, capped at character level and spilling to the next.
- **Inherent rolls and level-up ability increases now scale with total character level.** For
  multiclass characters both were undercounted because they keyed off the primary class's level
  instead of total level: `roll_inherents_func` rolled `floor(c_class_level / 2)` times and
  `level_up_stats` granted `floor(c_class_level / 4)` ability bumps. Both now use `character.level`
  (`Backend/utils/class_func/stats.py`), so a total-level-20 build gets the correct 5 ability bumps
  (levels 4/8/12/16/20) and the full inherent-roll count regardless of how levels split across
  classes. Single-class characters are unaffected (`c_class_level == level`). Skill ranks, BAB, and
  saves already summed correctly across classes.
- **Damage-dealing conditionals no longer render their damage type as "undefined."** A conditional
  damage modifier with an empty `damageType` displayed "undefined" on the pf1 sheet (pf1's damage-roll
  `??=` only defaults null/undefined, not an empty Set), and a conditional modifier can't inherit the
  weapon's type. Two-part fix: (1) **attach-time coercion** — the module (`modify-abilities.js`, all six
  modifier-build sites via a `dmgTypeOrUntyped` helper) and the applier (`mkMod`) coerce an empty
  `damageType` on a **dice** damage instance to `["untyped"]`, and `build_data.py` defaults typeless
  compendium parts (detonate, poisonous cloud) to `["untyped"]` — so the sheet never shows "undefined";
  (2) **curated the real element** on 65 dice damage modifiers (`spell_changes.json`, the module's
  magic/combat talent finals + the backend drafts, `feat_conditionals.json`) — e.g. Ectoplasmic
  Eruption → bludgeoning, Face of the Devourer → piercing, Nature/Earthquake → bludgeoning, Death-sphere
  strikes → negative; genuinely variable / per-strike / mixed damage (dragon breath, Detonate, martial
  strikes, the destructive-blast base) → `["untyped"]`. `validate_spell_conditionals.py` /
  `validate_talent_conditionals.py` now **WARN** (non-blocking) on any dice damage modifier with an
  empty `damageType`. Weapon-riding physical dice (Gravity Bow, Lead Blades, per-strike martial strikes
  — Deadly Shot / Fatal Thrust / Sever / Skewer / Limb Ripper / Clinch Strike / Shatter / Sword Shooter
  / Dolphin Strike / Forceful Jaunt / Open Vein — and the Savage Display feat) carry an `["as-weapon"]`
  sentinel that the module (`weaponDamageTypes`/`dmgTypeOrUntyped` on all attach sites) and the applier
  (`mkMod`) resolve **at attach time** to the target weapon's own damage type (pf1 v11 `type.values` or
  older `types`), so the bonus dice show the weapon's real slashing/bludgeoning/piercing (untyped
  fallback when the weapon has none). This avoids the conditional-can't-inherit limitation without a
  `wdamage`-Change (whose dice roll-vs-maximize behavior is unverified).
- **Spell riders that shipped a constant where a caster-level total was meant.** Converted the
  missed scaling in `spell_riders.json`: Blast Barrier (`[[5]] hit points per caster level` →
  `[[5*@spells.primary.cl.total]]`), Blazing Rainbow (bridge length), Fire Snake (affected squares),
  Curse of Unexpected Death (reduced damage, rider + `save.description`), Bloodbath (affected
  creatures), and tidied dangling "per caster level" prose on Wall of Bone / Warp Metal / Wall of Ice
  (which already carried the computed total). Nightmare (external dispel-evil CL) and "per inch of
  thickness" object-HP phrasings left as prose.
- **Applier left `@spheres.*` tokens raw**, so sphere talent riders/DCs applied via the macro read 0
  on an actor without live pf1spheres data. The applier now substitutes `@spheres.cl.total` (BAB-tier
  caster level) and `@spheres.cam`/`@spheres.pam` (→ ability mods) for such dabblers, while a real
  spheres caster (native `@spheres.cl.total > 0`) keeps the native tokens.

### Removed
- **Dropped the "Spell Conditionals (Rider Spells)" compendium pack** (it only duplicated pf1's
  built-in spell compendium). Unregistered from the module's `module.json` `packs[]`, and deleted the
  build chain `Backend/scripts/build_spell_conditional_compendium.py` +
  `Backend/scripts/_compendium/` (the `spell_conditionals_items.json` docs + the `pack_pf1_leveldb.js`
  LevelDB compiler — both preserved in the new `pf1-conditional-applier` repo's `build/`). The
  curated `spell_riders.json` / `spell_changes.json` stay; they now feed the external applier macro
  (below). The on-disk pack dir `<module>/packs/spell-conditionals/` is inert once unregistered —
  delete it after closing Foundry.
- **Superseded by an external tool:** conditional delivery moved out of a draggable
  compendium/palette into the new **`pf1-conditional-applier`** repo — a run-on-demand Foundry macro
  that scans an actor and wires its Path of War + Spheres + spell (A/B/C) conditionals onto all its
  weapons, idempotently, with a coverage-gap report. Reuses `spell_riders.json` / `spell_changes.json`
  + the module's maneuver/talent conditional dicts.

### Changed
- **Profession feats: reachable, level-scaled, and only Multi Talented buys ranks.** `Always Improving`
  was previously unreachable — `_roll_profession_feat_count` returned at most 2 and
  `_pick_profession_feats` sliced the list top-to-bottom, so the third feat was never taken. Now the
  roll is `random.choice([0,0,1,1,2,3])` (curated builds still floor at 2) **plus one guaranteed feat
  per 10 character levels**, and the order is **Multi Talented → True Calling → Always Improving →
  Multi Talented ×(remaining)**, with Multi Talented repeatable `1 + level//10` times. Each repeat is
  its **own** feat entry (`Multi Talented`, `Multi Talented (2nd)`, `Multi Talented (3rd)` — mirroring
  the `Extra Magic Talent (<suffix>)` convention in `spheres.py`), never collapsed into one line:
  `main_test.py` reserves feat slots with `len(character.profession_feats)`, so a collapsed entry would
  buy +10 profession ranks per repeat while paying the feat tax only once. The rank pool is now
  `5 + level + 10 × (Multi Talented picks only)` rather than `10 × (all profession feats)` — True
  Calling and Always Improving are riders on a pool, not purchases of one. The `n` ceiling
  (`3 + level//10`) and the Multi Talented repeat cap (`1 + level//10`) agree exactly at every level, so
  no pick is ever wasted. **Accepted consequence:** a low-roll level-20 build's pool drops from 45 to
  35, since its two picks now buy no ranks. **Rejected alternative:** reading Multi Talented literally
  as "+10 to the per-profession *cap*" — truer to the feat's wording, but it contradicts how the repo
  already implements it and a single Profession at rank 45 would break the rank-5/rank-15 ability tiers.
- **Profession ranks spread unevenly instead of filling each vocation to its cap.** The pool used to
  fill professions to 15/10/10/10 in order and clamp at a hard `_MAX_PROFESSIONS = 6`, which truncated
  large pools. Now the True Calling profession takes its 15-rank cap first and the remainder is split
  into a profession count chosen **up front** (`ceil(remaining/10) + randint(0,2)`), each vocation
  getting a random 1–10 ranks and the split summing to exactly the pool by construction. Gives the
  "one strong vocation plus a few dabbles" texture and removes the last place a rank could be silently
  truncated. **Rejected alternative:** draw professions until the pool empties — simpler, but an
  unlucky run of 1s produces fifteen vocations and any ceiling re-introduces the truncation.
- **One canonical skill list.** `Backend/utils/data.py` now owns both the skill pool (`skills`) and the
  name → pf1 id map (`SKILL_IDS`); `feat_skill_choice.py` imports it instead of keeping a private copy.
  `Backend/scripts/build_item_changes.py` deliberately keeps its own, looser `SKILLS` map — that one
  *parses* scraped rules prose and must still recognise Lore/Artistry and common typos even though the
  generator never grants ranks in them.
- **Weapon attack-roll dialog is now scrollable and resizable so the Attack button is always reachable.**
  The pf1 attack dialog uses `height:"auto"` with no inner scroll, so a weapon stacked with many
  conditionals grew the window past the viewport and pushed the Single/Full Attack buttons off-screen.
  A new stylesheet in the generator module (`pf1e_random_char_generator/styles/attack-dialog.css`,
  registered in `module.json`) flexes the `.conditionals` list to fill the dialog and scroll internally;
  other fields and the roll buttons stay put. A companion ready-hook patch
  (`scripts/attack-dialog-resize.js`) sets `resizable:true` on pf1's `AttackDialog` **and opens it at a
  concrete height (600)** so the whole pop-up can be dragged larger/smaller in **both** directions, with
  the conditionals area growing/shrinking to fit. **Decisions:** conditionals-only scroll was chosen over
  a whole-form scroll + sticky footer (avoids nested scrollbars / scroll-trapping); the native resizable
  *window* was chosen over a CSS-only resizable *panel* (dragging the window is more discoverable) at the
  cost of a small JS patch of the pf1 class; a concrete initial height was required because pf1's stock
  `height:"auto"` snaps the window back to content height, so a dragged height never sticks and only
  width would resize (no CSS `max-height` cap — Foundry already clamps the window to the viewport); and it
  all lives in the always-on generator module rather than the auto-generated `systems/pf1/pf1.css` so it
  survives pf1 system updates. Ships to other users only on the next module release.
- **Spheres-of-Power save DCs and blast damage now scale with a real caster level.** Generated NPCs
  are Spheres *dabblers* with no spherecasting class, so pf1spheres derived `@spheres.cl.total` = 0 and
  the module baked a flat caster level 1 into every Power DC/blast — pinning them at CL 1 regardless of
  level. The module's `subSpheres()` / `applySpheresFlags()` (`modify-abilities.js`) now substitute a
  **live, tier-accurate, multiclass-summed** sphere caster level built from the NPC's real caster
  classes: `max( Σ per caster book {high: @classes.<tag>.level, mid: floor(3·level/4), low:
  floor(level/2)}, 1)` (Pathfinder rounds down; caster levels stack per Spheres RAW; floored to 1).
  Safe because Power talents are only ever assigned to real casters (a non-caster gets Might only), so
  each has a populated pf1 spellbook; using class *level* (not spellbook CL) also matches the campaign's
  ½/¾/full model and sidesteps low casters' "no spells until L4". The authored data and the class-less
  Spheres **palette** keep native `@spheres.*` tokens (unchanged) so copies still scale on a real
  pf1spheres PC. Kineticist / spell-point classes with no spellbook remain floored to CL 1 (deferred).
- **Multiclass generation now caps caster classes at 3.** pf1 has only three spellbook slots, so a 4th
  caster's spellbook (its spells *and* its sphere-CL contribution) was silently dropped on the Foundry
  sheet. `select_classes()` (`Backend/utils/util.py`, new `_is_caster` helper) now stops drawing caster
  classes once three are picked; remaining multiclass slots fill from non-casters. Non-caster-heavy
  builds still reach four total classes.
- **Spells palette: spells re-sorted across the Items and Buffs tabs by role.** The `Spells_template`
  Items (inventory) tab now holds three conditional-toggle weapons in a fixed order under `____ … ____`
  dividers — **Self Buffs** (Bucket A cast-on-self buffs, 120 toggles), **Debuffs** (Bucket C enemy
  save/effect conditionals, `attack == null`), and **Damaging Spells** (Bucket B touch-attack spells,
  whose dice are pulled from the compendium so they roll real damage). The Buffs tab's **spells**
  section keeps only self-buffs that have `changes` or `contextNotes`; **debuffs moved to the
  Temporary section** (Bucket C only, distributable `(UNAMED)` onlyOthers buffs). Bucket-C debuffs
  appear in both places (rollable weapon + distributable buff), mirroring Path of War. The redundant
  Spellbook-tab rider-spell clones were dropped (B is now the Damaging weapon, C the Debuff weapon).
- **PoW palette weapons tab gets section headers; spell-buff toggles sorted by level.** Each
  template actor's weapons tab opens with a non-rollable divider weapon (`____ Spells ____`,
  `____ Path of War ____`, `____ Spheres ____`). The single "Spell Buffs — curated (cast-on-self)"
  weapon keeps one toggle per curated buff spell (120), now sorted by and prefixed with the
  spell's lowest class-list level (`(L3) Heroism: …`). Everything stays ONE copy — a per-class-list
  duplication pass (22 weapons / per-class rider spells / per-class buffs, 6 160 items) lagged
  Foundry unusably and was reverted same-day.
- **Spells sheet Buffs tab reorganized into `____ BUFFS ____` and `____ Debuffs ____`.** The
  distributable `(UNAMED)` buffs drop the placement-bucket dividers for the module's duration
  method (rounds / minutes / hours / other sub-dividers, level-sorted, `Aura Range` first line +
  `onlyOthers;` when set — 579 buffs). A new Debuffs section holds the enemy-targeted spells (the
  offensive pool behind the rider spells, 606 at `--debuffs all`; `curated` ≈ 240 if the sheet
  lags): each is an inactive `(UNAMED)` buff to place ON the target via the Multi-Buff Distributor,
  description leading with `Aura Range: X` then `onlyOthers;`, followed by the save + rider text +
  compendium stat block. Spells that parsed into both pools (e.g. Cause Fear) render under Debuffs
  only, keeping their changes/notes.
- **The palette now ships as THREE template actors instead of one.** One combined actor was too
  heavy for a single sheet, so `build_pow_template_actor.py --out DIR` now writes
  `Spells_template.json` (spell-buff weapon + rider spells + BUFFS/Debuffs sections, 1 803 items),
  `Path_of_War_template.json` (30 discipline weapons + stances, 233 items) and
  `Spheres_template.json` (sphere weapons + blast + sphere buffs, 119 items), each opening with its
  `____ Section ____` weapons-tab header and cloned from the same base skeleton (`pf1spheres` flags
  only on the Spheres actor).

### Added
- **Offensive spells now ship explicit save/damage/debuff conditionals (Bucket C).** The spell
  conditional classifier (`Backend/scripts/build_spell_conditionals.py`) gained a third bucket
  beyond attack-buffs (A) and touch-attack riders (B): any non-touch offensive spell — area/save
  damage (Fireball, Lightning Bolt), save-or-suffer (Hold Person, Phantasmal Killer), debuffs and
  conditions (Bane, Slow, Glitterdust) — gets a formal `save` block plus **default-on rider
  conditionals** that restate the save clause and full effect with every number (and per-CL damage
  formulas like `(min(10, @spells.primary.cl.total))d6`) as `[[ ]]` inline rolls, per the house
  "always explicit" rule. Batch 1 curation: **220 new spells** in
  `Backend/json/spells/spell_riders.json` (83 hand-authored gold entries for the RAW classics +
  137 vetted drafts; 239 total curated, prioritized by class-list breadth ∩ `every_spell.json`).
  Flows through the existing plumbing unchanged — generated NPCs get them via
  `spell_riders_dict` → the module's `addSpellRiders`, and the uploadable palette bundles them
  (now 606 rider spells, with the same harmless/stub curation gates applied to draft entries).
  New validator gate: `Backend/scripts/validate_spell_conditionals.py` (shape, save types,
  bracketed numbers, no PoW tokens, compendium-name warnings).
- **Every NPC now gets a build archetype + tactics line from a deterministic scorer** (Keep
  Away Fighter, Team Buffer, Magic Battlefield Controller, Trickster, …). The roster is a
  **generalized 33-entry two-axis set** — 7 role families × 16 tactical patterns, so an
  archetype captures *how the character plays* (charge-alpha vs full-attack-grind, save-or-suck
  vs zone-denial, …), not just its gear — deliberately free of system-branded or one-build
  labels: Path of War initiators and Spheres practitioners classify into the same generalized
  archetypes via their discipline/sphere signals (an Iron Tortoise warder is an AC Tank, a
  warlord is a Team Buffer), and famous-build names folded into their concepts (God Wizard →
  Magic Battlefield Controller; Reach Tripper/Sentinel → Keep Away Fighter; Battle Priest/Bard →
  Self vs Team Buffer). Persisted as `Backend/json/build_archetypes.json` with research +
  fold-in map in `docs/build_archetype_research.md`. The decider (`build_archetype.py`,
  rewritten) scores every entry from ~65 normalized build signals (casting tier/leans, BAB tier,
  PoW discipline tags, Spheres system/tags, weapon style/reach/crit, feat-bucket leanings, pets,
  mobility/stealth/precision/AoO packages) behind hard requires/veto gates — the structural fix
  for "wizard with a backup crossbow = Archer" — then L1-normalizes, and settles photo-finishes
  by specificity rank; Ollama is demoted to an optional near-tie arbiter, so production (no
  Ollama) gets identical answers. Shown as `- Archetype:` / `- Tactics:` in the biography fact
  block; exported as `build_archetype` + new `build_tactics`. Regression suite:
  `Backend/scripts/test_build_archetype.py` (37-fixture matrix — every non-Generalist archetype
  proven — plus determinism/parity/never-raises invariants and an `explain` mode for tuning).
- **Every NPC now rolls a casting tradition** (casting ability + Spheres drawbacks/boons), not just
  sphere-magic dabblers — latent flavor for pure martials describing how their magic would work.
  The mana pool remains dabbler-only. Exported as before via `casting_tradition` /
  `sphere_drawbacks` / `sphere_boons`.
- New `formatted_bio` payload key: a scannable, line-broken biography fact block
  (identity → professions → craft → trainers → family → traits → appearance, per the house
  Formatting.docx layout), built by `structured_bio()` in `Backend/utils/class_func/backstory.py`.
  Consumers render it at the top of the Biography with the prose backstory below, replacing the
  old raw labeled dump that previously landed in the Foundry Notes tab.

### Changed
- **Weapon rolls no longer dump the enchantment rules text into chat** (Foundry module): pf1
  bakes an item's description into its attack chat card, so the generated weapon is now split —
  the inventory weapon item keeps the full formatted description (base text, "Special
  abilities: …" summary, and a titled rules block per quality) but leaves the Combat tab
  (`showInCombat` false), while the attack-type twin (already created for Scaling Weapon Damage)
  becomes the sole rolled entry and carries only the one-line summary as its description. The
  quality conditionals (distilled house text with `[[ ]]` rolls + mechanical modifiers) ride on
  both twins' actions, so the roll card shows just rolls, conditionals, and the summary.
  Armor/shield rules text is untouched (those items are never rolled).
- **Every family roll now includes parents AND household.** `randomize_parents` rolls a status for
  each parent (loving/absent/dead) plus the household situation (wealthy/middle income/poor, or
  orphanage/adoption when no loving parent remains) instead of a single phrase that was EITHER
  parents OR a situation — so the biography's Family section always shows mother, father, and
  financial situation. Sibling counts are always listed too (explicit "No Siblings" when all zero).
- The biography fact block (`formatted_bio`) is now labeled bullet sections — noun headers
  (Name / Vocation / Family / Personality / Appearance) with one `- Label: Value` fact per line —
  so it reads as a clean prompt a GM or an AI can build a story from.
- **Prose backstories are disabled for now**: the backend exports `backstory` as an empty string
  (no Ollama call), so sheets show only the fact block. `generate_backstory` and its config /
  few-shot examples remain intact for the website to iterate on later.
- Prose backstories no longer end with the labeled Personality/Mannerisms/Appearance/Flaws list —
  the structured `formatted_bio` block already shows those facts. The Ollama prompt no longer asks
  for the list, the offline template no longer appends it, and `generate_backstory` defensively
  strips any trailing labeled paragraphs the model still imitates from older few-shot examples.
- **Spell buffs are now bucketed like items** (changes / contextNotes / unplaced).
  `build_spell_buffs.py` reuses the item sentence classifier from `build_item_changes.py`, so
  situational bonus sentences become targeted `contextNotes` instead of always-on changes and
  anchor-less effect text lands in a new `unplaced` bucket (kept in `spell_buffs.json` as
  reference data for the upcoming spell-conditionals work — see `docs/feature_spec_todo.md` §7).
  Spells with nothing but unplaced text no longer produce a Buffs-tab buff, cutting the
  description-only bulk; buffs that remain now carry their contextNotes onto the sheet.
- The PoW palette actor's distributable spell-buff section is now grouped by those same placement
  buckets (mechanical changes / situational — skills / situational — other) instead of by duration,
  and unplaced-only spells are dropped from the palette (922 → 676 buffs), matching the module's
  `addSpellBuffs()`.
- **Multiclass payloads are now level-sorted.** `character.classes` (and therefore the `classes`,
  `spellbooks`, and `archetypes_per_class` payload keys plus the web-sheet header) are ordered
  highest class level → lowest, with level ties broken by caster tier (high > mid > low) then
  roll order. The Foundry module maps caster classes onto the primary/secondary/tertiary pf1
  spellbooks in that order, so the highest-leveled caster's book is always "Primary".
- Each exported spellbook dict now carries `casting_stat` (the class's casting ability from
  `caster_mod`) and `divine` (bool), so consumers no longer derive them from the primary class.
- The web sheet labels multi-caster spellbook sections "Primary/Secondary/Tertiary: Class Level
  — Caster Level N" to match the Foundry book slots.

### Added
- `docs/CODEBASE_MAP.md`: a "where do I find X" appendix (pipeline order, class-choice bucket →
  data-file table, JSON/module/script indexes, gotchas) so tooling and contributors can locate
  code/data without repeated searching; linked from CLAUDE.md with a keep-it-updated rule.
- `Backend/scripts/audit_class_choice_descriptions.py`: audits every class-choice pool
  (talents, rage powers, hexes, discoveries, arcana, revelations, bloodlines, orders, blessings,
  inquisitions, spirits, …) for entries with empty/trivial description text — including the
  scraper field-glue case where benefit prose ends up inside `prerequisites` — and exits 1 with
  a per-class report.
- New payload key `class_feature_owners` (bucket → granting class): every class-feature chooser
  (talents, hexes, domains, wizard school, mysteries, orders, trainings, ...) records which class
  granted its bucket, enabling per-class "Class Features (Class)" grouping on character sheets.
- **Class-choice powers now carry mechanical effects.** Rage powers, ki powers, hexes,
  rogue/ninja/slayer/investigator/vigilante talents, magus arcana, discoveries, mercies,
  cruelties, arcanist exploits, oracle revelations/curses, and fighter trainings (~1,580 powers
  across 18 lists) now ship pf1 `changes`/`contextNotes`/weapon-toggle `conditionals` in two new
  export dicts (`class_feature_changes_dict`, `class_feature_conditionals_dict`), mirroring the
  feat/item buff pipeline. Auto-drafted from the class-data pools by
  `Backend/scripts/build_class_feature_changes.py` (draft entries ship contextNotes only), with
  ~54 hand-curated top powers in `class_feature_effects_overrides.json` (rogue-talent curation
  propagates to ninja/slayer); validated by
  `Backend/scripts/validate_class_feature_effects.py`. Hexes that affect other creatures (Evil
  Eye, Ward, Fortune, Misfortune) carry Multi-Buff-Distributor `tagBuff` payloads with
  caster-scaling formulas baked to the NPC's numbers; shared-pool formulas retarget to the class
  the character actually has (skald rage powers, shaman hexes). Foundry-module overlay is a
  follow-up in the module repo; the web sheet can read the payload dicts directly.
- **Multiclass generation.** The Multiclass dropdown (web form + API `multi_class` flag) is now
  live: "Yes" rolls 2/3/4 classes at 50%/35%/15% (capped by total level, each class ≥1 level) and
  splits the rolled level randomly across them. Classes live in a new `character.classes` list;
  the class with the most levels (tie → first rolled) is the "primary" and drives single-choice
  concerns (main stat, armor/weapon style, archetype, favored class). Multiple caster classes are
  allowed — each gets its own independent spellbook (own caster level, spells known/per day, spell
  list, domain/bloodline/school bonus spells routed to the right book) — while Path of War
  initiator classes and Spheres classes are capped at 1 per character. Every per-class system
  (HP dice, class talents/hexes/discoveries, fighter-style bonus-feat tracks, teamwork feats,
  domains, animal companions, ranger/monk feats, gunslinger guns, class abilities, traits,
  backstory) now fires for whichever class grants it, scaled by that class's own level; PoW
  initiator level = the initiator class's own level.
- **Rules-correct multiclass math, saves now computed server-side.** BAB stacks per class
  (floored per class, then summed), base saves sum each class's good/poor progression (new
  authoritative `good_saves` table in `Backend/utils/data.py`, exported as `save_bases`), skill
  points accrue per class with max ranks = total character level. New export keys: `classes`,
  `total_level`, `save_bases`, `spellbooks` — legacy keys (`level` = primary-class level,
  `c_class`, `c_class_2`, `bab_total`) keep their old semantics for the Foundry module.
- **Web sheet renders multiclass.** Header shows "Fighter 6 / Wizard 4", saves use the stacked
  `save_bases` (the "(multiclass: first class only)" caveat is gone), and each caster class gets
  its own Spellcasting block; old cached payloads still render via the legacy fallbacks.

- **Equipment now carries real mechanics.** A new generated side-map
  `Backend/json/items/item_changes.json` (built by `Backend/scripts/build_item_changes.py` from
  `items_best.json` descriptions, with `item_changes_overrides.json` merged on top) turns clean
  numeric bonuses ("+2 competence bonus on Intimidate checks", stat belts, cloaks of resistance)
  into pf1 `changes` and situational bonus text into `contextNotes`. Exported per character as
  `item_changes_dict`; the Foundry module overlays it onto each equipment item (deduped by change
  target so compendium-automated items like the Circlet of Persuasion don't double-apply), and the
  web sheet merges it into inventory rows so item bonuses feed its computed totals.
- **Every item with a real effect now gets a context note.** The item-changes builder grew a
  second pass: no-bonus sentences with mechanics (activated abilities, uses/day, saves, granted
  spells) become one summarizing pf1 context note per item, with dice/DCs/durations/distances
  wrapped as `[[ ]]` inline rolls in the house conditional style — coverage went from 528 to 1,381
  of 1,456 pool items; pure flavor text still gets nothing. Curated overrides now cover the tiered
  "hidden bonus" families (bracers of armor, ring of resistance, cloak-of-resistance variants,
  bodywrap of mighty strikes, and more — 56 entries), and note targets are validated against the
  pf1 `contextNoteTargets` enum at build time.

- **Magic weapon/armor qualities: full coverage, rules text, and a real +N.** The curated
  `Backend/json/items/quality_effects.json` grew from ~71 entries to ALL 197 weapon and 134
  armor/shield qualities the random enhancer can roll — every weapon quality now lands as an
  attack conditional in the house rider style (clean dice as modifiers, e.g. Corrosive's 1d6
  acid; riders/DCs/durations as `[[ ]]` text), and every armor/shield quality as pf1
  changes/context notes (e.g. Fortification's "25% negate crits" on AC). Each chosen quality
  also ships its full scraped rules text as `description`, which the Foundry module renders as
  a titled block under the item. A new `Backend/scripts/validate_quality_effects.py` enforces
  100% coverage, entry structure, and valid pf1 targets.
- **Items arrive with their numeric enhancement bonus.** The enhancement budget leftover after
  buying qualities (always 1–5) is now exported as `weapon/armor/shield_enhancement_bonus`; the
  Foundry module stamps it (`system.enh` / `system.armor.enh` + masterwork) and renames the item
  "+N <Qualities> <Base Name>" (e.g. "+1 Corrosive Longsword").

- **Mechanical flaws.** Characters' flaws are now real drawbacks instead of personality
  strings: a new `Backend/json/flaws/flaw_effects.json` carries 25 Minor and 19 Major flaws
  (user-authored + community-flaw and oracle-curse derived) in the house pf1 style — clean
  penalties as `changes`, situational rules as `[[ ]]` context notes, full rules text as a
  description. The existing 0–4 flaw roll now draws from it (1st flaw Minor, 2nd Major, extras
  80/20), exported as `flaw_effects_dict`; the Foundry module renders each as a Traits-tab item
  named "(Flaw, Minor/Major) <Name>" with its mechanics attached. Save DCs are standardized:
  always 5 in Minor flaws, always 15 in Major flaws (skill-check DCs unconstrained). The bonus
  flaw-feat formula is unchanged. Validated by `Backend/scripts/validate_flaw_effects.py`.
- **Foundry sheet sections match the campaign template.** The Class Features tab now has the
  template actor's divider layout — a Resource Pools group at the top (Hero Points for every
  character from the generated count; Stamina for fighters or Combat Stamina takers; per-class
  charge pools like Rage, Ki Pool, Bardic Performance, Lay on Hands, Grit, Panache with
  level-scaling formulas — the matching class-feature copy from the class harvest is removed
  so a pool ability lives only under Resource Pools, adopting the fuller rules text),
  Variable Modifiers (sizefordamage) / Natural AC / Death HP groups
  (Natural Armor HP + Death HP Pool trackers imported from the template), one divider per
  selection ladder (Rage Powers, Hexes, Rogue Talents, Discoveries, …) with items labeled
  "(Rage Power 4) <name>" from the recorded gain levels, and a Class Features divider for
  everything else. The Traits tab gains Traits / Flaws dividers.

### Changed
- **Item notes are now placed by branch: Mechanical / Context (skill) / Context (Other) /
  Unplaced.** Notes that used to fall onto the all-skills target by default are rehomed: if the
  item has an anchor (another targeted note or a change), the texts merge into ONE verbose note
  on that target in source order (Penitent's Robes: +1-saves change + a single saving-throws
  note carrying the whole vow ladder); items with no anchor move their text to a new per-item
  `unplaced` list that the Foundry module ignores (nothing misleading under Skills) but the
  Flask web sheet shows as an "Effects" block inside the item's expandable description.
  `+N armor/shield bonus` sentences now also parse into real pf1 changes (`aac`/`sac`, type
  `base`), and the build summary/report prints the four-branch counts with an unplaced
  curation list.
- **`/sheet` generate form: levels to 40, clearer dice labels.** Highest/Lowest
  Level inputs now accept up to 40 (the generator already clamps there); "Number of Dice" /
  "Sides per Die" are relabeled "Number of Dice for Stat Rolls" / "Dice Size for Stat Rolls (d6)";
  the Multiclass select (briefly locked while multiclass generation was unimplemented) is live
  again with a "Yes" option. Mirrors the same change in the standalone
  Pathfinder-Character-Sheet repo.

### Fixed
- Curated spell changes (`Backend/json/spells/spell_changes.json`) now actually layer into
  `spell_buffs.json`: the builder resolved the file against a doubled `Backend/Backend/...` path
  and silently fell back to no curation. Curated entries also win over a colliding auto-parsed
  change on the same target, so spells like Divine Favor and Magic Weapon no longer double-count
  attack/damage bonuses.
- **Multiclass class-choice slots no longer leak talents from a sibling class's pool.** The
  shared `chooseable_talents` candidate list accumulates across chooser calls (the feat system
  intentionally draws from it), so e.g. a barbarian/ninja's rage-power slots could pick leftover
  ninja tricks ("superior sniper", "trap spotter") whose description lookup against the barbarian
  pool then missed — exporting name-only, description-less class-feature items. Each chooser now
  picks only names belonging to its own pool, and the description lookup is case-insensitive.
- **Alchemist discoveries actually get rolled now.** `alchemist.json` nested the whole discovery
  pool one level too deep (`basic.alchemist`), so the discovery chooser saw a single "discovery"
  literally named `alchemist` (with the entire pool as its description) and padded remaining
  slots via the leak above. The pool is flattened to match every other class file.
- Class-choice pool data repairs found by the new audit: split benefit prose out of the
  `prerequisites` field for `celestial totem`, `celestial totem, greater`, and `linnorm death
  curse, cairn` (barbarian); filled missing text for `living pigment` (alchemist), `esoteric
  scholar` (rogue/ninja/slayer), and `Black Blade Riposte` (magus); dropped the junk
  `rage powers  samurai sheepdog` scrape row. All other pools audited clean.
- Class bonus feats and teamwork feats are now labeled with the class that actually grants them
  in multiclass rolls (e.g. a gunslinger dip's bonus feat reads "(Gunslinger 4)"). Labels were
  built from the primary class only, so feats granted by other classes had no label and the
  Foundry sheet fell back to a generic "(Class Bonus Feat 1/3/…)" counter — and even labeled ones
  were mis-attributed to the primary. The label slots and the feat counts now come from one
  shared per-class schedule (`class_bonus_feat_slots` / `teamwork_feat_slots`), so they can't
  drift apart.
- Antipaladins now cast with Charisma: the class was missing from the `caster_mod` ability table,
  so its exported spellbook had no `casting_stat` and it never received bonus spells per day from
  a high Charisma. The occult casters (occultist, psychic, spiritualist, medium, mesmerist) are
  mapped too so they don't hit the same gap when they join the random pool (kineticist stays
  unmapped — burn is Constitution-based, which the int/wis/cha table doesn't model).
- Foundry actors now get **every** rolled class, not just the primary: the payload's class entries
  each carry their own randomly-picked archetype, and the module builds one class item per class
  (highest level first, each followed by its archetype item), levels each independently so pf1
  trims that class's features to its own level, and registers secondary-class resource pools
  (rage, ki, …). Previously a multiclass roll produced a single-class sheet whose extra hexes/rage
  powers had no visible source class.
- Multiclass rolls containing a ranger or brawler no longer crash generation (the Foundry module's
  "Cannot read properties of undefined (reading 'toLowerCase')" build failure) or silently wipe the
  other classes' features: their list-pick chooser (favored terrains/enemies, brawler maneuvers)
  replaced the whole `class features` dict instead of merging, deleting earlier bloodline/hex/
  mystery picks and breaking the sorcerer bonus-spell lookup. The Foundry module now also reports
  the backend's real error message instead of crashing when generation fails.
- Multiclass characters no longer break generation: the old dead two-class "dip" path called
  `.lower()` on a list and passed a tuple to `random.randint`; both replaced by the new selection
  engine.
- A second class's single-pick class feature (bloodline/order/mystery/curse) no longer wipes the
  earlier class's pick — the chooser now merges into `class features` instead of overwriting.
- Druids only trade their animal companion for a domain on the intended 10% roll (an operator-
  precedence bug made every druid always qualify for a domain); a cleric rolled as a non-primary
  class now actually receives domain data instead of just passing the eligibility check.
- The level-1 max-HP die is always the primary class's hit die (`total_hp_calc` previously always
  used class slot 1, and a second class's HP dice could be skipped).
- Monk/bloodrager feat-description lookups no longer crash when the curated feat-tax searcher is
  called without a description dict (latent `NoneType.update` bug, newly reachable via
  multiclass).
- **Leaving Gold blank now really gives the Paizo wealth-by-level default.** The web route
  coerced a blank `goldAmount` to `0`, so `assign_gold`'s Paizo-table branch was unreachable and
  "blank = Paizo default" characters started with 0 gp (and bought their gear into the negative).
  Blank now stays non-numeric through `process_input_values` and lands on the table; the table
  itself (levels 2–20) also gained sane edges — level 1 gets 150 gp (≈ average class starting
  wealth) instead of wrapping around to the level-20 value (880,000 gp), and 21+ keeps the
  level-20 value.
- **Multi-bonus sentences no longer leak wrong changes.** The bonus-phrase capture stopped at
  the next `+`, and example text ("For example, with 3 vows…") now counts as conditional — this
  removes Penitent's Robes' accidental unconditional +4 AC change, among others.
- **The entire rings slot (210 items) had empty descriptions.** The ring scrape had glued each
  description onto the `weight` field ("… Description <text> Construction"); a one-off repair
  script (`Backend/scripts/fix_ring_descriptions.py`) split them back apart, so rings like Ring of
  Protection/Resistance now parse into real changes and notes instead of shipping blank.
- **Weapon/armor special abilities are automated.** Curated
  `Backend/json/items/quality_effects.json` (exported as `enhancement_effects_dict`) gives ~35
  weapon qualities (flaming/frost/shock/corrosive + bursts, holy/unholy/anarchic/axiomatic, bane,
  keen, speed, vorpal, wounding, …) attack-action conditionals in the house rider style, and ~40
  armor/shield qualities (shadow/slick tiers, spell resistance, fortification, energy resistance,
  bashing, …) pf1 changes/context notes on the armor item. The web sheet's Enhancements panel shows
  a mechanics summary line per quality.

- **"Prefer local backend (dev)" toggle in the Foundry module.** A per-machine (client-scoped)
  setting that probes the local Flask server at generate time and uses it when it's up, falling
  back to the hosted Render endpoint automatically when it isn't. Ships disabled, so released
  builds and other tables always default to the hosted server. Configured in Foundry's module
  settings; registration is now robust to load order (registers immediately when the init hook
  has already fired). `createCharacter.js` is now a proper ES module imported by `button.js`
  (it previously relied on the removed classic-scripts array to define a global).

### Fixed
- **Generated actors crashed the pf1 character sheet ("carriedWeight of undefined").** The
  homebrew-deities rework made `deity.json` names a list of aliases, and the payload shipped the
  raw list; pf1 v11's `details.deity` is a string field, so the array broke actor data
  preparation and the sheet died before rendering (also hiding the newly generated languages).
  The backend now exports the primary name as a string, and the module coerces list payloads
  from older backends.
- **Foundry module settings never registered.** `scripts/module.js` (which registers the module's
  settings on the init hook) was only listed in `module.json`'s classic `scripts` array, where its
  ES-module `export` is a silent SyntaxError — so no settings (including Backend URL) ever appeared
  and generation always used the hard-coded hosted fallback. `main.js` now imports it first, and
  the dead classic-scripts array (all six entries ES-module files that no-op'd) is removed.

- **Languages are actually generated now.** `language_chooser` previously sampled
  `int_mod` languages from a colon-split of the race blurb — most characters got an empty list (no
  guaranteed Common/racial tongue, zero picks at Int ≤ 11). It now always grants the race's
  automatic languages ("begin play speaking …", including "either X or Y" picks), and spends
  `max(Int mod, 0)` + Linguistics ranks on bonus languages from the race's proper bonus list
  ("choose any" races draw from the master list). Druids reliably know Druidic.
- **Druid generation no longer corrupts the master language list.** `druidic_flag_assigner` used to
  append `'Druidic'` to the module-level language pool (leaking it to every later character in the
  process) while setting `character.languages = None`; it now just sets a flag the language chooser
  reads.
- Removed a duplicate `language_chooser` call that burned RNG state on every generation.
- **Languages now render on the pf1 v11 actor sheet.** pf1 v11 stores traits as flat arrays in
  source data (prep splits known ids into `.standard`, unknown names into `.custom`); the module
  was writing the pre-v11 `{value, custom}` object shape, which pf1 silently ignores — only
  race-granted languages showed. The module now writes the flat id array.
- **Racial ability modifiers are now applied to generated stats.** Every race's PF1 modifiers
  (e.g. Orc +4 Str / −2 Int / −2 Wis / −2 Cha) are added to the rolled scores before ability mods,
  HP, skills, and spells are calculated; the floating "+2 to One Ability Score" races (Human,
  Half-Elf, Half-Orc) apply it to the class main stat. Values live in a new curated side-map
  `Backend/json/racial_stat_changes.json` (validated by `Backend/scripts/validate_racial_stats.py`,
  the old prose-key parser in `race_func.py` stays disabled), and the per-stat split is exported
  as `racial_stats` so the web sheet's ability-total breakdown shows `base X + racial ±N`.
- **"Monkey Goblin" no longer crashes generation.** `race_chooser` title-cased the chosen race but
  the data files key it `Monkey goblin`, so exact-case lookups (age/height/weight in
  `appearance.py`, land speed) raised KeyError. The chosen race is now canonicalized to the data
  files' key casing (a no-op for the other 24 races).
- **`selected_traits_desc` in the character payload.** The trait name+description pairs built during
  trait selection (previously only fed to backstory generation) are now exported, so the standalone
  web sheet can show descriptions for homebrew traits that are missing from the Foundry compendium
  data.
- **Web character sheet at `GET /sheet`.** A read-only, pf1-styled character sheet served by the Flask
  backend (`Backend/templates/sheet.html` + `static/scripts/sheet.js` + `static/styles/sheet.css`):
  generate a character in-page (POSTs the same payload as the Foundry module to
  `/update_character_data`), or paste/upload a saved character JSON. Renders every generator section —
  abilities, base combat estimates (AC/saves/CMB derived client-side from a class→good-saves map),
  gear, skills (with skill-unlock ★ and profession ranks), all feat buckets (trainer/profession/
  story/flaw/…), traits, class features, spellcasting, Path of War maneuvers & stances, Spheres
  talents/tradition, description, and backstory — hiding sections that don't apply. The last character
  persists in localStorage across refreshes; includes a print stylesheet. Stalker/Zealot are selectable
  here (no Foundry-compendium constraint). The old awesomeSheet-fork frontend is abandoned in its
  favor.
- **Every buff spell is now generated as a distributable Multi-Buff-Distributor buff.**
  `Backend/scripts/build_spell_buffs.py` scans the 3029-spell compendium (`every_spell.json`) and writes
  `spell_buffs.json` — **798 buff spells** (341 with auto-parsed mechanical `changes`, the rest
  description-only), each with an `aura_range` for emanation/allies-in-area spells. Spells carry no
  structured mechanics, so `changes` are parsed conservatively from the description (`+N <type> bonus
  to <target>` → the right pf1 change target; ability-score buffs emit only the ability, letting pf1
  derive AC/saves) with the curated `spell_changes.json` layered in. The palette
  (`build_pow_template_actor.py --spell-buffs all`) emits every one as a `<Spell> (UNAMED)` inactive
  temp buff under a "Spell Buffs (distribute)" divider; the module (`addSpellBuffs()` in
  `modify-abilities.js`) emits `<Spell> (TAG)` buffs for each spell the NPC actually knows
  (`spell_list_choose_from`). Even Personal/Self-range spells are included (shenanigans can place them
  on others). Same `(TAG)` / `Aura Range:` / `onlyOthers;` format as the sphere buffs. The spell-buffs
  are laid out under **duration dividers** (`____ rounds ____`, `____ minutes ____`, `____ hours ____`,
  `____ other durations ____`) and **sorted by spell level** within each, with `(level X)` on the title
  and in the description (after the `Aura Range:` line). The `(TAG)` now sits at the **front** of the
  name — `(TAG) <Spell> (level X)` — for every distributable buff (spell and sphere/companion/ally),
  so they all read consistently. Each spell-buff description is now a proper **spell stat block**
  (School/Level, Casting Time, Components, Range, Target, Duration, Saving Throw, Spell Resistance) +
  the **full** rules text + a bolded **Benefits:** summary of the parsed bonuses — the earlier
  600-character truncation is removed (that was why descriptions cut off mid-sentence). Every
  spell-buff now opens with an `Aura Range: X` line computed from the **spell's range** (close/medium/
  long conventions scaled by the NPC's caster level; touch → 5, personal → 0), and the spell-buffs use
  the pf1 **`spell` buff subType** so they render in the Buffs tab's "Spell Buffs" subsection (sphere/
  companion/ally buffs stay `temp`).
- **Affects-others sphere talents become distributable "aura" buffs** (allies, companions, aura
  recipients) instead of being skipped. Each is authored as a `buff` curation entry
  (`{aura_range, only_others, changes, contextNotes, description}`), promoted to the module's new
  `talent_aura_buffs.json`, and rendered as an **inactive temp buff** named `<Talent> (TAG)` following
  the **Multi-Buff Distributor** macro format (`Aura Range: N` / `onlyOthers;` description markers). The
  `(TAG)` is the source identifier: **`(UNAMED)`** on the uploadable palette actor, and the **first 5
  letters of the NPC's name** (uppercased, stopping at the first non-letter) on generated characters —
  built by `addSphereAuraBuffs()` in `scripts/modify-abilities.js` and the palette builder. Documented
  in the new **`multi-buff-distributor`** skill. **34 affects-others buffs** curated across 12 spheres:
  companion/mount buffs (Conjuration Raging/Regenerating/Bestial/Swarm/Troop/Mystical Companion,
  Beastmastery Frenzy Rider / Focusing Connection / Armored Charge), ally-buff auras (Fate Serendipity,
  Warleader Fortifying Phalanx / Fierce Shout / Coordinated Reflexes / Aggressive Flanking, War Totem of
  Tactical Prowess), single-ally grants (Guardian Defend Other, War Tenacity, Mind Shield, Shield Cover
  Ally, Life Adrenaline Surge, Gladiator Inspiring Pose), and enemy-aura debuffs with `onlyOthers;`
  (Gladiator Aura of Fear, Bear Fursome Aura, Nature Peace and Love, Fate Greater Serendipity, War Totem
  of Insanity / Expulsion).
- **Spheres of Power / Might talents now carry per-roll conditionals into the Foundry actor** (mirrors
  the Path of War maneuver-conditionals pipeline). Every attack-relevant sphere talent becomes a
  **default-off conditional toggle** on the character's main weapon (Might + non-Destruction Power) —
  clean on-hit damage/attack numbers as structured `modifiers[]` (auto source-labeled), and
  saves/DCs/conditions/durations/bleed as `[[ ]]` inline-roll rider text in the toggle name. The
  **Destruction** sphere additionally gets a synthesized **Destructive Blast** attack item whose base
  damage scales `(ceil(CL/2))d6` bludgeoning, with blast-type/shape talents (Fire/Frost/Acid/…) and an
  Empowered Blast spell-point toggle attached to it. Save DCs use the sphere formulas
  (Power `10 + ½ CL + CAM`, Might `10 + ½ BAB + practitioner mod`); for these dabbling NPCs the sphere
  roll-data tokens are substituted to concrete forms at attach time (`@spheres.cl.total → 1`,
  `@spheres.cam/pam → @abilities.*.mod`) and the actor is stamped `flags.pf1spheres.castingAbility/
  practitionerAbility` + a caster-level-1 `spherecl` change. New tooling:
  `Backend/scripts/build_talent_conditionals.py` (regex draft seeds + `--dump-worklist` per-sphere
  slices), the gitignored `Backend/scripts/_spheres_generator/` curation folder (per-sphere
  `curated_might/` / `curated_power/` files + `promote_talents_to_module.py`), and the module's
  `combat_talent_conditionals.json` / `magic_talent_conditionals.json` (nested
  `{Sphere:{Talent:{modifiers,rider}}}`, read by the new `addSphereTalentConditionals()` /
  `addDestructiveBlastAttack()` in `scripts/modify-abilities.js`). Passive Might self-buffs stay in the
  separate backend `combat_talent_changes.json` (Changes tab). **Coverage rule:** every sphere *strike*
  talent (a strike applies on any attack roll — e.g. Cryptic/Transforming/Crippling/Charming/Time/
  Warping/Weather Strike) plus any single-target damage or debuff talent becomes a conditional; only
  genuine battlefield-control / zone / ally-or-self-buff / utility talents stay description-only. 561
  conditionals curated (Might 344, Power 247 across all 24 spheres, incl. the full Destruction blast
  suite, every Weather shroud, the Berserker brutal-strike debuff suite, Alchemy poison/coating
  on-hit effects, and the Enhancement weapon buffs). Two further encoding conventions: **self-buffs
  that raise your attack or damage** become `modifiers[]` toggles, and an **enemy AC-reduction debuff**
  is modeled as a `target:"attack"` bonus **plus** a rider explaining it (the Inheritor's Smite
  pattern). Also adds the missing **Leadership** combat sphere to `data.py`. Rules of encoding:
  [docs/spheres_conditional_decision_rules.md](docs/spheres_conditional_decision_rules.md). Consuming
  this requires the matching (separate-repo) `pf1e_random_char_generator` module update, whose JS loads
  once at Foundry startup — hard-refresh + generate a fresh actor to pick it up.
- **Sphere talent conditionals bundled onto the palette actor for manual testing.** The palette builder
  (`Backend/scripts/_pow_generator/build_pow_template_actor.py`) gained `--spheres {none,curated,all}`
  (default `all`): it appends one weapon per combat sphere (talent-toggle conditionals + a full talent
  reference block), a Destructive Blast weapon, the Might passive self-buffs, and a "Palette: Sphere
  CL 10" helper buff, all clear of the discipline/spell sort blocks. The palette keeps the **native**
  `@spheres.*` tokens so a conditional copied off it scales on a real spherecasting PC. Regenerate to
  `%USERPROFILE%\Downloads\pow_palette.json` as usual.
- **Spheres Casting block now spells out every drawback, boon, and the tradition math.** Previously the
  generated "Spheres Casting" feat listed a magic dabbler's casting-tradition drawbacks and boons by
  name only; the rules text already lived in `Backend/json/class_data/spheres/spheres_traditions.json`
  but was discarded before export. `_choose_casting_tradition` (`Backend/utils/class_func/spheres.py`)
  now carries each drawback/boon through with full text in parallel
  `casting_tradition.drawbacks_detail`/`boons_detail` keys (`{name, description, counts_as}`), while the
  plain-name `drawbacks`/`boons` arrays (and the flat `sphere_drawbacks`/`sphere_boons`/`sphere_traits`
  exports) stay `.join()`-safe name strings so an older/stale front-end degrades to clean names instead
  of `[object Object]`. The FoundryVTT module's `processSpheres` (`scripts/modify-abilities.js`) reads
  the `*_detail` keys (falling back to the name arrays) and renders a fully self-explanatory block: the
  casting ability + mana-pool breakdown (base modifier + bonus spell points), Drawbacks and Boons as
  HTML-escaped description lists (each drawback tagged with its 1-/2-point weight), and a "tradition
  math" line showing drawback points → boons bought → leftover → bonus spell points. Consuming the new
  data requires the matching (separate-repo) `pf1e_random_char_generator` module update; that module's
  JS loads once at Foundry startup, so a hard refresh is needed to pick it up.
- **Spell conditionals bundled onto the Path of War palette actor.** The PoW palette builder
  (`Backend/scripts/_pow_generator/build_pow_template_actor.py`) now also attaches every spell
  conditional to the same test actor, so one importable FoundryVTT character shows both the PoW
  maneuvers/stances and all spell conditionals. Bucket-A buff spells become default-off attack
  toggles on two new weapons — `Spell Buffs — curated (cast-on-self)` (vetted `spell_changes.json`)
  and `Spell Buffs — draft/unvetted (cast-on-self)` (draft-only extras) — while Bucket-B damaging
  touch-attack spells are emitted as real spell items (cloned from the module's `every_spell.json`)
  carrying their formal save + `[[ ]]` rider conditionals, faithfully mirroring the live module's
  `addSpellConditionals()` / `addSpellRiders()`. A new `--spells {none,curated,all}` flag (default
  `all`) controls scope; spells are purely additive, leaving the discipline weapons and stances
  untouched.
- **Campaign-lore grounding so generated backstories fit the Fairdell/Cronia setting.** A new optional
  `Backend/json/campaign_lore.json` encodes the homebrew world (year ~5256) and the well-documented
  regions — Tal-Falko, Feyador, Sojoria, Ieso, Dolestan, Esterdragon — each with a short setting
  brief, local faiths/orders, and naming notes, plus per-deity flavor lines. The backstory generator
  (`Backend/utils/class_func/backstory.py`) now injects a **SETTING / CAMPAIGN CANON** block (world
  blurb + tone + homeland + faith note + one local order) as a second system message for documented
  regions, so NPCs read as e.g. Tanagaarian inquisitors of Feyador or guild-bound gunsmiths of
  Sojoria instead of generic/modern fantasy; the offline template fallback opens with a one-line
  homeland grounding. Region lookup is case-insensitive (matches the title-cased `character.region`
  and any `aliases`). Everything degrades to prior behavior when the file is absent or the region is
  undocumented (Spire, Dust-Cairn, Kaeru no Tochi, Grundy). Five canon few-shot examples (one per
  documented region) were added under `Backend/json/backstory_examples/`, and example matching now
  weights `region` (`_match_score`) so a region-matched canon example is preferred alongside the
  existing examples.
- **Homebrew deities and region-aware deity selection.** Added **Tanagaar** (the Aurulent Eye of
  Feyador) and **Ragathiel** to `Backend/json/deity.json` (in the alignment buckets within one step
  of their own alignment), and a `region_deity_affinity` map in `Backend/utils/data.py`.
  `randomize_deity` (`Backend/utils/class_func/alignment_and_deity.py`) now biases a random NPC's
  deity ~70% toward their homeland's documented faiths when those are valid for the rolled alignment
  — Feyador → Tanagaar, Sojoria → Abadar/Pharasma/Cayden Cailean/Desna/Iomedae/Shelyn, Esterdragon →
  Iomedae/Pharasma/Desna/Ragathiel — and otherwise falls back to the prior alignment-only random pick.
- **Combat-maneuver & rider text on spell and maneuver conditionals (the "Inheritor's Smite"
  pattern).** A weapon conditional can now carry a structured attack/damage bonus **and** `[[ ]]`
  rider text (a save, condition, or a rollable combat maneuver) in its name at once. (1) Spell
  conditionals gained a `rider` channel: `addSpellConditionals` in the FoundryVTT module appends an
  entry's `rider` to the toggle name, so e.g. **Inheritor's Smite** now shows both `+[[5]] sacred
  attack` and `on hit, free bull rush [[ d20 + @attributes.cmb.total + 5 ]] vs CMD (no AoO)`
  (Rock Whip likewise gains its caster-level bull rush). (2) **44 Path of War maneuvers** that
  described a grapple / trip / disarm / sunder / bull rush with no rollable check now carry a
  `[[ d20 + @attributes.cmb.total … ]] vs CMD` roll (flat bonuses folded in, IL-scaling via
  `@pow.initLevel`, `@INITMOD`-based CMB for Solar Wind, and Escape Artist for The World's Greatest
  Trick). (3) The `build_spell_conditionals.py` / `build_maneuver_changes.py` draft builders now
  detect combat-maneuver / save / condition clauses, and the `foundry-conditionals` skill +
  `docs/pow_conditional_decision_rules.md` document the pattern and the three CMB-roll forms (plain,
  skill-in-place-of-CMB, caster-level-in-place-of-BAB).
- **Spells now carry pf1 conditionals/riders into the Foundry actor.** A generated NPC's chosen
  spells that buff attack/damage or are themselves a touch-attack are wired into the export so the
  FoundryVTT module can attach mechanics instead of leaving them description-only. Two new
  name-keyed dicts ship in the character JSON: `spell_changes_dict` — Bucket A buffs (Bless, Divine
  Favor, True Strike, Magic Weapon, Flame Arrow) as a default-off conditional toggle / always-on
  change on the wielder's **weapon**; and `spell_riders_dict` — Bucket B damaging attack-spells
  (Chill Touch, Frigid Touch, Acid Arrow) as the save block + non-damage riders ([[ ]] inline text)
  on the **spell's own** action (its attack + damage already come from the compendium). Classified
  across all 2,827 spells by the new `Backend/scripts/build_spell_conditionals.py`
  (→ `spell_conditionals.draft.json`) and curated into `Backend/json/spells/spell_changes.json`
  (120 entries) + `spell_riders.json` (19); selected per-NPC by `spell_conditionals_selection()` in
  `spells.py`. The curated data is auto-derived from spell text and flagged for ongoing review;
  consuming it requires a matching update to the (separate-repo) `pf1e_random_char_generator` module.
- **Path of War maneuvers & stances — full mechanical automation in generated NPCs.** Every PoW
  strike/boost/counter and stance a generated NPC knows now renders rich mechanics in Foundry instead
  of description-only text. The FoundryVTT module's curated data was greatly expanded —
  `templates/character_sheet_folder/maneuver_changes.json` **581 → 846** entries,
  `stance_changes.json` **19 → 159** — so that, per the new
  [foundry-conditionals](.claude/skills/foundry-conditionals/SKILL.md) /
  `docs/pow_conditional_decision_rules.md` convention: on-hit **and** area/burst/cone/line damage are
  real **damage modifiers** (with damage types) that roll in the damage section; saves / conditions /
  durations ride the conditional name as `[[ ]]` inline rolls; skill / demoralize / feint checks
  resolve to the **discipline's main skill** (`[[ d20 + @skills.<id>.mod ]]`); and the
  formerly-description-only stances gained pf1 buff `changes` (always-on flat self-buffs) +
  `contextNotes` where expressible (per-die / aura / ally effects stay description-only by design). A
  1-line `addStanceBuffs` tweak in `scripts/modify-abilities.js` substitutes `@INITMOD` in stance
  contextNotes (parity with maneuver riders). The expanded data is **LLM-generated** from the scraped
  maneuver descriptions — review before relying on it. Produced by gitignored personal tooling under
  `Backend/scripts/_pow_generator/` (which also builds an importable per-discipline "palette" actor
  and a `promote_to_module.py` that pushes the data into the module's curated files).
- **Tunable, example-driven Ollama backstories.** The backstory generator
  (`Backend/utils/class_func/backstory.py`) now uses a proper chat `system` role and supports three new
  controls without code edits: (1) an editable **`Backend/json/backstory_config.json`** (system prompt,
  temperature, length, focus phrases — partial/missing file falls back to baked-in defaults);
  (2) **few-shot examples** — drop `.txt`/`.json` backstories into **`Backend/json/backstory_examples/`**
  and 1–3 are shown to the model as example turns (optionally matched to the character's class/race/etc.
  via `smart_match`); an empty folder reproduces the old behavior exactly; (3) an optional
  **`backstory_focus`** input (comma/space-separated aspects: `combat`, `profession`, `faith`, `family`,
  `personality`, `appearance`, `region`) that emphasizes chosen facets — threaded through
  `generate_random_char` and the Flask `update_character_data` endpoint (optional 21st input), and also
  honored by the deterministic offline template fallback.
- **Backstory house style — prose + closing list, vocation/family/homeland focus.** The default
  backstory prompt now centers the prose on **profession → family & upbringing → homeland/where they
  are from**, deliberately **stops reciting feats and game mechanics**, and ends with a short labeled
  list (`Personality:` / `Mannerisms:` / `Appearance:` / `Flaws:`); the facts block and offline
  template were reordered to match. Example backstories now ship as `.json` with `tags`
  (`Backend/json/backstory_examples/`) so `smart_match` feeds the 2 closest to each NPC, and the
  default length was raised to 220–400 words (`max_tokens` 1100) to fit the richer prose + closing list.
- **Numerical feat buffs on the Foundry "Changes" tab.** Selected feats now carry their mechanical
  effect onto the generated actor instead of being text-only. Two new curated, hand-vetted side-maps
  keyed by feat name ride the export: **`Backend/json/feats/feat_changes.json`** — always-on pf1
  `changes` (e.g. Advanced Defensive Combat Training +4 CMD, Tribal Scars +6 HP, scaling skill feats
  via `ifelse(gte(@skills.X.rank,10),4,2)`) plus situational `contextNotes` for conditional feats
  (vs undead / while charging / when adjacent to an ally, etc.); and
  **`Backend/json/feats/feat_conditionals.json`** — default-off **toggle conditionals** for active
  feats (Power Attack, Deadly Aim, Piranha Strike, Combat Expertise, …) the player ticks per attack.
  Exported as `feat_changes_dict` / `feat_conditionals_dict` (new keys in `export_list_dict`); the
  FoundryVTT module overlays the changes onto each feat item (deduped by target) and attaches the
  toggles to the main weapon's attack action. **Double-apply guard:** buffs are authored ONLY for
  feats Foundry's `every_feat.json` compendium does not already automate, so nothing stacks twice.
  Spheres-of-Power magic talents stay text-only by design (they cast effects, not passive self-buffs).
- **Numerical buffs on combat talents (Spheres of Might).** The previously-empty `changes` /
  `contextNotes` slots on combat-talent items are now filled from
  **`Backend/json/class_data/spheres/combat_talent_changes.json`** (e.g. Greater Disarm/Trip/Sunder
  competence bonuses to CMB/CMD, Compact Frame's situational dodge AC), injected by `_talent_item`
  in `spheres.py` and honored by the FoundryVTT module's talent builder. (Alchemy "flask/bomb"
  talents that create separate thrown weapons are deferred — they need their own weapon items.)
- **Buff authoring tooling.** New manual draft-builders mirroring the Path-of-War pattern:
  `Backend/scripts/build_feat_changes.py` (text-mines `data/feats.csv`, joins `every_feat.json` for
  the double-apply guard) and `Backend/scripts/build_talent_changes.py` (`--system might|power`).
  They emit `*.draft.json` drafts that are classified/verified and hand-curated into the production
  maps above.
- **Skill-feat coverage + Skill Focus actually works now.** Added always-on skill `changes` for
  un-automated fixed skill feats (e.g. **Sea Legs** +2 Acrobatics/Climb/Swim, **Sharp Senses** +4
  Perception) and situational `contextNotes` for conditional ones (Altitude Affinity, Stone-Faced,
  Divine Deception/Denouncer, Improved Stonecunning, Casual Illusionist). **Skill Focus / Prodigy**
  (which `feat_skill_choice.py` points at the NPC's professions) previously recorded a bonus that was
  never consumed — now `specialize_skill_choice_feats` emits the resolved pf1 change
  (`skill.pro` +3/+6, or a regular-skill fallback `skill.<id>`) which `main_test.py` folds into
  `feat_changes_dict`, so the bonus finally lands on the sheet.
- **Situational combat feats are now default-off toggles.** 41 feats whose bonus only applies under a
  condition (Bloody Vengeance, Demon Hunter, Ferocious Loyalty, Giant Killer, Moonlight Stalker,
  Death from Above, …) moved from informational `contextNotes` to **default-off weapon toggle
  conditionals** in `feat_conditionals.json` — the player ticks them in the attack dialog and the
  bonus applies numerically, with the trigger spelled out in the conditional name (`[[ ]]` inline
  rolls where relevant). Non-combat riders (e.g. Demon Hunter's Knowledge (planes) bonus) stay as
  context notes.
- **Weapon Focus / Weapon Specialization line.** When an NPC takes Weapon Focus (the feat-tax
  *primary* that bundles Greater Weapon Focus / Weapon Specialization / Greater Weapon Specialization
  into one merged item), the chain's bonuses are now summed onto the feat — +1 attack per focus tier
  and +2 weapon damage per specialization tier (full chain = +2 attack / +4 weapon damage) — via a
  new `Backend/utils/class_func/weapon_focus_buffs.py` folded into `feat_changes_dict`. The bonus is
  global to weapon attacks, matching the single main weapon the generator equips.
- **Five new profession genres + a curated profession catalog.** Added the themes **`noble`** (royalty,
  courtiers, regents), **`occult`** (witches, necromancers, cultists, warlocks), **`wayfarer`** (sellswords,
  treasure-hunters, monster-slayers), **`elementalist`** (fire/ice/storm/earth specialists), and
  **`villain`** (brigands, terrorists, tyrants, torturers) — each with its own ~20-ability power-0..5
  ladder (now 19 themes / 380 abilities). A new curated catalog (`Backend/json/profession_catalog.json`,
  359 professions tagged with an explicit genre + power tier) feeds the generation pool and is consulted
  before the keyword heuristics, so new/epic/low-tier names classify deterministically. Tier-4/5
  professions now have epic titles (Royal Bloodline, Divine Vessel, Avatar of the Storm, Necromancer-Lord,
  Thousand Fists Champion, …). (`profession_abilities.json`, `profession_catalog.json`,
  `profession_abilities.py`.)
- **`fantasy-expert` skill.** A reusable D&D/Pathfinder/fantasy-lore skill (`.claude/skills/fantasy-expert/`)
  encoding the profession genre roster, fantasy-commonality weights, the tier ladder, and epic naming
  conventions — used to drive the genre/name/ability authoring above.
- **Profession abilities are far more varied (98 → 279 abilities, 11 → 14 themes).** The tiered
  Rank 5 / Rank 15 profession-ability library (`Backend/json/profession_abilities.json`) roughly tripled
  — every theme now carries ~16-21 abilities across the full power 0-5 ladder (was 4-9), so professions
  no longer repeat the same handful of abilities across the generated population, and a character with
  several same-theme professions gets distinct picks instead of draining a tiny ladder. Three new themes
  were added — **`trade`** (merchants/mongers/peddlers: haggling, appraisal, contacts, gold from wares),
  **`performance`** (bards/minstrels/dancers/jesters: inspire, fascinate, demoralize, fame), and
  **`service`** (innkeepers/cooks/brewers/butchers: food-and-drink buffs, rumors, hospitality) — and
  these vocations were pulled out of the overloaded catch-all `skill`/`craft` themes so dissimilar
  professions (e.g. Embroiderer vs Fishmonger, now `craft` vs `trade`) stop sharing one pool. New
  abilities carry real pf1 v11 `changes`/`contextNotes`/`uses` where the effect is mechanical.
  Every ability is **specific**: limited-use abilities state their exact per-day count in the text (no
  "a few times"), and none are flavor-only — each grants a concrete, defined effect (e.g. a crafter's
  *Honest Materials* gives crafted objects hardness equal to half the relevant Craft ranks; a merchant's
  *Coin From Wares* earns gold equal to Profession ranks × 10).
  (`profession_abilities.json` data; `profession_abilities.py` theme routing.)
- **Spheres now render natively on the Foundry sheet.** Sphere talents are placed in the pf1spheres
  module's **Combat/Magic Talents** section (grouped by sphere, with the real compendium icons and
  text) — exactly as if dragged in from the pf1spheres compendium — instead of as plain feats in the
  Features list. Each talent is cloned from the `pf1spheres.combat-talents` / `magic-talents` pack by
  name (or synthesized as a `combatTalent`/`magicTalent` feat tagged with its sphere when the module is
  off or a talent is missing). Magic dabblers still get a casting-tradition / mana-pool summary feat;
  the sphere *feats* ride the normal feat pipeline. (`modify-abilities.js` → `processSpheres`.)
- **Magic-side bonus sphere feat.** A Spheres-of-Power dabbler now has a 50% chance to pick up a
  sphere-specific feat tied to their most-taken sphere (favoring exactly one), drawn prereq-aware from
  `sphere_feats.json`. (`spheres.py` → `_roll_magic_sphere_feats`.)
- **Advanced sphere talents are labeled and sorted last.** On the sheet, an advanced talent now shows
  as `(Advanced) <Name>` and sorts to the bottom of its sphere, with the normal talents alphabetical
  above it. The backend marks each talent's advanced status (`_talent_item`); the FoundryVTT module
  applies the `(Advanced)` prefix and orders each sphere (normals alphabetical, advanced last) via the
  item `sort` field. (`spheres.py`, `modify-abilities.js` → `processSpheres`.)
- **Only real compendium talents are picked.** The combat (Spheres of Might) talent data is now built
  directly from the pf1spheres **combat-talents compendium** instead of a wiki scrape, so non-talent
  entries that used to leak in (e.g. "Optional Rule: Vehicles as Mounts", variant-rule sidebars, empty
  stubs) are gone, and previously thin/mismatched spheres are complete (Equipment went 16→103 talents,
  Warleader 6→54). A committed allowlist (`compendium_talent_names.json`, emitted by
  `extract_spheres_talents.py`) backs a defensive filter in `spheres.py` so only compendium talents are
  ever selected. (Magic data was already compendium-sourced and is unchanged.)

### Changed
- **Every conditional damage roll now shows its source on the chat card.** The FoundryVTT module
  (`scripts/modify-abilities.js`) used to append a `[Source]` flavor label only to *attack*
  modifiers; it now labels *damage* modifiers too across maneuvers, spells, and feats
  (`addManeuverConditionals` / `addSpellConditionals` / `addFeatConditionals`), so a rolled `8d6`
  reads as `8d6 (Circle of Razor Feathers)`. The label rides the formula flavor while the structured
  `damageType` still drives the type chip (pf1 stores the conditional part as
  `[formula, damageType, false]`), so no type information is lost. Author formulas stay PLAIN — the
  module appends the label; the existing no-double-label guard is unchanged.
- **All 854 in-play Path of War maneuver riders rewritten to the conditionals convention.** Every
  curated maneuver rider in the module's `maneuver_changes.json` now leads with its contingency
  (on a charge / on hit / on a failed save), names range / targets / duration / save-DC where they
  apply, wraps **every number in `[[ ]]`** inline rolls, and no longer restates the rolled modifier
  damage in the note (secondary/ongoing/aura damage is kept). Many previously empty riders (e.g.
  Roar of Battle, Iron Defenders Riposte) are now fully described. Modifier formulas are kept plain
  for the new source label.
- **All 49 spell-conditional toggle names + 19 attack riders re-curated to the same convention** in
  `spell_changes.json` / `spell_riders.json`: full (untruncated) descriptions, every number in
  `[[ ]]`, the rolled damage left on the roll instead of the name, and meaningful range / duration /
  save criteria folded in.
- **`build_maneuver_changes.py` and `build_spell_conditionals.py` now emit convention-compliant
  drafts.** Maneuver riders pull non-trivial Range/Target/Duration from the structured fields and
  bracket every number; the spell-toggle label is built from the full description with the rolled
  damage stripped and all numbers bracketed — so newly drafted conditionals are born correct.
- **The Path of War palette test actor now faithfully showcases the revamp.** The offline builder
  `build_pow_template_actor.py` now (a) bakes the `[Source]` label onto **damage** formulas — not
  just attack — so an imported palette actor shows `8d6[Abyssal Drive]` on the card (matching the
  live module), and (b) sources maneuver riders from the revamped module `maneuver_changes.json`
  instead of the stale `maneuver_overrides.json` layer (which only masked 327 riders and added no
  unique modifiers). Regenerating it (`--out …\Downloads\pow_palette.json --spells all`) yields a
  single importable actor with all 854 revamped maneuver conditionals + the spell conditionals,
  every damage roll source-labeled.
- **The `foundry-conditionals` skill is substantially expanded.** It now distinguishes the two
  bracket syntaxes (`[[ ]]` inline rolls vs the module-applied `formula[Source]` damage label),
  documents prerequisites/contingencies, adds a "what every conditional must describe" checklist
  (contingency, DC, range, targets, saves, damage, attack boosts, duration), and states the hard
  rules (every number bracketed, never restate rolled damage in the note, never bury the dice in the
  toggle name, no length cap).
- **Path of War maneuver damage dice no longer multiply on a critical hit.** A maneuver conditional
  whose damage formula carries dice (e.g. Ravaging Blow `1d6`, Razor Tempest `8d6`, `4d6 + @INITMOD`)
  is now emitted as a pf1 **"Non-multiplying Bonus Formula"** (`critical:"nonCrit"`) — extra effect
  dice aren't multiplied on a crit, per the Pathfinder rules. Flat / `@`-only damage modifiers (no
  dice) stay `critical:"normal"` and scale with the crit like static damage; attack modifiers are
  untouched. Applied across all PoW maneuver data: the module's curated `maneuver_changes.json`
  (362 modifiers), the regenerated `maneuver_changes.draft.json`, and the palette's
  `_pow_generator/maneuver_overrides.json` (123 modifiers) — so both the auto-attached weapon
  conditionals and the rebuilt PoW palette now read `nonCrit` for dice damage. Enforced going forward
  by `_crit_for()` in `Backend/scripts/build_maneuver_changes.py` and re-runnable via the new
  idempotent `Backend/scripts/fix_maneuver_crit.py`. An audit of all 370 dice-bearing maneuvers
  against their rules text found exactly one genuine crit-tied case — **Doom Talon** (Thrashing
  Dragon), whose 4d6 fires only on a confirmed critical and isn't doubled — now encoded as the pf1
  **"On-critical Bonus Formula"** (`critical:"crit"`) in the curated data + palette override. Spheres
  talents and feat conditionals are intentionally left as-is.
  (`docs/pow_conditional_decision_rules.md` updated.)
- **Path of War skill-based attacks & combat maneuvers now roll correctly.** Maneuvers that resolve
  via a skill emit literal inline `[[ ]]` rolls following three conventions: a skill used **as an
  attack roll** adds the actor's misc attack bonus (`[[ d20 + @attributes.attack.general +
  @skills.<id>.mod ]]`); a skill **in place of CMB vs CMD** keeps CMB's size/misc and swaps out
  BAB + ability (`[[ d20 + @attributes.cmb.total - @abilities.<str|dex>.mod - @attributes.bab.total +
  @skills.<id>.mod ]] vs CMD`, melee→str / ranged→dex); a plain skill check stays
  `[[ d20 + @skills.<id>.mod ]]`. Fixed the **Roaring Mouse** discipline skill map (`acr` → `esc`,
  Escape Artist) and retrofitted 22 affected maneuvers (Roaring Mouse, all of Tempest Gale, Surging
  Shark's charges, Piercing Thunder leaps, Fool's Errand, Mithral Current, Sleeping Goddess) into the
  module's `maneuver_changes.json` + palette via the new
  `Backend/scripts/_pow_generator/apply_skill_rolls.py` → `promote_to_module.py`.
  (`docs/pow_conditional_decision_rules.md` + `foundry-conditionals` skill updated.)
- **Path of War stances: IL-scaling damage now mechanical, plus aura markers.** The eight stances that
  add initiator-level-scaling damage to the wielder's attacks (Savage Stance, Snapping Turtle Stance,
  Reaching Blade Stance, Stance of Aggression, Scarlet Einhander, Stance of Piercing Rays, Outer
  Sphere Stance, Phalanx Lancer) now emit that damage as a **rolled-dice, default-on weapon damage
  conditional** (`critical:"nonCrit"`) whose dice count scales off `@attributes.hd.total` — instead of
  passive `contextNotes` text (a buff `change` would maximize the dice). New
  `apply_stance_damage.py` authors them; the module's `addManeuverConditionals` and the palette attach
  them for known stances; the redundant `wdamage` contextNote was removed from each buff. Separately,
  ~20 aura / affects-others stances now carry `AuraRange: <feet-or-formula>` (and `onlyOthers;` when
  the wielder gains nothing) marker lines prepended to their buff description — driven by the new
  `Backend/json/class_data/path_of_war/stance_auras.json` — for downstream aura/buff-distributor
  tooling. (Data-only; a stance whose runtime description comes from the pf1-pow compendium won't show
  the markers — the palette always does.)
- **The Spheres Mentor now funds far fewer, caliber-scaled talents (~2.5 feats, was ~4.5).** A dedicated
  Spheres Mentor was funded by the **sum of two** caliber rolls plus overflow, so it could teach ~9
  off-budget talents (≈ 4.5 feats) and bloat a character past the flat-8. Now a single mentor of caliber
  C (one roll) teaches exactly **2·C talents** = C feats off-budget (C = 1/2/3/4 → 2/4/6/8 talents),
  capped at the flat-8, with no overflow — so the character's total talents never exceed 8 and the mentor
  averages ~2.5 feats. Trainer caliber weights were also retuned from `15/40/30/15` to **`8/45/45/2`**
  (mean ~2.4): mostly average/excellent, with the occasional terrible and a rare mythical.
  (`trainers.py` `roll_caliber`, `main_test.py` trainer-backed branch, `spheres.py` `choose_spheres_attr`.)
- **Generated professions now follow tunable power-tier and genre distributions.** Previously 85% of
  professions were "average" tier and 61% fell into the catch-all `craft` genre. Profession selection
  (`profession_chooser._themed_profession_names`) now rolls a target **tier** then **genre** from weight
  tables: tiers land at ~**5% / 35% / 35% / 20% / 3% / 2%** (garbage→top), and `craft` stays the single
  most common but drops to ~**15%**, with the rest spread across the other genres by how common each
  archetype is in fantasy. Implemented as weighted selection over a cached `(tier, genre)` index of the
  pool (so the marginals are precise and easy to retune via `_TIER_WEIGHTS` / `_GENRE_WEIGHTS`); the raw
  master list is unchanged. (`profession_chooser.py`.)
- **Profession feats now cost a feat and each render as their own feat (no more "feat-tax" chain).**
  The three homebrew profession feats (True Calling / Multi Talented / Always Improving) used to be
  attributed to a fake trainer slot and bundled as one `(Trainer N): True Calling > Multi Talented >
  Always Improving` feat-tax chain *on top of* the normal budget (free). Each now renders as its **own
  ordinary feat** in the Feats list and **consumes a normal feat slot** (like the Path of War / Spheres
  feats): the profession-feat count is reserved out of both `feat_amounts` and `normal_feat_amount`, so
  each one replaces a normal feat — or, at very low level, the profession feats take over the general
  feat track and clamp the normal feats down to 0. They are appended after every `feat_tax_func` pass
  and the feat-count guarantee, so they are never chained or trimmed. (`main_test.py`. No front-end
  change — they ride the normal feat pipeline.)
- **Dedicated mentor trainers now list what they funded.** In the 25% "trainer-backed" branch, the
  "Path of War Mentor" and "Spheres Mentor" trainer entries previously showed only generic flavor text.
  Now each names the off-budget homebrew it taught: the **Path of War Mentor** lists every PoW feat
  (style feats + Martial Training tiers) with its description, written like a normal PoW feat; the
  **Spheres Mentor** lists the spheres funded plus the off-budget talents it provided — presented as HR1
  `Extra Combat/Magic Talent > Extra Combat/Magic Talent` feats (one per 2 talents) followed by the
  talent names — i.e. only the talents *beyond* what the character paid for themselves (no duplication of
  the budget-paid Extra-Talent feats already in the main Feats list). Single-type characters now get one
  correctly-named mentor (padded to two with a uniquely-named "(Continued Study)" entry when needed) so
  the per-name descriptions never collide. (`spheres.py` → `mentor_sphere_summary` + `mentor_funded_talents`;
  `main_test.py` mentor block. No front-end change — the module synthesizes the trainer row from the
  description.)
- **Budget-paid sphere talents now show a feat slot for tracking.** Each talent paid from the feat
  budget is bundled onto an HR1 `Extra Combat Talent > Extra Combat Talent` feat (2 talents per slot;
  the first magic talent rides `Basic Magic Training`), listed in the Feats tab with the talents it
  paid for in the description — like any other feat-taxed feat. Talents funded by the 25% Spheres
  Mentor trainers stay tracked by that trainer entry (no Extra-Talent feat). The feats consume feat
  budget. (`spheres.py` → `choose_spheres_attr`, `main_test.py`.)
- **Path of War & Spheres are now guaranteed when selected, with priority over normal feats.** Previously
  their counts were capped by whatever feat budget remained after everything else, so a feat-heavy NPC
  (e.g. a PoW-loaded martial) could silently lose them entirely. Now, when an NPC is rolled to have PoW
  and/or Spheres, those selections are funded **first** and the normal feat chooser takes whatever
  remains (down to zero). The realized amount scales per character: a **75%** chance to take a "lean"
  dose (about half the rolled homebrew feats), and a **25%** chance to be "trainer-backed" — keeping at
  least the lean half and gaining **2 dedicated mentor trainers** whose off-budget rolls fund the rest,
  with any surplus becoming bonus sphere talents. (`main_test.py`, `spheres.py`, `path_of_war.py`.)
- **Sphere talent count is now a flat 8 (7 normal + 1 advanced)** for a spheres-selected NPC,
  prerequisite-legal (decoupled from the feat count; backfills a normal if no advanced qualifies).
  Trainer-backed NPCs still get overflow talents on top. For testing, a `SINGLE_SPHERE_TESTING` flag
  (on) forces all 8 talents to come from **one** sphere so the 7 normals satisfy the same-sphere
  prerequisites that gate advanced talents. Both are testing values — a level-scaled model (groups of
  two, capped at 16) is planned later. (`spheres.py` → `_pick_flat_talents` / `randomize_spheres_num`.)

- **Spheres of Power/Might toggle in the generator UI.** The FoundryVTT character-generator dialog now
  has a "Do you want Spheres of Power/Might" yes/no option (default No). Choosing **Yes** activates the
  existing Spheres dabbling logic, so generated NPCs can now actually pick up sphere feats and talents
  (and, for casters, a casting tradition + mana pool) — previously the feature was backend-only and the
  flag always defaulted off, leaving every character with empty sphere data. The flag is read by name in
  the backend (`spheres_of_power` in the POST body) and threaded through `app.py` to
  `generate_random_char`'s `spheres_flag`.
- **Professions sub-system.** Every character now gets one or more themed professions (e.g. a smith
  tends toward a smithing vocation) modelled as `Profession (X)` skills with ranks. The rank pool
  follows the campaign heuristic `5 + level + 10 per profession feat` and is spread across as many
  professions as needed to absorb it (primary/backstory vocation first). **Each profession caps at 10
  ranks, except one that reaches 15 when True Calling is taken.** Profession feats (**True Calling /
  Multi Talented / Always Improving**) are bonus feats — at least **2 are taken when feats aren't
  randomized**. Each profession unlocks a set of **tiered abilities**: a profession's power tier
  (garbage → top) is fixed by its name's prestige (Pope/Royal → top, Bishop/Cardinal → high,
  Knight/Guard & skilled smiths → good, most artisans → average, Acolyte/Nun → bad,
  Custodian/Pool-cleaner → garbage) and its theme (martial / ki / divine / arcane / alchemy / skill /
  craft / scholar / nature / medical / menial) by the same name — except **high/top-tier professions
  supercharge the character's actual class/build**. The **rank-5 entry** grants a weaker band of
  abilities (with the associate-skills line folded in); the **rank-15 entry** (only the True Calling
  profession) grants the full tier band — the strongest items on the sheet. Abilities carry pf1
  `changes`/`contextNotes`/`uses` so passive bonuses and pools are mechanically wired. They render at
  the **bottom of the Feats tab** under a `____ Professions ____` divider as `Profession Rank 5: (X)` /
  `Profession Rank 15: (X)` ability entries. The **profession feats themselves** (True Calling / Multi
  Talented / Always Improving) are no longer listed separately — they're attributed to a **dedicated
  trainer slot** (a mentor) and render in the Trainers section as one `(Trainer N): True Calling >
  Multi Talented > …` entry. New
  `Backend/utils/class_func/profession_abilities.py` + curated `Backend/json/profession_abilities.json`;
  rewrites the `profession_chooser.py` stub; new exports `profession_ranks`, `profession_feats`,
  `profession_feat_desc`, `profession_pool`, `profession_ability_items`.
- **Trainer slots.** Characters roll the trainers they studied under — up to `1 + (hit dice ÷ 3) +
  mythic rank` (mythic = 0 for now), rolled `0..max`. Each trainer has a weighted caliber
  (1 terrible → 4 mythical) that sets how many feat-taxed bonus feats they teach. They render at the
  **bottom of the Feats tab** under a `____ Trainers ____` divider, **just like normal feats** — one
  item per taught feat-tax chain (`(Trainer N): Base Feat > granted > granted`), with each feat's full
  compendium text under `<hr>` separators and **no caliber line**. New
  `Backend/utils/class_func/trainers.py`; exports `trainer_feats`, `trainer_feat_labels`,
  `trainer_feat_tax_dict`, `trainer_calibers`.
- **Free skill unlock.** Every character gains one Pathfinder Unchained skill unlock, chosen at
  random from a skill they have ranks in (Knowledge specializations map to the shared Knowledge
  unlock; Craft/Profession show their specialization). Appears as a `Skill Unlock: <skill>` class
  feature and a new `skill_unlock` export. New data file `Backend/json/skill_unlocks.json` (all 24
  skills at 5/10/15/20 ranks, scraped from Archive of Nethys) and picker
  `Backend/utils/class_func/skill_unlocks.py`.
- **Generated character backstory.** Characters now get a coherent 1-2 paragraph prose backstory
  (new `backstory` export) woven from their identity, homeland, alignment/deity, a build summary
  (class/level/role + Path of War + notable feats), their **traits (now with descriptions)**,
  personality, and family. Generated by an Ollama model when reachable — **local** (default
  `http://localhost:11434`, model `gpt-oss:20b`) or **Ollama Cloud** (set `OLLAMA_API_KEY` → host
  defaults to `https://ollama.com`, model `gpt-oss:20b-cloud`; `OLLAMA_THINK` defaults to a low
  reasoning level so gpt-oss doesn't spend the token budget "thinking") — with a deterministic template
  fallback when none is reachable (e.g. the deployed backend, or while a model is downloading).
  New `Backend/utils/class_func/backstory.py` (stdlib HTTP, no new dependency); `traits.py` now
  also captures trait descriptions (`selected_traits_desc`). The FoundryVTT module shows the
  backstory in the Biography tab (the raw field-by-field details moved to Notes).
- **Size-based damage scaling on generated FoundryVTT sheets.** Every actor now gets a
  `sizefordamage` feature (exposes `@resources.sizefordamage`, default 0) plus a generated
  **attack** item (pf1 "Create Attack" equivalent) carrying a "Scaling Weapon Damage" script call
  and two actions — "Attack" (the rollable copy, with any maneuver conditionals) and "Don't Touch"
  (the pristine base-damage reference the script scales from by size). The original weapon item is
  left untouched and stays in the Combat list alongside the attack. Needs the `ckl-roll-bonuses`
  module at runtime. (FoundryVTT module `modify-abilities.js` + new `sizefordamage_feature.json` /
  `scaling_weapon_damage.json` templates.)
- `Backend/scripts/build_maneuver_changes.py` — manual tool that drafts pf1 conditional modifiers
  for Path of War strikes/boosts/counters from `Martial_Disciplines.json` (conservative damage-dice
  / attack-bonus regexes → `maneuver_changes.draft.json`, flagged for hand-curation). The curated
  subset drives default-off conditional toggles on the generated character's main weapon in the
  FoundryVTT module (per-hit dice live here because buff changes can't roll dice; stance dice stay
  description-only).

### Fixed
- **Broken minus signs in `PlayableRaces.json` race-trait keys.** Dwarf's ability line used an
  en dash (`–2 Charisma`) and Elf's had lost the sign entirely (`2 Constitution`); both now read
  `-2` like every other race. Display-only — racial modifiers are applied from
  `racial_stat_changes.json`, not parsed from these keys.
- **Truncated and damage-naming spell-conditional toggles.** Spell toggle names were capped at 120
  characters by `build_spell_conditionals.py`, so entries like **Firebelly** were cut off mid-word
  ("…not enough to dam"); the cap is removed and the names are rebuilt in full. Toggles that put the
  rolled dice in the name (e.g. **Ectoplasmic Eruption**'s "Deal 6d6 points of damage…") no longer
  do — that damage is on the roll (now source-labeled). A new convention check in
  `test_spell_conditionals.py` asserts the curated spell **and** maneuver data carry no un-`[[ ]]`
  numbers, no restated rolled damage in a name, and only plain modifier formulas.
- **Crit-confirmation spells no longer add a bonus to every attack roll.** **Unerring Weapon** —
  whose rule grants "+2, +1 per four caster levels (max +7), on attack rolls **to confirm a critical
  hit**" — had been curated in `spell_changes.json` as an always-on general to-hit change; since pf1
  has no crit-confirm-only change target, it's now dropped (description-only). Root cause: the
  `build_spell_conditionals.py` draft builder's attack disqualifier only matched the noun
  "confirmation", so the verb idiom "to confirm a critical hit" (which trails just past the "attack
  rolls" the bonus names) slipped through. A new `_CRIT_CONFIRM_RE` check looks just past the match
  for that idiom, while still keeping genuine bonuses like **Mirror Strike**'s "+2 … attack roll
  (and confirmation attack roll)". Regression-guarded in `test_spell_conditionals.py`.
- **Spells with "of the"-style names now appear on generated caster sheets — no more orphaned weapon
  toggles.** ~250 spells (~9%) — e.g. Breath of Life, Shield of the Dawnflower, Wall of Fire,
  Protection from Evil, Ray of Enfeeblement — were silently dropped from the spell list: the
  generator's `data/spells.csv` over-title-cased articles/prepositions ("Shield **Of The**
  Dawnflower") while the Foundry compendium uses canonical casing ("Shield **of the** Dawnflower"),
  and the module's `processSpell` matched names case-sensitively (`r.name === spell`). Such a spell's
  weapon **conditional** still attached (it comes from `spell_changes_dict`, no compendium lookup),
  leaving a toggle with no matching spell on the list. Fixed on both sides: `processSpell` now matches
  case-insensitively (via a lowercase index, mirroring the rider/feat lookups), and a one-time
  migration `Backend/scripts/normalize_spell_name_casing.py` — using the module's `every_spell.json`
  as the casing authority — recased all 250 names in `spells.csv` plus the affected
  `spell_changes.json` / `spell_riders.json` keys. (module `modify-abilities.js`, `data/spells.csv`,
  `spell_changes.json`, `spell_riders.json`.)
- **Six misspelled / source-ambiguous spell names now match the Foundry compendium instead of being
  dropped.** Beyond the casing migration above, six `data/spells.csv` names had no case-insensitive
  compendium match and so were silently skipped by `processSpell`: two typos (**Liberating Comand** →
  Liberating Command, **Suppres Charms and Compulsions** → Suppress Charms and Compulsions), two
  punctuation/spacing mismatches (**Dead Eye's Arrow** → Deadeye's Arrow, **Winter's Grasp** → Winter
  Grasp), and two names the compendium disambiguates by source (**Fool's Gold** → Fool's Gold (VC),
  **Shield Companion** → Shield Companion (ACG) — the correct variant picked by matching each row's own
  school/level/source columns). Only the name column changed. The two genuinely-absent spells
  (Adjuring Step, Corpse Hammer) are left as-is. (`data/spells.csv`.)
- **Caster-level spell buffs are capped at their rules maximum instead of scaling forever.** Divine
  Favor (`+1 per 3 CL`, max +3), Aroden's Magic Army (`+1 per 5 CL`, max +4), and Unerring Weapon
  (`+1 per 4 CL`, max +7) had bare `floor(@spells.primary.cl.total/N)` formulas with no ceiling, so a
  high-CL NPC got an unbounded bonus. Their `spell_changes.json` formulas now wrap in `min(…, cap)`
  (Divine Favor also honors its "at least +1" floor: `min(max(floor(@CL/3), 1), 3)`). The draft
  builder `build_spell_conditionals.py` now reads a "maximum +N" / "at least +N" clause and emits the
  bounded formula, and a new regression check rejects any uncapped `cl.total` / `hd.total` formula.
  (`spell_changes.json`, `build_spell_conditionals.py`, `test_spell_conditionals.py`.)
- **Cantrips/orisons are always prepared and infinitely castable.** Every generated caster's
  level-0 spells (for both prepared and spontaneous casters) are now marked prepared and set to
  at-will (`system.atWill = true`) so they render with no per-day limit. (Module `modify-abilities.js`.)
- **Prepared casters now have the right spells marked prepared on the Foundry sheet.** Previously
  every generated spell sat at `preparation 0`, so a cleric/wizard imported with an empty prepared
  list. The backend already decides the per-level count (spells/day); it now exports a
  `spells_prepared_per_level` list aligned to `spell_list_choose_from` (divine casters prepare their
  whole daily loadout incl. domain spells; spellbook casters like wizard/witch prepare only
  spells/day out of the larger spellbook), and the FoundryVTT module marks exactly that many spells
  prepared per level on prepared/hybrid spellbooks. Also corrected the module's caster classification:
  **Bard, Summoner, Summoner (Unchained), and Skald** are now spontaneous (were wrongly listed as
  prepared). (`spells.py`, `main_test.py`, module `modify-abilities.js`.)
- **Path of War skill-based attack & counter checks now include the general attack bonus.** When a
  maneuver rolls a skill *in place of an attack roll* (vs AC) or opposes the *triggering attack
  roll* (a counter), the inline roll now adds `@attributes.attack.general` — e.g. Primal Fury's
  *Shrug It Off* counter is `[[ d20 + @skills.sur.mod + @attributes.attack.general ]]` instead of
  `[[ d20 + @skills.sur.mod ]]` — so these to-hit rolls are on equal footing with the enemy's
  attack. 41 maneuvers were corrected (incl. Leaden Hyena feints rolled vs Sense Motive *or AC*);
  pure skill checks (vs a DC), combat maneuvers (vs CMD), and Perception-opposed counters (Veiled
  Moon) are unchanged. The canonical source gained an `@ATTACKCHECK` token (sibling to
  `@SKILLCHECK`) resolved by `promote_to_module.py` / the palette builder; the new idempotent
  `Backend/scripts/_pow_generator/apply_attack_general.py` performs the conversion. Re-curates the
  (separate-repo) module's `maneuver_changes.json`.
- **No more blank dedicated-trainer slots.** A trainer-backed NPC could show a content-free trainer like
  `(Trainer 5): Spheres Mentor (Continued Study)` (generic text, teaches nothing) — an artefact of
  padding the dedicated mentors to a fixed count of two. Dedicated mentors are now emitted only when they
  actually funded off-budget content (the Spheres Mentor appears only with a non-empty funded-talent
  list), and the pad-to-two loop and the generic "Homebrew Mentor" fallback are gone. A trainer-backed
  PoW-only build simply shows no dedicated mentor rather than a blank one. (`main_test.py`.)
- **The "Path of War Mentor" trainer no longer re-lists feats the character already paid for.** In the
  25% "trainer-backed" branch, a dedicated **Path of War Mentor** trainer listed every Martial Training /
  style feat as though it had *funded* them — but those feats are real feats on the sheet (they grant the
  maneuvers), so they're always paid from the normal/class feat budget and already appear in the Feats
  list. The mentor was pure duplication. Unlike sphere talents (which can be granted off-budget, so the
  **Spheres Mentor** legitimately lists only what it funded), Path of War has nothing genuinely
  off-budget, so it now gets **no mentor**. Trainer-backed builds keep the Spheres Mentor; a PoW-only
  trainer-backed build shows a generic "Homebrew Mentor" that lists no feats. (`main_test.py`.)
- **Sphere talents no longer leak in as bare feats.** Intermittently a sphere talent (e.g. Hurricane
  Kick, Yoga Strikes, Fragmenting Shot) was being chosen as a normal/flaw/class/trainer feat and rendered
  as an empty-description row. Cause: `character.chooseable_talents` accumulates across selection passes
  and feeds the feat chooser, and the sphere-talent picker left its **unpicked** eligible talents in that
  list — which the chooser's "drop owned" guard didn't catch (they were never added to `chooseable`). The
  sphere picker now clears `chooseable_talents` when it finishes (in `choose_spheres_attr` and
  `add_overflow_talents`), so leftover talents can't bleed into the feat pool. (These leaked talents used
  to be silently dropped by the front-end — part of the earlier "missing feats"; the synthesize-on-unmatched
  change exposed them, and it correctly stays for genuine feats missing from `every_feat.json`.) Verified
  0 leaks across 40 generations.
- **Martial Training feat-tax chains render consistently again.** Within one discipline some tiers showed
  their free partner (e.g. `Martial Training III > Martial Training IV`) while others didn't. `assign_feats_to_levels`
  runs twice but the tax-bucket rehoming ran only after the first pass; the second pass re-migrated some
  feats between the normal/class buckets, leaving their tax bundle in the wrong dict so the sheet (which
  applies each bucket's tax dict only to its own bucket) dropped the chain. The rehoming now runs after
  the **final** reorder. Verified 0 mis-homed Martial Training primaries across 99 of them; feat/story
  counts unchanged. (`main_test.py`, `spheres.py`.)
- **Feats are no longer silently dropped on the sheet (the real cause of "missing 1-2 feats").** The
  backend exported the correct number of feats, but the FoundryVTT module's `processFeatTrait` silently
  dropped any feat name it couldn't resolve against its `every_feat.json` compendium (an incomplete
  export missing many real Paizo feats — Mighty Conditioning, Pet, Leg Slash, …) — and because feats are
  labeled positionally, a dropped feat removed the **top** slot (e.g. Feat 19 / Story Feat 20). Measured:
  every one of 20 generated Fighters dropped 1-4 feats across buckets. (It was not the feat-tax system —
  `applyFeatTax` only decorates a parent's name with `> Child`, never removes rows.) Fix: the backend now
  supplies a description entry for **every** placed feat (`homebrew_feat_desc_dict`, best-effort from
  `data/feats.csv`), so the module's existing fallback **synthesizes** any compendium-missing feat instead
  of dropping it — backend restart only, no Foundry reload needed. The module was also hardened
  (`modify-abilities.js`): `every_feat.json` matching is now case/punctuation-insensitive (compendium
  feats that differ only by casing now resolve to their real item), and an unmatched feat is synthesized
  rather than dropped as a final safety net. Verified: **0 would-be-dropped feats across 45 generations**
  (Fighter/Warder/Wizard), down from 1-4 per character, with bucket counts still exact.
- **Feat counts are now guaranteed exact, and the running backend's version is visible.** A final
  reconciliation pass (`main_test.py`, just before export) forces the general feat track to exactly
  `normal_feat_amount` (feats at the character's real levels 1,3,…,19 — no gaps, nothing past their
  level): it backfills any shortfall (locking in the earlier reservation/strip fixes against future
  regressions) and, in the rare case where homebrew (Path-of-War Martial Training + Sphere Extra-Talent
  feats) outnumbers the slots, caps to exact by trimming the lowest-priority excess — sphere Extra-Talent
  *tracking* feats first (the talents themselves stay on the sheet as native Combat/Magic talents), then
  any remaining tail. Verified exact (general 10/10, story 5/5) across 90 generations spanning
  Fighter/Warder/Wizard × both feat-randomization modes, with zero failures. Also added a
  `GENERATOR_VERSION` stamp: printed in a startup banner by `app.py`, logged per generation, returned on
  each result, and written by the FoundryVTT module to a hidden actor flag
  (`flags.pf1e_random_char_generator.version`) — so a restart visibly loads the new code and any exported
  sheet reveals which backend build produced it (the recurring "I restarted but it's still wrong" was a
  stale `:5001` backend serving old code).
- **NPCs with Spheres no longer lose high-level feats (and story feats are no longer dropped).** A
  Spheres-selected NPC could come out missing the top entries of its feat tracks — e.g. a level-20
  Fighter showing `(Feat 1…11)` but nothing at 13/15/17/19, and missing the level-20 story feat. Two
  causes: (1) the sphere/PoW feat-budget **reservation** (`main_test.py`) subtracted a *rolled estimate*
  (`_priority_reserve + max(0, sphere_feat_budget_count − realize_sphere)`) that drifted off the real
  number of homebrew feats appended to the list, so it over-reserved (dropping the top "(Feat N)" slots —
  the bug) or under-reserved (spilling feats past the top level); it now reserves **exactly**
  `len(mt_feats) + len(style_feats) + len(sphere_feats)` — the Martial-Training, style, and sphere
  Extra-Talent feats that actually get appended — so the normal track lands at exactly
  `normal_feat_amount` every time. (2) The tax-child **strip** removed story/flaw/flavor feats that
  happened to be feat-chain children but, unlike the class/normal buckets, never **backfilled** them, so
  the story list shrank and its top level slot (15/20) was orphaned; story/flaw/flavor are now topped
  back up to their budgeted counts after the strip. Verified over 80+ generations (Fighter & Warder,
  level 20, both feat-randomization modes): no track ever comes up short. (Trainers were ruled out —
  they're funded off-budget and never consumed the feat allotment.)
- **Advanced / legendary sphere talents are now reliably labeled, and the registry is comprehensive.**
  Advanced talents (especially combat *legendary* talents like Bomb Jump) were silently never flagged,
  so they never showed `(Advanced)` on the sheet and weren't treated as advanced by the §8 picker. Root
  cause: the `advanced_talents.json` registry stores wiki names with their variant suffix (e.g.
  `"bomb jump (leap)"`) but the talent datasets are keyed by the clean name (`"bomb jump"`), and the
  three advanced-matching sites normalized with `_norm` — which strips `[source]` tags but not a
  trailing `(variant)` — so the names never matched. Now they normalize with `_talent_match_norm` (the
  same suffix-stripping the compendium filter already uses) in `_advanced_set`, `_is_advanced`, and
  `_talent_item`. Separately, the registry was rebuilt comprehensively from the Spheres wiki by the new
  `Backend/scripts/scrape_advanced_talents.py` (every magic sphere's *Advanced … Talents* section + every
  combat sphere's *Legendary Talents* section), adding 213 names — including whole combat spheres that
  were missing entirely (Equipment, Warleader) — merged so curated/homebrew-only keys with no wiki page
  (e.g. power → `bear`) are preserved. Verified end-to-end: advanced talents are now flagged across 15
  combat spheres and the magic side is unchanged. (`spheres.py`, `advanced_talents.json`,
  `scrape_advanced_talents.py`.)

### Changed
- **Dev server: disabled the Flask auto-reloader (`use_reloader=False` in `Backend/app.py`).** Under
  the project's `.venv` (which redirects to the base `C:\Python310` interpreter), Werkzeug's debug
  reloader spawned a runaway cascade of nested processes that fought over port 5001 and served stale
  code. The debugger is kept; restart the server manually after code edits.
- **Backstory: "use API" toggle and stronger vocation focus.** A new `use_backstory_api` input
  (optional 20th field on `POST /update_character_data`, default on; older 19-field clients still
  work) decides whether the Ollama call runs at all — when off, the deterministic template is used
  with no network attempt. The prompt and template now also dedicate a substantial chunk of the
  story to the character's **professions, notable craft, and the trainers who taught them**, since
  those define the NPC's everyday life.
- **Path of War maneuvers now cover every available maneuver level.** Selection guarantees at
  least **2 maneuvers of each available level** (falling back to **1 each** when the class's fixed
  maneuvers-known total can't afford 2× every level), then fills any remainder randomly — so
  initiators no longer skew toward high-level maneuvers and low levels are no longer starved.
  Class/chain totals are unchanged (no power inflation). New `path_of_war.py` helper
  `_level_floor_counts`, applied in `_constrained_pick` (initiators) and `_build_martial_training`
  (Martial Training).
- **Martial Training (non-initiator Path of War) redesign.** Each rolled martial discipline (1–3)
  is now its **own full Martial Training chain** drawing maneuvers only from that discipline, so a
  multi-discipline character gets a separate set per discipline (≈ N× the maneuvers) instead of one
  shared 13-maneuver pool. **The feat tier is now the maneuver-level gate** — `max_lvl = depth`
  (the old initiator-level cap is gone), and each tier grants maneuvers of its matching level
  (MT I → level 1 … MT VI → level 6), spreading picks across levels instead of clustering high.
  **Each chain costs its own paid feats** (MT I/III/V per chain), capped by available normal feat
  slots, and the chain feats are discipline-labeled ("Martial Training I (Broken Blade)") with a
  hand-built feat-tax bundle granting II/IV/VI per chain. New `path_of_war.py` helpers
  `_build_martial_training` / `_pick_chain` / `_deltas` (replacing `_martial_training_counts`); new
  `mt_feat_tax` bundle key. Initiator classes are unchanged.

### Added
- **`initiation_stat` export** — the pf1-pow initiating ability ("int"/"wis"/"cha"), arg-max of
  the FINAL mental scores (base roll + inherents + level-up bumps, ties int > wis > cha) — the
  same calculation that drives homebrew skill-rank scaling. New shared helpers
  `final_ability_score`/`final_ability_mod` in `skill_ranks.py` (`highest_mental_mod` now sits on
  top, behavior unchanged); `initiation_stat()` in `path_of_war.py` rides the export bundle for
  every character.
- **Native pf1-pow maneuvers in FoundryVTT** (module repo): `processPathOfWar()` now creates real
  `pf1-pow.maneuver` items — cloned from the `pf1-pow.disciplines` compendium when the name
  matches (clean text/icons), synthesized from `maneuvers_desc_dict` otherwise — so maneuvers
  land in pf1-pow's own **Path of War tab**, grouped under the class, names prefixed
  `(Strike)/(Boost)/(Counter)/(Stance)`, readied maneuvers pre-readied with a charge. Martial
  Training characters get `maneuverProgression = archetype` (initiatorAttr = `initiation_stat`)
  on their class item + the pf1-pow `maneuverAttr` actor flag; initiator classes keep their
  compendium progression untouched. Each stance also becomes an inactive **temporary buff** under
  a "____ Path of War ____" buff divider — mechanical changes from a curated
  `stance_changes.json` (22 stances seeded; `@pow.initLevel` scaling via `ifelse()/gte()`),
  description-only otherwise. The tab's sort is overridden to discipline →
  Strike/Boost/Counter/Stance → level within each level section. Legacy feat-item section remains
  as the fallback when pf1-pow is disabled.
- `Backend/scripts/build_stance_changes.py` — manual tool that drafts pf1 buff `changes` for PoW
  stances from `Martial_Disciplines.json` (conservative flat-bonus + IL-scaling regexes; output
  flagged for hand-curation into the module's `stance_changes.json`).
- **Path of War selection v2.** Initiator classes now **specialize in 2-3** of their class
  disciplines (all maneuvers, stances, and style chains draw only from those); maneuver/stance
  selection is **prerequisite-legal** (a pick like Snapping Turtle Rush — 6th-level Iron Tortoise
  strike, "Two Iron Tortoise maneuvers" — is only taken once 2 same-discipline picks precede it;
  stances count, per PoW); and initiators always take **1 to N(specialized) style feat chains**
  from the Metzofitz catalogue — the base style feat consumes a normal feat slot like Martial
  Training, both followers always bundle free ("Iron Tortoise Style > Shell > Snap"). New exports:
  `style_feat_tax` rides the normal feat-tax dict; `homebrew_feat_desc_dict` carries descriptions
  for feats absent from the Foundry template (style chains + Martial Training I–VI).
- **FoundryVTT Path of War sheet section** (module repo): a "____ Path of War ____" separator
  followed by one item per known maneuver — charges 0/1, readied ones pre-charged 1/1, stances
  passive with a "(Stance)" suffix — under the modded sheet's **Combat Talents** (subType
  `combatTalent`) or pf1-pow's native **Martial Disciplines** section (subType
  `martialDiscipline`) on stock sheets.
- `.claude/skills/path-of-war` skill — Path of War rules + this repo's full implementation map
  (tables, prereq quirks, style-chain derivation, feat-tax interplay, Foundry integration).
- **Medic** (Metzofitz homebrew Path of War initiator) is now generatable like the base PoW classes:
  added to `class_data.json` (Wis / M BAB / d8 / 4 skill ranks, via `build_pow_class_data.py` which
  now also reads the `metzofitz` tree), the `path_of_war_class` list, and the front-end dropdowns.
  Its maneuvers/disciplines resolve from the `metzofitz` branch of `path_of_war_maneuvers_known.json`
  (`path_of_war.py` initiator-counts now falls back to that tree).
- `Backend/scripts/fix_foundry_change_formulas.py` — one-off migration tool for the FoundryVTT
  module's bundled item JSONs (`every_feat/trait/class_feature/class[.|_MODS].json`). Foundry v13's
  pf1 system (v11) dropped JS-ternary change formulas (`@skills.per.rank>=10?4:2` → `Unresolved
  StringTerm`); the script's recursive-descent parser rewrites every ternary in `formula`/duration
  `value` fields and `[[…]]` inline rolls to the new function syntax (`ifelse(gte(…), 4, 2)`), with
  `.bak` backups. Also a reusable `tools/export_every_class.macro.js` (in the module) that rebuilds
  `every_class.json` from the `everyClassPerson` actor so Path of War classes (and any future module
  classes) resolve on the Foundry sheet, plus a `collectItems` type-guard fixing the Stalker
  class-vs-Slayer-talent name collision. (FoundryVTT module repo only; backend generation unchanged.)
- **Path of War** (Dreamscarred Press) generation. The six base initiator classes — stalker,
  warlord, warder, harbinger, mystic, zealot — generate end-to-end (class entries built into
  `class_data.json` from the scraped Metzofitz data) and are **back in the random class pool**;
  they pick their disciplines, maneuvers known/readied and stances from their own class tables
  (`path_of_war_maneuvers_known.json`). **Any other character can roll "martial paths"** (BAB L:
  0–1 disciplines, M/H: 0–2; +1 to both bounds at level 20+): access rides the Martial Training
  I–VI feat chain taken as deep as BAB allows (I/III/V consume normal feat slots, II/IV/VI arrive
  free via the existing feat-tax pairs), with counts from a new cumulative
  `martial_training_progression.json` — mirroring the spells-known / spells-per-day concept with
  **no ability-modifier bonuses**. Actual maneuvers and stances are drawn from the chosen
  disciplines' lists, level-gated by initiator level (class level for initiators, half level for
  Martial Training users, further capped by chain depth). New exports: `martial_disciplines`,
  `initiator_level`, `maneuvers_known_list`/`maneuvers_readied_list`,
  `maneuvers_choose_from`/`maneuvers_readied_names`, `stances_chosen`, `mt_feats`, and
  `maneuvers_desc_dict` (full per-maneuver text for the sheet), plus a `PoW ->` audit line.
  (Metzofitz homebrew initiator classes and PoW archetypes are noted follow-ups in
  `docs/feature_spec_todo.md` §1.)
- `feat_budget` export (per-bucket feat-row targets: normal/story/flaw/flavor/class/teamwork/
  bloodline) plus a `feat rows -> actual/budget` audit line in the CLI output, so a generation
  that comes up short is visible at a glance.
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
- **Stalker** and **Zealot** are temporarily excluded from selection (random + explicit) via a new
  `pow_classes_pending_foundry` list in `data.py` — they generate fine on the backend but the
  pf1-pow FoundryVTT compendium doesn't ship their class items yet, so the Foundry sheet can't
  resolve them. Re-enable by emptying that list and uncommenting the dropdown entries once the
  module includes them.
- The six Martial Training feats now live in `data/feats.csv` with sentinel type `Path of War`
  (visible to the feat-tax engine and description lookups, invisible to every random feat pool),
  and their `feat_tax.json` entries moved to `tax_chain_override` respelled in roman numerals
  ("martial training i" → "martial training ii", …) so they actually match the CSV names — the
  old arabic spellings ("martial training 1") could never resolve.
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

### Removed
- Every character no longer receives Two-Weapon Fighting + Two-Weapon Defense unconditionally —
  leftover test appends in `main_test.py` (from the BAB/caster-level selection work) gave the pair,
  plus their tax chains, to ~every generated character and could duplicate an organically selected
  copy. They now appear only when actually selected or class-granted.

### Fixed
- Martial Training feats are no longer silently dropped on the FoundryVTT sheet: they're absent
  from the module's `every_feat.json`, so `processFeatTrait` console-warned and lost the rows;
  the module now synthesizes items from the backend's `homebrew_feat_desc_dict` (same fallback
  covers style-chain feats and feat-tax children).
- `archetype_data()` no longer crashes (`KeyError`) for a class with no entry in `archetypes.json`
  (e.g. the Metzofitz Medic) — it now returns an empty archetype instead of indexing blindly.
- Warder and Mystic class bonus feats are no longer silently zero: `extra_combat_feats()` returned
  early without ever assigning `class_feats_amount`, so the two classes' bonus-feat schedules
  existed but never granted feats.
- Path of War discipline parsing no longer corrupts names: the old parser substring-matched "or"
  inside "Cursed Razor"/"Iron Tortoise" and stripped "and" out of "Fools Errand", and left
  "either …" prefixes behind; it now splits on word boundaries and resolves "X or Y" choices
  correctly. Also fixed the `harbringer` key typo in `path_of_war_maneuvers_known.json` and the
  backslash + wrong-case data paths in the (previously commented) Path of War config entries,
  which would have broken on the Linux deploy.
- A feat-tax bundle now follows its feat when the level reorder reseats the feat between the
  normal and class-bonus buckets — previously the bundle stayed filed under the pre-reorder
  bucket's tax dict, so the sheet lost the "Primary > Child" chain for migrated feats.
- Feat-tax chains with ability-score prerequisites now grant. "Dex 13"-style gates matched neither
  prerequisite filter, so chain links like Rapid Shot, Manyshot and the whole Improved/Greater
  Two-Weapon Fighting and Two-Weapon Defense lines could never release as free tax feats; stat
  gates are now auto-satisfied like BAB/level gates (selection already guaranteed final-level
  legality). Point-Blank Shot now bundles its archery line instead of leaving Precise/Rapid Shot
  as separate rows.
- Feat-tax name matching is punctuation-normalized (hyphens/underscores read as spaces, curly as
  straight apostrophes) on every comparison — config keys, prerequisite parts, owned-feat checks,
  Mythic detection — so `feat_tax.json` spellings like "point blank shot"/"blind fight" fire for
  the CSV-spelled feats ("Point-Blank Shot"/"Blind-Fight") and vice versa; granted chain names
  keep their feats.csv spelling so the sheet strip and FoundryVTT compendium lookups still match.
- Characters no longer generate with fewer feat rows than their level grants. Three causes:
  `generic_feat_chooser` silently selected one fewer feat than requested (an internal `-1` that two
  call sites compensated for and the truly-random path didn't, leaving every truly-random character
  at least one feat short); the truly-random path had no shortfall top-up when the filtered feat
  pools ran dry (the curated path's top-up is now shared by both, widening the pool until the
  budget is met); and a slot freed by the feat-tax child strip (the feat renders bundled on its
  primary instead) was never refilled — normal and class-bonus slots are now backfilled with fresh
  picks, which get their own feat-tax pass so bundles stay consistent.
- The same feat can no longer be generated twice (e.g. "Weapon Focus" appearing two times on one
  sheet). Class-granted picks — ranger combat-style feats, monk bonus feats, bloodline feats — are
  now registered as owned **before** the general feat pool draws, so the pool can't re-pick them; a
  case-insensitive dedup of the merged feat list backstops any remaining same-name collisions.
- Teamwork-feat selection (Inquisitor/Hunter/Cavalier/…) can no longer re-pick a feat the main pool
  already chose (e.g. Dodge appearing under both feats and teamwork feats): `choosing_feats` now
  drops already-owned feats from its candidate pool, which accumulates across selection passes.
- **Greater combat-maneuver feats are now granted.** Improved Drag/Trip/Disarm/Bull Rush/Sunder/
  Overrun/Dirty Trick/Steal/Grapple/Feint (plus Mobility, Stunning Fist, …) were never recognized
  as feat-tax primaries because their only feat prerequisite is itself a house-waived free feat
  (Power Attack / Combat Expertise / Improved Unarmed Strike — the `tax_primary_blocklist`); waived
  prereqs no longer disqualify a feat from heading its chain, so a held Improved Drag now releases
  Greater Drag (then Quick Drag, …) on the 2-level cadence. The "Greater X" variant is hoisted to
  the front of an "Improved X" chain so it wins the first free slot instead of losing to
  alphabetically earlier siblings (e.g. Drag Down before Greater Trip).
- A chain feat shared by two primaries' trees no longer bundles under both (e.g. Craft Construct
  under both Craft Magic Arms and Armor and Craft Wondrous Item; Riptide Attack under both Improved
  Drag and Improved Trip): the five feat-tax passes now share one granted-set, and earlier grants
  count as owned for later links' prerequisites.
- The tax-child strip now also covers the separately-exported `teamwork_feats` and `bloodline_feats`
  lists (labels kept in lockstep), so a feat bundled onto a primary can't simultaneously render as
  its own teamwork/bloodline entry.
- Ranger mounted-combat style could offer the unmatchable `" Trick Riding"` (leading space) and the
  monk bonus list `gorgons fist` / `medusas wrath` (missing apostrophes vs `feats.csv`); the JSON
  data now uses the canonical names, and feat-name registration strips stray whitespace.
- Explicit feat-tax chain entries in `feat_tax.json` written with curly apostrophes (’) could never
  resolve against `data/feats.csv` (straight `'`) and were silently skipped: Scorpion Style's chain
  now names `gorgon's fist` / `medusa's wrath`, and the dead `serpent's lash` entry is renamed to
  the CSV's actual feat names (`serpent lash` → `greater serpent lash`). Entries for feats genuinely
  absent from `feats.csv` (Believer's Boon, Marksman's Utility, Possessed Hand's children) are left
  flagged until the feat data exists.
- Feats are now acquired at levels where their prerequisites are actually met. Selected feats (already
  legal at the character's final level) were dropped onto acquisition levels by list position, so a feat
  could surface before its prerequisite feat or before the required base attack bonus — e.g. a Fighter
  showing Greater Feint at level 4 (needs Improved Feint **and** BAB +6) ahead of Improved Feint. A new
  `assign_feats_to_levels()` (`Backend/utils/class_func/feat_level_assignment.py`) reorders the normal
  and class-bonus feats as one pool so each lands at a level slot that satisfies its BAB / class-level
  gates and follows its prerequisite feats; `class_feat_labels` (e.g. "Fighter 6") follow suit. Runs
  after the feat-tax child strip (which reindexes the positional levels) and reuses the cached
  prerequisite graph, so generation time is unchanged (sub-millisecond per character).
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
