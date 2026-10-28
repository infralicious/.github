# Contributing to Infralicious

Thank you for helping Infralicious repos.
This file is the org default, for repos without their own guide.
A repo guide, if it exists, wins over this file.

## How to start

Pick an open issue, or open a new issue first.
Describe the problem, the expected result, and the steps to reproduce it.
Wait for a maintainer reply, before a large change.
Small fixes need no prior discussion, open a pull request directly.

## Pull requests

Use a branch, never push to main directly.
Keep changes small, one idea per pull request.
Keep commits signed, with a clear message.
Update docs, if your change changes behavior.
Update tests, if the repo has tests, and your change touches code.
Link the issue, in the pull request body, if one exists.
A maintainer reviews, and merges, after checks pass.

## Repo settings, do not edit by hand

Repo settings are code, in the `.github` admin repo.
Do not edit live settings in the GitHub UI, without a config change.
Live edits will be reverted by the next safe-settings sync.
Open a pull request in the admin repo, for a settings change.
Safe-settings dry run previews, and live sync applies, after merge.

## Code style

Follow the style already in the repo, first.
Use short functions, clear names, and no secrets in code.
Never commit a password, a token, a key, or a private key.
Report a secret leak at once, see `SECURITY.md`.
Use Renovate pull requests for dependency updates, where Renovate runs.
Do not open a manual dependency pull request, if Renovate already covers it.

## License

Contributions fall under the repo license, MIT, unless stated otherwise.
See `LICENSE` in each repo, for the full text.
