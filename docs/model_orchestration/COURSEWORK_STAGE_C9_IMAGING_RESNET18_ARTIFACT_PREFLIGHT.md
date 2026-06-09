# Coursework Stage C9: CAP/COP Imaging ResNet18 Artifact Preflight

Scope: this stage performs a strict artifact/runtime preflight for the CAP/COP imaging ResNet18 route and produces a runner prototype candidate that does **not** load model weights, does **not** run inference, and does **not** alter backend or frontend behavior.

## 1. Files Read

Read-only inspection was performed on:

1. `/home/sygxdg/MedOrion/docs/coursework/COURSEWORK_STAGE_C7_IMAGING_RESNET18_RUNNER_ADAPTER_PLAN.md`
2. `/home/sygxdg/MedOrion/docs/coursework/COURSEWORK_STAGE_C3_IMAGING_RESNET18_PROVENANCE_AND_RUNNER_PLAN.md`
3. `/home/sygxdg/MedOrion/app/model-runners/cap_cop_clinical_mlp_fold5_runner.py`
4. `/srv/medorion/app/model-service/app/adapters/cap_cop/imaging_resnet18_adapter.py`
5. `/srv/medorion/app/model-service/app/adapters/cap_cop/registry.py`
6. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/README.md`
7. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/source_manifest.json`
8. `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/provenance/Best_Metrics_Summary.csv`

## 2. Artifact / Provenance Preflight Result

### Confirmed artifact family

- Disease agent: `cap_cop_classifier_agent`
- Model family: `imaging_resnet18_cap_cop_classifier`
- Adapter code: `imaging_resnet18_cap_cop_adapter`
- Registry state: metadata-only / shadow / disabled
- Label mapping: `CAP = 0`, `COP = 1`
- Modality family: CT / NIfTI imaging

### Confirmed exact artifact path

Selected preflight artifact:

`/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/imaging_resnet18_unimodal/weights/fold5_best_unimodal.pth`

This path is explicitly named in Stage 48 registry planning and is present in the staged artifact tree.

### Verified hash and file size

- `sha256`: `892fd836b0f361ca6ed4d90f5a57c71587984c817cc3ba1e6d88618f6da9f781`
- `file_size_bytes`: `132801280`

### Provenance summary

- Staged root exists at `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/`
- `README.md` explicitly says metadata/artifact staging only, no load, no real inference, no training during staging, and no Git commits for artifact files
- `source_manifest.json` ties imaging ResNet18 to `/home/sygxdg/MRI3DModel/3d_classification/restnet_classifaction`
- The provenance bundle confirms the imaging family is staged deliberately, but it does **not** mean the model is ready for live clinical use

## 3. Runtime Preflight

### MRI3D conda environment

- Python path: `/home/sygxdg/miniconda3/envs/MRI3D/bin/python`
- `torch` available: yes
- `torch` version: `2.6.0+cu124`
- CUDA visibility in that env: `True`

### model-service container environment

- Container: `medorion-model-service-1`
- Python path: `/usr/local/bin/python`
- `torch` available: no

### backend container environment

- Container: `medorion-backend-1`
- Python path: `/usr/local/bin/python`
- `torch` available: no

### Preflight interpretation

The artifact can be named precisely and the MRI3D environment can inspect it, but the live model-service and backend runtime environments do not currently expose `torch`, which is consistent with the existing stub / metadata-only stage.

## 4. Known Blockers

The following remain blockers for any real imaging inference:

1. No weight loading is allowed in this stage.
2. The final image preprocessing contract is still only a planning contract.
3. No live case image ingress path is being consumed here.
4. No calibration or external validation evidence is being claimed.
5. No production approval or default promotion exists.

## 5. Runner Prototype Candidate

### Decision

A runner prototype candidate **is created**, but it is intentionally non-executing.

### Prototype behavior

The candidate runner is limited to:

- argument parsing
- JSON input validation
- explicit artifact path / hash verification helper
- preprocessing contract guard
- returning `status=disabled` with `error.code=imaging_runner_not_loaded`
- returning `prototype_not_executed` when invoked in plan mode

It does **not**:

- `torch.load`
- instantiate a real model for inference
- read any neighboring folds
- perform real forward passes
- write trace / evidence
- touch database state

### Candidate runtime placement

- Authoring copy: `./cap_cop_imaging_resnet18_runner.py`
- Runtime copy target: `/srv/medorion/app/model-runners/cap_cop_imaging_resnet18_runner.py`

## 6. Backend Bridge Implication

The current C8 shadow bridge can treat this runner as the future execution target, but only after a later gated stage enables:

1. explicit image input schema binding,
2. explicit artifact enable switch,
3. registered model metadata,
4. shadow-audit plumbing,
5. a separate approval step for any real loading.

For C10 / C11 planning, the bridge should still call only the metadata-only path and keep the public response non-diagnostic.

## 7. What Cannot Be Claimed

This stage does **not** prove:

- diagnosis capability,
- recommendation quality,
- production readiness,
- external clinical validation,
- default eligibility,
- live inference readiness.

## 8. Next Stage Suggestion

Recommended next step: a tiny bridge-facing prototype stage that wires this runner candidate behind an explicit metadata-only guard, while keeping the imaging adapter disabled by default.

