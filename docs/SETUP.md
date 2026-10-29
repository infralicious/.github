# Setup, repeatable from scratch

This guide repeats the infralicious setup in a new org.
It assumes no safe-settings setup exists yet in that org.
It uses only free GitHub features, plus a GitHub App.
No server, no hosting, and no paid plan are needed.

## Step 1: Create the admin repo

Create a repo named `.github` in the org.
Make the repo public, so Action minutes stay free.
Set the default branch to `main`.
Copy this repo structure into the new admin repo.
Structure: workflows, `safe-settings/`, `docs/`, `README.md`.
Do not copy secrets, vars, or App IDs from another org.
Each org needs its own App, with its own keys.

## Step 2: Create the GitHub App

Create the App in the org, not in a personal account.
Use the GitHub web UI, Apps cannot be created by API alone.
Name the App clearly, for example `<org>-safe-settings`.
Set the App to private, not public.
Disable webhooks, no webhook URL and no events are needed.
Set these permissions, and no others unless a feature needs them.
Permissions: administration write, contents read, issues write.
Permissions: metadata read, pull_requests write.
Do not add checks write, unless you want check-run reports.
Check-run reports fail today, and sync still succeeds without them.
Save the App ID and the client ID from the App page.
Generate a private key, and download the `.pem` file once.
Generate a client secret, and copy it once.
Store both values only in GitHub Secrets, never in a file.
Delete the `.pem` file from disk after the secret is set.

## Step 3: Install the App

Install the App on all org repos, or on repos in scope.
Installation is a selection, not a workflow file in each repo.
No workflow file lands in a target repo.
Minutes bill to the admin repo, not to target repos.
Keep the install list in sync with the config scope.
A repo installed but not in config still gets the baseline.
A repo in config but not installed gets no sync at all.

## Step 4: Set vars and secrets

Set these vars in the admin repo, under Variables.
Vars: `SAFE_SETTINGS_GH_ORG`, `SAFE_SETTINGS_APP_ID`.
Vars: `SAFE_SETTINGS_GITHUB_CLIENT_ID`.
Set `SAFE_SETTINGS_GH_ORG` to the org login, in lower case.
Set these secrets in the admin repo, under Secrets.
Secrets: `SAFE_SETTINGS_PRIVATE_KEY`, `SAFE_SETTINGS_GITHUB_CLIENT_SECRET`.
Never commit a private key or a client secret.
Never paste a secret into chat, a file, or a log.

## Step 5: Protect the admin repo main branch, with a ruleset

Set a main ruleset by hand, not by safe-settings.
Safe-settings skips the admin repo, because it is restricted.
Ruleset id in infralicious: 26008879, name Protect main, active.
Block deletion and non-fast-forward, require a pull request.
Require checks: safeSettingsDryRun, validateConfig, configGuard, prConfigSimulation, securityDryRun, scriptTests.
Set required approvers to 0, for a sole maintainer.
Bypass: admin, bypass_mode pull_request, not always.
That blocks direct pushes, while PR merges still work.
Use pull requests for every config change.
CODEOWNERS gives notification only, it does not approve.

## Step 6: Test with a dry run pull request

Open a pull request from a branch, never push to main directly.
Change only a comment in `safe-settings/` to trigger a dry run.
Dry run workflow runs on every pull request to main.
Validation workflow runs on every pull request to main.
Dry run sets `FULL_SYNC_NOP=true` and `LOG_LEVEL=info`.
Dry run makes no live changes, it only previews.
Read the dry run log with care, see the limit below.
Dry run limit: full-sync loads config from main, not from the PR.
A green dry run proves main config syncs cleanly, not PR config.
Live sync after merge is the real test for a config change.

## Step 7: Run a live sync and verify

Merge the pull request, with squash, after review.
Dispatch the sync workflow by hand, from main, at once.
Do not wait for the scheduled run, it runs unattended.
Read the sync run log, and check for success.
Expect a check-run 403 error in the log, if checks write is missing.
That error is caught, and the job still succeeds.
Verify live settings for every non-restricted repo, by API.
Check wiki, delete on merge, labels, topics, and rulesets.
Check that restricted repos are unchanged, by API.
Restricted repos today are `.github`, `admin`, `safe-settings`, `docs`.

## Step 8: Connect Renovate

Add `renovate.json5` to the admin repo, if it is not there yet.
Verify Renovate is installed on the admin repo, in org settings.
A config file alone does nothing, if the App is not installed there.
Renovate runs before 3am on Monday, Chicago time.
Renovate groups GitHub Actions updates in one PR.
Renovate updates safe-settings in its own PR, never automerged.
Merge a safe-settings Renovate PR only after a live sync check.
See `docs/ARCHITECTURE.md` for the version pin design.
See `docs/RULESETS-MIGRATION.md` for the ruleset plan.

## Step 9: Keep it running

Check scheduled sync runs each month.
GitHub disables schedules after 60 days with no repo activity.
Workflow runs do not count as activity, for that rule.
Re-enable the workflow if GitHub disables it.
Manual dispatch still works, even after a schedule stops.
Review config changes by pull request, every time.
Never edit live settings in the UI, without a config change.
UI edits will be reverted by the next sync, by design.

## Step 10: Disaster recovery, read before you need it

See docs/DISASTER-RECOVERY.md, for admin repo loss, App loss, key loss, ruleset loss, and bad config.
No secrets live in this repo, so recovery never needs a secret from a file.

## Step 11: New org checklist, replace these values

Replace org login, App name, App ID, client ID, and all secrets.
Replace public repo list, private repo list, and restricted repo list.
Replace ruleset names, if the new org uses different names.
Replace sponsor account, in .github/FUNDING.yml, if the new org uses a different account.
Run scripts/check-config.py guard and simulate, before the first live sync.
