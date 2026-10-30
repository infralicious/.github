# Architecture

This file explains how safe-settings works in this org.
It explains the parts, the flow, and the sharp edges.
Read it before you change config, workflows, or App permissions.

## Parts

Admin repo: `infralicious/.github`, public, branch `main`.
Config root: `safe-settings/`, inside the admin repo.
Engine: safe-settings code, checked out from upstream at runtime.
Token: GitHub App installation token, not `GITHUB_TOKEN`.
Trigger: schedule every 4 hours, plus manual dispatch.
Preview: dry run workflow, on pull requests, NOP mode only.

## Config layers, in precedence order

Repo layer wins over suborg layer, suborg wins over org layer.
Org layer: `safe-settings/settings.yml`, baseline for all repos.
Suborg layer: `safe-settings/suborgs/*.yml`, for a repo group.
Repo layer: `safe-settings/repos/*.yml`, for one repo only.
Deployment layer: `safe-settings/deployment-settings.yml`, for guards.
Guards: `restrictedRepos` skips a repo, even if it is installed.
Restricted today: `.github`, `admin`, `safe-settings`, `docs`.
Per-repo files live in the admin repo, not in each target repo.
Safe-settings never reads a target repo `.github/settings.yml`.

## Plugins in use

Repository plugin: identity fields, flags, merge methods, security.
Labels plugin: additive mode only, see below.
Rulesets plugin: main and tag rulesets, weak gates, public repos only.
Suborg plugin: `suborgrepos` lists, exact names, no glob patterns.
No other plugin runs live today.
Other plugins are commented in config, with a reason for each.
Commented does not mean forgotten, it means a deliberate no.

## Additive labels

Org config sets `additive_plugins: - labels`.
Additive means safe-settings adds and updates labels, never deletes.
A label made in the GitHub UI stays, even if it is not in YAML.
Without additive mode, an unlisted label would be deleted by sync.
That risk is why additive mode is on, for all repos.

## Rulesets, weak gates by design, migrated 2026-10-27, hardened 2026-10-29

Main ruleset blocks force pushes and branch deletion.
Main ruleset sets no required reviews, and no required checks.
Main ruleset bypass is admin pull_request, since 2026-10-29, see ADR-0012.
Main ruleset allows squash merges only, since 2026-10-29, see ADR-0012.
Sole maintainer needs no required reviewer, and no required check.
Public repos get rulesets, private repos do not get branch rulesets.
Private repos on a free plan return 403 for branch rulesets.
That 403 is a plan limit, not a config error.
Rulesets are managed by safe-settings now, since the 2026-10-27 migration.
Rulesets are Diffable, so sync deletes rulesets not listed in YAML.
Tag rulesets have bypass empty, since 2026-10-29, except actions-checkout which already had it.
Tag creation still works, no creation rule exists in tag rulesets.
Required checks live in dedicated suborgs, see ADR-0014 and ADR-0016.
Actions-checkout required check test, since 2026-10-29, see ADR-0014, via dedicated suborg.
Site required check htmlproofer, since 2026-10-29, see ADR-0016, via dedicated suborg.
See `RULESETS-MIGRATION.md` for the 2026-10-27 migration history only.

## Flow, live sync

Schedule or manual dispatch starts the sync workflow.
Workflow checks out this admin repo, from main.
Workflow checks out safe-settings code, from upstream, by SHA.
Workflow installs Node 22, then runs `npm ci`.
Workflow runs `npm run full-sync`, with App env vars.
Full-sync reads config from the admin repo, by API.
Full-sync reads config from main, not from a pull request branch.
Full-sync builds one config per installed repo, in layers.
Full-sync applies settings, labels, and rulesets, by API.
Full-sync skips restricted repos, with no changes at all.
Full-sync writes a check-run report, if the App has checks write.
App has no checks write today, so that step fails with 403.
Code catches that failure, and the job still succeeds.

## Flow, dry run

