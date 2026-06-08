# Coursework Stage C2: Vision Task Definition and Imaging Readiness

Date: 2026-06-08

## Purpose
This document answers a narrow course question: what machine-vision task and what digital-twin expression are currently realistic for MedOrion, given the existing repo state and the course requirements.

The goal is to keep the course project scientifically defensible:
- machine vision must be explicit;
- the digital twin must be case-level and explainable;
- the result must remain doctor-assistive, not diagnostic;
- clinical MLP can only be a tabular shadow baseline or control, not the machine-vision主体.

## Current Capability Summary

| Area | Current state | Notes |
| --- | --- | --- |
| Clinical MLP CAP/COP | Usable shadow baseline | Shadow-only, not diagnosis, not default/canary |
| Imaging ResNet18 | Adapter skeleton / disabled | Registered in model-service, no real load |
| Multimodal ResNet18 | Adapter skeleton / disabled | Registered in model-service, no real load |
| Model-service | Stub + CAP/COP skeleton registry | `/models` lists 3 CAP/COP real-adapter skeleton versions; all `real_adapter_enabled=false` |
| Model-runners | Only clinical MLP fold5 runner exists | No imaging or multimodal runner is present |
| Model registry | Metadata + lifecycle skeleton exists | CAP/COP image/multimodal model metadata exists, but remains disabled |
| Model input schema | Skeleton exists | Supports `ct_image` / `mri_image` in schema metadata, but not a visual data ingress pipeline |
| Digital twin visualization | Shadow audit / lineage exists | No dedicated imaging twin panel yet |
| Artifact provenance | Available for staged artifacts | Research artifacts and provenance files exist under `/srv/medorion/models/...` |
| Visual data entry | Missing as a runnable course path | No explicit CT/NIfTI upload or image/video ingestion workflow in the frontend/backend |

## What the Repo Already Gives Us

The repo already contains useful CAP/COP imaging-related assets:
- `imaging_resnet18_unimodal/` weights, notebooks, and logs
- `multimodal_resnet18_bigdata/` weights, notebooks, logs, and preprocessing artifacts
- `preprocessing/` scripts and provenance files
- model-service metadata entries for imaging and multimodal CAP/COP adapters
- backend model-input schema skeletons that can already name `ct_image` / `mri_image`

That means the project is not starting from zero. The missing piece is the last-mile machine vision path: a clearly defined visual input source, a runnable or at least demonstrable visual perception task, and a twin visualization that makes the vision output legible.

## Course Requirement Gaps

The course explicitly requires:
1. image/video data acquisition or source description;
2. machine vision analysis;
3. state mapping;
4. digital twin display;
5. experimental validation.

Current MedOrion gaps for this course:
- no explicit CT/NIfTI or image/video acquisition path in the front-end or backend UI;
- no imaging runner wired as a course demo path;
- no dedicated digital twin panel for lung-region state or imaging-derived state;
- no course-ready experimental chain that can honestly be described as a vision pipeline without extra work;
- clinical MLP alone cannot satisfy the vision requirement.

## Relevant Repo State

### Imaging / Multimodal / Model-service
- `model-service` currently exposes 5 model entries total.
- CAP/COP has three real-adapter skeleton versions registered:
  - `clinical_mlp_cap_cop_classifier@v1.0.0`
  - `imaging_resnet18_cap_cop_classifier@v1.0.0`
  - `multimodal_resnet18_cap_cop_classifier@v1.0.0`
- All three are `shadow`, `registered_only`, and `real_adapter_enabled=false`.
- `/infer` remains disabled for real adapters.
- There is no active live imaging inference path.

### Model-runners
- Only one runner exists today: the CAP/COP clinical MLP fold5 runner.
- There is no imaging ResNet18 runner or multimodal ResNet18 runner yet.
- So the imaging side has provenance and metadata, but no mature execution lane in `model-runners`.

### Model registry and input schema
- The backend already separates:
  - disease-task feature sets,
  - model input schemas,
  - clinical feature mappings.
- CAP/COP image/multimodal schema metadata already exists in the catalog.
- This is enough to support a course-facing schema contract, but not enough by itself to claim a finished visual pipeline.

