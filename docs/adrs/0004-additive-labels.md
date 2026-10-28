# ADR-0004: Use additive labels, not destructive labels

Date: 2026-10-27
Status: Accepted

## Context

Safe-settings labels plugin can delete unlisted labels, by default.
Repos had custom labels, from UI, that were not in YAML.
A destructive sync would delete those labels, with no warning in advance.

## Decision

Use additive labels at org level, labels only add or update, never delete.
Keep the 10 label set in YAML, custom UI labels stay live.

## Consequences

Old labels never get cleaned by sync, clean them by hand, if needed.
Label color and description drift is fixed by sync, for YAML labels.
New repos get the 10 labels, plus any custom labels added later.

## Alternatives

Destructive labels: clean, but risky, custom labels lost, rejected.
No label management: labels drift per repo, rejected.
