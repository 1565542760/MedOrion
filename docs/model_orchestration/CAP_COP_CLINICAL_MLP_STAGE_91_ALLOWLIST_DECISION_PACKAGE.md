# Stage 91: CAP/COP Clinical MLP Fold5 Allowlist Decision Package

## 1. Decision Question

Should the exact model version b12f315a-7f44-491d-bf46-b0da73f6da03 be added to the clinical MLP shadow allowlist for a later config-only rehearsal?

Target allowlist:

CAP_COP_CLINICAL_MLP_SHADOW_ALLOWED_MODEL_VERSION_IDS

This package is for human governance decision-making only.

## 2. Important Clarification

Approving allowlist inclusion does not mean any of the following:

- shadow switch enablement
- model loading
- torch.load
- real inference
- live inference
- default assignment
- canary assignment
- recommendation write
- case trace write
- evidence write

## 3. Candidate Readiness Summary

The fold5 registry metadata baseline is now in place.

- Formal fold5 metadata row exists
- Provenance has been finalized
- artifact_hash is present
- file_size_bytes is present
- adapter_code is explicit
- metadata_only = true
- artifact_not_loaded = true
- not_for_diagnosis = true
- shadow is still not enabled

## 4. Risks

Key risks to keep visible:

- Mistaking allowlist entry for model enablement
- Mistaking shadow for recommendation
- Mistaking metadata readiness for clinical validation
- Treating internal retrospective evidence as if it were an independent held-out clinical validation
- Proceeding without a governance note that the usage remains audit-only and not-for-diagnosis

## 5. GO / NO-GO Options

### NO-GO

- Do not add the version to the allowlist
- Keep the allowlist empty
- Keep the shadow switch false
- Continue governance, validation, and external test planning only

### GO allowlist-only rehearsal

- Add only this exact model version to the allowlist in a later config-only rehearsal
- Keep ENABLE_CAP_COP_CLINICAL_MLP_SHADOW = false
- Verify that eligibility moves past the allowlist gate
- Do not load the model
- Do not call torch.load
- Do not run inference

No GO option is provided for live inference or default/canary use.

## 6. If GO Allowlist-Only

A later Stage 92 may do only the following:

- config-only allowlist update or rehearsal
- keep ENABLE_CAP_COP_CLINICAL_MLP_SHADOW = false
- verify eligibility transitions from model_not_allowlisted to the next gate
- do not load a model
- do not call torch.load
- do not run inference

## 7. If NO-GO

If NO-GO remains the decision:

- keep allowlist empty
- keep shadow switch false
- continue governance, validation, and external test planning

## 8. Required Sign-Off Fields

If a future GO allowlist-only decision is made, record the following:

- decision: GO allowlist-only or NO-GO
- approved model_version_id
- approver
- date
- rollback owner
- verification owner
- note acknowledging not_for_diagnosis / audit-only usage
