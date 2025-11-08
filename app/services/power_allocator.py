from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from app.models import LED, ArrayStatus
from app.services.events import EventsService


class PowerAllocator:
    def __init__(self, config: dict, events: EventsService):
        self.config = config
        self.events = events
        self.target_watts = config.get("power_budget", {}).get("target_watts", 400)
        self.restore_hysteresis_pct = config.get("power_budget", {}).get("restore_hysteresis_pct", 10)
        self.restore_delay_s = config.get("power_budget", {}).get("restore_delay_s", 10)
        
        self.last_shed_time: Dict[Tuple[str, str], datetime] = {}
        self.surplus_start_time: Dict[Tuple[str, str], datetime] = {}
    
    def calculate_load(self, arrays: List[ArrayStatus]) -> float:
        total_load = 0.0
        for array in arrays:
            if array.enabled:
                total_load += array.power_w
        return total_load
    
    def get_all_leds_sorted_by_priority(self, arrays: List[ArrayStatus]) -> List[Tuple[str, LED]]:
        all_leds = []
        for array in arrays:
            if array.enabled:
                for led in array.leds:
                    all_leds.append((array.id, led))
        
        all_leds.sort(key=lambda x: x[1].priority, reverse=True)
        return all_leds
    
    def shed_leds(
        self,
        arrays: List[ArrayStatus],
        pv_w: float,
        battery_w_available: float
    ) -> List[Tuple[str, str]]:
        available_power = pv_w + battery_w_available
        current_load = self.calculate_load(arrays)
        
        if current_load <= available_power:
            return []
        
        power_to_reduce = current_load - available_power
        leds_to_shed = []
        
        all_leds = self.get_all_leds_sorted_by_priority(arrays)
        
        for array_id, led in all_leds:
            if not led.is_on:
                continue
            
            array = next(a for a in arrays if a.id == array_id)
            
            led_power = (led.current_intensity_pct / 100.0) * (array.power_w / len([l for l in array.leds if l.is_on]))
            
            led.is_on = False
            led.current_intensity_pct = 0.0
            leds_to_shed.append((array_id, led.id))
            
            self.last_shed_time[(array_id, led.id)] = datetime.now()
            self.events.add_event(
                event_type="shed",
                message=f"Shed {array.name} - {led.label}",
                array_id=array_id,
                led_id=led.id,
                details={
                    "reason": "insufficient_power",
                    "available_w": available_power,
                    "load_w": current_load,
                    "led_power_w": led_power
                }
            )
            
            power_to_reduce -= led_power
            
            if power_to_reduce <= 0:
                break
        
        return leds_to_shed
    
    def restore_leds(
        self,
        arrays: List[ArrayStatus],
        pv_w: float,
        battery_w_available: float
    ) -> List[Tuple[str, str]]:
        available_power = pv_w + battery_w_available
        current_load = self.calculate_load(arrays)
        
        surplus = available_power - current_load
        required_surplus = available_power * (self.restore_hysteresis_pct / 100.0)
        
        if surplus <= required_surplus:
            self.surplus_start_time.clear()
            return []
        
        leds_to_restore = []
        
        all_leds = self.get_all_leds_sorted_by_priority(arrays)
        all_leds.reverse()
        
        now = datetime.now()
        
        for array_id, led in all_leds:
            if led.is_on:
                continue
            
            key = (array_id, led.id)
            
            if key not in self.surplus_start_time:
                self.surplus_start_time[key] = now
                continue
            
            if (now - self.surplus_start_time[key]).total_seconds() < self.restore_delay_s:
                continue
            
            array = next(a for a in arrays if a.id == array_id)
            
            estimated_power = (led.intensity_limit_pct / 100.0) * array.duty * (array.max_current_a * array.nominal_voltage_v / len(array.leds))
            
            if estimated_power > surplus:
                continue
            
            led.is_on = True
            led.current_intensity_pct = led.intensity_limit_pct * array.duty
            leds_to_restore.append((array_id, led.id))
            
            self.events.add_event(
                event_type="restore",
                message=f"Restored {array.name} - {led.label}",
                array_id=array_id,
                led_id=led.id,
                details={
                    "available_w": available_power,
                    "load_w": current_load,
                    "surplus_w": surplus,
                    "estimated_led_power_w": estimated_power
                }
            )
            
            surplus -= estimated_power
            self.surplus_start_time.pop(key, None)
        
        return leds_to_restore
    
    def allocate_power(
        self,
        arrays: List[ArrayStatus],
        pv_w: float,
        battery_w_available: float
    ) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        shed = self.shed_leds(arrays, pv_w, battery_w_available)
        restored = self.restore_leds(arrays, pv_w, battery_w_available)
        
        return (shed, restored)
