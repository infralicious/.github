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
    "infralicious.github.io",
    "renovate-config",
    "saas-auth-wall-of-shame",
    "terraform-aws-securityhub-batchupdatefindings",
]
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
    # Suborg lists, exact, private must never enter public
    public = load_yaml("safe-settings/suborgs/public.yml")
    public_repos = public.get("suborgrepos") or []
    if sorted(public_repos) != sorted(PUBLIC_REPOS):
        errors.append(f"public suborgrepos must be exactly {PUBLIC_REPOS}, got {public_repos}")
    if "rulesets" in public and public["rulesets"] is None:
        errors.append("public suborg rulesets must not be null")
    private = load_yaml("safe-settings/suborgs/private.yml")
    if sorted(private.get("suborgrepos") or []) != sorted(PRIVATE_REPOS):
        errors.append(f"private suborgrepos must be exactly {PRIVATE_REPOS}")
    for key in ["branches", "rulesets"]:
        if key in private and private[key] is not None:
            errors.append(f"private suborg must not set {key}, free plan returns 403")
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
    public = load_yaml("safe-settings/suborgs/public.yml")
    public_rules = [r.get("name") for r in (public.get("rulesets") or [])]
    for repo in PUBLIC_REPOS:
        merged[repo] = set(public_rules)
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
