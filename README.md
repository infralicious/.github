# infralicious .github

This is the special `.github` repo for the infralicious org.
GitHub treats a repo named `.github` as org-wide, not as a normal repo.
This repo holds org automation and defaults, not product code.
It holds no product code, no site code, and no app code.

## What this repo holds

- Safe-settings config, in `safe-settings/`.
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

## What this repo does not hold, on purpose

No org-wide community health files, like CONTRIBUTING or SECURITY.
Those files in a `.github` repo become defaults for all org repos.
That effect is too broad for this automation repo, today.
No issue or pull request templates, for the same reason.
No FUNDING file, this org does not use it.
Add a community health file only with an org-wide decision, first.

## License

MIT, see `LICENSE`.
Copyright (c) 2026 Infralicious.
