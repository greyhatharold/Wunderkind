"""
Main entry point for the AI Assistant project.
Handles initialization, event loop, and shutdown procedures.
"""

import logging
import signal
import sys
import time
from typing import Optional

# Append system root to path
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Internal modules
from src.config import load_config, get_pin_config
from src.data.world_model import WorldModel
from src.hardware.hardware_integration import HardwareIntegration

# These will be created later
from src.speech.speech_handler import SpeechRecognizer, TextToSpeech
from src.data.chat_handler_world import ChatHandlerWorld
# from hologram_display import HologramDisplay  # Future feature
# from gesture_recognition import GestureRecognizer  # Future feature

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_assistant.log')
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting AI Assistant application")

class AIAssistant:
    """Main AI Assistant class that coordinates all components."""
    
    def __init__(self):
        """Initialize the AI Assistant and its components."""
        logger.debug("Initializing AI Assistant")
        self.config = load_config()
        logger.debug("Configuration loaded")
        self.pin_config = get_pin_config()
        logger.debug("Pin configuration loaded")
        self.running = False
        
        # Add WorldModel initialization
        self.world_model = WorldModel()
        logger.debug("World model initialized")
        
        # Initialize hardware integration
        self.hardware = HardwareIntegration(self.world_model, self.config)
        logger.debug("Hardware integration initialized")
        
        # Initialize components
        try:
            self._init_components()
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def _init_components(self):
        """Initialize all component subsystems."""
        logger.info("Initializing AI Assistant components...")
        
        # Initialize speech components
        logger.debug("Initializing speech recognizer")
        self.speech_recognizer = SpeechRecognizer(
            language=self.config["STT_LANGUAGE"],
            timeout=self.config["STT_TIMEOUT"],
            phrase_timeout=self.config["STT_PHRASE_TIMEOUT"]
        )
        
        logger.debug("Initializing text-to-speech engine")
        self.tts_engine = TextToSpeech(
            voice_id=self.config["TTS_VOICE_ID"],
            rate=self.config["TTS_RATE"],
            volume=self.config["TTS_VOLUME"]
        )
        
        # Initialize chat handler with world model
        logger.debug("Initializing chat handler")
        self.chat_handler = ChatHandlerWorld(
            world_model=self.world_model,
            config=self.config
        )
        
        # Initialize hardware components
        self._init_hardware()
        
        # Start hardware monitoring
        self.hardware.start_monitoring()
        
        # Register hardware callbacks
        self.hardware.register_callback("button_press", self._handle_button_press)
        self.hardware.register_callback("motion_detected", self._handle_motion_detected)
        
        logger.info("All components initialized successfully")

    def _init_hardware(self):
        """Initialize hardware components (LED, button, sensors)."""
        try:
            try:
                import RPi.GPIO as GPIO
                logger.debug("Using RPi.GPIO")
            except ImportError:
                from gpio_wrapper import GPIO
                logger.debug("Using GPIO wrapper")
            GPIO.setmode(GPIO.BCM)
            
            # Setup LED
            logger.debug(f"Setting up LED on pin {self.pin_config['LED_PIN']}")
            GPIO.setup(self.pin_config["LED_PIN"], GPIO.OUT)
            
            # Setup button with pull-up resistor
            logger.debug(f"Setting up button on pin {self.pin_config['BUTTON_PIN']}")
            GPIO.setup(self.pin_config["BUTTON_PIN"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Setup motion sensor
            logger.debug(f"Setting up motion sensor on pin {self.pin_config['MOTION_SENSOR_PIN']}")
            GPIO.setup(self.pin_config["MOTION_SENSOR_PIN"], GPIO.IN)
            
            # Setup servo if enabled
            if self.config.get("ENABLE_SERVO") and self.pin_config.get("SERVO_PIN"):
                logger.debug(f"Setting up servo on pin {self.pin_config['SERVO_PIN']}")
                GPIO.setup(self.pin_config["SERVO_PIN"], GPIO.OUT)
            else:
                logger.debug("Servo functionality disabled")
            
            logger.info("Hardware components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize hardware: {e}")
            raise

    async def start(self):
        """Start the AI Assistant's main loop."""
        self.running = True
        logger.info("AI Assistant starting...")
        
        # Welcome message
        self.tts_engine.speak("AI Assistant is now online and ready.")
        
        try:
            while self.running:
                if self._check_activation():
                    await self._handle_interaction()
                time.sleep(0.1)  # Prevent CPU overuse
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.shutdown()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.shutdown()

    def _check_activation(self) -> bool:
        """
        Check if the assistant should be activated.
        
        Returns:
            bool: True if activation criteria are met, False otherwise.
        """
        # Check for wake word
        if self.speech_recognizer.detect_wake_word("wunderkind"):
            logger.info("Wake word detected")
            return True
        
        # Check for button press
        try:
            import RPi.GPIO as GPIO
            if not GPIO.input(self.pin_config["BUTTON_PIN"]):
                logger.info("Button press detected")
                return True
        except ImportError:
            logger.debug("GPIO import failed, skipping button check")
            pass
        
        return False

    async def _handle_interaction(self):
        """Handle a single interaction with the user."""
        # Visual feedback
        logger.debug("Setting LED on")
        self._set_led(True)
        
        # Get user input
        logger.debug("Listening for user input")
        user_input = self.speech_recognizer.listen()
        if not user_input:
            logger.debug("No user input received")
            self._set_led(False)
            return
        
        logger.info(f"User said: {user_input}")
        
        # Add the interaction to world model
        self.world_model.add_fact(f"User said: {user_input}")
        
        # Check for shutdown command
        if "shutdown" in user_input.lower():
            logger.info("Shutdown command received")
            self.tts_engine.speak("Shutting down. Goodbye!")
            self.shutdown()
            return
        
        # Get world model summary to provide context
        context = self.world_model.get_summary()
        
        # Process the input and get response with context
        logger.debug("Generating response")
        response = await self.chat_handler.generate_response(
            f"Context:\n{context}\n\nUser input: {user_input}"
        )
        
        # Speak the response
        logger.debug("Speaking response")
        self.tts_engine.speak(response)
        
        # Add the response to world model
        self.world_model.add_fact(f"Assistant responded: {response}")
        
        # Visual feedback off
        logger.debug("Setting LED off")
        self._set_led(False)

    def _set_led(self, state: bool):
        """Set the LED state."""
        try:
            import RPi.GPIO as GPIO
            GPIO.output(self.pin_config["LED_PIN"], state)
            logger.debug(f"LED set to {state}")
        except ImportError:
            logger.debug("GPIO import failed, skipping LED control")
            pass

    def shutdown(self):
        """Perform a clean shutdown of the AI Assistant."""
        logger.info("Shutting down AI Assistant...")
        self.running = False
        
        # Cleanup hardware
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            logger.debug("GPIO cleanup completed")
        except ImportError:
            logger.debug("GPIO import failed, skipping cleanup")
            pass
        
        # Cleanup other components
        logger.debug("Cleaning up components")
        self.speech_recognizer.cleanup()
        self.tts_engine.cleanup()
        self.chat_handler.cleanup()
        
        if hasattr(self, 'hardware'):
            self.hardware.cleanup()
        
        logger.info("Shutdown complete")
        sys.exit(0)

    def _handle_button_press(self):
        """Handle button press events."""
        logger.info("Button press detected")
        self.hardware.set_led(True)  # Visual feedback
        # Additional button press handling logic
        self.hardware.set_led(False)

    def _handle_motion_detected(self):
        """Handle motion detection events."""
        logger.info("Motion detected")
        self.hardware.set_led(True)
        time.sleep(0.5)
        self.hardware.set_led(False)

def main():
    """Main entry point for the AI Assistant."""
    logger.info("Starting main function")
    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: None)  # Handle Ctrl+C gracefully
    logger.debug("Signal handlers configured")
    
    try:
        assistant = AIAssistant()
        assistant.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
