# General Rules

Apply to every MCS repository, every language, humans and agents alike.

## Plan first

No code without an approved plan. The project is in a phase where
architecture decisions are open; building without agreement usually builds
the wrong thing.

1. **Understand**: read the existing code, ask questions, state assumptions.
2. **Propose**: options with pros and cons and a clear recommendation.
3. **Agree**: a human decides.
4. **Build**: only after approval.

Push back when a plan is bad. Agreement that only wants to be nice is harmful.

Never without asking first:

- refactors "while I was there"
- new dependencies
- architecture changes in passing
- files nobody asked for

## Git

- Never push directly to `main`, `develop` or `release/*`. The guard blocks
  it.
- Every change: branch `feature/<short-name>` or `fix/<short-name>`, small
  commits, push the branch, open a pull request, ask who reviews, wait. Never
  merge your own pull request.
- No `git push --force` on shared branches, no rewriting other people's
  history.
- One logical change per commit. Formatting-only changes get their own commit.
- Commit messages follow Conventional Commits: `type(scope): imperative
  summary`, at most 72 characters in the summary line. Types: `feat`, `fix`,
  `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`.
- No AI traces in commits, pull requests, comments or docs: no "Generated
  with", no tool `Co-Authored-By` trailers, no assistant phrasing.
- Never commit secrets, `.env` files with real values, build output, or
  editor and OS files.

## Pull requests

- Small enough to review in one sitting.
- Description: what changed, why, how it was tested.
- Before opening: thermo-nuclear review on the diff, then code-review.

## Documentation

- Every public class, function and enum has a doc comment: what it does, each
  parameter, the return value, behaviour on error. C and C++ use Doxygen
  (`///`, `@brief`, `@param`, `@return`).
- The project version appears in generated documentation.
- Comments explain why, not what. Link the bug report, plan or datasheet
  section when a line exists because of it.
- Change the comment when you change the code.

## Nothing leaves the project

- No emails, calendar entries, or messages in company tools (Slack, Teams,
  Jira, Confluence).
- Nothing written to synced cloud folders (OneDrive, SharePoint).
- No tickets, issues or comments in external systems.
- Results go into the project repository or the local project folder only.

When in doubt, ask instead of sending.
