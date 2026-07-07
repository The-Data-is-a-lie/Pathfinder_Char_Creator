---
name: pull-requests
description: How to write and open a pull request / merge request in this project — the title (Conventional Commits, since squash-merge makes the PR title the commit subject), the description structure (summary → what changed → why → test plan → reviewer notes → linked issues), and reviewability practices. Use whenever creating or editing a PR/MR (gh pr create/edit, GitLab MR API), writing a PR title or body, or deciding how to split work for review. Complements the commit-conventions and changelog skills.
---

# Pull request conventions

A PR is read twice: once by a reviewer deciding to approve, and forever after by whoever runs
`git log`/`git blame` to understand *why* a change was made. Write for both. The diff already shows
*how*; the PR must supply the *what* and the *why*.

## Title — Conventional Commits (required)
`type(scope): description` — the same grammar as a commit (see `commit-conventions`). On a
**squash-merge** the PR title *becomes* the commit subject, so it MUST be a valid Conventional Commit:

- imperative mood, lowercase after the colon, ≤ ~70 chars, **no trailing period**
  (e.g. `feat(spells): parse buff spells into distributable buffs`).
- types: `feat` `fix` `docs` `refactor` `perf` `test` `build` `ci` `chore` `style` `revert`.
- breaking change: `type(scope)!: …` **and** a `BREAKING CHANGE: <what breaks>` footer.
- pick the **headline** change for the type/scope when a branch does several things; the body enumerates the rest.

## Description structure (omit sections that don't apply)
1. **Summary** — 1–3 sentences: what this PR does and why, in plain language. Google's rule: the
   summary is a short imperative statement of *what*; the body fills in the *why*.
2. **What changed** — grouped bullets, **headline change first**. State what/why per group, not a
   line-by-line how.
3. **Why / context** — the problem solved, the approach and its trade-offs, background links
   (issues, design docs, benchmarks). This is the highest-value section; `"fix bug"` / `"update
   code"` with no context is the anti-pattern to avoid.
4. **Test plan** — the exact commands/steps a reviewer can run to verify (reproducible).
5. **Reviewer notes** — what feedback you want, risky areas, deliberate out-of-scope follow-ups,
   and `@mentions` *with a reason*. If not ready, open as **Draft** or prefix the title `[WIP]`.
6. **Linked issues** — `Closes #N` / `Refs #N` (auto-closes on merge).
7. **Screenshots / recordings** for any UI-visible change.

## Reviewability
- Keep a PR **small and single-purpose**. A large feature branch should still read as one coherent
  story; **atomic Conventional-Commits history** (see `commit-conventions`) lets a reviewer go
  commit-by-commit.
- **Self-review the diff** before requesting review and call out anything surprising.
- In review threads: ask, don't tell ("what do you think about …?"); explain the reason a change is
  requested; use emoji to set tone (plain text reads as negative).

## This repo
- **Two repos, both target `main`:** the backend (GitHub — `gh pr create/edit`, `gh` is
  keyring-authenticated) and the FoundryVTT module (GitLab — MR via the api-scoped `GITLAB_TOKEN`
  in the gitignored `.env`, because the GCM oauth cred lacks `api` scope). See the
  `github-pr-workflow-windows` / `gitlab-mr-workflow` memories.
- **End every PR/MR body** with the trailer:
  `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- Commit types map to `changelog.md` sections (`feat`→Added, `fix`→Fixed) — see the `changelog` skill.

---
_Synthesized from: Conventional Commits v1.0.0 (title grammar), Google eng-practices "Writing good
CL descriptions" (summary = what, body = why; avoid contextless descriptions), and GitHub's
"How to write the perfect pull request" (purpose/context, requested feedback, mentions, tone)._
