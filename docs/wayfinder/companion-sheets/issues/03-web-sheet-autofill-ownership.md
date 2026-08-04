# 03 — How does an auto-filled companion coexist with the user's hand-edits?

Type: grilling
Status: resolved (2026-08-03)
Blocked by: —
Map: [Companion sheets](../map.md)

## Answer — seed once into the user's own array, then get out of the way

**The collision the ticket was written to solve does not exist.** Two facts about the sheet repo,
both established by reading it rather than by preference:

1. **A generated payload never carries `_sheet`.** `toRecord()` (`scripts/library.js:54-59`) mints
   `sheet.id ??= newId()` lazily, so every backend fetch and every pasted raw payload lands as a
   **new** library record. There is no path by which a fresh generation overwrites a character whose
   companions were hand-edited. The only same-id reload is an *exported* JSON — which carries the
   user's `_sheet` verbatim, edits and seed-flag included, and therefore restores rather than
   clobbers.
2. **`adoptCharacter()` is the wrong seam.** `renderSheet()` (`scripts/sheet.js:531-532`) already
   calls two one-time seeders — `seedBackendStatBonuses` and `seedRacialColumn` — each guarded by its
   own `_sheet.*Seeded` flag. `seedRacialColumn`'s own comment says why that matters: *"Own flag (not
   statSeeded) so characters saved before this feature still upgrade."* An adopt-time hook would fill
   new characters and leave every record already in the library empty forever.

So: **`seedCompanions(data)` joins those two in `renderSheet`, guarded by `_sheet.companionsSeeded`.**
It goes in the same three-line block (`sheet.js:530-532`), which sits *above* the
`viewMode() === 'simple'` early return — so the fill happens in both view modes, and on
`loadCharacter()` (`roster.js:54`) as well as on a fresh generation.
It appends generated rows to `_sheet.companions` and never touches a row it did not create. After
that first render a generated companion is an *ordinary* companion — the same model, the same
`dblclickEditable` wiring, the same `×` button. Nothing refreshes, nothing merges, nothing is
read-only.

*Rejected:* live-derive with a per-field override layer (`_sheet.companionOverrides`) — it keeps
generated numbers correct if the payload ever changes, but the payload never changes for a saved
character, and the price is rewiring every editor in `companions.js` plus designing a
"reset to generated" affordance nobody asked for. *Rejected:* a read-only generated block above the
editable list — cleanest provenance, but the player cannot tick their own companion's HP down without
copying it first, and it splits one tab into two render paths.

### Provenance

Each seeded row carries two extra keys, both inert to the existing render code:

- `source: 'generated'`
- `grantor: <entry.grantor>` — `'druid'`, `'wizard'`, …

`id` is `'gen-' + grantor + '-' + index` (index within `bonded_creatures`), not the `Date.now()`
form `newCompanion()` uses, so a row is identifiable across a save/load without a second flag. The
existing `type` field is **not** overloaded to carry provenance: it is a user-editable dropdown, and
a player retyping their eidolon as "other" must not silently change what the row *is*.

### The mapping function

`bonded_creatures[i]` → one companion row. Entries with `stats === null` are **not** rows (see
*Absences* below).

| Row field | Source | Notes |
|---|---|---|
| `id` | — | `'gen-' + grantor + '-' + i` |
| `source` | — | literal `'generated'` |
| `grantor` | `entry.grantor` | |
| `name` | `entry.name` | bare, see *The title* |
| `type` | `entry.type` via `TYPE_MAP` | `companion → 'animal companion'`; `familiar`/`mount`/`eidolon` identity; anything else → `'other'` |
| `hd` | `stats.hd` | the creature's HD, **not** `effective_level` |
| `hp` | `stats.hp` | scalar → `{ current: hp, max: hp }` |
| `ac` / `touch` / `ff` | `stats.ac` / `stats.touch_ac` / `stats.flat_footed_ac` | |
| `saves` | `stats.saves` | same three keys |
| `abilities` | `stats.abilities` | same six keys; the tab recomputes modifiers itself |
| `speed` | `stats.speed` | **verbatim string** — see *Model changes* |
| `cmb` / `cmd` | `stats.cmb` / `stats.cmd` | new fields |
| `skills` | `stats.skills` | `{name, total}[]`, sorted by name; `ranks` is dropped — a total is what you roll |
| `attacks` | `stats.attacks` | folded per the rules below |
| `notes` | composed | see *The notes block* |