Pull request to main starts dry run, with no paths filter.
Dry run uses the same steps, plus `FULL_SYNC_NOP=true`.
Dry run logs planned changes, and makes no live changes.
Dry run also loads config from main, not from the PR branch.
Only the deployment file comes from the PR checkout.
That limit makes dry run a main-config check, not a PR preview.
Use dry run to catch syntax and auth errors early.
Use live sync after merge to verify a real config change.

## Version pin design

Safe-settings version is defined in two workflow files.
Files: sync workflow and dry run workflow, both in `.github/workflows/`.
Definition: a checkout step, with repository and ref, by SHA.
SHA today: `a9a1f366ad6a738b55682d346d94f8d6c4893b09`, tag `3.0.0`.
Tag is a comment after the SHA, not the ref itself.
SHA pins are safer than moving tags, tags can move.
Both workflows must use the same SHA, always.
A version change must update both files, in the same pull request.
Renovate does that update, see below, in one PR.

## Renovate, safe-settings version bumps

Renovate config: `renovate.json5`, in the admin repo root.
Renovate schedule: before 3am on Monday, Chicago time.
Renovate groups GitHub Actions updates in one PR.
Renovate never automerges safe-settings, by package rule.
Safe-settings is not an Action, so github-actions manager ignores it.
Safe-settings needs a custom regex manager, in `renovate.json5`.
Regex manager targets both safe-settings workflow files.
Regex pattern uses a comment, right before the ref line.
Comment: `# renovate: datasource=github-tags depName=github-community-projects/safe-settings`.
Ref line: `ref: <SHA> # safe-settings <version>`.
Renovate reads version from the ref comment, digest from the SHA.
When a new stable tag appears, Renovate opens one PR.
That PR updates version and SHA, in both workflows.
Merge that PR only after a live sync check, never automerge.
Manual bump, if Renovate is off: change SHA and version, in both files.
Verify the SHA matches the tag commit, by API, before merge.

## Actions, also pinned

Workflows pin actions/checkout and actions/setup-node, by SHA.
Each pin has a version comment, for example `actions/checkout v4`.
Renovate github-actions manager updates those SHA pins.
PinDigests is true, so Renovate keeps SHA pins, not tags.
Node version is 22, set in the workflow, not by Renovate.

## Secrets and tokens, flow

App private key and client secret live only in admin repo Secrets.
App ID and client ID live only in admin repo Variables.
Workflows pass those values as env vars, to full-sync only.
Full-sync mints an installation token, per repo, at runtime.
Installation token reaches target repos, `GITHUB_TOKEN` does not.
No secret is printed in a log, and no secret is in a file.
Rotation: new key, new secret, old key revoked, in that order.

## Known limits, do not work around silently

Dry run loads main config, not PR config, see above.
Check-run report fails with 403, App has no checks write.
Private repos have no branch rulesets, free plan limit.
Schedules stop after 60 days with no repo activity.
Labels in the admin repo are not managed, admin is restricted.
Wiki flag off hides a wiki, it does not delete wiki content.
Branch protection removal needs manual API calls, revert does not remove it.
Ruleset import needs exact YAML, before rulesets can be enabled.

## Schema discovery, not full validation

Upstream safe-settings ships JSON schemas, in schema/dereferenced/.
Files are settings.json, suborgs.json, and repos.json.
Upstream builds them with npm run build:schema, for API 2026-03-10.
Upstream calls them an editor aid, not a runtime gate.
Full validation is not possible, for 5 reasons.
Schema uses key repositories, but our YAML uses repository.
Runtime accepts both keys, but schema only covers repositories.
Schema does not set additionalProperties to false, so typos pass silently.
Schema covers API fields, not safe-settings only keys like additive_plugins.
Schema covers security_and_analysis, but safe-settings ignores that field.
Schema validates one file, not merged org plus suborg plus repo layers.
Workflow schema-discovery.yml runs scripts/check-schema.py on every PR.
Script downloads pinned schema, with same SHA as safe-settings pin.
Script fails when a schema key is neither active nor commented.
That forces a decision on a new feature: use it, or comment why not.
Editor schema comments sit at top of each config file, for autocomplete.
Update those comments on a safe-settings bump, by hand, with the new SHA.
