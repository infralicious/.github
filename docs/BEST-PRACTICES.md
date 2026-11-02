# Best practices, for admin repo and org

Scope, 2026-11-02: admin repo infralicious/.github, and org infralicious, only.
This doc does not cover TrueTime, credit freeze, site content, or other products.
Those products have their own best practices, in their own repos.
Only practices that apply to a config repo and to GitHub org security are listed.
Practices that do not apply are listed, with a reason, to show they were checked, not missed.

## OWASP Cheat Sheet Series, applicable sheets

OWASP Cheat Sheet Series is the security baseline, see AGENTS.md.
Index: https://cheatsheetseries.owasp.org/

### GitHub Actions Security, followed, with gaps

Followed:
- All actions are SHA pinned, with Renovate version comments, no tags, no branches, in all workflows.
- No pull_request_target trigger, in any workflow, verified by search.
- Workflow permissions are least privilege, mostly contents read, plus issues write for sync-health, plus security-events write for zizmor reusable, when merged.
- Secrets are never in code, guard checks for private key patterns, and for secrets.* references only.
- Workflows treat CI as production, because sync workflow uses App private key, and security dry run uses App token.

Gaps, with issues:
- App token blanket permissions, in security dry run and in renovate workflows, zizmor error github-app, High confidence, see new issue for token permission limiting, and issue 38 for zizmor trial.
- Artipacked warnings, checkout without persist-credentials false, 11 in admin, 2 in site, Low confidence, see issue 38, fix is easy, add persist-credentials false, workflows do not upload artifacts, risk is low today.
- Workflow_run trigger, in sync-health, zizmor error dangerous-triggers, Medium confidence, by-design, sync-health does not checkout PR code, it only opens an issue with run metadata, risk is low today, with a suppress comment if zizmor runs in CI.

### Secrets Management, followed, with one gap

Followed:
- Secrets live in GitHub Secrets, App private key, and vars, never in code, never in logs, never in memory files.
- App token is short lived, created per workflow run, revoked after run, via create-github-app-token, except skip-token-revoke false, default.
- Secret scanning and push protection are enabled, for all public repos, after PR 46, with 0 alerts, verified by API.
- Disaster recovery covers App private key lost or leaked, generate new key, delete old key, update secrets, see DISASTER-RECOVERY.md.

Gap, new issue:
- No scheduled rotation for App private key, only incident rotation, on leak or loss.
- OWASP Secrets Management says rotate regularly, so stolen credentials are short lived, and set expirations that force rotation.
- GitHub App private keys do not expire, unless rotated manually, so a schedule is needed, for example annual, on App creation anniversary, 2026-10-26, with procedure already in disaster recovery, just add a schedule and a reminder.

### CI/CD Security, followed, with gaps

Followed:
- Build, release, and run are separate, see 12-factor V below.
- PR checks are required, 7 checks, in admin ruleset, with bypass pull_request only, not always.
- Dry run tests main, not PR, see ADR-0010, guard mitigates, by checking PR config locally and in CI, before merge.
- Live sync after merge is the real verification, with run ID, and live API check, see AGENTS.md.

Gaps, with issues:
- No Scorecard workflow in admin repo, see new issue, site and actions-checkout have Scorecard, admin does not.
- No watchdog for missing scheduled sync, see new issue, sync-health opens an issue on sync failure, not on sync missing, and scheduled sync at 10:00 CST and at 14:00 CST, on 2026-11-02, did not run, with no failure log, because GitHub scheduler drops runs under load, especially at minute 0, top of hour.
- Schedule minute 0, cron 0 */4 * * *, is top of hour peak, GitHub docs recommend a different minute, for example 17, to reduce delay risk, see new issue, mitigation, not a guarantee.

### OWASP sheets, not applicable, with reasons

- XSS, SQL Injection, SSRF, CSRF, and other web app sheets: admin repo has no web app, no user input, no database, no server, so these sheets do not apply.
- Authentication and session sheets: admin repo has no user login, GitHub handles auth, org requires 2FA, verified, so these sheets apply only via GitHub, not via admin code.
- Cryptography sheets: admin repo has no custom crypto, only GitHub App private key, and SSH signing, both handled by GitHub and by git, so custom crypto sheets do not apply, except key rotation, above.