`stats.natural_armor` and `stats.space` are **not** mapped as fields: the first is already inside
`ac`, and the second is a consequence of `size`, which the notes block carries.

**Attack folding.** `stats.attacks[]` is richer than the row's `{name, atk, dmg}`:

- `name` ← `(alternative ? 'or ' : '') + (count > 1 ? count + ' ' : '') + name + (notes ? ' (' + notes + ')' : '')`
  — so `{name:'talons', count:2}` reads `2 talons`, and the roc's `spit` alternative reads
  `or spit (ranged touch attack, …)`.
- `atk` ← `line.atk ?? 0`.
- `dmg` ← `damage + (crit_multiplier ? '/×' + crit_multiplier : '')`, or `'—'` when `damage` is empty
  (an unparsed prose attack — the rider is already in the name).

**The notes block**, composed in this order, one line each, blank lines omitted:

```
Small, 5 ft. space · 4 bonus tricks
Special: link, share spells, evasion, 2 ability score increase, devotion, multiattack
Qualities: low-light vision
Special attacks: …
Feats: Acrobatic, Endurance, Improved Natural Armor, Intimidating Prowess, Spring Attack
Climb 30 ft. · Bonus feat                       ← stats.other, one "Key value" pair per entry
Grew Medium → Large (already applied above)     ← stats.size_change, provenance only
⚠ Not applied: progression_override: …          ← stats.unapplied
```

`stats.merge_notes` is **dropped**. It explains how a number was built (`"4th-level advancement
applied"`), not what the creature is, and neither renderer shows it. `stats.unapplied` is kept
precisely because it says the opposite — something the generator *could not* do, which the player
needs to know. `size_change` renders as a sentence and never as a modifier: ticket 04 established
that its values are already inside `ac` / `attacks[].atk` / `cmb` / `cmd` / `skills`, and re-applying
it double-counts.

### The merge rule

Three lines, and there is no fourth case:

1. `_sheet.companionsSeeded` set → **return immediately**. The character has been seeded; its
   companion rows are the user's.
2. Otherwise, set the flag, append one row per non-absence entry, and **leave every existing row
   untouched** — including hand-made rows on a character saved before this feature existed.
3. A character with hand-typed companions who is upgraded by (2) may end up with a duplicate — their
   own bird *and* the generated one. That is correct and visible: both rows are editable and either
   has a `×`. Silently reconciling them would require guessing which fields the player meant to keep.

### Absences

`bonded_creatures` entries with `species: null` are **not seeded** — they are not creatures and must
not become deletable rows. They render straight from the payload on every render, as one dim line
above the add-row, and they are the only thing on the tab that is not user-owned.

`outcome` is a closed set of five tokens, so the phrasing is a map, not a formatter:

| `outcome` | line |
|---|---|
| `granted` | *(not an absence)* |
| `domain` | `Druid — no animal companion: chose a domain instead.` |
| `bonded_object` | `Wizard — no familiar: took a bonded object instead.` |
| `bond_with_allies` | `Cavalier — no mount: bonded with allies instead.` |
| `archetype_removed` | `Ranger — no animal companion: traded away by <entry.archetype>.` |

The grantor is title-cased and the type label comes from the same `TYPE_MAP` as a real row, so the
two never drift. An unrecognised `outcome` falls through to the token itself rather than being
swallowed — a new `on_loss` in `companion_grantors.json` should look odd on the sheet, not vanish.

