# Architectural decision records

This folder holds concise decision records, for this repo.
Each record is short, one decision, with context and consequences.
Records are immutable, do not edit a record after it is accepted.
To change a decision, add a new record, and mark the old record superseded.
Use Simplified Technical English, short sentences, active voice, one idea each.
Template: Title, Date, Status, Context, Decision, Consequences, Alternatives.

## Index

- ADR-0001: Use safe-settings as a GitHub Action, not hosted Probot, not Terraform.
- ADR-0002: Use rulesets, not legacy branch protection, for public repos.
- ADR-0003: Keep admin repo restricted, manage its ruleset by hand.
- ADR-0004: Use additive labels, not destructive labels.
- ADR-0005: Keep Dependabot alerts on, security updates off, Renovate updates code.
- ADR-0006: Use JavaScript for security script, to match safe-settings, for upstream PR.
- ADR-0007: Do not use Terraform for org settings today, revisit at 20 plus repos.
- ADR-0008: Publish no email in community files, use contact form only.
- ADR-0009: Enable secret scanning per repo, not org config alone.
- ADR-0010: Dry run tests main, not PR, so simulate script is required.
