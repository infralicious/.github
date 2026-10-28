# ADR-0002: Use rulesets, not legacy branch protection

Date: 2026-10-27
Status: Accepted

## Context

Legacy branch protection was per repo, and rulesets replaced it in GitHub.
Rulesets support branch and tag targets, with bypass actors, in one model.
Free plan allows rulesets for public repos, not for private repos.

## Decision

Use rulesets for all public repos, Protect main and Protect tags.
Use Tag protection for actions-checkout, and Default for terraform.
Delete legacy branch protection, after live sync verification.

## Consequences

Rulesets are Diffable, an unlisted ruleset is deleted on sync, by design.
Private repos get no rulesets, free plan returns 403, see ADR-0003 notes.
Admin repo ruleset is by hand, see ADR-0003.

## Alternatives

Legacy branch protection: old model, less tag support, rejected.
Org rulesets: Enterprise only, free plan cannot use them, rejected.
