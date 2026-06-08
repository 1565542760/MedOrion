# Coursework Stage C3: CAP/COP Imaging ResNet18 Provenance and Runner Plan

Date: 2026-06-08

## Purpose
This document turns the Stage C2 recommendation into a more concrete imaging plan for MedOrion coursework.

The course now has a clear vision task direction:
- CAP/COP CT/NIfTI imaging classification as the machine-vision component;
- case-level lung-state digital twin as the state-mapping / visualization component;
- clinical MLP only as a tabular baseline or control.

This stage remains planning only. It does not load models, does not run inference, does not write trace/evidence, and does not change the repository or database.

## Current Imaging / Multimodal / Model-Service Status

### Model-service
- CAP/COP has three real-adapter skeleton versions registered.
- The model-service returns them as `shadow`, `registered_only`, and `real_adapter_enabled=false`.
- `/infer` remains disabled for real adapters.
- There is no live imaging inference path.

### Model-runners
- The only runner that currently exists is the CAP/COP clinical MLP fold5 runner.
- There is no imaging ResNet18 runner and no multimodal ResNet18 runner in `model-runners` yet.

### Backend / schema
- The backend model input catalog already separates disease-task feature sets and model input schemas.
- Imaging-related schema metadata exists, but the repo still lacks a real image ingress path and a runner lane for actual imaging evaluation.

### Artifact / provenance
- The CAP/COP staged artifact directory contains imaging ResNet18 and multimodal ResNet18 research artifacts, notebooks, logs, preprocessing scripts, and provenance files.
- These assets are usable as provenance evidence for a course report, but they are not yet a runnable imaging service.

## Provenance Evidence That Can Be Proven Today

The following provenance statements are supported by read-only inspection:

1. The CAP/COP staged artifact folder exists at:
   - `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/`

2. The staged folder explicitly contains:
   - `imaging_resnet18_unimodal/`
   - `multimodal_resnet18_bigdata/`
   - `clinical_mlp/`
   - `preprocessing/`
   - `provenance/`

3. The staged README states:
   - the folder is metadata/artifact staging only;
   - models have not been loaded by MedOrion;
   - no real inference has been enabled;
   - training was not performed during staging;
   - the files must not be committed to Git.

4. The provenance source manifest states:
   - the source root is `/home/sygxdg/MRI3DModel`;
   - the original research folder was not modified;
   - clinical MLP notebook/weights were copied via scp;
   - imaging ResNet18 and multimodal ResNet18 came from research artifact directories;
   - `processed_dataset` and the raw clinical CSVs were not copied.

5. The provenance metrics summary provides fold-level metrics for:
   - `ResNet_Unimodal`
   - `DenseNet_Unimodal`
   - `ResNet_Multimodal_Big`
   - `DenseNet_Multimodal_Big`

These files are enough to prove that imaging / multimodal research artifacts exist and were staged deliberately, but not enough to claim a finished clinical imaging pipeline.

## Imaging ResNet18 Artifact / Metadata Summary

The imaging family currently has the following provable state:

- model family: `imaging_resnet18_cap_cop_classifier`
- adapter code: `imaging_resnet18_cap_cop_adapter`
- adapter status in model-service: skeleton / disabled / metadata-only
- artifact family directory: `imaging_resnet18_unimodal/`
- artifact type in registry: `.pth`
- model-service `real_adapter_enabled`: `false`
- model-service lifecycle state: `shadow`
- provenance files: present in the staged artifact folder
- notebook: present (`restnet.ipynb`)
- logs: present for 5 folds
- weight files: present for folds 1-5

The multimodal family is similar:

- model family: `multimodal_resnet18_cap_cop_classifier`
- adapter code: `multimodal_resnet18_cap_cop_adapter`
- status: skeleton / disabled / metadata-only
- artifact directory: `multimodal_resnet18_bigdata/`
- provenance files: present
- notebook: present (`restnet_training_array_nii_notpre_add_label_mut.ipynb`)
- logs: present for 5 folds
- weight files: present for folds 1-5

## What Can Be Claimed About Visual Input

