# ADR-0006: Use JavaScript for security script, to match safe-settings

Date: 2026-10-27
Status: Accepted

## Context

Safe-settings is JavaScript, Node >= 22, CommonJS, Standard style, Jest tests.
A security script in Python would need a rewrite, for an upstream PR.
Issue 583 asks for secret scanning support, in safe-settings, open since 2024.

## Decision

Write scripts/security.js in JavaScript, same style as safe-settings.
Mirror a future plugin class, find, changed, update, with dry run mode.
Use JSON config here, no dependency, upstream would use YAML config, same logic.
Add a retire comment, when issue 583 lands in a stable release.

## Consequences

Upstream PR needs mainly a plugin file, a PLUGINS map entry, and tests.
Guard script stays Python, it is admin specific, not an upstream candidate.
JS script needs no npm install, it uses built-in fetch and JSON.parse.

## Alternatives

Python script: faster to write, but rewrite needed for upstream, rejected for this script.
Fork safe-settings: touches everything, drifts from upstream, rejected.
Gomgr: full org manager, two YAML formats, maintenance risk, rejected for now.
