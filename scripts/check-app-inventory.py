#!/usr/bin/env python3
"""Check org App installations against inventory, no dependency.

Usage, local, with org owner token:
  GITHUB_TOKEN=<token> python3 scripts/check-app-inventory.py

Usage, CI, with workflow token:
  GITHUB_TOKEN=<token> python3 scripts/check-app-inventory.py
  CI token may return 403, then check skips, it does not fail.
  Local run with org owner token is authoritative, CI run is advisory.

Inventory file is apps/inventory.json, one entry per installed App.
Inventory covers org installations only, not repo-only installs.
Repo-only installs need App JWT to list, and third-party keys are not here.
Inventory scope values are org, selected, and repo.
Scope org means all repos, with repository_selection all.
Scope selected means listed repos, with repository_selection selected.
Scope repo means one repo, with repository_selection selected and one repo listed.
Inventory permissions are granted installation permissions, not requested App permissions.
For owned Apps, inventory permissions must match manifest permissions.
For third-party Apps, inventory permissions are live granted permissions at codification time.
Check fails on unknown App, missing App, scope mismatch, permission mismatch, or event mismatch.
Check warns on installation_id mismatch, reinstall gives a new installation_id.
Check never changes a live App, it only reports drift.
Check never prints a token, a key, a JWT, or a secret.
"""
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_BASE = "https://api.github.com"
ORG = "infralicious"


def load_inventory(path):
    """Load inventory file. Return list of App entries, or None on error."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as error:
        print(f"FAIL: inventory cannot be read as JSON: {error}")
        return None
    if not isinstance(data, dict) or not isinstance(data.get("apps"), list):
        print("FAIL: inventory is not an object with an apps list")
        return None
    return data["apps"]


def validate_inventory(apps):
    """Validate inventory schema. Return list of error messages."""
    errors = []
    slugs = []
    for entry in apps:
        if not isinstance(entry, dict):
            errors.append("inventory entry is not an object")
            continue
        slug = entry.get("slug")
        if not slug:
            errors.append("inventory entry has no slug")
            continue
        slugs.append(slug)
        for field in ("app_id", "installation_id", "owner_type", "source", "scope", "repository_selection", "repositories", "permissions", "events", "purpose"):
            if field not in entry:
                errors.append(f"{slug} is missing field {field}")
        if entry.get("scope") not in ("org", "selected", "repo"):
            errors.append(f"{slug} scope is not org, selected, or repo")
        if entry.get("repository_selection") not in ("all", "selected"):
            errors.append(f"{slug} repository_selection is not all or selected")
        if entry.get("scope") == "org" and entry.get("repository_selection") != "all":
            errors.append(f"{slug} scope org needs repository_selection all")
        if entry.get("scope") == "repo" and len(entry.get("repositories", [])) != 1:
            errors.append(f"{slug} scope repo needs exactly one repository listed")
        if not isinstance(entry.get("permissions"), dict):
            errors.append(f"{slug} permissions is not an object")
        if not isinstance(entry.get("events"), list):
            errors.append(f"{slug} events is not a list")
    if len(slugs) != len(set(slugs)):
        errors.append("inventory has duplicate slugs")
    return errors


def compare_live_to_inventory(live, apps):
    """Compare live installations to inventory. Return (errors, warnings)."""
    errors = []
    warnings = []
    inventory = {entry["slug"]: entry for entry in apps if isinstance(entry, dict) and entry.get("slug")}
    live_slugs = set()
    for item in live:
        if not isinstance(item, dict):
            continue
        slug = item.get("app_slug")
        if not slug:
            continue
        live_slugs.add(slug)
        if slug not in inventory:
            errors.append(f"UNKNOWN App installed, not in inventory: {slug}, scope {item.get('repository_selection')}")
            continue
        entry = inventory[slug]
        if item.get("app_id") != entry.get("app_id"):
            errors.append(f"{slug} app_id is {item.get('app_id')}, inventory says {entry.get('app_id')}")
        live_installation_id = item.get("installation_id") or item.get("id")
        if live_installation_id != entry.get("installation_id"):
            warnings.append(f"{slug} installation_id is {live_installation_id}, inventory says {entry.get('installation_id')}, reinstall may explain it")
        if item.get("repository_selection") != entry.get("repository_selection"):
            errors.append(f"{slug} repository_selection is {item.get('repository_selection')}, inventory says {entry.get('repository_selection')}")
        if (item.get("permissions") or {}) != (entry.get("permissions") or {}):
            errors.append(f"{slug} permissions differ from inventory, check live install and inventory")
        if sorted(item.get("events") or []) != sorted(entry.get("events") or []):
            errors.append(f"{slug} events differ from inventory, check live install and inventory")
    for slug in sorted(set(inventory) - live_slugs):
        errors.append(f"MISSING App in inventory, not installed: {slug}, update inventory if uninstall was intentional")
    return errors, warnings


def check_manifest_sync(apps, apps_dir):
    """Check owned App inventory permissions match manifest permissions."""
    errors = []
    for entry in apps:
        if entry.get("source") != "manifest":
            continue
        slug = entry.get("slug")
        path = os.path.join(apps_dir, slug + ".json")
        try:
            with open(path, encoding="utf-8") as handle:
                manifest = json.load(handle)
        except (OSError, ValueError) as error:
            errors.append(f"{slug} manifest cannot be read: {error}")
            continue
        if manifest.get("default_permissions") != entry.get("permissions"):
            errors.append(f"{slug} inventory permissions differ from manifest permissions")
        if manifest.get("default_events") != entry.get("events"):
            errors.append(f"{slug} inventory events differ from manifest events")
    return errors


def fetch_live_installations(token, org=ORG, api_base=API_BASE):
    """Fetch org installations. Return (live list, error code or None)."""
    live = []
    page = 1
    while True:
        url = f"{api_base.rstrip('/')}/orgs/{org}/installations?per_page=100&page={page}"
        request = urllib.request.Request(url)
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("User-Agent", "app-inventory-check")
        request.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return None, error.code
        except (urllib.error.URLError, ValueError):
            return None, 0
        items = data.get("installations", []) if isinstance(data, dict) else []
        live.extend(items)
        if len(items) < 100:
            break
        page += 1
    return live, None


def main():
    """Run inventory check, skip on token error, fail on drift."""
    inventory_path = os.path.join(ROOT, "apps", "inventory.json")
    apps_dir = os.path.join(ROOT, "apps")
    apps = load_inventory(inventory_path)
    if apps is None:
        return 1
    schema_errors = validate_inventory(apps)
    if schema_errors:
        for message in schema_errors:
            print(f"FAIL: {message}")
        return 1
    manifest_errors = check_manifest_sync(apps, apps_dir)
    if manifest_errors:
        for message in manifest_errors:
            print(f"FAIL: {message}")
        return 1
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("SKIP: GITHUB_TOKEN is not set, cannot list installations, run locally with org owner token")
        return 0
    live, error_code = fetch_live_installations(token)
    if live is None:
        if error_code in (401, 403):
            print(f"SKIP: cannot list installations with this token, HTTP {error_code}, run locally with org owner token")
            return 0
        print(f"FAIL: cannot list installations, HTTP {error_code}")
        return 1
    errors, warnings = compare_live_to_inventory(live, apps)
    for message in warnings:
        print(f"WARN: {message}")
    for message in errors:
        print(f"FAIL: {message}")
    if errors:
        print("Inventory drift found. Review new App, update inventory in a pull request, or uninstall App.")
        return 1
    print(f"Inventory pass: {len(live)} live Apps match inventory, {len(warnings)} warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
