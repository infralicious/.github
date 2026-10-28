# ADR-0007: Do not use Terraform for org settings today

Date: 2026-10-27
Status: Accepted

## Context

Terraform provider can manage repo security settings, and org new-repo defaults.
Terraform needs state, and a PAT with broad scopes, with rotation pain.
Org has 9 repos, sole maintainer, phone-first workflow, free plan.

## Decision

Do not use Terraform for org settings today, keep safe-settings plus a small script.
Split by field, safe-settings owns repo settings and rulesets, script owns security.
Revisit Terraform at 20 plus repos, or when teams and secrets management are needed.
At migration, retire the custom script, do not run both for the same field.

## Consequences

No state file to manage, no PAT rotation, App token already works.
Drift detection is by guard and simulate, on PRs, not by Terraform plan.
Terraform gaps remain, no immutable releases resource, no free org rulesets.

## Alternatives

Terraform now: state and PAT friction outweigh benefits, at 9 repos, rejected for now.
Org config alone: unenforced and unattached, see ADR-0009, rejected as sole control.
