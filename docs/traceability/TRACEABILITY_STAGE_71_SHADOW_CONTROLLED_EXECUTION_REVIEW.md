# Traceability Stage 71 Review: Controlled Shadow Execution Design

## Review Conclusion

Stage 71R review conclusion: **conditionally passed**.

The design direction is correct, but the Stage 71A design document required three tightening edits before checkpoint:

1. State `not_for_diagnosis=true` as a runtime invariant.
2. Make the single explicit approved artifact reference rule stronger.
3. Clean small encoding/spelling issues, especially in the shadow audit write scope section.

Those required edits have been applied in the Stage 71A design document.

## Shadow Switch Review

The proposed switch design is safe:

```text
ENABLE_CAP_COP_CLINICAL_MLP_SHADOW=false
```

It defaults to disabled and may only be controlled by backend configuration. It must not be overrideable by frontend parameters, ordinary request fields, LLM scheduler output, model registry metadata alone, or artifact metadata alone.

If disabled, the path must fail closed with an explicit `shadow_disabled` status.

## Shadow Audit / Case Trace-Evidence Boundary

The boundary is correct.

A controlled shadow execution may write only to:

- `shadow_inference_runs`
- `shadow_inference_outputs`

It must not write:

- `recommendations`
- case `trace_events`
- `evidence_nodes`
- `evidence_edges`

Shadow outputs are audit/evaluation material only. They are not formal clinical recommendations and must not be added to the case evidence chain by default.

## Required Feature Handling

The design is consistent with the existing model input and missing-value consultation rules.

If required features are missing, the only allowed paths are:

- missing-value consultation
- explicit default strategy
- `insufficient_data_for_assessment`

The system must not silently fallback, hard-code substitute values, or present default-applied values as doctor-provided values.

## not_for_diagnosis / no_silent_fallback Review

Both rules are directionally correct and now strengthened in the design document.

`not_for_diagnosis=true` must be a mandatory runtime invariant for every shadow run and output.

`no_silent_fallback` must cover missing input, disabled switch, missing approved artifact, unavailable model, and any unsupported disease/task/model combination.

## Artifact Reference Review

The artifact rule is now sufficiently explicit.

A future implementation may only use a single explicit approved artifact reference. It must not scan directories, glob files, infer adjacent fold files, substitute another artifact, or treat a directory path as permission to discover models.

## Recommendation

Stage 72 can begin implementing a disabled-by-default code skeleton after this checkpoint.

Stage 72 must still avoid:

- default promotion
- live doctor-facing inference
- formal recommendation writes
- case trace/evidence writes
- training or automatic training
- broad `.pth/.pt/.onnx/.ckpt/.safetensors` operations

## Compliance Confirmation

This review and document tightening did not:

- modify database schema
- execute Alembic
- load a model
- train or run real inference
- enable Nginx
- modify frontend
- scan, copy, move, or guess model files
