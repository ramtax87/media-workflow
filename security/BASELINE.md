# Security baseline — version 1

Every change enters through a pull request with required security and application
checks. A checksum identifies the tested source; it does not establish that code is
safe. Repository owners must review changes to workflows, permissions and exceptions.

## Before developing

Identify the affected identities, tenant boundaries, data, network entry points and
privileged actions. Use disposable test data. Never put live credentials, customer
data, private connection files or production backups in source control or CI.

## Controls required in new features

- Enforce authentication and per-resource/tenant authorization on the server.
  Deny by default; test a second user and tenant, revoked access and forged roles.
- Parameterize database queries. Validate input size/type; escape output for its
  destination. Cover CSRF for cookie authentication, uploads, paths, SSRF and redirects.
- Treat prompts, retrieved documents and tool output as untrusted data. The model
  cannot grant permissions. Tools require scoped server-side authorization, bounded
  budgets, auditable actions and explicit approval for consequential operations.
- Keep secrets server-side with minimum privilege; use bounded timeouts, queues,
  request sizes and rate limits. Do not log tokens or unnecessary personal data.
- Verify webhooks, reject replay, enforce transaction/idempotency rules and compute
  financial values on the server. Test abuse and concurrency where relevant.
- Pin dependencies and CI actions; use lockfiles. Review updates before merging.

## Required merge evidence

`security-baseline` scans full Git history for secrets and checks dependencies.
Node audits block high/critical advisories, including development dependencies;
moderate findings still require triage. Python audits block all known findings.
Application checks exercise behavior and authorization using disposable data.
Jobs use read-only repository tokens, no production secrets, pinned actions, finite
timeouts and cancellation of superseded runs. Weekly scans catch new advisories.

Only exact historical false-positive fingerprints may be ignored, with explanations
in the ignore file. Never suppress a real exposed secret: rotate it and assess use.
New exceptions need a documented owner, scope, reason, compensating control and expiry.
Do not disable a failing gate just to merge.

## Deployment and incident requirements

Deploy the exact passing revision. Before stateful changes, create and verify a
restorable backup; keep an off-host copy. Verify health and authorization after
deployment and retain a rollback revision. Keep administration and databases private.
Review firewall/access rules, patch status, service identities, exposed ports,
backup restore drills and alert delivery on each actual server separately.

If compromised: restrict the affected access, preserve minimal evidence, revoke
sessions and rotate secrets, fix and restore from verified state, then review impact.
Report vulnerabilities privately to ramtaxdev@gmail.com without live credentials.

This baseline is a starting control, not a penetration-test certificate. Automated
scanning does not prove tenant isolation, prompt safety, recovery or runtime security.
