# GitHub App manifests

This folder holds one manifest file per GitHub App.
Each manifest is the source of truth for App permissions.
Each manifest has no secret, no private key, and no client secret.
Do not put a secret in any manifest file.

## What the drift check does

The drift check compares live Apps to these manifests.
It checks permissions and events only.
It does not check name, URL, description, or webhook settings.
It runs on every pull request to main.
It runs weekly, on Monday at 09:00 UTC.
It runs on manual dispatch, at any time.
It never changes a live App, it only reports drift.
It fails when live permissions differ from a manifest.

## Run the check locally

Run this command from the repo root.
`GITHUB_TOKEN=<token> python3 scripts/check-apps.py`
Both Apps are private, so the check needs a token.
Use a user token locally, and never commit that token.
CI sets GITHUB_TOKEN for the workflow run.

## Fix drift, in this order

First, decide which side is correct.
If the manifest is correct, fix the live App.
Edit permissions in the App settings page.
Approve the new permissions on the App install.
Re-run the check, and confirm a pass.
If the live App is correct, fix the manifest.
Update the manifest file in a pull request.
The check passes only after live and manifest match.

## Create a new App from a manifest

GitHub has no API to update an existing App from a manifest.
A manifest creates a new App, with a new ID and a new key.
Copy a manifest file, change only the name and the URL.
Submit the manifest in the GitHub App creation flow.
Install the new App, then update App ID and secrets.
Do not copy App IDs, keys, or secrets from another App.

## Notes for each App

- infralicious-safe-settings: permissions match the live App today.
- infralicious-renovate: permissions match the live App today.
- Renovate manifest uses vulnerability_alerts read.
- GitHub UI shows that permission as Dependabot alerts.
- The API key and the UI label name the same permission.
