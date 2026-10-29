# ADR-0015: Required PR checks must catch breaking changes

Date: 2026-10-29
Status: Accepted

## Context

PR 26 allow_forking bug passed all PR checks, then broke live sync with 422.
Dry run tests main config, not PR config, see ADR-0010, so dry run cannot catch a PR change.
Guard at that time checked only a subset of fields, so allow_forking for a private repo slipped through.
A breaking change in this repo is any change that fails live sync, weakens protection, or blocks PRs.
Examples are a wrong required check context, a bypass change to always, a security alert change to false, or a ruleset parameter change.

## Decision

Guard must check full parameters for all rulesets and all baseline fields, not a subset.
Baseline lock covers has_issues, merge methods, delete_branch_on_merge, web_commit_signoff, is_template, and security alerts and auto-fix.
Protect main check covers target, enforcement, bypass, conditions, rule types, and full pull_request parameters.
Tag ruleset check covers target, enforcement, bypass empty, rule types, and conditions.
Default ruleset check covers target, enforcement, bypass empty, rule types, and merge methods.
Repo files must set only identity fields, name, description, homepage, private, topics.
Any new config field must ship with a guard check in the same PR, or the PR must not merge.
If a guard check is missing for a field, that field is unmanaged for breaking changes, and the PR is incomplete.

## Consequences

PRs that weaken config fail CI before merge, not after merge in live sync.
Future config changes need a guard update in the same PR, which adds work but prevents silent breaks.
Dry run remains a main-config check only, guard and simulate are the pre-merge checks for PR config.
Live sync after merge remains the real verification, but it should now succeed on the first run.
A guard check that is too strict can block a legitimate change, then the guard update must explain the new reason in the PR.

## Rejected alternatives

Rely on dry run alone: rejected, dry run tests main, not PR, see ADR-0010.
Rely on live sync after merge: rejected, main is already broken, and sync failure opens an issue.
Rely on manual review alone: rejected, sole maintainer reviews own PRs, automated check is stronger.
Rely on a test repo sync: rejected for now, no test repo exists, and a test repo sync would still need API validation.
