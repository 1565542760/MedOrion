from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientCreateRequestV1(BaseModel):
    external_patient_id: str | None = None
    display_name: str | None = None
    name: str | None = None
    sex: str | None = None
    birth_date: date | None = None
    consent_status: str = 'unknown'


class PatientItemV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: str
    external_patient_id: str | None = None
    display_name: str | None = None
    sex: str | None = None
    birth_date: date | None = None
    consent_status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PatientResponseV1(BaseModel):
    status: str = 'ok'
    route: str
    item: PatientItemV1


class PatientListResponseV1(BaseModel):
    items: list[PatientItemV1] = Field(default_factory=list)
    total: int = 0
