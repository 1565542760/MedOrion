import uuid
from fastapi import APIRouter, HTTPException, Request

from app.modules.inference.model_service_client import ModelServiceError, infer_with_model_service
from app.modules.inference.schemas import (
    InferenceTaskResponseV1,
    ModelInferenceRequestV1,
    ModelInferenceResponseV1,
    ReassessmentJobCreateRequestV1,
    ReassessmentJobResponseV1,
    RecommendationStubV1,
)

router = APIRouter()


@router.post('/cases/{case_id}/inference-tasks', response_model=ModelInferenceResponseV1)
def create_case_inference_task(case_id: str, payload: ModelInferenceRequestV1, request: Request) -> ModelInferenceResponseV1:
    request_id = getattr(request.state, 'request_id', f'req_{uuid.uuid4().hex}')
    incoming_trace_id = getattr(request.state, 'trace_id', '-')
    trace_id = incoming_trace_id if incoming_trace_id != '-' else f'trace_stub_{uuid.uuid4().hex[:12]}'
    inference_task_id = f'itask_{uuid.uuid4().hex[:10]}'

    ms_payload = {
        'trace_id': trace_id,
        'inference_task_id': inference_task_id,
        'case_id': case_id,
        'patient_id': payload.patient_id,
        'disease_agent': payload.disease_agent,
        'requested_task': payload.requested_task,
        'model_version_policy': payload.model_version_policy,
        'inputs': payload.inputs,
        'clinical_context_refs': {'source': 'backend_stub'},
        'modality_refs': {'source': 'backend_stub'},
        'missing_value_context': payload.missing_value_context,
        'runtime_options': {'stub': True},
        'idempotency_key': payload.idempotency_key or f'idem_{uuid.uuid4().hex[:12]}',
    }

    try:
        ms_resp = infer_with_model_service(ms_payload, request_id=request_id, trace_id=trace_id)
    except ModelServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                'code': exc.code,
                'message': exc.message,
                'retryable': exc.status_code >= 500,
                'details': exc.details,
            },
        ) from exc

    recommendation = RecommendationStubV1(
        trace_id=ms_resp.get('trace_id', trace_id),
        inference_task_id=ms_resp.get('inference_task_id', inference_task_id),
        model_version_id=ms_resp.get('model_version_id', 'unknown'),
        confidence=ms_resp.get('confidence', {}),
        uncertainty=ms_resp.get('uncertainty', {}),
        limitations=ms_resp.get('limitations', []),
        evidence_refs=ms_resp.get('evidence_nodes_to_create', []),
    )

    return ModelInferenceResponseV1(
        route=f'/api/v1/cases/{case_id}/inference-tasks',
        task_id=inference_task_id,
        trace_id=trace_id,
        model_invocation_id=ms_resp.get('model_invocation_id'),
        model_version_id=ms_resp.get('model_version_id'),
        confidence=ms_resp.get('confidence', {}),
        uncertainty=ms_resp.get('uncertainty', {}),
        limitations=ms_resp.get('limitations', []),
        recommendation=recommendation,
        model_service={
            'trace_id': ms_resp.get('trace_id'),
            'inference_task_id': ms_resp.get('inference_task_id'),
            'model_invocation_id': ms_resp.get('model_invocation_id'),
            'model_version_id': ms_resp.get('model_version_id'),
            'status': ms_resp.get('status'),
        },
    )


@router.get('/inference-tasks/{task_id}', response_model=InferenceTaskResponseV1)
def get_inference_task(task_id: str) -> InferenceTaskResponseV1:
    return InferenceTaskResponseV1(route=f'/api/v1/inference-tasks/{task_id}', task_id=task_id)


@router.post('/reassessment-jobs', response_model=ReassessmentJobResponseV1)
def create_reassessment_job(payload: ReassessmentJobCreateRequestV1) -> ReassessmentJobResponseV1:
    return ReassessmentJobResponseV1(route='/api/v1/reassessment-jobs', job_id=f'stub-{payload.case_id}')
