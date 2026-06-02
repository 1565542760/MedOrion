
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ModelRegistryCreateRequestV1(BaseModel):
    model_name: str
    disease_agent: str
    task_type: str
    modality_scope: list[str] = Field(default_factory=list)
    owner_team: str | None = None
    description: str | None = None
    is_active: bool = True


class ModelVersionCreateRequestV1(BaseModel):
    version_label: str
    approval_state: str = 'draft'
    contract_version: str = 'v1'
    artifact_ref: dict | str = Field(default_factory=dict)
    input_schema: dict | str = Field(default_factory=dict)
    output_schema: dict | str = Field(default_factory=dict)
    metrics: dict | str = Field(default_factory=dict)
    runtime_constraints: dict | str = Field(default_factory=dict)
    notes: str | None = None


class ModelVersionPromoteRequestV1(BaseModel):
    target_state: str


class ModelVersionRollbackRequestV1(BaseModel):
    rollback_to_version_id: UUID


class ModelVersionItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version_id: UUID
    model_id: UUID
    version_label: str
    approval_state: str
    contract_version: str
    artifact_ref: dict | str = Field(default_factory=dict)
    input_schema: dict | str = Field(default_factory=dict)
    output_schema: dict | str = Field(default_factory=dict)
    metrics: dict | str = Field(default_factory=dict)
    runtime_constraints: dict | str = Field(default_factory=dict)
    notes: str | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    promoted_by: UUID | None = None
    promoted_at: datetime | None = None
    archived_at: datetime | None = None
    rollback_from_version_id: UUID | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelRegistrySummaryItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_id: UUID
    model_name: str
    disease_agent: str
    task_type: str
    modality_scope: list[str] = Field(default_factory=list)
    owner_team: str | None = None
    description: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelRegistryDetailItemV1(ModelRegistrySummaryItemV1):
    versions: list[ModelVersionItemV1] = Field(default_factory=list)


class ModelRegistryResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: ModelRegistryDetailItemV1


class ModelRegistryListResponseV1(BaseModel):
    items: list[ModelRegistrySummaryItemV1] = Field(default_factory=list)
    total: int = 0


class ModelVersionResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: ModelVersionItemV1


class ModelVersionEvaluationsItemV1(BaseModel):
    version_id: UUID
    model_id: UUID
    approval_state: str
    artifact_ref: dict | str = Field(default_factory=dict)
    metrics: dict | str = Field(default_factory=dict)
    runtime_constraints: dict | str = Field(default_factory=dict)
    notes: str | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelVersionEvaluationsResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: ModelVersionEvaluationsItemV1
