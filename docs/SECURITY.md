# Security Runbook

## Implemented Baseline
- Request ID correlation (`X-Request-ID`) and sanitized error envelopes.
- Secure response headers (`HSTS` on HTTPS, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control`).
- Optional CORS allowlist (`CORS_ALLOWED_ORIGINS`).
- Request body size guard (`MAX_REQUEST_BODY_BYTES`).
- Auth/chat write rate limiting with lockout/backoff.
- Refresh-token rotation with replay/reuse detection and deterministic bulk session revocation on compromise signal.
- Short-lived one-time websocket tickets (`POST /auth/ws-ticket`) replacing bearer tokens in websocket query strings.
- User MFA/TOTP APIs (all authenticated accounts) with shorter admin refresh-session TTL policy.
- Secure DB transport default (`DB_SSLMODE=require`).
- Privileged action audit trail (`admin_action_audit`, `publish_drain_events`, `publish_drain_session_audit`).
- Immutable security-event audit trail (`security_event_audit`) for auth/session event telemetry.
- CI security gates (`.github/workflows/security-scan.yml`).

## Secret Management Pattern
- Required for CI deploy/runtime: Secret Manager references in deploy env:
  - `JWT_SECRET_SECRET_REF`
  - `OPS_API_TOKEN_SECRET_REF`
  - `DB_PASSWORD_SECRET_REF`
- Plain env fallback is now local-only and must be explicitly enabled via `ALLOW_PLAIN_ENV_SECRETS=true`.
- CI cloud auth is WIF-only (`GCP_WORKLOAD_IDENTITY_PROVIDER` + `GCP_SERVICE_ACCOUNT`), removing long-lived service-account JSON keys.
- Rotation policy:
  1. create new secret version,
  2. deploy Cloud Run with updated secret ref,
  3. validate auth + ops + DB connectivity,
  4. disable old secret version after confirmation.

## Incident Response
### Account compromise wave
1. Increase auth lockout strictness (`AUTH_*` rate-limit env values).
2. Revoke suspected sessions (`user_sessions.revoked_at`).
3. Monitor `/ops/release/metrics` + auth failure rates.

### Token leakage
1. Rotate `JWT_SECRET` and `OPS_API_TOKEN`.
2. Revoke all sessions (bulk update `user_sessions.revoked_at`).
3. Force update/login gate via release policy activation.

### Refresh token replay detected
1. Inspect `GET /ops/release/security-audit?event_type=refresh_token_reuse_detected`.
2. Confirm automatic bulk revocation (`session_bulk_revocation`) fired for impacted account.
3. Force password reset and investigate associated IP/session timeline.

### Abuse/spam burst
1. Tighten chat rate limits (`CHAT_*` env values).
2. Apply network perimeter controls (Cloud Armor/WAF/IP throttling).
3. Review `admin_action_audit` and request IDs for timeline.

## Perimeter and Infra Recommendations
- Place Cloud Run behind HTTPS Load Balancer + Cloud Armor.
- Restrict unauthenticated access where possible and enforce only required public routes.
- Keep request-size limits and WAF bot/abuse rules enabled.
- Use least-privilege service accounts for deploy/runtime.
- Bootstrap Cloud Armor baseline with:
```bash
PROJECT_ID=<project-id> \
POLICY_NAME=karaxas-backend-policy \
BACKEND_SERVICE=<lb-backend-service> \
backend/scripts/configure_cloud_armor.sh
```

## Audit Retention Guidance
- `admin_action_audit`: keep indefinitely (compliance and rollback forensics).
- `publish_drain_*`: keep indefinitely (release incident traceability).
- `security_event_audit`: keep minimum 180 days hot, archive older rows to cold storage monthly.
- Query interfaces:
  - `GET /ops/release/admin-audit`
  - `GET /ops/release/security-audit`
  - `GET /ops/release/metrics` (`security_events` aggregate counters)
- Optional automated guardrail probe:
  - `backend/scripts/check_ops_metrics_guardrails.sh` (threshold checks for drain failures and auth/rate-limit pressure).

## Security Readiness Checklist
- Security scan workflow passing on `main`.
- No critical untriaged vulnerabilities.
- Secret refs used for production runtime credentials.
- Admin audit log endpoint reachable and monitored.
- Publish-drain and force-update enforcement validated on staging.
- Basic penetration-test checklist executed (auth, websocket, rate-limit, replay, error leakage).
