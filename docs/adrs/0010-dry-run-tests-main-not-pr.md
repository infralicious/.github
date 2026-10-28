# ADR-0010: Dry run tests main, not PR, so simulate script is required

Date: 2026-10-27
Status: Accepted

## Context

Safe-settings Action mode loads config by API, from main, not from PR.
A green dry run proves main syncs cleanly, it does not preview PR changes.
A PR config error would only appear on live sync, after merge, too late.

## Decision

Keep dry run workflow, for main config, as a first check.
Add simulate script, scripts/check-config.py simulate, on every PR.
Simulate merges PR rulesets locally, reads live rulesets, reports create, update, delete.
Simulate fails on missing required ruleset, and on protected ruleset deletion.

## Consequences

PR config errors are caught before merge, for rulesets, not for all fields.
Live sync after merge is still the real test, for all config changes.
Simulate is read only, no secrets, no live change, safe for PRs.

## Alternatives

Trust dry run alone: false confidence, PR errors slip to live, rejected.
Fork safe-settings to fix dry run: high maintenance, rejected.
No PR check: live sync is the only check, too late, rejected.
