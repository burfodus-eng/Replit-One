import random
import time
import math
from datetime import datetime


class SensorSim:
    def __init__(self, seed=None, stage_config=None):
        self.rng = random.Random(seed or time.time())
        self.stage_config = stage_config or {}
        self.base_vin = 36.0
        self.base_vout = stage_config.get("nominal_voltage_v", 30.0) if stage_config else 30.0
        self.max_current = stage_config.get("max_current_a", 2.0) if stage_config else 2.0
    
    def read(self, duty=0.0, enabled=True):
        """
        Simulate realistic sensor readings based on duty cycle and LED configuration
        duty: 0.0 to 1.0 (0% to 100%)
        enabled: whether the stage is enabled
        """
        if not enabled:
            vin = self.base_vin + self.rng.uniform(-1, 1)
            iin = self.rng.uniform(0.0, 0.1)
            vout = self.base_vout + self.rng.uniform(-1, 1)
            iout = 0.0
            return vin, iin, vout, iout
        
        base_current = duty * self.max_current
        iout = base_current + self.rng.uniform(-0.05, 0.05)
        iout = max(0.0, iout)
        
        voltage_drop_factor = 1.0 - (duty * 0.08)
        vout = (self.base_vout * voltage_drop_factor) + self.rng.uniform(-0.3, 0.3)
        
        iin = (iout * 1.1) + self.rng.uniform(-0.02, 0.02)
        iin = max(0.0, iin)
        
        vin = self.base_vin + self.rng.uniform(-1.5, 1.5)
        
        return vin, iin, vout, iout


class PVSimulator:
    def __init__(self, max_power_w=600, seed=None):
        self.max_power_w = max_power_w
        self.rng = random.Random(seed or time.time())
        self.base_voltage = 48.0
    
    def get_diurnal_factor(self):
        """
        Returns 0.0 to 1.0 based on time of day (simulates sunrise/sunset)
        Peak at noon, 0 at night
        """
        now = datetime.now()
        hour = now.hour + now.minute / 60.0
        
        if hour < 6 or hour > 20:
            return 0.0
        elif hour < 8:
            return (hour - 6) / 2.0
        elif hour < 18:
            return 1.0 - 0.2 * abs(13 - hour) / 5.0
        else:
            return 1.0 - (hour - 18) / 2.0
    
    def read(self):
        """
        Returns simulated PV panel output
        """
        diurnal = self.get_diurnal_factor()
        
        cloud_factor = self.rng.uniform(0.7, 1.0)
        
        power_factor = diurnal * cloud_factor
        current_power = self.max_power_w * power_factor
        
        current = current_power / self.base_voltage if self.base_voltage > 0 else 0.0
        voltage = self.base_voltage + self.rng.uniform(-2, 2)
        
        return voltage, current, voltage, current
