"""Real-time pattern engine for wavemaker control."""

import math
import time
import logging
from typing import Dict, Optional, Literal
from dataclasses import dataclass


PatternMode = Literal["OFF", "CONSTANT", "PULSE", "GYRE", "RANDOM"]


@dataclass
class PatternConfig:
    """Configuration for a pattern."""
    mode: PatternMode = "CONSTANT"
    period_s: float = 5.0
    on_ratio: float = 0.5
    phase_deg: float = 0.0
    min_intensity: float = 0.0
    max_intensity: float = 1.0


class Pattern:
    """Real-time pattern generator for wavemaker control."""
    
    def __init__(self, config: PatternConfig):
        """
        Initialize pattern generator.
        
        Args:
            config: Pattern configuration
        """
        self.config = config
        self.phase_rad = math.radians(config.phase_deg)
        self.start_time = time.time()
        self._last_random = 0.5
        self._random_target = 0.5
        self._random_update_time = 0.0
        
    def value(self, t: Optional[float] = None) -> float:
        """
        Calculate pattern value at given time.
        
        Args:
            t: Timestamp (seconds since epoch). If None, uses current time.
            
        Returns:
            Intensity value [0.0-1.0]
        """
        if t is None:
            t = time.time()
        
        # Time relative to start
        rel_t = t - self.start_time
        
        # Calculate base pattern value [0, 1]
        if self.config.mode == "OFF":
            raw = 0.0
        elif self.config.mode == "CONSTANT":
            raw = 1.0
        elif self.config.mode == "PULSE":
            raw = self._pulse_pattern(rel_t)
        elif self.config.mode == "GYRE":
            raw = self._gyre_pattern(rel_t)
        elif self.config.mode == "RANDOM":
            raw = self._random_pattern(rel_t)
        else:
            raw = 0.0
        
        # Scale to [min_intensity, max_intensity]
        return self.config.min_intensity + raw * (
            self.config.max_intensity - self.config.min_intensity
        )
    
    def _pulse_pattern(self, t: float) -> float:
        """Generate pulse pattern."""
        if self.config.period_s <= 0:
            return 1.0
        
        phase = (t % self.config.period_s) / self.config.period_s
        return 1.0 if phase < self.config.on_ratio else 0.0
    
    def _gyre_pattern(self, t: float) -> float:
        """Generate sinusoidal gyre pattern."""
        if self.config.period_s <= 0:
            return 0.5
        
        phase = (t % self.config.period_s) / self.config.period_s
        return 0.5 * (1.0 + math.sin(2 * math.pi * phase + self.phase_rad))
    
    def _random_pattern(self, t: float) -> float:
        """Generate smooth random pattern with transitions."""
        # Update target every ~10 seconds
        if t - self._random_update_time > 10.0:
            self._random_target = 0.3 + 0.7 * (hash(int(t / 10)) % 1000) / 1000
            self._random_update_time = t
        
        # Smooth transition to target
        alpha = min(1.0, (t - self._random_update_time) / 5.0)
        self._last_random = self._last_random * (1 - alpha) + self._random_target * alpha
        return self._last_random
    
    def update_config(self, config: PatternConfig) -> None:
        """Update pattern configuration."""
        self.config = config
        self.phase_rad = math.radians(config.phase_deg)
    
    def reset(self) -> None:
        """Reset pattern to start."""
        self.start_time = time.time()
        self._last_random = 0.5
        self._random_target = 0.5
        self._random_update_time = 0.0


class PatternRegistry:
    """Registry for managing patterns across devices."""
    
    def __init__(self):
        """Initialize empty pattern registry."""
        self.patterns: Dict[str, Pattern] = {}
    
    def create_pattern(self, device_id: str, config: PatternConfig) -> Pattern:
        """
        Create or update pattern for a device.
        
        Args:
            device_id: Device identifier
            config: Pattern configuration
            
        Returns:
            Pattern instance
        """
        if device_id in self.patterns:
            self.patterns[device_id].update_config(config)
        else:
            self.patterns[device_id] = Pattern(config)
        
        logging.info(f"Updated pattern for {device_id}: {config.mode}")
        return self.patterns[device_id]
    
    def get_pattern(self, device_id: str) -> Optional[Pattern]:
        """Get pattern for device."""
        return self.patterns.get(device_id)
    
    def remove_pattern(self, device_id: str) -> None:
        """Remove pattern for device."""
        if device_id in self.patterns:
            del self.patterns[device_id]
    
    def get_all_values(self, t: Optional[float] = None) -> Dict[str, float]:
        """Get current values for all patterns."""
        return {
            device_id: pattern.value(t)
            for device_id, pattern in self.patterns.items()
        }


# Global pattern registry
pattern_registry = PatternRegistry()
