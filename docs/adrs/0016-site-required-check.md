# ADR-0016: Site required check via dedicated suborg

Date: 2026-10-29
Status: Accepted

## Context

Site has a Check links workflow, job htmlproofer, which runs on pull_request.
Htmlproofer checks internal links, images, and scripts in the built site, with --disable-external.
External links are checked weekly, separately, with continue-on-error true, and are not required here.
Pages-build-deployment runs on push to main only, never on PRs, so it cannot be a required check.
Other public repos do not share htmlproofer, so a shared required check would block them.
Actions-checkout required check pattern, ADR-0014, already proves the dedicated suborg pattern.

## Decision

Split site out of public.yml into public-infralicious.github.io.yml.
Public.yml now holds four repos without required checks.
New suborg holds site only, Protect main plus required check htmlproofer.
Required check context is htmlproofer, integration_id 15368 for GitHub Actions, strict false.
Protect main in the new file copies public.yml exactly, except for the required check.
Guard checks union of public and checked suborgs equals all six public repos.
Guard checks required check context, integration, and strict policy exactly.
Site htmlproofer job can fail for Ruby environment reasons, not link reasons, as on 2026-10-29.
Admin bypass via PR remains available, for an emergency merge, with an audit log.

## Consequences

Site PRs cannot merge until htmlproofer passes, unless admin bypasses via PR.
Other public repos are unchanged, they keep Protect main without required checks.
A future checked repo follows the same pattern, one file per check set.
If Check links job name changes, guard and YAML must change together, or PRs will block.
After merge, a dummy PR to site must prove htmlproofer is required and passes, and that a failing link blocks merge.

## Rejected alternatives

Shared required check in public.yml: rejected, it would block repos with no workflows.
Repo-level Protect main override: rejected, same-name merge is untested.
Pages-build-deployment as required check: rejected, it never runs on PRs.
External links as required check: rejected, external sites can fail outside this repo, and weekly job uses continue-on-error.
Scorecard as required check too: rejected for now, htmlproofer alone is the minimal quality gate for docs.
