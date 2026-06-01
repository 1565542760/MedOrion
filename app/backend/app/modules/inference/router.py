import logging
import uuid

from fastapi import APIRouter, HTTPException, Request

from app.db.session import SessionLocal
from app.modules.inference.model_service_client import ModelServiceError, infer_with_model_service
from app.modules.inference.persistence import ensure_stub_case, write_failure_event, write_success_bundle
from app.modules.inference.schemas import (
    InferenceTaskResponseV1,
    ModelInferenceRequestV1,
    ModelInferenceResponseV1,
    ReassessmentJobCreateRequestV1,
    ReassessmentJobResponseV1,
    RecommendationStubV1,
)

logger = logging.getLogger('app.inference')
router = APIRouter()


@router.post('/cases/{case_id}/inference-tasks', response_model=ModelInferenceResponseV1)
def create_case_inference_task(case_id: str, payload: ModelInferenceRequestV1, request: Request) -> ModelInferenceResponseV1:
    request_id = getattr(request.state, 'request_id', f'req_{uuid.uuid4().hex}')
    incoming_trace_id = getattr(request.state, 'trace_id', '-')
    trace_id = incoming_trace_id if incoming_trace_id != '-' else f'trace_stub_{uuid.uuid4().hex[:12]}'

    db = SessionLocal()
    try:
        case_id_db, patient_id_db = ensure_stub_case(db, case_id, payload.patient_id)

        ms_payload = {
            'trace_id': trace_id,
            'inference_task_id': f'itask_{uuid.uuid4().hex[:10]}',
            'case_id': case_id_db,
            'patient_id': patient_id_db,
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
            try:
                write_failure_event(
                    db,
                    trace_id=trace_id,
                    case_id=case_id_db,
                    patient_id=patient_id_db,
                    error_payload={'code': exc.code, 'message': exc.message, 'details': exc.details},
                )
            except Exception:
                db.rollback()
            raise HTTPException(
                status_code=exc.status_code,
                detail={
                    'code': exc.code,
                    'message': exc.message,
                    'retryable': exc.status_code >= 500,
                    'details': exc.details,
                },
            ) from exc

        persisted = write_success_bundle(
            db,
            trace_id=trace_id,
            case_id=case_id_db,
            patient_id=patient_id_db,
            disease_agent=payload.disease_agent,
            requested_task=payload.requested_task,
            model_version_policy=payload.model_version_policy,
            inputs=payload.inputs,
            missing_value_context=payload.missing_value_context,
            idempotency_key=payload.idempotency_key or f'idem_{uuid.uuid4().hex[:12]}',
            model_response=ms_resp,
        )

        recommendation = RecommendationStubV1(
            trace_id=trace_id,
            inference_task_id=persisted['inference_task_id'],
            model_version_id=ms_resp.get('model_version_id', 'unknown'),
            confidence=ms_resp.get('confidence', {}),
            uncertainty=ms_resp.get('uncertainty', {}),
            limitations=ms_resp.get('limitations', []),
            evidence_refs=[{'node_id': persisted['model_node_id'], 'node_type': 'model_output'}],
        )

        return ModelInferenceResponseV1(
            route=f'/api/v1/cases/{case_id}/inference-tasks',
            task_id=persisted['inference_task_id'],
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
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception('inference persistence failed trace_id=%s', trace_id)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={'code': 'inference_persistence_failed', 'message': str(exc)},
        ) from exc
    finally:
        db.close()


@router.get('/inference-tasks/{task_id}', response_model=InferenceTaskResponseV1)
def get_inference_task(task_id: str) -> InferenceTaskResponseV1:
    return InferenceTaskResponseV1(route=f'/api/v1/inference-tasks/{task_id}', task_id=task_id)


@router.post('/reassessment-jobs', response_model=ReassessmentJobResponseV1)
def create_reassessment_job(payload: ReassessmentJobCreateRequestV1) -> ReassessmentJobResponseV1:
    return ReassessmentJobResponseV1(route='/api/v1/reassessment-jobs', job_id=f'stub-{payload.case_id}')
