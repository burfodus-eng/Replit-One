from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class AutomationService:
    def __init__(self, store=None, preset_manager=None):
        self.store = store
        self.preset_manager = preset_manager
        self.last_executed_tasks = {}
        
        self.feed_mode_active = False
        self.feed_mode_start_time = None
        self.feed_mode_duration_minutes = 10
        self.preset_before_feed = None
        
        self.completed_tasks = [
            {"name": "Morning Feeding", "time": "08:15 AM", "status": "completed"},
            {"name": "Peak Flow Cycle", "time": "10:30 AM", "status": "completed"},
            {"name": "Water Quality Check", "time": "12:00 PM", "status": "completed"},
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
        if not self.store:
            return [
                {"name": "Evening Feeding", "time": "06:00 PM", "eta_minutes": 45},
                {"name": "Night Mode Transition", "time": "08:30 PM", "eta_minutes": 195},
            ]
        
        tasks = self.store.get_all_scheduled_tasks()
        now = datetime.now()
        upcoming = []
        
        for task in tasks:
            if not task.enabled:
                continue
            
            try:
                task_hour, task_min = task.time.split(':')
                task_dt = now.replace(hour=int(task_hour), minute=int(task_min), second=0, microsecond=0)
                
                if task_dt < now:
                    task_dt += timedelta(days=1)
                
                eta_minutes = int((task_dt - now).total_seconds() / 60)
                
                upcoming.append({
                    "id": task.id,
                    "name": task.name,
                    "time": task.time,
                    "eta_minutes": eta_minutes,
                    "type": task.task_type,
                    "preset_id": task.preset_id
                })
            except:
                continue
        
        upcoming.sort(key=lambda x: x["eta_minutes"])
        return upcoming[:5]
    
    def get_wave_modes(self) -> List[str]:
        return list(self.wave_modes.keys())
    
    def get_current_wave_mode(self) -> str:
        return self.current_wave_mode
    
    def set_wave_mode(self, mode: str) -> bool:
        if mode in self.wave_modes:
            self.current_wave_mode = mode
            return True
        return False
    
    def start_feed_mode(self) -> Dict:
        if not self.preset_manager or not self.store:
            return {"success": False, "message": "Preset manager not available"}
        
        if self.feed_mode_active:
            return {"success": False, "message": "Feed mode already active"}
        
        feed_preset = self.store.get_preset_by_name("Feed Mode")
        if not feed_preset:
            return {"success": False, "message": "Feed Mode preset not found"}
        
        current_preset = self.preset_manager.get_active_preset()
        self.preset_before_feed = current_preset.id if current_preset else None
        
        self.preset_manager.set_active_preset(feed_preset.id)
        self.feed_mode_active = True
        self.feed_mode_start_time = datetime.now()
        
        print(f"[Feed Mode] Started - previous preset: {self.preset_before_feed}")
        return {"success": True, "message": "Feed mode activated"}
    
    def get_feed_mode_status(self) -> Dict:
        if not self.feed_mode_active:
            return {
                "active": False,
                "remaining_seconds": 0,
                "duration_minutes": self.feed_mode_duration_minutes
            }
        
        elapsed = (datetime.now() - self.feed_mode_start_time).total_seconds()
        total_seconds = self.feed_mode_duration_minutes * 60
        remaining = max(0, total_seconds - elapsed)
        
        return {
            "active": True,
            "remaining_seconds": int(remaining),
            "duration_minutes": self.feed_mode_duration_minutes,
            "start_time": self.feed_mode_start_time.isoformat()
        }
    
    def stop_feed_mode(self, restore_preset: bool = True) -> Dict:
        if not self.feed_mode_active:
            return {"success": False, "message": "Feed mode not active"}
        
        self.feed_mode_active = False
        
        if restore_preset and self.preset_before_feed:
            try:
                self.preset_manager.set_active_preset(self.preset_before_feed)
                print(f"[Feed Mode] Stopped - restored preset {self.preset_before_feed}")
            except Exception as e:
                print(f"[Feed Mode] Failed to restore preset: {e}")
        
        self.feed_mode_start_time = None
        self.preset_before_feed = None
        
        return {"success": True, "message": "Feed mode stopped"}
    
    def check_feed_mode_timeout(self):
        if not self.feed_mode_active or not self.feed_mode_start_time:
            return
        
        elapsed = (datetime.now() - self.feed_mode_start_time).total_seconds()
        duration_seconds = self.feed_mode_duration_minutes * 60
        
        if elapsed >= duration_seconds:
            print(f"[Feed Mode] Timeout reached, auto-stopping")
            self.stop_feed_mode(restore_preset=True)
    
    def check_and_execute_tasks(self):
        if not self.store or not self.preset_manager:
            return
        
        if self.feed_mode_active:
            return
        
        tasks = self.store.get_all_scheduled_tasks()
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = now.weekday()
        
        for task in tasks:
            if not task.enabled:
                continue
            
            if task.days_of_week:
                try:
                    days = json.loads(task.days_of_week) if isinstance(task.days_of_week, str) else task.days_of_week
                    if today not in days:
                        continue
                except:
                    pass
            
            task_key = f"{task.id}_{task.time}"
            last_exec = self.last_executed_tasks.get(task_key)
            
            if last_exec and (now - last_exec).total_seconds() < 60:
                continue
            
            if task.time == current_time:
                self._execute_task(task)
                self.last_executed_tasks[task_key] = now
    
    def _execute_task(self, task):
        if task.task_type == "preset_activation" and task.preset_id:
            try:
                self.preset_manager.set_active_preset(task.preset_id)
                print(f"[Automation] Activated preset {task.preset_id} for task '{task.name}'")
            except Exception as e:
                print(f"[Automation] Failed to execute task {task.name}: {e}")
