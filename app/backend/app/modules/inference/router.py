from fastapi import APIRouter

from app.modules.inference.schemas import (
    InferenceTaskResponseV1,
    ModelInferenceRequestV1,
    ModelInferenceResponseV1,
    ReassessmentJobCreateRequestV1,
    ReassessmentJobResponseV1,
)

router = APIRouter()


@router.post('/cases/{case_id}/inference-tasks', response_model=ModelInferenceResponseV1)
def create_case_inference_task(case_id: str, payload: ModelInferenceRequestV1) -> ModelInferenceResponseV1:
    _ = payload
    return ModelInferenceResponseV1(route=f'/api/v1/cases/{case_id}/inference-tasks', task_id='stub-task')


@router.get('/inference-tasks/{task_id}', response_model=InferenceTaskResponseV1)
def get_inference_task(task_id: str) -> InferenceTaskResponseV1:
    return InferenceTaskResponseV1(route=f'/api/v1/inference-tasks/{task_id}', task_id=task_id)


@router.post('/reassessment-jobs', response_model=ReassessmentJobResponseV1)
def create_reassessment_job(payload: ReassessmentJobCreateRequestV1) -> ReassessmentJobResponseV1:
    return ReassessmentJobResponseV1(route='/api/v1/reassessment-jobs', job_id=f'stub-{payload.case_id}')
