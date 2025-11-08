from datetime import datetime, timedelta
from typing import List, Dict


class AutomationService:
    def __init__(self):
        self.completed_tasks = [
            {"name": "Morning Feeding", "time": "08:15 AM", "status": "completed"},
            {"name": "Peak Flow Cycle", "time": "10:30 AM", "status": "completed"},
            {"name": "Water Quality Check", "time": "12:00 PM", "status": "completed"},
        ]
        
        self.upcoming_tasks = [
            {"name": "Evening Feeding", "time": "06:00 PM", "eta_minutes": 45},
            {"name": "Night Mode Transition", "time": "08:30 PM", "eta_minutes": 195},
            {"name": "Coral Acclimation", "time": "09:00 PM", "eta_minutes": 225},
        ]
        
        self.wave_modes = {
            "Left Swirl": {"pattern": "circular_left", "intensity": 0.7},
            "Right Swirl": {"pattern": "circular_right", "intensity": 0.7},
            "Front-Back Surge": {"pattern": "surge_fb", "intensity": 0.8},
            "Cross Current": {"pattern": "cross", "intensity": 0.6},
            "Reef Pulse": {"pattern": "pulse", "intensity": 0.9},
        }
        
        self.current_wave_mode = "Reef Pulse"
    
    def get_completed_tasks(self) -> List[Dict]:
        return self.completed_tasks
    
    def get_upcoming_tasks(self) -> List[Dict]:
        return self.upcoming_tasks
    
    def get_wave_modes(self) -> List[str]:
        return list(self.wave_modes.keys())
    
    def get_current_wave_mode(self) -> str:
        return self.current_wave_mode
    
    def set_wave_mode(self, mode: str) -> bool:
        if mode in self.wave_modes:
            self.current_wave_mode = mode
            return True
        return False
