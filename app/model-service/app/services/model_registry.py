from typing import Any


STUB_MODELS: list[dict[str, Any]] = [
    {
        'model_id': 'capcop_stub_classifier',
        'model_version_id': 'capcop_stub_v1',
        'disease_agent_code': 'cap_cop',
        'agent_contract_version': 'v1',
        'supported_tasks': ['classification', 'risk_scoring'],
        'supported_modalities': ['ct_image', 'clinical_table', 'emr_text'],
        'approval_state': 'approved_stub_only',
        'stub_only': True,
    },
    {
        'model_id': 'lung_nodule_stub_detector',
        'model_version_id': 'lung_nodule_stub_v1',
        'disease_agent_code': 'lung_nodule',
        'agent_contract_version': 'v1',
        'supported_tasks': ['detection'],
        'supported_modalities': ['ct_image'],
        'approval_state': 'approved_stub_only',
        'stub_only': True,
    },
]


def list_models() -> list[dict[str, Any]]:
    return STUB_MODELS


def get_model_by_version(model_version_id: str) -> dict[str, Any] | None:
    for model in STUB_MODELS:
        if model['model_version_id'] == model_version_id:
            return model
    return None
