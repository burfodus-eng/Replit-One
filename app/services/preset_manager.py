import time
import math
from typing import Optional, Dict, List
from .storage import WavemakerPreset, Store


class PresetManager:
    def __init__(self, store: Store):
        self.store = store
        self.active_preset_id: Optional[int] = None
        self.cycle_start_time: float = time.time()
        self._initialize_built_in_presets()
    
    def _initialize_built_in_presets(self):
        existing = self.store.get_all_presets()
        if not existing:
            built_in_presets = [
                self._create_gentle_preset(),
                self._create_pulse_preset(),
                self._create_gyre_cw_preset(),
                self._create_gyre_ccw_preset(),
                self._create_feed_mode_preset(),
                self._create_random_reef_preset(),
                self._create_sequential_walk_preset(),
                self._create_knight_rider_preset(),
                self._create_paired_police_preset()
            ]
            
            for preset in built_in_presets:
                self.store.create_preset(preset)
    
    def _create_gentle_preset(self) -> WavemakerPreset:
        flow_curves = {}
        for i in range(1, 13):
            flow_curves[f"wavemaker_{i}"] = [
                {"time": 0, "power": 30},
                {"time": 100, "power": 30}
            ]
        
        return WavemakerPreset(
            name="Gentle Flow",
            description="Calm, steady flow for sensitive corals",
            cycle_duration_sec=60,
            is_built_in=True,
            flow_curves=flow_curves
        )
    
    def _create_pulse_preset(self) -> WavemakerPreset:
        flow_curves = {}
        for i in range(1, 13):
            flow_curves[f"wavemaker_{i}"] = [
                {"time": 0, "power": 0},
                {"time": 20, "power": 100},
                {"time": 50, "power": 0},
                {"time": 100, "power": 0}
            ]
        
        return WavemakerPreset(
            name="Pulse",
            description="Short bursts of strong flow",
            cycle_duration_sec=10,
            is_built_in=True,
            flow_curves=flow_curves
        )
    
    def _create_gyre_cw_preset(self) -> WavemakerPreset:
        flow_curves = {}
        phase_offsets = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
        
        for i, offset in enumerate(phase_offsets, 1):
            points = []
            for t in range(0, 361, 30):
                phase = (t + offset) % 360
                power = int(50 + 50 * math.sin(math.radians(phase)))
                time_pct = (t / 360) * 100
                points.append({"time": round(time_pct, 1), "power": power})
            flow_curves[f"wavemaker_{i}"] = points
        
        return WavemakerPreset(
            name="Gyre Clockwise",
            description="Rotating flow pattern, clockwise",
            cycle_duration_sec=60,
            is_built_in=True,
            flow_curves=flow_curves
        )
    
    def _create_gyre_ccw_preset(self) -> WavemakerPreset:
        flow_curves = {}
        phase_offsets = [0, 330, 300, 270, 240, 210, 180, 150, 120, 90, 60, 30]
        
        for i, offset in enumerate(phase_offsets, 1):
            points = []
            for t in range(0, 361, 30):
                phase = (t + offset) % 360
                power = int(50 + 50 * math.sin(math.radians(phase)))
                time_pct = (t / 360) * 100
                points.append({"time": round(time_pct, 1), "power": power})
            flow_curves[f"wavemaker_{i}"] = points
        
        return WavemakerPreset(
            name="Gyre Counter-Clockwise",
            description="Rotating flow pattern, counter-clockwise",
            cycle_duration_sec=60,
            is_built_in=True,
            flow_curves=flow_curves
        )
    
    def _create_feed_mode_preset(self) -> WavemakerPreset:
        flow_curves = {}
        for i in range(1, 13):
            flow_curves[f"wavemaker_{i}"] = [
                {"time": 0, "power": 5},
                {"time": 100, "power": 5}
            ]
        
        return WavemakerPreset(
            name="Feed Mode",
            description="Minimal flow for feeding time",
            cycle_duration_sec=600,
            is_built_in=True,
            flow_curves=flow_curves
        )
    
    def _create_random_reef_preset(self) -> WavemakerPreset:
        import random
        random.seed(42)
        
        flow_curves = {}
        for i in range(1, 13):
            points = [{"time": 0, "power": random.randint(0, 100)}]
            for pct in range(8, 108, 8):
                points.append({"time": min(pct, 100), "power": random.randint(0, 100)})
            flow_curves[f"wavemaker_{i}"] = points
        
        return WavemakerPreset(
            name="Random Reef",
            description="Chaotic natural reef flow",
            cycle_duration_sec=60,
            is_built_in=True,
            flow_curves=flow_curves
        )
    
    def _create_sequential_walk_preset(self) -> WavemakerPreset:
        """Single channel walks 1-12 repeatedly"""
        flow_curves = {}
        segment_size = 100 / 12  # Each channel gets 1/12 of the cycle
        
        for i in range(1, 13):
            points = []
            
            # Determine which segment this channel is active (0-indexed)
            active_segment = i - 1  # Channel 1 is active in segment 0, etc.
            
            for seg in range(12):
                start_time = round(seg * segment_size, 1)
                end_time = round((seg + 1) * segment_size, 1)
                
                if seg == active_segment:
                    # This is the active segment - create plateau at 100%
                    # First, add a keyframe at start_time with power 0 to prevent ramp-up
                    if start_time > 0:
                        points.append({"time": start_time, "power": 0})
                    points.append({"time": start_time, "power": 100})
                    points.append({"time": end_time, "power": 100})
                    # Immediate drop to 0% at end of segment (even if end_time == 100)
                    points.append({"time": end_time, "power": 0})
                elif seg == 0:
                    # Start of cycle - set initial power
                    if active_segment == 0:
                        # Channel 1 starts at 100% immediately
                        pass
                    else:
                        points.append({"time": start_time, "power": 0})
            
            # Ensure we end at 100% with power 0
            if not any(p["time"] == 100 and p["power"] == 0 for p in points):
                points.append({"time": 100, "power": 0})
            
            flow_curves[f"wavemaker_{i}"] = points
        
        return WavemakerPreset(
            name="Sequential Walk",
            description="Single channel walks 1-12 repeatedly",
            cycle_duration_sec=12,
            is_built_in=True,
            flow_curves=flow_curves
        )
    
    def _create_knight_rider_preset(self) -> WavemakerPreset:
        """Bouncing pattern 1-12-1 like Knight Rider scanner"""
        flow_curves = {}
        
        # Pattern: 1,2,3,4,5,6,7,8,9,10,11,12,11,10,9,8,7,6,5,4,3,2 (22 steps)
        sequence = list(range(1, 13)) + list(range(11, 1, -1))
        num_steps = len(sequence)
        segment_size = 100 / num_steps
        
        for i in range(1, 13):
            points = []
            for step_idx, active_channel in enumerate(sequence):
                time_pct = step_idx * segment_size
                power = 100 if active_channel == i else 0
                points.append({"time": round(time_pct, 1), "power": power})
            
            # Add final point at 100%
            points.append({"time": 100, "power": 100 if sequence[0] == i else 0})
            flow_curves[f"wavemaker_{i}"] = points
        
        return WavemakerPreset(
            name="Knight Rider",
            description="Bouncing scanner pattern 1-12-1",
            cycle_duration_sec=22,
            is_built_in=True,
            flow_curves=flow_curves
        )
    
    def _create_paired_police_preset(self) -> WavemakerPreset:
        """Each pair oscillates like police lights: 1-2, 3-4, 5-6, etc."""
        flow_curves = {}
        
        for i in range(1, 13):
            # Determine which pair this channel belongs to
            pair_num = (i - 1) // 2  # 0-based pair index
            is_odd = (i % 2) == 1  # True if channel 1, 3, 5, 7, 9, 11
            
            # Create oscillating pattern
            points = [
                {"time": 0, "power": 100 if is_odd else 0},
                {"time": 50, "power": 0 if is_odd else 100},
                {"time": 100, "power": 100 if is_odd else 0}
            ]
            
            flow_curves[f"wavemaker_{i}"] = points
        
        return WavemakerPreset(
            name="Paired Police",
            description="Each pair oscillates independently (1-2, 3-4, 5-6...)",
            cycle_duration_sec=2,
            is_built_in=True,
            flow_curves=flow_curves
        )
    
    def set_active_preset(self, preset_id: int) -> bool:
        preset = self.store.get_preset(preset_id)
        if not preset:
            return False
        
        self.active_preset_id = preset_id
        self.cycle_start_time = time.time()
        return True
    
    def get_active_preset(self) -> Optional[WavemakerPreset]:
        if self.active_preset_id is None:
            return None
        return self.store.get_preset(self.active_preset_id)
    
    def get_current_power_levels(self) -> Dict[int, float]:
        if self.active_preset_id is None:
            return {i: 0.0 for i in range(1, 13)}
        
        preset = self.store.get_preset(self.active_preset_id)
        if not preset:
            return {i: 0.0 for i in range(1, 13)}
        
        elapsed = time.time() - self.cycle_start_time
        position_in_cycle_sec = elapsed % preset.cycle_duration_sec
        position_in_cycle_pct = (position_in_cycle_sec / preset.cycle_duration_sec) * 100
        
        power_levels = {}
        for i in range(1, 13):
            wm_key = f"wavemaker_{i}"
            if wm_key in preset.flow_curves:
                power_levels[i] = self._interpolate_power(
                    preset.flow_curves[wm_key],
                    position_in_cycle_pct
                )
            else:
                power_levels[i] = 0.0
        
        return power_levels
    
    def _interpolate_power(self, curve: List[Dict], time_pos: float) -> float:
        if not curve:
            return 0.0
        
        curve_sorted = sorted(curve, key=lambda x: x["time"])
        
        if time_pos <= curve_sorted[0]["time"]:
            return float(curve_sorted[0]["power"])
        
        if time_pos >= curve_sorted[-1]["time"]:
            return float(curve_sorted[-1]["power"])
        
        for i in range(len(curve_sorted) - 1):
            p1 = curve_sorted[i]
            p2 = curve_sorted[i + 1]
            
            if p1["time"] <= time_pos <= p2["time"]:
                t_range = p2["time"] - p1["time"]
                if t_range == 0:
                    return float(p1["power"])
                
                t_ratio = (time_pos - p1["time"]) / t_range
                power = p1["power"] + t_ratio * (p2["power"] - p1["power"])
                return float(power)
        
        return float(curve_sorted[-1]["power"])
