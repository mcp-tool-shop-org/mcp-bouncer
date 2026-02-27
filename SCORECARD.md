# Scorecard

> Score a repo before remediation. Fill this out first, then use SHIP_GATE.md to fix.

**Repo:** mcp-bouncer
**Date:** 2026-02-27
**Type tags:** [pypi] [cli]

## Pre-Remediation Assessment

| Category | Score | Notes |
|----------|-------|-------|
| A. Security | 7/10 | No SECURITY.md, no threat model in README |
| B. Error Handling | 8/10 | Structured results, but no formal error shape docs |
| C. Operator Docs | 7/10 | README good, but no CHANGELOG, no coverage badge |
| D. Shipping Hygiene | 5/10 | CI exists but no coverage, no dep-audit, no verify, lint has continue-on-error |
| E. Identity (soft) | 10/10 | Logo, translations, landing page |
| **Overall** | **37/50** | |

## Key Gaps

1. No SECURITY.md or data scope documentation
2. No CHANGELOG.md
3. No verify script, no coverage in CI, no dep-audit
4. CI lint/typecheck had continue-on-error (not enforced)
5. No Codecov badge

## Remediation Priority

| Priority | Item | Estimated effort |
|----------|------|-----------------|
| 1 | Add SECURITY.md + README data scope | 5 min |
| 2 | Add CHANGELOG.md | 3 min |
| 3 | Add coverage, dep-audit, verify, fix CI | 5 min |

## Post-Remediation

| Category | Before | After |
|----------|--------|-------|
| A. Security | 7/10 | 10/10 |
| B. Error Handling | 8/10 | 10/10 |
| C. Operator Docs | 7/10 | 10/10 |
| D. Shipping Hygiene | 5/10 | 10/10 |
| E. Identity (soft) | 10/10 | 10/10 |
| **Overall** | 37/50 | 50/50 |
