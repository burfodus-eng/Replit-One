"""GPIO/PWM interface protocol definitions."""

from typing import Protocol


class PWMChannel(Protocol):
    """Protocol for PWM channel control."""
    
    def start(self, duty: float) -> None:
        """Start PWM with given duty cycle (0.0-1.0)."""
        ...
    
    def set_frequency(self, hz: int) -> None:
        """Set PWM frequency in Hz."""
        ...
    
    def set_duty(self, duty: float) -> None:
        """Set duty cycle (0.0-1.0)."""
        ...
    
    def stop(self) -> None:
        """Stop PWM output (set to 0)."""
        ...
