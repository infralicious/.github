# ADR-0011: Enable secret scanning on admin repo itself

Date: 2026-10-27
Status: Accepted

## Context

Secret scanning was enabled on 6 public target repos, with 0 alerts.
Admin repo itself was missed, because it is restricted from safe-settings.
Admin repo is public, and it holds workflows with secret references.

## Decision

Enable secret scanning and push protection, on admin repo, by API.
Add admin repo to security.json, so security dry run checks it.
Add admin repo to security dry run workflow, App token repositories list.
Verify by API, after enablement, and check open alerts.

## Consequences

All 7 public org repos now have secret scanning and push protection.
Security dry run now covers admin repo, not just target repos.
Private repos stay off, free plan returns 422, GHAS would be needed.

## Alternatives

Leave admin repo off: gap, workflows repo is the most sensitive repo, rejected.
Use org config alone: unenforced and unattached, see ADR-0009, rejected.
