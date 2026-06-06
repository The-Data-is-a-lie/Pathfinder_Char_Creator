---
name: commit-conventions
description: Git commit and version-control conventions for this repo. Use whenever writing a commit message, committing or staging changes, creating a branch, or opening a pull request. Enforces Conventional Commits, atomic commits, a GitHub-Flow branching model, and a no-secrets rule.
---

# Commit & version-control conventions

Follow these whenever committing or managing branches in this repo.

## Commit message format — Conventional Commits
```
type(scope): subject

body (optional, wrapped ~72 chars)

footer (optional)
```
- **type** (required): `feat` (new feature), `fix` (bug fix), `docs`, `style` (formatting only), `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- **scope** (optional): the area touched — e.g. `feats`, `spells`, `stats`, `app`, `data`, `foundry`.
- **subject**: imperative mood ("add", not "added"/"adds"), ≤ ~50 chars, no trailing period.
- **body**: explain *what* and *why* (not how); wrap at ~72 chars; separate from the subject with one blank line.
- **footer**: `BREAKING CHANGE: <desc>` for incompatible changes; reference issues like `Refs #12` / `Closes #12`.

Examples:
```
feat(feats): wire Metzofitz homebrew feat selection behind the flag
fix(spells): keep domain spells when applying alignment exclusions
docs(readme): document the 12 generator inputs
chore(data): refresh scraped feats.csv from Archive of Nethys
```

## Atomic commits
One logical change per commit. Don't bundle unrelated edits — it keeps `git bisect`, code review, and reverts clean. When a working tree has mixed changes, stage selectively with `git add -p`.

## Branching — GitHub Flow
- `main` stays deployable (it's what Render serves).
- Branch per change off `main`: `feat/<short-name>`, `fix/<short-name>`.
- Commit small and often; open a pull request to merge; delete the branch after merge.
- Avoid committing non-trivial work directly to `main`.

## Never commit secrets
`*.env`, API keys, and `Backend/instance/config.py` are git-ignored — keep it that way. (A cached `.env` already had to be scrubbed from history in commit `24a83fb`; don't repeat it.) If a secret is staged, unstage it before committing.

## When Claude authors a commit
- Only commit or push when the user asks. If on `main`, create a branch first.
- End the commit message with the trailer:
  ```
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

## Payoff
Because commits follow Conventional Commits, the `changelog` skill's entries map straight from commit types (`feat` → Added, `fix` → Fixed), and changelogs / release notes can be generated from history.

---
_Guidance based on: [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/), atomic-commit and commit-message best practices, and the GitHub Flow branching model._
