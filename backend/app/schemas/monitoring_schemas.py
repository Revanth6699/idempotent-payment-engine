from typing import Literal

from pydantic import BaseModel, ConfigDict


ComponentStatus = Literal["healthy", "unhealthy"]


class ComponentHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ComponentStatus
    detail: str


class MonitoringStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["healthy", "degraded"]
    service: str
    database: ComponentHealth
    redpanda: ComponentHealth