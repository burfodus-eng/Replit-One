"""Real-time control loop for GPIO/PWM devices."""

import logging
import time
from typing import Dict, Set
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.hw_devices import registry as device_registry
from app.services.hw_patterns import pattern_registry


# LED follow mappings (LED_ID -> WAVEMAKER_ID)
led_follow_map: Dict[str, str] = {}

# Devices in manual mode (don't apply patterns)
manual_devices: Set[str] = set()


async def realtime_tick():
    """
    Real-time control loop - runs at 10-20Hz.
    
    Evaluates patterns and applies to hardware devices.
    """
    try:
        current_time = time.time()
        
        # Get all pattern values at current time
        pattern_values = pattern_registry.get_all_values(current_time)
        
        # Apply patterns to wavemakers (if not in manual mode)
        for device_id, value in pattern_values.items():
            if device_id in manual_devices:
                continue
            
            device = device_registry.get_wavemaker(device_id)
            if device:
                device.apply(value)
        
        # Apply LED follow mappings
        for led_id, wavemaker_id in led_follow_map.items():
            if led_id in manual_devices:
                continue
            
            # Get wavemaker's current pattern value
            if wavemaker_id in pattern_values:
                led_device = device_registry.get_led(led_id)
                if led_device:
                    led_device.apply(pattern_values[wavemaker_id])
    
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


def get_control_state() -> dict:
    """Get current state of control system."""
    return {
        "scheduler_running": hw_scheduler.running,
        "manual_devices": list(manual_devices),
        "led_follow_map": dict(led_follow_map),
        "gpio_mode": device_registry.mode,
    }
