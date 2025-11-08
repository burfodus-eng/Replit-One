from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel


Mode = Literal["OFF", "MANUAL", "AUTO", "REDUNDANT"]


class Telemetry(BaseModel):
    stage_id: str
    ts: datetime
    vin_v: float
    iin_a: float
    vout_v: float
    iout_a: float
    mode: Mode


class ControlRequest(BaseModel):
    stage_id: str
    mode: Mode
    duty: Optional[float] = None
    enable: Optional[bool] = None


class StageStatus(BaseModel):
    stage_id: str
    enabled: bool
    mode: Mode
    duty: float
