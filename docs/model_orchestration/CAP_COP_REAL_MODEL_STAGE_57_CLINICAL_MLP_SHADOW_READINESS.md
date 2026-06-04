# MedOrion Stage 57: CAP/COP Clinical MLP Shadow Readiness

Last updated: 2026-06-04

## Goals
Stage 57 prepares the CAP/COP clinical MLP family for shadow readiness. The purpose is to identify a plausible shadow candidate, define the shadow boundary, and list the metadata and schema gates required before any shadow activation can even be considered.

## Non Goals
- No live inference changes
- No database changes
- No Alembic
- No Nginx
- No frontend changes
- No training or auto-training
- No default promotion
- No replacing the stub path
- No writing patient trace/evidence
- No real diagnostic claim

## Why fold5 Is the Current Shadow Candidate
Based on Stage 56 internal retrospective check, fold5 is the strongest single-fold candidate in this family:
- AUC is highest
- ACC is highest
- sensitivity is highest
- specificity is tied with fold4 for the top value

Even so, evidence remains low because the evaluation is an internal retrospective check without a clearly identified independent held-out dataset.

## fold5 Status
fold5 may be considered a shadow_candidate only. It is not:
- default
- live inference enabled
- a substitute for the stub
- a real diagnostic claim
- automatic doctor advice

## Shadow Mode Definition
In MedOrion, shadow mode means the model runs in a background /旁路 path for comparison and audit only:
- it does not change what the doctor sees as the formal recommendation
- it does not alter production decision flow
- it only contributes to shadow evaluation and audit records
- it requires doctor feedback and quality review before any later canary consideration

## Gates Required Before Shadow
Before a shadow path can be considered, the following must be in place:
- artifact hash
- model registry metadata
- adapter enable switch
- model_input_schema
- clinical_feature_mapping
- trace/evidence provenance plan
- no_silent_fallback
- timeout / batch=1 / concurrency=1

## Table Schema Boundary
The CAP/COP clinical MLP currently depends on a historical 36-feature schema.
`Striated_shadow.1` is part of that historical training schema and must be preserved for this model family.

However, MedOrion cannot freeze all future patient tables to this 36-field shape.
The platform must support multiple models, multiple tabular shapes, and model-specific feature mappings.

Recommended future contracts:
- `model_input_schema`
- `clinical_feature_mapping`
- `model_feature_requirements`

## Current State
- clinical MLP adapter remains disabled
- imaging adapter remains disabled
- multimodal adapter remains disabled
- fold5 is only a shadow candidate
- live inference remains off
- default remains off

## Stage 58 Recommendation
Stage 58 should formalize the model input schema and clinical feature mapping contract so that shadow-ready models can be mapped without hard-coding one table shape for all disease agents.

## Main-Controller Writeback Summary
- Stage 57 defines shadow readiness for CAP/COP clinical MLP.
- fold5 is the current shadow candidate because it leads the Stage 56 metrics, but evidence is still low.
- fold5 must not be treated as default or a final clinical claim.
- Shadow mode is background-only evaluation and audit, not a doctor-facing recommendation override.
- MedOrion must support model-specific table schemas and feature mappings.
