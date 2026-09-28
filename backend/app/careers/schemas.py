from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RiasecProfileResponse(BaseModel):
    realistic: float | None = None
    investigative: float | None = None
    artistic: float | None = None
    social: float | None = None
    enterprising: float | None = None
    conventional: float | None = None

    model_config = ConfigDict(from_attributes=True)


class CareerListResponse(BaseModel):
    id: UUID
    onet_soc_code: str
    title: str
    description: str | None = None
    job_zone: int | None = None
    onet_version: str

    model_config = ConfigDict(from_attributes=True)


class CareerDetailResponse(CareerListResponse):
    riasec_profile: RiasecProfileResponse | None = None