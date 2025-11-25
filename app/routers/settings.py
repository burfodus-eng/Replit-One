from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import glob
import logging
import asyncio

router = APIRouter()


class DeviceConfigCreate(BaseModel):
    device_id: str
    name: str
    device_type: str
    gpio_pin: int = Field(ge=0, le=40)
    pwm_freq_hz: int = Field(ge=50, le=10000)
    min_intensity: float = Field(ge=0.0, le=1.0, default=0.0)
    max_intensity: float = Field(ge=0.0, le=1.0, default=1.0)
    volts_min: float = Field(ge=0.0, le=10.0, default=0.0)
    volts_max: float = Field(ge=0.0, le=10.0, default=5.0)
    follow_device_id: Optional[str] = None
    gpio_pin_monitor: Optional[int] = Field(None, ge=0, le=40)
    channel_name: Optional[str] = None


class DeviceConfigUpdate(BaseModel):
    name: Optional[str] = None
    gpio_pin: Optional[int] = Field(None, ge=0, le=40)
    pwm_freq_hz: Optional[int] = Field(None, ge=50, le=10000)
    min_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    volts_min: Optional[float] = Field(None, ge=0.0, le=10.0)
    volts_max: Optional[float] = Field(None, ge=0.0, le=10.0)
    follow_device_id: Optional[str] = None
    gpio_pin_monitor: Optional[int] = Field(None, ge=0, le=40)
    channel_name: Optional[str] = None


@router.get('/api/settings/hardware')
async def get_all_devices(request: Request):
    store = request.app.state.store
    devices = store.get_all_device_configs()
    return [device.model_dump() for device in devices]


