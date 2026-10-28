# AGENTS.md

Guide for AI agents that work in this repo.
This repo is automation, not product code.
A bad change can revert live settings, or block merges.

## Repo purpose

This repo holds safe-settings config for infralicious.
Config lives in `safe-settings/`, not in target repos.
Workflows live in `.github/workflows/`.
Docs live in `docs/`, safe-settings details live in `safe-settings/README.md`.
Root README is a high level guide only, keep it concise.

## Hard rules

Never push to main directly, use a pull request.
Never commit a secret, a private key, or a client secret.
Never edit live repo settings in the GitHub UI, without a config change.
UI edits will be reverted by the next sync, by design.
Never merge without an explicit go-ahead, in the same exchange.
Never use `--no-verify`, if a hook fails, fix the hook issue.
All commits must be signed, with SSH signing.
Git identity: Ronak Bhatia, 7775707+nitrocode@users.noreply.github.com.

## Config rules

Safe-settings merges layers: repo wins, then suborg, then org.
Per-repo overrides live in the admin repo, in `safe-settings/repos/`.
Safe-settings never reads a target repo `.github/settings.yml`.
Baseline must not set identity fields, or it wipes repo identity.
Labels run in additive mode, custom UI labels stay.
Branch rules are gone, rulesets replace them, migrated 2026-10-27.
Rulesets live in suborgs for main, and in repos for tags.
No push rulesets, free plan rejects them.
Private repos have no branch rulesets, free plan returns 403.
Rulesets are Diffable, enabling them deletes unlisted rulesets.
Do not remove a ruleset from YAML without a live deletion plan.
See `docs/RULESETS-MIGRATION.md` for the migration plan.

## Workflows

Sync workflow runs on schedule, every 4 hours, plus manual dispatch.
Sync workflow does not run on push to main.
Dry run workflow runs on every pull request to main, in NOP mode.
Dry run sets `FULL_SYNC_NOP=true` and `LOG_LEVEL=info`.
Dry run limit: full-sync loads config from main, not from the PR.
A green dry run proves main config syncs cleanly, not PR config.
Live sync after merge is the real verification for a config change.
Validation workflow runs on every pull request, no secrets needed.
Validation parses YAML, parses Renovate config, and checks version pins.
Safe-settings version must match in both workflows, always.
Safe-settings version is a SHA pin, with a version comment.
Renovate updates that SHA, by a regex manager, never automerged.

## How to verify a change

Parse all YAML files, before a commit.
Parse `renovate.json5`, after comment strip, before a commit.
Test the safe-settings regex pattern, against both workflows.
Open a pull request, wait for dry run and validation.
Merge only after approval, then dispatch a live sync by hand.
Verify live settings by API, after every live sync.
Check rulesets, labels, and restricted repos.
Report the live result, with run IDs, not just a green check.

## Language

Use Simplified Technical English, for all outputs and artifacts.
Short sentences, max 20 words, active voice, one idea each.
No idioms, no slang, no complex words, no em dashes.
Use hyphens, or restructure a sentence, instead of em dashes.

## Guards, added 2026-10-27
- scripts/check-config.py is the single guard source, local and CI use the same script.
- Config Guard workflow runs guard and simulate on every PR to main.
- Simulate reads live rulesets, read only, and fails on missing required or protected deletion.
- Admin ruleset requires safeSettingsDryRun, validateConfig, configGuard, prConfigSimulation, live from 2026-10-27.
- Admin main bypass is pull_request, not always, direct pushes to admin main are blocked.
- Pre-commit is optional, CI is the gate, phone-first work cannot run pre-commit.
