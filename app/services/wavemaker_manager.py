"""
Wavemaker Manager Service
Coordinates 6 wavemaker channels with different wave patterns
"""
import time
import math
import random
from datetime import datetime, timedelta
from collections import deque
from typing import List, Dict, Deque
from ..models import WavemakerMode, WavemakerChannel, WavemakerHistoryPoint
from ..hardware.hal import WavemakerHAL


class Channel:
    """Individual wavemaker channel with pattern generation"""
    
    def __init__(self, channel_id: int, name: str):
        self.id = channel_id
        self.name = name
        self.mode: WavemakerMode = "off"
        self.target_power_pct: int = 0
        self.current_duty: float = 0.0
        
        self.voltage_v: float = 0.0
        self.current_a: float = 0.0
        self.power_w: float = 0.0
        
        self.pattern_phase: float = 0.0
        self.pulse_on_time: float = 0.0
        self.pulse_period: float = 10.0
        self.pulse_duty_ratio: float = 0.6
        
        self.random_current: float = 0.0
        self.random_target: float = 0.0
        self.random_transition_start: float = 0.0
        self.random_transition_duration: float = 2.0
        
    def _compute_duty_from_mode(self, t_now: float) -> float:
        """
        Compute PWM duty cycle based on current mode and time
        
        Returns:
            Duty cycle from 0.0 to 1.0
        """
        if self.mode == "off":
            return 0.0
            
        if self.mode == "constant":
            return self.target_power_pct / 100.0
            
        if self.mode == "pulse":
            time_in_cycle = (t_now - self.pulse_on_time) % self.pulse_period
            on_duration = self.pulse_period * self.pulse_duty_ratio
            
            if time_in_cycle < on_duration:
                return self.target_power_pct / 100.0
            else:
                return 0.0
                
        if self.mode == "gyre_left":
            phase = (t_now / 30.0) * 2 * math.pi + self.pattern_phase
            wave = (math.sin(phase) + 1) / 2
            
            if self.id % 2 == 0:
                duty = wave * (self.target_power_pct / 100.0)
            else:
                duty = (1 - wave) * (self.target_power_pct / 100.0)
            return max(0.0, min(1.0, duty))
            
        if self.mode == "gyre_right":
            phase = (t_now / 30.0) * 2 * math.pi + self.pattern_phase
            wave = (math.sin(phase) + 1) / 2
            
            if self.id % 2 == 0:
                duty = (1 - wave) * (self.target_power_pct / 100.0)
            else:
                duty = wave * (self.target_power_pct / 100.0)
            return max(0.0, min(1.0, duty))
            
        if self.mode == "random_reef":
            elapsed = t_now - self.random_transition_start
            
            if elapsed >= self.random_transition_duration:
                self.random_current = self.random_target
                self.random_target = random.uniform(0.3, 1.0) * (self.target_power_pct / 100.0)
                self.random_transition_start = t_now
                self.random_transition_duration = random.uniform(5.0, 15.0)
                elapsed = 0.0
                
            progress = min(1.0, elapsed / self.random_transition_duration)
            smooth_progress = 0.5 * (1 - math.cos(progress * math.pi))
            
            duty = (1 - smooth_progress) * self.random_current + smooth_progress * self.random_target
            return max(0.0, min(1.0, duty))
            
        return 0.0
        
    def update_pwm(self, t_now: float, hal: WavemakerHAL):
        """Update PWM output based on current mode"""
        new_duty = self._compute_duty_from_mode(t_now)
        self.current_duty = new_duty
        hal.set_channel_pwm(self.id, new_duty)
        
    def read_power(self, hal: WavemakerHAL):
        """Read power telemetry from sensor"""
        telemetry = hal.read_channel_power(self.id)
        self.voltage_v = telemetry["voltage"]
        self.current_a = telemetry["current"]
        self.power_w = telemetry["power"]
        
    def set_mode(self, mode: WavemakerMode, target_pct: int, pulse_duty_ratio: float = None):
        """Update channel mode and target power"""
        self.mode = mode
        self.target_power_pct = max(0, min(100, target_pct))
        
        if pulse_duty_ratio is not None:
            self.pulse_duty_ratio = max(0.0, min(1.0, pulse_duty_ratio))
        
        if mode == "pulse":
            self.pulse_on_time = time.time()
            
        if mode == "random_reef":
            self.random_current = self.current_duty
            self.random_target = self.target_power_pct / 100.0
            self.random_transition_start = time.time()
            
    def to_model(self) -> WavemakerChannel:
        """Convert to API model"""
        return WavemakerChannel(
            id=self.id,
            name=self.name,
            mode=self.mode,
            target_power_pct=self.target_power_pct,
            pulse_duty_ratio=self.pulse_duty_ratio,
            current_power_w=round(self.power_w, 2),
            voltage_v=round(self.voltage_v, 2),
            current_a=round(self.current_a, 3)
        )


