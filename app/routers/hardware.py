"""API endpoints for hardware device control."""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Literal, Optional

from app.services.hw_devices import registry as device_registry, DeviceConfig
from app.services.hw_patterns import pattern_registry, PatternConfig, PatternMode
from app.hw_scheduler.realtime_loop import (
    set_manual_mode,
    set_led_follow,
    get_control_state,
    manual_devices,
)


router = APIRouter()


# Request models
class DeviceSettingsUpdate(BaseModel):
    """Update device hardware settings."""
    gpio_pin: Optional[int] = Field(None, ge=0, le=27, description="BCM GPIO pin number")
    pwm_freq_hz: Optional[int] = Field(None, ge=50, le=10000, description="PWM frequency in Hz")
    min_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    volts_min: Optional[float] = Field(None, ge=0.0, le=10.0)
    volts_max: Optional[float] = Field(None, ge=0.0, le=10.0)


class PatternUpdate(BaseModel):
    """Update device pattern."""
    mode: PatternMode
    period_s: Optional[float] = Field(5.0, ge=0.1, le=60.0)
    on_ratio: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    phase_deg: Optional[float] = Field(0.0, ge=0.0, le=360.0)
    min_intensity: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    max_intensity: Optional[float] = Field(1.0, ge=0.0, le=1.0)


class ManualControl(BaseModel):
    """Manual control request."""
    duty: float = Field(..., ge=0.0, le=1.0, description="Manual duty cycle")


class ModeSwitch(BaseModel):
    """Mode switch request."""
    manual: bool = Field(..., description="True for manual mode, False for automatic")


class LEDFollowConfig(BaseModel):
    """LED follow configuration."""
    wavemaker_id: Optional[str] = Field(None, description="Wavemaker ID to follow, null to disable")


# Endpoints

@router.get("/hardware/status")
async def get_hardware_status():
    """Get overall hardware and control status."""
    return {
        "devices": device_registry.get_all_states(),
        "control": get_control_state(),
    }


@router.post("/hardware/emergency_stop")
async def emergency_stop():
    """Emergency stop - zero all device outputs."""
    device_registry.stop_all()
    return {"status": "all devices stopped"}


