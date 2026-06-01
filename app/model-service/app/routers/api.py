import uuid
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import ValidationError

from app.config import settings
from app.schemas import ErrorPayload, ModelInferenceRequestV1, ModelInferenceResponseV1
from app.services.model_registry import get_model_by_version, list_models

router = APIRouter()


@router.get('/health')
def health() -> dict[str, Any]:
    from datetime import UTC, datetime

    return {
        'status': 'ok',
        'service': 'model-service-stub',
        'service_version': '0.1.0-stage02-stub',
        'cpu_mode': settings.model_service_cpu_only,
        'default_batch_size': settings.model_service_default_batch_size,
        'max_concurrency': settings.model_service_max_concurrency,
        'registered_model_count': len(list_models()),
        'timestamp': datetime.now(UTC).isoformat(),
    }


@router.get('/models')
def models() -> dict[str, Any]:
    return {'items': list_models(), 'total': len(list_models()), 'stub_only': True}


@router.get('/models/{model_version_id}')
def model_by_version(model_version_id: str) -> dict[str, Any]:
    model = get_model_by_version(model_version_id)
    if model is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorPayload(
                code='model_not_found',
                message=f'model_version_id not found: {model_version_id}',
                retryable=False,
            ).model_dump(),
        )
    return model


@router.post('/validate-input')
def validate_input(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        req = ModelInferenceRequestV1.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=ErrorPayload(
                code='invalid_input',
                message='request schema validation failed',
                retryable=False,
                details={'errors': exc.errors()},
            ).model_dump(),
        )

    issues: list[dict[str, str]] = []
    if not req.trace_id:
        issues.append({'code': 'trace_id_missing', 'message': 'trace_id is required for trace-bound inference'})

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'stub_only': True,
        'contract_version': 'ModelInferenceRequestV1',
    }


@router.post('/infer', response_model=ModelInferenceResponseV1)
def infer(payload: dict[str, Any], x_request_id: str | None = Header(default=None)) -> ModelInferenceResponseV1:
    try:
        req = ModelInferenceRequestV1.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=ErrorPayload(
                code='invalid_input',
                message='request schema validation failed',
                retryable=False,
                details={'errors': exc.errors()},
            ).model_dump(),
        )

    if not req.trace_id:
        raise HTTPException(
            status_code=400,
            detail=ErrorPayload(
                code='trace_id_missing',
                message='trace_id is required; model-service must not create or replace upstream trace_id',
                retryable=False,
                suggested_action='provide trace_id from upstream inference task',
            ).model_dump(),
        )

    model = get_model_by_version(req.model_version_policy.pinned_version or 'capcop_stub_v1')
    if model is None:
        model = get_model_by_version('capcop_stub_v1')

    invocation_id = f'inv_{uuid.uuid4().hex[:12]}'

    trace_events = [
        {
            'event_type': 'model_selected',
            'trace_id': req.trace_id,
            'inference_task_id': req.inference_task_id,
            'disease_agent': req.disease_agent,
            'requested_task': req.requested_task,
            'model_id': model['model_id'],
            'model_version_id': model['model_version_id'],
            'selection_reason': 'stage02_stub_default_selection',
        },
        {
            'event_type': 'model_invoked',
            'trace_id': req.trace_id,
            'inference_task_id': req.inference_task_id,
            'model_invocation_id': invocation_id,
            'request_id': x_request_id,
        },
        {
            'event_type': 'model_result_received',
            'trace_id': req.trace_id,
            'inference_task_id': req.inference_task_id,
            'model_invocation_id': invocation_id,
            'status': 'succeeded',
        },
    ]

    return ModelInferenceResponseV1(
        trace_id=req.trace_id,
        inference_task_id=req.inference_task_id,
        model_invocation_id=invocation_id,
        model_id=model['model_id'],
        model_version_id=model['model_version_id'],
        disease_agent=req.disease_agent,
        task_type=req.requested_task,
        status='succeeded',
        outputs={
            'stub': True,
            'candidate_label': 'STUB_ONLY_NOT_FOR_CLINICAL_USE',
            'classification': {
                'predicted_label': 'STUB_ONLY_NOT_FOR_CLINICAL_USE',
                'label_space': ['CAP', 'COP'],
                'probability': {'CAP': 0.5, 'COP': 0.5},
            },
            'risk_score': None,
        },
        confidence={'score': 0.0, 'level': 'not_applicable_stub'},
        uncertainty={
            'level': 'high',
            'reasons': ['stub_service_no_real_model_loaded', 'not_for_diagnosis'],
        },
        limitations=[
            'Stage 02 stub response only',
            'No real .pth model loaded',
            'Not for medical diagnosis',
        ],
        evidence_nodes_to_create=[
            {
                'node_type': 'model_output',
                'label': 'stub_model_output',
                'summary': 'Stub output for contract validation only',
            }
        ],
        evidence_edges_to_create=[],
        trace_events_to_emit=trace_events,
        error=None,
    )
