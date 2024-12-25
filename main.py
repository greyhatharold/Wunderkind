"""
Main entry point for the AI Assistant project.
Handles initialization, event loop, and shutdown procedures.
"""

import logging
import signal
import sys
import time
from typing import Optional

# Internal modules
from config import load_config, get_pin_config

# These will be created later
from speech_handler import SpeechRecognizer, TextToSpeech
from chat_handler import ChatHandler
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

class AIAssistant:
    """Main AI Assistant class that coordinates all components."""
    
    def __init__(self):
        """Initialize the AI Assistant and its components."""
        self.config = load_config()
        self.pin_config = get_pin_config()
        self.running = False
        
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
        self.speech_recognizer = SpeechRecognizer(
            language=self.config["STT_LANGUAGE"],
            timeout=self.config["STT_TIMEOUT"],
            phrase_timeout=self.config["STT_PHRASE_TIMEOUT"]
        )
        
        self.tts_engine = TextToSpeech(
            voice_id=self.config["TTS_VOICE_ID"],
            rate=self.config["TTS_RATE"],
            volume=self.config["TTS_VOLUME"]
        )
        
        # Initialize chat handler
        self.chat_handler = ChatHandler(
            config={  # Pass settings as a single config dictionary
                "OPENAI_API_KEY": self.config["OPENAI_API_KEY"],
                "OPENAI_MODEL": self.config["OPENAI_MODEL"],
                "MAX_TOKENS": self.config["OPENAI_MAX_TOKENS"],
                "TEMPERATURE": self.config["OPENAI_TEMPERATURE"]
            }
        )
        
        # Initialize hardware components
        self._init_hardware()
        
        logger.info("All components initialized successfully")

    def _init_hardware(self):
        """Initialize hardware components (LED, button, sensors)."""
        try:
            try:
                import RPi.GPIO as GPIO
            except ImportError:
                from gpio_wrapper import GPIO
            GPIO.setmode(GPIO.BCM)
            
            # Setup LED
            GPIO.setup(self.pin_config["LED_PIN"], GPIO.OUT)
            
            # Setup button with pull-up resistor
            GPIO.setup(self.pin_config["BUTTON_PIN"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Setup motion sensor
            GPIO.setup(self.pin_config["MOTION_SENSOR_PIN"], GPIO.IN)
            
            # Setup servo
            GPIO.setup(self.pin_config["SERVO_PIN"], GPIO.OUT)
            
            logger.info("Hardware components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize hardware: {e}")
            raise

    def start(self):
        """Start the AI Assistant's main loop."""
        self.running = True
        logger.info("AI Assistant starting...")
        
        # Welcome message
        self.tts_engine.speak("AI Assistant is now online and ready.")
        
        try:
            while self.running:
                if self._check_activation():
                    self._handle_interaction()
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
        if self.speech_recognizer.detect_wake_word("jarvis"):
            logger.info("Wake word detected")
            return True
        
        # Check for button press
        try:
            import RPi.GPIO as GPIO
            if not GPIO.input(self.pin_config["BUTTON_PIN"]):
                logger.info("Button press detected")
                return True
        except ImportError:
            pass
        
        return False

    def _handle_interaction(self):
        """Handle a single interaction with the user."""
        # Visual feedback
        self._set_led(True)
        
        # Get user input
        user_input = self.speech_recognizer.listen()
        if not user_input:
            self._set_led(False)
            return
        
        logger.info(f"User said: {user_input}")
        
        # Check for shutdown command
        if "shutdown" in user_input.lower():
            self.tts_engine.speak("Shutting down. Goodbye!")
            self.shutdown()
            return
        
        # Process the input and get response
        response = self.chat_handler.generate_response(user_input)
        
        # Speak the response
        self.tts_engine.speak(response)
        
        # Visual feedback off
        self._set_led(False)

    def _set_led(self, state: bool):
        """Set the LED state."""
        try:
            import RPi.GPIO as GPIO
            GPIO.output(self.pin_config["LED_PIN"], state)
        except ImportError:
            pass

    def shutdown(self):
        """Perform a clean shutdown of the AI Assistant."""
        logger.info("Shutting down AI Assistant...")
        self.running = False
        
        # Cleanup hardware
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except ImportError:
            pass
        
        # Cleanup other components
        self.speech_recognizer.cleanup()
        self.tts_engine.cleanup()
        self.chat_handler.cleanup()
        
        logger.info("Shutdown complete")
        sys.exit(0)

def main():
    """Main entry point for the AI Assistant."""
    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: None)  # Handle Ctrl+C gracefully
    
    try:
        assistant = AIAssistant()
        assistant.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
