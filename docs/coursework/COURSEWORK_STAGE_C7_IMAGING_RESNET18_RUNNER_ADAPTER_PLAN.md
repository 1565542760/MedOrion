# Coursework Stage C7: CAP/COP Imaging ResNet18 Runner / Adapter Compatibility Plan

Date: 2026-06-09

## Purpose
Stage C7 is a compatibility-planning stage for the CAP/COP imaging ResNet18 route.

The goal is to align the course project with the machine-vision requirement by defining how the imaging runner, adapter, and input contract would fit together if the team later decides to prototype a controlled shadow path.

This stage is planning only:
- no model load,
- no `torch.load`,
- no training,
- no scanning unknown model directories,
- no copy/move of model files,
- no live inference,
- no trace/evidence writes,
- no database changes,
- no frontend changes.

## Current Imaging / Model-Service Status

### Imaging / multimodal adapter state
The model-service currently contains three CAP/COP real-adapter skeletons:
- `clinical_mlp_cap_cop_classifier@v1.0.0`
- `imaging_resnet18_cap_cop_classifier@v1.0.0`
- `multimodal_resnet18_cap_cop_classifier@v1.0.0`

For all three:
- `real_adapter_enabled = false`
- lifecycle state is `shadow`
- approval state is metadata-only / registered-only
- `/infer` remains disabled for real adapters

### Model-runners state
Only one runtime runner exists today:
- `cap_cop_clinical_mlp_fold5_runner.py`

There is no imaging ResNet18 runner and no multimodal ResNet18 runner yet in `app/model-runners`.

### Backend schema state
The backend already separates:
- disease-task feature sets,
- model input schemas,
- clinical feature mappings,
- imaging-input candidate contracts.

However, the imaging path is still a contract-and-metadata path, not a runnable visual serving path.

## Known Artifact / Provenance State

