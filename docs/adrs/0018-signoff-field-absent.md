# ADR-0018: Baseline signoff field absent, to avoid 422 on new repos

Date: 2026-11-02
Status: Accepted

## Context

Org web_commit_signoff_required is true, verified by API on 2026-10-30.
Live repos already show signoff true, for terraform and actions-checkout.
Baseline set signoff true in PR 32, see ADR-0017, to fix sync run 41035007238.
Sync run 41100158831 failed on 2026-10-30, for new repo template only.
PATCH template returned 422, with message commit signoff is enforced by the organization and cannot be disabled.
PATCH body already contained signoff true, so value true did not fix the failure.
Existing repos succeeded in run 41042021521, because they had no diff, so no PATCH was sent.
New repos get a full PATCH on first sync, so they fail, when baseline includes this field.
Later sync runs on 2026-11-01 and 2026-11-02 succeeded, head 0ad854d, because template fields now match baseline, so no PATCH was sent.
Template still has no Protect main or Protect tags live, onboarding is PR 33, still open, separate from this fix.
This fix is preventive, for future new repos, not a fix for a current sync failure.

## Decision

Remove web_commit_signoff_required from baseline settings.yml entirely.
Safe-settings must never send this field, so baseline must not set it.
Update guard to require absence of the field, in the same PR, see ADR-0015.
Supersede ADR-0017, never edit ADR-0017 in place, see ADR pattern.
Do not set this field in a repo file, for the same reason, guard identity rule already bans non-identity fields in repo files.
Org enforcement keeps live signoff true, for all repos, even without a baseline field.
After merge, dispatch a live sync by hand, verify success, and verify template rulesets after PR 33 merges.
Close issue 44 after a successful sync, and after PR 33 merges, in that order, or PR 33 alone does not prove this fix.

## Consequences

Sync can succeed for a new repo, even when its fields differ from baseline.
Live signoff stays true, by org policy, not by baseline.
Web UI commits still require signoff, local git pushes are unchanged.
If org signoff is disabled later, live signoff may turn false, unless a repo sets it by hand.
That case needs a new decision, with a new ADR, and a new guard rule.
This PR does not onboard template, PR 33 does that, with Protect main and Protect tags.

## Rejected alternatives

Keep baseline signoff true, and accept future new-repo sync failures: rejected, next new repo with non-baseline fields would fail sync again.
Set signoff true in repo files only, not baseline: rejected, same 422, PATCH includes the field, for that repo.
Disable org signoff, to allow baseline field: rejected, org policy is to enforce signoff, and user chose baseline fix in PR 32.
