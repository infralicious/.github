# ADR-0001: Use safe-settings as a GitHub Action

Date: 2026-10-26
Status: Accepted

## Context

Org repo settings drifted, per repo, by hand, in UI.
No server hosting was wanted, and no paid plan was wanted.
Safe-settings can run as a Probot app, or as a GitHub Action.

## Decision

Run safe-settings as a GitHub Action, in a public `.github` admin repo.
Use a GitHub App, for auth, with schedule and manual dispatch.
Use no server, no hosting, and no paid plan.

## Consequences

Minutes bill to the admin repo, free for public repos.
Config lives in one repo, in code, with pull request review.
Dry run tests main, not PR, see ADR-0010, for the limit.

## Alternatives

Hosted Probot app: needs a server, more cost, more ops, rejected.
Terraform: needs state and a PAT, see ADR-0007, rejected for now.
