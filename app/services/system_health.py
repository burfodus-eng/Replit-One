from typing import List, Dict
import random


class SystemHealthService:
    def __init__(self):
        self.warnings = []
        self.errors = []
        self.last_check = None
    
    def check_health(self, stages_data) -> Dict:
        """Check system health based on current stage data"""
        self.warnings = []
        self.errors = []
        
        # Check battery voltage
        for stage in stages_data:
            if stage.get("stage_id") == "Battery":
                vout = stage.get("vout_v", 0)
                if vout < 12.2:
                    self.errors.append("Battery critically low - charging required")
                elif vout < 13.0:
                    self.warnings.append("Battery voltage below optimal")
        
        # Check LED arrays
        for stage in stages_data:
            if "Array" in stage.get("stage_id", ""):
                vin = stage.get("vin_v", 0)
                if vin > 80:
                    self.warnings.append(f"{stage['stage_id']}: Panel voltage high")
                elif vin < 20:
                    self.errors.append(f"{stage['stage_id']}: Panel offline or disconnected")
        
        # Simulate occasional warnings
        if random.random() < 0.1:
            self.warnings.append("Temperature sensor reading slightly elevated")
        
        # Determine overall status
        if self.errors:
            status = "error"
            color = "#ff4444"
        elif self.warnings:
            status = "warning"
            color = "#ffaa00"
        else:
            status = "ok"
            color = "#44ff44"
        
        return {
            "status": status,
            "color": color,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": [] if (self.errors or self.warnings) else ["All systems nominal"]
        }
