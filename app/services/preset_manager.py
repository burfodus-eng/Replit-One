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
                self._create_random_reef_preset()
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
                {"time": 0, "power": 20},
                {"time": 20, "power": 80},
                {"time": 50, "power": 20},
                {"time": 100, "power": 20}
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
                power = int(50 + 30 * math.sin(math.radians(phase)))
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
                power = int(50 + 30 * math.sin(math.radians(phase)))
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
            points = [{"time": 0, "power": random.randint(40, 70)}]
            for pct in range(8, 108, 8):
                points.append({"time": min(pct, 100), "power": random.randint(30, 80)})
            flow_curves[f"wavemaker_{i}"] = points
        
        return WavemakerPreset(
            name="Random Reef",
            description="Chaotic natural reef flow",
            cycle_duration_sec=60,
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
