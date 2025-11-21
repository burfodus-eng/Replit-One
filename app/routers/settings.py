from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import glob

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


class DeviceConfigUpdate(BaseModel):
    name: Optional[str] = None
    gpio_pin: Optional[int] = Field(None, ge=0, le=40)
    pwm_freq_hz: Optional[int] = Field(None, ge=50, le=10000)
    min_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    volts_min: Optional[float] = Field(None, ge=0.0, le=10.0)
    volts_max: Optional[float] = Field(None, ge=0.0, le=10.0)
    follow_device_id: Optional[str] = None


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
    return updated.model_dump()


@router.delete('/api/settings/hardware/{device_id}')
async def delete_device(device_id: str, request: Request):
    store = request.app.state.store
    success = store.delete_device_config(device_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return {"success": True}


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
