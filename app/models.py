from typing import Optional, Literal, List
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


class LED(BaseModel):
    id: str
    label: str
    intensity_limit_pct: int
    priority: int
    is_on: bool = True
    current_intensity_pct: float = 0.0


class ArrayConfig(BaseModel):
    id: str
    name: str
    description: str
    max_current_a: float
    nominal_voltage_v: float
    leds: List[LED]


class ArrayStatus(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool
    mode: Mode
    duty: float
    leds: List[LED]
    vin_v: float
    iin_a: float
    vout_v: float
    iout_a: float
    power_w: float


class LEDSettingsUpdate(BaseModel):
    label: Optional[str] = None
    intensity_limit_pct: Optional[int] = None
    priority: Optional[int] = None
    is_on: Optional[bool] = None


class ArraySettingsRequest(BaseModel):
    leds: dict[str, LEDSettingsUpdate]


class SystemLoad(BaseModel):
    pv_w: float
    load_w: float
    battery_w: float
    net_w: float
    budget_w: float
    timestamp: datetime


class PowerEvent(BaseModel):
    timestamp: datetime
    event_type: Literal["shed", "restore", "alert", "warning"]
    array_id: Optional[str] = None
    led_id: Optional[str] = None
    message: str
    details: Optional[dict] = None


class HistoryPoint(BaseModel):
    t: datetime
    v: float
    i: float
    p: float


WavemakerMode = Literal["off", "constant", "pulse", "gyre_left", "gyre_right", "random_reef"]


class WavemakerChannel(BaseModel):
    id: int
    name: str
    mode: WavemakerMode
    target_power_pct: int
    pulse_duty_ratio: float
    current_power_w: float
    voltage_v: float
    current_a: float


class WavemakerControlRequest(BaseModel):
    mode: Optional[WavemakerMode] = None
    target_power_pct: Optional[int] = None
    pulse_duty_ratio: Optional[float] = None


class WavemakerHistoryPoint(BaseModel):
    t: datetime
    power_w: float
    duty_pct: float
    pulse_duty_ratio: float
