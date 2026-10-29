# ADR-0014: Actions-checkout required check via dedicated suborg

Date: 2026-10-29
Status: Accepted

## Context

Protect main had no required checks, so a PR could merge with failing tests.
Actions-checkout has a Test workflow, job test, which runs on pull_request.
Site has a Check links workflow, job htmlproofer, which also runs on pull_request.
Saas and terraform have no workflows, so a shared required check would block them.
A repo-level Protect main override with the same name may conflict with the suborg ruleset.
Safe-settings ruleset merging for a same-name override is untested in this org.

## Decision

Split actions-checkout out of public.yml into public-actions-checkout.yml.
Public.yml now holds five repos without required checks.
Public-actions-checkout.yml holds actions-checkout only, with Protect main plus required check test.
Required check context is test, integration_id 15368 for GitHub Actions.
Strict policy is false, a PR does not need to be up to date with main before merge.
Protect main in the new file copies public.yml exactly, except for the required check.
Guard checks the union of public and checked suborgs equals all six public repos.
Guard checks the required check context, integration, and strict policy exactly.
Simulate now reads all suborg files, not just public.yml, for merged rulesets.
Site htmlproofer check is a separate follow-up, as its own dedicated suborg, later.
Awesome Link check is not added yet, its job name is not verified live.

## Consequences

Actions-checkout PRs cannot merge until test passes, unless admin bypasses via PR.
Bypass via PR is explicit, not automatic, and is logged by GitHub.
Other public repos are unchanged, they keep Protect main without required checks.
A future site suborg follows the same pattern, one file per check set.
If Test workflow job name changes, guard and YAML must change together, or PRs will block.
After merge, a dummy PR to actions-checkout must prove test is required and passes.

## Rejected alternatives

Shared required check in public.yml: rejected, it would block saas and terraform.
Repo-level Protect main override: rejected for now, same-name merge is untested.
Required checks for all repos at once: rejected, one repo at a time proves the pattern.
Strict policy true: rejected, it adds update-branch friction for a sole maintainer.
Scorecard as a required check too: rejected for now, test alone is the minimal quality gate.
