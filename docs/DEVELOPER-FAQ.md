# Developer FAQ: Change safe-settings in infralicious

This doc answers common change questions, for developers in this org.
It supplements upstream docs, it does not replace them.
Upstream docs answer the general model, this doc answers this org's rules.
All docs use Simplified Technical English, short sentences, active voice.

## Upstream links

- Upstream repo: https://github.com/github-community-projects/safe-settings
- Upstream GitHub Action doc: https://github.com/github-community-projects/safe-settings/blob/main-enterprise/docs/github-action.md
- Upstream configuration summary: https://deepwiki.com/github/safe-settings/3-configuration

Upstream says settings live centrally in an admin repo, not in target repos.
Upstream says settings have 3 levels: org, suborg, and repo.
Upstream says precedence is Repository > Sub-Organization > Organization.
Upstream says applied settings are org, overlayed with suborg, overlayed with repo.
Upstream says a repo creation applies the same overlay, org, then suborg, then repo.
Upstream does not clearly answer this org's guard rules, test limits, or failure recovery.
This doc answers those gaps, with live evidence from this org.

## Where settings live in this org

Admin repo is infralicious/.github, public, main branch.
Config folder is safe-settings/, not .github/, in this org.
Global file is safe-settings/settings.yml.
Suborg files are safe-settings/suborgs/*.yml.
Repo files are safe-settings/repos/*.yml.
Deployment file is safe-settings/deployment-settings.yml.
Target repos must not hold a .github/settings.yml file.
Safe-settings never reads a target repo .github/settings.yml file.
Old probot files were deleted in 2026-10-27, do not re-add them.

## Layers and precedence, in this org

Baseline is safe-settings/settings.yml, it applies to all managed repos.
Suborg is safe-settings/suborgs/*.yml, it applies to repos in its suborgrepos list.
Repo is safe-settings/repos/*.yml, it applies to one repo only.
Precedence is repo wins, then suborg, then baseline.
A suborg cannot strip a rule set at the baseline level, baseline has no rulesets here.
A repo cannot strip a suborg ruleset by omitting it, rulesets are Diffable, see below.
A repo belongs to exactly one suborg, for rulesets, or safe-settings throws a hard error.
Admin repo .github is restricted, it is not managed by safe-settings, it is set by hand.

Current suborgs, as of 2026-10-29:
- public.yml: four repos, no required checks, Protect main only.
- public-actions-checkout.yml: actions-checkout only, Protect main plus test check.
- public-infralicious.github.io.yml: site only, Protect main plus htmlproofer check.
- private.yml: service-control-policies only, no rulesets, free plan returns 403 for rulesets.

## Use case 1: Update global settings

Use this when a change must apply to all managed repos.
Edit safe-settings/settings.yml only, do not edit target repos.
Open a PR to admin repo main, wait for all 7 required checks.
Merge only after a separate tap, then dispatch a live sync by hand.
Verify live settings by API, after every live sync, for at least one repo.
Example: change a label, change a merge method, change a baseline field.
Do not put identity fields in baseline, name, description, homepage, private, or topics.
Baseline with identity fields would wipe repo identity, guard fails on those keys.
Do not put rulesets in baseline, private repos would fail with 403.
If you add a new baseline field, add a guard check for it in the same PR, see ADR-0015.
If guard has no check for a field, a PR can weaken that field silently, and must not merge.

## Use case 2: Update suborg settings

Use this when a change must apply to a group of repos, not all repos.
Edit the suborg file for that group, in safe-settings/suborgs/*.yml.
Open a PR to admin repo main, wait for all 7 required checks.
Merge only after a separate tap, then dispatch a live sync by hand.
Verify live settings by API, for each repo in that suborg.
Example: change Protect main rules for public repos, in public.yml.
Example: change a required check for actions-checkout, in public-actions-checkout.yml.
Do not use suborgteams or suborgproperties, guard forbids them today.
Teams and properties are live state, they can move a repo silently, with no PR review.
Do not use glob patterns in suborgrepos, guard forbids them today.
Use exact repo names only, glob can overmatch a new repo, for example test* matches testament.
A suborg file must not list a repo that is already in another suborg file.
Overlap throws a hard error in safe-settings, and can fail the whole org sync.

## Use case 3: Create a new suborg

Use this when a group of repos needs settings that differ from other groups.
Common reason is a different required check set, for example test, htmlproofer, or none.
Create a new file, safe-settings/suborgs/<name>.yml, with a clear name.
Use a name that matches the group, for example public-<repo>.yml for a single repo group.
List repos exactly, in suborgrepos, with no glob, no teams, no properties.
Copy Protect main from public.yml exactly, then change only the part that must differ.
For a required check, add a required_status_checks rule, with context, integration_id 15368, and strict false.
Update guard in scripts/check-config.py, in the same PR, or guard will fail on the new file.
Add the new file to CHECKED_SUBORGS, if it has a required check, with repo and context.
Update PUBLIC_NO_CHECK_REPOS, if you move a repo out of public.yml, and check the union.
Union of public and checked suborgs must equal all six public repos, guard checks this.
Update simulate, if needed, simulate now reads all suborg files, so no change is usually needed.
Update docs, ARCHITECTURE.md and GUARDS.md, and add an ADR, if the decision is hard to reverse.
Open a PR, wait for checks, merge after a tap, dispatch a live sync, verify live.
Test with a dummy PR to a repo in the new suborg, to prove the new rule works, then close it without merging.

## Use case 4: Override repository settings

Question: are repository settings overridable?
Upstream answer is yes, repo wins over suborg, suborg wins over baseline.
This org answer is yes, but only for identity and rulesets, by guard design.
Repo files are safe-settings/repos/<repo>.yml, one file per repo.
Repo files may set only identity fields: name, description, homepage, private, topics.
Repo files may set tag rulesets, for example Protect tags, and Tag protection for actions-checkout.
Repo files must not set any other repository field, guard fails on non-identity fields.
Examples of forbidden repo fields: has_wiki, has_discussions, has_projects, allow_auto_merge, allow_forking.
Reason: a repo override can weaken baseline silently, and dry run tests main, not PR, see ADR-0010.
If a repo truly needs a different repository field, do not edit the UI only, see below.
Open a PR that updates guard with a reason, and adds an ADR, if the change is hard to reverse.
Do not override Protect main in a repo file, Protect main comes from a suborg, not a repo file.
A repo file with Protect main again would create a duplicate ruleset name for that repo.
To change Protect main for one repo, use a dedicated suborg, see Use case 3, not a repo override.
To change a tag ruleset for one repo, edit that repo file, tag rulesets are repo-scoped by design.
Labels are additive, a custom label in the UI stays, baseline labels are added and updated, never deleted.
To delete a label live, delete it by hand in the UI, and remove it from YAML in the same change, or it will stay.

## Use case 5: Add a required check to one repo

Use a dedicated suborg, not a repo override, and not a shared suborg change.
Step 1: confirm the check job runs on pull_request, in the target repo workflow file.
Step 2: confirm the exact check context name, from live check runs, not from workflow name.
Example: actions-checkout workflow name is Test, job name is test, context is test.
Example: site workflow name is Check links, job name is htmlproofer, context is htmlproofer.
Step 3: create or update a dedicated suborg file, with Protect main plus required_status_checks.
Step 4: set context, integration_id 15368 for GitHub Actions, and strict_required_status_checks_policy false.
Step 5: update guard CHECKED_SUBORGS with repo and context, in the same PR.
Step 6: open a PR to admin repo, wait for checks, merge after a tap, dispatch a live sync.
Step 7: verify live Protect main gains the required check, by API.
Step 8: open a dummy PR to the target repo, verify the check is required and passes, then close it without merging.
Step 9: open a second dummy PR that fails the check, verify merge is BLOCKED, then close it without merging.
Do not require a check that never runs on PRs, for example pages-build-deployment, which runs on push to main only.
Do not require an external check, external sites can fail outside this repo, and weekly external checks use continue-on-error true.
Do not require all checks at once, one repo at a time proves the pattern, then repeat for the next repo.

## Use case 6: Create a new repo, rename a repo, archive a repo

New repo:
Create the repo by hand, in the GitHub UI or by API, do not use force_create in YAML.
Add the repo to the correct suborg list, in the same PR window, as soon as possible.
Add a repo file, if the repo needs identity fields or tag rulesets, otherwise baseline only is enough.
Until you add it to a suborg, the repo gets baseline only, no Protect main, no tag ruleset.
Org new-repo defaults already give secret scanning, push protection, Dependabot alerts, and dependency graph, all true.
Open a PR, merge after a tap, dispatch a live sync, verify live rulesets and labels.

Rename a repo:
Rename the repo in the UI first, then update config in the same change window.
Rename the repo file, safe-settings/repos/<old>.yml to safe-settings/repos/<new>.yml.
Update suborgrepos lists, from old name to new name, in every suborg file that lists it.
Update guard lists, if the repo is in PUBLIC_REPOS, PUBLIC_NO_CHECK_REPOS, or CHECKED_SUBORGS.
Open a PR, merge after a tap, dispatch a live sync, verify live rulesets under the new name.

Archive a repo:
Remove the repo from suborg lists first, in a PR, then merge and sync, then archive in the UI.
Simulate fails on an archived managed repo, with a message to remove it from suborg lists.
If a repo is already archived, remove it from config in a PR, simulate uses PR config, so it will pass.
Do not leave an archived repo in config, every admin PR simulate will fail until you remove it.

## Use case 7: Change a setting in the UI only

Do not do this, unless you also change YAML in the admin repo, in the same change.
Safe-settings sync will revert a UI change, by design, on the next sync, every 4 hours, or on manual dispatch.
Example: change a label in the UI, sync will add baseline labels back, and update them, but custom labels stay, because labels are additive.
Example: change a ruleset in the UI, sync will delete unlisted rulesets, and restore listed rulesets, because rulesets are Diffable.
Example: change a repository field in the UI, sync will restore the YAML value, if that field is in YAML.
Example: change a field that is not in YAML, sync will leave it alone, because that field is unmanaged.
Admin repo is the one exception, it is restricted, and its ruleset is set by hand, not by safe-settings.
If you must make an emergency UI change, open an admin PR right after, to record the same change in YAML, or sync will revert it.

## Use case 8: Delete a ruleset, delete a repo from config, request an exception

Delete a ruleset:
Do not remove a ruleset from YAML without a live deletion plan, see AGENTS.md.
Safe-settings rulesets are Diffable, sync deletes live rulesets that are not listed in YAML.
Simulate fails if a PR would delete a protected live ruleset, Protect main, Protect tags, Tag protection, or Default.
To delete a ruleset on purpose, confirm the deletion in the PR body, and update simulate lists, if needed.
After merge, dispatch a live sync, verify the ruleset is gone live, and no repo lost protection by accident.

Delete a repo from config:
Remove the repo from suborg lists, and delete its repo file, in the same PR.
Simulate will pass, because PR config no longer lists that repo.
After merge, dispatch a live sync, verify the repo no longer gets baseline or rulesets from safe-settings.
Restricted repos are different, see deployment-settings.yml, restrictedRepos must never shrink, guard checks this.

Request an exception:
Open an admin PR, with a reason, and a guard update, if guard forbids the change.
Add an ADR, if the change is hard to reverse, or touches security, see adrs/README.md.
Do not edit an old ADR in place, supersede it with a new ADR, in the same PR as the change.
Do not merge an exception PR without a separate tap, and without all 7 required checks passing.
Admin bypass via PR remains available, for an emergency merge, with an audit log, but it is not a substitute for a config PR.

## Use case 9: Test before merge, and after merge

Before merge, open a PR to admin repo main, and wait for checks.
Required checks are safeSettingsDryRun, validateConfig, configGuard, prConfigSimulation, securityDryRun, scriptTests, schemaDiscovery.
Dry run tests main config, not PR config, see ADR-0010, so a green dry run proves main syncs cleanly, not PR config.
Guard tests PR config, for invariants, overlap, glob, teams, properties, weakening, and required checks.
Simulate tests PR merged ruleset names, against live ruleset names, read only, no live writes.
Schema discovery tests that every upstream schema key is active in config, or mentioned in a comment.
Security dry run tests security.json values, against live secret scanning and push protection, with an App token.
After merge, dispatch a live sync by hand, do not wait for the 4 hour schedule.
Verify live settings by API, for rulesets, labels, repository fields, and restricted repos.
Report the live result, with run IDs, not just a green check, see AGENTS.md.
If live sync fails, fix main config in a new PR, dispatch again, and close the sync-health issue after success.
Sync-health opens an issue on sync failure, for the first time in 2026-10-29, issue 25, and that issue must be closed by hand after success.

## What is not managed by safe-settings, in this org

Security_and_analysis is ignored by safe-settings, even if you put it in YAML.
Secret scanning and push protection live in security.json, handled by scripts/security.js, dry run only, no workflow calls --apply yet.
Immutable releases for actions-checkout are set by API, no safe-settings field exists, and no Terraform resource exists.
Admin repo ruleset is set by hand, by API, with 7 required checks, and bypass pull_request.
Org new-repo defaults are set by API, secret scanning, push protection, Dependabot alerts, and dependency graph, all true.
Org code security configuration 17 is unenforced and unattached, do not rely on it alone.
Community health files in admin repo do proliferate org-wide, workflows and CODEOWNERS do not.
Governance and changelog are deliberately not added, sole maintainer, git log is the changelog.

## Checklist for any config PR

- File is in admin repo, not in a target repo, and uses .yml, not .yaml.
- Repo belongs to exactly one suborg, for rulesets, no overlap, no glob, no teams, no properties.
- Baseline has no identity fields, no rulesets, and no private or public flip.
- Repo file has only identity fields and tag rulesets, no non-identity repository fields.
- New field has a guard check, in the same PR, see ADR-0015.
- Ruleset parameters match expected exactly, see guard, for Protect main, tag, and Default.
- Required check context matches live check runs exactly, not workflow name.
- PR body states live impact after merge and sync, and states if a ruleset deletion is intended.
- All 7 required checks pass, merge needs a separate tap, live sync after merge is the real verification.
