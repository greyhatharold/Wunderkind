"""
Speech handling module for the AI Assistant project.
Provides text-to-speech and speech-to-text functionality using pyttsx3 and SpeechRecognition.
"""

import speech_recognition as sr
import pyttsx3
from typing import Optional, Tuple
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler and set level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create file handler and set level 
file_handler = logging.FileHandler('speech_handler.log')
file_handler.setLevel(logging.DEBUG)

# Create formatters
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatters to handlers
console_handler.setFormatter(console_formatter)
file_handler.setFormatter(file_formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

class SpeechRecognizer:
    """Handles speech-to-text operations."""
    
    def __init__(self, language: str = "en-US", timeout: int = 5, phrase_timeout: float = 1.5):
        """
        Initialize speech recognizer.
        
        Args:
            language (str): Language code for recognition
            timeout (int): Maximum time to listen for
            phrase_timeout (float): Timeout for phrase completion
        """
        self.language = language
        self.timeout = timeout
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = phrase_timeout
        self.recognizer.operation_timeout = timeout
        logger.info("Initialized SpeechRecognizer")

    def listen(self) -> Optional[str]:
        """
        Listen for speech input and convert to text.
        
        Returns:
            Optional[str]: Transcribed text or None if failed
        """
        try:
            with sr.Microphone() as source:
                logger.debug("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.debug("Listening for speech...")
                audio = self.recognizer.listen(source, timeout=self.timeout)
                
                logger.debug("Processing speech...")
                text = self.recognizer.recognize_google(
                    audio,
                    language=self.language
                )
                logger.info(f"Successfully transcribed: '{text}'")
                return text.lower()

        except sr.WaitTimeoutError:
            logger.warning("Listening timed out")
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
        except sr.RequestError as e:
            logger.error(f"Could not request results: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in listen(): {str(e)}")
        
        return None

    def detect_wake_word(self, wake_word: str = "hey wunderkind") -> bool:
        """
        Check for wake word in audio stream.
        
        Args:
            wake_word (str): Wake word to detect
            
        Returns:
            bool: True if wake word detected
        """
        try:
            with sr.Microphone() as source:
                logger.debug("Adjusting for ambient noise in wake word detection...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.debug("Listening for wake word...")
                audio = self.recognizer.listen(source, timeout=3)
                text = self.recognizer.recognize_google(audio).lower()
                detected = wake_word in text
                if detected:
                    logger.info(f"Wake word '{wake_word}' detected")
                return detected
        except Exception as e:
            logger.warning(f"Failed to detect wake word: {str(e)}")
            return False

    def cleanup(self):
        """Cleanup resources."""
        logger.debug("Cleaning up SpeechRecognizer resources")
        pass  # Add cleanup if needed

class TextToSpeech:
    """Handles text-to-speech operations."""
    
    def __init__(self, voice_id: Optional[str] = None, rate: int = 150, volume: float = 0.8):
        """
        Initialize text-to-speech engine.
        
        Args:
            voice_id (str, optional): Voice ID to use
            rate (int): Speech rate
            volume (float): Speech volume
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        
        # Set voice if specified
        if voice_id:
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if voice_id in voice.id:
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"Set voice to {voice.id}")
                    break
        logger.info("Initialized TextToSpeech")

    def speak(self, text: str) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text (str): Text to be spoken
            
        Returns:
            bool: True if successful
        """
        try:
            logger.debug(f"Speaking: '{text}'")
            self.engine.say(text)
            self.engine.runAndWait()
            logger.debug("Finished speaking")
            return True
        except Exception as e:
            logger.error(f"Error in speak(): {str(e)}")
            return False

    def cleanup(self):
        """Cleanup resources."""
        try:
            logger.debug("Cleaning up TextToSpeech resources")
            self.engine.stop()
        except Exception as e:
            logger.error(f"Error cleaning up TextToSpeech: {str(e)}")