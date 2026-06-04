# MedOrion Stage 52: Single-Artifact Hash Verification + Dry-Run Loading Plan

Last updated: 2026-06-04 Asia/Shanghai
Owner thread: MedOrion real-model onboarding and safety review
Scope: Stage 52 defines the single-artifact hash verification and dry-run loading plan for one CAP/COP artifact only. This stage does not load `.pth`, does not execute `torch.load`, does not train, does not run inference, does not enable GPU, does not change database schema, does not execute Alembic, does not enable Nginx, does not change frontend behavior, and does not write patient trace/evidence.

## 1. Goals

1. Define a safe, single-artifact verification path before any real CAP/COP model activation.
2. Select one concrete artifact for hash verification and dry-run planning.
3. Record the exact metadata needed for later registration and audit.
4. Define a CPU-only, batch=1, no-gradient, structure-only dry-run plan.
5. Keep the workflow explicitly non-diagnostic and non-promotional.

## 2. Non Goals

1. No real model loading.
2. No `torch.load` execution.
3. No training.
4. No real inference.
5. No GPU.
6. No model promotion.
7. No default activation.
8. No database schema changes.
9. No Alembic.
10. No Nginx.
11. No patient trace/evidence emission.
12. No directory scanning or artifact guessing.
13. No copying or moving model files.

## 3. Why Clinical MLP Is First

Clinical MLP is the best first artifact for Stage 52 because:
1. Its input contract is the simplest to validate structurally.
2. The input dimension is fixed at 36 clinical features.
3. Output dimension is binary, so structural expectations are narrow and easy to audit.
4. It does not depend on CT volume preprocessing or multimodal fusion logic.
5. It is the least ambiguous target for a CPU-only dry-run plan.

## 4. Why `fold1_best.pth` Is Chosen First

Recommended first artifact:

`/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/weights/fold1_best.pth`

Reasoning:
1. The plan needs one concrete artifact path, not a family-wide placeholder.
2. `fold1_best.pth` is a stable representative candidate for the first verification pass.
3. `fold1~fold5` are still not frozen as the final production selection.
4. Stage 52 is not choosing the final production weight.
5. Stage 52 only prepares the single-artifact verification path.

## 5. Why `fold1~fold5` Are Still Not Frozen

1. Cross-fold selection has not been finalized.
2. No final production decision should be inferred from one fold.
3. Later comparison across folds may still be required.
4. Stage 52 is deliberately limited to a single-artifact plan, not a final ranking.

## 6. This Stage Is Not Production Selection

1. This stage does not select the final production weight.
2. This stage does not promote any model to default.
3. This stage does not enable real diagnosis.
4. This stage does not replace the stub adapters.

## 7. Single-Artifact Hash Verification Plan

### 7.1 Preconditions

1. The user must have explicitly authorized the exact artifact path.
2. The path must be a single file path, not a directory.
3. No directory walk, recursion, or heuristic discovery is allowed.
4. No neighboring files may be assumed or inferred.
5. No copy or move operation is allowed.

### 7.2 Required metadata to record

For the single artifact, record:
1. `artifact_uri`
2. `artifact_type`
3. `sha256`
4. `file_size_bytes`
5. `hash_algorithm`
6. `computed_at`
7. `computed_by`
8. `metadata_only`

### 7.3 Verification flow

1. Receive one explicit artifact path from the user.
2. Confirm the path is exactly the single authorized file.
3. Compute hash only for that file.
4. Record file size and hash algorithm.
5. Store provenance metadata only.
6. Do not read or infer any other artifact in the directory.

### 7.4 Hash policy

1. Hash algorithm: `sha256`.
2. The hash must be computed only after explicit user authorization.
3. The hash calculation must target the exact file path only.
4. The result must be treated as metadata, not as a readiness claim.

## 8. Dry-Run Loading Plan

### 8.1 Preconditions

1. Hash verification must already be completed for the exact artifact.
2. Real loading still requires explicit main-controller approval.
3. This plan is only for structure validation.

### 8.2 Dry-run execution constraints

1. CPU-only.
2. `batch = 1`.
3. No gradient.
4. No real patient data.
5. No patient trace/evidence emission.
6. No diagnosis claim.
7. No GPU.
8. No production promotion.

### 8.3 Structure-only checks

The dry-run should verify:
1. ClinicalMLP input dimension = 36.
2. Output dimension = 2.
3. State-dict keys are structurally compatible.
4. Parameter shapes are consistent with the expected architecture.
5. The artifact can be inspected in a non-diagnostic validation context once explicitly approved.

### 8.4 Dry-run boundary

1. The dry-run is about structure matching, not diagnosis.
2. The dry-run must not be mistaken for clinical inference.
3. The dry-run must not be executed until the main controller approves the next step.

## 9. What Must Not Happen in Stage 52

1. No `torch.load`.
2. No real forward pass.
3. No real model inference.
4. No training.
5. No GPU.
6. No directory scanning.
7. No model-file copying.
8. No database schema changes.
9. No Alembic.
10. No Nginx.
11. No frontend changes.
12. No patient trace/evidence.

## 10. What Stage 53 Could Be

If Stage 52 is approved and the single-artifact metadata is ready, Stage 53 may be:
- `single-artifact CPU-only dry-run execution`

Stage 53 would still not be:
1. Production deployment.
2. Default activation.
3. Real diagnosis.
4. A replacement for the stub path.

## 11. Safety Statement

1. Stage 52 is a planning and readiness stage only.
2. The selected artifact is not yet a clinical model service.
3. The single-artifact verification is a metadata and structure exercise.
4. The system must remain stub-first until the main controller explicitly approves further steps.

## 12. Main-Controller Writeback Summary

1. Stage 52 document created for single-artifact hash verification and dry-run planning.
2. Clinical MLP is the recommended first artifact.
3. Recommended first artifact path: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/weights/fold1_best.pth`.
4. `fold1~fold5` are still not frozen as the final production selection.
5. Hash verification is exact-path only, SHA-256, no scanning.
6. Dry-run plan is CPU-only, batch=1, no gradient, structure-only.
7. No `torch.load`, no `.pth` loading, no training, no inference, no GPU.
8. Stage 53 is a possible next step only after main-controller approval.