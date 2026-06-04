# MedOrion Stage 55: CAP/COP Clinical MLP Fold1~Fold5 Offline Evaluation Plan

Last updated: 2026-06-04

## Goals
Stage 55 defines the offline evaluation plan for the CAP/COP clinical MLP family across fold1~fold5. The goal is to compare the five fold weights, decide whether a single fold should be selected, whether an ensemble is warranted, or whether a later freeze/retrain step is needed before any shadow/canary/default consideration.

## Non Goals
- No fold2~fold5 loading in this stage
- No training
- No real inference
- No GPU enablement
- No live inference change
- No default promotion
- No database change
- No Alembic
- No Nginx
- No frontend changes
- No dataset copying
- No directory scanning for additional artifacts

## Current Status
- clinical MLP adapter remains disabled
- imaging adapter remains disabled
- multimodal adapter remains disabled
- the system is not a live inference system
- the system is not a real diagnostic system

## Why fold1 Cannot Be the Final Production Model by Default
fold1 has passed a single-artifact CPU-only dry-run and therefore proves structure compatibility, but dry-run success is not a production decision. fold1 must not be assumed to be the final production model until offline evaluation against valid validation or test data demonstrates that it is competitive across the required metrics and failure cases.

## Evaluation Objectives Across fold1~fold5
The evaluation must answer:
- which fold performs best on the same held-out dataset
- whether one fold is consistently better across CAP and COP
- whether uncertainty and calibration are acceptable
- whether failure cases are clinically tolerable
- whether an ensemble is materially better than the best single fold
- whether a later freeze step is needed before any shadow/canary/default path

## Data Requirements
Offline evaluation requires a clearly identified evaluation dataset source:
- validation set or test set provenance must be explicit
- training data must not be reused as the final evaluation set
- if only prior experiment logs are available, the evidence level must be labeled lower and must not be treated as a full substitution for a proper held-out evaluation set
- no dataset copying is permitted in this stage
- no directory scanning is permitted
- no automatic reading of unauthorized data is permitted

## Metrics
Evaluation must include, at minimum:
- AUC
- ACC
- sensitivity
- specificity
- calibration
- confusion matrix
- CAP-specific performance
- COP-specific performance
- missing-value sensitivity
- failure cases

## What “Better” Means
A model or fold is not considered better solely because its AUC is higher once. The decision must consider:
- sensitivity and specificity balance
- uncertainty behavior
- calibration quality
- failure-case analysis
- quality review findings
- doctor feedback trends
- missing-value sensitivity

## Passing Gates
A fold can only advance if the offline evaluation meets the agreed gate conditions. The gate must not be based on AUC alone. The decision should combine:
- AUC
- sensitivity
- specificity
- calibration
- uncertainty quality
- failure analysis
- quality review
- doctor feedback

A single dry-run result is never sufficient for an operational promotion decision.

## Downstream Gate Sequence
If offline evaluation passes, the next possible steps are:
- shadow
- then canary
- then default

Each step requires separate approval and traceable evidence. doctor_feedback and quality_review may inform the quality judgment, but they do not trigger automatic training.

## Current Adapter State
- clinical MLP adapter: disabled
- imaging adapter: disabled
- multimodal adapter: disabled
- live inference: not enabled
- real diagnosis: not enabled

## Explicit Safety Rule
This stage is a plan only. It does not evaluate folds, does not select a winner, does not retrain, and does not enable live inference.

## Stage 56 Recommendation
Stage 56 should be the execution phase for clinical MLP offline evaluation, but only after the main controller approves the specific validation or test data path.

## Main-Controller Writeback Summary
- Stage 55 defines the offline evaluation plan for fold1~fold5.
- fold1 is not automatically the final production model.
- The plan requires explicit held-out data provenance.
- The plan defines metrics, gates, and post-evaluation shadow/canary/default sequencing.
- The current state remains disabled and non-diagnostic.
