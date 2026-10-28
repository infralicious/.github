# ADR-0003: Keep admin repo restricted, manage its ruleset by hand

Date: 2026-10-27
Status: Accepted

## Context

Safe-settings would sync the admin repo, if it was not restricted.
A sync error in admin config could lock the admin repo, or wipe it.
Admin repo needs protection, but safe-settings cannot protect itself safely.

## Decision

Restrict admin repo in deployment-settings.yml, with docs and others.
Manage admin ruleset by API, by hand, not by safe-settings.
Ruleset id 26008879, Protect main, 4 required checks, bypass pull_request.

## Consequences

Admin ruleset changes need a hand API call, and API verification.
Safe-settings will never delete admin ruleset, because admin is restricted.
Admin ruleset drift is not checked by guard, check it by API, on review.

## Alternatives

Safe-settings manages admin: risky, a bad config could block merges, rejected.
No admin protection: direct pushes could bypass checks, rejected.
