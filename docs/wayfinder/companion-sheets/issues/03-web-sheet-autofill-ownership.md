# 03 — How does an auto-filled companion coexist with the user's hand-edits?

Type: grilling
Status: open
Blocked by: —
Map: [Companion sheets](../map.md)

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
