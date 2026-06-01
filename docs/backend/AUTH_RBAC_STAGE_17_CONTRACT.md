# AUTH_RBAC_STAGE_17_CONTRACT

## Goals

- MedOrion has already formed a usable stub loop (`frontend -> backend -> model-service`) and minimal trace/evidence persistence, but it currently lacks identity boundaries.
- Before introducing real patient workflows, formal doctor feedback loops, model approval workflows, and non-stub case creation, we must establish authentication and RBAC contracts.
- Authentication/authorization is a prerequisite for:
  - real case ownership and attribution,
  - trace actor accountability,
  - model version approval accountability,
  - quality review accountability,
  - safe multi-user operation in a medical context.
- Therefore, auth must be completed before:
  1. real-case data onboarding,
  2. doctor feedback productionization,
  3. model approval lifecycle productionization,
  4. replacement of `case-001` stub anchor with formal case creation flow.

## Roles

Minimal MVP roles:

1. `doctor`
   - Clinical user who can trigger assisted inference and submit feedback.
2. `admin`
   - Operational administrator for user/account and platform-level settings.
3. `model_reviewer`
   - Reviewer who can evaluate and approve/reject model versions.
4. `qa_reviewer`
   - Reviewer for quality events, trace audits, and quality review records.
5. `super_admin`
   - Highest privilege role for emergency override and full user/role management.

## Permissions

MVP permission matrix (`Y` = allowed, `R` = read-only, `N` = not allowed by default):

| Capability | doctor | admin | model_reviewer | qa_reviewer | super_admin |
|---|---|---|---|---|---|
| View cases | Y | Y | R | R | Y |
| Create/Edit cases | Y (owned/scope-limited) | Y | N | N | Y |
| Trigger assisted inference | Y | Y | N | N | Y |
| View recommendations | Y | Y | R | R | Y |
| View trace/evidence | R (scope-limited) | Y | R | Y | Y |
| Submit doctor feedback | Y | Y | N | N | Y |
| Create quality review | N | Y | N | Y | Y |
| View model registry/versions | R | Y | Y | R | Y |
| Manage model versions metadata | N | Y | Y | N | Y |
| Approve model versions | N | N | Y | N | Y |
| Manage users | N | Y | N | N | Y |

Notes:
- Scope-limited means access constrained by tenant/site/department/case assignment policy (defined later).
- `super_admin` is break-glass and should be auditable with stricter controls.

## Backend API Draft

Auth APIs (MVP skeleton contract):

- `POST /api/v1/auth/login`
  - Input: username/email + password
  - Output: auth tokens/session metadata + minimal user profile + role set
- `POST /api/v1/auth/logout`
  - Input: current token/session context
  - Output: success/failure
- `GET /api/v1/auth/me`
  - Output: current authenticated user, roles, permission claims snapshot
- `POST /api/v1/auth/refresh` (optional but recommended for JWT mode)
  - Input: refresh token/session handle
  - Output: rotated access token (+ optional rotated refresh token)

User administration APIs (deferred, admin-only):

- `GET /api/v1/users` (admin/super_admin)
- `POST /api/v1/users` (admin/super_admin)

## Auth Strategy

Options considered:

1. JWT access token + refresh token
   - Pros:
     - works well with separate frontend/backend services,
     - simple stateless access token validation at API gateway/backend layer,
     - good fit for current containerized architecture.
   - Cons:
     - requires careful refresh token rotation/revocation strategy.

2. Server-side session
   - Pros:
     - centralized invalidation.
   - Cons:
     - more coupling to session store, less convenient for service-to-service boundaries.

### MVP Recommendation

Recommend **JWT access token + refresh token** with server-side refresh token tracking.

- Access token: short TTL (e.g., 10–20 minutes).
- Refresh token: longer TTL (e.g., 7–14 days), rotation on refresh.
- Logout: revoke current refresh token/session record.
- Compromise response: revoke token family/session chain.
- Password hash: **Argon2id preferred**, bcrypt acceptable fallback.

## Database Entity Draft

Design only (no migration in Stage 17):

1. `users`
   - `id`, `username`, `email`, `password_hash`, `is_active`, `is_locked`, `last_login_at`, `created_at`, `updated_at`
2. `roles`
   - `id`, `role_name` (`doctor/admin/model_reviewer/qa_reviewer/super_admin`), `description`
3. `user_roles` (recommended over single `users.role`)
   - `id`, `user_id`, `role_id`, `granted_by`, `granted_at`
4. `refresh_tokens` (or `auth_sessions`)
   - `id`, `user_id`, `token_jti/hash`, `issued_at`, `expires_at`, `revoked_at`, `revoked_reason`, `client_meta`
5. `audit_logs` decision
   - MVP can reuse `trace_events` + existing structured logs for operational audit bootstrap.
   - For production hardening, introduce dedicated `audit_logs` with immutable retention policy.

## Trace Actor Integration

After auth is introduced, trace and domain records must bind to user identity:

- `trace_events.actor_type`: include `doctor`, `admin`, `model_reviewer`, `qa_reviewer`, `system`.
- `trace_events.actor_id`: authenticated `users.id` when human-triggered.
- `doctor_feedback.doctor_id`: mandatory, FK to `users.id` (role-validated).
- `quality_reviews.opened_by`: FK to `users.id` (qa/admin role).
- `model_versions.approved_by`: FK to `users.id` (model_reviewer/super_admin).
- `inference_tasks` trigger actor:
  - store initiator user id (new field in later schema stage),
  - also emit in `trace_events` for immutable lineage.

## Frontend Impact

Doctor workstation and admin console follow-up requirements:

- Login page and logout action.
- Current-user state (`/api/v1/auth/me`) hydration.
- Route guards for authenticated-only pages.
- Role-gated menu/navigation (doctor/admin/reviewer views).
- Dedicated admin entry for user management.
- Unauthorized/forbidden pages:
  - 401 (not logged in),
  - 403 (logged in but insufficient permission).

## Security Boundaries

- Never commit tokens/passwords/secrets to Git.
- Do not print token/password plaintext in logs.
- Secrets remain in runtime env (`.env`/secret manager), not source code.
- Production login endpoints must be HTTPS-only.
- Current state remains internal only:
  - Nginx disabled,
  - no public auth endpoint exposure in this stage.
- Medical data context requires stronger future controls:
  - immutable audit policies,
  - stricter session/device policies,
  - least-privilege defaults,
  - periodic permission review.

## Stage Plan

- **Stage 18**: Minimal auth backend skeleton
  - auth router stubs, token issuing/verification scaffold, role dependency hooks.
- **Stage 19**: Frontend login + route protection
  - login page, auth store, protected routes, role-aware menus.
- **Stage 20**: Formal case creation flow
  - replace `case-001` stub anchor with authenticated, attributable case lifecycle.
- **Stage 21**: Frontend UI polish
  - UX refinement for auth states, permission-denied experiences, reviewer workflows.
- **Stage 22**: Model registry/version lifecycle hardening
  - approval workflow enforcement, model reviewer actions tied to actor identity.

## Out of Scope for Stage 17

- No DB schema migration.
- No Alembic execution.
- No login implementation code.
- No frontend code changes.
- No Nginx enablement or public exposure.
- No real-model integration/training/GPU runtime work.
