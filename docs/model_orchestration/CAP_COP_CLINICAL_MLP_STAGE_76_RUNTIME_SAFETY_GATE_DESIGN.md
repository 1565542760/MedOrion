# Stage 76 - CAP/COP Clinical MLP Shadow Runtime Safety Gate Design

## Purpose
This document defines the runtime safety and eligibility gate design for the CAP/COP clinical MLP controlled shadow path. It does **not** enable shadow execution and does **not** load any model artifact. Its purpose is to make the future enablement path explicit, conservative, and reviewable.

## Executive Summary
Current recommendation: keep the shadow path disabled until a future review explicitly approves all gate conditions.

Stage 75 identified the remaining gap areas. Stage 76 turns those gap areas into a clear design for runtime safety, eligibility gating, artifact/provenance gating, input gating, execution gating, audit gating, and rollback gating.

## 1. Runtime Safety Config Draft
The following configuration items should exist as a future-disabled-by-default safety envelope. These are design recommendations only, not enablement.

### Suggested Configuration Items
- `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=false`
  - Master switch for the shadow path.
- `CAP_COP_CLINICAL_MLP_SHADOW_CPU_ONLY=true`
  - Force CPU execution posture.
- `CAP_COP_CLINICAL_MLP_SHADOW_BATCH_SIZE=1`
  - Constrain each shadow execution to batch size 1.
- `CAP_COP_CLINICAL_MLP_SHADOW_MAX_CONCURRENCY=1`
  - Prevent parallel shadow fan-out.
- `CAP_COP_CLINICAL_MLP_SHADOW_TIMEOUT_SECONDS=10`
  - Hard timeout for a single shadow attempt.
- `CAP_COP_CLINICAL_MLP_SHADOW_FORCE_NO_GRAD=true`
  - Ensure no gradient tracking.
- `CAP_COP_CLINICAL_MLP_SHADOW_FORCE_EVAL_MODE=true`
  - Ensure evaluation mode only.
- `CAP_COP_CLINICAL_MLP_SHADOW_DISABLE_GPU=true`
  - Explicitly prevent GPU use.

### Design Intent
These settings should only be interpreted as a controlled safety envelope for future shadow execution. They must not be used to silently open a live inference path.

## 2. Eligibility Gate Design
A shadow run must satisfy **all** of the following before it is even eligible to attempt execution:

- Backend configuration allowlist permits the run.
- The selected model version is eligible for shadow according to registry lifecycle policy.
- Artifact metadata is complete.
- Artifact hash / provenance has been confirmed.
- `adapter_code` matches the allowed adapter family.
- `model_input_schema` matches the selected model version.
- `clinical_feature_mapping` is available and compatible.
- `no_silent_fallback` remains enforced.
- `not_for_diagnosis` remains true.

### Recommended Gate Shape
The enablement gate should be implemented as a short-circuit check sequence:
1. Check backend switch.
2. Check allowlist.
3. Check registry eligibility.
4. Check artifact/provenance.
5. Check input schema / mapping.
6. Check model-input validation result.
7. Only then allow the shadow execution skeleton to proceed.

## 3. Artifact / Provenance Gate
A shadow run must **not** be enabled by merely having an `artifact_uri`.

### Required Conditions
The following must be present and reviewed together:
- single approved artifact
- `artifact_hash`
- `hash_algorithm`
- `file_size_bytes`
- `model_version_id`
- `adapter_code`
- registry metadata
- enablement review sign-off

### Important Rule
Do **not** re-hash in Stage 76.
Do **not** read `.pth`.
Do **not** scan, copy, move, or guess any other model file.

### Design Meaning
Artifact metadata is a provenance contract, not a runtime loading instruction.

## 4. Input Gate
Before any future shadow execution attempt, the system must first pass through model-input validation.

### Required Behavior
If required features are missing, the system may only follow one of these paths:
- missing-value consultation
- explicit default strategy
- `insufficient_data_for_assessment`

### Forbidden Behavior
- silent fallback
- hard-coded input fabrication
- treating default values as doctor-provided inputs

### Design Meaning
Input gating is a hard stop for incomplete or ambiguous data.

## 5. Execution Gate
If the shadow path is ever enabled in a future reviewed stage, the runtime posture should be constrained as follows:
- CPU-only
- batch = 1
- concurrency = 1
- timeout enforced
- no_grad
- eval mode
- GPU disabled or explicitly reported unavailable

### Failure States
If the runtime attempt is not eligible or cannot complete safely, the shadow path should record one of the following states:
- `shadow_failed`
- `shadow_timeout`
- `shadow_insufficient_input`

### Current Stage Status
This stage does **not** execute those paths. It only defines them.

## 6. Audit Gate
The only approved write targets for the shadow path are:
- `shadow_inference_runs`
- `shadow_inference_outputs`

The following must remain untouched by the shadow path:
- `recommendations`
- `trace_events`
- `evidence_nodes`
- `evidence_edges`

### Design Meaning
Shadow audit is the authoritative record of the controlled shadow attempt. It is not a diagnosis record and not a case evidence record.

## 7. Rollback Gate
Turning the switch off must be enough to disable the path again.

### Rollback Actions
- set `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=false`
- keep shadow audit rows
- preserve model metadata
- do not alter recommendations
- do not alter case trace/evidence
- do not delete artifact provenance records

### Design Meaning
Rollback is a configuration rollback, not a data purge.

## 8. Future Stage Recommendation
### If Stage 76 Is Considered Sufficient
Stage 77 can be limited to:
- runtime safety config skeleton code
- eligibility gate helper skeleton
- still disabled-by-default
- still no model load
- still no real inference

### If Stage 76 Is Not Yet Sufficient
The remaining gaps would be:
- final artifact/provenance review sign-off
- final input mapping verification against real-case surfaces
- a concrete runtime safety test plan
- a small enablement review checklist for release gating

### Explicit Non-Goals
Do not jump to:
- default
- canary
- live inference
- recommendation generation

## 9. Decision
The current design is adequate to move into a very small Stage 77 planning exercise, but not to enable the shadow path.

Recommended next step: **Stage 77 should be a narrow runtime safety config skeleton / eligibility gate skeleton planning pass**, still disabled-by-default and still not loading models.
