"""
PCA9685 PWM Controller - Hardware Abstraction
Supports both simulated and real PCA9685 16-channel PWM driver
"""
import os
import time
import math
from typing import Optional

HARDWARE_MODE = os.getenv("HARDWARE_MODE", "sim")


class PCA9685Simulated:
    """Simulated PCA9685 for development/testing"""
    
    def __init__(self, address: int = 0x40):
        self.address = address
        self.channels = [0] * 16
        self.frequency = 1000
        
    def set_pwm_freq(self, freq: int):
        """Set PWM frequency"""
        self.frequency = freq
        
    def set_pwm(self, channel: int, on: int, off: int):
        """Set PWM duty cycle for a channel"""
        if 0 <= channel < 16:
            duty = off / 4096.0
            self.channels[channel] = duty
            
    def set_pwm_duty(self, channel: int, duty: float):
        """Set PWM duty cycle (0.0 to 1.0)"""
        if 0 <= channel < 16:
            off_value = int(duty * 4095)
            self.set_pwm(channel, 0, off_value)
            self.channels[channel] = duty


class PCA9685Real:
    """Real PCA9685 hardware driver"""
    
    def __init__(self, address: int = 0x40):
        try:
            from adafruit_pca9685 import PCA9685
            import board
            import busio
            
            i2c = busio.I2C(board.SCL, board.SDA)
            self.pca = PCA9685(i2c, address=address)
            self.pca.frequency = 1000
        except ImportError:
            raise RuntimeError("Real hardware libraries not available. Install adafruit-circuitpython-pca9685")
            
    def set_pwm_freq(self, freq: int):
        """Set PWM frequency"""
        self.pca.frequency = freq
        
    def set_pwm(self, channel: int, on: int, off: int):
        """Set PWM for channel"""
        self.pca.channels[channel].duty_cycle = off
        
    def set_pwm_duty(self, channel: int, duty: float):
        """Set PWM duty cycle (0.0 to 1.0)"""
        duty_cycle = int(duty * 65535)
        self.pca.channels[channel].duty_cycle = duty_cycle


def create_pca9685(address: int = 0x40):
    """Factory function to create appropriate PCA9685 instance"""
    if HARDWARE_MODE == "pi":
        return PCA9685Real(address)
    else:
        return PCA9685Simulated(address)