@router.get('/api/settings/hardware/{device_id}')
async def get_device(device_id: str, request: Request):
    store = request.app.state.store
    device = store.get_device_config(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device.model_dump()


@router.post('/api/settings/hardware')
async def create_device(device: DeviceConfigCreate, request: Request):
    from app.services.storage import DeviceConfigRow
    from app.services.hw_devices import registry, DeviceConfig
    
    store = request.app.state.store
    
    existing = store.get_device_config(device.device_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Device {device.device_id} already exists")
    
    all_devices = store.get_all_device_configs()
    for existing_device in all_devices:
        if existing_device.gpio_pin == device.gpio_pin:
            raise HTTPException(
                status_code=409, 
                detail=f"GPIO pin {device.gpio_pin} already in use by {existing_device.device_id}"
            )
    
    new_device = DeviceConfigRow(**device.model_dump())
    created = store.create_device_config(new_device)
    
    # Immediately register device in hardware registry
    config = DeviceConfig(
        name=created.name,
        gpio_pin=created.gpio_pin,
        pwm_freq_hz=created.pwm_freq_hz,
        min_intensity=created.min_intensity,
        max_intensity=created.max_intensity,
        volts_min=created.volts_min,
        volts_max=created.volts_max,
        gpio_pin_monitor=created.gpio_pin_monitor,
        channel_name=created.channel_name
    )
    
    if created.device_type == 'WAVEMAKER':
        registry.register_wavemaker(created.device_id, config)
    else:
        registry.register_led(created.device_id, config)
    
    logging.info(f"[Settings] Created and registered new device: {created.device_id}")
    
    return created.model_dump()


@router.put('/api/settings/hardware/{device_id}')
async def update_device(device_id: str, updates: DeviceConfigUpdate, request: Request):
    store = request.app.state.store
    
    device = store.get_device_config(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    update_data = {}
    for field, value in updates.model_dump(exclude_unset=True).items():
        update_data[field] = value
    
    if 'gpio_pin' in update_data:
        all_devices = store.get_all_device_configs()
        for existing_device in all_devices:
            if existing_device.device_id != device_id and existing_device.gpio_pin == update_data['gpio_pin']:
                raise HTTPException(
                    status_code=409, 
                    detail=f"GPIO pin {update_data['gpio_pin']} already in use by {existing_device.device_id}"
                )
    
    updated = store.update_device_config(device_id, **update_data)
    
    # Hot-reload device config for ANY parameter changes (not just GPIO/freq)
    from app.services.hw_devices import registry, DeviceConfig
    
    # Check if GPIO pin changed (requires full hardware re-init)
    gpio_changed = 'gpio_pin' in update_data
    
    # Build new config from updated device
    config = DeviceConfig(
        name=updated.name,
        gpio_pin=updated.gpio_pin,
        pwm_freq_hz=updated.pwm_freq_hz,
        min_intensity=updated.min_intensity,
        max_intensity=updated.max_intensity,
        volts_min=updated.volts_min,
        volts_max=updated.volts_max,
        gpio_pin_monitor=updated.gpio_pin_monitor,
        channel_name=updated.channel_name
    )
    
    if gpio_changed:
        # Full reload when GPIO pin changes (need to clean up old pin)
        registry.reload_device(device_id, config, updated.device_type)
        logging.info(f"[Settings] Hot-reloaded {device_id} with new GPIO pin {updated.gpio_pin}")
    else:
        # Just update the config in-place for other parameters
        registry.update_device_config(device_id, config, updated.device_type)
        logging.info(f"[Settings] Updated {device_id} config (intensity: {updated.min_intensity:.2f}-{updated.max_intensity:.2f})")
    
    return updated.model_dump()


@router.delete('/api/settings/hardware/{device_id}')
async def delete_device(device_id: str, request: Request):
    from app.services.hw_devices import registry
    
    store = request.app.state.store
    
    # First, unregister from hardware registry (stops output and cleans up)
    registry.unregister_device(device_id)
    
    # Then delete from database
    success = store.delete_device_config(device_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    logging.info(f"[Settings] Deleted device {device_id} from registry and database")
    return {"success": True}


class TestDeviceRequest(BaseModel):
    gpio_pin: int = Field(ge=0, le=40)
    duty_cycle: float = Field(ge=0.0, le=1.0, default=0.5)


@router.post('/api/settings/hardware/test')
async def test_device(test_req: TestDeviceRequest, request: Request):
    """Test a GPIO device by setting it to specified duty cycle for 3 seconds"""
    try:
        from app.services.hw_devices import registry, DeviceConfig, PWMDevice
        
        store = request.app.state.store
        
        # Check if this GPIO is already assigned to a device
        all_devices = store.get_all_device_configs()
        existing_device_id = None
        for dev in all_devices:
            if dev.gpio_pin == test_req.gpio_pin:
                existing_device_id = dev.device_id
                break
        
        if existing_device_id:
            # Use existing device for test
            device = registry.get_led(existing_device_id) or registry.get_wavemaker(existing_device_id)
            if device:
                logging.info(f"[Test] Testing existing device {existing_device_id} at {test_req.duty_cycle:.1%} for 3 seconds")
                
                # Save current state (as intensity, not raw duty)
                original_duty = device.current_duty
                
                # Apply test intensity using PWMDevice.apply() for proper scaling
                device.apply(test_req.duty_cycle)
                
                # Wait 3 seconds
                await asyncio.sleep(3)
                
                # Restore original state using apply()
                if original_duty > 0.0:
                    # Calculate intensity from duty within device's range
                    intensity = (original_duty - device.config.min_intensity) / (device.config.max_intensity - device.config.min_intensity) if (device.config.max_intensity - device.config.min_intensity) > 0 else 0
                    device.apply(intensity)
                else:
                    device.stop()
                
                logging.info(f"[Test] Device {existing_device_id} test complete")
                return {"success": True, "message": f"{existing_device_id} tested successfully"}
        
        # No existing device - create temporary test device
        config = DeviceConfig(
            name=f"Test GPIO {test_req.gpio_pin}",
            gpio_pin=test_req.gpio_pin,
            pwm_freq_hz=800,
            min_intensity=0.0,
            max_intensity=1.0,
            volts_min=0.0,
            volts_max=5.0
        )
        
        test_device = PWMDevice(config)
        
        logging.info(f"[Test] Testing GPIO{test_req.gpio_pin} at {test_req.duty_cycle:.1%} for 3 seconds")
        
        # Use apply() for proper driver scaling
        test_device.apply(test_req.duty_cycle)
        
        # Wait 3 seconds
        await asyncio.sleep(3)
        
        # Clean up
        test_device.cleanup()
        
        logging.info(f"[Test] GPIO{test_req.gpio_pin} test complete")
        
        return {"success": True, "message": f"GPIO{test_req.gpio_pin} tested successfully"}
    
    except Exception as e:
        logging.error(f"[Test] Failed to test GPIO{test_req.gpio_pin}: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.get('/api/logs')
async def get_logs(level: str = 'all'):
    log_files = glob.glob('/tmp/logs/reef-controller_*.log')
    if not log_files:
        return {"logs": "No log files found"}
    
    latest_log_file = max(log_files, key=os.path.getmtime)
    
    try:
        with open(latest_log_file, 'r') as f:
            logs = f.read()
        
        if level != 'all':
            lines = logs.split('\n')
            filtered_lines = [line for line in lines if level in line]
            logs = '\n'.join(filtered_lines)
        
        return {"logs": logs[-50000:]}
    except Exception as e:
        return {"logs": f"Error reading logs: {str(e)}"}


class ConfigImportData(BaseModel):
    devices: Optional[List[dict]] = None
    presets: Optional[List[dict]] = None
    scheduled_tasks: Optional[List[dict]] = None
    version: str = "1.0"


@router.get('/api/settings/export')
async def export_config(request: Request):
    """Export full system configuration as JSON for backup"""
    from datetime import datetime
    
    store = request.app.state.store
    
    devices = store.get_all_device_configs()
    presets = store.get_all_presets()
    scheduled_tasks = store.get_all_scheduled_tasks()
    
    export_data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "devices": [d.model_dump() for d in devices],
        "presets": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "cycle_duration_sec": p.cycle_duration_sec,
                "is_built_in": p.is_built_in,
                "flow_curves": p.flow_curves
            }
            for p in presets
        ],
        "scheduled_tasks": [t.model_dump() for t in scheduled_tasks]
    }
    
    logging.info(f"[Export] Exported config: {len(devices)} devices, {len(presets)} presets, {len(scheduled_tasks)} tasks")
    
    return export_data


@router.post('/api/settings/import')
async def import_config(config_data: ConfigImportData, request: Request):
    """Import system configuration from JSON backup"""
    from app.services.storage import DeviceConfigRow, WavemakerPreset, ScheduledTaskRow
    from app.services.hw_devices import registry, DeviceConfig
    from app.hw_scheduler.realtime_loop import set_led_follow
    
    store = request.app.state.store
    
    results = {
        "devices_imported": 0,
        "devices_skipped": 0,
        "presets_imported": 0,
        "presets_skipped": 0,
        "tasks_imported": 0,
        "tasks_skipped": 0,
        "errors": []
    }
    
    if config_data.devices:
        for device_data in config_data.devices:
            try:
                device_id = device_data.get('device_id')
                if not device_id:
                    results["errors"].append("Device missing required 'device_id' field")
                    continue
                    
                existing = store.get_device_config(device_id)
                
                if existing:
                    for key, value in device_data.items():
                        if key != 'device_id' and hasattr(existing, key):
                            setattr(existing, key, value)
                    updated = store.update_device_config(device_id, **device_data)
                    
                    # Hot-reload device config (same logic as PUT endpoint)
                    config = DeviceConfig(
                        name=updated.name,
                        gpio_pin=updated.gpio_pin,
                        pwm_freq_hz=updated.pwm_freq_hz,
                        min_intensity=updated.min_intensity,
                        max_intensity=updated.max_intensity,
                        volts_min=updated.volts_min,
                        volts_max=updated.volts_max,
                        gpio_pin_monitor=updated.gpio_pin_monitor,
                        channel_name=updated.channel_name
                    )
                    registry.reload_device(device_id, config, updated.device_type)
                    logging.info(f"[Import] Hot-reloaded existing device {device_id} with GPIO {updated.gpio_pin}")
                    
                    results["devices_skipped"] += 1
                else:
                    new_device = DeviceConfigRow(**device_data)
                    created = store.create_device_config(new_device)
                    
                    config = DeviceConfig(
                        name=created.name,
                        gpio_pin=created.gpio_pin,
                        pwm_freq_hz=created.pwm_freq_hz,
                        min_intensity=created.min_intensity,
                        max_intensity=created.max_intensity,
                        volts_min=created.volts_min,
                        volts_max=created.volts_max,
                        gpio_pin_monitor=created.gpio_pin_monitor,
                        channel_name=created.channel_name
                    )
                    
                    if created.device_type == 'WAVEMAKER':
                        registry.register_wavemaker(created.device_id, config)
                    else:
                        registry.register_led(created.device_id, config)
                    
                    logging.info(f"[Import] Registered new device {created.device_id} with GPIO {created.gpio_pin}")
                    
                    results["devices_imported"] += 1
                    
            except Exception as e:
                results["errors"].append(f"Device {device_data.get('device_id', 'unknown')}: {str(e)}")
    
    if config_data.presets:
        for preset_data in config_data.presets:
            try:
                if preset_data.get('is_built_in'):
                    results["presets_skipped"] += 1
                    continue
                
                preset_name = preset_data.get('name')
                if not preset_name:
                    results["errors"].append("Preset missing required 'name' field")
                    continue
                    
                preset = WavemakerPreset(
                    name=preset_name,
                    description=preset_data.get('description') or '',
                    cycle_duration_sec=preset_data.get('cycle_duration_sec') or 60,
                    is_built_in=False,
                    flow_curves=preset_data.get('flow_curves') or {}
                )
                store.create_preset(preset)
                results["presets_imported"] += 1
                
            except Exception as e:
                results["errors"].append(f"Preset {preset_data.get('name', 'unknown')}: {str(e)}")
    
    if config_data.scheduled_tasks:
        for task_data in config_data.scheduled_tasks:
            try:
                task_name = task_data.get('name')
                task_type = task_data.get('task_type')
                task_time = task_data.get('time')
                
                if not task_name or not task_type or not task_time:
                    results["errors"].append(f"Task missing required fields (name, task_type, time)")
                    continue
                
                task = ScheduledTaskRow(
                    name=task_name,
                    task_type=task_type,
                    time=task_time,
                    enabled=task_data.get('enabled', True),
                    preset_id=task_data.get('preset_id'),
                    days_of_week=task_data.get('days_of_week')
                )
                store.create_scheduled_task(task)
                results["tasks_imported"] += 1
                
            except Exception as e:
                results["errors"].append(f"Task {task_data.get('name', 'unknown')}: {str(e)}")
    
    for device in store.get_all_device_configs():
        if device.device_type == "LED" and device.follow_device_id:
            set_led_follow(device.device_id, device.follow_device_id)
    
    logging.info(f"[Import] Imported: {results['devices_imported']} devices, {results['presets_imported']} presets, {results['tasks_imported']} tasks")
    
    return results
