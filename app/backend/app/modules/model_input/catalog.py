from __future__ import annotations

from typing import Any


def _feature(
    order: int,
    name: str,
    feature_type: str,
    *,
    required: bool = False,
    unit: str | None = None,
    value_range: dict | list | str | None = None,
    enum_mapping: dict | list | str | None = None,
    default_strategy: str | None = None,
    missing_value_policy: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    return {
        'feature_order': order,
        'source_clinical_field': name,
        'model_feature_name': name,
        'feature_type': feature_type,
        'required': required,
        'optional': not required,
        'defaultable': default_strategy is not None,
        'unit': unit,
        'value_range': value_range,
        'enum_mapping': enum_mapping,
        'default_strategy': default_strategy,
        'missing_value_policy': missing_value_policy,
        'notes': notes,
    }


CAP_COP_CLINICAL_FEATURES = [
    _feature(1, 'Age', 'numeric', required=True, unit='years', missing_value_policy='consult_doctor_first', notes='Canonical CAP/COP artifact-order feature from clinical_tabular_standardization_v1.json.'),
    _feature(2, 'Height', 'numeric', required=True, unit='cm', missing_value_policy='consult_doctor_first', notes='Canonical CAP/COP artifact-order feature from clinical_tabular_standardization_v1.json.'),
    _feature(3, 'Weight', 'numeric', required=True, unit='kg', missing_value_policy='consult_doctor_first', notes='Canonical CAP/COP artifact-order feature from clinical_tabular_standardization_v1.json.'),
    _feature(4, 'BMI', 'numeric', required=True, unit='kg/m^2', missing_value_policy='consult_doctor_first', notes='Canonical CAP/COP artifact-order feature from clinical_tabular_standardization_v1.json.'),
    _feature(5, 'Hospitalization_duration', 'numeric', required=True, unit='days', missing_value_policy='consult_doctor_first', notes='Canonical CAP/COP artifact-order feature from clinical_tabular_standardization_v1.json.'),
    _feature(6, 'Upper_left_lung', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first', notes='Canonical CAP/COP artifact-order feature from clinical_tabular_standardization_v1.json.'),
    _feature(7, 'Lower_left_lung', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(8, 'Right_upper_lung', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(9, 'Right_middle_lung', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(10, 'Right_lower_lung', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(11, 'Whole_lung_lesion', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(12, 'The_lesion_is_located_subpleurally', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(13, 'dizziness', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(14, 'Anti-dizziness_signs', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(15, 'Tree_Bud_Syndrome', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(16, 'Striated_shadow', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first', notes='Canonical CAP/COP artifact-order feature preserved exactly as the first Striated_shadow field.'),
    _feature(17, 'Frosted_Glass_Shadow', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(18, 'Bronchial_inflation_sign', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(19, 'Hilar_lymphadenopathy', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(20, 'Pleural_traction', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(21, 'Fever', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(22, 'Cough', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(23, 'Sputum production (0 none; 1 white; 2 yellow; 3 bloody; 4 not specified; 5 rust-colored; 6 green)', 'categorical', required=True, unit='category', value_range={'allowed': ['0', '1', '2', '3', '4', '5', '6']}, enum_mapping={'0': 'none', '1': 'white', '2': 'yellow', '3': 'bloody', '4': 'not specified', '5': 'rust-colored', '6': 'green'}, default_strategy='ask_doctor_then_unknown', missing_value_policy='consult_doctor_first'),
    _feature(24, 'chest_tightness', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(25, 'Shortness_of_breath', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(26, 'Coughing_up_blood', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(27, 'Weight_loss', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first'),
    _feature(28, 'Lymphocyte_count', 'numeric', required=True, unit='10^9/L', missing_value_policy='consult_doctor_first'),
    _feature(29, 'ESR', 'numeric', required=True, unit='mm/h', missing_value_policy='consult_doctor_first'),
    _feature(30, 'C-reactive_protein', 'numeric', required=True, unit='mg/L', missing_value_policy='consult_doctor_first'),
    _feature(31, 'High-sensitivity_C-reactive_protein', 'numeric', required=True, unit='mg/L', missing_value_policy='consult_doctor_first'),
    _feature(32, 'Procalcitonin', 'numeric', required=True, unit='ng/mL', missing_value_policy='consult_doctor_first'),
    _feature(33, 'CEA', 'numeric', required=True, unit='ng/mL', missing_value_policy='consult_doctor_first'),
    _feature(34, 'CA153', 'numeric', required=True, unit='U/mL', missing_value_policy='consult_doctor_first'),
    _feature(35, 'Serum_non-small_cell lung_cancer-related antigen', 'numeric', required=True, unit='ng/mL', missing_value_policy='consult_doctor_first'),
    _feature(36, 'Striated_shadow.1', 'boolean', required=True, unit='flag', missing_value_policy='consult_doctor_first', notes='Canonical CAP/COP artifact-order feature retained exactly as the COP-only mangled duplicate column produced by pandas read_csv; this corresponds to the original ???? field and must not be conflated with the product-side ????.1 alias.'),
]

PULMONARY_TRIAGE_FEATURES = [
    _feature(1, 'Age', 'numeric', required=True, unit='years', missing_value_policy='consult_doctor_first', notes='Age is required for pulmonary triage support.'),
    _feature(2, 'RespiratoryRate', 'numeric', required=True, unit='breaths_per_minute', missing_value_policy='consult_doctor_first', notes='Respiratory rate is required for triage scoring.'),
    _feature(3, 'SPO2', 'numeric', required=True, unit='percent', missing_value_policy='consult_doctor_first', notes='SPO2 is required for triage escalation.'),
    _feature(4, 'Dyspnea', 'categorical', required=True, unit='category', value_range={'allowed': ['none', 'mild', 'moderate', 'severe', 'unknown']}, enum_mapping={'none': 'none', 'mild': 'mild', 'moderate': 'moderate', 'severe': 'severe', 'unknown': 'unknown'}, default_strategy='ask_doctor_then_unknown', missing_value_policy='consult_doctor_then_default', notes='Dyspnea severity is required for pulmonary triage.'),
    _feature(5, 'Wheeze', 'boolean', unit='flag', required=False),
    _feature(6, 'OxygenNeed', 'boolean', unit='flag', required=False),
]

CAP_COP_MULTIMODAL_FEATURES = [
    *CAP_COP_CLINICAL_FEATURES,
]

CAP_COP_IMAGING_FEATURES = [
    CAP_COP_CLINICAL_FEATURES[0],
    CAP_COP_CLINICAL_FEATURES[4],
    CAP_COP_CLINICAL_FEATURES[10],
    CAP_COP_CLINICAL_FEATURES[11],
    CAP_COP_CLINICAL_FEATURES[14],
    CAP_COP_CLINICAL_FEATURES[15],
    CAP_COP_CLINICAL_FEATURES[16],
    CAP_COP_CLINICAL_FEATURES[17],
]

FEATURE_SETS: dict[str, dict[str, Any]] = {
    'cap_cop_clinical_feature_set_v1': {
        'feature_set_id': 'cap_cop_clinical_feature_set_v1',
        'feature_set_key': 'cap_cop_clinical_feature_set_v1',
        'feature_set_name': 'CAP/COP Clinical Feature Set v1',
        'disease_task_code': 'cap_cop',
        'schema_version': 'v1',
        'description': 'CAP/COP task-family clinical attribute collection shared across multiple models.',
        'features': CAP_COP_CLINICAL_FEATURES,
    },
    'pulmonary_triage_clinical_feature_set_v1': {
        'feature_set_id': 'pulmonary_triage_clinical_feature_set_v1',
        'feature_set_key': 'pulmonary_triage_clinical_feature_set_v1',
        'feature_set_name': 'Pulmonary Triage Clinical Feature Set v1',
        'disease_task_code': 'pulmonary_triage',
        'schema_version': 'v1',
        'description': 'Task-specific clinical attribute collection for pulmonary triage.',
        'features': PULMONARY_TRIAGE_FEATURES,
    },
}

MODEL_INPUT_SCHEMA_PROFILES: dict[str, dict[str, Any]] = {
    'clinical_mlp_cap_cop_input_schema_v1': {
        'feature_set_id': 'cap_cop_clinical_feature_set_v1',
        'feature_set_key': 'cap_cop_clinical_feature_set_v1',
        'feature_set_name': 'CAP/COP Clinical Feature Set v1',
        'schema_id': 'clinical_mlp_cap_cop_input_schema_v1',
        'schema_key': 'clinical_mlp_cap_cop_input_schema_v1',
        'schema_name': 'clinical_mlp_cap_cop_input_schema_v1',
        'schema_version': 'v1',
        'disease_task': 'cap_cop',
        'supported_disease_tasks': ['cap_cop', 'CAP_COP_CLASSIFICATION'],
        'supported_modalities': ['clinical_table'],
        'lifecycle_status': 'default',
        'model_family': 'clinical_mlp',
        'preprocess_artifact_ref': 'metadata-only://cap_cop/clinical_mlp/preprocess/v1',
        'limitations': ['metadata_only', 'no_model_loaded', 'no_live_inference', 'training_time_median_imputation'],
        'feature_requirements': CAP_COP_CLINICAL_FEATURES,
    },
    'multimodal_resnet18_cap_cop_input_schema_v1': {
        'feature_set_id': 'cap_cop_clinical_feature_set_v1',
        'feature_set_key': 'cap_cop_clinical_feature_set_v1',
        'feature_set_name': 'CAP/COP Clinical Feature Set v1',
        'schema_id': 'multimodal_resnet18_cap_cop_input_schema_v1',
        'schema_key': 'multimodal_resnet18_cap_cop_input_schema_v1',
        'schema_name': 'multimodal_resnet18_cap_cop_input_schema_v1',
        'schema_version': 'v1',
        'disease_task': 'cap_cop',
        'supported_disease_tasks': ['cap_cop', 'CAP_COP_CLASSIFICATION'],
        'supported_modalities': ['clinical_table', 'ct_image', 'mri_image'],
        'lifecycle_status': 'approved',
        'model_family': 'multimodal_resnet18',
        'preprocess_artifact_ref': 'metadata-only://cap_cop/multimodal_resnet18/preprocess/v1',
        'limitations': ['metadata_only', 'stub_schema_only', 'no_live_inference'],
        'feature_requirements': CAP_COP_MULTIMODAL_FEATURES,
    },
    'imaging_resnet18_cap_cop_input_schema_v1': {
        'feature_set_id': 'cap_cop_clinical_feature_set_v1',
        'feature_set_key': 'cap_cop_clinical_feature_set_v1',
        'feature_set_name': 'CAP/COP Clinical Feature Set v1',
        'schema_id': 'imaging_resnet18_cap_cop_input_schema_v1',
        'schema_key': 'imaging_resnet18_cap_cop_input_schema_v1',
        'schema_name': 'imaging_resnet18_cap_cop_input_schema_v1',
        'schema_version': 'v1',
        'disease_task': 'cap_cop',
        'supported_disease_tasks': ['cap_cop', 'CAP_COP_CLASSIFICATION'],
        'supported_modalities': ['ct_image', 'mri_image'],
        'lifecycle_status': 'shadow',
        'model_family': 'imaging_resnet18',
        'preprocess_artifact_ref': 'metadata-only://cap_cop/imaging_resnet18/preprocess/v1',
        'limitations': ['metadata_only', 'stub_schema_only', 'no_live_inference'],
        'feature_requirements': CAP_COP_IMAGING_FEATURES,
    },
    'clinical_mlp_pulmonary_triage_input_schema_v1': {
        'feature_set_id': 'pulmonary_triage_clinical_feature_set_v1',
        'feature_set_key': 'pulmonary_triage_clinical_feature_set_v1',
        'feature_set_name': 'Pulmonary Triage Clinical Feature Set v1',
        'schema_id': 'clinical_mlp_pulmonary_triage_input_schema_v1',
        'schema_key': 'clinical_mlp_pulmonary_triage_input_schema_v1',
        'schema_name': 'clinical_mlp_pulmonary_triage_input_schema_v1',
        'schema_version': 'v1',
        'disease_task': 'pulmonary_triage',
        'supported_disease_tasks': ['pulmonary_triage'],
        'supported_modalities': ['clinical_table'],
        'lifecycle_status': 'default',
        'model_family': 'clinical_mlp',
        'preprocess_artifact_ref': 'metadata-only://pulmonary_triage/clinical_mlp/preprocess/v1',
        'limitations': ['metadata_only', 'no_model_loaded', 'no_live_inference'],
        'feature_requirements': PULMONARY_TRIAGE_FEATURES,
    },
}

TASK_MODEL_FILTERS: dict[str, dict[str, str]] = {
    'cap_cop': {'disease_agent': 'capcop_agent', 'task_type': 'risk_assessment'},
    'pulmonary_triage': {'disease_agent': 'pulmonary_triage', 'task_type': 'diagnosis_support'},
}

DISEASE_TASK_SCHEMA_ORDER: dict[str, list[str]] = {
    'cap_cop': [
        'clinical_mlp_cap_cop_input_schema_v1',
        'multimodal_resnet18_cap_cop_input_schema_v1',
        'imaging_resnet18_cap_cop_input_schema_v1',
    ],
    'pulmonary_triage': [
        'clinical_mlp_pulmonary_triage_input_schema_v1',
    ],
}
