from apscheduler.schedulers.asyncio import AsyncIOScheduler


class JobScheduler:
    def __init__(self, mgr, persist_cb=None, interval_s=1.0, power_allocator=None, wavemaker_manager=None, automation=None):
        self.mgr = mgr
        self.persist_cb = persist_cb
        self.interval_s = interval_s
        self.power_allocator = power_allocator
        self.wavemaker_manager = wavemaker_manager
        self.automation = automation
        self.sched = AsyncIOScheduler()


    def start(self, app):
        @self.sched.scheduled_job("interval", seconds=self.interval_s)
        def sample_job():
            snap = self.mgr.snapshot()
            
            if self.power_allocator:
                arrays_status = []
                pv_power = 0.0
                battery_power = 0.0
                
                for stage in self.mgr.stages:
                    if hasattr(stage, 'leds'):
                        arrays_status.append({
                            'id': stage.id,
                            'name': stage.name,
                            'description': stage.description,
                            'enabled': stage.enabled,
                            'mode': stage.mode,
                            'duty': stage.duty,
                            'leds': stage.leds,
                            'max_current_a': stage.max_current_a,
                            'nominal_voltage_v': stage.nominal_voltage_v,
                            'vin_v': 0.0,
                            'iin_a': 0.0,
                            'vout_v': 0.0,
                            'iout_a': 0.0,
                            'power_w': 0.0
                        })
                
                for reading in snap:
                    if reading.stage_id == 'Battery':
                        battery_power = reading.vout_v * reading.iout_a
                        battery_voltage = reading.vout_v
                    else:
                        for arr in arrays_status:
                            if reading.stage_id == arr['id']:
                                arr['vin_v'] = reading.vin_v
                                arr['iin_a'] = reading.iin_a
                                arr['vout_v'] = reading.vout_v
                                arr['iout_a'] = reading.iout_a
                                arr['power_w'] = reading.vout_v * reading.iout_a
                
                from app.models import ArrayStatus
                from datetime import datetime
                import math
                
                array_objs = [ArrayStatus(**arr) for arr in arrays_status]
                
                now = datetime.now()
                hour = now.hour + now.minute / 60.0
                if hour < 6 or hour > 20:
                    diurnal_factor = 0.0
                elif hour < 8:
                    diurnal_factor = (hour - 6) / 2.0
                elif hour < 18:
                    diurnal_factor = 1.0 - 0.2 * abs(13 - hour) / 5.0
                else:
                    diurnal_factor = 1.0 - (hour - 18) / 2.0
                
                max_pv_w = app.state.config.get('power_budget', {}).get('pv_max_w', 600)
                pv_power = max_pv_w * diurnal_factor
                
                max_discharge_w = app.state.config.get('stages', {}).get('battery', {}).get('max_discharge_w', 150)
                
                low_battery_v = app.state.config.get('alerts', {}).get('low_battery_v', 12.2)
                battery_ok = battery_voltage > low_battery_v if 'battery_voltage' in locals() else True
                battery_available = max_discharge_w if battery_ok else 0
                
                shed, restored = self.power_allocator.allocate_power(array_objs, pv_power, battery_available)
                
                for array_id, led_id in shed + restored:
                    stage = self.mgr.stage_dict.get(array_id)
                    if stage and hasattr(stage, 'leds'):
                        for led in stage.leds:
                            if led.id == led_id:
                                array_obj = next((a for a in array_objs if a.id == array_id), None)
                                if array_obj:
                                    led_obj = next((l for l in array_obj.leds if l.id == led_id), None)
                                    if led_obj:
                                        led.is_on = led_obj.is_on
                                        led.current_intensity_pct = led_obj.current_intensity_pct
                                break
            
            if self.persist_cb:
                self.persist_cb(snap)
            app.state.latest = snap
        
        if self.wavemaker_manager:
            import time
            
            @self.sched.scheduled_job("interval", seconds=0.05)
            def wavemaker_control_loop():
                """20Hz wavemaker PWM control loop"""
                self.wavemaker_manager.update_all(time.time())
            
            @self.sched.scheduled_job("interval", seconds=1.0)
            def wavemaker_telemetry_loop():
                """1Hz wavemaker telemetry sampling"""
                self.wavemaker_manager.sample_all_power()
        
        if self.automation:
            @self.sched.scheduled_job("interval", seconds=60)
            def automation_task_check():
                """1-minute interval task execution check"""
                self.automation.check_and_execute_tasks()
            
            @self.sched.scheduled_job("interval", seconds=1)
            def feed_mode_timeout_check():
                """1-second interval feed mode timeout check"""
                self.automation.check_feed_mode_timeout()
        
        self.sched.start()
