# MedOrion Stage 67 - Shadow Audit Write Skeleton Review

Date: 2026-06-04

Scope:
- Review only
- No schema changes
- No Alembic execution
- No Nginx enablement
- No model loading
- No training
- No inference execution
- No `.pth/.pt/.onnx/.ckpt/.safetensors` operations

Reviewed artifacts:
- `/home/sygxdg/MedOrion/app/backend/app/modules/shadow_audit/__init__.py`
- `/home/sygxdg/MedOrion/app/backend/app/modules/shadow_audit/schemas.py`
- `/home/sygxdg/MedOrion/app/backend/app/modules/shadow_audit/service.py`
- `/home/sygxdg/MedOrion/app/backend/app/modules/shadow_audit/router.py`
- `/home/sygxdg/MedOrion/app/backend/app/api/v1/router.py`

## Review verdict

Stage 67 is **approved at the review level**.

The write skeleton is correctly constrained to the shadow audit layer. It creates a controlled audit record path, validates the key safety flags, and does not spill into recommendations or the case trace/evidence chain by default.

## Findings

### 1. Write boundary is correct

The write path only targets:
- `shadow_inference_runs`
- `shadow_inference_outputs`

It does not write to:
- `recommendations`
- `trace_events`
- `evidence_nodes`
- `evidence_edges`

That separation is the right boundary for a controlled shadow-audit write skeleton.

### 2. Safety flags are enforced

The write skeleton explicitly requires:
- `not_for_diagnosis = true`
- `runtime_stub = true`

This is important because it keeps the shadow write path from being mistaken for clinical output.

### 3. Required validation is correct

The skeleton validates:
- `case_id` existence
- `model_version_id` existence
- allowed shadow status values
- `trace_id` presence

That is sufficient for a controlled stub record path.

### 4. Output handling is still audit-only

Optional output payloads are accepted as metadata and output audit data only.
They are not turned into formal recommendations or case evidence.

### 5. Query surfaces remain consistent

The read API surfaces stay consistent with the Stage 66 design:
- run lookup
- case-scoped run list
- trace-scoped run list
- run outputs

This makes the write path and read path match cleanly.

## Boundary ruling

Shadow write skeleton is audit-only storage.
It should remain separate from the doctor-facing recommendation chain and the case evidence chain by default.

Allowed to remain in shadow audit storage:
- ordinary shadow calls
- failed shadow calls
- timing and runtime detail
- adapter detail
- comparison payloads
- output payloads

May only enter case trace/evidence later if explicitly approved and clinically meaningful:
- concise summary
- clinically relevant comparison result
- doctor-facing note derived from approved review

Must not enter case trace/evidence by default:
- raw shadow prediction payloads
- operational logs
- adapter plumbing details
- non-clinical timing noise

## Apply recommendation

The write skeleton is suitable for a **restricted apply discussion** only if the team later wants to keep a fully controlled dev record path.

## Compliance confirmation

This review did not change the database, did not execute Alembic, did not load a model, did not train, did not run inference, did not enable Nginx, and did not inspect, copy, move, or guess any `.pth/.pt/.onnx/.ckpt/.safetensors` files.
