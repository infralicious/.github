# ADR-0013: Private allow_forking must not be set via safe-settings

Date: 2026-10-29
Status: Accepted
Supersedes: ADR-0012, allow_forking part only

## Context

ADR-0012 set allow_forking false for private service-control-policies.
Live sync run 40891902675 failed with exit 1, after PR 24 merged.
Error was PATCH repos/infralicious/service-control-policies, status 422.
Message was "This organization does not allow private repository forking".
Live allow_forking was already false, via org policy, not via safe-settings.
Other PR 24 changes did apply live, despite the sync failure.
Sync-health opened issue 25, which proves sync-health works for the first time.

## Decision

Remove allow_forking from service-control-policies.yml, do not set it at all.
Guard fails if a private repo file sets allow_forking, any value.
Baseline comment records that private forking is off via org policy.
ADR-0012 is not edited in place, this record supersedes its allow_forking part only.
All other ADR-0012 decisions stay in force, including bypass, squash, and field locking.

## Consequences

Next live sync should succeed, with no allow_forking PATCH for the private repo.
Live allow_forking stays false, via org policy, not via safe-settings.
A future org policy change that allows private forking would need a new decision.
Issue 25 must be closed by hand after a successful sync, per its body text.

## Rejected alternatives

Keep allow_forking false: rejected, it breaks every live sync with 422.
Set allow_forking true for private repo: rejected, it would allow private forks, and likely also 422.
Set allow_forking false in baseline for all repos: rejected, public repos need forking on.
