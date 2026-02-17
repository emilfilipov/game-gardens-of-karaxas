# Security Runbook

## Implemented Baseline
- Request ID correlation (`X-Request-ID`) and sanitized error envelopes.
- Secure response headers (`HSTS` on HTTPS, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control`).
- Optional CORS allowlist (`CORS_ALLOWED_ORIGINS`).
- Request body size guard (`MAX_REQUEST_BODY_BYTES`).
- Auth/chat write rate limiting with lockout/backoff.
- Short-lived one-time websocket tickets (`POST /auth/ws-ticket`) replacing bearer tokens in websocket query strings.
- Secure DB transport default (`DB_SSLMODE=require`).
- Privileged action audit trail (`admin_action_audit`, `publish_drain_events`, `publish_drain_session_audit`).
- CI security gates (`.github/workflows/security-scan.yml`).

## Secret Management Pattern
- Preferred: Secret Manager references in deploy env:
  - `JWT_SECRET_SECRET_REF`
  - `OPS_API_TOKEN_SECRET_REF`
  - `DB_PASSWORD_SECRET_REF`
- Fallback (non-production): plain env vars (`JWT_SECRET`, `OPS_API_TOKEN`, `DB_PASSWORD`).
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

### Abuse/spam burst
1. Tighten chat rate limits (`CHAT_*` env values).
2. Apply network perimeter controls (Cloud Armor/WAF/IP throttling).
3. Review `admin_action_audit` and request IDs for timeline.

## Perimeter and Infra Recommendations
- Place Cloud Run behind HTTPS Load Balancer + Cloud Armor.
- Restrict unauthenticated access where possible and enforce only required public routes.
- Keep request-size limits and WAF bot/abuse rules enabled.
- Use least-privilege service accounts for deploy/runtime.

## Security Readiness Checklist
- Security scan workflow passing on `main`.
- No critical untriaged vulnerabilities.
- Secret refs used for production runtime credentials.
- Admin audit log endpoint reachable and monitored.
- Publish-drain and force-update enforcement validated on staging.
- Basic penetration-test checklist executed (auth, websocket, rate-limit, replay, error leakage).
