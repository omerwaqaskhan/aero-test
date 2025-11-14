# WindWays Multi-Tenant Authentication Phase — Reusable Module Specification

> Branch: `auth-implementation`  •  Goal: Deliver a production-grade, reusable, multi-tenant authentication and authorization module for the WindWays travel platform with robust error handling, security, and coding standards (clean architecture, loose coupling) that can be dropped into other projects as-is.

---

## 1. Scope & Objectives

- Build a self-contained authentication subsystem with multi-tenancy, RBAC/ABAC-ready authorization, and comprehensive security controls.
- Provide consistent success and error response contracts, covering edge cases and failure modes explicitly.
- Offer a clean, loosely coupled architecture: DI-friendly services, repository pattern, adapters for I/O concerns, and clear module boundaries.
- Ship as a reusable package (library-first), plus a reference FastAPI service façade and OpenAPI docs.

### Non-Goals (for this phase)
- Full business domain integration (search, booking, payments). Only the auth/tenant/user domain is in scope.
- Advanced analytics dashboards or BI. Provide basic metrics only.

---

## 2. Architecture & Design Principles

- Clean Architecture layering: API (FastAPI routers) → Application Services → Domain → Infrastructure (DB, cache, email, SMS, OAuth).
- Loose coupling via interfaces/protocols and dependency injection; concrete adapters isolated in `infrastructure/` and swappable.
- Idempotent, side-effect-aware handlers for registration, password reset, MFA, and token flows.
- Security-by-default: hardened inputs, least-privilege data access, auditable events, rate limiting, lockout policies.
- Deterministic, explicit error taxonomy. All endpoints return consistent error envelopes and machine-actionable codes.
- Testability: services free of framework globals; pure functions where possible; external effects mocked behind ports.

---

## 3. Multi-Tenancy Model

### 3.1 Tenant Resolution Strategies (configurable)
- Subdomain: `tenant.example.com`
- Path prefix: `example.com/tenant/{slug}`
- Header: `X-Tenant-ID`
- Custom resolver: pluggable strategy interface

### 3.2 Isolation Patterns
- Shared DB, per-row isolation with `tenant_id` and RLS (recommended default)
- Shared DB, per-schema (optional)
- Database-per-tenant (optional for enterprise)

Configuration sets the isolation strategy; repositories enforce tenant scoping. Middleware resolves tenant context early and propagates via request-scoped container.

---

## 4. Data Model (Minimal, Extensible)

- `tenants` (id, slug [unique], name, domain, subdomain, status, settings jsonb, branding jsonb, timestamps)
- `users` (id, tenant_id fk, email [unique within tenant], password_hash, name fields, role, status, email_verified, mfa_enabled, last_login, timestamps)
- `roles` (id, tenant_id fk, name [unique within tenant], description, permissions jsonb, is_system_role, timestamps)
- `user_roles` (id, user_id fk, role_id fk, assigned_by, assigned_at, expires_at)
- `refresh_tokens` (id, user_id fk, token_hash, status, issued_at, expires_at, device_info, ip_address)
- `login_attempts` (id, tenant_id, user_id nullable, email, ip_address, user_agent, success bool, reason, occurred_at)
- `audit_logs` (id, tenant_id, actor_user_id, action, resource, metadata jsonb, occurred_at)

Indexes and constraints:
- Unique `(tenant_id, email)` on `users`.
- Partial index for active `refresh_tokens` by `user_id`.
- Btree index on `login_attempts(email, occurred_at)` for lockout windows.

---

## 5. API Surface (Reference FastAPI Contract)

Base prefix: `/api/v1`

Authentication
- `POST /auth/register` — multi-tenant user registration with optional invitation code
- `POST /auth/login` — email/password, optional MFA challenge
- `POST /auth/refresh` — rotate refresh tokens
- `POST /auth/forgot-password` — issue reset token
- `POST /auth/reset-password` — consume reset token
- `POST /auth/mfa/setup` — TOTP/SMS/email enrollment
- `POST /auth/mfa/verify` — verify factor to complete login
- `POST /auth/social/{provider}` — OAuth handoff (Google, Apple, etc.)
- `POST /auth/logout` — revoke tokens (all devices optional)

Tenants & Users
- `POST /tenants` — create tenant (admin)
- `GET /tenants/{slug}` — get tenant
- `PUT /tenants/{id}` — update tenant settings/branding/status
- `GET /tenants/{id}/users` — list users (paginated)
- `POST /tenants/{id}/users` — create/invite user (admin)
- `PUT /users/{id}` — update profile/role
- `DELETE /users/{id}` — deactivate
- `POST /users/{id}/roles` — assign role with optional expiry

All authenticated routes require tenant context and bearer access token; service checks RBAC and optional ABAC policies.

---

## 6. Response Contracts

### 6.1 Success Envelope
```
{
  "success": true,
  "data": { /* payload */ },
  "meta": { "timestamp": "ISO-8601", "request_id": "req_..." }
}
```

### 6.2 Error Envelope
```
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "details": { "field": "password", "attempts_remaining": 2 },
    "timestamp": "ISO-8601",
    "request_id": "req_..."
  }
}
```

### 6.3 Canonical Error Codes (subset)
- AUTH_INVALID_CREDENTIALS, AUTH_ACCOUNT_LOCKED, AUTH_EMAIL_NOT_VERIFIED
- AUTH_MFA_REQUIRED, AUTH_MFA_INVALID, AUTH_TOKEN_EXPIRED, AUTH_REFRESH_TOKEN_INVALID
- TENANT_NOT_FOUND, TENANT_SUSPENDED, TENANT_SLUG_TAKEN
- USER_NOT_FOUND, USER_EMAIL_TAKEN, USER_INSUFFICIENT_PERMISSIONS
- VALIDATION_ERROR, VALIDATION_PASSWORD_WEAK, VALIDATION_REQUIRED_FIELD
- SYSTEM_ERROR, SYSTEM_RATE_LIMITED, SYSTEM_MAINTENANCE

