# MedOrion Stage 46 - Artifact Metadata Review

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

Reviewed artifacts:
- `/home/sygxdg/MedOrion/app/backend/app/modules/model_registry/router.py`
- `/home/sygxdg/MedOrion/app/backend/app/modules/model_registry/schemas.py`

## Review verdict

Stage 46 is **approved at the review level**.

The backend now exposes a metadata-only artifact API layered over existing `model_versions.artifact_ref_json`, `metrics_json`, and `runtime_constraints_json`. The implementation remains governance-safe because it stores artifact metadata only and does not attempt to load, scan, hash, move, or validate a real binary artifact.

## Findings

### 1. Artifact URI handling

`artifact_uri` is treated as user-supplied metadata and stored as-is in the version metadata payload.
There is no directory scan, no existence check, no file read, and no in-process hash calculation.
That is the correct boundary for a metadata-only stage.

### 2. Metadata-only safety flags

The flags:
- `artifact_not_loaded: true`
- `metadata_only: true`
- `artifact_state: "metadata_only"`

are sufficient to prevent the metadata record from being mistaken for a loaded model artifact.
They are also propagated into both the metadata view and the validation record.

### 3. Provenance coverage

The current metadata fields are sufficient for provenance tracking at this stage:
- `artifact_type`
- `artifact_hash`
- `hash_algorithm`
- `file_size_bytes`
- `registered_by`
- `registered_at`
- `provenance_json`
- `safety_notes`
- `adapter_type`
- `preprocess_schema_version`
- `postprocess_schema_version`

Together they give a workable provenance envelope for later real-model onboarding.

### 4. Validation record semantics

`artifact-validation-record` is a registration record, not a runtime validation or model-load proof.
The implementation keeps it metadata-only and continues to mark the artifact as not loaded.
That is the right interpretation and should stay explicit in docs and UI.

### 5. Future real-model requirements

When a real model is eventually allowed into trace/evidence, the system will still need:
- approved `model_version_id`
- stable `artifact_hash`
- registry approval state
- adapter type and runtime constraints
- input references and output references
- runtime environment context
- explicit trace/evidence emission rules
- clear rollback/fallback policy state

Stage 46 is not yet that stage, and it should not pretend to be.

### 6. `.pth` and related file restrictions

The contract remains correctly strict.
It still forbids any scanning, guessing, copying, or moving of `.pth`-family files before the user provides an exact artifact path.
That remains the right operational constraint.

## Must-fix items

None found at review level.

## Suggested items

- Keep `metadata_only` and `artifact_not_loaded` visible in API responses and docs.
- Keep the validation-record endpoint documented as a metadata registration record, not a loading or execution proof.
- When Stage 47 eventually deals with real artifact onboarding, keep exact-path user input as the first hard gate.

## Boundary ruling

The metadata-only layer may store provenance metadata, but it must not become a proxy for real model onboarding.

Allowed in this stage:
- user-supplied artifact metadata
- registry linkage metadata
- safety notes
- adapter/preprocess/postprocess schema version metadata
- validation registration records

Not allowed in this stage:
- file discovery
- file existence probing
- artifact loading
- hash calculation from the real file in backend logic
- real inference execution
- trace/evidence emission from real model output

Real model artifact provenance will only enter case trace/evidence after governed activation and approved execution.

## Git checkpoint recommendation

A Git checkpoint is reasonable after this review.
The stage is coherent, non-destructive, and preserves the ??etadata only??governance posture.

## Compliance confirmation

This review did not change source code, database schema, or Alembic state.
It did not enable Nginx, did not load a real model, did not train anything, and did not inspect, copy, move, or guess any `.pth/.pt/.onnx/.ckpt/.safetensors` files.