*Rejected:* skipping absences entirely (an empty tab cannot distinguish "the generator decided no
companion" from "this is broken" — the exact confusion that opened this map). *Rejected:* folding the
line into the existing empty-state placeholder (a multiclass with one real companion and one absence
would silently lose the explanation).

### The title

The row's editable name field gets the **bare `entry.name`**. §8 **D9** and the charting note stand —
each renderer composes its own label — and on this consumer the composition is already on screen:
the tab heading says *Companions*, the dropdown beside the name says *animal companion*, and the
`HD` badge follows. `Aelia's animal companion: Rukh — [animal companion] — HD 5` states the type
three times and makes the field too long to double-click-edit comfortably. Foundry keeps the full
composed Actor name; the two renderers differ here on purpose.

### Model changes to `companions.js`

The mapping needs three changes to the row model. All three are backward-compatible with rows
already saved:

1. **`speed` becomes free text.** `editNum(comp, 'speed')` (`:120`) → the string `dblclickEditable`
   already used for `name` and `dmg`. `stats.speed` is prose — `'10 ft. , fly 80 ft. (average)'` —
   and the second number is the one a bird companion's player actually needs. Existing rows carry
   `speed: 40`, which stringifies unchanged.
2. **`cmb` / `cmd` join the vitals strip.** `newCompanion()` seeds `0` / `10`.
3. **`skills` joins the model** as `{name, total}[]`, rendered as a row mirroring the abilities row
   with a 🎲 per skill into the shared roll log. `newCompanion()` seeds `[]`, and the row is omitted
   when empty, so a hand-made companion looks exactly as it does today.

`newCompanion()` is otherwise untouched, which retires the ticket's *seeded defaults* question: a
generated row is built by the mapper and never passes through `newCompanion()`, so the familiar
HP-and-HD seeds (`:33-34`) never collide with real numbers. They remain the right default for a
hand-added familiar, which is the only thing they were ever for.

### What this leaves slice #34

A mapping function, a five-token phrase map, a three-line guard, and three small widget changes.
The check is the map's finish-line gate 3 — the same payload that produced the two Foundry Actors
opens on the web sheet with the Companions tab pre-filled and nothing hand-typed.

## Question

The web sheet's Companions tab is **user-owned**. `_sheet.companions[]`
(`Pathfinder-Character-Sheet/scripts/tabs/companions.js`) is created by `newCompanion()` (`:25-42`)
and every field — name, HD, HP/AC/saves, abilities, attack lines, notes — is wired to
`dblclickEditable` → `quietSave()` (`:61-190`). Nothing in it comes from the payload today.

The charting decision was to **auto-fill that tab** rather than mint a separate roster character
(upholding the header comment's ruling that *linked roster characters were ruled out by portability*).
That puts generated data and hand-typed data in the same array, and the collision has to be specified
before slice 8 writes a line.

Open:

- **Landing point.** `adoptCharacter()` (`scripts/roster.js:72-75`) is the single funnel for both the
  backend fetch (`scripts/generate.js:193-218`) and pasted JSON (`:237-245`), so it is the obvious
  seam. Confirm — or find a reason the mapping belongs inside `companions.js` instead, next to the
  model it writes.
- **Re-import.** A character is saved to the IndexedDB library (`scripts/library.js`) and re-loaded
  later, or the same seed is regenerated. Do generated entries get replaced, merged, or left alone?
  What happens to a companion the user edited by hand and then re-imported over?
- **Provenance.** Does a generated entry carry a marker (a `source: 'generated'` flag, or the
  backend's `grantor`) so it can be refreshed without clobbering user-created siblings? The model has
  an `id` and a `type` already; `type` is a closed set
  (`'animal companion'|'familiar'|'eidolon'|'mount'|'other'`) that maps cleanly onto the payload's
  `type` — is that mapping enough, or is an explicit flag needed?
- **Seeded defaults.** `newCompanion()` seeds familiar HP as half the master's `Total_HP` and `hd`
  as the master's level (`:33-34`). Once the payload carries real numbers those seeds are wrong —
  suppressed for generated entries, or overwritten?
- **Absence entries.** `bonded_creatures` includes entries with `species: null` that exist purely to
  explain *why* there is no creature (the druid's domain flip, an archetype trade-away). Does the tab
  render that explanation, or skip them entirely?
- **The title.** Charting settled that each renderer composes `<Master>'s animal companion: <Name>`
  itself. On this consumer the companion has no sheet header of its own — it is a block in a tab. Does
  the composed title appear in that block's name field, or does the bare `name`, with the tab's own
  heading supplying the context?

Answer concretely enough that slice 8 is a mapping function plus a merge rule, with no judgement left
in it.