The staged CAP/COP artifact folder is proven to exist and is intentionally isolated from the original research tree:
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/`

Known contents include:
- `imaging_resnet18_unimodal/`
- `multimodal_resnet18_bigdata/`
- `clinical_mlp/`
- `preprocessing/`
- `provenance/`

The staged README states that:
- the folder is metadata/artifact staging only,
- models have not been loaded by MedOrion,
- no real inference has been enabled,
- training was not performed during staging,
- the files must not be committed to Git.

The provenance source manifest states that:
- the source root is `/home/sygxdg/MRI3DModel`,
- the original research folder was not modified,
- the imaging and multimodal artifacts came from research artifact directories,
- raw datasets were not copied into the staged artifact area.

The provenance metrics summary provides fold-level metrics for the research families, but these are research artifacts, not a live runner contract.

## What We Can Prove Today vs What We Cannot Assume

### We can prove
- imaging and multimodal CAP/COP research artifacts exist in the staged folder;
- model-service metadata entries exist for imaging and multimodal CAP/COP adapter skeletons;
- backend schema metadata already names `ct_image` / `mri_image` and supports model input schema separation;
- the current runtime state is disabled / shadow-only.

### We cannot assume
- that the imaging weights are already validated in a live runner;
- that the exact preprocessing behavior is ready for model-service execution;
- that the imaging path is clinically validated;
- that a PNG/JPEG demo is equivalent to a real CT/NIfTI path;
- that the current product schema is the same as the training contract;
- that multimodal is ready just because metadata exists;
- that a runner can safely scan directories for other series or fallback files.

## Known Blockers Before a Real Imaging Runner

A future imaging runner still needs the following confirmed before any actual execution path is attempted:
- exact input image format contract,
- preprocessing policy,
- artifact path and hash for the exact allowed weight file,
- label mapping,
- runtime environment,
- output calibration/limitations,
- image de-identification and reference boundary,
- timeout and batch/concurrency constraints,
- runner output schema,
- shadow / not-for-diagnosis boundary.

### Artifact path / hash note
For this planning stage, we do **not** need to execute real loading.
If a later prototype is ever considered, it must be approved against an exact artifact path and hash, and the team must not scan unknown model directories or guess neighboring files.

## Proposed Runner Contract

A future imaging runner should accept a controlled reference object rather than raw bytes as the primary contract.

### Suggested request fields
- `trace_id`
- `case_id`
- `patient_id`
- `input_asset_id`
- `storage_uri`
- `modality`
- `source_type`
- `deidentified`
- `not_for_diagnosis`
- `provenance_json`
- `quality_flags_json`
- `runtime_options`
- `idempotency_key`

### Reference rules
The runner should only consume an explicitly referenced imaging object:
- a managed storage URI,
- or a backend-tracked input asset ID.

It must not:
- scan the object-store bucket for other files,
- infer the correct series from neighboring folders,
- silently substitute another file,
- treat a demo sample as a verified clinical scan.

### Safety rules
The runner must preserve:
- `trace_id` from upstream,
- `case_id` / `patient_id` linkage,
- `not_for_diagnosis = true`,
- `deidentified = true` where applicable,
- shadow-only semantics.

## Preprocessing Plan

The imaging preprocessing plan should remain explicitly versioned and should not be invented on the fly.

### Candidate preprocessing details that still need confirmation
- CT vs NIfTI handling,
- 2D slice versus 3D volume representation,
- input size / resize policy,
- spacing / resampling policy,
- channel layout,
- normalization strategy,
- windowing/window-level handling if CT is used,
- whether a course demo uses synthetic or de-identified images,
- whether a course demo uses a 2D slice or a 3D volume.

### Conservative default for the plan
The safest course-facing plan is:
- CT / NIfTI-style input contract,
- `float32`,
- channel-first for volume-based handling,
- explicit resize/resample policy,
- CPU-only,
- `eval()` and `torch.no_grad()` when a later prototype is authorized,
- `batch=1`,
- timeout guarded.

### What must not be written as already complete
Do not claim that these preprocessing details are finalized unless a separate artifact or contract explicitly confirms them.

## Output Schema Plan

A future imaging shadow output should contain at least:
- `shadow_run_id`
- `trace_id`
- `case_id`
- `patient_id` if permitted by the surrounding contract
- `input_asset_id`
- `model_version_id`
- `artifact_hash`
- `adapter_code`
- `prediction_raw`
- `prediction_probability`
- `candidate_label`
- `confidence`
- `uncertainty`
- `limitations`
- `runtime_env`
- `not_for_diagnosis`

Optional display helpers:
- `heatmap_reference`
- `region_state_summary`
- `sync_state`
- `error_code`

## How Imaging Fits With Clinical MLP and Future Multimodal

### Clinical MLP coexistence
Clinical MLP remains the tabular shadow baseline and should stay separate from imaging.

It can coexist as:
- a baseline/control path,
- a provenance example,
- a comparison against imaging outputs.

It should not be treated as the machine-vision route.

### Imaging ResNet18 role
Imaging ResNet18 is the primary machine-vision candidate for the course.

Its role is to:
- consume CT/NIfTI-style input;
- produce a shadow-only CAP vs COP candidate label;
- support a lung-state digital twin mapping;
- provide the visually defensible machine-vision narrative.

### Multimodal ResNet18 later role
Multimodal ResNet18 should be planned as a later extension that combines:
- imaging input,
- clinical table features,
- the CAP/COP feature contract,
- the same provenance / shadow boundaries.

It should not be brought in until the imaging-only contract is stable enough to avoid ambiguity.

## Digital Twin Mapping

Imaging output should map into a case-level lung-state twin, not into a formal diagnosis string.

### Suggested mapping dimensions
- lung-region state,
- imaging-derived candidate label,
- uncertainty,
- provenance,
- missing-input or incomplete-ingress state,
- doctor-review requirement,
- quality-review requirement,
- shadow/not-for-diagnosis state.

### Mapping rule
The digital twin should express:
- what the imaging model sees,
- how confident it is,
- what provenance produced it,
- what follow-up review is required,
- and what is still unknown.

It should not pretend to be a clinical verdict.

## Experimental Validation Suggestions

If the team later prototypes the runner, the course writeup can evaluate:
- accuracy,
- latency,
- robustness,
- output consistency,
- case-level state synchronization,
- visualization correctness,
- uncertainty visibility.

This stage does not execute those tests. It only lists them as the likely validation surface.

## What Cannot Be Claimed

Do not claim:
- diagnosis,
- recommendation,
- default/canary readiness,
- production deployment,
- external validation,
- automatic training,
- that the current imaging skeleton is already a runnable clinical pipeline,
- that the course machine-vision requirement is already satisfied by clinical MLP,
- that multimodal is ready for use without an explicit runner and input contract.

## Recommended Next Stage

The most useful next step is **backend bridge / API skeleton** for the imaging input contract, because that is the least ambiguous prerequisite for both runner work and the digital twin demo.

Reason:
- the input reference contract must be frozen before the runner can be safely prototyped;
- the frontend twin mock depends on a stable backend reference format;
- runner work should wait until the exact imaging input boundary is explicit.

If the project wants to move faster on the visual demo, the frontend mock can follow once the backend contract is stable.

## Read-only Sources Used

- `/home/sygxdg/MedOrion/docs/coursework/COURSEWORK_STAGE_C2_VISION_TASK_AND_IMAGING_READINESS.md`
- `/home/sygxdg/MedOrion/docs/coursework/COURSEWORK_STAGE_C3_IMAGING_RESNET18_PROVENANCE_AND_RUNNER_PLAN.md`
- `/home/sygxdg/MedOrion/docs/backend/COURSEWORK_STAGE_C4_IMAGING_INPUT_API_CONTRACT.md`
- `/home/sygxdg/MedOrion/docs/traceability/TRACEABILITY_COURSEWORK_STAGE_C5_IMAGING_INPUT_SCHEMA_REVIEW.md`
- `/home/sygxdg/MedOrion/docs/model_orchestration/CAP_COP_CLINICAL_MLP_STAGE_117B_CONTROLLED_RUNNER_PLAN.md`
- `/srv/medorion/app/model-runners/cap_cop_clinical_mlp_fold5_runner.py`
- `/srv/medorion/app/model-service/app/adapters/cap_cop/`
- `/srv/medorion/app/backend/app/modules/model_input/catalog.py`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/README.md`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/source_manifest.json`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/Best_Metrics_Summary.csv`