from .base import BaseStage
from app.models import LED


class LEDStage(BaseStage):
    def __init__(self, stage_id: str, sensor, gpio=None, config=None):
        super().__init__(stage_id, sensor, gpio)
        self.id = stage_id
        self.name = config.get("name", stage_id) if config else stage_id
        self.description = config.get("description", "") if config else ""
        self.max_current_a = config.get("max_current_a", 3.0) if config else 3.0
        self.nominal_voltage_v = config.get("nominal_voltage_v", 36.0) if config else 36.0
        
        self.leds = []
        if config and "leds" in config:
            for led_config in config["leds"]:
                led = LED(
                    id=led_config["id"],
                    label=led_config["label"],
                    intensity_limit_pct=led_config["intensity_limit_pct"],
                    priority=led_config["priority"],
                    is_on=True,
                    current_intensity_pct=0.0
                )
                self.leds.append(led)
    
    def apply_control(self, duty: float | None = None, enable: bool | None = None):
        super().apply_control(duty, enable)
        
        for led in self.leds:
            if led.is_on:
                led.current_intensity_pct = (led.intensity_limit_pct / 100.0) * self.duty * 100
