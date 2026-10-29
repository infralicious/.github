#!/usr/bin/env python3
"""Check GitHub App permissions against manifest files.

Usage: python3 scripts/check-apps.py
       python3 scripts/check-apps.py --apps-dir apps
       python3 scripts/check-apps.py --apps-dir /tmp/test-apps

The check reads every JSON file in the apps directory.
Each file name must match the App slug, in the name field.
The check fetches the live App, by slug, from the public API.
The check compares live permissions to default_permissions.
The check compares live events to default_events.
The check never applies a change, it only reports drift.
The check needs GITHUB_TOKEN, because both Apps are private.
Unauthenticated calls return 404 for private Apps, not drift.
The check never prints a token, a key, or a secret.
Exit 0 when every App matches its manifest.
Exit 1 when any App drifts, or any fetch fails.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_VERSION = "2022-11-28"


def fetch_app(slug, api_base, token):
    """Fetch one live App, by slug, from the GitHub API."""
    url = api_base.rstrip("/") + "/apps/" + slug
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", API_VERSION)
    request.add_header("User-Agent", "infralicious-app-drift-check")
    if token:
        request.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def compare_app(path, api_base, token):
    """Compare one manifest file to its live App. Return True on match."""
    with open(path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    slug = manifest.get("name")
    if not slug:
        print(f"FAIL: {path} has no name field")
        return False
    expected_permissions = manifest.get("default_permissions")
    expected_events = manifest.get("default_events")
    if not isinstance(expected_permissions, dict):
        print(f"FAIL: {slug} has no default_permissions object")
        return False
    if not isinstance(expected_events, list):
        print(f"FAIL: {slug} has no default_events list")
        return False
    try:
        live = fetch_app(slug, api_base, token)
    except urllib.error.HTTPError as error:
        print(f"FAIL: {slug} fetch failed with HTTP {error.code}")
        return False
    except urllib.error.URLError as error:
        print(f"FAIL: {slug} fetch failed: {error.reason}")
        return False
    live_permissions = live.get("permissions", {})
    live_events = live.get("events", [])
    failed = False
    missing = sorted(set(expected_permissions) - set(live_permissions))
    extra = sorted(set(live_permissions) - set(expected_permissions))
    changed = sorted(
        key
        for key in expected_permissions
        if key in live_permissions and live_permissions[key] != expected_permissions[key]
    )
    if missing:
        print(f"FAIL: {slug} missing permissions: {', '.join(missing)}")
        failed = True
    if extra:
        print(f"FAIL: {slug} extra permissions: {', '.join(extra)}")
        failed = True
    for key in changed:
        print(
            f"FAIL: {slug} permission {key} is {live_permissions[key]}, "
            f"manifest says {expected_permissions[key]}"
        )
        failed = True
    if sorted(live_events) != sorted(expected_events):
        print(
            f"FAIL: {slug} events are {sorted(live_events)}, "
            f"manifest says {sorted(expected_events)}"
        )
        failed = True
    if failed:
        return False
    print(f"PASS: {slug}")
    return True


def main():
    """Run the drift check for every manifest file."""
    parser = argparse.ArgumentParser(description="Check GitHub App drift.")
    parser.add_argument(
        "--apps-dir",
        default=os.path.join(ROOT, "apps"),
        help="Directory with App manifest JSON files.",
    )
    parser.add_argument(
        "--api-base",
        default="https://api.github.com",
        help="GitHub API base URL.",
    )
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("FAIL: GITHUB_TOKEN is not set, private Apps need a token")
        return 1
    paths = sorted(
        path
        for path in os.listdir(args.apps_dir)
        if path.endswith(".json")
    )
    if not paths:
        print(f"FAIL: no manifest files in {args.apps_dir}")
        return 1
    ok = True
    for name in paths:
        path = os.path.join(args.apps_dir, name)
        if not compare_app(path, args.api_base, token):
            ok = False
    if not ok:
        print("Drift found. Fix the live App, or fix the manifest, then re-run.")
        return 1
    print(f"All {len(paths)} Apps match their manifests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
