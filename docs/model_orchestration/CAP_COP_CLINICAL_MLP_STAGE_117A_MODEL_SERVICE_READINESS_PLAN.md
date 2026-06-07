# CAP/COP Clinical MLP Stage 117A - Model Service Runtime Readiness Plan

## Purpose
This document is a readiness plan only. It does not implement runtime changes, install dependencies, load any model artifact, or change any deployment topology. Its job is to answer one question clearly: what must be true for MedOrion's clinical MLP fold5 inference to run safely and predictably in runtime.

## Current Blocker
Stage 116 already concluded that the clinical MLP fold5 runtime should live in `model-service`, not in `backend`. However, the current runtime is not ready for that target.

Current blockers:

- `model-service` does not have usable `torch` in its runtime environment.
- The clinical MLP adapter is not present or not wired in the runtime path.
- The fold5 artifact path is not visible to `model-service`.
- The preprocessing artifact is not visible to `model-service`.

This means Stage 117 cannot begin by wiring a real adapter yet. The runtime first needs a clean, explicit placement decision.

## Runtime Options

### A. Install CPU torch into the `model-service` image
Pros:

- Keeps the inference path inside the existing service boundary.
- Simplifies operational ownership: one service owns the runtime, API, and tracing surface.
- Easier to standardize with Docker Compose and to reason about health checks.

Cons:

- Requires image rebuild and dependency management inside the container.
- CPU-only runtime may be slower than a dedicated optimized environment.
- If later upgraded to GPU, the image will need another evolution path.

Assessment:

- Good for productization if the adapter is meant to become a stable service boundary.
- Best if the team wants a small number of moving parts and a predictable deployment target.

### B. Let `model-service` use the MRI3D conda environment
Pros:

- Fastest route if the environment already has the needed scientific stack.
- Reuses an existing runtime that may already contain compatible packages.

Cons:

- Operationally fragile: container/service now depends on an external conda runtime.
- Harder to reproduce and harder to deploy consistently.
- Makes Docker Compose less self-contained.

Assessment:

- Acceptable for a short-lived validation phase.
- Not ideal as the long-term product runtime.

### C. Create a separate `inference-service` container based on MRI3D / torch runtime
Pros:

- Cleanest long-term boundary for clinical inference.
- Keeps `model-service` as a registry/orchestration surface if desired.
- Allows a purpose-built image with only the dependencies needed for inference.

Cons:

- Adds one more service to compose and operate.
- Requires a bit more design work for routing, readiness, and deployment.
- Slower to implement than a single-image patch.

Assessment:

- Best choice for a stable, productized runtime.
- Most aligned with a clear separation between registry/orchestration and inference execution.

### D. Let `backend` spawn a subprocess into the MRI3D conda environment
Pros:

- Can prove the model works with minimal new infrastructure.
- Useful as a temporary proof-of-concept.

Cons:

- Not suitable as a service architecture.
- Makes backend responsible for runtime execution, dependency discovery, and process supervision.
- Increases coupling and makes observability, retries, and scaling much worse.

Assessment:

- Only acceptable as a very temporary proof, not as a target architecture.
- Not recommended for the real clinical MLP runtime.

## Recommended Runtime Direction

Recommended path:

1. If the goal is stability and productization, prefer **C: a separate inference-service container** or a dedicated torch-enabled runtime image.
2. If the goal is fastest controlled validation, **B: `model-service` using the MRI3D conda environment** can be used temporarily, but with clear risk acceptance.

Recommendation summary:

- Long-term product path: **C**
- Short-term validation path: **B**
- Standalone `model-service` CPU torch image: acceptable intermediate path between B and C if the team wants to stay inside the existing service boundary.

## Artifact Mount Plan

The runtime must only read exact, explicit artifacts. It must not scan directories or guess paths.

Required artifacts:

- `fold5_best.pth`
- `clinical_tabular_standardization_v1.json`

Mount plan:

- Mount artifacts read-only into the runtime.
- Use exact, versioned mount paths.
- Keep the runtime read path stable and documented.
- Do not copy or move artifacts as part of the plan.

Recommended mount rule:

- Treat artifact paths as configuration, not discovery.
- The service should receive the exact artifact path at startup or via deployment config.
- The runtime should refuse to proceed if the exact artifact is not present.

## Adapter Implementation Plan

The adapter is a later implementation step, not part of this readiness plan.

Expected implementation pieces:

- `ClinicalMLP` architecture definition.
- Load `state_dict` from the exact artifact path.
- Verify artifact integrity with `sha256` before load.
- Preprocess 36 features in a deterministic way.
- Run inference under `no_grad`, `eval`, and `batch=1`.
- Return logits, probabilities, and a candidate label.

Expected output shape:

- One CAP/COP candidate label.
- Probability and confidence information.
- Explicit uncertainty and limitations text.

## API Contract

Planned future endpoint:

- `POST /cap-cop/clinical-mlp/fold5/shadow-infer`

An alternative is to reuse `/infer`, but only if it remains trace-bound and explicit about purpose.

### Request

Fields:

- `trace_id`
- `model_version_id`
- `input_snapshot_id`
- `mapped_features`
- `not_for_diagnosis`

### Response

Fields:

- `status`
- `candidate_label`
- `probability`
- `confidence`
- `uncertainty`
- `limitations`
- `error_code`

Contract notes:

- `trace_id` must be supplied by the upstream caller.
- The runtime must not generate or replace `trace_id`.
- The endpoint is for shadow / validation style usage only until explicitly promoted.

## Security Boundaries

Non-negotiable boundaries:

- No training.
- No automatic training.
- No recommendation write-back.
- No trace/evidence write from the model runtime.
- No directory scanning.
- No artifact guessing.
- No silent fallback.
- Exact artifact only.
- `sha256` verification before load.
- No GPU assumptions unless explicitly introduced later.

## Stage 117B Recommendation

Recommended next step after this readiness plan:

1. If the goal is stable runtime ownership, build a torch-capable `model-service` or a dedicated `inference-service`.
2. If the goal is fastest proof, allow temporary use of the MRI3D conda environment with explicit risk acknowledgment.
3. If neither is ready, pause Stage 117 implementation and keep the plan as the decision record.

My recommendation is:

- Prefer **C** for long-term stability.
- Use **B** only for a short-lived proof if the team needs quicker validation.

## Summary

Stage 116 already told us where the runtime should live. Stage 117A is the preparation step that makes that answer operationally safe. The current blocker is not the clinical logic itself; it is the runtime boundary, artifact visibility, and dependency readiness.

This plan intentionally stops before implementation so Stage 117 can move forward without ambiguity.
