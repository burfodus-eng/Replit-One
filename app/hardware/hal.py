"""
Hardware Abstraction Layer (HAL)
Provides unified interface for wavemaker hardware control
"""
import os
from typing import Dict
from .pca import create_pca9685
from .sensors import SensorArray

HARDWARE_MODE = os.getenv("HARDWARE_MODE", "sim")


class WavemakerHAL:
    """Hardware abstraction for 6-channel wavemaker system"""
    
    def __init__(self):
        self.pca = create_pca9685(address=0x40)
        self.pca.set_pwm_freq(1000)
        
        sensor_addresses = {
            0: 0x40,
            1: 0x41,
            2: 0x44,
            3: 0x45,
            4: 0x48,
            5: 0x49
        }
        self.sensors = SensorArray(sensor_addresses)
        
        self.channel_map = {
            0: 0,
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5
        }
        
    def set_channel_pwm(self, channel_id: int, duty: float):
        """
        Set PWM duty cycle for a channel
        
        Args:
            channel_id: Channel number (0-5)
            duty: Duty cycle 0.0 to 1.0
        """
        if channel_id not in self.channel_map:
            return
            
        duty = max(0.0, min(1.0, duty))
        pwm_channel = self.channel_map[channel_id]
        
        self.pca.set_pwm_duty(pwm_channel, duty)
        
        self.sensors.update_pwm_duty(channel_id, duty)
        
    def read_channel_power(self, channel_id: int) -> Dict[str, float]:
        """
        Read power telemetry for a channel
        
        Returns:
            Dict with voltage, current, power
        """
        return self.sensors.read_channel(channel_id)
        
    def read_all_power(self) -> Dict[int, Dict[str, float]]:
        """Read power for all channels"""
        return {
            channel_id: self.read_channel_power(channel_id)
            for channel_id in range(6)
        }
        
    def shutdown_all(self):
        """Emergency shutdown - set all channels to 0%"""
        for channel_id in range(6):
            self.set_channel_pwm(channel_id, 0.0)
