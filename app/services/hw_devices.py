"""Device registry for managing hardware PWM devices (wavemakers, LEDs)."""

import logging
import os
from typing import Dict, Optional
from dataclasses import dataclass

# Determine GPIO driver based on HARDWARE_MODE environment variable
HARDWARE_MODE = os.getenv("HARDWARE_MODE", "mock").lower()

if HARDWARE_MODE == "esp32":
    # ESP32 serial USB adapter
    try:
        from app.hw.esp32_serial import PigpioPWM
        GPIO_MODE = "ESP32"
        logging.info("GPIO Mode: ESP32 Serial (USB adapter)")
    except ImportError as e:
        logging.error(f"Failed to load ESP32 driver: {e}")
        from app.hw.gpio_mock import PigpioPWM
        GPIO_MODE = "MOCK (ESP32 fallback)"
        logging.warning("Falling back to MOCK mode")
elif HARDWARE_MODE in ("pi", "pigpio", "real"):
    # Raspberry Pi with pigpio
    try:
        import pigpio
        from app.hw.pigpio_driver import PigpioPWM
        GPIO_MODE = "PIGPIO"
        logging.info("GPIO Mode: PIGPIO (Raspberry Pi)")
    except (ImportError, RuntimeError) as e:
        logging.warning(f"Pigpio not available: {e}")
        from app.hw.gpio_mock import PigpioPWM
        GPIO_MODE = "MOCK (pigpio fallback)"
else:
    # Default to mock/simulation
    from app.hw.gpio_mock import PigpioPWM
    GPIO_MODE = "MOCK"
    logging.info("GPIO Mode: MOCK (simulation)")

logging.info(f"GPIO Driver loaded: {GPIO_MODE}")


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
    gpio_pin_monitor: Optional[int] = None
    channel_name: Optional[str] = None


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
    
    def cleanup(self) -> None:
        """Clean up hardware resources."""
        try:
            self.hw.stop()
            if hasattr(self.hw, 'cleanup'):
                self.hw.cleanup()
        except Exception as e:
            logging.error(f"Error during cleanup of {self.config.name}: {e}")
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
            "gpio_pin_monitor": self.config.gpio_pin_monitor,
            "channel_name": self.config.channel_name,
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
    
    def unregister_device(self, device_id: str) -> bool:
        """
        Unregister a device, stopping output and cleaning up resources.
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if device was found and unregistered, False otherwise
        """
        # Try wavemakers first
        device = self.wavemakers.get(device_id)
        if device:
            device.stop()
            device.cleanup()
            del self.wavemakers[device_id]
            logging.info(f"Unregistered wavemaker {device_id}")
            return True
        
        # Try LEDs
        device = self.leds.get(device_id)
        if device:
            device.stop()
            device.cleanup()
            del self.leds[device_id]
            logging.info(f"Unregistered LED {device_id}")
            return True
        
        logging.warning(f"Device {device_id} not found in registry")
        return False
    
    def update_device_config(self, device_id: str, config: DeviceConfig, device_type: str) -> bool:
        """
        Update device configuration in-place without hardware re-initialization.
        
        Use this for intensity/voltage range changes that don't require GPIO changes.
        
        Args:
            device_id: Device identifier
            config: New device configuration
            device_type: 'WAVEMAKER' or 'LED'
            
        Returns:
            True if device was found and updated
        """
        if device_type == 'WAVEMAKER':
            device = self.wavemakers.get(device_id)
        else:
            device = self.leds.get(device_id)
        
        if not device:
            logging.warning(f"Device {device_id} not found for config update")
            return False
        
        # Update config parameters in-place
        device.config.name = config.name
        device.config.min_intensity = config.min_intensity
        device.config.max_intensity = config.max_intensity
        device.config.volts_min = config.volts_min
        device.config.volts_max = config.volts_max
        device.config.gpio_pin_monitor = config.gpio_pin_monitor
        device.config.channel_name = config.channel_name
        
        # Update PWM frequency if it changed (doesn't require re-init)
        if device.config.pwm_freq_hz != config.pwm_freq_hz:
            device.set_frequency(config.pwm_freq_hz)
        
        logging.info(f"Updated {device_id} config in-place: range {config.min_intensity:.2f}-{config.max_intensity:.2f}")
        return True
    
    def reload_device(self, device_id: str, config: DeviceConfig, device_type: str) -> PWMDevice:
        """
        Reload a device with new configuration (hot-reload for GPIO pin changes).
        
        Args:
            device_id: Device identifier
            config: New device configuration
            device_type: 'WAVEMAKER' or 'LED'
            
        Returns:
            Reloaded PWMDevice instance
        """
        # Clean up old device
        if device_type == 'WAVEMAKER':
            old_device = self.wavemakers.get(device_id)
            if old_device:
                old_device.stop()
                old_device.cleanup()
                logging.info(f"Cleaned up old wavemaker {device_id}")
        else:
            old_device = self.leds.get(device_id)
            if old_device:
                old_device.stop()
                old_device.cleanup()
                logging.info(f"Cleaned up old LED {device_id}")
        
        # Create new device with updated config
        new_device = PWMDevice(config)
        
        if device_type == 'WAVEMAKER':
            self.wavemakers[device_id] = new_device
            logging.info(f"Reloaded wavemaker {device_id} on GPIO{config.gpio_pin}")
        else:
            self.leds[device_id] = new_device
            logging.info(f"Reloaded LED {device_id} on GPIO{config.gpio_pin}")
        
        return new_device


# Global registry instance
registry = DeviceRegistry()
