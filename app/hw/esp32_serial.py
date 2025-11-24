"""ESP32 serial GPIO driver for USB-to-GPIO adapter."""

import logging
import serial
from typing import Dict, Optional
import os


class PigpioPWM:
    """PWM control via ESP32 serial communication (USB adapter)."""
    
    _serial_conn: Optional[serial.Serial] = None
    _instances: Dict[int, 'PigpioPWM'] = {}
    
    def __init__(self, pin: int, freq: int = 500):
        """
        Initialize PWM on an ESP32 GPIO pin via serial.
        
        Args:
            pin: ESP32 GPIO pin number (e.g., 25, 33, 32)
            freq: PWM frequency in Hz (informational only - ESP32 uses fixed freq)
        """
        self.pin = pin
        self.freq = freq
        self.duty = 0.0
        self.running = False
        
        # Initialize serial connection if not already done
        if PigpioPWM._serial_conn is None:
            port = os.getenv('ESP32_SERIAL_PORT', 'COM4')
            baudrate = int(os.getenv('ESP32_SERIAL_BAUD', '115200'))
            
            try:
                PigpioPWM._serial_conn = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    timeout=1,
                    write_timeout=1
                )
                logging.info(f"[ESP32] Connected to {port} at {baudrate} baud")
            except serial.SerialException as e:
                logging.error(f"[ESP32] Failed to open {port}: {e}")
                raise RuntimeError(f"Cannot connect to ESP32 on {port}") from e
        
        PigpioPWM._instances[pin] = self
        logging.info(f"[ESP32] Initialized PWM on GPIO{pin} at {freq}Hz")
        
        # Set initial state (off)
        self.set_duty(0.0)
    
    def _send_command(self, pwm_value: int) -> None:
        """
        Send PWM command to ESP32.
        
        Args:
            pwm_value: PWM value (0-255)
        """
        if PigpioPWM._serial_conn is None:
            logging.error("[ESP32] No serial connection available")
            return
        
        try:
            # Format: "PIN:VALUE\n"
            command = f"{self.pin}:{pwm_value}\n"
            PigpioPWM._serial_conn.write(command.encode())
            logging.debug(f"[ESP32] Sent: {command.strip()}")
        except serial.SerialException as e:
            logging.error(f"[ESP32] Failed to send command to GPIO{self.pin}: {e}")
    
    def set_frequency(self, hz: int) -> None:
        """
        Set PWM frequency.
        
        Note: ESP32 firmware uses fixed frequency (analogWrite).
        This is stored for compatibility but not sent to device.
        
        Args:
            hz: PWM frequency in Hz
        """
        old_freq = self.freq
        self.freq = hz
        logging.debug(f"[ESP32] GPIO{self.pin} frequency changed: {old_freq}Hz → {hz}Hz (informational only)")
    
    def set_duty(self, duty: float) -> None:
        """
        Set duty cycle and send to ESP32.
        
        Args:
            duty: Duty cycle from 0.0 (0%) to 1.0 (100%)
        """
        # Clamp to valid range
        duty = max(0.0, min(1.0, duty))
        
        # Apply gamma correction for more natural brightness perception
        gamma = 2.2
        raw_pwm = (duty ** gamma) * 255
        
        # Enforce minimum floor for visibility (1% should still be visible)
        if duty > 0 and raw_pwm < 5:
            raw_pwm = 5
        
        # Convert to integer for ESP32
        pwm_value = int(raw_pwm)
        
        # Send to ESP32
        self._send_command(pwm_value)
        
        # Update internal state
        if abs(self.duty - duty) > 0.01:  # Log significant changes only
            logging.debug(f"[ESP32] GPIO{self.pin} duty: {self.duty:.2%} → {duty:.2%} (PWM={pwm_value})")
        
        self.duty = duty
        self.running = (duty > 0)
    
    def start(self, duty: float = 0.0) -> None:
        """
        Start PWM with given duty cycle.
        
        Args:
            duty: Initial duty cycle (0.0-1.0)
        """
        self.running = True
        self.set_duty(duty)
        logging.info(f"[ESP32] Started PWM on GPIO{self.pin} at {duty:.2%}")
    
    def stop(self) -> None:
        """Stop PWM output (set to 0)."""
        self.running = False
        self.set_duty(0.0)
        logging.info(f"[ESP32] Stopped PWM on GPIO{self.pin}")
    
    def cleanup(self) -> None:
        """Cleanup resources for this pin."""
        self.stop()
        if self.pin in PigpioPWM._instances:
            del PigpioPWM._instances[self.pin]
    
    @classmethod
    def close_serial(cls) -> None:
        """Close the shared serial connection."""
        if cls._serial_conn is not None:
            try:
                cls._serial_conn.close()
                logging.info("[ESP32] Closed serial connection")
            except Exception as e:
                logging.error(f"[ESP32] Error closing serial: {e}")
            finally:
                cls._serial_conn = None
    
    @classmethod
    def get_all_states(cls) -> Dict[int, dict]:
        """Get current state of all ESP32 PWM channels (for debugging)."""
        return {
            pin: {
                "duty": inst.duty,
                "freq": inst.freq,
                "running": inst.running
            }
            for pin, inst in cls._instances.items()
        }
