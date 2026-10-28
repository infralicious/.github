# ADR-0008: Publish no email in community files, use contact form only

Date: 2026-10-27
Status: Accepted

## Context

Public docs site carries no email addresses, by user direction.
Community files in .github repo become org-wide defaults, for all repos.
An email in those files would publish it, on every repo, with no control.

## Decision

Publish no email in CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, or SUPPORT.
Use contact form https://infralicious.com/contact.html, as public contact.
Use GitHub private vulnerability reporting, for security reports, where available.

## Consequences

Support email still forwards to personal email, but it is not public.
Security reports go by form or private reporting, not by email.
A repo file, if it exists, wins over an org default, so a repo can add email later.

## Alternatives

Publish support email: simple, but breaks prior direction, rejected.
No contact method: users cannot report, rejected.
