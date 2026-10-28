// Security and analysis script, in safe-settings style.
// Language: JavaScript, Node >= 22, CommonJS, Standard style.
// No semicolons, 2 space indent, single quotes, like safe-settings.
// This file mirrors a future safe-settings plugin, to ease an upstream PR.
// Upstream issue: github-community-projects/safe-settings #583, open, dormant.
// Retire this script when issue 583 lands in a stable safe-settings release.
// Then move security_and_analysis into safe-settings YAML, and delete this file.
// Upstream mapping, for a future PR:
// - Upstream config key: security_and_analysis, in settings.yml, parsed by js-yaml.
// - Here config file: security.json, parsed by JSON.parse, no dependency.
// - Upstream plugin class: lib/plugins/security.js, with find, changed, update.
// - Here class: SecurityAndAnalysis, with find, changed, update, same shape.
// - Upstream apply: Octokit, github.rest.repos.update, with security_and_analysis.
// - Here apply: fetch, PATCH /repos/{owner}/{repo}, with security_and_analysis.
// - Upstream dry run: NopCommand, in nop mode, no live change.
// - Here dry run: log planned change, no PATCH, exit 1 on drift, exit 0 on match.
// - Safe-settings ignores security_and_analysis today, in ignorableFields.
// - So this script will not fight safe-settings, fields are disjoint.
// - Private repos: secret scanning is not available on free plan, skip, warn, do not fail.
// Token note: use an App installation token, not a plain GITHUB_TOKEN.
// Plain GITHUB_TOKEN, contents read, sees security_and_analysis as disabled.
// App token, administration write, sees the true live status, verified 2026-10-27.
// Usage, dry run only, in this PR:
//   GITHUB_TOKEN=... node scripts/security.js --dry-run
// Apply mode exists in code, but no workflow calls it yet, review it first.
//   GITHUB_TOKEN=... node scripts/security.js --apply

const fs = require('node:fs')
const path = require('node:path')

const ORG = 'infralicious'
const API = 'https://api.github.com'

class SecurityAndAnalysis {
  constructor (nop, repo, entries, log) {
    this.nop = nop
    this.repo = repo
    this.entries = entries
    this.log = log
  }

  async find (token) {
    const res = await fetch(`${API}/repos/${ORG}/${this.repo}`, {
      headers: { Accept: 'application/vnd.github+json', Authorization: `Bearer ${token}`, 'User-Agent': 'security-script' }
    })
    if (!res.ok) {
      throw new Error(`GET repo ${this.repo} failed: ${res.status}`)
    }
    const data = await res.json()
    return data.security_and_analysis || {}
  }

  changed (existing, desired) {
    const out = {}
    for (const key of Object.keys(desired)) {
      const want = desired[key]
      const have = existing[key] ? existing[key].status : 'disabled'
      if (have !== want) {
        out[key] = { have, want }
      }
    }
    return out
  }

  toStatusObjects (desired) {
    const out = {}
    for (const key of Object.keys(desired)) {
      out[key] = { status: desired[key] }
    }
    return out
  }

  async update (token, desired) {
    if (this.nop) {
      this.log(`DRY RUN ${this.repo}: would PATCH security_and_analysis ${JSON.stringify(desired)}`)
      return
    }
    const res = await fetch(`${API}/repos/${ORG}/${this.repo}`, {
      method: 'PATCH',
      headers: { Accept: 'application/vnd.github+json', Authorization: `Bearer ${token}`, 'User-Agent': 'security-script', 'Content-Type': 'application/json' },
      body: JSON.stringify({ security_and_analysis: this.toStatusObjects(desired) })
    })
    if (!res.ok) {
      const body = await res.text()
      throw new Error(`PATCH repo ${this.repo} failed: ${res.status} ${body}`)
    }
    this.log(`APPLIED ${this.repo}: security_and_analysis ${JSON.stringify(desired)}`)
  }

  async sync (token) {
    const existing = await this.find(token)
    const diff = this.changed(existing, this.entries)
    if (Object.keys(diff).length === 0) {
      this.log(`OK ${this.repo}: security settings match desired`)
      return false
    }
    this.log(`DRIFT ${this.repo}: ${JSON.stringify(diff)}`)
    await this.update(token, this.entries)
    return true
  }
}

async function main () {
  const args = process.argv.slice(2)
  const nop = !args.includes('--apply')
  const token = process.env.GITHUB_TOKEN
  if (!token) {
    console.error('GITHUB_TOKEN is required')
    process.exit(1)
  }
  const configPath = path.join(__dirname, '..', 'security.json')
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'))
  const repos = config.repos || {}
  let drift = false
  for (const repo of Object.keys(repos).sort()) {
    const entries = repos[repo]
    if (entries.private === true) {
      console.log(`SKIP ${repo}: private repo, secret scanning not available on free plan`)
      continue
    }
    const desired = {}
    for (const key of Object.keys(entries)) {
      if (key !== 'private') {
        desired[key] = entries[key]
      }
    }
    const plugin = new SecurityAndAnalysis(nop, repo, desired, console.log)
    try {
      const changed = await plugin.sync(token)
      if (changed) {
        drift = true
      }
    } catch (e) {
      console.error(`ERROR ${repo}: ${e.message}`)
      process.exit(1)
    }
  }
  if (nop && drift) {
    console.log('DRY RUN: drift found, no live change made, exit 1')
    process.exit(1)
  }
  console.log(nop ? 'DRY RUN: no drift, no live change made' : 'APPLY: done')
}

if (require.main === module) {
  main()
}

module.exports = SecurityAndAnalysis
