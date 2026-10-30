#!/usr/bin/env python3
"""Guard for safe-settings config. Run locally and in CI.

Usage: python3 scripts/check-config.py guard
       python3 scripts/check-config.py simulate

Guard checks PR files, no secrets, no live writes.
Simulate compares PR merged rulesets to live rulesets, read only.
It uses GITHUB_TOKEN if set, else unauthenticated public API calls.
It never applies a change, it only reports and fails on footguns.
"""
import glob
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_REPOS = [
    "actions-checkout",
    "awesome-service-control-policies",
    "coderabbit",
    "infralicious.github.io",
    "renovate-config",
    "saas-auth-wall-of-shame",
    "terraform-aws-securityhub-batchupdatefindings",
]
PUBLIC_NO_CHECK_REPOS = [
    "awesome-service-control-policies",
    "coderabbit",
    "renovate-config",
    "saas-auth-wall-of-shame",
    "terraform-aws-securityhub-batchupdatefindings",
]
# Dedicated checked suborgs: file -> {repo: required check context}
CHECKED_SUBORGS = {
    "safe-settings/suborgs/public-actions-checkout.yml": {
        "actions-checkout": "test",
    },
    "safe-settings/suborgs/public-infralicious.github.io.yml": {
        "infralicious.github.io": "htmlproofer",
    },
}
PRIVATE_REPOS = ["service-control-policies"]
RESTRICTED = [".github", "admin", "safe-settings", "docs"]
REQUIRED_RULESETS = {
    "actions-checkout": {"Protect main", "Tag protection"},
    "terraform-aws-securityhub-batchupdatefindings": {
        "Protect main",
        "Default",
        "Protect tags",
    },
}
DEFAULT_REQUIRED = {"Protect main", "Protect tags"}

def load_yaml(path):
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML missing, run: pip install pyyaml")
    with open(path) as f:
        return yaml.safe_load(f) or {}

def fail(msg):
    print(f"GUARD FAIL: {msg}")
    sys.exit(1)

