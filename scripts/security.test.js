// Tests for scripts/security.js, Node built-in test runner, no dependency.
// Run: node --test scripts/security.test.js
// Upstream PR would move these tests to test/unit, with Jest, same cases.

const test = require('node:test')
const assert = require('node:assert')
const SecurityAndAnalysis = require('./security')

test('changed returns empty when live matches desired', () => {
  const plugin = new SecurityAndAnalysis(true, 'test-repo', {}, console.log)
  const existing = { secret_scanning: { status: 'enabled' }, secret_scanning_push_protection: { status: 'enabled' } }
  const desired = { secret_scanning: 'enabled', secret_scanning_push_protection: 'enabled' }
  assert.deepEqual(plugin.changed(existing, desired), {})
})

test('changed reports drift with have and want', () => {
  const plugin = new SecurityAndAnalysis(true, 'test-repo', {}, console.log)
  const existing = { secret_scanning: { status: 'disabled' } }
  const desired = { secret_scanning: 'enabled' }
  assert.deepEqual(plugin.changed(existing, desired), { secret_scanning: { have: 'disabled', want: 'enabled' } })
})

test('changed treats missing live field as disabled', () => {
  const plugin = new SecurityAndAnalysis(true, 'test-repo', {}, console.log)
  const existing = {}
  const desired = { secret_scanning_push_protection: 'enabled' }
  assert.deepEqual(plugin.changed(existing, desired), { secret_scanning_push_protection: { have: 'disabled', want: 'enabled' } })
})

test('toStatusObjects converts strings to status objects', () => {
  const plugin = new SecurityAndAnalysis(true, 'test-repo', {}, console.log)
  assert.deepEqual(plugin.toStatusObjects({ secret_scanning: 'enabled' }), { secret_scanning: { status: 'enabled' } })
})
