from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccessAuditEventItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_event_id: str
    actor_user_id: UUID | None = None
    actor_type: str | None = None
    actor_role: str | None = None
    access_mode: str
    resource_type: str
    resource_id: str | None = None
    case_id: UUID | None = None
    patient_id: UUID | None = None
    trace_id: str | None = None
    decision: str
    denial_reason: str | None = None
    policy_source: str | None = None
    request_id: str | None = None
    route_path: str | None = None
    method: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class AccessAuditEventListResponseV1(BaseModel):
    items: list[AccessAuditEventItemV1] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
