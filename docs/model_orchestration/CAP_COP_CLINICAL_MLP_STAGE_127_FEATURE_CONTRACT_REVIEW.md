# CAP/COP Clinical MLP Feature Contract Review (Stage 127)

## Verdict
- The current `clinical_mlp_cap_cop_input_schema_v1` is **not verified** against the fold5 training contract.
- The verified fold5 preprocessing order is the 36-column `feature_columns` list in `clinical_tabular_standardization_v1.json`.
- The current product-layer 36-feature schema is a different abstraction and cannot be claimed as the fold5 training schema.
- The backend one-shot path is positional for list inputs, so a mismatched feature contract can silently misalign inputs and outputs.
- Recommendation: mark the current feature contract as `schema_unverified`, and do **not** checkpoint Stage 126 until the contract is reconciled.

## Sources Reviewed
| Source | Path | What it showed |
| --- | --- | --- |
| CAP/COP raw CSV headers | /home/sygxdg/MRI3DModel/clinical_csv/CAP.csv and COP.csv | CAP has 38 headers; COP has 39 headers with a duplicated `Striated_shadow` that becomes `Striated_shadow.1` in pandas-like column handling. |
| Current product schema | /home/sygxdg/MedOrion/app/backend/app/modules/model_input/catalog.py | Defines `clinical_mlp_cap_cop_input_schema_v1` as a 36-feature catalog that is not the same set as the verified fold5 preprocess order. |
| Preprocess artifact | /srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/preprocessing/clinical_tabular_standardization_v1.json | Records the 36-feature training/preprocessing order and the source-file metadata used by the runner. |
| Runner | /home/sygxdg/MedOrion/app/model-runners/cap_cop_clinical_mlp_fold5_runner.py | Consumes the preprocess artifact feature order and materializes list inputs positionally, so order mismatches are dangerous. |

## CSV Header Facts
- `CAP.csv` header count: 38
- `COP.csv` header count: 39
- Both files begin with three metadata columns: `Classification`, `Name`, `Desensitized_ID`
- The verified training/preprocessing order comes from the columns after those metadata fields, with the duplicate `Striated_shadow` in COP preserved as `Striated_shadow.1`

## Current Schema vs Verified Fold5 Contract
- Current product schema size: **36**
- Verified preprocess feature order size: **36**
- Exact name matches: **10**
- Candidate aliases / unverified semantic overlaps: **3**
- Current-only fields with no verified artifact counterpart: **27**
- Artifact-only fields missing from the current product schema: **23**

| Current schema field | Status | Closest artifact field | Notes |
| --- | --- | --- | --- |
| Age | Exact | Age | Same feature name and same position class. |
| Sex | Missing from verified contract | - | No `Sex` column exists in the raw CSV headers or the preprocess artifact. |
| Temperature | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| HeartRate | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| RespiratoryRate | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| SPO2 | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| SystolicBP | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| DiastolicBP | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| WBC | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| NeutrophilPercent | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| LymphocytePercent | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| CRP | Candidate alias (unverified) | C-reactive_protein | Semantic overlap is plausible, but the exact verified artifact name is `C-reactive_protein`, not `CRP`. |
| Procalcitonin | Exact | Procalcitonin | Exact match. |
| ESR | Exact | ESR | Exact match. |
| Hemoglobin | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Platelet | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Sodium | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Potassium | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Chloride | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| BUN | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Creatinine | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| ALT | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| AST | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Albumin | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Glucose | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Cough | Exact | Cough | Exact match. |
| Fever | Exact | Fever | Exact match. |
| Dyspnea | Candidate alias (unverified) | Shortness_of_breath | Possible clinical synonym, but not an exact verified contract term. |
| ChestPain | Candidate alias (unverified) | chest_tightness | Possible symptom overlap, but the verified artifact uses `chest_tightness`. |
| Wheeze | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Crackles | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Consolidation | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| PleuralEffusion | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Infiltration | Missing from verified contract | - | Not present in the fold5 artifact feature order. |
| Striated_shadow.1 | Exact | Striated_shadow.1 | This is the duplicate-mangled COP column and is explicitly preserved by the verified preprocess artifact. |
| SmokingHistory | Missing from verified contract | - | Not present in the fold5 artifact feature order. |

