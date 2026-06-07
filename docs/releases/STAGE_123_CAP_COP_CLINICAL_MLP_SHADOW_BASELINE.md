# Stage 123 - CAP/COP Clinical MLP Shadow Usable Baseline

Date: 2026-06-08

Current stage: Stage 123 - CAP/COP clinical MLP shadow usable baseline.

## Summary

The CAP/COP clinical MLP fold5 path is now a usable shadow baseline. The system can take a validated `case_model_input_snapshot`, call the controlled CPU-only fold5 runner through the backend one-shot bridge, write shadow audit run/output records, and display the result in the frontend shadow audit page with explicit safety warnings.

This is a shadow/audit capability only. It is not a clinical diagnosis path and not a formal recommendation path.

## Completed Baseline

- Fold5 model metadata and provenance were finalized.
- The authorized fold5 artifact hash was verified.
- `case_model_input_snapshot` records can be saved, read, summarized, and protected behind RBAC/privacy boundaries.
- The clinical MLP fold5 runner can load the authorized artifact and run CPU-only forward.
- The backend one-shot bridge can call the runner and write `shadow_inference_runs` / `shadow_inference_outputs`.
- Shadow output metadata includes calibration and limitation warnings.
- The frontend shadow audit page can display the clinical MLP shadow result with warnings.
- The path still does not write recommendations.
- The path still does not write case `trace_events`, `evidence_nodes`, or `evidence_edges`.

## Example Shadow Record

Representative Stage 119/122 clinical MLP shadow result:

- `shadow_run_id = shadow_73c5d9bc56ee5644`
- `output_id = out_1eebf2c944505ae4`
- `candidate_label = COP`
- `probabilities = CAP 0.0 / COP 1.0`
- `calibrated = false`
- `not_externally_validated = true`
- `requires_doctor_review = true`
- `requires_quality_review_before_clinical_use = true`

The extreme probability is not clinical certainty. The result is a shadow audit artifact for review, not a diagnosis.

## Explicit Non-Claims

This baseline is not:

- A formal diagnosis system.
- A formal recommendation path.
- A default model.
- A canary model.
- A production deployment.
- External clinical validation.
- An automatic training system.
- A doctor replacement.

## Safety and Governance Boundaries

The clinical MLP shadow baseline must keep these boundaries visible:

- `not_for_diagnosis=true`.
- Shadow only.
- Not a formal recommendation.
- Probability uncalibrated.
- Extreme probability is not clinical certainty.
- Not externally validated.
- Requires doctor review.
- Requires quality review before clinical use.
- Temporary runner bridge; long-term target remains model-service or a dedicated inference-service.

## Recommended Next Stage Options

- A. Imaging ResNet18 provenance + runner plan, if the goal is three-model CAP/COP shadow coverage.
- B. Multimodal ResNet18 provenance + runner plan, after imaging or in a separate reviewed lane.
- C. Model-service / inference-service migration away from the temporary runner bridge, if the goal is long-term architecture.
- D. Clinical MLP further validation / external held-out-set plan, if the goal is clinical reliability.
- E. Access/shadow audit frontend polish later.

Main-controller recommendation:

- Choose A if the next product goal is three-model CAP/COP shadow coverage.
- Choose C if the next architecture goal is durable model runtime.
- Choose D if the next safety goal is clinical reliability and calibration evidence.

## Compliance Notes

This status update is documentation only. It does not change code, database schema, Alembic state, runtime configuration, model files, shadow switch state, recommendation behavior, trace/evidence behavior, or frontend runtime behavior.
