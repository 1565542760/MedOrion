# CAP/COP Clinical MLP Stage 116 Runtime Placement Decision

## Current Stage 115 Status

Stage 115 is complete and committed.

- Commit: `47f3003`
- Message: `feat: add clinical mlp one-shot shadow execution`

Current one-shot shadow execution behavior for the clinical MLP fold5 path:

- Endpoint exists: `POST /api/v1/cases/{case_id}/shadow-inference/clinical-mlp/fold5/one-shot`
- Authenticated calls return `200`
- The backend runtime currently does not have `torch`
- The one-shot path therefore resolves to:
  - `status = shadow_failed`
  - `error_code = torch_runtime_unavailable`
- Shadow audit is written for the failed attempt
- No recommendation is written
- No trace/evidence is written
- No access-audit write is triggered by the one-shot path

## What We Checked

### Backend container

Observed:

- `torch` is not available in the backend container

Implication:

- The backend container cannot be the place where the real fold5 forward pass runs unless we intentionally make it a model runtime container, which would blur service boundaries.

### Model-service container

Observed:

- `torch` is not available in the model-service container either
- The CAP/COP clinical MLP fold5 weight file is not present at the expected model-service path:
  - `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/weights/fold5_best.pth`
- The preprocess artifact is also not present in that model-service path tree

Implication:

- The model-service is the right architectural home for real inference, but it is not yet provisioned for this specific adapter runtime.

### MRI3D conda environment

Current conclusion:

- I do not have evidence that the MRI3D conda environment is currently wired into the model-service container for this fold5 runtime
- Treat it as not yet confirmed / not yet usable for Stage 117 until a follow-up runtime check proves the environment and artifacts are mounted and callable

### Model-service code shape

What the current tree suggests:

- I found `app/model-service/app/services/model_registry.py`
- I did not find a dedicated clinical MLP adapter file or a dedicated `/infer` route for this adapter in the current model-service tree

Implication:

- The model-service currently looks like it has registry plumbing, but not a finished clinical MLP runtime adapter for CAP/COP fold5 yet

### Backend to model-service network

Current recommendation:

- Keep backend -> model-service as the call boundary
- Stage 117 should verify service-to-service health and the adapter endpoint explicitly before enabling real shadow inference

## Option Comparison

### A. Install / enable torch in backend container

Pros:

- Minimal change to the current Stage 115 endpoint shape

Cons:

- Backend becomes heavier
- Business API and model runtime become tightly coupled
- Imaging and multimodal runtimes would likely push the backend further into runtime ownership
- GPU / conda / torch dependency management gets riskier
- Harder to keep audit and runtime concerns cleanly separated

Verdict:

- Not recommended

### B. Implement the real adapter in model-service

Pros:

- Fits the existing architectural split:
  - backend = business logic, validation, audit
  - model-service = model runtime
- Keeps model loading and runtime dependencies out of the backend API process
- Makes imaging and multimodal adapters easier to add later
- Lets us keep shadow audit in backend while routing actual inference to a dedicated runtime service

Cons:

- Requires the model-service to be provisioned with:
  - torch
  - the fold5 artifact
  - the preprocess artifact
  - a real clinical MLP adapter endpoint
- Requires one additional service hop

Verdict:

- Recommended

### C. Backend calls a local MRI3D conda subprocess

Pros:

- Could be the fastest temporary proof-of-concept

Cons:

- Operationally messy
- Harder to observe and audit
- Harder to containerize cleanly
- Couples backend execution to a local environment that is not the long-term ownership boundary

Verdict:

- Not recommended except as a temporary proof-only fallback

## Recommended Runtime Placement

Recommended choice: **B. model-service real adapter**

Reasoning:

- The backend already has the right control-plane responsibilities:
  - snapshot validation
  - case access
  - access/shadow auditing
- The model-service is the proper data-plane place for actual forward execution
- This keeps the system separable and makes the next two adapters easier:
  - imaging ResNet18
  - multimodal ResNet18

## Stage 117 Recommended Implementation Route

If we proceed with B, Stage 117 should do the following:

1. Add a clinical MLP adapter entry in model-service
   - Load the fold5 artifact in the model-service runtime
   - Keep the adapter isolated from business API concerns
   - Preserve CAP/COP label mapping:
     - `CAP = 0`
     - `COP = 1`

2. Make the backend one-shot endpoint call model-service
   - Backend keeps:
     - snapshot lookup
     - access checks
     - input sanitization
     - shadow audit writes
   - Backend sends a sanitized payload to model-service
   - Model-service returns:
     - probabilities
     - label
     - confidence / auxiliary runtime info

3. Write success / failure into shadow audit only
   - Success:
     - `shadow_success`
     - output row written
   - Failure:
     - `shadow_failed`
   - No recommendation write
   - No trace/evidence write

4. Keep runtime bounded
   - `no_grad`
   - `eval`
   - `batch=1`
   - single-shot execution only
   - no silent fallback

5. Keep failure explicit
   - Missing input -> `shadow_insufficient_input`
   - Runtime / artifact / adapter failure -> `shadow_failed`

## Compliance Boundaries

This decision does **not**:

- install torch into backend
- change containers yet
- load the model
- call `torch.load`
- train anything
- run real inference yet
- change the database
- run Alembic
- open the global shadow switch
- add allowlist rows
- write recommendation / trace / evidence
- change the frontend
- scan, copy, move, or guess any model files

## Final Decision

Recommended runtime placement for CAP/COP clinical MLP fold5 real inference: **B. model-service real adapter**

Stage 116 checkpoint recommendation:

- Yes, this decision should be checkpointed as a doc once remote repo access is stable
- If the remote repo remains unavailable, keep this as a draft and sync it to the repo mirror as soon as the source tree is reachable
