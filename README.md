# infralicious .github

This is the special `.github` repo for the infralicious org.
GitHub treats a repo named `.github` as org-wide, not as a normal repo.
This repo holds org automation and defaults, not product code.
It holds no product code, no site code, and no app code.

## What this repo holds

- Safe-settings config, in `safe-settings/`.
- Community health files, in repo root and in `.github/`.
- Guards, in `scripts/check-config.py`, `docs/GUARDS.md`, and `.pre-commit-config.yaml`.
- Sponsor button, in `.github/FUNDING.yml`, GitHub Sponsors nitrocode.
- Org profile README, in `profile/README.md`.
- Safe-settings sync and dry run workflows, in `.github/workflows/`.
- Setup and architecture docs, in `docs/`.
- Renovate config, in `renovate.json5`.
- License, in `LICENSE`.
- Agent guide, in `AGENTS.md`.

## What this repo does

Safe-settings syncs repo settings for all managed org repos.
Sync sets repo flags, labels, alerts, and branch protection.
Sync runs every 4 hours, and on manual dispatch.
Sync uses a GitHub App, not a personal token.
Safe-settings is the only settings enforcer in this org.
Live settings edits in the UI will be reverted by the next sync.

## How to change it

Use a pull request, never push to main directly.
Dry run runs on every pull request to main, in NOP mode.
Dry run previews changes, and it makes no live changes.
Dry run limit: full-sync loads config from main, not from the PR.
Live sync after merge is the real verification for a config change.
Validation runs on every pull request, for YAML and Renovate config.
Merge only after dry run and validation pass, where they run.
Admin main protection requires the dry run check, by hand.

## Where to read more

- Safe-settings details: `safe-settings/README.md`.
- Setup from scratch: `docs/SETUP.md`.
- Architecture and limits: `docs/ARCHITECTURE.md`.
- Ruleset migration plan: `docs/RULESETS-MIGRATION.md`.
- Agent guide: `AGENTS.md`.

## Community health files, proliferated org-wide

CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, and SUPPORT live in repo root.
Issue templates and a pull request template live in `.github/`.
Profile README lives in `profile/README.md`, for the org profile page.
Files in a `.github` repo become defaults for org repos without their own files.
A repo file, if it exists, wins over an org default file.
No FUNDING file, this org does not use it.
No email address is published in these files, on purpose.
Contact form is the public contact, see `SECURITY.md` and `SUPPORT.md`.

## License

MIT, see `LICENSE`.
Copyright (c) 2026 Infralicious.
