"""Mock GPIO driver for development/testing without hardware."""

import logging
from typing import Dict


class PigpioPWM:
    """Mock PWM channel for development without Raspberry Pi."""
    
    _instances: Dict[int, 'PigpioPWM'] = {}
    
    def __init__(self, pin: int, freq: int = 500):
        """
        Initialize mock PWM on a virtual pin.
        
        Args:
            pin: Virtual GPIO pin number
            freq: PWM frequency in Hz
        """
        self.pin = pin
        self.freq = freq
        self.duty = 0.0
        self.running = False
        
        PigpioPWM._instances[pin] = self
        logging.info(f"[MOCK] Initialized virtual PWM on GPIO{pin} at {freq}Hz")
    
    def set_frequency(self, hz: int) -> None:
        """Set PWM frequency in Hz."""
        old_freq = self.freq
        self.freq = hz
        logging.debug(f"[MOCK] GPIO{self.pin} frequency changed: {old_freq}Hz → {hz}Hz")
    
    def set_duty(self, duty: float) -> None:
        """Set duty cycle (0.0-1.0)."""
        duty = max(0.0, min(1.0, duty))
        if abs(self.duty - duty) > 0.01:  # Log significant changes only
            logging.debug(f"[MOCK] GPIO{self.pin} duty: {self.duty:.2%} → {duty:.2%}")
        self.duty = duty
        self.running = (duty > 0)
    
    def start(self, duty: float = 0.0) -> None:
        """Start PWM with given duty cycle."""
        self.running = True
        self.set_duty(duty)
        logging.info(f"[MOCK] Started PWM on GPIO{self.pin} at {duty:.2%}")
    
    def stop(self) -> None:
        """Stop PWM output."""
        self.running = False
        self.duty = 0.0
        logging.info(f"[MOCK] Stopped PWM on GPIO{self.pin}")
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.stop()
        if self.pin in PigpioPWM._instances:
            del PigpioPWM._instances[self.pin]
    
    @classmethod
    def get_all_states(cls) -> Dict[int, dict]:
        """Get current state of all mock PWM channels (for debugging)."""
        return {
            pin: {
                "duty": inst.duty,
                "freq": inst.freq,
                "running": inst.running
            }
            for pin, inst in cls._instances.items()
        }
