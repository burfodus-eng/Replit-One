from fastapi import APIRouter, Request, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional
from app.models import ArrayStatus, ArraySettingsRequest, SystemLoad, PowerEvent


router = APIRouter()


@router.get("/arrays")
async def get_arrays(request: Request):
    stage_manager = request.app.state.stage_manager
    arrays = []
    
    for stage in stage_manager.stages:
        if hasattr(stage, 'leds'):
            array_status = ArrayStatus(
                id=stage.id,
                name=stage.name,
                description=stage.description,
                enabled=stage.enabled,
                mode=stage.mode,
                duty=stage.duty,
                leds=stage.leds,
                vin_v=0.0,
                iin_a=0.0,
                vout_v=0.0,
                iout_a=0.0,
                power_w=0.0
            )
            
            latest = request.app.state.latest
            if latest:
                for reading in latest:
                    if reading.stage_id == stage.id:
                        array_status.vin_v = reading.vin_v
                        array_status.iin_a = reading.iin_a
                        array_status.vout_v = reading.vout_v
                        array_status.iout_a = reading.iout_a
                        array_status.power_w = reading.vout_v * reading.iout_a
                        break
            
            arrays.append(array_status)
    
    return {"arrays": arrays}


@router.post("/arrays/{array_id}/settings")
async def update_array_settings(
    array_id: str,
    settings: ArraySettingsRequest,
    request: Request
):
    stage_manager = request.app.state.stage_manager
    
    stage = None
    for s in stage_manager.stages:
        if s.id == array_id:
            stage = s
            break
    
    if not stage:
        raise HTTPException(status_code=404, detail="Array not found")
    
    if not hasattr(stage, 'leds'):
        raise HTTPException(status_code=400, detail="Stage is not an array")
    
    for led_id, updates in settings.leds.items():
        led = next((l for l in stage.leds if l.id == led_id), None)
        if not led:
            continue
        
        if updates.label is not None:
            led.label = updates.label
        if updates.intensity_limit_pct is not None:
            led.intensity_limit_pct = max(0, min(100, updates.intensity_limit_pct))
        if updates.priority is not None:
            led.priority = updates.priority
        if updates.is_on is not None:
            led.is_on = updates.is_on
    
    stage.apply_control()
    
    return {"success": True, "array_id": array_id}


@router.get("/system/load")
async def get_system_load(request: Request):
    latest = request.app.state.latest
    
    pv_w = 0.0
    load_w = 0.0
    
    if latest:
        for reading in latest:
            if reading.stage_id == "PV":
                pv_w = reading.vout_v * reading.iout_a
            else:
                load_w += reading.vout_v * reading.iout_a
    
    battery_w = pv_w - load_w
    
    config = request.app.state.config
    budget_w = config.get("power_budget", {}).get("target_watts", 400)
    
    return SystemLoad(
        pv_w=pv_w,
        load_w=load_w,
        battery_w=battery_w,
        net_w=pv_w - load_w,
        budget_w=budget_w,
        timestamp=datetime.now()
    )


@router.get("/events")
async def get_events(request: Request, limit: int = Query(default=50, ge=1, le=200)):
    events_service = request.app.state.events
    events = events_service.get_recent_events(limit=limit)
    return {"events": events}