def check_guard():
    errors = []
    # YAML parse, all config and workflow files
    for path in sorted(
        glob.glob("safe-settings/**/*.yml", recursive=True)
        + glob.glob(".github/workflows/*.yml")
        + glob.glob(".github/ISSUE_TEMPLATE/*.yml")
        + glob.glob(".github/FUNDING.yml")
    ):
        try:
            load_yaml(path)
            print(f"YAML OK: {path}")
        except Exception as e:
            errors.append(f"YAML parse fail {path}: {e}")
    # Restricted repos, exact list, never shrink
    dep = load_yaml("safe-settings/deployment-settings.yml")
    restricted = dep.get("restrictedRepos") or []
    for name in RESTRICTED:
        if name not in restricted:
            errors.append(f"restrictedRepos missing {name}, never remove it")
    # Baseline must not hold identity, branches, or rulesets
    base = load_yaml("safe-settings/settings.yml")
    for key in ["name", "description", "homepage", "private", "topics", "branches", "rulesets"]:
        if key in base and base[key] is not None:
            errors.append(f"baseline settings.yml must not set {key}, it would wipe or break repos")
    if (base.get("repository") or {}).get("default_branch") != "main":
        errors.append("baseline default_branch must stay main")
    repo_base = base.get("repository") or {}
    if repo_base.get("has_projects") is not False:
        errors.append("baseline has_projects must stay false, classic Projects are empty")
    if repo_base.get("has_pull_requests") is not True:
        errors.append("baseline has_pull_requests must stay true")
    if repo_base.get("allow_update_branch") is not True:
        errors.append("baseline allow_update_branch must stay true")
    if repo_base.get("allow_auto_merge") is not False:
        errors.append("baseline allow_auto_merge must stay false, merge needs a manual tap")
    if repo_base.get("has_wiki") is not False:
        errors.append("baseline has_wiki must stay false")
    if repo_base.get("has_discussions") is not False:
        errors.append("baseline has_discussions must stay false")
    if repo_base.get("squash_merge_commit_title") != "PR_TITLE":
        errors.append("baseline squash_merge_commit_title must stay PR_TITLE")
    if repo_base.get("squash_merge_commit_message") != "PR_BODY":
        errors.append("baseline squash_merge_commit_message must stay PR_BODY")
    # Full baseline lock, 2026-10-29, ADR-0015: every baseline field must be checked, or a PR can weaken it silently.
    # Dry run tests main, not PR, so guard is the only pre-merge check for these fields.
    if repo_base.get("has_issues") is not True:
        errors.append("baseline has_issues must stay true")
    if repo_base.get("allow_squash_merge") is not True:
        errors.append("baseline allow_squash_merge must stay true")
    if repo_base.get("allow_merge_commit") is not True:
        errors.append("baseline allow_merge_commit must stay true")
    if repo_base.get("allow_rebase_merge") is not True:
        errors.append("baseline allow_rebase_merge must stay true")
    if repo_base.get("delete_branch_on_merge") is not True:
        errors.append("baseline delete_branch_on_merge must stay true")
    if repo_base.get("web_commit_signoff_required") is not True:
        errors.append("baseline web_commit_signoff_required must stay true, org enforces signoff, false returns 422")
    if repo_base.get("is_template") is not False:
        errors.append("baseline is_template must stay false")
    sec_base = repo_base.get("security") or {}
    if sec_base.get("enableVulnerabilityAlerts") is not True:
        errors.append("baseline security enableVulnerabilityAlerts must stay true")
    if sec_base.get("enableAutomatedSecurityFixes") is not False:
        errors.append("baseline security enableAutomatedSecurityFixes must stay false, Renovate is the updater")
    label_names = [x.get("name") for x in (base.get("labels") or [])]
    if "security" not in label_names:
        errors.append("baseline labels must include security")
    # Full Protect main check, 2026-10-29, ADR-0015: every rule and parameter must match, or a PR can weaken it silently.
    EXPECTED_PR_PARAMS = {
        "allowed_merge_methods": ["squash"],
        "dismiss_stale_reviews_on_push": False,
        "dismissal_restriction": {"allowed_actors": [], "enabled": False},
        "require_code_owner_review": False,
        "require_extra_approval_for_unattributed_changes": True,
        "require_last_push_approval": False,
        "required_approving_review_count": 0,
        "required_review_thread_resolution": False,
    }
    def check_protect_main(pm, label, want_required):
        if pm.get("target") != "branch":
            errors.append(f"{label} Protect main target must stay branch")
        if pm.get("enforcement") != "active":
            errors.append(f"{label} Protect main enforcement must stay active")
        bypass = pm.get("bypass_actors") or []
        if len(bypass) != 1 or bypass[0].get("actor_type") != "RepositoryRole" or bypass[0].get("bypass_mode") != "pull_request":
            errors.append(f"{label} Protect main bypass must stay RepositoryRole admin pull_request")
        cond = (pm.get("conditions") or {}).get("ref_name") or {}
        if cond.get("include") != ["refs/heads/main"] or cond.get("exclude") != []:
            errors.append(f"{label} Protect main conditions must stay refs/heads/main only")
        rule_types = [r.get("type") for r in (pm.get("rules") or [])]
        want_types = ["deletion", "non_fast_forward", "pull_request"] + (["required_status_checks"] if want_required else [])
        if rule_types != want_types:
            errors.append(f"{label} Protect main rules must stay {want_types}, got {rule_types}")
        pr_rules = [r for r in (pm.get("rules") or []) if r.get("type") == "pull_request"]
        if len(pr_rules) != 1:
            errors.append(f"{label} Protect main must hold exactly one pull_request rule")
        elif pr_rules[0].get("parameters") != EXPECTED_PR_PARAMS:
            errors.append(f"{label} Protect main pull_request parameters must match expected exactly, got {pr_rules[0].get('parameters')}")
    public_rules = (load_yaml("safe-settings/suborgs/public.yml").get("rulesets") or [])
    protect_main = [r for r in public_rules if r.get("name") == "Protect main"]
    if len(protect_main) != 1:
        errors.append("public suborg must hold exactly one Protect main ruleset")
    else:
        check_protect_main(protect_main[0], "public suborg", False)
    # Suborg lists, exact, private must never enter public
    public = load_yaml("safe-settings/suborgs/public.yml")
    public_repos = public.get("suborgrepos") or []
    if sorted(public_repos) != sorted(PUBLIC_NO_CHECK_REPOS):
        errors.append(f"public suborgrepos must be exactly {PUBLIC_NO_CHECK_REPOS}, got {public_repos}")
    # Union of public and checked suborgs must be all public repos, no repo dropped silently.
    union_repos = list(public_repos)
    for checked_path, checked_map in CHECKED_SUBORGS.items():
        checked_data = load_yaml(checked_path)
        checked_repos = checked_data.get("suborgrepos") or []
        if sorted(checked_repos) != sorted(checked_map.keys()):
            errors.append(f"{checked_path} suborgrepos must be exactly {list(checked_map.keys())}, got {checked_repos}")
        union_repos.extend(checked_repos)
        # Checked Protect main must have the exact required check, integration 15368, strict false.
        checked_rules = checked_data.get("rulesets") or []
        pm_list = [r for r in checked_rules if r.get("name") == "Protect main"]
        if len(pm_list) != 1:
            errors.append(f"{checked_path} must hold exactly one Protect main ruleset")
        else:
            pm = pm_list[0]
            check_protect_main(pm, checked_path, True)
            rc_rules = [r for r in (pm.get("rules") or []) if r.get("type") == "required_status_checks"]
            if len(rc_rules) != 1:
                errors.append(f"{checked_path} Protect main must hold exactly one required_status_checks rule")
            else:
                params = rc_rules[0].get("parameters") or {}
                checks = params.get("required_status_checks") or []
                for repo_name, context in checked_map.items():
                    if not any(c.get("context") == context and c.get("integration_id") == 15368 for c in checks):
                        errors.append(f"{checked_path} Protect main must require check {context} with integration 15368 for {repo_name}")
                if params.get("strict_required_status_checks_policy") is not False:
                    errors.append(f"{checked_path} strict_required_status_checks_policy must stay false")
    if sorted(union_repos) != sorted(PUBLIC_REPOS):
        errors.append(f"public plus checked suborgs must be exactly {PUBLIC_REPOS}, got {union_repos}")
    if "rulesets" in public and public["rulesets"] is None:
        errors.append("public suborg rulesets must not be null")
    private = load_yaml("safe-settings/suborgs/private.yml")
    if sorted(private.get("suborgrepos") or []) != sorted(PRIVATE_REPOS):
        errors.append(f"private suborgrepos must be exactly {PRIVATE_REPOS}")
    for key in ["branches", "rulesets"]:
        if key in private and private[key] is not None:
            errors.append(f"private suborg must not set {key}, free plan returns 403")
    # Suborg overlap, glob, teams, properties, across ALL suborg files.
    # A repo in 2 suborgs is a hard error in safe-settings, not a merge.
    # Code throws Multiple suborg configs for X in Y and Z, and whole sync can fail.
    # Dry run cannot catch this, dry run tests main, not PR, so guard must catch it.
    # Teams and properties are live state, not YAML state, so they can move a repo silently.
    # Globs can overmatch a new repo, so exact names are required for ruleset suborgs.
    # Guard fails on teams, properties, or glob patterns in any suborg file, today.
    # To allow teams or properties later, remove this guard block first, with a live membership check.
    import fnmatch
    seen_suborg_repos = {}
    for sub_path in sorted(glob.glob("safe-settings/suborgs/*.yml")):
        sub_data = load_yaml(sub_path)
        if sub_data.get("suborgteams"):
            errors.append(f"{sub_path} must not use suborgteams, live team change can move a repo silently, guard forbids it today")
        if sub_data.get("suborgproperties"):
            errors.append(f"{sub_path} must not use suborgproperties, live property change can move a repo silently, guard forbids it today")
        for entry in (sub_data.get("suborgrepos") or []):
            if any(c in str(entry) for c in "*?["):
                errors.append(f"{sub_path} must not use glob pattern {entry}, exact repo names only, glob can overmatch a new repo")
            if entry in seen_suborg_repos:
                errors.append(f"repo {entry} is in 2 suborgs: {seen_suborg_repos[entry]} and {sub_path}, safe-settings throws a hard error on overlap")
            seen_suborg_repos[entry] = sub_path
    # Repo files, known names only, no unknown repo, no docs, no admin
    repo_files = sorted(os.path.basename(p)[:-4] for p in glob.glob("safe-settings/repos/*.yml"))
    known = set(PUBLIC_REPOS + PRIVATE_REPOS)
    for name in repo_files:
        if name not in known:
            errors.append(f"unknown repo file safe-settings/repos/{name}.yml, repo must exist in org")
    for name in RESTRICTED:
        if name in repo_files:
            errors.append(f"restricted repo {name} must not have a repo file")
    # Per-repo rules, no push, no private ruleset, no branch protection
    for path in sorted(glob.glob("safe-settings/repos/*.yml")):
        data = load_yaml(path)
        name = os.path.basename(path)[:-4]
        if "branches" in data and data["branches"] is not None:
            errors.append(f"{name} must not use legacy branches, rulesets replaced them")
        rulesets = data.get("rulesets") or []
        for rule in rulesets:
            if rule.get("target") == "push":
                errors.append(f"{name} must not use a push ruleset, free plan rejects it")
        if name in PRIVATE_REPOS and rulesets:
            errors.append(f"{name} is private, free plan returns 403 for rulesets")
        repo_cfg = data.get("repository") or {}
        # Identity only, ADR-0015: a repo file must not set any non-identity repository field, or it can weaken baseline silently.
        for key in repo_cfg.keys():
            if key not in {"name", "description", "homepage", "private", "topics"}:
                errors.append(f"{name} repo file must not set repository field {key}, only identity fields name, description, homepage, private, topics are allowed")
        if name in PRIVATE_REPOS and "allow_forking" in repo_cfg:
            errors.append(f"{name} must not set allow_forking at all, GitHub returns 422 for private repo PATCH when org forbids private forking, live false is via org policy, see ADR-0013")
        # Full tag and Default ruleset checks, ADR-0015.
        for rule in rulesets:
            if rule.get("target") == "tag":
                if rule.get("enforcement") != "active":
                    errors.append(f"{name} tag ruleset {rule.get('name')} enforcement must stay active")
                if rule.get("bypass_actors"):
                    errors.append(f"{name} tag ruleset {rule.get('name')} bypass must stay empty")
                if [r.get("type") for r in (rule.get("rules") or [])] != ["deletion", "non_fast_forward", "update"]:
                    errors.append(f"{name} tag ruleset {rule.get('name')} rules must stay deletion, non_fast_forward, update")
                cond = (rule.get("conditions") or {}).get("ref_name") or {}
                if cond.get("include") not in [["refs/tags/*"], ["refs/tags/v*"]] or cond.get("exclude") != []:
                    errors.append(f"{name} tag ruleset {rule.get('name')} conditions must stay refs/tags/* or refs/tags/v* only")
            if rule.get("name") == "Default":
                if rule.get("target") != "branch" or rule.get("enforcement") != "active" or rule.get("bypass_actors"):
                    errors.append(f"{name} Default ruleset must stay branch, active, bypass empty")
                if [r.get("type") for r in (rule.get("rules") or [])] != ["deletion", "non_fast_forward", "pull_request"]:
                    errors.append(f"{name} Default ruleset rules must stay deletion, non_fast_forward, pull_request")
                pr_rules = [r for r in (rule.get("rules") or []) if r.get("type") == "pull_request"]
                if len(pr_rules) == 1:
                    dparams = pr_rules[0].get("parameters") or {}
                    if dparams.get("allowed_merge_methods") != ["merge", "squash", "rebase"] or dparams.get("required_approving_review_count") != 0:
                        errors.append(f"{name} Default pull_request parameters must stay merge, squash, rebase, count 0")
        for rule in rulesets:
            if rule.get("enforcement") != "active":
                errors.append(f"{name} ruleset {rule.get('name')} enforcement must stay active")
            if rule.get("target") == "branch":
                for b in (rule.get("bypass_actors") or []):
                    if b.get("bypass_mode") == "always":
                        errors.append(f"{name} branch ruleset {rule.get('name')} bypass must not be always")
            if rule.get("target") == "tag" and rule.get("bypass_actors"):
                errors.append(f"{name} tag ruleset {rule.get('name')} bypass must stay empty")
        if "private" in data:
            if name == "service-control-policies" and data["private"] is not True:
                errors.append("service-control-policies must stay private: true")
            if name in PUBLIC_REPOS and data["private"] is not False and data["private"] is not None:
                errors.append(f"{name} is public, private must stay false or unset")
    # Secrets, raw values, never commit them
    for path in sorted(glob.glob("safe-settings/**/*.yml") + glob.glob(".github/workflows/*.yml")):
        text = open(path).read()
        for pattern in [r"PRIVATE_KEY:\s*[^\$\s]", r"BEGIN.*PRIVATE KEY", r"GITHUB_CLIENT_SECRET:\s*[^\$\s]"]:
            if re.search(pattern, text):
                errors.append(f"possible secret value in {path}, use secrets.* reference only")
    # Workflow pins, SHA only, both workflows must match
    pin_re = re.compile(r"ref: ([a-f0-9]{40}) # safe-settings (.*)")
    pins = {}
    for path in [".github/workflows/safe-settings-sync.yml", ".github/workflows/safe-settings-dry-run.yml"]:
        m = pin_re.search(open(path).read())
        if not m:
            errors.append(f"missing safe-settings SHA pin in {path}")
        else:
            pins[path] = (m.group(1), m.group(2))
    if len(set(pins.values())) != 1:
        errors.append(f"safe-settings pins differ: {pins}")
    # Security config, must parse, and must list public repos only, plus private skip
    try:
        sec = json.load(open('security.json'))
        sec_repos = sec.get('repos') or {}
        for name, vals in sec_repos.items():
            if vals.get('private') is True:
                continue
            for key, val in vals.items():
                if val not in ['enabled', 'disabled']:
                    errors.append(f'security.json {name} {key} must be enabled or disabled, got {val}')
    except Exception as e:
        errors.append(f'security.json parse fail: {e}')
    # ADR format, each ADR must hold Status, Date, Context, Decision, Consequences
    for adr in sorted(glob.glob('docs/adrs/0*.md')):
        text = open(adr).read()
        for section in ['Date:', 'Status:', '## Context', '## Decision', '## Consequences']:
            if section not in text:
                errors.append(f'{adr} missing {section}')
    # Renovate-valid action comment, must be # vX or # vX.Y.Z, not # actions/name vX
    for path in sorted(glob.glob('.github/workflows/*.yml')):
        for line in open(path):
            m = re.search(r'uses: .*@([a-f0-9]{40}) #(.*)', line)
            if m and not re.match(r'^v[0-9]+(\.[0-9]+)*$', m.group(2).strip()):
                errors.append(f'{path} action comment must be # vX.Y.Z, got #{m.group(2).strip()}, Renovate ignores other formats')
    # FUNDING, github sponsor must be a real account, not a placeholder
    funding_path = ".github/FUNDING.yml"
    if os.path.exists(funding_path):
        funding = load_yaml(funding_path)
        github_val = funding.get("github")
        if github_val and github_val in ["username", "placeholder", "example"]:
            errors.append("FUNDING.yml github value is a placeholder, use a real account")
    if errors:
        for e in errors:
            print(f"GUARD FAIL: {e}")
        sys.exit(1)
    print("GUARD PASS: all local invariants hold")

