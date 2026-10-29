# ADR-0012: Managed ruleset hardening and repository field locking

Date: 2026-10-29
Status: Accepted

## Context

Protect main had only deletion and non_fast_forward rules.
Protect main bypass was admin always, so admin could direct push main.
Tag rulesets for five repos also had bypass admin always.
Actions-checkout Tag protection already had bypass empty, so tag rulesets were inconsistent.
Baseline had has_projects true, but classic Projects API returns 404, and no projects exist.
Fields not in YAML are unmanaged, so UI drift would persist for those fields.
Required checks are per repo only, a shared required check would block repos with no workflows.

## Decision

Protect main bypass changes from always to pull_request, for branch rulesets.
Protect main gains a pull_request rule, with count 0 and merge methods squash only.
Tag rulesets for site, awesome, saas, renovate-config, and terraform gain bypass empty.
Actions-checkout Tag protection and terraform Default already had bypass empty, and stay unchanged.
Baseline locks has_projects false, has_pull_requests true, and allow_update_branch true.
Baseline locks squash_merge_commit_title PR_TITLE and squash_merge_commit_message PR_BODY.
Baseline gains a security label, and repo files lock live topics for awesome and terraform.
Private service-control-policies locks allow_forking false, public repos keep forking on.
Guard fails if a repo file weakens baseline, or if Protect main bypass or merge methods drift.
Required checks are deferred, they need a suborg split or a tested repo override.
Verified job names for a follow-up are test for actions-checkout and htmlproofer for site.
Awesome Link check job name is not verified live, so it is not added yet.

## Consequences

Admin can merge via PR, but cannot direct push main, which blocks accidental pushes.
Tag deletion and update are blocked even for admin, tag creation still works.
Squash history uses PR title and PR body, not a list of commit messages.
A repo file cannot weaken baseline without failing guard in CI, before merge.
Required checks remain absent, so a PR can still merge with failing tests, until the follow-up.
A follow-up must test per-repo required checks, or it can block PRs for repos with no workflows.

## Rejected alternatives

Bypass pull_request for tag rulesets: rejected, tag pushes are not PRs, so empty bypass is clearer.
Bypass always for all rulesets: rejected, it defeats protection for the sole maintainer.
Required checks in the shared Protect main ruleset: rejected, saas and terraform have no workflows.
Repo-level Protect main overrides for required checks: rejected for now, merge behaviour is untested.
Overridevalidators for weakening checks: rejected, guard runs pre-merge and is cheaper.
Teams, environments, variables, and custom properties: rejected for now, no need exists for seven repos.
