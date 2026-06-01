from fastapi import APIRouter

from app.modules.feedback.schemas import (
    DoctorFeedbackCreateRequestV1,
    DoctorFeedbackListResponseV1,
    DoctorFeedbackResponseV1,
)

router = APIRouter()


@router.get('/', response_model=DoctorFeedbackListResponseV1)
def list_feedback() -> DoctorFeedbackListResponseV1:
    return DoctorFeedbackListResponseV1()


@router.post('/', response_model=DoctorFeedbackResponseV1)
def create_feedback(payload: DoctorFeedbackCreateRequestV1) -> DoctorFeedbackResponseV1:
    _ = payload
    return DoctorFeedbackResponseV1(route='/api/v1/feedback')
