"""
Hardware integration module for the AI Assistant project.
Demonstrates how to track hardware events (motion detection, button presses, etc.)
and update the WorldModel accordingly. This uses the GPIO wrapper logic to remain
cross-platform compatible.
"""

import logging
import time
from typing import Optional, Dict, Any, Callable
from threading import Thread, Event

# Attempt to import RPi.GPIO or fallback to the gpio_wrapper
try:
    import RPi.GPIO as GPIO
except ImportError:
    from gpio_wrapper import GPIO

from data.world_model import WorldModel
from config import load_config, get_pin_config

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('hardware.log')

# Create formatters
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set formatters
console_handler.setFormatter(console_formatter)
file_handler.setFormatter(file_formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

class HardwareIntegration:
    """
    Manages hardware inputs/outputs and updates the WorldModel with relevant events.
    Provides methods for controlling LEDs, servos, and monitoring sensors.
    """

    def __init__(self, world_model: WorldModel, config: Optional[dict] = None):
        """
        Initialize hardware integration with WorldModel and configuration.
        
        Args:
            world_model (WorldModel): Instance to track hardware state
            config (Optional[dict]): Configuration dictionary
        """
        self.world_model = world_model
        self.config = config or load_config()
        self.pin_config = get_pin_config()
        
        # Get pin assignments from config
        self.led_pin = self.pin_config["LED_PIN"]
        self.button_pin = self.pin_config["BUTTON_PIN"]
        self.motion_sensor_pin = self.pin_config["MOTION_SENSOR_PIN"]
        self.servo_pin = self.pin_config["SERVO_PIN"]
        
        # Event monitoring control
        self._stop_monitoring = Event()
        self._monitor_thread: Optional[Thread] = None
        
        # Callback registry
        self.event_callbacks: Dict[str, Callable] = {}
        
        # Initialize GPIO
        self.setup_gpio()
        logger.info("Hardware integration initialized")

    def setup_gpio(self) -> None:
        """Initialize GPIO pins based on configuration."""
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Setup LED as output
            GPIO.setup(self.led_pin, GPIO.OUT)
            logger.debug(f"LED pin {self.led_pin} configured as output")
            
            # Setup button with pull-up resistor
            GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logger.debug(f"Button pin {self.button_pin} configured with pull-up")
            
            # Setup motion sensor as input
            GPIO.setup(self.motion_sensor_pin, GPIO.IN)
            logger.debug(f"Motion sensor pin {self.motion_sensor_pin} configured as input")
            
            # Setup servo if enabled
            if self.config.get("ENABLE_SERVO") and self.servo_pin is not None:
                GPIO.setup(self.servo_pin, GPIO.OUT)
                logger.debug(f"Servo pin {self.servo_pin} configured as output")
            else:
                logger.debug("Servo functionality disabled")
            
            logger.info("GPIO setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during GPIO setup: {str(e)}")
            raise

    def start_monitoring(self) -> None:
        """Start monitoring hardware events in a separate thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("Hardware monitoring already running")
            return
            
        self._stop_monitoring.clear()
        self._monitor_thread = Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        logger.info("Hardware monitoring started")

    def stop_monitoring(self) -> None:
        """Stop the hardware monitoring thread."""
        if self._monitor_thread:
            self._stop_monitoring.set()
            self._monitor_thread.join()
            logger.info("Hardware monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop for hardware events."""
        logger.debug("Entering hardware monitoring loop")
        
        button_state = GPIO.input(self.button_pin)
        motion_state = GPIO.input(self.motion_sensor_pin)
        
        while not self._stop_monitoring.is_set():
            try:
                # Check button state (active low with pull-up)
                new_button_state = GPIO.input(self.button_pin)
                if new_button_state != button_state:
                    if new_button_state == GPIO.LOW:
                        self._handle_event("button_press")
                        # Add state to world model
                        self.world_model.update_hardware_state("button", "pressed")
                    else:
                        self.world_model.update_hardware_state("button", "released")
                    button_state = new_button_state
                
                # Check motion sensor
                new_motion_state = GPIO.input(self.motion_sensor_pin)
                if new_motion_state != motion_state:
                    if new_motion_state == GPIO.HIGH:
                        self._handle_event("motion_detected")
                        self.world_model.update_hardware_state("motion_sensor", "active")
                    else:
                        self.world_model.update_hardware_state("motion_sensor", "inactive")
                    motion_state = new_motion_state
                
                time.sleep(0.1)  # Prevent CPU overuse
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(1)  # Delay before retry

    def _handle_event(self, event_type: str) -> None:
        """
        Handle hardware events and trigger callbacks.
        
        Args:
            event_type (str): Type of hardware event detected
        """
        event_description = f"Hardware event: {event_type}"
        logger.debug(event_description)
        
        # Update world model
        self.world_model.update_hardware_event(event_description)
        
        # Trigger any registered callbacks
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type]()
            except Exception as e:
                logger.error(f"Error in event callback: {str(e)}")

    def register_callback(self, event_type: str, callback: Callable) -> None:
        """
        Register a callback function for specific hardware events.
        
        Args:
            event_type (str): Type of event to watch for
            callback (Callable): Function to call when event occurs
        """
        self.event_callbacks[event_type] = callback
        logger.debug(f"Registered callback for {event_type}")

    def set_led(self, state: bool) -> None:
        """
        Control LED state.
        
        Args:
            state (bool): True to turn on, False to turn off
        """
        try:
            GPIO.output(self.led_pin, GPIO.HIGH if state else GPIO.LOW)
            # Update world model with LED state
            self.world_model.update_hardware_state("led", "on" if state else "off")
            event_desc = f"LED turned {'on' if state else 'off'}"
            self.world_model.update_hardware_event(event_desc)
            logger.debug(event_desc)
        except Exception as e:
            logger.error(f"Error controlling LED: {str(e)}")

    def control_servo(self, angle: float) -> None:
        """
        Control servo motor position if enabled.
        
        Args:
            angle (float): Desired angle in degrees (0-180)
        """
        if not self.config.get("ENABLE_SERVO") or self.servo_pin is None:
            logger.debug("Servo control skipped - servo not enabled")
            return
            
        try:
            # Convert angle to duty cycle (example conversion)
            duty_cycle = 2.5 + (angle / 180.0) * 10.0
            
            # Configure PWM
            pwm = GPIO.PWM(self.servo_pin, 50)  # 50Hz frequency
            pwm.start(duty_cycle)
            
            # Hold position briefly
            time.sleep(0.5)
            
            # Cleanup
            pwm.stop()
            
            # Update world model with servo state
            self.world_model.update_hardware_state("servo", angle)
            event_desc = f"Servo rotated to {angle} degrees"
            self.world_model.update_hardware_event(event_desc)
            logger.debug(event_desc)
            
        except Exception as e:
            logger.error(f"Error controlling servo: {str(e)}")

    def cleanup(self) -> None:
        """Cleanup GPIO resources."""
        try:
            self.stop_monitoring()
            GPIO.cleanup()
            logger.info("Hardware resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

def main():
    """Example usage of HardwareIntegration class."""
    try:
        # Initialize components
        world_model = WorldModel()
        hardware = HardwareIntegration(world_model)
        
        # Example callback
        def on_motion():
            print("Motion detected!")
            hardware.set_led(True)
            time.sleep(1)
            hardware.set_led(False)
        
        # Register callback
        hardware.register_callback("motion_detected", on_motion)
        
        # Start monitoring
        hardware.start_monitoring()
        
        # Run for a while
        print("Monitoring hardware events (Ctrl+C to exit)...")
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if 'hardware' in locals():
            hardware.cleanup()

if __name__ == "__main__":
    main() 