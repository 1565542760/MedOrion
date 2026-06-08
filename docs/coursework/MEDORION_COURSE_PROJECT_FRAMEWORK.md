# MedOrion Course Project Framework

## Working Title

面向 CAP/COP 鉴别的机器视觉与数字孪生辅助评估系统设计与验证

## Project Identity

This course project should be framed as a MedOrion scenario package, not as a separate application. It reuses MedOrion's existing local-first doctor workbench, traceability, model registry, model input snapshot, shadow audit, access audit, and frontend workflow as the system substrate.

The scientific claim must stay conservative:

- not a formal diagnosis system;
- not a formal recommendation path;
- not default/canary;
- not production deployment;
- not externally validated;
- not a physician replacement.

## Existing MedOrion Capabilities to Reuse

| Course need | Existing MedOrion component |
| --- | --- |
| Case and patient objects | patients, cases modules and frontend case workflow |
| Data provenance | trace/evidence skeleton, snapshot provenance, access audit |
| Model metadata | model registry and lifecycle metadata |
| Clinical/tabular input state | case_model_input_snapshot and model input schema/validation UI |
| Shadow model evaluation | shadow_inference_runs, shadow_inference_outputs, clinical MLP one-shot bridge |
| Frontend display | cases, model-input, shadow-audit, lineage, feedback, quality review pages |
| Governance | docs/traceability, releases, source-of-truth, no-silent-fallback rule |

## Required Gap for This Course

The course requires an explicit machine vision component. MedOrion currently has strong clinical/tabular and audit infrastructure, but the imaging ResNet18 and multimodal ResNet18 paths are still skeleton/disabled.

Therefore the recommended next course-aligned work is:

1. Define the machine vision task for CAP/COP imaging.
2. Add imaging ResNet18 provenance and runner plan.
3. Connect visual output to a digital-twin state model.
4. Show case-level visualization and evaluation metrics.

## Recommended System Chain

`	ext
CAP/COP data source
  -> visual input or imaging descriptor source
  -> machine vision module
  -> clinical/tabular feature validation
  -> case_model_input_snapshot
  -> shadow audit / model output provenance
  -> digital twin state mapping
  -> frontend visualization and report figures
  -> experimental evaluation
`

## Digital Twin Interpretation for MedOrion

The digital twin does not need to be a full 3D hospital environment. A scientifically defensible MedOrion twin can be a case-level disease-state twin with:

- lung-region involvement state;
- symptom/laboratory state;
- imaging descriptor state;
- model uncertainty/calibration warnings;
- missing-data state;
- trace/audit/provenance state;
- quality-review state.

A lightweight Three.js/WebGL or frontend SVG/Canvas visualization can satisfy the visualization requirement if it maps model/perception outputs to an interactive state representation.

## Suggested Stage Sequence for Course Alignment

### Stage C1 - Course framing and source extraction

- Freeze this framework.
- Link course assignment requirements to existing MedOrion docs.
- Clarify deliverables.

### Stage C2 - Imaging/vision task definition

- Decide whether real images, CT screenshots, masks, or simulation data will be used.
- If no real image data are available, document simulation limitations clearly.

### Stage C3 - Visual perception module

- Implement or connect one visual task.
- Prefer imaging ResNet18 provenance + runner if the existing CAP/COP model family is available.
- Otherwise use a smaller OpenCV/visual descriptor prototype.

### Stage C4 - Digital twin state model

- Define twin state JSON and mapping rules.
- Build visualization route or panel.

### Stage C5 - Evaluation and report artifacts

- Generate metrics, figures, screenshots, and report/PPT outline.

## Current Blockers and Non-Blockers

| Item | Status | Action |
| --- | --- | --- |
| Clinical MLP shadow baseline | Available but schema under review | Use only as shadow/provenance example |
| Stage 127 feature contract | Current frontend schema unverified | Do not claim fold5 input contract until fixed |
| Imaging model runtime | Not connected | Best next work for course machine-vision requirement |
| Digital twin visualization | Not yet built | Can be added as case-level state visualization |
| Real diagnosis | Out of scope | Keep non-diagnostic language |

