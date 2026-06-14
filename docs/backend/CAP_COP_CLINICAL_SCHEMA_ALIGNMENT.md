# CAP/COP Clinical Schema Alignment

This note records the canonical CAP/COP clinical input contract used by the backend catalog and the strict validation pipeline.

## Source of truth

Canonical artifact:

`/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/multimodal_resnet18_bigdata/preprocess_artifacts/clinical_tabular_standardization_v1.json`

The backend CAP/COP clinical schema is aligned to the artifact's `feature_columns` order exactly.

## Canonical 36-field order

1. Age
2. Height
3. Weight
4. BMI
5. Hospitalization_duration
6. Upper_left_lung
7. Lower_left_lung
8. Right_upper_lung
9. Right_middle_lung
10. Right_lower_lung
11. Whole_lung_lesion
12. The_lesion_is_located_subpleurally
13. dizziness
14. Anti-dizziness_signs
15. Tree_Bud_Syndrome
16. Striated_shadow
17. Frosted_Glass_Shadow
18. Bronchial_inflation_sign
19. Hilar_lymphadenopathy
20. Pleural_traction
21. Fever
22. Cough
23. Sputum production (0 none; 1 white; 2 yellow; 3 bloody; 4 not specified; 5 rust-colored; 6 green)
24. chest_tightness
25. Shortness_of_breath
26. Coughing_up_blood
27. Weight_loss
28. Lymphocyte_count
29. ESR
30. C-reactive_protein
31. High-sensitivity_C-reactive_protein
32. Procalcitonin
33. CEA
34. CA153
35. Serum_non-small_cell lung_cancer-related antigen
36. Striated_shadow.1

## Notes

- `Striated_shadow.1` is preserved literally because pandas-style duplicate-column mangling in the training artifact produced the COP-only companion field; this is the original `????` field and must not be conflated with the product-side `????.1` alias.
- Product-only fields such as `Sex`, `Temperature`, `HeartRate`, `RespiratoryRate`, `SPO2`, `WBC`, `NeutrophilPercent`, `SmokingHistory`, `Dyspnea`, `Consolidation`, `PleuralEffusion`, and `Infiltration` are not part of this canonical CAP/COP clinical contract.
- `app/backend/app/modules/model_input/catalog.py` now exposes this canonical order through `CAP_COP_CLINICAL_FEATURES`.
- `clinical_mlp_cap_cop_input_schema_v1.feature_requirements` and the multimodal clinical schema profile both reference the canonical CAP/COP contract.
- The multimodal schema profile uses the same strict 36-field clinical order so the workflow gate and runner payload builder stay aligned.
