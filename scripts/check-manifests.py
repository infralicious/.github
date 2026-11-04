#!/usr/bin/env python3
"""Lint GitHub App manifest files, no dependency, no network.

Usage: python3 scripts/check-manifests.py [--apps-dir apps]
       python3 scripts/check-manifests.py --fail-on-warning

Rules, ERROR fails the run, WARN does not fail by default:
- E01: file is not valid JSON.
- E02: file is not a JSON object.
- E03: name is missing, or name does not match infralicious prefix.
- E04: url is missing, or url is not an infralicious GitHub URL.
- E05: redirect_url is missing, or redirect_url does not equal url.
- E06: public is missing, or public is not false.
- E07: default_permissions is missing, empty, or not an object.
- E08: permission name is unknown to this linter.
- E09: permission value is not read or write.
- E10: default_events is missing, or not a list.
- E11: hook_attributes is present, but hook_attributes url is missing.
- E12: hook_attributes url is present, but url is not https.
- E13: events are present, but no webhook url is present.
- E14: description is missing, or description is empty.
- E15: file name does not match manifest name.
- W01: a write permission is present, review it.
- W02: hook_attributes is present, prefer omit for Action Apps.
- W03: administration write is present, review it.
- W04: workflows write is present, review it.
- W05: metadata read is missing, add it.

GitHub has no official manifest linter, so this script is the linter.
GitHub requires hook_attributes url when hook_attributes is present.
GitHub rejects a manifest with hook_attributes active false and no url.
Action Apps in this org use no webhook, so omit hook_attributes.
Linter skips inventory.json, inventory is not a manifest.
Inventory is checked by check-app-inventory.py, not by this linter.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME_RE = re.compile(r"^infralicious-[a-z0-9-]+$")
URL_PREFIX = "https://github.com/infralicious/"
KNOWN_PERMISSIONS = {
    "actions",
    "administration",
    "attestations",
    "checks",
    "code_scanning_alerts",
    "codespaces",
    "codespaces_metadata",
    "contents",
    "dependabot_secrets",
    "deployments",
    "discussions",
    "emails",
    "environments",
    "followers",
    "gists",
    "git_ssh_keys",
    "gpg_keys",
    "interaction_limits",
    "issues",
    "keys",
    "members",
    "metadata",
    "organization_administration",
    "organization_copilot_seat_management",
    "organization_custom_org_roles",
    "organization_custom_properties",
    "organization_events",
    "organization_hooks",
    "organization_packages",
    "organization_personal_access_token_requests",
    "organization_personal_access_tokens",
    "organization_plan",
    "organization_projects",
    "organization_secrets",
    "organization_self_hosted_runners",
    "organization_user_blocking",
    "packages",
    "pages",
    "plan",
    "profile",
    "projects",
    "pull_requests",
    "repository_hooks",
    "repository_projects",
    "repository_custom_properties",
    "secret_scanning_alerts",
    "security_events",
    "single_file",
    "starring",
    "statuses",
    "team_discussions",
    "vulnerability_alerts",
    "workflows",
    "watchers",
}


def lint_manifest(path):
    """Lint one manifest file. Return a list of (level, code, message)."""
    issues = []
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        with open(path, encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, ValueError) as error:
        return [("ERROR", "E01", f"{path} is not valid JSON: {error}")]
    if not isinstance(manifest, dict):
        return [("ERROR", "E02", f"{path} is not a JSON object")]
    manifest_name = manifest.get("name")
    if not isinstance(manifest_name, str) or not NAME_RE.match(manifest_name):
        issues.append(("ERROR", "E03", "name is missing, or name does not match infralicious prefix"))
    url = manifest.get("url")
    if not isinstance(url, str) or not url.startswith(URL_PREFIX):
        issues.append(("ERROR", "E04", "url is missing, or url is not an infralicious GitHub URL"))
    redirect_url = manifest.get("redirect_url")
    if not isinstance(redirect_url, str) or redirect_url != url:
        issues.append(("ERROR", "E05", "redirect_url is missing, or redirect_url does not equal url"))
    if manifest.get("public") is not False:
        issues.append(("ERROR", "E06", "public is missing, or public is not false"))
    permissions = manifest.get("default_permissions")
    if not isinstance(permissions, dict) or not permissions:
        issues.append(("ERROR", "E07", "default_permissions is missing, empty, or not an object"))
        permissions = {}
    for key, value in permissions.items():
        if key not in KNOWN_PERMISSIONS:
            issues.append(("ERROR", "E08", f"permission name is unknown: {key}"))
        if value not in ("read", "write"):
            issues.append(("ERROR", "E09", f"permission value is not read or write: {key}"))
        if value == "write":
            issues.append(("WARN", "W01", f"write permission is present, review it: {key}"))
    if permissions.get("administration") == "write":
        issues.append(("WARN", "W03", "administration write is present, review it"))
    if permissions.get("workflows") == "write":
        issues.append(("WARN", "W04", "workflows write is present, review it"))
    if permissions.get("metadata") != "read":
        issues.append(("WARN", "W05", "metadata read is missing, add it"))
    events = manifest.get("default_events")
    if not isinstance(events, list):
        issues.append(("ERROR", "E10", "default_events is missing, or not a list"))
        events = []
    hook = manifest.get("hook_attributes")
    hook_url = None
    if hook is not None:
        issues.append(("WARN", "W02", "hook_attributes is present, prefer omit for Action Apps"))
        if not isinstance(hook, dict):
            issues.append(("ERROR", "E11", "hook_attributes is present, but hook_attributes is not an object"))
        else:
            hook_url = hook.get("url")
            if not hook_url:
                issues.append(("ERROR", "E11", "hook_attributes is present, but hook_attributes url is missing"))
            elif not isinstance(hook_url, str) or not hook_url.startswith("https://"):
                issues.append(("ERROR", "E12", "hook_attributes url is present, but url is not https"))
    if events and not hook_url:
        issues.append(("ERROR", "E13", "events are present, but no webhook url is present"))
    description = manifest.get("description")
    if not isinstance(description, str) or not description.strip():
        issues.append(("ERROR", "E14", "description is missing, or description is empty"))
    if isinstance(manifest_name, str) and manifest_name != name:
        issues.append(("ERROR", "E15", "file name does not match manifest name"))
    return issues


def main(argv=None):
    """Lint every manifest file in the apps directory."""
    argv = list(sys.argv[1:] if argv is None else argv)
    apps_dir = os.path.join(ROOT, "apps")
    fail_on_warning = False
    for arg in argv:
        if arg == "--fail-on-warning":
            fail_on_warning = True
        elif arg.startswith("--apps-dir="):
            apps_dir = arg.split("=", 1)[1]
        elif arg in ("-h", "--help"):
            print("Usage: python3 scripts/check-manifests.py [--apps-dir apps] [--fail-on-warning]")
            return 0
    try:
        names = sorted(path for path in os.listdir(apps_dir) if path.endswith(".json") and path != "inventory.json")
    except OSError as error:
        print(f"ERROR: cannot list {apps_dir}: {error}")
        return 1
    if not names:
        print(f"ERROR: no manifest files in {apps_dir}")
        return 1
    errors = 0
    warnings = 0
    for name in names:
        path = os.path.join(apps_dir, name)
        for level, code, message in lint_manifest(path):
            print(f"{level} {code} {name}: {message}")
            if level == "ERROR":
                errors += 1
            else:
                warnings += 1
    print(f"Lint done: {len(names)} manifests, {errors} errors, {warnings} warnings")
    if errors or (fail_on_warning and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
