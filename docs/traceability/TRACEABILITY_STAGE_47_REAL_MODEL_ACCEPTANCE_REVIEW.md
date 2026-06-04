# MedOrion Stage 47 - Real Model Acceptance Review

Date: 2026-06-03

Scope:
- Review only
- No source changes
- No schema changes
- No Alembic execution
- No Nginx enablement
- No real model loading
- No training
- No `.pth/.pt/.onnx/.ckpt/.safetensors` operations

Reviewed artifact:
- `/home/sygxdg/MedOrion/docs/model_orchestration/REAL_MODEL_STAGE_47_ONBOARDING_ACCEPTANCE_PLAN.md`

## Review verdict

Stage 47 is **approved at the review level**.

The acceptance plan clearly defines when the main controller may ask the user for an exact model path, and it keeps that request separate from any actual load or runtime enablement. The plan also keeps hash verification, metadata registration, adapter enablement, offline evaluation, fallback/rollback, and trace/evidence provenance in the correct order.

## Findings

### 1. Asking the user for an exact model path

The conditions for asking the user for an exact path are clear enough.
The controller may ask only when the onboarding target is known, registry intent exists, and the request is a concrete onboarding task rather than directory exploration.
That is the correct governance boundary.

### 2. Path provided does not mean immediate load

The plan is explicit that a user-provided path does not permit immediate loading.
The required sequence is:
- receive exact path
- register metadata
- verify identity metadata
- record hash or pending-hash state
- attach to a specific `model_version_id`
- run acceptance prechecks
- only later enable a real adapter

That is the right ordering.

### 3. Hash boundary

The hash rules are appropriately strict.
Hash computation is allowed only for the exact user-authorized path.
The plan forbids directory scanning, guessing, nearby-file substitution, and alternate candidates.
That is sufficiently strict for safe onboarding.

### 4. Real adapter enablement checks

The enablement checklist is strong and practical.
It covers:
- version eligibility
- approval/default state
- CPU-first runtime assumptions
- timeout
- batch size 1
- concurrency 1
- preprocess/postprocess schema compatibility
- resource requirements
- trace/evidence readiness

This is the correct gate set before a real adapter can be switched on.

### 5. Trace / evidence requirements

The trace/evidence fields are sufficient for the acceptance stage.
The plan requires:
- `model_version_id`
- `artifact_hash`
- input refs
- output refs
- runtime env
- `model_invocation_id`
- `trace_id`
- approval status
- fallback reason
- runtime type

That is enough to support a future real-model provenance chain.

### 6. Offline evaluation and rollout gates

The offline evaluation, shadow, canary, and default gates are appropriately hard.
Fallback and rollback must be explicit and traceable.
`no_silent_fallback` remains a hard rule, which is necessary for any real-model governance stage.

### 7. Doctor feedback and quality review boundary

The boundary is correct.
Doctor feedback and quality review remain quality signals and do not trigger automatic training.
That prevents the acceptance stage from drifting into unsafe retraining behavior.

### 8. Stage 48 readiness

Stage 48 should proceed after the user provides an exact model path.
The proposed Stage 48 direction ??metadata registration and hash-verification readiness ??is appropriate.

## Must-fix items

None found at review level.

## Suggested items

- Keep the ??sk for one exact path, not a folder??wording prominent in governance tooling.
- Keep the requirement to register metadata before any later load attempt visible in Stage 48 handoff material.
- Preserve the explicit ??ash on exact authorized path only??wording in future runbooks so the no-scan rule stays hard.

## Boundary ruling

The acceptance plan keeps real-model provenance in the right place.
It is still too early for trace/evidence to contain live model outputs, but the acceptance plan correctly defines the metadata and runtime prerequisites that must exist before that happens.

The following remain separate until the real-model stage is actually activated:
- artifact discovery
- metadata registration
- hash verification
- adapter enablement
- inference execution
- case trace/evidence emission

The plan is careful not to imply that a path or metadata record equals an active real-model deployment.

## Stage 48 recommendation

Proceed to Stage 48 as **metadata registration and hash-verification readiness** after the user provides an exact artifact path.

## Compliance confirmation

This review did not change source code, database schema, or Alembic state.
It did not enable Nginx, did not load a real model, did not train anything, and did not inspect, copy, move, or guess any `.pth/.pt/.onnx/.ckpt/.safetensors` files.
