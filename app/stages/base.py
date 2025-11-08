from typing import Literal
Mode = Literal["OFF", "MANUAL", "AUTO", "REDUNDANT"]


class BaseStage:
    def __init__(self, stage_id: str, sensor, gpio=None):
        self.stage_id = stage_id
        self.sensor = sensor
        self.gpio = gpio
        self.mode: Mode = "OFF"
        self.enabled = True
        self.duty = 0.0
    def read_telemetry(self):
        vin, iin, vout, iout = self.sensor.read()
        return dict(vin_v=vin, iin_a=iin, vout_v=vout, iout_a=iout)
    def apply_control(self, duty: float | None = None, enable: bool | None = None):
        if duty is not None:
            self.duty = max(0.0, min(1.0, duty))
        if enable is not None:
            self.enabled = bool(enable)
    def set_mode(self, mode: Mode):
        self.mode = mode
    def tick(self, config):
        pass
