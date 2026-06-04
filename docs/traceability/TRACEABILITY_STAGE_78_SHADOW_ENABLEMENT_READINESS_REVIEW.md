# MedOrion Stage 78 - Shadow Enablement Readiness Review

Date: 2026-06-05

Scope:
- Review only
- No source changes
- No database changes
- No Alembic execution
- No model loading
- No `torch.load`
- No training
- No real inference
- No GPU enablement
- No Nginx enablement
- No frontend changes
- No recommendation writes
- No case trace/evidence writes
- No serialized model artifact file operations

Reviewed runtime state:
- `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=false`
- `CAP_COP_CLINICAL_MLP_SHADOW_ALLOWED_MODEL_VERSION_IDS=[]`
- Empty allowlist now rejects all model versions
- Outer status remains `shadow_disabled`
- Inner eligibility preview returns `model_not_allowlisted` with `allowlist_empty=true`

## Review verdict

Stage 78 is **not yet approved to open the shadow switch**.

The readiness stack is in good shape, but the final enablement condition is still intentionally not met because the global gate is disabled and the allowlist is empty. That is the correct safety posture for a pre-enablement stage.

## Findings

### 1. Readiness state

The current state is appropriate for the end of a readiness phase, but not for actual enablement.

What is already good:
- disabled-by-default gate
- fail-closed behavior
- allowlist rejects all when empty
- metadata-only eligibility evaluation
- no file loading, no hashing, no `torch.load`
- no live inference
- no case trace/evidence writes
- no recommendation writes

What is still missing for enablement:
- an explicit, approved allowlist entry for the target version(s)
- an explicit decision to turn the backend shadow gate on
- a final operational sign-off that the chosen shadow candidate is authorized for controlled execution

### 2. Allowlist safety

The empty allowlist behavior is now safe.
An empty list means reject all, which is the correct fail-closed semantics.

That said, an empty allowlist also means the switch still cannot be opened for execution.
The system is intentionally not ready to run shadow until a specific model version is explicitly allowlisted.

### 3. Runtime safety config

The runtime safety defaults remain conservative and appropriate:
- CPU only
- batch size 1
- max concurrency 1
- timeout 10 seconds
- force no-grad
- force eval mode
- disable GPU

These defaults are good and do not need further tightening for readiness.

### 4. Eligibility gate

The eligibility helper is in good shape.
It remains metadata-only and fail-closed.
The dual-layer status model is clear:
- outer execution status: `shadow_disabled`
- inner eligibility preview: `model_not_allowlisted` / `input_insufficient` / other short-circuit states

That is a sensible split, and it should stay documented.

### 5. Artifact provenance / feature mapping / input validation

The supporting provenance and feature-mapping stack is mature enough for the next step.
The important thing left is not technical capability but governance authorization:
- approved model version identity
- approved shadow candidate entry in the allowlist
- final readiness sign-off

Input validation and insufficient-data handling remain adequate for the controlled shadow path.

## Must-fix items

None found at review level in the code structure.

The only reason the switch remains closed is that the readiness policy is intentionally not authorized yet.

## Can the shadow switch be opened now?

**No.**

Why not:
- the backend gate is still disabled
- the allowlist is empty and intentionally rejects all versions
- there is no explicit allowlisted model version for activation
- the project has not yet recorded a final enablement sign-off

## What remains required before enablement

1. Choose and explicitly allowlist the intended clinical MLP fold5 candidate version.
2. Record the final authorization decision for that specific version.
3. Confirm the runtime safety config stays in effect.
4. Confirm the shadow path remains audit-only.
5. Then, and only then, consider turning the backend shadow gate on for a controlled rehearsal.

## Stage 79 recommendation

Stage 79 should be a **manual sign-off / enablement checklist stage**, not a live execution stage.

Recommended Stage 79 focus:
- final human approval checklist
- explicit allowlist confirmation
- operational go/no-go record
- documentation update for stage overview / handoff
- no live inference
- no recommendation path
- no case trace/evidence writes

A rehearsal is only appropriate if it remains disabled-by-default in practice and is clearly not a live clinical run.

## Git checkpoint recommendation

A Git checkpoint is reasonable now for the readiness baseline, because the safety posture is coherent and the remaining blocker is governance authorization rather than a code defect.

## Boundary ruling

The shadow stack remains correctly separated from the formal clinical chain.

Allowed:
- runtime safety config reporting
- metadata-only eligibility evaluation
- shadow audit visibility
- fail-closed `shadow_disabled` behavior

Not allowed yet:
- opening the shadow switch
- live shadow execution
- recommendations
- case trace/events
- evidence chain writes
- model loading
- `torch.load`

## Compliance confirmation

This review did not change the database, did not execute Alembic, did not load a model, did not call `torch.load`, did not train, did not run real inference, did not enable GPU, did not enable Nginx, did not change the frontend, and did not inspect, copy, move, or guess any model artifact files.
