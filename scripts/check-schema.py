#!/usr/bin/env python3
# Schema discovery check, not full schema validation.
# Full validation is not possible, see header notes below.
# 1. Schema uses key repositories, our YAML uses repository, runtime accepts both.
# 2. Schema does not set additionalProperties false, so typos pass silently.
# 3. Schema covers API fields, not safe-settings only keys like additive_plugins.
# 4. Schema covers security_and_analysis, but safe-settings ignores that field.
# 5. Schema validates one file, not merged org plus suborg plus repo layers.
# So this script does key discovery, not type validation.
# It fails when a schema key is neither active nor mentioned in a comment.
# That forces a decision on a new feature: use it, or comment why not.
# Usage: python3 scripts/check-schema.py
#   --schema-dir DIR reads local schema JSON files, for offline tests.
# Without --schema-dir, it downloads pinned schema from upstream.
# Pin comes from workflow safe-settings ref, never from a hardcoded SHA here.
# That keeps schema version equal to runtime version, by construction.

import argparse
import glob
import json
import re
import sys
import urllib.request

ALIASES = {
    "repositories": "repository",
}

# Safe-settings only keys, not in upstream schema, handled by guard, not by schema.
SAFE_SETTINGS_ONLY = {
    "additive_plugins",
    "disable_plugins",
    "suborgrepos",
    "suborgteams",
    "suborgproperties",
    "restrictedRepos",
}

def safe_settings_sha():
    for path in [
        ".github/workflows/safe-settings-sync.yml",
        ".github/workflows/safe-settings-dry-run.yml",
    ]:
        text = open(path).read()
        match = re.search(r"ref: ([a-f0-9]{40}) # safe-settings (.*)", text)
        if match:
            return match.group(1)
    sys.exit("No safe-settings SHA pin found in workflows")

def load_schema(name, args):
    if args.schema_dir:
        with open(f"{args.schema_dir}/{name}.json") as handle:
            return json.load(handle)
    sha = safe_settings_sha()
    url = (
        "https://raw.githubusercontent.com/github-community-projects/"
        f"safe-settings/{sha}/schema/dereferenced/{name}.json"
    )
    print(f"Download schema: {name} at {sha[:7]}")
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)

def schema_keys(schema):
    keys = set(schema.get("properties", {}).keys())
    repo = schema.get("properties", {}).get("repositories", {})
    repo_fields = set()
    for part in repo.get("allOf", []):
        repo_fields.update(part.get("properties", {}).keys())
    return keys, repo_fields

def config_text():
    text = ""
    for path in sorted(glob.glob("safe-settings/**/*.yml", recursive=True)):
        text += open(path).read() + "\n"
    return text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema-dir", default=None)
    args = parser.parse_args()
    text = config_text()
    errors = []
    for name in ["settings", "suborgs", "repos"]:
        schema = load_schema(name, args)
        keys, repo_fields = schema_keys(schema)
        for key in sorted(keys):
            yaml_key = ALIASES.get(key, key)
            # Active key: a top-level YAML key, or a comment mention, counts as documented.
            if re.search(rf"(?m)^[# ]*{re.escape(yaml_key)}:", text):
                continue
            if re.search(rf"(?m)^[# ]*{re.escape(key)}:", text):
                continue
            errors.append(f"{name} schema key {key} is neither active nor commented")
        if name == "settings":
            for field in sorted(repo_fields):
                if field in SAFE_SETTINGS_ONLY:
                    continue
                if re.search(rf"(?m)^[# ]*{re.escape(field)}:", text):
                    continue
                # security field in our YAML is named security, not security_and_analysis.
                if field == "security_and_analysis" and re.search(
                    r"(?m)^[# ]*security_and_analysis:", text
                ):
                    continue
                errors.append(f"settings repository field {field} is neither active nor commented")
    if errors:
        for error in errors:
            print(f"SCHEMA FAIL: {error}")
        sys.exit(1)
    print("SCHEMA PASS: all schema keys are active or commented")

if __name__ == "__main__":
    main()
