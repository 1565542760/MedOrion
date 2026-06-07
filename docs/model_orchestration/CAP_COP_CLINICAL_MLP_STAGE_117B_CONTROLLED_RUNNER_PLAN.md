# CAP/COP Clinical MLP Stage 117B Controlled Runner Plan

## 1. Goal

Use the existing MRI3D conda environment as a short-term one-shot shadow runner so we can get a CAP/COP clinical MLP fold5 shadow output as quickly as possible.

This is a temporary bridge, not the long-term runtime architecture.

## 2. Non Goals

This stage does not:

- replace the long-term model-service approach
- write a formal recommendation
- write trace or evidence rows
- enable default or canary traffic
- train anything
- auto-train anything
- add imaging or multimodal execution
- add frontend display work

## 3. Runtime

Use the MRI3D conda environment:

- Python path: `/home/sygxdg/miniconda3/envs/MRI3D/bin/python`
- Torch was previously verified in Stage 53:
  - `torch 2.6.0+cu124`

Runtime constraints:

- `CUDA_VISIBLE_DEVICES=""`
- `no_grad`
- `eval`
- `batch=1`
- `concurrency=1`

## 4. Runner Script Placement

The runner should live under MedOrion-owned paths, not inside the research tree.

Recommended location:

- `/srv/medorion/app/model-runners/cap_cop_clinical_mlp_fold5_runner.py`

Any equivalent MedOrion-owned path is acceptable as long as:

- it does not modify the MRI3DModel research directory
- it reads artifacts only
- it communicates via JSON stdin/stdout or a temporary JSON file
- it does not scan directories for models

## 5. Exact Artifact Inputs

Allowed artifact reads:

- Fold5 weight file:
  - `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/weights/fold5_best.pth`
- Preprocess artifact:
  - `clinical_tabular_standardization_v1.json`
  - MedOrion artifact path: **to be confirmed**

Before load, the runner must verify SHA-256:

- `0b66192745f6c35d5158596e89db7bd1a2d6292ed66a0de4ca3f28c49fa9426a`

## 6. Input Contract

Runner input must include:

- `trace_id`
- `case_id`
- `patient_id`
- `input_snapshot_id`
- `model_version_id`
- `mapped_features` in fixed 36-feature order
- `not_for_diagnosis=true`

Input requirements:

- preserve `Striated_shadow.1`
- preserve CAP/COP label mapping:
  - `CAP = 0`
  - `COP = 1`

## 7. Output Contract

Runner output must include:

- `status`
- `logits` optionally
- `probabilities`
  - `CAP`
  - `COP`
- `candidate_label`
- `confidence`
- `uncertainty`
- `limitations`
  - `not_for_diagnosis`
  - `shadow_only`
  - `not_formal_recommendation`
- `error_code`
- `error_message`

## 8. Backend Integration Plan

Future backend one-shot flow:

1. Validate the snapshot
2. Build a sanitized runner JSON payload
3. Call the MRI3D Python subprocess with a timeout
4. Parse the runner JSON response
5. Write to `shadow_inference_runs` and `shadow_inference_outputs`
6. On failure, write `shadow_failed`
7. Do not allow silent fallback

## 9. Security Controls

- Load only the exact file path
- Verify SHA-256 before load
- Enforce a timeout
- Minimize environment inheritance
- Set `CUDA_VISIBLE_DEVICES=""`
- Use argv lists instead of shell string interpolation
- Run only one runner at a time
- Do not log patient payloads
- Do not place raw clinical payload into access audit
- Do not write recommendation, trace, or evidence

## 10. Failure Taxonomy

The runner should classify failures as:

- `runner_unavailable`
- `artifact_missing`
- `artifact_hash_mismatch`
- `preprocess_artifact_missing`
- `input_insufficient`
- `torch_load_failed`
- `inference_failed`
- `runner_timeout`
- `invalid_runner_response`

## 11. Stage 117C Recommendation

Recommended next step:

- implement the runner script only
- test it with a synthetic fixture or an existing ready snapshot
- do not wire backend immediately

If the standalone runner proves stable, then wire the backend one-shot endpoint in a second step.

## 12. Compliance Boundary

This plan does not:

- modify code
- load models
- call `torch.load`
- train
- perform real inference
- change the database
- run Alembic
- open the shadow switch
- add allowlist entries
- write recommendation, trace, or evidence
- modify the frontend
- copy or move model files
