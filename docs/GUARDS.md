# Guards, footguns, and what else can break

This doc lists every footgun found in this repo, and the guard for it.
Guards are in layers, local, CI, ruleset, and live sync, in that order.
No single layer is enough, on its own.

## Footgun 1: dry run tests main, not the PR

Safe-settings Action mode loads config by API, from main, not from the PR.
A green dry run proves main syncs cleanly, it does not preview PR changes.
This is a design limit of safe-settings 3.0.0, in Action mode.
Guard: `scripts/check-config.py simulate`, in the Config Guard workflow.
It merges PR config locally, reads live rulesets by API, and reports create, update, and delete.
It fails on a missing required ruleset, and on a protected ruleset deletion.
It runs on every PR, with no secrets, read only, it never applies a change.
Live sync after merge is still the real test, see below.

## Footgun 2: Diffable rulesets delete unlisted rulesets

A ruleset name removed from YAML deletes the live ruleset on next sync.
Guard: simulate fails, if a live Protect main, Protect tags, Tag protection, or Default would be deleted.
Guard: local guard fails, if a required ruleset is missing from PR config.
To delete a ruleset on purpose, remove it from YAML and from the protected list in the script, in the same PR, with a clear PR body.

## Footgun 3: private and push rulesets fail on free plan

Private repos return 403 for rulesets, public repos return 422 for push rulesets.
Guard: local guard fails, on any ruleset in a private repo file, and on any push ruleset, anywhere.
This is why private service-control-policies has no rulesets, and no repo has a push ruleset.

## Footgun 4: baseline identity wipes repo identity

A name, description, homepage, private, or topics key in baseline would apply to all repos.
Guard: local guard fails, on any identity key in baseline, and on branches or rulesets in baseline.
Baseline holds only shared repo settings, labels, and additive labels.

## Footgun 5: restricted repo removal exposes a repo to sync

If docs or .github left restrictedRepos, safe-settings would sync them and could wipe them.
Guard: local guard fails, if restrictedRepos misses .github, admin, safe-settings, or docs.
Repo files for restricted repos also fail the guard.

## Footgun 6: suborg list errors move a repo to the wrong layer

A private repo in the public suborg would get rulesets and fail with 403.
A public repo missing from the public suborg would lose Protect main.
Guard: local guard requires the public list to be exactly the six public repos, and the private list to be exactly service-control-policies.

## Footgun 7: secret in a commit

A private key or client secret in a YAML file would be public, in a public repo.
Guard: local guard fails, on a raw private key or secret value, in config and workflows.
Guard: pre-commit detect-private-key hook fails, on a private key file.
Secrets live only in admin repo Secrets, referenced as secrets.* in workflows, never as values.

## Footgun 8: version pin drift

Safe-settings version lives in two workflows, a SHA in each, with a version comment.
Guard: local guard fails, if a pin is not a 40-char SHA, or if the two pins differ.
Renovate updates both pins, in one PR, never automerge, see renovate.json5.

## Footgun 9: direct push to main, bypassing checks

Admin ruleset bypass is pull_request, not always, for admin main only.
That blocks direct pushes to admin main, even for admins.
A PR can still be merged by an admin, with a failing check, that is a conscious bypass, not a silent push.
Target repos now also use bypass pull_request for branches, since 2026-10-29, see ADR-0012.
Target tag rulesets use bypass empty, since 2026-10-29, see ADR-0012.
Guard fails if a branch ruleset uses bypass always, or if a tag ruleset uses any bypass.
Guard fails if a repo file weakens baseline, see ADR-0012 for the full list.
Guard fails if a checked suborg Protect main misses its required check, see ADR-0014.

## Footgun 10: scheduled sync is not atomic

Scheduled sync runs every 4 hours, on main, and applies repos in batches.
A failure in one repo does not stop later repos, partial changes can land.
Guard: none, this is a safe-settings behavior, not a config error.
Mitigation: after every config merge, run live sync by hand, verify live, before the next schedule.
If live sync fails, fix main, do not wait for the schedule to retry.

## Footgun 11: workflow pin change to a tag, not a SHA

A tag ref would move over time, and Renovate regex would not match it.
Guard: local guard requires a 40-char SHA, with a version comment, in both workflows.

## Workflows, in order

- Validate Config, job validateConfig, YAML parse, Renovate parse, pin match.
- Config Guard, job configGuard, local invariants, see scripts/check-config.py guard.
- Config Guard, job prConfigSimulation, PR rulesets vs live rulesets, read only.
- Safe Settings Dry Run, job safeSettingsDryRun, main config only, see Footgun 1.
- Safe Settings Sync, schedule and manual, live, after merge, with verification.

Admin ruleset requires, live from 2026-10-27, ruleset id 26008879:
safeSettingsDryRun, validateConfig, configGuard, prConfigSimulation, securityDryRun, scriptTests, schemaDiscovery.
All seven run on every PR to main, so a PR cannot merge cleanly with a guard failure, unless an admin bypasses by PR.

## Pre-commit, optional, CI is the gate

Install: pre-commit install, run: pre-commit run --all-files.
Hooks: whitespace, end of file, YAML, large files, line endings, private key, and the local config guard.
Phone-first work cannot run pre-commit, so pre-commit is never required locally.
CI runs the same guard script, so a skipped pre-commit still fails in CI, before merge.
Pre-commit hooks from pre-commit-hooks v5.0.0 run in their own venv, on a Mac they work, on this VM python hooks fail, see AGENTS.md, CI is the fallback.

## FUNDING, org-wide default

.github/FUNDING.yml, github: nitrocode, verified live at https://github.com/sponsors/nitrocode
Repos without their own FUNDING.yml show the same sponsor button.
Add a platform only when an account exists, never a placeholder.

## What else can we do, later, not now

- A sync health check workflow, that opens an issue if a scheduled sync fails, no email or Slack exists today, so an issue is the only alert channel.
- A live ruleset snapshot, stored in docs, checked by simulate, to catch manual live edits that YAML does not cover, today live edits are the source of drift, and simulate already reports them as deletions.
- A branch protection to ruleset check, for target repos, today no legacy protection remains, so nothing to check.
- Renovate automerge for docs-only PRs, today automerge is off for safe-settings, and docs PRs are rare, so manual merge is fine.

## Suborg overlap, guard only, no scheduled check yet

A repo in 2 suborgs is a hard error in safe-settings, not a merge.
Guard fails on overlap, on glob patterns, and on suborgteams or suborgproperties.
Dry run cannot catch overlap, as dry run tests main, not PR.
Scheduled new-repo check is deferred, as repo creation is rare, and org has 1 member.
Revisit scheduled check if a second maintainer joins, or if repo creation becomes monthly.
