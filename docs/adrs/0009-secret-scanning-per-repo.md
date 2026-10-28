# ADR-0009: Enable secret scanning per repo, not org config alone

Date: 2026-10-27
Status: Accepted

## Context

Org has a GitHub recommended security configuration, id 17, unenforced, unattached.
Org new-repo defaults were all false, for secret scanning and push protection.
Safe-settings ignores security_and_analysis, in ignorableFields, so YAML cannot set it.

## Decision

Enable secret scanning and push protection, per public repo, by API.
Verify by API, per repo, and check open alerts, after enablement.
Private repos stay off, free plan returns 422, GHAS would be needed.
Set org new-repo defaults later, for new repos, as a separate step.

## Consequences

All 6 public repos are enabled, with 0 open alerts, verified 2026-10-27.
A new repo will not get protection, until org defaults or script covers it.
Script in ADR-0006 covers drift and new repos, with dry run first.

## Alternatives

Org config alone: unenforced, unattached, silent drift, rejected as sole control.
Terraform: see ADR-0007, rejected for now.
No secret scanning: security gap for a security org, rejected.
