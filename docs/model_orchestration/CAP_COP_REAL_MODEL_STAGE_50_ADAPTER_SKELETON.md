# MedOrion Stage 50: CAP/COP Real-Model Adapter Skeleton + Registry Wiring Draft

## Goals
- Define the adapter skeleton shape for CAP/COP real-model integration.
- Wire registry metadata to adapter dispatch without loading real weights.
- Make disabled / not-enabled states explicit and auditable.

## Non Goals
- No `.pth` / `.pt` / `.onnx` / `.ckpt` / `.safetensors` loading.
- No training, no inference, no GPU enablement.
- No database schema changes and no Alembic.
- No Nginx and no frontend changes.
- No silent fallback and no fake success responses.

## Adapter Skeleton Directory
- `app/adapters/cap_cop/clinical_mlp_adapter.py`
- `app/adapters/cap_cop/imaging_resnet18_adapter.py`
- `app/adapters/cap_cop/multimodal_resnet18_adapter.py`
- `app/adapters/cap_cop/base.py`
- `app/adapters/cap_cop/preprocessing.py`
- `app/adapters/cap_cop/schemas.py`
- `app/adapters/cap_cop/registry.py`

## Adapter Status
- `clinical_mlp_cap_cop_adapter` returns `disabled` with `real_adapter_not_enabled`.
- `imaging_resnet18_cap_cop_adapter` returns `disabled` with `real_adapter_not_enabled`.
- `multimodal_resnet18_cap_cop_adapter` returns `disabled` with `real_adapter_not_enabled`.

## Registry Wiring Draft
- Registry metadata resolves by `model_version_id` or `adapter_type`.
- `approved`, `shadow`, `canary`, and `default` are represented in metadata.
- In Stage 50, those states are metadata-only and do not activate a real model.
- No silent fallback: if a model version is not approved or not enabled, the service must say so.

## Validation Expectations
- `GET /health` reports adapter skeleton stage 50.
- `GET /models` lists stub and CAP/COP registry entries.
- `POST /validate-input` validates contract shape and trace binding.
- `POST /infer` preserves upstream `trace_id` and returns disabled status for CAP/COP real adapters.

## Safety Boundary
- The adapter skeleton is not a diagnostic service.
- Artifact metadata is registration-only and does not mean the artifact is loaded.
- `trace_id` must come from upstream and must not be replaced.

## Main-Controller Writeback Summary
- Stage 50 adapter skeleton and registry wiring draft are created.
- Real weights remain unloaded.
- CAP/COP real adapter requests are explicitly disabled, not faked as successful inference.
