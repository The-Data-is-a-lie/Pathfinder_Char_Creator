---
name: changelog
description: Maintains changelog.md for the Pathfinder character generator. Use after making any code change, completing a task or feature, fixing a bug, or when the user mentions a changelog, release notes, version bump, or "what changed". Adds entries under the Unreleased section using the Keep a Changelog format, and rolls Unreleased into a versioned release when cutting a version.
---

# Changelog maintenance

Keep `changelog.md` (repo root) current using the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format and [Semantic Versioning](https://semver.org/).

## When to update it
Update `changelog.md` whenever you make a **user- or developer-visible change**: a new feature, a behavior change, a bug fix, a removal, or a security fix. Skip purely internal noise (formatting, comment typos, ephemeral/scratch files such as `SESSION_PLAN.md`).

## How to add an entry
1. Open `changelog.md`.
2. Under `## [Unreleased]`, find or add the right category subheading and add a concise bullet:
   - **Added** — new features (e.g. a new generator option, a new class/race).
   - **Changed** — changes to existing behavior.
   - **Deprecated** — soon-to-be-removed features.
   - **Removed** — removed features.
   - **Fixed** — bug fixes.
   - **Security** — vulnerability fixes.
3. Replace the `_No changes yet._` placeholder with the first real entry when it appears.

Write entries from the reader's perspective — *what changed and why it matters*, not which files moved. One line each.

Example:
```
## [Unreleased]

### Added
- Optional Metzofitz homebrew feats via the `homebrew_feat_amount` flag.

### Fixed
- Alignment-based spell exclusions no longer drop domain spells.
```

## Cutting a release
When the user tags or ships a version `x.y.z`:
1. Rename `## [Unreleased]` to `## [x.y.z] - YYYY-MM-DD` (today's date).
2. Add a fresh empty `## [Unreleased]` block above it.
3. Choose the version per SemVer: **MAJOR** for breaking changes, **MINOR** for new backward-compatible features, **PATCH** for fixes.

## Works with commits
Changelog categories map cleanly onto the Conventional Commit types used in the `commit-conventions` skill (`feat` → Added, `fix` → Fixed, `perf`/`refactor` → Changed, etc.), so a clean commit history makes changelog upkeep mostly mechanical.
