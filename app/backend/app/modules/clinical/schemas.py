from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MissingValueQueryCreateRequestV1(BaseModel):
    field_name: str
    field_label: str | None = None
    modality: str | None = None
    reason: str | None = None
    question_text: str
    policy_version: str = 'v1'
    trace_id: str | None = None


class MissingValueQueryAnswerRequestV1(BaseModel):
    doctor_answer_text: str | None = None
    doctor_answer_json: dict | None = None


class MissingValueQueryDefaultRequestV1(BaseModel):
    default_strategy_code: str
    default_reason: str
    default_value_json: dict | None = None


class MissingValueQueryItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query_id: str
    case_id: str
    patient_id: str | None = None
    field_name: str
    field_label: str | None = None
    modality: str | None = None
    reason: str | None = None
    question_text: str
    status: str
    trace_id: str
    policy_version: str
    value_source: str
    doctor_answer_text: str | None = None
    doctor_answer_json: dict | None = None
    default_strategy_code: str | None = None
    default_reason: str | None = None
    default_value_json: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MissingValueQueryResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: MissingValueQueryItemV1


class MissingValueQueryListResponseV1(BaseModel):
    items: list[MissingValueQueryItemV1] = Field(default_factory=list)
    total: int = 0
