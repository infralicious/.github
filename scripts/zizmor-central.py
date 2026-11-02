#!/usr/bin/env python3
"""Central zizmor audit, for all org repos, via a GitHub App token.

Usage: python3 scripts/zizmor-central.py [--upload-sarif]
       GITHUB_TOKEN must be set, to an App token, or to a gh token for local test.
       ZIZMOR_BIN may point to a zizmor binary, default is zizmor in PATH.

Model, like safe-settings:
- One workflow in admin repo, on schedule, plus workflow_dispatch.
- Workflow creates an App token, with app-id var and private-key secret.
- Script lists org repos dynamically, via API, no hardcoded repo list.
- Dynamic list matters: a hardcoded list fails for a new repo, see PR 46 bug.
- Script runs zizmor on each repo slug, at default branch, with min-severity medium.
- Audit mode first: script exits 0 always, even with findings, unless --fail-on-high is set.
- SARIF upload is optional, off by default, because it needs security-events write.
- Safe-settings App token does not have security-events write, so upload would fail with that App.
- A new App, infralicious-zizmor, with contents read, metadata read, security-events write, is needed for upload.
- Until that App exists, run report mode only, with findings in log and in summary file.
- Per-repo caller workflows, PR 48, PR 15, PR 5, still provide PR blocking, central audit cannot block a PR in another repo.
- Central audit provides coverage for new repos, and for repos with no PR workflow, on main, on schedule.
"""
import json
import os
import subprocess
import sys
import urllib.request

ORG = "infralicious"
API = "https://api.github.com"

def api_get(path, token):
    req = urllib.request.Request(
        f"{API}{path}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "zizmor-central"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

def main():
    upload = "--upload-sarif" in sys.argv
    fail_high = "--fail-on-high" in sys.argv
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    zizmor = os.path.expanduser(os.environ.get("ZIZMOR_BIN") or "zizmor")
    repos = api_get(f"/orgs/{ORG}/repos?per_page=100", token)
    if repos is None:
        print("ZIZMOR CENTRAL FAIL: cannot list org repos")
        sys.exit(1)
    total_findings = 0
    high_findings = 0
    lines = ["# Central zizmor audit, org infralicious", ""]
    for repo in sorted(repos, key=lambda r: r["name"]):
        name = repo["name"]
        if repo.get("archived"):
            print(f"SKIP {name}: archived")
            lines.append(f"- {name}: skipped, archived")
            continue
        ref = repo.get("default_branch") or "main"
        slug = f"{ORG}/{name}@{ref}"
        # Zizmor binary, remote repo slug, min-severity medium, plain format, no progress.
        # Env GH_TOKEN is used by zizmor for remote repo access, if set.
        env = os.environ.copy()
        if token:
            env["GH_TOKEN"] = token
            env["GITHUB_TOKEN"] = token
        try:
            result = subprocess.run(
                [zizmor, "--format", "plain", "--min-severity", "medium", "--no-progress", slug],
                capture_output=True, text=True, timeout=120, env=env,
            )
            out = (result.stdout + result.stderr).strip()
            # Count findings by audit lines: plain format lines starting with error, warning, help.
            if "no inputs collected" in out:
                print(f"{name}: no workflows to audit, ref {ref}")
                lines.append(f"- {name}: no workflows to audit")
                continue
            count = sum(1 for line in out.splitlines() if line.startswith(("error[", "warning[", "help[")))
            # High findings are error level only, in plain format.
            high = sum(1 for line in out.splitlines() if line.startswith("error["))
            total_findings += count
            high_findings += high
            print(f"{name}: {count} findings, {high} high, ref {ref}")
            if out:
                print(out[:2000])
            lines.append(f"- {name}: {count} findings, {high} high")
            if upload:
                print(f"UPLOAD {name}: SARIF upload not implemented in v1, report only, see script header")
        except Exception as e:
            print(f"ERROR {name}: {e}")
            lines.append(f"- {name}: error, {e}")
    lines.append("")
    lines.append(f"Total findings, medium and above: {total_findings}, high: {high_findings}")
    summary = "\n".join(lines)
    print(summary)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write(summary + "\n")
    if fail_high and high_findings > 0:
        print("ZIZMOR CENTRAL FAIL: high findings found, fail-on-high set")
        sys.exit(1)
    print("ZIZMOR CENTRAL DONE: audit mode, exit 0, findings reported, no live change")

if __name__ == "__main__":
    main()
