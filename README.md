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
It sets `FULL_SYNC_NOP=true`.
It previews changes, and it makes no changes.
Require a green dry run before a merge.
Use branches in this repo for pull requests.
Fork pull requests get no secrets, so the dry run fails for forks.

## Supply chain pins

The workflows pin safe-settings to a full SHA.
That SHA is `ff7a65655d33006b9820479df0a9e1057a8927e4`.
That SHA matches tag `2.1.17` in both safe-settings repos.
The tag exists in `github/safe-settings` and in `github-community-projects/safe-settings`.
The workflows check out the community repo.
The workflows pin actions to full SHAs, with version comments.
Renovate should update those SHAs.
The workflows pin Node to version 22.
The workflows use `npm ci`, not `npm install`.
The safe-settings repo has a lockfile, so `npm ci` works.

## Secrets and vars

Create a GitHub App under the infralicious org.
Install the App only on repos in scope.
Set `GH_ORG` to `infralicious`.
Set `APP_ID` and `GITHUB_CLIENT_ID` as vars.
Set `PRIVATE_KEY` and `GITHUB_CLIENT_SECRET` as secrets.
Never commit a private key.
Never commit a client secret.

## Admin repo protection, by hand

Safe-settings does not manage this repo.
Restricted repos include `.github`, so sync skips it.
Set main protection for this repo by hand.
Block force pushes and branch deletion.
Require the dry run check.
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

Phase 1 covers two repos: `infralicious.github.io` and `actions-checkout`.
The public suborg lists those two repos only.
Branches apply only when the App is installed on a repo.
Install the App on a public repo to add it to scope.
Add that repo to the public suborg at the same time.
Run a dry run before a live sync for that repo.
Phase 2 changes wiki and branch deletion for three public repos.
Those repos now have wiki on and deletion off.
Approve those changes before you expand scope.
Private scope covers `service-control-policies` only.
Test the private suborg in a dry run first.
Private branch rules stay out, even after that test.

## Retire the probot Settings app

Create the App, and install it on phase 1 repos only.
Add vars and secrets to this repo.
Run a dry run, and check the preview.
Run a live sync, and verify both repos.
Uninstall the probot Settings app.
Delete the old per-repo `.github/settings.yml` files.
Delete those files only after a live sync verifies.
