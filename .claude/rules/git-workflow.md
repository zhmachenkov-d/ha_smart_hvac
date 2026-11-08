# Git workflow

## Branches and PRs

- Never commit or push to `main`; work on a feature branch and open a PR.
- Branch name: `<type>/<short-slug>` with a Conventional Commits type,
  e.g. `fix/1-7-commission-parse-hardening`, `chore/epic-retro`.

## Conventional Commits

CI (`.github/workflows/conventional-commits.yaml`) checks the PR title and
every non-merge commit subject in `base…head`.

- Shape: `<type>[(scope)][!]: <subject>`.
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`,
  `ci`, `chore`.
- Subject: imperative ("add", not "added"), no trailing period, first line
  ≤ 72 characters.
- Breaking change: `!` after type/scope and/or a `BREAKING CHANGE: …` footer.
- Body only when the "why" is not obvious; wrap at ~72 characters.
- Write the message from the actual diff (`git diff --staged`), not from intent.
  One logical change per commit.

## PR description

- **Summary**: what changed and why (1–3 sentences or bullets).
- **Test plan**: how it was verified.
- **Related issues**: only if the user gave or clearly implied an issue key;
  do not search trackers for one.

## History rewriting

- `--amend`, interactive rebase and squash only on personal feature branches.
- After rewriting a pushed branch, push with `--force-with-lease`, never `--force`.
- Never rewrite `main` history.

## Delete the feature branch after its PR is merged

Do this without asking once a PR is merged (the user merged it, or you did),
and when you find yourself on a branch whose PR is already merged.

1. Confirm the merge: `gh pr view <branch> --json state,headRefOid` must show
   `"state": "MERGED"`. If the PR is open or closed without merging, do not
   delete anything; tell the user.
2. Ensure the working tree is clean (`git status --short` is empty); otherwise stop
   and ask.
3. `git switch main && git pull --ff-only`
4. `git branch -d <branch>`. If `-d` refuses (squash or rebase merge), use `-D` only
   when `git rev-parse <branch>` equals the PR's `headRefOid`; otherwise the branch
   has unpushed commits — stop and report them.
5. `git push origin --delete <branch>` (an "already deleted" error is fine).
6. `git fetch --prune`
7. Never delete `main`.
