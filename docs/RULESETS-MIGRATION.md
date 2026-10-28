# Rulesets migration plan, implemented in PR, see status below

Status: migration live 2026-10-27, PR 6 merged as 135334e, PR 7 merged as b6f2e2f.
Live sync creates rulesets, legacy protection deleted by hand, final live sync succeeds.
Admin repo is the one exception, it stays legacy, see below.

Question: should branch protection move to rulesets?
Short answer: yes, rulesets are the GitHub direction, with care.
Long answer: migration is a separate live change, not a comment change.
This plan is not live config, it is a design to approve first.
Do not enable rulesets in config until this plan is approved.

## Why rulesets are better

Branch protection is legacy, rulesets are the current model.
Rulesets cover branches and tags, in one model.
Rulesets support bypass actors, with roles, teams, and Apps.
Rulesets support evaluate mode, to test before enforcement.
Rulesets support org rulesets, for org-wide rules later.
Branch protection supports none of those, in one rule.
Tag protection today is a manual ruleset, not branch protection.
Rulesets would bring tag protection into code, with branch rules.

## Why migration is not free

Safe-settings rulesets plugin is Diffable, not additive.
Enabling rulesets deletes any live ruleset not listed in YAML.
Two manual rulesets exist today, and must be imported exactly.
Branch protection stays after a ruleset sync, unless deleted by hand.
Removing branch rules from YAML does not delete live protection.
Migration needs a live sync, then a manual protection deletion step.
Private repos have no rulesets, free plan returns 403, same as protection.
Ruleset sync for private repos would fail, like branch protection does.

## Live rulesets today, verified 2026-10-27

Actions-checkout, Tag protection, id 25879837, target tag, active.
Conditions: ref_name include `refs/tags/v*`, exclude empty.
Rules: deletion, non_fast_forward, update, no parameters.
Bypass actors: empty, no one can bypass.
Terraform, Default, id 1435723, target branch, active.
Conditions: empty in API, verify in UI before import, see below.
Rules: deletion, non_fast_forward, pull_request.
Pull request parameters: required count 0, merge methods all.
Pull request parameters: dismiss stale false, code owner false.
Pull request parameters: last push approval false, thread resolution false.
Pull request parameters: extra approval for unattributed changes true.
Pull request parameters: dismissal restriction disabled, allowed actors empty.
Bypass actors: empty, no one can bypass.
Other public repos have no repo rulesets today.
Admin repo has no repo rulesets today.
Org rulesets endpoint returned 404, with the user token.

## Branch protection today, to replace

All six public repos have main branch protection, weak gates.
Protection blocks force pushes, and blocks branch deletion.
Protection sets required checks null, reviews null, restrictions null.
Protection sets enforce_admins false, admins are exempt.
That last point is the only mapping that needs care.
Rulesets with empty bypass actors would be stricter than today.
Rulesets with admin bypass always would match enforce_admins false.
Admin bypass in rulesets: actor_id 5, actor_type RepositoryRole.
Safe-settings resolves name `admin` to id 5, for RepositoryRole.
Use name form in YAML, not a raw id, for readability.

## Proposed ruleset design, per repo

Branch ruleset, for all six public repos, name `Protect main`.
Target branch, enforcement active, conditions ref_name main.
Conditions: include `refs/heads/main`, exclude empty.
Rules: deletion, non_fast_forward, no parameters.
Bypass actors: RepositoryRole admin, bypass_mode always.
That matches current protection, for force push and deletion.
No pull_request rule, to match current null reviews.
No required_status_checks rule, to match current null checks.
No creation, linear history, or signature rules, to match today.
Tag ruleset, for actions-checkout only, name `Tag protection`.
Target tag, enforcement active, conditions ref_name `refs/tags/v*`.
Rules: deletion, non_fast_forward, update, no parameters.
Bypass actors: empty, to match live Tag protection exactly.
Branch ruleset, for terraform only, name `Default`, plus Protect main.
Terraform would then have two branch rulesets, Protect main and Default.
Default ruleset must match live Default, exactly, see below.
Do not merge Default into Protect main, names and rules differ.
Default ruleset, target branch, enforcement active.
Conditions: verify in UI first, API shows empty, do not guess.
Rules: deletion, non_fast_forward, pull_request with live parameters.
Bypass actors: empty, to match live Default exactly.

## Terraform Default, open question before import

API returns conditions empty for the Default ruleset.
Empty conditions may mean all branches, or default branch only.
GitHub UI shows the target branches for that ruleset, check there.
Import only after the UI target is confirmed, in writing.
A wrong target could protect all branches, or protect none.
That risk is why Default import is a separate check, not a guess.

## Migration steps, in order

Step 1: Confirm terraform Default target branches, in UI.
Step 2: Add rulesets YAML, in a pull request, with no branch changes yet.
Step 3: Merge, then dispatch a live sync, then verify by API.
Step 4: Verify new rulesets exist, with exact names, rules, and bypass.
Step 5: Verify old manual rulesets are updated, not duplicated.
Step 6: Delete legacy branch protection, by API, per public repo.
Step 7: Verify rulesets still enforce, after protection deletion.
Step 8: Remove branches section from public suborg, in a new pull request.
Step 9: Merge, dispatch live sync, verify rulesets still present.
Step 10: Update docs, and remove the branch protection design notes.
Do not skip step 6, or both models will enforce at once.
Do not do step 8 before step 7, or protection could vanish.
Keep a backup of live ruleset JSON, before step 3, in a local file.
Rollback: restore branch protection by API, and revert the ruleset PR.
Rollback does not auto-delete rulesets, delete them by hand if needed.

## What changes, and what does not change

Changes: protection model, from legacy to rulesets, for public repos.
Changes: tag protection moves from manual to code, for actions-checkout.
Changes: terraform Default moves from manual to code, after target check.
No change: weak gates, no required reviews, no required checks.
No change: private repos, no protection and no rulesets, free plan limit.
No change: admin repo protection, admin is restricted, set by hand.
No change: labels, repo flags, alerts, or restricted repos.
No change: schedule, dry run, or validation workflows.

## Push rulesets, correction, verified live 2026-10-27

Push rulesets do not work on public repos, GitHub refuses them with 422.
Push rulesets also do not work on private repos on the free plan.
Live sync run 40608650379 failed only on private service-control-policies.
Error was 403, for rulesets get and create, on the free plan.
Public repos got their rulesets in that run, private repo got none.
PR 7 removed Protect pushes from the private repo, next live sync succeeded.
Private repo has no rulesets today, and no branch protection either.
That matches the free plan limit, not a config error.
Do not re-add a push ruleset to any repo on the free plan.

## Admin repo, the one legacy exception

Admin repo is restricted, safe-settings does not manage it.
Admin repo main protection stays legacy, for now, by hand.
Legacy protection requires PR, count 0, and check safeSettingsDryRun.
Ruleset equivalent needs a required_status_checks integration mapping.
That mapping is not verified yet, and a wrong mapping could block merges.
Migrate admin repo separately, after safe-settings rulesets prove live.
Admin bypass always would make that migration safe, when it happens.

## Recommendation

Approve migration, but as its own pull request, after this cleanup PR.
Cleanup PR must merge first, so migration review stays focused.
Migration PR should contain only ruleset YAML, and doc updates.
Live sync after migration PR is the real test, dry run is not.
Dry run loads main config, not PR config, so it cannot preview rulesets.
