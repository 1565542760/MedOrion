# CAP/COP Digital Twin Scientific Protocol

## Scientific Objective

Build a reproducible course-project prototype that demonstrates how machine vision outputs and clinical/tabular case state can be mapped into a CAP/COP digital twin workflow in MedOrion.

## Research Question

Can a local-first MedOrion workflow combine visual perception, clinical state modeling, shadow model provenance, and digital twin visualization to support transparent CAP/COP review without claiming formal diagnosis?

## Data Assets

Known local raw data candidates from prior review:

- /home/sygxdg/MRI3DModel/clinical_csv/CAP.csv
- /home/sygxdg/MRI3DModel/clinical_csv/COP.csv

Stage 127 verified important facts:

- CAP/COP raw CSV headers and preprocess artifact are not the same as the current product-layer frontend schema.
- The verified fold5 preprocessing feature order is recorded in clinical_tabular_standardization_v1.json.
- The current frontend/product schema must be treated as schema_unverified until reconciled.

## Vision Data Requirement

The final course project must identify one of these evidence paths:

1. Real image/video/CT-derived data with documented source and labels.
2. Existing imaging ResNet18 artifact with provenance and controlled runner.
3. Synthetic/simulation visual data clearly marked as non-clinical simulation.
4. Imaging descriptor visualization only, with an explicit limitation that raw machine vision validation is not complete.

If none of paths 1-3 is completed, the final report must not overclaim the machine vision component.

## Proposed Twin State

`json
{
   case_id: string,
  patient_id: string,
  trace_id: string,
  timestamp: ISO-8601,
  lung_region_state: {
    upper_left_lung: number_or_category,
    lower_left_lung: number_or_category,
    right_upper_lung: number_or_category,
    right_middle_lung: number_or_category,
    right_lower_lung: number_or_category
  },
  clinical_state: {
    symptoms: {},
    laboratory: {},
    missing_features: []
  },
  model_shadow_state: {
    candidate_label: CAP_or_COP_or_unknown,
    calibrated: false,
    not_for_diagnosis: true,
    schema_status: verified_or_schema_unverified
  },
  quality_state: {
    doctor_review_required: true,
    quality_review_required: true
  }
}
`

## Evaluation Plan

### Machine vision metrics

Use the metrics appropriate to the chosen visual task:

- classification: accuracy, precision, recall, F1, confusion matrix, ROC-AUC if probabilities are valid;
- detection: precision/recall, mAP if annotations exist;
- segmentation: Dice, IoU, pixel accuracy;
- tracking: ID switches, MOTA/MOTP if applicable;
- simulation: state recognition consistency and limitations.

### Digital twin metrics

- state mapping correctness;
- UI response time;
- synchronization latency;
- missing-data handling correctness;
- audit/provenance completeness;
- failure-mode clarity.

### Scientific controls

- Keep training/validation/test separation explicit.
- Do not use one demo case as proof of model performance.
- Report sample size and class balance.
- Discuss missing data and schema mismatch.
- Keep calibration warnings visible.

## Non-Claims

This project must not claim:

- clinical diagnosis;
- formal treatment recommendation;
- external clinical validation;
- deployment as a medical device;
- physician replacement;
- automatic training or self-improving clinical model.

