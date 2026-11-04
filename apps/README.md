# GitHub App manifests

This folder holds one manifest file per GitHub App.
Each manifest has no secret, no private key, and no client secret.
Do not put a secret in any manifest file.
This README is the dedicated guide for these manifests.

## What a manifest is

A manifest is creation input for a new GitHub App.
It sets name, homepage, description, permissions, and events at creation.
It sets redirect URL for the creation flow.
It is a record for recreation, if an App must be rebuilt.
It is not a live sync file for an existing App.

## What a manifest is not

A manifest change does not update a live App.
GitHub has no API endpoint to update an existing App.
GitHub has no API endpoint to change App permissions.
GitHub has no API endpoint to create a private key.
The manifest flow creates a new App only.
It does not update an App that already exists.

## Why auto-update is not possible

The Apps REST API manages installations, not App registration.
It can get an App, get an App by slug, and create an App from a manifest.
It can list installations, create tokens, suspend installs, and add repos.
It can update webhook config only, with PATCH /app/hook/config.
That endpoint changes webhook config only, not permissions.
App metadata changes are web UI only, by App owner.
A permission change in UI is only a request at first.
Each install must accept new permissions before they take effect.
A private key change is also web UI only.
No script can apply a manifest change to a live App.
Drift check can only report drift, it cannot fix drift.

## How to update a live App

First, decide which side is correct, manifest or live App.
If the manifest is correct, fix the live App in UI.
Open org settings, then Apps, then the App page.
Edit permissions on the App permissions page.
Save the change, then accept new permissions on the install page.
Re-run drift check, and confirm a pass.
If the live App is correct, fix the manifest in a pull request.
Update the manifest file, run lint, and run drift check.
Drift check passes only after live and manifest match.
If name or homepage must change, use UI, not a new App.
Recreate an App only if UI change is not possible.
Recreation gives a new App ID and a new private key.
Recreation needs new vars, new secrets, and a new install.
Recreation also needs old App uninstall, after new App works.

## Drift check

Drift check compares live Apps to these manifests.
It checks permissions and events only.
It does not check name, URL, description, or webhook settings.
It never changes a live App, it only reports drift.
It fails when live permissions differ from a manifest.
It runs on every pull request to main.
It runs on business days, Monday to Friday at 09:00 UTC.
It runs on manual dispatch, at any time.
CI uses JWT-all mode, for every manifest in this folder.
JWT-all mode discovers new manifests automatically.
JWT-all mode uses one private key per App, by naming convention.
Naming convention derives env names from App slug.
Example: infralicious-safe-settings uses SAFE_SETTINGS_APP_ID and SAFE_SETTINGS_PRIVATE_KEY.
Example: infralicious-zizmor uses ZIZMOR_APP_ID and ZIZMOR_PRIVATE_KEY.
Secrets are not enumerable in CI, so workflow must pass each key explicitly.
Workflow env lists safe-settings and zizmor keys today.
A new App is discovered automatically, but drift skips it until its key is wired.
Skip is not a fail, but skip list is visible in run summary.
Add a new App key to app-drift workflow, to enable its drift check.
Do not duplicate a key across repos, unless that key is already in admin repo.
Renovate key is not in admin repo, so admin CI skips renovate.
Renovate-config repo checks renovate, with its own key.
Local app mode can check every App, with a user token.
Local app mode needs GITHUB_TOKEN, and it reads Apps by slug.
GITHUB_TOKEN cannot read private Apps in CI, it returns 403.
JWT mode uses openssl, which is present on Ubuntu runners.
Drift check never prints a token, a key, a JWT, or a secret.

## Inventory

Inventory file is apps/inventory.json, one entry per installed App.
Inventory covers org installations only, not repo-only installs.
Repo-only installs need App JWT to list, and third-party keys are not here.
Inventory codifies every App installed on the org account.
Inventory codifies scope, so scope is visible in code, not only in UI.
Scope org means all repos, with repository_selection all.
Scope selected means listed repos, with repository_selection selected.
Scope repo means one repo, with repository_selection selected and one repo listed.
Today, all six Apps use scope org, with all repos.
Inventory permissions are granted installation permissions, not requested App permissions.
Socket install grants no emails read, but App page lists emails read.
Inventory records granted permissions only, for socket, to match live install.
For owned Apps, inventory permissions must match manifest permissions.
For third-party Apps, inventory permissions are live granted permissions at codification time.
Inventory check script is scripts/check-app-inventory.py, with no dependency.
Inventory check runs locally with GITHUB_TOKEN, org owner token.
Inventory check runs in CI, in app-inventory workflow, on pull request and dispatch.
Inventory check runs in CI, on business days, Monday to Friday at 09:00 UTC.
Inventory check is advisory, not a required check, like appDrift.
Inventory check fails on unknown App, missing App, scope mismatch, or permission mismatch.
Inventory check fails on event mismatch, and on manifest mismatch for owned Apps.
Inventory check warns on installation_id mismatch, reinstall may explain it.
Inventory check skips, it does not fail, when token cannot list installations.
Workflow token in CI may return 403, local run with org owner token is authoritative.
Safe-settings sync does not revert App installs, so inventory check is needed.
App installs persist until a human uninstalls them in UI.
A new App install will not be reverted by sync, so it must be flagged by inventory check.
To flag a new App, run inventory check locally, with org owner token.
Review new App purpose, scope, permissions, and events, before codifying it.
Add new App to inventory in a pull request, with purpose and scope.
Do not auto-add a new App to inventory, human review must come first.
Inventory tests are in scripts/check-app-inventory.test.py.

