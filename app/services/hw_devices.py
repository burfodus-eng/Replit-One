"""Device registry for managing hardware PWM devices (wavemakers, LEDs)."""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

try:
    import pigpio
    # If pigpio module exists, try to use it
    from app.hw.pigpio_driver import PigpioPWM
    GPIO_MODE = "HARDWARE"
except (ImportError, RuntimeError):
    # Pigpio not available, use mock
    from app.hw.gpio_mock import PigpioPWM
    GPIO_MODE = "MOCK"

logging.info(f"GPIO Mode: {GPIO_MODE}")


@dataclass
class DeviceConfig:
    """Configuration for a PWM device."""
    name: str
    gpio_pin: int
    pwm_freq_hz: int
    min_intensity: float = 0.0
    max_intensity: float = 1.0
    volts_min: float = 0.0
    volts_max: float = 5.0


class PWMDevice:
    """Represents a single PWM-controlled device (wavemaker or LED)."""
    
    def __init__(self, config: DeviceConfig):
        """
        Initialize PWM device.
        
        Args:
            config: Device configuration
        """
        self.config = config
        self.hw = PigpioPWM(config.gpio_pin, config.pwm_freq_hz)
        self.current_duty = 0.0
        
        logging.info(
            f"Initialized {config.name} on GPIO{config.gpio_pin} "
            f"({config.pwm_freq_hz}Hz, range {config.min_intensity:.2f}-{config.max_intensity:.2f})"
        )
    
    def apply(self, intensity: float) -> None:
        """
        Apply intensity value to device.
        
        Args:
            intensity: Target intensity [0.0-1.0]
        """
        # Clamp to [0, 1]
        intensity = max(0.0, min(1.0, intensity))
        
        # Map to [min_intensity, max_intensity] range
        scaled = self.config.min_intensity + intensity * (
            self.config.max_intensity - self.config.min_intensity
        )
        
        self.hw.set_duty(scaled)
        self.current_duty = scaled
    
    def set_frequency(self, freq_hz: int) -> None:
        """Update PWM frequency."""
        self.config.pwm_freq_hz = freq_hz
        self.hw.set_frequency(freq_hz)
    
    def set_range(self, min_intensity: float, max_intensity: float) -> None:
        """Update intensity range."""
        self.config.min_intensity = min_intensity
        self.config.max_intensity = max_intensity
    
    def stop(self) -> None:
        """Stop device output."""
        self.hw.stop()
        self.current_duty = 0.0
    
    def get_voltage(self) -> float:
        """Calculate approximate output voltage based on current duty."""
        return self.config.volts_min + self.current_duty * (
            self.config.volts_max - self.config.volts_min
        )
    
    def to_dict(self) -> dict:
        """Export device state as dictionary."""
        return {
            "name": self.config.name,
            "gpio_pin": self.config.gpio_pin,
            "pwm_freq_hz": self.config.pwm_freq_hz,
            "min_intensity": self.config.min_intensity,
            "max_intensity": self.config.max_intensity,
            "volts_min": self.config.volts_min,
            "volts_max": self.config.volts_max,
            "current_duty": self.current_duty,
            "current_voltage": self.get_voltage(),
        }


class DeviceRegistry:
    """Central registry for all PWM devices."""
    
    def __init__(self):
        """Initialize empty registry."""
        self.wavemakers: Dict[str, PWMDevice] = {}
        self.leds: Dict[str, PWMDevice] = {}
        self.mode = GPIO_MODE
    
    def register_wavemaker(self, device_id: str, config: DeviceConfig) -> PWMDevice:
        """
        Register a wavemaker device.
        
        Args:
            device_id: Unique identifier (e.g., "WM1")
            config: Device configuration
            
        Returns:
            Created PWMDevice instance
        """
        device = PWMDevice(config)
        self.wavemakers[device_id] = device
        logging.info(f"Registered wavemaker {device_id}")
        return device
    
    def register_led(self, device_id: str, config: DeviceConfig) -> PWMDevice:
        """
        Register an LED device.
        
        Args:
            device_id: Unique identifier (e.g., "LED1")
            config: Device configuration
            
        Returns:
            Created PWMDevice instance
        """
        device = PWMDevice(config)
        self.leds[device_id] = device
        logging.info(f"Registered LED {device_id}")
        return device
    
    def get_wavemaker(self, device_id: str) -> Optional[PWMDevice]:
        """Get wavemaker device by ID."""
        return self.wavemakers.get(device_id)
    
    def get_led(self, device_id: str) -> Optional[PWMDevice]:
        """Get LED device by ID."""
        return self.leds.get(device_id)
    
    def stop_all(self) -> None:
        """Emergency stop - zero all outputs."""
        logging.warning("EMERGENCY STOP - Zeroing all device outputs")
        for device in list(self.wavemakers.values()) + list(self.leds.values()):
            device.stop()
    
    def get_all_states(self) -> dict:
        """Get current state of all devices."""
        return {
            "mode": self.mode,
            "wavemakers": {
                device_id: device.to_dict()
                for device_id, device in self.wavemakers.items()
            },
            "leds": {
                device_id: device.to_dict()
                for device_id, device in self.leds.items()
            },
        }


# Global registry instance
registry = DeviceRegistry()
