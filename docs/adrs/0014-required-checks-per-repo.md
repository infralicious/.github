# ADR-0014: Required checks per repo, in separate rulesets

Date: 2026-10-29
Status: Accepted
Supersedes: ADR-0012, required checks part only

## Context

ADR-0012 deferred required checks.
A PR could still merge with failing tests, until the follow-up.
Renovate PR 10 in infralicious.github.io proved that gap.
PR 10 changed ruby 3.3 to 4.0, and htmlproofer failed on Ruby 4.0.
PR 10 stayed mergeable, because no check was required.
Protect main has no required_status_checks rule today.
Site PRs run link-check on pull_request, job htmlproofer.
Action PRs run test on pull_request, job test.
Saas and terraform have no workflows, so a shared check would block them.
Private repos cannot use rulesets on the free plan.

## Decision

Add a separate branch ruleset per repo, not a Protect main override.
Site gets ruleset Require site checks, with context htmlproofer.
Actions-checkout gets ruleset Require action checks, with context test.
Both rulesets target refs/heads/main, enforcement active.
Both rulesets use bypass admin pull_request, like Protect main.
Both rulesets use integration 15368, for GitHub Actions.
Both rulesets use strict false, so a PR need not be up to date first.
ADR-0012 is not edited in place, this record supersedes its required checks part only.
All other ADR-0012 decisions stay in force.

## Consequences

A failing htmlproofer check now blocks a site PR merge.
A failing test check now blocks an actions-checkout PR merge.
Admin can still bypass on a PR, but only by an explicit bypass, not by accident.
Saas, terraform, awesome, and renovate-config gain no required check.
A repo with no workflow still merges, because no check is required there.
Live sync after merge is the real test, dry run cannot preview rulesets.

## Rejected alternatives

Required checks in shared Protect main: rejected, saas and terraform have no workflows.
Repo-level Protect main override: rejected, merge behaviour is untested, per ADR-0012.
Strict true: rejected, it would force an update branch before merge, for every PR.
Bypass empty: rejected, it would block an admin fix for a flaky check, with no escape.
Bypass always: rejected, it defeats protection for the sole maintainer.