## 12-Factor App, applicable factors only

12-Factor App is for software-as-a-service apps, see https://12factor.net/
Admin repo is not a SaaS app, it is config plus workflows plus scripts, so most factors do not apply, as a service, but some apply, as a delivery pipeline.

### I Codebase, followed

One codebase, tracked in version control, many deploys.
Admin repo is one codebase, in git, with main branch, and PRs, and it deploys config to 11 org repos, via sync.
No other codebase holds safe-settings config, target repos do not hold .github/settings.yml, after probot retirement.

### II Dependencies, followed

Dependencies are declared, and isolated, with no implicit reliance on system tools.
Workflows declare actions, with SHA pins, and Renovate updates them, never automerged.
Scripts use Node built-in only, and Python stdlib only, no external packages, so no package.json, no lockfile, no supply chain for script deps.
Zizmor binary, version 1.31.1, is pinned in central workflow, with download URL, and in local VM, with version check, see PR 49.

### III Config, followed, with a note

Config that varies between deployments should be stored in the environment.
Safe-settings config itself is code, by purpose, it is the deployment, not an app config, so factor III applies differently here.
Secrets and App IDs vary by environment, and they live in GitHub Secrets and vars, not in code, see Secrets Management above.
Repo identity, name, description, homepage, private, topics, lives in repos/*.yml, not in baseline, to avoid wiping identity, see ARCHITECTURE.md.

### IV Backing services, not applicable, as a service

Admin repo has no database, queue, cache, or other backing service, as an app would.
GitHub API is an attached service, treated as external, with App token, and with API calls in scripts, not hardcoded credentials, so the principle holds, but factor IV, as written for SaaS apps, does not apply.

### V Build, release, run, partially followed, with a known gap

Build, release, and run stages are strictly separate.
Build is PR checks, 7 checks, plus guard and simulate, in CI, on PR to main.
Release is merge to main, with squash, and with a merge tap, per PR, not automerged.
Run is scheduled sync, every 4 hours, plus manual dispatch, with concurrency group, cancel-in-progress false, to avoid overlapping syncs.
Known gap, documented, not a new issue: dry run tests main, not PR, see ADR-0010, guard mitigates, live sync after merge is the real verification.

### VI Processes, not applicable, as an app

Admin repo has no long running app processes, workflows are short lived, stateless, and disposable, by GitHub Actions design.
Factor VI, as written for SaaS apps, does not apply, but the principle holds, no state lives in a workflow runner, state lives in GitHub, in repos, in rulesets, and in security.json, all in version control.

### VII Port binding, not applicable

Admin repo exports no service, binds no port, has no server, so factor VII does not apply.

### VIII Concurrency, partially followed

Concurrency is via process model, for apps, but for workflows, concurrency is via GitHub concurrency group.
Sync workflow uses concurrency group safe-settings-sync, cancel-in-progress false, so two syncs never run at once, and a second sync waits, not cancels, the first.
Other workflows have no concurrency group, because they are PR checks, and they can run in parallel, safely, with no shared state.

### IX Disposability, partially followed

Workflows start fast, on GitHub hosted runners, and stop fast, with no cleanup needed, except token revocation, which create-github-app-token does, by default.
Factor IX, as written for app processes, does not apply, but the principle holds, for workflows.

### X Dev/prod parity, partially followed, with a known gap

Dev, staging, and prod should be as similar as possible.
Admin repo has no staging org, no test org for safe-settings, unlike TrueTime, which has braindrain test site.
Parity is limited to dry run versus live sync, with a known gap, see ADR-0010, dry run tests main, not PR, and live sync is the real verification.
This gap is documented, not a new issue, unless a staging org is created, which is out of scope for a 1 person Free org, today.

### XI Logs, followed

Logs are event streams, with execution environment aggregating them.
Workflow logs are in GitHub Actions, with run IDs, and with sync-health issues, on failure, with run ID, and with live API checks, after sync.
No central log aggregation is needed, for a 1 person org, GitHub Actions logs are sufficient, and they are not stored in the repo, by design.

### XII Admin processes, followed

Admin tasks run as one-off processes, with code in version control.
Scripts in repo, check-config.py, security.js, zizmor-central.py, check-apps.py, all run as one-off processes, in CI, or by hand, with no manual UI edits, except admin ruleset, which is hand managed, because admin repo is restricted, see ADR-0003.
Manual UI edits, without a config change, are forbidden, see AGENTS.md, except admin ruleset, which is documented, hand managed, with a plan, in RULESETS-MIGRATION.md.

## GitHub best practices, followed, with gaps in issue 43

Followed:
- Org requires 2FA, verified, 1 member, sole maintainer, default repo permission read.
- Rulesets, not legacy branch protection, for all managed public repos, with Protect main and Protect tags, and with required checks, for site and actions-checkout.
- Secret scanning and push protection, for all public repos, after PR 46, with 0 alerts.
- Dependabot alerts on, for all checked repos, security updates off, by design, Renovate is the updater, see ADR-0005.
- Labels, topics, and identity fields, managed centrally, with guard, to prevent silent weakening, see ADR-0015.

Gaps, already in issue 43, do not duplicate:
- Private vulnerability reporting, enabled only on actions-checkout, disabled on all other public repos.
- CodeQL default setup, not configured for actions-checkout and site.
- Org Actions policies, unreadable, token lacks admin:org scope, 403, need a UI check, or a token with admin:org scope.

## OpenSSF Scorecard and SLSA, applicable only in part

Scorecard, applicable to admin, site, actions-checkout, and template, all have workflows, and all have branch protection or rulesets, token permissions, pinned actions, and dangerous workflow checks, all relevant.
Site and actions-checkout have Scorecard, admin does not, see new issue, for Scorecard in admin.
Template has Scorecard, plus zizmor, plus other checks, already covered.

SLSA, applicable only to actions-checkout, which is a public action, with tags, and with downstream trust, and with release integrity, see issue 41, for Sigstore signing, as an alternative, or in addition, to SLSA provenance.
SLSA is not applicable to admin repo, which has no release artifacts, no tags, no published package, and no downstream consumers, except as a config source.
SLSA is not applicable to site, which is docs, deployed via Pages, with Pages-build-deployment workflow, not a release artifact, and not a package.

## NIST and CIS, not applicable as formal frameworks

NIST CSF, NIST 800-53, CIS Benchmarks, SOC 2, and ISO 27001, are formal frameworks, with audits, and with costs, that do not fit a 1 person Free org, today.
Principles from those frameworks, identify, protect, detect, respond, recover, least privilege, and audit logs, are followed informally, via guard, sync-health, disaster recovery, and live verification, with no formal audit, no ISMS, and no certifications.
This decision matches TrueTime stance, no SOC 2 or ISO company audits, too expensive pre-revenue, inherit Atlassian via Forge, for TrueTime, and inherit GitHub via Actions, for admin repo, with no formal claim.
If org grows to a team, or to Enterprise, revisit formal frameworks, with a new decision, and a new ADR, not in this doc today.

## Gaps, summary, with issue links

New gaps, with new issues, created with this doc:
- Scorecard workflow in admin repo, new issue, see below.
- Sync schedule minute and missing sync watchdog, new issue, see below.
- App private key scheduled rotation, new issue, see below.
- App token permission limiting, in security dry run and in renovate workflows, new issue, see below.

Already tracked gaps, do not duplicate:
- Artipacked, in issue 38, zizmor trial.
- GitHub-app blanket token, in issue 38, and in new token permission issue, with a link, to avoid losing it in a trial issue.
- Private vulnerability reporting, CodeQL, and org Actions policies, in issue 43.
- Sigstore signing, in issue 41.
- Repolinter, in issue 40.
- Best Practices Badge, in issue 42.
- Zizmor CI, in issue 38, with PR 48, PR 15, and PR 5, plus central App PR 49.
- Harden Runner, in issue 39, with site PR 16.