## Verified Preprocess Feature Order
The runner must follow this exact order for fold5 inference:

| # | Feature |
| --- | --- |
| 1 | Age |
| 2 | Height |
| 3 | Weight |
| 4 | BMI |
| 5 | Hospitalization_duration |
| 6 | Upper_left_lung |
| 7 | Lower_left_lung |
| 8 | Right_upper_lung |
| 9 | Right_middle_lung |
| 10 | Right_lower_lung |
| 11 | Whole_lung_lesion |
| 12 | The_lesion_is_located_subpleurally |
| 13 | dizziness |
| 14 | Anti-dizziness_signs |
| 15 | Tree_Bud_Syndrome |
| 16 | Striated_shadow |
| 17 | Frosted_Glass_Shadow |
| 18 | Bronchial_inflation_sign |
| 19 | Hilar_lymphadenopathy |
| 20 | Pleural_traction |
| 21 | Fever |
| 22 | Cough |
| 23 | Sputum production (0 none; 1 white; 2 yellow; 3 bloody; 4 not specified; 5 rust-colored; 6 green) |
| 24 | chest_tightness |
| 25 | Shortness_of_breath |
| 26 | Coughing_up_blood |
| 27 | Weight_loss |
| 28 | Lymphocyte_count |
| 29 | ESR |
| 30 | C-reactive_protein |
| 31 | High-sensitivity_C-reactive_protein |
| 32 | Procalcitonin |
| 33 | CEA |
| 34 | CA153 |
| 35 | Serum_non-small_cell lung_cancer-related antigen |
| 36 | Striated_shadow.1 |

## Runner Order and Misalignment Risk
- The runner consumes `feature_columns` from the preprocess artifact.
- When the backend sends a list, the runner materializes it **positionally** rather than by name.
- The current backend builds the one-shot input from the product-layer schema order, not from the verified preprocess order.
- Therefore, even if a shadow run succeeds technically, the input contract is not verified unless the backend payload is realigned to the artifact order.
- This is a silent-feature-misalignment risk, not a cosmetic naming issue.

## Sex Encoding Conclusion
- `Sex` is **not verified** for fold5.
- There is no `Sex` column in the raw CSV headers or the verified preprocess artifact.
- No executable Sex-encoding rule was found in the runner or artifact metadata.
- Do not treat `Sex` as part of the verified fold5 contract.

## Risk Decision
- **Decision C**: the current product-layer schema is inconsistent with the verified fold5 training/preprocess contract, so it should **not** be treated as the source of truth.
- The safe interpretation is `schema_unverified`, not `verified_with_minor_edits`.

## Frontend Recommendation
- Mark the CAP/COP shadow input UI as `schema_unverified` until the product schema is rebuilt to match the verified preprocess artifact order.
- Disable or visually harden the run action so it cannot be mistaken for a validated clinical workflow.
- If the product wants a more clinician-friendly input form, add a translation layer later, but do not call the current 36-field form the fold5 training contract.
- The `Sex` field should not be presented as if it were part of the verified fold5 contract.

## Stage 126 Checkpoint Decision
- **Not allowed yet.**
- Stage 126 should wait until the feature contract is rebuilt or a verified translation layer is documented and tested.

## Practical Next Step
- Rebuild the input contract around the verified 36-column artifact order, or add an explicit, reviewed translation layer from product inputs to artifact features before any further UI or release checkpoint.

## File References
- `/home/sygxdg/MRI3DModel/clinical_csv/CAP.csv`
- `/home/sygxdg/MRI3DModel/clinical_csv/COP.csv`
- `/home/sygxdg/MedOrion/app/backend/app/modules/model_input/catalog.py`
- `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/preprocessing/clinical_tabular_standardization_v1.json`
- `/home/sygxdg/MedOrion/app/model-runners/cap_cop_clinical_mlp_fold5_runner.py`
