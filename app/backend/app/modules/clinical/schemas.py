from pydantic import BaseModel, Field


class MissingValueQueryCreateRequestV1(BaseModel):
    field_path: str | None = None


class MissingValueQueryResponseV1(BaseModel):
    status: str = 'stub'
    route: str
    case_id: str


class MissingValueQueryListResponseV1(BaseModel):
    items: list[MissingValueQueryResponseV1] = Field(default_factory=list)
    total: int = 0
