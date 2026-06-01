from pydantic import BaseModel, Field


class ModelRegistryCreateRequestV1(BaseModel):
    model_name: str


class ModelRegistryResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    model_name: str | None = None


class ModelRegistryListResponseV1(BaseModel):
    items: list[ModelRegistryResponseV1] = Field(default_factory=list)
    total: int = 0
