from pydantic import BaseModel, Field


class PatientCreateRequestV1(BaseModel):
    patient_display_id: str | None = None


class PatientResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    patient_id: str | None = None


class PatientListResponseV1(BaseModel):
    items: list[PatientResponseV1] = Field(default_factory=list)
    total: int = 0
