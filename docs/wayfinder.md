# Wayfinder maps have moved

The wayfinder tracker — the maps and decision tickets that chart this stack's in-flight design
efforts — now lives in a **separate repository**:

> **<https://github.com/The-Data-is-a-lie/tickets>**
> → `tks/pathfinder-char-creator/`

## Why it moved

These efforts increasingly span three repositories at once — this backend, the
`pf1e_random_char_generator` FoundryVTT module, and the standalone web sheet. A tracker living
inside one of the three repos it tracks had become the wrong home: a ticket about the module's
rendering was filed here, against code that isn't here.

The tickets repo follows the same format as the `okf-bundles` knowledge base — an index at every
level, YAML frontmatter, progressive disclosure down to leaf files — so both are readable by a
person or an agent with nothing but a `git clone`.

## Layout

```
tks/pathfinder-char-creator/
  index.md
  log.md
  feature/          class-choices · class-pool · companion-sheets · companions · psionics
  architecture/     scripts-and-phases
```

Each effort folder holds a `map.md` (destination, notes, decisions so far, fog, out-of-scope) and
its tickets as flat `NN-name.md` files beside it. A ticket body is the **question**; the resolution
is appended to it on close, and gisted onto the map.

## What is still here

- **`changelog.md` keeps its historical references** to `docs/wayfinder/...` paths. Those entries
  record what was true when they were written, and a changelog that gets rewritten is not a record.
  Everything from 2026-08-05 onward cites the tickets repo.
- **Links from `docs/plan_1.0_finish.md`, `docs/feature_spec_todo.md` and `docs/CODEBASE_MAP.md`**
  now point at the tickets repo directly.

Links *from* a ticket back into this repository are absolute GitHub URLs, so a ticket resolves no
matter where it is read from.
