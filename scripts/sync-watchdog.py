#!/usr/bin/env python3
"""Check last successful Safe Settings Sync run, open an issue if missing.

No external deps. Uses gh CLI, with GITHUB_TOKEN, or gh auth.
Exit 0 if sync is fresh, or if an issue already exists.
Exit 0 also on dry run, with a message, no issue opened.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "infralicious/.github")
MAX_AGE_HOURS = int(os.environ.get("MAX_AGE_HOURS", "8"))
DRY_RUN = os.environ.get("DRY_RUN", "") == "true"


def gh(*args):
    out = subprocess.check_output(["gh", "api", *args], text=True)
    return json.loads(out) if out.strip() else None


def main():
    runs = gh(f"repos/{REPO}/actions/workflows/397443686/runs?per_page=20&status=completed")
    last = None
    for r in runs.get("workflow_runs", []):
        if r.get("conclusion") == "success":
            last = r
            break
    if not last:
        print("No successful sync run found")
        age = 999
        run_id = "none"
    else:
        run_id = str(last["id"])
        created = datetime.fromisoformat(last["created_at"].replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - created).total_seconds() / 3600
        print(f"Last successful sync: run {run_id}, {last['created_at']}, age {age:.1f}h")
    if age <= MAX_AGE_HOURS:
        print("Sync is fresh, no issue needed")
        return 0
    title = "Safe Settings Sync missing: no successful run in 8 hours"
    issues = gh(f"repos/{REPO}/issues?state=open")
    for i in issues:
        if i.get("title") == title:
            print(f"Issue already open: {i['number']}, skip duplicate")
            return 0
    body = (
        f"No successful Safe Settings Sync run in {MAX_AGE_HOURS} hours. "
        f"Last successful run: {run_id}. "
        "Scheduled sync may have been delayed or dropped by GitHub, see issue 52. "
        "Dispatch a live sync by hand, verify live, then close this issue after a successful sync."
    )
    if DRY_RUN:
        print(f"DRY RUN: would open issue: {title}")
        print(body)
        return 0
    out = subprocess.check_output(
        ["gh", "api", "-X", "POST", f"repos/{REPO}/issues", "-f", f"title={title}", "-f", f"body={body}"],
        text=True,
    )
    print(f"Opened issue: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
