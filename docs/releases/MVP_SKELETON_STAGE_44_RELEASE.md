# MedOrion MVP Skeleton Stage 44 Release

Last updated: 2026-06-03 Asia/Shanghai
Owner thread: MedOrion release and baseline management

## 1. Release Positioning

Stage 44 is the runnable MVP skeleton baseline for MedOrion.
It is a working clinical-assist workflow skeleton, not a real diagnosis system.

The current release proves the platform pattern across authentication, case workflow, stub inference, trace/evidence, missing-value consultation, feedback, quality review, model registry, and agent gateway boundaries.

## 2. Verified Accepted Capabilities

The following areas have been accepted in the current skeleton baseline:

- Service status and containerized runtime are healthy.
- Health checks are available for core services.
- Authentication and RBAC skeleton are present.
- Patient and case creation flows are available.
- Inference, trace, and evidence skeletons are available.
- Missing-value consultation is available.
- Doctor feedback is available.
- Quality review is available.
- Model registry lifecycle skeleton is available.
- Agent gateway skeleton is available.
- Multi-stage orchestration-related contracts and reviews are documented.
- Frontend route acceptance is complete for the current MVP skeleton scope.

## 3. Runtime Access

Recommended access pattern:

```bash
ssh -L 3000:127.0.0.1:3000 sygxdg@100.73.42.19
```

Then open:

```text
http://127.0.0.1:3000
```

Nginx remains disabled and inactive. Public exposure is intentionally not enabled for this release.

## 4. Database Head

Current database migration head:

- `d8b6e2f94c10`

## 5. Current Release Limits

This release remains constrained to the MVP skeleton baseline.

Current limits:

- Stub-only, not a real diagnosis system.
- No real model inference system.
- No real training system.
- No public deployment.
- No GPU enablement.
- No Nginx/HTTPS public entry.
- No real model files loaded.
- No automatic real-time learning.
- No `.pth/.pt/.onnx/.ckpt/.safetensors` scanning, copying, guessing, or loading.

## 6. Recommended Next Stage

Suggested next directions:

1. Prepare real model onboarding prerequisites, including governed artifact handling and version contract checks.
2. Add orchestration audit frontend pages and deeper orchestration visibility.
3. Continue RBAC/admin and operational control surfaces.
4. Strengthen deployment for productionization, including Nginx/HTTPS, backup drills, and database externalization rehearsal.
5. Prepare for real model integration only after the controller explicitly requests a user-provided model path.
6. Continue future work on multi-agent orchestration and causal analysis only after the gateway and audit contracts are fully stabilized.

## 7. Rollback Baseline

If a rollback is needed, use the current Git commit/tag as the MVP skeleton release baseline.

Baseline commit:
- `78413cb`

Recommended release tag:
- `v0.2.0-mvp-skeleton`

This baseline represents the runnable MVP skeleton boundary and should be used as the reference point for future staged expansion.
