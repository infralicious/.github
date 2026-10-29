# Disaster recovery

This doc covers loss, not daily changes.
Daily changes go by pull request, see docs/SETUP.md.
No secrets live in this repo, so recovery never needs a secret from a file.

## Admin repo deleted

Recreate a repo named `.github`, public, branch main.
Copy this repo structure from a local clone, or from a fork.
Re-set vars and secrets, see docs/SETUP.md step 4.
Re-create the admin ruleset by API, see docs/RULESETS-MIGRATION.md.
Re-run a live sync, and verify live, see docs/SETUP.md step 7.
Target repos keep their last synced settings, until the next sync.
No settings are lost, if the admin repo is deleted, they stay live.

## App private key lost or leaked

Generate a new private key, in the App settings page.
Update secret `SAFE_SETTINGS_PRIVATE_KEY`, in the admin repo.
Delete the old private key, in the App settings page, after the new key works.
Test with a dry run pull request, then a live sync.
Do not commit the new key, delete the `.pem` file after the secret is set.

## App client secret lost or leaked

Generate a new client secret, in the App settings page.
Update secret `SAFE_SETTINGS_GITHUB_CLIENT_SECRET`, in the admin repo.
Old secret stops working at once, when a new one is generated.
Test with a dry run pull request, then a live sync.

## App deleted

Create a new App, see docs/app-manifest.json for permissions.
Install the new App on all org repos, in scope.
Update vars `SAFE_SETTINGS_APP_ID` and `SAFE_SETTINGS_GITHUB_CLIENT_ID`.
Update secrets, with the new private key and client secret.
Re-run a live sync, and verify live.
Old rulesets and settings stay live, until the next sync changes them.

## Admin ruleset deleted by accident

Recreate it by API, with the same name, target, and rules.
Name: Protect main, target branch, enforcement active.
Conditions: refs/heads/main only.
Rules: deletion, non_fast_forward, pull_request, required_status_checks.
Pull request: count 0, dismiss stale false, code owner false.
Pull request: last push false, thread resolution false.
Required checks: safeSettingsDryRun, validateConfig, configGuard, prConfigSimulation, securityDryRun, scriptTests, schemaDiscovery.
Integration for all checks: 15368, GitHub Actions.
Bypass: RepositoryRole admin, bypass_mode pull_request.
Verify by API, after creation, and check that legacy protection is absent.

## Bad config merged and synced

Revert the bad pull request, by a new pull request, not by a force push.
Merge the revert, then dispatch a live sync by hand, at once.
Verify live, by API, for every affected repo.
Rulesets deleted by a bad sync must be recreated from YAML, by the next sync.
If a ruleset deletion was intentional, do not revert it, confirm it in the PR body.
Scheduled sync will retry the bad config, if main is not fixed, fix main first.

## Schedule disabled after 60 days

GitHub disables schedules after 60 days with no repo activity.
Workflow runs do not count as activity, for that rule.
Check the sync workflow state, in the admin repo Actions tab.
Re-enable the workflow, if GitHub disabled it.
Manual dispatch still works, even after a schedule stops.
A merge, an issue, or a comment counts as activity, a run does not.

## New org, repeat from scratch

Use docs/SETUP.md, with a new App, new vars, and new secrets.
Copy docs/app-manifest.json, change only the name and the URL.
Do not copy App IDs, keys, or secrets from another org.
Replace the org login, the repo lists, and the restricted list, for the new org.
Run the guard script, before the first live sync, in the new org.
First live sync in a new org should be a dry run first, then live, then verify.
