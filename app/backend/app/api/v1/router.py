
from fastapi import APIRouter

from app.modules.assets.router import router as assets_router
from app.modules.auth.router import router as auth_router
from app.modules.cases.router import router as cases_router
from app.modules.clinical.router import router as clinical_router
from app.modules.feedback.router import router as feedback_router
from app.modules.inference.router import router as inference_router
from app.modules.model_registry.router import router as model_registry_router, version_router as model_version_router
from app.modules.patients.router import router as patients_router
from app.modules.quality.router import router as quality_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.traces.router import router as traces_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(patients_router, prefix='/patients', tags=['patients'])
api_router.include_router(cases_router, prefix='/cases', tags=['cases'])
api_router.include_router(assets_router, tags=['case-inputs'])
api_router.include_router(clinical_router, tags=['case-missing-values'])
api_router.include_router(inference_router, tags=['inference'])
api_router.include_router(recommendations_router, tags=['recommendations'])
api_router.include_router(model_registry_router, prefix='/model-registry', tags=['model-registry'])
api_router.include_router(model_version_router, tags=['model-versions'])
api_router.include_router(feedback_router, prefix='/feedback', tags=['feedback'])
api_router.include_router(traces_router, tags=['traces'])
api_router.include_router(quality_router, tags=['quality-reviews'])
