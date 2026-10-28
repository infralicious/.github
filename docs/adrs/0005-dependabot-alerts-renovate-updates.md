# ADR-0005: Keep Dependabot alerts on, security updates off, Renovate updates code

Date: 2026-10-27
Status: Accepted

## Context

Dependabot alerts and Renovate both can open update pull requests.
Two update engines would open duplicate pull requests, for the same update.
Renovate is already installed org-wide, with a shared config and dashboard.

## Decision

Keep Dependabot alerts on, in safe-settings baseline, for all managed repos.
Keep Dependabot security updates off, in baseline, on purpose.
Use Renovate as the update engine, for dependencies and safe-settings version.

## Consequences

Repos with no active Renovate get an alert, with no automated fix PR.
Most such repos are markdown only, so risk stays low.
Renovate PRs never automerge for safe-settings, review is required.

## Alternatives

Dependabot updates on, Renovate off: loses Renovate grouping and config, rejected.
Both on: duplicate PRs, noise, rejected.