def live_rulesets(repo):
    token = os.environ.get("GITHUB_TOKEN")
    req = urllib.request.Request(
        f"https://api.github.com/repos/infralicious/{repo}/rulesets",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "config-guard"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return [r["name"] for r in json.load(resp)]
    except Exception as e:
        print(f"SIMULATE WARN: cannot read live rulesets for {repo}: {e}")
        return None

def merged_rulesets():
    merged = {}
    for sub_path in sorted(glob.glob("safe-settings/suborgs/*.yml")):
        sub_data = load_yaml(sub_path)
        sub_rules = [r.get("name") for r in (sub_data.get("rulesets") or [])]
        for repo in (sub_data.get("suborgrepos") or []):
            merged.setdefault(repo, set()).update(sub_rules)
    for path in glob.glob("safe-settings/repos/*.yml"):
        name = os.path.basename(path)[:-4]
        data = load_yaml(path)
        rules = [r.get("name") for r in (data.get("rulesets") or [])]
        merged.setdefault(name, set()).update(rules)
    return merged

def org_repos():
    token = os.environ.get("GITHUB_TOKEN")
    req = urllib.request.Request(
        "https://api.github.com/orgs/infralicious/repos?per_page=100",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "config-guard"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except Exception as e:
        print(f"SIMULATE WARN: cannot list org repos: {e}")
        return None

def check_simulate():
    merged = merged_rulesets()
    errors = []
    # New repo detection: a new org repo gets baseline only, no Protect main,
    # until it is added to a suborg list. Fail, so it cannot stay unprotected.
    repos = org_repos()
    if repos is not None:
        known = set(PUBLIC_REPOS + PRIVATE_REPOS + RESTRICTED)
        for r in repos:
            name = r["name"]
            if name not in known:
                errors.append(f"org repo {name} is not in config, add it to a suborg list or to restrictedRepos, it gets baseline only today")
            if name in PUBLIC_REPOS and r.get("default_branch") != "main":
                errors.append(f"{name} default branch is {r.get('default_branch')}, not main, next sync would rename it")
            if r.get("archived"):
                errors.append(f"{name} is archived, config should not sync it, remove it from suborg lists")
    for repo in PUBLIC_REPOS:
        want = merged.get(repo, set())
        required = REQUIRED_RULESETS.get(repo, DEFAULT_REQUIRED)
        for name in required:
            if name not in want:
                errors.append(f"{repo} missing required ruleset {name} in PR config")
        live = live_rulesets(repo)
        if live is None:
            continue
        print(f"SIMULATE {repo}: live {sorted(live)}, PR merged {sorted(want)}")
        for name in live:
            if name not in want and name in ["Protect main", "Protect tags", "Tag protection", "Default"]:
                errors.append(f"{repo} would delete live ruleset {name}, add it back or confirm deletion explicitly")
        for name in want:
            if name not in live:
                print(f"SIMULATE {repo}: would create ruleset {name}")
    if errors:
        for e in errors:
            print(f"SIMULATE FAIL: {e}")
        sys.exit(1)
    print("SIMULATE PASS: no required ruleset missing, no protected ruleset deleted")

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["guard", "simulate"]:
        sys.exit("Usage: check-config.py guard|simulate")
    os.chdir(ROOT)
    if sys.argv[1] == "guard":
        check_guard()
    else:
        check_simulate()