class WavemakerManager:
    """Manages all 6 wavemaker channels"""
    
    def __init__(self):
        self.hal = WavemakerHAL()
        
        self.channels = [
            Channel(0, "Front Left"),
            Channel(1, "Front Right"),
            Channel(2, "Mid Left"),
            Channel(3, "Mid Right"),
            Channel(4, "Back Left"),
            Channel(5, "Back Right")
        ]
        
        self.history_window_s = 900
        self.history: Dict[int, Deque[WavemakerHistoryPoint]] = {
            i: deque(maxlen=900) for i in range(6)
        }
        
        self.last_telemetry_time = 0.0
        self.preset_manager = None
        
    def set_preset_manager(self, preset_manager):
        """Inject preset manager for preset-based control"""
        self.preset_manager = preset_manager
    
    def apply_preset_power_levels(self):
        """Apply power levels from active preset to all channels"""
        if not self.preset_manager:
            return
        
        power_levels = self.preset_manager.get_current_power_levels()
        
        for wavemaker_num, power_pct in power_levels.items():
            channel_index = wavemaker_num - 1
            if 0 <= channel_index < len(self.channels):
                channel = self.channels[channel_index]
                channel.mode = "constant"
                channel.target_power_pct = int(power_pct)
    
    def update_all(self, t_now: float):
        """Update all channels (20 Hz control loop)"""
        if self.preset_manager and self.preset_manager.get_active_preset():
            self.apply_preset_power_levels()
        
        for channel in self.channels:
            channel.update_pwm(t_now, self.hal)
            
    def sample_all_power(self):
        """Sample power from all channels (1 Hz telemetry loop)"""
        current_time = time.time()
        
        if current_time - self.last_telemetry_time < 0.5:
            return
            
        self.last_telemetry_time = current_time
        
        for channel in self.channels:
            channel.read_power(self.hal)
            
            point = WavemakerHistoryPoint(
                t=datetime.now(),
                power_w=channel.power_w,
                duty_pct=round(channel.current_duty * 100, 1),
                pulse_duty_ratio=channel.pulse_duty_ratio
            )
            self.history[channel.id].append(point)
            
    def get_channel_status(self, channel_id: int) -> WavemakerChannel:
        """Get status for a specific channel"""
        if 0 <= channel_id < len(self.channels):
            return self.channels[channel_id].to_model()
        raise ValueError(f"Invalid channel ID: {channel_id}")
        
    def get_all_status(self) -> List[WavemakerChannel]:
        """Get status for all channels"""
        return [ch.to_model() for ch in self.channels]
        
    def update_channel(self, channel_id: int, mode: WavemakerMode = None, target_pct: int = None, pulse_duty_ratio: float = None):
        """Update a channel's mode and/or target power (partial updates supported)"""
        if not (0 <= channel_id < len(self.channels)):
            raise ValueError(f"Invalid channel ID: {channel_id}")
            
        channel = self.channels[channel_id]
        
        new_mode = mode if mode is not None else channel.mode
        new_target = target_pct if target_pct is not None else channel.target_power_pct
        
        channel.set_mode(new_mode, new_target, pulse_duty_ratio)
        
    def get_channel_history(self, channel_id: int, window_s: int = 900) -> List[WavemakerHistoryPoint]:
        """Get power history for a channel"""
        if channel_id not in self.history:
            return []
            
        cutoff_time = datetime.now() - timedelta(seconds=window_s)
        
        return [
            point for point in self.history[channel_id]
            if point.t >= cutoff_time
        ]
        
    def emergency_stop(self):
        """Emergency stop all channels"""
        for channel in self.channels:
            channel.set_mode("off", 0)
        self.hal.shutdown_all()