---

## 7. Security Controls

- Password policy: min/max length, upper/lower/number/special, forbidden patterns, password history, breach checks.
- Password hashing: bcrypt/argon2 with calibrated cost; optional pepper.
- JWT: short-lived access (≈1h), long-lived refresh (≈30d), rotation on use, device binding metadata, issuer/audience claims, clock skew handling.
- Rate limiting: per-IP and per-identity buckets (login, forgot/reset, MFA verify, refresh, tenant creation).
- Lockout: progressive delays and temporary lock after N failures; IP reputation support.
- CSRF: only required if cookie-based auth is enabled; otherwise enforce same-site and secure flags.
- Headers: HSTS, CSP (for web app), referrer policy, frameguard, X-Content-Type-Options.
- Input hardening: strict validation, canonicalization, size limits; reject ambiguous encodings.
- Audit: immutable logs for security-sensitive actions; tamper-evident storage.

---

## 8. Authorization

- RBAC with hierarchical roles (Super Admin, Tenant Admin, Manager, User).
- Permissions as fine-grained actions (e.g., `users.read`, `users.write`, `tenants.manage`).
- Optional ABAC extension: policies can include tenant plan, user attributes, resource ownership.
- Authorization middleware checks route-level requirements; services perform resource-level checks.

---

## 9. Module Structure (Library-First)

```
auth_module/
  core/
    config.py            # settings and feature flags
    container.py         # DI wiring
    exceptions.py        # error taxonomy
    security.py          # crypto/jwt/factors
  domain/
    models/              # user, tenant, role, tokens
    policies/            # RBAC/ABAC rules
    services/            # auth, tenant, user, permission
    events.py            # domain events
  infrastructure/
    db/                  # repositories, migrations
    cache/               # redis adapters
    messaging/           # email/sms/queue providers
    oauth/               # social providers
  api/
    routers/             # auth, tenant, user
    middleware.py        # tenant resolver, auth guard
    schemas.py           # pydantic DTOs
  tests/
    unit/ integration/ security/ performance/
docs/
  README.md API.md SECURITY.md DEPLOYMENT.md
```

Guidelines:
- Public APIs type-annotated and stable; avoid leaking infrastructure types across boundaries.
- Repositories abstract persistence; no ORM leakage into services.
- Use composition over inheritance; no static singletons.

---

## 10. Error, Success, and Failure Handling

- Use typed exceptions mapped to canonical error codes; no blanket try/except.
- Explicit transactional boundaries; roll back on failure; outbox/event patterns for cross-service effects.
- Idempotency keys for sensitive endpoints (register, reset-password) to avoid duplicate effects.
- Emit structured audit logs on security events (login, logout, mfa, role changes, tenant changes).
- Provide deterministic HTTP status mapping: 200/201 success, 400 validation, 401 auth, 403 authorization, 404 not found, 409 conflict, 429 rate limited, 500/503 system.

---

## 11. Testing Strategy

- Unit tests for services/policies/utils (95%+ target on core domain/service code).
- Integration tests for tenant isolation, token flows, MFA, social login.
- Security tests: rate limiting, password policy, JWT tampering, CSRF (if cookies), SQLi/XSS input filters.
- Performance tests: concurrent logins, token refresh storms, tenant creation load.
- Contract tests: schema validation for success and error envelopes.

---

## 12. Observability & Operations

- Health: `/health` endpoint returning service/component status.
- Metrics: counters for failed/success logins, token validations, tenant count, lockouts.
- Tracing: propagate request/tenant ids; instrument critical paths.
- Logging: structured, JSON logs with redaction of sensitive fields.
- SLOs: p50 login < 200ms, token validate < 50ms; availability 99.9%.

---

## 13. Deployment & Branching

- Branch: `auth-implementation` (feature branch). PRs require tests and security checks to pass.
- CI: lint, type-check, unit/integration/security tests, build package, generate OpenAPI docs.
- Versioning: semantic versioning for the library; publish artifacts to internal registry or PyPI (optional).
- Migrations: Alembic-managed; forward-only, reversible scripts; preflight safety checks in CI.

---

## 14. Implementation Checklist (DoD)

- Multi-tenant context resolution and enforcement across API, services, and repositories.
- Core flows: register, login, refresh, logout, email verify, forgot/reset, MFA setup/verify, social login.
- RBAC with assignable roles and permission checks.
- Canonical success and error envelopes with codes and metadata.
- Security controls: rate limiting, lockouts, headers, validation, audit logs.
- 95%+ coverage on core services; green integration/security tests; performance thresholds met.
- OpenAPI documented; quickstart in `docs/README.md` with working examples.

---

## 15. Quickstart (Reference Integration)

```python
from fastapi import FastAPI
from auth_module.api.routers import auth_router, tenant_router
from auth_module.api.middleware import TenantMiddleware

app = FastAPI()
app.add_middleware(TenantMiddleware)
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(tenant_router, prefix="/api/v1/tenants")
```

---

## 16. Risks & Mitigations

- Incorrect tenant scoping → enforce tenant filters in repositories; add isolation tests and DB-level constraints/RLS.
- Token theft → short-lived access, rotating refresh, device binding, revoke-all endpoint, audit/alerts.
- MFA UX friction → progressive enrollment, backup codes, trusted devices with expiry.
- Email deliverability → provider fallback, retries, SPF/DKIM/DMARC guidance in docs.

---

Prepared to implement on `auth-implementation` and ship as a reusable module for the WindWays travel platform with robust security, error handling, and clean architecture.


