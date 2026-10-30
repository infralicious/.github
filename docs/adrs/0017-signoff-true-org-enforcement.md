# ADR-0017: Baseline signoff true, to match org enforcement

Date: 2026-10-30
Status: Accepted

## Context

Org web_commit_signoff_required is true, verified by API on 2026-10-30.
Live repos already show signoff true, for terraform and actions-checkout.
Baseline set signoff false, from the original baseline, before org enforcement.
Live sync run 41035007238 failed, on 2026-10-30, for all managed repos.
PATCH each repo returned 422, with message commit signoff is enforced by the organization and cannot be disabled.
Previous sync on 2026-10-29 succeeded with baseline false, so org setting changed between 2026-10-29 and 2026-10-30.
PR 29 did not change signoff, so PR 29 did not cause the failure.
Site Protect main still updated live, with htmlproofer, because ruleset plugin runs separately from repository plugin.

## Decision

Change baseline web_commit_signoff_required from false to true.
Update guard to require true, in the same PR, see ADR-0015.
Add new repo coderabbit to public suborg, in the same PR, because simulate fails otherwise.
Coderabbit is a public CodeRabbit config repo, created 2026-10-30, no workflows, no required checks.
Public suborg gives it Protect main, repo file gives it Protect tags, to match other public repos.
Coderabbit repo file sets only name and private false, no description, homepage, or topics, live values stay unchanged.
Do not set false again, unless org signoff is disabled first, in the UI, then change baseline in the same change.
After merge, dispatch a live sync by hand, verify success, and close sync-health issue 30.

## Consequences

Sync can succeed again, for repository fields, for all managed repos.
Web UI commits will require signoff, by org policy, not by this PR alone.
Local git pushes are unchanged, web signoff applies to web UI commits only.
If org signoff is disabled later, baseline must change back to false, in a new PR, or sync will still succeed, because true is allowed when org enforcement is off, but baseline would then be stricter than org policy, which is a policy choice, not a sync failure.
New repo coderabbit, created 2026-10-30, is not in any suborg, and is not covered by this PR, it needs a separate decision.

## Rejected alternatives

Disable org signoff, back to false, to restore old baseline: rejected by user tap, user chose baseline true fix PR.
Leave baseline false, and accept sync failures: rejected, every sync would fail, and issue 30 would stay open.
Set signoff true in repo files only, not baseline: rejected, org enforcement applies to all repos, baseline is the correct layer.