### Primary course-facing visual input contract
The best course-facing contract is:
- CT / NIfTI-style imaging input for CAP/COP imaging classification shadow.

This is the only route that is both scientifically defensible and aligned with the staged imaging artifact family.

### What is feasible in the course project
1. **CT/NIfTI-style imaging input**
   - Feasible as the conceptual primary input contract.
   - It matches the staged imaging ResNet18 family.
   - It should be described as a shadow or research prototype input, not a clinical ingress path.

2. **2D slice extraction**
   - Feasible only as a presentation or demo simplification.
   - Can be used to show a visual sample or explain the state mapping.
   - Must not be described as the canonical training contract if the provenance points to 3D / CT-NIfTI-style processing.

3. **PNG/JPEG demo images**
   - Feasible only as a synthetic / illustrative demonstration layer.
   - Good for UI mockups, slides, or a safe visual fallback.
   - Must be explicitly labeled as demo / simulation if used.

4. **Synthetic visual samples**
   - Feasible as a fallback when a real image ingress path cannot be completed in time.
   - Must be described as non-clinical simulation.
   - Cannot be used to claim actual clinical validation of the imaging model.

### What should not be claimed as real clinical validation
Do not say the project has clinically validated imaging unless there is an explicitly documented held-out evaluation path or an approved real-run pipeline.

Do not claim:
- real-time hospital PACS integration;
- production DICOM pipeline;
- externally validated clinical imaging performance;
- imaging model default/canary status;
- that a demo PNG equals a real CT/NIfTI validation path.

## Recommended Runner / Adapter Plan

This stage only defines the plan; it does not implement it.

### Intended runner role
A future imaging runner or adapter should:
- accept a clearly identified image object or file path;
- convert the input into a model-ready tensor;
- run CPU-only, `eval()`, `torch.no_grad()`, `batch=1`;
- respect timeout limits;
- emit shadow-only output metadata;
- keep provenance and uncertainty visible.

### Suggested input reference patterns
The runner should support one of these controlled input references:

1. **Explicit file path**
   - e.g. `ct_volume_path`, `nifti_path`, or a controlled staging URI.
   - Best for reproducibility and provenance.

2. **Uploaded object reference**
   - e.g. a backend-managed `image_object_id` or `input_snapshot_id`.
   - Best for integrating with the doctor workbench and traceable input snapshots.

3. **Synthetic sample reference**
   - e.g. a demo object ID or illustrative image URI.
   - Best only for simulation / presentation, not for claiming clinical performance.

### Preprocessing boundary
A future imaging runner should keep preprocessing explicit and narrow:
- input kind: `ct` / `nifti` / explicitly labeled demo image
- dtype: `float32`
- channel order: channel-first if volume-based
- normalization: z-score or the model’s documented equivalent
- resize / resample: model contract specific
- batch size: 1
- no gradient
- timeout guarded

The runner should not silently switch preprocessing rules. If the image contract is not met, it should return an explicit status instead of fabricating a successful result.

### Shadow output fields
A future shadow output should include at least:
- `shadow_run_id`
- `trace_id`
- `case_id`
- `model_version_id`
- `artifact_hash`
- `input_reference`
- `prediction_raw`
- `prediction_probability`
- `candidate_label`
- `runtime_env`
- `error_code`
- `not_for_diagnosis`

Optional but useful:
- `heatmap_reference`
- `region_state_summary`
- `uncertainty`
- `limitations`

### Heatmap / region-state handling
Heatmap or region-state output should be treated as optional display support, not as mandatory proof of clinical validity.

It is useful because:
- it helps explain why a case-level twin state changed;
- it supports a safer course presentation;
- it makes the twin more interpretable.

But it must not be described as clinical ground truth.

## Digital Twin State Mapping

The recommended twin is a **case-level lung-state twin**.

### Mapping concept
Imaging output should update a twin state that summarizes:
- lung-region involvement;
- imaging-derived state;
- model provenance;
- missing-data or incomplete-ingress state;
- doctor review state;
- quality-review state;
- shadow status;
- not-for-diagnosis state.