## Lint

GitHub has no official manifest linter, so this repo has its own linter.
Linter script is scripts/check-manifests.py, with no dependency and no network.
Linter runs on every pull request, in script-tests workflow.
Linter runs locally with python3 scripts/check-manifests.py.
Linter fails on ERROR, and passes on WARN by default.
ERROR rules cover JSON, name, URL, redirect, public, permissions, events, and hook.
Name must match infralicious prefix, with lowercase letters, digits, and hyphens.
URL must start with https://github.com/infralicious/.
Redirect URL must equal URL, to avoid external redirect.
Public must be false, Apps in this org are private.
Permissions must be known names, with read or write values only.
Events must be a list, and events need a webhook URL.
Hook attributes without a URL is an ERROR, GitHub rejects it.
Hook attributes with a URL is a WARN, prefer omit for Action Apps.
Write permissions are WARN, not ERROR, because some Apps need write.
Administration write and workflows write are WARN, review them.
Metadata read missing is WARN, add it.
File name must match manifest name, or linter fails.
Linter tests are in scripts/check-manifests.test.py.

## Add a new App

Copy an existing manifest file, and change only needed fields.
Change name, URL, description, permissions, and events as needed.
Run linter locally, and fix every ERROR before a pull request.
Submit the manifest in GitHub App creation flow.
Use an org owner account, and keep the App private.
Install the App on all org repos, after creation, if that scope fits.
Set admin vars, with naming convention, after creation.
Set admin secret for private key, by secure entry only.
Add App ID var and private key secret to app-drift workflow.
Add App to inventory, with scope, permissions, events, and purpose, in the same pull request.
Update this README, with new App notes, in the same pull request.
Do not copy App IDs, keys, or secrets from another App.
Do not put a secret in chat, in a file, or in memory.

## Remove an App

Delete the manifest file, in a pull request.
Remove App from inventory, in the same pull request.
Remove App vars and secrets from admin repo settings.
Uninstall the App from the org, after its workflows stop using it.
Remove drift workflow env for that App, in the same pull request.
Update this README, with removal notes, in the same pull request.

## Current Apps

All six installed Apps exist today, and all are installed org-wide.
All six Apps use all repos, current and future org repos.
Three Apps are owned by infralicious, with manifests in this folder.
Three Apps are third-party, with inventory entries only, no manifests here.
Third-party Apps have no manifest in this folder, because vendor owns them.
All three owned manifests match live permissions and events, as of 2026-11-03 manual check.
All six inventory entries match live installations, as of 2026-11-03 manual check.

- infralicious-safe-settings: administration write, contents read, issues write, metadata read, pull_requests write.
- infralicious-renovate: contents write, issues write, metadata read, pull_requests write, vulnerability_alerts read, workflows write.
- infralicious-zizmor: contents read, metadata read, security_events write.
- semantic-pull-requests: metadata read, pull_requests write, single_file read, statuses write, org-wide.
- socket-security: checks write, contents write, issues read, members read, merge_queues read, metadata read, pull_requests write, org-wide.
- coderabbitai: actions read, checks write, contents write, discussions read, issues write, members read, merge_queues read, metadata read, pull_requests write, statuses write, workflows write, org-wide.
- infralicious-zizmor: App ID 5597126, install is org-wide, var and secret exist in admin repo.
- infralicious-zizmor: workflow uses client-id, not app-id, for the token step.
- infralicious-zizmor: manifest omits hook_attributes, so webhook stays inactive by omission.
- infralicious-safe-settings and infralicious-renovate: manifests now omit hook_attributes, like zizmor.
- Renovate manifest uses vulnerability_alerts read.
- GitHub UI shows that permission as Dependabot alerts.
- The API key and the UI label name the same permission.

## Security notes

Never put a private key in chat, in a file, or in memory.
Never put a client secret in chat, in a file, or in memory.
Never put a webhook secret in chat, in a file, or in memory.
Manifest files hold public App settings only, no secrets.