### Artifact provenance
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/` contains:
  - imaging ResNet18 artifacts,
  - multimodal ResNet18 artifacts,
  - notebooks,
  - logs,
  - preprocessing scripts,
  - provenance files.
- The repository notes that raw training datasets were intentionally not copied into the artifact area.
- That is good for governance, but it also means the course report must be honest about the visual data path if no separate image ingress is added.

## Recommended Vision Task Definition

### Primary recommendation
Use **CAP/COP CT/NIfTI-based imaging classification shadow** as the explicit machine-vision task, with a **case-level lung-state digital twin** as the visualization target.

A precise task statement could be:

> Use CAP/COP imaging perception on CT/NIfTI-style input to produce a shadow-only CAP vs COP classification, then map the output into a case-level digital twin that summarizes lung-region involvement, model provenance, missing-data state, and quality-review state.

Why this is the best fit:
- it is a real machine-vision task, not only a tabular task;
- it matches the existing imaging ResNet18 / multimodal ResNet18 artifact family;
- it can be described conservatively as shadow / research prototype;
- it naturally supports a digital twin state model;
- it avoids pretending that clinical MLP is the vision task.

### Recommended twin expression
The digital twin should be a **case-level disease-state twin**, not a hospital-scale or organ-simulation twin.

Recommended twin fields:
- `case_id`
- `trace_id`
- `lung_region_state`
- `imaging_state`
- `clinical_state`
- `model_provenance`
- `missing_value_state`
- `quality_review_state`
- `shadow_state`
- `not_for_diagnosis`

Recommended visual form:
- a small interactive panel or page;
- a state diagram / case card / timeline;
- optional heatmap or region-state summary;
- provenance and uncertainty visible at the same time.

This is scientifically safer than a full 3D fantasy twin, and much more feasible for the current repo.

## Alternative Technical Routes

### Route A - Recommended
**CAP/COP imaging classification shadow + case-level twin display**

- Vision task: CT/NIfTI binary classification (CAP vs COP) with shadow-only output.
- Twin: case-level lung-state and provenance state display.
- Strength: best fit to existing imaging ResNet18 / multimodal ResNet18 artifacts and the course requirement.
- Limitation: still needs a clear visual data ingress and a demo-ready runner or safe simulation wrapper.

### Route B - Explainability-first variant
**Imaging feature-map / heatmap / region-state-driven twin**

- Vision task: same imaging classifier, but the report focuses on explainability outputs and region-state mapping.
- Twin: display uncertainty, heatmap summary, and lung-region involvement.
- Strength: easier to explain in a course defense.
- Limitation: still depends on the imaging classifier path being defined.

### Route C - Simulation fallback
**Synthetic or explicitly de-identified visual sample demo**

- Vision task: a clearly labeled non-clinical simulation or synthetic visual example.
- Twin: visual state demo built from simulated or illustrative inputs.
- Strength: safest if the real image ingress path cannot be completed in time.
- Limitation: the report must explicitly say it is a simulation and not a clinical validation of real imaging performance.

## Most Recommended Route

**Recommended route: Route A, with Route B as the presentation layer.**

If the imaging ingress or demo path remains blocked, use **Route C only as a fallback**, and state that it is a simulation-only visual verification path.

Why Route A is the best overall choice:
- it is the most aligned with the course requirement for machine vision;
- it matches the staged imaging ResNet18 / multimodal ResNet18 assets already present in MedOrion;
- it can stay conservative because MedOrion already labels the CAP/COP shadow path as `not_for_diagnosis`;
- it gives the report a clear machine-vision story instead of a purely tabular one.

## Clinical MLP Boundary for the Course

Clinical MLP may be used only as:
- a tabular shadow baseline;
- a comparison/control path;
- provenance or governance example.

It must not be used as the machine-vision主体 because:
- it consumes clinical tabular data, not image/video perception;
- the course requires an explicit machine-vision component;
- the clinical MLP feature contract has its own historical schema constraints and should not be confused with the imaging task.

## Scientific Language That Is Safe To Use in the Report

Use phrases like:
- “local-first clinical AI research prototype”
- “shadow-only CAP/COP imaging perception workflow”
- “case-level digital twin state mapping”
- “doctor-facing, not diagnosis-replacing”
- “internal retrospective / proof-of-concept evaluation”
- “provenance-aware machine vision demonstration”

## Claims That Must Not Be Made

Do not claim:
- formal clinical diagnosis;
- external clinical validation;
- production deployment;
- automatic training or self-improvement;
- default/canary promotion;
- that clinical MLP is the machine-vision task;
- that a visual demo is equivalent to a validated clinical imaging pipeline if the actual ingress path is still missing;
- that the system is a medical device.

## Next Stage Recommendation

For the course project, the next step should prioritize **model/data readiness for the vision path** first.

Recommended order:
1. Model/data readiness for imaging input and task definition.
2. Backend API contract if the vision input or twin state needs a formal interface.
3. Frontend visualization polish once the contract is clear.

Reason:
- the frontend can be mocked, but the course will not be defensible without a real or explicitly simulated visual input path;
- the backend already has enough schema skeleton to support the next layer;
- the biggest gap is still the machine-vision/data layer, not the doctor-facing shell.

## Read-only Investigation Sources

- `/home/sygxdg/MedOrion/docs/coursework/MACHINE_VISION_DIGITAL_TWIN_ASSIGNMENT_BRIEF.md`
- `/home/sygxdg/MedOrion/docs/coursework/MEDORION_COURSE_PROJECT_FRAMEWORK.md`
- `/home/sygxdg/MedOrion/docs/coursework/CAP_COP_DIGITAL_TWIN_SCIENTIFIC_PROTOCOL.md`
- `/home/sygxdg/MedOrion/docs/coursework/COURSE_DELIVERABLES_CHECKLIST.md`
- `/home/sygxdg/MedOrion/docs/architecture/SOURCE_OF_TRUTH.md`
- `/home/sygxdg/MedOrion/docs/PROJECT_BOARD.md`
- `/home/sygxdg/MedOrion/docs/HANDOFF_FOR_AI.md`
- `/home/sygxdg/MedOrion/docs/model_orchestration/CAP_COP_CLINICAL_MLP_STAGE_127_FEATURE_CONTRACT_REVIEW.md`
- `/home/sygxdg/MedOrion/docs/backend/MODEL_INPUT_SCHEMA_STAGE_58_CONTRACT.md`
- `/home/sygxdg/MedOrion/docs/backend/MODEL_INPUT_SCHEMA_STAGE_59_SKELETON.md`
- `/srv/medorion/app/model-service/app/services/model_registry.py`
- `/srv/medorion/app/model-service/app/adapters/cap_cop/registry.py`
- `/srv/medorion/app/model-service/app/adapters/cap_cop/imaging_resnet18_adapter.py`
- `/srv/medorion/app/model-service/app/adapters/cap_cop/multimodal_resnet18_adapter.py`
- `/srv/medorion/app/model-runners/cap_cop_clinical_mlp_fold5_runner.py`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/README.md`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/source_manifest.json`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/Best_Metrics_Summary.csv`
