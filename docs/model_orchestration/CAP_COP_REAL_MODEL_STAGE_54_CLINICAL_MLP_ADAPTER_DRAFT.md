# MedOrion Stage 54: Clinical MLP Adapter Implementation Draft

Last updated: 2026-06-04

## Purpose
Stage 54 turns the CAP/COP clinical MLP path into an adapter implementation draft while keeping the service disabled by default. This is a draft, not a live inference path, not a production model, and not a substitute for the stub response.

## What Changed
- The clinical MLP adapter now carries an explicit ClinicalMLP structure contract:
  - Linear(36,64)
  - ReLU
  - Dropout(0.3)
  - Linear(64,32)
  - ReLU
  - Dropout(0.3)
  - Linear(32,2)
- The adapter references the clinical preprocessing artifact:
  - `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/preprocess_artifacts/clinical_tabular_standardization_v1.json`
- The adapter preserves the clinical contract:
  - feature_count = 36
  - CAP = 0
  - COP = 1
  - `Striated_shadow.1` retained as the pandas duplicate-column name

## What Did Not Change
- `/infer` still returns `status: disabled`
- `error.code` remains `real_adapter_not_enabled`
- trace_id is still passed through from upstream without replacement
- missing trace_id still returns `trace_id_missing`
- no live inference, no real diagnosis, no trace/evidence write, no database change, no Alembic, no Nginx, no frontend change

## Artifact Scope
- fold1_best.pth remains the only artifact referenced by this draft
- fold1 is a successful dry-run artifact only; it is not the final production weight
- fold1~fold5 final selection still depends on offline evaluation and later review

## Draft Internal Plan
The adapter draft includes a controlled disabled-path helper and a dry-run plan scaffold that:
- only accepts an explicit single artifact path
- does not scan directories
- does not read fold2~fold5
- does not copy or move files
- does not write病例 trace/evidence
- stays CPU-first and batch=1 in the plan metadata

## Stage 55 Recommendation
Next stage should be offline evaluation planning for fold1~fold5, still without promoting any model to default or enabling live inference.

## Safety Statement
This is adapter draft work, not live model activation. The CAP/COP clinical MLP path remains disabled until the main controller approves a later readiness step.
