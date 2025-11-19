"""Real Raspberry Pi GPIO driver using pigpio library."""

import logging

try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    logging.warning("pigpio not available - using mock GPIO")


class PigpioPWM:
    """PWM control using pigpio library for Raspberry Pi."""
    
    def __init__(self, pin: int, freq: int = 500):
        """
        Initialize PWM on a GPIO pin.
        
        Args:
            pin: BCM GPIO pin number
            freq: PWM frequency in Hz
        """
        if not PIGPIO_AVAILABLE:
            raise ImportError("pigpio library not available")
            
        self.pin = pin
        self.freq = freq
        self.pi = pigpio.pi()
        
        if not self.pi.connected:
            raise RuntimeError(f"Failed to connect to pigpiod daemon")
        
        self.pi.set_mode(pin, pigpio.OUTPUT)
        self.set_frequency(freq)
        self.set_duty(0.0)
        
        logging.info(f"Initialized pigpio PWM on GPIO{pin} at {freq}Hz")
    
    def set_frequency(self, hz: int) -> None:
        """Set PWM frequency in Hz."""
        self.freq = hz
        self.pi.set_PWM_frequency(self.pin, hz)
    
    def set_duty(self, duty: float) -> None:
        """
        Set duty cycle.
        
        Args:
            duty: Duty cycle from 0.0 (0%) to 1.0 (100%)
        """
        duty = max(0.0, min(1.0, duty))
        # pigpio uses 0-255 range for duty cycle
        self.pi.set_PWM_dutycycle(self.pin, int(duty * 255))
    
    def start(self, duty: float = 0.0) -> None:
        """Start PWM with given duty cycle."""
        self.set_duty(duty)
    
    def stop(self) -> None:
        """Stop PWM output."""
        self.pi.set_PWM_dutycycle(self.pin, 0)
    
    def cleanup(self) -> None:
        """Cleanup GPIO resources."""
        self.stop()
        self.pi.stop()