### Suggested state mapping structure
```json
{
  "case_id": "...",
  "trace_id": "...",
  "lung_region_state": {
    "upper_left_lung": "...",
    "lower_left_lung": "...",
    "right_upper_lung": "...",
    "right_middle_lung": "...",
    "right_lower_lung": "..."
  },
  "imaging_state": {
    "candidate_label": "CAP|COP|unknown",
    "confidence": "...",
    "uncertainty": "...",
    "heatmap_available": true
  },
  "model_provenance": {
    "model_version_id": "...",
    "artifact_hash": "...",
    "runner_mode": "shadow"
  },
  "quality_state": {
    "doctor_review_required": true,
    "quality_review_required": true
  },
  "shadow_state": {
    "not_for_diagnosis": true,
    "shadow_only": true
  }
}
```

### Interpretation rule
The twin should never present the imaging result as a diagnosis. It should show a state transition or a state summary for review.

Examples of state mapping language that are safe:
- “imaging-derived CAP/COP candidate state”
- “case-level lung-state summary”
- “shadow-only perception output”
- “provenance-aware visual state mapping”

## Experimental Validation Suggestions

The course report can evaluate the vision/twin chain using metrics appropriate to the chosen visual path:

### Imaging metrics
- accuracy
- precision
- recall
- F1
- confusion matrix
- ROC-AUC if probabilities are meaningful
- latency / response time
- robustness under controlled perturbation

### Twin / system metrics
- state consistency
- state mapping correctness
- UI response time
- synchronization latency
- missing-data handling correctness
- audit/provenance completeness
- failure-mode clarity
- case-level visualization validation

### Presentation / demo metrics
- screenshot correctness
- ability to explain the twin state
- visibility of provenance and uncertainty
- no accidental diagnosis framing

## What Cannot Be Claimed

Do not claim:
- that the imaging path is already live in model-service;
- that imaging ResNet18 has been clinically validated;
- that a PNG/JPEG demo is equivalent to CT/NIfTI validation;
- that heatmaps prove diagnosis;
- that the multimodal model is ready for course use unless its visual and tabular ingress is explicitly defined;
- that the system is a medical device;
- that the shadow path is default or canary.

## Recommended Next Stage

For the course project, the next step should be:

1. **Backend image input API** if we need a formal way to reference visual inputs and connect them to the twin state.
2. **Frontend digital twin mock** if the goal is to present the case-level state visually for the report and defense.
3. **Runner prototype** only if a controlled demonstration path is needed and the input contract is already stable.

### My recommendation
Prioritize **backend image input API** first, because the course story needs a precise visual input contract before the UI can be considered trustworthy.

The frontend twin mock should follow once the input contract is fixed.

## Provenance / Source References

Read-only sources used for this plan:
- `/home/sygxdg/MedOrion/docs/coursework/COURSEWORK_STAGE_C2_VISION_TASK_AND_IMAGING_READINESS.md`
- `/home/sygxdg/MedOrion/docs/coursework/CAP_COP_DIGITAL_TWIN_SCIENTIFIC_PROTOCOL.md`
- `/home/sygxdg/MedOrion/docs/coursework/COURSE_DELIVERABLES_CHECKLIST.md`
- `/home/sygxdg/MedOrion/docs/model_orchestration/CAP_COP_CLINICAL_MLP_STAGE_127_FEATURE_CONTRACT_REVIEW.md`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/README.md`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/source_manifest.json`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/Best_Metrics_Summary.csv`
- `/srv/medorion/app/model-service/app/services/model_registry.py`
- `/srv/medorion/app/model-service/app/adapters/cap_cop/registry.py`
- `/srv/medorion/app/model-service/app/adapters/cap_cop/imaging_resnet18_adapter.py`
- `/srv/medorion/app/model-service/app/adapters/cap_cop/multimodal_resnet18_adapter.py`
- `/srv/medorion/app/backend/app/modules/model_input/catalog.py`
- `/srv/medorion/app/backend/app/modules/model_input/router.py`
- `/srv/medorion/app/model-runners/cap_cop_clinical_mlp_fold5_runner.py`
