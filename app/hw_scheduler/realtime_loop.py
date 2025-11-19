"""Real-time control loop for GPIO/PWM devices."""

import logging
import time
from typing import Dict, Set, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.hw_devices import registry as device_registry
from app.services.hw_patterns import pattern_registry


# LED follow mappings (LED_ID -> WAVEMAKER_ID)
led_follow_map: Dict[str, str] = {}

# Devices in manual mode (don't apply patterns)
manual_devices: Set[str] = set()

# Reference to PresetManager (set during startup)
preset_manager_ref: Optional[object] = None


async def realtime_tick():
    """
    Real-time control loop - runs at 10-20Hz.
    
    Evaluates patterns and applies to hardware devices.
    Priority: Preset power levels > Pattern values
    """
    try:
        current_time = time.time()
        
        # Check if we have an active preset - if so, use preset power levels
        # PresetManager returns Dict[int, float] with keys 1-6 and values 0-100
        preset_power_levels = {}
        preset_active = False
        if preset_manager_ref is not None:
            try:
                levels = preset_manager_ref.get_current_power_levels()
                if levels and any(v > 0 for v in levels.values()):
                    preset_power_levels = levels
                    preset_active = True
            except Exception as e:
                logging.debug(f"Could not get preset power levels: {e}")
        
        # Get all pattern values at current time (fallback when no preset)
        pattern_values = pattern_registry.get_all_values(current_time)
        
        # Apply to all registered wavemakers (not hard-coded range)
        for device_id in list(device_registry.wavemakers.keys()):
            if device_id in manual_devices:
                continue
            
            # Extract wavemaker number from device ID (e.g., "WM1" -> 1)
            try:
                wm_num = int(device_id.replace("WM", ""))
            except (ValueError, AttributeError):
                logging.warning(f"Could not extract wavemaker number from device ID: {device_id}")
                continue
            
            # Priority: preset power > pattern value > skip
            intensity = None
            if preset_active and wm_num in preset_power_levels:
                # Preset power levels are 0-100, convert to 0.0-1.0
                intensity = preset_power_levels[wm_num] / 100.0
            elif device_id in pattern_values:
                intensity = pattern_values[device_id]
            
            if intensity is not None:
                device = device_registry.get_wavemaker(device_id)
                if device:
                    device.apply(intensity)
        
        # Apply LED follow mappings
        for led_id, wavemaker_id in led_follow_map.items():
            if led_id in manual_devices:
                continue
            
            # Extract wavemaker number from device ID
            try:
                wm_num = int(wavemaker_id.replace("WM", ""))
            except (ValueError, AttributeError):
                logging.warning(f"Could not extract wavemaker number from {wavemaker_id}")
                continue
            
            # Get intensity using same priority logic
            intensity = None
            if preset_active and wm_num in preset_power_levels:
                intensity = preset_power_levels[wm_num] / 100.0
            elif wavemaker_id in pattern_values:
                intensity = pattern_values[wavemaker_id]
            
            if intensity is not None:
                led_device = device_registry.get_led(led_id)
                if led_device:
                    led_device.apply(intensity)
    
    except Exception as e:
        logging.error(f"Error in realtime tick: {e}", exc_info=True)


# APScheduler instance
hw_scheduler = AsyncIOScheduler()


def start_hw_scheduler():
    """Start the hardware control scheduler."""
    if hw_scheduler.running:
        logging.warning("Hardware scheduler already running")
        return
    
    # Add real-time control job at 20Hz (50ms interval)
    hw_scheduler.add_job(
        realtime_tick,
        "interval",
        seconds=0.05,  # 20Hz
        id="realtime_control",
        replace_existing=True
    )
    
    hw_scheduler.start()
    logging.info("Hardware scheduler started at 20Hz")


def stop_hw_scheduler():
    """Stop the hardware scheduler."""
    if hw_scheduler.running:
        hw_scheduler.shutdown()
        logging.info("Hardware scheduler stopped")


def set_manual_mode(device_id: str, manual: bool):
    """
    Set device to manual or automatic (pattern) mode.
    
    Args:
        device_id: Device identifier
        manual: True for manual mode, False for automatic
    """
    if manual:
        manual_devices.add(device_id)
        logging.info(f"{device_id} set to MANUAL mode")
    else:
        manual_devices.discard(device_id)
        logging.info(f"{device_id} set to AUTOMATIC mode")


def set_led_follow(led_id: str, wavemaker_id: str | None):
    """
    Configure LED to follow a wavemaker's pattern.
    
    Args:
        led_id: LED device identifier
        wavemaker_id: Wavemaker to follow, or None to disable following
    """
    if wavemaker_id is None:
        if led_id in led_follow_map:
            del led_follow_map[led_id]
        logging.info(f"{led_id} no longer following wavemaker")
    else:
        led_follow_map[led_id] = wavemaker_id
        logging.info(f"{led_id} now follows {wavemaker_id}")


def set_preset_manager(preset_manager):
    """
    Link PresetManager to hardware control loop.
    
    Args:
        preset_manager: PresetManager instance
    """
    global preset_manager_ref
    preset_manager_ref = preset_manager
    logging.info("PresetManager linked to hardware control loop")


def get_control_state() -> dict:
    """Get current state of control system."""
    return {
        "scheduler_running": hw_scheduler.running,
        "manual_devices": list(manual_devices),
        "led_follow_map": dict(led_follow_map),
        "gpio_mode": device_registry.mode,
        "preset_linked": preset_manager_ref is not None,
    }
