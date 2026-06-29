# Backstory examples (few-shot)

"Gold-standard" example backstories the generator shows the model as few-shot examples, so new
backstories imitate their **tone and structure**. This is in-context learning, **not** model
fine-tuning. An empty folder is fine — the generator just falls back to its built-in style.

How many are shown, and whether they're matched to the character, is set in
`Backend/json/backstory_config.json` (`num_examples`, `smart_match`). With more examples than
`num_examples`, `smart_match` feeds the closest ones (by `tags`).

## The house style these should model
- Flowing **prose** built around, in priority order: the character's **profession/vocation**, their
  **family & upbringing**, the **place they're from**, and their **situation growing up** — with only
  light other color, and **without reciting feats or game mechanics**.
- Then a short **labeled list** at the very end: `Personality:`, `Mannerisms:`, `Appearance:`,
  `Flaws:` — one brief line each.

## Preferred format: `.json` (with tags)
A single object (or a list of objects):

```json
{
  "backstory": "The finished prose backstory, ending with the short Personality:/Flaws:/… list.",
  "tags": { "race": "Human", "char_class": "Wizard", "alignment": "N", "gender": "female" }
}
```

- `backstory` is required.
- `tags` (optional) drive `smart_match` — the generator prefers examples whose **region** / class /
  race / alignment / main stat / gender resemble the NPC being generated (region and class weigh the
  most). Edit them freely. A `deity` tag is also accepted; it's informational (not currently scored).
- Optional `facts`: the FACTS block that produced the backstory; if present it's paired as a
  user→assistant example turn (a fuller demonstration).

## Also accepted: `.txt`
The entire file becomes one example backstory (prose, plus an optional bottom labeled list). No tags,
so it's selected without matching. Files are read BOM-safe. `README.md` is ignored.