@router.get("/hardware/wavemakers/{device_id}")
async def get_wavemaker_status(device_id: str):
    """Get status of specific wavemaker."""
    device = device_registry.get_wavemaker(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Wavemaker {device_id} not found")
    
    pattern = pattern_registry.get_pattern(device_id)
    is_manual = device_id in manual_devices
    
    return {
        "device": device.to_dict(),
        "pattern": {
            "mode": pattern.config.mode if pattern else "OFF",
            "config": vars(pattern.config) if pattern else None,
        } if pattern else None,
        "manual_mode": is_manual,
    }


@router.post("/hardware/wavemakers/{device_id}/settings")
async def update_wavemaker_settings(device_id: str, settings: DeviceSettingsUpdate):
    """Update wavemaker hardware settings (GPIO pin, PWM freq, voltage range)."""
    device = device_registry.get_wavemaker(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Wavemaker {device_id} not found")
    
    # Apply updates
    if settings.pwm_freq_hz is not None:
        device.set_frequency(settings.pwm_freq_hz)
    
    if settings.min_intensity is not None and settings.max_intensity is not None:
        if settings.min_intensity >= settings.max_intensity:
            raise HTTPException(status_code=400, detail="min_intensity must be < max_intensity")
        device.set_range(settings.min_intensity, settings.max_intensity)
    
    if settings.volts_min is not None:
        device.config.volts_min = settings.volts_min
    
    if settings.volts_max is not None:
        device.config.volts_max = settings.volts_max
    
    # Note: GPIO pin change requires device restart (not supported dynamically)
    if settings.gpio_pin is not None:
        logging.warning(f"GPIO pin change requested for {device_id} but requires restart")
        return {
            "status": "partial_update",
            "message": "GPIO pin change requires device restart",
            "device": device.to_dict()
        }
    
    return {"status": "updated", "device": device.to_dict()}


@router.post("/hardware/wavemakers/{device_id}/pattern")
async def update_wavemaker_pattern(device_id: str, pattern_update: PatternUpdate):
    """Update wavemaker pattern configuration."""
    device = device_registry.get_wavemaker(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Wavemaker {device_id} not found")
    
    # Create pattern config
    pattern_config = PatternConfig(
        mode=pattern_update.mode,
        period_s=pattern_update.period_s if pattern_update.period_s is not None else 5.0,
        on_ratio=pattern_update.on_ratio if pattern_update.on_ratio is not None else 0.5,
        phase_deg=pattern_update.phase_deg if pattern_update.phase_deg is not None else 0.0,
        min_intensity=pattern_update.min_intensity if pattern_update.min_intensity is not None else 0.0,
        max_intensity=pattern_update.max_intensity if pattern_update.max_intensity is not None else 1.0,
    )
    
    # Update pattern
    pattern_registry.create_pattern(device_id, pattern_config)
    
    return {
        "status": "pattern_updated",
        "device_id": device_id,
        "pattern": vars(pattern_config),
    }


@router.post("/hardware/wavemakers/{device_id}/mode")
async def set_wavemaker_mode(device_id: str, mode: ModeSwitch):
    """Switch between manual and automatic (pattern) mode."""
    device = device_registry.get_wavemaker(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Wavemaker {device_id} not found")
    
    set_manual_mode(device_id, mode.manual)
    
    return {
        "status": "mode_updated",
        "device_id": device_id,
        "manual_mode": mode.manual,
    }


@router.post("/hardware/wavemakers/{device_id}/manual")
async def set_wavemaker_manual_duty(device_id: str, control: ManualControl):
    """Set manual duty cycle (only works in manual mode)."""
    device = device_registry.get_wavemaker(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Wavemaker {device_id} not found")
    
    if device_id not in manual_devices:
        raise HTTPException(
            status_code=400,
            detail=f"Device {device_id} not in manual mode. Switch to manual mode first."
        )
    
    device.apply(control.duty)
    
    return {
        "status": "duty_set",
        "device_id": device_id,
        "duty": control.duty,
        "voltage": device.get_voltage(),
    }


# LED endpoints

@router.get("/hardware/leds/{device_id}")
async def get_led_status(device_id: str):
    """Get status of specific LED."""
    device = device_registry.get_led(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"LED {device_id} not found")
    
    is_manual = device_id in manual_devices
    
    from app.hw_scheduler.realtime_loop import led_follow_map
    following = led_follow_map.get(device_id)
    
    return {
        "device": device.to_dict(),
        "manual_mode": is_manual,
        "following": following,
    }


@router.post("/hardware/leds/{device_id}/follow")
async def set_led_follow_mode(device_id: str, config: LEDFollowConfig):
    """Configure LED to follow a wavemaker's pattern."""
    device = device_registry.get_led(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"LED {device_id} not found")
    
    # Verify wavemaker exists if specified
    if config.wavemaker_id:
        wm_device = device_registry.get_wavemaker(config.wavemaker_id)
        if not wm_device:
            raise HTTPException(
                status_code=404,
                detail=f"Wavemaker {config.wavemaker_id} not found"
            )
    
    set_led_follow(device_id, config.wavemaker_id)
    
    # If following, take LED out of manual mode
    if config.wavemaker_id:
        set_manual_mode(device_id, False)
    
    return {
        "status": "follow_configured",
        "led_id": device_id,
        "following": config.wavemaker_id,
    }


@router.post("/hardware/leds/{device_id}/mode")
async def set_led_mode(device_id: str, mode: ModeSwitch):
    """Switch LED between manual and automatic mode."""
    device = device_registry.get_led(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"LED {device_id} not found")
    
    set_manual_mode(device_id, mode.manual)
    
    return {
        "status": "mode_updated",
        "device_id": device_id,
        "manual_mode": mode.manual,
    }


@router.post("/hardware/leds/{device_id}/manual")
async def set_led_manual_duty(device_id: str, control: ManualControl):
    """Set manual LED brightness (only works in manual mode)."""
    device = device_registry.get_led(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"LED {device_id} not found")
    
    if device_id not in manual_devices:
        raise HTTPException(
            status_code=400,
            detail=f"LED {device_id} not in manual mode. Switch to manual mode first."
        )
    
    device.apply(control.duty)
    
    return {
        "status": "duty_set",
        "device_id": device_id,
        "duty": control.duty,
        "voltage": device.get_voltage(),
    }
