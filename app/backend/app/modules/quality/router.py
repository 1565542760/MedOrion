from fastapi import APIRouter

from app.modules.quality.schemas import (
    QualityReviewCreateRequestV1,
    QualityReviewListResponseV1,
    QualityReviewResponseV1,
)

router = APIRouter()


@router.get('/quality-reviews', response_model=QualityReviewListResponseV1)
def list_quality_reviews() -> QualityReviewListResponseV1:
    return QualityReviewListResponseV1()


@router.post('/quality-reviews', response_model=QualityReviewResponseV1)
def create_quality_review(payload: QualityReviewCreateRequestV1) -> QualityReviewResponseV1:
    _ = payload
    return QualityReviewResponseV1(route='/api/v1/quality-reviews')
