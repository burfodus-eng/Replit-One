"""
INA219/INA226 Power Sensors - Hardware Abstraction
Supports both simulated and real power monitoring sensors
"""
import os
import time
import random
import math
from typing import Dict

HARDWARE_MODE = os.getenv("HARDWARE_MODE", "sim")


class INA219Simulated:
    """Simulated INA219 power sensor"""
    
    def __init__(self, address: int, max_expected_amps: float = 2.0):
        self.address = address
        self.max_amps = max_expected_amps
        self.base_voltage = 24.0
        self.pwm_duty = 0.0
        self.last_update = time.time()
        
    def set_pwm_duty(self, duty: float):
        """Update the PWM duty cycle to calculate realistic power"""
        self.pwm_duty = max(0.0, min(1.0, duty))
        
    def voltage(self) -> float:
        """Simulate bus voltage with slight variation"""
        base_drop = 0.5 * self.pwm_duty
        noise = random.uniform(-0.1, 0.1)
        return self.base_voltage - base_drop + noise
        
    def current(self) -> float:
        """Simulate current draw based on PWM duty"""
        if self.pwm_duty < 0.05:
            return 0.0
            
        base_current = self.max_amps * self.pwm_duty
        efficiency = 0.85 + 0.1 * self.pwm_duty
        noise = random.uniform(-0.02, 0.02)
        
        return (base_current / efficiency) + noise
        
    def power(self) -> float:
        """Calculate power (V * I)"""
        return self.voltage() * self.current()


class INA219Real:
    """Real INA219 hardware sensor"""
    
    def __init__(self, address: int, max_expected_amps: float = 2.0):
        try:
            from ina219 import INA219
            self.ina = INA219(shunt_ohms=0.1, max_expected_amps=max_expected_amps, address=address)
            self.ina.configure(voltage_range=self.ina.RANGE_32V)
        except ImportError:
            raise RuntimeError("Real hardware libraries not available. Install pi-ina219")
            
    def set_pwm_duty(self, duty: float):
        """No-op for real sensors - they measure actual current draw"""
        pass
            
    def voltage(self) -> float:
        """Read bus voltage"""
        return self.ina.voltage()
        
    def current(self) -> float:
        """Read current in amps"""
        return self.ina.current() / 1000.0
        
    def power(self) -> float:
        """Read power in watts"""
        return self.ina.power() / 1000.0


class SensorArray:
    """Manages multiple power sensors"""
    
    def __init__(self, sensor_addresses: Dict[int, int]):
        """
        Args:
            sensor_addresses: Dict mapping channel_id to I2C address
        """
        self.sensors: Dict[int, INA219Simulated | INA219Real] = {}
        
        for channel_id, address in sensor_addresses.items():
            if HARDWARE_MODE == "pi":
                self.sensors[channel_id] = INA219Real(address, max_expected_amps=3.0)
            else:
                self.sensors[channel_id] = INA219Simulated(address, max_expected_amps=2.5)
                
    def read_channel(self, channel_id: int) -> Dict[str, float]:
        """Read voltage, current, power for a channel"""
        if channel_id not in self.sensors:
            return {"voltage": 0.0, "current": 0.0, "power": 0.0}
            
        sensor = self.sensors[channel_id]
        return {
            "voltage": round(sensor.voltage(), 2),
            "current": round(sensor.current(), 3),
            "power": round(sensor.power(), 2)
        }
        
    def update_pwm_duty(self, channel_id: int, duty: float):
        """Update PWM duty for simulated sensors (no-op for real sensors)"""
        if channel_id in self.sensors:
            self.sensors[channel_id].set_pwm_duty(duty)
