# Safe-settings admin repo for infralicious

This repo holds the safe-settings config for the infralicious org.
It does not hold app code.
It holds repo settings as code only.

## How the config fits together

Safe-settings merges three layers for each repo.
Repo files win on a conflict.
Suborg files sit between repo files and org files.
Org files set the baseline for all managed repos.

The org baseline lives in `safe-settings/settings.yml`.
It sets repo settings and labels only.
It sets no branch rules.
It sets no identity fields.
Identity fields live in `safe-settings/repos/*.yml`.
That split stops the baseline from wiping a repo identity.

Public branch rules live in `safe-settings/suborgs/public.yml`.
Private repos live in `safe-settings/suborgs/private.yml`.
The private suborg has no branch rules.
Branch protection fails on private repos on the free plan.
The API returns 403 for that case.
A suborg file cannot strip a rule set at the org level.
That fact forced branch rules out of the org baseline.

## What syncs, and what does not sync

The sync covers repo settings, branch rules for public repos, and labels.
It does not cover teams, collaborators, or environments.
It does not cover Actions permissions.
It does not cover immutable releases.
It does not cover tag rulesets yet.
Actions-checkout needs those steps by hand.
Immutable releases are already on for actions-checkout.
Safe-settings does not manage that switch.
Keep that switch on by hand.

Docs stays out of the sync.
Docs is an old repo.
Leave docs alone.
`safe-settings/deployment-settings.yml` lists docs as restricted.

## Workflows

The sync workflow runs on a schedule.
It runs every 4 hours.
It also runs on manual dispatch.
It does not run on a push to main.
That choice stops a direct push from syncing at once.
Use a pull request for config changes.

The dry run workflow runs on pull requests.
It runs only for changes under `safe-settings/`.
It sets `FULL_SYNC_NOP=true` and `LOG_LEVEL=info`.
It previews changes, and it makes no changes.
The info log shows the planned change summary.
Debug log level would also show full diffs for private repos.
Do not use debug in this public repo.
Require a green dry run before a merge.
Use branches in this repo for pull requests.
Fork pull requests get no secrets, so the dry run fails for forks.

## Supply chain pins

The workflows pin safe-settings to a full SHA.
That SHA is `a9a1f366ad6a738b55682d346d94f8d6c4893b09`.
That SHA matches tag `3.0.0` in both safe-settings repos. Version 2.1.17 failed dry runs with a NOP reporting crash, fixed in 3.0.0.
The tag exists in `github/safe-settings` and in `github-community-projects/safe-settings`.
The workflows check out the community repo.
The workflows pin actions to full SHAs, with version comments.
Renovate should update those SHAs.
The workflows pin Node to version 22.
The workflows use `npm ci`, not `npm install`.
The safe-settings repo has a lockfile, so `npm ci` works.

## Secrets and vars

Create a GitHub App under the infralicious org.
Install the App on all org repos, as decided 2026-10-27.
Set `GH_ORG` to `infralicious`.
Set `APP_ID` and `GITHUB_CLIENT_ID` as vars.
Set `PRIVATE_KEY` and `GITHUB_CLIENT_SECRET` as secrets.
Never commit a private key.
Never commit a client secret.

## Admin repo protection, by hand

Safe-settings does not manage this repo.
Restricted repos include `.github`, so sync skips it.
Set main protection for this repo by hand, before a merge.
Block force pushes and branch deletion.
Require the dry run check, named Safe Settings Dry Run.
That check does not need a human approver.
Admin protection is still unset as of 2026-10-27.
Use pull requests for config changes.
Do not set a required approver count.
The sole maintainer cannot approve their own pull request.
That count would stall every merge.
`CODEOWNERS` gives notification only.
It does not approve a pull request.

## Schedule reliability

GitHub disables scheduled workflows after 60 days with no activity.
Workflow runs do not count as activity.
Check workflow runs each month.
Re-enable the workflow when GitHub disables it.
Manual dispatch still works after a schedule stops.
A config change still syncs on manual dispatch.

## Scope and expansion

Baseline applies to all installed repos, as decided 2026-10-27.
Baseline covers repo settings, labels, and Dependabot alerts.
Branch rules cover only `infralicious.github.io` and `actions-checkout`.
The public suborg lists those two repos only.
Other public repos get baseline only, with no branch rules yet.
Add a repo to the public suborg to add branch rules for it.
Run a dry run before a live sync for that repo.
Live sync changes wiki off and deletion on for three public repos.
Those repos are awesome-service-control-policies, saas-auth-wall-of-shame, and renovate-config.
Live sync also changes deletion on for service-control-policies.
Private scope covers `service-control-policies` only.
Private branch rules stay out, even after that test.

## Renovate and Dependabot

Renovate is the primary updater where it runs.
Renovate dashboards exist for actions-checkout, infralicious.github.io, and terraform-aws-securityhub-batchupdatefindings.
Dependabot alerts are on in the baseline.
Dependabot auto-fix is off in the baseline.
Auto-fix off stops duplicate pull requests with Renovate.
Repos without Renovate need a manual fix for an alert.
Most non-Renovate repos hold markdown only, so alert volume should stay low.
Shared Renovate config in renovate-config does not apply to target repos.
Target repos extend best-practices only, or use no Renovate config.
Do not enable auto-fix globally to fix the non-Renovate gap.
That change would duplicate Renovate pull requests in Renovate repos.

## Retire the probot Settings app

Create the App, and install it on all org repos.
Add vars and secrets to this repo.
Run a dry run, and check the preview.
Uninstall the probot Settings app before live sync.
Probot could revert safe-settings changes on a target repo push.
Run a live sync, and verify all non-restricted repos.
Delete the old per-repo `.github/settings.yml` files.
Delete those files only after a live sync verifies.
