from fastapi import APIRouter

from app.modules.recommendations.schemas import (
    RecommendationCreateRequestV1,
    RecommendationListResponseV1,
    RecommendationResponseV1,
)

router = APIRouter()


@router.get('/cases/{case_id}/recommendations', response_model=RecommendationListResponseV1)
def list_recommendations(case_id: str) -> RecommendationListResponseV1:
    return RecommendationListResponseV1(
        items=[
            RecommendationResponseV1(
                route=f'/api/v1/cases/{case_id}/recommendations',
                case_id=case_id,
            )
        ]
    )


@router.post('/cases/{case_id}/recommendations', response_model=RecommendationResponseV1)
def create_recommendation_stub(case_id: str, payload: RecommendationCreateRequestV1) -> RecommendationResponseV1:
    _ = payload
    return RecommendationResponseV1(route=f'/api/v1/cases/{case_id}/recommendations', case_id=case_id)
