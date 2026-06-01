from fastapi import APIRouter

from app.modules.model_registry.schemas import (
    ModelRegistryCreateRequestV1,
    ModelRegistryListResponseV1,
    ModelRegistryResponseV1,
)

router = APIRouter()


@router.get('/', response_model=ModelRegistryListResponseV1)
def list_models() -> ModelRegistryListResponseV1:
    return ModelRegistryListResponseV1()


@router.post('/', response_model=ModelRegistryResponseV1)
def register_model(payload: ModelRegistryCreateRequestV1) -> ModelRegistryResponseV1:
    return ModelRegistryResponseV1(route='/api/v1/model-registry', model_name=payload.model_name)
