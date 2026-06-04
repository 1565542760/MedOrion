# MedOrion Stage 62: CAP/COP Clinical MLP Shadow Readiness Final Review

Last updated: 2026-06-04

## Scope
This is a short final review of the CAP/COP clinical MLP readiness chain. The confirmed artifacts currently visible in MedOrion docs cover Stage 53 through Stage 57. Stages 58 through 61 are not separately materialized in the current docs folder, so this review does not invent their details.

## Summary of Stage 53-57
- Stage 53: single-artifact CPU-only dry-run on `fold1_best.pth` passed; structure matched, dummy forward shape was `[1,2]`.
- Stage 54: clinical MLP adapter draft added the explicit 36-feature ClinicalMLP structure and preprocessing contract while remaining disabled.
- Stage 55: fold1~fold5 offline evaluation plan defined metrics, gates, and evidence-level rules.
- Stage 56: fold1~fold5 offline evaluation executed on the approved original research CSVs; evidence level was low / internal retrospective check.
- Stage 57: shadow readiness review selected `fold5` as the current shadow candidate, but only as a candidate.

## Current Capability and Boundary
MedOrion can now:
- represent the CAP/COP clinical MLP as a registered, disabled adapter draft
- evaluate fold1~fold5 offline using the approved historical research data
- identify a shadow candidate from retrospective results
- preserve traceability requirements, model metadata, and model-specific preprocessing assumptions

MedOrion still cannot:
- treat fold5 as default
- present the model as a real diagnostic system
- replace the stub path
- enable live inference automatically
- skip schema mapping or feature mapping
- assume one tabular schema fits every model family

## fold5 Shadow Candidate
fold5 is the current shadow candidate because it led the Stage 56 retrospective metrics, including AUC, ACC, and sensitivity, while specificity remained tied at the top. This is still a low-evidence retrospective result, not a clinical deployment claim.

## What Is Still Missing Before Shadow
Before entering shadow, MedOrion still needs:
- artifact hash as a first-class registry field
- model registry metadata completion
- adapter enable switch
- `model_input_schema`
- `clinical_feature_mapping`
- trace/evidence provenance plan
- `no_silent_fallback`
- timeout, batch=1, concurrency=1 enforcement in the shadow path

## Why Default Is Not Allowed
fold5 must not become default yet because:
- evidence is low and retrospective
- no independent held-out test set was established in the review chain
- shadow validation, canary observation, and doctor feedback are still required
- the model must remain doctor-assisted, not doctor-replacing

## Doctor-Aid Boundary
The CAP/COP clinical MLP remains an assistant for doctors, not a diagnostic replacement. Its output can inform review, audit, and later shadow/canary experiments, but it must not be presented as definitive diagnosis.

## Stage 63 Recommendation
Stage 63 can be entered as a controlled shadow adapter switch planning step only. That next step should remain behind the missing gates listed above and must not activate live inference or default promotion.

## Main-Controller Writeback Summary
- Stage 53-57 establish the confirmed readiness chain.
- fold5 is the current shadow candidate, but only as a candidate.
- default promotion is still forbidden.
- the system remains doctor-assisted, not diagnostic.
- Stage 63 is reasonable only as controlled shadow adapter switch planning, not activation.
